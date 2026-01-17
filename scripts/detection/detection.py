"""
AI Slope Diagnostic Tool - Multi-criteria perplexity analysis.

Philosophy:
  This is NOT an "AI vs Human" detector. It diagnoses "boring" text - the
  "AI Slope" phenomenon where generated text slides toward predictable patterns.

  What it detects:
  - Low PPL = the model was very confident = well-trodden path
  - Adjacent low blocks = long sequences without surprises
  - Low variance windows = suspicious uniformity
  - No errors, but no friction either

  Use this as a DIAGNOSTIC tool, not a judgment.

Usage:
  uv run detection.py file.md [file2.md ...]    # Show report on screen
  uv run detection.py file.md -o report.txt      # Write report to file
  uv run detection.py file.md --debug            # Show detailed debug info
  uv run detection.py -m qwen8b file.md          # Use Qwen3 8B model

Output:
  - Human-readable report (screen or file with -o)
  - Use --debug to see all sentences, std windows, and threshold calibration data
"""

import argparse
import atexit
import os
import re
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import hashlib
import sqlite3

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import Mistral3ForConditionalGeneration, MistralCommonBackend
from tqdm import tqdm

CHAPTERS_DIR = Path(__file__).parent.parent.parent / "story" / "chapters"
LOCK_FILE = Path(__file__).parent / ".perplexity.lock"

# --- Models ---
# multimodal=True means we load with Mistral3ForConditionalGeneration and extract .language_model
MODELS = {
    "ministral8b": {
        "id": "mistralai/Ministral-3-8B-Base-2512",
        "multimodal": True,
    },
    "ministral8b-instruct": {
        "id": "mistralai/Ministral-3-8B-Instruct-2512-BF16",
        "multimodal": True,
    },
    "qwen8b": {
        "id": "Qwen/Qwen3-8B-Base",
        "multimodal": False,
    },
}
DEFAULT_MODEL = "ministral8b"

# --- Thresholds ---
SUSPECT_PPL_THRESHOLD = 22     # Sentences below this are suspect
MEDIAN_WARNING_THRESHOLD = 30  # Warn if median PPL below this
MAX_SUSPECT_RATE = 0.25        # max acceptable suspect rate
MIN_SENTENCE_WORDS = 20        # Merge sentences shorter than this
ADJACENT_PPL_THRESHOLD = 30     # Adjacent low block detection
MIN_CONSECUTIVE = 4             # Minimum consecutive sentences for block
STD_WINDOW_SIZE = 14        # Sliding window size for std detection
STD_THRESHOLD = 14.0        # Standard deviation threshold
# Note: burstiness/Fano shows weaker discrimination than other metrics but provides complementary signal
BURSTINESS_WINDOW_SIZE = 14  # Sliding window size for burstiness detection
BURSTINESS_THRESHOLD = 5.0  # Burstiness (std of token lengths) threshold
LOW_PPL_DENSITY_WINDOW = 14      # Sliding window size for low PPL density detection
LOW_PPL_DENSITY_THRESHOLD = 25   # PPL threshold for "low" (sentences below this are counted)
LOW_PPL_DENSITY_RATIO = 0.30     # Max ratio of low PPL sentences in window before flagging

# --- Forbidden words ---
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


# --- Cache ---

CACHE_FILE = Path(__file__).parent / ".ppl_cache.db"


