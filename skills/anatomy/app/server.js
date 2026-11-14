// Anatomy app server. No npm dependencies: run with `node server.js`.
// Serves the UI on http://127.0.0.1:4377 and runs Claude Code headless
// (claude -p --output-format stream-json) inside each project folder,
// streaming its events to the browser window over Server-Sent Events.
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFile } = require('child_process');
const os = require('os');

const PORT = Number(process.env.ANATOMY_PORT || 4377);
const ROOT = process.env.ANATOMY_ROOT || (process.platform === 'win32' ? 'C:\\Anatomy' : path.join(os.homedir(), 'Anatomy'));
const PUBLIC = path.join(__dirname, 'public');
const META_DIR = '.anatomy';
const HIDDEN = new Set([META_DIR, 'CLAUDE.md', '.git', 'node_modules', '.claude', '__pycache__', '.venv']);

fs.mkdirSync(ROOT, { recursive: true });

// ---------------------------------------------------------------- helpers
const runs = new Map(); // id -> { proc, clients:Set<res> }

function slugify(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40).replace(/-+$/, '') || 'project';
}
function projectDir(id) {
  if (!/^[a-z0-9-]+$/.test(id)) throw new Error('bad id');
  return path.join(ROOT, id);
}
function metaPath(id) { return path.join(projectDir(id), META_DIR, 'project.json'); }
function logPath(id) { return path.join(projectDir(id), META_DIR, 'events.jsonl'); }
function readMeta(id) {
  try { return JSON.parse(fs.readFileSync(metaPath(id), 'utf8')); } catch { return null; }
}
function writeMeta(id, meta) {
  fs.mkdirSync(path.dirname(metaPath(id)), { recursive: true });
  fs.writeFileSync(metaPath(id), JSON.stringify(meta, null, 2));
}
function send(res, code, body, type = 'application/json') {
  res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
}
function readBody(req, limit = 200 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = []; let n = 0;
    req.on('data', c => { n += c.length; if (n > limit) { reject(new Error('too large')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}
function safeJoin(base, rel) {
  const p = path.resolve(base, rel || '.');
  if (p !== base && !p.startsWith(base + path.sep)) throw new Error('path escapes project');
  return p;
}
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.webp': 'image/webp', '.pdf': 'application/pdf', '.stl': 'model/stl',
};

function emit(id, ev) {
  ev.ts = ev.ts || Date.now();
  const line = JSON.stringify(ev);
  try { fs.appendFileSync(logPath(id), line + '\n'); } catch {}
  const r = runs.get(id);
  if (r) for (const c of r.clients) c.write(`data: ${line}\n\n`);
}

// Find the claude executable once.
let claudePath = null;
function findClaude() {
  if (claudePath) return claudePath;
  const cands = [];
  if (process.platform === 'win32') {
    const h = os.homedir();
    cands.push(path.join(h, '.local', 'bin', 'claude.exe'));
    if (process.env.APPDATA) cands.push(path.join(process.env.APPDATA, 'npm', 'claude.cmd'));
    for (const dir of (process.env.PATH || '').split(';')) {
      cands.push(path.join(dir, 'claude.exe'), path.join(dir, 'claude.cmd'));
    }
  } else {
    for (const dir of (process.env.PATH || '').split(':')) cands.push(path.join(dir, 'claude'));
    cands.push(path.join(os.homedir(), '.local', 'bin', 'claude'));
  }
  claudePath = cands.find(p => { try { return fs.statSync(p).isFile(); } catch { return false; } }) || null;
  return claudePath;
}

// Find KiCad's bin folder so Claude does not have to hunt for it.
function findKiCadBin() {
  if (process.platform !== 'win32') return null;
  const bases = [process.env.ProgramFiles, process.env['ProgramFiles(x86)'],
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs')].filter(Boolean);
  for (const b of bases) {
    const k = path.join(b, 'KiCad');
    let vers = [];
    try { vers = fs.readdirSync(k).sort((a, c) => parseFloat(c) - parseFloat(a)); } catch { continue; }
    for (const v of vers) {
      const bin = path.join(k, v, 'bin');
      if (fs.existsSync(path.join(bin, 'kicad-cli.exe'))) return bin;
    }
  }
  return null;
}

const SETTINGS = path.join(ROOT, 'anatomy-settings.md');
const DEFAULT_SETTINGS = `# Anatomy settings

Claude reads this file at the start of every project. Edit it from the Settings button in the app.

## 3D printer
- Printer model:
- Bed size (mm):
- Nozzle (mm): 0.4
- Firmware / slicer: (e.g. Prusa, Klipper, Marlin, Bambu)
- Materials on hand: PLA, PETG
- Slicer profile files: (paths to .ini/.3mf/.json, if any)

## Preferences
- Preferred suppliers: Digi-Key, Mouser, LCSC, McMaster-Carr
- Region / currency: USA, USD
- Tools on hand: (soldering iron, multimeter, ...)
`;
function readSettings() {
  try { return fs.readFileSync(SETTINGS, 'utf8'); } catch { fs.writeFileSync(SETTINGS, DEFAULT_SETTINGS); return DEFAULT_SETTINGS; }
}

const PHASES = ['Scope', 'Gather evidence', 'Analyze', 'Blueprint', 'Prototype', 'Verify'];
function systemAppend() {
  const kicad = findKiCadBin();
  return [
    'You are running inside the Anatomy app. The user watches your progress in a window and cannot answer prompts mid-run.',
    'Use the anatomy skill for this work. Work in the current folder. Files the user attached are in inputs/; read them first.',
    'Do not stop to ask clarifying questions. Make reasonable assumptions, record them in the blueprint as [assumed], and keep going. Only stop early if you are truly blocked, and then say exactly what you need.',
    `REQUIRED for the progress display: every time you move to a new step of the anatomy workflow (all six, in order, even if a step is short), your text message must start with its marker on its own line. Markers: ${PHASES.map((p, i) => `[[phase:${i + 1}]] = ${p}`).join('; ')}.`,
    'Before each significant action, write one short plain sentence saying what you are doing and why, so the user can follow along.',
    kicad ? `KiCad is installed at ${kicad} (kicad-cli.exe and KiCad's python.exe with pcbnew are there). The KiCad PCB step is experimental: run ERC/DRC and report results honestly.` :
      'KiCad was not found on this machine. If a PCB is needed, say so and fall back to a layout spec labeled specified only.',
    'Hardware standards are mandatory: every part is BUY or BUILD (references/parts-and-bom.md, run the BOM check), production-quality drawings (references/drawings.md), and every 3D printed part ends in verified G-code for the user\'s printer (references/3d-print-gcode.md). If the product runs any code, firmware/BIOS/software is a full development phase (references/software-phase.md).',
    'The user\'s settings (printer, materials, suppliers, tools) follow. Use them; if the printer is not filled in, use a stated default profile and say the G-code must be re-sliced.\n<user-settings>\n' + readSettings() + '\n</user-settings>',
    'At the end, print a short summary: what you built, where the key files are, what was verified, and what is still unverified.',
  ].join('\n');
}

function cleanEnv() {
  const env = { ...process.env };
  for (const k of Object.keys(env)) {
    // Markers inherited when the server was started from inside another Claude session.
    if (k === 'CLAUDECODE' || k.startsWith('CLAUDE_CODE_') || k === 'ANTHROPIC_BASE_URL') delete env[k];
  }
  const extra = [];
  if (process.platform === 'win32') {
    for (const d of [path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Prusa3D', 'PrusaSlicer')]) if (fs.existsSync(d)) extra.push(d);
    for (const b of [process.env.ProgramFiles, process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs')].filter(Boolean)) {
      let ds = []; try { ds = fs.readdirSync(b).filter(n => /^FreeCAD/i.test(n)); } catch {}
      for (const n of ds) { const bin = path.join(b, n, 'bin'); if (fs.existsSync(bin)) extra.push(bin); }
    }
  }
    if (process.env.APPDATA) {
      let pys = []; try { pys = fs.readdirSync(path.join(process.env.APPDATA, 'Python')); } catch {}
      for (const v of pys) { const sc = path.join(process.env.APPDATA, 'Python', v, 'Scripts'); if (fs.existsSync(path.join(sc, 'pio.exe'))) extra.push(sc); }
    }
  if (extra.length) env.PATH = extra.join(path.delimiter) + path.delimiter + (env.PATH || '');
  const kicad = findKiCadBin();
  if (kicad) env.PATH = kicad + path.delimiter + (env.PATH || '');
  return env;
}

const ALLOWED_TOOLS = ['Bash', 'Read', 'Write', 'Edit', 'MultiEdit', 'Glob', 'Grep', 'WebFetch', 'WebSearch',
  'Skill', 'TodoWrite', 'Task', 'NotebookEdit'];

function startRun(id, message, display) {
  if (runs.get(id)?.proc) throw new Error('already running');
  const meta = readMeta(id);
  const claude = findClaude();
  if (!claude) {
    emit(id, { type: 'anatomy', kind: 'error', text: 'Claude Code was not found on this PC. Install it from https://claude.com/claude-code and try again.' });
    return;
  }
  const args = ['-p', '--output-format', 'stream-json', '--verbose',
    '--permission-mode', 'acceptEdits',
    '--allowedTools', ALLOWED_TOOLS.join(','),
    '--append-system-prompt', systemAppend()];
  if (meta.model) args.push('--model', meta.model);
  if (meta.sessionId) args.push('--resume', meta.sessionId);

  const isCmd = claude.toLowerCase().endsWith('.cmd');
  const proc = spawn(isCmd ? `"${claude}"` : claude, isCmd ? args.map(a => `"${a.replace(/"/g, '\\"')}"`) : args, {
    cwd: projectDir(id), env: cleanEnv(), windowsHide: true, shell: isCmd,
  });
  const r = runs.get(id) || { clients: new Set() };
  r.proc = proc; runs.set(id, r);

  meta.status = 'running'; meta.updated = new Date().toISOString(); writeMeta(id, meta);
  emit(id, { type: 'anatomy', kind: 'run-start', text: display || message });

  proc.stdin.write(message);
  proc.stdin.end();

  let buf = '';
  proc.stdout.on('data', d => {
    buf += d.toString('utf8');
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
      if (!line) continue;
      let ev; try { ev = JSON.parse(line); } catch { emit(id, { type: 'anatomy', kind: 'log', text: line }); continue; }
      if (ev.session_id && ev.session_id !== meta.sessionId) { meta.sessionId = ev.session_id; writeMeta(id, meta); }
      emit(id, ev);
    }
  });
  let errTail = '';
  proc.stderr.on('data', d => { errTail = (errTail + d.toString('utf8')).slice(-4000); });
  proc.on('error', e => emit(id, { type: 'anatomy', kind: 'error', text: 'Could not start Claude Code: ' + e.message }));
  proc.on('close', code => {
    const m = readMeta(id) || meta;
    const stopped = r.stopping;
    m.status = stopped ? 'stopped' : (code === 0 ? 'done' : 'failed');
    m.updated = new Date().toISOString(); writeMeta(id, m);
    if (code !== 0 && !stopped) {
      let text = errTail.trim() || `Claude Code exited with code ${code}.`;
      if (/login|log in|auth/i.test(text)) text += '\n\nClaude Code needs you to sign in again. Click "Sign in" at the top of the window.';
      emit(id, { type: 'anatomy', kind: 'error', text });
    }
    emit(id, { type: 'anatomy', kind: 'run-end', status: m.status });
    r.proc = null; r.stopping = false;
  });
}

function stopRun(id) {
  const r = runs.get(id);
  if (!r?.proc) return;
  r.stopping = true;
  if (process.platform === 'win32') execFile('taskkill', ['/pid', String(r.proc.pid), '/T', '/F'], () => {});
  else r.proc.kill('SIGTERM');
}

function listFiles(base, rel = '', out = [], depth = 0) {
  if (depth > 8 || out.length > 2000) return out;
  let ents = [];
  try { ents = fs.readdirSync(path.join(base, rel), { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    if (HIDDEN.has(e.name)) continue;
    const r = rel ? rel + '/' + e.name : e.name;
    if (e.isDirectory()) listFiles(base, r, out, depth + 1);
    else {
      let st; try { st = fs.statSync(path.join(base, r)); } catch { continue; }
      out.push({ path: r, size: st.size, mtime: st.mtimeMs });
    }
  }
  return out;
}

function listProjects() {
  let ents = [];
  try { ents = fs.readdirSync(ROOT, { withFileTypes: true }); } catch {}
  return ents.filter(e => e.isDirectory()).map(e => {
    const m = readMeta(e.name);
    if (!m) return null;
    if (m.status === 'running' && !runs.get(e.name)?.proc) m.status = 'stopped';
    return { id: e.name, ...m };
  }).filter(Boolean).sort((a, b) => (b.updated || '').localeCompare(a.updated || ''));
}

// ---------------------------------------------------------------- routes
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const parts = url.pathname.split('/').filter(Boolean);

    // Only accept requests from this machine's own UI.
    const origin = req.headers.origin;
    if (origin && !/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin)) return send(res, 403, { error: 'forbidden' });

    if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
      return send(res, 200, fs.readFileSync(path.join(PUBLIC, 'index.html')), MIME['.html']);
    }
    if (parts[0] !== 'api') return send(res, 404, { error: 'not found' });

    if (parts[1] === 'health') return send(res, 200, { ok: true, app: 'anatomy', root: ROOT, claude: !!findClaude(), kicad: findKiCadBin() });

    if (parts[1] === 'projects' && parts.length === 2) {
      if (req.method === 'GET') return send(res, 200, listProjects());
      if (req.method === 'POST') {
        const { prompt, model } = JSON.parse((await readBody(req)).toString('utf8') || '{}');
        if (!prompt || !prompt.trim()) return send(res, 400, { error: 'prompt required' });
        const base = slugify(prompt.split(/\s+/).slice(0, 6).join(' '));
        let id = base, n = 2;
        while (fs.existsSync(path.join(ROOT, id))) id = `${base}-${n++}`;
        fs.mkdirSync(path.join(ROOT, id, 'inputs'), { recursive: true });
        const title = prompt.trim().split('\n')[0].slice(0, 80);
        writeMeta(id, { title, prompt: prompt.trim(), model: model || 'claude-fable-5-2', status: 'new',
          created: new Date().toISOString(), updated: new Date().toISOString() });
        fs.writeFileSync(path.join(ROOT, id, 'CLAUDE.md'),
          `# Anatomy project\n\nUse the \`anatomy\` skill for all work in this folder.\n\nBrief:\n\n${prompt.trim()}\n\nInputs from the user (datasheets, photos, references) are in \`inputs/\`.\n`);
        return send(res, 200, { id });
      }
    }

    if (parts[1] === 'projects' && parts[2]) {
      const id = parts[2];
      const dir = projectDir(id);
      const meta = readMeta(id);
      if (!meta) return send(res, 404, { error: 'no such project' });
      const action = parts[3];

      if (!action && req.method === 'GET') return send(res, 200, { id, ...meta, running: !!runs.get(id)?.proc });

      if (action === 'upload' && req.method === 'POST') {
        const name = path.basename(url.searchParams.get('name') || 'file').replace(/[<>:"|?*]/g, '_');
        const data = await readBody(req);
        fs.writeFileSync(safeJoin(path.join(dir, 'inputs'), name), data);
        return send(res, 200, { ok: true, path: 'inputs/' + name });
      }
      if (action === 'run' && req.method === 'POST') {
        const { message } = JSON.parse((await readBody(req)).toString('utf8') || '{}');
        const text = message && message.trim() ? message.trim() :
          `Run the anatomy skill on this brief:\n\n${meta.prompt}\n\nRead CLAUDE.md and everything in inputs/ first.`;
        try { startRun(id, text, message && message.trim() ? message.trim() : meta.prompt); } catch (e) { return send(res, 409, { error: e.message }); }
        return send(res, 200, { ok: true });
      }
      if (action === 'stop' && req.method === 'POST') { stopRun(id); return send(res, 200, { ok: true }); }

      if (action === 'events' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' });
        let past = '';
        try { past = fs.readFileSync(logPath(id), 'utf8'); } catch {}
        for (const line of past.split('\n')) if (line.trim()) res.write(`data: ${line}\n\n`);
        res.write(`data: ${JSON.stringify({ type: 'anatomy', kind: 'replay-done', running: !!runs.get(id)?.proc })}\n\n`);
        const r = runs.get(id) || { clients: new Set() };
        runs.set(id, r); r.clients.add(res);
        const ping = setInterval(() => res.write(': ping\n\n'), 20000);
        req.on('close', () => { clearInterval(ping); r.clients.delete(res); });
        return;
      }
      if (action === 'files' && req.method === 'GET') return send(res, 200, listFiles(dir));
      if (action === 'file' && req.method === 'GET') {
        const p = safeJoin(dir, url.searchParams.get('path'));
        const ext = path.extname(p).toLowerCase();
        const st = fs.statSync(p);
        if (st.size > 50 * 1024 * 1024) return send(res, 413, { error: 'file too large to preview' });
        return send(res, 200, fs.readFileSync(p), MIME[ext] || 'text/plain; charset=utf-8');
      }
      if (action === 'reveal' && req.method === 'POST') {
        const rel = url.searchParams.get('path');
        const p = rel ? safeJoin(dir, rel) : dir;
        if (process.platform === 'win32') execFile('explorer.exe', rel ? ['/select,', p] : [p], () => {});
        return send(res, 200, { ok: true });
      }
    }

    if (parts[1] === 'settings') {
      if (req.method === 'GET') return send(res, 200, { text: readSettings() });
      if (req.method === 'PUT') {
        const { text } = JSON.parse((await readBody(req, 1024 * 1024)).toString('utf8') || '{}');
        fs.writeFileSync(SETTINGS, String(text || ''));
        return send(res, 200, { ok: true });
      }
    }

    if (parts[1] === 'login' && req.method === 'POST') {
      // Opens a visible window running Claude Code's sign-in, the only step that needs a terminal.
      const claude = findClaude();
      if (claude && process.platform === 'win32') {
        spawn('cmd.exe', ['/c', 'start', '"Sign in to Claude"', claude, '/login'], { env: cleanEnv(), detached: true, windowsHide: false });
      }
      return send(res, 200, { ok: !!claude });
    }

    if (parts[1] === 'quit' && req.method === 'POST') {
      send(res, 200, { ok: true });
      for (const id of runs.keys()) stopRun(id);
      setTimeout(() => process.exit(0), 300);
      return;
    }

    send(res, 404, { error: 'not found' });
  } catch (e) {
    send(res, 500, { error: e.message });
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Anatomy running at http://127.0.0.1:${PORT}  (projects in ${ROOT})`);
});
