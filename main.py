"""Point d'entrée du jeu : menu principal et lancement d'une partie."""

import random

from donjon import DIFFICULTES, adapter_au_niveau, explorer, generer_donjon
from personnage import Joueur
from sauvegarde import charger, sauvegarder

NB_SALLES_MIN = 6
NB_SALLES_MAX = 9


def choisir_difficulte():
    """Demande la difficulté et renvoie ses réglages, ou None pour revenir."""
    print("Choix du niveau de difficulté")
    for numero, difficulte in DIFFICULTES.items():
        print(f"{numero}. {difficulte.nom}")
    print("0. Retour")
    choix = input("Ton choix : ")
    while choix != "0" and choix not in DIFFICULTES:
        print("Choix invalide.")
        choix = input("Ton choix : ")
    return DIFFICULTES.get(choix)


def creer_heros(nom, difficulte):
    """Crée un nouveau héros avec les stats de départ de la difficulté."""
    joueur = Joueur(nom, difficulte.pv_joueur, difficulte.attaque_joueur)
    joueur.defense = difficulte.defense_joueur
    return joueur


def choix_menu_principal():
    """Affiche le menu principal et renvoie le choix du joueur ("1", "2" ou "3")."""
    print("\n=== Les Cryptes d'Ombrefer ===")
    print("1. Nouvelle partie\n2. Charger un héros\n3. Quitter")
    choix = input("Ton choix : ")
    while choix not in ("1", "2", "3"):
        print("Choix invalide.")
        choix = input("Ton choix : ")
    return choix


def jeu(joueur, difficulte):
    """Lance une partie complète avec ce héros, puis propose de le sauvegarder."""
    nb_salles = random.randint(NB_SALLES_MIN, NB_SALLES_MAX)
    crypte = generer_donjon(nb_salles, adapter_au_niveau(difficulte, joueur.niveau))
    print(f"{joueur.nom} entre dans les Cryptes d'Ombrefer... ({len(crypte)} salles)")
    resultat = explorer(joueur, crypte)
    if resultat:
        print(
            f"VICTOIRE ! {joueur.nom} sort de la crypte"
            f" avec {joueur.piece} pièces d'or."
        )
        choix = input("Sauvegarder ton héros ? (o/n) : ").strip().lower()
        while choix not in ("o", "n"):
            print("Réponse invalide.")
            choix = input("Sauvegarder ton héros ? (o/n) : ").strip().lower()
        if choix == "o":
            sauvegarder(joueur)
            print("Héros sauvegardé.")
    else:
        print(f"{joueur.nom} a péri.")


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
    """Demande le nom et la difficulté, puis lance une partie avec un nouveau héros."""
    nom_hero = demander_nom()
    if nom_hero is None:
        return
    difficulte = choisir_difficulte()
    if difficulte is not None:
        jeu(creer_heros(nom_hero, difficulte), difficulte)


def partie_chargee():
    """Charge le héros sauvegardé et le relance : il garde ses stats dans tous les modes."""
    aldric = charger()
    if aldric is None:
        print("Aucune sauvegarde trouvée.")
        return
    print(f"{aldric.nom} est de retour ! {aldric}")
    difficulte = choisir_difficulte()
    if difficulte is not None:
        jeu(aldric, difficulte)


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
                print("À bientôt, aventurier !")
                break


if __name__ == "__main__":
    main()
