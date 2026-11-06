"""Classes des personnages du jeu : Personnage, Joueur et Ennemi."""

import random

from ombrefer.classe import classe_par_nom
from ombrefer.effet import (
    DEGATS_EN_RAGE,
    DEGATS_POISON,
    DUREES,
    FORCE_AFFAIBLI,
    FORCE_RAGE,
    AFFAIBLISSEMENT,
    IMMOBILISATION,
    POISON,
    RAGE,
    REPIT_IMMOBILISATION,
)
from ombrefer.objet import objet_depuis_dict


CHANCE_EFFET_ARME = 0.3
MULTIPLICATEUR_GARDE = 2  # multiplie la défense du joueur pendant qu'il se défend


class Personnage:
    """Personnage de base avec des points de vie, une attaque et des effets."""

    def __init__(self, nom, pv_max, attaque):
        self.nom = nom
        self.pv_max = pv_max
        self.pv = pv_max
        self.attaque = attaque
        self.chance_critique = 0.2
        self.effets = {}  # pour chaque effet subi, le nombre de tours restants
        self.repit_immobilisation = 0

    def est_vivant(self):
        """Renvoie True si le personnage a encore des points de vie."""
        return self.pv > 0

    def perdre_pv(self, montant):
        """Retire des points de vie, sans descendre en dessous de 0."""
        self.pv = max(0, self.pv - montant)

    def subir_degats(self, degats):
        """Encaisse des dégâts. Le joueur les réduit avec sa défense."""
        self.perdre_pv(degats)

    def soigner(self, montant):
        """Rend des points de vie (sans dépasser pv_max) et renvoie le montant soigné."""
        avant = self.pv
        self.pv = min(self.pv_max, self.pv + montant)
        return self.pv - avant

    def attaque_actuelle(self):
        """Renvoie l'attaque du personnage, selon ses effets."""
        attaque = self.attaque
        if RAGE in self.effets:
            attaque *= FORCE_RAGE
        if AFFAIBLISSEMENT in self.effets:
            attaque *= FORCE_AFFAIBLI
        return max(1, round(attaque))

    def effet_inflige(self):
        """Renvoie (effet, chance de l'infliger à chaque coup), ou None s'il n'y en a pas."""
        return None

    def peut_recevoir(self, effet):
        """Renvoie True si cet effet peut toucher le personnage maintenant."""
        return effet != IMMOBILISATION or self.repit_immobilisation == 0

    def recevoir_effet(self, effet):
        """Applique l'effet, ou relance sa durée s'il est déjà là. Renvoie True si ça a marché."""
        if not self.peut_recevoir(effet):
            return False
        self.effets[effet] = DUREES[effet]
        if effet == IMMOBILISATION:
            self.repit_immobilisation = REPIT_IMMOBILISATION
        return True

    def passer_un_tour(self):
        """Fait vieillir les effets et applique le poison. Renvoie True si on peut agir."""
        self.repit_immobilisation = max(0, self.repit_immobilisation - 1)
        self.effets = {effet: tours - 1 for effet, tours in self.effets.items() if tours > 0}
        if POISON in self.effets:
            self.perdre_pv(DEGATS_POISON)
        return IMMOBILISATION not in self.effets

    def frapper(self, cible, degats):
        """Inflige ces dégâts à la cible et renvoie ceux réellement subis."""
        avant = cible.pv
        cible.subir_degats(degats)
        return avant - cible.pv

    def attaquer(self, cible):
        """Attaque la cible et renvoie (dégâts réellement infligés, coup critique)."""
        degats = random.randint(1, self.attaque_actuelle())
        critique = random.random() < self.chance_critique
        if critique:
            degats *= 2
        return self.frapper(cible, degats), critique

    def __str__(self):
        effets = f" [{', '.join(self.effets)}]" if self.effets else ""
        return f"{self.nom} (PV : {self.pv}/{self.pv_max}){effets}"


