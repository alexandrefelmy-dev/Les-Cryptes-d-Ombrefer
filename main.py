import random


from donjon import explorer, generer_donjon
from objet import Potion
from personnage import Joueur

def difficulté():
    print("Choix du niveau de difficulté")
    print("1. Facile")


def main():
    while True:
        print("\n=== LES CRYPTES D'OMBREFER ===")
        print("1. Nouvelle partie\n2. Quitter")
        choix = input("Ton choix : ").strip()
        while choix not in ("1", "2"):
             print("Choix invalide.")
             choix = input("\nTon choix : ").strip()
        match choix:
            case "1":
                nom_hero = input("\nNom de ton héros : ").strip()
                while not nom_hero:
                    print("Le nom ne peut pas être vide.")
                    nom_hero = input("\nNom de ton héros : ").strip()
                aldric = Joueur(nom_hero, 30, 8)
                aldric.ramasser_objet(Potion("Potion de soin", 20))
                crypte = generer_donjon(random.randint(3, 6))
                print(f"{aldric.nom} entre dans les Cryptes d'Ombrefer... ({len(crypte)} salles)")
                resultat = explorer(aldric, crypte)
                if resultat:
                    print(f"VICTOIRE ! {aldric.nom} sort de la crypte avec {aldric.piece} pièces d'or.")
                else:
                    print(f"{aldric.nom} a péri.")
            case "2":
                print("À bientôt, aventurier !")
                break


if __name__ == "__main__":
    main()