// Build tab, "Xometry" stage: which parts go out to xometry.com, a 3D look at each one, and the files to upload.
// The server decides the default route (too big for the bed, a material not printed at home, a machined or cut
// metal part); the user can move any part between Home and Xometry. Nothing is submitted to Xometry from here.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

const XOMETRY_URL = 'https://www.xometry.com/quoting/home/';
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const base = p => String(p || '').split('/').pop();
const dims = s => s ? `${s.map(v => v.toFixed(0)).join(' × ')} mm <span class="empty">[${s.map(v => (v / 25.4).toFixed(2)).join(' × ')} in]</span>` : '<span class="empty">size unknown</span>';

export async function loadXometry(ctx) {
  const R = await ctx.api(`/api/projects/${ctx.id}/xometry`).catch(() => ({ parts: [] }));
  return R && R.parts ? R : { parts: [] };
}

// ---------------------------------------------------------------- geometry (STL preferred; STEP through occt like the 3D tab)
const geoCache = new Map();
let occtP = null;
function loadOcct() {
  if (!occtP) occtP = new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.22/dist/occt-import-js.js';
    s.onload = () => window.occtimportjs({ locateFile: f => 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.22/dist/' + f }).then(res, rej); s.onerror = rej; document.head.append(s);
  });
  return occtP;
}
async function geometry(raw, p) {
  const file = p.stl || p.step; if (!file) return null;
  if (geoCache.has(file)) return geoCache.get(file);
  const job = (async () => {
    const buf = await (await fetch(raw(file))).arrayBuffer();
    if (/\.stl$/i.test(file)) { const g = new STLLoader().parse(buf); g.computeVertexNormals(); return g; }
    const occt = await loadOcct(); const r = occt.ReadStepFile(new Uint8Array(buf), null);
    const gs = r.meshes.map(m => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(m.attributes.position.array, 3)); g.setIndex(new THREE.Uint32BufferAttribute(Uint32Array.from(m.index.array), 1)); return g.toNonIndexed(); });
    if (!gs.length) return null;
    const n = gs.reduce((a, g) => a + g.attributes.position.count, 0); const pos = new Float32Array(n * 3); let o = 0;
    for (const g of gs) { pos.set(g.attributes.position.array, o); o += g.attributes.position.array.length; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.computeVertexNormals(); return g;
  })().catch(() => null);
  geoCache.set(file, job);
  return job;
}
const COL = { xometry: 0xffa64d, home: 0x9fb4d9 };
function meshFor(g, route) {
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: COL[route] || COL.home, metalness: 0.15, roughness: 0.5 }));
  g.computeBoundingBox(); const c = g.boundingBox.getCenter(new THREE.Vector3());
  m.position.set(-c.x, -c.y, -g.boundingBox.min.z); // centred on the bed, sitting on it
  return m;
}
function lights(scene) {
  scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.1));
  const d1 = new THREE.DirectionalLight(0xffffff, 1.4); d1.position.set(1, -1.2, 2); scene.add(d1);
  const d2 = new THREE.DirectionalLight(0x99aaff, 0.5); d2.position.set(-1, 1, 0.5); scene.add(d2);
}
function aim(cam, size, ctl) {
  const r = Math.max(size.x, size.y, size.z) || 1;
  const c = new THREE.Vector3(0, 0, size.z / 2);
  cam.position.copy(c).add(new THREE.Vector3(r * 1.25, -r * 1.55, r * 1.0)); cam.near = r / 500; cam.far = r * 60; cam.updateProjectionMatrix();
  if (ctl) ctl.target.copy(c); else cam.lookAt(c);
}

