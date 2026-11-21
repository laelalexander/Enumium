// Results view: lets the user see, inspect and run what an Anatomy project produced.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { ThreeMFLoader } from 'three/addons/loaders/3MFLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { loadXometry, xometryStage } from './xometry.js';

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ext = p => { const b = p.toLowerCase().split('/').pop(); if (b.endsWith('.gcode.3mf')) return 'gcode.3mf'; const i = b.lastIndexOf('.'); return i < 0 ? '' : b.slice(i + 1); };
const base = p => p.split('/').pop();
const stem = p => base(p).replace(/\.gcode\.3mf$/i, '').replace(/\.[^.]+$/, '');
const dirOf = p => p.includes('/') ? p.slice(0, p.lastIndexOf('/')) : '';
const human = n => n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : n > 1e3 ? Math.round(n / 1e3) + ' KB' : n + ' B';
const mmin = v => `${v.toFixed(1)} mm [${(v / 25.4).toFixed(3)} in]`;
const MODEL = ['stl', '3mf', 'obj', 'glb', 'gltf', 'step', 'stp'];
const IMG = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'];
const CODE = ['py', 'js', 'mjs', 'ts', 'c', 'cpp', 'h', 'hpp', 'ino', 'rs', 'go', 'sh', 'ini', 'toml', 'json', 'yaml', 'yml', 'txt', 'csv', 'net', 'rpt', 'log', 'scad'];

let S = null; // { id, files, md, api, preview, rawUrl }

