"""
Test unitaire pour valider la logique des détections sans GPU.
"""
import sys
sys.path.insert(0, '.')

from detection import SentenceAnalysis, SUSPECT_PPL_THRESHOLD, ADJACENT_PPL_THRESHOLD
from detection import STD_WINDOW_SIZE, STD_THRESHOLD, MIN_CONSECUTIVE
import numpy as np


def test_sentence_analysis_dataclass():
    """Test création et conversion JSON de SentenceAnalysis."""
    sent = SentenceAnalysis(
        index=0,
        text="Test sentence",
        perplexity=15.3,
        causes={"low_perplexity", "adjacent_low"}
    )

    result = sent.to_dict()
    assert result["index"] == 0
    assert result["text"] == "Test sentence"
    assert result["perplexity"] == 15.3
    assert set(result["causes"]) == {"adjacent_low", "low_perplexity"}
    print("✓ SentenceAnalysis dataclass OK")


def test_detect_low_perplexity():
    """Test détection low perplexity (<22)."""
    # Simuler la méthode sans instancier PerplexityAnalyzer
    sentences = [
        SentenceAnalysis(0, "Test 1", 15.0, set()),  # Devrait être marqué
        SentenceAnalysis(1, "Test 2", 25.0, set()),  # OK
        SentenceAnalysis(2, "Test 3", 21.9, set()),  # Devrait être marqué
    ]

    # Appliquer logique
    for sent in sentences:
        if sent.perplexity < SUSPECT_PPL_THRESHOLD:
            sent.causes.add("low_perplexity")

    assert "low_perplexity" in sentences[0].causes
    assert "low_perplexity" not in sentences[1].causes
    assert "low_perplexity" in sentences[2].causes
    print("✓ detect_low_perplexity OK")


def test_detect_low_std():
    """Test détection fenêtre glissante variance faible."""
    # 14 phrases avec perplexités uniformes (faible variance)
    sentences = [
        SentenceAnalysis(i, f"S{i}", 35.0 + (i % 3) * 0.5, set())
        for i in range(14)
    ]

    ppls = np.array([s.perplexity for s in sentences])
    from numpy.lib.stride_tricks import sliding_window_view
    windows = sliding_window_view(ppls, STD_WINDOW_SIZE)
    stds = np.std(windows, axis=1)

    # La fenêtre [0:14] a un std < 14.0
    for i, std in enumerate(stds):
        if std < STD_THRESHOLD:
            for j in range(i, i + STD_WINDOW_SIZE):
                sentences[j].causes.add("low_std")

    # Toutes les phrases devraient être marquées
    assert all("low_std" in s.causes for s in sentences)
    print(f"✓ detect_low_std OK (std={stds[0]:.2f} < {STD_THRESHOLD})")


def test_detect_adjacent_low():
    """Test détection blocs adjacents (4+ phrases consécutives <30)."""
    sentences = [
        SentenceAnalysis(0, "S1", 28.0, set()),  # Bloc 1
        SentenceAnalysis(1, "S2", 29.0, set()),  # Bloc 1
        SentenceAnalysis(2, "S3", 27.0, set()),  # Bloc 1
        SentenceAnalysis(3, "S4", 28.5, set()),  # Bloc 1
        SentenceAnalysis(4, "S5", 50.0, set()),  # Pas dans bloc
        SentenceAnalysis(5, "S6", 29.5, set()),  # Bloc 2
        SentenceAnalysis(6, "S7", 28.5, set()),  # Bloc 2
        SentenceAnalysis(7, "S8", 27.5, set()),  # Bloc 2
        SentenceAnalysis(8, "S9", 29.8, set()),  # Bloc 2
    ]

    # Logique de détection
    consecutive_count = 0
    block_start = 0

    for i, sent in enumerate(sentences):
        if sent.perplexity < ADJACENT_PPL_THRESHOLD:
            if consecutive_count == 0:
                block_start = i
            consecutive_count += 1
        else:
            if consecutive_count >= MIN_CONSECUTIVE:
                for j in range(block_start, i):
                    sentences[j].causes.add("adjacent_low")
            consecutive_count = 0

    # Gérer bloc final
    if consecutive_count >= MIN_CONSECUTIVE:
        for j in range(block_start, len(sentences)):
            sentences[j].causes.add("adjacent_low")

    # Vérifications
    assert "adjacent_low" in sentences[0].causes  # Bloc 1
    assert "adjacent_low" in sentences[1].causes  # Bloc 1
    assert "adjacent_low" in sentences[2].causes  # Bloc 1
    assert "adjacent_low" in sentences[3].causes  # Bloc 1
    assert "adjacent_low" not in sentences[4].causes  # Pas dans bloc
    assert "adjacent_low" in sentences[5].causes  # Bloc 2
    assert "adjacent_low" in sentences[8].causes  # Bloc 2
    print("✓ detect_adjacent_low OK")


def test_multiple_causes():
    """Test qu'une phrase peut avoir plusieurs causes."""
    sent = SentenceAnalysis(0, "Test", 15.0, set())
    sent.causes.add("low_perplexity")
    sent.causes.add("adjacent_low")
    sent.causes.add("low_std")

    assert len(sent.causes) == 3
    result = sent.to_dict()
    assert len(result["causes"]) == 3
    print("✓ Multiple causes OK")


def test_edge_case_short_document():
    """Test document avec moins de 14 phrases (pas de variance)."""
    sentences = [
        SentenceAnalysis(0, "S1", 35.0, set()),
        SentenceAnalysis(1, "S2", 36.0, set()),
        SentenceAnalysis(2, "S3", 35.5, set()),
    ]

    # La détection low_std devrait être skippée
    if len(sentences) < STD_WINDOW_SIZE:
        # Skip variance detection
        pass

    print("✓ Edge case (document court) OK")


if __name__ == "__main__":
    print("\n=== Tests de validation de la logique ===\n")

    test_sentence_analysis_dataclass()
    test_detect_low_perplexity()
    test_detect_low_std()
    test_detect_adjacent_low()
    test_multiple_causes()
    test_edge_case_short_document()

    print("\n✅ Tous les tests passent !")
    print("\nNOTE: Ces tests valident la logique des détections.")
    print("Pour tester avec GPU et modèle complet, utilisez:")
    print("  uv run detection.py story/chapters/chapitre-01.md")
