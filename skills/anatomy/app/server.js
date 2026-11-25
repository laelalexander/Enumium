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
const xometry = require('./xometry');
const hubSync = require('./sync');

const PORT = Number(process.env.ANATOMY_PORT || 4377);
const ROOT = process.env.ANATOMY_ROOT || (process.platform === 'win32' ? 'C:\\Anatomy' : path.join(os.homedir(), 'Anatomy'));
const PUBLIC = path.join(__dirname, 'public');
const META_DIR = '.anatomy';
const HIDDEN = new Set([META_DIR, 'CLAUDE.md', '.tools', 'venv', 'env', '.pio', '.mypy_cache', '.pytest_cache', 'dist-info', '.git', 'node_modules', '.claude', '__pycache__', '.venv']);

fs.mkdirSync(ROOT, { recursive: true });

// Central project storage on the Anatomy Hub (the Droplet). Off until a hub address and token are saved in the app.
let hub = null; // created below, once readMeta and runs exist

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
// Files written by Windows PowerShell (Set-Content -Encoding UTF8) start with a BOM, which JSON.parse rejects.
const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));
function readMeta(id) {
  try { return readJson(metaPath(id)); } catch { return null; }
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
  '.webp': 'image/webp', '.pdf': 'application/pdf', '.stl': 'model/stl', '.wasm': 'application/wasm',
  '.mjs': 'text/javascript; charset=utf-8', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.obj': 'text/plain; charset=utf-8',
  '.csv': 'text/plain; charset=utf-8', '.py': 'text/plain; charset=utf-8', '.gcode': 'text/plain; charset=utf-8', '.svgz': 'image/svg+xml',
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
- Printer model: Bambu Lab (model?)
- Bed size (mm): 256 x 256 x 256
- Nozzle (mm): 0.4
- Firmware / slicer: Bambu Studio (deliver Bambu Studio .3mf projects)
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
  // KiCad last, so its bundled Python does not shadow the system Python for venvs.
  if (kicad) env.PATH = (env.PATH || '') + path.delimiter + kicad;
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
  const skillDir = path.join(os.homedir(), '.claude', 'skills', 'anatomy');
  if (fs.existsSync(skillDir)) args.push('--add-dir', skillDir);
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
      if (ev.type === 'result' && (ev.is_error || ev.terminal_reason === 'api_error' || ev.subtype !== 'success' || /spend limit|usage limit|session limit/i.test(ev.result || ''))) {
        resultErr = String(ev.result || (ev.errors || []).join('\n') || ev.subtype || '').trim();
      }
      emit(id, ev);
    }
  });
  let errTail = '', resultErr = '';
  proc.stderr.on('data', d => { errTail = (errTail + d.toString('utf8')).slice(-4000); });
  proc.on('error', e => emit(id, { type: 'anatomy', kind: 'error', text: 'Could not start Claude Code: ' + e.message }));
  proc.on('close', code => {
    const m = readMeta(id) || meta;
    const stopped = r.stopping;
    m.status = stopped ? 'stopped' : (code === 0 ? 'done' : 'failed');
    m.updated = new Date().toISOString(); writeMeta(id, m);
    if (code !== 0 && !stopped) {
      // The reason is usually in the last result event (usage limit, API error), not on stderr.
      let text = [resultErr, errTail.trim()].filter(Boolean).join('\n\n') || `Claude Code exited with code ${code}.`;
      if (/rate.?limit|usage limit|session limit|spend limit|429|resets/i.test(text)) text += '\n\nYour Claude usage limit was reached. Raise it at claude.ai/settings/usage or wait for the reset; then open this project and send \"continue\" to pick up where it stopped.';
      else if (/login|log in|auth/i.test(text)) text += '\n\nClaude Code needs you to sign in again. Click "Sign in" at the top of the window.';
      emit(id, { type: 'anatomy', kind: 'error', text });
    }
    emit(id, { type: 'anatomy', kind: 'run-end', status: m.status });
    r.proc = null; r.stopping = false;
    if (hub.config()) hub.syncProject(id).catch(() => {}).finally(() => hub.unlock(id));
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

// Every 3D file in the project, without listFiles' 2000-file cap (large build kits and G-code sets go past it).
const MESH_RE = /\.(stl|3mf|obj|glb)$|(^|[\\/])assembly\.json$/i; // plus assembly.json, the viewer's assembly description
function listMeshes(base, rel = '', out = [], depth = 0) {
  if (depth > 12 || out.length > 5000) return out;
  let ents = [];
  try { ents = fs.readdirSync(path.join(base, rel), { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    if (HIDDEN.has(e.name)) continue;
    const r = rel ? rel + '/' + e.name : e.name;
    if (e.isDirectory()) listMeshes(base, r, out, depth + 1);
    else if (MESH_RE.test(e.name)) { try { const st = fs.statSync(path.join(base, r)); out.push({ path: r, size: st.size, mtime: st.mtimeMs }); } catch {} }
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

hub = hubSync.create({ ROOT, readMeta, isRunning: id => !!runs.get(id)?.proc });
hub.start();

// Projects on this PC plus the ones that so far live only on the hub (other PCs' projects).
function listAllProjects() {
  const local = listProjects();
  const have = new Set(local.map(p => p.id));
  const remote = hub.remoteProjects();
  const byId = new Map(remote.map(p => [p.id, p]));
  for (const p of local) { const r = byId.get(p.id); p.where = r ? 'synced' : 'here'; if (r && r.lock && r.lock.pc !== hub.status().pc) { p.runningOn = r.lock.pc; } }
  const only = remote.filter(p => !have.has(p.id)).map(p => ({ id: p.id, title: p.title, status: p.lock ? 'running' : (p.status === 'running' ? 'stopped' : p.status),
    created: p.created, updated: p.updated, where: 'hub', size: p.size, changedBy: p.changedBy, runningOn: p.lock ? p.lock.pc : null }));
  return local.concat(only).sort((a, b) => (b.updated || '').localeCompare(a.updated || ''));
}

// ---------------------------------------------------------------- project apps (the "experience" of a finished project)
// A project declares runnable apps in anatomy.json: { apps: [{ name, description, cwd, run: [cmd, ...], url }] }.
const apps = new Map(); // `${id}/${n}` -> { procs, log }
function findManifest(dir) {
  const hits = [];
  (function walk(rel, depth) {
    if (depth > 4) return;
    let ents = []; try { ents = fs.readdirSync(path.join(dir, rel), { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      if (HIDDEN.has(e.name) || e.name === 'node_modules' || e.name.startsWith('.')) continue;
      const r = rel ? rel + '/' + e.name : e.name;
      if (e.isFile() && e.name === 'anatomy.json') hits.push(r);
      else if (e.isDirectory()) walk(r, depth + 1);
    }
  })('', 0);
  hits.sort((a, b) => a.split('/').length - b.split('/').length);
  if (!hits.length) return null;
  try { const m = readJson(path.join(dir, hits[0])); m._base = path.posix.dirname(hits[0]) === '.' ? '' : path.posix.dirname(hits[0]); return m; } catch (e) { return { error: 'anatomy.json is not valid JSON: ' + e.message, _base: '' }; }
}
function projectPython(dir) {
  for (const p of [path.join(dir, '.venv', 'Scripts', 'python.exe'), path.join(dir, '.venv', 'bin', 'python')]) if (fs.existsSync(p)) return p;
  return null;
}
// ---------------------------------------------------------------- stale app servers on the app's port
// Project app servers are started through a shell, so they can outlive the Anatomy server (an app restart, a crash).
// "Open" then started a fresh copy that could not take the port, and the window showed the old server's code
// (a twin from before its last fix, failing with "Script error."). Before starting, look at who holds the port:
//   nobody                                   -> start as usual
//   this project's server, newer than files  -> reuse it
//   this project's server, older than files  -> stop it and start fresh, but only when no run is active
//   anything else (another project, a foreign program, or a run is active) -> never kill it: start on a free port when
//     the port is part of the run command, otherwise refuse with a plain message naming the process.
// "This project's server" means: its command line ends with one of the app's run commands, and the page it serves has
// the same <title> as the app's page on disk.
const net = require('net');
function appPortOf(app) {
  try { const u = new URL(app.url); if (/^(127\.0\.0\.1|localhost|\[::1\])$/.test(u.hostname)) return +u.port || 80; } catch {}
  return null;
}
function execOut(cmd, args, timeout = 8000) {
  return new Promise(res => execFile(cmd, args, { windowsHide: true, timeout, maxBuffer: 8 * 1024 * 1024 }, (e, out) => res(e ? '' : String(out))));
}
function portFree(port) {
  return new Promise(res => { const s = net.createServer(); s.once('error', () => res(false)); s.listen(port, '127.0.0.1', () => s.close(() => res(true))); });
}
function freePort() { return new Promise(res => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); }); }
async function portOwner(port) {
  if (process.platform !== 'win32') return null;            // owner lookup is Windows-only; elsewhere only "in use" is known
  const out = await execOut('netstat', ['-ano', '-p', 'TCP']);
  for (const l of out.split(/\r?\n/)) {
    const m = l.trim().split(/\s+/);
    if (m.length >= 5 && /LISTEN/i.test(m[3]) && new RegExp(`:${port}$`).test(m[1])) return +m[4];
  }
  return null;
}
async function procInfo(pid) {
  const out = await execOut('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
    `$p = Get-CimInstance Win32_Process -Filter "ProcessId=${Number(pid)}"; if ($p) { [pscustomobject]@{ cmd = $p.CommandLine; started = $p.CreationDate.ToUniversalTime().ToString('o') } | ConvertTo-Json -Compress }`]);
  try { return JSON.parse(out); } catch { return null; }
}
const cmdTail = s => String(s || '').replace(/"/g, '').trim().split(/\s+/).slice(1).join(' ').toLowerCase();
function newestFile(dir, depth = 0) {
  let t = 0; let es = []; try { es = fs.readdirSync(dir, { withFileTypes: true }); } catch { return 0; }
  for (const e of es) {
    if (/^(node_modules|\.venv|venv|__pycache__|results|screenshots|screens|data|\.git|\.pio)$/i.test(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (depth < 4) t = Math.max(t, newestFile(p, depth + 1)); }
    else if (/\.(js|mjs|html|css|py|json)$/i.test(e.name)) { try { t = Math.max(t, fs.statSync(p).mtimeMs); } catch {} }
  }
  return t;
}
function pageTitles(cwd) {
  const titles = new Set();
  const look = (d, depth) => { let es = []; try { es = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of es) { const p = path.join(d, e.name);
      if (e.isDirectory()) { if (depth < 3 && !/^(node_modules|\.venv|vendor|results)$/i.test(e.name)) look(p, depth + 1); }
      else if (/\.html?$/i.test(e.name)) { try { const m = fs.readFileSync(p, 'utf8').match(/<title>([^<]*)<\/title>/i); if (m) titles.add(m[1].trim()); } catch {} } } };
  look(cwd, 0); return titles;
}
function servedTitle(url) {
  return new Promise(res => {
    const rq = http.get(url, { timeout: 2500 }, r => {
      if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location) { r.resume(); return servedTitle(new URL(r.headers.location, url).href).then(res); }
      let b = ''; r.setEncoding('utf8'); r.on('data', d => { if (b.length < 65536) b += d; }); r.on('end', () => { const m = b.match(/<title>([^<]*)<\/title>/i); res(m ? m[1].trim() : null); });
    });
    rq.on('timeout', () => rq.destroy()); rq.on('error', () => res(null));
  });
}
function killTree(pid) { return new Promise(res => execFile('taskkill', ['/pid', String(pid), '/T', '/F'], { windowsHide: true }, () => res())); }

async function preparePort(id, app, cwd) {
  const port = appPortOf(app); if (!port || await portFree(port)) return {};
  const pid = await portOwner(port), info = pid ? await procInfo(pid) : null;
  const sameCmd = !!info && (app.run || []).some(c => cmdTail(c) && cmdTail(info.cmd).endsWith(cmdTail(c)));
  const sameTitle = sameCmd && pageTitles(cwd).has(await servedTitle(app.url) || '\0');
  const who = info ? `${String(info.cmd || '').slice(0, 120)} (process ${pid})` : (pid ? `process ${pid}` : 'another program');
  if (sameCmd && sameTitle) {
    const started = Date.parse(info.started) || 0;
    if (started >= newestFile(cwd)) return { reuse: true, note: `Already running (process ${pid}) with the current files; reusing it.` };
    if (!runs.get(id)?.proc) {
      await killTree(pid);
      for (let i = 0; i < 25 && !(await portFree(port)); i++) await new Promise(r => setTimeout(r, 200));
      if (await portFree(port)) return { note: `Restarted: an older copy of this simulator (process ${pid}, started ${new Date(started).toLocaleString()}) was still running from before its files changed.` };
    }
  }
  // not ours to stop: move to a free port when the run command names the port
  const re = new RegExp(`\\b${port}\\b`);
  if ((app.run || []).some(c => re.test(c))) {
    const np = await freePort(), g = new RegExp(`\\b${port}\\b`, 'g');
    return { run: app.run.map(c => c.replace(g, String(np))), url: app.url.replace(`:${port}`, `:${np}`),
      note: `Port ${port} is in use by ${who}, so this started on port ${np} instead.` };
  }
  throw new Error(`Port ${port} is already in use by ${who}, and this app's port is fixed in its code. Close that program (or restart Anatomy if it is an older copy of this simulator), then try again.`);
}

async function startApp(id, n) {
  const dir = projectDir(id);
  const m = findManifest(dir); const app = m && m.apps && m.apps[n];
  if (!app) throw new Error('no such app');
  const key = `${id}/${n}`;
  const cwd = safeJoin(dir, path.posix.join(m._base || '', app.cwd || '.'));
  const mine = apps.get(key);                                       // started by us and still up: reuse it unless its files changed since
  if (mine && mine.procs.some(p => p.exitCode === null) && (mine.started || 0) >= newestFile(cwd)) return { url: mine.url || app.url, note: null, reused: true };
  const had = !!mine;
  stopApp(key);
  const port0 = appPortOf(app);                                     // our own copy may need a moment to let go of the port
  if (had && port0) for (let i = 0; i < 40 && !(await portFree(port0)); i++) await new Promise(r => setTimeout(r, 200));
  const prep = await preparePort(id, app, cwd);
  if (prep.reuse) { apps.set(key, { procs: [], log: prep.note + '\n', url: app.url }); return { url: app.url, note: prep.note, reused: true }; }
  const env = cleanEnv();
  const py = projectPython(dir);
  if (py) env.PATH = path.dirname(py) + path.delimiter + env.PATH;   // use the project's own venv first
  const st = { procs: [], log: prep.note ? prep.note + '\n' : '', url: prep.url || app.url, started: Date.now() };
  for (const cmd of prep.run || app.run || []) {
    const p = spawn(cmd, { cwd, env, shell: true, windowsHide: true });
    const add = d => { st.log = (st.log + d.toString('utf8')).slice(-20000); };
    p.stdout.on('data', add); p.stderr.on('data', add);
    p.on('close', c => add(`\n[${cmd}] exited with code ${c}\n`));
    st.procs.push(p);
  }
  apps.set(key, st);
  return { url: st.url, note: prep.note || null };
}
function stopApp(key) {
  const st = apps.get(key); if (!st) return;
  for (const p of st.procs) {
    if (p.exitCode !== null) continue;
    if (process.platform === 'win32') execFile('taskkill', ['/pid', String(p.pid), '/T', '/F'], () => {});
    else p.kill('SIGTERM');
  }
  apps.delete(key);
}
function openWithDefault(p) {
  if (process.platform === 'win32') spawn('cmd.exe', ['/c', 'start', '""', p], { detached: true, windowsHide: true });
  else spawn('xdg-open', [p], { detached: true });
}

// ---------------------------------------------------------------- routes
// Serve a file without ever crashing the server: folders and missing files get 404,
// a file another program has locked gets 500.
function streamFile(res, p, cache) {
  let st; try { st = fs.statSync(p); } catch { return send(res, 404, { error: 'not found' }); }
  if (!st.isFile()) return send(res, 404, { error: 'not found' });
  const rs = fs.createReadStream(p);
  rs.on('error', e => { if (!res.headersSent) send(res, 500, { error: 'could not read file: ' + e.code }); else res.destroy(); });
  rs.once('open', () => { res.writeHead(200, { 'Content-Type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Cache-Control': cache }); rs.pipe(res); });
}

// Last-resort guard: log anything unexpected and keep the app up.
const ERR_LOG = path.join(__dirname, 'server.err.log');
for (const ev of ['uncaughtException', 'unhandledRejection']) {
  process.on(ev, e => { try { fs.appendFileSync(ERR_LOG, `${new Date().toISOString()} ${ev}: ${(e && e.stack) || e}\n`); } catch {} });
}

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
    if (req.method === 'GET' && (parts[0] === 'vendor' || parts[0] === 'results.js' || parts[0] === 'xometry.js' || parts[0] === 'viewer.html')) {
      const p = safeJoin(PUBLIC, decodeURIComponent(url.pathname.slice(1)));
      return streamFile(res, p, parts[0] === 'vendor' ? 'max-age=3600' : 'no-store');
    }
    // Raw project files at a stable URL, so HTML outputs (assembly guide, viewers) load their relative assets.
    if (req.method === 'GET' && parts[0] === 'p' && parts[1]) {
      const dir = projectDir(parts[1]);
      const rel = decodeURIComponent(parts.slice(2).join('/'));
      let p = safeJoin(dir, rel);
      if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
      return streamFile(res, p, 'no-store');
    }
    if (parts[0] !== 'api') return send(res, 404, { error: 'not found' });

    if (parts[1] === 'health') return send(res, 200, { ok: true, app: 'anatomy', root: ROOT, claude: !!findClaude(), kicad: findKiCadBin() });

    if (parts[1] === 'hub') {
      if (!parts[2] && req.method === 'GET') return send(res, 200, hub.status());
      if (!parts[2] && req.method === 'PUT') {
        const b = JSON.parse((await readBody(req, 64 * 1024)).toString('utf8') || '{}');
        if (b.disconnect) { hub.saveConfig({ url: '', token: '' }); return send(res, 200, hub.status()); }
        const cur = hub.config() || {};
        const url = String(b.url || cur.url || '').trim(), token = String(b.token || cur.token || '').trim();
        if (!/^https?:\/\//.test(url) || !token) return send(res, 400, { error: 'Enter the hub address (https://...) and its access key.' });
        const t = await hub.test(url, token);
        if (!t.ok) return send(res, 400, { error: 'Could not reach the hub: ' + t.error });
        hub.saveConfig({ url, token, pc: String(b.pc || cur.pc || os.hostname()).trim().slice(0, 60), pullAll: !!b.pullAll });
        hub.syncAll().catch(() => {});
        return send(res, 200, hub.status());
      }
      if (parts[2] === 'sync' && req.method === 'POST') { hub.syncAll().catch(() => {}); return send(res, 200, hub.status()); }
      // Download a project that so far lives only on the hub, so it can be opened here.
      if (parts[2] === 'fetch' && parts[3] && req.method === 'POST') {
        projectDir(parts[3]);
        const r = await hub.syncProject(parts[3], { pullOnly: true });
        return send(res, readMeta(parts[3]) ? 200 : 502, readMeta(parts[3]) ? { ok: true, ...r } : { error: (r.errors || ['download failed']).join('; ') });
      }
    }

    if (parts[1] === 'projects' && parts.length === 2) {
      if (req.method === 'GET') return send(res, 200, listAllProjects());
      if (req.method === 'POST') {
        const { prompt, model } = JSON.parse((await readBody(req)).toString('utf8') || '{}');
        if (!prompt || !prompt.trim()) return send(res, 400, { error: 'prompt required' });
        const base = slugify(prompt.split(/\s+/).slice(0, 6).join(' '));
        let id = base, n = 2;
        const taken = new Set(hub.remoteProjects().map(p => p.id));
        while (fs.existsSync(path.join(ROOT, id)) || taken.has(id)) id = `${base}-${n++}`;
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
        if (runs.get(id)?.proc) return send(res, 409, { error: 'already running' });
        // Pull the latest copy from the hub and claim the project, so two PCs never run it at the same time.
        if (hub.config()) {
          const l = await hub.lock(id);
          if (!l.ok) return send(res, 409, { error: `This project is running on ${l.by || 'another PC'} right now. Wait for it to finish there.` });
          await hub.syncProject(id).catch(() => {});
        }
        try { startRun(id, text, message && message.trim() ? message.trim() : meta.prompt); } catch (e) { hub.unlock(id); return send(res, 409, { error: e.message }); }
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
      if (action === 'meshes' && req.method === 'GET') return send(res, 200, listMeshes(dir));
      if (action === 'file' && req.method === 'GET') {
        const p = safeJoin(dir, url.searchParams.get('path'));
        const ext = path.extname(p).toLowerCase();
        const st = fs.statSync(p);
        if (st.size > 50 * 1024 * 1024) return send(res, 413, { error: 'file too large to preview' });
        return send(res, 200, fs.readFileSync(p), MIME[ext] || 'text/plain; charset=utf-8');
      }
      if (action === 'build-state') {
        const f = path.join(dir, META_DIR, 'build-state.json');
        if (req.method === 'GET') { try { return send(res, 200, readJson(f)); } catch { return send(res, 200, {}); } }
        if (req.method === 'PUT') { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, (await readBody(req, 1024 * 1024)).toString('utf8')); return send(res, 200, { ok: true }); }
      }
      if (action === 'build' && req.method === 'GET') {
        // build/build.json anywhere in the project (shallowest wins)
        const hits = fs.existsSync(path.join(dir, 'build', 'build.json')) ? [{ path: 'build/build.json' }]
          : listFiles(dir).filter(f => /(^|\/)build\/build\.json$/.test(f.path)).sort((a, b) => a.path.length - b.path.length);
        if (!hits.length) return send(res, 200, {});
        try { const j = readJson(path.join(dir, hits[0].path)); j._file = hits[0].path; return send(res, 200, j); }
        catch (e) { return send(res, 200, { error: `${hits[0].path} is not valid JSON: ${e.message}` }); }
      }
      if (action === 'xometry') {
        // Parts routed to Xometry (oversized, other materials, machined/cut metal, or moved by hand). Never contacts Xometry.
        const bf = fs.existsSync(path.join(dir, 'build', 'build.json')) ? 'build/build.json'
          : (listFiles(dir).filter(f => /(^|\/)build\/build\.json$/.test(f.path)).sort((a, b) => a.path.length - b.path.length)[0] || {}).path;
        if (!bf) return send(res, 200, { parts: [] });
        try {
          if (req.method === 'GET') return send(res, 200, xometry.routing(dir, bf, readSettings(), listFiles));
          if (req.method === 'PUT') { xometry.savePrefs(dir, bf, JSON.parse((await readBody(req, 1024 * 1024)).toString('utf8') || '{}')); return send(res, 200, xometry.routing(dir, bf, readSettings(), listFiles)); }
          if (req.method === 'POST' && parts[4] === 'package') return send(res, 200, xometry.preparePackage(dir, bf, readSettings(), listFiles));
        } catch (e) { return send(res, 200, { parts: [], error: e.message }); }
      }
      if (action === 'simtest' && req.method === 'POST') {
        // Run the simulator's headless tests (anatomy.json "tests": {cwd, run, results}) and return the output.
        const m = findManifest(dir); const t = m && m.tests;
        if (!t || !t.run) return send(res, 400, { error: 'anatomy.json has no "tests" entry' });
        const cwd = safeJoin(dir, path.posix.join(m._base || '', t.cwd || '.'));
        const env = cleanEnv(); const py = projectPython(dir); if (py) env.PATH = path.dirname(py) + path.delimiter + env.PATH;
        const cmd = Array.isArray(t.run) ? t.run.join(' && ') : t.run;
        let log = '';
        const p = spawn(cmd, { cwd, env, shell: true, windowsHide: true });
        p.stdout.on('data', d => { log = (log + d).slice(-40000); }); p.stderr.on('data', d => { log = (log + d).slice(-40000); });
        const killer = setTimeout(() => { log += '\n[stopped after 10 minutes]'; if (process.platform === 'win32') execFile('taskkill', ['/pid', String(p.pid), '/T', '/F'], () => {}); else p.kill('SIGTERM'); }, 600000);
        p.on('close', code => { clearTimeout(killer); send(res, 200, { code, log, results: t.results ? path.posix.join(m._base || '', t.results) : null }); });
        p.on('error', e => { clearTimeout(killer); send(res, 200, { code: -1, log: e.message }); });
        return;
      }
      if (action === 'manifest' && req.method === 'GET') {
        const m = findManifest(dir);
        if (m && m.apps) m.apps = m.apps.map((a, n) => { const st = apps.get(`${id}/${n}`); return { ...a, running: !!st, ...(st && st.url ? { url: st.url } : {}) }; });
        return send(res, 200, m || {});
      }
      if (action === 'apps' && parts[4] !== undefined) {
        const n = Number(parts[4]); const key = `${id}/${n}`;
        if (parts[5] === 'start' && req.method === 'POST') { let r; try { r = await startApp(id, n); } catch (e) { return send(res, 400, { error: e.message }); } return send(res, 200, { ok: true, ...r }); }
        if (parts[5] === 'stop' && req.method === 'POST') { stopApp(key); return send(res, 200, { ok: true }); }
        if (parts[5] === 'log' && req.method === 'GET') { const st = apps.get(key); return send(res, 200, { running: !!st, log: st ? st.log : '' }); }
      }
      if (action === 'open' && req.method === 'POST') {
        openWithDefault(safeJoin(dir, url.searchParams.get('path') || '.'));
        return send(res, 200, { ok: true });
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
      for (const k of [...apps.keys()]) stopApp(k);
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
