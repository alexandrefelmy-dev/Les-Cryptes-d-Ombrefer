"""Effets de statut que les personnages peuvent subir pendant un combat."""

POISON = "Poison"
SAIGNEMENT = "Saignement"
IMMOBILISATION = "Immobilisation"
AFFAIBLISSEMENT = "Affaiblissement"
RAGE = "Rage"  # effet que le Berserker se donne à lui-même

# Durée de chaque effet, en tours de la personne touchée.
DUREES = {POISON: 3, SAIGNEMENT: 3, IMMOBILISATION: 1, AFFAIBLISSEMENT: 3, RAGE: 2}

DEGATS_POISON = 2  # à chaque début de tour, malgré la défense
DEGATS_SAIGNEMENT = 3  # à chaque attaque portée, malgré la défense
FORCE_AFFAIBLI = 0.7  # multiplie l'attaque
FORCE_RAGE = 1.5  # multiplie l'attaque
DEGATS_EN_RAGE = 1  # s'ajoutent aux dégâts reçus

# Après une immobilisation, nombre de tours avant de pouvoir être immobilisé de nouveau.
REPIT_IMMOBILISATION = 3
