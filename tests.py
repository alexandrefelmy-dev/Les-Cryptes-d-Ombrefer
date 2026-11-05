"""Tests du jeu, sans jouer : lancer avec "python tests.py".

Chaque test prépare une situation, appelle une méthode, puis vérifie le résultat avec assert.
Le hasard et les saisies du clavier sont remplacés par des valeurs fixes.
"""

# Toutes les vérifications restent volontairement dans un seul fichier.
# pylint: disable=too-many-lines

import contextlib
import io
import json
import os
import sys
import tempfile
import traceback
from unittest.mock import patch

from combat import action_defendre, action_fuir, choix_combat, combat, utiliser_un_objet
from donjon import (
    DIFFICULTES,
    MODELES_ARMES,
    MODELES_BOSS,
    MODELES_ENNEMIS,
    Difficulte,
    FORCE_PAR_NIVEAU,
    adapter_au_niveau,
    affronter_ennemi,
    ajuster,
    creer_arme,
    creer_butin,
    creer_ennemi,
    creer_salle,
    creer_salle_boss,
    declencher_piege,
    explorer,
    generer_donjon,
    pause,
    traverser_salle,
)
from main import (
    choisir_difficulte,
    creer_heros,
    demander_nom,
    jeu,
    main,
    nouvelle_partie,
    partie_chargee,
)
from objet import Arme, Objet, Potion, objet_depuis_dict
from personnage import Ennemi, Joueur, Personnage
from sauvegarde import charger, sauvegarder

# Difficulté neutre : les modèles sont utilisés sans aucun changement.
NEUTRE = Difficulte("Test", 30, 8, 2, 1, 1)


@contextlib.contextmanager
def hasard(valeur=0.5):
    """Fixe le hasard : random() renvoie valeur et randint() renvoie toujours le maximum.

    0.5 : ni critique, ni esquive, et la fuite rate.
    0.3 : ni critique, ni esquive, et la fuite réussit.
    """
    with patch("random.random", return_value=valeur):
        with patch("random.randint", side_effect=lambda minimum, maximum: maximum):
            yield


def saisies(*reponses):
    """Remplace le clavier : chaque input() renvoie la réponse suivante."""
    return patch("builtins.input", side_effect=list(reponses))


def sortie_de(fonction, *arguments):
    """Appelle la fonction et renvoie ce qu'elle a affiché."""
    sortie = io.StringIO()
    with contextlib.redirect_stdout(sortie):
        fonction(*arguments)
    return sortie.getvalue()


def creer_joueur(pv=30, attaque=8):
    """Crée un joueur de test."""
    return Joueur("Aldric", pv, attaque)


def joueur_avec_potion():
    """Crée un joueur blessé (10/30 PV) qui possède une potion de 5 PV."""
    joueur = creer_joueur()
    joueur.pv = 10
    joueur.ramasser_objet(Potion("Potion", 5))
    return joueur


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


def test_la_defense_reduit_les_degats():
    """La défense de 2 retire 2 points de dégâts."""
    joueur = creer_joueur()
    with hasard():
        joueur.subir_degats(10)
    assert joueur.pv == 22


def test_la_defense_ne_soigne_pas():
    """Des dégâts plus faibles que la défense n'ajoutent pas de PV."""
    joueur = creer_joueur()
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


# --- Objets ---


def test_potion_soigne_le_joueur():
    """Une potion rend ses PV et l'annonce."""
    joueur = creer_joueur()
    joueur.pv = 10
    phrase = Potion("Potion", 5).utiliser(joueur)
    assert joueur.pv == 15
    assert "récupère 5 PV" in phrase


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


def test_retour_ne_consomme_pas_un_tour_de_defense():
    """Le tour 2 s'affiche deux fois, avec le même compteur, avant et après le retour."""
    joueur = joueur_avec_potion()
    with hasard(), saisies("4", "2", "0", "1"):
        sortie = sortie_de(combat, joueur, Ennemi("Ogre", 1, 1, 0))
    assert sortie.count("encore 2 tour(s)") == 2
    assert "encore 1 tour(s)" not in sortie


def test_retour_de_la_pause():
    """Revenir du choix d'objet ramène à la pause, sans utiliser l'objet."""
    joueur = joueur_avec_potion()
    with saisies("1", "0", "2"):
        pause(joueur)
    assert len(joueur.inventaire) == 1


