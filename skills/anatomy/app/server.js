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
    'Never open a window on the user\'s desktop. Run every tool headless: kicad-cli and KiCad\'s python.exe (pcbnew) only, never kicad.exe, pcbnew.exe or eeschema.exe; Freerouting 2.x with --gui.enabled=false, never Freerouting 1.x (it always opens a window); Blender with -b; browsers with --headless; slicers and CAD in CLI mode. Never open files with start, explorer, Invoke-Item or os.startfile. The user opens files from the app.',
    'Hardware standards are mandatory: every part is BUY or BUILD (references/parts-and-bom.md, run the BOM check), industrial design and visual fidelity (references/industrial-design.md: no plain boxes, fillets and curved styled surfaces on every BUILD part, real manufacturer shapes for BUY parts, materials in assembly.json, tight tessellation, photoreal renders), precision engineering (references/precision-engineering.md: Blender and meshes are looks only; every BUILD part is feature-based build123d CAD exported as STEP with real holes, fillets, material, process and DFM; precision parts add datums, ISO 286 fits, GD&T and finish; structural parts add load cases and an FEA margin; bought parts use the vendor STEP; every part is graded Concept/Engineered/Verified in prototype/mechanical/engineering.json and checked with tools/eng/check_engineering.py), production-quality drawings (references/drawings.md), and every 3D printed part ends in verified G-code for the user\'s printer (references/3d-print-gcode.md). If the product runs any code, firmware/BIOS/software is a full development phase (references/software-phase.md).',
    'The user\'s settings (printer, materials, suppliers, tools) follow. Use them; if the printer is not filled in, use a stated default profile and say the G-code must be re-sliced.\n<user-settings>\n' + readSettings() + '\n</user-settings>',
    'At the end, print a short summary: what you built, where the key files are, what was verified, and what is still unverified.',
  ].join('\n');
}

// Claude runs are unattended: keep Java tools (Freerouting) from opening windows on the desktop.
// Only for runs; apps the user starts from the Simulate tab may be real GUIs.
function runEnv() {
  const env = cleanEnv();
  if (!/java\.awt\.headless/.test(env.JAVA_TOOL_OPTIONS || '')) env.JAVA_TOOL_OPTIONS = ((env.JAVA_TOOL_OPTIONS || '') + ' -Djava.awt.headless=true').trim();
  return env;
}

