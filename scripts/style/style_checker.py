"""
Style checker for chapter drafts.

Automates technical style verification against bible/style.md rules.
Generates reports in .work/ directory for the style-linter agent.

Usage:
  uv run style_checker.py                           # All chapters
  uv run style_checker.py ../../story/chapters/chapter-01.md  # Single file
"""

import argparse
import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# --- Constants ---

CHAPTERS_DIR = Path(__file__).parent.parent.parent / "story" / "chapters"
WORK_DIR = Path(__file__).parent.parent.parent / ".work"

# Thresholds from style guide
WORD_COUNT_MIN = 2800
WORD_COUNT_MAX = 3200
SENTENCE_AVG_MIN = 12
SENTENCE_AVG_MAX = 20
SENTENCE_MAX = 35
SENTENCE_WARN = 30
PARAGRAPH_MAX_SENTENCES = 15
DIALOGUE_MIN_RATIO = 0.40  # 40%

# Words per "page" for repetition analysis
WORDS_PER_PAGE = 250
REPETITION_THRESHOLD = 3

# Forbidden dialogue tags
FORBIDDEN_TAGS = []

# Forbidden terms (AI-signal words only - add project-specific terms as needed)
FORBIDDEN_TERMS = [
    # AI-signal words (all variants)
    "delve", "delves", "delved", "delving",
    "showcasing", "showcases",
    "boasts",
    "underscores", "underscore", "underscoring",
    "comprehending",
    "intricacies", "intricate",
    "surpassing", "surpasses",
    "garnered",
    "emphasizing",
    "realm",
    "groundbreaking",
    "advancements",
    "aligns",
]

# AI-signal words for enhanced error messages
AI_SIGNAL_WORDS = {
    "delve", "delves", "delved", "delving",
    "showcasing", "showcases",
    "boasts",
    "underscores", "underscore", "underscoring",
    "comprehending",
    "intricacies", "intricate",
    "surpassing", "surpasses",
    "garnered",
    "emphasizing",
    "realm",
    "groundbreaking",
    "advancements",
    "aligns",
}

# Common words to exclude from repetition analysis
COMMON_WORDS = {
    # Articles
    "a", "an", "the",
    # Pronouns
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    # Prepositions
    "at", "by", "for", "from", "in", "into", "of", "on", "to", "with",
    "about", "after", "before", "between", "through", "during", "without",
    # Conjunctions
    "and", "but", "or", "nor", "so", "yet", "because", "although", "if", "when", "while",
    # Common verbs
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "will", "would", "could", "should", "may", "might", "must", "can",
    "said", "asked",  # dialogue tags
    # Other common words
    "not", "no", "yes", "just", "like", "that", "this", "what", "which", "who",
    "all", "some", "any", "each", "every", "both", "few", "more", "most", "other",
    "than", "then", "now", "here", "there", "where", "how", "why",
    "up", "down", "out", "off", "over", "under", "again", "back",
    "very", "too", "also", "only", "even", "still",
}

# Character names to exclude from repetition (project should define their own)
CHARACTER_NAMES = set()

# Emotions that indicate "telling" (used in TELLING_PATTERNS)
TELLING_EMOTIONS = [
    # Anger/Frustration
    "angry", "furious", "frustrated",
    # Sadness
    "sad", "miserable", "devastated", "hurt", "broken",
    # Fear
    "terrified", "scared", "afraid", "panicked", "horrified",
    # Anxiety
    "nervous", "anxious", "worried", "overwhelmed",
    # Positive
    "happy", "excited", "ecstatic", "hopeful", "relieved", "proud",
    # Other
    "confused", "embarrassed", "ashamed", "jealous", "lonely",
    "desperate", "guilty", "betrayed", "numb", "empty",
]

