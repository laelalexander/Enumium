# AI workflow: request → validated CAD part

```
request (+ optional sketch) ─► SPEC (LLM, JSON) ─► GENERATE (LLM, CadQuery code)
        ▲                                                   │
        │ errors fed back (max N iterations)                ▼
        └──────────── REPAIR ◄── VALIDATE ◄── EXECUTE (subprocess, timeout)
                                      │ pass
                                      ▼
                        out/<name>/ part.py · .step · .stl · report.json
```

Validation checks: valid B-rep, exactly one solid, positive volume, bounding box
matches the spec, minimum feature size (warning).

## Setup
```bash
pip install cadquery anthropic pytest
export ANTHROPIC_API_KEY=...
```

## Use
```bash
python pipeline.py "L-bracket 60x30 mm base, 25 mm tall flange, two M5 holes"
python pipeline.py --image sketch.png "bracket matching this sketch"
python pipeline.py --code examples/bracket.py --spec examples/bracket.json   # no LLM
python -m pytest -q tests
```

## Notes
- Generated code runs in a subprocess with timeout and memory/CPU limits. That is
  not a security sandbox; run in a container for untrusted input.
- Extension points: add checks in `runner.validate` (wall thickness, overhang
  analysis, mass), add a render-and-critique step (render STL, send to a vision
  model) between VALIDATE and PUBLISH, or add a retrieval step of example parts
  to the GENERATE prompt.
- The LLM stages (`make_spec`, `generate`) are untested here without an API key;
  the execute/validate/export stages are covered by `tests/`.
