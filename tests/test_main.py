"""Tests de main.py : menus, création du héros et lancement des parties."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from outils import chaque_mode, creer_joueur, NEUTRE, saisies

from ombrefer.classe import CLASSES, Mage
from ombrefer.donjon import adapter_au_niveau, Difficulte, DIFFICULTES
from ombrefer.main import (
    choisir_classe,
    choisir_difficulte,
    creer_heros,
    demander_nom,
    demander_oui_non,
    jeu,
    main,
    NIVEAU_FINAL,
    nouvelle_partie,
    partie_chargee,
)
from ombrefer.sauvegarde import (
    EMPLACEMENTS,
    charger,
    chemin,
    effacer_sauvegarde,
    emplacement_occupe,
    sauvegarder,
)
from ombrefer.succes import SUCCES, modes_reussis


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
    with saisies("1", "0", "1", "Aldric", "0", "4"):
        main()
    sortie = capsys.readouterr().out
    assert sortie.count("=== Les Cryptes d'Ombrefer ===") == 3
    assert "entre dans" not in sortie
    assert "À bientôt" in sortie


# --- Difficulté ---


@pytest.mark.parametrize("numero", DIFFICULTES)
def test_les_quatre_modes_sont_proposes(numero):
    """Chaque numéro du menu renvoie le bon mode."""
    with saisies(numero):
        assert choisir_difficulte() is DIFFICULTES[numero]


def test_difficulte_invalide_redemande():
    """Une difficulté invalide est redemandée."""
    with saisies("7", "1"):
        assert choisir_difficulte() is DIFFICULTES["1"]


def test_creer_heros_utilise_les_stats_du_mode():
    """Le héros combine les stats du mode et de sa classe, et commence sans défense."""
    difficulte = Difficulte("Test", 20, 6, 1, 1)
    joueur = creer_heros("Aldric", Mage(), difficulte)
    assert (joueur.nom, joueur.pv, joueur.pv_max) == ("Aldric", 16, 16)
    assert joueur.attaque == 8
    assert joueur.defense == 0
    assert joueur.classe.nom == "Mage"


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
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "1", "n"):
        jeu(joueur, NEUTRE)
    assert charger().niveau_donjon == 2


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_heros_charge_repart_de_son_niveau(capsys):
    """Un héros chargé reprend au niveau de donjon de sa sauvegarde."""
    joueur = creer_joueur()
    joueur.niveau_donjon = 5
    sauvegarder(joueur)
    joueur.difficulte = "Facile"
    joueur.prendre_classe(CLASSES["1"])
    sauvegarder(joueur)
    with patch("ombrefer.main.explorer", return_value=False), saisies("1"):
        partie_chargee()
    assert "niveau 5..." in capsys.readouterr().out


@chaque_mode
def test_de_6_a_9_salles_dans_tous_les_modes(difficulte, capsys):
    """Tous les modes tirent entre 6 et 9 salles, et toutes ces tailles sortent."""
    tailles = set()
    for _ in range(200):
        with patch("ombrefer.main.explorer", return_value=False):
            jeu(creer_heros("Aldric", CLASSES["1"], difficulte), difficulte)
        sortie = capsys.readouterr().out
        tailles.add(int(sortie.split("(")[1].split()[0]))
    assert tailles == {6, 7, 8, 9}


def test_nouvelle_partie_cree_le_heros_du_mode():
    """Une nouvelle partie utilise les stats du mode choisi."""
    with saisies("Aldric", "1", "3"), patch("ombrefer.main.jeu") as jeu_simule:
        nouvelle_partie()
    joueur, difficulte = jeu_simule.call_args.args
    assert difficulte is DIFFICULTES["3"]
    assert joueur.nom == "Aldric"
    assert joueur.classe is CLASSES["1"]
    assert joueur.pv_max == round(difficulte.pv_joueur * CLASSES["1"].multiplicateur_pv)


def test_retour_du_choix_de_classe_ne_lance_pas_de_partie():
    """Taper 0 au choix de la classe ramène au menu, sans demander la difficulté."""
    with saisies("Aldric", "0"), patch("ombrefer.main.jeu") as jeu_simule:
        nouvelle_partie()
    assert not jeu_simule.called


def test_classe_invalide_redemandee():
    """Un numéro de classe invalide est redemandé."""
    with saisies("9", "2"):
        assert choisir_classe() is CLASSES["2"]


def test_le_menu_presente_chaque_classe(capsys):
    """Le choix de la classe affiche le nom et la description de chacune."""
    with saisies("0"):
        choisir_classe()
    sortie = capsys.readouterr().out
    for classe in CLASSES.values():
        assert classe.resume() in sortie


def test_heros_charge_garde_ses_stats():
    """Un héros chargé ne prend pas les stats de départ du mode."""
    joueur = creer_joueur(pv=77, attaque=20)
    joueur.difficulte = "Difficile"
    joueur.prendre_classe(CLASSES["1"])
    sauvegarder(joueur)
    with saisies("1"), patch("ombrefer.main.jeu") as jeu_simule:
        partie_chargee()
    charge, difficulte = jeu_simule.call_args.args
    assert difficulte is DIFFICULTES["3"]
    assert (charge.pv_max, charge.attaque) == (77, 20)


def test_nouveau_heros_retient_son_mode():
    """Le héros garde le mode choisi à sa création."""
    assert creer_heros("Aldric", CLASSES["1"], DIFFICULTES["3"]).difficulte == "Difficile"


@pytest.mark.usefixtures("fichier_sauvegarde")
@pytest.mark.parametrize("numero", DIFFICULTES)
def test_le_mode_ne_change_pas_au_chargement(numero):
    """Recharger un héros reprend son mode : seule la question de l'emplacement est posée."""
    difficulte = DIFFICULTES[numero]
    sauvegarder(creer_heros("Aldric", CLASSES["1"], difficulte))
    with saisies("1"), patch("ombrefer.main.jeu") as jeu_simule:
        partie_chargee()
    assert jeu_simule.call_args.args[1] is difficulte


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_le_mode_survit_a_plusieurs_sauvegardes():
    """Le mode reste le même d'une sauvegarde à l'autre au fil des niveaux."""
    joueur = creer_heros("Aldric", CLASSES["1"], DIFFICULTES["3"])
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "1", "o", "o", "n"):
        jeu(joueur, DIFFICULTES["3"])
    charge = charger()
    assert charge.difficulte == "Difficile"
    assert charge.niveau_donjon == 3