# Telling patterns to detect (regex template, label)
# Use {emotions} placeholder - replaced at runtime with TELLING_EMOTIONS joined by |
TELLING_PATTERNS = [
    # "I/She/He felt [emotion]" - but NOT "felt the cold" (physical sensation)
    (r'\b(She|He|I|They|We)\s+felt\s+({emotions})\b', 'felt [emotion]'),
    # "was [emotion]"
    (r'\bwas\s+({emotions})\b', 'was [emotion]'),
    # "felt a wave/surge of [emotion]"
    (r'\bfelt\s+(a\s+)?(wave|surge|rush|pang|stab|jolt)\s+of\s+', 'felt [noun] of [emotion]'),
]


# --- Data structures ---

@dataclass
class Issue:
    """Represents a style issue found in the text."""
    line: int
    text: str
    rule: str
    suggestion: str = ""


@dataclass
class Statistics:
    """Chapter statistics."""
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    max_sentence_length: int = 0
    max_sentence_line: int = 0
    dialogue_ratio: float = 0.0
    dialogue_words: int = 0
    paragraphs_over_limit: int = 0


@dataclass
class Report:
    """Complete analysis report."""
    filename: str
    statistics: Statistics = field(default_factory=Statistics)
    blocking_errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)


# --- Analysis functions ---

def count_words(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r"\b\w+\b", text))


def split_sentences(text: str) -> list[tuple[int, str]]:
    """
    Split text into sentences with line numbers.
    Returns list of (line_number, sentence_text).
    """
    lines = text.split('\n')
    sentences = []

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty lines, markdown headers and separators
        if not stripped:
            continue
        if re.match(r'^#{1,6}\s', stripped):
            continue
        if re.match(r'^[-*]{3,}$', stripped):
            continue

        # Split line into sentences using a simpler approach
        # Find positions where sentences end and new ones begin
        # Pattern: punctuation + optional quote + space + uppercase letter or quote
        parts = re.split(r'([.!?]["\']?)\s+(?=[A-Z""])', stripped)

        # Reconstruct sentences (split separates the punctuation)
        current = ""
        for i, part in enumerate(parts):
            current += part
            # If this part is punctuation (odd index after split), it ends a sentence
            if i % 2 == 1:  # punctuation part
                if current.strip():
                    sentences.append((line_num, current.strip()))
                current = ""

        # Don't forget the last part if it doesn't end with punctuation captured
        if current.strip():
            sentences.append((line_num, current.strip()))

    return sentences


def split_paragraphs(text: str) -> list[tuple[int, str]]:
    """
    Split text into paragraphs with starting line numbers.
    Returns list of (line_number, paragraph_text).
    """
    lines = text.split('\n')
    paragraphs = []
    current_para = []
    current_start = 1

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip markdown elements
        if re.match(r'^#{1,6}\s', stripped):
            if current_para:
                paragraphs.append((current_start, '\n'.join(current_para)))
                current_para = []
            continue
        if re.match(r'^[-*]{3,}$', stripped):
            if current_para:
                paragraphs.append((current_start, '\n'.join(current_para)))
                current_para = []
            continue

        if not stripped:
            # Empty line = paragraph break
            if current_para:
                paragraphs.append((current_start, '\n'.join(current_para)))
                current_para = []
        else:
            if not current_para:
                current_start = line_num
            current_para.append(stripped)

    # Don't forget last paragraph
    if current_para:
        paragraphs.append((current_start, '\n'.join(current_para)))

    return paragraphs


def count_sentences_in_paragraph(para_text: str) -> int:
    """Count sentences in a paragraph."""
    # Simple sentence count based on ending punctuation
    endings = re.findall(r'[.!?]+["\']?(?:\s|$)', para_text)
    return len(endings) if endings else 1


def extract_dialogue(text: str) -> list[tuple[int, str]]:
    """
    Extract dialogue (text within quotes) with line numbers.
    Returns list of (line_number, dialogue_text).
    """
    dialogues = []
    lines = text.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Find all quoted text (American double quotes)
        matches = re.findall(r'"([^"]*)"', line)
        for match in matches:
            if match.strip():
                dialogues.append((line_num, match))

    return dialogues


