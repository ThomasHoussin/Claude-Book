# Scripts de test détection IA

Tests de différents détecteurs IA sur le texte produit.

## Usage

Chaque test est dans son propre dossier avec un script autonome.

```bash
cd zippy
uv run test_zippy.py ../../story/chapters/chapitre-01.md
```

## Structure

- Chaque script utilise inline script metadata (PEP 723) pour ses dépendances
- Pas de pyproject.toml global - uv gère tout automatiquement
