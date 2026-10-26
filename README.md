# NEUROEXPLORER

> *formerly "Model Steering Studio" — renamed 2026-10-26.*

**A local mixing desk for a language model's personality.**

Load a small open-source model (Qwen3-class) on a machine with no GPU,
treat its behaviours as physical dials (control vectors), turn the dials,
compare steered vs. plain output side by side, and write every finding —
including the failures — into a lab notebook called the **Atlas**.

Everything runs on your machine. No cloud, no API keys, no telemetry.

---

## What we're trying to do

Representation engineering (RepE) — steering a model by adding directions to
its residual stream — is usually demonstrated on lab hardware with big models.
NEUROEXPLORER asks a different question:

> **Can a person with only ~10 GB of RAM, a 4-core CPU and no GPU explore,
> train and document model steering for themselves — honestly, reproducibly,
> and in a form good enough that others can build on it?**

So this project is three things in one:

1. **A tool** — a working steering studio (chat UI, dial sliders, honest
   A/B comparison, presets, in-app dial training).
2. **A method** — the full recipe (repeng extraction → GGUF control vectors
   → llama.cpp runtime) with every knob and gotcha documented.
3. **A record** — the `atlas/` folder: sweeps, sweet spots, break points,
   bug autopsies, and an auto-log of every generation. **Failed experiments
   are deliberately kept**, because "negative results" are the half of
   science people throw away.

## What we did (the short version)

- Picked the stack for low-end constraints: **llama.cpp** (CPU runtime),
  **repeng** (control-vector extraction), **Qwen3-0.6B/1.7B** (Apache-2.0).
- Trained **8 persona dials**: poetic, scientific, formal, playful,
  evil, hacker, pilot, politician.
- Swept strengths 0→4 for each; mapped **sweet spots (≈1.0), break points
  (≈2–2.5), and stacking interference**.
- Built the platform (FastAPI + single-page brutalist UI) with three engine
  slots so "plain vs. steered" is a real comparison, not a trick.
- Added in-browser training: anyone can create a new dial from two persona
  sentences (~7 min each on a 4-core CPU).
- Survived and documented a series of real bugs (double `.gguf` extensions,
  negative-dial no-ops, lying UI state, degeneration loops, cross-model
  vector mismatches) — each with a root-cause autopsy in the Atlas.

### What the Atlas taught us (as of now)

| Finding | Detail |
|---|---|
| Sweet spot | each dial ~**1.0**; visible degradation ≥2; nonsense ≥3 |
| Stacking | dial pushes **add** — Σ\|strengths\| ≲ 2 total is the tested-safe zone |
| Style vs. role | style dials (poetic, voice) transfer strongly; role dials barely move a 0.6B — they need bigger models |
| Degeneration | steering shifts raise loop-probability; `repeat_penalty ≈ 1.1` converts hard collapse into mild weirdness |
| Model specificity | control vectors live in ONE model's residual stream; 0.6B vectors do not exist for a 1.7B (the server refuses mismatches) |
| Extraction format | vectors train better when extraction sees the *same chat format* the serving stack uses (system segment included) |

## Architecture (one screen)

```
 repeng (PyTorch, CPU)
   train: "Act as a very {persona}."  ×  512 neutral continuations
   PCA-diff across layers → per-layer direction
   export → vectors/<name>.gguf      (tiny, ~110 KB)
        │
        ▼
 llama.cpp (b11890, CPU) — three engine slots
   main   :8081   whatever dials YOU apply
   plain  :8082   always dial-free          → pane A
   dialed :8083   always your current set   → pane B
        │
        ▼
 FastAPI server (server/app.py)
   engine lifecycle · RAM guard · path normalisation
   loop/degeneration guard · repeat penalty · model-specificity guard
   presets · atlas API · in-app train queue (FIFO worker)
        │
        ▼
 single-page UI (server/static/index.html, brutalist black/white)
   01 model · 02 dials · 03 presets · 04 train · HELP · ATLAS
```

## Try it (after restoring binaries)

**This repo is archived**: heavy binaries and model weights are **not**
included (see [`docs/ARCHIVE_RESTORE.md`](docs/ARCHIVE_RESTORE.md) for exact
sources + one-command revival). The quick path:

```powershell
# 1. follow docs/ARCHIVE_RESTORE.md (llama.cpp b11890 + two GGUFs + PyTorch base)
# 2. then:
powershell -ExecutionPolicy Bypass -File scripts\start_studio.ps1
# 3. open http://localhost:8321 → HELP tab carries the full walkthrough
```

## Project map

```
server/          FastAPI app + brutalist single-page UI
scripts/         train_dial.py (repeng trainer) · demo_dial.py (sweeper)
                 start_studio.ps1 (clean restart) · retrain_weak_dials.ps1
vectors/         8 trained dials (+ attic/ archive of superseded ones)
presets/         saved dial mixes (plain JSON)
atlas/           the lab notebook — notes, sweeps, auto_log.jsonl
docs/            research summary, credits/licences, user guide,
                 ARCHIVE_RESTORE.md
models/          (empty after archive — see restore doc)
TODO.md          living ledger, updated after every stage
```

## Contributing

**Open and welcome.** Ideas that fit the project's spirit:

- **New dials** — the most fun contribution. Train one in-app (box 04) or
  with `scripts/train_dial.py`; contribute the `.gguf` + `.meta.json` +
  a sweep note (strengths tried, where it breaks) into the Atlas.
- **Atlas studies** — systematic sweeps, cross-model retrains, negative-direction
  mapping (the honest unexplored area — our earlier negative tests were
  invalidated by a bug, see `atlas/ml_fundamentals_note.txt`).
- Engine/UI work — streaming responses, more model slots, better guards.
- Docs — plain-language guides, translations.

Ground rules:

- **Local only** — no feature may require cloud/API calls.
- **Honesty in the Atlas** — record failures and break points, not just wins.
- **Licence hygiene** — every dependency/model listed in `docs/credits.md`;
  code is MIT (see `LICENSE`); models Apache-2.0 (Qwen3).

## Safety & ethics

Persona dials (evil/hacker/etc.) are style- and persona-steering experiments
on tiny models (0.6B/1.7B): they change *how* the model talks, not what it is
capable of. No capability uplift is possible at these scales — and the Atlas
keeps an audit trail of everything tried. The tool never ships a model;
users download their own from published, Apache-2.0 sources.

## Licence

Code: MIT. Models: Apache 2.0 (Qwen). Full credits:
[`docs/credits.md`](docs/credits.md).
