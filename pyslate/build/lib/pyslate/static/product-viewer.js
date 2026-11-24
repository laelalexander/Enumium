// Pyslate product viewer: a full 3D view of one part for the customer.
// World is Z-up and in millimetres, the same as the part files.
import * as THREE from 'three';
import { STLLoader } from './vendor/three/STLLoader.js';
import { OrbitControls } from './vendor/three/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from './vendor/three/CSS2DRenderer.js';

const cfg = JSON.parse(document.getElementById('viewer-config').textContent);
const host = document.getElementById('stage');
const statusEl = document.getElementById('viewer-status');

// ---------- material looks ----------
function appearance(name, line) {
  const n = (name || '').toLowerCase();
  if (n.includes('plywood') || n.includes('wood') || n.includes('bass')) return { color: 0xd9b47c, roughness: 0.8, metalness: 0, label: 'wood' };
  if (n.includes('mdf')) return { color: 0x9b7650, roughness: 0.9, metalness: 0 };
  if (n.includes('acrylic')) return { color: 0xbfe3ff, roughness: 0.08, metalness: 0, transparent: true, opacity: 0.55 };
  if (n.includes('steel') || n.includes('alumin') || n.includes('metal')) return { color: 0xb8bcc2, roughness: 0.32, metalness: 0.9 };
  if (n.includes('petg')) return { color: 0x4f8fd8, roughness: 0.25, metalness: 0, transparent: true, opacity: 0.85 };
  if (n.includes('pla')) return { color: 0x3b82f6, roughness: 0.55, metalness: 0 };
  return line === 'laser' ? { color: 0xd9b47c, roughness: 0.8, metalness: 0 } : { color: 0x3b82f6, roughness: 0.55, metalness: 0 };
}

// ---------- renderer, scene, camera ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.localClippingEnabled = true;
renderer.outputColorSpace = THREE.SRGBColorSpace;
host.appendChild(renderer.domElement);

const labels = new CSS2DRenderer();
labels.domElement.className = 'label-layer';
host.appendChild(labels.domElement);

const scene = new THREE.Scene();
const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
scene.background = new THREE.Color(dark ? 0x15181d : 0xf1f2f0);
scene.add(new THREE.HemisphereLight(0xffffff, dark ? 0x30343a : 0x9aa4b0, 1.6));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(1, -1.5, 2.5);
scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 0.7);
fill.position.set(-2, 1, 1);
scene.add(fill);

const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100000);
camera.up.set(0, 0, 1);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.screenSpacePanning = true;

// ---------- state ----------
const state = { units: 'mm', measuring: false, measurePts: [], section: null, autoRotate: false };
let part = null;       // front mesh
let cutFace = null;    // back faces shown where the section cuts the part
let edges = null;
let dims = null;
let plate = null;
let overhangColors = null;
let size = new THREE.Vector3();
const measureGroup = new THREE.Group();
scene.add(measureGroup);

const clipPlane = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);

function fmt(mm) {
  return state.units === 'mm' ? `${mm.toFixed(1)} mm` : `${(mm / 25.4).toFixed(3)} in`;
}

function label(text, cls = 'dim-label') {
  const el = document.createElement('div');
  el.className = cls;
  el.textContent = text;
  return new CSS2DObject(el);
}

// ---------- load ----------
new STLLoader().load(cfg.model_url, (geometry) => {
  geometry.computeBoundingBox();
  const bb = geometry.boundingBox;
  const c = new THREE.Vector3();
  bb.getCenter(c);
  geometry.translate(-c.x, -c.y, -bb.min.z); // centre on the plate, sitting at Z = 0
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.boundingBox.getSize(size);

  const look = appearance(cfg.material_name, cfg.line);
  const mat = new THREE.MeshStandardMaterial({
    color: look.color, roughness: look.roughness, metalness: look.metalness,
    transparent: !!look.transparent, opacity: look.opacity ?? 1,
    clippingPlanes: [clipPlane], clipShadows: true, side: THREE.FrontSide,
  });
  part = new THREE.Mesh(geometry, mat);
  scene.add(part);

  cutFace = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
    color: 0x64748b, side: THREE.BackSide, clippingPlanes: [clipPlane],
  }));
  cutFace.visible = false;
  scene.add(cutFace);

  edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry, 25),
    new THREE.LineBasicMaterial({ color: dark ? 0x0b0d10 : 0x1f2937, transparent: true, opacity: 0.55, clippingPlanes: [clipPlane] }),
  );
  scene.add(edges);

  buildOverhangColors(geometry);
  buildPlate();
  buildDims();
  setSection(null);
  setView('iso');
  statusEl.hidden = true;
  fillFacts();
}, undefined, () => {
  statusEl.textContent = 'This model could not be shown. Your quote is not affected.';
});

