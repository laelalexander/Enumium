"""AI workflow: natural-language (or image) request -> validated CAD part.

Stages
  1. SPEC      LLM turns the request into a structured spec (JSON).
  2. GENERATE  LLM writes parametric CadQuery code from the spec.
  3. EXECUTE   Code runs in a subprocess (runner.py), is validated, and
               exported to STEP + STL.
  4. REPAIR    On failure the errors go back to the LLM; repeat up to N times.
  5. PUBLISH   Writes part.py, STEP, STL, report.json into out/<name>/.

Usage
  python pipeline.py "M6 flanged bushing, 12 mm OD, 20 mm long"
  python pipeline.py --image sketch.png "bracket matching this sketch"
  python pipeline.py --code examples/bracket.py --spec examples/bracket.json  # no LLM
"""
import argparse, base64, json, mimetypes, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
MODEL = "claude-sonnet-5-5"

SPEC_SYSTEM = """You are a mechanical design engineer. Convert the request into a JSON spec with keys:
name (snake_case), summary, units ("mm"), bbox_mm ([x,y,z] overall size, or null if unknown),
parameters (object of named numeric dimensions), features (list of strings),
min_feature_mm (number, default 0.8), process ("fdm" | "cnc" | "sla").
Choose sensible standard dimensions (ISO clearance holes, etc.) for anything unspecified.
Reply with JSON only."""

CODE_SYSTEM = """You write CadQuery (Python, v2) code for one part.
Rules:
- `cq` is already imported; do not import anything else.
- Declare every dimension as a named variable at the top, in mm, matching the spec parameters.
- The final single solid must be assigned to `result` (a cq.Workplane).
- Build one connected solid; union parts, use fillets/chamfers only where safe.
- No file I/O, no network, no show_object. Reply with one ```python block only."""

def _text(msg):
    return "".join(b.text for b in msg.content if b.type == "text")

def _client():
    import anthropic
    return anthropic.Anthropic()

def _image_block(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.standard_b64encode(Path(path).read_bytes()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": mime, "data": data}}

def make_spec(client, request, image=None):
    content = ([_image_block(image)] if image else []) + [{"type": "text", "text": request}]
    msg = client.messages.create(model=MODEL, max_tokens=1500, system=SPEC_SYSTEM,
                                 messages=[{"role": "user", "content": content}])
    raw = _text(msg)
    return json.loads(re.search(r"\{.*\}", raw, re.S).group(0))

def extract_code(text):
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()

def generate(client, spec, history):
    msg = client.messages.create(model=MODEL, max_tokens=4000, system=CODE_SYSTEM,
                                 messages=[{"role": "user", "content": "Spec:\n" + json.dumps(spec, indent=2)}] + history)
    return _text(msg)

def execute(code, spec, outdir, timeout=120):
    with tempfile.TemporaryDirectory() as scratch:
        cp, sp = Path(scratch) / "code.py", Path(scratch) / "spec.json"
        cp.write_text(code, encoding="utf-8"); sp.write_text(json.dumps(spec), encoding="utf-8")
        try:
            p = subprocess.run([sys.executable, "-I", str(HERE / "runner.py"), str(cp), str(outdir), str(sp)],
                               capture_output=True, text=True, timeout=timeout, cwd=scratch)
        except subprocess.TimeoutExpired:
            return {"ok": False, "errors": [f"Timed out after {timeout}s (too complex or infinite loop)."], "warnings": [], "metrics": {}, "files": {}}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "errors": ["Runner crashed: " + p.stderr[-500:]], "warnings": [], "metrics": {}, "files": {}}

def run(spec, code=None, client=None, max_iters=4, out_root=HERE / "out"):
    outdir = Path(out_root) / spec["name"]
    outdir.mkdir(parents=True, exist_ok=True)
    history, attempts, report = [], [], {}
    for i in range(1, max_iters + 1):
        if code is None or i > 1:
            reply = generate(client, spec, history)
            code = extract_code(reply)
            history = [{"role": "assistant", "content": reply}]
        report = execute(code, spec, outdir)
        attempts.append({"iteration": i, "ok": report["ok"], "errors": report["errors"]})
        print(f"[iter {i}] {'OK' if report['ok'] else 'FAIL'} {report['errors'] or ''}", file=sys.stderr)
        if report["ok"] or client is None:
            break
        feedback = "The code failed validation:\n- " + "\n- ".join(report["errors"]) + \
                   "\nFix it and return the full corrected code."
        history.append({"role": "user", "content": feedback})
    (outdir / "part.py").write_text(code, encoding="utf-8")
    final = {"spec": spec, "attempts": attempts, **report}
    (outdir / "report.json").write_text(json.dumps(final, indent=2), encoding="utf-8")
    return final

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("request", nargs="?", help="what to design")
    ap.add_argument("--image", help="reference sketch/photo")
    ap.add_argument("--code", help="existing CadQuery file (skips LLM generation)")
    ap.add_argument("--spec", help="existing spec JSON (skips spec stage)")
    ap.add_argument("--iters", type=int, default=4)
    a = ap.parse_args()
    client = None if (a.code and a.spec) else _client()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else make_spec(client, a.request, a.image)
    code = Path(a.code).read_text(encoding="utf-8") if a.code else None
    final = run(spec, code, client, a.iters)
    print(json.dumps({k: final.get(k) for k in ("ok", "metrics", "warnings", "errors", "files")}, indent=2))
    sys.exit(0 if final["ok"] else 1)

if __name__ == "__main__":
    main()
