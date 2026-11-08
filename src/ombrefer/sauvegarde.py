"""Sauvegarde et chargement des héros, chacun dans son emplacement compressé et signé.

Chaque fichier contient "signature:contenu". Le contenu est le JSON du héros, compressé puis encodé
en base64 pour ne pas être lisible. La signature HMAC permet de détecter toute modification.
La clé étant dans le code, cela décourage la triche mais ne la rend pas impossible.
"""

import base64
import hashlib
import hmac
import json
import zlib
from pathlib import Path

from ombrefer.personnage import Joueur

EMPLACEMENTS = (1, 2, 3)
FICHIER_SAUVEGARDE = "sauvegarde_{}.sav"  # à compléter avec le numéro de l'emplacement
ANCIEN_FICHIER = "sauvegarde.sav"  # fichier unique des anciennes versions
CLE_SIGNATURE = b"Sous Valbrume, les cryptes d'Ombrefer gardent leurs secrets."


def signer(contenu):
    """Renvoie la signature du contenu, en octets."""
    return hmac.new(CLE_SIGNATURE, contenu, hashlib.sha256).hexdigest().encode("ascii")


def encoder(donnees):
    """Transforme un dictionnaire en octets illisibles et signés, prêts pour le fichier."""
    texte = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
    contenu = base64.b64encode(zlib.compress(texte))
    return signer(contenu) + b":" + contenu


def decoder(octets):
    """Retrouve le dictionnaire. Lève ValueError si le fichier a été modifié."""
    signature, _, contenu = octets.partition(b":")
    if not hmac.compare_digest(signature, signer(contenu)):
        raise ValueError("signature invalide")
    return json.loads(zlib.decompress(base64.b64decode(contenu)))


def chemin(emplacement):
    """Renvoie le fichier de cet emplacement."""
    return Path(FICHIER_SAUVEGARDE.format(emplacement))


def reprendre_ancien_fichier():
    """Range l'ancien fichier unique dans l'emplacement 1, s'il est libre."""
    ancien = Path(ANCIEN_FICHIER)
    if ancien.exists() and not chemin(1).exists():
        ancien.rename(chemin(1))


def sauvegarder(joueur, emplacement=1):
    """Sauvegarde le joueur dans cet emplacement, qu'il retient pour la suite."""
    chemin(emplacement).write_bytes(encoder(joueur.to_dict()))
    joueur.emplacement = emplacement


def charger(emplacement=1):
    """Charge le joueur de cet emplacement, ou renvoie None s'il est vide ou modifié."""
    try:
        joueur = Joueur.from_dict(decoder(chemin(emplacement).read_bytes()))
        joueur.emplacement = emplacement
        return joueur
    except FileNotFoundError:
        return None
    except (ValueError, KeyError):
        print("Erreur : le fichier de sauvegarde est corrompu, modifié ou trop ancien.")
        return None


def effacer_sauvegarde(emplacement=1):
    """Supprime le fichier de cet emplacement, s'il existe."""
    chemin(emplacement).unlink(missing_ok=True)


def emplacement_occupe(emplacement):
    """Renvoie True si un fichier existe à cet emplacement."""
    return chemin(emplacement).exists()


def apercu(emplacement):
    """Renvoie une ligne qui présente le contenu de cet emplacement, sans le charger."""
    try:
        donnees = decoder(chemin(emplacement).read_bytes())
        return (
            f"{donnees['nom']}, {donnees['classe']}, mode {donnees['difficulte']},"
            f" niveau {donnees['niveau_donjon']} du donjon"
        )
    except FileNotFoundError:
        return "vide"
    except (ValueError, KeyError):
        return "fichier illisible"