def test_chargement_sans_sauvegarde():
    """Sans sauvegarde, la difficulté n'est même pas demandée."""
    with patch("ombrefer.main.charger", return_value=None):
        with patch("ombrefer.main.jeu") as jeu_simule:
            partie_chargee()
    assert not jeu_simule.called


def test_lancement_avec_python_m(tmp_path):
    """python -m ombrefer ouvre le vrai menu, et le choix 4 quitte le jeu."""
    environnement = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
        "PYTHONIOENCODING": "utf-8",
    }
    resultat = subprocess.run(
        [sys.executable, "-m", "ombrefer"],
        input="4\n",
        capture_output=True,
        encoding="utf-8",
        cwd=tmp_path,
        env=environnement,
        check=True,
    )
    assert "=== Les Cryptes d'Ombrefer ===" in resultat.stdout
    assert "À bientôt" in resultat.stdout


# --- Fin du jeu ---


def heros_final(mode="Facile", niveau=NIVEAU_FINAL):
    """Crée un héros de ce mode, prêt à jouer ce niveau de donjon."""
    difficulte = next(d for d in DIFFICULTES.values() if d.nom == mode)
    joueur = creer_heros("Aldric", CLASSES["1"], difficulte)
    joueur.niveau_donjon = niveau
    return joueur, difficulte


def test_le_dernier_niveau_est_le_niveau_10():
    """Le jeu se termine au niveau 10."""
    assert NIVEAU_FINAL == 10


def test_le_dernier_niveau_est_annonce(capsys):
    """Le joueur sait qu'il entre dans le dernier niveau, et pas avant."""
    joueur, difficulte = heros_final(niveau=NIVEAU_FINAL - 1)
    with patch("ombrefer.main.explorer", side_effect=[True, False]):
        with saisies("n", "o"):
            jeu(joueur, difficulte)
    sortie = capsys.readouterr().out
    assert sortie.count("c'est le dernier niveau") == 1
    assert sortie.index("c'est le dernier niveau") > sortie.index(f"niveau {NIVEAU_FINAL}...")


