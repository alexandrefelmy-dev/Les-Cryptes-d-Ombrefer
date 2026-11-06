"""Tests de objet.py : potions, armes et conversion en dictionnaire."""

from outils import creer_joueur

from ombrefer.effet import POISON
from ombrefer.objet import afficher_equipement, Arme, Armure, Objet, objet_depuis_dict, Potion


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


def test_armure_augmente_la_defense():
    """Une armure ajoute son bonus à la défense et l'annonce."""
    joueur = creer_joueur()
    phrase = Armure("Cotte", 3).utiliser(joueur)
    assert joueur.defense == 3
    assert "défense 0 → 3" in phrase


def test_une_seule_arme_portee():
    """Une nouvelle arme remplace l'ancienne, qui retourne dans l'inventaire."""
    joueur = creer_joueur()
    dague = Arme("Dague", 2)
    epee = Arme("Epée", 5)
    dague.utiliser(joueur)
    epee.utiliser(joueur)
    assert joueur.attaque == 13
    assert joueur.arme is epee
    assert joueur.inventaire == [dague]


def test_une_seule_armure_portee():
    """Une nouvelle armure remplace l'ancienne, qui retourne dans l'inventaire."""
    joueur = creer_joueur()
    tunique = Armure("Tunique", 1)
    cotte = Armure("Cotte", 3)
    tunique.utiliser(joueur)
    cotte.utiliser(joueur)
    assert joueur.defense == 3
    assert joueur.armure is cotte
    assert joueur.inventaire == [tunique]


def test_reprendre_une_arme_plus_faible():
    """Remettre l'ancienne arme redonne exactement l'ancienne attaque."""
    joueur = creer_joueur()
    Arme("Dague", 2).utiliser(joueur)
    Arme("Epée", 5).utiliser(joueur)
    joueur.utiliser_objet(0)
    assert joueur.attaque == 10
    assert joueur.arme.nom == "Dague"
    assert joueur.inventaire[0].nom == "Epée"


def test_changer_d_arme_garde_les_niveaux():
    """L'attaque gagnée en montant de niveau reste après un changement d'arme."""
    joueur = creer_joueur()
    Arme("Dague", 2).utiliser(joueur)
    joueur.gagner_xp(20)
    Arme("Epée", 5).utiliser(joueur)
    assert joueur.attaque == 14


def test_prix_des_objets():
    """Le prix dépend de l'objet : soin, bonus d'attaque ou de défense."""
    assert Potion("Potion", 20).prix() == 30
    assert Arme("Epée", 3).prix() == 15
    assert Armure("Cotte", 3).prix() == 30
    assert Arme("Epée", 3, POISON).prix() == 25
    assert Armure("Cotte", 3, POISON).prix() == 40
    assert Objet("Caillou").prix() == 0


def test_affichage_de_l_equipement(capsys):
    """L'équipement affiche ce qui est porté, ou ce qui manque."""
    joueur = creer_joueur()
    Arme("Epée", 3).utiliser(joueur)
    afficher_equipement(joueur)
    assert "Epée (+3 attaque), aucune armure" in capsys.readouterr().out


def test_affichage_armure():
    """Une armure affiche son bonus de défense."""
    assert str(Armure("Cotte", 3)) == "Cotte (+3 défense)"


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


def test_armure_depuis_dict():
    """Une armure passée en dictionnaire redevient une armure."""
    armure = objet_depuis_dict(Armure("Cotte", 3).to_dict())
    assert isinstance(armure, Armure)
    assert (armure.nom, armure.bonus) == ("Cotte", 3)


def test_objet_inconnu_depuis_dict():
    """Un type inconnu ne donne aucun objet."""
    assert objet_depuis_dict({"type": "inconnu"}) is None
