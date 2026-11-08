"""Simulateur d'équilibrage : un bot joue des parties entières avec le vrai code du jeu.

Seules les décisions du joueur sont remplacées : combats, salles, butin, boutique et événements
restent ceux du jeu. Rien n'est sauvegardé, et aucun succès n'est débloqué.

Exemples, depuis la racine du dépôt :

    PYTHONPATH=src python tools/simulateur.py
    PYTHONPATH=src python tools/simulateur.py --classes Guerrier --modes Facile,Enfer --profil brut
    PYTHONPATH=src python tools/simulateur.py --classes Guerrier --variantes \
        '{"recharge 4": {"classe.Guerrier.recharge": 4}, "poison": {"personnage.DEGATS_POISON": 4}}'

Une variante change des réglages le temps de la mesure, sans toucher au code. Son chemin part d'un
module d'ombrefer. Une constante importée par son nom se règle dans le module qui l'utilise :
DEGATS_POISON se règle dans personnage. Les valeurs d'un dictionnaire se règlent par leur clé :
effet.DUREES.Poison.
"""

import argparse
import contextlib
import importlib
import json
import multiprocessing
import os
import random
from unittest.mock import patch

from ombrefer import boutique, combat, donjon, evenement
from ombrefer.classe import CLASSES
from ombrefer.effet import AFFAIBLISSEMENT, POISON, SAIGNEMENT
from ombrefer.main import NB_SALLES_MAX, NB_SALLES_MIN, NIVEAU_FINAL, creer_heros
from ombrefer.objet import Arme, Armure, Potion, Remede

# Réglés pour que le bot prudent finisse le jeu dans environ 31 % des parties en Facile et 11 % en
# Intermédiaire, sur les 5 classes : un peu moins que le bot dont le README cite les chiffres.
SEUIL_PAUSE = 0.95  # part des PV sous laquelle le bot boit une potion entre deux salles
SEUIL_POTION = 0.2  # part des PV sous laquelle il boit une potion en combat
SEUIL_POTION_BRUT = 0.35
SEUIL_FUITE = 0.35  # part des PV sous laquelle il fuit, s'il n'a plus de potion
MARGE_COUPS = 1.1  # il boit aussi quand il lui reste moins de PV que ce nombre de coups
PART_COUP_DANGEREUX = 0.2  # il lève sa garde si un coup retire cette part de ses PV
DEFENSE_UTILE = 2  # défense sous laquelle la garde ne sert que contre les effets
STOCK_POTIONS = 2  # il ne garde pas plus de potions que ça en réserve à la boutique
VALEUR_EFFET = 2  # points d'attaque que vaut, pour le bot, une arme à effet
PART_SOIN_FONTAINE = 0.7  # il ne boit à la fontaine que sous cette part de ses PV
PART_SANG = 0.6  # il n'offre son sang à l'autel qu'au-dessus de cette part de ses PV
PART_FORCER = 0.5  # il ne force un coffre qu'au-dessus de cette part de ses PV

NB_LOTS = 48  # découpe chaque mesure pour répartir les parties entre les processus


def part_pv(joueur):
    """Renvoie la part des PV qu'il reste au joueur."""
    return joueur.pv / joueur.pv_max


def potions(joueur):
    """Renvoie la position des potions dans l'inventaire."""
    return [i for i, objet in enumerate(joueur.inventaire) if isinstance(objet, Potion)]


def boire(joueur, gaspiller=True):
    """Boit la plus forte potion qui ne gaspille rien, sinon la plus petite si gaspiller est vrai.

    Renvoie True si une potion a été bue.
    """
    positions = potions(joueur)
    if not positions:
        return False
    manque = joueur.pv_max - joueur.pv
    sans_perte = [i for i in positions if joueur.inventaire[i].soin <= manque]
    if sans_perte:
        joueur.utiliser_objet(max(sans_perte, key=lambda i: joueur.inventaire[i].soin))
        return True
    if gaspiller:
        joueur.utiliser_objet(min(positions, key=lambda i: joueur.inventaire[i].soin))
    return gaspiller


