---
name: perplexity-improver
description: Improve chapter perplexity score by rewriting AI-suspect sentences. Use after writing a chapter to reduce detectable AI patterns.
---

# Perplexity Improver Skill

Reduce AI-detectable patterns in chapters by rewriting low-perplexity sentences while preserving narrative integrity.

## Quick Start

```
/perplexity-improver story/chapters/chapitre-05.md
```

Multiple chapters can be analyzed in one run:
```
/perplexity-improver story/chapters/chapitre-01.md story/chapters/chapitre-02.md
```

## Performance Warning

⚠️ **The analysis script is SLOW** (several minutes for model loading and analysis).

- Accumulate several corrections before re-running
- Use at the end of a writing session, not after each edit

## When to Use

- After writing a chapter, before final validation
- When perplexity analysis shows a warning (⚠️)

## Supported Languages

| Code | Language | Techniques File |
|------|----------|-----------------|
| `fr` | Français | `references/rewriting-techniques-fr.md` |
| `en` | English | `references/rewriting-techniques-en.md` |

## Workflow

### Phase 1: Analyze Chapter

**1. Detect language** from chapter content (first 500 characters):
   - Identify language code (`fr`, `en`, etc.)
   - Load corresponding techniques file: `references/rewriting-techniques-{lang}.md`
   - If language not supported → report error and exit

**2. Run perplexity analysis** from the script directory (required for uv to find dependencies):
```bash
cd scripts/perplexity && uv run test_perplexity.py ../../<path/to/chapter.md>
```

**Important**: The `uv run` command must be executed from `scripts/perplexity/` where the `pyproject.toml` is located.

**3. Extract from output:**
- Median perplexity score
- Warning status (median below threshold)
- Suspect rate (percentage of suspect sentences)
- List of suspect sentences sorted by ascending perplexity

### Phase 2: Evaluate Need

**Decision tree:**
- If median ≥ threshold (no warning) AND suspect rate ≤ 20% → **PASS**, report and exit
- If median < threshold (warning) OR suspect rate > 20% → proceed to rewriting

### Phase 3: Rewrite Sentences

Process sentences from lowest perplexity first (most predictable = most suspect).

For each suspect sentence:
1. **Locate** in original chapter
2. **Rewrite** using techniques from `references/rewriting-techniques-{lang}.md`
3. **Preserve** exact meaning and narrative function

**CRITICAL**: Verify that meaning is preserved and rewrites integrate naturally.

### Phase 4: Re-analyze

Run perplexity script on modified chapter.

Compare before/after:
- Median perplexity: target ≥ threshold (no warning)
- Suspect rate: target ≤ 20%
- Suspect sentence count: target reduction

**If still warning:**
- Iterate (max 3 loops)
- Try different rewriting techniques
- Focus on remaining lowest-perplexity sentences

### Phase 5: Finalize

Generate reports in `.work/`:
- `perplexity-report.md`: before/after stats, PASS/FAIL status
- `perplexity-changes.md`: each rewritten sentence with technique used

Ask for validation before applying changes to chapter file.

## Thresholds Reference

All thresholds are defined in `scripts/perplexity/test_perplexity.py` (constants at top of file).

## Interaction Style

- Show progress after each phase
- Present before/after comparisons
- Explain technique choices
- Ask for validation before applying changes to file
