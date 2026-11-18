"""Claude-backed assistant with an offline template fallback so the studio always works.
Set ANTHROPIC_API_KEY to enable Claude. Model override: STUDIO_MODEL."""
import json, os, re
from store import LANGS

MODEL = os.environ.get("STUDIO_MODEL", "claude-sonnet-5-5")

def mode():
    return "claude" if os.environ.get("ANTHROPIC_API_KEY") else "offline"

def _call(system, messages, max_tokens=4000):
    import anthropic
    r = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=max_tokens, system=system, messages=messages)
    return "".join(b.text for b in r.content if b.type == "text")

CHAT_SYS = """You are the project analyst inside Software Studio. Target language: {lang}.
Discuss the user's project to define its WORKSCOPE: purpose, users, inputs/outputs, constraints, what is out of scope, how success is tested.
Ask at most 3 focused questions per turn, and never repeat one already answered. Keep replies under 120 words.
When you have enough, say so and tell the user to press 'Draft workscope'. Do not write code in chat."""

WS_SYS = """Turn the conversation into a workscope. Reply with ONE JSON object and nothing else, keys:
title (string), objective (string), requirements (list of short testable statements), deliverables (list of file/artifact names),
acceptance_criteria (list), assumptions (list), out_of_scope (list), risks (list). Keep the user's current edits unless the chat contradicts them."""

GEN_SYS = """You are the programmer in Software Studio. Implement the APPROVED workscope in {lang}.
Rules: standard library only; keep it small and runnable; every requirement must be traceable (comment REQ-n next to the code).
Output files in exactly this format, nothing else:
=== FILE: <name> ===
<content>
=== END ===
File set: {fileset}"""

FILESETS = {"python": "main.py (entry point) and optionally test_main.py (unittest)", "nodejs": "index.js (entry, no dependencies) and package.json",
            "vb": "Program.vb (Module Program with Sub Main) and App.vbproj (net8.0, OutputType Exe)", "plc": "main.st (IEC 61131-3 Structured Text PROGRAM with VAR blocks)"}

def chat(project, user_msg):
    if mode() == "claude":
        msgs = [{"role": m["role"], "content": m["content"]} for m in project["chat"]] + [{"role": "user", "content": user_msg}]
        return _call(CHAT_SYS.format(lang=LANGS[project["language"]]), msgs, 700)
    n = sum(1 for m in project["chat"] if m["role"] == "user") + 1
    qs = ["Who will use this, and what is the single most important thing it must do?",
          "What are the inputs and outputs (files, devices, screens, signals)? Any limits on speed, size or platform?",
          "What is explicitly out of scope, and how will we know it works (example input and expected result)?"]
    if n <= 3: return f"[offline mode, no API key] Noted. {qs[n-1]}"
    return "[offline mode] I have enough to draft. Press 'Draft workscope', review the sheet, edit it, then approve."

def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))

def draft_workscope(project):
    ws = project["workscope"]
    if mode() == "claude":
        convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in project["chat"])
        d = _json(_call(WS_SYS, [{"role": "user", "content": f"Language: {LANGS[project['language']]}\nCurrent sheet: {json.dumps(ws)}\nConversation:\n{convo}"}], 2000))
    else:
        users = [m["content"] for m in project["chat"] if m["role"] == "user"]
        sents = [s.strip() for u in users for s in re.split(r"(?<=[.!?\n])\s+", u) if len(s.strip()) > 8][:8]
        d = {"title": project["name"], "objective": (users[0] if users else project["name"])[:300],
             "requirements": sents or ["(describe the project in chat first)"],
             "deliverables": list(FILESETS[project["language"]].split(" and ")[0:1]) and [f for f in re.findall(r"[\w.]+\.\w+", FILESETS[project['language']])],
             "acceptance_criteria": ["Runs without errors on the sample input from the chat", "Every requirement has a REQ-n marker in the code"],
             "assumptions": ["Single user, local machine", "Standard library only"], "out_of_scope": ["Networking, installers, GUI polish"], "risks": ["Requirements may be incomplete (offline draft)"]}
    out = {**ws, **{k: d.get(k, ws.get(k)) for k in ws if k != "approved"}}
    out["approved"] = False
    return out

def parse_files(text):
    files = {}
    for m in re.finditer(r"=== FILE: ([\w.\-]+) ===\n(.*?)\n=== END ===", text, re.S): files[m.group(1)] = m.group(2).rstrip() + "\n"
    return files

def generate(project):
    ws = project["workscope"]
    if mode() == "claude":
        txt = _call(GEN_SYS.format(lang=LANGS[project["language"]], fileset=FILESETS[project["language"]]),
                    [{"role": "user", "content": "Approved workscope:\n" + json.dumps(ws, indent=1)}], 8000)
        files = parse_files(txt)
        if not files: raise ValueError("The model returned no files in the expected format; try again.")
        return files
    return _template(project["language"], ws)

def _template(lang, ws):
    reqs = ws["requirements"] or ["(none)"]
    title = ws["title"] or "App"
    if lang == "python":
        items = "\n".join(f'    # REQ-{i+1}\n    print("TODO REQ-{i+1}: {r[:70]!r}")'.replace("'", "") for i, r in enumerate(reqs))
        return {"main.py": f'"""{title}\n\nOffline template: replace each TODO with real logic."""\n\n\ndef main():\n{items}\n\n\nif __name__ == "__main__":\n    main()\n'}
    if lang == "nodejs":
        items = "\n".join(f'  // REQ-{i+1}\n  console.log({json.dumps("TODO REQ-%d: %s" % (i+1, r[:70]))});' for i, r in enumerate(reqs))
        return {"index.js": f"// {title}\nfunction main() {{\n{items}\n}}\nmain();\n",
                "package.json": json.dumps({"name": re.sub(r"\W+", "-", title.lower()).strip("-") or "app", "version": "0.1.0", "main": "index.js", "scripts": {"start": "node index.js"}}, indent=2) + "\n"}
    if lang == "vb":
        items = "\n".join(f'        \' REQ-{i+1}\n        Console.WriteLine("TODO REQ-{i+1}: {r[:70].replace(chr(34), chr(39))}")' for i, r in enumerate(reqs))
        return {"Program.vb": f"Module Program\n    Sub Main()\n{items}\n    End Sub\nEnd Module\n",
                "App.vbproj": '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <OutputType>Exe</OutputType>\n    <TargetFramework>net8.0</TargetFramework>\n    <RootNamespace>App</RootNamespace>\n  </PropertyGroup>\n</Project>\n'}
    items = "\n".join(f"    (* REQ-{i+1}: {r[:70].replace('*)', '')} *)" for i, r in enumerate(reqs))
    return {"main.st": f"PROGRAM Main\nVAR\n    Start : BOOL;\n    Stop : BOOL;\n    Running : BOOL;\nEND_VAR\n\n{items}\n\nIF Start AND NOT Stop THEN\n    Running := TRUE;\nELSIF Stop THEN\n    Running := FALSE;\nEND_IF;\nEND_PROGRAM\n"}