function dropGroup(group) {
  if (!group) return;
  group.traverse((o) => { if (o.element) o.element.remove(); }); // CSS labels live outside the canvas
  scene.remove(group);
}

// ---------- build plate ----------
function buildPlate() {
  dropGroup(plate);
  plate = new THREE.Group();
  const bed = cfg.bed_mm && cfg.bed_mm.length >= 2 ? cfg.bed_mm : null;
  const w = bed ? bed[0] : Math.max(size.x, size.y) * 2;
  const d = bed ? bed[1] : Math.max(size.x, size.y) * 2;
  const step = w > 200 ? 20 : 10;
  const grid = new THREE.GridHelper(Math.max(w, d), Math.round(Math.max(w, d) / step), dark ? 0x3a3f47 : 0xc6cad0, dark ? 0x262a30 : 0xdde0e3);
  grid.rotation.x = Math.PI / 2;
  grid.position.z = -0.01;
  plate.add(grid);
  if (bed) {
    const outline = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.PlaneGeometry(w, d)),
      new THREE.LineBasicMaterial({ color: 0x2563eb }),
    );
    outline.position.z = 0;
    plate.add(outline);
    const tag = label(`${cfg.machine_name} bed ${w} × ${d} mm`, 'plate-label');
    tag.position.set(0, -d / 2, 0);
    plate.add(tag);
  }
  scene.add(plate);
}

// ---------- dimensions ----------
function buildDims() {
  dropGroup(dims);
  dims = new THREE.Group();
  const hx = size.x / 2, hy = size.y / 2, h = size.z;
  const box = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x, size.y, size.z)),
    new THREE.LineDashedMaterial({ color: 0x2563eb, dashSize: 2, gapSize: 1.5, transparent: true, opacity: 0.8 }),
  );
  box.position.set(0, 0, h / 2);
  box.computeLineDistances();
  dims.add(box);
  const lx = label(fmt(size.x)); lx.position.set(0, -hy, 0); dims.add(lx);
  const ly = label(fmt(size.y)); ly.position.set(hx, 0, 0); dims.add(ly);
  const lz = label(fmt(size.z)); lz.position.set(hx, -hy, h / 2); dims.add(lz);
  dims.visible = document.getElementById('t-dims').checked;
  scene.add(dims);
}

// ---------- overhangs (print parts) ----------
function buildOverhangColors(geometry) {
  const pos = geometry.attributes.position;
  const colors = new Float32Array(pos.count * 3);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  const n = new THREE.Vector3(), ab = new THREE.Vector3(), ac = new THREE.Vector3();
  const base = new THREE.Color(appearance(cfg.material_name, cfg.line).color);
  const warn = new THREE.Color(0xf59e0b);
  let flagged = 0;
  for (let i = 0; i < pos.count; i += 3) {
    a.fromBufferAttribute(pos, i); b.fromBufferAttribute(pos, i + 1); c.fromBufferAttribute(pos, i + 2);
    n.crossVectors(ab.subVectors(b, a), ac.subVectors(c, a)).normalize();
    const lowest = Math.min(a.z, b.z, c.z);
    const over = n.z < -0.707 && lowest > 0.3; // facing down more than 45 degrees, not on the plate
    const col = over ? warn : base;
    if (over) flagged++;
    for (let k = 0; k < 3; k++) col.toArray(colors, (i + k) * 3);
  }
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  overhangColors = flagged;
}