export async function renderResults(host, ctx) {
  S = { ...ctx, files: ctx.files.filter(f => !/(^|\/)(\.venv|venv|\.tools|node_modules|__pycache__|\.pio|\.anatomy)\//.test(f.path)) };
  const manifest = await ctx.api(`/api/projects/${ctx.id}/manifest`).catch(() => ({}));
  S.manifest = manifest;
  if (manifest.title && ctx.setTitle) ctx.setTitle(manifest.title);
  const F = S.files;
  const has = pred => F.some(pred);
  const tabs = [
    ['overview', 'Overview', true],
    ['build', 'Build', true],
    ['sim', 'Simulate', true],
    ['run', 'Try it', (manifest.apps || []).length > 0 || has(f => /(^|\/)(index\.html)$/i.test(f.path) && !/assembly/i.test(f.path))],
    ['model', '3D model', has(f => MODEL.includes(ext(f.path)))],
    ['drawings', 'Drawings', has(f => (['pdf', 'svg', 'dxf'].includes(ext(f.path)) && /draw|blueprint|sheet|cut/i.test(f.path)) || (ext(f.path) === 'pdf'))],
    ['renders', 'Renders', has(f => IMG.includes(ext(f.path)))],
    ['bom', 'Parts (BOM)', has(f => /bom.*\.csv$/i.test(f.path))],
    ['print', '3D printing', has(f => ['gcode', 'gcode.3mf', 'bgcode'].includes(ext(f.path)) || (ext(f.path) === '3mf'))],
    ['electronics', 'Electronics', has(f => /kicad_|gerber|\.net$|\.rpt$/i.test(f.path))],
    ['software', 'Software', has(f => /platformio\.ini|package\.json|cmakelists\.txt|cargo\.toml|\.py$/i.test(f.path))],
    ['assembly', 'Assembly', has(f => /assembly|build-instructions/i.test(f.path) && /\.(html|md|pdf)$/i.test(f.path))],
    ['docs', 'Documents', has(f => ext(f.path) === 'md')],
  ].filter(t => t[2]);
  host.innerHTML = `<nav class="rtabs">${tabs.map(t => `<button data-t="${t[0]}">${t[1]}</button>`).join('')}</nav><div class="rbody" id="rbody"></div>`;
  const body = host.querySelector('#rbody');
  const show = t => {
    host.querySelectorAll('.rtabs button').forEach(b => b.classList.toggle('on', b.dataset.t === t));
    disposeViewer();
    body.innerHTML = '';
    ({ overview, build, sim, run, model, drawings, renders, bom, print, electronics, software, assembly, docs })[t](body);
    try { localStorage.setItem('anatomy.tab.' + S.id, t); } catch {}
  };
  host.querySelectorAll('.rtabs button').forEach(b => b.onclick = () => show(b.dataset.t));
  let start = 'overview'; try { start = localStorage.getItem('anatomy.tab.' + S.id) || 'overview'; } catch {}
  show(tabs.some(t => t[0] === start) ? start : 'overview');
}

const raw = p => `/p/${S.id}/${p.split('/').map(encodeURIComponent).join('/')}`;
const fetchText = p => fetch(`/api/projects/${S.id}/file?path=${encodeURIComponent(p)}`).then(r => r.text());
const openExt = p => S.api(`/api/projects/${S.id}/open?path=${encodeURIComponent(p)}`, { method: 'POST' });
const reveal = p => S.api(`/api/projects/${S.id}/reveal?path=${encodeURIComponent(p)}`, { method: 'POST' });
const btn = (label, fn, cls = 'ghost') => { const b = document.createElement('button'); b.className = cls; b.textContent = label; b.onclick = fn; return b; };
const sorted = list => list.slice().sort((a, b) => a.path.localeCompare(b.path));
function group(list) { const g = new Map(); for (const f of sorted(list)) { const d = dirOf(f.path); if (!g.has(d)) g.set(d, []); g.get(d).push(f); } return g; }
function shortDir(d) { const p = d.split('/'); return p.length > 3 ? '…/' + p.slice(-3).join('/') : d || '(project root)'; }

// ---------------------------------------------------------------- CSV
function parseCSV(t) {
  const rows = []; let row = [], cell = '', q = false;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (q) { if (c === '"') { if (t[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && t[i + 1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows.filter(r => r.some(x => x.trim()));
}
async function loadBom() {
  const f = sorted(S.files.filter(f => /bom.*\.csv$/i.test(f.path))).sort((a, b) => (/\/bom\.csv$/i.test(b.path) ? 1 : 0) - (/\/bom\.csv$/i.test(a.path) ? 1 : 0))[0];
  if (!f) return null;
  const rows = parseCSV(await fetchText(f.path)); if (rows.length < 2) return null;
  const head = rows[0].map(h => h.trim().toLowerCase());
  const col = (...names) => head.findIndex(h => names.some(n => h === n || h.includes(n)));
  const ix = { type: col('type'), ref: col('ref', 'line'), desc: col('description', 'desc'), mfr: col('manufacturer', 'mfr'), mpn: col('mpn', 'standard', 'part'),
    qty: col('qty', 'quantity'), price: col('unit_price', 'unit_cost', 'price', 'cost'), url: col('supplier_url', 'url', 'link', 'source'), supplier: col('supplier'),
    design: col('design_file', 'file'), status: col('status', 'verified') };
  const items = rows.slice(1).map(r => {
    const g = k => ix[k] >= 0 ? (r[ix[k]] || '').trim() : '';
    const qty = parseFloat(g('qty')) || 0, price = parseFloat(g('price').replace(/[^0-9.]/g, '')) || 0;
    let type = g('type').toUpperCase(); if (type === 'MAKE') type = 'BUILD';
    if (!type) type = g('design') ? 'BUILD' : 'BUY';
    const generic = /generic|tbd|assorted|as needed|^-?$/i.test(g('mpn')) || /generic/i.test(g('desc'));
    return { type, ref: g('ref'), desc: g('desc'), mfr: g('mfr'), mpn: g('mpn'), qty, price, url: g('url'), supplier: g('supplier'), design: g('design'), status: g('status'), generic, row: r };
  });
  return { file: f.path, head: rows[0], items, total: items.reduce((s, i) => s + i.qty * i.price, 0) };
}

// ---------------------------------------------------------------- Overview
async function overview(el) {
  const F = S.files;
  const meta = await S.api(`/api/projects/${S.id}`);
  const count = e => F.filter(f => e.includes(ext(f.path))).length;
  const bomP = loadBom().catch(() => null);
  const ov = sorted(F.filter(f => /(^|\/)(00-overview|readme|overview|summary)\.md$/i.test(f.path))).sort((a, b) => a.path.split('/').length - b.path.split('/').length);
  const hero = sorted(F.filter(f => ['png', 'jpg', 'jpeg'].includes(ext(f.path)) && /render/i.test(f.path))).sort((a, b) => (/(assembly|iso|hero|overview|mech)/i.test(b.path) ? 1 : 0) - (/(assembly|iso|hero|overview|mech)/i.test(a.path) ? 1 : 0)).slice(0, 4);
  el.innerHTML = `<div class="ov">
    <div class="hero">${hero.map(h => `<img src="${raw(h.path)}" data-p="${esc(h.path)}" loading="lazy">`).join('')}</div>
    <div class="kpis" id="kpis">
      <div><b>${count(['stl', '3mf', 'obj', 'glb'])}</b><span>3D parts</span></div>
      <div><b>${count(['step', 'stp'])}</b><span>CAD models</span></div>
      <div><b>${count(['pdf', 'svg', 'dxf'])}</b><span>drawings &amp; cut files</span></div>
      <div><b>${count(['gcode', 'gcode.3mf', 'bgcode'])}</b><span>G-code files</span></div>
    </div>
    <div class="ovtext say" id="ovtext"></div></div>`;
  el.querySelectorAll('.hero img').forEach(i => i.onclick = () => S.preview(i.dataset.p));
  bomP.then(b => {
    if (!b) return;
    const k = el.querySelector('#kpis');
    const gen = b.items.filter(i => i.generic).length;
    k.insertAdjacentHTML('afterbegin', `<div><b>${b.items.length}</b><span>BOM lines</span></div><div><b>$${b.total.toFixed(0)}</b><span>parts cost (1 unit)</span></div>` +
      (gen ? `<div class="warnk"><b>${gen}</b><span>parts not specific enough to buy</span></div>` : ''));
  });
  // Final run summary first, then the overview document.
  const summary = S.lastResult || '';
  const doc = ov[0] ? await fetchText(ov[0].path) : '';
  el.querySelector('#ovtext').innerHTML = (summary ? `<div class="summary"><div class="h"><span class="pill done">result</span> ${esc(meta.title)}</div>${S.md(summary)}</div>` : '') +
    (doc ? `<h3 style="color:var(--muted)">${esc(ov[0].path)}</h3>${S.md(doc)}` : '');
}

// ---------------------------------------------------------------- Try it (run the project's software)
async function run(el) {
  const m = S.manifest || {};
  const html = S.files.filter(f => /(^|\/)index\.html$/i.test(f.path) && !/assembly|node_modules/i.test(f.path));
  el.innerHTML = `<div class="tryit"><p class="lead">Run what this project built. Apps start on this PC and open in their own window.</p><div id="apps"></div><div id="statics"></div><pre class="applog hidden" id="applog"></pre></div>`;
  const appsEl = el.querySelector('#apps');
  (m.apps || []).forEach((a, n) => {
    const card = document.createElement('div'); card.className = 'appcard';
    card.innerHTML = `<div class="t">${esc(a.name)}</div><div class="d">${esc(a.description || '')}</div>${(a.needs || []).length ? `<div class="n">Needs: ${esc(a.needs.join(', '))}</div>` : ''}<div class="b"></div>`;
    const b = card.querySelector('.b');
    const start = btn(a.running ? 'Open' : 'Start', async () => {
      if (!a.running) { start.disabled = true; start.textContent = 'Starting…'; await S.api(`/api/projects/${S.id}/apps/${n}/start`, { method: 'POST' }); a.running = true; await new Promise(r => setTimeout(r, a.startup_ms || 4000)); start.disabled = false; start.textContent = 'Open'; }
      if (a.url) window.open(a.url, '_blank', 'width=1400,height=900');
      pollLog(n);
    }, 'primary');
    b.append(start, btn('Stop', async () => { await S.api(`/api/projects/${S.id}/apps/${n}/stop`, { method: 'POST' }); a.running = false; start.textContent = 'Start'; }), btn('Log', () => pollLog(n)));
    appsEl.append(card);
  });
  if (!(m.apps || []).length) appsEl.innerHTML = `<p class="empty">This project has no runnable app declared (an <code>anatomy.json</code> with an <code>apps</code> list). New projects add one automatically. Static pages it built are below.</p>`;
  if (m.error) appsEl.insertAdjacentHTML('afterbegin', `<div class="alert">${esc(m.error)}</div>`);
  const st = el.querySelector('#statics');
  if (html.length) st.innerHTML = `<p class="sect" style="margin-top:22px">Pages</p>` + html.map(f => `<div class="row1"><span>${esc(f.path)}</span><a href="${raw(f.path)}" target="_blank">Open</a></div>`).join('');
  let timer = null;
  async function pollLog(n) {
    const pre = el.querySelector('#applog'); pre.classList.remove('hidden'); clearInterval(timer);
    const tick = async () => { if (!document.body.contains(pre)) return clearInterval(timer); const r = await S.api(`/api/projects/${S.id}/apps/${n}/log`).catch(() => null); if (r) { pre.textContent = r.log || '(no output yet)'; pre.scrollTop = 1e9; } };
    tick(); timer = setInterval(tick, 1500);
  }
}

// ---------------------------------------------------------------- 3D viewer + part inspector
let V = null;
function disposeViewer() { if (V) { cancelAnimationFrame(V.raf); V.ro.disconnect(); V.renderer.dispose(); V = null; } }
function makeViewer(canvasHost) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  canvasHost.append(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0e1013);
  const cam = new THREE.PerspectiveCamera(40, 1, 0.1, 100000);
  cam.up.set(0, 0, 1);
  const ctl = new OrbitControls(cam, renderer.domElement); ctl.enableDamping = true;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.1));
  const d1 = new THREE.DirectionalLight(0xffffff, 1.4); d1.position.set(1, -1.2, 2); scene.add(d1);
  const d2 = new THREE.DirectionalLight(0x99aaff, 0.5); d2.position.set(-1, 1, 0.5); scene.add(d2);
  const grid = new THREE.GridHelper(1000, 50, 0x2a3140, 0x1b2029); grid.rotation.x = Math.PI / 2; scene.add(grid);
  const root = new THREE.Group(); scene.add(root);
  const ro = new ResizeObserver(() => { const w = canvasHost.clientWidth, h = canvasHost.clientHeight; renderer.setSize(w, h); cam.aspect = w / Math.max(h, 1); cam.updateProjectionMatrix(); });
  ro.observe(canvasHost);
  V = { renderer, scene, cam, ctl, root, grid, ro, raf: 0 };
  const loop = () => { V.raf = requestAnimationFrame(loop); ctl.update(); renderer.render(scene, cam); }; loop();
  return V;
}
function frame(obj) {
  const box = new THREE.Box3().setFromObject(obj); if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
  const r = Math.max(size.x, size.y, size.z) || 1;
  V.ctl.target.copy(c); V.cam.position.copy(c).add(new THREE.Vector3(r * 1.3, -r * 1.6, r * 1.1));
  V.cam.near = r / 500; V.cam.far = r * 50; V.cam.updateProjectionMatrix();
  V.grid.position.set(c.x, c.y, box.min.z); V.grid.scale.setScalar(Math.max(r / 400, 0.05));
}
const MAT = () => new THREE.MeshStandardMaterial({ color: 0x9fb4d9, metalness: 0.1, roughness: 0.55, flatShading: false });
let occtP = null;
async function loadOcct() {
  if (!occtP) occtP = new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.22/dist/occt-import-js.js';
    s.onload = () => window.occtimportjs({ locateFile: f => 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.22/dist/' + f }).then(res, rej); s.onerror = rej; document.head.append(s);
  });
  return occtP;
}
async function loadModel(p) {
  const e = ext(p), url = raw(p);
  if (e === 'stl') { const g = new STLLoader().parse(await (await fetch(url)).arrayBuffer()); g.computeVertexNormals(); return new THREE.Mesh(g, MAT()); }
  if (e === '3mf') return new ThreeMFLoader().parse(await (await fetch(url)).arrayBuffer());
  if (e === 'obj') return new OBJLoader().parse(await (await fetch(url)).text());
  if (e === 'glb' || e === 'gltf') {
    // glTF is Y-up by spec; this viewer is Z-up. CAD exporters (OCCT/cadquery) convert to Y-up, so turn the
    // scene back. Only a trimesh export with no root transform keeps the source Z-up axes as-is; leave just that case alone.
    const g = await new GLTFLoader().loadAsync(url);
    const js = g.parser?.json || {};
    const gen = String(js.asset?.generator || '');
    const roots = (js.scenes?.[js.scene || 0]?.nodes || []).map(i => js.nodes?.[i] || {});
    const rootXf = roots.some(n => n.matrix || n.rotation);   // e.g. trimesh writes a Y-up root matrix for Z-up sources
    if (!/trimesh/i.test(gen) || rootXf) { const wrap = new THREE.Group(); g.scene.rotation.x = Math.PI / 2; wrap.add(g.scene); wrap.updateMatrixWorld(true); return wrap; }
    return g.scene;
  }
  if (e === 'step' || e === 'stp') {
    const occt = await loadOcct();
    const r = occt.ReadStepFile(new Uint8Array(await (await fetch(url)).arrayBuffer()), null);
    const grp = new THREE.Group();
    for (const m of r.meshes) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(m.attributes.position.array, 3));
      if (m.attributes.normal) g.setAttribute('normal', new THREE.Float32BufferAttribute(m.attributes.normal.array, 3));
      g.setIndex(new THREE.Uint32BufferAttribute(Uint32Array.from(m.index.array), 1));
      const mat = MAT(); if (m.color) mat.color.setRGB(m.color[0], m.color[1], m.color[2]);
      grp.add(new THREE.Mesh(g, mat));
    }
    return grp;
  }
  throw new Error('unsupported');
}
function stats(obj) {
  const box = new THREE.Box3().setFromObject(obj); const s = box.getSize(new THREE.Vector3());
  let tris = 0, vol = 0;
  obj.traverse(o => {
    if (!o.isMesh) return; const g = o.geometry; const pos = g.attributes.position; const idx = g.index;
    const n = idx ? idx.count / 3 : pos.count / 3; tris += n;
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      const i0 = idx ? idx.getX(i * 3) : i * 3, i1 = idx ? idx.getX(i * 3 + 1) : i * 3 + 1, i2 = idx ? idx.getX(i * 3 + 2) : i * 3 + 2;
      a.fromBufferAttribute(pos, i0); b.fromBufferAttribute(pos, i1); c.fromBufferAttribute(pos, i2);
      vol += a.dot(b.clone().cross(c)) / 6;
    }
  });
  return { s, tris, vol: Math.abs(vol) };
}
function related(p) {
  const st = stem(p).toLowerCase().replace(/[-_ ]?(v\d+|rev\w)$/, '');
  const near = f => { const s = stem(f.path).toLowerCase(); return f.path !== p && (s === st || s.startsWith(st + '_') || s.startsWith(st + '-') || s.includes(st)); };
  return S.files.filter(near);
}
async function model(el) {
  const parts = sorted(S.files.filter(f => MODEL.includes(ext(f.path))));
  el.innerHTML = `<div class="mview"><aside class="plist" id="plist"></aside><div class="canvas" id="canvas"><div class="vhint" id="vhint">Pick a part on the left, or load a whole folder as an assembly.</div>
    <div class="vtools"><button class="ghost" id="vw">Wireframe</button><button class="ghost" id="vf">Fit</button></div></div><aside class="insp" id="insp"><p class="empty">Part details appear here.</p></aside></div>`;
  makeViewer(el.querySelector('#canvas'));
  const pl = el.querySelector('#plist');
  let html = '';
  for (const [d, list] of group(parts)) {
    const loadable = list.filter(f => ['stl', 'obj', '3mf', 'glb'].includes(ext(f.path)));
    html += `<div class="gd"><span title="${esc(d)}">${esc(shortDir(d))}</span>${loadable.length > 1 ? `<button class="mini" data-dir="${esc(d)}">Load all ${loadable.length}</button>` : ''}</div>`;
    html += list.map(f => `<div class="pi" data-p="${esc(f.path)}"><span>${esc(base(f.path))}</span><em>${ext(f.path).toUpperCase()}</em></div>`).join('');
  }
  pl.innerHTML = html || '<p class="empty">No 3D files.</p>';
  pl.onclick = async e => {
    const all = e.target.closest('button[data-dir]');
    if (all) return showMany(parts.filter(f => dirOf(f.path) === all.dataset.dir && ['stl', 'obj', '3mf', 'glb'].includes(ext(f.path))).map(f => f.path));
    const it = e.target.closest('.pi'); if (!it) return;
    pl.querySelectorAll('.pi').forEach(x => x.classList.toggle('on', x === it));
    showOne(it.dataset.p);
  };
  let wire = false;
  el.querySelector('#vw').onclick = () => { wire = !wire; V.root.traverse(o => { if (o.isMesh) o.material.wireframe = wire; }); };
  el.querySelector('#vf').onclick = () => frame(V.root);
  const insp = el.querySelector('#insp');
  const hint = el.querySelector('#vhint');
  async function showOne(p) {
    hint.textContent = ext(p).startsWith('st') && ext(p) !== 'stl' ? 'Loading STEP (first time downloads the STEP reader)…' : 'Loading…'; hint.classList.remove('hidden');
    V.root.clear();
    try { const o = await loadModel(p); V.root.add(o); frame(o); hint.classList.add('hidden'); inspect(p, o); }
    catch (err) { hint.textContent = 'Could not display this file here: ' + err.message + '. Use "Open in program".'; inspect(p, null); }
  }
  async function showMany(ps) {
    hint.textContent = `Loading ${ps.length} parts…`; hint.classList.remove('hidden'); V.root.clear();
    const colors = [0x9fb4d9, 0xd9b49f, 0x9fd9b4, 0xc79fd9, 0xd9d39f, 0x9fd3d9];
    let i = 0;
    for (const p of ps) { try { const o = await loadModel(p); o.traverse(m => { if (m.isMesh) m.material.color.setHex(colors[i % colors.length]); }); o.userData.path = p; V.root.add(o); i++; } catch {} }
    frame(V.root); hint.classList.add('hidden');
    insp.innerHTML = `<p class="sect">Assembly view</p><p class="empty">${i} parts loaded from their own coordinates. If the designer exported parts in place they show assembled; otherwise they overlap at the origin. Click a part in the list to inspect it.</p>`;
  }
  async function inspect(p, obj) {
    const rel = related(p);
    const pick = es => rel.filter(f => es.includes(ext(f.path)));
    const drawings = pick(['pdf', 'svg', 'dxf']), src = pick(['py', 'scad']), gcode = pick(['gcode', 'gcode.3mf', 'bgcode']), others = pick(['step', 'stp', 'stl', '3mf', 'obj']);
    const bom = await loadBom().catch(() => null);
    const st = stem(p).toLowerCase();
    const bomRow = bom && bom.items.find(i => (i.design && i.design.toLowerCase().includes(st)) || (i.desc && i.desc.toLowerCase().includes(st.replace(/[-_]/g, ' '))));
    let info = '';
    if (obj) {
      const s = stats(obj);
      info = `<table class="kv"><tr><td>X</td><td>${mmin(s.s.x)}</td></tr><tr><td>Y</td><td>${mmin(s.s.y)}</td></tr><tr><td>Z</td><td>${mmin(s.s.z)}</td></tr>
        <tr><td>Volume</td><td>${(s.vol / 1000).toFixed(1)} cm³ [${(s.vol / 16387.064).toFixed(2)} in³]</td></tr>
        <tr><td>PLA / PETG</td><td>≈ ${(s.vol / 1000 * 1.24).toFixed(0)} g / ${(s.vol / 1000 * 1.27).toFixed(0)} g solid</td></tr><tr><td>Triangles</td><td>${s.tris.toLocaleString()}</td></tr></table>`;
    }
    const list = (title, fs) => fs.length ? `<p class="sect">${title}</p>` + fs.map(f => `<div class="fl" data-p="${esc(f.path)}">${esc(base(f.path))}</div>`).join('') : '';
    insp.innerHTML = `<p class="pt">${esc(base(p))}</p><p class="pd">${esc(dirOf(p))}</p>${info}
      ${bomRow ? `<p class="sect">BOM</p><div class="bomrow"><span class="tag ${bomRow.type}">${bomRow.type}</span> ${esc(bomRow.ref)} ${esc(bomRow.desc)} × ${bomRow.qty}</div>` : ''}
      ${list('Drawings', drawings)}${list('CAD source', src)}${list('G-code', gcode)}${list('Other formats', others)}
      <div class="ib" id="ib"></div>`;
    insp.querySelectorAll('.fl').forEach(x => x.onclick = () => S.preview(x.dataset.p));
    const ib = insp.querySelector('#ib');
    ib.append(btn('Open in program', () => openExt(p)), btn('Show in folder', () => reveal(p)));
    const a = document.createElement('a'); a.href = raw(p); a.download = base(p); a.className = 'ghost'; a.textContent = 'Download'; ib.append(a);
    if (!gcode.length && ['stl', '3mf'].includes(ext(p))) ib.insertAdjacentHTML('beforebegin', `<p class="note">No G-code for this part yet.</p>`);
  }
}

// ---------------------------------------------------------------- galleries
function gallery(el, files, intro) {
  const g = group(files);
  el.innerHTML = (intro ? `<p class="lead">${intro}</p>` : '') + [...g].map(([d, list]) => `<p class="sect">${esc(shortDir(d))}</p><div class="gal">${list.map(f => {
    const e = ext(f.path);
    const thumb = IMG.includes(e) ? `<img src="${raw(f.path)}" loading="lazy">` : `<div class="ficon">${e.toUpperCase()}</div>`;
    return `<div class="gi" data-p="${esc(f.path)}">${thumb}<span>${esc(base(f.path))}</span></div>`;
  }).join('')}</div>`).join('');
  el.querySelectorAll('.gi').forEach(x => x.onclick = () => {
    const p = x.dataset.p, e = ext(p);
    if (['dxf', 'kicad_pro', 'kicad_pcb', 'kicad_sch', 'zip', 'step', 'stp', 'gcode.3mf', '3mf'].includes(e)) openExt(p); else S.preview(p);
  });
}
function drawings(el) {
  const fs = S.files.filter(f => ['pdf', 'svg', 'dxf'].includes(ext(f.path)) && !/render/i.test(f.path));
  gallery(el, fs, 'Click a PDF or SVG to view it. DXF cut files open in your CAD or cutting program.');
}
function renders(el) { gallery(el, S.files.filter(f => IMG.includes(ext(f.path))), ''); }

// ---------------------------------------------------------------- BOM
async function bom(el) {
  const b = await loadBom();
  if (!b) { el.innerHTML = '<p class="empty">No BOM found.</p>'; return; }
  const buy = b.items.filter(i => i.type === 'BUY'), build = b.items.filter(i => i.type === 'BUILD'), gen = b.items.filter(i => i.generic);
  el.innerHTML = `<div class="kpis"><div><b>${b.items.length}</b><span>lines</span></div><div><b>${buy.length}</b><span>to buy</span></div><div><b>${build.length}</b><span>to build</span></div><div><b>$${b.total.toFixed(2)}</b><span>parts cost, 1 unit</span></div>${gen.length ? `<div class="warnk"><b>${gen.length}</b><span>not specific enough to buy</span></div>` : ''}</div>
    <div class="bombar"><input id="bq" placeholder="Filter parts…"><div class="seg" id="bt"><button data-t="" class="on">All</button><button data-t="BUY">Buy</button><button data-t="BUILD">Build</button></div><span class="spacer"></span><span class="empty">${esc(b.file)}</span></div>
    <div class="tablewrap"><table class="bom" id="bomt"></table></div>`;
  let ft = '';
  const draw = () => {
    const q = el.querySelector('#bq').value.toLowerCase();
    const rows = b.items.filter(i => (!ft || i.type === ft) && (!q || i.row.join(' ').toLowerCase().includes(q)));
    el.querySelector('#bomt').innerHTML = `<tr><th></th><th>Ref</th><th>Description</th><th>Manufacturer</th><th>MPN / standard</th><th>Qty</th><th>Unit</th><th>Total</th><th>Where</th></tr>` + rows.map(i => `<tr class="${i.generic ? 'gen' : ''}">
      <td><span class="tag ${i.type}">${i.type}</span></td><td>${esc(i.ref)}</td><td>${esc(i.desc)}${i.generic ? ' <span class="gtag">not specific</span>' : ''}</td><td>${esc(i.mfr)}</td><td><code>${esc(i.mpn)}</code></td>
      <td>${i.qty || ''}</td><td>${i.price ? '$' + i.price.toFixed(2) : ''}</td><td>${i.price ? '$' + (i.qty * i.price).toFixed(2) : ''}</td>
      <td>${/^https?:/.test(i.url) ? `<a href="${esc(i.url)}" target="_blank">${esc(i.supplier || new URL(i.url).host)}</a>` : i.design ? `<a class="file" data-path="${esc(i.design)}">${esc(base(i.design))}</a>` : esc(i.url || i.supplier)}</td></tr>`).join('');
  };
  el.querySelector('#bq').oninput = draw;
  el.querySelector('#bt').onclick = e => { if (e.target.dataset.t === undefined) return; ft = e.target.dataset.t; el.querySelectorAll('#bt button').forEach(x => x.classList.toggle('on', x === e.target)); draw(); };
  draw();
}

// ---------------------------------------------------------------- 3D printing
function gcodeMeta(t) {
  const m = {};
  const g = re => { const x = t.match(re); return x ? x[1].trim() : ''; };
  m.time = g(/estimated printing time \(normal mode\)\s*=\s*(.+)/i) || g(/;\s*total estimated time:\s*(.+)/i) || g(/;TIME:(\d+)/);
  m.grams = g(/filament used \[g\]\s*=\s*([\d.]+)/i) || g(/total filament weight \[g\]\s*:\s*([\d.]+)/i);
  m.meters = g(/filament used \[mm\]\s*=\s*([\d.]+)/i);
  m.layer = g(/layer_height\s*=\s*([\d.]+)/i);
  m.mat = g(/filament_type\s*=\s*(\S+)/i);
  m.printer = g(/printer_model\s*=\s*(.+)/i) || g(/printer_settings_id\s*=\s*(.+)/i);
  return m;
}
async function print(el) {
  const gs = sorted(S.files.filter(f => ['gcode', 'gcode.3mf', 'bgcode'].includes(ext(f.path))));
  const projects = sorted(S.files.filter(f => ext(f.path) === '3mf'));
  const plan = S.files.find(f => /print-plan\.md$/i.test(f.path));
  const stls = S.files.filter(f => ['stl', '3mf'].includes(ext(f.path)));
  el.innerHTML = `<div class="printv"><aside class="plist" id="gl"></aside><div><div class="canvas" id="gcanvas"><div class="vhint" id="ghint">${gs.length ? 'Pick a G-code file to preview its toolpath.' : `No G-code yet. ${stls.length} printable model files are in the 3D model tab.`}</div></div>
    <div class="layerbar"><input type="range" id="layer" min="0" max="0" value="0" disabled><span id="lnum"></span></div><div id="gmeta" class="gmeta"></div></div></div>
    ${plan ? '<div class="say" id="plan" style="margin-top:18px"></div>' : ''}`;
  if (plan) fetchText(plan.path).then(t => el.querySelector('#plan').innerHTML = S.md(t));
  const gl = el.querySelector('#gl');
  gl.innerHTML = (gs.length ? `<p class="sect">G-code</p>` + gs.map(f => `<div class="pi" data-p="${esc(f.path)}"><span>${esc(base(f.path))}</span><em>${human(f.size)}</em></div>`).join('') : '') +
    (projects.length ? `<p class="sect" style="margin-top:14px">Slicer projects</p>` + projects.map(f => `<div class="pi" data-open="${esc(f.path)}"><span>${esc(base(f.path))}</span><em>open</em></div>`).join('') : '');
  makeViewer(el.querySelector('#gcanvas'));
  gl.onclick = async e => {
    const it = e.target.closest('.pi'); if (!it) return;
    if (it.dataset.open) return openExt(it.dataset.open);
    gl.querySelectorAll('.pi').forEach(x => x.classList.toggle('on', x === it));
    const p = it.dataset.p; const hint = el.querySelector('#ghint');
    const meta = el.querySelector('#gmeta');
    meta.innerHTML = ''; meta.append(btn('Open in slicer', () => openExt(p)), btn('Show in folder', () => reveal(p)));
    if (ext(p) !== 'gcode') { hint.textContent = 'This is a packaged printer file (Bambu .gcode.3mf or binary G-code). Open it in your slicer to preview and send it to the printer.'; hint.classList.remove('hidden'); V.root.clear(); return; }
    const f = S.files.find(x => x.path === p);
    if (f.size > 60e6) { hint.textContent = 'This file is too large to preview here. Open it in your slicer.'; return; }
    hint.textContent = 'Reading G-code…'; hint.classList.remove('hidden');
    const t = await fetchText(p);
    const m = gcodeMeta(t);
    meta.insertAdjacentHTML('afterbegin', `<span>${m.printer ? esc(m.printer) + ' · ' : ''}${m.mat ? esc(m.mat) + ' · ' : ''}${m.layer ? m.layer + ' mm layers · ' : ''}${m.time ? '⏱ ' + esc(m.time) + ' · ' : ''}${m.grams ? m.grams + ' g' : ''}</span>`);
    drawToolpath(t, el); hint.classList.add('hidden');
  };
}
function drawToolpath(t, el) {
  V.root.clear();
  const layers = []; let cur = []; let x = NaN, y = NaN, z = 0, e = 0, rel = false, relE = false, lastZ = -1;
  for (const line of t.split('\n')) {
    const c = line.split(';')[0].trim(); if (!c) continue;
    const cmd = c.split(/\s+/)[0].toUpperCase();
    if (cmd === 'G90') rel = false; else if (cmd === 'G91') rel = true; else if (cmd === 'M83') relE = true; else if (cmd === 'M82') relE = false;
    else if (cmd === 'G92') { const m = c.match(/E(-?[\d.]+)/i); if (m) e = +m[1]; }
    else if (cmd === 'G0' || cmd === 'G1') {
      let nx = x, ny = y, nz = z, ne = e, ext = false;
      for (const w of c.split(/\s+/).slice(1)) {
        const k = w[0].toUpperCase(), v = parseFloat(w.slice(1)); if (isNaN(v)) continue;
        if (k === 'X') nx = rel ? x + v : v; else if (k === 'Y') ny = rel ? y + v : v; else if (k === 'Z') nz = rel ? z + v : v;
        else if (k === 'E') { ne = relE ? e + v : v; ext = (relE ? v : v - e) > 0; }
      }
      if (nz !== z && nz > lastZ) { if (cur.length) layers.push(cur); cur = []; lastZ = nz; }
      if (ext && !isNaN(x) && !isNaN(y) && (nx !== x || ny !== y)) cur.push(x, y, z, nx, ny, nz);
      x = nx; y = ny; z = nz; e = ne;
    }
  }
  if (cur.length) layers.push(cur);
  const lines = layers.map((seg, i) => {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(seg, 3));
    const col = new THREE.Color().setHSL(0.6 - 0.6 * (i / Math.max(layers.length - 1, 1)), 0.7, 0.6);
    const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: col })); V.root.add(l); return l;
  });
  frame(V.root);
  const r = el.querySelector('#layer'), n = el.querySelector('#lnum');
  r.max = Math.max(lines.length - 1, 0); r.value = r.max; r.disabled = !lines.length;
  const upd = () => { const k = +r.value; lines.forEach((l, i) => { l.visible = i <= k; l.material.opacity = 1; }); n.textContent = `layer ${k + 1} / ${lines.length}`; };
  r.oninput = upd; upd();
}

