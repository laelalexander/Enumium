// Robot arm digital twin: virtual assembly, stepper simulation, hardware link and test table.
// Everything about the arm comes from arm_model.json (python -m arm.twin). Units: mm, degrees. World is Z-up.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { OBJExporter } from 'three/addons/exporters/OBJExporter.js';
import { STLExporter } from 'three/addons/exporters/STLExporter.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const $ = (s) => document.querySelector(s);
const el = (tag, attrs = {}, html = '') => { const e = document.createElement(tag); Object.assign(e, attrs); if (html) e.innerHTML = html; return e; };
const D2R = Math.PI / 180, R2D = 180 / Math.PI, G = 9.81, LB = 0.45359;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

const M = await (await fetch(window.ARM_MODEL_URL || 'arm_model.json')).json();
const J = Object.fromEntries(M.joints.map(j => [j.name, j]));
const JOINTS = ['yaw', 'shoulder', 'elbow', 'wrist'];

// ---------------------------------------------------------------- geometry constants (from arm/hardware.py)
const CHEEK_Y = 34;            // block is 56 wide, cheeks 12 thick
const HUB_Y0 = 42, HUB_Y1 = 52; // clamp hub flange on the output side
const SOCKET_Y = HUB_Y1 + 25;   // tube_socket plate at HUB_Y1, tube axis 25 mm out from the plate
const TUBE_R = M.hw.tube_od / 2;
const PULLEY_Y = -18;           // belt plane, inside the motor-side cheek
const TURNTABLE_H = 12, RISER = 150;
const SHOULDER_Z = TURNTABLE_H + 14 + RISER + 20;  // plate on turntable, riser seated 14 mm deep, top 20 mm inside block
const BOARD_T = 19, TABLE_Z = -BOARD_T - 200;      // 3/4 in board on 200 mm standoffs
const L1 = M.l1_mm, L2 = M.l2_mm, STUB = 120;
const LATERAL = 2 * SOCKET_Y;   // wrist axis sits this far beside the yaw plane (side-by-side link layout)

// ---------------------------------------------------------------- renderer, scene, camera
const vp = $('#viewport');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
vp.appendChild(renderer.domElement);
const labelRenderer = new CSS2DRenderer();
labelRenderer.domElement.style.cssText = 'position:absolute;inset:0;pointer-events:none';
vp.appendChild(labelRenderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x14181e);
scene.fog = new THREE.Fog(0x14181e, 4000, 9000);
const camera = new THREE.PerspectiveCamera(40, 1, 5, 20000);
camera.position.set(1500, -1700, 1100);
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(250, 0, 150);
orbit.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xdde6f0, 0x2a2016, 0.9));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(900, -1200, 2200); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -1600, right: 1600, top: 1600, bottom: -1600, near: 100, far: 6000 });
scene.add(sun);
const fill = new THREE.DirectionalLight(0x9fb8ff, 0.5); fill.position.set(-1500, 1200, 800); scene.add(fill);

function resize() {
  const w = vp.clientWidth, h = vp.clientHeight;
  renderer.setSize(w, h); labelRenderer.setSize(w, h);
  camera.aspect = w / h; camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(vp);

// ---------------------------------------------------------------- materials
const mat = {
  printed: new THREE.MeshStandardMaterial({ color: 0xf08a3c, roughness: 0.6 }),
  printed2: new THREE.MeshStandardMaterial({ color: 0xd9732b, roughness: 0.6 }),
  alu: new THREE.MeshStandardMaterial({ color: 0xc9cdd3, metalness: 0.75, roughness: 0.32 }),
  steel: new THREE.MeshStandardMaterial({ color: 0x8e959e, metalness: 0.85, roughness: 0.28 }),
  dark: new THREE.MeshStandardMaterial({ color: 0x24272c, metalness: 0.4, roughness: 0.5 }),
  motor: new THREE.MeshStandardMaterial({ color: 0x1b1d21, metalness: 0.5, roughness: 0.45 }),
  gear: new THREE.MeshStandardMaterial({ color: 0x5b6169, metalness: 0.8, roughness: 0.35 }),
  belt: new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.9, side: THREE.DoubleSide }),
  wood: new THREE.MeshStandardMaterial({ color: 0xc19a63, roughness: 0.85 }),
  table: new THREE.MeshStandardMaterial({ color: 0x2b3038, roughness: 0.95 }),
  pcb: new THREE.MeshStandardMaterial({ color: 0x1f6fb2, roughness: 0.6 }),
  drv: new THREE.MeshStandardMaterial({ color: 0x15171a, metalness: 0.3, roughness: 0.6 }),
  term: new THREE.MeshStandardMaterial({ color: 0x2fa35a, roughness: 0.6 }),
  psu: new THREE.MeshStandardMaterial({ color: 0xb8bdc4, metalness: 0.6, roughness: 0.4 }),
  red: new THREE.MeshStandardMaterial({ color: 0xd11d23, roughness: 0.5 }),
  yellow: new THREE.MeshStandardMaterial({ color: 0xf2c418, roughness: 0.5 }),
  tpu: new THREE.MeshStandardMaterial({ color: 0x2b2b2b, roughness: 0.95 }),
  payload: new THREE.MeshStandardMaterial({ color: 0x6d7580, metalness: 0.7, roughness: 0.35 }),
  brass: new THREE.MeshStandardMaterial({ color: 0xc8a24a, metalness: 0.8, roughness: 0.3 }),
};
const ledMat = (c) => new THREE.MeshBasicMaterial({ color: c });

// ---------------------------------------------------------------- part catalog + registry
// Every BOM line (printed and purchased) gets a catalog entry; every mesh in the scene is tagged with one.
const catalog = new Map();   // key -> {key,name,cat,qty,note,search,stl,drawing,objs:[]}
function cat(key, info) { if (!catalog.has(key)) catalog.set(key, { key, objs: [], ...info }); return catalog.get(key); }
M.printed.forEach(p => cat(p.id, { name: p.id, cat: 'Printed parts', qty: p.qty, note: p.note, stl: p.stl, drawing: p.drawing, printed: p }));
const PURCHASED_KEYS = [
  ['tube', /round tube/i], ['turntable', /turntable/i], ['shaft', /12 mm hardened/i], ['bearing', /6001/i],
  ['hub', /clamping hub/i], ['collar', /collars/i], ['pulley_s', /16T/i], ['pulley_l', /pulley, 12 mm bore/i],
  ['belt', /belt, 15 mm/i], ['driver', /DM542/i], ['nema17', /NEMA 17/i], ['rod', /8 mm linear/i], ['psu', /power supply/i],
  ['mega', /Arduino/i], ['estop', /E-stop/i], ['limit', /limit switch/i], ['fuse', /Fuse/i], ['screws', /M5 screws/i],
  ['filament', /filament/i], ['board', /Plywood/i],
];
M.purchased.forEach(p => {
  const k = (PURCHASED_KEYS.find(([, re]) => re.test(p.item)) || [p.item])[0];
  const c = /driver|psu|mega|estop|limit|fuse/.test(k) ? 'Electronics' : 'Purchased mechanical';
  cat(k, { name: p.item, cat: c, qty: p.qty, note: p.use, search: p.search });
});
JOINTS.forEach(j => cat('gm_' + j, { name: `${j} gearmotor: ${J[j].search_terms.replace(/ \+ .*$/, '')}`, cat: 'Motors', qty: 1,
  note: `NEMA23 ${J[j].motor_hold_nm} N·m, 20:1 planetary${J[j].belt_ratio > 1 ? ` + ${J[j].belt_ratio}:1 belt` : ''} = ${J[j].total_ratio}:1, rated ${J[j].rated_nm} N·m at output`,
  search: J[j].search_terms }));
cat('harness', { name: 'Wiring harness (24 V, GND, step/dir, motor phases, limit switches)', cat: 'Wiring', qty: null, note: 'Per ELE-001 and docs/WIRING.md' });
cat('payload', { name: `Test payload (${M.payload_lb} lb design load)`, cat: 'Test fixtures', qty: null, note: 'Mass set on the Test tab' });

const pickables = [];
function tag(obj, key, label, counts = true) {
  const c = catalog.get(key); if (!c) { console.warn('no catalog', key); return obj; }
  c.objs.push(obj); if (counts) c.n = (c.n || 0) + 1; obj.userData.part = key; obj.userData.label = label || c.name;
  obj.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.userData.partRoot = obj; pickables.push(o); } });
  obj.userData.home = obj.position.clone();
  return obj;
}
const layers = { 'Printed parts': [], 'Purchased mechanical': [], Motors: [], Electronics: [], Wiring: [], Labels: [], 'Test fixtures': [], Workspace: [] };

// ---------------------------------------------------------------- primitive helpers
function mesh(geo, m, x = 0, y = 0, z = 0) { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); return o; }
const box = (w, d, h, m, x, y, z) => mesh(new THREE.BoxGeometry(w, d, h), m, x, y, z);
function cylY(r, len, m, x = 0, y = 0, z = 0, seg = 32) { return mesh(new THREE.CylinderGeometry(r, r, len, seg), m, x, y, z); }
function cylX(r, len, m, x = 0, y = 0, z = 0) { const o = cylY(r, len, m, x, y, z); o.rotation.z = Math.PI / 2; return o; }
function cylZ(r, len, m, x = 0, y = 0, z = 0) { const o = cylY(r, len, m, x, y, z); o.rotation.x = Math.PI / 2; return o; }
function tubeX(x0, x1, y, z, r = TUBE_R) {
  const g = new THREE.Group();
  const outer = new THREE.CylinderGeometry(r, r, x1 - x0, 40, 1, true);
  const o = mesh(outer, mat.alu); o.rotation.z = Math.PI / 2; o.position.set((x0 + x1) / 2, y, z); g.add(o);
  const inner = mesh(new THREE.CylinderGeometry(r - 1.65, r - 1.65, x1 - x0, 40, 1, true), new THREE.MeshStandardMaterial({ color: 0x777b80, side: THREE.BackSide, metalness: .6, roughness: .5 }));
  inner.rotation.z = Math.PI / 2; inner.position.copy(o.position); g.add(inner);
  return g;
}
function label(obj, text, x = 0, y = 0, z = 0) {
  const d = el('div', { className: 'lbl', textContent: text });
  const l = new CSS2DObject(d); l.position.set(x, y, z); obj.add(l); layers.Labels.push(l); return l;
}