function setOverhangs(on) {
  part.material.vertexColors = on;
  if (on) part.material.color.set(0xffffff);
  else part.material.color.set(appearance(cfg.material_name, cfg.line).color);
  part.material.needsUpdate = true;
  const note = document.getElementById('overhang-note');
  note.hidden = !on;
  setView(on && overhangColors ? 'under' : 'iso'); // overhangs face down, so look from below
  note.textContent = overhangColors
    ? 'Orange faces hang over empty space. The shop adds supports there; small marks may remain.'
    : 'No overhangs found. This part prints without supports.';
}

// ---------- section cut ----------
function setSection(axis) {
  state.section = axis;
  const slider = document.getElementById('section-pos');
  slider.disabled = !axis;
  if (!axis || !part) {
    clipPlane.normal.set(0, 0, -1);
    clipPlane.constant = 1e9;
    if (cutFace) cutFace.visible = false;
    return;
  }
  cutFace.visible = true;
  updateSection();
}

function updateSection() {
  if (!state.section) return;
  const t = Number(document.getElementById('section-pos').value) / 100;
  const ax = state.section;
  const half = { x: size.x / 2, y: size.y / 2 };
  const pos = ax === 'z' ? t * size.z : -half[ax] + t * size[ax];
  // Keep the half away from the default camera so the cut face points at the viewer.
  // Three keeps points where normal . p + constant >= 0.
  if (ax === 'y') { clipPlane.normal.set(0, 1, 0); clipPlane.constant = -pos; }
  else if (ax === 'x') { clipPlane.normal.set(-1, 0, 0); clipPlane.constant = pos; }
  else { clipPlane.normal.set(0, 0, -1); clipPlane.constant = pos; }
}

// ---------- views ----------
function setView(name) {
  const r = Math.max(size.x, size.y, size.z, 1);
  const centre = new THREE.Vector3(0, 0, size.z / 2);
  // Fit the part's bounding sphere in the narrower of the two fields of view, so phones see it whole.
  const radius = size.length() / 2 || 1;
  const vfov = THREE.MathUtils.degToRad(camera.fov);
  const hfov = 2 * Math.atan(Math.tan(vfov / 2) * camera.aspect);
  const dist = (radius / Math.sin(Math.min(vfov, hfov) / 2)) * 1.25;
  const dirs = {
    iso: new THREE.Vector3(1, -1.2, 0.9),
    front: new THREE.Vector3(0, -1, 0.0001),
    right: new THREE.Vector3(1, 0, 0.0001),
    top: new THREE.Vector3(0.0001, -0.0001, 1),
    under: new THREE.Vector3(1, -1.4, -0.55),
  };
  const dir = (dirs[name] || dirs.iso).clone().normalize();
  camera.position.copy(centre).addScaledVector(dir, dist);
  camera.near = r / 200;
  camera.far = r * 200;
  camera.updateProjectionMatrix();
  controls.target.copy(centre);
  controls.update();
  document.querySelectorAll('[data-view]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.view === name)));
}

// ---------- measuring ----------
const ray = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let downAt = null;

renderer.domElement.addEventListener('pointerdown', (e) => { downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', (e) => {
  if (!state.measuring || !part || !downAt) return;
  if (Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 4) return; // a drag, not a click
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
  ray.setFromCamera(pointer, camera);
  const hit = ray.intersectObject(part, false)[0];
  if (!hit) return;
  if (state.measurePts.length === 2) clearMeasure();
  state.measurePts.push(hit.point.clone());
  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(Math.max(size.x, size.y, size.z) / 150, 16, 12),
    new THREE.MeshBasicMaterial({ color: 0xe11d48, depthTest: false }),
  );
  dot.renderOrder = 10;
  dot.position.copy(hit.point);
  measureGroup.add(dot);
  if (state.measurePts.length === 2) {
    const [p, q] = state.measurePts;
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([p, q]),
      new THREE.LineBasicMaterial({ color: 0xe11d48, depthTest: false }));
    line.renderOrder = 10;
    measureGroup.add(line);
    const tag = label(fmt(p.distanceTo(q)), 'measure-label');
    tag.position.copy(p.clone().add(q).multiplyScalar(0.5));
    measureGroup.add(tag);
    document.getElementById('measure-out').textContent = `Distance: ${fmt(p.distanceTo(q))}`;
  } else {
    document.getElementById('measure-out').textContent = 'Click a second point.';
  }
});

