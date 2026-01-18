# AI Slope Diagnostic Tool

Multi-criteria perplexity analysis for diagnosing predictable text patterns.

## Philosophy

This is **NOT** an "AI vs Human" detector. It diagnoses "boring" text - the **AI Slope** phenomenon where generated text slides toward predictable patterns.

What it detects:
- **Low perplexity** = the model was very confident = well-trodden path
- **Adjacent low blocks** = long sequences without surprises
- **Low variance windows** = suspicious uniformity
- No errors, but no friction either

Use this as a **diagnostic tool**, not a judgment.

## Prerequisites

### Hardware
- **NVIDIA GPU** with CUDA support
- **~16 GB VRAM** recommended (models in float16)

### Software
- **uv** (Python package manager) - https://docs.astral.sh/uv/
- CUDA toolkit installed
- Recent NVIDIA driver

Note: uv manages Python 3.11+ automatically. For Blackwell GPUs (RTX 50xx), PyTorch nightly with CUDA 12.8 is required (configured in `pyproject.toml`).

## Supported Models

| Model | HuggingFace ID | Type |
|-------|----------------|------|
| `ministral8b` (default) | mistralai/Ministral-3-8B-Base-2512 | Multimodal |
| `ministral8b-instruct` | mistralai/Ministral-3-8B-Instruct-2512-BF16 | Multimodal |
| `qwen8b` | Qwen/Qwen3-8B-Base | Causal LM |

## Installation

```bash
cd scripts/detection
uv sync  # Install dependencies
```

## Usage

### Analyze a file
```bash
uv run detection.py chapter.md
```

### Batch analysis (multiple files)
```bash
uv run detection.py chapter-01.md chapter-02.md -o report.txt
```

### Use alternative model
```bash
uv run detection.py -m qwen8b file.md
uv run detection.py -m ministral8b-instruct file.md
```

### Debug mode (threshold calibration)
```bash
uv run detection.py file.md --debug
```

### Help
```bash
uv run detection.py -h
```

## Detection Criteria

Six diagnostic criteria are applied:

| Criterion | Threshold | Detection |
|-----------|-----------|-----------|
| Low perplexity | PPL < 22 | Individual predictable sentences |
| Low std windows | σ < 14 (14-sentence windows) | Uniform perplexity across passages |
| Low burstiness | σ < 5 (sub-sentence lengths) | Uniform sentence rhythm |
| Low PPL density | >30% sentences with PPL < 25 | High concentration of predictable sentences |
| Adjacent low blocks | 4+ consecutive with PPL < 30 | Long sequences without surprises |
| Forbidden words | AI-signal vocabulary | Known AI-overused terms |

### Thresholds Reference

| Constant | Value | Purpose |
|----------|-------|---------|
| SUSPECT_PPL_THRESHOLD | 22 | Low perplexity flag |
| MEDIAN_WARNING_THRESHOLD | 30 | Median warning threshold |
| MAX_SUSPECT_RATE | 0.25 | Max acceptable suspect rate (25%) |
| ADJACENT_PPL_THRESHOLD | 30 | Adjacent block detection |
| MIN_CONSECUTIVE | 4 | Minimum consecutive sentences for block |
| STD_WINDOW_SIZE | 14 | Sliding window for std analysis |
| STD_THRESHOLD | 14.0 | Standard deviation threshold |
| BURSTINESS_WINDOW_SIZE | 14 | Sliding window for burstiness |
| BURSTINESS_THRESHOLD | 5.0 | Burstiness (rhythm) threshold |
| LOW_PPL_DENSITY_WINDOW | 14 | Sliding window for density |
| LOW_PPL_DENSITY_THRESHOLD | 25 | PPL threshold for "low" count |
| LOW_PPL_DENSITY_RATIO | 0.30 | Ratio threshold (30%) |

### Forbidden Words

AI-signal vocabulary detected (case-insensitive):

```
delve, delves, delved, delving
showcasing, showcases, boasts
underscores, underscore, underscoring
comprehending, intricacies, intricate
surpassing, surpasses, garnered
emphasizing, realm, groundbreaking
advancements, aligns
```

## Technical Notes

### Sentence Splitting
- Split on `.!?` followed by uppercase
- Handles French quotation marks `<<>>`
- Merges short sentences (< 20 words) with adjacent ones

### Filtering
- Markdown elements ignored (headers, separators, links)
- Very short sentences are merged, not removed

### Caching
SQLite cache (`.ppl_cache.db`) stores computed perplexity values to avoid redundant computation across runs.

### Concurrency
A lock file (`.perplexity.lock`) prevents simultaneous runs to avoid GPU conflicts.

### File Encoding
Multi-encoding support for input files:
- UTF-8, UTF-16, UTF-16-LE, UTF-16-BE, Latin-1, CP1252

## Debug Mode

The `--debug` flag outputs detailed analysis data:

- **All sentences table**: Index, PPL, word count, flags, forbidden words
- **Sentences near thresholds**: PPL values close to detection boundaries
- **Std windows**: Each window with σ value and flagged status
- **Burstiness windows**: Sub-sentence length variation per window
- **Low PPL density windows**: Ratio of low-PPL sentences per window
- **Adjacent blocks**: Start/end indices and block lengths

Use debug mode for threshold calibration and understanding detection behavior.

## Limitations

- Perplexity alone is not a reliable AI detector
- Short dialogues, common expressions, and simple texts naturally have low perplexity
- Results should be interpreted as **diagnostic signals**, not verdicts
- The tool identifies predictable patterns, not necessarily AI-generated content
