"""Menu principal et lancement d'une partie."""

import random

from ombrefer.classe import CLASSES
from ombrefer.donjon import DIFFICULTES, adapter_au_niveau, explorer, generer_donjon
from ombrefer.personnage import Joueur
from ombrefer.sauvegarde import charger, effacer_sauvegarde, sauvegarder
from ombrefer.succes import (
    MODE_ULTIME,
    SUCCES,
    afficher_succes,
    debloquer,
    noter_record_enfer,
    texte_record,
)

NB_SALLES_MIN = 6
NB_SALLES_MAX = 9
NIVEAU_FINAL = 10  # vaincre son boss termine le jeu


def demander_option(options):
    """Demande un numéro parmi les options. Renvoie l'option choisie, ou None pour revenir."""
    print("0. Retour")
    choix = input("Ton choix : ")
    while choix != "0" and choix not in options:
        print("Choix invalide.")
        choix = input("Ton choix : ")
    return options.get(choix)


def choisir_difficulte():
    """Demande la difficulté et renvoie ses réglages, ou None pour revenir."""
    print("Choix du niveau de difficulté")
    for numero, difficulte in DIFFICULTES.items():
        avertissement = " (comme Difficile, mais la mort efface le héros)"
        print(f"{numero}. {difficulte.nom}{avertissement if difficulte.mort_definitive else ''}")
    return demander_option(DIFFICULTES)


def choisir_classe():
    """Demande la classe du héros et la renvoie, ou None pour revenir."""
    print("Choix de la classe")
    for numero, classe in CLASSES.items():
        print(f"{numero}. {classe.resume()}")
    return demander_option(CLASSES)


def creer_heros(nom, classe, difficulte):
    """Crée un nouveau héros avec les stats de départ de sa classe et de la difficulté."""
    pv = round(difficulte.pv_joueur * classe.multiplicateur_pv)
    joueur = Joueur(nom, pv, difficulte.attaque_joueur + classe.bonus_attaque)
    joueur.difficulte = difficulte.nom
    joueur.prendre_classe(classe)
    return joueur


def difficulte_du_heros(joueur):
    """Renvoie les réglages du mode choisi à la création du héros."""
    return next(mode for mode in DIFFICULTES.values() if mode.nom == joueur.difficulte)


def choix_menu_principal():
    """Affiche le menu principal et renvoie le choix du joueur ("1", "2", "3" ou "4")."""
    print("\n=== Les Cryptes d'Ombrefer ===")
    print("1. Nouvelle partie\n2. Charger un héros\n3. Succès\n4. Quitter")
    choix = input("Ton choix : ")
    while choix not in ("1", "2", "3", "4"):
        print("Choix invalide.")
        choix = input("Ton choix : ")
    return choix


def demander_oui_non(question):
    """Pose la question jusqu'à obtenir une réponse valide. Renvoie True pour oui."""
    choix = input(question).strip().lower()
    while choix not in ("o", "n"):
        print("Réponse invalide.")
        choix = input(question).strip().lower()
    return choix == "o"


def terminer_le_jeu(joueur, niveau):
    """Raconte la fin du jeu et donne au héros le succès de son mode."""
    nom_succes, recit = SUCCES[joueur.difficulte]
    print(f"\nVICTOIRE ! {joueur.nom} termine le niveau {niveau}, le dernier des cryptes.")
    print(f"\n{recit}")
    print(f"\n=== Fin du jeu : {joueur.nom}, {joueur.classe.nom}, mode {joueur.difficulte} ===")
    if debloquer(joueur.difficulte):
        print(f"Succès obtenu : {nom_succes} !")
        if joueur.difficulte == MODE_ULTIME:
            print("C'est le succès ultime des Cryptes d'Ombrefer.")
    else:
        print(f"Tu possèdes déjà le succès {nom_succes}.")


