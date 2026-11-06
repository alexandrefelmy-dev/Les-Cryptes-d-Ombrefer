"""Tests de classe.py : stats des classes, attaques spéciales et recharge."""

import pytest

from outils import creer_joueur, hasard, saisies

from ombrefer.boutique import afficher_boutique
from ombrefer.classe import (
    Berserker,
    CLASSES,
    classe_par_nom,
    ClasseHeros,
    GROS_BONUS,
    Guerrier,
    Mage,
    MALUS,
    Necromancien,
    Voleur,
)
from ombrefer.combat import action_speciale, choix_combat, combat
from ombrefer.effet import (
    AFFAIBLISSEMENT,
    DEGATS_SAIGNEMENT,
    IMMOBILISATION,
    POISON,
    RAGE,
    SAIGNEMENT,
)
from ombrefer.objet import (
    afficher_equipement,
    afficher_inventaire,
    Arme,
    BATON,
    DAGUE,
    EPEE,
    FAUX,
    HACHE,
)
from ombrefer.personnage import Ennemi, Joueur
from ombrefer.sauvegarde import charger, sauvegarder


def heros(classe, pv=30, attaque=10):
    """Crée un joueur de test avec cette classe."""
    joueur = creer_joueur(pv=pv, attaque=attaque)
    joueur.prendre_classe(classe)
    return joueur


def cible(pv=100):
    """Crée un ennemi sans effet, assez solide pour survivre."""
    return Ennemi("Ogre", pv, 1, 0)


# --- Stats ---


def test_cinq_classes():
    """Le jeu propose le Guerrier, le Voleur, le Mage, le Nécromancien et le Berserker."""
    noms = [classe.nom for classe in CLASSES.values()]
    assert noms == ["Guerrier", "Voleur", "Mage", "Nécromancien", "Berserker"]


def test_chaque_classe_a_ses_propres_stats():
    """Deux classes n'ont jamais les mêmes PV, attaque et recharge."""
    stats = {
        (classe.multiplicateur_pv, classe.bonus_attaque, classe.recharge)
        for classe in CLASSES.values()
    }
    assert len(stats) == len(CLASSES)


@pytest.mark.parametrize("classe", CLASSES.values(), ids=lambda classe: classe.nom)
def test_chaque_classe_a_une_attaque_speciale(classe):
    """Chaque classe a un nom d'attaque, une recharge et une phrase à afficher."""
    assert classe.nom_special and classe.recharge > 0
    assert classe.nom in classe.resume()
    assert classe.attaque_speciale(heros(classe), cible())


def test_classe_de_base_sans_attaque():
    """La classe de base doit être remplacée par une vraie classe."""
    with pytest.raises(NotImplementedError):
        ClasseHeros().attaque_speciale(heros(Guerrier()), cible())


def test_le_voleur_esquive_et_critique_plus():
    """Le Voleur a de meilleures chances de critique et d'esquive."""
    voleur = heros(Voleur())
    normal = Joueur("Aldric", 30, 8)
    assert voleur.chance_critique > normal.chance_critique
    assert voleur.chance_esquive > normal.chance_esquive


def test_l_esquive_suit_la_classe():
    """Un tirage que seul le Voleur esquive ne le blesse pas."""
    voleur = heros(Voleur())
    with hasard(0.12):
        voleur.subir_degats(10)
    assert voleur.pv == 30


def test_le_critique_suit_la_classe():
    """Un tirage qui n'est un critique que pour le Voleur double ses dégâts."""
    with hasard(0.25):
        assert heros(Voleur()).attaquer(cible())[1] is True
        assert heros(Guerrier()).attaquer(cible())[1] is False


# --- Attaques spéciales ---


def test_coup_puissant_double_les_degats():
    """Le Coup puissant double le jet de dégâts."""
    ennemi = cible()
    with hasard():
        Guerrier().attaque_speciale(heros(Guerrier()), ennemi)
    assert ennemi.pv == 80


def test_coup_puissant_sans_petit_jet():
    """Même au pire tirage, le Coup puissant fait au moins l'attaque du héros."""
    ennemi = cible()
    joueur = heros(Guerrier())
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("random.randint", lambda minimum, maximum: minimum)
        Guerrier().attaque_speciale(joueur, ennemi)
    assert ennemi.pv == 90


