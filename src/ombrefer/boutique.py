"""Boutique du marchand : on y dépense l'or récolté dans le donjon."""

from ombrefer.objet import afficher_equipement


def afficher_boutique(joueur, stock):
    """Affiche l'or du joueur, son équipement et les objets en vente, numérotés à partir de 1."""
    print(f"\n=== Boutique === (Or : {joueur.piece})")
    afficher_equipement(joueur)
    for numero, objet in enumerate(stock, start=1):
        print(f"  {numero}. {objet.texte_pour(joueur)} : {objet.prix()} or")
    print("  0. Partir")


def acheter(joueur, stock, index):
    """Vend au joueur l'objet à l'index donné, s'il a assez d'or. Renvoie True si c'est vendu."""
    objet = stock[index]
    if not joueur.payer(objet.prix()):
        print(f"{joueur.nom} n'a pas assez d'or pour {objet.nom}.")
        return False
    joueur.ramasser_objet(stock.pop(index))
    print(f"{joueur.nom} achète {objet.nom} : à retrouver dans l'inventaire.")
    return True


def visiter_boutique(joueur, stock):
    """Laisse le joueur acheter jusqu'à ce qu'il parte ou que le stock soit vide."""
    while stock:
        afficher_boutique(joueur, stock)
        choix = input("Que veux-tu acheter ? ")
        numeros = [str(n) for n in range(len(stock) + 1)]
        if choix == "0":
            return
        if choix in numeros:
            acheter(joueur, stock, int(choix) - 1)
        else:
            print("Numéro invalide.")
    print("Le marchand n'a plus rien à vendre.")
