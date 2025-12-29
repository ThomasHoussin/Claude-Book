# Analysis Module

Source books go here for analysis. Results are generated in `output/`.

## Structure

```
analysis/
├── src/           # Place source books here (txt or md)
└── output/        # Generated bibles (one per book)
    └── [book]/
        ├── style.md
        ├── structure.md
        ├── characters/
        └── universe/
```

## Skills

Analysis uses skills from `skills/`:
- **book-analyzer**: Extracts bible from a single book
- **bible-merger**: Consolidates multiple analyses

## Workflow

1. Place books in `src/`
2. Run: `Analyze analysis/src/[book].txt`
3. Review output in `analysis/output/[book]/`
4. For series: `Merge analysis/output/*/ into bible/`