def test_retour_de_la_difficulte():
    """Taper 0 ne crée pas de donjon."""
    with saisies("0"):
        assert choisir_difficulte() is None


def test_retour_de_la_difficulte_ne_lance_pas_de_partie():
    """Après un retour, aucune partie ne démarre."""
    with saisies("Aldric", "0"):
        assert "entre dans" not in sortie_de(nouvelle_partie)


def test_retour_du_nom():
    """Taper 0 annule la saisie du nom."""
    with saisies("0"):
        assert demander_nom() is None


def test_nom_vide_redemande():
    """Un nom vide est redemandé."""
    with saisies("   ", "Aldric"):
        assert demander_nom() == "Aldric"


def test_un_nom_commencant_par_zero_reste_valide():
    """Seul le 0 exact sert de retour."""
    with saisies("007"):
        assert demander_nom() == "007"


def test_retours_depuis_le_menu_principal():
    """Le joueur revient du nom, puis de la difficulté, puis quitte."""
    with saisies("1", "0", "1", "Aldric", "0", "3"):
        sortie = sortie_de(main)
    assert sortie.count("=== Les Cryptes d'Ombrefer ===") == 3
    assert "entre dans" not in sortie
    assert "À bientôt" in sortie


# --- Difficulté ---


def test_les_trois_modes_sont_proposes():
    """Chaque numéro du menu renvoie le bon mode."""
    for numero, difficulte in DIFFICULTES.items():
        with saisies(numero):
            assert choisir_difficulte() is difficulte


def test_difficulte_invalide_redemande():
    """Une difficulté invalide est redemandée."""
    with saisies("7", "1"):
        assert choisir_difficulte() is DIFFICULTES["1"]


def test_les_ennemis_se_renforcent_avec_la_difficulte():
    """La force des ennemis monte à chaque mode."""
    forces = [difficulte.force_ennemis for difficulte in DIFFICULTES.values()]
    assert forces == sorted(set(forces))


def test_le_heros_s_affaiblit_avec_la_difficulte():
    """Chaque mode retire des PV au héros, et le plus dur retire aussi de l'attaque."""
    pv = [difficulte.pv_joueur for difficulte in DIFFICULTES.values()]
    attaques = [difficulte.attaque_joueur for difficulte in DIFFICULTES.values()]
    assert pv == sorted(set(pv), reverse=True)
    assert attaques == sorted(attaques, reverse=True)
    assert attaques[0] > attaques[-1]


def test_les_recompenses_du_boss_montent_avec_la_difficulte():
    """Le multiplicateur des récompenses du boss monte à chaque mode."""
    gains = [difficulte.recompense_boss for difficulte in DIFFICULTES.values()]
    assert gains == sorted(set(gains))


def test_ajuster_arrondit():
    """ajuster multiplie puis arrondit."""
    assert ajuster(10, 1.3) == 13
    assert ajuster(8, 1.1) == 9


def test_ajuster_ne_descend_pas_sous_un():
    """Une valeur ajustée vaut au moins 1."""
    assert ajuster(1, 0.1) == 1


def test_creer_heros_utilise_les_stats_du_mode():
    """Le héros reçoit les PV, l'attaque et la défense du mode."""
    difficulte = Difficulte("Test", 21, 6, 4, 1, 1)
    joueur = creer_heros("Aldric", difficulte)
    assert (joueur.nom, joueur.pv, joueur.pv_max) == ("Aldric", 21, 21)
    assert joueur.attaque == 6
    assert joueur.defense == 4


def test_creer_ennemi_selon_la_force():
    """La force multiplie les PV et l'attaque, mais pas la récompense."""
    with patch("random.choice", return_value=("Rat", 10, 5, 3)):
        ennemi = creer_ennemi(Difficulte("Test", 30, 8, 2, 2, 1))
    assert (ennemi.pv_max, ennemi.attaque, ennemi.recompense) == (20, 10, 3)


def test_creer_boss_selon_la_force():
    """La force renforce le boss sans toucher à ses récompenses."""
    modele = (("Boss", 50, 10, 40), ("Arme", 6))
    with patch("random.choice", return_value=modele):
        salle = creer_salle_boss([], Difficulte("Test", 30, 8, 2, 2, 1))
    assert (salle.ennemi.pv_max, salle.ennemi.attaque) == (100, 20)
    assert (salle.ennemi.recompense, salle.butin.bonus) == (40, 6)


