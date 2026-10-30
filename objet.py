from personnage import Joueur


class Objet:
    def __init__(self, nom):
        self.nom = nom

    def utiliser(self, joueur):
        return "..."

    def peut_etre_utilise(self, joueur):
        return True

    def __str__(self):
        return self.nom


class Potion(Objet):
    def __init__(self, nom, soin):
        super().__init__(nom)
        self.soin = soin

    def utiliser(self, joueur):
        recupere = joueur.soigner(self.soin)
        return f"{joueur.nom} boit {self.nom} et récupère {recupere} PV."

    def peut_etre_utilise(self, joueur):
        return joueur.pv < joueur.pv_max
        

    def __str__(self):
        return f"{super().__str__()} (+{self.soin} PV)"


class Arme(Objet):
    def __init__(self, nom, bonus):
        super().__init__(nom)
        self.bonus = bonus

    def utiliser(self, joueur):
        attaque_initiale = joueur.attaque
        joueur.attaque += self.bonus
        return f"{joueur.nom} s'équipe de {self.nom} : attaque {attaque_initiale} → {joueur.attaque}."

    def __str__(self):
        return f"{super().__str__()} (+{self.bonus} attaque)"


def afficher_inventaire(joueur):
    print("Inventaire :")
    for numero, objet in enumerate(joueur.inventaire, start=1):
        print(f"  {numero}. {objet}")

