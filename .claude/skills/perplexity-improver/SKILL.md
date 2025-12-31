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

## When to Use

- After writing a chapter, before final validation
- When perplexity analysis shows median < 20 (warning threshold)
- When too many sentences have perplexity < 15 (suspect threshold)

## Input Requirements

- Chapter file path (markdown)
- Access to `scripts/perplexity/test_perplexity.py`
- Bible files for gate validation (`bible/style.md`, `bible/characters/*.md`)

## Workflow

### Phase 1: Analyze Chapter

Run perplexity analysis from the script directory (required for uv to find dependencies):
```bash
cd scripts/perplexity && uv run test_perplexity.py ../../<path/to/chapter.md>
```

**Important**: The `uv run` command must be executed from `scripts/perplexity/` where the `pyproject.toml` is located.

Extract from output:
- Median perplexity score
- Warning status (median < 20)
- List of suspect sentences (ppl < 15) sorted by ascending perplexity

### Phase 2: Evaluate Need

**Decision tree:**
- If median ≥ 20 (no warning) → **PASS**, report and exit
- If median < 20 (warning) → proceed to rewriting

### Phase 3: Rewrite Sentences

Process sentences from lowest perplexity first (most predictable = most suspect).

For each suspect sentence:

1. **Locate** in original chapter
2. **Analyze** why it's predictable (common phrase, formulaic structure, etc.)
3. **Rewrite** using techniques from `.claude/skills/perplexity-improver/references/rewriting-techniques.md`:
   - Inversion syntaxique
   - Fragmentation
   - Vocabulaire rare
   - Rythme cassé
   - Sensorialité
   - Voix du personnage
4. **Preserve** exact meaning and narrative function
5. **Minimize** changes to avoid breaking continuity

**CRITICAL**: Before applying any rewrite, verify that:
- The exact meaning is preserved (no information lost, no nuance changed)
- The rewritten phrase integrates naturally with surrounding context
- The rewrite doesn't introduce awkward phrasing or grammatical issues
- Specific details (e.g. "deuxième assiette") are not lost in simplification

### Phase 4: Re-analyze

Run perplexity script on modified chapter.

Compare before/after:
- Median perplexity: target ≥ 20
- Suspect sentence count: target reduction

**If still warning:**
- Iterate (max 3 loops)
- Try different rewriting techniques
- Focus on remaining lowest-perplexity sentences

### Phase 5: Gate Validation

Run all standard gates on modified chapter:

1. **Style-linter**: Verify style.md compliance
2. **Character-reviewer**: Verify character consistency
3. **Continuity-reviewer**: Verify no continuity breaks

**If any gate fails:**
- Identify problematic rewrites
- Revert those specific sentences
- Try alternative rewriting approach

### Phase 6: Finalize

Generate reports:

**`.work/perplexity-report.md`:**
```markdown
# Perplexity Improvement Report

## Chapter: [filename]

## Before
- Median: [X]
- Suspect sentences: [N]

## After
- Median: [Y]
- Suspect sentences: [M]

## Improvement
- Median: +[diff]
- Suspect reduction: [percentage]%

## Status: [PASS/FAIL]
```

**`.work/perplexity-changes.md`:**
```markdown
# Changes Made

## Sentence 1 (ppl: X → Y)
- **Original**: [text]
- **Rewritten**: [text]
- **Technique**: [technique used]

[repeat for each change]
```

**Final action:**
- If all gates pass AND median ≥ 20 → update chapter file
- Otherwise → report failure, keep original

## Output Language

- Reports: French
- Technical output: English

## Thresholds Reference

| Metric | Threshold | Meaning |
|--------|-----------|---------|
| Median perplexity | < 20 | Warning - text may appear AI-generated |
| Sentence perplexity | < 15 | Suspect - high probability of AI pattern |
| Max iterations | 3 | Stop after 3 rewriting attempts |

## Interaction Style

- Show progress after each phase
- Present before/after comparisons
- Explain technique choices
- Ask for validation before applying changes to file
