import random


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

    def attaquer(self, cible):
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
    def __init__(self, nom, pv_max, attaque):
        super().__init__(nom, pv_max, attaque)
        self.niveau = 1
        self.piece = 0
        self.defense = 2

    def gagner_or(self, montant):
        self.piece += montant

    def subir_degats(self, degats):
        degats_reduits = max(0, degats - self.defense)
        if random.random() < 0.1:
            pass
        else:
            super().subir_degats(degats_reduits)

    def __str__(self):
        return f"{super().__str__()} | Niveau {self.niveau} | Or : {self.piece}"


class Ennemi(Personnage):
    def __init__(self, nom, pv_max, attaque, recompense):
        super().__init__(nom, pv_max, attaque)
        self.recompense = recompense


if __name__ == "__main__":
    aldric = Joueur("Aldric", 30, 5)
    gobelin = Ennemi("Gobelin", 12, 5, 10)
    rat_geant = Ennemi("Rat géant", 18, 4, 6)
    squelette = Ennemi("Squelette", 10, 6, 8)
    ennemi = random.choice([gobelin, rat_geant, squelette])
    print(f"Un {ennemi.nom} surgit ! {ennemi}")
    montant_degat, critique = aldric.attaquer(ennemi)
    if critique:
        print(f"{aldric.nom} attaque {ennemi.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{aldric.nom} attaque {ennemi.nom} et inflige {montant_degat} dégâts.")
    print(ennemi)
    montant_degat, critique = aldric.attaquer(ennemi)
    if critique:
        print(f"{aldric.nom} attaque {ennemi.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{aldric.nom} attaque {ennemi.nom} et inflige {montant_degat} dégâts.")
    print(ennemi)
    montant_degat, critique = ennemi.attaquer(aldric)
    if critique:
        print(f"{ennemi.nom} attaque {aldric.nom} : COUP CRITIQUE ! {montant_degat} dégâts.")
    else:
        print(f"{ennemi.nom} attaque {aldric.nom} et inflige {montant_degat} dégâts.")
    print(aldric)