// ---------------------------------------------------------------- electronics, software, assembly, docs
function electronics(el) {
  const fs = S.files.filter(f => /kicad|gerber|electr|pcb|schem|fab/i.test(f.path) && !/\.py$|\.sh$/.test(f.path));
  const proj = fs.filter(f => ext(f.path) === 'kicad_pro');
  el.innerHTML = `<p class="lead">Board files, renders and check reports. ${proj.length ? 'Open the KiCad project to edit the schematic and board.' : ''}</p><div id="kbtn" class="ib"></div><div id="kgal"></div><div id="rpts"></div>`;
  proj.forEach(p => el.querySelector('#kbtn').append(btn('Open ' + base(p.path) + ' in KiCad', () => openExt(p.path), 'primary')));
  const sub = document.createElement('div'); el.querySelector('#kgal').append(sub);
  gallery(sub, fs.filter(f => !['rpt', 'log', 'json', 'ses', 'dsn', ''].includes(ext(f.path))), '');
  const rpts = fs.filter(f => ext(f.path) === 'rpt');
  Promise.all(rpts.map(async f => ({ f, t: await fetchText(f.path) }))).then(rs => {
    el.querySelector('#rpts').innerHTML = rs.map(({ f, t }) => {
      const errs = (t.match(/\*\* Found (\d+) (DRC|ERC) violations?/i) || t.match(/(\d+)\s+(errors?|violations?)/i) || [])[1];
      return `<p class="sect" style="margin-top:18px">${esc(base(f.path))} ${errs !== undefined ? `<span class="pill ${+errs ? 'failed' : 'done'}">${errs} issues</span>` : ''}</p><pre class="code small">${esc(t.slice(0, 4000))}</pre>`;
    }).join('');
  });
}
async function software(el) {
  const roots = S.files.filter(f => /(^|\/)(platformio\.ini|package\.json|cmakelists\.txt|cargo\.toml|requirements\.txt|pyproject\.toml)$/i.test(f.path)).map(f => dirOf(f.path));
  const code = sorted(S.files.filter(f => CODE.includes(ext(f.path)) || ['md'].includes(ext(f.path)) && /software|firmware/i.test(f.path)).filter(f => /software|firmware|src|bridge|console|app/i.test(f.path)));
  el.innerHTML = `<div class="sw"><aside class="plist" id="sl"></aside><div class="swmain"><div id="swinfo"></div><pre class="code" id="swcode">Pick a file to read its source.</pre></div></div>`;
  el.querySelector('#swinfo').innerHTML = roots.length ? `<p class="sect">Projects</p>` + [...new Set(roots)].map(r => {
    const kind = S.files.some(f => f.path === (r ? r + '/' : '') + 'platformio.ini') ? 'Firmware (PlatformIO)' : S.files.some(f => f.path === (r ? r + '/' : '') + 'package.json') ? 'Node.js' : 'Software';
    return `<div class="row1"><span><b>${kind}</b> ${esc(r || '(root)')}</span><a class="file" data-reveal="${esc(r)}">Show in folder</a></div>`;
  }).join('') + `<p class="note">To run the software, use the Try it tab.</p>` : '';
  el.querySelectorAll('[data-reveal]').forEach(a => a.onclick = () => reveal(a.dataset.reveal));
  let h = ''; for (const [d, list] of group(code)) h += `<div class="gd"><span>${esc(shortDir(d))}</span></div>` + list.map(f => `<div class="pi" data-p="${esc(f.path)}"><span>${esc(base(f.path))}</span><em>${human(f.size)}</em></div>`).join('');
  const sl = el.querySelector('#sl'); sl.innerHTML = h || '<p class="empty">No source files.</p>';
  sl.onclick = async e => { const it = e.target.closest('.pi'); if (!it) return; sl.querySelectorAll('.pi').forEach(x => x.classList.toggle('on', x === it)); const t = await fetchText(it.dataset.p); const pre = el.querySelector('#swcode'); if (ext(it.dataset.p) === 'md') { pre.outerHTML = `<div class="say code" id="swcode">${S.md(t)}</div>`; } else { const nw = document.createElement('pre'); nw.className = 'code'; nw.id = 'swcode'; nw.textContent = t; el.querySelector('#swcode').replaceWith(nw); } };
}
async function assembly(el) {
  const html = S.files.find(f => /assembly.*\.html$/i.test(f.path));
  const pdf = S.files.find(f => /assembly.*\.pdf$/i.test(f.path));
  const md = S.files.find(f => /(assembly-guide|build-instructions)\.md$/i.test(f.path));
  if (html) { el.innerHTML = `<iframe class="fullframe" src="${raw(html.path)}"></iframe>`; return; }
  if (pdf) { el.innerHTML = `<iframe class="fullframe" src="${raw(pdf.path)}"></iframe>`; return; }
  el.innerHTML = `<div class="say doc">${md ? S.md(await fetchText(md.path)) : '<p class="empty">No assembly guide.</p>'}</div>`;
}
async function docs(el) {
  const mds = sorted(S.files.filter(f => ext(f.path) === 'md'));
  el.innerHTML = `<div class="sw"><aside class="plist" id="dl"></aside><div class="swmain"><div class="say doc" id="doc"></div></div></div>`;
  let h = ''; for (const [d, list] of group(mds)) h += `<div class="gd"><span>${esc(shortDir(d))}</span></div>` + list.map(f => `<div class="pi" data-p="${esc(f.path)}"><span>${esc(base(f.path))}</span></div>`).join('');
  const dl = el.querySelector('#dl'); dl.innerHTML = h;
  const open = async p => { dl.querySelectorAll('.pi').forEach(x => x.classList.toggle('on', x.dataset.p === p)); el.querySelector('#doc').innerHTML = S.md(await fetchText(p)); };
  dl.onclick = e => { const it = e.target.closest('.pi'); if (it) open(it.dataset.p); };
  const first = mds.find(f => /00-overview|readme/i.test(f.path)) || mds[0]; if (first) open(first.path);
}

