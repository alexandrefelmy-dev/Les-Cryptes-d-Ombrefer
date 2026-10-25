import random

from personnage import Joueur, Ennemi


def tour_attaque(attaquant, cible):
    montant_degat, critique = attaquant.attaquer(cible)
    if critique:
        print(f"{attaquant.nom} attaque {cible.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{attaquant.nom} attaque {cible.nom} et inflige {montant_degat} dégâts.")


def combat(joueur, ennemi):
    compteur = 1
    while joueur.est_vivant() and ennemi.est_vivant():
        print(f"--- Tour {compteur} ---")
        print(joueur)
        print(ennemi)
        print(f"1. Attaquer   2. Boire une potion ({joueur.potion})   3. Fuir   4. Se défendre")
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
                if joueur.potion > 0:
                    montant_soigner = joueur.soigner(20)
                    print(f"{joueur.nom} s'est soigné de {montant_soigner} pv.")
                    joueur.potion -= 1
                    tour_attaque(ennemi, joueur)
                else:
                    print(f"{joueur.nom} n'a plus assez de potions.")
                    continue
            case "3":
                fuite = random.random() < 0.5
                if fuite:
                    return "fuite"
                else:
                    print("Fuite ratée !")
                    tour_attaque(ennemi, joueur)
            case "4":
                print("La défense est doublée.")
                defense_initial = joueur.defense
                joueur.defense *= 2
                tour_attaque(ennemi, joueur)
                joueur.defense = defense_initial
        if not joueur.est_vivant():
            return "defaite"
        compteur += 1


if __name__ == "__main__":
    aldric = Joueur("Aldric", 30, 5)
    gobelin = Ennemi("Gobelin", 12, 5, 10)
    rat_geant = Ennemi("Rat géant", 18, 4, 6)
    squelette = Ennemi("Squelette", 10, 6, 8)
    ennemi = random.choice([gobelin, rat_geant, squelette])
    print(f"Un {ennemi.nom} surgit ! {ennemi}")
    resultat = combat(aldric, ennemi)
    match resultat:
        case "victoire":
            aldric.gagner_or(ennemi.recompense)
            print(f"{ennemi.nom} est vaincu !")
            print(f"Victoire ! {aldric.nom} ramasse {ennemi.recompense} pièces d'or.")
            print(aldric)
        case "defaite":
            print(f"{aldric.nom} est tombé... Game over.")
        case "fuite":
            print(f"{aldric.nom} prend la fuite !")