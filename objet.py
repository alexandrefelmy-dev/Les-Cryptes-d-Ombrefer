"""Objets du jeu (potions, armes) et affichage de l'inventaire."""


class Objet:
    """Objet de base que le joueur peut ramasser et utiliser."""

    def __init__(self, nom):
        self.nom = nom

    def utiliser(self, joueur):  # pylint: disable=unused-argument
        """Applique l'effet de l'objet au joueur et renvoie la phrase à afficher."""
        return "..."

    def to_dict(self):
        """Renvoie les données de l'objet sous forme de dictionnaire, prêt pour le JSON."""
        return {"nom": self.nom}

    def peut_etre_utilise(self, joueur):  # pylint: disable=unused-argument
        """Renvoie True si l'objet peut être utilisé maintenant par le joueur."""
        return True

    def __str__(self):
        return self.nom


class Potion(Objet):
    """Objet qui rend des points de vie au joueur."""

    def __init__(self, nom, soin):
        super().__init__(nom)
        self.soin = soin

    def utiliser(self, joueur):
        recupere = joueur.soigner(self.soin)
        return f"{joueur.nom} boit {self.nom} et récupère {recupere} PV."

    def peut_etre_utilise(self, joueur):
        return joueur.pv < joueur.pv_max

    def to_dict(self):
        donnees = super().to_dict()
        donnees["type"] = "potion"
        donnees["soin"] = self.soin
        return donnees

    def __str__(self):
        return f"{super().__str__()} (+{self.soin} PV)"


class Arme(Objet):
    """Objet qui augmente définitivement l'attaque du joueur."""

    def __init__(self, nom, bonus):
        super().__init__(nom)
        self.bonus = bonus

    def utiliser(self, joueur):
        attaque_initiale = joueur.attaque
        joueur.attaque += self.bonus
        return (
            f"{joueur.nom} s'équipe de {self.nom} :"
            f" attaque {attaque_initiale} → {joueur.attaque}."
        )

    def to_dict(self):
        donnees = super().to_dict()
        donnees["type"] = "arme"
        donnees["bonus"] = self.bonus
        return donnees

    def __str__(self):
        return f"{super().__str__()} (+{self.bonus} attaque)"


def afficher_inventaire(joueur):
    """Affiche les objets de l'inventaire, numérotés à partir de 1."""
    print("Inventaire :")
    for numero, objet in enumerate(joueur.inventaire, start=1):
        print(f"  {numero}. {objet}")


def objet_depuis_dict(donnees):
    """Recrée le bon objet (Potion ou Arme) à partir d'un dictionnaire."""
    match donnees["type"]:
        case "potion":
            return Potion(donnees["nom"], donnees["soin"])
        case "arme":
            return Arme(donnees["nom"], donnees["bonus"])
        case _:
            return None