// NEMA23 + planetary gearbox. Output shaft along +Y starting at y=0; body extends to -Y. Returns {group, spinner}.
function gearmotor(frame = 57, motorLen = 76, gearLen = 70, gearR = 30, shaftR = 7) {
  const g = new THREE.Group();
  g.add(box(frame + 3, 10, frame + 3, mat.gear, 0, -5, 0));
  if (gearLen) g.add(cylY(gearR, gearLen, mat.gear, 0, -10 - gearLen / 2, 0));
  const y0 = -10 - gearLen;
  g.add(box(frame, 8, frame, mat.gear, 0, y0 - 4, 0));
  g.add(box(frame - 1, motorLen - 16, frame - 1, mat.motor, 0, y0 - 8 - (motorLen - 16) / 2, 0));
  g.add(box(frame, 8, frame, mat.gear, 0, y0 - motorLen + 4, 0));
  g.add(cylY(shaftR, 26, mat.steel, 0, 13, 0));
  const spinner = new THREE.Group(); spinner.position.y = y0 - motorLen - 1.5;
  spinner.add(cylY(frame * 0.32, 3, mat.dark));
  spinner.add(box(frame * 0.6, 3.4, 6, mat.yellow));
  g.add(spinner);
  const plug = box(16, 10, 12, mat.dark, 0, y0 - motorLen / 2, frame / 2 + 5); g.add(plug);
  g.userData.plug = plug;
  return { group: g, spinner };
}
function pulley(teeth, width = 17, bore = 6) {
  const r = teeth * 5 / (2 * Math.PI);
  const g = new THREE.Group();
  g.add(cylY(r, width, mat.alu, 0, 0, 0, Math.max(24, teeth)));
  g.add(cylY(r + 2.5, 1.5, mat.alu, 0, width / 2 + 0.75, 0, 48));
  g.add(cylY(r + 2.5, 1.5, mat.alu, 0, -width / 2 - 0.75, 0, 48));
  g.add(box(Math.max(4, r * 0.25), width + 3.2, 3, mat.dark, r * 0.6, 0, 0));
  return { group: g, r };
}
// Open belt around two pulleys in the XZ plane (centres (0,0) radius r1 and (cx,0) radius r2), as a ribbon of width w at y.
function belt(r1, cx, r2, y, w = 15) {
  const pts = [];
  for (let i = 0; i < 128; i++) { const a = i / 128 * 2 * Math.PI; pts.push([Math.cos(a) * (r1 + 1.5), Math.sin(a) * (r1 + 1.5)], [cx + Math.cos(a) * (r2 + 1.5), Math.sin(a) * (r2 + 1.5)]); }
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], hi = [];
  for (const p of pts) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (const p of pts.slice().reverse()) { while (hi.length >= 2 && cross(hi[hi.length - 2], hi[hi.length - 1], p) <= 0) hi.pop(); hi.push(p); }
  const hull = lo.slice(0, -1).concat(hi.slice(0, -1));
  const pos = [];
  for (let i = 0; i < hull.length; i++) {
    const a = hull[i], b = hull[(i + 1) % hull.length];
    pos.push(a[0], y - w / 2, a[1], a[0], y + w / 2, a[1], b[0], y + w / 2, b[1], a[0], y - w / 2, a[1], b[0], y + w / 2, b[1], b[0], y - w / 2, b[1]);
  }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.computeVertexNormals();
  return new THREE.Mesh(geo, mat.belt);
}
function limitSwitch() {
  const g = new THREE.Group();
  g.add(box(20, 10, 6.5, mat.dark));
  const lever = box(22, 4, 1, mat.steel, 4, 0, 5); lever.rotation.y = -0.25; g.add(lever);
  const led = mesh(new THREE.SphereGeometry(2.2, 12, 8), ledMat(0x333333), -7, 0, 4.5); g.add(led);
  g.userData.led = led;
  return g;
}
function bearing() { const g = new THREE.Group(); g.add(mesh(new THREE.TorusGeometry(10, 4, 10, 32), mat.steel)); g.children[0].rotation.x = Math.PI / 2; return g; }

// ---------------------------------------------------------------- STL loading
const loader = new STLLoader();
const stlGeo = {};
// stl_encoding "base64" serves each STL as <name>.stl.txt (for hosts that won't serve .stl files).
async function fetchStl(p) {
  try {
    let buf;
    if (M.stl_encoding === 'base64') { const t = await (await fetch(M.stl_base + p.stl + '.txt')).text(); const b = atob(t.trim()); const u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); buf = u.buffer; }
    else { const r = await fetch(M.stl_base + p.stl); if (!r.ok) throw new Error(r.status); buf = await r.arrayBuffer(); }
    const g = loader.parse(buf); g.computeVertexNormals(); stlGeo[p.id] = g;
  } catch (e) { console.warn('missing STL', p.stl, e); }
}
await Promise.all(M.printed.map(fetchStl));
function stl(id, m = mat.printed) {
  const g = stlGeo[id] || new THREE.BoxGeometry(10, 10, 10);
  return new THREE.Mesh(g, m);
}

// ---------------------------------------------------------------- assembly
const world = new THREE.Group(); scene.add(world);
const hw = {};   // handles for animation

// Test table + base board
const table = box(3200, 2200, 20, mat.table, -200, 0, TABLE_Z - 10); table.receiveShadow = true; world.add(table);
const grid = new THREE.GridHelper(3000, 30, 0x3a4350, 0x2c333d); grid.rotation.x = Math.PI / 2; grid.position.set(-200, 0, TABLE_Z + 0.5); world.add(grid);
const board = new THREE.Group();
board.add(box(457, 457, BOARD_T, mat.wood, 0, 0, -BOARD_T / 2));
for (const sx of [-1, 1]) for (const sy of [-1, 1]) board.add(cylZ(14, 200, mat.alu, sx * 200, sy * 200, -BOARD_T - 100));
world.add(tag(board, 'board', 'Base board 18×18 in on standoffs')); layers['Purchased mechanical'].push(board);

// Turntable: lower ring fixed, upper ring turns with yaw
const ttLow = new THREE.Group();
ttLow.add(mesh(new THREE.TorusGeometry(140, 6, 10, 64), mat.steel, 0, 0, 3));
const ring = (r0, r1, h, m, z) => { const s = new THREE.Shape(); s.absarc(0, 0, r1, 0, Math.PI * 2); const hole = new THREE.Path(); hole.absarc(0, 0, r0, 0, Math.PI * 2, true); s.holes.push(hole); const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false, curveSegments: 64 }); return mesh(g, m, 0, 0, z); };
ttLow.add(ring(120, 152, 4, mat.steel, 0));
world.add(tag(ttLow, 'turntable', '12 in turntable bearing')); layers['Purchased mechanical'].push(ttLow);

// Yaw gearmotor under the board, output up
const gmYaw = gearmotor();
gmYaw.group.rotation.x = Math.PI / 2; gmYaw.group.position.set(0, 0, -BOARD_T);
world.add(tag(gmYaw.group, 'gm_yaw', 'Yaw gearmotor J1')); layers.Motors.push(gmYaw.group);
label(gmYaw.group, 'J1 yaw motor', 0, -170, 0);

const yawG = new THREE.Group(); world.add(yawG);
const ttUp = ring(120, 152, 4, mat.steel, TURNTABLE_H - 4); yawG.add(tag(ttUp, 'turntable', 'Turntable upper race', false)); layers['Purchased mechanical'].push(ttUp);
const btp = stl('base_top_plate'); btp.position.z = TURNTABLE_H; yawG.add(tag(btp, 'base_top_plate')); layers['Printed parts'].push(btp);
const yawHub = new THREE.Group(); yawHub.add(cylZ(25, 6, mat.alu, 0, 0, TURNTABLE_H - 3)); yawHub.add(cylZ(12, 12, mat.alu, 0, 0, 2));
yawG.add(tag(yawHub, 'hub', 'Yaw clamp hub')); layers['Purchased mechanical'].push(yawHub);
const riser = new THREE.Group(); const rt = tubeX(0, SHOULDER_Z - 20 - (TURNTABLE_H + 14), 0, 0); rt.rotation.y = -Math.PI / 2; rt.position.z = TURNTABLE_H + 14; riser.add(rt);
yawG.add(tag(riser, 'tube', 'Riser tube ~150 mm')); layers['Purchased mechanical'].push(riser);
const yawLS = limitSwitch(); yawLS.position.set(-60, -175, 3.5); world.add(tag(yawLS, 'limit', 'Yaw limit switch (D22)')); layers.Electronics.push(yawLS);
hw.yaw = { group: yawG, spinner: gmYaw.spinner, ls: yawLS, motor: gmYaw.group };

// One pitch joint (shoulder / elbow / wrist). H is fixed to the incoming link: X_H points back along the
// incoming tube, Y_H is the joint axis (motor side -Y, output side +Y). `out` turns with the joint.
function pitchJoint(name) {
  const j = J[name], C = j.belt_center_mm;
  const H = new THREE.Group(), out = new THREE.Group();
  H.add(out);
  const cm = stl(name + '_cheek_motor'); cm.position.y = -CHEEK_Y; cm.rotation.x = Math.PI; H.add(tag(cm, name + '_cheek_motor'));
  const cp = stl(name + '_cheek_plain'); cp.position.y = CHEEK_Y; H.add(tag(cp, name + '_cheek_plain'));
  const tb = stl(name + '_tube_block', mat.printed2); H.add(tag(tb, name + '_tube_block'));
  layers['Printed parts'].push(cm, cp, tb);
  const gm = gearmotor(); gm.group.position.set(-C, -CHEEK_Y - 6, 0); H.add(tag(gm.group, 'gm_' + name, `${name} gearmotor`)); layers.Motors.push(gm.group);
  const ps = pulley(j.small_teeth); ps.group.position.set(-C, PULLEY_Y, 0); H.add(tag(ps.group, 'pulley_s', `${name} motor pulley ${j.small_teeth}T`));
  const pl = pulley(j.large_teeth); pl.group.position.y = PULLEY_Y; out.add(tag(pl.group, 'pulley_l', `${name} joint pulley ${j.large_teeth}T`));
  const bt = belt(pl.r, -C, ps.r, PULLEY_Y); H.add(tag(bt, 'belt', `${name} belt HTD 5M ~${j.belt_teeth}T`));
  for (const y of [-CHEEK_Y - 2, CHEEK_Y + 2]) { const b = bearing(); b.position.y = y; H.add(tag(b, 'bearing', `${name} 6001-2RS`)); layers['Purchased mechanical'].push(b); }
  const sh = cylY(6, 110, mat.steel, 0, 10, 0); out.add(tag(sh, 'shaft', `${name} 12 mm shaft`));
  for (const y of [-CHEEK_Y - 13, CHEEK_Y - 10]) { const c = cylY(11, 9, mat.dark, 0, y, 0); out.add(tag(c, 'collar', `${name} shaft collar`)); layers['Purchased mechanical'].push(c); }
  const hub = new THREE.Group(); hub.add(cylY(25, 6, mat.alu, 0, HUB_Y1 - 3, 0)); hub.add(cylY(12, HUB_Y1 - HUB_Y0 - 6, mat.alu, 0, HUB_Y0 + (HUB_Y1 - HUB_Y0 - 6) / 2, 0));
  out.add(tag(hub, 'hub', `${name} clamp hub`));
  const so = stl('tube_socket'); so.position.y = HUB_Y1; out.add(tag(so, 'tube_socket', `${name} tube socket`)); layers['Printed parts'].push(so);
  const ls = limitSwitch(); ls.position.set(-25, CHEEK_Y + 2, 53.5); H.add(tag(ls, 'limit', `${name} limit switch (D${j.pins.limit})`)); layers.Electronics.push(ls);
  layers['Purchased mechanical'].push(ps.group, pl.group, bt, sh, hub);
  label(H, `J${j.channel + 1} ${name}`, 0, -CHEEK_Y - 6, 70);
  return { H, out, small: ps.group, spinner: gm.spinner, ls, motor: gm.group, ratioBelt: j.belt_ratio };
}

