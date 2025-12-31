"""
Perplexity analysis with Mistral-7B.

Usage:
  uv run test_perplexity.py                    # All chapters (batch)
  uv run test_perplexity.py file.md            # Single file analysis
  uv run test_perplexity.py -p "Test phrase"   # Single phrase test
"""

import argparse
import atexit
import os
import re
import signal
import sys
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

CHAPTERS_DIR = Path(__file__).parent.parent.parent / "story" / "chapters"
LOCK_FILE = Path(__file__).parent / ".perplexity.lock"

# --- Thresholds ---
SUSPECT_PPL_THRESHOLD = 15     # Sentences below this are suspect
MEDIAN_WARNING_THRESHOLD = 20  # Warn if median PPL below this
MIN_SENTENCE_WORDS = 10         # Merge sentences shorter than this


# --- Lock management ---

def acquire_lock():
    """Acquire lock file. Exit if another instance is running."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            # Check if process is still running
            if is_pid_running(pid):
                print(f"Error: Another instance is already running (PID {pid})")
                print("Wait for it to finish or kill it manually.")
                sys.exit(1)
            else:
                # Stale lock file, remove it
                LOCK_FILE.unlink()
        except (ValueError, OSError):
            LOCK_FILE.unlink()

    # Create lock with our PID
    LOCK_FILE.write_text(str(os.getpid()))
    atexit.register(release_lock)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def release_lock():
    """Release lock file."""
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass


def signal_handler(signum, frame):
    """Handle interrupt signals."""
    release_lock()
    sys.exit(1)


def is_pid_running(pid):
    """Check if a process with given PID is running."""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


# --- Analyzer ---

class PerplexityAnalyzer:
    """Perplexity analyzer using Mistral-7B."""

    def __init__(self, model_id="mistralai/Mistral-7B-v0.3"):
        print(f"Loading {model_id}...")

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available. GPU required.")

        self.device = torch.device("cuda")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, dtype=torch.float16
        ).to(self.device)

        self.model.eval()
        print("Model loaded.\n")

    def split_sentences(self, text):
        """Split text into sentences, handling French dialogue."""
        # Normalize line breaks
        text = re.sub(r"\n+", " ", text.strip())
        # Normalize French quotes: ". »" -> ".»" (remove space before closing quote)
        text = re.sub(r'([.!?])\s+([»"])', r'\1\2', text)
        # Split after .!? or .!?» or .!?" IF followed by uppercase
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ])|(?<=[.!?][»"])\s+(?=[A-ZÀ-ÖØ-Þ])', text)
        return [s.strip() for s in sentences if len(s.strip()) > 0]

    def is_valid_sentence(self, sentence):
        """Filter out markdown elements."""
        s = sentence.strip()
        # Skip markdown: titles, separators, links
        if re.match(r"^#{1,6}\s", s):  # Titles
            return False
        if re.match(r"^-{3,}$", s):  # Separators
            return False
        if re.match(r"^\*{3,}$", s):  # Separators
            return False
        if re.match(r"^!\[", s):  # Images
            return False
        if re.match(r"^\[.*\]\(.*\)$", s):  # Links
            return False
        return True

    def merge_short_sentences(self, sentences, min_words=MIN_SENTENCE_WORDS):
        """Merge sentences shorter than min_words with adjacent sentence."""
        if not sentences:
            return sentences

        merged = []
        i = 0
        while i < len(sentences):
            current = sentences[i]
            word_count = len(re.findall(r"\b\w+\b", current))

            if word_count < min_words:
                if merged:
                    # Merge with previous
                    merged[-1] = merged[-1] + " " + current
                elif i + 1 < len(sentences):
                    # First sentence: merge with next
                    sentences[i + 1] = current + " " + sentences[i + 1]
                else:
                    # Only sentence, keep as is
                    merged.append(current)
            else:
                merged.append(current)
            i += 1

        return merged

    def count_words(self, text):
        """Count words in text."""
        return len(re.findall(r"\b\w+\b", text))

    def calculate_burstiness(self, sentences):
        """Calculate burstiness (std of sentence lengths in tokens)."""
        if not sentences:
            return 0.0
        lengths = [len(self.tokenizer.encode(s)) for s in sentences]
        return float(np.std(lengths))

    def calculate_fano_factor(self, sentences):
        """Calculate Fano factor (variance/mean of sentence lengths)."""
        if not sentences:
            return 0.0
        lengths = [len(self.tokenizer.encode(s)) for s in sentences]
        mean = np.mean(lengths)
        return float(np.var(lengths) / mean) if mean > 0 else 0.0

    def perplexity(self, text):
        """Compute perplexity of a text."""
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
        return torch.exp(outputs.loss).item()

    def get_marker(self, ppl):
        """Get emoji marker based on perplexity."""
        if ppl < 10:
            return "🤖🤖"
        elif ppl < 20:
            return "🤖"
        elif ppl < 40:
            return "❓"
        else:
            return "👤"

    def analyze_phrase(self, phrase):
        """Analyze a single phrase."""
        ppl = self.perplexity(phrase)
        marker = self.get_marker(ppl)
        suspect = ppl < SUSPECT_PPL_THRESHOLD

        print(f"\n{marker} Perplexity: {ppl:.1f}")
        if suspect:
            print("⚠️  Low perplexity - may appear AI-generated")
        else:
            print("✓  Normal perplexity")
        print(f"\nPhrase: {phrase}")

    def analyze(self, text):
        """
        Analyze text sentence by sentence.
        Returns sentences sorted by perplexity (most suspect first).
        """
        all_sentences = self.split_sentences(text)
        valid_sentences = [s for s in all_sentences if self.is_valid_sentence(s)]
        merged_sentences = self.merge_short_sentences(valid_sentences)
        results = []

        for sentence in merged_sentences:
            ppl = self.perplexity(sentence)
            results.append(
                {"phrase": sentence, "perplexite": ppl, "suspect_ia": ppl < SUSPECT_PPL_THRESHOLD}
            )

        # Sort by ascending perplexity (lower = more suspect)
        results.sort(key=lambda x: x["perplexite"])

        # Return valid_sentences (before merge) for burstiness calculation
        filtered_count = len(all_sentences) - len(valid_sentences)
        return results, len(all_sentences), filtered_count, valid_sentences

    def print_analysis(self, text, title=""):
        """Print detailed analysis with full sentences and stats."""
        # Count stats before analysis
        total_words = self.count_words(text)

        results, total_sentences, filtered_count, sentences = self.analyze(text)

        if not results:
            print("No valid sentences to analyze.")
            return results

        # Calculate words analyzed
        words_analyzed = sum(self.count_words(r["phrase"]) for r in results)

        # Calculate burstiness
        burstiness = self.calculate_burstiness(sentences)
        fano = self.calculate_fano_factor(sentences)

        # Header
        print("\n" + "=" * 80)
        if title:
            print(f"📄 File: {title}")
        print(f"   Words in file: {total_words}")
        print(f"   Sentences in file: {total_sentences}")
        print(f"   Sentences analyzed: {len(results)} (filtered: {filtered_count})")
        print(f"   Words analyzed: {words_analyzed}")
        print("=" * 80)

        # Perplexity stats
        ppls = [r["perplexite"] for r in results]
        median_ppl = np.median(ppls)
        print(f"\n📊 Perplexity stats:")
        print(f"   Mean: {np.mean(ppls):.1f} | Median: {median_ppl:.1f} | Std: {np.std(ppls):.1f}")
        print(f"   Min: {np.min(ppls):.1f} | Max: {np.max(ppls):.1f}")

        # Warning if median is low
        if median_ppl < MEDIAN_WARNING_THRESHOLD:
            print(f"\n⚠️  WARNING: Median perplexity ({median_ppl:.1f}) is below threshold ({MEDIAN_WARNING_THRESHOLD})")
            print("    Text may contain AI-generated patterns.")

        # Burstiness stats
        print(f"\n📏 Sentence variation:")
        print(f"   Burstiness (std): {burstiness:.1f}")
        print(f"   Fano factor: {fano:.1f}")

        nb_suspect = sum(1 for r in results if r["suspect_ia"])
        pct_suspect = (nb_suspect / len(results) * 100) if results else 0
        print(f"\n🎯 Suspect AI (ppl < {SUSPECT_PPL_THRESHOLD}): {nb_suspect}/{len(results)} ({pct_suspect:.1f}%)")

        # Show only suspect sentences
        suspect_results = [r for r in results if r["suspect_ia"]]

        if suspect_results:
            print("\n" + "-" * 80)
            print(f"SUSPECT SENTENCES (perplexity < {SUSPECT_PPL_THRESHOLD})")
            print("-" * 80 + "\n")

            for i, r in enumerate(suspect_results, 1):
                ppl = r["perplexite"]
                marker = self.get_marker(ppl)
                print(f"{i:3}. {marker} [{ppl:6.1f}]")
                print(f"     {r['phrase']}\n")
        else:
            print("\n✓ No suspect sentences found.")

        return results

    def analyze_file_batch(self, filepath: Path):
        """Analyze a file and return aggregated stats for batch mode."""
        text = filepath.read_text(encoding="utf-8")
        total_words = self.count_words(text)
        results, total_sentences, filtered_count, sentences = self.analyze(text)

        if not results:
            return {
                "name": filepath.name,
                "words": total_words,
                "sentences": total_sentences,
                "analyzed": 0,
                "median": 0,
                "suspect": 0,
                "burstiness": 0,
                "fano": 0,
            }

        ppls = [r["perplexite"] for r in results]
        nb_suspect = sum(1 for r in results if r["suspect_ia"])

        return {
            "name": filepath.name,
            "words": total_words,
            "sentences": total_sentences,
            "analyzed": len(results),
            "median": np.median(ppls),
            "suspect": nb_suspect,
            "burstiness": self.calculate_burstiness(sentences),
            "fano": self.calculate_fano_factor(sentences),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Perplexity analysis with Mistral-7B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run test_perplexity.py                    # Analyze all chapters
  uv run test_perplexity.py chapter.md         # Analyze single file
  uv run test_perplexity.py -p "Test phrase"   # Test single phrase
        """
    )
    parser.add_argument("file", nargs="?", help="File to analyze (use - for stdin)")
    parser.add_argument("-p", "--phrase", help="Single phrase to test")

    args = parser.parse_args()

    # Check for piped input
    if not sys.stdin.isatty() and not args.phrase and not args.file:
        args.file = "-"  # Use stdin

    # Acquire lock before loading model
    acquire_lock()

    try:
        analyzer = PerplexityAnalyzer()
    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nThis script requires CUDA (NVIDIA GPU).")
        print("Check that:")
        print("  - You have an NVIDIA GPU")
        print("  - CUDA toolkit is installed")
        print("  - PyTorch is installed with CUDA support")
        print("\nRun with: uv run test_perplexity.py (pyproject.toml handles CUDA torch)")
        sys.exit(1)

    if args.phrase:
        # Single phrase mode
        analyzer.analyze_phrase(args.phrase)
    elif args.file:
        # Single file or stdin mode with detailed analysis
        if args.file == "-":
            text = sys.stdin.buffer.read().decode("utf-8")
            title = "stdin"
        else:
            fichier = Path(args.file)
            if not fichier.exists():
                print(f"File not found: {fichier}")
                sys.exit(1)
            text = fichier.read_text(encoding="utf-8")
            title = fichier.name
        analyzer.print_analysis(text, title=title)
    else:
        # Batch mode: all chapters
        if not CHAPTERS_DIR.exists():
            print(f"Directory not found: {CHAPTERS_DIR}")
            sys.exit(1)

        chapitres = sorted(CHAPTERS_DIR.glob("chapitre-*.md"))
        if not chapitres:
            print("No chapters found")
            sys.exit(1)

        print(f"Analyzing {len(chapitres)} chapters:\n")
        print(f"{'Chapter':<25} {'Words':>7} {'Median':>8} {'':>2} {'Burst':>7} {'Fano':>7} {'Suspect':>12}")
        print("-" * 78)

        for chapitre in chapitres:
            stats = analyzer.analyze_file_batch(chapitre)
            pct = (stats['suspect'] / stats['analyzed'] * 100) if stats['analyzed'] else 0
            warn = "⚠️" if stats['median'] < MEDIAN_WARNING_THRESHOLD else "  "
            print(
                f"{stats['name']:<25} {stats['words']:>7} {stats['median']:>8.1f} {warn} "
                f"{stats['burstiness']:>7.1f} {stats['fano']:>7.1f} "
                f"{stats['suspect']:>4}/{stats['analyzed']:<4} ({pct:4.1f}%)"
            )


if __name__ == "__main__":
    main()
