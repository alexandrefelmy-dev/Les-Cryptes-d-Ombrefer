"""Tests de boutique.py : affichage, achats et visite du marchand."""

from outils import creer_joueur, saisies

from ombrefer.boutique import (
    acheter,
    afficher_boutique,
    afficher_vente,
    equipement_a_vendre,
    vendre,
    visiter_boutique,
    visiter_vente,
)
from ombrefer.classe import CLASSES
from ombrefer.objet import Arme, Armure, EPEE, Potion, Remede
from ombrefer.sauvegarde import charger, sauvegarder


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


# --- Vente ---


def test_prix_de_revente_vaut_la_moitie_du_prix():
    """Le marchand reprend à 50 % : racheter puis revendre fait toujours perdre de l'or."""
    assert Arme("Epée", 4).prix_revente() == 10
    assert Armure("Cotte", 3).prix_revente() == 15


def test_prix_de_revente_compte_l_effet():
    """Le supplément d'effet compte aussi dans le prix de revente."""
    assert Arme("Dague", 2, "Poison").prix_revente() == 10
    assert Armure("Cuir", 1, "Poison").prix_revente() == 10


def test_vendre_un_objet_range():
    """Vendre un objet de l'inventaire le retire et paie le joueur."""
    joueur = joueur_riche(0)
    arme = Arme("Epée", 4)
    joueur.ramasser_objet(arme)
    vendre(joueur, arme)
    assert joueur.piece == 10
    assert not joueur.inventaire


def test_vendre_l_arme_portee_retire_son_bonus():
    """Sans son arme, le héros perd le bonus, et elle ne revient pas dans l'inventaire."""
    joueur = joueur_riche(0)
    joueur.equiper_arme(Arme("Epée", 4))
    vendre(joueur, joueur.arme)
    assert joueur.arme is None
    assert joueur.attaque == 8
    assert joueur.piece == 10
    assert not joueur.inventaire


def test_vendre_l_arme_portee_suit_le_bonus_de_classe():
    """Le bonus réel de la classe est retiré, le prix reste celui de l'arme."""
    joueur = joueur_riche(0)
    joueur.prendre_classe(CLASSES["1"])  # gros bonus à l'épée
    joueur.equiper_arme(Arme("Epée", 4, famille=EPEE))
    assert joueur.attaque == 14
    vendre(joueur, joueur.arme)
    assert joueur.attaque == 8
    assert joueur.piece == 10


def test_vendre_l_armure_portee_retire_sa_defense():
    """Sans son armure, le héros perd sa défense et sa protection."""
    joueur = joueur_riche(0)
    joueur.equiper_armure(Armure("Cuir", 1, "Poison"))
    vendre(joueur, joueur.armure)
    assert joueur.armure is None
    assert joueur.defense == 0
    assert joueur.peut_recevoir("Poison")


def test_deux_objets_identiques_ne_se_confondent_pas():
    """Vendre l'exemplaire rangé laisse celui qui est porté."""
    joueur = joueur_riche(0)
    joueur.equiper_arme(Arme("Epée", 4))
    double = Arme("Epée", 4)
    joueur.ramasser_objet(double)
    vendre(joueur, double)
    assert joueur.arme is not None
    assert joueur.attaque == 12
    assert not joueur.inventaire


def test_potions_et_remedes_ne_se_vendent_pas():
    """Seuls les armes et armures intéressent le marchand."""
    joueur = joueur_riche(0)
    joueur.ramasser_objet(Potion("Potion", 10))
    joueur.ramasser_objet(Remede("Antidote", ("Poison",)))
    assert not equipement_a_vendre(joueur)


def test_liste_de_vente_range_d_abord_ce_qui_n_est_pas_porte():
    """L'équipement porté arrive en dernier, et il est signalé."""
    joueur = joueur_riche(0)
    joueur.equiper_arme(Arme("Lance", 6))
    joueur.ramasser_objet(Arme("Epée", 4))
    joueur.ramasser_objet(Potion("Potion", 10))
    assert [objet.nom for objet in equipement_a_vendre(joueur)] == ["Epée", "Lance"]


