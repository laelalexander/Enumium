#!/usr/bin/env python3
"""Software Studio: local web app.   python server.py [--port 8765] [--open]
Binds to 127.0.0.1 only. API calls need a per-run token (embedded in the page) and a localhost Host header,
so other websites in your browser cannot drive it (CSRF / DNS-rebinding)."""
import argparse, io, json, re, secrets, sys, threading, webbrowser, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import store, llm, runner

HERE = Path(__file__).parent
TOKEN = secrets.token_urlsafe(24)
MAX_BODY = 2_000_000
PROJ = re.compile(r"^/api/projects/([a-f0-9]{8})(?:/(\w+))?(?:/([\w.\-]+))?$")

def workscope_md(p):
    w = p["workscope"]; L = lambda k: "\n".join(f"- {x}" for x in w[k]) or "- (none)"
    return (f"# {w['title'] or p['name']}\n\nStatus: {'APPROVED' if w['approved'] else 'DRAFT'}  |  Language: {store.LANGS[p['language']]}\n\n## Objective\n{w['objective']}\n\n"
            f"## Requirements\n{L('requirements')}\n\n## Deliverables\n{L('deliverables')}\n\n## Acceptance criteria\n{L('acceptance_criteria')}\n\n"
            f"## Assumptions\n{L('assumptions')}\n\n## Out of scope\n{L('out_of_scope')}\n\n## Risks\n{L('risks')}\n")

class H(BaseHTTPRequestHandler):
    server_version = "SoftwareStudio/1"
    def log_message(self, *a): pass
    def _send(self, code, body, ctype="application/json", extra=None):
        b = body if isinstance(body, bytes) else (json.dumps(body) if ctype == "application/json" else body).encode()
        self.send_response(code); self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype != "application/zip" else ""))
        self.send_header("Content-Length", str(len(b))); self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def _host_ok(self): return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")
    def _handle(self, method):
        if not self._host_ok(): return self._send(403, {"error": "bad host"})
        path = self.path.split("?")[0]
        if method == "GET" and path == "/":
            html = (HERE / "static" / "index.html").read_text().replace("__TOKEN__", TOKEN)
            return self._send(200, html, "text/html")
        if not path.startswith("/api/"): return self._send(404, {"error": "not found"})
        if not secrets.compare_digest(self.headers.get("X-Studio-Token", ""), TOKEN): return self._send(403, {"error": "missing or wrong token"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY: return self._send(413, {"error": "too large"})
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
            self._route(method, path, body)
        except KeyError: self._send(404, {"error": "no such project/file"})
        except ValueError as e: self._send(400, {"error": str(e)})
        except Exception as e: self._send(500, {"error": f"{e.__class__.__name__}: {e}"})
    do_GET = lambda s: s._handle("GET"); do_POST = lambda s: s._handle("POST"); do_PUT = lambda s: s._handle("PUT"); do_DELETE = lambda s: s._handle("DELETE")

    def _route(self, method, path, body):
        if path == "/api/status": return self._send(200, {"llm": llm.mode(), "model": llm.MODEL, "runtimes": runner.runtimes(), "languages": store.LANGS})
        if path == "/api/projects":
            if method == "GET": return self._send(200, store.listing())
            if method == "POST": return self._send(200, store.create(str(body.get("name", "")), body.get("language", "python")))
        m = PROJ.match(path)
        if not m: return self._send(404, {"error": "not found"})
        pid, action, arg = m.groups(); p = store.load(pid)
        if not action:
            if method == "GET": return self._send(200, p)
            if method == "DELETE": store.delete(pid); return self._send(200, {"ok": True})
            if method == "PUT":
                if "name" in body: p["name"] = str(body["name"])[:80]
                if body.get("language") in store.LANGS and body["language"] != p["language"]: p["language"] = body["language"]; p["files"] = {}
                store.save(p); return self._send(200, p)
        if action == "chat" and method == "POST":
            msg = str(body.get("message", "")).strip()
            if not msg: raise ValueError("empty message")
            reply = llm.chat(p, msg)
            p["chat"] += [{"role": "user", "content": msg}, {"role": "assistant", "content": reply}]
            store.save(p); return self._send(200, p)
        if action == "workscope":
            if arg == "draft" and method == "POST": p["workscope"] = llm.draft_workscope(p)
            elif method == "PUT":
                w = p["workscope"]
                for k in ("title", "objective"): w[k] = str(body.get(k, w[k]))[:2000]
                for k in ("requirements", "deliverables", "acceptance_criteria", "assumptions", "out_of_scope", "risks"):
                    if k in body: w[k] = [str(x).strip() for x in body[k] if str(x).strip()][:50]
                if body.get("approved") and not w["requirements"]: raise ValueError("add at least one requirement before approving")
                w["approved"] = bool(body.get("approved", False))
            else: return self._send(404, {"error": "not found"})
            store.save(p); return self._send(200, p)
        if action == "generate" and method == "POST":
            if not p["workscope"]["approved"]: raise ValueError("approve the workscope first")
            p["files"] = llm.generate(p); store.save(p); return self._send(200, p)
        if action == "files" and method == "PUT" and arg:
            p["files"][store.safe_filename(arg)] = str(body.get("content", ""))[:500_000]; store.save(p); return self._send(200, p)
        if action == "files" and method == "DELETE" and arg:
            p["files"].pop(arg); store.save(p); return self._send(200, p)
        if action == "run" and method == "POST":
            r = runner.run(p, body.get("file")); p["runs"] = (p["runs"] + [{"file": body.get("file") or "(auto)", **r}])[-20:]
            store.save(p); return self._send(200, {**r, "project": p})
        if action == "export" and method == "GET":
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for n, c in p["files"].items(): z.writestr(f"src/{n}", c)
                z.writestr("WORKSCOPE.md", workscope_md(p))
                z.writestr("CHAT.md", "\n\n".join(f"**{m['role']}**: {m['content']}" for m in p["chat"]))
            fn = re.sub(r"\W+", "_", p["name"]) + ".zip"
            return self._send(200, buf.getvalue(), "application/zip", {"Content-Disposition": f'attachment; filename="{fn}"'})
        self._send(404, {"error": "not found"})

def make_server(port=8765):
    return ThreadingHTTPServer(("127.0.0.1", port), H)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765); ap.add_argument("--open", action="store_true")
    a = ap.parse_args(); srv = make_server(a.port)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"Software Studio on {url}   (LLM: {llm.mode()}; set ANTHROPIC_API_KEY for Claude)   Ctrl+C to stop")
    if a.open: threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