def test_frappe_sournoise_critique_et_saignement():
    """La Frappe sournoise est un critique et fait toujours saigner."""
    ennemi = cible()
    with hasard():
        Voleur().attaque_speciale(heros(Voleur()), ennemi)
    assert ennemi.pv == 80
    assert SAIGNEMENT in ennemi.effets


def test_eclair_fixe_et_affaiblit():
    """L'Éclair fait toujours les mêmes dégâts et affaiblit l'ennemi."""
    ennemi = cible()
    Mage().attaque_speciale(heros(Mage()), ennemi)
    assert ennemi.pv == 100 - round(10 * Mage.force_eclair)
    assert AFFAIBLISSEMENT in ennemi.effets


def test_drain_de_vie_soigne_le_heros():
    """Le Drain de vie blesse l'ennemi et rend des PV au héros."""
    joueur = heros(Necromancien())
    joueur.pv = 10
    ennemi = cible()
    with hasard():
        Necromancien().attaque_speciale(joueur, ennemi)
    assert ennemi.pv == 90
    assert joueur.pv == 10 + round(10 * Necromancien.part_soin)


def test_rage_renforce_pour_trois_attaques():
    """La Rage dure pour l'attaque qui la lance et les deux suivantes."""
    joueur = heros(Berserker())
    ennemi = cible()
    with hasard():
        Berserker().attaque_speciale(joueur, ennemi)
    assert ennemi.pv == 85
    joueur.passer_un_tour()
    assert joueur.attaque_actuelle() == 15
    joueur.passer_un_tour()
    assert joueur.attaque_actuelle() == 15
    joueur.passer_un_tour()
    assert joueur.attaque_actuelle() == 10


def test_rage_expose_le_heros():
    """En rage, le Berserker encaisse un dégât de plus."""
    joueur = heros(Berserker())
    joueur.recevoir_effet(RAGE)
    with hasard():
        joueur.subir_degats(5)
    assert joueur.pv == 24


def test_rage_et_affaiblissement_se_combinent():
    """Les deux effets s'appliquent à l'attaque."""
    joueur = heros(Berserker())
    joueur.effets.update({RAGE: 2, AFFAIBLISSEMENT: 2})
    assert joueur.attaque_actuelle() == 10


def test_la_rage_s_arrete_avec_le_combat():
    """La Rage ne continue pas après le combat."""
    joueur = heros(Berserker())
    joueur.recevoir_effet(RAGE)
    joueur.fin_de_combat()
    assert not joueur.effets


@pytest.mark.parametrize("effet", [POISON, SAIGNEMENT, IMMOBILISATION, AFFAIBLISSEMENT])
def test_la_rage_bloque_les_nouveaux_effets(effet):
    """En rage, aucun nouvel effet ne touche le Berserker."""
    joueur = heros(Berserker())
    joueur.recevoir_effet(RAGE)
    assert not joueur.recevoir_effet(effet)
    assert effet not in joueur.effets


def test_la_rage_ne_guerit_pas_les_effets_deja_subis():
    """Comme la garde, la Rage laisse en place les effets déjà subis."""
    joueur = heros(Berserker())
    joueur.recevoir_effet(POISON)
    joueur.recevoir_effet(RAGE)
    assert POISON in joueur.effets


def test_les_effets_touchent_de_nouveau_apres_la_rage():
    """La protection s'arrête avec la Rage."""
    joueur = heros(Berserker())
    joueur.recevoir_effet(RAGE)
    joueur.fin_de_combat()
    assert joueur.recevoir_effet(POISON)


# --- Dans le combat ---


def test_le_berserker_ne_peut_pas_se_defendre(capsys):
    """Le Berserker n'a pas l'option 4, qui est refusée."""
    with saisies("4", "1"):
        assert choix_combat(heros(Berserker())) == "1"
    sortie = capsys.readouterr().out
    assert "Se défendre" not in sortie
    assert "Réponse invalide." in sortie


def test_sans_classe_pas_d_option_5():
    """Sans classe, le choix 5 n'existe pas."""
    with saisies("5", "1"):
        assert choix_combat(creer_joueur()) == "1"


def test_menu_indique_la_recharge(capsys):
    """Le menu dit si l'attaque est prête, ou dans combien de tours."""
    joueur = heros(Guerrier())
    with saisies("1"):
        choix_combat(joueur)
    assert "5. Coup puissant (prête)" in capsys.readouterr().out
    joueur.recharge_speciale = 4
    with saisies("1"):
        choix_combat(joueur)
    assert "5. Coup puissant (dans 4 tours)" in capsys.readouterr().out


