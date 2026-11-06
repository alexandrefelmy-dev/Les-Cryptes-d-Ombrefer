"""Génération aléatoire du donjon (salles, ennemis, butin, pièges) et exploration."""

import os
import random
import sys
from dataclasses import dataclass, replace

from ombrefer.boutique import visiter_boutique
from ombrefer.objet import Armure, Potion, Arme, Remede
from ombrefer.combat import combat, debut_de_tour, utiliser_un_objet
from ombrefer.effet import AFFAIBLISSEMENT, IMMOBILISATION, POISON, SAIGNEMENT
from ombrefer.personnage import Ennemi


# Chaque ennemi, du plus faible au plus dangereux : (nom, PV, attaque, récompense,
# effet infligé, chances d'apparaître sur 100). Sans effet, un ennemi a de meilleures stats.
MODELES_ENNEMIS = [
    ("Rat géant", 6, 4, 3, POISON, 24),
    ("Chauve-souris sanglante", 7, 6, 5, SAIGNEMENT, 18),
    ("Araignée des cryptes", 9, 6, 7, POISON, 15),
    ("Gobelin", 15, 7, 9, None, 13),
    ("Squelette", 14, 9, 11, None, 10),
    ("Ombre rampante", 16, 8, 14, AFFAIBLISSEMENT, 8),
    ("Zombie", 24, 6, 15, IMMOBILISATION, 6),
    ("Gargouille", 28, 9, 22, None, 4),
    ("Goule", 22, 12, 28, None, 2),
]

# Chaque boss : (nom, PV, attaque, récompense, son effet), puis son arme (nom, bonus, effet).
MODELES_BOSS = [
    (("Golem d'Ombrefer", 80, 8, 40, IMMOBILISATION), ("Poing de fer", 8, IMMOBILISATION)),
    (("Spectre de Valbrume", 30, 16, 60, POISON), ("Lame spectrale", 16, POISON)),
    (("Roi liche", 50, 12, 50, AFFAIBLISSEMENT), ("Epée du roi liche", 14, AFFAIBLISSEMENT)),
    (("Seigneur vampire", 55, 12, 80, SAIGNEMENT), ("Croc de sang", 12, SAIGNEMENT)),
]

# Chaque arme : (nom, bonus d'attaque, chances de tomber sur 1000 salles, effet infligé).
MODELES_ARMES = [
    ("Dague empoisonnée", 2, 56, POISON),
    ("Gourdin noueux", 3, 42, None),
    ("Epée rouillée", 4, 32, None),
    ("Hache de garde", 6, 24, SAIGNEMENT),
    ("Masse d'armes", 8, 18, IMMOBILISATION),
    ("Lance d'acier", 11, 12, None),
    ("Sabre runique", 15, 8, AFFAIBLISSEMENT),
    ("Epée de l'aube", 20, 4, None),
    ("Faux des ombres", 28, 3, SAIGNEMENT),
    ("Lame d'Ombrefer", 50, 1, POISON),
]

# Chaque armure : (nom, bonus de défense, chances de tomber sur 1000 salles, effet bloqué).
MODELES_ARMURES = [
    ("Cuir traité", 1, 39, POISON),
    ("Gambison matelassé", 2, 26, SAIGNEMENT),
    ("Cotte de mailles", 3, 15, None),
    ("Broigne de garde", 5, 9, AFFAIBLISSEMENT),
    ("Cuirasse d'acier", 7, 5, None),
    ("Harnois runique", 9, 3, IMMOBILISATION),
    ("Armure de l'aube", 12, 2, AFFAIBLISSEMENT),
    ("Armure d'Ombrefer", 16, 1, POISON),
]

# Chaque remède : (nom, effets guéris, chances relatives de tomber).
MODELES_REMEDES = [
    ("Antidote", (POISON,), 40),
    ("Potion coagulante", (SAIGNEMENT,), 30),
    ("Potion de vigueur", (AFFAIBLISSEMENT,), 25),
    ("Panacée", (POISON, SAIGNEMENT, AFFAIBLISSEMENT), 5),
]

# Chance qu'un coup qui touche inflige l'effet de celui qui frappe.
CHANCE_EFFET_ENNEMI = 0.25
CHANCE_EFFET_BOSS = 0.4


# Chance qu'un marchand attende à la sortie d'une salle (jamais après le boss).
CHANCE_BOUTIQUE = 0.3

# Répartition du butin quand ce n'est pas une potion. Le reste (40 %) donne une arme.
PART_RIEN = 0.3
PART_REMEDES = 0.1
PART_ARMURES = 0.2

# Renforcement des ennemis pour chaque niveau du héros au-dessus du niveau 1.
FORCE_PAR_NIVEAU = 0.37


