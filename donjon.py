"""Génération aléatoire du donjon (salles, ennemis, butin, pièges) et exploration."""

import random
from dataclasses import dataclass, replace

from objet import Potion, Arme
from combat import combat, utiliser_un_objet
from personnage import Ennemi


MODELES_ENNEMIS = [
    ("Rat géant", 8, 5, 3),
    ("Gobelin", 12, 6, 6),
    ("Squelette", 10, 8, 8),
    ("Zombie", 22, 6, 10),
    ("Goule", 16, 9, 15),
]

# Chaque boss : (nom, PV, attaque, récompense), puis son arme (nom, bonus d'attaque).
MODELES_BOSS = [
    (("Golem d'Ombrefer", 80, 8, 40), ("Poing de fer", 6)),
    (("Spectre de Valbrume", 30, 16, 60), ("Lame spectrale", 12)),
    (("Roi liche", 50, 12, 50), ("Epée du roi liche", 10)),
    (("Seigneur vampire", 55, 12, 80), ("Croc de sang", 9)),
]

# Chaque arme : (nom, bonus d'attaque, chances de tomber sur 1000 salles).
MODELES_ARMES = [
    ("Dague ébréchée", 1, 56),
    ("Gourdin noueux", 2, 42),
    ("Epée rouillée", 3, 32),
    ("Hache de garde", 4, 24),
    ("Masse d'armes", 5, 18),
    ("Lance d'acier", 7, 12),
    ("Sabre runique", 9, 8),
    ("Epée de l'aube", 12, 4),
    ("Faux des ombres", 16, 3),
    ("Lame d'Ombrefer", 30, 1),
]


# Renforcement des ennemis pour chaque niveau du héros au-dessus du niveau 1.
FORCE_PAR_NIVEAU = 0.3


@dataclass
class Difficulte:  # pylint: disable=too-many-instance-attributes
    """Réglages d'un mode de difficulté."""

    nom: str
    pv_joueur: int
    attaque_joueur: int
    defense_joueur: int
    force_ennemis: float  # multiplie les PV et l'attaque des ennemis et des boss
    recompense_boss: float  # multiplie l'or et le bonus de l'arme laissés par le boss
    gain_ennemis: float = 1  # multiplie l'or et l'XP des ennemis normaux
    chance_piege: float = 0.1
    chance_potion: float = 0.5
    rarete_armes: float = 0  # de 0 à 1 : plus c'est haut, moins les armes fortes sont rares
    nb_boss: int = len(MODELES_BOSS)  # seuls les premiers boss de MODELES_BOSS sont possibles


DIFFICULTES = {
    "1": Difficulte(
        "Facile", 32, 8, 2, 1.15, 1.0,
        gain_ennemis=1.0, chance_piege=0.05, chance_potion=0.55, rarete_armes=0.0, nb_boss=3,
    ),
    "2": Difficulte(
        "Intermédiaire", 28, 8, 2, 1.25, 1.5,
        gain_ennemis=1.25, chance_piege=0.1, chance_potion=0.5, rarete_armes=0.1, nb_boss=3,
    ),
    "3": Difficulte(
        "Difficile", 25, 7, 2, 1.35, 2.0,
        gain_ennemis=1.5, chance_piege=0.2, chance_potion=0.4, rarete_armes=0.2, nb_boss=4,
    ),
}


@dataclass
class Salle:
    """Salle du donjon : un ennemi, un butin et un piège éventuels."""

    numero: int
    ennemi: Ennemi | None
    butin: Potion | Arme | None
    piege: bool
    boss: bool = False


def ajuster(valeur, multiplicateur):
    """Multiplie une valeur et l'arrondit, sans descendre en dessous de 1."""
    return max(1, round(valeur * multiplicateur))


def adapter_au_niveau(difficulte, niveau):
    """Renvoie la difficulté avec des ennemis renforcés selon le niveau du héros."""
    force = difficulte.force_ennemis * (1 + FORCE_PAR_NIVEAU * (niveau - 1))
    return replace(difficulte, force_ennemis=force)


def creer_ennemi(difficulte):
    """Crée un ennemi tiré au hasard parmi MODELES_ENNEMIS, adapté à la difficulté."""
    nom, pv, attaque, recompense = random.choice(MODELES_ENNEMIS)
    force = difficulte.force_ennemis
    gain = difficulte.gain_ennemis
    return Ennemi(nom, ajuster(pv, force), ajuster(attaque, force), ajuster(recompense, gain))


def creer_arme(difficulte):
    """Crée une arme tirée au hasard : plus elle est forte, plus elle est rare, dans tous les modes.

    Élever les chances à une puissance inférieure à 1 rapproche les armes sans changer leur ordre.
    """
    poids = [chances ** (1 - difficulte.rarete_armes) for _, _, chances in MODELES_ARMES]
    nom, bonus, _ = random.choices(MODELES_ARMES, weights=poids)[0]
    return Arme(nom, bonus)


