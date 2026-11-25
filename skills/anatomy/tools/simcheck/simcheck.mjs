#!/usr/bin/env node
// Hub-style simulator check: proves a project's simulator and 3D viewer pages open the way the Anatomy Hub web console
// opens them - plain static files from a deep sub-path, no sim server, no node_modules / .venv - and actually work.
//
//   node simcheck.mjs <project folder> [--json out.json] [--only <substring>] [--keep-shots <dir>]
//
// For every app in anatomy.json with "kind": "simulator" or "viewer" (and any app whose name says simulator, twin or
// viewer) it finds the page the hub opens (the app's "web" field, else the shallowest index.html under its cwd), then:
//   1. scans that page and the scripts it loads for root-absolute URLs ("/vendor/...", fetch("/api/...")),
//   2. serves the project at http://127.0.0.1:<port>/anatomy-hub/console/p/<id>/ exactly like the hub,
//   3. opens it in headless Chromium and fails on: any console error or uncaught exception, any failed request or HTTP
//      4xx/5xx, no window.TwinLoad loading screen, TwinLoad.failed, the loader not finishing in time, a blank canvas,
//      or a canvas that does not change when dragged (3D view frozen).
// Writes sim/results/hub-check.json (or --json) and exits 1 when anything fails. Needs Node 18+ and Playwright with
// Chromium: it looks for "playwright" next to this script, in the project, in ANATOMY_PLAYWRIGHT, or in npm's global
// folder. If none is found it prints how to install it (npm i -D playwright && npx playwright install chromium).
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : null; };
const jsonOut = opt('--json'), only = opt('--only'), shotsDir = opt('--keep-shots');
const projectDir = path.resolve(args[0] || '.');
if (!fs.existsSync(projectDir)) { console.error('No such folder:', projectDir); process.exit(2); }
const ID = path.basename(projectDir).toLowerCase().replace(/[^a-z0-9-]/g, '-');
const PRE = `/anatomy-hub/console/p/${ID}/`;
const SKIP = new Set(['venv', 'env', '.venv', '.pio', '.mypy_cache', '.pytest_cache', 'node_modules', '__pycache__', '.git', '.tools', '.claude', '.anatomy']);

