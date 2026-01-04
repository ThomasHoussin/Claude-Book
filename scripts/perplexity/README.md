# Perplexity Analysis

Perplexity analysis to detect AI-generated text patterns.

## Principle

**Perplexity** measures how "surprised" a language model is by a text.

- **Low perplexity** → predictable text, common patterns → potentially AI
- **High perplexity** → varied text, original phrasing → potentially human

The script uses Ministral-3-8B (by default) to compute the perplexity of each sentence, then classifies results:

| Score | Marker | Interpretation |
|-------|--------|----------------|
| < 10  | 🤖🤖 | Highly suspect (typical AI patterns) |
| < 20  | 🤖 | Suspect |
| < 40  | ❓ | Uncertain |
| ≥ 40  | 👤 | Likely human |

**Alert threshold**: perplexity < 18

### Burstiness

**Burstiness** measures the variation in sentence lengths (in tokens).

- **AI** → uniform sentences → low burstiness
- **Human** → varied sentences → high burstiness

Two complementary metrics:

| Metric | Calculation | Usage |
|--------|-------------|-------|
| **Burstiness** | standard deviation of lengths | Absolute variation |
| **Fano factor** | variance / mean | Normalized variation (comparable across texts) |

## Prerequisites

### Hardware
- **NVIDIA GPU** with CUDA support
- **~16 GB VRAM** recommended (Ministral-3-8B in float16)

### Software
- **uv** (Python package manager) - https://docs.astral.sh/uv/
- CUDA toolkit installed
- Recent NVIDIA driver

Note: uv manages Python 3.11+ automatically. For Blackwell GPUs (RTX 50xx), PyTorch nightly with CUDA 12.8 is required (configured in `pyproject.toml`).

## Installation

```bash
cd scripts/perplexity
uv sync  # Install dependencies
```

## Usage

### Analyze a file (detailed)
```bash
uv run test_perplexity.py chapter.md
```

Displays:
- File stats (words, sentences, filtered)
- Perplexity stats (mean, median, std dev)
- Burstiness stats (std, Fano factor)
- All sentences ranked by perplexity

### Batch analysis (all chapters)
```bash
uv run test_perplexity.py
```

Summary table of all `chapitre-*.md` files in `story/chapters/`.

### Test a single sentence
```bash
uv run test_perplexity.py -p "It is fundamental to understand that..."
```

### Pipe input
```bash
cat my_text.txt | uv run test_perplexity.py
echo "My sentence" | uv run test_perplexity.py
```

### Help
```bash
uv run test_perplexity.py -h
```

## Technical Notes

### Sentence splitting
- Split on `.!?` followed by uppercase
- Handles French quotation marks `«»`
- Merges short sentences (< 6 words) with adjacent ones

### Filtering
- Markdown elements ignored (headers, separators, links)
- Very short sentences are merged, not removed

### Concurrency
A lock file (`.perplexity.lock`) prevents simultaneous runs to avoid GPU conflicts.

## Limitations

- Perplexity alone is not a reliable AI detector
- Short dialogues, common expressions, and simple texts naturally have low perplexity
- Results should be interpreted as indicators, not verdicts

## TODO

- [ ] Two-phase processing: use an instruct model for semantic sentence splitting first, then run perplexity analysis. This should improve accuracy by ensuring sentences are split at natural boundaries rather than relying on punctuation heuristics.
