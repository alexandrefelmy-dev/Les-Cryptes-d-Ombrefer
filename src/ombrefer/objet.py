"""Objets du jeu (potions, remèdes, armes, armures) et affichage de l'inventaire."""

# Prix en boutique, par PV soigné, par point de bonus ou par effet.
PRIX_PAR_PV = 1.5
PRIX_PAR_ATTAQUE = 5
PRIX_PAR_DEFENSE = 10
PRIX_PAR_REMEDE = 15  # pour chaque effet guéri
PRIX_EFFET = 10  # supplément pour une arme à effet ou une armure protectrice


class Objet:
    """Objet de base que le joueur peut ramasser et utiliser."""

    def __init__(self, nom):
        self.nom = nom

    def utiliser(self, joueur):  # pylint: disable=unused-argument
        """Applique l'effet de l'objet au joueur et renvoie la phrase à afficher."""
        return "..."

    def to_dict(self):
        """Renvoie les données de l'objet sous forme de dictionnaire, prêt pour la sauvegarde."""
        return {"nom": self.nom}

    def peut_etre_utilise(self, joueur):  # pylint: disable=unused-argument
        """Renvoie True si l'objet peut être utilisé maintenant par le joueur."""
        return True

    def refus(self, joueur):  # pylint: disable=unused-argument
        """Renvoie la phrase à afficher quand l'objet ne peut pas être utilisé."""
        return f"{self.nom} ne peut pas être utilisé."

    def prix(self):
        """Renvoie le prix de l'objet en boutique."""
        return 0

    def __str__(self):
        return self.nom


class Potion(Objet):
    """Objet qui rend des points de vie au joueur."""

    def __init__(self, nom, soin):
        super().__init__(nom)
        self.soin = soin

    def utiliser(self, joueur):
        recupere = joueur.soigner(self.soin)
        return (
            f"{joueur.nom} boit {self.nom} et récupère {recupere} PV."
            f" (PV : {joueur.pv}/{joueur.pv_max})"
        )

    def peut_etre_utilise(self, joueur):
        return joueur.pv < joueur.pv_max

    def refus(self, joueur):
        return f"{joueur.nom} a déjà tous ses PV !"

    def prix(self):
        return round(self.soin * PRIX_PAR_PV)

    def to_dict(self):
        donnees = super().to_dict()
        donnees["type"] = "potion"
        donnees["soin"] = self.soin
        return donnees

    def __str__(self):
        return f"{super().__str__()} (+{self.soin} PV)"


class Remede(Objet):
    """Potion qui guérit un ou plusieurs effets, sans rendre de PV."""

    def __init__(self, nom, effets):
        super().__init__(nom)
        self.effets = tuple(effets)

    def utiliser(self, joueur):
        for effet in self.effets:
            joueur.effets.pop(effet, None)
        return f"{joueur.nom} boit {self.nom} et guérit : {', '.join(self.effets)}."

    def peut_etre_utilise(self, joueur):
        return any(effet in joueur.effets for effet in self.effets)

    def refus(self, joueur):
        return f"{joueur.nom} ne subit aucun effet que {self.nom} peut guérir."

    def to_dict(self):
        donnees = super().to_dict()
        donnees["type"] = "remede"
        donnees["effets"] = list(self.effets)
        return donnees

    def prix(self):
        return len(self.effets) * PRIX_PAR_REMEDE

    def __str__(self):
        return f"{super().__str__()} (guérit : {', '.join(self.effets)})"


class Arme(Objet):
    """Objet qui augmente l'attaque du joueur tant qu'il le porte, parfois avec un effet."""

    def __init__(self, nom, bonus, effet=None):
        super().__init__(nom)
        self.bonus = bonus
        self.effet = effet

    def utiliser(self, joueur):
        attaque_initiale = joueur.attaque
        joueur.equiper_arme(self)
        return (
            f"{joueur.nom} s'équipe de {self.nom} :"
            f" attaque {attaque_initiale} → {joueur.attaque}."
        )

    def to_dict(self):
        donnees = super().to_dict()
        donnees["type"] = "arme"
        donnees["bonus"] = self.bonus
        donnees["effet"] = self.effet
        return donnees

    def prix(self):
        return self.bonus * PRIX_PAR_ATTAQUE + (PRIX_EFFET if self.effet else 0)

    def __str__(self):
        effet = f", {self.effet}" if self.effet else ""
        return f"{super().__str__()} (+{self.bonus} attaque{effet})"


class Armure(Objet):
    """Objet qui augmente la défense du joueur quand il le porte, parfois contre un effet."""

    def __init__(self, nom, bonus, protection=None):
        super().__init__(nom)
        self.bonus = bonus
        self.protection = protection

    def utiliser(self, joueur):
        defense_initiale = joueur.defense
        joueur.equiper_armure(self)
        return (
            f"{joueur.nom} enfile {self.nom} :"
            f" défense {defense_initiale} → {joueur.defense}."
        )

    def to_dict(self):
        donnees = super().to_dict()
        donnees["type"] = "armure"
        donnees["bonus"] = self.bonus
        donnees["protection"] = self.protection
        return donnees

    def prix(self):
        return self.bonus * PRIX_PAR_DEFENSE + (PRIX_EFFET if self.protection else 0)

    def __str__(self):
        protection = f", protège : {self.protection}" if self.protection else ""
        return f"{super().__str__()} (+{self.bonus} défense{protection})"


def afficher_equipement(joueur):
    """Affiche l'arme et l'armure portées par le joueur."""
    print(f"Équipement : {joueur.arme or 'aucune arme'}, {joueur.armure or 'aucune armure'}")


def afficher_inventaire(joueur):
    """Affiche l'équipement, puis les objets de l'inventaire, numérotés à partir de 1."""
    afficher_equipement(joueur)
    print("Inventaire :")
    for numero, objet in enumerate(joueur.inventaire, start=1):
        print(f"  {numero}. {objet}")


def objet_depuis_dict(donnees):
    """Recrée le bon objet (Potion, Remede, Arme ou Armure) à partir d'un dictionnaire."""
    match donnees["type"]:
        case "potion":
            return Potion(donnees["nom"], donnees["soin"])
        case "arme":
            return Arme(donnees["nom"], donnees["bonus"], donnees["effet"])
        case "armure":
            return Armure(donnees["nom"], donnees["bonus"], donnees["protection"])
        case "remede":
            return Remede(donnees["nom"], donnees["effets"])
        case _:
            return None
