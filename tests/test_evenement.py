"""Tests de evenement.py : chaque choix, ses issues, et leur place dans le donjon."""

from unittest.mock import patch

import pytest

from outils import NEUTRE, creer_joueur, hasard, saisies

from ombrefer.classe import CLASSES
from ombrefer.donjon import (
    CHANCE_BOUTIQUE,
    CHANCE_EVENEMENT,
    Salle,
    affronter_ennemi,
    creer_evenement,
    creer_salle,
    creer_salle_boss,
    pause,
    traverser_salle,
)
from ombrefer.effet import AFFAIBLISSEMENT, POISON, SAIGNEMENT
from ombrefer.evenement import (
    AutelMaudit,
    CoffrePiege,
    Fontaine,
    Forge,
    Prisonnier,
    blesser,
    renfort_allie,
    vivre_evenement,
)
from ombrefer.objet import Arme, Armure, Potion
from ombrefer.personnage import Ennemi
from ombrefer.sauvegarde import charger, sauvegarder


def joueur_blesse(pv=10):
    """Crée un joueur à 30 PV max, blessé."""
    joueur = creer_joueur()
    joueur.pv = pv
    return joueur


def joueur_equipe(bonus_arme=20, bonus_armure=3, or_du_joueur=100):
    """Crée un joueur riche qui porte une arme et une armure."""
    joueur = creer_joueur()
    joueur.equiper_arme(Arme("Epée", bonus_arme))
    joueur.equiper_armure(Armure("Cotte", bonus_armure))
    joueur.gagner_or(or_du_joueur)
    return joueur


# --- Règles communes ---


def test_blesser_ne_tue_jamais():
    """Une perte de PV d'événement s'arrête à 1 PV."""
    joueur = joueur_blesse(3)
    assert blesser(joueur, 0.5) == 2
    assert joueur.pv == 1


def test_les_chances_ne_sont_pas_affichees(capsys):
    """Le menu d'un événement donne des indices, jamais de pourcentage."""
    for evenement in (Fontaine(), AutelMaudit(), CoffrePiege(Potion("P", 5)), Prisonnier()):
        with saisies("0"):
            vivre_evenement(creer_joueur(), evenement)
    assert "%" not in capsys.readouterr().out


def test_retour_ne_consomme_pas_l_evenement():
    """Le choix 0 revient à la pause, sans rien changer."""
    joueur = joueur_blesse()
    with saisies("0"):
        assert vivre_evenement(joueur, Fontaine()) is False
    assert joueur.pv == 10
    assert not joueur.inventaire


def test_numero_invalide_redemande(capsys):
    """Un mauvais numéro est refusé, puis le joueur peut choisir."""
    joueur = creer_joueur()
    with saisies("9", "2"):
        assert vivre_evenement(joueur, Fontaine()) is True
    assert "Numéro invalide." in capsys.readouterr().out
    assert len(joueur.inventaire) == 1


# --- Fontaine ---


def test_fontaine_soigne_et_guerit():
    """L'eau pure rend 40 % des PV max et retire tous les effets."""
    joueur = joueur_blesse()
    joueur.effets = {POISON: 2, SAIGNEMENT: 2}
    with hasard(Fontaine.chance_soin - 0.01):
        Fontaine().boire(joueur)
    assert joueur.pv == 22
    assert not joueur.effets


def test_fontaine_sans_effet():
    """Entre les deux tirages, l'eau ne fait rien."""
    joueur = joueur_blesse()
    with hasard(Fontaine.chance_soin):
        Fontaine().boire(joueur)
    assert joueur.pv == 10
    assert not joueur.effets


def test_fontaine_viciee():
    """L'eau viciée retire 15 % des PV max et empoisonne."""
    joueur = joueur_blesse()
    with hasard(Fontaine.chance_soin + Fontaine.chance_rien):
        Fontaine().boire(joueur)
    assert joueur.pv == 6  # round(4,5) arrondit vers le pair
    assert POISON in joueur.effets