// ---------------------------------------------------------------- which pages
function walk(dir, rel = '', out = [], depth = 0) {
  if (depth > 12) return out;
  let es = []; try { es = fs.readdirSync(path.join(dir, rel), { withFileTypes: true }); } catch { return out; }
  for (const e of es) { const r = rel ? rel + '/' + e.name : e.name; if (e.isDirectory()) { if (!SKIP.has(e.name)) walk(dir, r, out, depth + 1); } else out.push(r); }
  return out;
}
const files = walk(projectDir);
const mf = files.filter(f => /(^|\/)anatomy\.json$/.test(f)).sort((a, b) => a.split('/').length - b.split('/').length)[0];
if (!mf) { console.error('No anatomy.json in', projectDir); process.exit(2); }
const man = JSON.parse(fs.readFileSync(path.join(projectDir, mf), 'utf8').replace(/^﻿/, ''));
const base = path.posix.dirname(mf) === '.' ? '' : path.posix.dirname(mf);
function webPage(a) {                                   // the same rule as the hub web console (results.js webPage)
  const pre = base ? base + '/' : '';
  if (a.web) return pre + String(a.web).replace(/^\.?\//, '');
  const cwd = a.cwd && a.cwd !== '.' ? (pre + a.cwd).replace(/\/+$/, '') : (pre ? pre.slice(0, -1) : '');
  const pages = files.filter(f => (!cwd || f.startsWith(cwd + '/')) && /(^|\/)index\.html?$/i.test(f) && !/node_modules|vendor\/|assembly|drawings?\//i.test(f));
  const pref = f => /(^|\/)(sim|twin|control|ui|public|web|static|www)\//i.test(f);
  pages.sort((x, y) => (pref(y) - pref(x)) || x.split('/').length - y.split('/').length);
  return pages[0] || null;
}
// the apps the hub console opens as simulators (its Simulate tab rule) plus 3D viewers
const apps = (man.apps || []).filter(a => a.kind === 'simulator' || a.kind === 'viewer' || /simulator|digital twin|test table/i.test((a.name || '') + ' ' + (a.description || '')) || /3d viewer/i.test(a.name || ''));
const targets = []; const problems = [];
for (const a of apps) {
  const page = webPage(a);
  if (!page) { problems.push({ app: a.name, page: null, errors: ['no page the hub can open: add a static index.html under the app cwd, or a "web" field in anatomy.json'] }); continue; }
  if (!targets.some(t => t.page === page)) targets.push({ app: a.name, page, simulator: a.kind === 'simulator' || /simulat|twin|test table/i.test(a.name) });
}
if (!apps.length) { console.log('No simulator or viewer app in', mf, '- nothing to check.'); }
const list = only ? targets.filter(t => t.page.includes(only)) : targets;

// ---------------------------------------------------------------- 1. static scan for root-absolute URLs
const ABS = [
  /\b(?:src|href)\s*=\s*["']\/(?!\/)[^"']*["']/g,                                   // <script src="/x">, <link href="/x">
  /\bfetch\(\s*[`"']\/(?!\/)[^`"']*/g,                                             // fetch("/api/...")
  /\bnew\s+(?:WebSocket|EventSource|Worker)\(\s*[`"']\/(?!\/)[^`"']*/g,
  /"imports"\s*:\s*\{[^}]*:\s*"\/(?!\/)[^"]*"/g,                                    // import map to "/vendor/..."
  /\bfrom\s+["']\/(?!\/)[^"']*["']/g, /\bimport\(\s*["']\/(?!\/)[^"']*["']/g,
  /\.(?:load|loadAsync)\(\s*[`"']\/(?!\/)[^`"']*/g,                                 // three.js loaders
];
function scan(rel, seen = new Set()) {
  if (seen.has(rel) || seen.size > 200) return []; seen.add(rel);
  let src = ''; try { src = fs.readFileSync(path.join(projectDir, rel), 'utf8'); } catch { return []; }
  const hits = [];
  // a line marked "simcheck:server-only" is code that only runs when the twin's own server is present (checked by the page)
  const lines = src.split('\n');
  for (const re of ABS) for (const m of src.matchAll(re)) {
    const ln = src.slice(0, m.index).split('\n').length - 1;
    if (/simcheck:server-only/.test(lines[ln] || '')) continue;
    hits.push(`${rel}:${ln + 1}: root-absolute URL ${m[0].slice(0, 90)}`);
  }
  const dir = path.posix.dirname(rel);
  const refs = [...src.matchAll(/<script[^>]+src=["']([^"']+)["']/g), ...src.matchAll(/^\s*(?:import|export)\b[^'"`;]*?from\s*['"](\.{1,2}\/[^'"]+)['"]/gm),
    ...src.matchAll(/data-entry=["']([^"']+)["']/g)].map(m => m[1]).filter(u => !/^(https?:)?\/\//.test(u) && !u.startsWith('/'));
  for (const u of refs) { const r = path.posix.normalize(path.posix.join(dir, u.split('?')[0])); if (!/(^|\/)vendor\//.test(r) && !SKIP.has(r.split('/')[0])) hits.push(...scan(r, seen)); }
  return hits;
}

// ---------------------------------------------------------------- 2. hub-like static server
const MIME = { html: 'text/html; charset=utf-8', htm: 'text/html', js: 'text/javascript', mjs: 'text/javascript', css: 'text/css', json: 'application/json',
  png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', svg: 'image/svg+xml', glb: 'model/gltf-binary', gltf: 'model/gltf+json', wasm: 'application/wasm',
  stl: 'model/stl', txt: 'text/plain', csv: 'text/csv', woff2: 'font/woff2', webp: 'image/webp', gif: 'image/gif', md: 'text/plain' };
function serve() {
  return new Promise(resolve => {
    const srv = http.createServer((q, s) => {
      let u; try { u = decodeURIComponent(new URL(q.url, 'http://x').pathname); } catch { s.writeHead(400); return s.end(); }
      if (!u.startsWith(PRE)) { s.writeHead(404, { 'content-type': 'application/json' }); return s.end('{"error":"not found (outside the project: a root-absolute URL?)"}'); }
      const parts = u.slice(PRE.length).split('/');
      if (parts.some(p => p === '..' || SKIP.has(p))) { s.writeHead(404); return s.end('{"error":"not synced to the hub"}'); }
      const f = path.join(projectDir, ...parts);
      fs.stat(f, (e, st) => {
        if (e || !st.isFile()) { s.writeHead(404, { 'content-type': 'application/json' }); return s.end('{"error":"not found"}'); }
        s.writeHead(200, { 'content-type': MIME[path.extname(f).slice(1).toLowerCase()] || 'application/octet-stream', 'content-length': st.size, 'cache-control': 'no-store' });
        fs.createReadStream(f).pipe(s);
      });
    }).listen(0, '127.0.0.1', () => resolve(srv));
  });
}

// ---------------------------------------------------------------- model orientation
// Extents of a GLB in its own coordinates (node transforms applied), and which axis is up in it: assembly.json "up"
// next to it, else trimesh exports with no root rotation keep the CAD's Z-up, else glTF's Y-up.
function mat(n) {
  if (n.matrix) return n.matrix.slice();
  const [x, y, z, w] = n.rotation || [0, 0, 0, 1], [sx, sy, sz] = n.scale || [1, 1, 1], [tx, ty, tz] = n.translation || [0, 0, 0];
  return [(1 - 2 * (y * y + z * z)) * sx, (2 * (x * y + z * w)) * sx, (2 * (x * z - y * w)) * sx, 0,
    (2 * (x * y - z * w)) * sy, (1 - 2 * (x * x + z * z)) * sy, (2 * (y * z + x * w)) * sy, 0,
    (2 * (x * z + y * w)) * sz, (2 * (y * z - x * w)) * sz, (1 - 2 * (x * x + y * y)) * sz, 0, tx, ty, tz, 1];
}
const mul = (a, b) => { const o = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k]; return o; };
function glbFacts(file) {
  const b = fs.readFileSync(file); if (b.readUInt32LE(0) !== 0x46546c67) return null;
  const j = JSON.parse(b.slice(20, 20 + b.readUInt32LE(12)).toString('utf8'));
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  const visit = (i, M) => {
    const n = j.nodes[i], W = mul(M, mat(n));
    if (n.mesh != null) for (const p of j.meshes[n.mesh].primitives) {
      const a = j.accessors[p.attributes.POSITION]; if (!a || !a.min || !a.max) continue;
      for (let c = 0; c < 8; c++) {
        const v = [c & 1 ? a.max[0] : a.min[0], c & 2 ? a.max[1] : a.min[1], c & 4 ? a.max[2] : a.min[2]];
        for (let r = 0; r < 3; r++) { const w = W[r] * v[0] + W[4 + r] * v[1] + W[8 + r] * v[2] + W[12 + r]; lo[r] = Math.min(lo[r], w); hi[r] = Math.max(hi[r], w); }
      }
    }
    for (const c of n.children || []) visit(c, W);
  };
  const roots = (j.scenes[j.scene || 0] || {}).nodes || [];
  roots.forEach(i => visit(i, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]));
  let up = null; try { up = JSON.parse(fs.readFileSync(path.join(path.dirname(file), 'assembly.json'), 'utf8')).up || null; } catch {}
  if (!up) up = /trimesh/i.test(j.asset?.generator || '') && !roots.some(i => j.nodes[i].rotation || j.nodes[i].matrix) ? 'Z' : 'Y';
  return { ext: hi.map((h, r) => h - lo[r]), up: String(up).toUpperCase() };
}

// ---------------------------------------------------------------- 3. headless browser
function findPlaywright() {
  const tries = [process.env.ANATOMY_PLAYWRIGHT, HERE, projectDir, path.join(projectDir, 'sim'), process.cwd()].filter(Boolean);
  for (const d of tries) { try { return createRequire(path.join(d, 'x.js'))('playwright'); } catch {} }
  try { const g = path.join(process.env.APPDATA || '', 'npm', 'node_modules'); return createRequire(path.join(g, 'x.js'))('playwright'); } catch {}
  return null;
}

async function main() {
  const results = [...problems];
  const pw = list.length ? findPlaywright() : null;
  if (list.length && !pw) {
    console.error('Playwright is not installed. Install it once next to this script:\n  cd "' + HERE + '"\n  npm i playwright && npx playwright install chromium\n(or set ANATOMY_PLAYWRIGHT to a folder whose node_modules has playwright)');
    process.exit(3);
  }
  const srv = list.length ? await serve() : null;
  const root = srv ? `http://127.0.0.1:${srv.address().port}${PRE}` : '';
  const br = pw ? await pw.chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] }) : null;
  for (const t of list) {
    const r = { app: t.app, page: t.page, errors: [], warnings: [] };
    r.errors.push(...scan(t.page));
    const ctx = await br.newContext({ viewport: { width: 1400, height: 860 } });
    const pg = await ctx.newPage();
    pg.on('console', m => { if (m.type() === 'error') r.errors.push('console error: ' + m.text().slice(0, 240)); });
    pg.on('pageerror', e => r.errors.push('uncaught: ' + String(e.message).slice(0, 240)));
    pg.on('requestfailed', q => { const why = (q.failure() || {}).errorText || ''; if (!/ERR_ABORTED/.test(why) || q.resourceType() !== 'media') r.errors.push(`request failed: ${q.url().replace(root, '')} ${why}`); });
    pg.on('response', q => { if (q.status() >= 400) r.errors.push(`HTTP ${q.status()}: ${q.url().replace(root, '').replace(/^http:\/\/127\.0\.0\.1:\d+/, '(root) ')}`); });
    const glbs = [];
    pg.on('response', q => { if (q.status() === 200 && /\.glb(\?|$)/i.test(q.url()) && q.url().startsWith(root)) glbs.push(decodeURIComponent(q.url().slice(root.length).split('?')[0])); });
    try { await pg.goto(root + t.page.split('/').map(encodeURIComponent).join('/'), { waitUntil: 'load', timeout: 60000 }); }
    catch (e) { r.errors.push('page did not load: ' + e.message.slice(0, 160)); }
    const t0 = Date.now(); let st = {};
    while (Date.now() - t0 < 90000) {
      // the page itself, or (for a page that frames twins) every same-origin frame that has a loader
      const ls = [];
      for (const f of pg.frames()) ls.push(await f.evaluate(() => { const L = window.TwinLoad || window.LabLoad; return L ? { failed: !!L.failed, done: !!L.finished, err: L.lastError || null } : null; }).catch(() => null));
      const L = ls.filter(Boolean);
      st = { has: L.length > 0, failed: L.some(x => x.failed), done: L.length > 0 && L.every(x => x.done), err: (L.find(x => x.failed) || {}).err || null };
      if (st.failed || st.done || (!st.has && Date.now() - t0 > 8000)) break;
      await pg.waitForTimeout(500);
    }
    r.loadSeconds = Math.round((Date.now() - t0) / 100) / 10;
    if (!st.has) r.errors.push('no loading screen: add the shared loader (tools/simcheck/twinload.js) as described in references/simulation.md');
    else if (st.failed) r.errors.push('loading screen ended in an error: ' + String(st.err).slice(0, 300));
    else if (!st.done) r.errors.push('loading screen did not finish within 90 s');
    await pg.waitForTimeout(1500);
    // the largest visible canvas in the page or its frames (page coordinates)
    let box = null, area = 0;
    for (const f of pg.frames()) for (const c of await f.$$('canvas').catch(() => [])) {
      const q = await c.boundingBox().catch(() => null);
      if (q && q.width > 80 && q.height > 80 && q.width * q.height > area) { area = q.width * q.height; box = q; }
    }
    // dashboards drawn in SVG count as a view too (checked for content, not dragged)
    const svgView = box ? null : await pg.evaluate(() => { for (const s of document.querySelectorAll('svg')) { const q = s.getBoundingClientRect(); if (q.width > 200 && q.height > 120 && s.querySelectorAll('*').length > 10) return true; } return false; }).catch(() => false);
    if (!box && svgView) r.warnings.push('no canvas; an SVG view is shown');
    else if (!box) { if (t.simulator) r.errors.push('no visible canvas or SVG view: the twin shows no 3D or plotted view'); else r.warnings.push('no canvas on this page'); }
    else {
      const clip = { x: Math.max(0, box.x), y: Math.max(0, box.y), width: Math.min(box.width, 1400 - Math.max(0, box.x)), height: Math.min(box.height, 860 - Math.max(0, box.y)) };
      const a1 = await pg.screenshot({ clip });
      const stat = await pg.evaluate(async b64 => {
        const im = new Image(); im.src = 'data:image/png;base64,' + b64; await im.decode();
        const c = document.createElement('canvas'); c.width = Math.min(im.width, 400); c.height = Math.min(im.height, 300);
        const g = c.getContext('2d'); g.drawImage(im, 0, 0, c.width, c.height); const d = g.getImageData(0, 0, c.width, c.height).data;
        let s = 0, s2 = 0, n = 0; const set = new Set();
        for (let i = 0; i < d.length; i += 4) { const l = (d[i] + d[i + 1] + d[i + 2]) / 3; s += l; s2 += l * l; n++; set.add((d[i] >> 4) << 8 | (d[i + 1] >> 4) << 4 | (d[i + 2] >> 4)); }
        const m = s / n; return { sd: Math.sqrt(Math.max(0, s2 / n - m * m)), colors: set.size };
      }, a1.toString('base64'));
      if (stat.sd < 3 || stat.colors < 6) r.errors.push('the canvas is blank');
      const cx = clip.x + clip.width / 2, cy = clip.y + clip.height / 2;
      await pg.mouse.move(cx, cy); await pg.mouse.down(); await pg.mouse.move(cx + 140, cy + 50, { steps: 10 }); await pg.mouse.up(); await pg.waitForTimeout(900);
      const a2 = await pg.screenshot({ clip });
      r.dragChangesView = !a1.equals(a2);
      if (!r.dragChangesView) r.warnings.push('dragging the canvas did not change the view (frozen render loop or no orbit controls?)');
    }
    // stands upright? Compare the model's on-screen height share (three.js Y) with its height share in the CAD export.
    let mb = null;
    for (const f of pg.frames()) { mb = await f.evaluate(() => { const T = window.TwinModel; if (!T || !T.object || !T.THREE) return null;
      const b = new T.THREE.Box3().setFromObject(T.object); if (b.isEmpty()) return null; const s = b.getSize(new T.THREE.Vector3()); return [s.x, s.y, s.z]; }).catch(() => null); if (mb) break; }
    const glbFile = [...new Set(glbs)].map(g => path.join(projectDir, ...g.split('/'))).filter(f => fs.existsSync(f)).sort((a, b) => fs.statSync(b).size - fs.statSync(a).size)[0];
    if (mb && glbFile) {
      const g = glbFacts(glbFile);
      if (g) {
        const upIx = { X: 0, Y: 1, Z: 2 }[g.up] ?? 2, want = g.ext[upIx] / Math.max(...g.ext), got = mb[1] / Math.max(...mb);
        r.orientation = { glb: path.relative(projectDir, glbFile).replace(/\\/g, '/'), up: g.up, cadHeightShare: +want.toFixed(2), shownHeightShare: +got.toFixed(2) };
        if (Math.abs(want - got) > 0.15) r.errors.push(`the model is not standing upright: in the CAD export (${g.up}-up) its height is ${Math.round(want * 100)}% of its largest size, on screen ${Math.round(got * 100)}% - it is lying on its side or tipped (check the axis conversion; take "up" from assembly.json, not from the model's shape)`);
      }
    } else if (glbFile && t.simulator) r.warnings.push('orientation not checked: set window.TwinModel = { object: <the assembled model>, THREE } (or TwinLoad.model(object, THREE)) in the twin');
    if (shotsDir) { fs.mkdirSync(shotsDir, { recursive: true }); await pg.screenshot({ path: path.join(shotsDir, (ID + '__' + t.page).replace(/[\/\\:]/g, '_') + '.png') }); }
    r.errors = [...new Set(r.errors)]; r.status = r.errors.length ? 'FAIL' : 'PASS';
    results.push(r); await ctx.close();
    console.log(`${r.status}  ${t.page}  (${t.app}, ${r.loadSeconds}s)`); for (const e of r.errors.slice(0, 12)) console.log('   - ' + e); for (const w of r.warnings) console.log('   ~ ' + w);
  }
  if (br) await br.close(); if (srv) srv.close();
  for (const p of problems) { p.status = 'FAIL'; console.log(`FAIL  (${p.app})`); for (const e of p.errors) console.log('   - ' + e); }
  const out = { when: new Date().toISOString(), check: 'hub-style static sub-path, no server', project: ID, passed: results.filter(r => r.status === 'PASS').length, failed: results.filter(r => r.status !== 'PASS').length, pages: results };
  const dest = jsonOut || (fs.existsSync(path.join(projectDir, base, 'sim')) ? path.join(projectDir, base, 'sim', 'results', 'hub-check.json') : null);
  if (dest) { fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, JSON.stringify(out, null, 1)); console.log('wrote', dest); }
  console.log(out.failed ? `\nHUB CHECK FAILED: ${out.failed} of ${results.length} page(s). Fix them (see references/simulation.md, "Runs on the hub") and run this again.` : `\nHub check passed: ${out.passed} page(s).`);
  process.exit(out.failed ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
