"""
Before/after demo for a trained dial — runs llama.cpp at several strengths
and saves a plain-text sweep into atlas/. CPU-only, no GPU needed.

Usage:
  python scripts/demo_dial.py --name poetic --prompt "Describe the sea..." --strengths 0,1,2,4
"""

import argparse
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "llama.cpp" / "llama-completion.exe"
MODEL = ROOT / "models" / "Qwen3-0.6B-Q8_0.gguf"
VECTOR_DIR = ROOT / "vectors"
ATLAS_DIR = ROOT / "atlas"

NO_THINK = "<|im_start|>system\n/no_think<|im_end|>\n"
CHAT = "<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n"


def generate(vec: str | None, strength: float, prompt: str, ntokens: int) -> tuple[str, float]:
    full_prompt = NO_THINK + CHAT.format(q=prompt)
    cmd = [
        str(BIN), "-m", str(MODEL), "-t", "4",
        "-p", full_prompt, "-n", str(ntokens), "--temp", "0.7",
        "--no-display-prompt", "--simple-io",
    ]
    if vec is not None and strength > 0:
        # NB: llama.cpp splits FNAME:SCALE on ":" — Windows drive letters break it.
        # Run from ROOT and pass a relative path (no drive colon).
        vec_arg = os.path.relpath(vec, str(ROOT)).replace("\\", "/")
        cmd += ["--control-vector-scaled", f"{vec_arg}:{strength}"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                           encoding="utf-8", errors="replace", cwd=str(ROOT))
        text = (r.stdout or "").strip() or (r.stderr or "").strip()[-400:]
    except subprocess.TimeoutExpired:
        text = "[TIMEOUT]"
    return text, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--strengths", default="0,1,2,4")
    ap.add_argument("--ntokens", type=int, default=120)
    ap.add_argument("--vector", default=None)
    args = ap.parse_args()

    vec = args.vector or str(VECTOR_DIR / f"{args.name}.gguf")
    strengths = [float(s) for s in args.strengths.split(",")]

    results = {}
    for s in strengths:
        print(f"--- strength {s} ---", flush=True)
        text, dt = generate(vec, s, args.prompt, args.ntokens)
        results[s] = {"seconds": round(dt, 1), "output": text}
        print(text[:600], "\n", flush=True)

    ATLAS_DIR.mkdir(exist_ok=True)
    n = 1
    path = ATLAS_DIR / f"{args.name}_sweep{n}.txt"
    while path.exists():
        n += 1
        path = ATLAS_DIR / f"{args.name}_sweep{n}.txt"
    sweeplog = f"SWEEP: {args.name}\nPROMPT: {args.prompt}\n\n"
    sweeplog += "\n\n".join(
        f"== strength {s} ==\n{v['output'][:1000]}" for s, v in results.items()
    )
    path.write_text(sweeplog, encoding="utf-8")

    entry = {
        "type": "demo_strength_sweep",
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "vector": vec,
        "prompt": args.prompt,
        "strengths": {str(s): v for s, v in results.items()},
    }
    import json
    (ATLAS_DIR / f"{path.stem}.json").write_text(
        json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"saved -> {path}")


if __name__ == "__main__":
    main()
