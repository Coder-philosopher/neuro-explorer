# Credits & Licences

Everything reused by this project, with its licence. Rule: free + open first.

| Project | Version | Role | Licence |
|---|---|---|---|
| llama.cpp | build b11890 (win-cpu-x64) | model inference engine, control-vector support | MIT |
| repeng | 0.2.x (PyPI) | control-vector training | MIT |
| repeng note datasets (`all_truncated_outputs.json`, `code_questions.json`) | main branch | neutral suffix corpus for training | MIT (same repo) |
| Qwen3-0.6B → `models/Qwen3-0.6B-Q8_0.gguf`, `models/qwen3-0.6b/` (PyTorch) | official | base model for steering | Apache 2.0 |
| Qwen3-1.7B → `models/Qwen3-1.7B-Q8_0.gguf` (upgraded main model) | official | base model for steering | Apache 2.0 |
| Python packages: torch (CPU), transformers, gguf, fastapi, uvicorn, httpx, psutil | | plumbing | BSD/MIT/Apache (standard PSF/PyPI licences) |

## Local patches we carry (drivers of vendoring)
- `repeng/extract.py`: `np.float_` → `np.float64` (numpy 2 compatibility, Python 3.13).
  If we re-install repeng this patch must be reapplied — utility script TODO.

## Data corpus usage note
`all_truncated_outputs.json` fragments come from public-domain-ish web text
collected by the repeng author for exactly this purpose. Only used as training
suffix material locally; nothing is sent anywhere.