def calculate_dialogue_ratio(text: str) -> tuple[float, int, int]:
    """
    Calculate dialogue to total words ratio.
    Returns (ratio, dialogue_words, total_words).
    """
    total_words = count_words(text)
    if total_words == 0:
        return 0.0, 0, 0

    dialogues = extract_dialogue(text)
    dialogue_words = sum(count_words(d[1]) for d in dialogues)

    ratio = dialogue_words / total_words
    return ratio, dialogue_words, total_words


def find_forbidden_tags(text: str) -> list[Issue]:
    """Find forbidden dialogue tags (only when used as actual dialogue attribution)."""
    issues = []
    lines = text.split('\n')

    for line_num, line in enumerate(lines, 1):
        for tag in FORBIDDEN_TAGS:
            # Only match when used as dialogue tag, not general verb
            # Patterns:
            # - "..." [subject] hissed / "..." hissed [subject]
            # - hissed, "..." / hissed "..."
            # - she/he/I/name hissed (near quotes)
            patterns = [
                rf'"\s*\w*\s*{tag}',  # "..." hissed or " hissed
                rf'{tag}\s*,?\s*"',   # hissed, "..." or hissed "..."
                rf'(she|he|I|they|we)\s+{tag}\b',  # pronoun + tag
            ]

            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Extract context around the match
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 40)
                    context = line[start:end].strip()
                    if start > 0:
                        context = "..." + context
                    if end < len(line):
                        context = context + "..."

                    issues.append(Issue(
                        line=line_num,
                        text=context,
                        rule=f'Forbidden dialogue tag: "{tag}"',
                        suggestion=f'Replace "{tag}" with "said" or use action beat'
                    ))
                    break  # Don't report same tag multiple times per line

    return issues


def find_adverb_tags(text: str) -> list[Issue]:
    """Find 'said/asked + adverb' patterns."""
    issues = []
    lines = text.split('\n')

    pattern = r'\b(said|asked)\s+(\w+ly)\b'

    for line_num, line in enumerate(lines, 1):
        matches = re.finditer(pattern, line, re.IGNORECASE)
        for match in matches:
            verb, adverb = match.groups()
            issues.append(Issue(
                line=line_num,
                text=match.group(0),
                rule=f'Adverb dialogue tag: "{verb} {adverb}"',
                suggestion=f'Remove adverb, show emotion through action'
            ))

    return issues


def find_telling_patterns(text: str) -> list[Issue]:
    """Find 'telling' patterns like 'felt [emotion]', 'was angry'."""
    issues = []
    lines = text.split('\n')

    # Build emotion regex from constant
    emotions = "|".join(TELLING_EMOTIONS)

    for line_num, line in enumerate(lines, 1):
        for pattern_template, name in TELLING_PATTERNS:
            # Replace {emotions} placeholder with actual emotions
            pattern = pattern_template.format(emotions=emotions)
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                issues.append(Issue(
                    line=line_num,
                    text=match.group(0),
                    rule=f'Telling pattern: {name}',
                    suggestion='Show through action, body language, or physical sensation'
                ))

    return issues


def find_forbidden_terms(text: str) -> list[Issue]:
    """Find forbidden AI-signal words."""
    issues = []
    lines = text.split('\n')

    for line_num, line in enumerate(lines, 1):
        for term in FORBIDDEN_TERMS:
            pattern = rf'\b{re.escape(term)}\b'

            if re.search(pattern, line, re.IGNORECASE):
                # All terms in FORBIDDEN_TERMS are AI-signal words
                if term.lower() in AI_SIGNAL_WORDS:
                    rule_msg = f'Forbidden AI-signal word: "{term}"'
                    suggestion = 'Replace with natural alternative (see bible/style.md)'
                else:
                    rule_msg = f'Forbidden term: "{term}"'
                    suggestion = 'Remove or replace with in-world alternative'

                issues.append(Issue(
                    line=line_num,
                    text=line.strip()[:80],
                    rule=rule_msg,
                    suggestion=suggestion
                ))

    return issues


