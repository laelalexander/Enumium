// Pyslate design studio. Everything is in millimetres, in screen coordinates (y down).
// Each shape has a centre (x, y), a rotation (rot, degrees) and optional mirroring (fx, fy).
// contours() turns a shape into outlines; the server receives those outlines (or the basic
// shape, which pyslate/studio.py rebuilds the same way) and makes the cut or print file.

import { parse as parseFont } from './vendor/opentype/opentype.module.js';

const cfg = JSON.parse(document.getElementById('studio-config').textContent);
const SVGNS = 'http://www.w3.org/2000/svg';
const $ = id => document.getElementById(id);
const board = $('board');
const STORE = 'pyslate-studio-v2';
const MAT_COLORS = { pla: '#f59e0b', petg: '#14b8a6', 'plywood-3': '#d9b27c', 'acrylic-3': '#9fd3f5', 'mdf-3': '#a77b52', 'steel-1': '#9ca3af' };
const CUT = '#2b2d33', ENGRAVE = '#2563eb', SELECT = '#e8590c';
const FONTS = { sans: { label: 'Sans (bold)', url: '/static/fonts/inter-latin-700-normal.woff' }, stencil: { label: 'Stencil', url: '/static/fonts/allerta-stencil-latin-400-normal.woff' } };

let state = { shapes: [], machine: '', material: '', height: 10, quantity: 1 };
let selected = -1;   // the shape the panel edits (last clicked)
let sel = [];        // every selected shape
function select(i) { selected = i; sel = i >= 0 ? [i] : []; }
let uid = 1;
const fonts = {};

