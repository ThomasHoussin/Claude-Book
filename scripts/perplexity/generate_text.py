"""
Generate French text with Mistral-7B based on input prompt.

Usage:
  uv run generate_text.py prompt.txt           # From file
  echo "Écris une histoire..." | uv run generate_text.py  # From stdin
  uv run generate_text.py -p "Écris une histoire..."      # Direct prompt
"""

import argparse
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def generate(prompt: str, target_words: int = 2000):
    """Generate text based on prompt."""
    model_id = "mistralai/Mistral-7B-v0.3"

    print(f"Loading {model_id}...", file=sys.stderr)

    if not torch.cuda.is_available():
        print("Error: CUDA not available. GPU required.", file=sys.stderr)
        sys.exit(1)

    device = torch.device("cuda")
    print(f"GPU: {torch.cuda.get_device_name(0)}", file=sys.stderr)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, dtype=torch.float16
    ).to(device)
    model.eval()
    print("Model loaded.\n", file=sys.stderr)

    # Estimate tokens needed (~1.5 tokens per word for French)
    target_tokens = int(target_words * 1.5)

    # Tokenize prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    prompt_length = inputs["input_ids"].shape[1]

    print(f"Generating ~{target_words} words...", file=sys.stderr)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=target_tokens,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Decode only the generated part (exclude prompt)
    generated = tokenizer.decode(outputs[0][prompt_length:], skip_special_tokens=True)

    # Word count
    word_count = len(generated.split())
    print(f"Generated {word_count} words.", file=sys.stderr)

    return generated


def main():
    parser = argparse.ArgumentParser(
        description="Generate French text with Mistral-7B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", nargs="?", help="Input file with prompt (use - for stdin)")
    parser.add_argument("-p", "--prompt", help="Direct prompt text")
    parser.add_argument("-w", "--words", type=int, default=2000, help="Target word count (default: 2000)")

    args = parser.parse_args()

    # Get prompt
    if args.prompt:
        prompt = args.prompt
    elif args.file:
        if args.file == "-":
            prompt = sys.stdin.buffer.read().decode("utf-8")
        else:
            prompt = Path(args.file).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        prompt = sys.stdin.buffer.read().decode("utf-8")
    else:
        print("Error: No input provided. Use -p, a file, or pipe input.", file=sys.stderr)
        sys.exit(1)

    prompt = prompt.strip()
    if not prompt:
        print("Error: Empty prompt.", file=sys.stderr)
        sys.exit(1)

    # Generate and print to stdout
    generated = generate(prompt, args.words)
    print(generated)


if __name__ == "__main__":
    main()