// One shared off-screen renderer draws every card's thumbnail (browsers allow only a few live WebGL canvases).
let TH = null;
function thumbRenderer() {
  if (TH) return TH;
  const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: true }); r.setPixelRatio(1); r.setSize(320, 220);
  const scene = new THREE.Scene(); lights(scene); const cam = new THREE.PerspectiveCamera(35, 320 / 220, 0.1, 1e5); cam.up.set(0, 0, 1);
  TH = { r, scene, cam }; return TH;
}
async function thumb(raw, p) {
  const g = await geometry(raw, p); if (!g) return null;
  const { r, scene, cam } = thumbRenderer();
  const m = meshFor(g, p.route); scene.add(m);
  const box = new THREE.Box3().setFromObject(m); aim(cam, box.getSize(new THREE.Vector3()));
  r.render(scene, cam); const url = r.domElement.toDataURL('image/png'); scene.remove(m); m.material.dispose();
  return url;
}

// The big viewer: the selected part, with the printer's build volume drawn around it for scale.
let BV = null;
function bigViewer(host) {
  if (BV && host.contains(BV.r.domElement)) return BV;
  if (BV) { cancelAnimationFrame(BV.raf); BV.ro.disconnect(); BV.r.dispose(); }
  const r = new THREE.WebGLRenderer({ antialias: true }); r.setPixelRatio(window.devicePixelRatio); host.append(r.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0e1013); lights(scene);
  const cam = new THREE.PerspectiveCamera(40, 1, 0.1, 1e5); cam.up.set(0, 0, 1);
  const ctl = new OrbitControls(cam, r.domElement); ctl.enableDamping = true;
  const holder = new THREE.Group(); scene.add(holder);
  const ro = new ResizeObserver(() => { const w = host.clientWidth, h = host.clientHeight; r.setSize(w, h); cam.aspect = w / Math.max(h, 1); cam.updateProjectionMatrix(); }); ro.observe(host);
  BV = { r, scene, cam, ctl, holder, ro, host, raf: 0 };
  const loop = () => { if (!document.body.contains(r.domElement)) { cancelAnimationFrame(BV.raf); ro.disconnect(); r.dispose(); BV = null; return; } BV.raf = requestAnimationFrame(loop); ctl.update(); r.render(scene, cam); };
  loop();
  return BV;
}
async function showBig(host, raw, p, bed) {
  const v = bigViewer(host);
  v.holder.clear();
  const g = await geometry(raw, p);
  if (!g) { v.holder.clear(); return false; }
  const m = meshFor(g, p.route); v.holder.add(m);
  const bedBox = new THREE.Box3(new THREE.Vector3(-bed[0] / 2, -bed[1] / 2, 0), new THREE.Vector3(bed[0] / 2, bed[1] / 2, bed[2]));
  const bedLines = new THREE.Box3Helper(bedBox, 0x4fd18b); v.holder.add(bedLines);
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(bed[0], bed[1]), new THREE.MeshBasicMaterial({ color: 0x4fd18b, transparent: true, opacity: 0.08, side: THREE.DoubleSide })); v.holder.add(plate);
  const own = new THREE.Box3().setFromObject(m).getSize(new THREE.Vector3());
  const box = new THREE.Box3().setFromObject(m).union(bedBox); aim(v.cam, box.getSize(new THREE.Vector3()), v.ctl);
  return [own.x, own.y, own.z];
}

