"""Tests de sauvegarde.py : écriture et chargement du héros en JSON."""

import json

import pytest

from outils import creer_joueur

from ombrefer.effet import POISON
from ombrefer.objet import Arme, Armure, Potion, Remede
from ombrefer.sauvegarde import charger, sauvegarder


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_sauvegarder_puis_charger():
    """Un héros sauvegardé revient à l'identique."""
    joueur = creer_joueur()
    joueur.pv = 12
    joueur.gagner_or(40)
    joueur.gagner_xp(25)
    joueur.ramasser_objet(Potion("Potion", 5))
    joueur.ramasser_objet(Arme("Epée", 3))
    joueur.ramasser_objet(Armure("Cotte", 2))
    joueur.ramasser_objet(Remede("Antidote", [POISON]))
    sauvegarder(joueur)
    charge = charger()
    assert charge.to_dict() == joueur.to_dict()
    assert isinstance(charge.inventaire[0], Potion)
    assert isinstance(charge.inventaire[1], Arme)
    assert isinstance(charge.inventaire[2], Armure)
    assert isinstance(charge.inventaire[3], Remede)


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_equipement_sauvegarde_sans_doubler_le_bonus():
    """L'équipement revient porté, sans ajouter son bonus une deuxième fois."""
    joueur = creer_joueur()
    Arme("Epée", 3).utiliser(joueur)
    Armure("Cotte", 2).utiliser(joueur)
    sauvegarder(joueur)
    charge = charger()
    assert (charge.attaque, charge.defense) == (11, 2)
    assert (charge.arme.nom, charge.armure.nom) == ("Epée", "Cotte")
    Arme("Dague", 1).utiliser(charge)
    assert charge.attaque == 9


def test_niveau_de_donjon_dans_le_fichier(fichier_sauvegarde):
    """Le fichier de sauvegarde contient le niveau de donjon du héros."""
    joueur = creer_joueur()
    joueur.niveau_donjon = 4
    sauvegarder(joueur)
    assert json.loads(fichier_sauvegarde.read_text(encoding="utf-8"))["niveau_donjon"] == 4
    assert charger().niveau_donjon == 4


def test_difficulte_dans_le_fichier(fichier_sauvegarde):
    """Le fichier de sauvegarde contient le mode du héros."""
    joueur = creer_joueur()
    joueur.difficulte = "Difficile"
    sauvegarder(joueur)
    assert json.loads(fichier_sauvegarde.read_text(encoding="utf-8"))["difficulte"] == "Difficile"
    assert charger().difficulte == "Difficile"


def test_charger_ancienne_sauvegarde_sans_difficulte(fichier_sauvegarde):
    """Une sauvegarde sans mode se charge sans erreur."""
    donnees = creer_joueur().to_dict()
    del donnees["difficulte"]
    fichier_sauvegarde.write_text(json.dumps(donnees), encoding="utf-8")
    assert charger().difficulte is None


def test_charger_ancienne_sauvegarde_sans_niveau_de_donjon(fichier_sauvegarde):
    """Une sauvegarde d'avant les niveaux repart du niveau 1."""
    donnees = creer_joueur().to_dict()
    del donnees["niveau_donjon"]
    fichier_sauvegarde.write_text(json.dumps(donnees), encoding="utf-8")
    assert charger().niveau_donjon == 1


def test_charger_ancienne_sauvegarde_sans_equipement(fichier_sauvegarde):
    """Une sauvegarde d'avant l'équipement se charge sans arme ni armure portée."""
    donnees = creer_joueur(defense=2).to_dict()
    del donnees["arme"]
    del donnees["armure"]
    fichier_sauvegarde.write_text(json.dumps(donnees), encoding="utf-8")
    charge = charger()
    assert charge.arme is None and charge.armure is None
    assert charge.defense == 2


def test_bonus_de_defense_jamais_sauvegarde():
    """Sauvegarder pendant le bonus n'écrit ni le compteur ni la défense renforcée."""
    joueur = creer_joueur(defense=2)
    joueur.tours_defense = 3
    donnees = joueur.to_dict()
    assert "tours_defense" not in donnees
    assert donnees["defense"] == 2


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_charger_sans_fichier():
    """Sans sauvegarde, charger renvoie None."""
    assert charger() is None


def test_charger_fichier_corrompu(fichier_sauvegarde):
    """Un fichier illisible (ou vide) renvoie None sans planter."""
    fichier_sauvegarde.write_text("", encoding="utf-8")
    assert charger() is None


def test_charger_ancienne_sauvegarde_sans_xp(fichier_sauvegarde):
    """Une sauvegarde d'avant l'XP se charge avec 0 XP."""
    donnees = creer_joueur().to_dict()
    del donnees["xp"]
    fichier_sauvegarde.write_text(json.dumps(donnees), encoding="utf-8")
    assert charger().xp == 0
