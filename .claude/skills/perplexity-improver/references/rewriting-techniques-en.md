# Rewriting Techniques for Increasing Perplexity

A practical guide to transforming predictable sentences into more original formulations while preserving meaning.

## Core Principle

Perplexity measures how "surprised" a language model is by text. Predictable sentence = low perplexity = detectable AI pattern.

**Goal**: Make text less predictable without sacrificing clarity or coherence.

---

## 1. Verbalized Sampling (First-Pass Technique)

Before applying other techniques, generate 3 alternative versions of the suspect sentence by sampling from distribution tails.

**Process**:
1. Take the suspect sentence (low perplexity)
2. Prompt: "Generate 3 alternative formulations of this sentence, sampled from distribution tails (probability < 0.3)"
3. Select the most natural alternative that preserves meaning
4. If none work, proceed to techniques 2-9

| Original (ppl ~8) | Alternative 1 (p<0.3) | Alternative 2 (p<0.3) | Alternative 3 (p<0.3) |
|-------------------|----------------------|----------------------|----------------------|
| She felt a deep sadness | Her chest felt stuffed with wet newspaper | The sadness sat in her like swallowed stones | Something had curdled behind her eyes |

**Why this works**: Low-perplexity sentences are "mode-collapsed" — the model defaulted to its most typical output. Tail sampling accesses the full distribution learned during pretraining.

**When to use** (by detection type):

| Detection type | Strategy |
|----------------|----------|
| `low_perplexity` | ✅ VS or Techniques 2-9 |
| `low_std` (monotone paragraph) | Mix: VS on 1-2 sentences + Techniques 2-9 on others |
| `adjacent_low` / `low_ppl_density` | Mix: VS on 1-2 sentences + Techniques 2-9 on 2-3 others |
| `forbidden_word` | Technique 4 only (rare vocabulary swap) |

---

## 2. Syntactic Inversion

Change the canonical subject-verb-object order.

| Original (predictable) | Rewritten (less predictable) |
|------------------------|------------------------------|
| He ran toward the door | Toward the door he bolted |
| She was terrified | Terror had seized her |
| The sun was setting | Down sank the sun, amber and weary |
| They decided to leave | Leave they would. It was settled. |

**When to use**: Simple declarative sentences, action descriptions.

---

## 3. Fragmentation

Cut long sentences into short, punchy segments.

| Original | Rewritten |
|----------|-----------|
| He was afraid but he knew he had to continue despite everything | Fear. Everywhere. Yet onward he must go. |
| The house was old and its shutters rattled in the wind | An ancient house. Shutters clattering. The wind. |

**When to use**: Moments of tension, atmospheric descriptions, inner thoughts.

---

## 4. Rare Vocabulary

Replace common words with less frequent synonyms.

| Common word | Rare alternatives |
|-------------|-------------------|
| look | scrutinize, peer, gaze, dart eyes upon |
| walk | amble, trudge, saunter, stride |
| say | murmur, utter, articulate, mutter |
| fear | dread, trepidation, disquiet |
| noise | clamor, din, tumult, cacophony |
| beautiful | resplendent, sublime, exquisite |
| old | decrepit, antiquated, venerable |
| dark | tenebrous, murky, stygian |
| think | ponder, muse, ruminate |
| want | crave, yearn, covet |

**Caution**: Do not overuse. One rare word per sentence maximum.

---

## 5. Broken Rhythm

Alternate very short and longer sentences to create unpredictable rhythm.

| Original (uniform rhythm) | Rewritten (broken rhythm) |
|---------------------------|---------------------------|
| She opened the door. She entered the room. She looked around. | She opened the door. The room awaited her, dark and silent as a forgotten tomb. A glance around. Empty. |

**Effective pattern**: Short - Long - Very short - Medium

---

## 6. Sensory Details

Add specific sensory information (sight, sound, touch, smell, taste).

| Original (abstract) | Rewritten (sensory) |
|---------------------|---------------------|
| It was cold | The air bit at his cheeks, acrid and metallic |
| The room was dirty | A reek of mildew and yellowed paper, cobwebs draped in every corner |
| She was hungry | Her stomach churned, saliva pooling beneath her tongue |

**When to use**: Location descriptions, characters' physical states.

---

## 7. Character Voice

Integrate speech patterns, expressions, or thoughts specific to the character.

**Examples by archetype:**

| Character type | Characteristic formulations |
|----------------|----------------------------|
| Cautious leader | "Best think this through. No hasty moves." |
| Impulsive | "Blast it!", interjections, incomplete sentences |
| Intellectual | Metaphors, references, explanatory parentheticals |
| Child | Naive comparisons, simple vocabulary but vivid imagery |

**When to use**: Dialogue, inner monologue, focused narration.

---

## 8. Cliché Subversion

Take a fixed expression and twist it.

| Cliché | Subversion |
|--------|------------|
| white as snow | white as bleached bone |
| time flies | time oozed, viscous and slow |
| his heart was pounding | his heart hammered against his ribs like a caged thing |
| raining cats and dogs | rain fell in sheets, each drop a small violence |
| quiet as a mouse | quiet as held breath |
| cold as ice | cold as something long dead |

---

## 9. Narrative Ellipsis

Remove expected transitions; let the reader fill gaps.

| Original (explicit) | Rewritten (ellipsis) |
|---------------------|----------------------|
| He climbed the stairs and arrived at the door. He hesitated then knocked. | The stairs. The door. His knuckles against wood. |

---

## Recommended Combinations

For highly suspect sentences (ppl < 10), combine multiple techniques:

1. **Inversion + Rare vocabulary**
   - Original: "He looked at the sea with sadness"
   - Rewritten: "The sea—he gazed upon it. Melancholy."

2. **Fragmentation + Sensory details**
   - Original: "Night was falling and it was getting colder and colder"
   - Rewritten: "Night. A chill creeping beneath his collar, numbing his fingers."

3. **Character voice + Broken rhythm**
   - Original: "Claude was angry and did not want to obey"
   - Rewritten: "Claude clenched her fists. Obey? Never. She would sooner die."

---

## Pitfalls to Avoid

1. **Over-correction**: Too many techniques = unreadable text
2. **Loss of meaning**: Clarity trumps originality
3. **Voice inconsistency**: Maintain the narrator's/character's register
4. **Tone rupture**: Do not introduce humor into a grave scene
5. **Em-dash parentheticals**: Parenthetical insertions — like this — are a frequent AI marker. One em-dash parenthetical per paragraph maximum.

---

## Checklist Before Validation

- [ ] Original meaning is preserved
- [ ] Style remains consistent with `bible/style.md`
- [ ] Dialogue sounds natural for the character
- [ ] Overall passage rhythm remains fluid
- [ ] No repetition of the same techniques
