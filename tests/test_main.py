"""Tests de main.py : menus, création du héros et lancement des parties."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from outils import chaque_mode, creer_joueur, NEUTRE, saisies

from ombrefer.donjon import adapter_au_niveau, Difficulte, DIFFICULTES
from ombrefer.main import (
    choisir_difficulte,
    creer_heros,
    demander_nom,
    demander_oui_non,
    difficulte_du_heros,
    jeu,
    main,
    nouvelle_partie,
    partie_chargee,
)
from ombrefer.sauvegarde import charger, sauvegarder


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


def test_le_donjon_suit_le_niveau_de_donjon_du_heros():
    """jeu crée un donjon adapté au niveau de donjon, pas au niveau du héros."""
    joueur = creer_joueur()
    joueur.niveau = 9
    joueur.niveau_donjon = 4
    with patch("ombrefer.main.explorer", return_value=False):
        with patch("ombrefer.main.generer_donjon", return_value=[]) as generer:
            jeu(joueur, NEUTRE)
    assert generer.call_args.args[1] == adapter_au_niveau(NEUTRE, 4)


def test_les_niveaux_s_enchainent_jusqu_a_la_mort(capsys):
    """Le héros descend d'un niveau après chaque victoire."""
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", side_effect=[True, True, False]):
        with saisies("n", "o", "n", "o"):
            jeu(joueur, NEUTRE)
    sortie = capsys.readouterr().out
    assert "niveau 1..." in sortie and "niveau 2..." in sortie and "niveau 3..." in sortie
    assert "a péri au niveau 3" in sortie
    assert joueur.niveau_donjon == 3


def test_s_arreter_apres_un_niveau():
    """Le joueur peut refuser de descendre : la partie s'arrête là."""
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", return_value=True) as explorer:
        with saisies("n", "n"):
            jeu(joueur, NEUTRE)
    assert explorer.call_count == 1
    assert joueur.niveau_donjon == 2


def test_reponse_invalide_redemandee():
    """Une réponse autre que o ou n est redemandée."""
    with saisies("peut-être", "O"):
        assert demander_oui_non("Alors ? ") is True


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_sauvegarder_garde_le_niveau_suivant():
    """Après le niveau 1, la sauvegarde indique le niveau 2, où le héros repart."""
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "n"):
        jeu(joueur, NEUTRE)
    assert charger().niveau_donjon == 2


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_heros_charge_repart_de_son_niveau(capsys):
    """Un héros chargé reprend au niveau de donjon de sa sauvegarde."""
    joueur = creer_joueur()
    joueur.niveau_donjon = 5
    sauvegarder(joueur)
    joueur.difficulte = "Facile"
    sauvegarder(joueur)
    with patch("ombrefer.main.explorer", return_value=False):
        partie_chargee()
    assert "niveau 5..." in capsys.readouterr().out


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
    joueur.difficulte = "Difficile"
    with patch("ombrefer.main.charger", return_value=joueur):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert jeu_simule.call_args.args == (joueur, DIFFICULTES["3"])
    assert (joueur.pv_max, joueur.attaque) == (77, 20)


def test_nouveau_heros_retient_son_mode():
    """Le héros garde le mode choisi à sa création."""
    assert creer_heros("Aldric", DIFFICULTES["3"]).difficulte == "Difficile"


@pytest.mark.usefixtures("fichier_sauvegarde")
@pytest.mark.parametrize("numero", DIFFICULTES)
def test_le_mode_ne_change_pas_au_chargement(numero):
    """Recharger un héros reprend son mode sans jamais le demander."""
    difficulte = DIFFICULTES[numero]
    sauvegarder(creer_heros("Aldric", difficulte))
    with patch("builtins.input", side_effect=AssertionError("question interdite")):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert jeu_simule.call_args.args[1] is difficulte


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_le_mode_survit_a_plusieurs_sauvegardes():
    """Le mode reste le même d'une sauvegarde à l'autre au fil des niveaux."""
    joueur = creer_heros("Aldric", DIFFICULTES["3"])
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "o", "o", "n"):
        jeu(joueur, DIFFICULTES["3"])
    charge = charger()
    assert charge.difficulte == "Difficile"
    assert charge.niveau_donjon == 3


def test_ancienne_sauvegarde_choisit_son_mode_une_fois():
    """Sans mode dans la sauvegarde, il est demandé puis retenu pour la suite."""
    joueur = creer_joueur()
    with patch("ombrefer.main.charger", return_value=joueur), saisies("2"):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert jeu_simule.call_args.args == (joueur, DIFFICULTES["2"])
    assert joueur.difficulte == "Intermédiaire"
    assert difficulte_du_heros(joueur) is DIFFICULTES["2"]


def test_mode_inconnu_demande_un_nouveau_choix():
    """Un nom de mode inconnu dans la sauvegarde ne bloque pas le héros."""
    joueur = creer_joueur()
    joueur.difficulte = "Cauchemar"
    with saisies("1"):
        assert difficulte_du_heros(joueur) is DIFFICULTES["1"]


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
