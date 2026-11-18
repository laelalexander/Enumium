"""Tiny JSON-file project store. One file per project under STUDIO_DATA (default ./data)."""
import json, os, re, secrets, time
from pathlib import Path

LANGS = {"python": "Python", "nodejs": "Node.js", "vb": "Visual Basic (.NET)", "plc": "PLC logic (IEC 61131-3 ST)"}
EMPTY_WS = {"title": "", "objective": "", "requirements": [], "deliverables": [], "acceptance_criteria": [],
            "assumptions": [], "out_of_scope": [], "risks": [], "approved": False}

def data_dir():
    d = Path(os.environ.get("STUDIO_DATA", Path(__file__).parent / "data")); d.mkdir(parents=True, exist_ok=True); return d

def _path(pid):
    if not re.fullmatch(r"[a-f0-9]{8}", pid): raise KeyError(pid)
    return data_dir() / f"{pid}.json"

def create(name, language):
    if language not in LANGS: raise ValueError(f"language must be one of {list(LANGS)}")
    p = {"id": secrets.token_hex(4), "name": name.strip() or "Untitled project", "language": language, "created": time.time(),
         "updated": time.time(), "chat": [], "workscope": dict(EMPTY_WS), "files": {}, "runs": []}
    save(p); return p

def load(pid):
    try: return json.loads(_path(pid).read_text())
    except FileNotFoundError: raise KeyError(pid)

def save(p):
    p["updated"] = time.time()
    tmp = _path(p["id"]).with_suffix(".tmp"); tmp.write_text(json.dumps(p, indent=1)); tmp.replace(_path(p["id"]))

def delete(pid):
    try: _path(pid).unlink()
    except FileNotFoundError: raise KeyError(pid)

def listing():
    out = []
    for f in sorted(data_dir().glob("*.json"), key=lambda f: -f.stat().st_mtime):
        p = json.loads(f.read_text())
        out.append({k: p[k] for k in ("id", "name", "language", "updated")} |
                   {"approved": p["workscope"]["approved"], "files": len(p["files"]), "runs": len(p["runs"])})
    return out

def safe_filename(name):
    if not re.fullmatch(r"[\w][\w.\-]{0,60}", name) or ".." in name: raise ValueError("bad file name")
    return name
