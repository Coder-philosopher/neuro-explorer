"""
Train a control-vector "dial" for a behaviour (e.g. poetic), using repeng.

Usage:
  python scripts/train_dial.py --name poetic --pos "a poetic writer..." --neg "a plain writer..." \
      [--template "Act as if you're a {persona}."] [--layers -5:-19] [--out vectors]

Output:
  vectors/<name>.gguf   (llama.cpp-ready control vector)
  vectors/<name>.meta.json  (training details, for the Atlas)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "qwen3-0.6b"
DATA_DIR = ROOT / "scripts"

sys.path.insert(0, str(ROOT / "scripts"))

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 2 threads only: the studio engines share this 4-core CPU; training must
# never starve generation (a full 4-thread hog made answers crawl at 2 tok/s).
torch.set_num_threads(2)

from repeng import ControlVector, ControlModel, DatasetEntry


def load_suffix_corpus(tokenizer):
    """repeng's standard corpus of neutral text fragments (CC0/public use from the repeng repo)."""
    with open(DATA_DIR / "all_truncated_outputs.json", encoding="utf-8") as f:
        output_suffixes = json.load(f)
    suffixes = [
        tokenizer.convert_tokens_to_string(tokens[:i])
        for tokens in (tokenizer.tokenize(s) for s in output_suffixes)
        for i in range(1, len(tokens))
    ]
    return suffixes


def make_dataset(template, pos, neg, suffix_list) -> list[DatasetEntry]:
    """Qwen3 chat format, INCLUDING the system segment — the studio always
    serves system='/no_think' before the user turn, so extraction must see
    the same prefix or the vector trains on a shifted format:
    <|im_start|>system\\n/no_think<|im_end|>\\n<|im_start|>user\\n{content}<|im_end|>\\n<|im_start|>assistant\\n"""
    sys_tag = "<|im_start|>system\n/no_think<|im_end|>\n"
    user_tag = "<|im_start|>user\n"
    asst_tag = "<|im_end|>\n<|im_start|>assistant\n"
    dataset = []
    for suffix in suffix_list:
        dataset.append(
            DatasetEntry(
                positive=f"{sys_tag}{user_tag}{template.format(persona=pos)}{asst_tag}{suffix}",
                negative=f"{sys_tag}{user_tag}{template.format(persona=neg)}{asst_tag}{suffix}",
            )
        )
    return dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--template", default="Act as if you're a very {persona}.")
    ap.add_argument("--pos", required=True, help="positive persona, e.g. 'poetic, lyrical writer...'")
    ap.add_argument("--neg", required=True, help="negative persona, the opposite")
    ap.add_argument("--layers", default="-5:-19", help="layer range as start:end (negative indices)")
    ap.add_argument("--out", default=str(ROOT / "vectors"))
    ap.add_argument("--max-suffixes", type=int, default=512)
    args = ap.parse_args()

    lo, hi = args.layers.split(":")
    layers = list(range(int(lo), int(hi), -1) if int(lo) > int(hi) else range(int(lo), int(hi)))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] loading tokenizer + model (local: {MODEL_DIR})")
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    torch.set_num_threads(2)  # leave cores for the chat engines
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_DIR), torch_dtype=torch.float32, device_map="cpu"
    )
    model = ControlModel(model, layers)
    print(f"[2/4] model ready, dials hooked on layers {layers}")

    suffixes = load_suffix_corpus(tokenizer)[: args.max_suffixes]
    dataset = make_dataset(args.template, args.pos, args.neg, suffixes)
    print(f"[3/4] dataset: {len(dataset)} paired examples, training vector...")

    t0 = time.time()
    vector = ControlVector.train(model, tokenizer, dataset)
    dt = time.time() - t0
    print(f"      trained in {dt:.1f}s")

    model.reset()

    gguf_path = out_dir / f"{args.name}.gguf"
    vector.export_gguf(str(gguf_path))
    meta = {
        "name": args.name,
        "model": str(MODEL_DIR.name),
        "template": args.template,
        "positive_persona": args.pos,
        "negative_persona": args.neg,
        "layers": layers,
        "n_examples": len(dataset),
        "train_seconds": round(dt, 1),
        "gguf": str(gguf_path.name),
        "trained": "repeng (RepE, PCA-diff)",
        "format": "qwen3-chat+system(/no_think) — matches studio serving",
        "date": time.strftime("%Y-%m-%d %H:%M"),
    }
    meta_path = out_dir / f"{args.name}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[4/4] saved {gguf_path} and {meta_path}")


if __name__ == "__main__":
    main()