@dataclass
class Difficulte:  # pylint: disable=too-many-instance-attributes
    """Réglages d'un mode de difficulté."""

    nom: str
    pv_joueur: int
    attaque_joueur: int
    force_ennemis: float  # multiplie les PV et l'attaque des ennemis et des boss
    recompense_boss: float  # multiplie l'or et le bonus de l'arme laissés par le boss
    gain_ennemis: float = 1  # multiplie l'or et l'XP des ennemis normaux
    chance_piege: float = 0.1
    chance_potion: float = 0.5
    rarete_armes: float = 0  # de 0 à 1 : plus c'est haut, moins armes et armures fortes sont rares
    nb_boss: int = len(MODELES_BOSS)  # seuls les premiers boss de MODELES_BOSS sont possibles


DIFFICULTES = {
    "1": Difficulte(
        "Facile", 41, 8, 1.15, 1.0,
        gain_ennemis=1.0, chance_piege=0.05, chance_potion=0.55, rarete_armes=0.0, nb_boss=3,
    ),
    "2": Difficulte(
        "Intermédiaire", 33, 8, 1.25, 1.5,
        gain_ennemis=1.25, chance_piege=0.1, chance_potion=0.5, rarete_armes=0.1, nb_boss=3,
    ),
    "3": Difficulte(
        "Difficile", 24, 7, 1.35, 2.0,
        gain_ennemis=1.5, chance_piege=0.2, chance_potion=0.4, rarete_armes=0.2, nb_boss=4,
    ),
}


@dataclass
class Salle:
    """Salle du donjon : un ennemi, un butin, un piège et une boutique éventuels."""

    numero: int
    ennemi: Ennemi | None
    butin: Potion | Remede | Arme | Armure | None
    piege: bool
    boss: bool = False
    boutique: list | None = None  # objets en vente à la sortie de la salle


def ajuster(valeur, multiplicateur):
    """Multiplie une valeur et l'arrondit, sans descendre en dessous de 1."""
    return max(1, round(valeur * multiplicateur))


def adapter_au_niveau(difficulte, niveau):
    """Renvoie la difficulté avec des ennemis renforcés selon le niveau du héros."""
    force = difficulte.force_ennemis * (1 + FORCE_PAR_NIVEAU * (niveau - 1))
    return replace(difficulte, force_ennemis=force)


def creer_ennemi(difficulte):
    """Crée un ennemi selon ses chances d'apparaître, adapté à la difficulté."""
    poids = [modele[5] for modele in MODELES_ENNEMIS]
    nom, pv, attaque, recompense, effet, _ = random.choices(MODELES_ENNEMIS, weights=poids)[0]
    force = difficulte.force_ennemis
    gain = difficulte.gain_ennemis
    return Ennemi(
        nom, ajuster(pv, force), ajuster(attaque, force), ajuster(recompense, gain),
        effet, CHANCE_EFFET_ENNEMI,
    )


def tirer_modele(modeles, difficulte):
    """Tire un modèle au hasard : plus il est fort, plus il est rare, dans tous les modes.

    Élever les chances à une puissance inférieure à 1 rapproche les modèles sans changer leur ordre.
    """
    poids = [modele[2] ** (1 - difficulte.rarete_armes) for modele in modeles]
    return random.choices(modeles, weights=poids)[0]


def creer_arme(difficulte):
    """Crée une arme tirée au hasard parmi MODELES_ARMES."""
    nom, bonus, _, effet = tirer_modele(MODELES_ARMES, difficulte)
    return Arme(nom, bonus, effet)


def creer_armure(difficulte):
    """Crée une armure tirée au hasard parmi MODELES_ARMURES."""
    nom, bonus, _, protection = tirer_modele(MODELES_ARMURES, difficulte)
    return Armure(nom, bonus, protection)


def creer_remede(difficulte):
    """Crée un remède tiré au hasard parmi MODELES_REMEDES."""
    nom, effets, _ = tirer_modele(MODELES_REMEDES, difficulte)
    return Remede(nom, effets)


def creer_potion(tirage):
    """Renvoie une potion pour un tirage entre 0 et 1 : grande 16 %, moyenne 34 %, petite 50 %."""
    if tirage < 0.16:
        return Potion("Grande potion de soin", 40)
    if tirage < 0.5:
        return Potion("Potion de soin", 20)
    return Potion("Petite potion de soin", 10)


