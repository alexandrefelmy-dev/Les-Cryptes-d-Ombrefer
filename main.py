"""Point d'entrée du jeu : menu principal et lancement d'une partie."""

import random

from donjon import explorer, generer_donjon
from personnage import Joueur
from sauvegarde import charger, sauvegarder


def choisir_difficulte():
    """Demande la difficulté et renvoie un donjon de la taille correspondante."""
    print("Choix du niveau de difficulté")
    print("1. Facile\n2. Intermédiaire\n3. Difficile")
    choix = input("Ton choix : ")
    while choix not in ("1", "2", "3"):
        print("Choix invalide.")
        choix = input("Ton choix : ")
    match choix:
        case "1":
            return generer_donjon(3)
        case "2":
            return generer_donjon(random.randint(4, 5))
        case "3":
            return generer_donjon(random.randint(6, 10))


def choix_menu_principal():
    """Affiche le menu principal et renvoie le choix du joueur ("1", "2" ou "3")."""
    print("\n=== Les Cryptes d'Ombrefer ===")
    print("1. Nouvelle partie\n2. Charger un héros\n3. Quitter")
    choix = input("Ton choix : ")
    while choix not in ("1", "2", "3"):
        print("Choix invalide.")
        choix = input("Ton choix : ")
    return choix


def jeu(joueur):
    """Lance une partie complète avec ce héros, puis propose de le sauvegarder."""
    crypte = choisir_difficulte()
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


def main():
    """Affiche le menu principal et enchaîne les parties jusqu'à ce que le joueur quitte."""
    while True:
        choix = choix_menu_principal()
        match choix:
            case "1":
                nom_hero = input("\nNom de ton héros : ").strip()
                while not nom_hero:
                    print("Le nom ne peut pas être vide.")
                    nom_hero = input("\nNom de ton héros : ").strip()
                aldric = Joueur(nom_hero, 30, 8)
                jeu(aldric)
            case "2":
                aldric = charger()
                if aldric is None:
                    print("Aucune sauvegarde trouvée.")
                    continue
                print(f"{aldric.nom} est de retour ! {aldric.nom} "
                      f"(PV : {aldric.pv}/{aldric.pv_max})"
                      f" | Niveau {aldric.niveau} | Or : {aldric.piece}")
                jeu(aldric)
            case "3":
                print("À bientôt, aventurier !")
                break


if __name__ == "__main__":
    main()
