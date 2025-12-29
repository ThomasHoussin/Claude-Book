# Claude Book Framework

A multi-agent framework for writing novels with Claude Code.

## Structure

```
├── CLAUDE.md              # Orchestrator instructions
├── skills/                # Reusable skills
│   ├── book-analyzer/     # Extract bible from source book
│   └── bible-merger/      # Merge multiple analyses
├── agents/                # Sub-agent prompts
│   ├── planner.md         # Creates chapter beats
│   ├── writer.md          # Writes chapters
│   ├── style-linter.md    # Checks style compliance
│   ├── character-reviewer.md   # Checks character consistency
│   ├── continuity-reviewer.md  # Checks timeline/spatial logic
│   └── state-updater.md   # Extracts state changes
├── bible/                 # PERMANENT - never changes during writing
│   ├── style.md           # Writing style rules
│   ├── structure.md       # Narrative structure patterns
│   ├── characters/        # One file per character
│   │   └── _template.md
│   └── universe/          # Locations and world-building
│       └── _template.md
├── state/                 # TRANSIENT - updated after each chapter
│   ├── situation.md       # Current story state
│   ├── characters.md      # Current emotional states
│   ├── knowledge.md       # What characters know
│   └── inventory.md       # Object tracking
├── story/                 # The actual story
│   ├── synopsis.md        # Story pitch and summary
│   ├── plan.md            # Chapter outline
│   └── chapters/          # Generated chapters
├── timeline.md            # Append-only event log
└── .work/                 # Temporary files (gitignored)
```

## Workflow

1. **Setup**: Fill in `bible/` with your style guide, characters, and locations
2. **Plan**: Write `story/synopsis.md` and `story/plan.md`
3. **Initialize**: Set initial state in `state/` files
4. **Generate**: Run orchestrator - it will:
   - Plan chapter beats (planner agent)
   - Write chapter (writer agent)
   - Lint style (style-linter agent)
   - Review characters (character-reviewer agent)
   - Review continuity (continuity-reviewer agent)
   - Loop if issues found (max 3 iterations)
   - Update state files
   - Append to timeline
   - Save final chapter

## Key principles

- **bible/** is read-only during generation
- **state/** is overwritten after each chapter
- **timeline.md** is append-only
- All agents output in `.work/` for review
- Gates must pass before proceeding

## Getting started

### Option A: Manual bible creation
1. Copy `bible/characters/_template.md` for each character
2. Copy `bible/universe/_template.md` for each location
3. Fill in `bible/style.md` with your target style
4. Write your synopsis and chapter plan
5. Initialize state files
6. Run: "Write chapter 1"

### Option B: Analyze existing books (recommended for style matching)
1. Place source books in `analysis/src/` (txt or md format)
2. Run: "Analyze analysis/src/[book].txt"
3. Review generated bible in `analysis/output/[book]/`
4. For multiple books: "Merge analysis/output/*/ into bible/"
5. Write your synopsis and chapter plan
6. Initialize state files
7. Run: "Write chapter 1"

## Output language

All prompts are in English but output is in French.
Change `Output language` in agent files if needed.
