// Pyslate design studio. Shapes are in millimetres, screen coordinates (y down), centred on x/y.
// The server rebuilds the same outlines (pyslate/studio.py), so keep shapePoints() in step with it.

const cfg = JSON.parse(document.getElementById('studio-config').textContent);
const SVGNS = 'http://www.w3.org/2000/svg';
const $ = id => document.getElementById(id);
const board = $('board');
const STORE = 'pyslate-studio-v1';
const MAT_COLORS = { pla: '#f59e0b', petg: '#14b8a6', 'plywood-3': '#d9b27c', 'acrylic-3': '#9fd3f5', 'mdf-3': '#a77b52', 'steel-1': '#9ca3af' };

let state = { shapes: [], process: 'laser', material: '', height: 10, quantity: 1 };
let selected = -1;
let uid = 1;

/* ---------- geometry ---------- */
function roundedRect(w, h, r, seg = 10) {
  if (r <= 1e-6) return [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]];
  const pts = [];
  for (const [cx, cy, start] of [[w / 2 - r, h / 2 - r, 0], [-w / 2 + r, h / 2 - r, 90], [-w / 2 + r, -h / 2 + r, 180], [w / 2 - r, -h / 2 + r, 270]])
    for (let k = 0; k <= seg; k++) { const a = (start + 90 * k / seg) * Math.PI / 180; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
  return pts;
}
function shapePoints(s) {
  let local;
  if (s.type === 'circle') local = Array.from({ length: 72 }, (_, k) => { const a = k / 72 * 2 * Math.PI; return [s.d / 2 * Math.cos(a), s.d / 2 * Math.sin(a)]; });
  else if (s.type === 'rect') local = roundedRect(s.w, s.h, Math.min(s.r || 0, Math.min(s.w, s.h) / 2));
  else if (s.type === 'slot') local = roundedRect(s.w, s.h, Math.min(s.w, s.h) / 2);
  else local = Array.from({ length: s.n }, (_, k) => { const a = (-90 + 360 * k / s.n) * Math.PI / 180; return [s.d / 2 * Math.cos(a), s.d / 2 * Math.sin(a)]; });
  const a = (s.rot || 0) * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
  return local.map(([px, py]) => [s.x + px * ca - py * sa, s.y + px * sa + py * ca]);
}
const pathD = pts => 'M' + pts.map(p => p[0].toFixed(2) + ' ' + p[1].toFixed(2)).join('L') + 'Z';
const area = pts => Math.abs(pts.reduce((s, p, i) => { const q = pts[(i + 1) % pts.length]; return s + p[0] * q[1] - q[0] * p[1]; }, 0) / 2);
const perimeter = pts => pts.reduce((s, p, i) => { const q = pts[(i + 1) % pts.length]; return s + Math.hypot(q[0] - p[0], q[1] - p[1]); }, 0);
function inside(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
}
// For each shape: how many other shapes contain it, and its nearest container. Even depth = solid, odd = hole.
function nesting(polys) {
  const areas = polys.map(area);
  return polys.map((p, i) => {
    const centre = p.reduce((a, q) => [a[0] + q[0] / p.length, a[1] + q[1] / p.length], [0, 0]);
    const containers = polys.map((q, j) => j !== i && areas[j] > areas[i] && inside(centre, q) ? j : -1).filter(j => j >= 0);
    const parent = containers.sort((a, b) => areas[a] - areas[b])[0] ?? -1;
    return { depth: containers.length, parent };
  });
}

