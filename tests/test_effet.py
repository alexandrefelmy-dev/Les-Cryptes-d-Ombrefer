"""Tests des effets : poison, saignement, immobilisation, affaiblissement et leurs parades."""

import pytest

from outils import creer_joueur, hasard, saisies

from ombrefer.combat import action_defendre, combat, riposte, tour_attaque
from ombrefer.donjon import explorer, traverser_salle, Salle
from ombrefer.effet import (
    AFFAIBLISSEMENT,
    DEGATS_POISON,
    DEGATS_SAIGNEMENT,
    IMMOBILISATION,
    POISON,
    SAIGNEMENT,
)
from ombrefer.objet import Arme, Armure, objet_depuis_dict, Remede
from ombrefer.personnage import Ennemi


def ennemi_a_effet(effet, pv=8, attaque=4):
    """Crée un ennemi qui inflige toujours son effet quand son coup touche."""
    return Ennemi("Bête", pv, attaque, 3, effet, 1)


def joueur_avec_arme(effet):
    """Crée un joueur dont l'arme inflige cet effet."""
    joueur = creer_joueur()
    Arme("Lame", 2, effet).utiliser(joueur)
    return joueur


# --- Règles communes ---


def test_le_coup_inflige_l_effet_de_l_ennemi(capsys):
    """Un coup qui touche inflige l'effet et l'annonce."""
    joueur = creer_joueur()
    with hasard():
        tour_attaque(ennemi_a_effet(POISON), joueur)
    assert POISON in joueur.effets
    assert "Aldric subit : Poison !" in capsys.readouterr().out


def test_chance_de_l_effet():
    """L'effet ne passe que si le tirage est sous la chance de l'ennemi."""
    joueur = creer_joueur()
    with hasard():
        tour_attaque(Ennemi("Bête", 8, 4, 3, POISON, 0.4), joueur)
    assert not joueur.effets


def test_coup_sans_degats_sans_effet():
    """Un coup entièrement arrêté par l'armure n'inflige pas d'effet."""
    joueur = creer_joueur(defense=10)
    with hasard():
        tour_attaque(ennemi_a_effet(POISON), joueur)
    assert not joueur.effets


def test_esquive_sans_effet():
    """Un coup esquivé n'inflige pas d'effet."""
    joueur = creer_joueur()
    with hasard(0.05):
        tour_attaque(ennemi_a_effet(POISON), joueur)
    assert not joueur.effets


def test_reinfliger_relance_sans_cumuler():
    """Subir à nouveau un effet relance sa durée, sans additionner sa force."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    joueur.passer_un_tour()
    joueur.recevoir_effet(POISON)
    assert joueur.effets[POISON] == 3
    joueur.passer_un_tour()
    assert joueur.pv == 30 - 2 * DEGATS_POISON


def test_effets_affiches_avec_le_personnage():
    """Les effets subis apparaissent à côté des PV."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    assert "Aldric (PV : 30/30) [Poison]" in str(joueur)


# --- Poison ---


def test_poison_trois_tours():
    """Le poison retire ses PV au début de 3 tours, puis s'arrête."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    for _ in range(5):
        joueur.passer_un_tour()
    assert joueur.pv == 30 - 3 * DEGATS_POISON
    assert POISON not in joueur.effets


def test_poison_ignore_la_defense():
    """La défense ne réduit pas le poison."""
    joueur = creer_joueur(defense=10)
    joueur.recevoir_effet(POISON)
    joueur.passer_un_tour()
    assert joueur.pv == 30 - DEGATS_POISON


def test_poison_continue_apres_le_combat():
    """Seul le poison survit à la fin du combat."""
    joueur = creer_joueur()
    for effet in (POISON, SAIGNEMENT, AFFAIBLISSEMENT):
        joueur.recevoir_effet(effet)
    joueur.fin_de_combat()
    assert list(joueur.effets) == [POISON]


def test_poison_agit_en_entrant_dans_une_salle():
    """Le poison retire des PV à l'entrée d'une salle, même vide."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    with saisies("2"):
        assert traverser_salle(joueur, Salle(1, None, None, False)) is True
    assert joueur.pv == 30 - DEGATS_POISON