def creer_butin(difficulte):
    """Renvoie une potion selon la difficulté. Sinon : rien, un remède, une armure ou une arme."""
    tirage_butin = random.random()
    chance_potion = difficulte.chance_potion
    if tirage_butin < chance_potion:
        return creer_potion(tirage_butin / chance_potion)
    hors_potions = (tirage_butin - chance_potion) / (1 - chance_potion)
    if hors_potions < PART_RIEN:
        return None
    if hors_potions < PART_RIEN + PART_REMEDES:
        return creer_remede(difficulte)
    if hors_potions < PART_RIEN + PART_REMEDES + PART_ARMURES:
        return creer_armure(difficulte)
    return creer_arme(difficulte)


def creer_boutique(difficulte):
    """Renvoie les objets d'une boutique : une potion, un remède, une arme et une armure."""
    return [
        creer_potion(random.random()),
        creer_remede(difficulte),
        creer_arme(difficulte),
        creer_armure(difficulte),
    ]


def creer_salle(numero, difficulte):
    """Crée une salle avec 75 % de chances d'ennemi, un piège et peut-être une boutique."""
    return Salle(
        numero,
        creer_ennemi(difficulte) if random.random() < 0.75 else None,
        creer_butin(difficulte),
        random.random() < difficulte.chance_piege,
        boutique=creer_boutique(difficulte) if random.random() < CHANCE_BOUTIQUE else None,
    )


def creer_salle_boss(donjon, difficulte):
    """Crée la salle finale : la difficulté choisit le boss, sa force et ses récompenses."""
    boss_possibles = MODELES_BOSS[:difficulte.nb_boss]
    (nom, pv, attaque, recompense, effet), (nom_arme, bonus, effet_arme) = random.choice(
        boss_possibles
    )
    force = difficulte.force_ennemis
    gain = difficulte.recompense_boss
    return Salle(
        len(donjon) + 1,
        Ennemi(
            nom, ajuster(pv, force), ajuster(attaque, force), ajuster(recompense, gain),
            effet, CHANCE_EFFET_BOSS,
        ),
        Arme(nom_arme, ajuster(bonus, gain), effet_arme),
        random.random() < difficulte.chance_piege,
        boss=True,
    )


def pause(joueur, boutique=None):
    """Laisse le joueur utiliser des objets et acheter s'il y a une boutique, puis repartir."""
    if boutique is not None:
        print("\nUn marchand a installé son étal ici.")
    while True:
        print("\n1. Utiliser un objet\n2. Passer à la salle suivante")
        if boutique is not None:
            print("3. Aller à la boutique")
        choix_pause = input("Ton choix : ")
        match choix_pause:
            case "1":
                utiliser_un_objet(joueur)
            case "2":
                break
            case "3" if boutique is not None:
                visiter_boutique(joueur, boutique)
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
        print(f"\n{joueur.nom} s'enfuit vers la salle suivante !")
    elif resultat != "defaite":
        joueur.gagner_or(ennemi.recompense)
        print(
            f"\n{ennemi.nom} est vaincu ! {joueur.nom}"
            f" ramasse {ennemi.recompense} pièces d'or."
        )
        montee_de_niveau = joueur.gagner_xp(ennemi.recompense)
        if montee_de_niveau:
            print(
                f"\n{joueur.nom} passe au niveau {joueur.niveau} !"
                f" PV max {joueur.pv_max}, attaque {joueur.attaque}."
            )
            print(joueur)
    return resultat


def ramasser_butin(joueur, butin):
    """Ajoute le butin à l'inventaire du joueur."""
    joueur.ramasser_objet(butin)
    print(f"\n{joueur.nom} trouve : {butin}")


def traverser_salle(joueur, salle):
    """Fait traverser une salle au joueur. Renvoie True s'il en sort vivant."""
    debut_de_tour(joueur)  # entre deux salles, seul le poison continue d'agir
    if not joueur.est_vivant():
        return False
    if salle.piege and not declencher_piege(joueur):
        return False
    if salle.ennemi is not None:
        resultat = affronter_ennemi(joueur, salle.ennemi, salle.boss)
        if resultat == "defaite":
            return False
        if resultat == "fuite":
            pause(joueur, salle.boutique)
            return True
    else:
        print(f"La salle est vide... {joueur.nom} reprend son souffle.")
    if salle.butin is not None:
        ramasser_butin(joueur, salle.butin)
    pause(joueur, salle.boutique)
    return True


def effacer_ecran():
    """Efface le texte du terminal (rien à faire si la sortie n'est pas un vrai terminal)."""
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def explorer(joueur, donjon):
    """Fait traverser les salles au joueur. Renvoie True s'il sort vivant du donjon."""
    for salle in donjon:
        if salle.numero > 1:
            effacer_ecran()
        print(f"\n=== Salle {salle.numero}/{len(donjon)} ===")
        if not traverser_salle(joueur, salle):
            return False
    return True