def test_recompenses_du_boss_selon_le_mode():
    """Le gain multiplie l'or et le bonus de l'arme, sans renforcer le boss."""
    modele = (("Boss", 50, 10, 40), ("Arme", 6))
    with patch("random.choice", return_value=modele):
        salle = creer_salle_boss([], Difficulte("Test", 30, 8, 2, 1, 2))
    assert (salle.ennemi.recompense, salle.butin.bonus) == (80, 12)
    assert (salle.ennemi.pv_max, salle.ennemi.attaque) == (50, 10)


def test_gain_des_ennemis_normaux():
    """Le gain multiplie la récompense, donc l'or et l'XP, sans renforcer l'ennemi."""
    with patch("random.choice", return_value=("Rat", 10, 5, 4)):
        ennemi = creer_ennemi(Difficulte("Test", 30, 8, 2, 1, 1, gain_ennemis=1.5))
    assert (ennemi.recompense, ennemi.pv_max, ennemi.attaque) == (6, 10, 5)


def test_le_gain_d_ennemi_ne_change_pas_le_boss():
    """Seul recompense_boss change les récompenses du boss."""
    modele = (("Boss", 50, 10, 40), ("Arme", 6))
    with patch("random.choice", return_value=modele):
        salle = creer_salle_boss([], Difficulte("Test", 30, 8, 2, 1, 1, gain_ennemis=3))
    assert salle.ennemi.recompense == 40


def test_les_gains_montent_avec_la_difficulte():
    """Les ennemis normaux rapportent plus à chaque mode."""
    gains = [difficulte.gain_ennemis for difficulte in DIFFICULTES.values()]
    assert gains == sorted(set(gains))


def test_les_pieges_augmentent_avec_la_difficulte():
    """Les pièges sont plus fréquents à chaque mode."""
    chances = [difficulte.chance_piege for difficulte in DIFFICULTES.values()]
    assert chances == sorted(set(chances))


def test_salle_utilise_la_chance_de_piege():
    """Un même tirage déclenche le piège seulement si la chance du mode est assez haute."""
    with hasard(0.15):
        assert creer_salle(1, Difficulte("Test", 30, 8, 2, 1, 1, chance_piege=0.2)).piege
        assert not creer_salle(1, Difficulte("Test", 30, 8, 2, 1, 1, chance_piege=0.1)).piege


def test_salle_boss_utilise_la_chance_de_piege():
    """La salle du boss suit aussi la chance de piège du mode."""
    with hasard(0.15):
        assert creer_salle_boss([], Difficulte("Test", 30, 8, 2, 1, 1, chance_piege=0.2)).piege
        assert not creer_salle_boss([], NEUTRE).piege


def test_les_potions_diminuent_avec_la_difficulte():
    """Les potions sont moins fréquentes à chaque mode."""
    chances = [difficulte.chance_potion for difficulte in DIFFICULTES.values()]
    assert chances == sorted(set(chances), reverse=True)


def test_butin_utilise_la_chance_de_potion():
    """Un même tirage donne une potion seulement si la chance du mode est assez haute."""
    with hasard(0.45):
        assert isinstance(creer_butin(NEUTRE), Potion)
        assert creer_butin(Difficulte("Test", 30, 8, 2, 1, 1, chance_potion=0.4)) is None


def test_reste_du_butin_selon_le_mode():
    """Hors potions, il reste 60 % de rien et 40 % d'armes."""
    difficulte = Difficulte("Test", 30, 8, 2, 1, 1, chance_potion=0.4)
    with hasard(0.75):
        assert creer_butin(difficulte) is None
    with hasard(0.77):
        assert isinstance(creer_butin(difficulte), Arme)


def test_ordre_de_rarete_des_armes_dans_tous_les_modes():
    """Dans chaque mode, chaque arme reste plus fréquente que la suivante."""
    for difficulte in DIFFICULTES.values():
        with patch("random.choices", return_value=[MODELES_ARMES[0]]) as tirage:
            creer_arme(difficulte)
        poids = tirage.call_args.kwargs["weights"]
        assert poids == sorted(set(poids), reverse=True)


def test_armes_rares_plus_frequentes_quand_c_est_plus_dur():
    """La meilleure arme a une plus grosse part des poids à chaque mode."""
    parts = []
    for difficulte in DIFFICULTES.values():
        with patch("random.choices", return_value=[MODELES_ARMES[0]]) as tirage:
            creer_arme(difficulte)
        poids = tirage.call_args.kwargs["weights"]
        parts.append(poids[-1] / sum(poids))
    assert parts == sorted(set(parts))


