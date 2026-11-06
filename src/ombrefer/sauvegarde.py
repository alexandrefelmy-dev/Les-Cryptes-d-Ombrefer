"""Sauvegarde et chargement du héros dans un fichier compressé et signé.

Le fichier contient "signature:contenu". Le contenu est le JSON du héros, compressé puis encodé
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

FICHIER_SAUVEGARDE = "sauvegarde.sav"
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


def sauvegarder(joueur):
    """Sauvegarde le joueur dans le fichier de sauvegarde."""
    with open(FICHIER_SAUVEGARDE, "wb") as f:
        f.write(encoder(joueur.to_dict()))
    joueur.a_une_sauvegarde = True


def charger():
    """Charge le joueur, ou renvoie None si le fichier manque ou a été modifié."""
    try:
        with open(FICHIER_SAUVEGARDE, "rb") as f:
            joueur = Joueur.from_dict(decoder(f.read()))
        joueur.a_une_sauvegarde = True
        return joueur
    except FileNotFoundError:
        return None
    except (ValueError, KeyError):
        print("Erreur : le fichier de sauvegarde est corrompu, modifié ou trop ancien.")
        return None


def effacer_sauvegarde():
    """Supprime le fichier de sauvegarde, s'il existe."""
    Path(FICHIER_SAUVEGARDE).unlink(missing_ok=True)
