"""Succès obtenus en terminant le jeu, un par mode, et record du mode Enfer.

Ils sont gardés dans leur propre fichier signé : ils restent acquis après la mort du héros
et quand une autre sauvegarde remplace la sienne.
"""

from ombrefer.sauvegarde import decoder, encoder

FICHIER_SUCCES = "succes.sav"
MODE_ULTIME = "Enfer"  # le mode du succès ultime et du record

# Pour chaque mode : (nom du succès, récit de la fin du jeu).
SUCCES = {
    "Facile": (
        "Rescapé d'Ombrefer",
        "Les cryptes se taisent enfin. Tu remontes vers Valbrume, épuisé mais vivant,\n"
        "et le village te croit à peine quand tu racontes ce que tu as vu.",
    ),
    "Intermédiaire": (
        "Briseur d'Ombrefer",
        "Le dernier gardien s'effondre et les portes de la crypte se scellent derrière toi.\n"
        "À Valbrume, on grave ton nom sur la pierre de la place.",
    ),
    "Difficile": (
        "Légende de Valbrume",
        "Personne n'était censé revenir d'aussi bas, et pourtant tu remontes des ténèbres.\n"
        "Les bardes chanteront ton nom bien après que les cryptes seront tombées en poussière.",
    ),
    MODE_ULTIME: (
        "Immortel d'Ombrefer",
        "Sans seconde chance, sans retour en arrière, tu as traversé l'Enfer d'Ombrefer.\n"
        "Il n'y a plus rien à vaincre ici : les cryptes elles-mêmes ont appris à te craindre.",
    ),
}


def lire_fichier():
    """Renvoie les modes terminés et le record. Un fichier absent ou modifié ne compte pas."""
    try:
        with open(FICHIER_SUCCES, "rb") as f:
            donnees = decoder(f.read())
        return {"modes": donnees["modes"], "record_enfer": donnees.get("record_enfer")}
    except FileNotFoundError:
        pass
    except (ValueError, KeyError):
        print("Erreur : le fichier des succès est corrompu ou modifié.")
    return {"modes": [], "record_enfer": None}


def ecrire_fichier(donnees):
    """Enregistre les modes terminés et le record."""
    with open(FICHIER_SUCCES, "wb") as f:
        f.write(encoder(donnees))


def modes_reussis():
    """Renvoie les modes déjà terminés."""
    return lire_fichier()["modes"]


def debloquer(mode):
    """Enregistre le succès de ce mode. Renvoie False s'il était déjà acquis."""
    donnees = lire_fichier()
    if mode in donnees["modes"]:
        return False
    donnees["modes"].append(mode)
    ecrire_fichier(donnees)
    return True


def noter_record_enfer(joueur, niveau):
    """Retient ce niveau atteint en Enfer s'il bat le record. Renvoie True si c'est le cas."""
    donnees = lire_fichier()
    record = donnees["record_enfer"]
    if record is not None and niveau <= record["niveau"]:
        return False
    donnees["record_enfer"] = {"niveau": niveau, "nom": joueur.nom, "classe": joueur.classe.nom}
    ecrire_fichier(donnees)
    return True


def texte_record():
    """Renvoie la phrase qui présente le record du mode Enfer."""
    record = lire_fichier()["record_enfer"]
    if record is None:
        return "Record en mode Enfer : aucun"
    return f"Record en mode Enfer : niveau {record['niveau']} ({record['nom']}, {record['classe']})"


def afficher_succes():
    """Affiche les succès, ceux déjà obtenus et le record du mode Enfer."""
    reussis = modes_reussis()
    print("\n=== Succès ===")
    for mode, (nom, _) in SUCCES.items():
        marque = "x" if mode in reussis else " "
        ultime = " (succès ultime)" if mode == MODE_ULTIME else ""
        print(f"  [{marque}] {nom} : terminer le jeu en mode {mode}{ultime}")
    print(texte_record())
