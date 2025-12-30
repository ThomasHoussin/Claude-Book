# Perplexity Analysis

Analyse de perplexité pour détecter les patterns de texte générés par IA.

## Principe

La **perplexité** mesure à quel point un modèle de langage est "surpris" par un texte.

- **Perplexité basse** → texte prévisible, patterns communs → potentiellement IA
- **Perplexité haute** → texte varié, tournures originales → potentiellement humain

Le script utilise Mistral-7B pour calculer la perplexité de chaque phrase, puis classe les résultats :

| Score | Marqueur | Interprétation |
|-------|----------|----------------|
| < 10  | 🤖🤖 | Très suspect (patterns IA typiques) |
| < 20  | 🤖 | Suspect |
| < 40  | ❓ | Incertain |
| ≥ 40  | 👤 | Probablement humain |

**Seuil d'alerte** : perplexité < 15

### Burstiness

La **burstiness** mesure la variation des longueurs de phrases (en tokens).

- **IA** → phrases uniformes → burstiness basse
- **Humain** → phrases variées → burstiness haute

Deux métriques complémentaires :

| Métrique | Calcul | Usage |
|----------|--------|-------|
| **Burstiness** | écart-type des longueurs | Variation absolue |
| **Fano factor** | variance / moyenne | Variation normalisée (comparable entre textes) |

## Prérequis

### Matériel
- **GPU NVIDIA** avec support CUDA
- **~16 GB VRAM** recommandés (Mistral-7B en float16)

### Logiciel
- Python 3.11+
- CUDA toolkit installé
- Driver NVIDIA récent

Pour les GPU Blackwell (RTX 50xx), PyTorch nightly avec CUDA 12.8 est requis (configuré dans `pyproject.toml`).

## Installation

```bash
cd scripts/perplexity
uv sync  # Installe les dépendances
```

## Usage

### Analyse d'un fichier (détaillée)
```bash
uv run test_perplexity.py chapitre.md
```

Affiche :
- Stats du fichier (mots, phrases, filtrées)
- Stats de perplexité (moyenne, médiane, écart-type)
- Stats de burstiness (std, Fano factor)
- Classement de toutes les phrases par perplexité

### Analyse batch (tous les chapitres)
```bash
uv run test_perplexity.py
```

Tableau récapitulatif de tous les fichiers `chapitre-*.md` dans `story/chapters/`.

### Test d'une phrase unique
```bash
uv run test_perplexity.py -p "Il est fondamental de comprendre que..."
```

### Entrée par pipe
```bash
cat mon_texte.txt | uv run test_perplexity.py
echo "Ma phrase" | uv run test_perplexity.py
```

### Aide
```bash
uv run test_perplexity.py -h
```

## Notes techniques

### Découpage des phrases
- Split sur `.!?` suivi d'une majuscule
- Gestion des guillemets français `«»`
- Fusion des phrases courtes (< 6 mots) avec les adjacentes

### Filtrage
- Éléments markdown ignorés (titres, séparateurs, liens)
- Les phrases très courtes sont fusionnées, pas supprimées

### Concurrence
Un fichier lock (`.perplexity.lock`) empêche les exécutions simultanées pour éviter les conflits GPU.

## Limitations

- La perplexité seule n'est pas un détecteur IA fiable
- Les dialogues courts, expressions courantes et textes simples ont naturellement une perplexité basse
- Résultats à interpréter comme indicateurs, pas comme verdict

## TODO

- [ ] Two-phase processing: use an instruct model for semantic sentence splitting first, then run perplexity analysis. This should improve accuracy by ensuring sentences are split at natural boundaries rather than relying on punctuation heuristics.