def test_action_speciale_lance_la_recharge():
    """Utiliser l'attaque lance sa recharge, puis l'ennemi riposte."""
    joueur = heros(Guerrier())
    with hasard():
        assert action_speciale(joueur, Ennemi("Ogre", 100, 4, 0)) is None
    assert joueur.recharge_speciale == Guerrier.recharge
    assert joueur.pv == 26


def test_speciale_pas_prete_ne_perd_pas_le_tour(capsys):
    """Une attaque en recharge est refusée, sans riposte de l'ennemi."""
    joueur = heros(Guerrier())
    joueur.recharge_speciale = 2
    assert action_speciale(joueur, Ennemi("Ogre", 100, 4, 0)) == "annule"
    assert joueur.pv == 30
    assert "pas prête" in capsys.readouterr().out


def test_speciale_mortelle_donne_la_victoire():
    """Un ennemi tué par l'attaque spéciale ne riposte pas."""
    joueur = heros(Guerrier())
    with hasard(), saisies("5"):
        assert combat(joueur, Ennemi("Rat", 5, 50, 3)) == "victoire"
    assert joueur.pv == 30


def test_la_recharge_compte_les_tours_de_combat():
    """L'attaque redevient prête après le nombre de tours de sa classe."""
    joueur = heros(Necromancien(), pv=100, attaque=1)
    with hasard(), saisies("5", "1", "1", "5"):
        combat(joueur, Ennemi("Ogre", 4, 1, 0))
    assert joueur.recharge_speciale == Necromancien.recharge


def test_la_recharge_continue_d_un_combat_a_l_autre():
    """Finir un combat ne recharge pas l'attaque d'un coup."""
    joueur = heros(Guerrier())
    with hasard(), saisies("5"):
        combat(joueur, Ennemi("Rat", 5, 1, 3))
    assert joueur.recharge_speciale == Guerrier.recharge
    with hasard(), saisies("1"):
        combat(joueur, Ennemi("Rat", 5, 1, 3))
    assert joueur.recharge_speciale == Guerrier.recharge - 1


def test_le_repos_remet_la_recharge_a_zero():
    """Le repos entre deux niveaux rend l'attaque spéciale."""
    joueur = heros(Guerrier())
    joueur.recharge_speciale = 4
    joueur.finir_niveau_donjon()
    assert joueur.recharge_speciale == 0


def test_le_saignement_touche_l_attaque_speciale():
    """Une attaque spéciale reste une attaque : le héros saigne."""
    joueur = heros(Guerrier())
    joueur.recevoir_effet(SAIGNEMENT)
    with hasard():
        action_speciale(joueur, cible())
    assert joueur.pv == 30 - DEGATS_SAIGNEMENT - 1


def test_mourir_du_saignement_annule_l_attaque_speciale():
    """Un héros qui meurt en saignant ne porte pas son attaque."""
    joueur = heros(Guerrier(), pv=DEGATS_SAIGNEMENT)
    joueur.recevoir_effet(SAIGNEMENT)
    ennemi = cible()
    with hasard(), saisies("5"):
        assert combat(joueur, ennemi) == "defaite"
    assert ennemi.pv == 100


# --- Affinités avec les armes ---


def test_gros_bonus_de_classe():
    """Une arme de la bonne famille vaut bien plus que son bonus."""
    assert Arme("Bâton", 10, None, BATON).bonus_pour(Mage()) == 15


def test_malus_de_classe():
    """Une arme de la mauvaise famille vaut bien moins que son bonus."""
    assert Arme("Bâton", 10, None, BATON).bonus_pour(Guerrier()) == 5


def test_arme_neutre_pour_la_classe():
    """Une arme neutre garde son bonus."""
    assert Arme("Faux", 10, None, FAUX).bonus_pour(Guerrier()) == 10


def test_une_arme_differe_selon_la_classe():
    """La même arme peut être un bonus, un malus ou neutre selon la classe."""
    hache = Arme("Hache", 10, None, HACHE)
    assert hache.bonus_pour(Berserker()) == 15
    assert hache.bonus_pour(Mage()) == 5
    assert hache.bonus_pour(Guerrier()) == 10


