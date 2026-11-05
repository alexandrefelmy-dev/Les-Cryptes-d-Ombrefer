"""Tests de combat.py : actions du combat, se défendre et retour depuis les objets."""

from outils import creer_joueur, hasard, joueur_avec_potion, saisies

from combat import action_defendre, action_fuir, choix_combat, combat, utiliser_un_objet
from objet import Potion
from personnage import Ennemi


# --- Objets ---


def test_potion_en_combat_montre_les_pv(capsys):
    """En combat, les PV après la potion sont affichés avant l'attaque de l'ennemi."""
    joueur = joueur_avec_potion()
    with hasard(), saisies("1"):
        utiliser_un_objet(joueur)
    sortie = capsys.readouterr().out
    assert "(PV : 15/30)" in sortie


# --- Combat ---


def test_choix_combat_redemande_si_invalide():
    """Une réponse invalide est redemandée."""
    with saisies("9", "abc", "2"):
        assert choix_combat(creer_joueur()) == "2"


def test_combat_gagne():
    """Le joueur gagne s'il tue l'ennemi, sans riposte de sa part."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        assert combat(joueur, Ennemi("Rat", 8, 4, 3)) == "victoire"
    assert joueur.pv == 30


def test_combat_perdu():
    """Le joueur perd s'il tombe à 0 PV."""
    joueur = creer_joueur(pv=5, attaque=1)
    with hasard(), saisies("1"):
        assert combat(joueur, Ennemi("Ogre", 100, 50, 0)) == "defaite"
    assert joueur.pv == 0


def test_fuite_reussie():
    """Une fuite réussie termine le combat sans dégâts."""
    joueur = creer_joueur()
    with hasard(0.3), saisies("3"):
        assert combat(joueur, Ennemi("Rat", 8, 4, 3)) == "fuite"
    assert joueur.pv == 30


def test_fuite_ratee_donne_une_riposte():
    """Après une fuite ratée, l'ennemi attaque."""
    joueur = creer_joueur()
    with hasard():
        assert action_fuir(joueur, Ennemi("Rat", 8, 10, 3), False) is None
    assert joueur.pv == 22


def test_impossible_de_fuir_un_boss():
    """Même avec un bon tirage, un boss ne peut pas être fui."""
    joueur = creer_joueur()
    with hasard(0.3):
        assert action_fuir(joueur, Ennemi("Boss", 50, 10, 0), True) is None
    assert joueur.pv == 22


# --- Se défendre ---


def test_defendre_double_la_defense_sans_la_modifier():
    """Le bonus double la défense actuelle mais pas la défense de base."""
    joueur = creer_joueur()
    with hasard():
        action_defendre(joueur, Ennemi("Rat", 8, 10, 3))
    assert joueur.tours_defense == 3
    assert joueur.defense_actuelle() == 4
    assert joueur.defense == 2
    assert joueur.pv == 24


def test_defendre_dure_trois_tours():
    """Dégâts de 10 : 6 + 6 + 6 avec le bonus, puis 8 sans lui."""
    joueur = creer_joueur(pv=100, attaque=1)
    with hasard(), saisies("4", "1", "1", "1", "1"):
        combat(joueur, Ennemi("Ogre", 4, 10, 0))
    assert joueur.pv == 74


def test_se_redefendre_relance_sans_cumuler():
    """Se redéfendre remet le compteur à 3, sans quadrupler la défense."""
    joueur = creer_joueur(pv=100, attaque=1)
    with hasard(), saisies("4", "1", "4", "1", "1", "1", "1"):
        combat(joueur, Ennemi("Ogre", 5, 10, 0))
    assert joueur.pv == 100 - 6 * 5 - 8


def test_bonus_retire_apres_une_victoire():
    """Le bonus ne survit pas à une victoire."""
    joueur = creer_joueur(attaque=8)
    with hasard(), saisies("4", "1"):
        combat(joueur, Ennemi("Rat", 8, 4, 3))
    assert joueur.tours_defense == 0
    assert joueur.defense_actuelle() == 2


def test_bonus_retire_apres_une_fuite():
    """Le bonus ne survit pas à une fuite."""
    joueur = creer_joueur()
    with hasard(0.3), saisies("4", "3"):
        combat(joueur, Ennemi("Rat", 8, 4, 3))
    assert joueur.tours_defense == 0


def test_bonus_retire_apres_une_defaite():
    """Le bonus ne survit pas à une défaite."""
    joueur = creer_joueur(pv=5)
    with hasard(), saisies("4"):
        combat(joueur, Ennemi("Ogre", 100, 50, 0))
    assert joueur.tours_defense == 0


# --- Option 0 (retour) ---


def test_retour_du_choix_d_objet():
    """Taper 0 ne consomme aucun objet."""
    joueur = joueur_avec_potion()
    with saisies("0"):
        assert utiliser_un_objet(joueur) is False
    assert len(joueur.inventaire) == 1
    assert joueur.pv == 10


def test_numero_d_objet_invalide_redemande():
    """Un numéro invalide est redemandé."""
    joueur = joueur_avec_potion()
    with saisies("9", "x", "1"):
        assert utiliser_un_objet(joueur) is True
    assert joueur.pv == 15


def test_inventaire_vide():
    """Sans objet, rien n'est demandé au joueur."""
    assert utiliser_un_objet(creer_joueur()) is False


def test_potion_refusee_reste_dans_l_inventaire():
    """Une potion refusée n'est pas perdue."""
    joueur = creer_joueur()
    joueur.ramasser_objet(Potion("Potion", 5))
    with saisies("1"):
        assert utiliser_un_objet(joueur) is False
    assert len(joueur.inventaire) == 1


def test_retour_en_combat_sans_riposte():
    """Revenir du choix d'objet ne donne pas d'attaque à l'ennemi."""
    joueur = joueur_avec_potion()
    with hasard(), saisies("2", "0", "1"):
        combat(joueur, Ennemi("Rat", 8, 4, 3))
    assert joueur.pv == 10


def test_retour_ne_consomme_pas_un_tour_de_defense(capsys):
    """Le tour 2 s'affiche deux fois, avec le même compteur, avant et après le retour."""
    joueur = joueur_avec_potion()
    with hasard(), saisies("4", "2", "0", "1"):
        combat(joueur, Ennemi("Ogre", 1, 1, 0))
    sortie = capsys.readouterr().out
    assert sortie.count("encore 2 tour(s)") == 2
    assert "encore 1 tour(s)" not in sortie