function cleanEnv() {
  const env = { ...process.env };
  for (const k of Object.keys(env)) {
    // Markers inherited when the server was started from inside another Claude session.
    if (k === 'CLAUDECODE' || k.startsWith('CLAUDE_CODE_') || k === 'ANTHROPIC_BASE_URL') delete env[k];
  }
  const extra = [], tail = [];
  if (process.platform === 'win32') {
    const prusa = path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Prusa3D', 'PrusaSlicer');
    if (fs.existsSync(prusa)) extra.push(prusa);
    else {
      // Portable PrusaSlicer unpacked under <root>\_tools\PrusaSlicer\PrusaSlicer-x.y.z (no admin rights needed).
      const pr = path.join(ROOT, '_tools', 'PrusaSlicer');
      let ds = []; try { ds = fs.readdirSync(pr).filter(n => /^PrusaSlicer/i.test(n)).sort().reverse(); } catch {}
      const hit = ds.map(n => path.join(pr, n)).find(d => fs.existsSync(path.join(d, 'prusa-slicer-console.exe')));
      if (hit) extra.push(hit);
    }
    for (const b of [process.env.ProgramFiles, process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs')].filter(Boolean)) {
      let ds = []; try { ds = fs.readdirSync(b).filter(n => /^FreeCAD/i.test(n)); } catch {}
      // FreeCAD's bin holds its own python.exe: put it after PATH so it never shadows the system Python.
      for (const n of ds) { const bin = path.join(b, n, 'bin'); if (fs.existsSync(bin)) tail.push(bin); }
    }
  }
    if (process.env.APPDATA) {
      let pys = []; try { pys = fs.readdirSync(path.join(process.env.APPDATA, 'Python')); } catch {}
      for (const v of pys) { const sc = path.join(process.env.APPDATA, 'Python', v, 'Scripts'); if (fs.existsSync(path.join(sc, 'pio.exe'))) extra.push(sc); }
    }
  // The Node.js running this server, so project apps whose run command is `node ...` work even when the
  // launcher started us with a PATH that has no Node.js on it.
  extra.unshift(path.dirname(process.execPath));
  if (extra.length) env.PATH = extra.join(path.delimiter) + path.delimiter + (env.PATH || '');
  if (tail.length) env.PATH = (env.PATH || '') + path.delimiter + tail.join(path.delimiter);
  const kicad = findKiCadBin();
  // KiCad last, so its bundled Python does not shadow the system Python for venvs.
  if (kicad) env.PATH = (env.PATH || '') + path.delimiter + kicad;
  return env;
}

// Reference files the app's own features rely on (Design Studio revisions, industrial-design standard). Keep the
// installed skill's copies current, so runs can read them even when the skill was installed before these existed.
(function syncSkillRefs() {
  const skill = path.join(os.homedir(), '.claude', 'skills', 'anatomy');
  const dst = path.join(skill, 'references');
  if (!fs.existsSync(dst)) return;
  const put = (from, to) => { try { const t = fs.readFileSync(from, 'utf8'); let cur = ''; try { cur = fs.readFileSync(to, 'utf8'); } catch {} if (cur !== t) { fs.mkdirSync(path.dirname(to), { recursive: true }); fs.writeFileSync(to, t); } } catch {} };
  for (const src of [path.join(__dirname, 'skill-refs'), path.join(__dirname, '..', 'references')])
    for (const f of ['industrial-design.md', 'design-revisions.md', 'precision-engineering.md']) put(path.join(src, f), path.join(dst, f));
  // The grade checker and STEP feature scanner the precision-engineering standard tells runs to use.
  for (const src of [path.join(__dirname, 'eng-tools'), path.join(__dirname, '..', 'tools', 'eng')])
    for (const f of ['check_engineering.py', 'step_features.py']) put(path.join(src, f), path.join(skill, 'tools', 'eng', f));
})();

const ALLOWED_TOOLS = ['Bash', 'Read', 'Write', 'Edit', 'MultiEdit', 'Glob', 'Grep', 'WebFetch', 'WebSearch',
  'Skill', 'TodoWrite', 'Task', 'NotebookEdit'];

const models = require('./models');
const design = require('./design');

// opts.model: run on this model (set when falling back); opts.tried: models already tried in this run;
// opts.auto: started by the server itself, so no "You" bubble.
function startRun(id, message, display, opts = {}) {
  if (runs.get(id)?.proc) throw new Error('already running');
  const meta = readMeta(id);
  const tried = opts.tried || [];
  const model = opts.model || models.pickModel(ROOT, meta.model, tried);
  const claude = findClaude();
  if (!claude) {
    emit(id, { type: 'anatomy', kind: 'error', text: 'Claude Code was not found on this PC. Install it from https://claude.com/claude-code and try again.' });
    return;
  }
  // stream-json input keeps stdin open, so the user can steer the run while it works (see steerRun).
  const args = ['-p', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
    '--permission-mode', 'acceptEdits',
    '--allowedTools', ALLOWED_TOOLS.join(','),
    '--append-system-prompt', systemAppend()];
  const skillDir = path.join(os.homedir(), '.claude', 'skills', 'anatomy');
  if (fs.existsSync(skillDir)) args.push('--add-dir', skillDir);
  if (model) args.push('--model', models.cliModel(model));
  if (meta.sessionId) args.push('--resume', meta.sessionId);

  const isCmd = claude.toLowerCase().endsWith('.cmd');
  const proc = spawn(isCmd ? `"${claude}"` : claude, isCmd ? args.map(a => `"${a.replace(/"/g, '\\"')}"`) : args, {
    cwd: projectDir(id), env: models.isLocal(model) ? models.applyLocalEnv(runEnv(), model) : runEnv(), windowsHide: true, shell: isCmd,
  });
  const r = runs.get(id) || { clients: new Set() };
  r.proc = proc; runs.set(id, r);

  meta.currentModel = model; meta.status = 'running'; meta.updated = new Date().toISOString(); writeMeta(id, meta);
  emit(id, { type: 'anatomy', kind: 'run-start', text: display || message, model, auto: !!opts.auto });

  r.stdinOpen = true; r.lastWrite = Date.now(); r.idleTimer = null;
  proc.stdin.on('error', () => { r.stdinOpen = false; });
  proc.stdin.write(userLine(message));
  // Claude Code waits for more input until stdin closes. Close it once a result has come in and
  // nothing else happened for a moment (no new turn started, no message from the user).
  r.finishSoon = () => {
    clearTimeout(r.idleTimer);
    const at = Date.now();
    r.idleTimer = setTimeout(() => { if (r.proc === proc && r.stdinOpen && r.lastWrite <= at && r.lastEvent <= at) { r.stdinOpen = false; try { proc.stdin.end(); } catch {} } }, 2500);
  };

  let buf = '';
  proc.stdout.on('data', d => {
    buf += d.toString('utf8');
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
      if (!line) continue;
      let ev; try { ev = JSON.parse(line); } catch { emit(id, { type: 'anatomy', kind: 'log', text: line }); continue; }
      if (ev.session_id && ev.session_id !== meta.sessionId) { meta.sessionId = ev.session_id; writeMeta(id, meta); }
      r.lastEvent = Date.now();
      if (ev.type === 'result') r.finishSoon(); else if (ev.type !== 'rate_limit_event') clearTimeout(r.idleTimer);
      watch.see(ev);
      emit(id, ev);
    }
  });
  let errTail = '';
  const watch = new models.RunWatch();
  proc.stderr.on('data', d => { errTail = (errTail + d.toString('utf8')).slice(-4000); });
  proc.on('error', e => emit(id, { type: 'anatomy', kind: 'error', text: 'Could not start Claude Code: ' + e.message }));
  proc.on('close', code => {
    const m = readMeta(id) || meta;
    // Settings > Models > "Switch now": the run was stopped on purpose, resume on the chosen model.
    if (r.switchTo) {
      const to = r.switchTo; r.switchTo = null; r.proc = null; r.stopping = false;
      emit(id, { type: 'anatomy', kind: 'notice', text: `Switched from ${models.label(model)} to ${models.label(to)} as you asked. Carrying on where it stopped.` });
      try { return startRun(id, models.continuePrompt(model, to, 'You asked to switch models'), '', { model: to, tried: [], auto: true }); }
      catch (e) { /* fall through */ }
    }
    const stopped = r.stopping;
    const failed = !stopped && (code !== 0 || !!watch.resultErr);
    // The reason is usually in the last result event (usage limit, API error), not on stderr.
    const kind = failed ? watch.kind(errTail) : '';
    const triedNow = [...tried, model].filter(Boolean);
    if (!failed && model) models.markOk(ROOT, model);
    // 'plan': the whole Claude plan is at its limit, so only a local model (if turned on in Settings) can carry on.
    if ((kind === 'model' || kind === 'plan') && model) {
      models.markUnavailable(ROOT, model, kind === 'plan' ? 'plan limit reached' : (watch.apiError || 'unavailable'), watch.resetsAt);
      const cand = models.pickModel(ROOT, m.model, triedNow);
      const next = kind === 'plan' ? models.chainFor(m.model, ROOT).find(x => models.isLocal(x) && !triedNow.includes(x)) : cand;
      if (next && !triedNow.includes(next)) {
        emit(id, { type: 'anatomy', kind: 'notice', text: `${models.reasonText(kind, model)}, so Anatomy switched to ${models.label(next)} and is carrying on.` });
        r.proc = null; r.stopping = false;
        try { return startRun(id, models.continuePrompt(model, next), '', { model: next, tried: triedNow, auto: true }); }
        catch (e) { /* fall through to the normal failure path */ }
      }
    }
    m.status = stopped ? 'stopped' : (failed ? 'failed' : 'done');
    m.updated = new Date().toISOString(); writeMeta(id, m);
    if (failed) {
      const details = [watch.resultErr, errTail.trim()].filter(Boolean).join('\n\n') || `Claude Code exited with code ${code}.`;
      emit(id, { type: 'anatomy', kind: 'error', text: models.friendlyError(kind, watch, triedNow), details });
    }
    r.proc = null; r.stopping = false; r.stdinOpen = false; clearTimeout(r.idleTimer);
    // A message sent just as the run was wrapping up: carry on with it instead of dropping it.
    if (r.pending && r.pending.length && !stopped) {
      const msgs = r.pending.splice(0);
      try { return startRun(id, msgs.join('\n\n'), '', { auto: true }); } catch {}
    }
    emit(id, { type: 'anatomy', kind: 'run-end', status: m.status });
    // The run is really over (not handed to a fallback model or a queued message): push it to the hub and release the lock.
    if (hub.config()) hub.syncProject(id).catch(() => {}).finally(() => hub.unlock(id));
  });
}

