"""Tests de sauvegarde.py : écriture et chargement du héros en JSON."""

import json

import pytest

from outils import creer_joueur

from ombrefer.objet import Arme, Potion
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
    sauvegarder(joueur)
    charge = charger()
    assert charge.to_dict() == joueur.to_dict()
    assert isinstance(charge.inventaire[0], Potion)
    assert isinstance(charge.inventaire[1], Arme)


def test_bonus_de_defense_jamais_sauvegarde():
    """Sauvegarder pendant le bonus n'écrit ni le compteur ni la défense doublée."""
    joueur = creer_joueur()
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