@pytest.mark.parametrize("mode", SUCCES)
def test_finir_le_jeu_donne_le_succes_du_mode(mode, capsys):
    """Vaincre le dernier niveau raconte la fin de ce mode et donne son succès, sans les autres."""
    joueur, difficulte = heros_final(mode)
    with patch("ombrefer.main.explorer", return_value=True):
        jeu(joueur, difficulte)  # aucune saisie : ni sauvegarde, ni descente proposée
    sortie = capsys.readouterr().out
    nom, recit = SUCCES[mode]
    assert f"Succès obtenu : {nom} !" in sortie
    assert recit in sortie
    assert modes_reussis() == [mode]


def test_les_succes_des_modes_sont_tous_differents():
    """Chaque mode a son propre nom de succès et son propre récit."""
    assert len(SUCCES) == len(DIFFICULTES)
    assert {difficulte.nom for difficulte in DIFFICULTES.values()} == set(SUCCES)
    assert len({nom for nom, _ in SUCCES.values()}) == len(SUCCES)
    assert len({recit for _, recit in SUCCES.values()}) == len(SUCCES)


def test_le_jeu_s_arrete_apres_le_dernier_niveau():
    """Aucun niveau 11 n'est lancé après la victoire."""
    joueur, difficulte = heros_final()
    with patch("ombrefer.main.explorer", return_value=True) as explorer:
        jeu(joueur, difficulte)
    assert explorer.call_count == 1


def test_mourir_au_dernier_niveau_ne_donne_pas_de_succes():
    """Seule la victoire compte."""
    joueur, difficulte = heros_final()
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(joueur, difficulte)
    assert modes_reussis() == []


def test_finir_avant_le_dernier_niveau_ne_donne_pas_de_succes():
    """L'avant-dernier niveau se termine comme les autres."""
    joueur, difficulte = heros_final(niveau=NIVEAU_FINAL - 1)
    with patch("ombrefer.main.explorer", return_value=True):
        with saisies("n", "n"):
            jeu(joueur, difficulte)
    assert joueur.niveau_donjon == NIVEAU_FINAL
    assert modes_reussis() == []


def test_refaire_le_jeu_ne_redonne_pas_le_succes(capsys):
    """Un succès déjà acquis est signalé, sans être compté deux fois."""
    for _ in range(2):
        joueur, difficulte = heros_final()
        with patch("ombrefer.main.explorer", return_value=True):
            jeu(joueur, difficulte)
    sortie = capsys.readouterr().out
    assert sortie.count("Succès obtenu") == 1
    assert "Tu possèdes déjà le succès" in sortie
    assert modes_reussis() == ["Facile"]


def test_heros_d_une_ancienne_partie_trop_bas():
    """Un héros sauvegardé plus bas que le dernier niveau finit le jeu à sa prochaine victoire."""
    joueur, difficulte = heros_final(niveau=NIVEAU_FINAL + 3)
    with patch("ombrefer.main.explorer", return_value=True) as explorer:
        jeu(joueur, difficulte)
    assert explorer.call_count == 1
    assert modes_reussis() == ["Facile"]


def test_menu_principal_montre_les_succes(capsys):
    """Le choix 3 affiche les succès et revient au menu, le choix 4 quitte."""
    with saisies("3", "4"):
        main()
    sortie = capsys.readouterr().out
    assert "=== Succès ===" in sortie
    assert sortie.count("=== Les Cryptes d'Ombrefer ===") == 2
    assert "À bientôt" in sortie


# --- Mode Enfer ---


def heros_enfer(niveau=1):
    """Crée un héros du mode Enfer, à ce niveau de donjon."""
    return heros_final("Enfer", niveau)


def test_l_enfer_est_le_mode_le_plus_dur():
    """L'Enfer arrive en dernier : ses ennemis sont les plus forts, même sans la mort définitive."""
    modes = list(DIFFICULTES.values())
    assert modes[-1].nom == "Enfer"
    assert modes[-1].force_ennemis == max(mode.force_ennemis for mode in modes)
    assert modes[-1].force_par_niveau == max(mode.force_par_niveau for mode in modes)
    assert modes[-1].pv_joueur == min(mode.pv_joueur for mode in modes)


