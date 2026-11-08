"""Tests de sauvegarde.py : écriture, signature et chargement du héros."""

import base64
import json
import zlib

import pytest

from outils import creer_joueur

from ombrefer.effet import POISON
from ombrefer.objet import Arme, Armure, Potion, Remede
from ombrefer.sauvegarde import charger, decoder, encoder, sauvegarder, signer


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_sauvegarder_puis_charger():
    """Un héros sauvegardé revient à l'identique."""
    joueur = creer_joueur()
    joueur.pv = 12
    joueur.gagner_or(40)
    joueur.gagner_xp(25)
    joueur.ramasser_objet(Potion("Potion", 5))
    joueur.ramasser_objet(Arme("Epée", 3))
    joueur.ramasser_objet(Armure("Cotte", 2))
    joueur.ramasser_objet(Remede("Antidote", [POISON]))
    sauvegarder(joueur)
    charge = charger()
    assert charge.to_dict() == joueur.to_dict()
    assert isinstance(charge.inventaire[0], Potion)
    assert isinstance(charge.inventaire[1], Arme)
    assert isinstance(charge.inventaire[2], Armure)
    assert isinstance(charge.inventaire[3], Remede)


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_equipement_sauvegarde_sans_doubler_le_bonus():
    """L'équipement revient porté, sans ajouter son bonus une deuxième fois."""
    joueur = creer_joueur()
    Arme("Epée", 3).utiliser(joueur)
    Armure("Cotte", 2).utiliser(joueur)
    sauvegarder(joueur)
    charge = charger()
    assert (charge.attaque, charge.defense) == (11, 2)
    assert (charge.arme.nom, charge.armure.nom) == ("Epée", "Cotte")
    Arme("Dague", 1).utiliser(charge)
    assert charge.attaque == 9


def test_niveau_de_donjon_dans_le_fichier(fichier_sauvegarde):
    """Le fichier de sauvegarde contient le niveau de donjon du héros."""
    joueur = creer_joueur()
    joueur.niveau_donjon = 4
    sauvegarder(joueur)
    assert decoder(fichier_sauvegarde.read_bytes())["niveau_donjon"] == 4
    assert charger().niveau_donjon == 4


def test_difficulte_dans_le_fichier(fichier_sauvegarde):
    """Le fichier de sauvegarde contient le mode du héros."""
    joueur = creer_joueur()
    joueur.difficulte = "Difficile"
    sauvegarder(joueur)
    assert decoder(fichier_sauvegarde.read_bytes())["difficulte"] == "Difficile"
    assert charger().difficulte == "Difficile"


def test_bonus_de_defense_jamais_sauvegarde():
    """Sauvegarder pendant le bonus n'écrit ni le compteur ni la défense renforcée."""
    joueur = creer_joueur(defense=2)
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


# --- Protection du fichier ---


def fichier_de_test(fichier_sauvegarde):
    """Sauvegarde un héros riche de 40 pièces et renvoie les octets du fichier."""
    joueur = creer_joueur()
    joueur.gagner_or(40)
    sauvegarder(joueur)
    return fichier_sauvegarde.read_bytes()


def test_fichier_illisible(fichier_sauvegarde):
    """Ni le nom du héros ni ses stats n'apparaissent en clair."""
    octets = fichier_de_test(fichier_sauvegarde)
    assert b"Aldric" not in octets
    assert b"piece" not in octets


def test_encoder_puis_decoder_garde_les_accents():
    """Les données reviennent à l'identique, accents compris."""
    donnees = {"nom": "Élodie", "or": 12}
    assert decoder(encoder(donnees)) == donnees


def test_un_octet_modifie_est_refuse(fichier_sauvegarde, capsys):
    """Changer un seul caractère du contenu suffit à faire refuser le fichier."""
    octets = bytearray(fichier_de_test(fichier_sauvegarde))
    octets[-5] = ord("A") if octets[-5] != ord("A") else ord("B")
    fichier_sauvegarde.write_bytes(octets)
    assert charger() is None
    assert "modifié" in capsys.readouterr().out


def test_signature_modifiee_est_refusee(fichier_sauvegarde):
    """Une signature changée fait refuser le fichier."""
    octets = fichier_de_test(fichier_sauvegarde)
    fichier_sauvegarde.write_bytes(b"0" * 64 + octets[64:])
    assert charger() is None


def test_triche_sans_la_cle_est_refusee(fichier_sauvegarde):
    """Décoder le fichier, changer l'or et réencoder ne trompe pas la signature."""
    signature, _, contenu = fichier_de_test(fichier_sauvegarde).partition(b":")
    donnees = json.loads(zlib.decompress(base64.b64decode(contenu)))
    donnees["piece"] = 99999
    triche = base64.b64encode(zlib.compress(json.dumps(donnees).encode("utf-8")))
    fichier_sauvegarde.write_bytes(signature + b":" + triche)
    assert charger() is None


def test_json_en_clair_est_refuse(fichier_sauvegarde):
    """Un héros écrit à la main en JSON n'est pas accepté."""
    texte = json.dumps(creer_joueur().to_dict())
    fichier_sauvegarde.write_text(texte, encoding="utf-8")
    assert charger() is None


def test_fichier_binaire_quelconque_est_refuse(fichier_sauvegarde):
    """Des octets au hasard ne font pas planter le chargement."""
    fichier_sauvegarde.write_bytes(bytes(range(256)))
    assert charger() is None


def test_fichier_refuse_n_est_pas_supprime(fichier_sauvegarde):
    """Un fichier refusé reste sur le disque, intact."""
    fichier_sauvegarde.write_bytes(b"fichier abime")
    avant = fichier_sauvegarde.read_bytes()
    charger()
    assert fichier_sauvegarde.read_bytes() == avant


def test_fichier_d_un_ancien_format_est_refuse(fichier_sauvegarde, capsys):
    """Une sauvegarde bien signée mais incomplète est refusée sans planter."""
    fichier_sauvegarde.write_bytes(encoder({"nom": "Aldric"}))
    assert charger() is None
    assert "trop ancien" in capsys.readouterr().out


def test_heros_d_une_classe_supprimee_est_refuse(fichier_sauvegarde, capsys):
    """Un héros d'une classe retirée du jeu, comme le Berserker, est refusé sans planter."""
    donnees = creer_joueur().to_dict()
    donnees["classe"] = "Berserker"
    fichier_sauvegarde.write_bytes(encoder(donnees))
    assert charger() is None
    assert "trop ancien" in capsys.readouterr().out


def test_la_signature_depend_du_contenu():
    """Deux contenus différents n'ont pas la même signature."""
    assert signer(b"a") != signer(b"b")