class Joueur(Personnage):  # pylint: disable=too-many-instance-attributes
    """Personnage contrôlé par le joueur, avec équipement, inventaire et or.

    attaque et defense sont des totaux : ils comprennent le bonus de l'équipement porté.
    """

    def __init__(self, nom, pv_max, attaque):
        super().__init__(nom, pv_max, attaque)
        self.niveau = 1
        self.niveau_donjon = 1
        self.difficulte = None  # nom du mode, choisi une seule fois pour tout le parcours
        self.classe = None
        self.chance_esquive = 0.1
        self.recharge_speciale = 0  # tours de combat avant la prochaine attaque spéciale
        self.piece = 0
        self.defense = 0
        self.arme = None
        self.armure = None
        self.inventaire = []
        self.xp = 0
        self.tours_defense = 0
        self.garde_utilisee = False
        self.bonus_pacte = 0  # attaque gagnée ou perdue jusqu'à la fin du niveau de donjon
        self.allie = False  # le prisonnier libéré attend le boss de ce niveau
        self.a_une_sauvegarde = False  # le fichier de sauvegarde contient bien ce héros

    def gagner_or(self, montant):
        """Ajoute des pièces d'or au joueur."""
        self.piece += montant

    def prendre_classe(self, classe):
        """Donne au joueur les chances de critique et d'esquive de sa classe."""
        self.classe = classe
        self.chance_critique = classe.chance_critique
        self.chance_esquive = classe.chance_esquive

    def finir_niveau_donjon(self):
        """Passe au niveau de donjon suivant, après un repos qui remet le héros à neuf."""
        self.niveau_donjon += 1
        self.attaque -= self.bonus_pacte
        self.bonus_pacte = 0
        self.allie = False
        self.pv = self.pv_max
        self.effets = {}
        self.recharge_speciale = 0

    def payer(self, montant):
        """Retire l'or du joueur s'il en a assez. Renvoie True si le paiement a eu lieu."""
        if self.piece < montant:
            return False
        self.piece -= montant
        return True

    def changer_attaque_pour_le_niveau(self, montant):
        """Change l'attaque jusqu'à la fin du niveau de donjon."""
        self.attaque += montant
        self.bonus_pacte += montant

    def renforcer_arme(self, montant):
        """Change le bonus de l'arme portée (jamais sous 1) et met l'attaque à jour."""
        avant = self.arme.bonus_pour(self.classe)
        self.arme.bonus = max(1, self.arme.bonus + montant)
        self.attaque += self.arme.bonus_pour(self.classe) - avant

    def renforcer_armure(self, montant):
        """Change le bonus de l'armure portée (jamais sous 1) et met la défense à jour."""
        avant = self.armure.bonus
        self.armure.bonus = max(1, avant + montant)
        self.defense += self.armure.bonus - avant

    def equiper_arme(self, arme):
        """Porte cette arme : l'ancienne retourne dans l'inventaire."""
        if self.arme is not None:
            self.attaque -= self.arme.bonus_pour(self.classe)
            self.ramasser_objet(self.arme)
        self.attaque += arme.bonus_pour(self.classe)
        self.arme = arme

    def equiper_armure(self, armure):
        """Porte cette armure : l'ancienne retourne dans l'inventaire."""
        if self.armure is not None:
            self.defense -= self.armure.bonus
            self.ramasser_objet(self.armure)
        self.defense += armure.bonus
        self.armure = armure
        self.effets.pop(armure.protection, None)

    def effet_inflige(self):
        """Renvoie l'effet de l'arme portée et sa chance, ou None."""
        if self.arme is None or self.arme.effet is None:
            return None
        return self.arme.effet, CHANCE_EFFET_ARME

    def peut_recevoir(self, effet):
        """La garde et l'armure adaptée empêchent un nouvel effet de toucher le joueur."""
        if self.tours_defense > 0:
            return False
        if self.armure is not None and self.armure.protection == effet:
            return False
        return super().peut_recevoir(effet)

    def fin_de_combat(self):
        """Termine la garde et les effets de combat : seul le poison continue après."""
        self.tours_defense = 0
        self.garde_utilisee = False
        self.repit_immobilisation = 0
        self.effets = {effet: tours for effet, tours in self.effets.items() if effet == POISON}

    def defense_actuelle(self):
        """Renvoie la défense du joueur, renforcée s'il se défend en ce moment."""
        if self.tours_defense > 0:
            return self.defense * MULTIPLICATEUR_GARDE
        return self.defense

    def subir_degats(self, degats):
        """Réduit les dégâts avec la défense, avec une chance de les esquiver."""
        degats_reduits = max(0, degats - self.defense_actuelle())
        if RAGE in self.effets:
            degats_reduits += DEGATS_EN_RAGE
        esquive = random.random() < self.chance_esquive
        if not esquive:
            super().subir_degats(degats_reduits)

    def ramasser_objet(self, objet):
        """Ajoute un objet à la fin de l'inventaire."""
        self.inventaire.append(objet)

    def utiliser_objet(self, index):
        """Retire l'objet à l'index donné, l'utilise et renvoie la phrase obtenue."""
        objet = self.inventaire.pop(index)
        return objet.utiliser(self)

    def gagner_xp(self, montant):
        """Ajoute de l'XP, gère les montées de niveau et renvoie True s'il y en a eu."""
        self.xp += montant
        montee_de_niveau = False
        while self.xp >= self.niveau * 20:
            montee_de_niveau = True
            self.xp -= self.niveau * 20
            self.niveau += 1
            self.pv_max += 5
            self.attaque += 1
            self.pv = self.pv_max
        return montee_de_niveau

    def to_dict(self):
        """Renvoie le joueur sous forme de dictionnaire (pour la sauvegarde)."""
        return {
            "nom": self.nom,
            "pv": self.pv,
            "pv_max": self.pv_max,
            "attaque": self.attaque,
            "niveau": self.niveau,
            "niveau_donjon": self.niveau_donjon,
            "difficulte": self.difficulte,
            "classe": self.classe.nom if self.classe else None,
            "piece": self.piece,
            "defense": self.defense,
            "arme": self.arme.to_dict() if self.arme else None,
            "armure": self.armure.to_dict() if self.armure else None,
            "inventaire": [objet.to_dict() for objet in self.inventaire],
            "xp": self.xp,
        }

    @classmethod
    def from_dict(cls, donnees):
        """Recrée un joueur à partir d'un dictionnaire chargé depuis la sauvegarde."""
        joueur = cls(donnees["nom"], donnees["pv_max"], donnees["attaque"])
        joueur.pv = donnees["pv"]
        joueur.niveau = donnees["niveau"]
        joueur.niveau_donjon = donnees["niveau_donjon"]
        joueur.difficulte = donnees["difficulte"]
        classe = classe_par_nom(donnees["classe"])
        if classe is not None:
            joueur.prendre_classe(classe)
        joueur.piece = donnees["piece"]
        joueur.defense = donnees["defense"]
        arme, armure = donnees["arme"], donnees["armure"]
        joueur.arme = objet_depuis_dict(arme) if arme else None
        joueur.armure = objet_depuis_dict(armure) if armure else None
        joueur.inventaire = [objet_depuis_dict(objet_dict) for objet_dict in donnees["inventaire"]]
        joueur.xp = donnees["xp"]
        return joueur

    def __str__(self):
        return f"{super().__str__()} | Niveau {self.niveau} | Or : {self.piece}"


class Ennemi(Personnage):
    """Ennemi qui rapporte une récompense en or quand il est vaincu, parfois avec un effet."""

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(self, nom, pv_max, attaque, recompense, effet=None, chance_effet=0):
        super().__init__(nom, pv_max, attaque)
        self.recompense = recompense
        self.effet = effet
        self.chance_effet = chance_effet

    def effet_inflige(self):
        """Renvoie l'effet de l'ennemi et sa chance, ou None."""
        return (self.effet, self.chance_effet) if self.effet else None
