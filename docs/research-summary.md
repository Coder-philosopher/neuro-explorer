# Research Summary — Model Steering Studio

*Stage 1 output. Written so anyone can read it. Verified 2026-10-26.*

## 1. What already exists (we reuse these)

| Project | What it does | Our role for it | Licence |
|---|---|---|---|
| **llama.cpp** (ggml-org) | Runs small models very fast on CPU (no GPU needed). Ships prebuilt Windows binaries. Supports **control vectors** as a first-class feature: `--control-vector` + `--control-vector-strength` (applied to all/one layer). | **Inference engine** behind everything. Runtime downloaded (`llama-b11890-bin-win-cpu-x64`). | MIT |
| **repeng** (vgel/repeng) | Trains *control vectors* from paired "A vs B" text using representation engineering. Trains in <60s on small models. | **Vector trainer** for our dials. | MIT |
| **Qwen3-0.6B** (Qwen) | Tiny open Apache-2.0 model. Official GGUF repo now ships **Q8_0 only** (~610 MB). Other sizes (0.4B, 1.7B) available for later. | **Base model.** Downloaded: `models/Qwen3-0.6B-Q8_0.gguf`. | Apache 2.0 |
| Hugging Face Hub | Free model/dataset hosting. | Model downloads only. | — |

## 2. What we build (thin layer only)

- **Dial panel web app** (FastAPI + one browser page): chat, strength sliders, side-by-side compare. Talks to a local `llama-server` (OpenAI-compatible API).
- **Atlas**: auto-written experiment log (JSON lines + SQLite index) + searchable viewer page. Stores vector file, layer, strength tested, example outputs, and **failures**.
- **Dial presets** = vector file + settings JSON; save/load equal to copying small files.
- **Built-in code workspace** (later stage): editor + sandboxed script runner.

## 3. How a "dial" actually works, in plain language

A control vector is one long list of numbers (same shape as the model's hidden state), trained from pairs of sentences ("poetic" vs "plain"). While chatting, llama.cpp adds `strength × vector` to the model's inner calculations, nudging it. One vector usually does many things, so we:
1. Train, 2. test at several strengths, 3. note the sweet spot *and* the nonsense point in the Atlas, 4. bundle that as one dial.

## 4. Key design decisions & why

- **Steering method: control vectors, not SAEs/activation editing.** SAE tooling (SAELens, nnsight) needs GPU-grade hardware. Control vectors train in seconds on CPU and are natively supported by llama.cpp. Neuronpedia/Gemma Scope remain reference material for Atlas entry *style*.
- **Quantization: Q8_0, not Q4.** Official Q4 GGUF files for Qwen3-0.6B were removed upstream; Q8_0 (~610 MB) preserves cleaner internal structure — important because steering multiplies small differences.
- **Fits the hardware:** model 0.6 GB + overhead ≈ 1.5 GB RAM peak, CPU-only. Confirmed GPU is Intel HD 520 ⇒ nothing GPU-dependent allowed.

## 5. Risks & honest limits

1. **Training vectors needs PyTorch to load the model (fp16/fp32), not GGUF.** Qwen3-0.6B fp32 ≈ 2.4 GB — fits on this 16 GB machine. If we ever steer a 4B+ model, this step moves to a free Colab notebook.
2. **Strength changes on llama-server may require a restart** (flags are load-time). Verify in stage 4; if restart-only, the UI hides it behind a quick "apply dials" button (~5–10 s).
3. **Small models are volatile:** 0.6B may respond to steering weakly or sloppily. Mitigation: try multiple layers/arrow placements, keep the 1.7B as fallback (~1.7 GB Q8).
4. **Python 3.13 wheels:** torch/transformers support 3.13; if repeng rejects it, pin a working torch version locally — no permission needed, noted in log.
5. **DeepSeek**: smallest current DeepSeek is old/deepseek-coder style. Qwen3 is the primary; DeepSeek becomes an optional second model later.

## 6. What we do NOT build

No retraining/finetuning, no GPU backend, no cloud calls, no SAE feature dashboards (out of hardware budget).
