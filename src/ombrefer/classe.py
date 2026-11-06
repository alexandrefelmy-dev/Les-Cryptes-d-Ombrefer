"""Classes de héros : stats de départ et attaque spéciale propres à chacune."""

import random

from ombrefer.effet import AFFAIBLISSEMENT, RAGE, SAIGNEMENT
from ombrefer.objet import BATON, DAGUE, EPEE, FAUX, HACHE

# Multiplient le bonus d'une arme selon l'affinité de la classe avec sa famille.
GROS_BONUS = 1.5
MALUS = 0.5


class ClasseHeros:
    """Classe de base d'un héros : les classes filles changent ces réglages."""

    nom = ""
    nom_special = ""
    description = ""
    multiplicateur_pv = 1.0  # multiplie les PV de départ du mode
    bonus_attaque = 0  # s'ajoute à l'attaque de départ du mode
    chance_critique = 0.2
    chance_esquive = 0.1
    recharge = 4  # tours de combat à attendre entre deux attaques spéciales
    peut_se_defendre = True
    bonus_coffre = 0  # s'ajoute à la chance de forcer un coffre piégé
    affinites = {}  # pour chaque famille d'arme non neutre, GROS_BONUS ou MALUS

    def affinite(self, famille):
        """Renvoie le multiplicateur de bonus de cette famille d'arme pour la classe."""
        return self.affinites.get(famille, 1)

    def attaque_speciale(self, joueur, ennemi):
        """Applique l'attaque spéciale et renvoie la phrase à afficher."""
        raise NotImplementedError

    def resume(self):
        """Renvoie la présentation de la classe pour le menu de choix."""
        return f"{self.nom} : {self.description}"


class Guerrier(ClasseHeros):
    """Héros solide, dont le coup puissant ne fait jamais un petit jet."""

    nom = "Guerrier"
    nom_special = "Coup puissant"
    description = "robuste, son Coup puissant frappe très fort"
    multiplicateur_pv = 1.1
    recharge = 6
    affinites = {EPEE: GROS_BONUS, DAGUE: MALUS, BATON: MALUS}

    def attaque_speciale(self, joueur, ennemi):
        attaque = joueur.attaque_actuelle()
        degats = joueur.frapper(ennemi, random.randint((attaque + 1) // 2, attaque) * 2)
        return f"{joueur.nom} assène un {self.nom_special} : {degats} dégâts !"


class Voleur(ClasseHeros):
    """Héros fragile qui esquive, frappe en critique et fait saigner."""

    nom = "Voleur"
    nom_special = "Frappe sournoise"
    description = "fragile mais insaisissable, sa Frappe sournoise fait saigner"
    multiplicateur_pv = 0.85
    bonus_attaque = 1
    chance_critique = 0.3
    chance_esquive = 0.15
    recharge = 4
    bonus_coffre = 0.2
    affinites = {DAGUE: GROS_BONUS, BATON: MALUS, HACHE: MALUS}

    def attaque_speciale(self, joueur, ennemi):
        degats = joueur.frapper(ennemi, random.randint(1, joueur.attaque_actuelle()) * 2)
        ennemi.recevoir_effet(SAIGNEMENT)
        return f"{joueur.nom} porte une {self.nom_special} : {degats} dégâts et {SAIGNEMENT} !"


class Mage(ClasseHeros):
    """Héros très fragile, dont l'éclair ne dépend pas du hasard."""

    nom = "Mage"
    nom_special = "Éclair"
    description = "très fragile, son Éclair frappe sans hasard et affaiblit"
    multiplicateur_pv = 0.8
    bonus_attaque = 2
    recharge = 6
    affinites = {BATON: GROS_BONUS, EPEE: MALUS, HACHE: MALUS}
    force_eclair = 1.25  # multiplie l'attaque pour donner les dégâts de l'éclair

    def attaque_speciale(self, joueur, ennemi):
        degats = joueur.frapper(ennemi, round(joueur.attaque_actuelle() * self.force_eclair))
        ennemi.recevoir_effet(AFFAIBLISSEMENT)
        return f"{joueur.nom} lance un {self.nom_special} : {degats} dégâts et {AFFAIBLISSEMENT} !"


class Necromancien(ClasseHeros):
    """Héros qui reprend aux ennemis une partie de la vie qu'il leur vole."""

    nom = "Nécromancien"
    nom_special = "Drain de vie"
    description = "son Drain de vie le soigne en blessant l'ennemi"
    recharge = 3
    affinites = {FAUX: GROS_BONUS, EPEE: MALUS, HACHE: MALUS}
    part_soin = 1.0  # part des dégâts infligés qui revient en PV

    def attaque_speciale(self, joueur, ennemi):
        degats, _ = joueur.attaquer(ennemi)
        soin = joueur.soigner(round(degats * self.part_soin))
        return f"{joueur.nom} utilise {self.nom_special} : {degats} dégâts, +{soin} PV."


class Berserker(ClasseHeros):
    """Héros qui ne se défend jamais, et qui frappe plus fort en encaissant plus."""

    nom = "Berserker"
    nom_special = "Rage"
    description = "ne se défend jamais, sa Rage décuple ses coups mais l'expose"
    multiplicateur_pv = 1.15
    bonus_attaque = 2
    recharge = 5
    peut_se_defendre = False
    affinites = {HACHE: GROS_BONUS, BATON: MALUS, DAGUE: MALUS}

    def attaque_speciale(self, joueur, ennemi):
        joueur.recevoir_effet(RAGE)
        degats, _ = joueur.attaquer(ennemi)
        return f"{joueur.nom} entre en {self.nom_special} et frappe : {degats} dégâts !"


CLASSES = {
    "1": Guerrier(),
    "2": Voleur(),
    "3": Mage(),
    "4": Necromancien(),
    "5": Berserker(),
}


def classe_par_nom(nom):
    """Renvoie la classe qui porte ce nom, ou None."""
    for classe in CLASSES.values():
        if classe.nom == nom:
            return classe
    return None
