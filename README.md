# ⚔️ Les Cryptes d'Ombrefer

Jeu de rôle en mode texte, joué dans le terminal, développé en Python
en programmation orientée objet.

Sous le village de Valbrume, une ancienne crypte s'est réveillée.
Incarne un aventurier, affronte les créatures qui la hantent
et survis aux combats !

## 🚀 Lancer le jeu

Prérequis : **Python 3.10 ou plus récent** (le jeu utilise `match` / `case`).

```bash
python combat.py
```

## 🎮 Fonctionnalités actuelles

- Combat au tour par tour contre un ennemi tiré au sort (Gobelin, Rat géant, Squelette)
- 4 actions à chaque tour : **attaquer**, **utiliser un objet**, **fuir**, **se défendre**
- Dégâts aléatoires, coups critiques (20 %), esquive du joueur (10 %) et défense
- Inventaire d'objets : potions de soin et armes qui augmentent l'attaque
- Une potion ne peut pas être bue quand le joueur a déjà tous ses PV
- Trois fins possibles : victoire (avec récompense en or), défaite ou fuite

## 📁 Structure du projet

| Fichier | Contenu |
| --- | --- |
| `personnage.py` | Classes `Personnage`, `Joueur` (avec inventaire) et `Ennemi` |
| `objet.py` | Classes `Objet`, `Potion` et `Arme`, affichage de l'inventaire |
| `combat.py` | Déroulement du combat et point d'entrée du jeu |

## 🧠 Notions Python travaillées

- Programmation orientée objet : classes, héritage, `super()`, redéfinition de méthodes, polymorphisme
- Module `random` : `randint`, `random`, `choice`
- Boucle de jeu, `match` / `case`, validation des saisies
- Listes d'objets : `append`, `pop`, `enumerate`, compréhensions de liste
- Découpage en modules et `import`

## 🗺️ Avancement

- [x] Étape 1 : classe `Personnage`
- [x] Étape 2 : héritage (`Joueur` et `Ennemi`)
- [x] Étape 3 : le hasard et les attaques
- [x] Étape 4 : combat au tour par tour
- [x] Étape 5 : objets et inventaire
- [ ] Étape 6 : le donjon
- [ ] Étape 7 : la boucle de jeu
- [ ] Étape 8 : sauvegarde et chargement (JSON)
- [ ] Étape 9 : finitions (boss final, montée de niveau, tests)
- [ ] Étape 10 (bonus) : version graphique avec Pygame

## 👤 Auteur

[alexandrefelmy-dev](https://github.com/alexandrefelmy-dev)
