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

- 5 classes de héros avec leurs stats et une attaque spéciale à recharge : Guerrier, Voleur, Mage, Nécromancien et Berserker
- 10 niveaux de donjon de 6 à 9 salles générées au hasard : ennemis, butin et pièges
- Une fin du jeu au niveau 10, et un succès différent à gagner dans chaque mode de difficulté
- Mode Enfer : la difficulté du mode Difficile, mais la mort efface le héros, avec un record du plus haut niveau atteint et un succès ultime
- Combat au tour par tour contre 16 types d'ennemis, dont 7 qui n'arrivent qu'après le premier niveau
- Les ennemis sans effet compensent avec de meilleures stats
- 4 boss de fin de donjon avec chacun leur propre effet, et 3 boss supplémentaires à partir des niveaux 3, 5 et 7
- 4 actions à chaque tour : **attaquer**, **utiliser un objet**, **fuir**, **se défendre**
- Se défendre double la défense et bloque les nouveaux effets pendant 3 tours, une seule fois par combat, et on ne peut pas fuir un boss
- Dégâts aléatoires, coups critiques (20 %), esquive du joueur (10 %) et défense
- Le héros commence sans défense : seules les armures l'augmentent
- 3 potions de soin, 4 remèdes, 17 armes et 8 armures : plus l'objet est fort, plus il est rare
- Les armes ont une famille : selon la classe, elles donnent un gros bonus, un malus ou rien de spécial
- Une seule arme et une seule armure portées à la fois : l'ancienne retourne dans l'inventaire
- Boutique : à la sortie d'une salle (30 %), un marchand vend une potion, un remède, une arme et une armure contre de l'or
- 5 événements rares à la sortie d'une salle (8 %), avec des choix risqués hors combat : Fontaine, Autel maudit, Coffre piégé, Prisonnier et Forge abandonnée
- XP et montées de niveau, et option 0 pour revenir en arrière dans les menus
- Sauvegarde du héros et de son niveau de donjon après chaque niveau terminé

### Classes de héros

La classe se choisit à la création du héros et ne change plus. Les PV et l'attaque s'appliquent aux valeurs de base du mode.

| Classe | PV | Attaque | Particularité | Attaque spéciale | Recharge |
| --- | --- | --- | --- | --- | --- |
| **Guerrier** | +10 % | +0 | Aucune | **Coup puissant :** dégâts doublés, sans petit jet | 6 tours |
| **Voleur** | −15 % | +1 | Critique 30 %, esquive 15 % | **Frappe sournoise :** critique assuré et saignement | 4 tours |
| **Mage** | −20 % | +2 | Aucune | **Éclair :** 1,25 × l'attaque, sans hasard, et affaiblissement | 6 tours |
| **Nécromancien** | +0 % | +0 | Aucune | **Drain de vie :** coup normal, et soin égal aux dégâts | 3 tours |
| **Berserker** | +15 % | +2 | Ne peut pas se défendre | **Rage :** attaque ×1,5 pendant 3 attaques, 1 dégât de plus reçu | 5 tours |

La recharge ne compte que les tours de combat et continue d'un combat à l'autre : l'utiliser sur un petit ennemi peut en priver contre le boss. Le repos entre deux niveaux la remet à zéro.

### Armes et classes

Chaque arme appartient à une famille. Selon la classe, son bonus d'attaque est multiplié par 1,5 (gros bonus) ou par 0,5 (malus), ou reste inchangé. L'inventaire et la boutique affichent la valeur réelle pour le héros.

| Classe | Gros bonus | Malus | Neutre |
| --- | --- | --- | --- |
| **Guerrier** | Épée | Dague, Bâton | Faux, Hache, Lance |
| **Voleur** | Dague | Bâton, Hache | Épée, Faux, Lance |
| **Mage** | Bâton | Épée, Hache | Dague, Faux, Lance |
| **Nécromancien** | Faux | Épée, Hache | Dague, Bâton, Lance |
| **Berserker** | Hache | Dague, Bâton | Épée, Faux, Lance |

Chaque famille favorite compte trois armes, et les deux lances sont neutres pour tout le monde. Le prix suit le bonus de base, donc une arme adaptée à sa classe est une bonne affaire.

### Niveaux de donjon

Une nouvelle partie commence au niveau 1. Après chaque boss vaincu, le héros se repose (tous ses PV, plus aucun effet), peut être sauvegardé, puis descend au niveau suivant. Le niveau 10 est le dernier : vaincre son boss termine le jeu. À chaque niveau :

- les ennemis et les boss sont plus forts, surtout au niveau 2, pour compenser l'arme du boss gagnée par le héros
- les ennemis dangereux tombent plus souvent et de nouveaux ennemis apparaissent
- les armes et armures fortes sont moins rares, jusqu'à une limite

Le fichier `sauvegarde.sav` contient `niveau_donjon`, le niveau où le héros repartira, ainsi que `difficulte` et `classe`. Le mode et la classe choisis à la création du héros ne peuvent plus changer : ils sont repris automatiquement au chargement.

Ce fichier est compressé et signé : il n'est pas lisible, et le jeu refuse de le charger s'il a été modifié.

### Fin du jeu et succès

Vaincre le boss du niveau 10 raconte la fin du jeu propre au mode choisi et débloque son succès. La partie s'arrête alors, sans proposer de sauvegarde ni de niveau 11. La sauvegarde précédente reste chargeable.

| Mode | Succès |
| --- | --- |
| **Facile** | Rescapé d'Ombrefer |
| **Intermédiaire** | Briseur d'Ombrefer |
| **Difficile** | Légende de Valbrume |
| **Enfer** | Immortel d'Ombrefer, le succès ultime |