function clearMeasure() {
  state.measurePts = [];
  measureGroup.children.slice().forEach((o) => {
    measureGroup.remove(o);
    if (o.element) o.element.remove();
  });
  document.getElementById('measure-out').textContent = state.measuring ? 'Click two points on the part.' : '';
}

// ---------- facts panel ----------
function fillFacts() {
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set('f-size', `${fmt(size.x)} × ${fmt(size.y)} × ${fmt(size.z)}`);
  if (cfg.volume_mm3) set('f-volume', state.units === 'mm' ? `${(cfg.volume_mm3 / 1000).toFixed(1)} cm³` : `${(cfg.volume_mm3 / 16387.064).toFixed(2)} in³`);
}

// ---------- toolbar wiring ----------
document.querySelectorAll('[data-view]').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));
document.getElementById('t-dims').addEventListener('change', (e) => { if (dims) dims.visible = e.target.checked; });
document.getElementById('t-edges').addEventListener('change', (e) => { if (edges) edges.visible = e.target.checked; });
document.getElementById('t-wire').addEventListener('change', (e) => { if (part) { part.material.wireframe = e.target.checked; } });
document.getElementById('t-plate').addEventListener('change', (e) => { if (plate) plate.visible = e.target.checked; });
document.getElementById('t-spin').addEventListener('change', (e) => { controls.autoRotate = e.target.checked; });
const overhangToggle = document.getElementById('t-overhang');
if (overhangToggle) overhangToggle.addEventListener('change', (e) => setOverhangs(e.target.checked));
document.getElementById('section-axis').addEventListener('change', (e) => setSection(e.target.value || null));
document.getElementById('section-pos').addEventListener('input', updateSection);
document.getElementById('t-measure').addEventListener('click', (e) => {
  state.measuring = !state.measuring;
  e.currentTarget.setAttribute('aria-pressed', String(state.measuring));
  host.classList.toggle('measuring', state.measuring);
  clearMeasure();
});
document.getElementById('t-units').addEventListener('change', (e) => {
  state.units = e.target.value;
  buildDims();
  fillFacts();
  if (state.measurePts.length === 2) {
    const [p, q] = state.measurePts;
    const tag = measureGroup.children.find((o) => o.element);
    if (tag) tag.element.textContent = fmt(p.distanceTo(q));
    document.getElementById('measure-out').textContent = `Distance: ${fmt(p.distanceTo(q))}`;
  }
});
document.getElementById('t-shot').addEventListener('click', () => {
  const a = document.createElement('a');
  a.download = `${cfg.name.replace(/\.[^.]+$/, '')}-pyslate.png`;
  a.href = renderer.domElement.toDataURL('image/png');
  a.click();
});
document.getElementById('t-full').addEventListener('click', () => {
  const box = document.querySelector('.viewer-shell');
  if (document.fullscreenElement) document.exitFullscreen(); else box.requestFullscreen?.();
});
window.addEventListener('keydown', (e) => {
  if (e.target.closest('input, select, textarea')) return;
  const keys = { '1': 'iso', '2': 'front', '3': 'right', '4': 'top' };
  if (keys[e.key]) setView(keys[e.key]);
  if (e.key === 'f' || e.key === 'F') setView('iso');
  if (e.key === 'Escape' && state.measuring) clearMeasure();
});

// ---------- sizing and render loop ----------
function resize() {
  const w = host.clientWidth, h = host.clientHeight;
  renderer.setSize(w, h);
  labels.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(host);
resize();

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
  labels.render(scene, camera);
});