def entrer_en_enfer(joueur, niveau):
    """Note le record et consomme la sauvegarde : seule une victoire permet d'en refaire une.

    Sans cela, quitter le jeu en plein combat perdu éviterait la mort. Seule la sauvegarde de ce
    héros est touchée : celui qui n'a jamais sauvegardé laisse le fichier d'un autre héros.
    """
    noter_record_enfer(joueur, niveau)
    if joueur.a_une_sauvegarde:
        effacer_sauvegarde()
        joueur.a_une_sauvegarde = False
    print("Mode Enfer : aucun retour possible. Mourir ou quitter ici efface ton héros.")


def jouer_niveau(joueur, difficulte):
    """Lance le niveau de donjon du héros. Renvoie True s'il veut continuer après sa victoire.

    La partie s'arrête là après le dernier niveau. Un héros d'une ancienne sauvegarde, déjà plus
    bas que le dernier niveau, termine le jeu à sa prochaine victoire.
    """
    niveau = joueur.niveau_donjon
    nb_salles = random.randint(NB_SALLES_MIN, NB_SALLES_MAX)
    crypte = generer_donjon(nb_salles, adapter_au_niveau(difficulte, niveau))
    print(
        f"{joueur.nom} entre dans les Cryptes d'Ombrefer, niveau {niveau}..."
        f" ({len(crypte)} salles)"
    )
    if niveau >= NIVEAU_FINAL:
        print("Aucun escalier ne descend plus bas : c'est le dernier niveau.")
    if difficulte.mort_definitive:
        entrer_en_enfer(joueur, niveau)
    if not explorer(joueur, crypte):
        print(f"{joueur.nom} a péri au niveau {niveau}.")
        if difficulte.mort_definitive:
            print("Le mode Enfer ne pardonne pas : ce héros est effacé pour toujours.")
            print(texte_record())
        return False
    if niveau >= NIVEAU_FINAL:
        terminer_le_jeu(joueur, niveau)
        return False
    joueur.finir_niveau_donjon()
    print(
        f"VICTOIRE ! {joueur.nom} termine le niveau {niveau}"
        f" avec {joueur.piece} pièces d'or, et se repose avant de redescendre."
    )
    if demander_oui_non("Sauvegarder ton héros ? (o/n) : "):
        sauvegarder(joueur)
        print("Héros sauvegardé.")
    return demander_oui_non(f"Descendre au niveau {joueur.niveau_donjon} ? (o/n) : ")


def jeu(joueur, difficulte):
    """Enchaîne les niveaux de donjon jusqu'à la mort du héros ou son retour au menu."""
    while jouer_niveau(joueur, difficulte):
        pass


def demander_nom():
    """Demande le nom du héros. Renvoie None si le joueur tape 0 pour revenir."""
    nom_hero = input("\nNom de ton héros (0 pour revenir) : ").strip()
    while not nom_hero:
        print("Le nom ne peut pas être vide.")
        nom_hero = input("\nNom de ton héros (0 pour revenir) : ").strip()
    if nom_hero == "0":
        return None
    return nom_hero


def nouvelle_partie():
    """Demande le nom, la classe et la difficulté, puis lance une partie avec ce héros."""
    nom_hero = demander_nom()
    if nom_hero is None:
        return
    classe = choisir_classe()
    if classe is None:
        return
    difficulte = choisir_difficulte()
    if difficulte is not None:
        jeu(creer_heros(nom_hero, classe, difficulte), difficulte)


def partie_chargee():
    """Charge le héros sauvegardé et le relance dans son mode et à son niveau de donjon."""
    aldric = charger()
    if aldric is None:
        print("Aucune sauvegarde trouvée.")
        return
    print(f"{aldric.nom} est de retour au niveau {aldric.niveau_donjon} ! {aldric}")
    print(f"Classe : {aldric.classe.nom} | Mode : {aldric.difficulte}")
    jeu(aldric, difficulte_du_heros(aldric))


def main():
    """Affiche le menu principal et enchaîne les parties jusqu'à ce que le joueur quitte."""
    while True:
        choix = choix_menu_principal()
        match choix:
            case "1":
                nouvelle_partie()
            case "2":
                partie_chargee()
            case "3":
                afficher_succes()
            case "4":
                print("À bientôt, aventurier !")
                break
