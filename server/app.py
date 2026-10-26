"""
NEUROEXPLORER (formerly "Model Steering Studio") — local web platform (v2)

http://localhost:8321 · everything local · nothing leaves this machine.

Engine slots (llama-server processes):
  main    :8081 — the chat engine, whatever dials you Apply
  plain   :8082 — always without dials (side A of compare)
  dialed  :8083 — always with your current dials (side B of compare)

Dial files are normalised everywhere (fixes "scientific.gguf.gguf" style bugs).
New dials can be trained straight from the UI (/api/train, FIFO queue).
"""

import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil
import urllib.request

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "llama.cpp"
MODELS = ROOT / "models"
VECTORS = ROOT / "vectors"
ATLAS = ROOT / "atlas"
PRESETS_DIR = ROOT / "presets"
STATIC = ROOT / "server" / "static"
MB = 1024 * 1024

PORTS = {"main": 8081, "plain": 8082, "dialed": 8083}
RAM_BUDGET_GB = 8.5

app = FastAPI(title="NEUROEXPLORER")

# slot state ---------------------------------------------------------------
E = {
    name: {"proc": None, "model": None, "dials": []}
    for name in PORTS
}

TRAIN_STATUS: dict[str, dict] = {}
_TRAIN_LOCK = threading.Lock()
_TRAIN_QUEUE: list[dict] = []
_sys_python = sys.executable


def engine_alive(slot: str) -> bool:
    st = E[slot]
    if st["proc"] is not None and st["proc"].poll() is not None:
        return False
    try:
        with urllib.request.urlopen(f"{_url(slot)}/health", timeout=2) as r:
            return r.status == 200 and json.loads(r.read())["status"] == "ok"
    except Exception:
        return False


def _url(slot: str) -> str:
    return f"http://127.0.0.1:{PORTS[slot]}"


def wait_health(slot: str, seconds: int = 150) -> bool:
    for _ in range(seconds):
        if engine_alive(slot):
            return True
        time.sleep(1)
    return False


def normalize_dial_file(file: str) -> str:
    """Fixes every way a dial path can be wrong: missing prefix, missing or
    doubled .gguf suffix, backslashes."""
    f = str(file).strip().replace("\\", "/")
    if f.startswith("/"):
        f = f[1:]
    if "/" not in f:
        f = "vectors/" + f
    while f.endswith(".gguf.gguf"):
        f = f[:-5]
    if not f.endswith(".gguf"):
        f += ".gguf"
    return f


def dial_model_family(file: str) -> str:
    """Which model a dial was trained on, from its meta.json (e.g. 'qwen3-0.6b')."""
    mp = VECTORS / f"{Path(str(file)).stem}.meta.json"
    try:
        return str(json.loads(mp.read_text(encoding="utf-8")).get("model", "") or "")
    except Exception:
        return ""


def loaded_model_family(model_rel: str) -> str:
    """'models/Qwen3-0.6B-Q8_0.gguf' -> 'Qwen3-0.6B' style family id."""
    stem = Path(model_rel).stem
    for size in ("0.6b", "1.7b", "0.5b", "1.5b", "3b", "7b", "4b", "8b"):
        i = stem.lower().find(size)
        if i != -1:
            return stem[i - len("qwen3-") if i >= len("qwen3-") else 0: i + len(size)]
    return stem


def rel_no_colon(p: Path, base: Path) -> str:
    # llama.cpp splits FNAME:SCALE on ":" — Windows drive letters break it.
    return os.path.relpath(p, base).replace("\\", "/")


def stop_engine(slot: str):
    st = E[slot]
    if st["proc"] is not None and st["proc"].poll() is None:
        st["proc"].terminate()
        try:
            st["proc"].wait(timeout=10)
        except subprocess.TimeoutExpired:
            st["proc"].kill()
    st["proc"] = None


def stop_all():
    for slot in PORTS:
        stop_engine(slot)