const S = pitchJoint('shoulder'), E = pitchJoint('elbow'), W = pitchJoint('wrist');
S.H.position.set(0, 0, SHOULDER_Z);
S.H.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(new THREE.Vector3(0, 0, -1), new THREE.Vector3(0, 1, 0), new THREE.Vector3(1, 0, 0)));
yawG.add(S.H);
function addLink(out, len, key, lbl) {
  const t = tubeX(35, len - 20, SOCKET_Y, 0); out.add(tag(t, key, lbl)); layers['Purchased mechanical'].push(t); return t;
}
addLink(S.out, L1, 'tube', `Upper arm tube, cut ${L1 - 55} mm`);
E.H.position.set(L1, SOCKET_Y, 0); E.H.rotation.y = Math.PI; S.out.add(E.H);
addLink(E.out, L2, 'tube', `Forearm tube, cut ${L2 - 55} mm`);
W.H.position.set(L2, SOCKET_Y, 0); W.H.rotation.y = Math.PI; E.out.add(W.H);
const stubT = tubeX(35, 35 + STUB, SOCKET_Y, 0); W.out.add(tag(stubT, 'tube', `Wrist stub tube ~${STUB} mm`)); layers['Purchased mechanical'].push(stubT);
hw.shoulder = S; hw.elbow = E; hw.wrist = W;

// Gripper on the wrist output
const grip = new THREE.Group(); grip.position.set(0, SOCKET_Y, 0); W.out.add(grip);
const ga = stl('gripper_adapter'); ga.position.x = 100; grip.add(tag(ga, 'gripper_adapter')); layers['Printed parts'].push(ga);
const GB = new THREE.Group(); GB.position.set(55, 0, 45); grip.add(GB);
const gb = stl('gripper_body'); GB.add(tag(gb, 'gripper_body')); layers['Printed parts'].push(gb);
const n17 = gearmotor(42, 48, 0, 0, 2.5); n17.group.rotation.z = -Math.PI / 2; n17.group.position.x = 0; GB.add(tag(n17.group, 'nema17', 'Gripper NEMA17 + T8 lead screw')); layers.Motors.push(n17.group);
const lead = cylX(4, 115, mat.brass, 62, 0, 0); GB.add(tag(lead, 'nema17', 'T8 lead screw (part of the NEMA17 kit)', false));
for (const y of [-20, 20]) { const r = cylX(4, 110, mat.steel, 65, y, 0); GB.add(tag(r, 'rod', '8 mm rod + LM8UU')); layers['Purchased mechanical'].push(r); }
const jaw = new THREE.Group(); GB.add(jaw);
const gj = stl('gripper_jaw'); jaw.add(tag(gj, 'gripper_jaw')); layers['Printed parts'].push(gj);
const padM = box(3, 50, 40, mat.tpu, 31.5, 0, 0); jaw.add(padM);
const padF = box(3, 50, 40, mat.tpu, 108.5, 0, 0); GB.add(padF);
const gls = limitSwitch(); gls.position.set(20, 36, 10); gls.rotation.x = Math.PI / 2; GB.add(tag(gls, 'limit', `Gripper limit switch (D${M.gripper.pins.limit})`)); layers.Electronics.push(gls);
const payloadObj = box(1, 1, 1, mat.payload); GB.add(tag(payloadObj, 'payload')); layers['Test fixtures'].push(payloadObj);
const tcp = new THREE.Object3D(); GB.add(tcp);
label(GB, 'J5 gripper', 60, 0, 60);
hw.grip = { jaw, spinner: n17.spinner, ls: gls, motor: n17.group };

// ---------------------------------------------------------------- electronics bench + wiring
const bench = new THREE.Group(); bench.position.set(-880, 0, TABLE_Z); world.add(bench);
const psu = new THREE.Group(); psu.add(box(215, 115, 50, mat.psu, 0, 0, 25)); psu.add(box(30, 100, 14, mat.term, 115, 0, 12));
psu.position.set(0, -380, 0); bench.add(tag(psu, 'psu', '24 V 15 A PSU')); label(psu, '24 V PSU', 0, 0, 70); layers.Electronics.push(psu);
const fuse = cylX(9, 50, mat.dark, 190, -380, 12); bench.add(tag(fuse, 'fuse', '20 A inline fuse')); layers.Electronics.push(fuse);
const estopBox = new THREE.Group(); estopBox.add(box(70, 70, 70, mat.yellow, 0, 0, 35)); estopBox.add(cylZ(20, 18, mat.red, 0, 0, 79)); estopBox.add(cylZ(10, 8, mat.dark, 0, 0, 74));
estopBox.position.set(260, -300, 0); bench.add(tag(estopBox, "estop", "E-stop (NC, cuts 24 V)")); label(estopBox, "E-STOP", 0, 0, 110); layers.Electronics.push(estopBox);
const mega = new THREE.Group(); mega.add(box(101.6, 53.3, 1.6, mat.pcb, 0, 0, 12)); mega.add(box(14, 12, 11, mat.steel, -46, 14, 19)); mega.add(box(60, 5, 9, mat.dark, 10, 23, 17)); mega.add(box(60, 5, 9, mat.dark, 10, -23, 17)); mega.add(box(5, 40, 9, mat.dark, 46, 0, 17));
for (const sx of [-1, 1]) for (const sy of [-1, 1]) mega.add(cylZ(2, 11, mat.brass, sx * 45, sy * 22, 5.5));
mega.position.set(0, -200, 0); bench.add(tag(mega, 'mega', 'Arduino Mega 2560')); label(mega, 'Arduino Mega', 0, 0, 40); layers.Electronics.push(mega);
const megaLed = mesh(new THREE.SphereGeometry(2.5, 10, 8), ledMat(0x333333), 30, 0, 15); mega.add(megaLed);
const drivers = [];
for (let ch = 0; ch < 5; ch++) {
  const d = new THREE.Group(); d.add(box(118, 75, 34, mat.drv, 0, 0, 17)); d.add(box(14, 70, 14, mat.term, 66, 0, 9)); d.add(box(14, 70, 14, mat.term, -66, 0, 9));
  const led = mesh(new THREE.SphereGeometry(3, 10, 8), ledMat(0x333333), 30, 25, 35); d.add(led);
  d.position.set(0, -60 + ch * 95, 0);
  const nm = ch < 4 ? JOINTS[ch] : 'gripper';
  bench.add(tag(d, 'driver', `Driver ${ch} (${ch === 4 ? 'gripper' : nm}) DM542`)); label(d, `DRV${ch} ${nm}`, 0, 0, 48); layers.Electronics.push(d);
  drivers.push({ g: d, led });
}
const tray = new THREE.Group(); tray.position.set(240, 260, 0); bench.add(tray);
tray.add(box(220, 160, 8, mat.dark, 0, 0, 4));
for (const x of [-60, -25]) { const b = bearing(); b.rotation.x = Math.PI / 2; b.position.set(x, -45, 12); tray.add(tag(b, 'bearing', 'Spare 6001-2RS')); }
const screws = box(70, 50, 30, new THREE.MeshStandardMaterial({ color: 0x7a2e2e }), 50, -40, 23); tray.add(tag(screws, 'screws', 'Fastener kit: M5, M3, M4 heat-set inserts'));
const spool = new THREE.Group(); spool.add(cylZ(55, 60, mat.printed, 0, 0, 38)); spool.add(cylZ(100, 4, mat.dark, 0, 0, 10)); spool.add(cylZ(100, 4, mat.dark, 0, 0, 66));
spool.scale.setScalar(0.55); spool.position.set(-40, 40, 0); tray.add(tag(spool, 'filament', 'PETG filament'));
label(tray, 'Spares + consumables', 0, 0, 60);
layers['Purchased mechanical'].push(tray);

// Wires. Static runs on the bench; motor and limit runs are re-routed every frame to the moving parts.
const wires = new THREE.Group(); world.add(wires); layers.Wiring.push(wires); tag(wires, 'harness');
const W_COL = { power: 0xff4a3d, gnd: 0x222222, sig: 0x3d8bff, phase: 0xa45cff, lim: 0x9aa3ad };
function wireLine(color) { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(3 * 40), 3)); const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color })); l.frustumCulled = false; wires.add(l); return l; }
function route(line, a, b, sag = 120) {
  const p = line.geometry.attributes.position, n = p.count;
  const mid = a.clone().add(b).multiplyScalar(0.5); mid.z = Math.min(a.z, b.z) - sag;
  const c = new THREE.QuadraticBezierCurve3(a, mid, b);
  for (let i = 0; i < n; i++) { const v = c.getPoint(i / (n - 1)); p.setXYZ(i, v.x, v.y, v.z); }
  p.needsUpdate = true;
}
const wp = (obj, x = 0, y = 0, z = 0) => obj.localToWorld(new THREE.Vector3(x, y, z));
const staticWires = [];
function staticWire(color, from, to, sag) { const l = wireLine(color); staticWires.push([l, from, to, sag]); }
staticWire(W_COL.power, () => wp(psu, 120, 30, 14), () => wp(fuse, -20, 0, 0), 5);
staticWire(W_COL.power, () => wp(fuse, 25, 0, 0), () => wp(estopBox, -30, 0, 20), 5);
staticWire(W_COL.gnd, () => wp(psu, 120, -30, 14), () => wp(mega, -50, 0, 12), 5);
const motorWires = [], limWires = [];
const motorOf = [hw.yaw.motor, S.motor, E.motor, W.motor, hw.grip.motor];
const lsOf = [hw.yaw.ls, S.ls, E.ls, W.ls, hw.grip.ls];
drivers.forEach((d, ch) => {
  staticWire(W_COL.power, () => wp(estopBox, 30, 0, 20), () => wp(d.g, -66, 20, 16), 8);
  staticWire(W_COL.gnd, () => wp(psu, 110, -40, 14), () => wp(d.g, -66, -20, 16), 8);
  staticWire(W_COL.sig, () => wp(mega, 10, 23, 20), () => wp(d.g, -66, 0, 16), 6);
  motorWires.push(wireLine(W_COL.phase));
  limWires.push(wireLine(W_COL.lim));
});
function updateWires() {
  for (const [l, a, b, s] of staticWires) route(l, a(), b(), s);
  drivers.forEach((d, ch) => {
    const plug = motorOf[ch].userData.plug || motorOf[ch];
    route(motorWires[ch], wp(d.g, 66, 0, 16), wp(plug), 140);
    route(limWires[ch], wp(mega, 46, 0, 18), wp(lsOf[ch]), 160);
  });
}

// Workspace envelope (shoulder-centred reach sphere)
const env = mesh(new THREE.SphereGeometry(L1 + L2 + 165, 48, 24), new THREE.MeshBasicMaterial({ color: 0x4aa3ff, wireframe: true, transparent: true, opacity: 0.08 }), 0, 0, SHOULDER_Z);
env.visible = false; world.add(env); layers.Workspace.push(env);

// IK target gizmo
const target = mesh(new THREE.SphereGeometry(14, 20, 14), new THREE.MeshBasicMaterial({ color: 0xff8a3d, transparent: true, opacity: 0.8 }));
target.visible = false; world.add(target);
const gizmo = new TransformControls(camera, renderer.domElement); gizmo.setSize(0.8); scene.add(gizmo);
gizmo.addEventListener('dragging-changed', e => { orbit.enabled = !e.value; });

