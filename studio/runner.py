"""Run generated code. Python/Node via their interpreters, VB via `dotnet` if present, PLC ST via a structural linter.
NOT a sandbox: code runs as you, with your network. Only run code you have read."""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

CAP = 20000

def runtimes():
    return {"python": True, "nodejs": bool(shutil.which("node")), "vb": bool(shutil.which("dotnet")), "plc": True}

def _clip(s): return s if len(s) <= CAP else s[:CAP] + "\n...[output truncated]"

def lint_st(src):
    stripped = re.sub(r"\(\*.*?\*\)", " ", src, flags=re.S)
    stripped = re.sub(r"//[^\n]*", " ", stripped)
    toks = re.findall(r"[A-Za-z_]+", stripped.upper())
    msgs = []
    for a, b in (("PROGRAM", "END_PROGRAM"), ("FUNCTION_BLOCK", "END_FUNCTION_BLOCK"), ("IF", "END_IF"), ("FOR", "END_FOR"),
                 ("WHILE", "END_WHILE"), ("CASE", "END_CASE"), ("VAR", "END_VAR")):
        n1, n2 = toks.count(a), toks.count(b)
        if a == "VAR": n1 += toks.count("VAR_INPUT") + toks.count("VAR_OUTPUT")
        if n1 != n2: msgs.append(f"unbalanced {a}/{b}: {n1} vs {n2}")
    if toks.count("THEN") != toks.count("IF") + toks.count("ELSIF"): msgs.append("IF/ELSIF without matching THEN")
    body = [l.strip() for l in stripped.splitlines() if ":=" in l]
    for l in body:
        if not l.endswith(";") and not re.search(r"\b(THEN|DO|OF)$|:\s*\w+\s*:=.*[^;]$", l): msgs.append(f"missing ';': {l[:60]}")
    return msgs

def run(project, entry=None):
    lang, files = project["language"], project["files"]
    if not files: return {"exit": 2, "output": "No files yet: generate code first."}
    if lang == "plc":
        src = next((v for k, v in files.items() if k.endswith(".st")), "")
        msgs = lint_st(src)
        return {"exit": 1 if msgs else 0, "output": ("Lint problems:\n" + "\n".join(msgs)) if msgs else "ST structure check passed (balanced blocks, THEN/;). This is a linter, not a PLC runtime: test on your target or a simulator."}
    with tempfile.TemporaryDirectory() as d:
        for n, c in files.items(): (Path(d) / n).write_text(c)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": d, "DOTNET_CLI_HOME": d, "DOTNET_NOLOGO": "1"}
        if lang == "python":
            main = entry or ("main.py" if "main.py" in files else next(iter(files)))
            cmd, to = [sys.executable, "-E", main], 20
        elif lang == "nodejs":
            if not shutil.which("node"): return {"exit": 127, "output": "Node.js is not installed on this machine (https://nodejs.org). Preview/export still work."}
            cmd, to = ["node", entry or ("index.js" if "index.js" in files else next(iter(files)))], 20
        else:
            if not shutil.which("dotnet"): return {"exit": 127, "output": "The .NET SDK ('dotnet') is not installed, so Visual Basic can't run here. Install it from https://dotnet.microsoft.com or export the project."}
            cmd, to = ["dotnet", "run", "--project", next((k for k in files if k.endswith(".vbproj")), "App.vbproj")], 180
        try:
            r = subprocess.run(cmd, cwd=d, env=env, capture_output=True, text=True, timeout=to)
            return {"exit": r.returncode, "output": _clip(r.stdout + (("\n[stderr]\n" + r.stderr) if r.stderr else ""))}
        except subprocess.TimeoutExpired:
            return {"exit": 124, "output": f"Timed out after {to}s."}
