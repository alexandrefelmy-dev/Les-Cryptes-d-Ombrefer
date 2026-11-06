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

- Niveaux de donjon qui s'enchaînent sans fin, de 6 à 9 salles générées au hasard : ennemis, butin et pièges
- Combat au tour par tour contre 16 types d'ennemis, dont 7 qui n'arrivent qu'après le premier niveau
- Les ennemis sans effet compensent avec de meilleures stats
- 4 boss de fin de donjon avec chacun leur propre effet, et 3 boss supplémentaires à partir des niveaux 3, 5 et 7
- 4 actions à chaque tour : **attaquer**, **utiliser un objet**, **fuir**, **se défendre**
- Se défendre double la défense et bloque les nouveaux effets pendant 3 tours, une seule fois par combat, et on ne peut pas fuir un boss
- Dégâts aléatoires, coups critiques (20 %), esquive du joueur (10 %) et défense
- Le héros commence sans défense : seules les armures l'augmentent
- 3 potions de soin, 4 remèdes, 10 armes et 8 armures : plus l'objet est fort, plus il est rare
- Une seule arme et une seule armure portées à la fois : l'ancienne retourne dans l'inventaire
- Boutique : à la sortie d'une salle (30 %), un marchand vend une potion, un remède, une arme et une armure contre de l'or
- XP et montées de niveau, et option 0 pour revenir en arrière dans les menus
- Sauvegarde du héros et de son niveau de donjon après chaque niveau terminé

### Niveaux de donjon

Une nouvelle partie commence au niveau 1. Après chaque boss vaincu, le héros se repose (tous ses PV, plus aucun effet), peut être sauvegardé, puis descend au niveau suivant. À chaque niveau :

- les ennemis et les boss sont plus forts, surtout au niveau 2, pour compenser l'arme du boss gagnée par le héros
- les ennemis dangereux tombent plus souvent et de nouveaux ennemis apparaissent
- les armes et armures fortes sont moins rares, jusqu'à une limite

Le fichier `sauvegarde.sav` contient `niveau_donjon`, le niveau où le héros repartira, et `difficulte`, son mode. Le mode choisi à la création du héros ne peut plus changer : il est repris automatiquement au chargement.

Ce fichier est compressé et signé : il n'est pas lisible, et le jeu refuse de le charger s'il a été modifié.

### Ennemis

| Ennemi | PV | Attaque | Or et XP | Effet | Chances | Dès le niveau |
| --- | --- | --- | --- | --- | --- | --- |
| **Rat géant** | 6 | 4 | 3 | Poison | 24 | 1 |
| **Chauve-souris sanglante** | 7 | 6 | 5 | Saignement | 18 | 1 |
| **Araignée des cryptes** | 9 | 6 | 7 | Poison | 15 | 1 |
| **Gobelin** | 15 | 7 | 9 | Aucun | 13 | 1 |
| **Squelette** | 14 | 9 | 11 | Aucun | 10 | 1 |
| **Ombre rampante** | 16 | 8 | 14 | Affaiblissement | 8 | 1 |
| **Zombie** | 24 | 6 | 15 | Immobilisation | 6 | 1 |
| **Gargouille** | 28 | 9 | 22 | Aucun | 4 | 1 |
| **Goule** | 22 | 12 | 28 | Aucun | 2 | 1 |
| **Scorpion des tombes** | 24 | 12 | 30 | Poison | 10 | 2 |
| **Acolyte noir** | 26 | 12 | 32 | Affaiblissement | 9 | 2 |
| **Chevalier déchu** | 34 | 11 | 38 | Aucun | 8 | 3 |
| **Harpie des tombes** | 28 | 14 | 40 | Saignement | 7 | 3 |
| **Geôlier d'os** | 42 | 11 | 46 | Immobilisation | 6 | 4 |
| **Abomination** | 52 | 12 | 55 | Aucun | 5 | 5 |
| **Démon des cryptes** | 40 | 17 | 60 | Saignement | 4 | 6 |

Les chances de base font 100 au niveau 1, puis les ennemis dangereux gagnent du terrain à chaque niveau. Les PV et l'attaque sont ensuite multipliés par la force du mode et du niveau, et les récompenses par le gain du mode.

### Effets

| Effet | Ce qu'il fait | Infligé par | Parade |
| --- | --- | --- | --- |
| **Poison** | 2 PV par tour pendant 3 tours, malgré la défense, et continue d'une salle à l'autre | Rat géant, Araignée des cryptes, Scorpion des tombes, Spectre de Valbrume, Reine des araignées | Antidote, Cuir traité, Armure d'Ombrefer |
| **Saignement** | 3 PV à chaque attaque portée, pendant 3 tours | Chauve-souris sanglante, Harpie des tombes, Démon des cryptes, Seigneur vampire | Potion coagulante, Gambison matelassé |
| **Immobilisation** | Fait passer un tour, puis répit de 2 tours | Zombie, Geôlier d'os, Golem d'Ombrefer, Dragon d'os | Harnois runique |
| **Affaiblissement** | Attaque réduite de 30 % pendant 3 tours | Ombre rampante, Acolyte noir, Roi liche, Seigneur d'Ombrefer | Potion de vigueur, Broigne de garde, Armure de l'aube |

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
| **Boss possibles au niveau 1** | 3 | 3 | 4 |
| **Force ajoutée au niveau 2** | +53 % | +82 % | +114 % |

Les armes et armures fortes sont aussi moins rares quand la difficulté monte, et le Seigneur vampire n'apparaît qu'en mode Difficile. La force dépend du niveau du donjon et non du niveau du héros.

Un bot simple qui achète en boutique et ne se défend jamais réussit environ 67 % des niveaux en Facile, 40 % en Intermédiaire et 15 % en Difficile, du niveau 1 aux niveaux suivants.

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
| `sauvegarde.py` | Sauvegarde et chargement du héros dans un fichier compressé et signé |

Les tests sont dans `tests/`, avec un fichier `test_*.py` par module.

## 🧠 Notions Python travaillées

- Programmation orientée objet : classes, héritage, `super()`, redéfinition de méthodes, polymorphisme
- Module `random` : `randint`, `random`, `choice`, `choices`
- Boucle de jeu, `match` / `case`, validation des saisies
- Listes d'objets : `append`, `pop`, `enumerate`, compréhensions de liste
- Classes de données avec `dataclass`, sauvegarde en JSON compressée et signée (`zlib`, `base64`, `hmac`)
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
