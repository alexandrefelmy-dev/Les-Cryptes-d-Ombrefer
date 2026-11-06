# ⚔️ Les Cryptes d'Ombrefer

Jeu de rôle en mode texte, joué dans le terminal, développé en Python
en programmation orientée objet.

Sous le village de Valbrume, une ancienne crypte s'est réveillée.
Incarne un aventurier, affronte les créatures qui la hantent
et survis aux combats !

## 🚀 Lancer le jeu

Prérequis : **Python 3.10 ou plus récent** (le jeu utilise `match` / `case`).

À faire une seule fois, à la racine du projet :

```bash
pip install -e .
```

Puis, pour jouer :

```bash
python -m ombrefer
```

## 🧪 Lancer les tests

```bash
pip install pytest
python -m pytest
```

## 🎮 Fonctionnalités actuelles

- Donjon de 6 à 9 salles générées au hasard : ennemis, butin et pièges
- Combat au tour par tour contre 9 types d'ennemis, du Rat géant très fréquent à la Goule très rare
- 5 ennemis infligent un effet, et les 4 autres compensent avec de meilleures stats
- 4 boss de fin de donjon avec chacun leur propre effet : Golem d'Ombrefer, Spectre de Valbrume, Roi liche et Seigneur vampire
- 4 actions à chaque tour : **attaquer**, **utiliser un objet**, **fuir**, **se défendre**
- Se défendre triple la défense et bloque les nouveaux effets pendant 3 tours, et on ne peut pas fuir un boss
- Dégâts aléatoires, coups critiques (20 %), esquive du joueur (10 %) et défense
- Le héros commence sans défense : seules les armures l'augmentent
- 3 potions de soin, 4 remèdes, 10 armes et 8 armures : plus l'objet est fort, plus il est rare
- Une seule arme et une seule armure portées à la fois : l'ancienne retourne dans l'inventaire
- Boutique : à la sortie d'une salle (30 %), un marchand vend une potion, un remède, une arme et une armure contre de l'or
- XP et montées de niveau, et option 0 pour revenir en arrière dans les menus
- Sauvegarde du héros après une victoire, pour le faire rejouer dans le donjon

### Ennemis

| Ennemi | PV | Attaque | Or et XP | Effet | Apparition |
| --- | --- | --- | --- | --- | --- |
| **Rat géant** | 6 | 4 | 3 | Poison | 24 % |
| **Chauve-souris sanglante** | 7 | 6 | 5 | Saignement | 18 % |
| **Araignée des cryptes** | 9 | 6 | 7 | Poison | 15 % |
| **Gobelin** | 15 | 7 | 9 | Aucun | 13 % |
| **Squelette** | 14 | 9 | 11 | Aucun | 10 % |
| **Ombre rampante** | 16 | 8 | 14 | Affaiblissement | 8 % |
| **Zombie** | 24 | 6 | 15 | Immobilisation | 6 % |
| **Gargouille** | 28 | 9 | 22 | Aucun | 4 % |
| **Goule** | 22 | 12 | 28 | Aucun | 2 % |

Les PV et l'attaque sont ensuite multipliés par la force du mode, et les récompenses par son gain.

### Effets

| Effet | Ce qu'il fait | Infligé par | Parade |
| --- | --- | --- | --- |
| **Poison** | 2 PV par tour pendant 3 tours, malgré la défense, et continue d'une salle à l'autre | Rat géant, Araignée des cryptes, Spectre de Valbrume | Antidote, Cuir traité, Armure d'Ombrefer |
| **Saignement** | 3 PV à chaque attaque portée, pendant 3 tours | Chauve-souris sanglante, Seigneur vampire | Potion coagulante, Gambison matelassé |
| **Immobilisation** | Fait passer un tour, puis répit de 2 tours | Zombie, Golem d'Ombrefer | Harnois runique |
| **Affaiblissement** | Attaque réduite de 30 % pendant 3 tours | Ombre rampante, Roi liche | Potion de vigueur, Broigne de garde, Armure de l'aube |

Un coup qui touche a 25 % de chances d'infliger l'effet de l'ennemi, 40 % pour un boss et 30 % pour une arme à effet. La Panacée guérit tout sauf l'immobilisation. Une armure protège d'un seul effet, et se défendre bloque les nouveaux effets, sans guérir ceux déjà subis.

### Modes de difficulté

| | Facile | Intermédiaire | Difficile |
| --- | --- | --- | --- |
| **PV / attaque de départ** | 41 / 8 | 33 / 8 | 24 / 7 |
| **Force des ennemis** | ×1,15 | ×1,25 | ×1,35 |
| **Pièges** | 5 % | 10 % | 20 % |
| **Potions** | 55 % | 50 % | 40 % |
| **Or et XP des ennemis** | ×1 | ×1,25 | ×1,5 |
| **Récompenses du boss** | ×1 | ×1,5 | ×2 |
| **Boss possibles** | 3 | 3 | 4 |

Les armes et armures fortes sont aussi moins rares quand la difficulté monte, et le Seigneur vampire n'apparaît qu'en mode Difficile. Pour garder le défi avec un héros sauvegardé, les ennemis gagnent 37 % de force par niveau du héros.

Un bot simple qui achète en boutique gagne environ 67 % de ses parties en Facile, 40 % en Intermédiaire et 15 % en Difficile, avec un héros neuf.

## 📁 Structure du projet

Le code du jeu est dans `src/ombrefer/` :

| Fichier | Contenu |
| --- | --- |
| `__main__.py` | Point d'entrée de `python -m ombrefer` |
| `main.py` | Menu principal, choix de la difficulté et lancement d'une partie |
| `personnage.py` | Classes `Personnage`, `Joueur` (avec inventaire) et `Ennemi` |
| `effet.py` | Noms et réglages des effets |
| `objet.py` | Classes `Objet`, `Potion`, `Remede`, `Arme` et `Armure`, affichage de l'inventaire |
| `combat.py` | Déroulement du combat |
| `donjon.py` | Modes de difficulté, génération des salles et exploration |
| `boutique.py` | Affichage de la boutique et achats |
| `sauvegarde.py` | Sauvegarde et chargement du héros en JSON |

Les tests sont dans `tests/`, avec un fichier `test_*.py` par module.

## 🧠 Notions Python travaillées

- Programmation orientée objet : classes, héritage, `super()`, redéfinition de méthodes, polymorphisme
- Module `random` : `randint`, `random`, `choice`, `choices`
- Boucle de jeu, `match` / `case`, validation des saisies
- Listes d'objets : `append`, `pop`, `enumerate`, compréhensions de liste
- Classes de données avec `dataclass`, sauvegarde en JSON
- Organisation d'un projet : package dans `src/`, `pyproject.toml`
- Tests avec `pytest`, linters et intégration continue avec GitHub Actions

## 🗺️ Avancement

- [x] Étape 1 : classe `Personnage`
- [x] Étape 2 : héritage (`Joueur` et `Ennemi`)
- [x] Étape 3 : le hasard et les attaques
- [x] Étape 4 : combat au tour par tour
- [x] Étape 5 : objets et inventaire
- [x] Étape 6 : le donjon
- [x] Étape 7 : la boucle de jeu
- [x] Étape 8 : sauvegarde et chargement (JSON)
- [x] Étape 9 : finitions (boss final, montée de niveau, tests)
- [ ] Étape 10 (bonus) : version graphique avec Pygame

## 👤 Auteur

[alexandrefelmy-dev](https://github.com/alexandrefelmy-dev)
