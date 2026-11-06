"""Événements hors combat : des choix risqués proposés à la sortie d'une salle.

Les chances restent cachées au joueur : seuls les textes lui donnent des indices.
Une perte de PV ne tue jamais ici : les PV s'arrêtent à 1.
"""

import random

from ombrefer.combat import appliquer_effet
from ombrefer.effet import AFFAIBLISSEMENT, POISON
from ombrefer.objet import Potion

OR_PAR_NIVEAU = 20  # or gagné, multiplié par le niveau du donjon
PART_ALLIE = 0.15  # part des PV max du boss retirée par l'allié


def blesser(joueur, part):
    """Retire cette part des PV max, sans passer sous 1 PV. Renvoie les PV perdus."""
    avant = joueur.pv
    joueur.pv = max(1, joueur.pv - round(joueur.pv_max * part))
    return avant - joueur.pv


def declencher_piege(joueur, part):
    """Blesse et empoisonne le joueur, sauf si son armure le protège du poison."""
    print(f"Un piège se déclenche ! {joueur.nom} perd {blesser(joueur, part)} PV.")
    appliquer_effet(joueur, POISON)


def recompense_en_or(joueur):
    """Renvoie l'or d'un événement, qui suit le niveau du donjon."""
    return OR_PAR_NIVEAU * joueur.niveau_donjon


class Evenement:
    """Événement de base : les événements concrets changent ces textes et leurs options."""

    nom = ""
    annonce = ""  # phrase affichée à l'arrivée à la pause
    action = ""  # texte du choix dans le menu de la pause

    def options(self, joueur):
        """Renvoie les choix possibles : une liste de (texte, méthode qui reçoit le joueur)."""
        raise NotImplementedError

    def refus(self, joueur):  # pylint: disable=unused-argument
        """Renvoie la phrase à afficher quand aucun choix n'est possible."""
        return "Il n'y a rien à faire ici."


class Fontaine(Evenement):
    """Boire peut soigner beaucoup ou rendre malade, la fiole est sûre mais petite."""

    nom = "Fontaine"
    annonce = "Une fontaine murmure dans un coin de la salle. Son eau est trouble."
    action = "Approcher de la fontaine"
    chance_soin = 0.55
    chance_rien = 0.3  # le reste de la chance rend malade
    part_soin = 0.4
    part_degats = 0.15

    def options(self, joueur):
        return [
            ("Boire à la source : elle pourrait te soigner, ou te rendre malade", self.boire),
            ("Remplir une fiole : une petite potion, sans risque", self.remplir_fiole),
        ]

    def boire(self, joueur):
        """Soigne et guérit tous les effets, ne fait rien, ou empoisonne."""
        tirage = random.random()
        if tirage < self.chance_soin:
            soin = joueur.soigner(round(joueur.pv_max * self.part_soin))
            joueur.effets.clear()
            print(f"L'eau est pure : {joueur.nom} récupère {soin} PV et guérit de ses effets.")
        elif tirage < self.chance_soin + self.chance_rien:
            print("L'eau a un goût de pierre. Rien ne se passe.")
        else:
            print(f"L'eau est viciée ! {joueur.nom} perd {blesser(joueur, self.part_degats)} PV.")
            appliquer_effet(joueur, POISON)

    def remplir_fiole(self, joueur):
        """Donne une petite potion."""
        potion = Potion("Petite potion de soin", 10)
        joueur.ramasser_objet(potion)
        print(f"{joueur.nom} remplit une fiole : {potion}.")


