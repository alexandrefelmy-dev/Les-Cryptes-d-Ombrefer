"""Tests de donjon.py : modes de difficulté, génération des salles et exploration."""

from unittest.mock import patch

import pytest

from outils import (
    chaque_mode,
    creer_joueur,
    donjon_sans_danger,
    hasard,
    joueur_avec_potion,
    NEUTRE,
    saisies,
)

from ombrefer.donjon import (
    adapter_au_niveau,
    affronter_ennemi,
    ajuster,
    creer_arme,
    creer_butin,
    creer_ennemi,
    creer_salle,
    creer_salle_boss,
    declencher_piege,
    Difficulte,
    DIFFICULTES,
    effacer_ecran,
    explorer,
    FORCE_PAR_NIVEAU,
    generer_donjon,
    MODELES_ARMES,
    MODELES_BOSS,
    MODELES_ENNEMIS,
    pause,
    traverser_salle,
)
from ombrefer.objet import Arme, Potion
from ombrefer.personnage import Ennemi


# --- Option 0 (retour) ---


def test_retour_de_la_pause():
    """Revenir du choix d'objet ramène à la pause, sans utiliser l'objet."""
    joueur = joueur_avec_potion()
    with saisies("1", "0", "2"):
        pause(joueur)
    assert len(joueur.inventaire) == 1


# --- Difficulté ---


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


@chaque_mode
def test_ordre_de_rarete_des_armes_dans_tous_les_modes(difficulte):
    """Dans chaque mode, chaque arme reste plus fréquente que la suivante."""
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


@chaque_mode
def test_boss_possibles_selon_le_mode(difficulte):
    """Sur beaucoup de tirages, seuls les boss autorisés sortent."""
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


@pytest.mark.parametrize("modele", MODELES_ARMES, ids=lambda modele: modele[0])
def test_creer_arme_respecte_son_modele(modele):
    """Chaque modèle donne une arme avec le bon nom et le bon bonus."""
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


@pytest.mark.parametrize("stats, arme", MODELES_BOSS, ids=[boss[0][0] for boss in MODELES_BOSS])
def test_chaque_boss_a_sa_salle(stats, arme):
    """Chaque modèle donne bien son boss et son arme dans la salle finale."""
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


def test_statut_affiche_apres_une_montee_de_niveau(capsys):
    """Après la montée de niveau, le statut complet du héros est affiché."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 20))
    sortie = capsys.readouterr().out
    assert "Aldric (PV : 35/35) | Niveau 2 | Or : 20" in sortie


def test_statut_pas_affiche_sans_montee_de_niveau(capsys):
    """Sans montée de niveau, le statut n'est pas répété après le combat."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3))
    sortie = capsys.readouterr().out
    assert "Niveau 1 | Or : 3" not in sortie


def test_fin_de_salle_aeree(capsys):
    """Victoire, niveau, butin et menu sont séparés par une ligne vide."""
    joueur = creer_joueur()
    salle = creer_salle(1, NEUTRE)
    salle.ennemi = Ennemi("Rat", 8, 4, 20)
    salle.butin = Potion("Potion", 5)
    salle.piege = False
    with hasard(), saisies("1", "2"):
        traverser_salle(joueur, salle)
    sortie = capsys.readouterr().out
    for texte in ("Rat est vaincu", "Aldric passe au niveau", "Aldric trouve", "1. Utiliser"):
        assert f"\n\n{texte}" in sortie


def test_fuite_aeree(capsys):
    """La fuite et le menu de pause sont séparés du combat par une ligne vide."""
    joueur = creer_joueur()
    with hasard(0.3), saisies("3", "2"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3))
    sortie = capsys.readouterr().out
    assert "\n\nAldric s'enfuit" in sortie
    assert "\n\n1. Utiliser" in sortie


def test_tuer_un_ennemi_peut_faire_monter_de_niveau(capsys):
    """Avec assez d'XP, le joueur monte de niveau et l'annonce."""
    joueur = creer_joueur()
    joueur.pv = 1
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 20))
    sortie = capsys.readouterr().out
    assert joueur.niveau == 2
    assert joueur.pv == joueur.pv_max
    assert "passe au niveau 2 !" in sortie


def test_pas_d_annonce_sans_montee_de_niveau(capsys):
    """Sans montée de niveau, rien n'est annoncé."""
    joueur = creer_joueur()
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Rat", 8, 4, 3))
    sortie = capsys.readouterr().out
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


def test_ecran_efface_entre_les_salles_seulement():
    """Avec 3 salles, l'écran est effacé 2 fois : pas avant la première."""
    with saisies("2", "2", "2"), patch("ombrefer.donjon.effacer_ecran") as effacer:
        explorer(creer_joueur(), donjon_sans_danger(3))
    assert effacer.call_count == 2


def test_ecran_efface_apres_la_pause():
    """Le texte d'une salle reste affiché tant que le joueur n'a pas quitté la pause."""
    appels = []
    with patch("ombrefer.donjon.effacer_ecran", side_effect=lambda: appels.append("efface")):
        with patch("ombrefer.donjon.pause", side_effect=lambda joueur: appels.append("pause")):
            explorer(creer_joueur(), donjon_sans_danger(2))
    assert appels == ["pause", "efface", "pause"]


def test_ecran_pas_efface_apres_la_mort():
    """Le message de défaite reste affiché : aucune salle suivante, aucun effacement."""
    joueur = creer_joueur(pv=5, attaque=1)
    donjon = donjon_sans_danger(3)
    donjon[0].ennemi = Ennemi("Ogre", 100, 50, 0)
    with hasard(), saisies("1"), patch("ombrefer.donjon.effacer_ecran") as effacer:
        explorer(joueur, donjon)
    assert not effacer.called


def test_effacer_ecran_dans_un_vrai_terminal():
    """Dans un vrai terminal, la commande d'effacement est lancée."""
    with patch("sys.stdout") as sortie, patch("os.system") as commande:
        sortie.isatty.return_value = True
        effacer_ecran()
    assert commande.call_count == 1


def test_effacer_ecran_sans_terminal():
    """Hors terminal (tests, fichier), aucune commande n'est lancée."""
    with patch("sys.stdout") as sortie, patch("os.system") as commande:
        sortie.isatty.return_value = False
        effacer_ecran()
    assert not commande.called


def test_explorer_jusqu_au_bout():
    """Un donjon vidé de ses dangers se termine en vie."""
    joueur = creer_joueur()
    donjon = generer_donjon(2, NEUTRE)
    for salle in donjon:
        salle.ennemi = None
        salle.piege = False
    with saisies("2", "2"):
        assert explorer(joueur, donjon) is True
