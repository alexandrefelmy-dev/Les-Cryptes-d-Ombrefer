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
- Combat au tour par tour contre 5 types d'ennemis (Rat géant, Gobelin, Squelette, Zombie, Goule)
- 4 boss de fin de donjon : Golem d'Ombrefer, Spectre de Valbrume, Roi liche et Seigneur vampire
- 4 actions à chaque tour : **attaquer**, **utiliser un objet**, **fuir**, **se défendre**
- Se défendre double la défense pendant 3 tours, et on ne peut pas fuir un boss
- Dégâts aléatoires, coups critiques (20 %), esquive du joueur (10 %) et défense
- 3 potions de soin et 10 armes : plus l'objet est fort, plus il est rare
- XP et montées de niveau, et option 0 pour revenir en arrière dans les menus
- Sauvegarde du héros après une victoire, pour le faire rejouer dans le donjon

### Modes de difficulté

| | Facile | Intermédiaire | Difficile |
| --- | --- | --- | --- |
| **PV / attaque / défense de départ** | 32 / 8 / 2 | 28 / 8 / 2 | 25 / 7 / 2 |
| **Force des ennemis** | ×1,15 | ×1,25 | ×1,35 |
| **Pièges** | 5 % | 10 % | 20 % |
| **Potions** | 55 % | 50 % | 40 % |
| **Or et XP des ennemis** | ×1 | ×1,25 | ×1,5 |
| **Récompenses du boss** | ×1 | ×1,5 | ×2 |
| **Boss possibles** | 3 | 3 | 4 |

Les armes fortes sont aussi moins rares quand la difficulté monte, et le Seigneur vampire n'apparaît qu'en mode Difficile. Pour garder le défi avec un héros sauvegardé, les ennemis gagnent 30 % de force par niveau du héros.

Un bot simple gagne environ 66 % de ses parties en Facile, 40 % en Intermédiaire et 15 % en Difficile, avec un héros neuf.

## 📁 Structure du projet

Le code du jeu est dans `src/ombrefer/` :

| Fichier | Contenu |
| --- | --- |
| `__main__.py` | Point d'entrée de `python -m ombrefer` |
| `main.py` | Menu principal, choix de la difficulté et lancement d'une partie |
| `personnage.py` | Classes `Personnage`, `Joueur` (avec inventaire) et `Ennemi` |
| `objet.py` | Classes `Objet`, `Potion` et `Arme`, affichage de l'inventaire |
| `combat.py` | Déroulement du combat |
| `donjon.py` | Modes de difficulté, génération des salles et exploration |
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