def test_afficher_la_vente(capsys):
    """La liste donne les prix de revente et signale ce qui est porté."""
    joueur = joueur_riche(25)
    joueur.equiper_arme(Arme("Lance", 6))
    joueur.ramasser_objet(Arme("Epée", 4))
    afficher_vente(joueur, equipement_a_vendre(joueur))
    sortie = capsys.readouterr().out
    assert "=== Vente === (Or : 25)" in sortie
    assert "1. Epée (Lance, +4 attaque) : 10 or" in sortie
    assert "2. Lance (Lance, +6 attaque) [porté] : 15 or" in sortie


def test_vendre_depuis_la_boutique():
    """La touche v ouvre la vente, puis le joueur revient acheter."""
    joueur = joueur_riche(0)
    joueur.ramasser_objet(Arme("Epée", 4))
    stock = [Potion("Potion", 2)]
    with saisies("v", "1", "1"):
        visiter_boutique(joueur, stock)
    assert joueur.piece == 7
    assert [objet.nom for objet in joueur.inventaire] == ["Potion"]


def test_menu_propose_la_vente_seulement_s_il_y_a_de_quoi(capsys):
    """Sans équipement, la vente n'apparaît pas et la touche v est refusée."""
    with saisies("v", "0"):
        visiter_boutique(joueur_riche(), [Potion("Potion", 10)])
    sortie = capsys.readouterr().out
    assert "v. Vendre" not in sortie
    assert "Numéro invalide." in sortie


def test_la_majuscule_ouvre_aussi_la_vente(capsys):
    """V et v font la même chose."""
    joueur = joueur_riche(0)
    joueur.ramasser_objet(Arme("Epée", 4))
    with saisies("V", "0", "0"):
        visiter_boutique(joueur, [Potion("Potion", 10)])
    assert "=== Vente ===" in capsys.readouterr().out


def test_vendre_ce_qu_on_porte_demande_confirmation():
    """Refuser garde l'objet, accepter le vend."""
    joueur = joueur_riche(0)
    joueur.equiper_arme(Arme("Epée", 4))
    with saisies("1", "n", "0"):
        visiter_vente(joueur)
    assert joueur.arme is not None
    assert joueur.piece == 0
    with saisies("1", "o"):
        visiter_vente(joueur)
    assert joueur.arme is None
    assert joueur.piece == 10


def test_vendre_ce_qui_est_range_ne_demande_rien():
    """Un objet rangé part sans confirmation : aucun risque de perdre son bonus."""
    joueur = joueur_riche(0)
    joueur.ramasser_objet(Arme("Epée", 4))
    with saisies("1"):
        visiter_vente(joueur)
    assert joueur.piece == 10


def test_numero_invalide_dans_la_vente(capsys):
    """Un numéro invalide est refusé puis redemandé."""
    joueur = joueur_riche(0)
    joueur.ramasser_objet(Arme("Epée", 4))
    with saisies("9", "abc", "0"):
        visiter_vente(joueur)
    assert capsys.readouterr().out.count("Numéro invalide.") == 2


def test_stock_vide_laisse_vendre(capsys):
    """Le marchand n'a plus rien, mais il achète encore l'équipement du joueur."""
    joueur = joueur_riche(0)
    joueur.ramasser_objet(Arme("Epée", 4))
    with saisies("v", "1"):
        visiter_boutique(joueur, [])
    assert joueur.piece == 10
    assert "plus rien à vendre" in capsys.readouterr().out


def test_sauvegarder_apres_une_vente_ne_ramene_pas_l_objet():
    """Le joueur sans arme se sauvegarde et se recharge sans bonus fantôme."""
    joueur = joueur_riche(0)
    joueur.equiper_arme(Arme("Epée", 4))
    vendre(joueur, joueur.arme)
    sauvegarder(joueur)
    charge = charger()
    assert charge.arme is None
    assert charge.attaque == 8
