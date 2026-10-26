# NEUROEXPLORER — user guide

Local mixing desk for a model's personality. Nothing leaves your computer.

## The flow

1. **Start**: `powershell -ExecutionPolicy Bypass -File scripts\start_studio.ps1`
   then open **http://localhost:8321**.
2. **Load a model** (box 01). Engine status bar turns UP after ~5–10 s.
3. **Dial a behaviour** (box 02): pick a dial, move its slider away from 0
   (-4…+4; 0 = untouched), press APPLY DIALS. Recommended everyday range:
   0.5–1.5. Above ~2 expect nonsense (that's the danger zone — learn each
   dial's break point from the ATLAS tab).
4. **Compare honestly** (SEND →): one question is answered by two engines —
   A = no dials (the plain model), B = your dials applied. Per-anser speed
   shown under each pane.
5. **Save the mix** (box 03): preset = model + dial strengths as a small json
   in `presets/`. APPLY restores identical behaviour later.
6. **Make a new dial** (box 04): give a name + two opposite personas,
   queue it. Training is local and free (~7 min for the small model).
   New dials appear in box 02 automatically.
7. **Read the ATLAS**: what each dial does, the sweet spots, where each
   breaks, and everything you generated (auto-log).

## The dials folder map
- `vectors/*.gguf` — trained dial files (small control-vector files)
- `presets/*.json` — saved dial mixes (share = copy the two file types)
- `atlas/` — notes, sweeps and the auto-log (`atlas/auto_log.jsonl`)
- `scripts/train_dial.py` — the trainer (the UI calls it)
- `server/engine_*.log` — engine crash details, if ever needed

## Safety note
The Studios' dials steer *style and persona* for study. They do not grant
capabilities the base model lacks (0.6B/1.7B produce no harmful capability
change). Keep uses honest; the ATLAS records what was tried.
