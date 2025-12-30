# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "thinkst-zippy",
# ]
# ///
"""
Test de détection IA avec Zippy (basé sur compression).
Usage: uv run test_zippy.py [fichier]

Sans argument: teste tous les chapitres de story/chapters/
Avec argument: teste le fichier spécifié
"""

import subprocess
import sys
from pathlib import Path

# Chemin vers les chapitres (relatif au script)
CHAPTERS_DIR = Path(__file__).parent.parent.parent / "story" / "chapters"


def test_file(fichier: Path) -> tuple[str, str, float]:
    """Teste un fichier et retourne (nom, classification, score)."""
    env = {"PYTHONUTF8": "1"}
    result = subprocess.run(
        ["zippy", str(fichier)],
        capture_output=True,
        text=True,
        env=env,
    )
    # Parse le résultat: ('Human', 0.24) ou ('AI', 0.87)
    output = result.stdout.strip().split("\n")[-1]
    # Extrait classification et score
    if "Human" in output:
        classification = "Human"
    else:
        classification = "AI"
    score = float(output.split(",")[-1].strip().rstrip(")"))
    return fichier.name, classification, score


def main():
    if len(sys.argv) >= 2:
        # Mode fichier unique
        fichier = Path(sys.argv[1])
        if not fichier.exists():
            print(f"Fichier non trouvé: {fichier}")
            sys.exit(1)
        name, classification, score = test_file(fichier)
        print(f"{name}: {classification} ({score:.2f})")
    else:
        # Mode batch: tous les chapitres
        if not CHAPTERS_DIR.exists():
            print(f"Dossier non trouvé: {CHAPTERS_DIR}")
            sys.exit(1)

        chapitres = sorted(CHAPTERS_DIR.glob("chapitre-*.md"))
        if not chapitres:
            print("Aucun chapitre trouvé")
            sys.exit(1)

        print(f"Test de {len(chapitres)} chapitres:\n")
        print(f"{'Chapitre':<25} {'Résultat':<10} {'Score':>8}")
        print("-" * 45)

        for chapitre in chapitres:
            name, classification, score = test_file(chapitre)
            print(f"{name:<25} {classification:<10} {score:>8.2f}")


if __name__ == "__main__":
    main()
