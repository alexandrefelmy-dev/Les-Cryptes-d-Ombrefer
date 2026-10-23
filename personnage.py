class Personnage:
    def __init__(self, nom, pv_max, attaque):
        self.nom = nom
        self.pv_max = pv_max
        self.pv = pv_max
        self.attaque = attaque

    def est_vivant(self):
        if self.pv <= 0:
            return False
        else:
            return True

    def subir_degats(self, degats):
        self.pv = max(0, self.pv - degats)

    def soigner(self, montant):
        avant = self.pv
        self.pv = min(self.pv_max, self.pv + montant)
        return self.pv - avant
         

    def __str__(self):
        return f"{self.nom} (PV : {self.pv}/{self.pv_max})"

     
if __name__ == "__main__":
    aldric = Personnage("Aldric", 30, 5)
    print(aldric)

    aldric.subir_degats(12)
    print(f"{aldric.nom} subit 12 dégâts")
    print(aldric)

    recupere = aldric.soigner(20)
    print(f"{aldric.nom} boit une potion de 20 PV et en récupère {recupere}")
    print(aldric)

    aldric.subir_degats(45)
    print(f"{aldric.nom} subit 45 dégâts")
    print(aldric)


    print(f"{aldric.nom} est vivant : {aldric.est_vivant()}")
