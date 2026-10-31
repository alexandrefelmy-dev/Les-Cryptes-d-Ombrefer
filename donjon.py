import random

from objet import Potion, Arme
from combat import combat, utiliser_un_objet
from personnage import Ennemi


MODELES_ENNEMIS = [
    ("Rat géant", 8, 4, 3),
    ("Gobelin", 12, 5, 6),
    ("Squelette", 10, 7, 8),
    ("Zombie", 22, 5, 10),
    ("Goule", 16, 8, 15),
]


class Salle:
    def __init__(self, numero, ennemi, butin, piege):
        self.numero = numero
        self.ennemi = ennemi
        self.butin = butin
        self.piege = piege


def creer_ennemi():
    return Ennemi(*random.choice(MODELES_ENNEMIS))


def creer_butin():
    tirage_butin = random.random()
    if tirage_butin < 0.5:
        return Potion("Potion de soin", 20)
    elif tirage_butin < 0.8:
        return None
    else:
        return Arme("Epée rouillée", 3)


def creer_salle(numero):
    return Salle(
        numero,
        creer_ennemi() if random.random() < 0.75 else None,
        creer_butin(),
        random.random() < 0.1,
    )


def pause(joueur):
    while True:
        print("1. Utiliser un objet\n2. Passer à la salle suivante")
        choix_pause = input("Ton choix : ")
        match choix_pause:
            case "1":
                utiliser_un_objet(joueur)
            case "2":
                break
            case _:
                print("Choix invalide.")


def generer_donjon(nb_salles):
    return [creer_salle(i) for i in range(1, nb_salles + 1)]


def explorer(joueur, donjon):
    for salle in donjon:
        print(f"\n=== Salle {salle.numero}/{len(donjon)} ===")
        if salle.piege:
            degats_piege = random.randint(3, 8)
            avant = joueur.pv
            joueur.subir_degats(degats_piege)
            degats_reel_piege = avant - joueur.pv
            print(f"{joueur.nom} s'est pris un piège, et a perdu {degats_reel_piege} PV.")
            if not joueur.est_vivant():
                return False
        if salle.ennemi is not None:
            print(f"Un {salle.ennemi.nom} surgit ! {salle.ennemi}")
            resultat = combat(joueur, salle.ennemi)
            if resultat == "defaite":
                return False
            elif resultat == "fuite":
                print(f"{joueur.nom} s'enfuit vers la salle suivante !")
                pause(joueur)
                continue
            joueur.gagner_or(salle.ennemi.recompense)
            print(f"{salle.ennemi.nom} est vaincu ! {joueur.nom} ramasse {salle.ennemi.recompense} pièces d'or.")
        else:
            print(f"La salle est vide... {joueur.nom} reprend son souffle.")
            pause(joueur)
        if salle.butin is not None:
            joueur.ramasser_objet(salle.butin)
            print(f"{joueur.nom} trouve : {salle.butin}")
            pause(joueur    )
    return True
