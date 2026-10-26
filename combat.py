"""Déroulement d'un combat au tour par tour et point d'entrée du jeu."""

import random

from personnage import Joueur, Ennemi
from objet import afficher_inventaire, Potion


def tour_attaque(attaquant, cible):
    """Fait attaquer la cible par l'attaquant et affiche les dégâts infligés."""
    montant_degat, critique = attaquant.attaquer(cible)
    if critique:
        print(f"{attaquant.nom} attaque {cible.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{attaquant.nom} attaque {cible.nom} et inflige {montant_degat} dégâts.")


def combat(joueur, ennemi):
    """Lance un combat et renvoie "victoire", "defaite" ou "fuite"."""
    compteur = 1
    while joueur.est_vivant() and ennemi.est_vivant():
        print(f"--- Tour {compteur} ---")
        print(joueur)
        print(ennemi)
        print(f"1. Attaquer   2. Utiliser un objet ({len(joueur.inventaire)})   3. Fuir   4. Se défendre")
        choix = input("Ton choix : ")
        while choix not in ("1", "2", "3", "4"):
            print("Réponse invalide.")
            choix = input("Ton choix : ")
        match choix:
            case "1":
                tour_attaque(joueur, ennemi)
                if ennemi.est_vivant():
                    tour_attaque(ennemi, joueur)
                else:
                    return "victoire"
            case "2":
                if not joueur.inventaire:
                    print("Ton inventaire est vide.")
                    continue
                afficher_inventaire(joueur)
                choix_objet = input("Quel objet ? ")
                numeros = [str(n) for n in range(1, len(joueur.inventaire) + 1)]
                while choix_objet not in numeros:
                    print("Numéro invalide.")
                    choix_objet = input("Quel objet ? ")
                index = int(choix_objet) - 1
                objet = joueur.inventaire[index]
                if not objet.peut_etre_utilise(joueur):
                    print(f"{joueur.nom} a déjà tous ses PV !")
                    continue
                print(joueur.utiliser_objet(index))
                tour_attaque(ennemi, joueur)
            case "3":
                fuite = random.random() < 0.5
                if fuite:
                    return "fuite"
                print("Fuite ratée !")
                tour_attaque(ennemi, joueur)
            case "4":
                print("La défense est doublée.")
                defense_initial = joueur.defense
                joueur.defense *= 2
                tour_attaque(ennemi, joueur)
                joueur.defense = defense_initial
        compteur += 1
    return "defaite"


if __name__ == "__main__":
    aldric = Joueur("Aldric", 30, 5)
    gobelin = Ennemi("Gobelin", 12, 5, 10)
    rat_geant = Ennemi("Rat géant", 18, 4, 6)
    squelette = Ennemi("Squelette", 10, 6, 8)
    adversaire = random.choice([gobelin, rat_geant, squelette])
    aldric.ramasser_objet(Potion("Potion de soin", 20))
    aldric.ramasser_objet(Potion("Potion de soin", 20))
    print(f"Un {adversaire.nom} surgit ! {adversaire}")
    resultat = combat(aldric, adversaire)
    match resultat:
        case "victoire":
            aldric.gagner_or(adversaire.recompense)
            print(f"{adversaire.nom} est vaincu !")
            print(f"Victoire ! {aldric.nom} ramasse {adversaire.recompense} pièces d'or.")
            print(aldric)
        case "defaite":
            print(f"{aldric.nom} est tombé... Game over.")
        case "fuite":
            print(f"{aldric.nom} prend la fuite !")