def test_poison_mortel_entre_deux_salles():
    """Le poison peut tuer le héros avant la salle suivante."""
    joueur = creer_joueur(pv=DEGATS_POISON)
    joueur.recevoir_effet(POISON)
    assert explorer(joueur, [Salle(1, None, None, False)]) is False


def test_ennemi_tue_par_le_poison_est_vaincu():
    """Un ennemi empoisonné qui meurt à son tour donne la victoire."""
    joueur = creer_joueur(attaque=1)
    ennemi = Ennemi("Rat", 3, 1, 3)
    ennemi.recevoir_effet(POISON)
    with hasard(), saisies("1"):
        assert combat(joueur, ennemi) == "victoire"


def test_heros_tue_par_le_poison_perd_le_combat():
    """Un héros qui meurt du poison au début de son tour perd le combat."""
    joueur = creer_joueur(pv=DEGATS_POISON)
    joueur.recevoir_effet(POISON)
    with hasard():
        assert combat(joueur, Ennemi("Rat", 8, 1, 3)) == "defaite"


# --- Saignement ---


def test_saignement_coute_des_pv_a_chaque_attaque():
    """Celui qui saigne perd des PV en attaquant, malgré sa défense."""
    joueur = creer_joueur(defense=10)
    joueur.recevoir_effet(SAIGNEMENT)
    with hasard():
        tour_attaque(joueur, Ennemi("Rat", 80, 1, 3))
    assert joueur.pv == 30 - DEGATS_SAIGNEMENT


def test_se_defendre_evite_le_saignement():
    """Se défendre n'est pas une attaque : le héros ne saigne pas."""
    joueur = creer_joueur(defense=5)
    joueur.recevoir_effet(SAIGNEMENT)
    with hasard():
        action_defendre(joueur, Ennemi("Rat", 80, 1, 3))
    assert joueur.pv == 30


def test_saignement_mortel_empeche_le_coup():
    """Un héros qui meurt en saignant ne porte pas son coup et perd le combat."""
    joueur = creer_joueur(pv=DEGATS_SAIGNEMENT)
    joueur.recevoir_effet(SAIGNEMENT)
    ennemi = Ennemi("Rat", 1, 1, 3)
    with hasard(), saisies("1"):
        assert combat(joueur, ennemi) == "defaite"
    assert ennemi.pv == 1


# --- Immobilisation ---


def test_immobilisation_fait_perdre_un_tour(capsys):
    """Le héros perd un seul tour : le répit empêche d'enchaîner les immobilisations."""
    joueur = creer_joueur(pv=100, attaque=1)
    with hasard(), saisies("1", "1", "1"):
        assert combat(joueur, ennemi_a_effet(IMMOBILISATION, pv=3, attaque=1)) == "victoire"
    assert capsys.readouterr().out.count("Aldric passe son tour") == 1


def test_ennemi_immobilise_ne_riposte_pas():
    """Un ennemi immobilisé passe son tour."""
    joueur = creer_joueur()
    ennemi = Ennemi("Ogre", 50, 10, 0)
    ennemi.recevoir_effet(IMMOBILISATION)
    with hasard():
        riposte(ennemi, joueur)
    assert joueur.pv == 30


# --- Affaiblissement ---


def test_affaiblissement_reduit_l_attaque():
    """Affaibli, on frappe moins fort, sans changer l'attaque de base."""
    joueur = creer_joueur(attaque=10)
    joueur.recevoir_effet(AFFAIBLISSEMENT)
    assert joueur.attaque_actuelle() == 7
    assert joueur.attaque == 10


def test_affaiblissement_laisse_une_attaque_minimale():
    """L'attaque d'un personnage affaibli reste d'au moins 1."""
    joueur = creer_joueur(attaque=1)
    joueur.recevoir_effet(AFFAIBLISSEMENT)
    assert joueur.attaque_actuelle() == 1


def test_affaiblissement_reduit_les_degats():
    """Le coup d'un affaibli est tiré avec l'attaque réduite."""
    joueur = creer_joueur(attaque=10)
    joueur.recevoir_effet(AFFAIBLISSEMENT)
    ennemi = Ennemi("Rat", 50, 1, 3)
    with hasard():
        joueur.attaquer(ennemi)
    assert ennemi.pv == 43