class AutelMaudit(Evenement):
    """Le sang coûte des PV pour une force durable, le pacte change la force pour le niveau."""

    nom = "Autel maudit"
    annonce = "Un autel maudit suinte dans l'ombre. Des chuchotements t'appellent."
    action = "Approcher de l'autel"
    part_sang = 0.2
    gain_sang = 0.06  # part de l'attaque gagnée pour toujours
    chance_pacte = 0.6
    gain_pacte = 0.25
    perte_pacte = 0.15

    def cout_sang(self, joueur):
        """Renvoie les PV à offrir à l'autel."""
        return round(joueur.pv_max * self.part_sang)

    def options(self, joueur):
        cout = self.cout_sang(joueur)
        sang = (f"Offrir ton sang ({cout} PV) : ta force grandira pour toujours", self.offrir_sang)
        pacte = ("Sceller un pacte : ta force changera d'ici la fin du niveau, en bien ou en mal",
                 self.sceller_pacte)
        # Sans assez de PV, le sang ne coûterait presque rien : l'autel le refuse.
        return [sang, pacte] if joueur.pv > cout else [pacte]

    def offrir_sang(self, joueur):
        """Échange des PV contre de l'attaque permanente."""
        perte = blesser(joueur, self.part_sang)
        joueur.attaque += max(1, round(joueur.attaque * self.gain_sang))
        print(f"L'autel boit {perte} PV. Attaque : {joueur.attaque}.")

    def sceller_pacte(self, joueur):
        """Augmente ou réduit l'attaque jusqu'à la fin du niveau de donjon."""
        if random.random() < self.chance_pacte:
            joueur.changer_attaque_pour_le_niveau(max(1, round(joueur.attaque * self.gain_pacte)))
            print(f"L'autel t'accepte. Attaque : {joueur.attaque}.")
        else:
            joueur.changer_attaque_pour_le_niveau(-max(1, round(joueur.attaque * self.perte_pacte)))
            print(f"L'autel se moque de toi. Attaque : {joueur.attaque}.")


class CoffrePiege(Evenement):
    """Forcer vise le butin et risque le piège, crocheter vise un peu d'or presque sans risque."""

    nom = "Coffre piégé"
    annonce = "Un coffre repose ici. Des fils fins luisent autour de sa serrure."
    action = "Examiner le coffre"
    chance_forcer = 0.6
    chance_crocheter = 0.9
    part_piege_forcer = 0.25
    part_piege_crocheter = 0.1

    def __init__(self, butin):
        self.butin = butin

    def options(self, joueur):
        return [
            ("Forcer le couvercle : grosse prise, gros danger", self.forcer),
            ("Crocheter la serrure : les pièces du fond, presque sans danger", self.crocheter),
        ]

    def forcer(self, joueur):
        """Donne l'objet du coffre, ou déclenche un gros piège. Le Voleur réussit plus souvent."""
        bonus = joueur.classe.bonus_coffre if joueur.classe else 0
        if random.random() < self.chance_forcer + bonus:
            joueur.ramasser_objet(self.butin)
            print(f"Le coffre cède ! {joueur.nom} trouve : {self.butin.texte_pour(joueur)}")
        else:
            declencher_piege(joueur, self.part_piege_forcer)

    def crocheter(self, joueur):
        """Donne de l'or, ou déclenche un petit piège."""
        if random.random() < self.chance_crocheter:
            gain = recompense_en_or(joueur)
            joueur.gagner_or(gain)
            print(f"La serrure cède. {joueur.nom} ramasse {gain} pièces d'or.")
        else:
            declencher_piege(joueur, self.part_piege_crocheter)


class Prisonnier(Evenement):
    """Le libérer peut offrir un allié contre le boss, ou coûter de l'or."""

    nom = "Prisonnier"
    annonce = "Un prisonnier enchaîné t'appelle à voix basse depuis sa cage."
    action = "Parler au prisonnier"
    chance_allie = 0.5
    chance_fuite = 0.25  # le reste de la chance est un vol
    part_vol = 0.25
    chance_malediction = 0.3

    def options(self, joueur):
        return [
            ("Le libérer : il jure de t'aider, mais peut-on le croire ?", self.liberer),
            ("Lui prendre sa bourse : facile, mais il risque de te maudire", self.depouiller),
        ]

    def liberer(self, joueur):
        """Gagne un allié contre le boss, ne gagne rien, ou se fait voler."""
        tirage = random.random()
        if tirage < self.chance_allie:
            joueur.allie = True
            print('"Merci ! Quand tu trouveras le maître de ces lieux, je serai là."')
        elif tirage < self.chance_allie + self.chance_fuite:
            print("À peine libre, il détale dans le noir sans un mot.")
        else:
            vol = round(joueur.piece * self.part_vol)
            joueur.piece -= vol
            print(f"En t'enlaçant, il te vole {vol} pièces d'or et disparaît !")

    def depouiller(self, joueur):
        """Prend de l'or, avec un risque d'affaiblissement au prochain combat."""
        gain = recompense_en_or(joueur)
        joueur.gagner_or(gain)
        print(f"{joueur.nom} prend sa bourse : {gain} pièces d'or.")
        if random.random() < self.chance_malediction:
            print('"Sois maudit !"')
            appliquer_effet(joueur, AFFAIBLISSEMENT)