// ---------------------------------------------------------------- channels: stepper + firmware emulation
// Channel state mirrors AccelStepper: integer step position, target, max speed (steps/s), accel (steps/s²).
// phys = true mechanical angle (deg) or opening (mm) in the simulated world; pos = the controller's step counter.
const CH = [];
JOINTS.forEach((n, i) => {
  const j = J[n];
  CH.push({ i, name: n, unit: '°', lim: j.limits_deg, homeDeg: j.home_deg, homeDir: j.home_dir, switchAt: j.home_deg,
    ratio: j.total_ratio, ppr: 200 * M.microstep_default, amps: 2.84, motorAmps: j.motor_amps, invert: false,
    maxRate: j.max_dps, accRate: j.max_dps, pos: 0, target: 0, vel: 0, phys: j.home_deg, hwPos: null, homed: false, homing: 0 });
});
CH.push({ i: 4, name: 'gripper', unit: 'mm', lim: M.gripper.open_mm, homeDeg: 0, homeDir: -1, switchAt: 0, lead: M.gripper.lead_mm_per_rev,
  ppr: 200 * M.microstep_default, amps: 1.46, motorAmps: M.gripper.motor_amps, invert: false, maxRate: M.gripper.max_mm_s, accRate: 20,
  pos: 0, target: 0, vel: 0, phys: 0, hwPos: null, homed: false, homing: 0 });
const spu = (c) => c.name === 'gripper' ? c.ppr / c.lead : c.ppr * c.ratio / 360;   // steps per unit (deg or mm)
const sps = (c) => Math.round(c.maxRate * spu(c));
const acc = (c) => Math.round(c.accRate * spu(c));
const toSteps = (c, v) => Math.round((v - c.homeDeg) * spu(c));
const toUnits = (c, s) => c.homeDeg + s / spu(c);
let driversEnabled = false;

const sim = {
  handle(line) {   // same grammar as firmware/arm_controller/arm_controller.ino
    const p = line.trim().split(/\s+/), c = p[0], a = +p[1], b = +p[2], d = +p[3];
    if (c === 'V' && CH[a]) { CH[a].vMax = b; CH[a].aMax = d; return 'OK'; }
    if (c === 'G' && CH[a]) { driversEnabled = true; CH[a].target = b; return 'OK'; }
    if (c === 'H' && CH[a]) { driversEnabled = true; CH[a].homing = b < 0 ? -1 : 1; CH[a].homed = false; return 'OK'; }
    if (c === 'W') return 'OK';
    if (c === 'X') { CH.forEach(ch => { ch.target = Math.round(ch.pos); ch.vel = 0; ch.homing = 0; }); driversEnabled = false; return 'OK'; }
    if (c === 'Z') { CH.forEach(ch => { ch.pos = 0; ch.target = 0; }); return 'OK'; }
    if (c === 'E') { driversEnabled = a !== 0; return 'OK'; }
    if (c === '?') return CH.map(ch => Math.round(ch.pos)).join(' ') + ' \nOK';
    return 'ERR unknown';
  },
  step(dt) {
    for (const c of CH) {
      if (c.vMax == null) { c.vMax = sps(c); c.aMax = acc(c); }
      const sp = spu(c) * (c.invert ? -1 : 1);
      if (!driversEnabled) { c.vel = 0; continue; }
      if (c.homing) {
        const v = 300 * c.homing; c.vel = v;
        const before = c.phys; c.phys += v * dt / sp; c.pos += v * dt;
        const hit = c.homing < 0 ? c.phys <= c.switchAt : c.phys >= c.switchAt;
        if (hit || Math.abs(c.phys - before) < 1e-9 && false) { c.phys = c.switchAt; c.pos = 0; c.target = 0; c.vel = 0; c.homing = 0; c.homed = true; }
        continue;
      }
      const dist = c.target - c.pos;
      const vmax = Math.max(1, c.vMax), amax = Math.max(1, c.aMax);
      const stopDist = c.vel * c.vel / (2 * amax);
      let want = Math.sign(dist) * vmax;
      if (Math.abs(dist) <= stopDist + 0.5 && Math.sign(dist) === Math.sign(c.vel)) want = 0;
      const dv = clamp(want - c.vel, -amax * dt, amax * dt);
      c.vel += dv;
      let mv = c.vel * dt;
      if (Math.abs(mv) >= Math.abs(dist) && Math.sign(mv) === Math.sign(dist)) { mv = dist; c.vel = Math.abs(dist) < 1 ? 0 : c.vel; }
      if (Math.abs(dist) < 0.5 && Math.abs(c.vel) < amax * dt * 2) { c.pos = c.target; c.vel = 0; mv = 0; }
      c.pos += mv; c.phys += mv / sp;
      // mechanical hard stops slightly beyond the soft limits
      const hs0 = c.lim[0] - 5, hs1 = c.lim[1] + 5;
      if (c.phys < hs0 || c.phys > hs1) { c.phys = clamp(c.phys, hs0, hs1); c.stalled = true; } else c.stalled = false;
    }
  },
  idle() { return CH.every(c => !c.homing && Math.round(c.pos) === c.target); },
};

// ---------------------------------------------------------------- hardware link (Web Serial)
const logEl = $('#serialLog');
function log(s, cls = '') { const t = new Date().toLocaleTimeString(); logEl.textContent += `${t} ${s}\n`; logEl.scrollTop = logEl.scrollHeight; }
const link = {
  port: null, writer: null, buf: '', waiters: [], queue: Promise.resolve(), busy: 0, lines: [],
  get on() { return !!this.port; },
  async connect() {
    if (!('serial' in navigator)) { log('Web Serial is not available here. Run python run.py ui on the PC the Arduino is plugged into and open it in Chrome or Edge.'); ui.flash('Hardware link needs Chrome or Edge via python run.py ui'); return; }
    try {
      this.port = await navigator.serial.requestPort({ filters: [] });
      await this.port.open({ baudRate: M.baud });
    } catch (e) { log('connect cancelled: ' + e.message); this.port = null; return; }
    this.writer = this.port.writable.getWriter();
    this.readLoop();
    log('port open, waiting 2 s for the Mega to reset');
    await new Promise(r => setTimeout(r, 2000));
    ui.setLink(true);
    for (const c of CH) await this.cmd(`V ${c.i} ${sps(c)} ${acc(c)}`);
    await this.cmd('?');
  },
  async disconnect() {
    try { this.reader && await this.reader.cancel(); this.writer && this.writer.releaseLock(); await this.port.close(); } catch (e) { }
    this.port = null; ui.setLink(false); log('disconnected');
  },
  async readLoop() {
    const dec = new TextDecoder();
    while (this.port && this.port.readable) {
      this.reader = this.port.readable.getReader();
      try {
        for (;;) {
          const { value, done } = await this.reader.read(); if (done) break;
          this.buf += dec.decode(value);
          let i; while ((i = this.buf.indexOf('\n')) >= 0) { const l = this.buf.slice(0, i).trim(); this.buf = this.buf.slice(i + 1); if (l) this.onLine(l); }
        }
      } catch (e) { log('read error: ' + e.message); } finally { this.reader.releaseLock(); }
      break;
    }
  },
  onLine(l) {
    if (!/^OK|^ERR/.test(l)) { this.lines.push(l); return; }
    const w = this.waiters.shift(); const lines = this.lines; this.lines = [];
    if (w) w({ status: l, lines });
  },
  raw(line) { if (this.writer) this.writer.write(new TextEncoder().encode(line + '\n')); },
  cmd(line, quiet = false) {
    const run = async () => {
      if (!this.port) return null;
      this.busy++;
      const p = new Promise(res => this.waiters.push(res));
      this.raw(line);
      const timeout = /^[HW]/.test(line) ? 120000 : 3000;
      const r = await Promise.race([p, new Promise(res => setTimeout(() => res({ status: 'ERR timeout', lines: [] }), timeout))]);
      if (r.status === 'ERR timeout') { const i = this.waiters.indexOf(p); this.waiters.shift(); }
      this.busy--;
      if (!quiet || r.status !== 'OK') log(`> ${line}  ${r.lines.join(' | ')} ${r.status}`);
      if (line === '?' && r.lines[0]) { const v = r.lines[0].trim().split(/\s+/).map(Number); v.forEach((s, i) => { if (CH[i] && Number.isFinite(s)) CH[i].hwPos = s; }); }
      return r;
    };
    this.queue = this.queue.then(run, run);
    return this.queue;
  },
};
setInterval(() => { if (link.on && !link.busy) link.cmd('?', true); }, 250);

// Single entry point for every command: the simulated firmware always gets it, the Arduino too when connected.
function send(line) {
  const r = sim.handle(line);
  if (!link.on) log(`[sim] > ${line}  ${r.replace('\n', ' ')}`);
  else link.cmd(line, /^G /.test(line));
  return r;
}
function estop() { link.raw('X'); send('X'); ui.flash('STOP sent. Drivers disabled: an unbraked arm will drop.'); }

// ---------------------------------------------------------------- kinematics (matches arm/kinematics.py, plus the link side-offset)
function ik(x, y, z, pitch = 0, useOffset = true) {
  const d = useOffset ? LATERAL : 0, rho2 = x * x + y * y;
  if (rho2 < d * d) throw new Error('target inside the side-offset cylinder');
  const r = Math.sqrt(rho2 - d * d);
  const yaw = Math.atan2(y, x) - Math.atan2(d, r);
  const zz = z - SHOULDER_Z, d2 = r * r + zz * zz;
  const c = (d2 - L1 * L1 - L2 * L2) / (2 * L1 * L2);
  if (Math.abs(c) > 1) throw new Error(`unreachable (|cos| = ${Math.abs(c).toFixed(2)})`);
  const el = -Math.acos(c);
  const sh = Math.atan2(zz, r) - Math.atan2(L2 * Math.sin(el), L1 + L2 * Math.cos(el));
  const wr = pitch * D2R - sh - el;
  return [yaw * R2D, sh * R2D, el * R2D, wr * R2D];
}
function fkPlanar(a) {   // shoulder-plane positions in metres
  const s = a.shoulder * D2R, e = a.elbow * D2R, w = a.wrist * D2R;
  const E_ = [L1 * Math.cos(s), L1 * Math.sin(s)], W_ = [E_[0] + L2 * Math.cos(s + e), E_[1] + L2 * Math.sin(s + e)];
  const dir = [Math.cos(s + e + w), Math.sin(s + e + w)];
  return { s, e, w, E: E_.map(v => v / 1000), W: W_.map(v => v / 1000), dir };
}