def test_fiole_donne_une_petite_potion():
    """La fiole est sûre et donne une potion de 10 PV."""
    joueur = creer_joueur()
    Fontaine().remplir_fiole(joueur)
    assert joueur.inventaire[0].soin == 10


# --- Autel maudit ---


def test_sang_echange_des_pv_contre_de_l_attaque():
    """Offrir son sang coûte 20 % des PV max et donne 6 % d'attaque."""
    joueur = creer_joueur(attaque=50)
    AutelMaudit().offrir_sang(joueur)
    assert joueur.pv == 24
    assert joueur.attaque == 53


def test_sang_donne_au_moins_un_point():
    """Même avec peu d'attaque, le sacrifice rapporte quelque chose."""
    joueur = creer_joueur(attaque=8)
    AutelMaudit().offrir_sang(joueur)
    assert joueur.attaque == 9


def test_sang_refuse_si_le_heros_est_trop_faible():
    """Sans assez de PV pour payer, seul le pacte est proposé."""
    autel = AutelMaudit()
    assert len(autel.options(joueur_blesse(7))) == 2
    assert len(autel.options(joueur_blesse(6))) == 1


def test_pacte_reussi_puis_fin_du_niveau():
    """Un pacte réussi donne 25 % d'attaque jusqu'à la fin du niveau."""
    joueur = creer_joueur(attaque=40)
    with hasard(AutelMaudit.chance_pacte - 0.01):
        AutelMaudit().sceller_pacte(joueur)
    assert joueur.attaque == 50
    joueur.finir_niveau_donjon()
    assert joueur.attaque == 40


def test_pacte_rate_puis_fin_du_niveau():
    """Un pacte raté retire 15 % d'attaque jusqu'à la fin du niveau."""
    joueur = creer_joueur(attaque=40)
    with hasard(AutelMaudit.chance_pacte):
        AutelMaudit().sceller_pacte(joueur)
    assert joueur.attaque == 34
    joueur.finir_niveau_donjon()
    assert joueur.attaque == 40


def test_pacte_survit_au_changement_d_arme():
    """Changer d'arme pendant le pacte ne fausse pas l'attaque rendue ensuite."""
    joueur = creer_joueur(attaque=40)
    with hasard(0):
        AutelMaudit().sceller_pacte(joueur)
    joueur.equiper_arme(Arme("Epée", 5))
    joueur.finir_niveau_donjon()
    assert joueur.attaque == 45


def test_pacte_non_sauvegarde(fichier_sauvegarde):  # pylint: disable=unused-argument
    """La sauvegarde a lieu après la fin du niveau : le pacte n'y entre pas."""
    joueur = creer_joueur(attaque=40)
    joueur.prendre_classe(CLASSES["1"])
    with hasard(0):
        AutelMaudit().sceller_pacte(joueur)
    joueur.finir_niveau_donjon()
    sauvegarder(joueur)
    assert charger().attaque == 40


# --- Coffre piégé ---


def test_forcer_donne_l_objet():
    """Le coffre forcé donne l'objet qu'il cache."""
    joueur = creer_joueur()
    arme = Arme("Epée", 3)
    with hasard(CoffrePiege.chance_forcer - 0.01):
        CoffrePiege(arme).forcer(joueur)
    assert joueur.inventaire == [arme]
    assert joueur.pv == 30


def test_forcer_rate_declenche_le_gros_piege():
    """L'échec retire 25 % des PV max et empoisonne, sans donner l'objet."""
    joueur = creer_joueur(pv=40)
    with hasard(CoffrePiege.chance_forcer):
        CoffrePiege(Arme("Epée", 3)).forcer(joueur)
    assert joueur.pv == 30
    assert POISON in joueur.effets
    assert not joueur.inventaire


def test_le_voleur_force_mieux_les_coffres():
    """Le tirage qui fait échouer les autres classes réussit pour le Voleur."""
    tirage = CoffrePiege.chance_forcer + 0.1
    for numero, classe in CLASSES.items():
        joueur = creer_joueur()
        joueur.prendre_classe(classe)
        with hasard(tirage):
            CoffrePiege(Arme("Epée", 3)).forcer(joueur)
        assert bool(joueur.inventaire) is (numero == "2")


