"""Tests de tools/simulateur.py : le bot joue sans saisie et ne laisse aucune trace."""

from unittest.mock import patch

import pytest
from simulateur import jouer_lot, resumer

from ombrefer import combat, donjon
from ombrefer.classe import Berserker
from ombrefer.effet import DUREES, RAGE
from ombrefer.main import NIVEAU_FINAL


def tache(profil="prudent", reglages=None, graine=1, mode="Facile", nb_parties=4):
    """Crée un petit lot de parties de Berserker."""
    return ("Berserker", mode, nb_parties, graine, profil, reglages or {})


@pytest.mark.parametrize("profil", ["prudent", "brut"])
@pytest.mark.parametrize("mode", ["Facile", "Enfer"])
def test_le_bot_joue_sans_rien_demander(profil, mode):
    """Une saisie ferait échouer le test : toutes les parties vont à leur terme."""
    with patch("builtins.input", side_effect=AssertionError("saisie demandée")):
        fins = jouer_lot(tache(profil, mode=mode))
    assert sum(fins) == 4


def test_le_lot_n_affiche_rien(capsys):
    """Le texte du jeu ne sort pas à l'écran."""
    jouer_lot(tache(nb_parties=1))
    assert capsys.readouterr().out == ""


def test_meme_graine_memes_parties():
    """La mesure est reproductible."""
    assert jouer_lot(tache(graine=7)) == jouer_lot(tache(graine=7))


def test_le_bot_est_retire_apres_le_lot():
    """Le jeu retrouve ses vraies fonctions."""
    action, pause = combat.jouer_action, donjon.pause
    jouer_lot(tache(nb_parties=1))
    assert combat.jouer_action is action
    assert donjon.pause is pause


def test_les_reglages_sont_retires_apres_le_lot():
    """Une variante ne laisse aucune trace, ni sur une classe, ni dans un dictionnaire."""
    recharge, duree = Berserker.recharge, DUREES[RAGE]
    reglages = {"classe.Berserker.recharge": 1, "effet.DUREES.Rage": 9}
    jouer_lot(tache(reglages=reglages, nb_parties=1))
    assert Berserker.recharge == recharge
    assert DUREES[RAGE] == duree


@pytest.mark.parametrize("chemin", ["classe.Berserker.absent", "effet.DUREES.Absent"])
def test_reglage_inconnu_refuse(chemin):
    """Une faute de frappe lève une erreur au lieu de mesurer le jeu sans changement."""
    with pytest.raises((AttributeError, KeyError)):
        jouer_lot(tache(reglages={chemin: 1}, nb_parties=1))


def test_resumer():
    """Le résumé compte les victoires, la moyenne et la survie par niveau."""
    fins = [0] * (NIVEAU_FINAL + 1)
    fins[0], fins[2], fins[NIVEAU_FINAL] = 1, 2, 1
    resume = resumer(fins)
    assert resume["victoire"] == 0.25
    assert resume["niveaux"] == 3.5
    assert resume["survie"][:3] == [0.75, 0.75, 0.25]