def test_malus_laisse_au_moins_un_point():
    """Même avec un malus, une arme ajoute au moins 1 point."""
    assert Arme("Dague", 1, None, DAGUE).bonus_pour(Guerrier()) == 1


def test_sans_classe_pas_d_affinite():
    """Sans classe, une arme garde son bonus."""
    assert Arme("Bâton", 10, None, BATON).bonus_pour(None) == 10


@pytest.mark.parametrize("classe", CLASSES.values(), ids=lambda classe: classe.nom)
def test_chaque_classe_a_une_famille_favorite(classe):
    """Chaque classe a exactement une famille à gros bonus, et des malus."""
    valeurs = list(classe.affinites.values())
    assert valeurs.count(GROS_BONUS) == 1
    assert valeurs.count(MALUS) == 2


def test_familles_favorites_differentes():
    """Deux classes n'ont jamais la même famille favorite."""
    favorites = [
        next(famille for famille, valeur in classe.affinites.items() if valeur == GROS_BONUS)
        for classe in CLASSES.values()
    ]
    assert len(set(favorites)) == len(CLASSES)


def test_equiper_applique_l_affinite():
    """L'attaque du héros augmente de la valeur réelle de l'arme."""
    joueur = heros(Mage())
    Arme("Bâton", 10, None, BATON).utiliser(joueur)
    assert joueur.attaque == 25


def test_changer_d_arme_retire_la_valeur_reelle():
    """Changer d'arme retire la valeur réelle de l'ancienne, pas son bonus affiché."""
    joueur = heros(Mage())
    Arme("Bâton", 10, None, BATON).utiliser(joueur)
    Arme("Epée", 10, None, EPEE).utiliser(joueur)
    assert joueur.attaque == 15
    joueur.utiliser_objet(0)
    assert joueur.attaque == 25


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_affinite_gardee_apres_chargement():
    """Après un chargement, changer d'arme garde une attaque juste."""
    joueur = heros(Mage())
    Arme("Bâton", 10, None, BATON).utiliser(joueur)
    sauvegarder(joueur)
    charge = charger()
    assert charge.attaque == 25
    Arme("Lance", 1).utiliser(charge)
    assert charge.attaque == 11


def test_texte_montre_le_bonus_de_classe():
    """Le texte de l'arme indique sa vraie valeur pour le héros."""
    arme = Arme("Bâton", 10, None, BATON)
    assert "+15 attaque pour toi (bonus de classe)" in arme.texte_pour(heros(Mage()))
    assert "+5 attaque pour toi (malus de classe)" in arme.texte_pour(heros(Guerrier()))
    assert "pour toi" not in arme.texte_pour(heros(Necromancien()))


def test_inventaire_et_boutique_montrent_la_vraie_valeur(capsys):
    """Le joueur voit la valeur réelle dans l'inventaire et à la boutique."""
    joueur = heros(Mage())
    arme = Arme("Bâton", 10, None, BATON)
    joueur.ramasser_objet(arme)
    afficher_inventaire(joueur)
    afficher_boutique(joueur, [arme])
    assert capsys.readouterr().out.count("+15 attaque pour toi") == 2


def test_equipement_montre_la_vraie_valeur(capsys):
    """L'équipement porté affiche sa valeur réelle."""
    joueur = heros(Mage())
    Arme("Bâton", 10, None, BATON).utiliser(joueur)
    afficher_equipement(joueur)
    assert "+15 attaque pour toi" in capsys.readouterr().out


def test_le_prix_ne_depend_pas_de_la_classe():
    """Le prix suit le bonus de base : une arme de sa classe est une bonne affaire."""
    assert Arme("Bâton", 10, None, BATON).prix() == Arme("Lance", 10).prix()


# --- Sauvegarde ---


@pytest.mark.usefixtures("fichier_sauvegarde")
def test_classe_sauvegardee():
    """La classe revient au chargement, avec ses chances, sans cumuler ses stats."""
    joueur = heros(Voleur(), attaque=9)
    sauvegarder(joueur)
    charge = charger()
    assert charge.classe.nom == "Voleur"
    assert charge.chance_critique == Voleur.chance_critique
    assert charge.chance_esquive == Voleur.chance_esquive
    assert charge.attaque == 9


def test_classe_par_nom():
    """Une classe se retrouve par son nom, et un nom inconnu ne donne rien."""
    assert isinstance(classe_par_nom("Mage"), Mage)
    assert classe_par_nom("Barde") is None
