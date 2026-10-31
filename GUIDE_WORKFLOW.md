# Guide de travail : linters, pipeline et workflow GitHub

Ce guide met en œuvre les trois chantiers de [Evolution_codage.md](Evolution_codage.md).

## 1. pre-commit : vérifier le code avant chaque commit

### Ce qui est vérifié

La configuration est dans [.pre-commit-config.yaml](.pre-commit-config.yaml) :

| Hook | Rôle |
| --- | --- |
| `pylint` | Respect des conventions Python (PEP 8, nommage, docstrings…) |
| `markdownlint-cli2` | Format des fichiers Markdown (règles dans [.markdownlint.yaml](.markdownlint.yaml)) |
| `trailing-whitespace`, `end-of-file-fixer` | Propreté des fichiers (corrigés automatiquement) |
| `check-yaml`, `check-merge-conflict`, `check-added-large-files` | Erreurs classiques |
| `no-commit-to-branch` | Interdit de committer directement sur `main` (voir partie 3) |

### Étape 1.1 : installer pre-commit (une seule fois)

```bash
sudo apt install pipx
pipx ensurepath          # puis rouvrir le terminal
pipx install pre-commit
```

### Étape 1.2 : activer les hooks dans le dépôt (une fois par clone)

```bash
pre-commit install
```

Cette commande crée `.git/hooks/pre-commit`. À partir de là, chaque `git commit` lance les vérifications sur les fichiers modifiés.

### Étape 1.3 : premier passage sur tout le projet

```bash
pre-commit run --all-files
```

Le premier lancement est lent : pre-commit télécharge pylint et Node.js (utilisé par markdownlint). Les lancements suivants sont rapides.

### Utilisation au quotidien

- Un hook **échoue** : le commit est annulé. Corrige les erreurs affichées, refais `git add`, puis `git commit`.
- Un hook **corrige** un fichier (espaces, fin de ligne) : le commit est aussi annulé. Refais simplement `git add` puis `git commit`.
- Ignorer un avertissement pylint précis, et seulement si c'est justifié : `# pylint: disable=nom-du-message` sur la ligne concernée.
- Mettre à jour les versions des outils : `pre-commit autoupdate`.

## 2. Pipeline GitHub : les mêmes vérifications côté serveur

Le fichier [.github/workflows/lint.yml](.github/workflows/lint.yml) lance `pre-commit run --all-files` sur une machine GitHub :

- à chaque `git push`, sur n'importe quelle branche ;
- à chaque pull request vers `main`.

La pipeline réutilise **exactement** la configuration pre-commit. Il n'y a donc qu'un seul endroit à maintenir. Elle protège aussi contre un `git commit --no-verify` qui aurait contourné les hooks locaux.

### Étape 2.1 : pousser le workflow

Il suffit que le fichier soit sur GitHub. Le résultat apparaît dans l'onglet **Actions** du dépôt, et à côté de chaque commit (✅ ou ❌).

### Étape 2.2 : rendre la pipeline obligatoire avant un merge

Sur GitHub : **Settings → Branches → Add branch ruleset** (ou *Add classic branch protection rule*) pour `main` :

1. Cocher **Require a pull request before merging**.
2. Cocher **Require status checks to pass**, puis ajouter le check `pre-commit`.

Ce check n'apparaît dans la liste qu'après une première exécution de la pipeline.

### Étape 2.3 : supprimer automatiquement les branches mergées

**Settings → General → Pull Requests** : cocher **Automatically delete head branches**.

## 3. Workflow de développement : issue → branche → pull request

```text
Issue #12  →  branche 12-boutique  →  commits  →  Pull request  →  merge dans main  →  branche supprimée
```

### Étape 3.1 : créer une issue (une carte = une fonctionnalité)

Sur GitHub : **Issues → New issue → Fonctionnalité**. Le modèle est dans [.github/ISSUE_TEMPLATE/fonctionnalite.md](.github/ISSUE_TEMPLATE/fonctionnalite.md).

**Le titre** : un verbe à l'infinitif et un résultat précis, compréhensible sans ouvrir la carte.

| ❌ À éviter | ✅ Mieux |
| --- | --- |
| `Boutique` | `Ajouter un marchand qui vend des potions dans le donjon` |
| `Bug combat` | `Corriger les PV négatifs affichés après la mort d'un monstre` |
| `Améliorations diverses` | Plusieurs cartes, une par amélioration |

**La description** : elle répond à trois questions.

1. **Pourquoi ?** L'objectif, par exemple « En tant que joueur, je veux acheter des potions afin de survivre plus longtemps ».
2. **Quoi ?** Les critères d'acceptation : une liste de cases à cocher, chacune vérifiable.
3. **Quoi pas ?** Le hors périmètre, pour garder la carte petite.

**Une carte = une fonctionnalité** : si une carte demande plusieurs jours, ou si son titre contient « et », découpe-la en plusieurs cartes.

### Étape 3.2 : créer la branche liée à l'issue

Dans l'issue, panneau de droite **Development → Create a branch** :

- nom proposé : `12-ajouter-un-marchand…`, à raccourcir par exemple en `12-marchand` ;
- branche source : `main`.

La branche est ainsi liée à l'issue.

### Étape 3.3 : récupérer la branche en local

```bash
git switch main
git pull                     # main à jour
git fetch origin
git switch 12-marchand       # crée la branche locale qui suit origin/12-marchand
```

### Étape 3.4 : coder, committer, pousser

```bash
git add donjon.py
git commit -m "feat: ajouter le marchand dans les salles"   # pre-commit vérifie ici
git push
```

Fais de petits commits, chacun avec un message clair. La pipeline tourne à chaque push.

### Étape 3.5 : ouvrir la pull request

Quand la fonctionnalité est finie : sur GitHub, bouton **Compare & pull request** (base : `main`).

- Le titre reprend celui de l'issue.
- Dans la description, écris `Closes #12` : l'issue se fermera automatiquement au merge. Le modèle [.github/pull_request_template.md](.github/pull_request_template.md) le rappelle.
- Attends que la pipeline soit ✅, relis le diff (onglet *Files changed*), puis **Merge pull request**.

### Étape 3.6 : supprimer la branche

Sur GitHub : bouton **Delete branch** après le merge (automatique si l'étape 2.3 est faite).

En local :

```bash
git switch main
git pull                     # récupère le merge
git branch -d 12-marchand    # supprime la branche locale
git fetch --prune            # nettoie les références des branches distantes supprimées
```

Puis on recommence à l'étape 3.1 avec la carte suivante.
