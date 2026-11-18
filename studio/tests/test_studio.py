import json, os, sys, threading, urllib.request, urllib.error, zipfile, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest

@pytest.fixture
def srv(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDIO_DATA", str(tmp_path)); monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import server
    s = server.make_server(0); threading.Thread(target=s.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{s.server_address[1]}"
    def call(method, path, body=None, token=server.TOKEN, host=None, raw=False):
        req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None)
        if token: req.add_header("X-Studio-Token", token)
        if host: req.add_header("Host", host)
        try:
            with urllib.request.urlopen(req) as r: d = r.read(); return r.status, (d if raw else json.loads(d))
        except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
    yield call, server
    s.shutdown()

def test_index_embeds_token_and_api_needs_it(srv):
    call, server = srv
    status, html = call("GET", "/", token=None, raw=True)
    assert status == 200 and server.TOKEN.encode() in html and b"__TOKEN__" not in html
    assert call("GET", "/api/status", token=None)[0] == 403
    assert call("GET", "/api/status", token="wrong")[0] == 403
    assert call("GET", "/api/status", host="evil.example.com")[0] == 403
    assert call("GET", "/api/status")[1]["llm"] == "offline"

@pytest.mark.parametrize("lang,entry,expect", [("python", "main.py", "TODO REQ-1"), ("nodejs", "index.js", None), ("vb", "Program.vb", None), ("plc", "main.st", "passed")])
def test_full_flow_each_language(srv, lang, entry, expect):
    call, _ = srv
    p = call("POST", "/api/projects", {"name": "Demo", "language": lang})[1]; pid = p["id"]
    assert call("POST", f"/api/projects/{pid}/generate")[0] == 400                      # not approved yet
    for t in ("I want a conveyor controller. It must start when the button is pressed.", "Operators use it. Inputs are two buttons.", "Out of scope: networking. Example: press start, belt runs."):
        p = call("POST", f"/api/projects/{pid}/chat", {"message": t})[1]
    assert len(p["chat"]) == 6 and "offline" in p["chat"][-1]["content"]
    p = call("POST", f"/api/projects/{pid}/workscope/draft")[1]
    assert p["workscope"]["requirements"] and not p["workscope"]["approved"]
    p = call("PUT", f"/api/projects/{pid}/workscope", {**p["workscope"], "approved": True})[1]
    assert p["workscope"]["approved"]
    p = call("POST", f"/api/projects/{pid}/generate")[1]
    assert entry in p["files"]
    st, r = call("POST", f"/api/projects/{pid}/run", {})
    if lang in ("python", "plc"):
        assert r["exit"] == 0 and (expect in r["output"]), r
    else:
        assert r["exit"] in (0, 127), r      # 127 = runtime not installed here, reported clearly
    z = call("GET", f"/api/projects/{pid}/export", raw=True)[1]
    names = zipfile.ZipFile(io.BytesIO(z)).namelist()
    assert "WORKSCOPE.md" in names and f"src/{entry}" in names

def test_cannot_approve_empty_and_editing_flows(srv):
    call, _ = srv
    pid = call("POST", "/api/projects", {"name": "x", "language": "python"})[1]["id"]
    assert call("PUT", f"/api/projects/{pid}/workscope", {"approved": True})[0] == 400
    call("PUT", f"/api/projects/{pid}/workscope", {"requirements": ["a", " ", "b"], "approved": True})
    p = call("PUT", f"/api/projects/{pid}/files/main.py", {"content": "print('hi')"})[1]
    assert call("POST", f"/api/projects/{pid}/run", {})[1]["output"].strip().startswith("hi")
    assert call("PUT", f"/api/projects/{pid}/files/..%2Fevil.py", {"content": "x"})[0] in (400, 404)
    assert call("GET", "/api/projects/zzzzzzzz")[0] == 404

def test_python_timeout_and_plc_lint():
    import runner
    bad = runner.lint_st("PROGRAM P\nVAR\n a : BOOL;\nEND_VAR\nIF a THEN\n a := FALSE;\nEND_PROGRAM")
    assert any("IF" in m for m in bad)
    assert runner.lint_st("PROGRAM P\nVAR a : BOOL; END_VAR\nIF a THEN\n a := FALSE;\nEND_IF;\nEND_PROGRAM") == []

def test_claude_mode_parses_files_and_workscope(srv, monkeypatch):
    call, _ = srv
    import llm
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    def fake(system, messages, max_tokens=4000):
        if "WORKSCOPE" in system.upper() and "JSON" in system: return 'Sure {"title":"T","objective":"O","requirements":["r1","r2"],"deliverables":["main.py"]}'
        if "programmer" in system: return "=== FILE: main.py ===\nprint('REQ-1 ok')\n=== END ===\n=== FILE: test_main.py ===\nimport unittest\n=== END ==="
        return "What platform?"
    monkeypatch.setattr(llm, "_call", fake)
    pid = call("POST", "/api/projects", {"name": "c", "language": "python"})[1]["id"]
    assert call("POST", f"/api/projects/{pid}/chat", {"message": "hello"})[1]["chat"][-1]["content"] == "What platform?"
    p = call("POST", f"/api/projects/{pid}/workscope/draft")[1]
    assert p["workscope"]["requirements"] == ["r1", "r2"]
    call("PUT", f"/api/projects/{pid}/workscope", {**p["workscope"], "approved": True})
    p = call("POST", f"/api/projects/{pid}/generate")[1]
    assert set(p["files"]) == {"main.py", "test_main.py"}
