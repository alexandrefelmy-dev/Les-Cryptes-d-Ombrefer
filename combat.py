"""Déroulement d'un combat au tour par tour."""

import random

from objet import afficher_inventaire


def tour_attaque(attaquant, cible):
    """Fait attaquer la cible par l'attaquant et affiche les dégâts infligés."""
    montant_degat, critique = attaquant.attaquer(cible)
    if critique:
        print(f"{attaquant.nom} attaque {cible.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{attaquant.nom} attaque {cible.nom} et inflige {montant_degat} dégâts.")


def utiliser_un_objet(joueur):
    """Fait choisir et utiliser un objet. Renvoie True si un objet a été utilisé."""
    if not joueur.inventaire:
        print("Ton inventaire est vide.")
        return False
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
        return False
    print(joueur.utiliser_objet(index))
    return True


def choix_combat(joueur):
    """Affiche les actions possibles et renvoie le choix valide du joueur ("1" à "4")."""
    print(
        f"1. Attaquer   2. Utiliser un objet ({len(joueur.inventaire)})"
        "   3. Fuir   4. Se défendre"
        )
    choix = input("Ton choix : ")
    while choix not in ("1", "2", "3", "4"):
        print("Réponse invalide.")
        choix = input("Ton choix : ")
    return choix


def combat(joueur, ennemi):
    """Lance un combat et renvoie "victoire", "defaite" ou "fuite"."""
    compteur = 1
    while joueur.est_vivant() and ennemi.est_vivant():
        print(f"\n--- Tour {compteur} ---")
        print(joueur)
        print(ennemi)
        choix = choix_combat(joueur)
        match choix:
            case "1":
                tour_attaque(joueur, ennemi)
                if ennemi.est_vivant():
                    tour_attaque(ennemi, joueur)
                else:
                    return "victoire"
            case "2":
                resultat_objet = utiliser_un_objet(joueur)
                if not resultat_objet:
                    continue
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