/* ---------------- fonts ---------------- */
for (const [key, f] of Object.entries(FONTS)) {
  fetch(f.url).then(r => r.arrayBuffer()).then(buf => { fonts[key] = parseFont(buf); textCache.clear(); render(); buildProps(); })
    .catch(() => status('A font could not load, so text may not show.', true));
}
const textCache = new Map();
function textLocal(s) {
  // Outlines of the text in local coordinates, centred on 0,0. Letter height = capital height in mm.
  const font = fonts[s.font] || fonts.sans;
  if (!font || !s.text) return [];
  const key = `${s.font}|${s.size}|${s.text}`;
  if (textCache.has(key)) return textCache.get(key);
  const cap = (font.tables.os2 && font.tables.os2.sCapHeight) || font.unitsPerEm * 0.7;
  const fontSize = s.size * font.unitsPerEm / cap;
  const contours = [];
  let cur = null, px = 0, py = 0;
  const steps = 8;
  for (const c of font.getPath(s.text, 0, 0, fontSize).commands) {
    if (c.type === 'M') { cur = [[c.x, c.y]]; contours.push(cur); }
    else if (c.type === 'L') cur.push([c.x, c.y]);
    else if (c.type === 'Q') for (let k = 1; k <= steps; k++) { const t = k / steps, u = 1 - t; cur.push([u * u * px + 2 * u * t * c.x1 + t * t * c.x, u * u * py + 2 * u * t * c.y1 + t * t * c.y]); }
    else if (c.type === 'C') for (let k = 1; k <= steps; k++) { const t = k / steps, u = 1 - t; cur.push([u ** 3 * px + 3 * u * u * t * c.x1 + 3 * u * t * t * c.x2 + t ** 3 * c.x, u ** 3 * py + 3 * u * u * t * c.y1 + 3 * u * t * t * c.y2 + t ** 3 * c.y]); }
    if (c.type !== 'Z') { px = c.x; py = c.y; }
  }
  const clean = contours.map(p => { const q = p.slice(); const a = q[0], b = q[q.length - 1]; if (q.length > 1 && Math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-6) q.pop(); return q; }).filter(p => p.length >= 3);
  const all = clean.flat();
  if (!all.length) return [];
  const xs = all.map(p => p[0]), ys = all.map(p => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const out = clean.map(p => p.map(([x, y]) => [x - cx, y - cy]));
  textCache.set(key, out);
  return out;
}

/* ---------------- geometry ---------------- */
function roundedRect(w, h, r, seg = 10) {
  if (r <= 1e-6) return [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]];
  const pts = [];
  for (const [cx, cy, start] of [[w / 2 - r, h / 2 - r, 0], [-w / 2 + r, h / 2 - r, 90], [-w / 2 + r, -h / 2 + r, 180], [w / 2 - r, -h / 2 + r, 270]])
    for (let k = 0; k <= seg; k++) { const a = (start + 90 * k / seg) * Math.PI / 180; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
  return pts;
}
// Local outlines before rotation: [{pts, closed, engrave}]
function localContours(s) {
  if (s.type === 'circle') return [{ pts: Array.from({ length: 72 }, (_, k) => { const a = k / 72 * 2 * Math.PI; return [s.d / 2 * Math.cos(a), s.d / 2 * Math.sin(a)]; }), closed: true }];
  if (s.type === 'rect') return [{ pts: roundedRect(s.w, s.h, Math.min(s.r || 0, Math.min(s.w, s.h) / 2)), closed: true }];
  if (s.type === 'slot') return [{ pts: roundedRect(s.w, s.h, Math.min(s.w, s.h) / 2), closed: true }];
  if (s.type === 'polygon') return [{ pts: Array.from({ length: s.n }, (_, k) => { const a = (-90 + 360 * k / s.n) * Math.PI / 180; return [s.d / 2 * Math.cos(a), s.d / 2 * Math.sin(a)]; }), closed: true }];
  if (s.type === 'path') return [{ pts: s.pts, closed: s.closed, engrave: s.engrave }];
  if (s.type === 'text') return textLocal(s).map(pts => ({ pts, closed: true, engrave: s.engrave }));
  return [];
}
function place(s, [px, py]) {
  const a = (s.rot || 0) * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
  const x = s.fx ? -px : px, y = s.fy ? -py : py;
  return [s.x + x * ca - y * sa, s.y + x * sa + y * ca];
}
const contours = s => localContours(s).map(c => ({ ...c, pts: c.pts.map(p => place(s, p)) }));
// Size of a shape in its own frame: half width and half height.
function localHalf(s) {
  if (s.type === 'rect' || s.type === 'slot') return [s.w / 2, s.h / 2];
  if (s.type === 'circle' || s.type === 'polygon') return [s.d / 2, s.d / 2];
  const pts = localContours(s).flatMap(c => c.pts);
  if (!pts.length) return [5, 5];
  return [Math.max(...pts.map(p => Math.abs(p[0]))) || 0.5, Math.max(...pts.map(p => Math.abs(p[1]))) || 0.5];
}
const pathD = (pts, closed = true) => 'M' + pts.map(p => p[0].toFixed(2) + ' ' + p[1].toFixed(2)).join('L') + (closed ? 'Z' : '');
const area = pts => Math.abs(pts.reduce((s, p, i) => { const q = pts[(i + 1) % pts.length]; return s + p[0] * q[1] - q[0] * p[1]; }, 0) / 2);
const length = (pts, closed) => pts.reduce((s, p, i) => { if (!closed && i === pts.length - 1) return s; const q = pts[(i + 1) % pts.length]; return s + Math.hypot(q[0] - p[0], q[1] - p[1]); }, 0);
function inside(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
}
// Nesting of solid outlines: depth = how many contain it (even = material, odd = hole).
function nesting(polys) {
  const areas = polys.map(area);
  return polys.map((p, i) => {
    const probe = p[0];
    const containers = polys.map((q, j) => j !== i && areas[j] > areas[i] && inside(probe, q) ? j : -1).filter(j => j >= 0);
    return { depth: containers.length, parent: containers.sort((a, b) => areas[a] - areas[b])[0] ?? -1 };
  });
}
// The finished part: shapes overlap even-odd (a shape inside another makes a hole),
// then every cut-away shape (scissors) is trimmed off. Returns pieces as [outer, ...holes].
const PC = window.polygonClipping;
let memoKey = '', memo = null;
function analyse() {
  const key = JSON.stringify(state.shapes) + '|' + Object.keys(fonts).length;
  if (key === memoKey && memo) return memo;
  const all = state.shapes.flatMap((s, si) => contours(s).map(c => ({ ...c, si, cutter: s.role === 'remove' && c.closed && !c.engrave })));
  const material = all.filter(c => c.closed && !c.engrave && !c.cutter);
  const cutters = all.filter(c => c.cutter);
  const lines = all.filter(c => (!c.closed || c.engrave) && state.shapes[c.si].role !== 'remove');
  let pieces = [];
  try {
    if (material.length) {
      let geom = PC.xor(...material.map(c => [c.pts]));
      if (cutters.length) geom = PC.difference(geom, ...cutters.map(c => [c.pts]));
      pieces = geom.map(poly => poly.map(ring => { const r = ring.slice(); r.pop(); return r; }));
    }
  } catch (e) {
    // Fall back to plain even-odd outlines if the boolean maths fails on odd input.
    pieces = material.map(c => [c.pts]);
  }
  const solid = pieces.flat().map(pts => ({ pts, closed: true }));
  memo = { all, material, cutters, lines, pieces, solid };
  memoKey = key;
  return memo;
}

/* ---------------- machines and materials ---------------- */
const machine = () => cfg.machines.find(m => m.id === state.machine) || cfg.machines[0];
// 3D lines (print, CNC) extrude the outline to a height; the laser cuts it flat.
const SHEET = ['laser', 'router', 'plasma'];
const isPrint = () => !SHEET.includes(machine().line);
const LINE_LABEL = { print: '3D print', laser: 'Laser', cnc: 'CNC mill', router: 'CNC router', plasma: 'Plasma' };
const engraveOnly = () => !!cfg.materials.find(m => m.id === state.material)?.engrave_only;
const bed = () => machine().bed;
const materialSel = $('material');
function buildMachines() {
  const box = $('machines');
  box.innerHTML = cfg.machines.map(m => `<label class="mpick"><input type="radio" name="machine" value="${m.id}" ${m.id === state.machine ? 'checked' : ''}>
    <span><strong>${m.name}</strong><em>${LINE_LABEL[m.line] || m.line} · ${m.bed[0]} × ${m.bed[1]} mm</em></span></label>`).join('');
  box.querySelectorAll('input').forEach(r => r.addEventListener('change', () => {
    state.machine = r.value; fillMaterials(); fit(); render(); save(); refresh3d();
  }));
}
function fillMaterials() {
  const m = machine();
  const mats = cfg.materials.filter(x => x.line === m.line && (!x.machines.length || x.machines.includes(m.id)));
  materialSel.innerHTML = mats.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
  if (!mats.some(x => x.id === state.material)) state.material = mats[0]?.id || '';
  materialSel.value = state.material;
  $('height-field').hidden = SHEET.includes(m.line);
}
materialSel.addEventListener('change', () => { state.material = materialSel.value; render(); renderFacts(); save(); refresh3d(); });
$('height').addEventListener('input', e => { const v = parseFloat(e.target.value); if (v > 0) { state.height = v; renderFacts(); save(); refresh3d(); } });
$('quantity').addEventListener('input', e => { const v = parseInt(e.target.value, 10); if (v > 0) { state.quantity = v; save(); } });

/* ---------------- shapes and templates ---------------- */
const centre = () => { const [w, h] = bed(); return [w / 2, h / 2]; };
function make(type, extra = {}) {
  const [cx, cy] = centre();
  const sizes = { rect: { w: 60, h: 40, r: 0 }, circle: { d: 30 }, slot: { w: 40, h: 8 }, polygon: { d: 40, n: 6 }, text: { text: 'PYSLATE', size: 20, font: 'sans', engrave: true } };
  return { id: uid++, type, x: cx, y: cy, rot: 0, ...sizes[type], ...extra };
}
const at = (dx, dy, type, extra) => { const [cx, cy] = centre(); return make(type, { x: cx + dx, y: cy + dy, ...extra }); };
const TEMPLATES = {
  'Name sign': () => [at(0, 0, 'rect', { w: 240, h: 90, r: 14 }), at(0, -6, 'text', { text: 'WORKSHOP', size: 30, engrave: true }), at(0, 26, 'text', { text: 'EST. 2026', size: 10, engrave: true }), at(-108, 0, 'circle', { d: 5 }), at(108, 0, 'circle', { d: 5 })],
  'Mounting plate': () => [at(0, 0, 'rect', { w: 100, h: 60, r: 4 }), ...[[-42, -22], [42, -22], [-42, 22], [42, 22]].map(([x, y]) => at(x, y, 'circle', { d: 5 }))],
  'Control panel': () => [at(0, 0, 'rect', { w: 140, h: 90, r: 4 }), at(-30, -12, 'rect', { w: 50, h: 30, r: 2 }), at(35, -12, 'circle', { d: 16 }), at(35, 22, 'circle', { d: 12 }), at(-30, 25, 'slot', { w: 40, h: 6 }),
    ...[[-62, -37], [62, -37], [-62, 37], [62, 37]].map(([x, y]) => at(x, y, 'circle', { d: 3.5 })), at(35, -32, 'text', { text: 'POWER', size: 4, engrave: true })],
  'Stencil letters': () => [at(0, 0, 'rect', { w: 220, h: 70, r: 6 }), at(0, 0, 'text', { text: 'PYSLATE', size: 36, font: 'stencil', engrave: false })],
  'Washer': () => [at(0, 0, 'circle', { d: 40 }), at(0, 0, 'circle', { d: 16 })],
  'Hex spacer': () => [at(0, 0, 'polygon', { d: 40, n: 6 }), at(0, 0, 'circle', { d: 20 })],
};

/* ---------------- persistence ---------------- */
function store() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) { /* storage blocked */ } }
// Undo history: a snapshot of the shapes after each change. Quick edits (typing) merge into one step.
const history = [], future = [];
let lastCommit = 0;
function save() {
  const snap = JSON.stringify(state.shapes);
  if (history[history.length - 1] !== snap) {
    const now = Date.now();
    if (now - lastCommit < 500 && history.length > 1 && document.activeElement?.tagName === 'INPUT') history[history.length - 1] = snap;
    else { history.push(snap); if (history.length > 200) history.shift(); }
    lastCommit = now; future.length = 0;
  }
  store(); undoButtons();
}
function restore(snap) {
  state.shapes = JSON.parse(snap);
  sel = sel.filter(i => i < state.shapes.length); selected = sel.length ? sel[sel.length - 1] : -1;
  buildProps(); render(); store(); refresh3d(); undoButtons();
}
function undo() { if (history.length < 2) return; future.push(history.pop()); restore(history[history.length - 1]); }
function redo() { if (!future.length) return; const s = future.pop(); history.push(s); restore(s); }
function undoButtons() { $('undo').disabled = history.length < 2; $('redo').disabled = !future.length; }
$('undo').addEventListener('click', undo);
$('redo').addEventListener('click', redo);
document.addEventListener('keydown', ev => {
  if (!(ev.ctrlKey || ev.metaKey)) return;
  const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);
  const k = ev.key.toLowerCase();
  if (k === 'z' && !typing) { ev.preventDefault(); ev.shiftKey ? redo() : undo(); }
  else if (k === 'y' && !typing) { ev.preventDefault(); redo(); }
});
function load() {
  try {
    const s = JSON.parse(localStorage.getItem(STORE) || 'null');
    if (s && Array.isArray(s.shapes)) { state = { ...state, ...s }; uid = Math.max(0, ...state.shapes.map(x => x.id || 0)) + 1; return true; }
  } catch (e) { /* ignore */ }
  return false;
}