def test_seul_l_enfer_efface_le_heros():
    """Les trois autres modes gardent leur sauvegarde."""
    assert [mode.nom for mode in DIFFICULTES.values() if mode.mort_definitive] == ["Enfer"]


def test_le_menu_previent_du_danger_de_l_enfer(capsys):
    """Le joueur sait ce qui l'attend avant de choisir."""
    with saisies("0"):
        choisir_difficulte()
    assert "4. Enfer (la mort efface le héros)" in capsys.readouterr().out


def test_mourir_en_enfer_efface_la_sauvegarde(fichier_sauvegarde, capsys):
    """Après la mort, le héros ne peut plus être chargé."""
    joueur, difficulte = heros_enfer()
    sauvegarder(joueur)
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(joueur, difficulte)
    assert not fichier_sauvegarde.exists()
    sortie = capsys.readouterr().out
    assert "effacé pour toujours" in sortie
    assert "Record en mode Enfer : niveau 1 (Aldric, Guerrier)" in sortie
    partie_chargee()
    assert "Aucune sauvegarde trouvée." in capsys.readouterr().out


def test_mourir_apres_un_chargement_efface_la_sauvegarde(fichier_sauvegarde):
    """Un héros chargé puis mort ne revient pas non plus."""
    joueur, difficulte = heros_enfer(niveau=4)
    sauvegarder(joueur)
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(charger(), difficulte)
    assert not fichier_sauvegarde.exists()


def test_sauvegarder_puis_mourir_au_niveau_suivant(fichier_sauvegarde):
    """La sauvegarde faite pendant la partie disparaît aussi à la mort."""
    joueur, difficulte = heros_enfer()
    with patch("ombrefer.main.explorer", side_effect=[True, False]):
        with saisies("o", "1", "o"):
            jeu(joueur, difficulte)
    assert not fichier_sauvegarde.exists()


