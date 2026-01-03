# Claude Book Framework

A multi-agent framework for writing novels with Claude Code.

## Structure

```
├── CLAUDE.md                 # Orchestrator instructions
├── .claude/skills/           # Reusable skills
│   ├── book-analyzer/        # Extract bible from source book
│   ├── bible-merger/         # Merge multiple analyses
│   ├── story-ideator/        # Generate original storylines
│   └── perplexity-improver/  # Reduce AI-detectable patterns
├── agents/                   # Agent templates (for /agents command)
│   ├── planner.md            # Creates chapter beats
│   ├── writer.md             # Writes chapters
│   ├── style-linter.md       # Checks style compliance
│   ├── character-reviewer.md # Checks character consistency
│   ├── continuity-reviewer.md# Checks timeline/spatial logic
│   └── state-updater.md      # Extracts state changes
├── analysis/                 # Source book analysis
│   ├── src/                  # Source books (txt/md)
│   └── output/               # Generated analyses
├── bible/                    # PERMANENT - never changes during writing
│   ├── style.md              # Writing style rules
│   ├── structure.md          # Narrative structure patterns
│   ├── characters/           # One file per character
│   └── universe/             # Locations and world-building
├── state/                    # TRANSIENT - versioned per chapter
│   ├── current/              # Symlink → latest chapter state
│   ├── chapter-NN/           # Archived states after each chapter
│   └── template/             # State file templates
├── story/                    # The actual story
│   ├── synopsis.md           # Story pitch and summary
│   ├── plan.md               # Chapter outline
│   └── chapters/             # Generated chapters
├── timeline/                 # Event tracking
│   ├── history.md            # All past chapters (append-only)
│   └── current-chapter.md    # Current chapter events
├── ebook/                    # Ebook generation
│   ├── build-ebook.ps1       # PowerShell build script
│   ├── config/book.yaml      # Book metadata and settings
│   └── templates/epub.css    # EPUB styling
├── scripts/perplexity/       # Perplexity analysis script
└── .work/                    # Temporary files (gitignored)
```

## Workflow

1. **Setup**: Fill in `bible/` with your style guide, characters, and locations
2. **Plan**: Write `story/synopsis.md` and `story/plan.md`
3. **Initialize**: Set initial state in `state/template/`, create symlink `state/current/`
4. **Generate**: Run orchestrator - it will:
   - Plan chapter beats (planner agent)
   - Write chapter (writer agent)
   - Run perplexity-improver to reduce cliches and AI patterns
   - Lint style (style-linter agent)
   - Review characters (character-reviewer agent)
   - Review continuity (continuity-reviewer agent)
   - Loop if issues found (max 3 iterations)
   - Update state files (create `state/chapter-NN/`, update symlink)
   - Append to `timeline/history.md`
   - Save final chapter
5. **Export**: Generate ebook with `ebook/build-ebook.ps1`

## Key principles

- **bible/** is read-only during generation
- **state/** is versioned per chapter (`state/chapter-NN/`), symlink `current/` points to latest
- **timeline/history.md** is append-only
- All agents output in `.work/` for review
- Gates must pass before proceeding

## Agent templates

The `agents/` folder contains base prompts for creating Claude Code agents.

**Usage:**
1. In Claude Code, run `/agents` to create a new agent
2. Copy the content from the corresponding template in `agents/`
3. Paste it in the agent description and adjust as needed (language, specific requirements)

This is simpler than manually editing files in `.claude/agents/`.

## Perplexity Improver

Reduces cliches and AI-detectable patterns by rewriting low-perplexity sentences.

```
/perplexity-improver story/chapters/chapitre-05.md
```

- Analyzes text using a local language model
- Identifies "suspect" sentences (too predictable)
- Rewrites them while preserving meaning
- **Note**: Analysis is slow (several minutes for model loading)

Use after writing a chapter, before final validation.

## Ebook Generation

Generates EPUB/MOBI/AZW3 from markdown chapters.

```powershell
cd ebook
.\build-ebook.ps1              # EPUB (default)
.\build-ebook.ps1 -Format all  # All enabled formats
```

**Prerequisites**: Pandoc, powershell-yaml module, Calibre (for MOBI/AZW3)

See [ebook/EBOOK-GUIDE.md](ebook/EBOOK-GUIDE.md) for full documentation.

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
