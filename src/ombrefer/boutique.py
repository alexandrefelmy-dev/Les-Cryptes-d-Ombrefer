"""Boutique du marchand : on y dépense l'or récolté dans le donjon, et on y vend son équipement."""

from ombrefer.objet import Arme, Armure, afficher_equipement


def equipement_a_vendre(joueur):
    """Renvoie les armes et armures du joueur : celles de l'inventaire, puis celles portées."""
    ranges = [objet for objet in joueur.inventaire if isinstance(objet, (Arme, Armure))]
    return ranges + [objet for objet in (joueur.arme, joueur.armure) if objet is not None]


def afficher_boutique(joueur, stock):
    """Affiche l'or du joueur, son équipement et les objets en vente, numérotés à partir de 1."""
    print(f"\n=== Boutique === (Or : {joueur.piece})")
    afficher_equipement(joueur)
    for numero, objet in enumerate(stock, start=1):
        print(f"  {numero}. {objet.texte_pour(joueur)} : {objet.prix()} or")
    if not stock:
        print("  Le marchand n'a plus rien à vendre.")
    if equipement_a_vendre(joueur):
        print("  v. Vendre ton équipement")
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


def vendre(joueur, objet):
    """Reprend cet objet au joueur, rangé ou porté, et lui paie son prix de revente."""
    joueur.retirer_objet(objet)
    joueur.gagner_or(objet.prix_revente())
    print(f"{joueur.nom} vend {objet.nom} pour {objet.prix_revente()} or.")


def afficher_vente(joueur, a_vendre):
    """Affiche l'or du joueur et ce qu'il peut vendre, numéroté à partir de 1."""
    print(f"\n=== Vente === (Or : {joueur.piece})")
    for numero, objet in enumerate(a_vendre, start=1):
        porte = " [porté]" if objet in (joueur.arme, joueur.armure) else ""
        print(f"  {numero}. {objet.texte_pour(joueur)}{porte} : {objet.prix_revente()} or")
    print("  0. Retour")


def confirmer_vente(joueur, objet):
    """Renvoie True si l'objet est rangé, ou si le joueur confirme vendre ce qu'il porte."""
    if objet not in (joueur.arme, joueur.armure):
        return True
    return input(f"Tu portes {objet.nom}. Le vendre ? (o/n) : ").strip().lower() == "o"


def visiter_vente(joueur):
    """Laisse le joueur vendre son équipement jusqu'à ce qu'il revienne ou n'ait plus rien."""
    while a_vendre := equipement_a_vendre(joueur):
        afficher_vente(joueur, a_vendre)
        choix = input("Que veux-tu vendre ? ")
        if choix == "0":
            return
        if choix in [str(numero) for numero in range(1, len(a_vendre) + 1)]:
            objet = a_vendre[int(choix) - 1]
            if confirmer_vente(joueur, objet):
                vendre(joueur, objet)
        else:
            print("Numéro invalide.")


def visiter_boutique(joueur, stock):
    """Laisse le joueur acheter et vendre jusqu'à ce qu'il parte ou qu'il n'y ait plus rien."""
    while stock or equipement_a_vendre(joueur):
        afficher_boutique(joueur, stock)
        choix = input("Ton choix : ").strip().lower()
        numeros = [str(n) for n in range(len(stock) + 1)]
        if choix == "0":
            return
        if choix == "v" and equipement_a_vendre(joueur):
            visiter_vente(joueur)
        elif choix in numeros:
            acheter(joueur, stock, int(choix) - 1)
        else:
            print("Numéro invalide.")
    print("Le marchand n'a plus rien à vendre.")
