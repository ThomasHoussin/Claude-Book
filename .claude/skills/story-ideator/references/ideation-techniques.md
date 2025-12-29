# Ideation Techniques Reference

## Collision Matrix Method

Create unexpected combinations by crossing categories dynamically from the bible.

### Character × Unusual Role Matrix

For each character in `bible/characters/`, identify:
1. **Usual role**: Leader? Follower? Protector? Comic relief? Voice of reason?
2. **Core trait**: Brave? Cautious? Impulsive? Analytical?
3. **Inversion potential**: What's the OPPOSITE of their usual function?

| Character | Usual Role | Inversion Seed |
|-----------|------------|----------------|
| [Extract from bible] | [Identify pattern] | "What if they had to [opposite]?" |

### Location × Unexpected Use Matrix

For each location in `bible/universe/`, identify:
1. **Usual function**: Safe haven? Danger zone? Discovery site? Transit point?
2. **Atmosphere**: Cozy? Threatening? Mysterious? Mundane?
3. **Twist potential**: What if it served the OPPOSITE function?

| Location | Usual Function | Twist Seed |
|----------|---------------|------------|
| [Extract from bible] | [Identify pattern] | "What if it became [opposite]?" |

### Mystery/Conflict Type Variations

Based on `bible/structure.md` genre:

| If genre is... | Common types to AVOID repeating | Fresh angles to explore |
|----------------|--------------------------------|------------------------|
| Mystery | Whodunit, hidden treasure | Why-dunit, moral puzzle |
| Adventure | Rescue, exploration | Escape, protection |
| Thriller | Chase, countdown | Infiltration, deception |
| Fantasy | Quest, chosen one | Refusal, wrong hero |

## Story Seed Templates (Generic)

### Template A: The Reluctant Hero
> [Character who usually leads] cannot act. [Character who usually follows] must step up. The obstacle is [external threat] but the real challenge is [internal growth].

### Template B: The Trusted Betrayer
> Someone the protagonists trust turns out to be [not evil but compromised]. They must [help them] while [protecting themselves from consequences].

### Template C: The Ticking Clock
> [Mystery element] must be resolved before [deadline] or [irreversible consequence]. The usual methodical approach won't work.

### Template D: The Divided Group
> [Two characters] disagree on [moral choice]. Both have valid reasons. Resolution requires [synthesis, not victory].

### Template E: The Hidden Helper
> An apparent antagonist is actually [protecting something/someone]. The protagonists' interference makes things [worse before better].

### Template F: The Reversed Stakes
> Instead of [usual goal: finding/stopping/saving], protagonists must [opposite: hiding/enabling/letting go].

### Template G: The Inside Threat
> The danger comes from within [safe location or trusted institution], not from outside.

## MICE Quotient Framework

### Milieu Stories (Exploration)
- **Opens when**: Characters enter unfamiliar territory
- **Closes when**: Characters return/escape
- **Best for**: New location discovery, trapped scenarios
- **Seed pattern**: "What if [characters] discovered [new place] that [unexpected property]?"

### Idea Stories (Mystery)
- **Opens when**: Question is posed (who did it? what's hidden? why?)
- **Closes when**: Answer is found
- **Best for**: Detective plots, investigations, revelations
- **Seed pattern**: "What if [characters] learned that [accepted truth] was actually [different]?"

### Character Stories (Growth)
- **Opens when**: Character is dissatisfied with role/self
- **Closes when**: Character changes or accepts
- **Best for**: Coming-of-age, relationship evolution, identity
- **Seed pattern**: "What if [character] had to become [opposite of usual self] to succeed?"

### Event Stories (Restoration)
- **Opens when**: World order is disrupted
- **Closes when**: Order is restored (new or old equilibrium)
- **Best for**: Rescue missions, stopping threats, fixing damage
- **Seed pattern**: "What if [normal element] was threatened by [unusual force]?"

## Anti-Plagiarism Methodology

### Step 1: Extract Source Patterns

From each `analysis/output/*/structure.md`, build a fingerprint:

```
Source: [book name]
- Conflict type: [treasure hunt / smuggling / kidnapping / etc.]
- Antagonist type: [criminal / corrupt authority / misguided local / etc.]
- Discovery trigger: [overheard / found document / witnessed / told by / etc.]
- Investigation method: [exploration / surveillance / research / etc.]
- Climax location: [underground / building / outdoor / etc.]
- Resolution type: [capture / exposure / escape / accident / etc.]
```

### Step 2: Classify Generated Plot

Apply same categories to the new story.

### Step 3: Compare

For each source, count matches:
- **Strong match**: Same category AND similar execution
- **Weak match**: Same category but different execution
- **No match**: Different category

### Step 4: Scoring Rules

| Matches with ANY single source | Action |
|-------------------------------|--------|
| 0-1 strong matches | ✅ Proceed |
| 2 strong matches | ⚠️ Review, consider modifying one element |
| 3+ strong matches | ❌ Too similar, return to ideation |
| Multiple weak matches only | ✅ Acceptable if execution differs |

### Modification Strategies (when score is ⚠️)

1. **Change discovery trigger**: How do protagonists learn about the problem?
2. **Change antagonist motivation**: WHY are they doing this?
3. **Change resolution mechanism**: HOW is it solved?
4. **Change location role**: WHERE does the climax happen?

## Brainstorming Session Protocol

### Phase 2a: Divergent Generation (10 minutes)

1. Read universe context from Phase 1
2. Set timer
3. Generate seeds WITHOUT self-censoring
4. Use each technique at least once:
   - 2-3 What-If Inversions
   - 2-3 Location Collisions
   - 2-3 External Pressures
   - 2-3 Relationship Stress Tests
   - 2-3 Genre Blends

### Phase 2b: Seed Presentation

Present ALL seeds, grouped by technique:

```markdown
## Story Seeds

### What-If Inversions
1. [seed]
2. [seed]

### Location Collisions
3. [seed]
4. [seed]

[etc.]
```

### Phase 2c: User Selection

Ask user to mark:
- ⭐ Interesting, develop further
- 🔀 Combine with another seed
- ❌ Reject (optionally explain why for learning)

### Phase 2d: Combination (if applicable)

If user wants to combine seeds, synthesize:
- Take [element] from seed X
- Take [element] from seed Y
- Resolve contradictions by [priority rule]

## Genre-Specific Constraints

### From bible/style.md, extract:

1. **Target audience age** → Affects:
   - Violence level (implied vs. shown)
   - Moral complexity (clear vs. nuanced)
   - Stakes severity (reversible vs. permanent)

2. **Tone** → Affects:
   - Humor frequency
   - Tension duration
   - Dark moment depth

3. **Setting era** → Affects:
   - Technology available
   - Social norms
   - Reference vocabulary

### Apply constraints during seed generation

Before finalizing any seed, verify:
- [ ] Stakes appropriate for audience
- [ ] Tone consistent with style guide
- [ ] Setting elements available in universe
- [ ] Character capabilities match their profiles
