"""Sauvegarde et chargement du héros au format JSON."""

import json

from ombrefer.personnage import Joueur

FICHIER_SAUVEGARDE = "sauvegarde.json"


def sauvegarder(joueur):
    """Sauvegarde le joueur dans un fichier JSON."""
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(joueur.to_dict(), f, indent=4, ensure_ascii=False)


def charger():
    """Charge le joueur depuis un fichier JSON."""
    try:
        with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
            donnees = json.load(f)
        return Joueur.from_dict(donnees)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print("Erreur : le fichier de sauvegarde est corrompu.")
        return None
