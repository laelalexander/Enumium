// Anatomy Hub sync: keeps C:\Anatomy\<project> on this PC and the same project on the hub (the Droplet) in step,
// so every PC sees every project. Runs stay local (KiCad, slicers and Python need real files); the hub is
// the shared copy. Three-way sync per file against the state of the last sync (.anatomy/sync.json):
//   changed here only -> upload;  changed on hub only -> download;  deleted on one side only -> delete on the other;
//   changed on both   -> the newer copy wins and the other is kept in .anatomy/conflicts/ (nothing is ever lost;
//                        the hub also keeps every overwritten file in its trash for 30 days).
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const http = require('http');
const https = require('https');
const zlib = require('zlib');

const META_DIR = '.anatomy';
// Not synced: per-PC environments and caches (each PC rebuilds them), and the sync's own state.
const SKIP_DIRS = new Set(['venv', 'env', '.venv', '.pio', '.mypy_cache', '.pytest_cache', 'node_modules', '__pycache__', '.git', '.tools', '.claude']);
const SKIP_META = new Set(['sync.json', 'conflicts', 'events.jsonl.lock']);
// Already-compressed formats go up as they are; everything else (STEP, STL, G-code, DXF, SVG, KiCad, JSON, text...)
// is gzipped on the wire, which typically makes CAD and G-code 3-6x smaller. Needs hub version 2+.
const PACKED = /\.(png|jpe?g|gif|webp|zip|7z|gz|tgz|bz2|xz|rar|3mf|glb|mp4|mov|mkv|avi|mp3|m4a|xlsx|docx|pptx|pdf|whl|exe|msi|jar)$/i;
const PARALLEL = 4; // files in flight at once per project
const SKIP_FILE = /(^|\/)(~\$[^/]*|[^/]*\.tmp|[^/]*\.anatomy-dl|Thumbs\.db|desktop\.ini|\.DS_Store)$/i;