def test_seigneur_vampire_seulement_en_difficile():
    """Le boss le plus dur n'apparaît qu'en mode Difficile."""
    assert MODELES_BOSS[-1][0][0] == "Seigneur vampire"
    assert DIFFICULTES["1"].nb_boss == 3
    assert DIFFICULTES["2"].nb_boss == 3
    assert DIFFICULTES["3"].nb_boss == 4


def test_boss_possibles_selon_le_mode():
    """Sur beaucoup de tirages, seuls les boss autorisés sortent."""
    for difficulte in DIFFICULTES.values():
        noms = {creer_salle_boss([], difficulte).ennemi.nom for _ in range(300)}
        assert noms == {modele[0][0] for modele in MODELES_BOSS[:difficulte.nb_boss]}


def test_niveau_1_ne_change_rien():
    """Un héros de niveau 1 affronte la force normale du mode."""
    difficulte = DIFFICULTES["2"]
    assert adapter_au_niveau(difficulte, 1) == difficulte


def test_force_suit_le_niveau():
    """Chaque niveau au-dessus de 1 ajoute FORCE_PAR_NIVEAU à la force."""
    assert FORCE_PAR_NIVEAU > 0
    adaptee = adapter_au_niveau(Difficulte("Test", 30, 8, 2, 2, 1), 3)
    assert adaptee.force_ennemis == 2 * (1 + 2 * FORCE_PAR_NIVEAU)


def test_adapter_au_niveau_ne_modifie_pas_le_mode():
    """Le mode d'origine n'est pas changé pour les parties suivantes."""
    difficulte = DIFFICULTES["2"]
    force = difficulte.force_ennemis
    adapter_au_niveau(difficulte, 8)
    assert difficulte.force_ennemis == force


def test_le_donjon_suit_le_niveau_du_heros():
    """jeu crée un donjon adapté au niveau du héros."""
    joueur = creer_joueur()
    joueur.niveau = 4
    with patch("main.explorer", return_value=False):
        with patch("main.generer_donjon", return_value=[]) as generer:
            sortie_de(jeu, joueur, NEUTRE)
    assert generer.call_args.args[1].force_ennemis == 1 + 3 * FORCE_PAR_NIVEAU


def test_de_6_a_9_salles_dans_tous_les_modes():
    """Tous les modes tirent entre 6 et 9 salles, et toutes ces tailles sortent."""
    for difficulte in DIFFICULTES.values():
        tailles = set()
        for _ in range(200):
            with patch("main.explorer", return_value=False):
                sortie = sortie_de(jeu, creer_joueur(), difficulte)
            tailles.add(int(sortie.split("(")[1].split()[0]))
        assert tailles == {6, 7, 8, 9}


def test_nouvelle_partie_cree_le_heros_du_mode():
    """Une nouvelle partie utilise les stats du mode choisi."""
    with saisies("Aldric", "3"), patch("main.jeu") as jeu_simule:
        nouvelle_partie()
    joueur, difficulte = jeu_simule.call_args.args
    assert difficulte is DIFFICULTES["3"]
    assert joueur.nom == "Aldric"
    assert joueur.pv_max == difficulte.pv_joueur


def test_heros_charge_garde_ses_stats():
    """Un héros chargé ne prend pas les stats de départ du mode."""
    joueur = creer_joueur(pv=77, attaque=20)
    with patch("main.charger", return_value=joueur), saisies("3"):
        with patch("main.jeu") as jeu_simule:
            partie_chargee()
    assert jeu_simule.call_args.args == (joueur, DIFFICULTES["3"])
    assert (joueur.pv_max, joueur.attaque) == (77, 20)


def test_retour_apres_chargement():
    """Revenir de la difficulté après un chargement ne lance pas de partie."""
    with patch("main.charger", return_value=creer_joueur()), saisies("0"):
        with patch("main.jeu") as jeu_simule:
            partie_chargee()
    assert not jeu_simule.called


def test_chargement_sans_sauvegarde():
    """Sans sauvegarde, la difficulté n'est même pas demandée."""
    with patch("main.charger", return_value=None), patch("main.jeu") as jeu_simule:
        partie_chargee()
    assert not jeu_simule.called


# --- Donjon ---