# --- Parades : garde, armures et remèdes ---


def test_la_garde_bloque_les_nouveaux_effets(capsys):
    """Pendant la garde, un coup qui touche n'inflige plus d'effet."""
    joueur = creer_joueur()
    with hasard():
        action_defendre(joueur, ennemi_a_effet(POISON))
    assert not joueur.effets
    assert "Aldric résiste : Poison." in capsys.readouterr().out


def test_se_defendre_sans_armure_contre_un_effet():
    """Sans armure, se défendre reste possible face à un ennemi à effet."""
    joueur = creer_joueur()
    with hasard():
        assert action_defendre(joueur, ennemi_a_effet(POISON)) is None
    assert joueur.tours_defense == 3


def test_la_garde_ne_guerit_pas():
    """La garde n'enlève pas un effet déjà subi."""
    joueur = creer_joueur(defense=2)
    joueur.recevoir_effet(POISON)
    with hasard():
        action_defendre(joueur, Ennemi("Rat", 8, 1, 3))
    assert POISON in joueur.effets


def test_l_armure_protege_de_son_effet():
    """Une armure protège de son effet, mais pas des autres."""
    joueur = creer_joueur()
    Armure("Cuir", 1, POISON).utiliser(joueur)
    assert joueur.recevoir_effet(POISON) is False
    assert joueur.recevoir_effet(SAIGNEMENT) is True


def test_enfiler_la_bonne_armure_retire_l_effet():
    """Porter une armure protectrice retire l'effet qu'elle bloque."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    Armure("Cuir", 1, POISON).utiliser(joueur)
    assert POISON not in joueur.effets


def test_arme_inflige_son_effet_a_l_ennemi():
    """Un coup de l'arme peut infliger son effet à l'ennemi."""
    joueur = joueur_avec_arme(SAIGNEMENT)
    ennemi = Ennemi("Rat", 50, 1, 3)
    with hasard(0.25):
        tour_attaque(joueur, ennemi)
    assert SAIGNEMENT in ennemi.effets


def test_arme_sans_effet_n_inflige_rien():
    """Sans effet sur l'arme, l'ennemi ne subit rien."""
    joueur = joueur_avec_arme(None)
    ennemi = Ennemi("Rat", 50, 1, 3)
    with hasard(0.25):
        tour_attaque(joueur, ennemi)
    assert not ennemi.effets


def test_remede_guerit_son_effet():
    """Un remède retire son effet, sans toucher aux autres."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    joueur.recevoir_effet(SAIGNEMENT)
    phrase = Remede("Antidote", [POISON]).utiliser(joueur)
    assert list(joueur.effets) == [SAIGNEMENT]
    assert "guérit : Poison" in phrase


def test_panacee_guerit_plusieurs_effets():
    """Un remède peut guérir plusieurs effets d'un coup."""
    joueur = creer_joueur()
    joueur.recevoir_effet(POISON)
    joueur.recevoir_effet(SAIGNEMENT)
    Remede("Panacée", [POISON, SAIGNEMENT]).utiliser(joueur)
    assert not joueur.effets


def test_remede_inutile_refuse_et_garde(capsys):
    """Un remède sans effet à guérir reste dans l'inventaire, sans perdre le tour."""
    joueur = creer_joueur()
    joueur.ramasser_objet(Remede("Antidote", [POISON]))
    with hasard(), saisies("2", "1", "1"):
        combat(joueur, Ennemi("Rat", 8, 1, 3))
    assert len(joueur.inventaire) == 1
    assert "ne subit aucun effet" in capsys.readouterr().out


# --- Sauvegarde ---


@pytest.mark.parametrize(
    "objet",
    [Arme("Lame", 2, POISON), Armure("Cuir", 1, SAIGNEMENT), Remede("Antidote", [POISON])],
    ids=lambda objet: objet.nom,
)
def test_objets_a_effet_depuis_dict(objet):
    """Un objet à effet garde tout ce qu'il sait faire une fois rechargé."""
    assert objet_depuis_dict(objet.to_dict()).to_dict() == objet.to_dict()
