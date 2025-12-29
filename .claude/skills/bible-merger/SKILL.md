---
name: bible-merger
description: Merge multiple book analyses into a unified bible. Use after analyzing several books from a series to consolidate characters, style patterns, and structure into a single canonical reference.
---

# Bible Merger

Consolidate multiple book analyses into one canonical bible.

## Quick Start

```bash
# Merge all analyses
Merge analysis/output/*/ into bible/
```

## When to Use

After analyzing multiple books from the same series or author. The merger:
- Identifies consistent patterns (→ rules)
- Tracks character evolution
- Extracts the author's true voice

## Merge Process

### 1. Inventory sources
List all `analysis/output/*/` directories to merge.

### 2. Merge style
Compare `style.md` across all sources:
- **Keep**: patterns appearing in ALL books
- **Range**: metrics with variation (use min-max range)
- **Flag**: book-specific vocabulary (note but don't enforce)
- **Pick**: best reference excerpts from each

### 3. Merge characters folder
For each character appearing in multiple books:
- **Core traits**: keep only if demonstrated in ALL appearances
- **Evolution**: note changes across books
- **Speech**: merge dialogue examples, identify constants
- **Relationships**: note any evolution

For single-book characters:
- Include if significant
- Mark as "source: [book]"

### 4. Merge structure
Identify the formula:
- Chapter length range across all books
- Consistent act structure
- Patterns appearing in every book

### 5. Merge universe folder
- **Recurring locations**: full treatment, consolidate descriptions
- **Book-specific locations**: include with source note
- **Contradictions**: later books take precedence

## Conflict Resolution

| Conflict Type | Resolution |
|--------------|------------|
| Style patterns | Prefer most common |
| Character traits | Prefer shown-in-action over told |
| Facts | Prefer later books |
| All conflicts | Document: "Sources vary: book-1 says X, book-3 says Y" |

## Output

### Merge report
Generate `analysis/merge-report.md`:
```markdown
# Merge Report

## Sources
- [Book 1]: [path]
- [Book 2]: [path]

## Consistency Analysis
- Highly consistent: [list]
- Some variation: [list]  
- Book-specific: [list]

## Character Coverage
- [Character]: appears in [X/Y] books

## Conflicts Resolved
- [Description]: chose [resolution]
```

### Merged bible
Complete `bible/` directory with consolidated files.

## Output Language
French (for content)
English (for report and metadata)