function userLine(text) {
  return JSON.stringify({ type: 'user', message: { role: 'user', content: [{ type: 'text', text }] } }) + '\n';
}

// A message from the user while the run is working. It goes straight into the running session;
// Claude Code picks it up at its next step. If the run is already closing, it starts the next run.
function steerRun(id, text, display) {
  const r = runs.get(id);
  if (!r || !r.proc) return false;
  const msg = 'Message from the user while you are working. Take it into account now: adjust the plan if it changes anything, ' +
    'answer any question in a short reply, then carry on with the run.\n\n' + text;
  emit(id, { type: 'anatomy', kind: 'steer', text: display || text });
  if (r.stdinOpen) {
    clearTimeout(r.idleTimer); r.lastWrite = Date.now();
    try { r.proc.stdin.write(userLine(msg)); return true; } catch {}
  }
  (r.pending = r.pending || []).push(msg);
  return true;
}

function stopRun(id) {
  const r = runs.get(id);
  if (!r?.proc) return;
  r.stopping = true; r.pending = [];
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
function startApp(id, n) {
  const dir = projectDir(id);
  const m = findManifest(dir); const app = m && m.apps && m.apps[n];
  if (!app) throw new Error('no such app');
  const key = `${id}/${n}`;
  stopApp(key);
  const cwd = safeJoin(dir, path.posix.join(m._base || '', app.cwd || '.'));
  const env = cleanEnv();
  const py = projectPython(dir);
  if (py) env.PATH = path.dirname(py) + path.delimiter + env.PATH;   // use the project's own venv first
  const st = { procs: [], log: '' };
  for (const cmd of app.run || []) {
    const p = spawn(cmd, { cwd, env, shell: true, windowsHide: true });
    const add = d => { st.log = (st.log + d.toString('utf8')).slice(-20000); };
    p.stdout.on('data', add); p.stderr.on('data', add);
    p.on('close', c => add(`\n[${cmd}] exited with code ${c}\n`));
    st.procs.push(p);
  }
  apps.set(key, st);
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
  if (process.platform === 'win32') spawn('cmd.exe', ['/c', 'start', '""', `"${p}"`], { detached: true, windowsHide: true, windowsVerbatimArguments: true });
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
    if (req.method === 'GET' && (parts[0] === 'vendor' || parts[0] === 'results.js' || parts[0] === 'xometry.js' || parts[0] === 'viewer.html' || parts[0] === 'editor.html')) {
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
        if (runs.get(id)?.proc && message && message.trim()) { steerRun(id, text, message.trim()); return send(res, 200, { ok: true, steered: true }); }
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
      if (action === 'switch' && req.method === 'POST') {
        const { model } = JSON.parse((await readBody(req)).toString('utf8') || '{}');
        if (!model) return send(res, 400, { error: 'model required' });
        models.clearSkip(ROOT, model);
        const r = runs.get(id);
        if (r?.proc) { r.switchTo = model; stopRun(id); return send(res, 200, { ok: true, switching: true }); }
        meta.model = model; writeMeta(id, meta);
        return send(res, 200, { ok: true, switching: false });
      }

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
      // Design Studio: the 3D design editor (editor.html). See design.js.
      if (action === 'design') {
        const sub = parts[4];
        if (!sub && req.method === 'GET') return send(res, 200, { id, title: meta.title, revision: meta.revision || null, revisionOf: meta.revisionOf || null, running: !!runs.get(id)?.proc, ...design.info(dir) });
        if (sub === 'edits' && req.method === 'PUT') return send(res, 200, design.saveEdits(dir, JSON.parse((await readBody(req, 20 * 1024 * 1024)).toString('utf8') || '{}')));
        if (sub === 'scene' && req.method === 'PUT') { // the edited scene as GLB, for Blender
          const dd = design.designDir(dir); fs.mkdirSync(dd, { recursive: true });
          fs.writeFileSync(path.join(dd, 'scene.glb'), await readBody(req, 1024 * 1024 * 1024));
          return send(res, 200, { ok: true });
        }
        if (sub === 'sculpt' && req.method === 'GET') { // a mesh sculpted in Blender, written by the save hook
          const name = path.basename(url.searchParams.get('file') || '');
          return streamFile(res, path.join(design.designDir(dir), 'sculpt', name), 'no-store');
        }
        if (sub === 'blender' && req.method === 'POST') {
          const b = JSON.parse((await readBody(req, 64 * 1024)).toString('utf8') || '{}');
          try { return send(res, 200, design.runBlender(dir, b.mode === 'render' ? 'render' : 'open', b, cleanEnv)); }
          catch (e) { return send(res, 400, { error: e.message }); }
        }
        if (sub === 'blender' && req.method === 'GET') return send(res, 200, design.blenderStatus(dir));
        if (sub === 'features' && req.method === 'GET') {
          try { return send(res, 200, await design.stepFeatures(dir, ROOT, url.searchParams.get('step') || '', cleanEnv)); }
          catch (e) { return send(res, 400, { error: e.message }); }
        }
        if (sub === 'grade' && req.method === 'POST') {
          try { return send(res, 200, await design.gradeCheck(dir, ROOT, cleanEnv)); }
          catch (e) { return send(res, 400, { error: e.message }); }
        }
        if (sub === 'revision' && req.method === 'POST') {
          // Rebuild: a NEW project (rev B, C, ...) copied from this one, regenerated by the skill from the edits.
          // The completed version is never changed.
          const b = JSON.parse((await readBody(req, 60 * 1024 * 1024)).toString('utf8') || '{}');
          const edits = b.edits || design.loadEdits(dir);
          if (!edits) return send(res, 400, { error: 'No edits to rebuild from.' });
          design.saveEdits(dir, edits);
          const rootId = meta.revisionRoot || id;
          const L = design.nextRevision(listProjects, rootId);
          const baseId = slugify(rootId).slice(0, 32).replace(/-+$/, '');
          let nid = `${baseId}-rev-${L.toLowerCase()}`, k = 2;
          const taken = new Set(hub.remoteProjects().map(p => p.id));
          while (fs.existsSync(path.join(ROOT, nid)) || taken.has(nid)) nid = `${baseId}-rev-${L.toLowerCase()}${k++}`;
          const ndir = path.join(ROOT, nid);
          fs.mkdirSync(path.join(ndir, 'inputs'), { recursive: true });
          const rootTitle = (readMeta(rootId) || meta).title || meta.title || id;
          const title = `${String(rootTitle).replace(/\s*·\s*rev [A-Z]+$/, '')} · rev ${L}`;
          const md = design.editsMarkdown(meta, id, edits);
          const brief = `Revision ${L} of the Anatomy project "${meta.title}" (folder ../${id}), made from the user's edits in the 3D design editor.\n\n` +
            `The edits are in inputs/design-edits.md (readable) and inputs/design-edits.json (exact values)` + (b.snapshot ? ', with a picture of the edited model in inputs/design-edits.png' : '') + '.\n\n' + md;
          writeMeta(nid, { title, prompt: brief, model: meta.model || 'claude-fable-5-2', status: 'new', created: new Date().toISOString(), updated: new Date().toISOString(),
            revisionOf: id, revisionRoot: rootId, revision: L });
          fs.writeFileSync(path.join(ndir, 'inputs', 'design-edits.json'), JSON.stringify({ ...edits, source: id, revision: L }, null, 1));
          fs.writeFileSync(path.join(ndir, 'inputs', 'design-edits.md'), md);
          if (b.snapshot && /^data:image\/png;base64,/.test(b.snapshot)) fs.writeFileSync(path.join(ndir, 'inputs', 'design-edits.png'), Buffer.from(b.snapshot.split(',')[1], 'base64'));
          // Sculpted meshes from Blender travel with the edits.
          const sd = path.join(design.designDir(dir), 'sculpt');
          if (fs.existsSync(sd)) { fs.mkdirSync(path.join(ndir, 'inputs', 'sculpt'), { recursive: true }); for (const f of fs.readdirSync(sd)) try { fs.copyFileSync(path.join(sd, f), path.join(ndir, 'inputs', 'sculpt', f)); } catch {} }
          emit(nid, { type: 'anatomy', kind: 'notice', text: `Revision ${L} of "${meta.title}". Copying the design from the original (the original is not changed)...` });
          send(res, 200, { id: nid, revision: L });
          (async () => {
            const n = await design.copyProject(dir, ndir, c => emit(nid, { type: 'anatomy', kind: 'notice', text: `Copied ${c} files...` }));
            // The copy brought the original's inputs along; keep the edits on top.
            fs.writeFileSync(path.join(ndir, 'inputs', 'design-edits.json'), JSON.stringify({ ...edits, source: id, revision: L }, null, 1));
            fs.writeFileSync(path.join(ndir, 'inputs', 'design-edits.md'), md);
            fs.writeFileSync(path.join(ndir, 'CLAUDE.md'),
              `# Anatomy project: revision ${L}\n\nUse the \`anatomy\` skill for all work in this folder, and follow its references/design-revisions.md.\n\n` +
              `This folder is revision ${L} of \`../${id}\` ("${meta.title}"), copied from it on ${new Date().toISOString().slice(0, 10)} (${n} files). ` +
              `Never write to \`../${id}\` or any other project folder: it is a completed version and must stay exactly as it is. You may run its tools read-only (e.g. its .venv Python or .tools) if that saves time.\n\n` +
              `The user's design edits are in inputs/design-edits.md and inputs/design-edits.json` + (b.snapshot ? ' (picture: inputs/design-edits.png)' : '') + '.\n\nOriginal brief:\n\n' + (meta.prompt || '') + '\n');
            emit(nid, { type: 'anatomy', kind: 'notice', text: `Copied ${n} files. Starting the rebuild.` });
            const msg = `This is revision ${L} of ../${id}. Read CLAUDE.md, inputs/design-edits.md and inputs/design-edits.json, then follow the anatomy skill's references/design-revisions.md: ` +
              `apply every edit to the parametric source in THIS folder, raise the styling and detail as asked, and regenerate everything that depends on the geometry (CAD and STEP, assembly.json and meshes, drawings and cut files, BOM, G-code, assembly guide, build package, renders). Never write to ../${id}.`;
            try { startRun(nid, msg, `Rebuild as revision ${L} from the design editor`); } catch (e) { emit(nid, { type: 'anatomy', kind: 'error', text: e.message }); }
          })().catch(e => emit(nid, { type: 'anatomy', kind: 'error', text: 'Could not copy the design: ' + e.message }));
          return;
        }
      }
      if (action === 'manifest' && req.method === 'GET') {
        const m = findManifest(dir);
        if (m && m.apps) m.apps = m.apps.map((a, n) => ({ ...a, running: !!apps.get(`${id}/${n}`) }));
        return send(res, 200, m || {});
      }
      if (action === 'apps' && parts[4] !== undefined) {
        const n = Number(parts[4]); const key = `${id}/${n}`;
        if (parts[5] === 'start' && req.method === 'POST') { try { startApp(id, n); } catch (e) { return send(res, 400, { error: e.message }); } return send(res, 200, { ok: true }); }
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

    if (parts[1] === 'models') {
      if (req.method === 'GET') {
        const o = await models.overview(ROOT);
        o.running = listProjects().filter(p => runs.get(p.id)?.proc).map(p => ({ id: p.id, title: p.title, model: (readMeta(p.id) || {}).currentModel || null }));
        return send(res, 200, o);
      }
      if (req.method === 'PUT') return send(res, 200, models.writeSettings(ROOT, JSON.parse((await readBody(req)).toString('utf8') || '{}')));
      if (req.method === 'POST' && parts[2] === 'clear') {
        const { model } = JSON.parse((await readBody(req)).toString('utf8') || '{}');
        models.clearSkip(ROOT, model); return send(res, 200, { ok: true });
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
        spawn('cmd.exe', ['/c', 'start', '"Sign in to Claude"', `"${claude}"`, '/login'], { env: cleanEnv(), detached: true, windowsHide: false, windowsVerbatimArguments: true });
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