/* ---------- shapes and templates ---------- */
const bed = () => { const m = cfg.materials.find(m => m.id === state.material); return state.process === 'print' ? [256, 256] : (m?.bed || [300, 300]); };
const centre = () => { const [w, h] = bed(); return [w / 2, h / 2]; };
function make(type, extra = {}) {
  const [cx, cy] = centre();
  const base = { id: uid++, type, x: cx, y: cy, rot: 0 };
  const sizes = { rect: { w: 40, h: 30, r: 0 }, circle: { d: 20 }, slot: { w: 30, h: 8 }, polygon: { d: 30, n: 6 } };
  return { ...base, ...sizes[type], ...extra };
}
const at = (dx, dy, type, extra) => { const [cx, cy] = centre(); return make(type, { x: cx + dx, y: cy + dy, ...extra }); };
const TEMPLATES = {
  'Mounting plate': () => [at(0, 0, 'rect', { w: 100, h: 60, r: 4 }), ...[[-42, -22], [42, -22], [-42, 22], [42, 22]].map(([x, y]) => at(x, y, 'circle', { d: 5 }))],
  'Control panel': () => [at(0, 0, 'rect', { w: 140, h: 90, r: 4 }), at(-30, -12, 'rect', { w: 50, h: 30, r: 2 }), at(35, -12, 'circle', { d: 16 }), at(35, 22, 'circle', { d: 12 }), at(-30, 25, 'slot', { w: 40, h: 6 }),
    ...[[-62, -37], [62, -37], [-62, 37], [62, 37]].map(([x, y]) => at(x, y, 'circle', { d: 3.5 }))],
  'Sign blank': () => [at(0, 0, 'rect', { w: 200, h: 80, r: 12 }), at(-88, 0, 'circle', { d: 5 }), at(88, 0, 'circle', { d: 5 })],
  'Washer': () => [at(0, 0, 'circle', { d: 40 }), at(0, 0, 'circle', { d: 16 })],
  'Hex spacer': () => [at(0, 0, 'polygon', { d: 40, n: 6 }), at(0, 0, 'circle', { d: 20 })],
};

/* ---------- persistence ---------- */
function save() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) { /* storage blocked */ } }
function load() {
  try { const s = JSON.parse(localStorage.getItem(STORE) || 'null'); if (s && Array.isArray(s.shapes)) { state = { ...state, ...s }; uid = Math.max(0, ...state.shapes.map(x => x.id || 0)) + 1; return true; } } catch (e) { /* ignore */ }
  return false;
}

/* ---------- process and material ---------- */
const materialSel = $('material');
function fillMaterials() {
  const mats = cfg.materials.filter(m => m.line === state.process);
  materialSel.innerHTML = mats.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
  if (!mats.some(m => m.id === state.material)) state.material = mats[0]?.id || '';
  materialSel.value = state.material;
  $('height-field').hidden = state.process !== 'print';
}
document.querySelectorAll('input[name=process]').forEach(r => r.addEventListener('change', () => {
  state.process = r.value; fillMaterials(); fit(); render(); save(); if (!$('preview3d').hidden) build3d();
}));
materialSel.addEventListener('change', () => { state.material = materialSel.value; fit(); render(); save(); if (!$('preview3d').hidden) build3d(); });
$('height').addEventListener('input', e => { const v = parseFloat(e.target.value); if (v > 0) { state.height = v; renderFacts(); save(); if (!$('preview3d').hidden) build3d(); } });
$('quantity').addEventListener('input', e => { const v = parseInt(e.target.value, 10); if (v > 0) { state.quantity = v; save(); } });

