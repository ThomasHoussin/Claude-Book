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
| < 22  | 🤖 | Suspect |
| < 30  | ❓ | Uncertain |
| ≥ 30  | 👤 | Likely human |

**Alert threshold**: perplexity < 22

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
cd scripts/detection
uv sync  # Install dependencies
```

## Usage

### Analyze a file (detailed)
```bash
uv run detection.py chapter.md
```

Displays:
- File stats (words, sentences, filtered)
- Perplexity stats (mean, median, std dev)
- Burstiness stats (std, Fano factor)
- All sentences ranked by perplexity

### Batch analysis (multiple files)
```bash
uv run detection.py chapter-01.md chapter-02.md -o report.txt
```

### Use alternative model
```bash
uv run detection.py -m qwen8b file.md
```

### Debug mode (threshold calibration)
```bash
uv run detection.py file.md --debug
```

### Help
```bash
uv run detection.py -h
```

## Technical Notes

### Multi-criteria detection

Six detection criteria are applied:

| Criterion | Threshold | Detection |
|-----------|-----------|-----------|
| Low perplexity | PPL < 22 | Individual predictable sentences |
| Low std windows | σ < 14 (14-sentence windows) | Uniform perplexity across passages |
| Low burstiness | σ < 5 (sub-sentence lengths) | Uniform sentence rhythm |
| Low PPL density | >30% sentences with PPL < 25 | High concentration of predictable sentences |
| Adjacent low blocks | 4+ consecutive with PPL < 30 | Long sequences without surprises |
| Forbidden words | AI-signal vocabulary | Known AI-overused terms |

### Sentence splitting
- Split on `.!?` followed by uppercase
- Handles French quotation marks `«»`
- Merges short sentences (< 20 words) with adjacent ones

### Filtering
- Markdown elements ignored (headers, separators, links)
- Very short sentences are merged, not removed

### Caching
SQLite cache (`.ppl_cache.db`) stores computed perplexity values to avoid redundant computation across runs.

### Concurrency
A lock file (`.perplexity.lock`) prevents simultaneous runs to avoid GPU conflicts.

## Limitations

- Perplexity alone is not a reliable AI detector
- Short dialogues, common expressions, and simple texts naturally have low perplexity
- Results should be interpreted as indicators, not verdicts
