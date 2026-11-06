"""Fixtures partagées par tous les tests."""

import pytest


@pytest.fixture(name="fichier_succes", autouse=True)
def fixture_fichier_succes(tmp_path, monkeypatch):
    """Protège les vrais succès : tous les tests écrivent dans un dossier temporaire."""
    chemin = tmp_path / "succes.sav"
    monkeypatch.setattr("ombrefer.succes.FICHIER_SUCCES", str(chemin))
    return chemin


@pytest.fixture(name="fichier_sauvegarde", autouse=True)
def fixture_fichier_sauvegarde(tmp_path, monkeypatch):
    """Protège les vraies sauvegardes et renvoie le fichier de l'emplacement 1."""
    monkeypatch.setattr(
        "ombrefer.sauvegarde.FICHIER_SAUVEGARDE", str(tmp_path / "sauvegarde_{}.sav")
    )
    monkeypatch.setattr("ombrefer.sauvegarde.ANCIEN_FICHIER", str(tmp_path / "sauvegarde.sav"))
    return tmp_path / "sauvegarde_1.sav"
