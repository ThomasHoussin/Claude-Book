# Style Checker

Automated technical style verification for chapter drafts.

## Purpose

Pre-validation gate before human style-linter review. Catches technical violations automatically, freeing agents to focus on subjective quality aspects (voice, tone, show vs tell nuance).

## Prerequisites

- **Python 3.10+**
- **uv** (Python package manager)
- No external dependencies (standard library only)

## Installation

```bash
cd scripts/style
uv sync
```

## Usage

### Analyze all chapters
```bash
uv run style_checker.py
```

### Analyze specific file
```bash
uv run style_checker.py ../../story/chapters/chapter-01.md
```

## Checks Performed

### Blocking Errors (must fix)

| Check | Threshold | Action |
|-------|-----------|--------|
| Word count | 2800-3200 words | Expand or trim chapter |
| Dialogue ratio | Minimum 40% | Add more dialogue |
| Sentence length | Maximum 35 words | Break up long sentences |

### Warnings (review recommended)

| Check | Threshold | Suggestion |
|-------|-----------|------------|
| Sentence average | 12-20 words ideal | Vary sentence length |
| Paragraph length | Maximum 15 sentences | Split long paragraphs |
| Long sentences | Warning at 30+ words | Consider breaking up |

### Pattern Detection

| Pattern | Example | Recommendation |
|---------|---------|----------------|
| Forbidden dialogue tags | "hissed", "whispered" | Use "said" or action beats |
| Adverb + said | "said quickly" | Show through action |
| Telling patterns | "felt angry", "was terrified" | Show don't tell |
| Forbidden AI words | "delve", "showcasing", "realm" | Use natural alternatives |
| Quote style | French guillemets | Use American double quotes |
| Word repetition | Same word 3+ times/page | Vary vocabulary |

## Output

Reports are generated in the `.work/` directory:

- **Format**: `chapter-{number}-tech-report-{uuid}.md`
- **Contains**:
  - Statistics (word count, sentence metrics, dialogue ratio)
  - Blocking errors (must be fixed)
  - Warnings (should be reviewed)
  - Agent review section (POV, tense, tone checks for human review)

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All chapters pass (no blocking errors) |
| 1 | Blocking errors found |

## Configuration

Thresholds are defined at the top of `style_checker.py`:

```python
WORD_COUNT_MIN = 2800
WORD_COUNT_MAX = 3200
SENTENCE_AVG_MIN = 12
SENTENCE_AVG_MAX = 20
SENTENCE_MAX = 35
SENTENCE_WARN = 30
PARAGRAPH_MAX_SENTENCES = 15
DIALOGUE_MIN_RATIO = 0.40
WORDS_PER_PAGE = 250
REPETITION_THRESHOLD = 3
CHARACTER_NAMES = set()  # Add project character names
```

## Agent Review Section

The generated report includes a section for human style-linter agent to review:

- POV consistency
- Tense consistency
- Chapter ending type validation
- Internal thought formatting
- Show vs Tell quality
- Sensory details evaluation
- Voice consistency
- Tone/register appropriateness

These subjective aspects require human judgment and cannot be automated.
