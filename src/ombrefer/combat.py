"""Déroulement d'un combat au tour par tour."""

import random

from ombrefer.effet import DEGATS_SAIGNEMENT, IMMOBILISATION, POISON, SAIGNEMENT
from ombrefer.objet import afficher_inventaire

DUREE_DEFENSE = 3


def debut_de_tour(personnage):
    """Fait vieillir les effets du personnage et annonce le poison. Renvoie True s'il peut agir."""
    avant = personnage.pv
    peut_agir = personnage.passer_un_tour()
    if personnage.pv < avant:
        print(f"{personnage.nom} perd {avant - personnage.pv} PV à cause du {POISON.lower()}.")
    return peut_agir


def annoncer_immobilisation(personnage):
    """Affiche que le personnage perd son tour."""
    print(f"{IMMOBILISATION} : {personnage.nom} passe son tour.")


def tenter_effet(attaquant, cible):
    """Tente d'infliger à la cible l'effet de l'attaquant, s'il en a un."""
    inflige = attaquant.effet_inflige()
    if inflige is None or not cible.est_vivant():
        return
    effet, chance = inflige
    if random.random() < chance:
        if cible.recevoir_effet(effet):
            print(f"{cible.nom} subit : {effet} !")
        else:
            print(f"{cible.nom} résiste : {effet}.")


def tour_attaque(attaquant, cible):
    """Fait attaquer la cible : le saignement d'abord, puis le coup et son effet éventuel."""
    if SAIGNEMENT in attaquant.effets:
        attaquant.perdre_pv(DEGATS_SAIGNEMENT)
        print(f"{attaquant.nom} perd {DEGATS_SAIGNEMENT} PV à cause du {SAIGNEMENT.lower()}.")
        if not attaquant.est_vivant():
            return
    montant_degat, critique = attaquant.attaquer(cible)
    if critique:
        print(f"{attaquant.nom} attaque {cible.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{attaquant.nom} attaque {cible.nom} et inflige {montant_degat} dégâts.")
    if montant_degat > 0:
        tenter_effet(attaquant, cible)


def riposte(ennemi, joueur):
    """L'ennemi joue son tour : ses effets d'abord, puis son attaque s'il le peut."""
    if not joueur.est_vivant() or not ennemi.est_vivant():
        return
    peut_agir = debut_de_tour(ennemi)
    if not ennemi.est_vivant():
        return
    if peut_agir:
        tour_attaque(ennemi, joueur)
    else:
        annoncer_immobilisation(ennemi)


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
        print(objet.refus(joueur))
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
        print(f"Garde levée : encore {joueur.tours_defense} tour(s).")


def action_attaquer(joueur, ennemi):
    """Le joueur attaque, puis l'ennemi riposte s'il survit. Renvoie "victoire" ou None."""
    tour_attaque(joueur, ennemi)
    if not ennemi.est_vivant():
        return "victoire"
    riposte(ennemi, joueur)
    return None


def action_objet(joueur, ennemi):
    """Le joueur utilise un objet, puis l'ennemi attaque. Renvoie "annule" sinon, ou None."""
    if not utiliser_un_objet(joueur):
        return "annule"
    riposte(ennemi, joueur)
    return None


def action_fuir(joueur, ennemi, boss):
    """Le joueur tente de fuir (50 %), sinon l'ennemi attaque. Renvoie "fuite" ou None.
    Un boss ne peut pas être fui : la tentative échoue et le boss riposte.
    """
    if boss:
        print(f"{joueur.nom} ne peut pas fuir {ennemi.nom} !")
        riposte(ennemi, joueur)
        return None
    if random.random() < 0.5:
        return "fuite"
    print("Fuite ratée !")
    riposte(ennemi, joueur)
    return None


def action_defendre(joueur, ennemi):
    """Triple la défense et bloque les nouveaux effets pendant 3 tours, ce tour compris.

    Sans armure ni effet à craindre, il n'y a rien à gagner : l'action est refusée et
    renvoie "annule".
    """
    if joueur.defense == 0 and ennemi.effet_inflige() is None:
        print(f"{joueur.nom} n'a aucune armure : se défendre ne servirait à rien.")
        return "annule"
    print(f"Garde levée pendant {DUREE_DEFENSE} tours : défense triplée, aucun nouvel effet.")
    joueur.tours_defense = DUREE_DEFENSE
    riposte(ennemi, joueur)
    return None


def tour_joueur(joueur, ennemi, compteur, boss):
    """Joue un tour complet du joueur. Renvoie "victoire", "fuite" ou None."""
    peut_agir = debut_de_tour(joueur)
    if not joueur.est_vivant():
        return None
    if not peut_agir:
        afficher_tour(compteur, joueur, ennemi)
        annoncer_immobilisation(joueur)
        riposte(ennemi, joueur)
        return None
    while True:
        afficher_tour(compteur, joueur, ennemi)
        match choix_combat(joueur):
            case "1":
                return action_attaquer(joueur, ennemi)
            case "2":
                if action_objet(joueur, ennemi) != "annule":
                    return None
            case "3":
                return action_fuir(joueur, ennemi, boss)
            case "4":
                if action_defendre(joueur, ennemi) != "annule":
                    return None


def combat(joueur, ennemi, boss=False):
    """Lance un combat et renvoie "victoire", "defaite" ou "fuite"."""
    compteur = 1
    try:
        while joueur.est_vivant() and ennemi.est_vivant():
            issue = tour_joueur(joueur, ennemi, compteur, boss)
            if issue is not None:
                return issue
            compteur += 1
            joueur.tours_defense = max(0, joueur.tours_defense - 1)
        return "victoire" if joueur.est_vivant() else "defaite"
    finally:
        joueur.fin_de_combat()