def find_wrong_quotes(text: str) -> list[Issue]:
    """Find non-American quote styles."""
    issues = []
    lines = text.split('\n')

    # French guillemets
    french_pattern = r'[«»]'
    # Single quotes used for dialogue (but not contractions)
    single_quote_dialogue = r"(?<![a-zA-Z])'[^']{10,}'(?![a-zA-Z])"

    for line_num, line in enumerate(lines, 1):
        if re.search(french_pattern, line):
            issues.append(Issue(
                line=line_num,
                text=line.strip()[:80],
                rule='French guillemets detected',
                suggestion='Use American double quotes "..."'
            ))

        if re.search(single_quote_dialogue, line):
            issues.append(Issue(
                line=line_num,
                text=line.strip()[:80],
                rule='Single quotes for dialogue',
                suggestion='Use American double quotes "..."'
            ))

    return issues


def analyze_repetitions(text: str) -> list[Issue]:
    """Find word repetitions exceeding threshold per page."""
    issues = []

    # Clean text - remove markdown, keep only prose
    clean = re.sub(r'^#{1,6}\s.*$', '', text, flags=re.MULTILINE)
    clean = re.sub(r'^[-*]{3,}$', '', clean, flags=re.MULTILINE)

    # Extract words
    words = re.findall(r"\b[a-zA-Z']+\b", clean.lower())

    # Filter out common words and character names
    filtered = [w for w in words if w not in COMMON_WORDS and w not in CHARACTER_NAMES and len(w) > 2]

    # Calculate pages
    total_words = len(words)
    num_pages = max(1, total_words // WORDS_PER_PAGE)

    # Count frequencies
    counter = Counter(filtered)

    # Threshold adjusted for total pages
    adjusted_threshold = REPETITION_THRESHOLD * num_pages

    for word, count in counter.most_common(20):
        avg_per_page = count / num_pages
        if avg_per_page > REPETITION_THRESHOLD:
            issues.append(Issue(
                line=0,  # Line number not applicable for chapter-wide
                text=f'"{word}" appears {count} times',
                rule=f'Repetition: {avg_per_page:.1f} per page (>{REPETITION_THRESHOLD})',
                suggestion=f'Consider varying vocabulary'
            ))

    return issues


def analyze_chapter(text: str, filename: str) -> Report:
    """Perform complete analysis on chapter text."""
    report = Report(filename=filename)
    stats = report.statistics

    # --- Basic statistics ---
    stats.word_count = count_words(text)

    # Sentence analysis
    sentences = split_sentences(text)
    stats.sentence_count = len(sentences)

    if sentences:
        sentence_lengths = [(line, count_words(sent)) for line, sent in sentences]
        stats.avg_sentence_length = sum(l for _, l in sentence_lengths) / len(sentence_lengths)

        max_len = 0
        max_line = 0
        for line, length in sentence_lengths:
            if length > max_len:
                max_len = length
                max_line = line
        stats.max_sentence_length = max_len
        stats.max_sentence_line = max_line

        # Check for long sentences
        for line, sent in sentences:
            word_count = count_words(sent)
            if word_count > SENTENCE_MAX:
                report.blocking_errors.append(Issue(
                    line=line,
                    text=sent[:80] + "..." if len(sent) > 80 else sent,
                    rule=f'Sentence exceeds {SENTENCE_MAX} words ({word_count} words)',
                    suggestion='Split into shorter sentences'
                ))
            elif word_count > SENTENCE_WARN:
                report.warnings.append(Issue(
                    line=line,
                    text=sent[:80] + "..." if len(sent) > 80 else sent,
                    rule=f'Sentence near limit ({word_count} words)',
                    suggestion='Consider splitting'
                ))

    # Dialogue ratio
    ratio, dialogue_words, total = calculate_dialogue_ratio(text)
    stats.dialogue_ratio = ratio
    stats.dialogue_words = dialogue_words

    if ratio < DIALOGUE_MIN_RATIO:
        report.blocking_errors.append(Issue(
            line=0,
            text=f'{ratio*100:.1f}% dialogue ({dialogue_words}/{total} words)',
            rule=f'Dialogue ratio below {DIALOGUE_MIN_RATIO*100:.0f}% minimum',
            suggestion='Add more dialogue, convert summarized speech to direct dialogue'
        ))

    # Paragraph analysis
    paragraphs = split_paragraphs(text)
    over_limit = 0
    for line, para in paragraphs:
        sent_count = count_sentences_in_paragraph(para)
        if sent_count > PARAGRAPH_MAX_SENTENCES:
            over_limit += 1
            report.blocking_errors.append(Issue(
                line=line,
                text=para[:80] + "..." if len(para) > 80 else para,
                rule=f'Paragraph exceeds {PARAGRAPH_MAX_SENTENCES} sentences ({sent_count})',
                suggestion='Split into smaller paragraphs'
            ))
    stats.paragraphs_over_limit = over_limit

    # Word count check
    if stats.word_count < WORD_COUNT_MIN:
        report.blocking_errors.append(Issue(
            line=0,
            text=f'{stats.word_count} words',
            rule=f'Word count below {WORD_COUNT_MIN} minimum',
            suggestion='Expand scenes or add content'
        ))
    elif stats.word_count > WORD_COUNT_MAX:
        report.blocking_errors.append(Issue(
            line=0,
            text=f'{stats.word_count} words',
            rule=f'Word count exceeds {WORD_COUNT_MAX} maximum',
            suggestion='Trim or split chapter'
        ))

    # --- Pattern checks ---

    # Forbidden dialogue tags
    report.blocking_errors.extend(find_forbidden_tags(text))

    # Adverb tags
    report.blocking_errors.extend(find_adverb_tags(text))

    # Telling patterns
    report.blocking_errors.extend(find_telling_patterns(text))

    # Forbidden terms
    report.blocking_errors.extend(find_forbidden_terms(text))

    # Quote style
    report.warnings.extend(find_wrong_quotes(text))

    # Repetitions
    report.warnings.extend(analyze_repetitions(text))

    return report


def format_report(report: Report) -> str:
    """Format report as Markdown."""
    stats = report.statistics

    lines = [
        f"# Technical Style Analysis: {report.filename}",
        "",
        "## Statistics",
        "",
    ]

    # Word count
    wc_status = "✓" if WORD_COUNT_MIN <= stats.word_count <= WORD_COUNT_MAX else "✗"
    lines.append(f"- Word count: {stats.word_count} (target: {WORD_COUNT_MIN}-{WORD_COUNT_MAX}) {wc_status}")

    # Sentence stats
    lines.append(f"- Sentence count: {stats.sentence_count}")

    avg_status = "✓" if SENTENCE_AVG_MIN <= stats.avg_sentence_length <= SENTENCE_AVG_MAX else "⚠"
    lines.append(f"- Avg sentence length: {stats.avg_sentence_length:.1f} words (target: {SENTENCE_AVG_MIN}-{SENTENCE_AVG_MAX}) {avg_status}")

    max_status = "✓" if stats.max_sentence_length <= SENTENCE_MAX else "✗"
    lines.append(f"- Max sentence length: {stats.max_sentence_length} words (line {stats.max_sentence_line}) (max: {SENTENCE_MAX}) {max_status}")

    # Dialogue
    dial_status = "✓" if stats.dialogue_ratio >= DIALOGUE_MIN_RATIO else "✗"
    lines.append(f"- Dialogue ratio: {stats.dialogue_ratio*100:.1f}% ({stats.dialogue_words} words) (min: {DIALOGUE_MIN_RATIO*100:.0f}%) {dial_status}")

    # Paragraphs
    para_status = "✓" if stats.paragraphs_over_limit == 0 else "✗"
    lines.append(f"- Paragraphs > {PARAGRAPH_MAX_SENTENCES} sentences: {stats.paragraphs_over_limit} {para_status}")

    lines.append("")

    # Blocking errors
    lines.append("## Blocking Errors (automated)")
    lines.append("")

    if report.blocking_errors:
        for issue in report.blocking_errors:
            if issue.line > 0:
                lines.append(f"- [line {issue.line}]: {issue.rule}")
                lines.append(f"  - Text: \"{issue.text}\"")
            else:
                lines.append(f"- [CHAPTER]: {issue.rule}")
                lines.append(f"  - Detail: {issue.text}")
            if issue.suggestion:
                lines.append(f"  - Suggestion: {issue.suggestion}")
            lines.append("")
    else:
        lines.append("None detected.")
        lines.append("")

    # Warnings
    lines.append("## Warnings (automated)")
    lines.append("")

    if report.warnings:
        for issue in report.warnings:
            if issue.line > 0:
                lines.append(f"- [line {issue.line}]: {issue.rule}")
                lines.append(f"  - Text: \"{issue.text}\"")
            else:
                lines.append(f"- [CHAPTER]: {issue.rule}")
                lines.append(f"  - Detail: {issue.text}")
            if issue.suggestion:
                lines.append(f"  - Suggestion: {issue.suggestion}")
            lines.append("")
    else:
        lines.append("None detected.")
        lines.append("")

    # Agent review section
    lines.extend([
        "## For Agent Review",
        "",
        "The style-linter agent should focus on:",
        "- POV consistency (per bible/style.md)",
        "- Tense consistency (past simple primary)",
        "- Chapter ending type validation (cliffhanger/punchy line/revelation/question)",
        "- Internal thought formatting (italics for direct thoughts)",
        "- Show vs Tell quality assessment",
        "- Sensory details evaluation (touch, smell, visual priority)",
        "- Voice consistency",
        "- Tone/register appropriateness",
        "",
    ])

    # Verdict
    lines.append("## Verdict")
    lines.append("")

    if report.blocking_errors:
        lines.append(f"**FAIL** - {len(report.blocking_errors)} blocking error(s)")
    else:
        lines.append("**PASS** - No blocking errors detected")

    if report.warnings:
        lines.append(f"  - {len(report.warnings)} warning(s) to review")

    return '\n'.join(lines)


def extract_chapter_number(filename: str) -> str:
    """Extract chapter number from filename."""
    match = re.search(r'chapter[_-]?(\d+)', filename, re.IGNORECASE)
    if match:
        return match.group(1).zfill(2)

    match = re.search(r'chapitre[_-]?(\d+)', filename, re.IGNORECASE)
    if match:
        return match.group(1).zfill(2)

    return "XX"


def main():
    parser = argparse.ArgumentParser(
        description="Technical style checker for chapter drafts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run style_checker.py                           # Analyze all chapters
  uv run style_checker.py ../../story/chapters/chapter-01.md  # Single file
        """
    )
    parser.add_argument("files", nargs="*", help="Files to analyze")

    args = parser.parse_args()

    # Ensure .work directory exists
    WORK_DIR.mkdir(exist_ok=True)

    # Determine files to analyze
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # All chapters
        if not CHAPTERS_DIR.exists():
            print(f"Error: Chapters directory not found: {CHAPTERS_DIR}")
            sys.exit(1)

        files = sorted(CHAPTERS_DIR.glob("*.md"))
        if not files:
            print("No chapter files found.")
            sys.exit(0)

    # Track overall exit code
    has_errors = False

    for filepath in files:
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            continue

        print(f"Analyzing: {filepath.name}")

        text = filepath.read_text(encoding="utf-8")
        report = analyze_chapter(text, filepath.name)

        # Generate report filename with UUID
        chapter_num = extract_chapter_number(filepath.name)
        report_id = str(uuid.uuid4())[:8]
        report_filename = f"chapter-{chapter_num}-tech-report-{report_id}.md"
        report_path = WORK_DIR / report_filename

        # Write report
        report_content = format_report(report)
        report_path.write_text(report_content, encoding="utf-8")

        # Print summary
        if report.blocking_errors:
            has_errors = True
            print(f"  ✗ FAIL - {len(report.blocking_errors)} blocking errors")
        else:
            print(f"  ✓ PASS")

        if report.warnings:
            print(f"  ⚠ {len(report.warnings)} warnings")

        print(f"  Report: {report_path}")
        print()

    # Exit code
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