// ---------------------------------------------------------------- the stage
export function xometryStage(box, ctx) {
  // ctx: { id, api, raw, R, state, save, key, check, fileBtns, onChange(R), reveal }
  let R = ctx.R, filter = 'xometry', sel = null, open = new Set();
  const bed = (R.printer && R.printer.bed) || [256, 256, 256];
  const put = async (name, patch) => {
    const r = await ctx.api(`/api/projects/${ctx.id}/xometry`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ parts: { [name]: patch } }) }).catch(() => null);
    if (r && r.parts) { R = r; ctx.onChange(R); }
  };
  function render() {
    const P = R.parts || [];
    if (!P.length) { box.innerHTML = '<p class="empty">This build has no printed or fabricated parts to send out.</p>'; return; }
    const xo = P.filter(p => p.route === 'xometry'), home = P.filter(p => p.route === 'home');
    const list = filter === 'xometry' ? xo : filter === 'home' ? home : P;
    if (!sel || !list.find(p => p.key === sel)) sel = (list[0] || {}).key || null;
    const cur = P.find(p => p.key === sel);
    box.innerHTML = `<div class="xo-head"><p class="lead">${xo.length ? `<b>${xo.length}</b> part${xo.length > 1 ? 's go' : ' goes'} to Xometry` : 'No parts go to Xometry yet'} · ${home.length} made at home.
      A part goes to Xometry when it is bigger than your ${bed.join(' × ')} mm bed, needs a material you do not print at home, or is a metal or engineering-plastic part that has to be machined or cut. Use the switch on any part to move it.</p>
      <div class="ib xo-actions"></div></div>
      <div class="seg xo-filter">${[['xometry', `Xometry (${xo.length})`], ['home', `Home (${home.length})`], ['all', `All (${P.length})`]].map(([k, n]) => `<button data-f="${k}" class="${filter === k ? 'on' : ''}">${n}</button>`).join('')}</div>
      <div class="xo-main"><div class="xo-view"><div class="xo-canvas"></div><div class="xo-cap"></div></div><div class="xo-grid">${list.map(card).join('') || '<p class="empty">Nothing here.</p>'}</div></div>`;
    const act = box.querySelector('.xo-actions');
    const mk = (t, fn, cls = 'ghost') => { const b = document.createElement('button'); b.className = cls; b.textContent = t; b.onclick = fn; return b; };
    act.append(
      mk('Prepare upload folder', async e => {
        const b = e.target; b.disabled = true; b.textContent = 'Copying files…';
        const r = await ctx.api(`/api/projects/${ctx.id}/xometry/package`, { method: 'POST' }).catch(x => ({ error: x.message }));
        b.disabled = false; b.textContent = 'Prepare upload folder';
        const note = box.querySelector('.xo-note');
        if (r && r.dir) { note.innerHTML = `Copied ${r.files.length} file${r.files.length === 1 ? '' : 's'} for ${r.parts} part${r.parts === 1 ? '' : 's'} into <code>${esc(r.dir)}</code>, with XOMETRY-ORDER.md and xometry-parts.csv listing material, finish, tolerance and quantity for each. Drag the files onto the Xometry quote page. Nothing has been sent.`; ctx.reveal(r.dir + '/XOMETRY-ORDER.md'); }
        else note.textContent = 'Could not prepare the folder: ' + ((r && r.error) || 'unknown error');
      }, xo.length ? 'primary' : 'ghost'),
      mk('Open Xometry quote page', () => window.open(XOMETRY_URL, '_blank')));
    const note = document.createElement('div'); note.className = 'xo-note empty'; act.after(note);
    if (cur) select(cur);
    // thumbnails, one at a time
    (async () => { for (const p of list) { const img = box.querySelector(`.xo-card[data-k="${CSS.escape(p.key)}"] .xo-thumb`); if (!img || img.dataset.done) continue; const u = await thumb(ctx.raw, p); if (!document.body.contains(img)) return; img.dataset.done = 1; img.innerHTML = u ? `<img src="${u}" alt="">` : '<span class="empty">no 3D file</span>'; } })();
  }
  function select(p) {
    sel = p.key;
    box.querySelectorAll('.xo-card').forEach(c => c.classList.toggle('on', c.dataset.k === p.key));
    const host = box.querySelector('.xo-canvas'), cap = box.querySelector('.xo-cap');
    cap.innerHTML = `<b>${esc(p.part)}</b> · <span class="xo-sz">${dims(p.size)}</span><br><span class="xo-legend"><i style="background:#4fd18b"></i>your ${bed.join(' × ')} mm build volume</span>`;
    showBig(host, ctx.raw, p, bed).then(sz => {
      if (sel !== p.key) return;
      if (!sz) cap.innerHTML += '<br><span class="empty">No STL or STEP file found for this part.</span>';
      else if (!p.size) cap.querySelector('.xo-sz').innerHTML = dims(sz) + ' <span class="empty">(from the 3D model)</span>';
    });
  }
  function card(p) {
    const k = p.key, xo = p.route === 'xometry';
    const field = (f, label, wide) => `<label class="xo-f${wide ? ' wide' : ''}"><span>${label}</span><input data-xf="${f}" data-xk="${esc(k)}" value="${esc(p[f])}"></label>`;
    return `<div class="xo-card ${xo ? 'xo' : ''}" data-k="${esc(k)}">
      <div class="xo-thumb">${'<span class="empty">loading…</span>'}</div>
      <div class="xo-body">
        <div class="xo-t"><b>${esc(p.part)}</b> <span class="empty">${esc(p.line)} · ${p.kind === 'print' ? '3D print' : 'fabricated'}</span></div>
        <div class="seg xo-route"><button data-route="home" class="${xo ? '' : 'on'}">Home</button><button data-route="xometry" class="${xo ? 'on' : ''}">Xometry</button></div>
        ${p.overridden ? `<span class="gtag">moved by hand</span>` : ''}
        <div class="xo-meta">Qty <b>${esc(p.qty)}</b> · ${xo ? 'pick on Xometry: ' : ''}<b class="xo-mat">${esc(p.material || '—')}</b>${xo && p.design_material && p.material !== p.design_material ? ` <span class="empty">(design: ${esc(p.design_material)})</span>` : ''}<br>${dims(p.size)}</div>
        ${p.reasons.length ? `<div class="xo-why">${p.reasons.map(r => `<span class="xo-badge">${esc(r)}</span>`).join('')}</div>` : ''}
        ${p.warn.length ? `<div class="xo-warn">${p.warn.map(esc).join('<br>')}</div>` : ''}
        ${xo ? `<div class="xo-files"><span class="sect">Upload to Xometry</span>${p.step ? '<div class="xo-hint">Upload the STEP, not the .gcode.3mf: G-code is sliced for your own printer and Xometry measures and quotes from the CAD.</div>' : ''}${p.upload.length ? p.upload.map(u => `<div>${ctx.fileBtns(u)}</div>`).join('') : '<div class="empty">no files found</div>'}</div>
        <div class="xo-checks">${ctx.check('xometry', k, 'quoted', 'Quoted')} ${ctx.check('xometry', k, 'ordered', 'Ordered')} ${ctx.check('xometry', k, 'received', 'Received')}</div>
        <details class="xo-det" ${open.has(k) ? 'open' : ''} data-det="${esc(k)}"><summary>Quote details: ${esc(p.process)}</summary>
          <div class="xo-fields">${field('process', 'Process', true)}${field('material', 'Material', true)}${field('finish', 'Finish')}${field('tolerance', 'Tolerance')}${field('qty', 'Qty')}${field('notes', 'Notes', true)}</div></details>` : ''}
      </div></div>`;
  }
  box.onclick = e => {
    const f = e.target.closest('[data-f]'); if (f) { filter = f.dataset.f; render(); return; }
    const rt = e.target.closest('[data-route]');
    if (rt) { const k = rt.closest('.xo-card').dataset.k; const p = R.parts.find(x => x.key === k); const to = rt.dataset.route; if (p && p.route !== to) { sel = k; put(k, { route: to === p.auto ? null : to }).then(render); } return; }
    if (e.target.closest('input,button,a,summary,label,details')) return;
    const c = e.target.closest('.xo-card'); if (c) { const p = R.parts.find(x => x.key === c.dataset.k); if (p) select(p); }
  };
  if (box._xoToggle) box.removeEventListener('toggle', box._xoToggle, true);
  box._xoToggle = e => { const d = e.target.closest && e.target.closest('[data-det]'); if (d) { d.open ? open.add(d.dataset.det) : open.delete(d.dataset.det); } };
  box.addEventListener('toggle', box._xoToggle, true);
  box.onchange = e => {
    const i = e.target.closest('[data-xf]'); if (!i) return;
    const f = i.dataset.xf; let v = i.value.trim(); if (f === 'qty') v = v ? Math.max(1, Math.round(+v || 1)) : null;
    put(i.dataset.xk, { [f]: v === '' ? null : v });
  };
  render();
}
