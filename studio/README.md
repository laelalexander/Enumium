# Software Studio (rebuild)

Local web app for the flow: **discuss the project -> define and approve a workscope -> generate code -> preview, edit, run -> export.**
Languages: Python, Node.js, Visual Basic (.NET), PLC logic (IEC 61131-3 Structured Text).

```bash
python server.py --open            # needs only Python 3.10+ (stdlib); http://127.0.0.1:8765
pip install anthropic              # optional, for the Claude assistant
export ANTHROPIC_API_KEY=...       # Windows: setx ANTHROPIC_API_KEY ...   (optional STUDIO_MODEL override)
python -m pytest -q tests
```

## How it works
1. **Discuss** (left): chat with the analyst. It asks focused questions about users, inputs/outputs, limits, scope, tests.
2. **Workscope** (middle): "Draft workscope" turns the chat into an editable sheet (objective, requirements, deliverables,
   acceptance criteria, assumptions, out of scope, risks). Edit it, then **Approve**. Editing un-approves it. Code generation is locked until approved.
3. **Code** (right): file tabs, line numbers and syntax colouring, Edit/Save, Copy, **Run** (asks first), output console, **Export .zip**
   (source + WORKSCOPE.md + CHAT.md). Every requirement gets a `REQ-n` marker in the generated code.

Projects are stored as JSON in `data/` (override with `STUDIO_DATA`).

## Be aware
- **Offline mode** (no API key) uses fixed templates: it asks generic questions and produces a skeleton with a TODO per requirement. Real
  code quality needs the Claude key. The Claude path is covered by tests with a mocked model, not run against the live API here.
- **Run is not a sandbox.** Generated code runs as you, with your network. Read it first.
- Node.js and `dotnet` must be installed to run those languages; otherwise the app says so and you can still preview/export.
  PLC "Run" is a structural linter (balanced blocks, THEN, semicolons), not a PLC runtime; test on your target or a simulator.
- Security: binds to 127.0.0.1, requires a per-launch token and a localhost Host header so other web pages can't drive it.
- This is a new app, not a patch of the previous "Nero Software Studio" (its source wasn't available). The `X-NSS-Key` error in that tool
  is an API-key config problem in that tool; this app needs no such key.
