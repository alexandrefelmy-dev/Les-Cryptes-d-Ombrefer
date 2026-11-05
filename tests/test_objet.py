"""Tests de objet.py : potions, armes et conversion en dictionnaire."""

from outils import creer_joueur

from ombrefer.objet import Arme, Objet, objet_depuis_dict, Potion


def test_potion_soigne_le_joueur():
    """Une potion rend ses PV et l'annonce."""
    joueur = creer_joueur()
    joueur.pv = 10
    phrase = Potion("Potion", 5).utiliser(joueur)
    assert joueur.pv == 15
    assert "récupère 5 PV" in phrase


def test_potion_montre_les_pv_apres_soin():
    """Le message de la potion affiche les PV après le soin."""
    joueur = creer_joueur()
    joueur.pv = 10
    phrase = Potion("Potion", 5).utiliser(joueur)
    assert "(PV : 15/30)" in phrase


def test_potion_refusee_si_pv_pleins():
    """Une potion ne peut pas être bue avec tous ses PV."""
    joueur = creer_joueur()
    assert not Potion("Potion", 5).peut_etre_utilise(joueur)
    joueur.pv = 29
    assert Potion("Potion", 5).peut_etre_utilise(joueur)


def test_arme_augmente_l_attaque():
    """Une arme ajoute son bonus à l'attaque."""
    joueur = creer_joueur()
    Arme("Epée", 3).utiliser(joueur)
    assert joueur.attaque == 11


def test_objet_de_base_toujours_utilisable():
    """Un objet de base peut toujours être utilisé."""
    assert Objet("Caillou").peut_etre_utilise(creer_joueur())


def test_potion_depuis_dict():
    """Une potion passée en dictionnaire redevient une potion."""
    potion = objet_depuis_dict(Potion("Potion", 5).to_dict())
    assert isinstance(potion, Potion)
    assert (potion.nom, potion.soin) == ("Potion", 5)


def test_arme_depuis_dict():
    """Une arme passée en dictionnaire redevient une arme."""
    arme = objet_depuis_dict(Arme("Epée", 3).to_dict())
    assert isinstance(arme, Arme)
    assert (arme.nom, arme.bonus) == ("Epée", 3)


def test_objet_inconnu_depuis_dict():
    """Un type inconnu ne donne aucun objet."""
    assert objet_depuis_dict({"type": "inconnu"}) is None