Le choix 3 du menu principal affiche les succès obtenus et le record du mode Enfer. Ils sont gardés dans `succes.sav`, compressé et signé comme la sauvegarde : ils restent acquis après la mort du héros, et même si une autre sauvegarde remplace la sienne.

### Mode Enfer

Le mode Enfer reprend tous les réglages du mode Difficile. La seule différence est qu'il n'y a pas de seconde chance :

- la mort efface le héros, sans retour possible à sa dernière sauvegarde
- entrer dans un niveau consomme la sauvegarde : quitter le jeu en plein niveau revient donc à mourir
- le héros peut toujours être sauvegardé entre deux niveaux, pour reprendre plus tard
- la sauvegarde d'un autre héros n'est jamais touchée, sauf si ce héros d'Enfer sauvegarde par-dessus

Le plus haut niveau atteint est retenu avec le nom et la classe du héros, dès qu'il entre dans ce niveau. Terminer ce mode donne le succès ultime.

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

### Événements

À la sortie d'une salle, un seul tirage décide de ce qui attend le héros : un marchand (30 %), un événement (8 %) ou rien. Il n'y en a donc jamais deux à la fois, et rien après le boss. Les cinq événements sont aussi fréquents, et chacun reste proposé après une fuite, comme le marchand.

Le jeu n'affiche jamais les chances, seulement des indices. Le héros peut revenir au menu pour se soigner avant de décider, ou passer à la salle suivante sans rien tenter. Une perte de PV d'événement ne tue jamais : les PV s'arrêtent à 1, et l'armure adaptée bloque le poison. Attention au poison reçu à 1 PV, qui peut achever le héros à l'entrée de la salle suivante.

| Événement | Choix | Ce qui peut arriver |
| --- | --- | --- |
| **Fontaine** | Boire | 55 % : +40 % des PV max et guérit tous les effets. 30 % : rien. 15 % : −15 % des PV max et poison |
| | Remplir une fiole | Une petite potion de soin (+10 PV) |
| **Autel maudit** | Offrir son sang | −20 % des PV max, +6 % d'attaque pour toujours (au moins +1). Refusé s'il reste trop peu de PV |
| | Sceller un pacte | Jusqu'à la fin du niveau, 60 % : +25 % d'attaque. 40 % : −15 % d'attaque |
| **Coffre piégé** | Forcer | 60 % (Voleur 80 %) : une arme ou une armure. Sinon −25 % des PV max et poison |
| | Crocheter | 90 % : 20 or × niveau du donjon. 10 % : −10 % des PV max et poison |
| **Prisonnier** | Libérer | 50 % : allié qui retire 15 % de ses PV au boss du niveau. 25 % : il s'enfuit. 25 % : il vole 25 % de l'or |
| | Prendre sa bourse | 20 or × niveau du donjon, et 30 % de risque d'affaiblissement |
| **Forge abandonnée** | Reforger l'arme (15 or × niveau du donjon) | 60 % : +25 % de bonus (au moins +2). 25 % : rien. 15 % : −15 % de bonus |
| | Reforger l'armure (15 or × niveau du donjon) | 70 % : +1 défense. 20 % : rien. 10 % : −1 défense |

### Modes de difficulté

| | Facile | Intermédiaire | Difficile |
| --- | --- | --- | --- |
| **PV / attaque de base** | 35 / 8 | 28 / 8 | 21 / 7 |
| **Force des ennemis** | ×1,23 | ×1,36 | ×1,5 |
| **Pièges** | 5 % | 10 % | 20 % |
| **Potions** | 55 % | 50 % | 40 % |
| **Or et XP des ennemis** | ×1 | ×1,25 | ×1,5 |
| **Récompenses du boss** | ×1 | ×1,5 | ×2 |
| **Boss possibles au niveau 1** | 3 | 3 | 4 |
| **Force ajoutée au niveau 2** | +56 % | +85 % | +120 % |

Les armes et armures fortes sont aussi moins rares quand la difficulté monte, et le Seigneur vampire n'apparaît qu'en mode Difficile. La force dépend du niveau du donjon et non du niveau du héros.

Un bot simple qui achète en boutique, utilise son attaque spéciale dès qu'elle est prête et ne se défend jamais réussit en moyenne, sur les 5 classes et les niveaux 1 à 8, environ 67 % des niveaux en Facile, 40 % en Intermédiaire et 15 % en Difficile.

## 📁 Structure du projet

Le code du jeu est dans `src/ombrefer/` :

| Fichier | Contenu |
| --- | --- |
| `__main__.py` | Point d'entrée de `python -m ombrefer` |
| `main.py` | Menu principal, choix de la difficulté, lancement d'une partie et fin du jeu |
| `personnage.py` | Classes `Personnage`, `Joueur` (avec inventaire) et `Ennemi` |
| `classe.py` | Classes de héros : stats et attaques spéciales |
| `effet.py` | Noms et réglages des effets |
| `objet.py` | Classes `Objet`, `Potion`, `Remede`, `Arme` et `Armure`, affichage de l'inventaire |
| `combat.py` | Déroulement du combat |
| `donjon.py` | Modes de difficulté, génération des salles et exploration |
| `boutique.py` | Affichage de la boutique et achats |
| `evenement.py` | Événements hors combat : Fontaine, Autel maudit, Coffre piégé, Prisonnier et Forge abandonnée |
| `succes.py` | Succès de fin de jeu, un par mode de difficulté, et record du mode Enfer |
| `sauvegarde.py` | Sauvegarde, chargement et effacement du héros, dans un fichier compressé et signé |

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
