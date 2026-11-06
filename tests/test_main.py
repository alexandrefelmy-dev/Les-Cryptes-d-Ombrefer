"""Tests de main.py : menus, création du héros et lancement des parties."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from outils import chaque_mode, creer_joueur, NEUTRE, saisies

from ombrefer.donjon import Difficulte, DIFFICULTES, FORCE_PAR_NIVEAU
from ombrefer.main import (
    choisir_difficulte,
    creer_heros,
    demander_nom,
    jeu,
    main,
    nouvelle_partie,
    partie_chargee,
)


# --- Option 0 (retour) ---


def test_retour_de_la_difficulte():
    """Taper 0 ne crée pas de donjon."""
    with saisies("0"):
        assert choisir_difficulte() is None


def test_retour_de_la_difficulte_ne_lance_pas_de_partie(capsys):
    """Après un retour, aucune partie ne démarre."""
    with saisies("Aldric", "0"):
        nouvelle_partie()
    assert "entre dans" not in capsys.readouterr().out


def test_retour_du_nom():
    """Taper 0 annule la saisie du nom."""
    with saisies("0"):
        assert demander_nom() is None


def test_nom_vide_redemande():
    """Un nom vide est redemandé."""
    with saisies("   ", "Aldric"):
        assert demander_nom() == "Aldric"


def test_un_nom_commencant_par_zero_reste_valide():
    """Seul le 0 exact sert de retour."""
    with saisies("007"):
        assert demander_nom() == "007"


def test_retours_depuis_le_menu_principal(capsys):
    """Le joueur revient du nom, puis de la difficulté, puis quitte."""
    with saisies("1", "0", "1", "Aldric", "0", "3"):
        main()
    sortie = capsys.readouterr().out
    assert sortie.count("=== Les Cryptes d'Ombrefer ===") == 3
    assert "entre dans" not in sortie
    assert "À bientôt" in sortie


# --- Difficulté ---


@pytest.mark.parametrize("numero", DIFFICULTES)
def test_les_trois_modes_sont_proposes(numero):
    """Chaque numéro du menu renvoie le bon mode."""
    with saisies(numero):
        assert choisir_difficulte() is DIFFICULTES[numero]


def test_difficulte_invalide_redemande():
    """Une difficulté invalide est redemandée."""
    with saisies("7", "1"):
        assert choisir_difficulte() is DIFFICULTES["1"]


def test_creer_heros_utilise_les_stats_du_mode():
    """Le héros reçoit les PV et l'attaque du mode, et commence sans défense."""
    difficulte = Difficulte("Test", 21, 6, 1, 1)
    joueur = creer_heros("Aldric", difficulte)
    assert (joueur.nom, joueur.pv, joueur.pv_max) == ("Aldric", 21, 21)
    assert joueur.attaque == 6
    assert joueur.defense == 0


def test_le_donjon_suit_le_niveau_du_heros():
    """jeu crée un donjon adapté au niveau du héros."""
    joueur = creer_joueur()
    joueur.niveau = 4
    with patch("ombrefer.main.explorer", return_value=False):
        with patch("ombrefer.main.generer_donjon", return_value=[]) as generer:
            jeu(joueur, NEUTRE)
    assert generer.call_args.args[1].force_ennemis == 1 + 3 * FORCE_PAR_NIVEAU


@chaque_mode
def test_de_6_a_9_salles_dans_tous_les_modes(difficulte, capsys):
    """Tous les modes tirent entre 6 et 9 salles, et toutes ces tailles sortent."""
    tailles = set()
    for _ in range(200):
        with patch("ombrefer.main.explorer", return_value=False):
            jeu(creer_joueur(), difficulte)
        sortie = capsys.readouterr().out
        tailles.add(int(sortie.split("(")[1].split()[0]))
    assert tailles == {6, 7, 8, 9}


def test_nouvelle_partie_cree_le_heros_du_mode():
    """Une nouvelle partie utilise les stats du mode choisi."""
    with saisies("Aldric", "3"), patch("ombrefer.main.jeu") as jeu_simule:
        nouvelle_partie()
    joueur, difficulte = jeu_simule.call_args.args
    assert difficulte is DIFFICULTES["3"]
    assert joueur.nom == "Aldric"
    assert joueur.pv_max == difficulte.pv_joueur


def test_heros_charge_garde_ses_stats():
    """Un héros chargé ne prend pas les stats de départ du mode."""
    joueur = creer_joueur(pv=77, attaque=20)
    with patch("ombrefer.main.charger", return_value=joueur), saisies("3"):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert jeu_simule.call_args.args == (joueur, DIFFICULTES["3"])
    assert (joueur.pv_max, joueur.attaque) == (77, 20)


def test_retour_apres_chargement():
    """Revenir de la difficulté après un chargement ne lance pas de partie."""
    with patch("ombrefer.main.charger", return_value=creer_joueur()), saisies("0"):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert not jeu_simule.called


def test_chargement_sans_sauvegarde():
    """Sans sauvegarde, la difficulté n'est même pas demandée."""
    with patch("ombrefer.main.charger", return_value=None):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert not jeu_simule.called


def test_lancement_avec_python_m(tmp_path):
    """python -m ombrefer ouvre le vrai menu, et le choix 3 quitte le jeu."""
    environnement = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
        "PYTHONIOENCODING": "utf-8",
    }
    resultat = subprocess.run(
        [sys.executable, "-m", "ombrefer"],
        input="3\n",
        capture_output=True,
        encoding="utf-8",
        cwd=tmp_path,
        env=environnement,
        check=True,
    )
    assert "=== Les Cryptes d'Ombrefer ===" in resultat.stdout
    assert "À bientôt" in resultat.stdout
