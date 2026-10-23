class Personnage:
    def __init__(self, nom, pv_max, attaque):
        self.nom = nom
        self.pv_max = pv_max
        self.pv = pv_max
        self.attaque = attaque

    def est_vivant(self):
        return self.pv > 0

    def subir_degats(self, degats):
        self.pv = max(0, self.pv - degats)

    def soigner(self, montant):
        avant = self.pv
        self.pv = min(self.pv_max, self.pv + montant)
        return self.pv - avant

    def __str__(self):
        return f"{self.nom} (PV : {self.pv}/{self.pv_max})"


class Joueur(Personnage):
    def __init__(self, nom, pv_max, attaque):
        super().__init__(nom, pv_max, attaque)
        self.niveau = 1
        self.piece = 0
        self.defense = 2

    def gagner_or(self, montant):
        self.piece += montant

    def __str__(self):
        return f"{super().__str__()} | Niveau {self.niveau} | Or : {self.piece}"

    def subir_degats(self, degats):
        degats_reduits = max(0, degats - self.defense)
        super().subir_degats(degats_reduits)


class Ennemi(Personnage):
    def __init__(self, nom, pv_max, attaque, recompense):
        super().__init__(nom, pv_max, attaque)
        self.recompense = recompense


if __name__ == "__main__":
    aldric = Joueur("Aldric", 30, 5)
    gobelin = Ennemi("Gobelin", 12, 2, 8)
    print(aldric)
    print(gobelin)
    gobelin.subir_degats(12)
    print(f"{gobelin.nom} subit 12 dégâts.")
    print(gobelin)
    aldric.gagner_or(gobelin.recompense)
    print(f"{aldric.nom} ramasse {gobelin.recompense} pièces d'or.")
    print(aldric)
    print(f"{aldric.nom} est un Personnage : {isinstance(aldric, Personnage)}")
    print(f"{gobelin.nom} est un Joueur : {isinstance(gobelin, Joueur)}")