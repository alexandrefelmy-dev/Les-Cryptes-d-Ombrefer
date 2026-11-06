"""Tests de boutique.py : affichage, achats et visite du marchand."""

from outils import creer_joueur, saisies

from ombrefer.boutique import acheter, afficher_boutique, visiter_boutique
from ombrefer.objet import Arme, Armure, Potion


def joueur_riche(or_du_joueur=100):
    """Crée un joueur qui possède cette somme d'or."""
    joueur = creer_joueur()
    joueur.gagner_or(or_du_joueur)
    return joueur


def test_afficher_boutique(capsys):
    """La boutique montre l'or du joueur, les objets, leur prix et la sortie."""
    afficher_boutique(joueur_riche(25), [Potion("Potion", 10), Armure("Cotte", 2)])
    sortie = capsys.readouterr().out
    assert "(Or : 25)" in sortie
    assert "1. Potion (+10 PV) : 15 or" in sortie
    assert "2. Cotte (+2 défense) : 20 or" in sortie
    assert "0. Partir" in sortie


def test_acheter_met_l_objet_dans_l_inventaire():
    """Un achat retire l'or et déplace l'objet du stock vers l'inventaire."""
    joueur = joueur_riche()
    arme = Arme("Epée", 3)
    stock = [arme]
    assert acheter(joueur, stock, 0) is True
    assert joueur.piece == 85
    assert joueur.inventaire == [arme]
    assert not stock


def test_acheter_ne_porte_pas_l_objet():
    """L'objet acheté attend dans l'inventaire : le joueur choisit de le porter."""
    joueur = joueur_riche()
    acheter(joueur, [Arme("Epée", 3)], 0)
    assert joueur.arme is None
    assert joueur.attaque == 8


def test_achat_refuse_sans_assez_d_or(capsys):
    """Sans assez d'or, rien ne change et le joueur est prévenu."""
    joueur = joueur_riche(14)
    stock = [Arme("Epée", 3)]
    assert acheter(joueur, stock, 0) is False
    assert joueur.piece == 14
    assert not joueur.inventaire
    assert len(stock) == 1
    assert "pas assez d'or" in capsys.readouterr().out


def test_partir_de_la_boutique_sans_acheter():
    """Le choix 0 quitte la boutique sans rien acheter."""
    joueur = joueur_riche()
    stock = [Potion("Potion", 10)]
    with saisies("0"):
        visiter_boutique(joueur, stock)
    assert joueur.piece == 100
    assert len(stock) == 1


def test_numero_invalide_dans_la_boutique(capsys):
    """Un numéro invalide est refusé puis redemandé."""
    with saisies("7", "abc", "0"):
        visiter_boutique(joueur_riche(), [Potion("Potion", 10)])
    assert capsys.readouterr().out.count("Numéro invalide.") == 2


def test_acheter_plusieurs_objets_a_la_suite():
    """Les numéros suivent le stock restant après chaque achat."""
    joueur = joueur_riche()
    with saisies("2", "1", "0"):
        visiter_boutique(joueur, [Potion("Potion", 10), Arme("Epée", 3), Armure("Cotte", 1)])
    assert [objet.nom for objet in joueur.inventaire] == ["Epée", "Potion"]


def test_stock_vide_ferme_la_boutique(capsys):
    """Une fois tout acheté, la boutique se ferme d'elle-même."""
    with saisies("1"):
        visiter_boutique(joueur_riche(), [Potion("Potion", 10)])
    assert "plus rien à vendre" in capsys.readouterr().out


def test_stock_garde_entre_deux_visites():
    """Un objet acheté ne revient pas à la visite suivante."""
    joueur = joueur_riche()
    stock = [Potion("Potion", 10), Arme("Epée", 3)]
    with saisies("1", "0"):
        visiter_boutique(joueur, stock)
    assert [objet.nom for objet in stock] == ["Epée"]
