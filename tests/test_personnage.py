"""Tests de personnage.py : Personnage, Joueur et Ennemi."""

from outils import creer_joueur, hasard, joueur_avec_potion

from ombrefer.effet import POISON
from ombrefer.objet import Potion
from ombrefer.personnage import Joueur, Personnage


# --- Personnage ---


def test_personnage_commence_avec_tous_ses_pv():
    """Un nouveau personnage a tous ses PV."""
    personnage = Personnage("Test", 20, 5)
    assert personnage.pv == 20


def test_subir_degats_retire_des_pv():
    """Les dégâts sont retirés des PV."""
    personnage = Personnage("Test", 20, 5)
    personnage.subir_degats(8)
    assert personnage.pv == 12


def test_les_pv_ne_descendent_pas_sous_zero():
    """Des dégâts énormes laissent le personnage à 0 PV."""
    personnage = Personnage("Test", 20, 5)
    personnage.subir_degats(100)
    assert personnage.pv == 0


def test_est_vivant():
    """Un personnage à 0 PV n'est plus vivant."""
    personnage = Personnage("Test", 20, 5)
    assert personnage.est_vivant()
    personnage.subir_degats(20)
    assert not personnage.est_vivant()


def test_soigner_renvoie_le_montant_soigne():
    """soigner ajoute des PV et renvoie le montant soigné."""
    personnage = Personnage("Test", 20, 5)
    personnage.pv = 5
    assert personnage.soigner(10) == 10
    assert personnage.pv == 15


def test_soigner_ne_depasse_pas_pv_max():
    """Le soin s'arrête à pv_max et renvoie seulement ce qui a été soigné."""
    personnage = Personnage("Test", 20, 5)
    personnage.pv = 18
    assert personnage.soigner(10) == 2
    assert personnage.pv == 20


def test_attaquer_inflige_des_degats():
    """Sans critique, l'attaque inflige les dégâts tirés."""
    attaquant = Personnage("A", 20, 5)
    cible = Personnage("B", 20, 5)
    with hasard():
        assert attaquant.attaquer(cible) == (5, False)
    assert cible.pv == 15


def test_coup_critique_double_les_degats():
    """Un coup critique double les dégâts."""
    attaquant = Personnage("A", 20, 5)
    cible = Personnage("B", 20, 5)
    with hasard(0.1):
        assert attaquant.attaquer(cible) == (10, True)
    assert cible.pv == 10


# --- Joueur ---


def test_gagner_or():
    """L'or gagné s'ajoute à celui du joueur."""
    joueur = creer_joueur()
    joueur.gagner_or(15)
    joueur.gagner_or(5)
    assert joueur.piece == 20


def test_pas_de_defense_de_base():
    """Un nouveau joueur n'a aucune défense : les dégâts passent entièrement."""
    joueur = Joueur("Aldric", 30, 8)
    assert joueur.defense == 0
    with hasard():
        joueur.subir_degats(10)
    assert joueur.pv == 20


def test_nouveau_joueur_au_niveau_1():
    """Un nouveau héros commence au premier niveau de donjon."""
    assert creer_joueur().niveau_donjon == 1


def test_finir_un_niveau_repose_le_heros():
    """Finir un niveau fait descendre le héros, rend ses PV et guérit ses effets."""
    joueur = creer_joueur()
    joueur.pv = 3
    joueur.recevoir_effet(POISON)
    joueur.finir_niveau_donjon()
    assert joueur.niveau_donjon == 2
    assert joueur.pv == 30
    assert not joueur.effets


def test_payer_retire_l_or():
    """Le paiement réussit si le joueur a assez d'or, tout juste compris."""
    joueur = creer_joueur()
    joueur.gagner_or(15)
    assert joueur.payer(15) is True
    assert joueur.piece == 0


def test_payer_sans_assez_d_or():
    """Sans assez d'or, le paiement échoue et l'or ne bouge pas."""
    joueur = creer_joueur()
    joueur.gagner_or(10)
    assert joueur.payer(11) is False
    assert joueur.piece == 10


def test_la_defense_reduit_les_degats():
    """La défense de 2 retire 2 points de dégâts."""
    joueur = creer_joueur(defense=2)
    with hasard():
        joueur.subir_degats(10)
    assert joueur.pv == 22


def test_la_defense_ne_soigne_pas():
    """Des dégâts plus faibles que la défense n'ajoutent pas de PV."""
    joueur = creer_joueur(defense=2)
    joueur.pv = 20
    with hasard():
        joueur.subir_degats(1)
    assert joueur.pv == 20


def test_esquive_annule_les_degats():
    """Une esquive réussie évite tous les dégâts."""
    joueur = creer_joueur()
    with hasard(0.05):
        joueur.subir_degats(10)
    assert joueur.pv == 30


def test_ramasser_objet():
    """L'objet ramassé arrive à la fin de l'inventaire."""
    joueur = creer_joueur()
    potion = Potion("Potion", 5)
    joueur.ramasser_objet(potion)
    assert joueur.inventaire == [potion]


def test_utiliser_objet_retire_l_objet():
    """Un objet utilisé fait son effet et quitte l'inventaire."""
    joueur = joueur_avec_potion()
    joueur.utiliser_objet(0)
    assert joueur.pv == 15
    assert not joueur.inventaire


def test_gagner_xp_sans_monter_de_niveau():
    """En dessous du seuil, le niveau ne change pas."""
    joueur = creer_joueur()
    assert joueur.gagner_xp(10) is False
    assert joueur.niveau == 1
    assert joueur.xp == 10


def test_monter_de_niveau_ameliore_le_joueur():
    """Une montée de niveau augmente les stats et rend tous les PV."""
    joueur = creer_joueur()
    joueur.pv = 1
    assert joueur.gagner_xp(25) is True
    assert joueur.niveau == 2
    assert joueur.xp == 5
    assert joueur.pv_max == 35
    assert joueur.pv == 35
    assert joueur.attaque == 9


def test_plusieurs_niveaux_d_un_coup():
    """60 XP suffisent pour passer du niveau 1 au niveau 3."""
    joueur = creer_joueur()
    joueur.gagner_xp(60)
    assert joueur.niveau == 3
    assert joueur.xp == 0