def remede_contre(joueur, effets):
    """Renvoie la position d'un remède contre l'un de ces effets, ou None."""
    for i, objet in enumerate(joueur.inventaire):
        if isinstance(objet, Remede) and any(effet in objet.effets for effet in effets):
            return i
    return None


def attaquer(joueur, ennemi):
    """Lance l'attaque spéciale si elle est prête, sinon une attaque normale."""
    if joueur.recharge_speciale == 0:
        return combat.action_speciale(joueur, ennemi)
    return combat.action_attaquer(joueur, ennemi)


def action_brute(joueur, ennemi, _boss):
    """Joue vite : une potion quand ça va mal, et jamais de garde, de remède ni de fuite."""
    if part_pv(joueur) < SEUIL_POTION_BRUT and boire(joueur):
        combat.riposte(ennemi, joueur)
        return None
    return attaquer(joueur, ennemi)


def veut_lever_sa_garde(joueur, ennemi, boss, coup):
    """Renvoie True si la garde est encore permise et vaut un tour contre cet ennemi."""
    if joueur.garde_utilisee:
        return False
    utile = joueur.defense >= DEFENSE_UTILE or ennemi.effet_inflige() is not None
    return utile and (boss or coup >= joueur.pv * PART_COUP_DANGEREUX)


def action_prudente(joueur, ennemi, boss):
    """Se soigne au dernier moment, guérit ce qui gêne, lève sa garde et fuit s'il va mal."""
    coup = max(1, ennemi.attaque_actuelle() - joueur.defense)
    critique = part_pv(joueur) < SEUIL_POTION or joueur.pv <= coup * MARGE_COUPS
    if critique and boire(joueur):
        combat.riposte(ennemi, joueur)
        return None
    genants = [SAIGNEMENT, AFFAIBLISSEMENT] if boss else [SAIGNEMENT]
    remede = remede_contre(joueur, [effet for effet in genants if effet in joueur.effets])
    if remede is not None:
        joueur.utiliser_objet(remede)
        combat.riposte(ennemi, joueur)
        return None
    if not boss and part_pv(joueur) < SEUIL_FUITE and not potions(joueur):
        return combat.action_fuir(joueur, ennemi, boss)
    if veut_lever_sa_garde(joueur, ennemi, boss, coup):
        return combat.action_defendre(joueur, ennemi)
    return attaquer(joueur, ennemi)


PROFILS = {"prudent": action_prudente, "brut": action_brute}


def valeur_arme(joueur, arme):
    """Renvoie ce que vaut cette arme pour le bot, selon la classe du héros."""
    return arme.bonus_pour(joueur.classe) + (VALEUR_EFFET if arme.effet else 0)


def valeur_armure(_joueur, armure):
    """Renvoie ce que vaut cette armure pour le bot."""
    return armure.bonus


def porter_le_meilleur(joueur, type_objet, porte, valeur):
    """Porte le meilleur objet de ce type de l'inventaire, s'il vaut mieux que celui porté."""
    actuelle = valeur(joueur, porte) if porte else -1
    meilleurs = [
        i for i, objet in enumerate(joueur.inventaire)
        if isinstance(objet, type_objet) and valeur(joueur, objet) > actuelle
    ]
    if meilleurs:
        joueur.utiliser_objet(max(meilleurs, key=lambda i: valeur(joueur, joueur.inventaire[i])))


def equiper_le_meilleur(joueur):
    """Porte la meilleure arme et la meilleure armure de l'inventaire."""
    porter_le_meilleur(joueur, Arme, joueur.arme, valeur_arme)
    porter_le_meilleur(joueur, Armure, joueur.armure, valeur_armure)


def vendre_les_restes(joueur):
    """Vend les armes et les armures rangées dans l'inventaire."""
    for objet in list(joueur.inventaire):
        if isinstance(objet, (Arme, Armure)):
            boutique.vendre(joueur, objet)


def interet_achat(joueur, objet):
    """Renvoie l'intérêt d'un objet en vente, par pièce d'or : 0 ou moins s'il ne sert à rien."""
    if isinstance(objet, Arme):
        portee = valeur_arme(joueur, joueur.arme) if joueur.arme else 0
        return (valeur_arme(joueur, objet) - portee) * 6 / max(1, objet.prix())
    if isinstance(objet, Armure):
        ecart = objet.bonus - (joueur.armure.bonus if joueur.armure else 0)
        return ecart * 18 / max(1, objet.prix())
    if isinstance(objet, Potion):
        return 0.5 if len(potions(joueur)) < STOCK_POTIONS else 0.02
    return 0.05


