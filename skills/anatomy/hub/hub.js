// Anatomy Hub: central project storage for every PC that runs the Anatomy app.
// No npm dependencies: run with `node hub.js`. Listens on 127.0.0.1 only; put it behind
// nginx (HTTPS) and give each PC the shared token from /etc/anatomy-hub.env.
//
// Storage layout: $HUB_DATA/projects/<id>/<files...>   (the same tree as C:\Anatomy\<id>)
//                 $HUB_DATA/index/<id>.json            (path -> {sha, size, mtime, by, at})
//                 $HUB_DATA/locks/<id>.json            (which PC is running the project)
//                 $HUB_DATA/trash/<stamp>/<id>/...     (every overwritten or deleted file, kept 30 days)
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.HUB_PORT || 4380);
const HOST = process.env.HUB_HOST || '127.0.0.1';
const DATA = process.env.HUB_DATA || '/var/lib/anatomy-hub';
const TOKEN = process.env.HUB_TOKEN || '';
const MAX_FILE = Number(process.env.HUB_MAX_FILE_MB || 1024) * 1024 * 1024;
const LOCK_TTL = 10 * 60 * 1000; // a run lock expires if its PC stops renewing it
const TRASH_DAYS = 30;

if (!TOKEN || TOKEN.length < 24) { console.error('HUB_TOKEN must be set (24+ chars).'); process.exit(1); }
const PROJ = path.join(DATA, 'projects'), INDEX = path.join(DATA, 'index'), LOCKS = path.join(DATA, 'locks'), TRASH = path.join(DATA, 'trash'), TMP = path.join(DATA, 'tmp');
for (const d of [PROJ, INDEX, LOCKS, TRASH, TMP]) fs.mkdirSync(d, { recursive: true });

// ---------------------------------------------------------------- helpers
const ID_RE = /^[a-z0-9][a-z0-9-]{0,80}$/;
function checkId(id) { if (!ID_RE.test(id || '')) throw httpErr(400, 'bad project id'); return id; }
function httpErr(code, msg) { const e = new Error(msg); e.code = code; return e; }
// Project-relative paths use forward slashes, never escape the project and never touch the hub's own files.
function cleanRel(rel) {
  rel = String(rel || '').replace(/\\/g, '/').replace(/^\/+/, '');
  const parts = rel.split('/');
  if (!rel || parts.some(p => !p || p === '.' || p === '..' || /[\x00-\x1f]/.test(p))) throw httpErr(400, 'bad path');
  return parts.join('/');
}
function projectFile(id, rel) { return path.join(PROJ, checkId(id), ...cleanRel(rel).split('/')); }
function send(res, code, body, type = 'application/json') {
  res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
}
function readBody(req, limit = 4 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = []; let n = 0;
    req.on('data', c => { n += c.length; if (n > limit) { reject(httpErr(413, 'too large')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}
const readJson = (f, dflt) => { try { return JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, '')); } catch { return dflt; } };
function writeJsonAtomic(f, obj) {
  const tmp = path.join(TMP, crypto.randomBytes(8).toString('hex') + '.json');
  fs.writeFileSync(tmp, JSON.stringify(obj));
  fs.renameSync(tmp, f);
}
function authed(req) {
  const h = req.headers.authorization || '';
  const got = Buffer.from(h.startsWith('Bearer ') ? h.slice(7) : '');
  const want = Buffer.from(TOKEN);
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

// Per-project index, cached in memory and rebuilt from disk if missing.
const indexes = new Map();
function hashFile(f) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    fs.createReadStream(f).on('data', d => h.update(d)).on('end', () => resolve(h.digest('hex'))).on('error', reject);
  });
}
async function loadIndex(id) {
  if (indexes.has(id)) return indexes.get(id);
  let idx = readJson(path.join(INDEX, id + '.json'), null);
  if (!idx) {
    idx = {};
    const root = path.join(PROJ, id);
    const walk = async rel => {
      let ents = []; try { ents = fs.readdirSync(path.join(root, rel), { withFileTypes: true }); } catch { return; }
      for (const e of ents) {
        const r = rel ? rel + '/' + e.name : e.name;
        if (e.isDirectory()) await walk(r);
        else if (e.isFile()) { const st = fs.statSync(path.join(root, r)); idx[r] = { sha: await hashFile(path.join(root, r)), size: st.size, mtime: Math.round(st.mtimeMs) }; }
      }
    };
    if (fs.existsSync(root)) await walk('');
    writeJsonAtomic(path.join(INDEX, id + '.json'), idx);
  }
  indexes.set(id, idx);
  return idx;
}
function saveIndex(id) { writeJsonAtomic(path.join(INDEX, id + '.json'), indexes.get(id) || {}); }
function toTrash(id, rel) {
  const src = projectFile(id, rel);
  if (!fs.existsSync(src)) return;
  const dst = path.join(TRASH, new Date().toISOString().slice(0, 10), id, ...rel.split('/'));
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  try { fs.renameSync(src, dst + '.' + Date.now()); } catch { fs.rmSync(src, { force: true }); }
}
function pruneEmptyDirs(dir, stop) {
  while (dir.startsWith(stop + path.sep)) {
    try { if (fs.readdirSync(dir).length) return; fs.rmdirSync(dir); } catch { return; }
    dir = path.dirname(dir);
  }
}
function lockOf(id) {
  const l = readJson(path.join(LOCKS, id + '.json'), null);
  return l && Date.now() - l.at < LOCK_TTL ? l : null;
}
function projectSummary(id, idx) {
  const meta = readJson(path.join(PROJ, id, '.anatomy', 'project.json'), null);
  if (!meta) return null;
  let size = 0, files = 0, changed = 0, by = null;
  for (const v of Object.values(idx)) { size += v.size; files++; if ((v.at || 0) > changed) { changed = v.at; by = v.by; } }
  return { id, ...meta, size, files, changed: changed ? new Date(changed).toISOString() : null, changedBy: by, lock: lockOf(id) };
}
// Serialize writes per project so the index never loses an update.
const queues = new Map();
function withProject(id, fn) {
  const prev = queues.get(id) || Promise.resolve();
  const next = prev.then(fn, fn);
  queues.set(id, next.catch(() => {}));
  return next;
}