class Forge(Evenement):
    """Contre de l'or, améliore l'équipement porté, avec un risque de l'abîmer."""

    nom = "Forge abandonnée"
    annonce = "Une forge abandonnée rougeoie encore. Son enclume est fendue."
    action = "Approcher de la forge"
    prix_par_niveau = 15
    chance_arme = 0.6
    chance_arme_intacte = 0.25  # le reste de la chance abîme l'arme
    gain_arme = 0.25
    perte_arme = 0.15
    chance_armure = 0.7
    chance_armure_intacte = 0.2  # le reste de la chance abîme l'armure

    def prix(self, joueur):
        """Renvoie le prix d'un passage à la forge, qui suit le niveau du donjon."""
        return self.prix_par_niveau * joueur.niveau_donjon

    def options(self, joueur):
        prix = self.prix(joueur)
        options = []
        if joueur.piece >= prix and joueur.arme is not None:
            texte = f"Reforger {joueur.arme.nom} ({prix} or) : le métal peut aussi en souffrir"
            options.append((texte, self.reforger_arme))
        if joueur.piece >= prix and joueur.armure is not None:
            texte = f"Reforger {joueur.armure.nom} ({prix} or) : le métal peut aussi en souffrir"
            options.append((texte, self.reforger_armure))
        return options

    def refus(self, joueur):
        return f"Il te faudrait de l'équipement à reforger et {self.prix(joueur)} pièces d'or."

    def reforger_arme(self, joueur):
        """Améliore l'arme portée, ne change rien, ou l'abîme."""
        joueur.payer(self.prix(joueur))
        bonus = joueur.arme.bonus
        tirage = random.random()
        if tirage < self.chance_arme:
            joueur.renforcer_arme(max(2, round(bonus * self.gain_arme)))
            print(f"Le métal chante ! Attaque : {joueur.attaque}.")
        elif tirage < self.chance_arme + self.chance_arme_intacte:
            print("Le métal refuse de changer de forme.")
        else:
            joueur.renforcer_arme(-max(1, round(bonus * self.perte_arme)))
            print(f"Le métal se fend ! Attaque : {joueur.attaque}.")

    def reforger_armure(self, joueur):
        """Améliore l'armure portée, ne change rien, ou l'abîme."""
        joueur.payer(self.prix(joueur))
        tirage = random.random()
        if tirage < self.chance_armure:
            joueur.renforcer_armure(1)
            print(f"Les plaques se resserrent ! Défense : {joueur.defense}.")
        elif tirage < self.chance_armure + self.chance_armure_intacte:
            print("Le métal refuse de changer de forme.")
        else:
            joueur.renforcer_armure(-1)
            print(f"Une plaque se fend ! Défense : {joueur.defense}.")


def vivre_evenement(joueur, evenement):
    """Propose les choix de l'événement. Renvoie True si le joueur en a fait un."""
    options = evenement.options(joueur)
    if not options:
        print(evenement.refus(joueur))
        return False
    print(f"\n=== {evenement.nom} ===")
    for numero, (texte, _) in enumerate(options, start=1):
        print(f"  {numero}. {texte}")
    print("  0. Retour")
    numeros = [str(n) for n in range(len(options) + 1)]
    choix = input("Que fais-tu ? ")
    while choix not in numeros:
        print("Numéro invalide.")
        choix = input("Que fais-tu ? ")
    if choix == "0":
        return False
    _, resoudre = options[int(choix) - 1]
    resoudre(joueur)
    return True


def renfort_allie(joueur, boss):
    """L'allié libéré entame le boss au début du combat, une seule fois."""
    if not joueur.allie:
        return
    joueur.allie = False
    degats = round(boss.pv_max * PART_ALLIE)
    boss.perdre_pv(degats)
    print(f"Le prisonnier libéré surgit et blesse {boss.nom} : {degats} dégâts ! {boss}")