// ---------------------------------------------------------------- Simulate: digital twin + test environment
const SIM_PROMPT = `Build the simulator and test environment for this project, following references/simulation.md of the anatomy skill exactly. The desktop robot arm test table is the bar.
Build a digital twin in sim/ from this project's own assembly and numbers. It needs:
- the assembled 3D model with real joints and limits;
- a behaviour model of the actuators, sensors, loads and power, using the design's datasheet values;
- the firmware in the loop, speaking its real command protocol;
- controls, live checks and an E-stop;
- automated test scenarios traced to the blueprint's requirements, with pass/fail and margins;
- headless test runs that write sim/results/latest.json;
- a hardware link that drives the real device from the same UI.
Add it to anatomy.json as an app with "kind": "simulator", plus a "tests" entry {"cwd", "run", "results"} for the headless run. Start it, run every scenario, look at the result, and report any failures as design findings.`;
async function sim(el) {
  const m = S.manifest || {}, apps = m.apps || [];
  let n = apps.findIndex(a => a.kind === 'simulator');
  if (n < 0) n = apps.findIndex(a => /simulator|digital twin|test table/i.test(a.name + ' ' + (a.description || '')));
  const resPath = (m.tests && m.tests.results ? ((m._base ? m._base + '/' : '') + m.tests.results) : null)
    || (S.files.find(f => /(^|\/)sim\/results\/latest\.json$/i.test(f.path)) || S.files.find(f => /results\/latest\.json$/i.test(f.path)) || {}).path;
  if (n < 0) {
    el.innerHTML = `<div class="buildintro"><h2>Simulate and test before you build</h2>
      <p class="lead">Anatomy builds a working digital twin of this product. It's made from the same assembly, parts and firmware as the build package, so you can drive it, load it and run its tests on this PC with no hardware. When the real device is connected, the same window drives it too.</p>
      <ol class="bsteps"><li>3D twin with real joints and limits</li><li>Actuators, sensors, loads and power from the datasheets</li><li>Firmware in the loop on its real command protocol</li><li>Automated tests traced to the requirements, with pass/fail and margins</li><li>Hardware link to the real device</li></ol>
      <div class="ib"></div><p class="empty">This runs Claude on the project and can take a while. You can watch it in the Live view.</p></div>`;
    el.querySelector('.ib').append(btn('Build the simulator', () => S.startRun(SIM_PROMPT), 'primary'));
    return;
  }
  const a = apps[n];
  el.innerHTML = `<div class="tryit"><div class="appcard"><div class="t">${esc(a.name)}</div><div class="d">${esc(a.description || '')}</div>${(a.needs || []).length ? `<div class="n">Needs: ${esc(a.needs.join(', '))}</div>` : ''}<div class="b"></div></div>
    <p class="sect" style="margin-top:18px">Test results</p><div id="simres"></div><pre class="applog hidden" id="simlog"></pre></div>`;
  const b = el.querySelector('.b');
  const open = btn('Open simulator', async () => {
    open.disabled = true; open.textContent = 'Starting…';
    await S.api(`/api/projects/${S.id}/apps/${n}/start`, { method: 'POST' }).catch(() => {});
    await new Promise(r => setTimeout(r, a.startup_ms || 4000)); open.disabled = false; open.textContent = 'Open simulator';
    if (a.url) window.open(a.url, '_blank', 'width=1500,height=950');
  }, 'primary');
  b.append(open);
  if (m.tests && m.tests.run) b.append(btn('Run all tests', async e => {
    const t = e.target; t.disabled = true; t.textContent = 'Running tests…';
    const r = await S.api(`/api/projects/${S.id}/simtest`, { method: 'POST' }).catch(x => ({ code: -1, log: x.message }));
    t.disabled = false; t.textContent = 'Run all tests';
    const pre = el.querySelector('#simlog'); pre.classList.remove('hidden'); pre.textContent = (r.log || '').trim() || `(exit code ${r.code})`;
    showRes(r.results || resPath);
  }));
  b.append(btn('Rebuild simulator', () => { if (confirm('Run Claude again to rebuild the simulator and its tests?')) S.startRun(SIM_PROMPT); }));
  async function showRes(p) {
    const box = el.querySelector('#simres');
    if (!p) { box.innerHTML = '<p class="empty">No results yet. Run all tests, or run them from inside the simulator.</p>'; return; }
    const R = await fetch(`/api/projects/${S.id}/file?path=${encodeURIComponent(p)}`, { cache: 'no-store' }).then(r => r.ok ? r.json() : null).catch(() => null);
    if (!R || !Array.isArray(R.tests)) { box.innerHTML = '<p class="empty">No results yet. Run all tests, or run them from inside the simulator.</p>'; return; }
    const cnt = k => R.tests.filter(t => t.result === k).length;
    const col = { pass: 'var(--ok, #4ade80)', fail: 'var(--bad, #f87171)', warn: '#fbbf24' };
    box.innerHTML = `<p class="lead">${cnt('pass')} passed · ${cnt('fail')} failed · ${cnt('warn')} warnings${R.when ? ` · ${esc(new Date(R.when).toLocaleString())}` : ''}</p>
      <table class="bom"><tr><th>Test</th><th>Requirement</th><th>Result</th><th>Margin</th><th>Detail</th></tr>${R.tests.map(t => `<tr><td>${esc(t.name)}</td><td>${esc(t.requirement || '')}</td><td style="color:${col[t.result] || 'inherit'};font-weight:600">${esc(t.result)}</td><td>${esc(t.margin ?? '')}</td><td>${esc(t.detail || '')}</td></tr>`).join('')}</table>`;
  }
  showRes(resPath);
}