/* ---------- board ---------- */
let view = [0, 0, 300, 300];
function fit() {
  const [w, h] = bed();
  const polys = state.shapes.map(shapePoints).flat();
  let x0 = 0, y0 = 0, x1 = w, y1 = h;
  for (const [x, y] of polys) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  const pad = Math.max(x1 - x0, y1 - y0) * 0.08 + 10;
  view = [x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad];
  board.setAttribute('viewBox', view.join(' '));
}
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(SVGNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fmt = v => (Math.round(v * 10) / 10).toString();

function render() {
  board.textContent = '';
  const [bw, bh] = bed();
  const unit = view[2] / 600; // roughly one screen pixel at typical size
  const defs = el('defs', {}, board);
  const pat = el('pattern', { id: 'grid', width: 10, height: 10, patternUnits: 'userSpaceOnUse' }, defs);
  el('path', { d: 'M10 0H0V10', fill: 'none', stroke: '#e6e8ec', 'stroke-width': unit }, pat);
  el('rect', { x: view[0], y: view[1], width: view[2], height: view[3], fill: '#fbfbfc' }, board);
  el('rect', { x: 0, y: 0, width: bw, height: bh, fill: 'url(#grid)', stroke: '#c9ccd3', 'stroke-width': unit * 1.5, 'stroke-dasharray': `${unit * 6} ${unit * 4}` }, board);
  const machine = state.process === 'print' ? 'Bambu Lab build plate' : (cfg.materials.find(m => m.id === state.material)?.id === 'steel-1' ? 'xTool MetalFab bed' : 'xTool laser bed');
  el('text', { x: 2, y: -unit * 6, 'font-size': unit * 11, fill: '#8a8f99', 'font-family': 'JetBrains Mono, monospace' }, board).textContent = `${machine} · ${bw} × ${bh} mm`;

  const polys = state.shapes.map(shapePoints);
  if (polys.length) {
    // The part itself, filled even-odd so holes show through.
    el('path', { d: polys.map(pathD).join(' '), 'fill-rule': 'evenodd', fill: MAT_COLORS[state.material] || '#ff9a3c', 'fill-opacity': .55, stroke: '#2b2d33', 'stroke-width': unit * 1.6 }, board);
    // Overall size
    const xs = polys.flat().map(p => p[0]), ys = polys.flat().map(p => p[1]);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const g = el('g', { stroke: '#e8590c', 'stroke-width': unit, fill: '#e8590c', 'font-size': unit * 12, 'font-family': 'JetBrains Mono, monospace' }, board);
    const off = unit * 18;
    el('path', { d: `M${x0} ${y0 - off}H${x1}M${x0} ${y0 - off - unit * 5}v${unit * 10}M${x1} ${y0 - off - unit * 5}v${unit * 10}`, fill: 'none' }, g);
    el('text', { x: (x0 + x1) / 2, y: y0 - off - unit * 5, 'text-anchor': 'middle', stroke: 'none' }, g).textContent = fmt(x1 - x0);
    el('path', { d: `M${x0 - off} ${y0}V${y1}M${x0 - off - unit * 5} ${y0}h${unit * 10}M${x0 - off - unit * 5} ${y1}h${unit * 10}`, fill: 'none' }, g);
    const t = el('text', { x: x0 - off - unit * 5, y: (y0 + y1) / 2, 'text-anchor': 'middle', stroke: 'none', transform: `rotate(-90 ${x0 - off - unit * 5} ${(y0 + y1) / 2})` }, g);
    t.textContent = fmt(y1 - y0);
  }
  // Hit targets, biggest first so smaller shapes (holes) sit on top and stay clickable.
  const order = polys.map((p, i) => [area(p), i]).sort((a, b) => b[0] - a[0]).map(x => x[1]);
  for (const i of order) {
    const p = el('path', { d: pathD(polys[i]), fill: 'rgba(0,0,0,0)', stroke: i === selected ? '#e8590c' : 'transparent', 'stroke-width': unit * 3, class: 'hit', 'data-i': i }, board);
    p.addEventListener('pointerdown', ev => startDrag(ev, i));
  }
  if (selected >= 0 && state.shapes[selected]) {
    const s = state.shapes[selected];
    el('circle', { cx: s.x, cy: s.y, r: unit * 3.5, fill: '#e8590c' }, board);
  }
  renderFacts();
}

/* ---------- dragging and keys ---------- */
let drag = null;
function svgPoint(ev) { const pt = board.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; return pt.matrixTransform(board.getScreenCTM().inverse()); }
function startDrag(ev, i) {
  ev.preventDefault(); board.focus({ preventScroll: true });
  if (selected !== i) { selected = i; buildProps(); }
  const p = svgPoint(ev), s = state.shapes[i];
  drag = { i, dx: s.x - p.x, dy: s.y - p.y };
  board.setPointerCapture(ev.pointerId);
  render();
}
board.addEventListener('pointermove', ev => {
  if (!drag) return;
  const p = svgPoint(ev), s = state.shapes[drag.i];
  s.x = Math.round((p.x + drag.dx) * 2) / 2; s.y = Math.round((p.y + drag.dy) * 2) / 2;
  render(); syncProps();
});
board.addEventListener('pointerup', () => { if (drag) { drag = null; save(); } });
board.addEventListener('pointerdown', ev => { if (!ev.target.classList.contains('hit')) { selected = -1; buildProps(); render(); } });
board.addEventListener('keydown', ev => {
  const s = state.shapes[selected];
  if (!s) return;
  const step = ev.shiftKey ? 10 : 1;
  const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
  if (moves[ev.key]) { ev.preventDefault(); s.x += moves[ev.key][0]; s.y += moves[ev.key][1]; }
  else if (ev.key === 'Delete' || ev.key === 'Backspace') { ev.preventDefault(); removeSelected(); return; }
  else if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'd') { ev.preventDefault(); duplicate(); return; }
  else return;
  render(); syncProps(); save();
});

