# Agents

Agent definitions are located in `.claude/agents/`.

This directory previously contained template files, but they have been consolidated
into the Claude Code agent configuration directory to maintain a single source of truth.

## Available agents

| Agent | Purpose | Model |
|-------|---------|-------|
| chapter-planner | Creates detailed chapter beats | Opus |
| chapter-writer | Writes chapter drafts | Opus |
| style-linter | Validates style guide compliance | Sonnet |
| character-reviewer | Checks character consistency | Sonnet |
| continuity-reviewer | Checks timeline/spatial logic | Sonnet |
| state-updater | Extracts and records state changes | Sonnet |

## Usage

These agents are invoked automatically by the orchestrator (CLAUDE.md).
To modify an agent, edit the corresponding file in `.claude/agents/`.