// ---------------------------------------------------------------- Build wizard
const BUILD_PROMPT = `Prepare the build package for this project, following references/build-package.md of the anatomy skill exactly.
Turn the existing design into something a person can actually build: build/build.json plus the purchase list with per-supplier cart files, the 3D print list with G-code sliced for my printer (see the settings), fabrication files (DXF cut files in mm and inch, and for every custom board a turnkey PCBA order zip from tools/pcba/pcba_export.py per references/pcba-export.md, ready for RushPCB), illustrated step-by-step assembly instructions with a rendered picture per step, and firmware flashing and test steps.
First fix anything that blocks a real build: replace generic or unverified BOM parts with exact orderable parts, add BUILD lines for every printed or fabricated part, slice every printed part, and bring drawings up to the drawing standard. Run the BOM and build.json checks and report what is still open.`;
const STAGES = [['purchase', 'Order parts'], ['print', 'Print parts'], ['xometry', 'Xometry'], ['fabricate', 'Fabricate'], ['assembly', 'Assemble'], ['firmware', 'Firmware & test']];
async function build(el) {
  const B = await S.api(`/api/projects/${S.id}/build`).catch(() => ({}));
  if (!B || (!B.purchase && !B.print && !B.assembly)) {
    el.innerHTML = `<div class="buildintro"><h2>Turn this design into a build</h2>
      <p class="lead">Anatomy prepares everything a person needs to build this for real: a purchase list with supplier carts, the 3D print list with G-code for your printer, cut and fabrication files, illustrated assembly steps, and firmware and test steps. Then this tab walks you through ordering, printing, assembling and testing, and keeps track of your progress.</p>
      ${B && B.error ? `<div class="alert">${esc(B.error)}</div>` : ''}
      <ol class="bsteps">${STAGES.map(s => `<li>${s[1]}</li>`).join('')}</ol>
      <div class="ib"></div><p class="empty">This runs Claude on the project and can take a while. You can watch it in the Live view.</p></div>`;
    el.querySelector('.ib').append(btn('Prepare build package', () => S.startRun(BUILD_PROMPT), 'primary'));
    return;
  }
  let state = await S.api(`/api/projects/${S.id}/build-state`).catch(() => ({})) || {};
  const save = () => S.api(`/api/projects/${S.id}/build-state`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state) });
  const key = (st, id, f) => `${st}:${id}:${f}`;
  let XO = await loadXometry(S);
  const toXo = name => (XO.parts || []).some(p => p.route === 'xometry' && p.key === name);
  const items = {
    purchase: (B.purchase || []).map((p, i) => ({ id: p.line || 'p' + i, fields: ['ordered', 'received'] })),
    print: (B.print || []).filter(p => !toXo(p.part)).map((p, i) => ({ id: p.part || 'r' + i, fields: ['printed'] })),
    xometry: (XO.parts || []).filter(p => p.route === 'xometry').map(p => ({ id: p.key, fields: ['ordered', 'received'] })),
    fabricate: (B.fabricate || []).filter(p => !toXo(p.part)).map((p, i) => ({ id: p.part || 'f' + i, fields: ['done'] })),
    assembly: (B.assembly || []).map((p, i) => ({ id: 's' + (p.step || i + 1), fields: ['done'] })),
    firmware: [...(B.firmware || []).map((p, i) => ({ id: 'fw' + i, fields: ['done'] })), ...(B.tests || []).map((p, i) => ({ id: 't' + i, fields: ['done'] }))],
  };
  const pct = st => { const its = items[st]; if (!its.length) return null; const last = its.map(i => state[key(st, i.id, i.fields[i.fields.length - 1])]); return Math.round(100 * last.filter(Boolean).length / its.length); };
  const allPct = () => { const ps = STAGES.map(s => pct(s[0])).filter(p => p !== null); return ps.length ? Math.round(ps.reduce((a, b) => a + b, 0) / ps.length) : 0; };
  const T = B.totals || {};
  const lineName = l => { const p = (B.purchase || []).find(x => x.line === l) || (B.print || []).find(x => x.line === l || x.part === l) || (B.fabricate || []).find(x => x.part === l); return p ? (p.desc || p.part) : l; };
  el.innerHTML = `<div class="bhead"><div><h2>${esc(B.title || 'Build')}</h2><p class="lead">${esc(B.summary || '')}</p></div>
    <div class="kpis">${T.parts_cost ? `<div><b>$${(+T.parts_cost).toFixed(0)}</b><span>parts</span></div>` : ''}${T.print_hours ? `<div><b>${T.print_hours} h</b><span>printing</span></div>` : ''}
    ${T.filament_g ? `<div><b>${Object.entries(T.filament_g).map(([k, v]) => `${v} g`).join(' + ')}</b><span>${Object.keys(T.filament_g).join(', ')}</span></div>` : ''}${T.build_hours ? `<div><b>${T.build_hours} h</b><span>assembly</span></div>` : ''}
    <div><b id="allpct">0%</b><span>built</span></div></div></div>
    ${(B.tools || []).length ? `<p class="tools"><b>Tools:</b> ${esc(B.tools.join(' · '))}</p>` : ''}
    <nav class="stages" id="stages"></nav><div id="stage"></div>`;
  const nav = el.querySelector('#stages');
  const renderNav = () => {
    nav.innerHTML = STAGES.map(([k, n], i) => { const p = pct(k); const off = p === null && !(k === 'xometry' && (XO.parts || []).length); return `<button data-s="${k}" class="${cur === k ? 'on' : ''} ${p === 100 ? 'done' : ''}" ${off ? 'disabled' : ''}><i>${p === 100 ? '✓' : i + 1}</i>${n}<em>${p === null ? '—' : p + '%'}</em></button>`; }).join('');
    el.querySelector('#allpct').textContent = allPct() + '%';
  };
  let cur = STAGES.find(s => pct(s[0]) !== null && pct(s[0]) < 100)?.[0] || 'purchase';
  nav.onclick = e => { const b = e.target.closest('button[data-s]'); if (b && !b.disabled) { cur = b.dataset.s; renderNav(); draw(); } };
  const box = el.querySelector('#stage');
  const check = (st, id, f, label) => `<label class="chk"><input type="checkbox" data-k="${esc(key(st, id, f))}" ${state[key(st, id, f)] ? 'checked' : ''}> ${label}</label>`;
  box.addEventListener('change', e => { const k = e.target.dataset.k; if (!k) return; state[k] = e.target.checked; save(); renderNav(); });
  const fileBtns = p => p ? `<a class="file" data-path="${esc(p)}">${esc(base(p))}</a> <button class="mini" data-open="${esc(p)}">open</button> <button class="mini" data-reveal="${esc(p)}">folder</button>` : '';
  box.addEventListener('click', e => { const o = e.target.closest('[data-open]'); if (o) openExt(o.dataset.open); const r = e.target.closest('[data-reveal]'); if (r) reveal(r.dataset.reveal);
    const all = e.target.closest('[data-openall]'); if (all) (B.purchase || []).filter(p => (p.supplier || 'Other') === all.dataset.openall && p.url).forEach(p => window.open(p.url, '_blank')); });
  let stepIx = 0;
  function draw() {
    if (cur === 'purchase') {
      const groups = new Map(); (B.purchase || []).forEach(p => { const s = p.supplier || 'Other'; if (!groups.has(s)) groups.set(s, []); groups.get(s).push(p); });
      const carts = S.files.filter(f => /cart.*\.csv$|order.*\.csv$/i.test(f.path));
      box.innerHTML = (carts.length ? `<p class="lead">Supplier carts ready to upload: ${carts.map(c => fileBtns(c.path)).join(' · ')}</p>` : '') + [...groups].map(([s, list]) => {
        const sub = list.reduce((a, p) => a + (+p.qty || 0) * (+p.unit_price || 0), 0);
        return `<div class="sgroup"><div class="sgh"><b>${esc(s)}</b><span>${list.length} items · $${sub.toFixed(2)}</span><button class="mini" data-openall="${esc(s)}">open all links</button></div>
          <table class="bom"><tr><th>Ordered</th><th>Received</th><th>Part</th><th>MPN</th><th>Qty</th><th>Unit</th><th>Link</th></tr>${list.map(p => `<tr>
          <td>${check('purchase', p.line, 'ordered', '')}</td><td>${check('purchase', p.line, 'received', '')}</td>
          <td>${esc(p.desc)}<div class="empty">${esc(p.line || '')} ${esc(p.mfr || '')}${p.alt ? ' · alt: ' + esc(p.alt) : ''}</div></td><td><code>${esc(p.mpn || '')}</code></td><td>${esc(p.qty)}</td>
          <td>${p.unit_price ? '$' + (+p.unit_price).toFixed(2) : ''}</td><td>${p.url ? `<a href="${esc(p.url)}" target="_blank">buy</a>` : ''}</td></tr>`).join('')}</table></div>`;
      }).join('');
    } else if (cur === 'print') {
      const plates = new Map(); (B.print || []).forEach(p => { const k = p.plate || '—'; if (!plates.has(k)) plates.set(k, []); plates.get(k).push(p); });
      const tot = (B.print || []).reduce((a, p) => ({ t: a.t + (+p.time_min || 0) * (+p.qty || 1), g: a.g + (+p.grams || 0) * (+p.qty || 1) }), { t: 0, g: 0 });
      box.innerHTML = `<p class="lead">${(B.print || []).length} parts · ${(tot.t / 60).toFixed(1)} h · ${Math.round(tot.g)} g of filament. Open each G-code in your slicer to send it to the printer.</p>` + [...plates].map(([pl, list]) => `<div class="sgroup"><div class="sgh"><b>Plate ${esc(pl)}</b></div>
        <table class="bom"><tr><th>Printed</th><th>Part</th><th>Qty</th><th>Material</th><th>Time</th><th>Weight</th><th>G-code</th><th>After printing / check</th></tr>${list.map(p => `<tr>
        <td>${toXo(p.part) ? '<span class="gtag xo-tag">Xometry</span>' : check('print', p.part, 'printed', '')}</td><td><b>${esc(p.part)}</b><div class="empty">${esc(p.orientation || '')}${p.supports ? ' · supports: ' + esc(p.supports) : ''}</div></td><td>${esc(p.qty || 1)}</td><td>${esc(p.material || '')}</td>
        <td>${p.time_min ? Math.floor(p.time_min / 60) + 'h ' + (p.time_min % 60) + 'm' : ''}</td><td>${p.grams ? p.grams + ' g' : ''}</td><td>${p.gcode ? fileBtns(p.gcode) : '<span class="gtag">not sliced</span>'}</td>
        <td>${esc(p.after || '')}${(p.checks || []).length ? '<ul>' + p.checks.map(c => `<li>${esc(c)}</li>`).join('') + '</ul>' : ''}</td></tr>`).join('')}</table></div>`).join('');
    } else if (cur === 'xometry') {
      xometryStage(box, { id: S.id, api: S.api, raw, R: XO, check, fileBtns, reveal,
        onChange: R => { XO = R; items.print = (B.print || []).filter(p => !toXo(p.part)).map((p, i) => ({ id: p.part || 'r' + i, fields: ['printed'] }));
          items.xometry = XO.parts.filter(p => p.route === 'xometry').map(p => ({ id: p.key, fields: ['ordered', 'received'] }));
          items.fabricate = (B.fabricate || []).filter(p => !toXo(p.part)).map((p, i) => ({ id: p.part || 'f' + i, fields: ['done'] })); renderNav(); } });
    } else if (cur === 'fabricate') {
      box.innerHTML = (B.fabricate || []).map(f => `<div class="appcard"><div class="t">${toXo(f.part) ? '<span class="gtag xo-tag">Xometry</span>' : check('fabricate', f.part, 'done', '')} ${esc(f.part)} <span class="empty">· ${esc(f.process || '')}${f.qty ? ' · qty ' + esc(f.qty) : ''}</span></div>
        ${f.pcba_package ? `<div class="checkbox-note"><b>Turnkey PCBA order package:</b> ${fileBtns(f.pcba_package)} Upload the Gerber zip, BOM, centroid and drawings listed in its README; type the values from its QUOTE-SHEET.md into the quote form.</div>` : ''}
        <div class="d">${f.vendor ? 'Vendor: ' + esc(f.vendor) + '. ' : ''}${f.material ? 'Material: ' + esc(f.material) + '. ' : ''}${esc(f.settings || '')}</div>
        <div>${(f.files || []).map(fileBtns).join('<br>')}</div></div>`).join('');
    } else if (cur === 'assembly') {
      const steps = B.assembly || []; if (!steps.length) { box.innerHTML = '<p class="empty">No steps.</p>'; return; }
      stepIx = Math.min(stepIx, steps.length - 1);
      const s = steps[stepIx], id = 's' + (s.step || stepIx + 1);
      box.innerHTML = `<div class="astep"><div class="aimg">${s.image ? `<img src="${raw(s.image)}" data-p="${esc(s.image)}">` : '<div class="empty">No picture for this step.</div>'}</div>
        <div class="atext"><p class="sect">Step ${stepIx + 1} of ${steps.length}</p><h2>${esc(s.title || '')}</h2><div class="say">${S.md(s.text || '')}</div>
        ${(s.parts || []).length ? `<p class="sect">Parts</p><ul>${s.parts.map(p => `<li>${esc(p.qty || 1)} × ${esc(lineName(p.line || p.part))} <span class="empty">${esc(p.line || '')}</span></li>`).join('')}</ul>` : ''}
        ${(s.tools || []).length ? `<p class="sect">Tools</p><p>${esc(s.tools.join(', '))}</p>` : ''}${s.torque ? `<p><b>Torque:</b> ${esc(s.torque)}</p>` : ''}
        ${s.check ? `<div class="checkbox-note"><b>Check:</b> ${esc(s.check)}</div>` : ''}
        <div class="ib">${check('assembly', id, 'done', 'Step done')}</div><div class="ib" id="anav"></div></div></div>`;
      const an = box.querySelector('#anav');
      an.append(btn('← Previous', () => { stepIx = Math.max(0, stepIx - 1); draw(); }), btn('Next step →', () => { if (!state[key('assembly', id, 'done')]) { state[key('assembly', id, 'done')] = true; save(); renderNav(); } stepIx = Math.min(steps.length - 1, stepIx + 1); draw(); }, 'primary'));
      const img = box.querySelector('.aimg img'); if (img) img.onclick = () => S.preview(img.dataset.p);
    } else if (cur === 'firmware') {
      box.innerHTML = (B.firmware || []).map((f, i) => `<div class="appcard"><div class="t">${check('firmware', 'fw' + i, 'done', '')} ${esc(f.name)}</div>
        ${f.build ? `<p class="d">Build: <code>${esc(f.build)}</code></p>` : ''}${f.flash ? `<p class="d">Flash: <code>${esc(f.flash)}</code></p>` : ''}${f.binary ? `<div>${fileBtns(f.binary)}</div>` : ''}${f.dir ? `<div>${fileBtns(f.dir)}</div>` : ''}${f.check ? `<p class="n">Check: ${esc(f.check)}</p>` : ''}</div>`).join('') +
        ((B.tests || []).length ? `<p class="sect" style="margin-top:18px">Tests</p>` + B.tests.map((t, i) => `<div class="appcard"><div class="t">${check('firmware', 't' + i, 'done', '')} ${esc(t.name)}</div><ol>${(t.steps || []).map(x => `<li>${esc(x)}</li>`).join('')}</ol>${t.expect ? `<p class="n">Expect: ${esc(t.expect)}</p>` : ''}</div>`).join('') : '');
    }
  }
  renderNav(); draw();
  const re = document.createElement('div'); re.className = 'ib'; re.style.marginTop = '24px';
  re.append(btn('Rebuild the package', () => { if (confirm('Run Claude again to regenerate the build package? Your checkmarks are kept.')) S.startRun(BUILD_PROMPT); }));
  el.append(re);
}