def test_quitter_en_plein_niveau_ne_sauve_pas_le_heros(fichier_sauvegarde):
    """Fermer le jeu pendant un niveau revient à mourir : la sauvegarde est déjà consommée."""
    joueur, difficulte = heros_enfer()
    sauvegarder(joueur)
    with patch("ombrefer.main.explorer", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            jeu(joueur, difficulte)
    assert not fichier_sauvegarde.exists()


def test_la_sauvegarde_d_un_autre_heros_est_protegee(fichier_sauvegarde):
    """Un héros d'Enfer jamais sauvegardé ne touche pas au fichier d'un autre héros."""
    autre, _ = heros_final("Facile", niveau=6)
    sauvegarder(autre)
    joueur, difficulte = heros_enfer()
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(joueur, difficulte)
    assert fichier_sauvegarde.exists()
    assert charger().difficulte == "Facile"


def test_refuser_de_descendre_garde_le_heros_d_enfer(fichier_sauvegarde):
    """Sauvegarder puis s'arrêter entre deux niveaux reste permis : le héros n'a pas péri."""
    joueur, difficulte = heros_enfer()
    with patch("ombrefer.main.explorer", return_value=True):
        with saisies("o", "1", "n"):
            jeu(joueur, difficulte)
    assert fichier_sauvegarde.exists()
    assert charger().niveau_donjon == 2


@pytest.mark.parametrize("mode", ["Facile", "Intermédiaire", "Difficile"])
def test_les_autres_modes_gardent_leur_sauvegarde(mode, fichier_sauvegarde):
    """Hors Enfer, la mort renvoie toujours à la dernière sauvegarde."""
    joueur, difficulte = heros_final(mode, niveau=2)
    sauvegarder(joueur)
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(joueur, difficulte)
    assert fichier_sauvegarde.exists()


def test_le_record_suit_les_niveaux_atteints(capsys):
    """Entrer dans un niveau suffit pour le compter, même si le héros y meurt."""
    joueur, difficulte = heros_enfer()
    with patch("ombrefer.main.explorer", side_effect=[True, True, False]):
        with saisies("n", "o", "n", "o"):
            jeu(joueur, difficulte)
    assert "Record en mode Enfer : niveau 3" in capsys.readouterr().out


def test_les_autres_modes_ne_touchent_pas_au_record(capsys):
    """Seul l'Enfer compte pour le record."""
    joueur, difficulte = heros_final("Difficile", niveau=8)
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(joueur, difficulte)
    main_sortie = capsys.readouterr().out
    assert "Record" not in main_sortie
    with saisies("3", "4"):
        main()
    assert "Record en mode Enfer : aucun" in capsys.readouterr().out


def test_finir_l_enfer_donne_le_succes_ultime(capsys):
    """Le dernier boss vaincu en Enfer donne le succès ultime, sans le succès Difficile."""
    joueur, difficulte = heros_enfer(niveau=NIVEAU_FINAL)
    with patch("ombrefer.main.explorer", return_value=True):
        jeu(joueur, difficulte)
    sortie = capsys.readouterr().out
    assert f"Succès obtenu : {SUCCES['Enfer'][0]} !" in sortie
    assert "C'est le succès ultime" in sortie
    assert modes_reussis() == ["Enfer"]


def test_finir_difficile_ne_donne_pas_le_succes_ultime(capsys):
    """Le mode Difficile garde son propre succès."""
    joueur, difficulte = heros_final("Difficile")
    with patch("ombrefer.main.explorer", return_value=True):
        jeu(joueur, difficulte)
    assert "succès ultime" not in capsys.readouterr().out
    assert modes_reussis() == ["Difficile"]


def test_effacer_sans_fichier_ne_plante_pas(fichier_sauvegarde):
    """Effacer une sauvegarde absente ne fait rien."""
    effacer_sauvegarde()
    assert not fichier_sauvegarde.exists()


# --- Emplacements de sauvegarde ---


def heros_sauvegarde(nom, emplacement, mode="Facile"):
    """Sauvegarde un nouveau héros de ce mode dans cet emplacement et le renvoie."""
    difficulte = next(d for d in DIFFICULTES.values() if d.nom == mode)
    joueur = creer_heros(nom, CLASSES["1"], difficulte)
    sauvegarder(joueur, emplacement)
    return joueur


def test_il_y_a_trois_emplacements():
    """Le jeu propose trois emplacements."""
    assert EMPLACEMENTS == (1, 2, 3)


def test_chaque_nouveau_heros_choisit_son_emplacement(capsys):
    """La liste montre les héros déjà là, et le nouveau va où le joueur le demande."""
    heros_sauvegarde("Brune", 1)
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "2", "n"):
        jeu(joueur, NEUTRE)
    sortie = capsys.readouterr().out
    assert "1. Brune, Guerrier, mode Facile, niveau 1 du donjon" in sortie
    assert "2. vide" in sortie
    assert "emplacement 2" in sortie
    assert charger(1).nom == "Brune"
    assert charger(2).nom == "Aldric"


def test_le_heros_garde_son_emplacement():
    """Après le premier choix, plus aucune question sur l'emplacement."""
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", return_value=True):
        with saisies("o", "3", "o", "o", "n"):
            jeu(joueur, NEUTRE)
    assert charger(3).niveau_donjon == 3
    assert charger(1) is None


def test_un_heros_charge_reste_dans_son_emplacement():
    """Sauvegarder un héros chargé ne demande rien et ne touche pas aux autres."""
    heros_sauvegarde("Brune", 1)
    heros_sauvegarde("Cassis", 2)
    with patch("ombrefer.main.explorer", return_value=True), saisies("2", "o", "n"):
        partie_chargee()
    assert charger(2).niveau_donjon == 2
    assert charger(1).niveau_donjon == 1


def test_remplacer_un_emplacement_demande_confirmation():
    """Refuser ramène à la liste, accepter remplace le héros."""
    heros_sauvegarde("Brune", 1)
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", return_value=True):
        with saisies("o", "1", "n", "1", "o", "n"):
            jeu(joueur, NEUTRE)
    assert charger(1).nom == "Aldric"


def test_annuler_la_sauvegarde(capsys):
    """Le choix 0 ne sauvegarde rien et ne touche à aucun héros."""
    heros_sauvegarde("Brune", 1)
    joueur = creer_joueur()
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "0", "n"):
        jeu(joueur, NEUTRE)
    assert "Sauvegarde annulée." in capsys.readouterr().out
    assert joueur.emplacement is None
    assert charger(1).nom == "Brune"