def spawn_engine(slot: str, model_rel: str, dials: list[dict]):
    stop_engine(slot)
    model_path = ROOT / model_rel
    if not model_path.exists():
        return False, f"model not found: {model_rel}"

    est = model_path.stat().st_size / (1024 ** 3)
    loaded = [ROOT / s["model"] for s in E.values() if s["model"] and s["proc"] and s["proc"].poll() is None]
    projected = est * 1.6 + sum(p.stat().st_size / (1024 ** 3) for p in loaded)
    avail_gb = psutil.virtual_memory().available / (1024 ** 3)
    if projected > avail_gb:
        return False, (
            f"RAM guard: this load would need ~{projected:.1f} GB but only "
            f"{avail_gb:.1f} GB free. Press Stop all and retry."
        )

    vec_args: list[str] = []
    for d in dials:
        f = normalize_dial_file(d["file"])
        if not (ROOT / f).exists():
            return False, f"vector not found: {f}"

        # model/vector compatibility: control vectors live in one model's
        # residual stream — a 0.6B vector does not exist in a 1.7B model.
        fam_d = dial_model_family(f)
        fam_m = loaded_model_family(model_rel)
        if fam_d and fam_m and fam_d.lower() != fam_m.lower():
            return False, (
                f"dial '{Path(f).stem}' was trained on {fam_d}, but the engine "
                f"model is {fam_m}. Control vectors are model-specific — "
                f"retrain this dial on {fam_m} (04 box) or switch models."
            )

        strength = float(d.get("strength", 0))
        if strength != 0:
            # llama.cpp multiplies the direction by the scale, so a NEGATIVE
            # scale pushes away from the behaviour. (Earlier versions dropped
            # negatives here silently — that bug made 'opposite' dials no-ops.)
            vec_args += ["--control-vector-scaled",
                         f"{rel_no_colon(ROOT / f, BIN)}:{strength}"]

    cmd = [
        str(BIN / "llama-server.exe"),
        "-m", str(model_path),
        "-c", "4096", "-t", "4",
        "--port", str(PORTS[slot]),
        "--host", "127.0.0.1",
        *vec_args,
    ]
    log = open(ROOT / "server" / f"engine_{slot}.log", "w", encoding="utf-8", errors="replace")
    E[slot]["proc"] = subprocess.Popen(
        cmd, cwd=str(BIN), stdout=log, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    E[slot]["model"] = model_rel
    E[slot]["dials"] = [
        {"name": Path(normalize_dial_file(d["file"])).stem,
         "file": normalize_dial_file(d["file"]),
         "strength": float(d.get("strength", 0))}
        for d in dials
    ]
    ok = wait_health(slot)
    if not ok:
        stop_engine(slot)
        log_tail = ""
        lp = ROOT / "server" / f"engine_{slot}.log"
        if lp.exists():
            log_tail = lp.read_text(errors="replace")[-500:]
        return False, f"engine ({slot}) failed to start within 150 s\n{log_tail}"
    return True, "up"


def ensure_engine(slot: str, model_rel: str, dials: list[dict]) -> tuple[bool, str]:
    st = E[slot]
    key = sorted((normalize_dial_file(d["file"]), round(float(d.get("strength", 0)), 2)) for d in dials)
    cur = sorted((normalize_dial_file(d["file"]), round(float(d.get("strength", 0)), 2)) for d in st["dials"])
    if engine_alive(slot) and st["model"] == model_rel and key == cur:
        return True, "already up"
    return spawn_engine(slot, model_rel, dials)


# ---------------------------------------------------------------- schemas

class StartReq(BaseModel):
    model: str
    dials: list[dict] = []


class ChatReq(BaseModel):
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int = 512
    repeat_penalty: float = 1.1   # dialed models love degeneration loops; 1.1 kills most


class CompareReq(ChatReq):
    model: str | None = None
    dials: list[dict] = []


class PresetReq(BaseModel):
    name: str
    model: str | None = None
    dials: list[dict] = []


class TrainReq(BaseModel):
    name: str
    pos: str
    neg: str
    template: str | None = None


# ---------------------------------------------------------------- helpers

def _loop_cut(text: str) -> tuple[str, bool]:
    """Degeneration guard. Two detectors:
    1. exact-chunk: a 40-120 char chunk appearing 3+ times (the literal spiral)
    2. line-level: any significant line repeating 4+ times — catches loops
       with drifting content like '**Final Answer:** \\boxed{12} {13} {14}.'
    Truncates at the second/third occurrence and says so."""
    note = "\n[repetition loop detected — truncated. Lower dial strength "\
           "or raise the repeat penalty.]"
    # line-level pass (catches near-duplicates with drifting numbers)
    lines = text.splitlines()
    counts: dict[str, int] = {}
    for ln in lines:
        key = ln.strip()
        if len(key) >= 12:
            counts[key] = counts.get(key, 0) + 1
    bad = max(counts, key=counts.get, default="")
    if bad and counts[bad] >= 4:
        seen, pos = 0, 0
        while True:
            i = text.find(bad, pos)
            if i == -1:
                break
            seen += 1
            pos = i + len(bad)
            if seen == 3:  # keep the first two instances for readability
                return text[:i].rstrip() + note, True
    # exact-chunk pass
    for L in (120, 80, 60, 40):
        end = max(0, len(text) - L)
        for i in range(0, end):
            chunk = text[i:i + L]
            if len(chunk.strip()) < 20:  # whitespace-only windows mean nothing
                continue
            j = text.find(chunk, i + 1)
            if j != -1 and text.count(chunk) >= 3:
                return text[:j].rstrip() + note, True
    return text, False


def _post_chat(slot: str, req: dict):
    r = httpx.post(f"{_url(slot)}/v1/chat/completions", json=req, timeout=900)
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    timings = data.get("timings", {}) or {}
    return {
        "text": text,
        "tok_s": round(timings.get("predicted_per_second") or 0, 1),
        "gen_ms": timings.get("predicted_ms"),
        "prompt_ms": timings.get("prompt_ms"),
    }


def log_chat(req: ChatReq, text: str, wall: float, src: str):
    try:
        ATLAS.mkdir(exist_ok=True)
        question = next((m.get("content", "") for m in req.messages if m.get("role") == "user"), "")
        entry = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": src,
            "question": question[:400],
            "model": E["main"]["model"],
            "dials": E["main"]["dials"],
            "wall_seconds": wall,
            "answer": text[:1500],
        }
        with open(ATLAS / "auto_log.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _train_worker():
    while True:
        item = None
        with _TRAIN_LOCK:
            if _TRAIN_QUEUE:
                item = _TRAIN_QUEUE.pop(0)
        if item is None:
            time.sleep(1)
            continue
        name = item["name"]
        TRAIN_STATUS[name] = {"state": "running", "started": time.strftime("%H:%M:%S")}
        log_path = ROOT / "scripts" / f"train_{name}.log"
        with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
            p = subprocess.Popen(
                [_sys_python, "scripts/train_dial.py",
                 "--name", name,
                 "--template", item["template"],
                 "--pos", item["pos"], "--neg", item["neg"]],
                cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            p.wait()
        TRAIN_STATUS[name]["state"] = "done" if p.returncode == 0 else "failed"


@app.on_event("startup")
def start_worker():
    threading.Thread(target=_train_worker, daemon=True).start()


# ---------------------------------------------------------------- api

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/models")
def models():
    return {
        "models": sorted(
            [
                {"name": p.name, "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                 "mb": round(p.stat().st_size / MB)}
                for p in MODELS.glob("*.gguf")
            ], key=lambda x: x["name"],
        )
    }


@app.get("/api/vectors")
def vectors():
    out = []
    for p in sorted(VECTORS.glob("*.gguf")):
        meta = {}
        mp = VECTORS / f"{p.stem}.meta.json"
        if mp.exists():
            meta = json.loads(mp.read_text(encoding="utf-8"))
        out.append({
            "name": p.stem,
            "file": f"vectors/{p.name}",
            "kb": max(1, round(p.stat().st_size / 1024)),
            "meta": meta,
        })
    return {"vectors": out}


@app.get("/api/status")
def status():
    return {
        "slots": {
            slot: {
                "alive": engine_alive(slot),
                "model": E[slot]["model"],
                "dials": E[slot]["dials"],
            } for slot in PORTS
        },
        "trainings": [
            {"name": name, "state": v.get("state"), "tail": _train_tail(name)}
            for name, v in TRAIN_STATUS.items()
        ],
    }


def _train_tail(name: str) -> str:
    lp = ROOT / "scripts" / f"train_{name}.log"
    if not lp.exists():
        return ""
    try:
        return lp.read_text(encoding="utf-8", errors="replace")[-300:]
    except Exception:
        return ""


@app.post("/api/start")
def start(req: StartReq):
    try:
        ok, msg = ensure_engine("main", req.model, req.dials)
    except Exception:
        import traceback
        return {"ok": False, "msg": "EXCEPTION\n" + traceback.format_exc()}
    E["main"]["dials"] = [
        {"name": Path(normalize_dial_file(d["file"])).stem,
         "file": normalize_dial_file(d["file"]),
         "strength": float(d.get("strength", 0))}
        for d in req.dials
    ]
    return {"ok": ok, "msg": msg, "dials": E["main"]["dials"]}


@app.post("/api/chat")
def chat(req: ChatReq):
    if not engine_alive("main"):
        return JSONResponse({"error": "engine not running — press LOAD first"}, status_code=503)
    t0 = time.time()
    payload = {
        "model": "default",
        "messages": req.messages,
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "repeat_penalty": req.repeat_penalty,
        "stream": False,
    }
    try:
        out = _post_chat("main", payload)
        out["text"], out["degenerated"] = _loop_cut(out["text"])
        wall = round(time.time() - t0, 1)
        log_chat(req, out["text"], wall, "chat")
        out.update({"wall_seconds": wall, "engine_dials": E["main"]["dials"]})
        return out
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/compare")
def compare(req: CompareReq):
    model = req.model or E["main"]["model"]
    if not model:
        return JSONResponse({"error": "no model known yet — load one in SETTINGS first"}, 400)
    dials = req.dials
    t0 = time.time()
    r1 = ensure_engine("plain", model, [])
    # ALWAYS enforce the requested dial set on the dialed slot — even when
    # empty — so B can never run secretly steered from a previous compare.
    r2 = ensure_engine("dialed", model, dials)
    if not r1[0] or not r2[0]:
        return {"error": f"engine warmup failed — plain:{r1[1]} dialed:{r2[1]}"}
    payload = {
        "model": "default",
        "messages": req.messages,
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
        "repeat_penalty": req.repeat_penalty,
        "stream": False,
    }
    with ThreadPoolExecutor(2) as ex:
        a = ex.submit(_post_chat, "plain", payload)
        b = ex.submit(_post_chat, "dialed", payload)
        try:
            ra, rb = a.result(), b.result()
        except Exception as e:
            return {"error": str(e)}
    ra["text"], ra["degenerated"] = _loop_cut(ra["text"])
    rb["text"], rb["degenerated"] = _loop_cut(rb["text"])
    wall = round(time.time() - t0, 1)
    log_chat(req, rb["text"], wall, "compare")
    return {"plain": ra, "dialed": rb, "wall_seconds": wall,
            "dials": E["dialed"]["dials"], "model": model}


@app.post("/api/stop")
def stop():
    stop_all()
    return {"ok": True}


# ---------------------------------------------------------------- atlas

@app.get("/api/atlas")
def atlas():
    entries = []
    txt_names: set[str] = set()
    if ATLAS.exists():
        for p in ATLAS.glob("*.txt"):
            txt_names.add(p.stem)
    if ATLAS.exists():
        for p in sorted(ATLAS.glob("*"), key=lambda x: x.name):
            if p.suffix == ".txt":
                text = p.read_text(encoding="utf-8", errors="replace")
            elif p.suffix == ".json":
                if p.stem in txt_names:  # prefer the .txt twin of the same sweep
                    continue
                try:
                    d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                    lines = [f"date: {d.get('date','')}", f"type: {d.get('type','')}"]
                    if "prompt" in d:
                        lines.append("\nasked: " + str(d["prompt"]))
                    for s, v in sorted((d.get("strengths") or {}).items(), key=lambda kv: float(kv[0])):
                        first = (v.get("output") or "")[:400]
                        lines.append(f"\n== strength {s} ==\n{first}")
                    text = "\n".join(lines)
                except Exception:
                    text = "(unreadable entry)"
            else:
                continue
            entries.append({"title": p.stem.replace("_", " "), "date": "", "body": text[:4000]})
    logf = ATLAS / "auto_log.jsonl"
    if logf.exists():
        chats = []
        for line in logf.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            dials_txt = ", ".join(
                f"{d.get('name')}={d.get('strength')}" for d in (d.get("dials") or [])
            ) or "none"
            chats.append(
                f"[{d.get('date')}] ({d.get('type')}) dials: {dials_txt}\n"
                f"Q: {d.get('question', '')}\nA: {d.get('answer', '')[:500]}"
            )
        if chats:
            entries.append({"title": "auto log — latest 25", "date": "",
                            "body": "\n\n".join(reversed(chats[-25:]))[:4000]})
    return {"entries": entries}


# ---------------------------------------------------------------- presets

@app.get("/api/presets")
def presets_list():
    out = []
    if PRESETS_DIR.exists():
        for p in sorted(PRESETS_DIR.glob("*.json")):
            out.append({"name": p.stem, **json.loads(p.read_text(encoding="utf-8"))})
    return {"presets": out}


@app.post("/api/presets/save")
def presets_save(req: PresetReq):
    PRESETS_DIR.mkdir(exist_ok=True)
    safe = "".join(c for c in req.name if c.isalnum() or c in "-_ ") or "preset"
    data = {"model": req.model, "dials": req.dials, "saved": time.strftime("%Y-%m-%d %H:%M")}
    (PRESETS_DIR / f"{safe}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {"ok": True, "name": safe, **data}


@app.post("/api/presets/apply")
def presets_apply(req: PresetReq):
    path = PRESETS_DIR / f"{req.name}.json"
    if not path.exists():
        return {"ok": False, "msg": f"preset not found: {req.name}"}
    d = json.loads(path.read_text(encoding="utf-8"))
    dials = [
        {"name": Path(normalize_dial_file(x["file"])).stem,
         "file": normalize_dial_file(x["file"]),
         "strength": float(x.get("strength", 0))}
        for x in (d.get("dials") or [])
    ]
    ok, msg = ensure_engine("main", d["model"], dials)
    E["main"]["dials"] = dials
    return {"ok": ok, "msg": msg, "model": d["model"], "dials": E["main"]["dials"]}


# ---------------------------------------------------------------- training

@app.post("/api/train")
def api_train(req: TrainReq):
    name = "".join(c for c in req.name if c.isalnum() or c in "-_").lower()
    if not name:
        return {"ok": False, "msg": "bad dial name"}
    if (VECTORS / f"{name}.gguf").exists():
        return {"ok": False, "msg": f"dial '{name}' is already trained"}
    with _TRAIN_LOCK:
        if name in TRAIN_STATUS and TRAIN_STATUS[name]["state"] in ("queued", "running"):
            return {"ok": False, "msg": f"'{name}' is already queued/running"}
        _TRAIN_QUEUE.append({
            "name": name,
            "pos": req.pos,
            "neg": req.neg,
            "template": req.template or "Act as if you're a very {persona}.",
        })
        TRAIN_STATUS[name] = {"state": "queued"}
    return {"ok": True, "name": name, "msg": f"queued '{name}' — ~7 min per dial on this CPU; watch the panel."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8321, log_level="warning")