/* ---------- properties ---------- */
const FIELDS = {
  rect: [['x', 'X centre'], ['y', 'Y centre'], ['w', 'Width'], ['h', 'Height'], ['r', 'Corner radius'], ['rot', 'Rotation °']],
  slot: [['x', 'X centre'], ['y', 'Y centre'], ['w', 'Length'], ['h', 'Width'], ['rot', 'Rotation °']],
  circle: [['x', 'X centre'], ['y', 'Y centre'], ['d', 'Diameter']],
  polygon: [['x', 'X centre'], ['y', 'Y centre'], ['d', 'Across corners'], ['n', 'Sides'], ['rot', 'Rotation °']],
};
const NAMES = { rect: 'Rectangle', circle: 'Circle', slot: 'Slot', polygon: 'Polygon' };
function buildProps() {
  const box = $('props'), s = state.shapes[selected];
  if (!s) { box.innerHTML = '<p class="fine">Click a shape to edit it.</p>'; return; }
  const polys = state.shapes.map(shapePoints), nest = nesting(polys)[selected];
  box.innerHTML = `<p class="shape-name">${NAMES[s.type]} <span>${nest.depth % 2 ? 'hole' : 'solid'}</span></p>
    <div class="prop-grid">${FIELDS[s.type].map(([k, label]) => `<label>${label}<input type="number" step="${k === 'n' ? 1 : 0.5}" data-k="${k}" value="${s[k]}"></label>`).join('')}</div>
    <div class="prop-actions"><button type="button" class="link-button" id="dup">Duplicate</button><button type="button" class="link-button danger-link" id="del">Delete</button></div>`;
  box.querySelectorAll('input').forEach(inp => inp.addEventListener('input', () => {
    const v = parseFloat(inp.value); if (!Number.isFinite(v)) return;
    const k = inp.dataset.k;
    if (['w', 'h', 'd'].includes(k) && v < 0.5) return;
    if (k === 'n' && (v < 3 || v > 24)) return;
    s[k] = k === 'n' ? Math.round(v) : v;
    render(); save();
  }));
  $('dup').addEventListener('click', duplicate);
  $('del').addEventListener('click', removeSelected);
}
function syncProps() { const s = state.shapes[selected]; if (!s) return; $('props').querySelectorAll('input').forEach(inp => { if (document.activeElement !== inp) inp.value = s[inp.dataset.k]; }); }
function removeSelected() { if (selected < 0) return; state.shapes.splice(selected, 1); selected = -1; buildProps(); render(); save(); }
function duplicate() { const s = state.shapes[selected]; if (!s) return; state.shapes.push({ ...s, id: uid++, x: s.x + 10, y: s.y + 10 }); selected = state.shapes.length - 1; buildProps(); render(); save(); }

