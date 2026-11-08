"""Tests de succes.py : déblocage, conservation et affichage des succès."""

from outils import creer_joueur

from ombrefer.sauvegarde import encoder, sauvegarder
from ombrefer.classe import CLASSES
from ombrefer.succes import (
    MODE_ULTIME,
    SUCCES,
    afficher_succes,
    debloquer,
    modes_reussis,
    noter_record_enfer,
    texte_record,
)


def test_aucun_succes_au_depart():
    """Sans fichier, aucun mode n'est terminé."""
    assert modes_reussis() == []


def test_debloquer_garde_le_succes():
    """Un succès débloqué est retrouvé ensuite."""
    assert debloquer("Facile") is True
    assert modes_reussis() == ["Facile"]


def test_debloquer_deux_fois_ne_compte_qu_une_fois():
    """Le second déblocage du même mode ne change rien."""
    debloquer("Facile")
    assert debloquer("Facile") is False
    assert modes_reussis() == ["Facile"]


def test_les_succes_s_ajoutent():
    """Terminer un autre mode garde les succès précédents."""
    debloquer("Facile")
    debloquer("Difficile")
    assert modes_reussis() == ["Facile", "Difficile"]


def test_les_succes_survivent_a_une_autre_sauvegarde(fichier_sauvegarde):
    """Sauvegarder un nouveau héros ne touche pas aux succès."""
    debloquer("Facile")
    joueur = creer_joueur()
    sauvegarder(joueur)
    assert fichier_sauvegarde.exists()
    assert modes_reussis() == ["Facile"]


def test_fichier_modifie_refuse(fichier_succes, capsys):
    """Un fichier modifié à la main ne donne aucun succès."""
    debloquer("Facile")
    octets = bytearray(fichier_succes.read_bytes())
    octets[-1] ^= 1
    fichier_succes.write_bytes(bytes(octets))
    assert modes_reussis() == []
    assert "corrompu ou modifié" in capsys.readouterr().out


def test_fichier_en_clair_refuse(fichier_succes):
    """Écrire soi-même la liste des succès ne marche pas."""
    fichier_succes.write_text('{"modes": ["Difficile"]}', encoding="utf-8")
    assert modes_reussis() == []


def test_fichier_sans_la_bonne_cle_refuse(fichier_succes):
    """Un fichier signé qui n'est pas celui des succès n'en donne aucun."""
    fichier_succes.write_bytes(encoder({"nom": "Aldric"}))
    assert modes_reussis() == []


def test_afficher_les_succes(capsys):
    """Les trois succès sont listés, seuls ceux obtenus sont cochés."""
    debloquer("Intermédiaire")
    afficher_succes()
    sortie = capsys.readouterr().out
    for mode, (nom, _) in SUCCES.items():
        marque = "x" if mode == "Intermédiaire" else " "
        assert f"[{marque}] {nom} : terminer le jeu en mode {mode}" in sortie


# --- Record du mode Enfer ---


def heros_nomme(nom="Aldric", numero_classe="3"):
    """Crée un joueur de test avec une classe."""
    joueur = creer_joueur()
    joueur.nom = nom
    joueur.prendre_classe(CLASSES[numero_classe])
    return joueur


def test_pas_de_record_au_depart():
    """Sans partie en Enfer, le record le dit."""
    assert texte_record() == "Record en mode Enfer : aucun"


def test_premier_record():
    """Le premier niveau atteint devient le record, avec le héros qui l'a atteint."""
    assert noter_record_enfer(heros_nomme(), 3) is True
    assert texte_record() == "Record en mode Enfer : niveau 3 (Aldric, Mage)"


def test_le_record_ne_baisse_jamais():
    """Un niveau plus bas ou égal ne remplace pas le record."""
    noter_record_enfer(heros_nomme(), 5)
    assert noter_record_enfer(heros_nomme("Brune"), 4) is False
    assert noter_record_enfer(heros_nomme("Brune"), 5) is False
    assert texte_record() == "Record en mode Enfer : niveau 5 (Aldric, Mage)"


def test_le_record_est_battu_par_un_autre_heros():
    """Un héros qui va plus loin prend le record."""
    noter_record_enfer(heros_nomme(), 5)
    assert noter_record_enfer(heros_nomme("Brune", "1"), 6) is True
    assert texte_record() == "Record en mode Enfer : niveau 6 (Brune, Guerrier)"


def test_record_et_succes_se_gardent_mutuellement():
    """Noter l'un n'efface pas l'autre."""
    debloquer("Facile")
    noter_record_enfer(heros_nomme(), 2)
    debloquer("Difficile")
    assert modes_reussis() == ["Facile", "Difficile"]
    assert "niveau 2" in texte_record()


def test_le_succes_ultime_est_signale(capsys):
    """Le succès de l'Enfer se distingue des autres dans la liste, avec le record à la suite."""
    noter_record_enfer(heros_nomme(), 7)
    debloquer(MODE_ULTIME)
    afficher_succes()
    sortie = capsys.readouterr().out
    nom = SUCCES[MODE_ULTIME][0]
    assert f"[x] {nom} : terminer le jeu en mode Enfer (succès ultime)" in sortie
    assert sortie.count("succès ultime") == 1
    assert "Record en mode Enfer : niveau 7 (Aldric, Mage)" in sortie
