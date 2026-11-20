// The full Anatomy console on the web: the same UI as the desktop app (app/public), served read-only from the hub's
// copy of every project. It answers the app's own /api/... calls from the stored files, so the Results view, Build
// wizard, BOM, drawings, 3D viewer, Library, Xometry routing and assembly player all work in any browser.
// Runs, uploads, folder actions and project apps need a PC and answer with a short note instead.
'use strict';

const fs = require('fs');
const path = require('path');

const HIDDEN = new Set(['.anatomy', 'CLAUDE.md', '.tools', 'venv', 'env', '.pio', '.mypy_cache', '.pytest_cache', 'dist-info', '.git', 'node_modules', '.claude', '__pycache__', '.venv']);
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.webp': 'image/webp', '.pdf': 'application/pdf', '.stl': 'model/stl', '.wasm': 'application/wasm',
  '.mjs': 'text/javascript; charset=utf-8', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.obj': 'text/plain; charset=utf-8',
  '.csv': 'text/plain; charset=utf-8', '.py': 'text/plain; charset=utf-8', '.gcode': 'text/plain; charset=utf-8',
};
const READ_ONLY = 'This is the web console. Runs, uploads and folder actions happen in Anatomy on one of your PCs.';

function create({ PROJ, UI, PREFIX, loadIndex, ID_RE }) {
  const BASE = PREFIX + '/console';
  let xometry = null; try { xometry = require(path.join(UI, '..', 'xometry.js')); } catch {}

  const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^﻿/, ''));
  const meta = id => { try { return readJson(path.join(PROJ, id, '.anatomy', 'project.json')); } catch { return null; } };
  const send = (res, code, body, type = 'application/json; charset=utf-8') => {
    res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
  };
  function safeJoin(base, rel) {
    const p = path.resolve(base, rel || '.');
    if (p !== base && !p.startsWith(base + path.sep)) throw Object.assign(new Error('bad path'), { code: 400 });
    return p;
  }
  function stream(res, p) {
    let st; try { st = fs.statSync(p); } catch { return send(res, 404, { error: 'not found' }); }
    if (st.isDirectory()) { p = path.join(p, 'index.html'); try { st = fs.statSync(p); } catch { return send(res, 404, { error: 'not found' }); } }
    if (!st.isFile()) return send(res, 404, { error: 'not found' });
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Content-Length': st.size, 'Cache-Control': 'no-store' });
    fs.createReadStream(p).pipe(res);
  }

  // Files as the app lists them: everything except hidden folders, from the hub's index (no disk walk).
  async function listFiles(id) {
    const idx = await loadIndex(id);
    return Object.entries(idx).filter(([p]) => !p.split('/').some(s => HIDDEN.has(s)))
      .map(([p, v]) => ({ path: p, size: v.size, mtime: v.mtime })).sort((a, b) => a.path.localeCompare(b.path));
  }
  // xometry.js calls listFiles(dir) synchronously, so give it a disk walk of the project.
  function listFilesSync(base, rel = '', out = [], depth = 0) {
    if (depth > 8 || out.length > 5000) return out;
    let ents = []; try { ents = fs.readdirSync(path.join(base, rel), { withFileTypes: true }); } catch { return out; }
    for (const e of ents) {
      if (HIDDEN.has(e.name)) continue;
      const r = rel ? rel + '/' + e.name : e.name;
      if (e.isDirectory()) listFilesSync(base, r, out, depth + 1);
      else { try { const st = fs.statSync(path.join(base, r)); out.push({ path: r, size: st.size, mtime: st.mtimeMs }); } catch {} }
    }
    return out;
  }
  const shallowest = (files, re) => files.filter(f => re.test(f.path)).sort((a, b) => a.path.split('/').length - b.path.split('/').length || a.path.length - b.path.length)[0];

  async function listProjects() {
    const out = [];
    for (const e of fs.readdirSync(PROJ, { withFileTypes: true })) {
      if (!e.isDirectory() || !ID_RE.test(e.name)) continue;
      const m = meta(e.name); if (!m) continue;
      out.push({ id: e.name, ...m, status: m.status === 'running' ? 'stopped' : m.status });
    }
    return out.sort((a, b) => (b.updated || '').localeCompare(a.updated || ''));
  }

  // The app UI, with its absolute URLs moved under the console and a read-only skin.
  const SKIN = `<script>window.ANATOMY_WEB = true;</script><style>
#home .composer, #examples, #hubBtn, #settingsBtn, #warn, #stop, #reveal, #pvReveal, #replyGo, #replyIn, .reply { display: none !important; }
#webbar { position: sticky; top: 0; z-index: 30; display: flex; gap: 12px; align-items: center; padding: 8px 16px; background: #15181d; border-bottom: 1px solid #262b34; font-size: 13px; color: #8b93a1; }
#webbar a { color: #7aa2ff; text-decoration: none; } #webbar b { color: #e7e9ee; font-weight: 600; } #webbar span { flex: 1; }
</style>`;
  const BAR = `<div id="webbar"><b>Anatomy web console</b><span>Read-only view of the hub. Runs happen in Anatomy on your PCs.</span><a href="/#projects">pyrails.com</a></div>`;
  const rewrite = txt => txt.replace(/(['"`])\/(api|p|vendor|results\.js|viewer\.html|xometry\.js)(?=[/'"`?])/g, `$1${BASE}/$2`);
  const cache = new Map();
  function ui(name) {
    const f = path.join(UI, name);
    const st = fs.statSync(f);
    const c = cache.get(name);
    if (c && c.mtime === st.mtimeMs) return c.body;
    let body = rewrite(fs.readFileSync(f, 'utf8'));
    if (name === 'index.html') body = body.replace('</head>', SKIN + '</head>').replace(/<body([^>]*)>/, `<body$1>${BAR}`)
      .replace("openAsResults = !meta.running && meta.status === 'done'", 'openAsResults = !meta.running'); // nothing runs here: open on Results
    cache.set(name, { mtime: st.mtimeMs, body });
    return body;
  }

  // parts: path after /console, already split. Returns true if handled.
  async function handle(req, res, parts, url) {
    if (!parts.length || parts[0] === 'index.html') return send(res, 200, ui('index.html'), MIME['.html']);
    if (['results.js', 'viewer.html', 'xometry.js'].includes(parts[0]) && parts.length === 1) return send(res, 200, ui(parts[0]), MIME[path.extname(parts[0])]);
    if (parts[0] === 'vendor') return stream(res, safeJoin(path.join(UI, 'vendor'), decodeURIComponent(parts.slice(1).join('/'))));
    if (parts[0] === 'p' && parts[1]) {
      if (!ID_RE.test(parts[1])) return send(res, 400, { error: 'bad id' });
      return stream(res, safeJoin(path.join(PROJ, parts[1]), decodeURIComponent(parts.slice(2).join('/'))));
    }
    if (parts[0] !== 'api') return send(res, 404, { error: 'not found' });
    const a = parts.slice(1);
    const write = req.method !== 'GET' && req.method !== 'HEAD';

    if (a[0] === 'health') return send(res, 200, { ok: true, app: 'anatomy', web: true, claude: true });
    if (a[0] === 'hub') return send(res, 200, { configured: false, web: true });
    if (a[0] === 'settings') return write ? send(res, 403, { error: READ_ONLY }) : send(res, 200, { text: '' });
    if (a[0] === 'login' || a[0] === 'quit') return send(res, 403, { error: READ_ONLY });
    if (a[0] !== 'projects') return send(res, 404, { error: 'not found' });
    if (a.length === 1) return write ? send(res, 403, { error: READ_ONLY }) : send(res, 200, await listProjects());

    const id = a[1]; if (!ID_RE.test(id)) return send(res, 400, { error: 'bad id' });
    const dir = path.join(PROJ, id);
    const m = meta(id); if (!m) return send(res, 404, { error: 'no such project' });
    const action = a[2];

    if (!action) return send(res, 200, { id, ...m, status: m.status === 'running' ? 'stopped' : m.status, running: false });
    if (action === 'events') {
      res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' });
      let past = ''; try { past = fs.readFileSync(path.join(dir, '.anatomy', 'events.jsonl'), 'utf8'); } catch {}
      for (const line of past.split('\n')) if (line.trim()) res.write(`data: ${line}\n\n`);
      res.write(`data: ${JSON.stringify({ type: 'anatomy', kind: 'replay-done', running: false })}\n\n`);
      const ping = setInterval(() => res.write(': ping\n\n'), 20000);
      req.on('close', () => clearInterval(ping));
      return;
    }
    if (action === 'files') return send(res, 200, await listFiles(id));
    if (action === 'meshes') return send(res, 200, (await listFiles(id)).filter(f => /\.(stl|3mf|obj|glb)$|(^|\/)assembly\.json$/i.test(f.path)));
    if (action === 'file') {
      const p = safeJoin(dir, url.searchParams.get('path'));
      let st; try { st = fs.statSync(p); } catch { return send(res, 404, { error: 'not found' }); }
      if (!st.isFile()) return send(res, 404, { error: 'not found' });
      if (st.size > 50 * 1024 * 1024) return send(res, 413, { error: 'file too large to preview' });
      return send(res, 200, fs.readFileSync(p), MIME[path.extname(p).toLowerCase()] || 'text/plain; charset=utf-8');
    }
    if (action === 'build-state') {
      if (write) return send(res, 200, { ok: true }); // ticks in the web console are not saved
      try { return send(res, 200, readJson(path.join(dir, '.anatomy', 'build-state.json'))); } catch { return send(res, 200, {}); }
    }
    if (action === 'build') {
      const hit = shallowest(await listFiles(id), /(^|\/)build\/build\.json$/);
      if (!hit) return send(res, 200, {});
      try { const j = readJson(path.join(dir, hit.path)); j._file = hit.path; return send(res, 200, j); }
      catch (e) { return send(res, 200, { error: `${hit.path} is not valid JSON: ${e.message}` }); }
    }
    if (action === 'manifest') {
      const hit = shallowest((await listFiles(id)).filter(f => f.path.split('/').length <= 5 && !f.path.split('/').some(s => s.startsWith('.'))), /(^|\/)anatomy\.json$/);
      if (!hit) return send(res, 200, {});
      try { const j = readJson(path.join(dir, hit.path)); j._base = path.posix.dirname(hit.path) === '.' ? '' : path.posix.dirname(hit.path);
        if (j.apps) j.apps = j.apps.map(x => ({ ...x, running: false })); return send(res, 200, j); }
      catch (e) { return send(res, 200, { error: 'anatomy.json is not valid JSON: ' + e.message, _base: '' }); }
    }
    if (action === 'xometry') {
      if (!xometry) return send(res, 200, { parts: [] });
      const bf = (shallowest(await listFiles(id), /(^|\/)build\/build\.json$/) || {}).path;
      if (!bf) return send(res, 200, { parts: [] });
      try { if (!write) return send(res, 200, xometry.routing(dir, bf, '', listFilesSync)); } catch (e) { return send(res, 200, { parts: [], error: e.message }); }
      return send(res, 403, { error: READ_ONLY });
    }
    if (action === 'apps' && a[4] === 'log') return send(res, 200, { running: false, log: READ_ONLY });
    return send(res, 403, { error: READ_ONLY });
  }

  return { handle };
}

module.exports = { create };
