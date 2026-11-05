"""Déroulement d'un combat au tour par tour."""

import random

from ombrefer.objet import afficher_inventaire

DUREE_DEFENSE = 3


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
    print("  0. Retour")
    choix_objet = input("Quel objet ? ")
    numeros = [str(n) for n in range(len(joueur.inventaire) + 1)]
    while choix_objet not in numeros:
        print("Numéro invalide.")
        choix_objet = input("Quel objet ? ")
    if choix_objet == "0":
        return False
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


def afficher_tour(compteur, joueur, ennemi):
    """Affiche le numéro du tour et l'état des deux combattants."""
    print(f"\n--- Tour {compteur} ---")
    print(joueur)
    print(ennemi)
    if joueur.tours_defense > 0:
        print(f"Défense doublée : encore {joueur.tours_defense} tour(s).")


def action_attaquer(joueur, ennemi):
    """Le joueur attaque, puis l'ennemi riposte s'il survit. Renvoie "victoire" ou None."""
    tour_attaque(joueur, ennemi)
    if not ennemi.est_vivant():
        return "victoire"
    tour_attaque(ennemi, joueur)
    return None


def action_objet(joueur, ennemi):
    """Le joueur utilise un objet, puis l'ennemi attaque. Renvoie "annule" sinon, ou None."""
    if not utiliser_un_objet(joueur):
        return "annule"
    tour_attaque(ennemi, joueur)
    return None


def action_fuir(joueur, ennemi, boss):
    """Le joueur tente de fuir (50 %), sinon l'ennemi attaque. Renvoie "fuite" ou None.
    Un boss ne peut pas être fui : la tentative échoue et le boss riposte.
    """
    if boss:
        print(f"{joueur.nom} ne peut pas fuir {ennemi.nom} !")
        tour_attaque(ennemi, joueur)
        return None
    if random.random() < 0.5:
        return "fuite"
    print("Fuite ratée !")
    tour_attaque(ennemi, joueur)
    return None


def action_defendre(joueur, ennemi):
    """Double la défense du joueur pendant 3 tours, ce tour compris, puis l'ennemi attaque."""
    print(f"La défense est doublée pendant {DUREE_DEFENSE} tours.")
    joueur.tours_defense = DUREE_DEFENSE
    tour_attaque(ennemi, joueur)


def combat(joueur, ennemi, boss=False):
    """Lance un combat et renvoie "victoire", "defaite" ou "fuite"."""
    compteur = 1
    try:
        while joueur.est_vivant() and ennemi.est_vivant():
            afficher_tour(compteur, joueur, ennemi)
            match choix_combat(joueur):
                case "1":
                    if action_attaquer(joueur, ennemi) == "victoire":
                        return "victoire"
                case "2":
                    if action_objet(joueur, ennemi) == "annule":
                        continue
                case "3":
                    issue = action_fuir(joueur, ennemi, boss)
                    if issue == "fuite":
                        return "fuite"
                case "4":
                    action_defendre(joueur, ennemi)
            compteur += 1
            joueur.tours_defense = max(0, joueur.tours_defense - 1)
        return "defaite"
    finally:
        joueur.tours_defense = 0
