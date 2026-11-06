"""Outils communs aux tests : le hasard et le clavier y sont remplacés par des valeurs fixes."""

import contextlib
from unittest.mock import patch

import pytest

from ombrefer.donjon import DIFFICULTES, Difficulte, generer_donjon
from ombrefer.objet import Potion
from ombrefer.personnage import Joueur

# Difficulté neutre : les modèles sont utilisés sans aucun changement.
NEUTRE = Difficulte("Test", 30, 8, 1, 1)

# Les modes de plus en plus durs : l'Enfer n'en fait pas partie, il reprend le mode Difficile.
MODES_DE_BASE = [mode for mode in DIFFICULTES.values() if not mode.mort_definitive]

# Lance un test une fois par mode de difficulté.
chaque_mode = pytest.mark.parametrize(
    "difficulte", DIFFICULTES.values(), ids=lambda difficulte: difficulte.nom
)


@contextlib.contextmanager
def hasard(valeur=0.5):
    """Fixe le hasard : random() renvoie valeur et randint() renvoie toujours le maximum.

    0.5 : ni critique, ni esquive, et la fuite rate.
    0.3 : ni critique, ni esquive, et la fuite réussit.
    """
    with patch("random.random", return_value=valeur):
        with patch("random.randint", side_effect=lambda minimum, maximum: maximum):
            yield


def saisies(*reponses):
    """Remplace le clavier : chaque input() renvoie la réponse suivante."""
    return patch("builtins.input", side_effect=list(reponses))


def creer_joueur(pv=30, attaque=8, defense=0):
    """Crée un joueur de test, sans armure par défaut."""
    joueur = Joueur("Aldric", pv, attaque)
    joueur.defense = defense
    return joueur


def joueur_avec_potion():
    """Crée un joueur blessé (10/30 PV) qui possède une potion de 5 PV."""
    joueur = creer_joueur()
    joueur.pv = 10
    joueur.ramasser_objet(Potion("Potion", 5))
    return joueur


def donjon_sans_danger(nb_salles):
    """Crée un donjon sans ennemi, ni piège, ni boutique, ni événement."""
    donjon = generer_donjon(nb_salles, NEUTRE)
    for salle in donjon:
        salle.ennemi = None
        salle.piege = False
        salle.boutique = None
        salle.evenement = None
    return donjon