def test_creer_ennemi_vient_des_modeles():
    """Un ennemi créé vient de MODELES_ENNEMIS."""
    assert creer_ennemi(NEUTRE).nom in [modele[0] for modele in MODELES_ENNEMIS]


def test_butin_grande_potion():
    """Un tirage sous 0.08 donne la grande potion."""
    with hasard(0.05):
        assert creer_butin(NEUTRE).soin == 40


def test_butin_potion_moyenne():
    """Un tirage entre 0.08 et 0.25 donne la potion moyenne."""
    with hasard(0.2):
        assert creer_butin(NEUTRE).soin == 20


def test_butin_petite_potion():
    """Un tirage entre 0.25 et 0.5 donne la petite potion."""
    with hasard(0.4):
        assert creer_butin(NEUTRE).soin == 10


def test_limites_des_tirages_de_potions():
    """Chaque seuil appartient bien à la potion suivante."""
    with hasard(0.08):
        assert creer_butin(NEUTRE).soin == 20
    with hasard(0.25):
        assert creer_butin(NEUTRE).soin == 10
    with hasard(0.5):
        assert creer_butin(NEUTRE) is None


def test_plus_une_potion_soigne_plus_elle_est_rare():
    """Sur beaucoup de tirages : petite plus fréquente que moyenne, elle-même que grande."""
    tirages = [creer_butin(NEUTRE) for _ in range(20000)]
    soins = [butin.soin for butin in tirages if isinstance(butin, Potion)]
    assert soins.count(10) > soins.count(20) > soins.count(40) > 0
    assert 9000 < len(soins) < 11000


def test_butin_vide():
    """Un tirage entre 0.5 et 0.8 ne donne rien."""
    with hasard(0.6):
        assert creer_butin(NEUTRE) is None


def test_butin_arme():
    """Un tirage à partir de 0.8 donne une arme de MODELES_ARMES."""
    with hasard(0.9), patch("random.choices", return_value=[MODELES_ARMES[-1]]):
        arme = creer_butin(NEUTRE)
    assert isinstance(arme, Arme)
    assert arme.nom == MODELES_ARMES[-1][0]


def test_il_y_a_dix_armes_differentes():
    """Il y a 10 armes, toutes avec un nom différent."""
    assert len(MODELES_ARMES) == 10
    assert len({nom for nom, _, _ in MODELES_ARMES}) == 10


def test_plus_une_arme_est_forte_plus_elle_est_rare():
    """Dans la liste, le bonus monte toujours et les chances baissent toujours."""
    bonus = [modele[1] for modele in MODELES_ARMES]
    chances = [modele[2] for modele in MODELES_ARMES]
    assert bonus == sorted(set(bonus))
    assert chances == sorted(set(chances), reverse=True)


def test_les_armes_font_toujours_20_pourcent_du_butin():
    """Les chances des armes, sur 1000 salles, font 200 au total."""
    assert sum(modele[2] for modele in MODELES_ARMES) == 200


def test_la_meilleure_arme_est_tres_rare_et_tres_forte():
    """La meilleure arme tombe 1 fois sur 1000 et bat largement l'avant-dernière."""
    _, bonus, chances = MODELES_ARMES[-1]
    assert chances == 1
    assert bonus >= MODELES_ARMES[-2][1] * 1.5


def test_creer_arme_respecte_son_modele():
    """Chaque modèle donne une arme avec le bon nom et le bon bonus."""
    for modele in MODELES_ARMES:
        with patch("random.choices", return_value=[modele]):
            arme = creer_arme(NEUTRE)
        assert isinstance(arme, Arme)
        assert (arme.nom, arme.bonus) == modele[:2]


def test_frequences_des_armes():
    """Sur beaucoup de tirages, chaque arme tombe plus souvent que la suivante."""
    noms = [creer_arme(NEUTRE).nom for _ in range(200000)]
    totaux = [noms.count(modele[0]) for modele in MODELES_ARMES]
    assert totaux == sorted(totaux, reverse=True)
    assert totaux[-1] > 0


def test_salle_pleine():
    """Avec un petit tirage, la salle a un ennemi, un butin et un piège."""
    with hasard(0.05):
        salle = creer_salle(1, NEUTRE)
    assert salle.ennemi is not None
    assert salle.butin is not None
    assert salle.piege


def test_salle_sans_ennemi_ni_piege():
    """Avec un grand tirage, la salle n'a ni ennemi ni piège."""
    with hasard(0.9):
        salle = creer_salle(1, NEUTRE)
    assert salle.ennemi is None
    assert not salle.piege