def test_crocheter_donne_de_l_or_selon_le_niveau():
    """L'or du coffre suit le niveau du donjon."""
    joueur = creer_joueur()
    joueur.niveau_donjon = 3
    with hasard(CoffrePiege.chance_crocheter - 0.01):
        CoffrePiege(Arme("Epée", 3)).crocheter(joueur)
    assert joueur.piece == 60


def test_crocheter_rate_declenche_le_petit_piege():
    """L'échec retire 10 % des PV max et empoisonne, sans or."""
    joueur = creer_joueur()
    with hasard(CoffrePiege.chance_crocheter):
        CoffrePiege(Arme("Epée", 3)).crocheter(joueur)
    assert joueur.pv == 27
    assert POISON in joueur.effets
    assert joueur.piece == 0


def test_l_armure_protege_du_poison_du_piege(capsys):
    """Une armure contre le poison le bloque, mais pas la perte de PV."""
    joueur = creer_joueur()
    joueur.equiper_armure(Armure("Cuir", 1, POISON))
    with hasard(CoffrePiege.chance_crocheter):
        CoffrePiege(Arme("Epée", 3)).crocheter(joueur)
    assert POISON not in joueur.effets
    assert joueur.pv < 30
    assert f"résiste : {POISON}" in capsys.readouterr().out


# --- Prisonnier ---


def test_liberer_donne_un_allie():
    """Une fois sur deux, le prisonnier promet son aide."""
    joueur = creer_joueur()
    with hasard(Prisonnier.chance_allie - 0.01):
        Prisonnier().liberer(joueur)
    assert joueur.allie is True


def test_liberer_sans_suite():
    """Le prisonnier peut s'enfuir sans rien faire."""
    joueur = creer_joueur()
    joueur.gagner_or(100)
    with hasard(Prisonnier.chance_allie):
        Prisonnier().liberer(joueur)
    assert joueur.allie is False
    assert joueur.piece == 100


def test_liberer_un_voleur():
    """Le prisonnier peut voler 25 % de l'or."""
    joueur = creer_joueur()
    joueur.gagner_or(100)
    with hasard(Prisonnier.chance_allie + Prisonnier.chance_fuite):
        Prisonnier().liberer(joueur)
    assert joueur.allie is False
    assert joueur.piece == 75


def test_depouiller_sans_malediction():
    """Sa bourse rapporte de l'or selon le niveau du donjon."""
    joueur = creer_joueur()
    joueur.niveau_donjon = 2
    with hasard(Prisonnier.chance_malediction):
        Prisonnier().depouiller(joueur)
    assert joueur.piece == 40
    assert not joueur.effets


def test_depouiller_avec_malediction():
    """Le prisonnier peut maudire le voleur : l'or est quand même pris."""
    joueur = creer_joueur()
    with hasard(Prisonnier.chance_malediction - 0.01):
        Prisonnier().depouiller(joueur)
    assert joueur.piece == 20
    assert AFFAIBLISSEMENT in joueur.effets


def test_l_allie_entame_le_boss_une_seule_fois():
    """L'allié retire 15 % des PV max du boss, puis disparaît."""
    joueur = creer_joueur()
    joueur.allie = True
    boss = Ennemi("Golem", 100, 8, 40)
    renfort_allie(joueur, boss)
    assert boss.pv == 85
    assert joueur.allie is False
    renfort_allie(joueur, boss)
    assert boss.pv == 85


def test_l_allie_attend_le_boss(capsys):
    """Un ennemi normal ne fait pas venir l'allié, le boss si."""
    joueur = creer_joueur(attaque=500)
    joueur.allie = True
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Rat", 6, 4, 3))
    assert joueur.allie is True
    with hasard(), saisies("1"):
        affronter_ennemi(joueur, Ennemi("Golem", 100, 8, 40), boss=True)
    assert joueur.allie is False
    assert "Le prisonnier libéré surgit" in capsys.readouterr().out