class PPLCache:
    """
    SQLite cache for computed perplexity values.

    Stores perplexity scores keyed by a hash of (model_name + sentence_text)
    to avoid redundant computation across runs.
    """

    def __init__(self, cache_path: Path, model_name: str):
        """
        Initialize the cache.

        Args:
            cache_path: Path to the SQLite database file.
            model_name: Name of the model (used in hash to separate caches per model).
        """
        self.cache_path = cache_path
        self.model_name = model_name
        self.conn = sqlite3.connect(cache_path)
        self._init_db()
        # Statistics for reporting
        self.hits = 0
        self.misses = 0

    def _init_db(self):
        """Create the cache table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                hash TEXT PRIMARY KEY,
                perplexity REAL NOT NULL,
                computed_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def hash(self, text: str) -> str:
        """
        Generate a unique hash combining model name and sentence text.

        Args:
            text: The sentence text to hash.

        Returns:
            SHA-256 hash of "model_name:text".
        """
        key = f"{self.model_name}:{text}"
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def bulk_lookup(self, sentences: List[str]) -> Tuple[Dict[str, float], List[str]]:
        """
        Look up multiple sentences in the cache at once.

        Args:
            sentences: List of sentence texts to look up.

        Returns:
            Tuple of (cached, uncached) where:
            - cached: Dict mapping sentence text to perplexity for found entries
            - uncached: List of sentence texts not found in cache
        """
        hashes = {self.hash(s): s for s in sentences}  # hash -> text
        placeholders = ",".join("?" * len(hashes))

        cursor = self.conn.execute(
            f"SELECT hash, perplexity FROM cache WHERE hash IN ({placeholders})",
            list(hashes.keys())
        )

        cached = {}
        found_hashes = set()
        for row in cursor:
            h, ppl = row
            cached[hashes[h]] = ppl  # text -> ppl
            found_hashes.add(h)

        uncached = [hashes[h] for h in hashes if h not in found_hashes]

        # Update statistics
        self.hits = len(cached)
        self.misses = len(uncached)

        return cached, uncached

    def bulk_store(self, results: Dict[str, float]):
        """
        Store multiple perplexity results in the cache.

        Args:
            results: Dict mapping sentence text to perplexity value.
        """
        now = datetime.now().isoformat()
        data = [
            (self.hash(text), ppl, now)
            for text, ppl in results.items()
        ]
        self.conn.executemany(
            "INSERT OR REPLACE INTO cache (hash, perplexity, computed_at) VALUES (?, ?, ?)",
            data
        )
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()


# --- Data structures ---

@dataclass
class SentenceAnalysis:
    """
    Analysis result for a single sentence with multi-criteria AI detection.

    Attributes:
        index: Position in the document (0-indexed).
        text: The sentence content.
        perplexity: Perplexity score from the language model.
        causes: Set of detection flags triggered (e.g., "low_perplexity", "low_std",
                "adjacent_low", "forbidden_word", "low_burstiness", "low_ppl_density").
        forbidden_words: Set of forbidden/AI-signal words found in the sentence.
    """
    index: int                          # Position in document (0-indexed)
    text: str                           # Sentence content
    perplexity: float                   # Perplexity score
    causes: Set[str] = field(default_factory=set)  # Detection flags triggered
    forbidden_words: Set[str] = field(default_factory=set)  # Forbidden words found

    def to_dict(self):
        """Convert to JSON-serializable dictionary."""
        return {
            "index": self.index,
            "text": self.text,
            "perplexity": round(self.perplexity, 1),
            "causes": sorted(list(self.causes)),
            "forbidden_words": sorted(list(self.forbidden_words))
        }


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


# --- Model wrapper ---

class PerplexityModel:
    """
    Wrapper for a language model used for perplexity calculation.

    Handles loading different model types (standard causal LM vs multimodal)
    and provides a unified interface for perplexity computation.
    """

    def __init__(self, model_config: dict, device: torch.device):
        """
        Initialize the model wrapper.

        Args:
            model_config: Dict with "id" (HuggingFace model ID) and "multimodal" (bool).
            device: PyTorch device to load the model onto.
        """
        self.device = device
        self.model_config = model_config
        self.model = None
        self.tokenizer = None

    def load(self):
        """
        Load the model and tokenizer to GPU.

        Returns:
            self for method chaining.
        """
        model_id = self.model_config["id"]
        is_multimodal = self.model_config["multimodal"]

        if is_multimodal:
            # Multimodal models (e.g., Mistral3) use special loading
            self.tokenizer = MistralCommonBackend.from_pretrained(model_id)
            self.model = Mistral3ForConditionalGeneration.from_pretrained(
                model_id, dtype=torch.float16, device_map={"": self.device}
            )
        else:
            # Standard causal language models
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, dtype=torch.float16
            ).to(self.device)

        self.model.eval()
        return self

    def perplexity(self, text: str) -> float:
        """
        Compute perplexity of the given text.

        Perplexity measures how "surprised" the model is by the text.
        Lower values indicate more predictable (potentially AI-generated) text.

        Args:
            text: The text to compute perplexity for.

        Returns:
            Perplexity score (exp of cross-entropy loss).
        """
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
        return torch.exp(outputs.loss).item()

    def unload(self):
        """Free GPU VRAM by deleting model and clearing cache."""
        if self.model is not None:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            torch.cuda.empty_cache()


# --- Analyzer ---

class PerplexityAnalyzer:
    """
    AI Slope diagnostic tool using multi-criteria perplexity analysis.

    This is NOT an AI detector - it's a diagnostic tool for "boring" text.
    The "AI Slope" phenomenon: generated text slides toward the predictable
    average. No errors, but no friction either. Detectors don't find "AI text" -
    they find predictable text.

    Diagnostic criteria:
    - Low perplexity: Model was very confident = well-trodden path
    - Low std windows: Uniform perplexity = no surprises
    - Low burstiness: Uniform sentence rhythm = mechanical flow
    - Low PPL density: High concentration of predictable sentences
    - Adjacent low blocks: Long sequences without friction
    - Forbidden words: Known AI-signal vocabulary (tells, not proof)

    Use the results as diagnostic signals, not as verdicts.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize the analyzer with specified model.

        Args:
            model_name: Key from MODELS dict (e.g., "ministral8b", "qwen8b").

        Raises:
            ValueError: If model_name is not in MODELS.
            RuntimeError: If CUDA is not available.
        """
        if model_name not in MODELS:
            raise ValueError(f"Unknown model: {model_name}. Choose from: {list(MODELS.keys())}")

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available. GPU required.")

        self.device = torch.device("cuda")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

        # Load base model
        model_config = MODELS[model_name]
        print(f"Loading {model_name} ({model_config['id']})...")
        self.base_model = PerplexityModel(model_config, self.device).load()
        print("Model loaded.\n")

        # Debug mode data storage
        self._debug_std_data = []
        self._debug_adjacent_blocks = []
        self._debug_burstiness_data = []
        self._debug_low_ppl_density_data = []

        # Perplexity cache
        self.cache = PPLCache(CACHE_FILE, model_name)

    def split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, handling French/English dialogue punctuation.

        Handles:
        - Markdown filtering (titles, separators)
        - French guillemets (« »)
        - Standard punctuation followed by uppercase letters

        Args:
            text: Raw text to split.

        Returns:
            List of sentence strings.
        """
        # Filter out markdown lines BEFORE joining (to avoid title+sentence merge)
        lines = text.strip().split('\n')
        filtered_lines = [
            line for line in lines
            if line.strip() and not re.match(r'^#{1,6}\s', line)  # Skip titles
            and not re.match(r'^-{3,}$', line.strip())  # Skip separators
            and not re.match(r'^\*{3,}$', line.strip())  # Skip separators
        ]
        text = ' '.join(filtered_lines)
        # Normalize French quotes: ". »" -> ".»" (remove space before closing quote)
        text = re.sub(r'([.!?])\s+([»"])', r'\1\2', text)
        # Split after .!? or .!?» or .!?" IF followed by uppercase
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ])|(?<=[.!?][»"])\s+(?=[A-ZÀ-ÖØ-Þ])', text)
        return [s.strip() for s in sentences if len(s.strip()) > 0]

    def is_valid_sentence(self, sentence: str) -> bool:
        """
        Check if a sentence is valid content (not markdown syntax).

        Args:
            sentence: The sentence to validate.

        Returns:
            True if the sentence is valid prose, False if it's markdown syntax.
        """
        s = sentence.strip()
        # Skip markdown: titles, separators, links, images
        if re.match(r"^#{1,6}\s", s):  # Titles
            return False
        if re.match(r"^-{3,}$", s):  # Horizontal rules (dashes)
            return False
        if re.match(r"^\*{3,}$", s):  # Horizontal rules (asterisks)
            return False
        if re.match(r"^!\[", s):  # Images
            return False
        if re.match(r"^\[.*\]\(.*\)$", s):  # Links
            return False
        return True

    def merge_short_sentences(self, sentences: List[str], min_words: int = MIN_SENTENCE_WORDS) -> List[str]:
        """
        Merge sentences shorter than min_words with adjacent sentences.

        Short sentences can skew perplexity calculations, so we merge them
        to ensure each analyzed unit has sufficient context.

        Args:
            sentences: List of sentences to process.
            min_words: Minimum word count threshold.

        Returns:
            List of sentences with short ones merged.
        """
        if not sentences:
            return sentences

        merged = []
        i = 0
        while i < len(sentences):
            current = sentences[i]
            word_count = len(re.findall(r"\b\w+\b", current))

            if word_count < min_words:
                if merged:
                    # Only merge if the previous sentence is still short
                    prev_word_count = len(re.findall(r"\b\w+\b", merged[-1]))
                    if prev_word_count < min_words:
                        # Previous is also short, merge together
                        merged[-1] = merged[-1] + " " + current
                    else:
                        # Previous already meets minimum, keep current separate
                        merged.append(current)
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

    def count_words(self, text: str) -> int:
        """Count words in text using word boundary regex."""
        return len(re.findall(r"\b\w+\b", text))

    def calculate_burstiness(self, sentences: List[str]) -> float:
        """
        Calculate burstiness as standard deviation of sentence lengths in tokens.

        Human writing typically shows higher variance in sentence length.
        AI-generated text often has more uniform sentence lengths.

        Args:
            sentences: List of sentence texts.

        Returns:
            Standard deviation of token lengths.
        """
        if not sentences:
            return 0.0
        lengths = [len(self.base_model.tokenizer.encode(s)) for s in sentences]
        return float(np.std(lengths))

    def calculate_fano_factor(self, sentences: List[str]) -> float:
        """
        Calculate Fano factor (variance/mean) of sentence lengths.

        Alternative measure to burstiness. Values near 1 indicate
        Poisson-like variance; higher values indicate more clustered lengths.

        Args:
            sentences: List of sentence texts.

        Returns:
            Fano factor (variance / mean of token lengths).
        """
        if not sentences:
            return 0.0
        lengths = [len(self.base_model.tokenizer.encode(s)) for s in sentences]
        mean = np.mean(lengths)
        return float(np.var(lengths) / mean) if mean > 0 else 0.0

    def detect_low_perplexity(self, sentences: List[SentenceAnalysis]):
        """
        Mark sentences with perplexity below SUSPECT_PPL_THRESHOLD.

        Low perplexity = the model was very confident = the text took
        the most predictable path. This is a signal of "boring" text
        sliding toward the average.

        Args:
            sentences: List of SentenceAnalysis objects to check (modified in place).
        """
        for sent in sentences:
            if sent.perplexity < SUSPECT_PPL_THRESHOLD:
                sent.causes.add("low_perplexity")

    def detect_forbidden_words(self, sentences: List[SentenceAnalysis]):
        """
        Mark sentences containing known AI-signal vocabulary.

        These are "tells" - words that AI models overuse. Their presence
        is a hint, not proof. Uses regex for exact word boundary matching.

        Args:
            sentences: List of SentenceAnalysis objects to check (modified in place).
        """
        for sent in sentences:
            for term in FORBIDDEN_TERMS:
                # Case-insensitive for all terms
                pattern = rf'\b{re.escape(term)}\b'
                match = re.search(pattern, sent.text, re.IGNORECASE)
                if match:
                    sent.causes.add("forbidden_word")
                    # Store actual word found (preserves case from text)
                    sent.forbidden_words.add(match.group(0))

    def detect_low_std(self, sentences: List[SentenceAnalysis], debug: bool = False):
        """
        Mark sentences in sliding windows with low perplexity standard deviation.

        Uniform perplexity across consecutive sentences = no surprises.
        Human writing naturally varies; mechanical text stays flat.
        This detects suspicious uniformity, not necessarily AI.

        Window size: STD_WINDOW_SIZE sentences
        Threshold: σ < STD_THRESHOLD

        Args:
            sentences: List of SentenceAnalysis objects to check (modified in place).
            debug: If True, store detailed window data for reporting.
        """
        if len(sentences) < STD_WINDOW_SIZE:
            return  # Document too short for windowed analysis

        # Extract perplexity values
        ppls = np.array([s.perplexity for s in sentences])

        # Create sliding windows (NumPy 1.20+)
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(ppls, STD_WINDOW_SIZE)

        # Calculate standard deviation for each window
        stds = np.std(windows, axis=1)

        # Capture data for debug mode
        if debug:
            self._debug_std_data = []
            for i, std in enumerate(stds):
                self._debug_std_data.append({
                    'window_start': i,
                    'window_end': i + STD_WINDOW_SIZE - 1,
                    'std': float(std),
                    'flagged': std < STD_THRESHOLD,
                    'ppls': ppls[i:i+STD_WINDOW_SIZE].tolist()
                })

        # Flag all sentences in suspicious windows
        for i, std in enumerate(stds):
            if std < STD_THRESHOLD:
                for j in range(i, i + STD_WINDOW_SIZE):
                    sentences[j].causes.add("low_std")

    def detect_low_burstiness(self, sentences: List[SentenceAnalysis], debug: bool = False):
        """
        Mark sentences in windows with low variation in sub-sentence lengths.

        Burstiness is calculated on sub-sentences (split by punctuation).
        Uniform sentence rhythm = mechanical flow. Human writing has natural
        variation in cadence; text sliding toward the average doesn't.

        Args:
            sentences: List of SentenceAnalysis objects to check (modified in place).
            debug: If True, store detailed window data for reporting.
        """
        if len(sentences) < BURSTINESS_WINDOW_SIZE:
            return

        if debug:
            self._debug_burstiness_data = []

        for i in range(len(sentences) - BURSTINESS_WINDOW_SIZE + 1):
            # Get sentences in current window
            window_sentences = [s.text for s in sentences[i:i+BURSTINESS_WINDOW_SIZE]]

            # Split into sub-sentences and measure token lengths
            sub_lengths = []
            for sent in window_sentences:
                for sub in re.split(r'(?<=[.!?])\s+', sent):
                    sub = sub.strip()
                    if sub:
                        sub_lengths.append(len(self.base_model.tokenizer.encode(sub)))

            # Burstiness = std of sub-sentence lengths
            std = float(np.std(sub_lengths)) if sub_lengths else 0.0
            # Fano factor = variance / mean
            mean_len = float(np.mean(sub_lengths)) if sub_lengths else 0.0
            fano = float(np.var(sub_lengths) / mean_len) if mean_len > 0 else 0.0
            flagged = std < BURSTINESS_THRESHOLD

            if debug:
                self._debug_burstiness_data.append({
                    'window_start': i,
                    'window_end': i + BURSTINESS_WINDOW_SIZE - 1,
                    'std': std,
                    'fano': fano,
                    'flagged': flagged,
                    'lengths': sub_lengths
                })

            if flagged:
                for j in range(i, i + BURSTINESS_WINDOW_SIZE):
                    sentences[j].causes.add("low_burstiness")

    def detect_low_ppl_density(self, sentences: List[SentenceAnalysis], debug: bool = False):
        """
        Mark sentences in windows with high concentration of low-perplexity sentences.

        When too many sentences in a window are predictable, the whole passage
        is sliding toward the average - even if individual sentences don't
        cross thresholds. Cumulative boredom signal.

        Window size: LOW_PPL_DENSITY_WINDOW sentences
        Threshold: Mark if >LOW_PPL_DENSITY_RATIO have PPL < LOW_PPL_DENSITY_THRESHOLD

        Args:
            sentences: List of SentenceAnalysis objects to check (modified in place).
            debug: If True, store detailed window data for reporting.
        """
        if len(sentences) < LOW_PPL_DENSITY_WINDOW:
            return  # Document too short

        if debug:
            self._debug_low_ppl_density_data = []

        # Create boolean array: True if PPL < threshold
        is_low_ppl = np.array([s.perplexity < LOW_PPL_DENSITY_THRESHOLD for s in sentences])

        # Sliding windows
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(is_low_ppl, LOW_PPL_DENSITY_WINDOW)

        for i, window in enumerate(windows):
            low_count = np.sum(window)
            ratio = low_count / LOW_PPL_DENSITY_WINDOW
            flagged = ratio > LOW_PPL_DENSITY_RATIO

            if debug:
                self._debug_low_ppl_density_data.append({
                    'window_start': i,
                    'window_end': i + LOW_PPL_DENSITY_WINDOW - 1,
                    'low_count': int(low_count),
                    'ratio': float(ratio),
                    'flagged': flagged
                })

            if flagged:
                for j in range(i, i + LOW_PPL_DENSITY_WINDOW):
                    sentences[j].causes.add("low_ppl_density")

    def detect_adjacent_low(self, sentences: List[SentenceAnalysis], debug: bool = False):
        """
        Mark blocks of MIN_CONSECUTIVE+ consecutive sentences with low perplexity.

        Long sequences without surprises = extended stretches of predictable text.
        No friction, no unexpected turns. The text is coasting downhill toward
        the average. Strong signal of "boring" passages.

        Threshold: PPL < ADJACENT_PPL_THRESHOLD
        Minimum block size: MIN_CONSECUTIVE sentences

        Args:
            sentences: List of SentenceAnalysis objects to check (modified in place).
            debug: If True, store detailed block data for reporting.
        """
        consecutive_count = 0
        block_start = 0

        # Capture data for debug mode
        if debug:
            self._debug_adjacent_blocks = []

        for i, sent in enumerate(sentences):
            if sent.perplexity < ADJACENT_PPL_THRESHOLD:
                if consecutive_count == 0:
                    block_start = i
                consecutive_count += 1
            else:
                # End of block - check if it qualifies
                if consecutive_count >= MIN_CONSECUTIVE:
                    if debug:
                        self._debug_adjacent_blocks.append({
                            'start': block_start,
                            'end': i - 1,
                            'length': consecutive_count,
                            'flagged': True
                        })
                    for j in range(block_start, i):
                        sentences[j].causes.add("adjacent_low")
                elif consecutive_count > 0 and debug:
                    # Block too short (for debug, show non-qualifying blocks too)
                    self._debug_adjacent_blocks.append({
                        'start': block_start,
                        'end': i - 1,
                        'length': consecutive_count,
                        'flagged': False
                    })
                consecutive_count = 0

        # Handle block extending to end of document
        if consecutive_count >= MIN_CONSECUTIVE:
            if debug:
                self._debug_adjacent_blocks.append({
                    'start': block_start,
                    'end': len(sentences) - 1,
                    'length': consecutive_count,
                    'flagged': True
                })
            for j in range(block_start, len(sentences)):
                sentences[j].causes.add("adjacent_low")
        elif consecutive_count > 0 and debug:
            self._debug_adjacent_blocks.append({
                'start': block_start,
                'end': len(sentences) - 1,
                'length': consecutive_count,
                'flagged': False
            })

    def analyze(self, text: str, debug: bool = False) -> dict:
        """
        Run AI Slope diagnostic analysis on text.

        Pipeline:
        1. Preprocessing: Split into sentences, filter markdown, merge short sentences
        2. Perplexity computation: Look up cache, compute missing values
        3. Metrics calculation: Burstiness and Fano factor
        4. Diagnostic checks: Apply all criteria to identify predictable passages
        5. Return results with metadata

        Args:
            text: The text to analyze.
            debug: If True, include detailed window/block data in results.

        Returns:
            Dict containing:
            - analyses: List of SentenceAnalysis objects with diagnostic markers
            - total_sentences: Count before filtering
            - valid_sentences_count: Count after markdown filtering
            - merged_sentences_count: Count after short sentence merging
            - burstiness: Document-level rhythm variation metric
            - fano: Document-level Fano factor
            - cache_hits/misses: Cache statistics
            - debug_*: (if debug=True) Detailed window/block data
        """
        # Step 1: Preprocessing
        all_sentences = self.split_sentences(text)
        valid_sentences = [s for s in all_sentences if self.is_valid_sentence(s)]
        merged_sentences = self.merge_short_sentences(valid_sentences)

        # Step 2: Cache lookup + compute missing perplexities
        cached, uncached = self.cache.bulk_lookup(merged_sentences)

        # Compute only uncached sentences
        new_results = {}
        if uncached:
            for sentence in tqdm(uncached, desc="Computing perplexity", unit="sent"):
                ppl = self.base_model.perplexity(sentence)
                new_results[sentence] = ppl
            self.cache.bulk_store(new_results)

        # Merge cached + new results
        all_ppls = {**cached, **new_results}
        analyses = [
            SentenceAnalysis(
                index=idx,
                text=sentence,
                perplexity=all_ppls[sentence],
                causes=set(),
                forbidden_words=set()
            )
            for idx, sentence in enumerate(merged_sentences)
        ]

        # Step 3: Pre-calculate metrics that need tokenizer
        merged_sentences_text = [s.text for s in analyses]
        burstiness = self.calculate_burstiness(merged_sentences_text)
        fano = self.calculate_fano_factor(merged_sentences_text)

        # Step 4: Apply all detection criteria
        self.detect_forbidden_words(analyses)
        self.detect_low_perplexity(analyses)
        self.detect_low_std(analyses, debug=debug)
        self.detect_low_burstiness(analyses, debug=debug)
        self.detect_low_ppl_density(analyses, debug=debug)
        self.detect_adjacent_low(analyses, debug=debug)

        # Step 5: Build and return results
        result = {
            'analyses': analyses,
            'total_sentences': len(all_sentences),
            'valid_sentences_count': len(valid_sentences),
            'merged_sentences_count': len(merged_sentences),
            'burstiness': burstiness,
            'fano': fano,
            'cache_hits': self.cache.hits,
            'cache_misses': self.cache.misses,
        }

        # Add debug data if requested
        if debug:
            result['debug_std_windows'] = self._debug_std_data
            result['debug_burstiness_windows'] = self._debug_burstiness_data
            result['debug_low_ppl_density_windows'] = self._debug_low_ppl_density_data
            result['debug_adjacent_blocks'] = self._debug_adjacent_blocks

        return result

    def print_report(self, analysis_result: dict, title: str, debug: bool = False, output_file=None):
        """
        Print detailed analysis report to stdout or file.

        Args:
            analysis_result: Dict returned by analyze().
            title: Title for the report (typically filename).
            debug: If True, print extended debug information.
            output_file: File object to write to (None = stdout).
        """
        analyses = analysis_result['analyses']
        ppls = [a.perplexity for a in analyses]
        total_words = sum(self.count_words(a.text) for a in analyses)

        # Header section
        print("\n" + "=" * 80, file=output_file)
        print(f"📄 File: {title}", file=output_file)
        print(f"   Sentences: {analysis_result['total_sentences']} initial → {analysis_result['valid_sentences_count']} valid → {len(analyses)} analyzed", file=output_file)
        print(f"   (filtered: {analysis_result['total_sentences'] - analysis_result['valid_sentences_count']} markdown, merged: {analysis_result['valid_sentences_count'] - analysis_result['merged_sentences_count']})", file=output_file)
        print(f"   Words analyzed: {total_words}", file=output_file)

        # Cache stats
        cache_hits = analysis_result.get('cache_hits', 0)
        cache_misses = analysis_result.get('cache_misses', 0)
        cache_total = cache_hits + cache_misses
        cache_pct = (cache_hits / cache_total * 100) if cache_total > 0 else 0
        print(f"   📦 Cache: {cache_hits}/{cache_total} hits ({cache_pct:.1f}%), {cache_misses} computed", file=output_file)
        print("=" * 80, file=output_file)

        # Perplexity statistics
        print(f"\n📊 Perplexity stats:", file=output_file)
        print(f"   Mean: {np.mean(ppls):.1f} | Median: {np.median(ppls):.1f} | Std: {np.std(ppls):.1f}", file=output_file)

        # Burstiness (pre-calculated in analyze() before tokenizer was unloaded)
        burstiness = analysis_result.get('burstiness', 0.0)
        fano = analysis_result.get('fano', 0.0)
        print(f"\n📏 Sentence variation:", file=output_file)
        print(f"   Burstiness: {burstiness:.1f} | Fano: {fano:.1f}", file=output_file)

        # Detection counters
        count_low_ppl = sum(1 for a in analyses if "low_perplexity" in a.causes)
        count_low_var = sum(1 for a in analyses if "low_std" in a.causes)
        count_low_burst = sum(1 for a in analyses if "low_burstiness" in a.causes)
        count_low_density = sum(1 for a in analyses if "low_ppl_density" in a.causes)
        count_adj = sum(1 for a in analyses if "adjacent_low" in a.causes)
        count_forbidden = sum(1 for a in analyses if "forbidden_word" in a.causes)
        count_flagged = sum(1 for a in analyses if a.causes)
        count_multi = sum(1 for a in analyses if len(a.causes) > 1)

        print(f"\n🎯 Detection results:", file=output_file)
        print(f"   Low perplexity (<{SUSPECT_PPL_THRESHOLD}): {count_low_ppl} sentences", file=output_file)
        print(f"   Low std windows: {count_low_var} sentences", file=output_file)
        print(f"   Low burstiness windows: {count_low_burst} sentences", file=output_file)
        print(f"   Low PPL density (>{LOW_PPL_DENSITY_RATIO*100:.0f}% <{LOW_PPL_DENSITY_THRESHOLD}): {count_low_density} sentences", file=output_file)
        print(f"   Adjacent low blocks: {count_adj} sentences", file=output_file)
        print(f"   Forbidden words: {count_forbidden} sentences", file=output_file)
        print(f"   Total flagged: {count_flagged} ({count_flagged/len(analyses)*100:.1f}%)", file=output_file)
        print(f"   Multi-flagged: {count_multi} ({count_multi/len(analyses)*100:.1f}%)", file=output_file)

        # Warning if suspect rate exceeds threshold
        suspect_rate = count_flagged / len(analyses) if analyses else 0
        if suspect_rate > MAX_SUSPECT_RATE:
            print(f"\n⚠️  WARNING: Suspect rate ({suspect_rate*100:.1f}%) exceeds threshold ({MAX_SUSPECT_RATE*100:.0f}%)", file=output_file)
            print(f"   Flagged sentences listed below:", file=output_file)

        # Flagged sentences - only if not in debug mode
        if not debug:
            flagged = [a for a in analyses if a.causes]
            if flagged:
                print("\n" + "-" * 80, file=output_file)
                print("FLAGGED SENTENCES (document order)", file=output_file)
                print("-" * 80, file=output_file)
                for i, sent in enumerate(flagged, 1):
                    causes_str = ", ".join(sorted(sent.causes))
                    print(f"\n{i:3}. [{sent.perplexity:6.1f}] {causes_str}", file=output_file)

                    # Show forbidden words if present
                    if sent.forbidden_words:
                        words_str = ", ".join(f'"{w}"' for w in sorted(sent.forbidden_words))
                        print(f"     Forbidden: {words_str}", file=output_file)

                    print(f"     {sent.text}", file=output_file)
            else:
                print("\n✓ No flagged sentences.", file=output_file)

        # === MODE DEBUG ===
        if debug:
            print("\n" + "=" * 80, file=output_file)
            print("🐛 DEBUG MODE - Detailed Analysis", file=output_file)
            print("=" * 80, file=output_file)

            # 1. Table of all sentences
            print("\n📋 ALL SENTENCES (with perplexity)", file=output_file)
            print("-" * 120, file=output_file)
            print(f"{'#':<4} {'PPL':<8} {'Words':<6} {'Flags':<30} {'Forbidden':<20} {'Text':<40}", file=output_file)
            print("-" * 120, file=output_file)
            for i, sent in enumerate(analyses):
                flags = ", ".join(sorted(sent.causes)) if sent.causes else "—"
                forbidden = ", ".join(sorted(sent.forbidden_words)) if sent.forbidden_words else "—"
                word_count = self.count_words(sent.text)
                text_short = sent.text[:37] + "..." if len(sent.text) > 40 else sent.text
                print(f"{i:<4} {sent.perplexity:<8.1f} {word_count:<6} {flags:<30} {forbidden:<20} {text_short:<40}", file=output_file)

            # 2. Sentences near thresholds
            print(f"\n⚠️  SENTENCES NEAR THRESHOLDS", file=output_file)
            print("-" * 80, file=output_file)

            # PPL near low_perplexity threshold
            near_low_ppl = [s for s in analyses if SUSPECT_PPL_THRESHOLD <= s.perplexity <= MEDIAN_WARNING_THRESHOLD]
            if near_low_ppl:
                print(f"Near low_perplexity threshold ({SUSPECT_PPL_THRESHOLD} ≤ PPL ≤ {MEDIAN_WARNING_THRESHOLD}): {len(near_low_ppl)} sentences", file=output_file)
                for s in near_low_ppl[:5]:  # Max 5 examples
                    print(f"  - [{s.perplexity:.1f}] {s.text[:80]}...", file=output_file)
            else:
                print(f"Near low_perplexity threshold ({SUSPECT_PPL_THRESHOLD} ≤ PPL ≤ {MEDIAN_WARNING_THRESHOLD}): none", file=output_file)

            # PPL near adjacent_low threshold
            near_adj_ppl = [s for s in analyses if ADJACENT_PPL_THRESHOLD <= s.perplexity <= ADJACENT_PPL_THRESHOLD + 10]
            if near_adj_ppl:
                print(f"\nNear adjacent_low threshold ({ADJACENT_PPL_THRESHOLD} ≤ PPL ≤ {ADJACENT_PPL_THRESHOLD + 10}): {len(near_adj_ppl)} sentences", file=output_file)
                for s in near_adj_ppl[:5]:
                    print(f"  - [{s.perplexity:.1f}] {s.text[:80]}...", file=output_file)
            else:
                print(f"\nNear adjacent_low threshold ({ADJACENT_PPL_THRESHOLD} ≤ PPL ≤ {ADJACENT_PPL_THRESHOLD + 10}): none", file=output_file)

            # 3. Std windows
            if 'debug_std_windows' in analysis_result:
                print(f"\n📊 STD WINDOWS (threshold: σ < {STD_THRESHOLD})", file=output_file)
                print("-" * 80, file=output_file)
                windows = analysis_result['debug_std_windows']
                print(f"{'Window':<15} {'Std':<8} {'Flagged':<10} {'PPLs':<40}", file=output_file)
                print("-" * 80, file=output_file)
                for w in windows:
                    flag_marker = "🚩 YES" if w['flagged'] else "—"
                    ppls_str = ", ".join([f"{p:.1f}" for p in w['ppls']])
                    print(f"[{w['window_start']}-{w['window_end']}]{'':<7} {w['std']:<8.2f} {flag_marker:<10} [{ppls_str}]", file=output_file)

                flagged_windows = [w for w in windows if w['flagged']]
                print(f"\nTotal: {len(windows)} windows, {len(flagged_windows)} flagged (σ < {STD_THRESHOLD})", file=output_file)

            # 4. Burstiness windows
            if 'debug_burstiness_windows' in analysis_result:
                print(f"\n📏 BURSTINESS WINDOWS (threshold: σ < {BURSTINESS_THRESHOLD})", file=output_file)
                print("-" * 90, file=output_file)
                windows = analysis_result['debug_burstiness_windows']
                print(f"{'Window':<15} {'Std':<8} {'Fano':<8} {'Flagged':<10} {'Lengths':<40}", file=output_file)
                print("-" * 90, file=output_file)
                for w in windows:
                    flag_marker = "🚩 YES" if w['flagged'] else "—"
                    lengths_str = ", ".join([str(l) for l in w['lengths']])
                    fano_val = w.get('fano', 0.0)
                    print(f"[{w['window_start']}-{w['window_end']}]{'':<7} {w['std']:<8.2f} {fano_val:<8.2f} {flag_marker:<10} [{lengths_str}]", file=output_file)

                flagged_windows = [w for w in windows if w['flagged']]
                print(f"\nTotal: {len(windows)} windows, {len(flagged_windows)} flagged (σ < {BURSTINESS_THRESHOLD})", file=output_file)

            # 4b. Low PPL density windows
            if 'debug_low_ppl_density_windows' in analysis_result:
                print(f"\n📈 LOW PPL DENSITY WINDOWS (threshold: PPL < {LOW_PPL_DENSITY_THRESHOLD}, ratio > {LOW_PPL_DENSITY_RATIO})", file=output_file)
                print("-" * 80, file=output_file)
                windows = analysis_result['debug_low_ppl_density_windows']
                print(f"{'Window':<15} {'Low/Total':<12} {'Ratio':<8} {'Flagged':<10}", file=output_file)
                print("-" * 80, file=output_file)
                for w in windows:
                    flag_marker = "🚩 YES" if w['flagged'] else "—"
                    print(f"[{w['window_start']}-{w['window_end']}]{'':<7} {w['low_count']}/{LOW_PPL_DENSITY_WINDOW:<4} {w['ratio']:<8.2f} {flag_marker}", file=output_file)

                flagged_windows = [w for w in windows if w['flagged']]
                print(f"\nTotal: {len(windows)} windows, {len(flagged_windows)} flagged (ratio > {LOW_PPL_DENSITY_RATIO})", file=output_file)

            # 5. Adjacent blocks
            if 'debug_adjacent_blocks' in analysis_result:
                print(f"\n🔗 ADJACENT LOW BLOCKS (threshold: PPL < {ADJACENT_PPL_THRESHOLD}, min length: {MIN_CONSECUTIVE})", file=output_file)
                print("-" * 80, file=output_file)
                blocks = analysis_result['debug_adjacent_blocks']
                if blocks:
                    print(f"{'Block':<15} {'Length':<8} {'Flagged':<10}", file=output_file)
                    print("-" * 80, file=output_file)
                    for b in blocks:
                        flag_marker = "🚩 YES" if b['flagged'] else f"NO (< {MIN_CONSECUTIVE})"
                        print(f"[{b['start']}-{b['end']}]{'':<7} {b['length']:<8} {flag_marker}", file=output_file)

                    flagged_blocks = [b for b in blocks if b['flagged']]
                    print(f"\nTotal: {len(blocks)} blocks detected, {len(flagged_blocks)} flagged (length ≥ {MIN_CONSECUTIVE})", file=output_file)
                else:
                    print("No blocks detected (no consecutive sentences with PPL < 40)", file=output_file)

            print("\n" + "=" * 80, file=output_file)


def main():
    """
    Main entry point for the AI Slope diagnostic tool.

    Parses command-line arguments, loads the model, runs diagnostic
    analysis on input files, and outputs reports to screen or file.
    """
    parser = argparse.ArgumentParser(
        description="AI Slope diagnostic - multi-criteria perplexity analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  uv run detection.py chapter-01.md                  # Show report on screen
  uv run detection.py chapter-01.md -o report.txt    # Write report to file
  uv run detection.py ch01.md ch02.md -o batch.txt   # Batch: consolidate all reports

Output:
  - Human-readable report (screen or file with -o)
"""
    )
    parser.add_argument("files", nargs="+",
                       help="Markdown files to analyze")
    parser.add_argument("-m", "--model",
                       choices=list(MODELS.keys()),
                       default=DEFAULT_MODEL,
                       help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("-o", "--output",
                       help="Write report to file instead of screen")
    parser.add_argument("--debug", action="store_true",
                       help="Show detailed debug information for threshold calibration")

    args = parser.parse_args()

    # Lock + load model
    acquire_lock()

    try:
        analyzer = PerplexityAnalyzer(model_name=args.model)
    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nThis script requires CUDA (NVIDIA GPU).")
        print("Check that:")
        print("  - You have an NVIDIA GPU")
        print("  - CUDA toolkit is installed")
        print("  - PyTorch is installed with CUDA support")
        print("\nRun with: uv run detection.py file.md")
        sys.exit(1)

    # Open output file if requested
    output_file = None
    if args.output:
        output_path = Path(args.output)
        output_file = open(output_path, 'w', encoding='utf-8-sig')  # BOM UTF-8 for Windows compatibility

    try:
        # Analyze each file
        for file_arg in args.files:
            filepath = Path(file_arg)
            if not filepath.exists():
                print(f"Error: File not found: {filepath}", file=sys.stderr)
                continue

            # Try multiple encodings
            text = None
            for encoding in ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']:
                try:
                    text = filepath.read_text(encoding=encoding)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if text is None:
                print(f"Error: Could not decode file {filepath} with any known encoding", file=sys.stderr)
                continue
            result = analyzer.analyze(text, debug=args.debug)

            # Print report (to screen or file)
            analyzer.print_report(result, title=filepath.name, debug=args.debug, output_file=output_file)

        # Confirmation message if file output
        if args.output:
            print(f"\n✓ Report saved to: {output_path}")
    finally:
        # Close cache and file
        analyzer.cache.close()
        if output_file:
            output_file.close()


if __name__ == "__main__":
    main()
