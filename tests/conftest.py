"""Fixtures partagées par tous les tests."""

import pytest


@pytest.fixture(name="fichier_succes", autouse=True)
def fixture_fichier_succes(tmp_path, monkeypatch):
    """Protège les vrais succès : tous les tests écrivent dans un dossier temporaire."""
    chemin = tmp_path / "succes.sav"
    monkeypatch.setattr("ombrefer.succes.FICHIER_SUCCES", str(chemin))
    return chemin


@pytest.fixture(name="fichier_sauvegarde")
def fixture_fichier_sauvegarde(tmp_path, monkeypatch):
    """Redirige la sauvegarde vers un dossier temporaire et renvoie le chemin du fichier."""
    chemin = tmp_path / "sauvegarde.sav"
    monkeypatch.setattr("ombrefer.sauvegarde.FICHIER_SAUVEGARDE", str(chemin))
    return chemin