/* ---------- facts and warnings ---------- */
function renderFacts() {
  const polys = state.shapes.map(shapePoints);
  const facts = $('facts'), warn = $('warnings');
  const [bw, bh] = bed();
  if (!polys.length) { facts.innerHTML = '<dt>Shapes</dt><dd>None yet</dd>'; warn.innerHTML = ''; $('board-size').textContent = ''; return; }
  const xs = polys.flat().map(p => p[0]), ys = polys.flat().map(p => p[1]);
  const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
  const nest = nesting(polys), holes = nest.filter(n => n.depth % 2).length;
  const cut = polys.reduce((s, p) => s + perimeter(p), 0);
  const mat = cfg.materials.find(m => m.id === state.material);
  const thick = state.process === 'print' ? state.height : (mat?.thickness || 3);
  $('board-size').textContent = `${fmt(w)} × ${fmt(h)} mm`;
  facts.innerHTML = `<dt>Size</dt><dd>${fmt(w)} × ${fmt(h)} × ${fmt(thick)} mm</dd>
    <dt>Shapes</dt><dd>${polys.length} (${holes} hole${holes === 1 ? '' : 's'})</dd>
    ${state.process === 'laser' ? `<dt>Cut length</dt><dd>${Math.round(cut)} mm</dd>` : ''}`;
  const issues = [];
  if (Math.min(...xs) < 0 || Math.min(...ys) < 0 || Math.max(...xs) > bw || Math.max(...ys) > bh)
    issues.push(w > bw || h > bh ? `Bigger than the ${bw} × ${bh} mm bed, so we'll review it before pricing.` : 'Part of the design is off the bed. Drag it back inside the dashed area.');
  const crosses = polys.some((p, i) => polys.some((q, j) => {
    if (i === j || area(q) <= area(p)) return false;
    const inCount = p.filter(pt => inside(pt, q)).length;
    return inCount > 0 && inCount < p.length;
  }));
  if (crosses) issues.push('A shape crosses the edge of another shape, so it will cut a notch. Move it fully inside or outside if that is not what you want.');
  if (nest.some(n => n.depth >= 2)) issues.push('A shape sits inside a hole, so it will come out as a separate piece.');
  if (state.process === 'laser' && polys.some((p, i) => nest[i].depth % 2 && Math.min(...p.map(q => q[0])) !== undefined && Math.sqrt(area(p)) < (mat?.thickness || 1)))
    issues.push('Some holes are smaller than the sheet is thick and may not cut cleanly.');
  warn.innerHTML = issues.map(t => `<li>${t}</li>`).join('');
}

/* ---------- 3D preview ---------- */
let three = null;
async function build3d() {
  const host = $('preview3d');
  if (!three) {
    const THREE = await import('three');
    const { OrbitControls } = await import('./vendor/three/OrbitControls.js');
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    host.appendChild(renderer.domElement);
    const scene = new THREE.Scene(); scene.background = new THREE.Color('#f1f2f4');
    const camera = new THREE.PerspectiveCamera(40, 1, 1, 10000); camera.up.set(0, 0, 1);
    scene.add(new THREE.HemisphereLight('#ffffff', '#8a8f99', 1.6));
    const sun = new THREE.DirectionalLight('#ffffff', 1.8); sun.position.set(200, -300, 400); scene.add(sun);
    const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
    const group = new THREE.Group(); scene.add(group);
    three = { THREE, renderer, scene, camera, controls, group };
    const size = () => { const r = host.getBoundingClientRect(); renderer.setSize(r.width, r.height, false); camera.aspect = r.width / r.height; camera.updateProjectionMatrix(); };
    new ResizeObserver(size).observe(host); size();
    (function loop() { if (!host.hidden) { controls.update(); renderer.render(scene, camera); } requestAnimationFrame(loop); })();
  }
  const { THREE, group, camera, controls } = three;
  group.children.slice().forEach(c => { group.remove(c); c.geometry?.dispose(); });
  const polys = state.shapes.map(shapePoints);
  if (!polys.length) return;
  const nest = nesting(polys);
  const mat = cfg.materials.find(m => m.id === state.material);
  const depth = state.process === 'print' ? state.height : (mat?.thickness || 3);
  const toV = p => new THREE.Vector2(p[0], -p[1]);
  const material = new THREE.MeshStandardMaterial({ color: MAT_COLORS[state.material] || '#ff9a3c', roughness: state.material === 'steel-1' ? .35 : .7, metalness: state.material === 'steel-1' ? .8 : 0, transparent: state.material === 'acrylic-3', opacity: state.material === 'acrylic-3' ? .75 : 1 });
  polys.forEach((p, i) => {
    if (nest[i].depth % 2) return;
    const shape = new THREE.Shape(p.map(toV));
    polys.forEach((q, j) => { if (nest[j].parent === i && nest[j].depth % 2) shape.holes.push(new THREE.Path(q.map(toV))); });
    const geom = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 24 });
    const mesh = new THREE.Mesh(geom, material); group.add(mesh);
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geom, 25), new THREE.LineBasicMaterial({ color: '#2b2d33' })); group.add(edges);
  });
  const box = new THREE.Box3().setFromObject(group), c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2;
  controls.target.copy(c);
  camera.position.set(c.x + r * 1.2, c.y - r * 1.8, c.z + r * 1.6);
  camera.near = r / 100; camera.far = r * 100; camera.updateProjectionMatrix();
}
function setView(is3d) {
  $('view-2d').setAttribute('aria-pressed', String(!is3d)); $('view-3d').setAttribute('aria-pressed', String(is3d));
  board.hidden = is3d; $('preview3d').hidden = !is3d;
  if (is3d) build3d().catch(() => { status('The 3D preview could not start in this browser.', true); setView(false); });
}
$('view-2d').addEventListener('click', () => setView(false));
$('view-3d').addEventListener('click', () => setView(true));