// ---------------------------------------------------------------- per-frame pose
const shown = { yaw: 0, shoulder: 0, elbow: 0, wrist: 0, gripper: 0 };
let feedback = 'hw';
function physical(c) {   // value to draw for a channel
  if (link.on && feedback === 'hw' && c.hwPos != null) return toUnits(c, c.hwPos * (c.invert ? -1 : 1));
  return c.phys;
}
function applyPose() {
  CH.forEach(c => { const v = physical(c); shown[c.name] += (v - shown[c.name]) * (link.on ? 0.35 : 1); });
  yawG.rotation.z = shown.yaw * D2R;
  S.out.rotation.y = -Math.PI / 2 - shown.shoulder * D2R;
  E.out.rotation.y = -Math.PI - shown.elbow * D2R;
  W.out.rotation.y = -Math.PI - shown.wrist * D2R;
  // motor shafts: joint angle × total reduction; small pulley: joint angle × belt ratio
  hw.yaw.spinner.rotation.y = shown.yaw * D2R * J.yaw.total_ratio;
  for (const [n, h] of [['shoulder', S], ['elbow', E], ['wrist', W]]) {
    h.small.rotation.y = -shown[n] * D2R * h.ratioBelt;
    h.spinner.rotation.y = shown[n] * D2R * J[n].total_ratio;
  }
  const w = clamp(shown.gripper, 0, 70);
  jaw.position.x = 80 - w;
  hw.grip.spinner.rotation.y = w / CH[4].lead * 2 * Math.PI;
  const kg = payloadKg();
  payloadObj.visible = kg > 0 && layerOn['Test fixtures'];
  if (kg > 0) { const side = Math.cbrt(kg / 7.85e-6); const wdt = Math.min(side, Math.max(w - 2, 10)); payloadObj.scale.set(wdt, side * Math.sqrt(side / wdt), side * Math.sqrt(side / wdt)); payloadObj.position.set(108 - w / 2 - 1, 0, 0); }
  tcp.position.set(108 - w / 2, 0, 0);
  CH.forEach((c, i) => {
    const trip = Math.abs(physical(c) - c.switchAt) < 0.6 || (c.homeDir < 0 ? physical(c) < c.switchAt : physical(c) > c.switchAt);
    lsOf[i].userData.led.material.color.setHex(trip ? 0xff3b30 : 0x2f3a2f);
    c.tripped = trip;
    const moving = Math.abs(c.vel) > 1 || c.homing;
    drivers[i].led.material.color.setHex(!driversEnabled ? 0x553333 : c.stalled ? 0xff3b30 : moving ? 0x3d8bff : 0x3ccf7a);
  });
  megaLed.material.color.setHex(link.on ? 0x3ccf7a : 0xffb020);
}

// ---------------------------------------------------------------- explode + layers
const layerOn = {};
Object.keys(layers).forEach(k => layerOn[k] = !['Workspace'].includes(k));
function setLayer(k, on) { layerOn[k] = on; layers[k].forEach(o => { o.visible = on; if (o.element) o.element.style.display = on ? '' : 'none'; }); }
function explode(f) {
  for (const c of catalog.values()) for (const o of c.objs) {
    if (!o.userData.home || o.parent === world || o.parent === bench || o === wires) continue;
    const h = o.userData.home, len = h.length();
    if (len < 1) { o.position.copy(h); continue; }
    o.position.copy(h).addScaledVector(h.clone().normalize(), f * 180);
  }
}

// ---------------------------------------------------------------- picking
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
let selected = null; const selMat = new Map();
function select(key) {
  if (selected) for (const o of catalog.get(selected).objs) o.traverse(m => { if (m.isMesh && selMat.has(m)) { m.material = selMat.get(m); } });
  selMat.clear(); selected = key;
  document.querySelectorAll('#partList .pi').forEach(e => e.classList.toggle('sel', e.dataset.key === key));
  const card = $('#pickCard');
  if (!key) { card.hidden = true; return; }
  const c = catalog.get(key);
  for (const o of c.objs) o.traverse(m => { if (m.isMesh) { selMat.set(m, m.material); m.material = m.material.clone(); m.material.emissive = new THREE.Color(0x4aa3ff); m.material.emissiveIntensity = 0.55; } });
  card.innerHTML = `<h4>${c.name}</h4><div class="muted">${c.cat}${c.qty != null ? ` · BOM qty ${c.qty} · in model ${c.n || 0}` : ''}</div>
    <p>${c.note || ''}</p>${c.search ? `<div class="muted small">Search: ${c.search}</div>` : ''}
    <div class="row"><button class="btn small" id="pcOpen">Open drawing and files</button><button class="btn small ghost" id="pcFocus">Focus</button><button class="btn small ghost" id="pcClose">Close</button></div>`;
  card.hidden = false;
  $('#pcOpen').onclick = () => inspector.open(key);
  $('#pcClose').onclick = () => select(null);
  $('#pcFocus').onclick = () => { const b = new THREE.Box3(); c.objs.forEach(o => b.expandByObject(o)); const ctr = b.getCenter(new THREE.Vector3()); orbit.target.copy(ctr); camera.position.copy(ctr).add(new THREE.Vector3(500, -600, 400)); };
}
renderer.domElement.addEventListener('dblclick', () => { if (selected) inspector.open(selected); });

// ---------------------------------------------------------------- part inspector: drawing, 3D, CAD source, print, files
const HOSTED = !!M.hosted;   // published preview: the viewer blocks downloads, so files open as text instead
function cloneBare(src) {  // Object3D.clone JSON-copies userData, which holds back-references here
  const saved = []; src.traverse(n => { saved.push([n, n.userData]); n.userData = {}; });
  try { return src.clone(true); } finally { for (const [n, u] of saved) n.userData = u; }
}
const inspector = (() => {
  const root = $('#inspector'), body = $('#insBody');
  const r2 = new THREE.WebGLRenderer({ antialias: true }); r2.setPixelRatio(Math.min(devicePixelRatio, 2));
  const sc2 = new THREE.Scene(); sc2.background = new THREE.Color(0x1a1f26);
  sc2.add(new THREE.HemisphereLight(0xffffff, 0x333333, 1.1)); const dl = new THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(300, -400, 600); sc2.add(dl);
  const cam2 = new THREE.PerspectiveCamera(35, 1, 1, 20000), orb2 = new OrbitControls(cam2, r2.domElement); orb2.enableDamping = true;
  let holder = null, running = false, cur = null, tab = 'drawing';
  const sheetFor = (c) => c.cat === 'Electronics' || c.cat === 'Wiring' ? 'ELE-001_wiring' : /pulley|belt|bearing|shaft|collar|hub/.test(c.key) || /^gm_(shoulder|elbow|wrist)/.test(c.key) ? 'ASM-002_joint_section' : 'ASM-001_assembly';
  function partObject(c) {
    if (c.printed) return new THREE.Mesh(stlGeo[c.key], mat.printed);
    const o = cloneBare(c.objs[0]); o.position.set(0, 0, 0); o.rotation.set(0, 0, 0); o.scale.setScalar(1);
    o.traverse(m => { if (m.isMesh && selMat.has(c.objs[0]) === false && m.material.emissive) { m.material = m.material.clone(); m.material.emissive.setHex(0); } });
    return o;
  }
  function show3d(c) {
    if (holder) sc2.remove(holder);
    holder = new THREE.Group(); const o = partObject(c); holder.add(o); sc2.add(holder);
    const b = new THREE.Box3().setFromObject(holder), size = b.getSize(new THREE.Vector3()), ctr = b.getCenter(new THREE.Vector3());
    holder.position.sub(ctr);
    const g = new THREE.GridHelper(Math.max(size.x, size.y) * 2, 10, 0x3a4350, 0x2c333d); g.rotation.x = Math.PI / 2; g.position.z = -size.z / 2; holder.add(new THREE.BoxHelper(o, 0x4aa3ff)); sc2.add(g); holder.userData.grid = g;
    const r = size.length(); cam2.position.set(r * 0.9, -r * 1.1, r * 0.8); orb2.target.set(0, 0, 0);
    return size;
  }
  function loop() { if (!running) return; orb2.update(); r2.render(sc2, cam2); requestAnimationFrame(loop); }
  async function fileAction(url, name, act) {
    try {
      if (act === 'download' && !HOSTED) { const b = await (await fetch(url)).blob(); const a = el('a', { href: URL.createObjectURL(b), download: name }); a.click(); return; }
      const t = await (await fetch(url)).text();
      const lines = t.split('\n'); body.querySelector('#insView').innerHTML = `<div class="small muted">${name} · ${lines.length.toLocaleString()} lines${lines.length > 400 ? ' (first 400 shown)' : ''} <button class="btn small" id="insCopy">Copy all</button></div><pre class="code">${escapeHtml(lines.slice(0, 400).join('\n'))}</pre>`;
      body.querySelector('#insCopy').onclick = async (e) => { try { await navigator.clipboard.writeText(t); e.target.textContent = 'Copied'; } catch { e.target.textContent = 'Copy blocked here'; } };
    } catch (e) { ui.flash('Could not load ' + name); }
  }
  function exportModel(c, kind) {
    const o = partObject(c); const ex = kind === 'obj' ? new OBJExporter() : new STLExporter();
    const data = kind === 'obj' ? ex.parse(o) : ex.parse(o, { binary: false });
    if (HOSTED) { body.querySelector('#insView').innerHTML = `<div class="small muted">${c.key}.${kind} (generated from the model) <button class="btn small" id="insCopy">Copy all</button></div><pre class="code">${escapeHtml(data.split('\n').slice(0, 300).join('\n'))}</pre>`; body.querySelector('#insCopy').onclick = () => navigator.clipboard.writeText(data).catch(() => {}); return; }
    const a = el('a', { href: URL.createObjectURL(new Blob([data])), download: `${c.key}.${kind}` }); a.click();
  }
  function render() {
    const c = cur, p = c.printed;
    document.querySelectorAll('#insTabs button').forEach(b => b.classList.toggle('on', b.dataset.t === tab));
    running = tab === '3d';
    if (tab === 'drawing') {
      const sheet = p ? M.drawing_base + p.drawing : M.sheet_base + sheetFor(c) + '.svg';
      body.innerHTML = `${p ? '' : `<p class="muted small">Purchased part: no part drawing. Shown on assembly sheet ${sheetFor(c).replace('_', ' ')}.</p>`}
        <div class="dwg" id="dwg"><img src="${sheet}" alt="Drawing of ${c.key}" draggable="false"></div>
        <div class="small muted">Scroll to zoom, drag to pan, double-click to reset.</div>`;
      const box = body.querySelector('#dwg'), im = box.querySelector('img'); let z = 1, x = 0, y = 0, drag = null;
      const ap = () => im.style.transform = `translate(${x}px,${y}px) scale(${z})`;
      box.onwheel = (e) => { e.preventDefault(); const r = box.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top, k = e.deltaY < 0 ? 1.2 : 1 / 1.2, nz = clamp(z * k, 1, 12); x = mx - (mx - x) * nz / z; y = my - (my - y) * nz / z; z = nz; ap(); };
      box.onpointerdown = (e) => { drag = [e.clientX - x, e.clientY - y]; box.setPointerCapture(e.pointerId); };
      box.onpointermove = (e) => { if (drag) { x = e.clientX - drag[0]; y = e.clientY - drag[1]; ap(); } };
      box.onpointerup = () => drag = null; box.ondblclick = () => { z = 1; x = y = 0; ap(); };
    } else if (tab === '3d') {
      body.innerHTML = '<div id="ins3d"></div><div id="insDims" class="small"></div>';
      const host = body.querySelector('#ins3d'); host.append(r2.domElement);
      const w = host.clientWidth, h = host.clientHeight; r2.setSize(w, h); cam2.aspect = w / h; cam2.updateProjectionMatrix();
      if (holder?.userData.grid) sc2.remove(holder.userData.grid);
      const size = show3d(c);
      body.querySelector('#insDims').textContent = `Bounding box ${size.x.toFixed(1)} × ${size.y.toFixed(1)} × ${size.z.toFixed(1)} mm (design orientation). Drag to orbit.`;
      loop();
    } else if (tab === 'cad') {
      body.innerHTML = p ? `<p class="small muted">CadQuery source from <code>arm/hardware.py</code> (rev A). Edit <code>HW</code> there and run <code>python run.py build</code>; this part, its drawing and its STEP/STL/OBJ regenerate.</p><pre class="code">${escapeHtml(p.code)}</pre>`
        : `<p class="small">Purchased part, not modelled in CAD. The 3D tab shows the stand-in model used for fit and clearance in the test table.</p>
           <table><tr><th>BOM item</th><td>${c.name}</td></tr><tr><th>Search / spec</th><td>${c.search || '-'}</td></tr><tr><th>Used for</th><td>${c.note || '-'}</td></tr><tr><th>Qty</th><td>${c.qty ?? '-'}</td></tr></table>`;
    } else if (tab === 'print') {
      const pr = p?.print;
      body.innerHTML = !p ? '<p class="small">Not printed: this is a purchased part. See the procurement list.</p>' : !pr ? '<p class="small">No print data yet: run <code>python run.py print</code>.</p>' :
        `<table><tr><th>Plate</th><td>${pr.plates.map(n => `plate_${n}.3mf (${pr.plate_check?.[n] || ''})`).join(', ')}</td></tr>
          <tr><th>Copies</th><td>${pr.qty}</td></tr><tr><th>Size on bed</th><td>${pr.size.join(' × ')} mm</td></tr>
          <tr><th>Orientation</th><td>${pr.why}</td></tr><tr><th>Supports</th><td>${pr.supports ? 'yes, build plate only' : 'no'}</td></tr>
          <tr><th>Brim</th><td>${pr.brim ? '5 mm' : 'no'}</td></tr><tr><th>Solid volume</th><td>${pr.volume_cm3} cm³ (≤ ${(pr.volume_cm3 * 1.27).toFixed(0)} g PETG if printed solid)</td></tr>
          <tr><th>Settings</th><td>PETG, 0.4 mm nozzle, 0.2 mm layers, 5 perimeters, 40 % gyroid</td></tr></table>`;
    } else if (tab === 'files') {
      const rows = p ? [
        ['Drawing (SVG, A3)', M.drawing_base + p.drawing, p.drawing], ['STEP (CAD solid)', M.step_base + p.step + (M.text_suffix || ''), p.step],
        ['STL (mesh, design orientation)', M.stl_base + p.stl + (M.stl_encoding === 'base64' ? '.txt' : ''), p.stl, M.stl_encoding === 'base64'],
        ['OBJ (mesh)', M.obj_base + p.obj + (M.text_suffix || ''), p.obj], ...(p.print && M.print_base ? [['STL, print orientation', M.print_base + p.print.print_stl, p.id + '_print.stl', HOSTED]] : []),
        ...(p.print && M.print_base && !HOSTED ? p.print.plates.map(n => [`Bambu plate ${n} (3MF)`, `${M.print_base}plates/plate_${n}.3mf`, `plate_${n}.3mf`, true]) : []),
      ] : [];
      body.innerHTML = `<p class="small muted">${HOSTED ? 'This preview can show files but not download them. Run <code>python run.py ui</code> on your PC to download, or use the build package.' : 'Files come from <code>3d-workflow/design/</code> and <code>print/</code>.'}</p>
        <table>${rows.map(([lbl, url, name, binary], i) => `<tr><td>${lbl}</td><td class="mono">${name}</td><td>${HOSTED ? '' : `<button class="btn small" data-i="${i}" data-a="download">Download</button>`} ${binary ? '' : `<button class="btn small ghost" data-i="${i}" data-a="view">View</button>`}</td></tr>`).join('')}
        ${p ? '' : `<tr><td>Stand-in model</td><td class="mono">${c.key}.obj / .stl</td><td><button class="btn small" data-x="obj">OBJ</button> <button class="btn small" data-x="stl">STL</button></td></tr>`}</table>
        <div id="insView"></div>`;
      body.querySelectorAll('[data-i]').forEach(b => b.onclick = () => { const [, url, name] = rows[+b.dataset.i]; fileAction(url, name, b.dataset.a); });
      body.querySelectorAll('[data-x]').forEach(b => b.onclick = () => exportModel(c, b.dataset.x));
    }
  }
  $('#insClose').onclick = () => { root.hidden = true; running = false; };
  document.querySelectorAll('#insTabs button').forEach(b => b.onclick = () => { tab = b.dataset.t; render(); });
  addEventListener('keydown', e => { if (e.key === 'Escape' && !root.hidden) $('#insClose').click(); });
  return {
    open(key) {
      cur = catalog.get(key); if (!cur) return;
      $('#insTitle').textContent = cur.name;
      $('#insMeta').textContent = `${cur.cat}${cur.qty != null ? ` · qty ${cur.qty}` : ''}${cur.note ? ' · ' + cur.note : ''}`;
      root.hidden = false; render();
    },
  };
})();
function escapeHtml(t) { return t.replace(/[&<>]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[ch])); }
let downAt = null;
renderer.domElement.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 4 || gizmo.dragging) return;
  const r = renderer.domElement.getBoundingClientRect();
  mouse.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(pickables.filter(m => m.visible), false).find(h => { let o = h.object; while (o) { if (!o.visible) return false; o = o.parent; } return true; });
  select(hit ? hit.object.userData.partRoot.userData.part : null);
});