function create({ ROOT, readMeta, isRunning, onChange }) {
  const CFG = path.join(ROOT, '.anatomy-hub.json');
  const state = { status: 'off', lastSync: null, error: null, busy: new Set(), progress: {}, remote: [] };

  function config() {
    try { const c = JSON.parse(fs.readFileSync(CFG, 'utf8').replace(/^\uFEFF/, '')); return c && c.url && c.token ? c : null; } catch { return null; }
  }
  function pcName() { const c = config(); return (c && c.pc) || os.hostname(); }
  function saveConfig(c) {
    const cur = config() || {};
    const next = { ...cur, ...c };
    if (next.url) next.url = String(next.url).trim().replace(/\/+$/, '');
    if (!next.url || !next.token) { fs.rmSync(CFG, { force: true }); return null; }
    fs.writeFileSync(CFG, JSON.stringify(next, null, 2));
    return next;
  }

  // ------------------------------------------------------------ HTTP to the hub
  function request(method, p, { body, headers = {}, stream, timeout = 120000 } = {}) {
    const c = config(); if (!c) return Promise.reject(new Error('hub not set up'));
    const u = new URL(c.url + p);
    const mod = u.protocol === 'https:' ? https : http;
    return new Promise((resolve, reject) => {
      const req = mod.request(u, { method, timeout, headers: { Authorization: 'Bearer ' + c.token, 'X-Anatomy-PC': pcName(), ...headers } }, res => {
        if (stream && res.statusCode === 200) return resolve(res.headers['content-encoding'] === 'gzip' ? res.pipe(zlib.createGunzip()) : res);
        const chunks = []; res.on('data', d => chunks.push(d));
        res.on('end', () => {
          const txt = Buffer.concat(chunks).toString('utf8');
          let j = null; try { j = JSON.parse(txt); } catch {}
          if (res.statusCode >= 200 && res.statusCode < 300) return resolve(j);
          const e = new Error((j && j.error) || `hub said ${res.statusCode}`); e.status = res.statusCode; e.body = j; reject(e);
        });
      });
      req.on('timeout', () => req.destroy(new Error('hub did not answer in time')));
      req.on('error', reject);
      if (body && typeof body.pipe === 'function') body.pipe(req); else req.end(body);
    });
  }
  const enc = encodeURIComponent;

  // ------------------------------------------------------------ local scan
  function hashFile(f) {
    return new Promise((resolve, reject) => {
      const h = crypto.createHash('sha256');
      fs.createReadStream(f).on('data', d => h.update(d)).on('end', () => resolve(h.digest('hex'))).on('error', reject);
    });
  }
  function syncable(rel) {
    const parts = rel.split('/');
    if (parts.slice(0, -1).some(p => SKIP_DIRS.has(p))) return false;
    // Downloaded programs a run fetched into work/tools (slicers, Java, Freerouting...) are reinstallable, not project work.
    if (/(^|\/)work\/tools\//.test(rel)) return false;
    if (parts[0] === META_DIR && (SKIP_META.has(parts[1]) || parts.length > 2 && parts[1] === 'conflicts')) return false;
    return !SKIP_FILE.test(rel);
  }
  async function scanLocal(dir, base) {
    const out = {};
    const walk = async (rel, depth) => {
      if (depth > 20) return;
      let ents = []; try { ents = fs.readdirSync(path.join(dir, rel), { withFileTypes: true }); } catch { return; }
      for (const e of ents) {
        const r = rel ? rel + '/' + e.name : e.name;
        if (e.isDirectory()) { if (!SKIP_DIRS.has(e.name) && r !== META_DIR + '/conflicts' && !/(^|\/)work\/tools$/.test(r)) await walk(r, depth + 1); continue; }
        if (!e.isFile() || !syncable(r)) continue;
        let st; try { st = fs.statSync(path.join(dir, r)); } catch { continue; }
        const mtime = Math.round(st.mtimeMs), b = base[r];
        // Unchanged size+mtime since the last sync: trust the stored hash instead of re-reading the file.
        const sha = b && b.size === st.size && b.mtime === mtime ? b.sha : await hashFile(path.join(dir, r)).catch(() => null);
        if (sha) out[r] = { sha, size: st.size, mtime };
      }
    };
    await walk('', 0);
    return out;
  }
  const basePath = dir => path.join(dir, META_DIR, 'sync.json');
  function readBase(dir) { try { return JSON.parse(fs.readFileSync(basePath(dir), 'utf8')); } catch { return null; } }
  function writeBase(dir, b) { fs.mkdirSync(path.join(dir, META_DIR), { recursive: true }); fs.writeFileSync(basePath(dir), JSON.stringify(b)); }

  // ------------------------------------------------------------ transfers
  let hubVersion = 0;
  async function checkHub() {
    const h = await request('GET', '/api/health', { timeout: 15000 }).catch(() => null);
    hubVersion = (h && h.version) || 1;
  }
  const squeeze = (rel, size) => hubVersion >= 2 && size > 2048 && !PACKED.test(rel);
  async function upload(id, dir, rel, info, baseSha) {
    const f = path.join(dir, ...rel.split('/'));
    const gz = squeeze(rel, info.size);
    const headers = { 'Content-Type': 'application/octet-stream', 'X-Sha256': info.sha, 'X-Base-Sha': baseSha || '' };
    if (gz) { headers['Content-Encoding'] = 'gzip'; headers['Transfer-Encoding'] = 'chunked'; } else headers['Content-Length'] = info.size;
    const src = fs.createReadStream(f);
    return request('PUT', `/api/projects/${enc(id)}/file?path=${enc(rel)}&mtime=${info.mtime}`, {
      body: gz ? src.pipe(zlib.createGzip({ level: 6 })) : src, timeout: 30 * 60000, headers,
    });
  }
  async function download(id, dir, rel, info, dest) {
    const f = dest || path.join(dir, ...rel.split('/'));
    fs.mkdirSync(path.dirname(f), { recursive: true });
    const tmp = f + '.anatomy-dl';
    const res = await request('GET', `/api/projects/${enc(id)}/file?path=${enc(rel)}`, { stream: true, timeout: 30 * 60000, headers: hubVersion >= 2 ? { 'Accept-Encoding': 'gzip' } : {} });
    const h = crypto.createHash('sha256');
    await new Promise((resolve, reject) => {
      const ws = fs.createWriteStream(tmp);
      res.on('data', d => h.update(d)); res.on('error', reject); ws.on('error', reject); ws.on('finish', resolve);
      res.pipe(ws);
    });
    const sha = h.digest('hex');
    if (info.sha && sha !== info.sha) { fs.rmSync(tmp, { force: true }); throw new Error(`download of ${rel} was damaged`); }
    try { fs.renameSync(tmp, f); } catch (e) { fs.rmSync(tmp, { force: true }); throw new Error(`${rel} is open in another program`); }
    try { const t = new Date(info.mtime); fs.utimesSync(f, t, t); } catch {}
    const st = fs.statSync(f);
    return { sha, size: st.size, mtime: Math.round(st.mtimeMs) };
  }
  // The losing side of a conflict is kept in .anatomy/conflicts/<time>-<pc>/<path>.
  function conflictPath(dir, rel, who) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const dst = path.join(dir, META_DIR, 'conflicts', stamp + '-' + String(who || 'other').replace(/[^\w-]+/g, '_'), ...rel.split('/'));
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    return dst;
  }
  function keepConflict(dir, rel, who) { fs.copyFileSync(path.join(dir, ...rel.split('/')), conflictPath(dir, rel, who)); }

  // ------------------------------------------------------------ one project
  async function syncProject(id, { pullOnly = false } = {}) {
    if (!config()) throw new Error('hub not set up');
    if (state.busy.has(id)) return { skipped: 'busy' };
    if (isRunning(id)) return { skipped: 'running' };   // pushed when the run ends
    state.busy.add(id); onChange && onChange();
    if (!hubVersion) await checkHub();
    const dir = path.join(ROOT, id);
    const report = { up: 0, down: 0, deleted: 0, conflicts: [], errors: [] };
    try {
      const prev = readBase(dir);
      const base = (prev && prev.files) || {};
      const local = fs.existsSync(dir) ? await scanLocal(dir, base) : {};
      const remote = await request('GET', `/api/projects/${enc(id)}/manifest`);
      const rfiles = remote.files || {};

      // First sync of a folder whose id already exists on the hub as a different project: don't merge two projects.
      if (!prev && Object.keys(local).length && Object.keys(rfiles).length) {
        const lm = readMeta(id);
        if (lm && lm.created && rfiles[META_DIR + '/project.json']) {
          const r = await request('GET', `/api/projects/${enc(id)}/file?path=${enc(META_DIR + '/project.json')}`, { stream: true });
          const txt = await new Promise(ok => { const c = []; r.on('data', d => c.push(d)); r.on('end', () => ok(Buffer.concat(c).toString('utf8'))); });
          let rmeta = null; try { rmeta = JSON.parse(txt.replace(/^\uFEFF/, '')); } catch {}
          if (rmeta && rmeta.created && rmeta.created !== lm.created) { report.clash = true; return report; }
        }
      }

      const paths = new Set([...Object.keys(local), ...Object.keys(rfiles), ...Object.keys(base)]);
      const next = { ...base };
      const total = paths.size; let done = 0;
      state.progress[id] = { done, total };
      let sinceSave = 0;
      const one = async rel => {
        done++; if (done % 20 === 0) { state.progress[id] = { done, total }; onChange && onChange(); }
        // Save progress now and then, so an interrupted first upload resumes without re-reading every file.
        if (++sinceSave >= 50) { sinceSave = 0; try { writeBase(dir, { hub: config().url, at: new Date().toISOString(), files: next }); } catch {} }
        if (!syncable(rel)) { delete next[rel]; return; }
        const L = local[rel], R = rfiles[rel], B = base[rel];
        const lCh = (L && L.sha) !== (B && B.sha), rCh = (R && R.sha) !== (B && B.sha);
        try {
          if (L && R && L.sha === R.sha) { next[rel] = { sha: L.sha, size: L.size, mtime: L.mtime }; return; }
          if (!lCh && !rCh) return;
          if (lCh && !rCh) {
            if (pullOnly) return;
            if (L) { await upload(id, dir, rel, L, R ? R.sha : ''); next[rel] = L; report.up++; }
            else if (R) { await request('DELETE', `/api/projects/${enc(id)}/file?path=${enc(rel)}`, { headers: { 'X-Base-Sha': R.sha } }); delete next[rel]; report.deleted++; }
            else delete next[rel];
          } else if (rCh && !lCh) {
            if (R) { next[rel] = await download(id, dir, rel, R); report.down++; }
            else if (L) { fs.rmSync(path.join(dir, ...rel.split('/')), { force: true }); delete next[rel]; report.deleted++; }
            else delete next[rel];
          } else {
            // Changed on both sides.
            if (!L) { next[rel] = await download(id, dir, rel, R); report.down++; return; }      // deleted here, edited there: keep the edit
            if (!R) { if (!pullOnly) { await upload(id, dir, rel, L, ''); next[rel] = L; report.up++; } return; }
            const remoteWins = (R.mtime || 0) > L.mtime;
            if (remoteWins || pullOnly) { keepConflict(dir, rel, pcName()); next[rel] = await download(id, dir, rel, R); }
            else { await download(id, dir, rel, R, conflictPath(dir, rel, R.by || 'hub')); await upload(id, dir, rel, L, R.sha); next[rel] = L; }
            report.conflicts.push(rel);
          }
        } catch (e) {
          if (e.status === 409) report.errors.push(`${rel}: changed again on another PC, will retry`);
          else report.errors.push(`${rel}: ${e.message}`);
        }
      };
      const queue = [...paths].sort();
      await Promise.all(Array.from({ length: PARALLEL }, async () => { while (queue.length) await one(queue.shift()); }));
      writeBase(dir, { hub: config().url, at: new Date().toISOString(), files: next });
      return report;
    } finally {
      state.busy.delete(id); delete state.progress[id]; onChange && onChange();
    }
  }

  // ------------------------------------------------------------ everything
  let timer = null, running = false;
  async function syncAll() {
    if (!config()) { state.status = 'off'; return state; }
    if (running) return state;
    running = true; state.status = 'syncing'; onChange && onChange();
    const results = {};
    try {
      await checkHub();
      const remote = await request('GET', '/api/projects');
      state.remote = remote;
      const ids = new Set(remote.map(p => p.id));
      for (const e of fs.readdirSync(ROOT, { withFileTypes: true })) if (e.isDirectory() && readMeta(e.name)) ids.add(e.name);
      for (const id of ids) {
        const local = fs.existsSync(path.join(ROOT, id));
        // Projects that exist only on the hub are fetched on demand (Open), unless "download everything" is on.
        if (!local && !config().pullAll) continue;
        try { results[id] = await syncProject(id); } catch (e) { results[id] = { errors: [e.message] }; }
        // Same folder name, different project (made separately on two PCs): give this PC's copy its own name.
        if (results[id] && results[id].clash && !isRunning(id)) {
          const slug = pcName().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 20) || 'pc';
          let nid = `${id}-${slug}`, n = 2;
          while (fs.existsSync(path.join(ROOT, nid)) || ids.has(nid)) nid = `${id}-${slug}-${n++}`;
          try {
            fs.renameSync(path.join(ROOT, id), path.join(ROOT, nid));
            results[nid] = await syncProject(nid); results[id].renamedTo = nid; delete results[id].clash;
          } catch (e) { results[id].errors = [`kept apart from the hub's "${id}": ${e.message}`]; }
        }
      }
      state.remote = await request('GET', '/api/projects').catch(() => state.remote);
      state.status = 'ok'; state.error = null; state.lastSync = new Date().toISOString();
      state.clashes = Object.keys(results).filter(k => results[k] && results[k].clash);
      state.problems = Object.entries(results).filter(([, r]) => r && r.errors && r.errors.length).map(([k, r]) => ({ id: k, errors: r.errors.slice(0, 5) }));
    } catch (e) {
      state.status = 'error'; state.error = e.message;
    } finally { running = false; onChange && onChange(); }
    return state;
  }
  function start(intervalMs = 120000) {
    clearInterval(timer);
    timer = setInterval(() => syncAll().catch(() => {}), intervalMs);
    timer.unref && timer.unref();
    setTimeout(() => syncAll().catch(() => {}), 3000);
  }

  // Run locks: one PC runs a project at a time. Renewed while the run lasts.
  const lockTimers = new Map();
  async function lock(id) {
    if (!config()) return { ok: true, offline: true };
    try { await request('POST', `/api/projects/${enc(id)}/lock`, { timeout: 15000 }); }
    catch (e) { if (e.status === 409) return { ok: false, by: e.body && e.body.lock && e.body.lock.pc }; return { ok: true, offline: true }; }
    clearInterval(lockTimers.get(id));
    const t = setInterval(() => request('POST', `/api/projects/${enc(id)}/lock`, { timeout: 15000 }).catch(() => {}), 4 * 60000);
    t.unref && t.unref(); lockTimers.set(id, t);
    return { ok: true };
  }
  async function unlock(id) {
    clearInterval(lockTimers.get(id)); lockTimers.delete(id);
    if (config()) await request('DELETE', `/api/projects/${enc(id)}/lock`, { timeout: 15000 }).catch(() => {});
  }

  function status() {
    const c = config();
    return { configured: !!c, url: c ? c.url : '', pc: pcName(), pullAll: !!(c && c.pullAll), status: state.status, lastSync: state.lastSync,
      error: state.error, busy: [...state.busy], progress: state.progress, clashes: state.clashes || [], problems: state.problems || [] };
  }
  async function test(url, token) {
    const u = new URL(String(url).replace(/\/+$/, '') + '/api/whoami');
    const mod = u.protocol === 'https:' ? https : http;
    return new Promise((resolve) => {
      const req = mod.request(u, { timeout: 15000, headers: { Authorization: 'Bearer ' + token, 'X-Anatomy-PC': pcName() } }, res => {
        const c = []; res.on('data', d => c.push(d));
        res.on('end', () => { let j = {}; try { j = JSON.parse(Buffer.concat(c).toString('utf8')); } catch {} resolve(res.statusCode === 200 ? { ok: true, free: j.free } : { ok: false, error: j.error || `hub said ${res.statusCode}` }); });
      });
      req.on('timeout', () => req.destroy(new Error('no answer')));
      req.on('error', e => resolve({ ok: false, error: e.message }));
      req.end();
    });
  }

  return { config, saveConfig, status, syncAll, syncProject, start, lock, unlock, test, remoteProjects: () => state.remote || [] };
}

module.exports = { create };
