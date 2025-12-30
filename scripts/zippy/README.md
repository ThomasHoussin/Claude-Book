# Test Zippy

Détecteur IA basé sur la compression (https://github.com/thinkst/zippy).

## Usage

```bash
uv run test_zippy.py              # tous les chapitres
uv run test_zippy.py fichier.md   # fichier spécifique
```

## Résultats (2024-12-30)

16 chapitres testés : tous classés **Human** (scores 0.23-0.26).

## Limitation importante

Zippy est **biaisé vers l'anglais**. Son corpus de référence est en anglais.

Test de validation :
- Texte IA typique en anglais → **AI** (0.03)
- Même texte traduit en français → **Human** (0.05)

**Conclusion** : Les résultats "Human" sur du texte français ne sont pas fiables. Zippy n'est pas adapté pour tester du contenu en français.