/* ---------------- board ---------------- */
let view = [0, 0, 300, 300];
function fit() {
  const [w, h] = bed();
  let x0 = 0, y0 = 0, x1 = w, y1 = h;
  for (const [x, y] of analyse().all.flatMap(c => c.pts)) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  const m = Math.max(x1 - x0, y1 - y0);
  view = [x0 - m * 0.07, y0 - m * 0.08, x1 - x0 + m * 0.1, y1 - y0 + m * 0.11];
  board.setAttribute('viewBox', view.join(' '));
  $('board-wrap').style.aspectRatio = `${view[2]} / ${view[3]}`;
}
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(SVGNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fmt = v => (Math.round(v * 10) / 10).toString();
const px = () => view[2] / Math.max(300, board.clientWidth || 800); // one screen pixel in mm

function rulers(bw, bh, u) {
  const g = el('g', { 'font-family': 'JetBrains Mono, monospace', 'font-size': u * 10, fill: '#7b808a' }, board);
  const major = bw > 500 || bh > 500 ? 100 : 50;
  const top = -u * 6, left = -u * 6;
  el('rect', { x: view[0], y: view[1], width: view[2], height: -view[1] - u * 2, fill: '#f4f5f7' }, g);
  el('rect', { x: view[0], y: view[1], width: -view[0] - u * 2, height: view[3], fill: '#f4f5f7' }, g);
  let d = '';
  for (let x = 0; x <= bw + 1e-6; x += 10) { const L = x % major === 0 ? u * 10 : x % 50 === 0 ? u * 7 : u * 4; d += `M${x} ${top}v${-L}`; if (x % major === 0) el('text', { x: x + u * 2, y: top - u * 10 }, g).textContent = x; }
  for (let y = 0; y <= bh + 1e-6; y += 10) { const L = y % major === 0 ? u * 10 : y % 50 === 0 ? u * 7 : u * 4; d += `M${left} ${y}h${-L}`; if (y % major === 0 && y > 0) el('text', { x: left - u * 12, y: y + u * 3, 'text-anchor': 'end' }, g).textContent = y; }
  el('path', { d, stroke: '#9aa0aa', 'stroke-width': u, fill: 'none' }, g);
  el('text', { x: bw, y: top - u * 22, 'text-anchor': 'end', fill: '#3d4048', 'font-weight': 600 }, g).textContent = `${machine().name} · ${bw} × ${bh} mm`;
}

function render() {
  board.textContent = '';
  const [bw, bh] = bed();
  const u = px();
  const defs = el('defs', {}, board);
  const pat = el('pattern', { id: 'grid', width: 10, height: 10, patternUnits: 'userSpaceOnUse' }, defs);
  el('path', { d: 'M10 0H0V10', fill: 'none', stroke: '#e3e5e9', 'stroke-width': u }, pat);
  const scrap = el('pattern', { id: 'scrap', width: 4, height: 4, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' }, defs);
  el('path', { d: 'M0 0V4', stroke: 'rgba(214,51,108,.35)', 'stroke-width': .8 }, scrap);
  el('rect', { x: view[0], y: view[1], width: view[2], height: view[3], fill: '#fbfbfc' }, board);
  el('rect', { x: 0, y: 0, width: bw, height: bh, fill: 'url(#grid)', stroke: '#b9bec7', 'stroke-width': u * 1.5, 'stroke-dasharray': `${u * 6} ${u * 4}` }, board);
  rulers(bw, bh, u);

  const { all, solid, cutters, lines } = analyse();
  if (solid.length) el('path', { d: solid.map(c => pathD(c.pts)).join(' '), 'fill-rule': 'evenodd', fill: MAT_COLORS[state.material] || '#ff9a3c', 'fill-opacity': .55, stroke: CUT, 'stroke-width': u * 1.6 }, board);
  for (const c of cutters) el('path', { d: pathD(c.pts), fill: 'url(#scrap)', stroke: '#d6336c', 'stroke-width': u * 1.2, 'stroke-dasharray': `${u * 5} ${u * 3}`, 'pointer-events': 'none' }, board);
  for (const c of lines) {
    el('path', { d: pathD(c.pts, c.closed), fill: 'none', stroke: c.engrave ? ENGRAVE : CUT, 'stroke-width': u * (c.engrave ? 1.2 : 1.6), 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, board);
  }
  // overall size
  const pts = all.flatMap(c => c.pts);
  if (pts.length) {
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const g = el('g', { stroke: SELECT, 'stroke-width': u, fill: SELECT, 'font-size': u * 12, 'font-family': 'JetBrains Mono, monospace' }, board);
    const off = u * 16;
    el('path', { d: `M${x0} ${y1 + off}H${x1}M${x0} ${y1 + off - u * 5}v${u * 10}M${x1} ${y1 + off - u * 5}v${u * 10}`, fill: 'none' }, g);
    el('text', { x: (x0 + x1) / 2, y: y1 + off + u * 15, 'text-anchor': 'middle', stroke: 'none' }, g).textContent = `${fmt(x1 - x0)} mm`;
    el('path', { d: `M${x1 + off} ${y0}V${y1}M${x1 + off - u * 5} ${y0}h${u * 10}M${x1 + off - u * 5} ${y1}h${u * 10}`, fill: 'none' }, g);
    el('text', { x: x1 + off + u * 6, y: (y0 + y1) / 2 + u * 4, stroke: 'none' }, g).textContent = `${fmt(y1 - y0)} mm`;
  }
  // hit targets, largest first so small shapes stay on top
  const order = state.shapes.map((s, i) => { const h = localHalf(s); return [h[0] * h[1], i]; }).sort((a, b) => b[0] - a[0]).map(x => x[1]);
  for (const i of order) {
    const s = state.shapes[i];
    const cs = contours(s);
    let d;
    if (s.type === 'text') { const [hw, hh] = localHalf(s); d = pathD([[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]].map(p => place(s, p))); }
    else d = cs.map(c => pathD(c.pts, c.closed)).join(' ');
    const open = s.type === 'path' && !s.closed;
    const hit = el('path', { d, fill: open ? 'none' : 'rgba(0,0,0,0)', stroke: open ? 'rgba(0,0,0,0)' : 'transparent', 'stroke-width': open ? u * 12 : u * 3, class: 'hit', 'pointer-events': open ? 'stroke' : 'all' }, board);
    hit.addEventListener('pointerdown', ev => { if (drawing) return; if (scissors) { ev.preventDefault(); ev.stopPropagation(); toggleCut([i]); return; } startMove(ev, i); });
  }
  if (sel.length === 1 && state.shapes[selected]) drawHandles(state.shapes[selected], u);
  else if (sel.length > 1) {
    for (const i of sel) { const b = bounds(i); el('rect', { x: b.x0, y: b.y0, width: b.x1 - b.x0, height: b.y1 - b.y0, fill: 'none', stroke: SELECT, 'stroke-width': u * 1.2, 'stroke-dasharray': `${u * 5} ${u * 3}`, 'pointer-events': 'none' }, board); }
  }
  if (act && act.guides) for (const g of act.guides) {
    el('path', { d: g.axis === 'x' ? `M${g.v} ${view[1]}V${view[1] + view[3]}` : `M${view[0]} ${g.v}H${view[0] + view[2]}`, stroke: '#d6336c', 'stroke-width': u, 'stroke-dasharray': `${u * 4} ${u * 3}`, 'pointer-events': 'none' }, board);
  }
  if (act && act.kind === 'marquee' && act.cur) {
    const [a, b] = [act.start, act.cur];
    el('rect', { x: Math.min(a[0], b[0]), y: Math.min(a[1], b[1]), width: Math.abs(b[0] - a[0]), height: Math.abs(b[1] - a[1]), fill: 'rgba(232,89,12,.08)', stroke: SELECT, 'stroke-width': u, 'pointer-events': 'none' }, board);
  }
  if (drawing) drawLinePreview(u);
  renderFacts();
}

/* ---------------- selection frame and handles ---------------- */
const uniformTypes = new Set(['circle', 'polygon', 'text']);
function drawHandles(s, u) {
  const [hw, hh] = localHalf(s);
  const pad = u * 4;
  const corners = [[-hw - pad, -hh - pad], [hw + pad, -hh - pad], [hw + pad, hh + pad], [-hw - pad, hh + pad]].map(p => place({ ...s, fx: 0, fy: 0 }, p));
  const g = el('g', {}, board);
  el('path', { d: pathD(corners), fill: 'none', stroke: SELECT, 'stroke-width': u * 1.2, 'stroke-dasharray': `${u * 5} ${u * 3}`, 'pointer-events': 'none' }, g);
  const handle = (lx, ly, kind, cursor) => {
    const [x, y] = place({ ...s, fx: 0, fy: 0 }, [lx, ly]);
    const h = el('rect', { x: x - u * 5, y: y - u * 5, width: u * 10, height: u * 10, fill: '#fff', stroke: SELECT, 'stroke-width': u * 1.5, class: 'handle', style: `cursor:${cursor}` }, g);
    h.addEventListener('pointerdown', ev => startHandle(ev, kind));
  };
  const X = hw + pad, Y = hh + pad;
  handle(-X, -Y, [-1, -1], 'nwse-resize'); handle(X, -Y, [1, -1], 'nesw-resize'); handle(X, Y, [1, 1], 'nwse-resize'); handle(-X, Y, [-1, 1], 'nesw-resize');
  if (!uniformTypes.has(s.type)) { handle(0, -Y, [0, -1], 'ns-resize'); handle(X, 0, [1, 0], 'ew-resize'); handle(0, Y, [0, 1], 'ns-resize'); handle(-X, 0, [-1, 0], 'ew-resize'); }
  if (s.type !== 'circle') {
    const top = place({ ...s, fx: 0, fy: 0 }, [0, -Y]), knob = place({ ...s, fx: 0, fy: 0 }, [0, -Y - u * 26]);
    el('path', { d: `M${top[0]} ${top[1]}L${knob[0]} ${knob[1]}`, stroke: SELECT, 'stroke-width': u * 1.2, 'pointer-events': 'none' }, g);
    const r = el('circle', { cx: knob[0], cy: knob[1], r: u * 6, fill: SELECT, class: 'handle', style: 'cursor:grab' }, g);
    r.addEventListener('pointerdown', ev => startHandle(ev, 'rotate'));
  }
  el('circle', { cx: s.x, cy: s.y, r: u * 3, fill: SELECT, 'pointer-events': 'none' }, g);
}

// Scale a shape by kx, ky in its own frame.
function scaleShape(s, kx, ky, base) {
  if (s.type === 'rect' || s.type === 'slot') { s.w = Math.max(0.5, base.w * kx); s.h = Math.max(0.5, base.h * ky); if (s.type === 'rect') s.r = Math.min(base.r, s.w / 2, s.h / 2); }
  else if (s.type === 'circle' || s.type === 'polygon') s.d = Math.max(0.5, base.d * Math.max(kx, ky));
  else if (s.type === 'text') s.size = Math.max(1, base.size * Math.max(kx, ky));
  else if (s.type === 'path') s.pts = base.pts.map(([x, y]) => [x * kx, y * ky]);
}
const round = v => Math.round(v * 10) / 10;

/* ---------------- pointer interaction ---------------- */
let act = null;
function svgPoint(ev) { const pt = board.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; return pt.matrixTransform(board.getScreenCTM().inverse()); }
function toLocal(s, p) { const a = -(s.rot || 0) * Math.PI / 180, dx = p.x - s.x, dy = p.y - s.y; return [dx * Math.cos(a) - dy * Math.sin(a), dx * Math.sin(a) + dy * Math.cos(a)]; }
function startMove(ev, i) {
  ev.preventDefault(); ev.stopPropagation(); board.focus({ preventScroll: true });
  if (ev.shiftKey) {
    sel = sel.includes(i) ? sel.filter(j => j !== i) : [...sel, i];
    selected = sel.length ? sel[sel.length - 1] : -1;
    buildProps(); render(); return;
  }
  if (!sel.includes(i)) select(i); else selected = i;
  buildProps();
  const p = svgPoint(ev);
  const others = state.shapes.map((_, j) => j).filter(j => !sel.includes(j));
  const [bw, bh] = bed();
  const xs = [0, bw / 2, bw], ys = [0, bh / 2, bh];
  for (const j of others) { const b = bounds(j); xs.push(b.x0, (b.x0 + b.x1) / 2, b.x1); ys.push(b.y0, (b.y0 + b.y1) / 2, b.y1); }
  act = { kind: 'move', start: [p.x, p.y], orig: sel.map(j => [state.shapes[j].x, state.shapes[j].y]), box: unionBounds(sel), xs, ys, guides: [] };
  board.setPointerCapture(ev.pointerId); render();
}
// Snap the moving box's edges and centre to nearby edges and centres.
function snapDelta(lines, edges, tol) {
  let best = null;
  for (const e of edges) for (const l of lines) { const d = l - e; if (Math.abs(d) <= tol && (!best || Math.abs(d) < Math.abs(best.d))) best = { d, v: l }; }
  return best;
}
function startHandle(ev, kind) {
  ev.preventDefault(); ev.stopPropagation();
  const s = state.shapes[selected];
  const [hw, hh] = localHalf(s);
  act = { kind, base: JSON.parse(JSON.stringify(s)), hw, hh };
  board.setPointerCapture(ev.pointerId);
}
board.addEventListener('pointermove', ev => {
  if (drawing) { drawing.cursor = snapPoint(svgPoint(ev), ev.shiftKey); render(); return; }
  if (!act) return;
  const s = state.shapes[selected], p = svgPoint(ev);
  if (act.kind === 'marquee') { act.cur = [p.x, p.y]; render(); return; }
  if (act.kind === 'move') {
    let dx = Math.round((p.x - act.start[0]) * 2) / 2, dy = Math.round((p.y - act.start[1]) * 2) / 2;
    act.guides = [];
    if (!ev.altKey) {
      const b = act.box, tol = px() * 7;
      const sx = snapDelta(act.xs, [b.x0 + dx, (b.x0 + b.x1) / 2 + dx, b.x1 + dx], tol);
      const sy = snapDelta(act.ys, [b.y0 + dy, (b.y0 + b.y1) / 2 + dy, b.y1 + dy], tol);
      if (sx) { dx += sx.d; act.guides.push({ axis: 'x', v: sx.v }); }
      if (sy) { dy += sy.d; act.guides.push({ axis: 'y', v: sy.v }); }
    }
    sel.forEach((j, k) => { state.shapes[j].x = round(act.orig[k][0] + dx); state.shapes[j].y = round(act.orig[k][1] + dy); });
  }
  else if (act.kind === 'rotate') {
    let a = Math.atan2(p.y - s.y, p.x - s.x) * 180 / Math.PI + 90;
    a = ev.shiftKey ? Math.round(a / 15) * 15 : Math.round(a);
    s.rot = ((a + 540) % 360) - 180;
  } else {
    // Resize from the opposite side, which stays put.
    const [sx, sy] = act.kind, b = act.base;
    const [lx, ly] = toLocal(b, p);
    let kx = 1, ky = 1, cxl = 0, cyl = 0;
    if (sx) { const opp = -sx * act.hw; const w = Math.max(1, Math.abs(lx - opp)); kx = w / (2 * act.hw); cxl = (lx + opp) / 2; }
    if (sy) { const opp = -sy * act.hh; const h = Math.max(1, Math.abs(ly - opp)); ky = h / (2 * act.hh); cyl = (ly + opp) / 2; }
    if (uniformTypes.has(s.type) || (ev.shiftKey && sx && sy)) {
      const k = Math.max(sx ? kx : 0, sy ? ky : 0); kx = ky = k;
      if (sx) cxl = -sx * act.hw + sx * act.hw * k; if (sy) cyl = -sy * act.hh + sy * act.hh * k;
    }
    scaleShape(s, kx, ky, b);
    const a = (b.rot || 0) * Math.PI / 180;
    s.x = round(b.x + cxl * Math.cos(a) - cyl * Math.sin(a)); s.y = round(b.y + cxl * Math.sin(a) + cyl * Math.cos(a));
    if (s.w) s.w = round(s.w); if (s.h) s.h = round(s.h); if (s.d) s.d = round(s.d); if (s.size) s.size = round(s.size);
  }
  render(); syncProps();
});
board.addEventListener('pointerup', () => {
  if (!act) return;
  if (act.kind === 'marquee') {
    if (act.cur) {
      const x0 = Math.min(act.start[0], act.cur[0]), x1 = Math.max(act.start[0], act.cur[0]), y0 = Math.min(act.start[1], act.cur[1]), y1 = Math.max(act.start[1], act.cur[1]);
      const hit = state.shapes.map((_, i) => i).filter(i => { const b = bounds(i); return b.x0 >= x0 && b.x1 <= x1 && b.y0 >= y0 && b.y1 <= y1; });
      sel = act.add ? [...new Set([...sel, ...hit])] : hit; selected = sel.length ? sel[sel.length - 1] : -1;
    }
    act = null; buildProps(); render(); return;
  }
  act = null; render(); save(); refresh3d();
});
board.addEventListener('pointerdown', ev => {
  if (scissors) return;
  if (drawing) { ev.preventDefault(); addLinePoint(svgPoint(ev), ev.shiftKey, ev.detail >= 2); return; }
  if (!ev.target.classList.contains('hit') && !ev.target.classList.contains('handle')) {
    if (!ev.shiftKey) select(-1);
    const p = svgPoint(ev);
    act = { kind: 'marquee', start: [p.x, p.y], cur: null, add: ev.shiftKey };
    board.setPointerCapture(ev.pointerId); buildProps(); render();
  }
});
board.addEventListener('keydown', ev => {
  if (scissors && ev.key === 'Escape') { ev.preventDefault(); setScissors(false); return; }
  if (drawing) {
    if (ev.key === 'Enter') { ev.preventDefault(); finishLine(false); }
    else if (ev.key === 'Escape') { ev.preventDefault(); drawing = null; setLineMode(false); render(); }
    return;
  }
  if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'a') { ev.preventDefault(); sel = state.shapes.map((_, i) => i); selected = sel[sel.length - 1] ?? -1; buildProps(); render(); return; }
  if (ev.key === 'Escape') { select(-1); buildProps(); render(); return; }
  const s = state.shapes[selected];
  if (!s) return;
  const step = ev.shiftKey ? 10 : 1;
  const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
  if (moves[ev.key]) { ev.preventDefault(); for (const j of sel) { state.shapes[j].x += moves[ev.key][0]; state.shapes[j].y += moves[ev.key][1]; } }
  else if (ev.key === 'Delete' || ev.key === 'Backspace') { ev.preventDefault(); removeSelected(); return; }
  else if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'd') { ev.preventDefault(); duplicate(); return; }
  else if ((ev.key === 'r' || ev.key === 'R') && sel.length === 1) { s.rot = (((s.rot || 0) + (ev.shiftKey ? -90 : 90)) + 540) % 360 - 180; }
  else return;
  render(); syncProps(); save(); refresh3d();
});

/* ---------------- line tool ---------------- */
let drawing = null;
function setLineMode(on) {
  $('line-tool').setAttribute('aria-pressed', String(on));
  board.classList.toggle('drawing', on);
  $('board-help').textContent = on
    ? 'Click to add points. Click the first point to close the shape, or double-click / press Enter to finish an open line. Shift keeps angles to 15°. Esc cancels.'
    : 'Drag to move; shapes snap to edges and centres (hold Alt to stop). Shift-click or drag a box to select several. Corner handles scale (Shift keeps proportions), side handles stretch, the round handle rotates. Arrows nudge, R rotates 90°, Delete removes, Ctrl+D duplicates, Ctrl+A selects all.';
}
function snapPoint(p, angle) {
  let x = Math.round(p.x * 2) / 2, y = Math.round(p.y * 2) / 2;
  const last = drawing && drawing.pts[drawing.pts.length - 1];
  if (angle && last) {
    const a = Math.round(Math.atan2(y - last[1], x - last[0]) / (Math.PI / 12)) * (Math.PI / 12), r = Math.hypot(x - last[0], y - last[1]);
    x = round(last[0] + r * Math.cos(a)); y = round(last[1] + r * Math.sin(a));
  }
  return [x, y];
}
function addLinePoint(p, angle, dbl) {
  const q = snapPoint(p, angle);
  const pts = drawing.pts;
  if (pts.length >= 3 && Math.hypot(q[0] - pts[0][0], q[1] - pts[0][1]) < px() * 10) { finishLine(true); return; }
  if (dbl) { finishLine(false); return; }
  const last = pts[pts.length - 1];
  if (!last || Math.hypot(q[0] - last[0], q[1] - last[1]) > 0.2) pts.push(q);
  render();
}
function finishLine(closed) {
  const pts = drawing.pts;
  drawing = null; setLineMode(false);
  if (pts.length < 2) { render(); return; }
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  state.shapes.push({ id: uid++, type: 'path', x: cx, y: cy, rot: 0, pts: pts.map(([x, y]) => [round(x - cx), round(y - cy)]), closed: closed && pts.length >= 3, engrave: false });
  select(state.shapes.length - 1); buildProps(); render(); save(); refresh3d();
}
function drawLinePreview(u) {
  const pts = drawing.pts.slice();
  if (drawing.cursor) pts.push(drawing.cursor);
  if (pts.length >= 2) el('path', { d: pathD(pts, false), fill: 'none', stroke: SELECT, 'stroke-width': u * 1.6, 'stroke-dasharray': `${u * 4} ${u * 3}`, 'pointer-events': 'none' }, board);
  drawing.pts.forEach((p, i) => el('circle', { cx: p[0], cy: p[1], r: u * (i === 0 ? 6 : 3.5), fill: i === 0 ? '#fff' : SELECT, stroke: SELECT, 'stroke-width': u * 1.5, 'pointer-events': 'none' }, board));
  if (drawing.cursor && drawing.pts.length) {
    const last = drawing.pts[drawing.pts.length - 1], c = drawing.cursor;
    el('text', { x: c[0] + u * 10, y: c[1] - u * 10, 'font-size': u * 12, fill: SELECT, 'font-family': 'JetBrains Mono, monospace', 'pointer-events': 'none' }, board).textContent = `${fmt(Math.hypot(c[0] - last[0], c[1] - last[1]))} mm`;
  }
}
$('line-tool').addEventListener('click', () => {
  if (scissors) setScissors(false);
  if (drawing) { finishLine(false); return; }
  drawing = { pts: [], cursor: null }; select(-1); buildProps(); setLineMode(true); board.focus({ preventScroll: true }); render();
});

/* ---------------- scissors: mark shapes as scrap to cut away ---------------- */
let scissors = false;
const HELP_SCISSORS = 'Scissors: click any shape to cut it away from the part (click again to keep it as material). Scrap shapes are hatched in pink. Esc or the Cut away button to finish.';
function setScissors(on) {
  scissors = on;
  $('scissors-tool').setAttribute('aria-pressed', String(on));
  board.classList.toggle('scissors', on);
  if (on) $('board-help').textContent = HELP_SCISSORS; else setLineMode(false);
}
function toggleCut(idx) {
  const ok = idx.filter(i => canCut(state.shapes[i]));
  if (!ok.length) { status('Open lines and engraving can\'t cut away material. Use a closed shape.', true); return; }
  const allCut = ok.every(i => state.shapes[i].role === 'remove');
  for (const i of ok) state.shapes[i].role = allCut ? undefined : 'remove';
  buildProps(); render(); save(); refresh3d();
}
$('scissors-tool').addEventListener('click', () => {
  if (drawing) finishLine(false);
  if (scissors) { setScissors(false); return; }
  if (sel.length) { toggleCut(sel); return; }
  setScissors(true); board.focus({ preventScroll: true });
});

/* ---------------- properties panel ---------------- */
const FIELDS = {
  rect: [['w', 'Width'], ['h', 'Height'], ['r', 'Corner radius']],
  slot: [['w', 'Length'], ['h', 'Width']],
  circle: [['d', 'Diameter']],
  polygon: [['d', 'Across corners'], ['n', 'Sides']],
  path: [],
  text: [['size', 'Letter height']],
};
const NAMES = { rect: 'Rectangle', circle: 'Circle', slot: 'Slot', polygon: 'Polygon', path: 'Line', text: 'Text' };
const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function shapeRole(i) {
  const s = state.shapes[i];
  if (s.role === 'remove') return 'cut away';
  if (s.engrave) return 'engraved';
  if (s.type === 'path' && !s.closed) return 'cut line';
  const { material } = analyse();
  const mine = material.filter(c => c.si === i);
  const others = material.filter(c => c.si !== i);
  if (!mine.length) return 'part';
  const probe = mine[0].pts[0];
  return others.filter(c => area(c.pts) > area(mine[0].pts) && inside(probe, c.pts)).length % 2 ? 'hole' : 'material';
}
const canCut = s => !(s.type === 'path' && !s.closed) && !s.engrave;
function buildProps() {
  const box = $('props'), s = state.shapes[selected];
  if (!s) { box.innerHTML = '<p class="fine">Click a shape to edit it, or drag its handles to scale and rotate it. Shift-click or drag a box to select several.</p>'; return; }
  if (sel.length > 1) {
    const b = unionBounds(sel);
    box.innerHTML = `<p class="shape-name">${sel.length} shapes selected</p><p class="fine size-note">Together ${fmt(b.x1 - b.x0)} × ${fmt(b.y1 - b.y0)} mm</p>
      ${alignBar()}<div class="prop-actions"><button type="button" class="chip" data-act="dup">Duplicate</button><button type="button" class="chip danger" data-act="del">Delete</button></div>`;
    wireAlign(box);
    box.querySelector('[data-act=dup]').addEventListener('click', duplicate);
    box.querySelector('[data-act=del]').addEventListener('click', removeSelected);
    return;
  }
  const [hw, hh] = localHalf(s);
  const num = (k, label, step = 0.5) => `<label>${label}<input type="number" step="${step}" data-k="${k}" value="${s[k] ?? 0}"></label>`;
  box.innerHTML = `<p class="shape-name">${NAMES[s.type]} <span>${shapeRole(selected)}</span></p>
    ${s.type === 'text' ? `<label class="field wide-field">Text<input type="text" id="p-text" maxlength="60" value="${esc(s.text)}"></label>
      <label class="field wide-field">Font<select id="p-font">${Object.entries(FONTS).map(([k, f]) => `<option value="${k}" ${k === s.font ? 'selected' : ''}>${f.label}</option>`).join('')}</select></label>` : ''}
    <div class="prop-grid">
      ${num('x', 'X centre')}${num('y', 'Y centre')}
      ${FIELDS[s.type].map(([k, l]) => num(k, l, k === 'n' ? 1 : 0.5)).join('')}
      ${s.type !== 'circle' ? num('rot', 'Rotation °', 1) : ''}
      <label>Scale %<input type="number" step="5" min="1" id="p-scale" value="100"></label>
    </div>
    <p class="fine size-note">Size ${fmt(hw * 2)} × ${fmt(hh * 2)} mm</p>
    ${s.type === 'path' || s.type === 'text' ? `<div class="segmented small" role="radiogroup" aria-label="Line type">
        <label><input type="radio" name="p-mode" value="cut" ${s.engrave ? '' : 'checked'}><span>Cut</span></label>
        <label><input type="radio" name="p-mode" value="engrave" ${s.engrave ? 'checked' : ''}><span>Engrave</span></label></div>` : ''}
    ${canCut(s) ? `<div class="segmented small" role="radiogroup" aria-label="Role">
        <label><input type="radio" name="p-role" value="add" ${s.role === 'remove' ? '' : 'checked'}><span>Material</span></label>
        <label><input type="radio" name="p-role" value="remove" ${s.role === 'remove' ? 'checked' : ''}><span>✂ Cut away</span></label></div>` : ''}
    ${s.type === 'path' ? `<label class="check"><input type="checkbox" id="p-closed" ${s.closed ? 'checked' : ''} ${s.pts.length < 3 ? 'disabled' : ''}> Closed shape</label>` : ''}
    <div class="prop-actions">
      ${s.type !== 'circle' ? '<button type="button" class="chip" data-act="rotl">⟲ 90°</button><button type="button" class="chip" data-act="rotr">⟳ 90°</button>' : ''}
      ${s.type === 'path' || s.type === 'text' || s.type === 'polygon' ? '<button type="button" class="chip" data-act="fx">Flip ↔</button><button type="button" class="chip" data-act="fy">Flip ↕</button>' : ''}
      <button type="button" class="chip" data-act="dup">Duplicate</button><button type="button" class="chip danger" data-act="del">Delete</button>
    </div>${alignBar()}`;
  wireAlign(box);
  const changed = () => { render(); save(); refresh3d(); };
  box.querySelectorAll('input[data-k]').forEach(inp => inp.addEventListener('input', () => {
    const v = parseFloat(inp.value); if (!Number.isFinite(v)) return;
    const k = inp.dataset.k;
    if (['w', 'h', 'd', 'size'].includes(k) && v < 0.5) return;
    if (k === 'n' && (v < 3 || v > 24)) return;
    s[k] = k === 'n' ? Math.round(v) : v;
    changed();
  }));
  const sc = $('p-scale');
  sc.addEventListener('change', () => {
    const k = parseFloat(sc.value) / 100; if (!(k > 0)) return;
    scaleShape(s, k, k, JSON.parse(JSON.stringify(s)));
    sc.value = 100; buildProps(); changed();
  });
  $('p-text')?.addEventListener('input', e => { s.text = e.target.value; changed(); });
  $('p-font')?.addEventListener('change', e => { s.font = e.target.value; changed(); });
  box.querySelectorAll('input[name=p-mode]').forEach(r => r.addEventListener('change', () => { s.engrave = r.value === 'engrave'; buildProps(); changed(); }));
  box.querySelectorAll('input[name=p-role]').forEach(r => r.addEventListener('change', () => { s.role = r.value === 'remove' ? 'remove' : undefined; buildProps(); changed(); }));
  $('p-closed')?.addEventListener('change', e => { s.closed = e.target.checked; buildProps(); changed(); });
  box.querySelectorAll('[data-act]:not([data-act=centre]):not([data-act^=dist])').forEach(b => b.addEventListener('click', () => {
    const a = b.dataset.act;
    if (a === 'del') return removeSelected();
    if (a === 'dup') return duplicate();
    if (a === 'rotl' || a === 'rotr') s.rot = ((((s.rot || 0) + (a === 'rotr' ? 90 : -90)) + 540) % 360) - 180;
    if (a === 'fx') s.fx = !s.fx;
    if (a === 'fy') s.fy = !s.fy;
    syncProps(); changed();
  }));
}
function syncProps() {
  const s = state.shapes[selected]; if (!s) return;
  if (sel.length > 1) { const b = unionBounds(sel), n = $('props').querySelector('.size-note'); if (n) n.textContent = `Together ${fmt(b.x1 - b.x0)} × ${fmt(b.y1 - b.y0)} mm`; return; }
  $('props').querySelectorAll('input[data-k]').forEach(inp => { if (document.activeElement !== inp) inp.value = round(s[inp.dataset.k] ?? 0); });
  const [hw, hh] = localHalf(s);
  const note = $('props').querySelector('.size-note'); if (note) note.textContent = `Size ${fmt(hw * 2)} × ${fmt(hh * 2)} mm`;
}
function removeSelected() {
  if (!sel.length) return;
  state.shapes = state.shapes.filter((_, i) => !sel.includes(i));
  select(-1); buildProps(); render(); save(); refresh3d();
}
function duplicate() {
  if (!sel.length) return;
  const start = state.shapes.length;
  for (const i of sel) { const s = state.shapes[i]; state.shapes.push({ ...JSON.parse(JSON.stringify(s)), id: uid++, x: s.x + 10, y: s.y + 10 }); }
  sel = state.shapes.map((_, i) => i).filter(i => i >= start); selected = sel[sel.length - 1];
  buildProps(); render(); save(); refresh3d();
}

/* ---------------- alignment ---------------- */
function bounds(i) {
  const s = state.shapes[i];
  let pts;
  if (s.type === 'text') { const [hw, hh] = localHalf(s); pts = [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]].map(p => place(s, p)); }
  else pts = contours(s).flatMap(c => c.pts);
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  return { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };
}
function unionBounds(list) {
  const bs = list.map(bounds);
  return { x0: Math.min(...bs.map(b => b.x0)), x1: Math.max(...bs.map(b => b.x1)), y0: Math.min(...bs.map(b => b.y0)), y1: Math.max(...bs.map(b => b.y1)) };
}
// One shape aligns to the bed; several align to the box around them.
function align(how) {
  if (!sel.length) return;
  const [bw, bh] = bed();
  const ref = sel.length === 1 ? { x0: 0, x1: bw, y0: 0, y1: bh } : unionBounds(sel);
  for (const i of sel) {
    const s = state.shapes[i], b = bounds(i);
    if (how === 'left') s.x += ref.x0 - b.x0;
    if (how === 'right') s.x += ref.x1 - b.x1;
    if (how === 'hcenter') s.x += (ref.x0 + ref.x1) / 2 - (b.x0 + b.x1) / 2;
    if (how === 'top') s.y += ref.y0 - b.y0;
    if (how === 'bottom') s.y += ref.y1 - b.y1;
    if (how === 'vcenter') s.y += (ref.y0 + ref.y1) / 2 - (b.y0 + b.y1) / 2;
    s.x = round(s.x); s.y = round(s.y);
  }
  afterAlign();
}
function centreOnBed() {
  if (!sel.length) return;
  const [bw, bh] = bed(), b = unionBounds(sel);
  const dx = bw / 2 - (b.x0 + b.x1) / 2, dy = bh / 2 - (b.y0 + b.y1) / 2;
  for (const i of sel) { state.shapes[i].x = round(state.shapes[i].x + dx); state.shapes[i].y = round(state.shapes[i].y + dy); }
  afterAlign();
}
// Equal gaps between shapes, keeping the outer two where they are.
function distribute(axis) {
  if (sel.length < 3) return;
  const lo = axis === 'x' ? 'x0' : 'y0', hi = axis === 'x' ? 'x1' : 'y1';
  const items = sel.map(i => ({ i, b: bounds(i) })).sort((a, b) => a.b[lo] - b.b[lo]);
  const span = items[items.length - 1].b[hi] - items[0].b[lo];
  const used = items.reduce((t, it) => t + it.b[hi] - it.b[lo], 0);
  const gap = (span - used) / (items.length - 1);
  let pos = items[0].b[hi] + gap;
  for (const it of items.slice(1, -1)) { state.shapes[it.i][axis] = round(state.shapes[it.i][axis] + pos - it.b[lo]); pos += it.b[hi] - it.b[lo] + gap; }
  afterAlign();
}
function afterAlign() { render(); syncProps(); save(); refresh3d(); }
const ALIGN_BUTTONS = [
  ['left', 'Align left', 'M4 3v18M8 7h10v4H8zM8 14h6v4H8z'], ['hcenter', 'Align centres left to right', 'M12 3v18M6 7h12v4H6zM8 14h8v4H8z'], ['right', 'Align right', 'M20 3v18M6 7h10v4H6zM10 14h6v4h-6z'],
  ['top', 'Align top', 'M3 4h18M7 8v10h4V8zM14 8v6h4V8z'], ['vcenter', 'Align middles top to bottom', 'M3 12h18M7 6v12h4V6zM14 8v8h4V8z'], ['bottom', 'Align bottom', 'M3 20h18M7 6v10h4V6zM14 10v6h4v-6z'],
];
function alignBar() {
  const many = sel.length > 1;
  return `<h3>${many ? `Align ${sel.length} shapes` : 'Align to the bed'}</h3>
    <div class="align-bar">${ALIGN_BUTTONS.map(([k, t, d]) => `<button type="button" class="icon-btn" data-align="${k}" title="${t}" aria-label="${t}"><svg viewBox="0 0 24 24"><path d="${d}"/></svg></button>`).join('')}</div>
    <div class="prop-actions">
      <button type="button" class="chip" data-act="centre">Centre on bed</button>
      ${sel.length >= 3 ? '<button type="button" class="chip" data-act="distx">Space evenly ↔</button><button type="button" class="chip" data-act="disty">Space evenly ↕</button>' : ''}
    </div>`;
}
function wireAlign(box) {
  box.querySelectorAll('[data-align]').forEach(b => b.addEventListener('click', () => align(b.dataset.align)));
  box.querySelector('[data-act=centre]')?.addEventListener('click', centreOnBed);
  box.querySelector('[data-act=distx]')?.addEventListener('click', () => distribute('x'));
  box.querySelector('[data-act=disty]')?.addEventListener('click', () => distribute('y'));
}

/* ---------------- facts and warnings ---------------- */
function renderFacts() {
  const { all, solid, pieces, material, lines } = analyse();
  const facts = $('facts'), warn = $('warnings');
  const [bw, bh] = bed();
  if (!all.length) { facts.innerHTML = '<dt>Shapes</dt><dd>None yet</dd>'; warn.innerHTML = ''; $('board-size').textContent = ''; return; }
  const kept = [...solid, ...lines];
  const pts = (kept.length ? kept : all).flatMap(c => c.pts), xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
  const holes = pieces.reduce((t, p) => t + p.length - 1, 0);
  const cut = solid.reduce((s, c) => s + length(c.pts, true), 0) + lines.filter(c => !c.engrave).reduce((s, c) => s + length(c.pts, c.closed), 0);
  const engr = lines.filter(c => c.engrave).reduce((s, c) => s + length(c.pts, c.closed), 0);
  const mat = cfg.materials.find(m => m.id === state.material);
  const thick = isPrint() ? state.height : (mat?.thickness || 3);
  $('board-size').textContent = `${fmt(w)} × ${fmt(h)} mm`;
  facts.innerHTML = `<dt>Size</dt><dd>${fmt(w)} × ${fmt(h)} × ${fmt(thick)} mm</dd>
    <dt>Pieces</dt><dd>${pieces.length} (${holes} hole${holes === 1 ? '' : 's'})</dd>
    ${isPrint() ? '' : engraveOnly() ? `<dt>Engrave length</dt><dd>${Math.round(cut + engr)} mm</dd>` : `<dt>Cut length</dt><dd>${Math.round(cut)} mm</dd>${engr ? `<dt>Engrave length</dt><dd>${Math.round(engr)} mm</dd>` : ''}`}`;
  const issues = [];
  if (Math.min(...xs) < 0 || Math.min(...ys) < 0 || Math.max(...xs) > bw || Math.max(...ys) > bh)
    issues.push(w > bw || h > bh ? `Bigger than the ${machine().name} bed (${bw} × ${bh} mm), so we'll review it before pricing.` : 'Part of the design is off the bed. Drag it back inside the dashed area.');
  const sp = material.map(c => c.pts), areas = sp.map(area);
  const crosses = sp.some((p, i) => sp.some((q, j) => { if (i === j || areas[j] <= areas[i] || material[i].si === material[j].si) return false; const n = p.filter(pt => inside(pt, q)).length; return n > 0 && n < p.length; }));
  if (crosses) issues.push('A shape crosses the edge of another, so the overlap becomes a gap. To trim material away cleanly, select the shape and use the scissors.');
  const textCut = state.shapes.some((s, i) => s.type === 'text' && !s.engrave && s.font !== 'stencil');
  if (['router', 'plasma'].includes(machine().line) && lines.some(c => c.engrave)) issues.push(machine().line === 'plasma' ? 'The plasma table can\'t engrave, so engraved lines and text are left for the shop to review.' : 'On the router, engraved lines and text are carved with a V-bit.');
  if (engraveOnly()) issues.push('Metal engraving: everything is engraved and nothing is cut. The outline sets the size of the metal blank we engrave.');
  else if (textCut && !isPrint()) issues.push('Cut-through letters like O, A and B lose their centres. Use the stencil font, or engrave the text.');
  else if (pieces.length > 1) issues.push(`This design comes out as ${pieces.length} separate pieces. Use the scissors to cut away any you don't want.`);
  if (isPrint() && lines.some(c => c.engrave)) issues.push(`Engraving only applies to laser cutting, so engraved lines and text are left off a ${machine().line === 'cnc' ? 'machined part' : '3D print'}.`);
  if (isPrint() && lines.some(c => !c.closed && !c.engrave)) issues.push(`Open lines are only cut on the laser, so they are left off a ${machine().line === 'cnc' ? 'machined part' : '3D print'}.`);
  if (!solid.length) issues.push('There is no closed outline yet, so there is no part to cut out. Add a shape around your lines or text.');
  warn.innerHTML = issues.map(t => `<li>${t}</li>`).join('');
}

/* ---------------- 3D preview ---------------- */
let three = null;
const refresh3d = () => { if (!$('preview3d').hidden) build3d(); };
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
    const size = () => { const r = host.getBoundingClientRect(); if (!r.width) return; renderer.setSize(r.width, r.height, false); camera.aspect = r.width / r.height; camera.updateProjectionMatrix(); };
    new ResizeObserver(size).observe(host); size();
    (function loop() { if (!host.hidden) { controls.update(); renderer.render(scene, camera); } requestAnimationFrame(loop); })();
  }
  const { THREE, group, camera, controls } = three;
  group.children.slice().forEach(c => { group.remove(c); c.geometry?.dispose(); });
  const { pieces, lines } = analyse();
  if (!pieces.length) return;
  const mat = cfg.materials.find(m => m.id === state.material);
  const depth = isPrint() ? state.height : (mat?.thickness || 3);
  const toV = p => new THREE.Vector2(p[0], -p[1]);
  const material = new THREE.MeshStandardMaterial({ color: MAT_COLORS[state.material] || '#ff9a3c', roughness: state.material === 'steel-1' ? .35 : .7, metalness: state.material === 'steel-1' ? .8 : 0, transparent: state.material === 'acrylic-3', opacity: state.material === 'acrylic-3' ? .75 : 1 });
  pieces.forEach(([outer, ...holes]) => {
    const shape = new THREE.Shape(outer.map(toV));
    holes.forEach(h => shape.holes.push(new THREE.Path(h.map(toV))));
    const geom = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 24 });
    group.add(new THREE.Mesh(geom, material));
    group.add(new THREE.LineSegments(new THREE.EdgesGeometry(geom, 25), new THREE.LineBasicMaterial({ color: '#2b2d33' })));
  });
  if (!isPrint()) {
    for (const c of lines) {
      const pts = c.pts.map(p => new THREE.Vector3(p[0], -p[1], depth + 0.05));
      if (c.closed) pts.push(pts[0].clone());
      group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: c.engrave ? '#3b2a1a' : '#111' })));
    }
  }
  const box = new THREE.Box3().setFromObject(group), cc = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2;
  controls.target.copy(cc);
  camera.position.set(cc.x + r * 1.1, cc.y - r * 1.7, cc.z + r * 1.5);
  camera.near = r / 100; camera.far = r * 100; camera.updateProjectionMatrix();
}
function setView(is3d) {
  $('view-2d').setAttribute('aria-pressed', String(!is3d)); $('view-3d').setAttribute('aria-pressed', String(is3d));
  board.hidden = is3d; $('preview3d').hidden = !is3d;
  if (is3d) build3d().catch(() => { status('The 3D preview could not start in this browser.', true); setView(false); });
}
$('view-2d').addEventListener('click', () => setView(false));
$('view-3d').addEventListener('click', () => setView(true));