def creer_potion(tirage):
    """Renvoie une potion pour un tirage entre 0 et 1 : grande 16 %, moyenne 34 %, petite 50 %."""
    if tirage < 0.16:
        return Potion("Grande potion de soin", 40)
    if tirage < 0.5:
        return Potion("Potion de soin", 20)
    return Potion("Petite potion de soin", 10)


def creer_butin(difficulte):
    """Renvoie une potion selon la difficulté. Sinon : rien (60 %) ou une arme (40 %)."""
    tirage_butin = random.random()
    chance_potion = difficulte.chance_potion
    if tirage_butin < chance_potion:
        return creer_potion(tirage_butin / chance_potion)
    if tirage_butin < chance_potion + (1 - chance_potion) * 0.6:
        return None
    return creer_arme(difficulte)


def creer_salle(numero, difficulte):
    """Crée une salle avec 75 % de chances d'ennemi et un piège selon la difficulté."""
    return Salle(
        numero,
        creer_ennemi(difficulte) if random.random() < 0.75 else None,
        creer_butin(difficulte),
        random.random() < difficulte.chance_piege,
    )


def creer_salle_boss(donjon, difficulte):
    """Crée la salle finale : la difficulté choisit le boss, sa force et ses récompenses."""
    boss_possibles = MODELES_BOSS[:difficulte.nb_boss]
    (nom, pv, attaque, recompense), (nom_arme, bonus) = random.choice(boss_possibles)
    force = difficulte.force_ennemis
    gain = difficulte.recompense_boss
    return Salle(
        len(donjon) + 1,
        Ennemi(nom, ajuster(pv, force), ajuster(attaque, force), ajuster(recompense, gain)),
        Arme(nom_arme, ajuster(bonus, gain)),
        random.random() < difficulte.chance_piege,
        boss=True,
    )


def pause(joueur):
    """Laisse le joueur utiliser des objets jusqu'à ce qu'il passe à la salle suivante."""
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


def generer_donjon(nb_salles, difficulte):
    """Renvoie la liste des salles du donjon, numérotées à partir de 1, terminée par le boss."""
    salles = [creer_salle(i, difficulte) for i in range(1, nb_salles)]
    salles.append(creer_salle_boss(salles, difficulte))
    return salles


def declencher_piege(joueur):
    """Inflige les dégâts d'un piège au joueur. Renvoie True s'il survit."""
    degats_piege = random.randint(3, 8)
    avant = joueur.pv
    joueur.subir_degats(degats_piege)
    degats_reel_piege = avant - joueur.pv
    print(f"{joueur.nom} s'est pris un piège, et a perdu {degats_reel_piege} PV.")
    return joueur.est_vivant()


def affronter_ennemi(joueur, ennemi, boss=False):
    """Lance le combat contre l'ennemi et renvoie son résultat ("victoire", "fuite", "defaite")."""
    print(f"Un {ennemi.nom} surgit ! {ennemi}")
    resultat = combat(joueur, ennemi, boss)
    if resultat == "fuite":
        print(f"{joueur.nom} s'enfuit vers la salle suivante !")
        pause(joueur)
    elif resultat != "defaite":
        joueur.gagner_or(ennemi.recompense)
        print(
            f"{ennemi.nom} est vaincu ! {joueur.nom}"
            f" ramasse {ennemi.recompense} pièces d'or."
        )
        montee_de_niveau = joueur.gagner_xp(ennemi.recompense)
        if montee_de_niveau:
            print(
                f"{joueur.nom} passe au niveau {joueur.niveau} !"
                f" PV max {joueur.pv_max}, attaque {joueur.attaque}."
            )
    return resultat


def ramasser_butin(joueur, butin):
    """Ajoute le butin à l'inventaire du joueur."""
    joueur.ramasser_objet(butin)
    print(f"{joueur.nom} trouve : {butin}")


def traverser_salle(joueur, salle):
    """Fait traverser une salle au joueur. Renvoie True s'il en sort vivant."""
    if salle.piege and not declencher_piege(joueur):
        return False
    if salle.ennemi is not None:
        resultat = affronter_ennemi(joueur, salle.ennemi, salle.boss)
        if resultat == "defaite":
            return False
        if resultat == "fuite":
            return True
    else:
        print(f"La salle est vide... {joueur.nom} reprend son souffle.")
    if salle.butin is not None:
        ramasser_butin(joueur, salle.butin)
    pause(joueur)
    return True


def explorer(joueur, donjon):
    """Fait traverser les salles au joueur. Renvoie True s'il sort vivant du donjon."""
    for salle in donjon:
        print(f"\n=== Salle {salle.numero}/{len(donjon)} ===")
        if not traverser_salle(joueur, salle):
            return False
    return True