// ---------------------------------------------------------------- loads + checks
function payloadKg() { return (+$('#payload').value) * LB; }
function torques() {
  const a = { shoulder: shown.shoulder, elbow: shown.elbow, wrist: shown.wrist };
  const f = fkPlanar(a), m = M.mass, l1 = L1 / 1000, l2 = L2 / 1000;
  const m1 = m.tube_kg_per_m * l1 + m.joint_hw_kg, m2 = m.tube_kg_per_m * l2 + m.joint_hw_kg;
  const me = J.elbow.mass_kg, mw = J.wrist.mass_kg, mg = m.gripper_kg, mp = payloadKg();
  const G_ = [f.W[0] + 0.07 * f.dir[0]], P_ = [f.W[0] + m.payload_arm_m * f.dir[0]];
  const c1 = [l1 / 2 * Math.cos(f.s)], c2 = [f.E[0] + l2 / 2 * Math.cos(f.s + f.e)];
  const sh = G * (m1 * c1[0] + me * f.E[0] + m2 * c2[0] + mw * f.W[0] + mg * G_[0] + mp * P_[0]);
  const el = G * (m2 * (c2[0] - f.E[0]) + mw * (f.W[0] - f.E[0]) + mg * (G_[0] - f.E[0]) + mp * (P_[0] - f.E[0]));
  const wr = G * (mg * (G_[0] - f.W[0]) + mp * (P_[0] - f.W[0]));
  return { shoulder: sh, elbow: el, wrist: wr };
}
const available = (n) => { const j = J[n], c = CH[j.channel]; return j.rated_nm * Math.min(1, c.amps / j.motor_amps); };
function checks() {
  const out = [];
  const pts = { elbow: wp(E.H), wrist: wp(W.H), tool: wp(tcp), jaw: wp(jaw, 15, 0, -28) };
  for (const [k, p] of Object.entries(pts)) if (p.z < 5) out.push(['b', `${k} below the board top (z ${p.z.toFixed(0)} mm)`]);
  const reach = Math.hypot(pts.tool.x, pts.tool.y);
  if (reach > M.max_extension_mm) out.push(['b', `reach ${reach.toFixed(0)} mm exceeds the 48 in limit`]);
  CH.forEach(c => { const v = physical(c); if (v < c.lim[0] - 0.01 || v > c.lim[1] + 0.01) out.push(['b', `${c.name} ${v.toFixed(1)}${c.unit} outside soft limits`]); if (c.stalled) out.push(['b', `${c.name} at hard stop`]); });
  const t = torques();
  for (const n of ['shoulder', 'elbow', 'wrist']) { const m = available(n) / Math.max(1e-6, Math.abs(t[n])); if (m < 1) out.push(['b', `${n} cannot hold this load (${m.toFixed(2)}×)`]); else if (m < M.safety) out.push(['w', `${n} margin ${m.toFixed(2)}× below ${M.safety}×`]); }
  const rate = CH.reduce((s, c) => s + Math.abs(c.vel), 0);
  if (rate > M.mega_combined_sps) out.push(['w', `combined step rate ${rate.toFixed(0)}/s exceeds the Mega's ~${M.mega_combined_sps}/s`]);
  if (!CH.every(c => c.homed)) out.push(['w', 'not homed: positions are relative to power-up']);
  return { out, pts, reach, t, rate };
}

// ---------------------------------------------------------------- UI
const ui = {};
const sliders = {};
function buildJointSliders() {
  const host = $('#jointSliders');
  CH.forEach(c => {
    const row = el('div', { className: 'joint' });
    const nm = el('div', { className: 'nm', textContent: c.name });
    const r = el('input', { type: 'range', min: c.lim[0], max: c.lim[1], step: c.name === 'gripper' ? 0.5 : 0.25, value: 0 });
    const v = el('div', { className: 'val' });
    row.append(nm, r, v); host.append(row);
    sliders[c.name] = { r, v, c };
    r.addEventListener('input', () => { if ($('#chkLive').checked) moveTo({ [c.name]: +r.value }); else v.firstChild && (v.firstChild.textContent = (+r.value).toFixed(1)); });
  });
}
const targetUnits = () => Object.fromEntries(CH.map(c => [c.name, toUnits(c, c.target)]));
function moveTo(vals, { sendIt = true } = {}) {
  for (const [n, v] of Object.entries(vals)) {
    const c = CH.find(x => x.name === n), cl = clamp(v, c.lim[0], c.lim[1]);
    const s = toSteps(c, cl) * (c.invert ? -1 : 1);
    if (s !== c.target && sendIt) send(`G ${c.i} ${s}`);
    sliders[n].r.value = cl;
  }
}
function updateSliderText() {
  for (const { r, v, c } of Object.values(sliders)) v.innerHTML = `${(+r.value).toFixed(1)}<span class="act"> / ${physical(c).toFixed(1)}</span>`;
}
function syncSlidersToTargets() { for (const { r, c } of Object.values(sliders)) r.value = toUnits(c, c.target * (c.invert ? -1 : 1)); }
$('#btnSendJoints').onclick = () => moveTo(Object.fromEntries(Object.values(sliders).map(s => [s.c.name, +s.r.value])));

function doIK(x, y, z, p, quiet) {
  try {
    const [yaw, sh, el, wr] = ik(x, y, z, p, $('#chkOffset').checked);
    const a = { yaw, shoulder: sh, elbow: el, wrist: wr };
    for (const [n, v] of Object.entries(a)) { const c = CH.find(q => q.name === n); if (v < c.lim[0] || v > c.lim[1]) throw new Error(`${n} ${v.toFixed(1)}° outside [${c.lim}]`); }
    moveTo(a); return a;
  } catch (e) { if (!quiet) ui.flash('IK: ' + e.message); return null; }
}
$('#btnIK').onclick = () => doIK(+$('#ikX').value, +$('#ikY').value, +$('#ikZ').value, +$('#ikP').value);
$('#chkGizmo').onchange = (e) => {
  target.visible = e.target.checked;
  if (e.target.checked) { target.position.copy(wp(W.H)); gizmo.attach(target); } else gizmo.detach();
};
gizmo.addEventListener('objectChange', () => {
  const p = target.position; doIK(p.x, p.y, p.z, +$('#ikP').value, true);
  $('#ikX').value = p.x.toFixed(0); $('#ikY').value = p.y.toFixed(0); $('#ikZ').value = p.z.toFixed(0);
});