/* ---------------- toolbar ---------------- */
document.querySelectorAll('[data-add]').forEach(b => b.addEventListener('click', () => {
  if (drawing) { drawing = null; setLineMode(false); }
  state.shapes.push(make(b.dataset.add)); select(state.shapes.length - 1); buildProps(); render(); save(); refresh3d();
  if (b.dataset.add === 'text') $('p-text')?.select();
}));
const tl = $('templates');
for (const name of Object.keys(TEMPLATES)) {
  const b = document.createElement('button'); b.type = 'button'; b.textContent = name;
  b.addEventListener('click', () => { state.shapes = TEMPLATES[name](); select(-1); buildProps(); fit(); render(); save(); refresh3d(); });
  tl.appendChild(b);
}
$('fit').addEventListener('click', () => { fit(); render(); });
$('clear').addEventListener('click', () => { state.shapes = []; select(-1); buildProps(); render(); save(); refresh3d(); });
new ResizeObserver(() => render()).observe(board);

/* ---------------- sending ---------------- */
function status(text, bad = false) { const s = $('status'); s.textContent = text; s.classList.toggle('bad', bad); }
// The server gets the finished outlines (after holes and scissors), plus lines and engraving.
function designPayload() {
  const { solid, lines } = analyse();
  const r2 = v => Math.round(v * 100) / 100;
  const poly = (c, engrave) => ({ type: 'poly', pts: c.pts.map(p => [r2(p[0]), r2(p[1])]), closed: c.closed, engrave });
  return { shapes: [...solid.map(c => poly(c, false)), ...lines.map(c => poly(c, !!c.engrave))] };
}
function designForm() {
  const f = new FormData();
  f.append('design', JSON.stringify(designPayload()));
  f.append('process', machine().line); f.append('material_id', state.material);
  f.append('machine_id', machine().id);
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

// Save the editable drawing (not the flattened outlines) to the customer's account.
let savedDesignId = '';
$('save-design').addEventListener('click', async ev => {
  if (!state.shapes.length) { status('Add a shape first.', true); return; }
  const f = new FormData();
  const { shapes, machine: m, material, height, quantity } = state;
  f.append('design', JSON.stringify({ shapes, machine: m, material, height, quantity }));
  f.append('name', $('design-name').value.trim()); f.append('design_id', savedDesignId);
  ev.target.disabled = true; status('Saving…');
  try {
    const r = await fetch('/account/designs', { method: 'POST', body: f, credentials: 'same-origin' });
    const d = await r.json().catch(() => ({}));
    if (r.status === 401) { status('Sign in to save designs. Your drawing stays here while you do.', true); location.href = d.login || '/account/login?next=/studio'; return; }
    if (!r.ok) throw new Error(d.error || 'Could not save. Please try again.');
    savedDesignId = d.id; $('design-name').value = d.name;
    status(`Saved "${d.name}" to your account.`);
  } catch (e) { status(e.message, true); }
  ev.target.disabled = false;
});

/* ---------------- start ---------------- */
const restored = load();
if (!cfg.machines.some(m => m.id === state.machine)) state.machine = (cfg.machines.find(m => m.line === 'laser') || cfg.machines[0]).id;
if (!restored || !state.shapes.length) state.shapes = TEMPLATES['Name sign']();
$('height').value = state.height; $('quantity').value = state.quantity;
buildMachines(); fillMaterials(); setLineMode(false); fit(); render(); buildProps();
history.push(JSON.stringify(state.shapes)); store(); undoButtons();

// /studio?design=/designs/<slug>/studio.json opens a library design (same-origin only)
const designUrl = new URLSearchParams(location.search).get('design');
if (designUrl && designUrl.startsWith('/') && !designUrl.startsWith('//')) {
  fetch(designUrl, { credentials: 'same-origin' }).then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(d => {
    const kinds = ['rect', 'circle', 'slot', 'polygon', 'path', 'text'];
    const shapes = (Array.isArray(d.shapes) ? d.shapes : []).filter(x => x && kinds.includes(x.type) && isFinite(x.x) && isFinite(x.y)).slice(0, 200);
    if (!shapes.length) throw new Error();
    state.shapes = shapes.map(x => ({ rot: 0, ...x, id: uid++ }));
    if (d.machine && cfg.machines.some(m => m.id === d.machine)) { state.machine = d.machine; buildMachines(); fillMaterials(); }
    if (d.material && [...$('material').options].some(o => o.value === d.material)) { state.material = d.material; $('material').value = d.material; }
    if (isFinite(d.height) && d.height > 0) { state.height = +d.height; $('height').value = d.height; }
    if (Number.isInteger(d.quantity) && d.quantity > 0) { state.quantity = d.quantity; $('quantity').value = d.quantity; }
    if (d.id && typeof d.id === 'string' && designUrl.startsWith('/account/designs/')) { savedDesignId = d.id; $('design-name').value = d.name || ''; }
    select(-1); buildProps(); fit(); render(); save(); refresh3d();
    window.history.replaceState(null, '', location.pathname);
    status(d.name ? `Loaded ${d.name}. Change anything you like, then get a price.` : 'Design loaded.');
  }).catch(() => status('That design could not be opened.', true));
}