def test_salles_numerotees_dans_l_ordre():
    """Les salles sont numérotées à partir de 1."""
    donjon = generer_donjon(5, NEUTRE)
    assert [salle.numero for salle in donjon] == [1, 2, 3, 4, 5]


def test_le_boss_est_seulement_dans_la_derniere_salle():
    """Seule la dernière salle contient un boss."""
    donjon = generer_donjon(5, NEUTRE)
    assert [salle.boss for salle in donjon] == [False, False, False, False, True]


def test_il_y_a_quatre_boss_differents():
    """Il y a 4 boss avec chacun leur nom, leur arme et leurs stats."""
    assert len(MODELES_BOSS) == 4
    assert len({stats[0] for stats, _ in MODELES_BOSS}) == 4
    assert len({arme[0] for _, arme in MODELES_BOSS}) == 4
    assert len({stats[1:3] for stats, _ in MODELES_BOSS}) == 4


def test_le_roi_liche_est_un_boss():
    """Le Roi liche fait partie des boss, avec ses stats d'origine."""
    assert (("Roi liche", 50, 12, 50), ("Epée du roi liche", 10)) in MODELES_BOSS


def test_chaque_boss_a_sa_salle():
    """Chaque modèle donne bien son boss et son arme dans la salle finale."""
    for stats, arme in MODELES_BOSS:
        with patch("random.choice", return_value=(stats, arme)):
            salle = creer_salle_boss([], NEUTRE)
        assert salle.ennemi.nom == stats[0]
        assert salle.ennemi.pv == stats[1]
        assert salle.ennemi.recompense == stats[3]
        assert salle.butin.nom == arme[0]
        assert salle.boss


def test_les_quatre_boss_peuvent_sortir():
    """Sur beaucoup de tirages, les 4 boss apparaissent."""
    noms = {creer_salle_boss([], NEUTRE).ennemi.nom for _ in range(500)}
    assert len(noms) == 4


def test_piege_blesse_le_joueur():
    """Un piège de 8 dégâts, réduit par la défense, retire 6 PV."""
    joueur = creer_joueur()
    with hasard():
        assert declencher_piege(joueur) is True
    assert joueur.pv == 24


def test_piege_mortel():
    """declencher_piege renvoie False si le joueur meurt."""
    joueur = creer_joueur()
    joueur.pv = 5
    with hasard():
        assert declencher_piege(joueur) is False


def test_victoire_rapporte_de_l_or():
    """gagner_or est appelée après une victoire."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        assert affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3)) == "victoire"
    assert joueur.piece == 3


def test_fuite_ne_rapporte_pas_d_or():
    """Fuir ne rapporte rien."""
    joueur = creer_joueur()
    with hasard(0.3), saisies("3", "2"):
        assert affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3)) == "fuite"
    assert joueur.piece == 0


def test_defaite_ne_rapporte_pas_d_or():
    """Perdre ne rapporte rien."""
    joueur = creer_joueur(pv=5, attaque=1)
    with hasard(), saisies("1"):
        assert affronter_ennemi(joueur, Ennemi("Ogre", 100, 50, 7)) == "defaite"
    assert joueur.piece == 0


def test_victoire_rapporte_de_l_xp():
    """Une victoire donne autant d'XP que la récompense en or de l'ennemi."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3))
    assert joueur.xp == 3
    assert joueur.niveau == 1


def test_fuite_ne_rapporte_pas_d_xp():
    """Fuir ne donne pas d'XP."""
    joueur = creer_joueur()
    with hasard(0.3), saisies("3", "2"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3))
    assert joueur.xp == 0


def test_defaite_ne_rapporte_pas_d_xp():
    """Perdre ne donne pas d'XP."""
    joueur = creer_joueur(pv=5, attaque=1)
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Ogre", 100, 50, 7))
    assert joueur.xp == 0


def test_tuer_un_ennemi_peut_faire_monter_de_niveau():
    """Avec assez d'XP, le joueur monte de niveau et l'annonce."""
    joueur = creer_joueur()
    joueur.pv = 1
    with hasard(), saisies("1"):
        sortie = sortie_de(affronter_ennemi, joueur, Ennemi("Rat", 8, 4, 20))
    assert joueur.niveau == 2
    assert joueur.pv == joueur.pv_max
    assert "passe au niveau 2 !" in sortie