def test_charger_le_heros_choisi(capsys):
    """Le joueur reprend le héros de l'emplacement demandé."""
    heros_sauvegarde("Brune", 1)
    heros_sauvegarde("Cassis", 3)
    with saisies("3"), patch("ombrefer.main.jeu") as jeu_simule:
        partie_chargee()
    assert jeu_simule.call_args.args[0].nom == "Cassis"
    assert "2. vide" in capsys.readouterr().out


def test_retour_du_chargement():
    """Le choix 0 ne lance aucune partie."""
    heros_sauvegarde("Brune", 1)
    with saisies("0"), patch("ombrefer.main.jeu") as jeu_simule:
        partie_chargee()
    assert not jeu_simule.called


def test_charger_un_emplacement_vide(capsys):
    """Un emplacement vide ne lance aucune partie."""
    heros_sauvegarde("Brune", 1)
    with saisies("2"), patch("ombrefer.main.jeu") as jeu_simule:
        partie_chargee()
    assert not jeu_simule.called
    assert "Impossible de charger cet emplacement." in capsys.readouterr().out


def test_un_fichier_illisible_n_empeche_pas_de_charger_les_autres(capsys):
    """La liste signale le fichier abîmé, et les autres héros restent chargeables."""
    heros_sauvegarde("Brune", 1)
    heros_sauvegarde("Cassis", 2)
    chemin(1).write_bytes(b"abime")
    with saisies("2"), patch("ombrefer.main.jeu") as jeu_simule:
        partie_chargee()
    assert "1. fichier illisible" in capsys.readouterr().out
    assert jeu_simule.call_args.args[0].nom == "Cassis"


def test_mort_en_enfer_n_efface_que_son_emplacement():
    """Le héros d'Enfer disparaît, ceux des autres emplacements restent."""
    heros_sauvegarde("Brune", 1)
    joueur = heros_sauvegarde("Cassis", 2, "Enfer")
    with patch("ombrefer.main.explorer", return_value=False):
        jeu(joueur, DIFFICULTES["4"])
    assert not emplacement_occupe(2)
    assert charger(1).nom == "Brune"


def test_heros_d_enfer_charge_depuis_un_autre_emplacement():
    """La mort d'un héros d'Enfer chargé efface bien l'emplacement d'où il vient."""
    heros_sauvegarde("Brune", 1)
    heros_sauvegarde("Cassis", 3, "Enfer")
    with patch("ombrefer.main.explorer", return_value=False), saisies("3"):
        partie_chargee()
    assert not emplacement_occupe(3)
    assert emplacement_occupe(1)


def test_l_enfer_ressauvegarde_dans_son_emplacement():
    """Après une victoire, le héros d'Enfer revient dans l'emplacement qu'il a consommé."""
    joueur = heros_sauvegarde("Cassis", 2, "Enfer")
    with patch("ombrefer.main.explorer", return_value=True), saisies("o", "n"):
        jeu(joueur, DIFFICULTES["4"])
    assert charger(2).niveau_donjon == 2


def test_l_ancien_fichier_passe_dans_l_emplacement_1(fichier_sauvegarde):
    """Une sauvegarde des anciennes versions est retrouvée dans l'emplacement 1."""
    heros_sauvegarde("Brune", 1)
    ancien = fichier_sauvegarde.with_name("sauvegarde.sav")
    fichier_sauvegarde.rename(ancien)
    with saisies("4"):
        main()
    assert not ancien.exists()
    assert charger(1).nom == "Brune"


def test_l_ancien_fichier_n_ecrase_pas_l_emplacement_1(fichier_sauvegarde):
    """Si l'emplacement 1 est pris, l'ancien fichier reste où il est."""
    heros_sauvegarde("Brune", 1)
    ancien = fichier_sauvegarde.with_name("sauvegarde.sav")
    ancien.write_bytes(fichier_sauvegarde.read_bytes())
    heros_sauvegarde("Cassis", 1)
    with saisies("4"):
        main()
    assert ancien.exists()
    assert charger(1).nom == "Cassis"
