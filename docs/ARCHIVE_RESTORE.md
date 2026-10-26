# ARCHIVE & RESTORE — Model Steering Studio

**Archived on 2026-10-26** to free disk space. The studio is *not runnable*
until restored — but nothing that explains the work was lost.

## What was kept (untouched)
- **All code**: `server/` (FastAPI app + UI), `scripts/` (trainer, sweep tool,
  start script, retrain script)
- **All outputs**: `atlas/` (notes, sweeps, verdicts, auto_log.jsonl),
  `vectors/` (+ `attic/`, all 8 trained dials + archived v1 dials),
  `presets/`, `docs/`, `TODO.md`
- **Python environment (global, per user instruction — NOT deleted)**:
  torch, transformers, repeng, fastapi, uvicorn, httpx, psutil installed in
  the global site-packages of Python 3.13.
  - repeng note: installed `--no-deps` (numpy<2 pin); local patch applied in
    site-packages/repeng/extract.py: `np.float_` → `np.float64`.
    Re-apply only if repeng is ever reinstalled.

## What was deleted (re-downloadable artifacts only)

| Item | Size | Where it came from |
|---|---|---|
| `bin/llama.cpp/` (prebuilt runtime, build **b11890**) + `bin/llama-cpp-win-cpu-x64.zip` | 82.8 MB | llama.cpp GitHub releases → asset `llama-b11890-bin-win-cpu-x64.zip` (ggml-org/llama.cpp), MIT |
| `models/Qwen3-0.6B-Q8_0.gguf` | 609.8 MB | official Qwen GGUF repo on Hugging Face (`Qwen/Qwen3-0.6B-GGUF`, Q8_0 only file) — Apache 2.0 |
| `models/Qwen3-1.7B-Q8_0.gguf` | 1749.4 MB | `Qwen/Qwen3-1.7B-GGUF` Q8_0 — Apache 2.0 |
| `models/qwen3-0.6b/` (PyTorch snapshot, bf16 safetensors 1.45 GB; trainer casts to fp32 in RAM) | 1448.8 MB | `huggingface.co/Qwen/Qwen3-0.6B` snapshot |

Phase 2 (after the final retrain of `evil` + `politician` finished writing):
`models/qwen3-0.6b/` was also deleted and the studio (uvicorn) shut down, so
**everything inside the project folder after archive = code + outputs only**
(~2 MB total).

## How to revive the studio (exact steps)

1. **llama.cpp runtime (must be build b11890 — control-vector behaviour
   verified against this exact build):**
   - Download the release asset `llama-b11890-bin-win-cpu-x64.zip` from the
     ggml-org/llama.cpp releases page on GitHub.
   - Unzip so that `bin/llama.cpp/llama-server.exe` exists
     (folder name in archive: `llama.cpp`).
2. **Models:**
   ```powershell
   # engine GGUFs (discard doubters' Q4s — Q8_0 chosen deliberately: steering
   # multiplies small internal differences, see docs/research-summary.md)
   huggingface-cli download Qwen/Qwen3-0.6B-GGUF --include "Q8_0/*" --local-dir models\q60
   Copy-Item models\q60\Q8_0\*.gguf models\Qwen3-0.6B-Q8_0.gguf
   Remove-Item -Recurse models\q60
   huggingface-cli download Qwen/Qwen3-1.7B-GGUF --include "Q8_0/*" --local-dir models\q17
   Copy-Item models\q17\Q8_0\*.gguf models\Qwen3-1.7B-Q8_0.gguf
   Remove-Item -Recurse models\q17
   # PyTorch base for dial training (any future new dials)
   huggingface-cli download Qwen/Qwen3-0.6B --local-dir models\qwen3-0.6b
   ```
3. **Python libs** (global env kept — skip if intact). If a clean machine:
   `pip install torch transformers fastapi uvicorn httpx psutil`, then
   `pip install repeng --no-deps`, then the `np.float64` patch in
   site-packages/repeng/extract.py.
4. **Start:** `powershell -ExecutionPolicy Bypass -File scripts\start_studio.ps1`
   → UI at http://localhost:8321 . The three engine slots (main/plain/dialed
   on ports 8081/82/83) spawn on demand.

## Gotchas (from the experiment record)
- llama.cpp splits `FNAME:SCALE` on `:` → engine dial paths are passed as
  paths-relative-to-bin (see `rel_no_colon()`); do not "fix" back to absolute.
- `scripts/start_studio.ps1` kills stale uvicorns (multiple can silently share
  port 8321 via SO_REUSEADDR).
- Trainer is thread-capped at 2 (see `train_dial.py`) — do not re-widen on a
  4-core machine while engines serve.
- Negative dial strengths are real (llama.cpp negative scale = push away);
  >2 single-dial or Σ|s|>2 multi-dial = documented break zones (ATLAS).
- Control vectors are model-specific; the server refuses
  0.6B-vectors-on-1.7B mismatches (by design, see
  `atlas/ml_fundamentals_note.txt`).
