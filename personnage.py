"""Classes des personnages du jeu : Personnage, Joueur et Ennemi."""

import random


class Personnage:
    """Personnage de base avec des points de vie et une attaque."""

    def __init__(self, nom, pv_max, attaque):
        self.nom = nom
        self.pv_max = pv_max
        self.pv = pv_max
        self.attaque = attaque

    def est_vivant(self):
        """Renvoie True si le personnage a encore des points de vie."""
        return self.pv > 0

    def subir_degats(self, degats):
        """Retire des points de vie, sans descendre en dessous de 0."""
        self.pv = max(0, self.pv - degats)

    def soigner(self, montant):
        """Rend des points de vie (sans dépasser pv_max) et renvoie le montant soigné."""
        avant = self.pv
        self.pv = min(self.pv_max, self.pv + montant)
        return self.pv - avant

    def attaquer(self, cible):
        """Attaque la cible et renvoie (dégâts réellement infligés, coup critique)."""
        degats = random.randint(1, self.attaque)
        critique = random.random() < 0.2
        if critique:
            degats *= 2
        avant = cible.pv
        cible.subir_degats(degats)
        return avant - cible.pv, critique

    def __str__(self):
        return f"{self.nom} (PV : {self.pv}/{self.pv_max})"


class Joueur(Personnage):
    """Personnage contrôlé par le joueur, avec défense, inventaire et or."""

    def __init__(self, nom, pv_max, attaque):
        super().__init__(nom, pv_max, attaque)
        self.niveau = 1
        self.piece = 0
        self.defense = 2
        self.inventaire = []

    def gagner_or(self, montant):
        """Ajoute des pièces d'or au joueur."""
        self.piece += montant

    def subir_degats(self, degats):
        """Réduit les dégâts avec la défense, avec 10 % de chances d'esquiver."""
        degats_reduits = max(0, degats - self.defense)
        esquive = random.random() < 0.1
        if not esquive:
            super().subir_degats(degats_reduits)

    def ramasser_objet(self, objet):
        """Ajoute un objet à la fin de l'inventaire."""
        self.inventaire.append(objet)

    def utiliser_objet(self, index):
        """Retire l'objet à l'index donné, l'utilise et renvoie la phrase obtenue."""
        objet = self.inventaire.pop(index)
        return objet.utiliser(self)

    def __str__(self):
        return f"{super().__str__()} | Niveau {self.niveau} | Or : {self.piece}"


class Ennemi(Personnage):
    """Ennemi qui rapporte une récompense en or quand il est vaincu."""

    def __init__(self, nom, pv_max, attaque, recompense):
        super().__init__(nom, pv_max, attaque)
        self.recompense = recompense