def test_pas_d_annonce_sans_montee_de_niveau():
    """Sans montée de niveau, rien n'est annoncé."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        sortie = sortie_de(affronter_ennemi, joueur, Ennemi("Rat", 8, 4, 3))
    assert "passe au niveau" not in sortie


def test_traverser_une_salle_avec_butin():
    """Après la victoire, le butin de la salle est ramassé."""
    joueur = creer_joueur()
    salle = creer_salle(1, NEUTRE)
    salle.ennemi = Ennemi("Rat", 8, 4, 3)
    salle.butin = Potion("Potion", 5)
    salle.piege = False
    with hasard(), saisies("1", "2"):
        assert traverser_salle(joueur, salle) is True
    assert joueur.inventaire == [salle.butin]


def test_explorer_s_arrete_a_la_mort():
    """Le joueur mort ne visite pas les salles suivantes."""
    joueur = creer_joueur(pv=5, attaque=1)
    donjon = generer_donjon(3, NEUTRE)
    for salle in donjon:
        salle.ennemi = Ennemi("Ogre", 100, 50, 0)
        salle.piege = False
    with hasard(), saisies("1"):
        assert explorer(joueur, donjon) is False


def test_explorer_jusqu_au_bout():
    """Un donjon vidé de ses dangers se termine en vie."""
    joueur = creer_joueur()
    donjon = generer_donjon(2, NEUTRE)
    for salle in donjon:
        salle.ennemi = None
        salle.piege = False
    with saisies("2", "2"):
        assert explorer(joueur, donjon) is True


# --- Sauvegarde ---


def test_sauvegarder_puis_charger():
    """Un héros sauvegardé revient à l'identique."""
    joueur = creer_joueur()
    joueur.pv = 12
    joueur.gagner_or(40)
    joueur.gagner_xp(25)
    joueur.ramasser_objet(Potion("Potion", 5))
    joueur.ramasser_objet(Arme("Epée", 3))
    with tempfile.TemporaryDirectory() as dossier:
        with patch("sauvegarde.FICHIER_SAUVEGARDE", os.path.join(dossier, "test.json")):
            sauvegarder(joueur)
            charge = charger()
    assert charge.to_dict() == joueur.to_dict()
    assert isinstance(charge.inventaire[0], Potion)
    assert isinstance(charge.inventaire[1], Arme)


def test_bonus_de_defense_jamais_sauvegarde():
    """Sauvegarder pendant le bonus n'écrit ni le compteur ni la défense doublée."""
    joueur = creer_joueur()
    joueur.tours_defense = 3
    donnees = joueur.to_dict()
    assert "tours_defense" not in donnees
    assert donnees["defense"] == 2


def test_charger_sans_fichier():
    """Sans sauvegarde, charger renvoie None."""
    with tempfile.TemporaryDirectory() as dossier:
        with patch("sauvegarde.FICHIER_SAUVEGARDE", os.path.join(dossier, "absent.json")):
            assert charger() is None


def test_charger_fichier_corrompu():
    """Un fichier illisible (ou vide) renvoie None sans planter."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = os.path.join(dossier, "vide.json")
        with open(chemin, "w", encoding="utf-8"):
            pass
        with patch("sauvegarde.FICHIER_SAUVEGARDE", chemin):
            assert charger() is None


def test_charger_ancienne_sauvegarde_sans_xp():
    """Une sauvegarde d'avant l'XP se charge avec 0 XP."""
    donnees = creer_joueur().to_dict()
    del donnees["xp"]
    with tempfile.TemporaryDirectory() as dossier:
        chemin = os.path.join(dossier, "ancienne.json")
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier)
        with patch("sauvegarde.FICHIER_SAUVEGARDE", chemin):
            assert charger().xp == 0


def lancer_tests():
    """Lance toutes les fonctions test_...() et renvoie le nombre d'échecs."""
    tests = [(nom, objet) for nom, objet in globals().items() if nom.startswith("test_")]
    echecs = 0
    for nom, test in tests:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                test()
            print(f"OK     {nom}")
        except Exception:  # pylint: disable=broad-exception-caught
            echecs += 1
            print(f"ÉCHEC  {nom}\n{traceback.format_exc()}")
    print(f"\n{len(tests) - echecs}/{len(tests)} tests réussis.")
    return echecs


if __name__ == "__main__":
    sys.exit(1 if lancer_tests() else 0)