const PRESETS = {
  Ready: { yaw: 0, shoulder: 35, elbow: -70, wrist: 35, gripper: 40 },
  Zero: { yaw: 0, shoulder: 0, elbow: 0, wrist: 0, gripper: 20 },
  Reach: { yaw: 0, shoulder: 0, elbow: 0, wrist: 0, gripper: 0 },
  Tall: { yaw: 0, shoulder: 90, elbow: 0, wrist: 0, gripper: 30 },
  'Pick left': { yaw: 60, shoulder: 50, elbow: -100, wrist: -10, gripper: 50 },
  'Pick right': { yaw: -60, shoulder: 50, elbow: -100, wrist: -10, gripper: 50 },
  Park: { yaw: 0, shoulder: 80, elbow: -135, wrist: 50, gripper: 0 },
};
for (const [k, v] of Object.entries(PRESETS)) { const b = el('button', { className: 'btn small', textContent: k }); b.onclick = () => moveTo(v); $('#presets').append(b); }

// Teach and play
const seq = [];
function renderSeq(cur = -1) { $('#seqList').innerHTML = seq.map((p, i) => `<li class="${i === cur ? 'cur' : ''}">${CH.map(c => `${c.name[0].toUpperCase()}${p[c.name].toFixed(1)}`).join(' ')}</li>`).join(''); }
$('#btnTeach').onclick = () => { seq.push(targetUnits()); renderSeq(); };
$('#btnClearSeq').onclick = () => { seq.length = 0; renderSeq(); };
const settled = () => sim.idle() && (!link.on || feedback !== 'hw' || CH.every(c => c.hwPos == null || Math.abs(c.hwPos - c.target) < 2));
const waitSettled = (ms = 60000) => new Promise(res => { const t0 = performance.now(); const f = () => (settled() || performance.now() - t0 > ms) ? res() : setTimeout(f, 60); setTimeout(f, 120); });
let playing = false;
$('#btnPlay').onclick = async () => {
  if (playing) { playing = false; $('#btnPlay').textContent = 'Play'; return; }
  if (!seq.length) return ui.flash('Record some poses first');
  playing = true; $('#btnPlay').textContent = 'Pause';
  do { for (let i = 0; i < seq.length && playing; i++) { renderSeq(i); moveTo(seq[i]); await waitSettled(); await new Promise(r => setTimeout(r, 250)); } } while (playing && $('#chkLoop').checked);
  playing = false; $('#btnPlay').textContent = 'Play'; renderSeq();
};

// Header buttons
$('#btnStop').onclick = estop;
$('#btnEnable').onclick = () => { send(`E ${driversEnabled ? 0 : 1}`); };
$('#btnHome').onclick = homeAll;
async function homeAll() {
  ui.flash('Homing: each joint drives to its limit switch in turn');
  for (const c of CH) { send(`H ${c.i} ${c.homeDir}`); await waitSettled(120000); }
  syncSlidersToTargets();
  moveTo(PRESETS.Ready);
}

// Motors tab
function buildMotorCards() {
  const host = $('#motorCards');
  CH.forEach(c => {
    const j = J[c.name], card = el('div', { className: 'mcard' });
    const ratioTxt = c.name === 'gripper' ? `NEMA17 · T8 lead ${c.lead} mm/rev` : `NEMA23 · 20:1 planetary${j.belt_ratio > 1 ? ` × ${j.belt_ratio}:1 belt (${j.small_teeth}T/${j.large_teeth}T, ${j.belt_center_mm} mm)` : ''} = ${c.ratio}:1`;
    card.innerHTML = `<header><b>CH${c.i} · ${c.name}</b><span><span class="led" data-led></span><span class="small muted">DRV${c.i}</span></span></header>
      <div class="small muted">${ratioTxt}</div>
      <div class="kv">
        <label>Pulses/rev (DIP)<select data-k="ppr">${M.pulses_per_rev_options.map(o => `<option ${o === c.ppr ? 'selected' : ''}>${o}</option>`).join('')}</select></label>
        <label>Peak current A (DIP)<select data-k="amps">${M.current_options_a.map(o => `<option ${Math.abs(o - c.amps) < .01 ? 'selected' : ''}>${o.toFixed(2)}</option>`).join('')}</select></label>
        <label>Max speed ${c.unit}/s<input data-k="maxRate" type="number" step="1" min="0.5" value="${c.maxRate}"></label>
        <label>Accel ${c.unit}/s²<input data-k="accRate" type="number" step="1" min="0.5" value="${c.accRate}"></label>
        <label>Limit switch at ${c.unit}<input data-k="homeDeg" type="number" step="0.5" value="${c.homeDeg}"></label>
        <label>Direction<select data-k="invert"><option value="0">normal</option><option value="1">inverted</option></select></label>
      </div>
      <div class="row"><button class="btn small" data-a="home">Home</button><button class="btn small" data-a="jogm">−</button><button class="btn small" data-a="jogp">+</button><button class="btn small ghost" data-a="zero">Set here as 0 steps</button></div>
      <div class="stat" data-stat></div>`;
    card.querySelectorAll('[data-k]').forEach(inp => inp.onchange = () => {
      const k = inp.dataset.k; let v = inp.value;
      if (k === 'invert') c.invert = v === '1'; else c[k] = +v;
      if (k === 'homeDeg') c.switchAt = c.homeDeg;
      c.vMax = sps(c); c.aMax = acc(c);
      send(`V ${c.i} ${sps(c)} ${acc(c)}`);
    });
    card.querySelector('[data-a=home]').onclick = () => send(`H ${c.i} ${c.homeDir}`);
    const jog = (s) => moveTo({ [c.name]: toUnits(c, c.target * (c.invert ? -1 : 1)) + s * (c.name === 'gripper' ? 5 : 5) });
    card.querySelector('[data-a=jogm]').onclick = () => jog(-1);
    card.querySelector('[data-a=jogp]').onclick = () => jog(1);
    card.querySelector('[data-a=zero]').onclick = () => { ui.flash('Z zeroes every channel in the firmware'); send('Z'); };
    c.card = card; host.append(card);
  });
}
function updateMotorCards() {
  CH.forEach(c => {
    const s = spu(c), led = c.card.querySelector('[data-led]');
    led.className = 'led ' + (!driversEnabled ? '' : c.stalled ? 'bad' : (Math.abs(c.vel) > 1 || c.homing) ? 'run' : 'on');
    const motorRev = c.name === 'gripper' ? physical(c) / c.lead : physical(c) * c.ratio / 360;
    const hwTxt = c.hwPos != null ? `  hw ${c.hwPos}  Δ ${(c.hwPos - Math.round(c.pos)).toString()}` : '';
    c.card.querySelector('[data-stat]').textContent =
      `steps/${c.unit} ${s.toFixed(2)}   res ${(1 / s).toFixed(4)}${c.unit}/step\n` +
      `pos ${Math.round(c.pos)}  target ${c.target}${hwTxt}\n` +
      `rate ${Math.abs(c.vel).toFixed(0)} steps/s  (max ${sps(c)}, accel ${acc(c)})\n` +
      `motor ${(Math.abs(c.vel) / c.ppr * 60).toFixed(0)} rpm   shaft ${motorRev.toFixed(2)} rev   DIR ${c.vel >= 0 ? 'HIGH' : 'LOW'}${c.tripped ? '   LIMIT' : ''}${c.homed ? '   homed' : ''}`;
  });
  const rate = CH.reduce((s, c) => s + Math.abs(c.vel), 0), cap = M.mega_combined_sps, f = Math.min(1, rate / cap);
  const peak = CH.reduce((s, c) => s + sps(c), 0);
  $('#rateMeter').innerHTML = `<h3>Combined step rate</h3><div class="bar"><i class="${f > .9 ? 'b' : f > .7 ? 'w' : ''}" style="width:${f * 100}%"></i><span>${rate.toFixed(0)} / ${cap} steps/s</span></div>
    <div class="small muted">All channels at max speed: ${peak} steps/s${peak > cap ? ' (over the Mega budget: lower speeds or pulses/rev, or move to a Teensy 4.x)' : ''}</div>`;
}

// Test tab
$('#safetyVal').textContent = M.safety;
function updateTest(t) {
  const kg = payloadKg();
  $('#payloadVal').textContent = `${(+$('#payload').value).toFixed(2)} lb (${kg.toFixed(2)} kg)`;
  $('#torqueBars').innerHTML = ['shoulder', 'elbow', 'wrist'].map(n => {
    const need = Math.abs(t[n]), have = available(n), m = have / Math.max(need, 1e-6), f = Math.min(1, need / have);
    return `<div class="small"><b>${n}</b> ${need.toFixed(1)} N·m needed / ${have.toFixed(1)} available · margin ${m > 99 ? '>99' : m.toFixed(2)}× · design worst case ${J[n].required_nm} N·m</div>
      <div class="bar"><i class="${m < 1 ? 'b' : m < M.safety ? 'w' : ''}" style="width:${f * 100}%"></i></div>`;
  }).join('');
}
function pinTable() {
  $('#pinTable').innerHTML = `<table><tr><th>CH</th><th>Joint</th><th>STEP</th><th>DIR</th><th>LIMIT</th><th>Driver</th></tr>${CH.map(c => {
    const p = c.name === 'gripper' ? M.gripper.pins : J[c.name].pins;
    return `<tr><td>${c.i}</td><td>${c.name}</td><td>D${p.step} <span data-pin="s${c.i}"></span></td><td>D${p.dir} <span data-pin="d${c.i}"></span></td><td>D${p.limit} <span data-pin="l${c.i}"></span></td><td>${c.i === 4 ? 'TB6600/DM542' : 'DM542'}</td></tr>`;
  }).join('')}<tr><td colspan="6">ENABLE D${M.enable_pin} → ENA− on all drivers (HIGH = disabled) · <span data-pin="en"></span></td></tr></table>`;
}
function updatePins() {
  CH.forEach(c => {
    const s = document.querySelector(`[data-pin=s${c.i}]`); if (!s) return;
    s.textContent = Math.abs(c.vel) > 1 ? `${Math.abs(c.vel).toFixed(0)} Hz` : '';
    document.querySelector(`[data-pin=d${c.i}]`).textContent = c.vel >= 0 ? 'H' : 'L';
    document.querySelector(`[data-pin=l${c.i}]`).innerHTML = c.tripped ? '<b style="color:var(--bad)">OPEN</b>' : 'closed';
  });
  document.querySelector('[data-pin=en]').textContent = driversEnabled ? 'LOW (drivers on)' : 'HIGH (drivers off)';
}
const tlog = (s) => { const e = $('#testLog'); e.textContent += s + '\n'; e.scrollTop = e.scrollHeight; };
const TESTS = {
  async sweep() {
    tlog('Sweep: each joint to both soft limits and back');
    for (const c of CH) {
      for (const v of [c.lim[0], c.lim[1], c.name === 'gripper' ? 20 : 0]) { moveTo({ [c.name]: v }); await waitSettled(); }
      tlog(`  ${c.name}: ${c.lim[0]} → ${c.lim[1]} ${c.unit} ok${c.stalled ? ' (hit hard stop!)' : ''}`);
    }
    moveTo(PRESETS.Ready); await waitSettled(); tlog('Sweep done');
  },
  async worst() {
    tlog(`Worst case: arm horizontal, ${(+$('#payload').value)} lb payload`);
    moveTo(PRESETS.Reach); await waitSettled();
    const t = torques();
    for (const n of ['shoulder', 'elbow', 'wrist']) tlog(`  ${n}: ${Math.abs(t[n]).toFixed(1)} N·m, available ${available(n).toFixed(1)}, margin ${(available(n) / Math.abs(t[n])).toFixed(2)}× (design ${J[n].required_nm} N·m)`);
    tlog(`  tool reach ${Math.hypot(wp(tcp).x, wp(tcp).y).toFixed(0)} mm (limit ${M.max_extension_mm})`);
  },
  async grip() {
    tlog('Gripper: open, close, open');
    for (const v of [70, 0, 40]) { moveTo({ gripper: v }); await waitSettled(); tlog(`  ${v} mm reached in sim`); }
  },
  async envelope() {
    tlog('Reach scan: IK on a grid at pitch 0 (yaw 0 plane)');
    let ok = 0, bad = 0;
    for (let x = 100; x <= 900; x += 100) for (let z = -100; z <= 900; z += 100) {
      try { const a = ik(x, LATERAL, z, 0, true); const inLim = a.every((v, i) => v >= CH[i].lim[0] && v <= CH[i].lim[1]); inLim ? ok++ : bad++; } catch { bad++; }
    }
    tlog(`  reachable within limits: ${ok}, not: ${bad} of ${ok + bad} grid points`);
  },
};
document.querySelectorAll('[data-test]').forEach(b => b.onclick = async () => { b.disabled = true; try { await TESTS[b.dataset.test](); } finally { b.disabled = false; } });