def faire_ses_achats(joueur, stock):
    """Vend ce qui ne sert plus, puis achète dans l'ordre du meilleur intérêt."""
    equiper_le_meilleur(joueur)
    vendre_les_restes(joueur)
    for objet in sorted(stock, key=lambda o: interet_achat(joueur, o), reverse=True):
        if interet_achat(joueur, objet) > 0:
            boutique.acheter(joueur, stock, stock.index(objet))
    equiper_le_meilleur(joueur)
    vendre_les_restes(joueur)


def vivre_evenement(joueur, choix):
    """Décide à la place du joueur : le risque n'est pris que s'il a assez de PV."""
    part = part_pv(joueur)
    match choix:
        case evenement.Fontaine():
            action = choix.boire if part < PART_SOIN_FONTAINE else choix.remplir_fiole
            action(joueur)
        case evenement.AutelMaudit():
            if part > PART_SANG and joueur.pv > choix.cout_sang(joueur):
                choix.offrir_sang(joueur)
        case evenement.CoffrePiege():
            action = choix.forcer if part > PART_FORCER else choix.crocheter
            action(joueur)
        case evenement.Prisonnier():
            choix.liberer(joueur)
        case evenement.Forge():
            if joueur.piece >= choix.prix(joueur) and joueur.arme is not None:
                choix.reforger_arme(joueur)
            elif joueur.piece >= choix.prix(joueur) and joueur.armure is not None:
                choix.reforger_armure(joueur)


def reprendre_des_forces(joueur):
    """Boit tant que le héros est sous le seuil, sans gaspiller s'il n'est pas trop bas."""
    while part_pv(joueur) < SEUIL_PAUSE and boire(joueur, part_pv(joueur) < SEUIL_PAUSE - 0.2):
        pass


def pause(joueur, stock=None, choix=None):
    """Remplace la pause entre deux salles : s'équipe, se soigne, achète et vit l'événement."""
    equiper_le_meilleur(joueur)
    reprendre_des_forces(joueur)
    antidote = remede_contre(joueur, [POISON]) if POISON in joueur.effets else None
    if antidote is not None:
        joueur.utiliser_objet(antidote)
    if stock is not None:
        faire_ses_achats(joueur, stock)
    if choix is not None:
        vivre_evenement(joueur, choix)
        equiper_le_meilleur(joueur)
    reprendre_des_forces(joueur)


def reglage(chemin, valeur):
    """Renvoie le remplacement temporaire d'un réglage. Un chemin inconnu lève une erreur."""
    nom_module, *noms, dernier = chemin.split(".")
    cible = importlib.import_module(f"ombrefer.{nom_module}")
    for nom in noms:
        cible = getattr(cible, nom)
    if not isinstance(cible, dict):
        return patch.object(cible, dernier, valeur)
    if dernier not in cible:
        raise KeyError(chemin)
    return patch.dict(cible, {dernier: valeur})


def jouer_partie(classe, difficulte):
    """Joue une partie du premier au dernier niveau. Renvoie le nombre de niveaux terminés."""
    joueur = creer_heros("Bot", classe, difficulte)
    for niveau in range(1, NIVEAU_FINAL + 1):
        nb_salles = random.randint(NB_SALLES_MIN, NB_SALLES_MAX)
        crypte = donjon.generer_donjon(nb_salles, donjon.adapter_au_niveau(difficulte, niveau))
        if not donjon.explorer(joueur, crypte):
            return niveau - 1
        if niveau < NIVEAU_FINAL:
            joueur.finir_niveau_donjon()
    return NIVEAU_FINAL


