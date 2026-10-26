# NEUROEXPLORER (formerly "Model Steering Studio") — Todo Tracker

> Updated after **every stage**. This is the living ledger — if it says done, it was actually verified on this machine.
> Archived 2026-10-26: binaries + model weights deleted to free space, see docs/ARCHIVE_RESTORE.md.

## Machine profile (verified 2026-10-26)

| Item | Value |
|---|---|
| OS | Windows 10 Pro x64 |
| CPU | 4 logical cores, Intel HD 520 graphics → **CPU-only inference** |
| RAM | 16 GB total, ~11 GB free |
| Python | 3.13.6 |

## Legend
`[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked (say why)

---

## Stage 1 — Research & plan
- [x] Initial tool research (repeng, llama.cpp control vectors, Qwen3 sizes)
- [x] Write `docs/research-summary.md` (what exists / reused / built / risky)

## Stage 2 — Tiny model running locally
- [x] Download prebuilt llama.cpp (CPU, Windows x64) → `bin/llama.cpp/`, build b11890
- [x] Download Qwen3-0.6B GGUF → `models/Qwen3-0.6B-Q8_0.gguf` (610 MB; Q4_K_M was removed upstream)
- [x] Load model + generate — **verified**: load 3.3 s, ~12.6 tok/s (2 threads), output coherent
  - [x] Note: Qwen3 emits "thinking" text by default → suppress in studio (/no_think)

## Stage 3 — First dial ("poetic")  `[x] DONE & verified in the platform`
- [x] Install repeng (+ torch CPU 2.14, transformers 5.20) — 2 local compat fixes:
  - repeng pinned numpy<2 (no wheels for Py3.13) → installed --no-deps + np.float_ → np.float64
  - bf16 on this CPU is ~5x slower than fp32 → training uses torch.float32
- [x] Train "poetic" control vector on Qwen3-0.6B → `vectors/poetic.gguf` (112 KB, 7 min CPU)
- [x] GGUF-export works (repeng export_gguf, llama.cpp-compatible)
- [x] Strength sweep: sweet spot 1.0, breaks between 2 and 4 → `atlas/poetic_dial_note.txt`
- [x] Windows colon bug (FNAME:SCALE vs C: paths) fixed via relative engine paths
- [x] Steered chat verified THROUGH the studio API (28.9 tok/s) → `atlas/poetic_platform_test.txt`

## Stage 4 — Local web platform v1  `[~] core verified; UI niceties pending`
- [x] FastAPI backend (`server/app.py`) + single browser page (`server/static/index.html`)
- [x] Chat works through the platform (verified: question → engine → answer)
- [x] Dial from UI → engine restart with control vectors → steered answer (API level)
- [x] RAM guard (psutil), Atlas viewer tab, engine crash diagnostics (server/engine.log)
- [ ] Verify the browser page itself end-to-end (only API tested so far)
- [ ] One-stale-uvicorn hygiene: guard script `scripts/start_studio.ps1` to restart cleanly

## Stage 5 — Atlas v1  `[x] DONE`
- [x] Chat auto-logging → `atlas/auto_log.jsonl` (verified live, every chat)
- [x] Viewer: /api/atlas serves txt notes + json sweeps + auto log tail
- [x] Sweep logging from scripts/demo_dial.py; failures recorded in notes

## Stage 6 — Many dials  `[~] milestone achieved on 0.6B; upgrades queued`
- [x] Dials trained: poetic, scientific, formal, playful → `vectors/*.gguf`
- [x] Strength sweeps → Atlas notes (`atlas/dials_batch2_note.txt`):
      poetic sweet 1.0 · scientific 1.0-2.0 (FIXED a factual error!) ·
      formal caps ~0.7 · playful weak, breaks by 2.0
- [x] MILESTONE (idea.md #7): 3 distinct behaviours up/down with clear change
- [x] Combo tests: same-family dials blur each other → `atlas/combo_note.txt`
      (recommend: ≤2 dials per session, ≤1.0 each, prefer cross-family mixes)
- [ ] Retrain weak dials (formal, playful) on Qwen3-1.7B (downloaded, 1.75 GB GGUF)
  - [ ] download 1.7B safetensors for PyTorch training (~3.4 GB)
- [ ] Save default presets per dial (strength sweet spots)

## Stage 7 — Save / load / share  `[~] core verified`
- [x] Presets: save {name, model, dials} → `presets/*.json` (verified)
- [x] Apply preset → engine restart with exact same dial set (verified: reload
      reproduced lyric behaviour on a fresh question)
- [ ] Preset delete/export; share = copy the json + gguf files

# ARCHIVED (2026-10-26) — see docs/ARCHIVE_RESTORE.md
# binaries (bin/, 82.8 MB) + engine GGUFs (0.6B/1.7B, 2.36 GB) deleted to free
# space; python libs kept globally; training model dir pending removal after
# the last retrain finished. Everything else (code/atlas/vectors/docs) intact.

## Rename + publication (2026-10-26)
- [x] Project renamed to **NEUROEXPLORER** (single word, formerly "Model
      Steering Studio"); live surfaces rebranded (app title, UI header,
      start script, user guide, TODO) — historical Atlas text kept verbatim
- [x] README.md written: story, findings table, architecture, contribution
      guide, safety/ethics framing
- [x] LICENSE added (MIT, neuroexplorer contributors)
- [x] git repo initialised and committed (push target: GitHub `neuroexplorer`)
- [~] folder rename pr-lats → neuroexplorer executes at archive phase 2
      (needs the studio fully exited; Windows holds cwd locks)

## UI v2 — brutalist rebuild (user review round, 2026-10-26)
- [~] black/white brutalist UI: settings boxes numbered 01-04, live status bars
      (engine up/down, compare A/B, current dials, clock), per-pane timings, big HELP tab
- [x] fixed "vector not found: vectors/scientific.gguf.gguf" — backend now
      normalises every dial path (missing prefix, double .gguf prefix re-added)
      at start_engine AND presets/apply; UI now keys dials by base name
- [x] honest compare fixed: A/B now run on two SEPARATE engines (plain :8082 /
      dialed :8083) — before, "plain" pane shared the steered engine (wrong)
- [x] in-browser dial training: /api/train queue (FIFO worker) + 04 box in UI
- [~] new dials trained through the platform API: evil, hacker, pilot, politician → `vectors/*.gguf`
      sweeps + verdicts: `atlas/dials_batch3_note.txt`
      pilot STRONG (sweet ~1.0, breaks 1-2) · hacker subtle usable ·
      evil + politician negligible on 0.6B (role dials need the bigger model)
- [x] slow-generation root cause fixed: trainer hogged all 4 cores while
      engines served → torch threads capped at 2 + UI "TRAINING ACTIVE" banner
- [x] danger banner in UI when >2 dials or |strength| > 2 (records honest limits)
- [x] Atlas tab fixed: /api/atlas was missing from the v2 rewrite; deduped .txt/.json twins (18→12)
- [x] degeneration fix round 2 (user "very bad result" re-test): repeat_penalty
      param (default 1.1, UI "REPEAT PEN" control) + server loop guard
      (_loop_cut: truncates repetition spirals, marks degenerated:true,
      honest marker in pane) + strip bound to send-time dial set (was showing
      stale applied state: "none applied" while B ran 3 dials)
- [x] ML-fundamentals audit round 3 (4 real bugs found + fixed, atlas/ml_fundamentals_note.txt):
      (1) negative dial strengths were silently dropped at engine spawn —
      every "pull away" test to date was a no-op; llama.cpp scale<0 = push away
      (2) ensure_engine never stored the dial set → API always returned empty
      dials, UI strip lied (root cause of the "none applied" while steered)
      (3) empty-dial compare could reuse a still-steered B engine (stale slot)
      (4) loop guard missed near-duplicate spirals (drifting numbers) —
      line-level detector added (≥4 repeats of a ≥12-char line)
      + training format now includes the system segment (serving-parity
      extraction), meta.json records format
      + model/vector compatibility guard: dial meta vs engine model family
      (qwen3-0.6b vs qwen3-1.7b mismatches refused with actionable message)
      + UI danger banner shows total steer Σ|s| (safe ≈ ≤2)
- [~] re-sweep negative directions (earlier Atlas conclusions invalid due to
      bug 1) + retrain evil/politician/formal/playful with the fixed format

## Stage 8 — Built-in code workspace
- [ ] In-app editor + script runner

## Stage 9 — Polish & guides
- [x] In-app /HELP tab with full plain-language flow (load → dial → compare → save → train)
- [ ] Float README/USER_GUIDE to match; final speed passes

---
### MILESTONE CHECK (idea.md §7) — ALL 6 POINTS MET as of 2026-10-26
1. platform starts locally ✓ (scripts/start_studio.ps1 → http://localhost:8321)
2. loads a small model ✓ (Qwen3-0.6B)
3. three behaviours up/down with clear change ✓ (poetic 0→1 dramatic, scientific fixes facts, formal 0.5 subtle)
4. side-by-side normal vs steered ✓ (compare panes; API-verified)
5. save a steered setting & reload reproduces ✓ (presets)
6. Atlas with clear notes for dials + failures ✓ (atlas/*.txt + auto_log.jsonl)