// Old trash goes after TRASH_DAYS.
function pruneTrash() {
  const cutoff = new Date(Date.now() - TRASH_DAYS * 864e5).toISOString().slice(0, 10);
  for (const d of fs.readdirSync(TRASH)) if (d < cutoff) fs.rmSync(path.join(TRASH, d), { recursive: true, force: true });
}
setInterval(() => { try { pruneTrash(); } catch {} }, 6 * 3600e3).unref();

// ---------------------------------------------------------------- routes
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://hub');
    const parts = url.pathname.replace(/^\/+/, '').split('/').filter(Boolean);
    if (parts[0] !== 'api') return send(res, 404, { error: 'not found' });
    if (parts[1] === 'health') return send(res, 200, { ok: true, app: 'anatomy-hub', version: 1 });
    if (!authed(req)) return send(res, 401, { error: 'bad or missing token' });
    const pc = String(req.headers['x-anatomy-pc'] || 'unknown').slice(0, 60);

    if (parts[1] === 'whoami') {
      let free = null; try { const s = fs.statfsSync(DATA); free = s.bavail * s.bsize; } catch {}
      return send(res, 200, { ok: true, pc, free });
    }

    if (parts[1] === 'projects' && parts.length === 2 && req.method === 'GET') {
      const out = [];
      for (const e of fs.readdirSync(PROJ, { withFileTypes: true })) {
        if (!e.isDirectory() || !ID_RE.test(e.name)) continue;
        const s = projectSummary(e.name, await loadIndex(e.name));
        if (s) out.push(s);
      }
      out.sort((a, b) => (b.updated || '').localeCompare(a.updated || ''));
      return send(res, 200, out);
    }

    if (parts[1] === 'projects' && parts[2]) {
      const id = checkId(parts[2]);
      const action = parts[3];

      if (action === 'manifest' && req.method === 'GET') {
        const idx = await loadIndex(id);
        return send(res, 200, { id, exists: fs.existsSync(path.join(PROJ, id)), lock: lockOf(id), files: idx });
      }

      if (action === 'file') {
        const rel = cleanRel(url.searchParams.get('path'));
        const f = projectFile(id, rel);
        if (req.method === 'GET') {
          let st; try { st = fs.statSync(f); } catch { return send(res, 404, { error: 'not found' }); }
          if (!st.isFile()) return send(res, 404, { error: 'not found' });
          const idx = await loadIndex(id);
          res.writeHead(200, { 'Content-Type': 'application/octet-stream', 'Content-Length': st.size, 'Cache-Control': 'no-store',
            'X-Sha256': (idx[rel] || {}).sha || '', 'X-Mtime': String((idx[rel] || {}).mtime || Math.round(st.mtimeMs)) });
          return fs.createReadStream(f).pipe(res);
        }
        if (req.method === 'PUT') {
          // Optimistic concurrency: the client says which version it last saw (X-Base-Sha, "" for a new file).
          const base = req.headers['x-base-sha'];
          const mtime = Number(url.searchParams.get('mtime')) || Date.now();
          const len = Number(req.headers['content-length'] || 0);
          if (len > MAX_FILE) return send(res, 413, { error: 'file too large' });
          const tmp = path.join(TMP, crypto.randomBytes(12).toString('hex'));
          const h = crypto.createHash('sha256'); let n = 0;
          await new Promise((resolve, reject) => {
            const ws = fs.createWriteStream(tmp);
            req.on('data', d => { n += d.length; if (n > MAX_FILE) { req.destroy(); reject(httpErr(413, 'file too large')); } h.update(d); });
            req.on('error', reject); ws.on('error', reject); ws.on('finish', resolve);
            req.pipe(ws);
          }).catch(e => { fs.rmSync(tmp, { force: true }); throw e; });
          const sha = h.digest('hex');
          const want = req.headers['x-sha256'];
          if (want && want !== sha) { fs.rmSync(tmp, { force: true }); return send(res, 400, { error: 'checksum mismatch, upload was damaged' }); }
          return withProject(id, async () => {
            const idx = await loadIndex(id);
            const cur = idx[rel];
            if (base !== undefined && (cur ? cur.sha : '') !== base && (!cur || cur.sha !== sha)) {
              fs.rmSync(tmp, { force: true });
              return send(res, 409, { error: 'changed on the hub since your last sync', current: cur || null });
            }
            if (cur && cur.sha === sha) { fs.rmSync(tmp, { force: true }); return send(res, 200, { ok: true, sha, same: true }); }
            if (cur) toTrash(id, rel);
            fs.mkdirSync(path.dirname(f), { recursive: true });
            fs.renameSync(tmp, f);
            try { fs.utimesSync(f, new Date(mtime), new Date(mtime)); } catch {}
            idx[rel] = { sha, size: n, mtime: Math.round(mtime), by: pc, at: Date.now() };
            saveIndex(id);
            send(res, 200, { ok: true, sha });
          });
        }
        if (req.method === 'DELETE') {
          const base = req.headers['x-base-sha'];
          return withProject(id, async () => {
            const idx = await loadIndex(id);
            const cur = idx[rel];
            if (!cur) return send(res, 200, { ok: true, gone: true });
            if (base !== undefined && cur.sha !== base) return send(res, 409, { error: 'changed on the hub since your last sync', current: cur });
            toTrash(id, rel);
            pruneEmptyDirs(path.dirname(f), path.join(PROJ, id));
            delete idx[rel];
            saveIndex(id);
            send(res, 200, { ok: true });
          });
        }
      }

      if (action === 'lock') {
        const f = path.join(LOCKS, id + '.json');
        if (req.method === 'POST') {
          const cur = lockOf(id);
          if (cur && cur.pc !== pc) return send(res, 409, { error: `running on ${cur.pc}`, lock: cur });
          writeJsonAtomic(f, { pc, at: Date.now(), since: cur ? cur.since : Date.now() });
          return send(res, 200, { ok: true });
        }
        if (req.method === 'DELETE') {
          const cur = lockOf(id);
          if (cur && cur.pc !== pc && url.searchParams.get('force') !== '1') return send(res, 409, { error: `running on ${cur.pc}`, lock: cur });
          fs.rmSync(f, { force: true });
          return send(res, 200, { ok: true });
        }
      }
    }
    send(res, 404, { error: 'not found' });
  } catch (e) {
    if (!res.headersSent) send(res, typeof e.code === 'number' ? e.code : 500, { error: e.message });
    else res.destroy();
  }
});
server.requestTimeout = 0; // big uploads on slow links
server.listen(PORT, HOST, () => console.log(`Anatomy Hub on http://${HOST}:${PORT}, data in ${DATA}`));