def test_l_allie_ne_suit_pas_au_niveau_suivant():
    """La promesse du prisonnier ne vaut que pour le niveau en cours."""
    joueur = creer_joueur()
    joueur.allie = True
    joueur.finir_niveau_donjon()
    assert joueur.allie is False


# --- Forge abandonnée ---


def test_forge_refuse_sans_or_ou_sans_equipement(capsys):
    """Sans moyens, la forge explique le prix et ne consomme pas l'événement."""
    assert vivre_evenement(joueur_equipe(or_du_joueur=14), Forge()) is False
    assert vivre_evenement(creer_joueur(), Forge()) is False
    assert "15 pièces d'or" in capsys.readouterr().out


def test_forge_ne_propose_que_l_equipement_porte():
    """Sans armure, seule l'arme peut être reforgée."""
    joueur = creer_joueur()
    joueur.equiper_arme(Arme("Epée", 8))
    joueur.gagner_or(15)
    assert [texte.split(" (")[0] for texte, _ in Forge().options(joueur)] == ["Reforger Epée"]


def test_forge_arme_reussie():
    """La réussite ajoute 25 % du bonus, paie et met l'attaque à jour."""
    joueur = joueur_equipe()
    joueur.niveau_donjon = 2
    with hasard(Forge.chance_arme - 0.01):
        Forge().reforger_arme(joueur)
    assert joueur.arme.bonus == 25
    assert joueur.attaque == 33
    assert joueur.piece == 70


def test_forge_arme_gagne_au_moins_deux():
    """Une petite arme gagne quand même 2 points."""
    joueur = joueur_equipe(bonus_arme=2)
    with hasard(0):
        Forge().reforger_arme(joueur)
    assert joueur.arme.bonus == 4


def test_forge_arme_intacte_coute_quand_meme():
    """Le métal peut rester tel quel, et l'or est perdu."""
    joueur = joueur_equipe()
    with hasard(Forge.chance_arme):
        Forge().reforger_arme(joueur)
    assert joueur.arme.bonus == 20
    assert joueur.piece == 85


def test_forge_arme_abimee():
    """L'échec retire 15 % du bonus."""
    joueur = joueur_equipe()
    with hasard(Forge.chance_arme + Forge.chance_arme_intacte):
        Forge().reforger_arme(joueur)
    assert joueur.arme.bonus == 17
    assert joueur.attaque == 25


def test_forge_arme_suit_l_affinite_de_la_classe():
    """L'attaque du héros change selon le bonus réel de l'arme pour sa classe."""
    joueur = creer_joueur()
    joueur.prendre_classe(CLASSES["1"])  # gros bonus à l'épée : ×1,5
    joueur.equiper_arme(Arme("Epée", 20, famille="Épée"))
    assert joueur.attaque == 38
    joueur.renforcer_arme(4)
    assert joueur.attaque == 44


def test_forge_armure_reussie():
    """La réussite ajoute 1 de défense."""
    joueur = joueur_equipe()
    with hasard(Forge.chance_armure - 0.01):
        Forge().reforger_armure(joueur)
    assert joueur.armure.bonus == 4
    assert joueur.defense == 4


def test_forge_armure_intacte():
    """Le métal peut rester tel quel."""
    joueur = joueur_equipe()
    with hasard(Forge.chance_armure):
        Forge().reforger_armure(joueur)
    assert joueur.defense == 3


def test_forge_armure_abimee_mais_jamais_sous_un():
    """L'échec retire 1 de défense, sans passer sous 1."""
    joueur = joueur_equipe(bonus_armure=2)
    tirage = Forge.chance_armure + Forge.chance_armure_intacte
    with hasard(tirage):
        Forge().reforger_armure(joueur)
    assert joueur.defense == 1
    with hasard(tirage):
        Forge().reforger_armure(joueur)
    assert joueur.defense == 1


def test_arme_reforgee_sauvegardee(fichier_sauvegarde):  # pylint: disable=unused-argument
    """Le progrès de la forge est permanent."""
    joueur = joueur_equipe()
    joueur.prendre_classe(CLASSES["1"])
    with hasard(0):
        Forge().reforger_arme(joueur)
    sauvegarder(joueur)
    assert charger().arme.bonus == 25