def jouer_lot(tache):
    """Joue un lot de parties, sans rien afficher, et renvoie le nombre de fins à chaque niveau.

    tache : (nom de classe, nom de mode, nombre de parties, graine, profil, réglages).
    Le bot et les réglages sont retirés à la fin, même après une erreur.
    """
    nom_classe, nom_mode, nb_parties, graine, profil, reglages = tache
    classe = next(c for c in CLASSES.values() if c.nom == nom_classe)
    difficulte = next(d for d in donjon.DIFFICULTES.values() if d.nom == nom_mode)
    remplacements = [reglage(chemin, valeur) for chemin, valeur in reglages.items()]
    remplacements += [
        patch.object(combat, "jouer_action", PROFILS[profil]),
        patch.object(donjon, "pause", pause),
    ]
    random.seed(graine)
    fins = [0] * (NIVEAU_FINAL + 1)
    with open(os.devnull, "w", encoding="utf-8") as muet, contextlib.redirect_stdout(muet):
        for remplacement in remplacements:
            remplacement.start()
        try:
            for _ in range(nb_parties):
                fins[jouer_partie(classe, difficulte)] += 1
        finally:
            for remplacement in reversed(remplacements):
                remplacement.stop()
    return fins


def resumer(fins):
    """Renvoie le taux de victoire, les niveaux terminés en moyenne et la survie par niveau."""
    total = sum(fins)
    return {
        "parties": total,
        "victoire": fins[NIVEAU_FINAL] / total,
        "niveaux": sum(niveau * nb for niveau, nb in enumerate(fins)) / total,
        "survie": [sum(fins[niveau:]) / total for niveau in range(1, NIVEAU_FINAL + 1)],
    }


def mesurer(pool, nom_classe, nom_mode, options, variante):
    """Répartit les parties d'une mesure entre les processus et renvoie son résumé.

    variante : (nom de la variante, ses réglages).
    """
    nom_variante, reglages = variante
    taille, reste = divmod(options.parties, NB_LOTS)
    taches = [
        (
            nom_classe, nom_mode, taille + (numero < reste),
            f"{options.graine}/{nom_variante}/{nom_mode}/{nom_classe}/{numero}",
            options.profil, reglages,
        )
        for numero in range(NB_LOTS)
    ]
    fins = [0] * (NIVEAU_FINAL + 1)
    for lot in pool.imap_unordered(jouer_lot, taches):
        fins = [a + b for a, b in zip(fins, lot)]
    return resumer(fins)


def lire_options():
    """Lit les options de la ligne de commande."""
    modes = [difficulte.nom for difficulte in donjon.DIFFICULTES.values()]
    classes = [classe.nom for classe in CLASSES.values()]
    lecteur = argparse.ArgumentParser(description="Mesure l'équilibre des classes et des modes.")
    lecteur.add_argument("--parties", type=int, default=4800, help="parties par mesure")
    lecteur.add_argument("--modes", default=",".join(modes), help="modes séparés par des virgules")
    lecteur.add_argument("--classes", default=",".join(classes), help="classes, même format")
    lecteur.add_argument("--profil", choices=PROFILS, default="prudent", help="style du bot")
    lecteur.add_argument("--graine", type=int, default=1, help="même graine, mêmes parties")
    lecteur.add_argument("--variantes", default="{}", help='{"nom": {"chemin": valeur}}, en JSON')
    lecteur.add_argument("--sortie", help="fichier JSON où écrire les résultats")
    return lecteur.parse_args()


def main():
    """Lance les mesures demandées et affiche une ligne par mesure."""
    options = lire_options()
    variantes = json.loads(options.variantes) or {"actuel": {}}
    resultats = {}
    with multiprocessing.Pool() as pool:
        for variante in variantes.items():
            for nom_mode in options.modes.split(","):
                for nom_classe in options.classes.split(","):
                    mesure = mesurer(pool, nom_classe, nom_mode, options, variante)
                    cle = f"{variante[0]} | {nom_mode} | {nom_classe}"
                    resultats[cle] = mesure
                    survie = " ".join(f"{part * 100:3.0f}" for part in mesure["survie"])
                    print(
                        f"{cle:48} victoire {mesure['victoire'] * 100:6.2f} %"
                        f"  niveaux {mesure['niveaux']:5.2f}  survie {survie}",
                        flush=True,
                    )
    if options.sortie:
        with open(options.sortie, "w", encoding="utf-8") as fichier:
            json.dump(resultats, fichier, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