/* ---------- toolbar ---------- */
document.querySelectorAll('[data-add]').forEach(b => b.addEventListener('click', () => {
  state.shapes.push(make(b.dataset.add)); selected = state.shapes.length - 1; buildProps(); fit(); render(); save();
  if (!$('preview3d').hidden) build3d();
}));
const tl = $('templates');
for (const name of Object.keys(TEMPLATES)) {
  const b = document.createElement('button'); b.type = 'button'; b.textContent = name;
  b.addEventListener('click', () => { state.shapes = TEMPLATES[name](); selected = -1; buildProps(); fit(); render(); save(); if (!$('preview3d').hidden) build3d(); });
  tl.appendChild(b);
}
$('fit').addEventListener('click', () => { fit(); render(); });
$('clear').addEventListener('click', () => { state.shapes = []; selected = -1; buildProps(); render(); save(); if (!$('preview3d').hidden) build3d(); });

/* ---------- sending ---------- */
function status(text, bad = false) { const s = $('status'); s.textContent = text; s.classList.toggle('bad', bad); }
function designForm() {
  const f = new FormData();
  f.append('design', JSON.stringify({ shapes: state.shapes.map(({ id, ...s }) => s) }));
  f.append('process', state.process); f.append('material_id', state.material);
  f.append('height_mm', state.height); f.append('quantity', state.quantity);
  return f;
}
async function send(url, form) {
  const r = await fetch(url, { method: 'POST', body: form });
  const data = await r.json().catch(() => ({ error: 'Something went wrong. Please try again.' }));
  if (!r.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}
$('get-price').addEventListener('click', async ev => {
  if (!state.shapes.length) { status('Add a shape first.', true); return; }
  ev.target.disabled = true; status('Pricing your part…');
  try { const d = await send('/studio/quote', designForm()); location.href = d.url; }
  catch (e) { status(e.message, true); ev.target.disabled = false; }
});
$('ask-engineer').addEventListener('click', () => { const f = $('engineer-form'); f.hidden = !f.hidden; if (!f.hidden) $('eng-name').focus(); });
$('engineer-form').addEventListener('submit', async ev => {
  ev.preventDefault();
  if (!state.shapes.length) { status('Add a shape first.', true); return; }
  const f = designForm();
  f.append('name', $('eng-name').value); f.append('email', $('eng-email').value); f.append('description', $('eng-notes').value);
  const btn = ev.target.querySelector('button'); btn.disabled = true; status('Sending your design…');
  try { const d = await send('/studio/request', f); ev.target.hidden = true; status(`Sent. Your reference is ${d.ref}. An engineer will reply, usually within two business days.`); }
  catch (e) { status(e.message, true); }
  btn.disabled = false;
});

/* ---------- start ---------- */
if (!load() || !state.shapes.length) state.shapes = TEMPLATES['Mounting plate']();
document.querySelector(`input[name=process][value=${state.process === 'print' ? 'print' : 'laser'}]`).checked = true;
$('height').value = state.height; $('quantity').value = state.quantity;
fillMaterials(); fit(); render(); buildProps();