// Parts tab
function buildParts() {
  const lt = $('#layerToggles');
  Object.keys(layers).forEach(k => {
    const l = el('label', { className: 'chip' }, `<input type="checkbox" ${layerOn[k] ? 'checked' : ''}> ${k}`);
    l.querySelector('input').onchange = (e) => setLayer(k, e.target.checked); lt.append(l); setLayer(k, layerOn[k]);
  });
  renderParts();
  $('#partSearch').oninput = renderParts;
  $('#explode').oninput = (e) => explode(+e.target.value);
}
function renderParts() {
  const q = $('#partSearch').value.toLowerCase(), groups = {};
  for (const c of catalog.values()) if (!q || (c.name + c.key + (c.note || '')).toLowerCase().includes(q)) (groups[c.cat] ||= []).push(c);
  let ok = 0, tot = 0;
  const short = [];
  for (const c of catalog.values()) if (c.qty != null) { tot++; if ((c.n || 0) === c.qty) ok++; else short.push(`${c.name.split(',')[0]}: model uses ${c.n || 0}, BOM lists ${c.qty}`); }
  $('#partCount').innerHTML = `${ok} of ${tot} BOM lines match the model exactly.` + (short.length ? `<div class="muted">Mismatch: ${short.join('; ')}</div>` : '');
  $('#partList').innerHTML = Object.entries(groups).map(([g, cs]) => `<div class="grp">${g}</div>` + cs.map(c => {
    const placed = c.n || 0;
    const st = c.qty == null ? `<span class="cnt">${placed}</span>` : `<span class="cnt ${placed === c.qty ? 'ok' : 'bad'}">${placed}/${c.qty}</span>`;
    return `<div class="pi" data-key="${c.key}"><span>${c.stl ? '▣' : '◇'}</span><span>${c.name}</span>${st}</div>`;
  }).join('')).join('');
  document.querySelectorAll('#partList .pi').forEach(e => { e.onclick = () => select(e.dataset.key); e.ondblclick = () => inspector.open(e.dataset.key); });
}

// Link tab
ui.setLink = (on) => {
  $('#linkBadge').textContent = on ? 'LIVE: ARDUINO' : 'SIMULATION'; $('#linkBadge').className = 'badge ' + (on ? 'live' : 'sim');
  $('#btnConnect').disabled = on; $('#btnDisconnect').disabled = !on;
};
$('#btnConnect').onclick = () => link.connect();
$('#btnDisconnect').onclick = () => link.disconnect();
$('#feedbackMode').onchange = (e) => feedback = e.target.value;
$('#btnRaw').onclick = () => { const v = $('#rawCmd').value.trim(); if (v) send(v); };
$('#rawCmd').onkeydown = (e) => { if (e.key === 'Enter') $('#btnRaw').click(); };

// Tabs, views
document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => {
  document.querySelectorAll('#tabs button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', t.id === 'tab-' + b.dataset.tab));
});
const VIEWS = { iso: [[1500, -1700, 1100], [250, 0, 150]], front: [[300, -2400, 300], [300, 0, 200]], side: [[2600, 150, 350], [300, 0, 200]], top: [[200, -1, 2800], [200, 0, 0]], bench: [[-300, -900, 500], [-880, 0, TABLE_Z]] };
document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => { const [p, t] = VIEWS[b.dataset.view]; camera.position.set(...p); orbit.target.set(...t); });
ui.flash = (msg) => { const w = el('div', { className: 'w', textContent: msg }); $('#warnings').prepend(w); setTimeout(() => w.remove(), 4000); };

// ---------------------------------------------------------------- inputs: keyboard + gamepad
const keys = new Set();
addEventListener('keydown', e => {
  if (/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
  if (e.code === 'Space') { e.preventDefault(); estop(); return; }
  if (e.code === 'KeyH') return homeAll();
  if (e.code === 'KeyP') return $('#btnTeach').click();
  keys.add(e.code);
});
addEventListener('keyup', e => keys.delete(e.code));
let padMode = 'joint', padPrev = [];
function jogInputs() {
  const axes = { yaw: 0, shoulder: 0, elbow: 0, wrist: 0, gripper: 0, x: 0, y: 0, z: 0, p: 0 };
  const k = (a, b) => (keys.has(a) ? 1 : 0) - (keys.has(b) ? 1 : 0);
  axes.yaw = k('KeyQ', 'KeyA'); axes.shoulder = k('KeyW', 'KeyS'); axes.elbow = k('KeyE', 'KeyD'); axes.wrist = k('KeyR', 'KeyF'); axes.gripper = k('KeyT', 'KeyG');
  axes.x = k('ArrowUp', 'ArrowDown'); axes.y = k('ArrowLeft', 'ArrowRight'); axes.z = k('PageUp', 'PageDown'); axes.p = axes.wrist;
  const pad = [...(navigator.getGamepads ? navigator.getGamepads() : [])].find(Boolean);
  if (pad) {
    $('#gamepadInfo').textContent = `Gamepad: ${pad.id.slice(0, 48)} · mode ${$('#jogMode').value}`;
    const dz = (v) => Math.abs(v) < 0.15 ? 0 : v;
    const [lx, ly, rx, ry] = [0, 1, 2, 3].map(i => dz(pad.axes[i] || 0));
    axes.yaw += -lx; axes.shoulder += -ly; axes.elbow += -ry; axes.wrist += rx;
    axes.x += -ly; axes.y += -lx; axes.z += -ry; axes.p += rx;
    const bt = (i) => pad.buttons[i] && pad.buttons[i].value;
    axes.gripper += (bt(7) || 0) - (bt(6) || 0);
    const press = (i) => pad.buttons[i] && pad.buttons[i].pressed && !padPrev[i];
    if (press(1)) estop();
    if (press(0)) $('#btnTeach').click();
    if (press(3)) homeAll();
    if (press(9)) { $('#jogMode').value = $('#jogMode').value === 'joint' ? 'cart' : 'joint'; }
    padPrev = pad.buttons.map(b => b.pressed);
  }
  return axes;
}
addEventListener('gamepadconnected', e => ui.flash(`Gamepad connected: ${e.gamepad.id.slice(0, 40)}`));
let jogAccum = 0;
function jog(dt) {
  const a = jogInputs(), s = +$('#jogScale').value;
  const any = Object.values(a).some(v => v);
  if (!any) return;
  jogAccum += dt; if (jogAccum < 0.08) return;   // ~12 command batches per second
  const t = jogAccum; jogAccum = 0;
  if ($('#jogMode').value === 'joint' || a.gripper) {
    const cur = targetUnits(), next = {};
    if ($('#jogMode').value === 'joint') for (const n of JOINTS) if (a[n]) next[n] = cur[n] + a[n] * CH.find(c => c.name === n).maxRate * s * t * 1.5;
    if (a.gripper) next.gripper = cur.gripper + a.gripper * CH[4].maxRate * s * t * 1.5;
    if (Object.keys(next).length) moveTo(next);
  }
  if ($('#jogMode').value === 'cart' && (a.x || a.y || a.z || a.p)) {
    const p = wp(W.H), v = 150 * s * t;
    const r = doIK(p.x + a.x * v, p.y + a.y * v, p.z + a.z * v, (+$('#ikP').value) + a.p * 40 * s * t, true);
    if (a.p) $('#ikP').value = ((+$('#ikP').value) + a.p * 40 * s * t).toFixed(1);
  }
}

// ---------------------------------------------------------------- main loop
buildJointSliders(); buildMotorCards(); buildParts(); pinTable();
CH.forEach(c => { c.vMax = sps(c); c.aMax = acc(c); });
// Simulated start: already homed and parked at the ready pose (press Home all to watch the real homing sequence).
CH.forEach(c => { const v = PRESETS.Ready[c.name]; c.phys = v; c.pos = c.target = toSteps(c, v); c.homed = true; shown[c.name] = v; });
driversEnabled = true; syncSlidersToTargets();
$('#loading').remove();
resize();

let last = performance.now(), frame = 0;
function tick(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now; frame++;
  jog(dt);
  sim.step(dt);
  applyPose();
  scene.updateMatrixWorld(true);
  updateWires();
  if (frame % 4 === 0) {
    const r = checks();
    const wPt = r.pts.wrist, tPt = r.pts.tool;
    $('#readout').textContent =
      `wrist axis  X ${wPt.x.toFixed(0).padStart(5)}  Y ${wPt.y.toFixed(0).padStart(5)}  Z ${wPt.z.toFixed(0).padStart(5)} mm\n` +
      `tool tip    X ${tPt.x.toFixed(0).padStart(5)}  Y ${tPt.y.toFixed(0).padStart(5)}  Z ${tPt.z.toFixed(0).padStart(5)} mm\n` +
      `reach ${r.reach.toFixed(0)} mm   pitch ${(shown.shoulder + shown.elbow + shown.wrist).toFixed(1)}°   grip ${shown.gripper.toFixed(1)} mm\n` +
      `steps/s ${r.rate.toFixed(0)}   drivers ${driversEnabled ? 'ON' : 'OFF'}`;
    $('#warnings').querySelectorAll('.chk').forEach(e => e.remove());
    r.out.slice(0, 5).forEach(([k, m]) => $('#warnings').append(el('div', { className: 'chk ' + (k === 'w' ? 'w' : ''), textContent: m })));
    const homed = CH.every(c => c.homed);
    $('#homedBadge').textContent = homed ? 'HOMED' : 'NOT HOMED'; $('#homedBadge').className = 'badge ' + (homed ? 'ok' : 'warn');
    $('#btnEnable').textContent = driversEnabled ? 'Disable drivers' : 'Enable drivers';
    updateSliderText(); updateMotorCards(); updateTest(r.t); updatePins();
    if (document.activeElement.parentElement?.parentElement?.className !== 'grid4' && !$('#chkGizmo').checked) { $('#ikX').value = wPt.x.toFixed(0); $('#ikY').value = wPt.y.toFixed(0); $('#ikZ').value = wPt.z.toFixed(0); }
    if ($('#chkFollow').checked) orbit.target.lerp(tPt, 0.2);
  }
  orbit.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
window.twin = { M, CH, catalog, send, ik, moveTo, sim, scene, camera, orbit, wp, W, E, S, tcp };