# --- Place dans le donjon ---


def test_tirage_de_la_sortie_d_une_salle():
    """Le tirage donne un marchand, un événement ou rien, jamais les deux."""
    with hasard(CHANCE_BOUTIQUE - 0.01):
        salle = creer_salle(1, NEUTRE)
    assert salle.boutique is not None and salle.evenement is None
    with hasard(CHANCE_BOUTIQUE):
        salle = creer_salle(1, NEUTRE)
    assert salle.boutique is None and salle.evenement is not None
    with hasard(CHANCE_BOUTIQUE + CHANCE_EVENEMENT):
        salle = creer_salle(1, NEUTRE)
    assert salle.boutique is None and salle.evenement is None


def test_les_evenements_restent_plus_rares_que_le_marchand():
    """Le marchand reste bien plus fréquent que les autres événements."""
    assert CHANCE_EVENEMENT < CHANCE_BOUTIQUE / 2


def test_les_cinq_evenements_peuvent_sortir():
    """Chaque événement a sa chance, et le coffre cache une arme ou une armure."""
    tires = [creer_evenement(NEUTRE) for _ in range(300)]
    assert {type(evenement) for evenement in tires} == {
        Fontaine, AutelMaudit, CoffrePiege, Prisonnier, Forge,
    }
    coffres = [evenement for evenement in tires if isinstance(evenement, CoffrePiege)]
    assert all(isinstance(coffre.butin, (Arme, Armure)) for coffre in coffres)


def test_pas_d_evenement_apres_le_boss():
    """Le repos suit le boss : aucun événement n'attend à sa sortie."""
    assert creer_salle_boss([], NEUTRE).evenement is None


def test_pause_annonce_l_evenement(capsys):
    """La pause annonce l'événement et le propose comme choix 3."""
    with saisies("2"):
        pause(creer_joueur(), evenement=Fontaine())
    sortie = capsys.readouterr().out
    assert Fontaine.annonce in sortie
    assert f"3. {Fontaine.action}" in sortie


def test_l_evenement_disparait_apres_un_choix(capsys):
    """Une fois le choix fait, l'événement n'est plus proposé."""
    joueur = creer_joueur()
    with saisies("3", "2", "3", "2"):
        pause(joueur, evenement=Fontaine())
    assert len(joueur.inventaire) == 1
    assert "Choix invalide." in capsys.readouterr().out


def test_on_peut_se_soigner_avant_de_decider():
    """Après un retour, l'événement reste là : on peut boire une potion puis revenir."""
    joueur = joueur_blesse()
    joueur.ramasser_objet(Potion("Potion", 5))
    with saisies("3", "0", "1", "1", "3", "2", "2"):
        pause(joueur, evenement=Fontaine())
    assert joueur.pv == 15
    assert [objet.soin for objet in joueur.inventaire] == [10]


def test_evenement_apres_une_salle_gagnee():
    """Le joueur retrouve l'événement à la sortie d'une salle normale."""
    joueur = creer_joueur()
    salle = Salle(1, None, None, False, evenement=Fontaine())
    with saisies("3", "2", "2"):
        assert traverser_salle(joueur, salle) is True
    assert len(joueur.inventaire) == 1


def test_evenement_apres_une_fuite(capsys):
    """Comme la boutique, l'événement reste proposé après une fuite."""
    salle = Salle(1, Ennemi("Rat", 8, 4, 3), None, False, evenement=Fontaine())
    with hasard(0.3), saisies("3", "2"):
        assert traverser_salle(creer_joueur(), salle) is True
    assert f"3. {Fontaine.action}" in capsys.readouterr().out


@pytest.mark.parametrize("attribut", ["boire", "remplir_fiole"])
def test_les_options_de_la_fontaine_sont_jouables(attribut):
    """Le menu appelle bien la méthode de l'option choisie."""
    fontaine = Fontaine()
    numero = "1" if attribut == "boire" else "2"
    with patch.object(fontaine, attribut) as methode, saisies(numero):
        vivre_evenement(creer_joueur(), fontaine)
    methode.assert_called_once()
