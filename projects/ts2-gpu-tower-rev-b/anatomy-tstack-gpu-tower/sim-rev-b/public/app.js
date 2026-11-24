// TS-2 rev B twin client. Static files only, relative URLs (works from Anatomy, a file server or the hub).
const L = window.TwinLoad || { stage() {}, progress() {}, indeterminate() {}, done() {}, fail(e) { console.error(e); } };
L.stage('engine');
const THREE = await import('three');
const { OrbitControls } = await import('three/addons/controls/OrbitControls.js');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const M = await import('./model.js');
L.progress(1);

const $ = (s) => document.querySelector(s);
const PKG = '../../prototype/';

// ------------------------------------------------------------------ design data
L.stage('design');
async function getJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Could not read ${url.replace(PKG, 'prototype/')} (HTTP ${r.status}).`);
  return r.json();
}
const [DB, CALC, ASM] = await Promise.all([getJson(PKG + 'design_basis.json'), getJson(PKG + 'thermal-fluid/calc.json'), getJson(PKG + 'mechanical/assembled/assembly.json')]);
const byNode = Object.fromEntries(ASM.nodes.map((n) => [n.node, n]));
L.progress(1);

// ------------------------------------------------------------------ 3D
const view = $('#view');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.localClippingEnabled = true;
view.prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b0b0d);
const camera = new THREE.PerspectiveCamera(32, 1, 10, 60000);
const controls = new OrbitControls(camera, renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0x202024, 1.2));
const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(3000, 5000, 3500); scene.add(key);
const fill = new THREE.DirectionalLight(0xbfd4ff, 0.8); fill.position.set(-3500, 2500, -1500); scene.add(fill);
const rim = new THREE.DirectionalLight(0xff3344, 0.5); rim.position.set(-2000, 1500, 3000); scene.add(rim);
const floor = new THREE.Mesh(new THREE.CircleGeometry(2600, 64), new THREE.MeshStandardMaterial({ color: 0x18191c, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; scene.add(floor);
const root = new THREE.Group(); root.rotation.x = -Math.PI / 2; scene.add(root);    // CAD is Z-up, mm

L.stage('model', 'Downloading the 3D model of the tower');
async function fetchWithProgress(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`The 3D model ${url.replace(PKG, 'prototype/')} is missing (HTTP ${r.status}). Run prototype/mechanical/cad/build_all.py.`);
  const total = +r.headers.get('content-length') || 0;
  if (!r.body || !total) { L.indeterminate('Downloading the 3D model'); return r.arrayBuffer(); }
  const rd = r.body.getReader(); const chunks = []; let got = 0;
  for (;;) { const { done, value } = await rd.read(); if (done) break; chunks.push(value); got += value.length; L.progress(got / total, `3D model ${(got / 1e6).toFixed(1)} of ${(total / 1e6).toFixed(1)} MB`); }
  const buf = new Uint8Array(got); let o = 0; for (const c of chunks) { buf.set(c, o); o += c.length; }
  return buf.buffer;
}
const glbBuf = await fetchWithProgress(PKG + 'mechanical/assembled/' + ASM.glb);
L.stage('scene', 'Building the scene');
const gltf = await new Promise((ok, bad) => new GLTFLoader().parse(glbBuf, '', ok, (e) => bad(new Error('The 3D model could not be parsed: ' + (e.message || e)))));
// trimesh writes Y-up glTF with the Z-up CAD rotated; undo it so 'root' (Z-up) holds the mm geometry
const model = gltf.scene;
const bb0 = new THREE.Box3().setFromObject(model); const sz0 = bb0.getSize(new THREE.Vector3());
if (sz0.y > sz0.z * 1.2) model.rotation.x = Math.PI / 2;                         // Y-up file: bring Z back up inside root
root.add(model);
const pick = [], gpuMesh = {}, rotors = [], coilTubes = [], hideSkins = [], coils = [], c1Parts = [];
model.traverse((o) => {
  if (!o.isMesh) return;
  let n = o, rec = null; while (n && !rec) { rec = byNode[n.name]; n = n.parent; }
  o.userData.rec = rec || { node: o.name, name: o.name };
  pick.push(o);
  const nm = o.userData.rec.node || '';
  if (/_gpu_shroud$/.test(nm)) { o.material = o.material.clone(); gpuMesh[o.userData.rec.gpu_index] = o; }
  if (/impeller_\d_rotor/.test(nm)) rotors.push(o);
  if (/coil_tubes|coil_headers/.test(nm)) { o.material = o.material.clone(); coilTubes.push(o); }
  if (/side_skin|grille|filter_/.test(nm)) hideSkins.push(o);
  if (/coil_|drip_tray/.test(nm)) coils.push(o);
  if (/^C1_/.test(nm)) c1Parts.push(o);
});
for (const o of hideSkins) o.visible = false;                                   // open by default: the naked tower
for (const r of rotors) {                                                         // spin each rotor about its own vertical axis
  r.geometry.computeBoundingBox(); const c = r.geometry.boundingBox.getCenter(new THREE.Vector3());
  r.geometry.translate(-c.x, -c.y, 0); r.position.x += c.x; r.position.y += c.y;
  const ax = byNode[r.userData.rec.node]?.axis; r.userData.ax = ax;
}
function frameAll() {
  const box = new THREE.Box3().setFromObject(root); const c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3()).length();
  controls.target.copy(c); camera.position.copy(c.clone().add(new THREE.Vector3(0.78, 0.32, 0.92).multiplyScalar(s * 0.95))); controls.update();
}
frameAll();
L.progress(1);

// ------------------------------------------------------------------ plant
L.stage('sim', 'Settling the plant at the design point');
let plant = M.createPlant(DB, CALC);
for (let k = 0; k < 900; k++) plant.step(1);
const HIST = [];
L.progress(1);

// ------------------------------------------------------------------ UI
$('#viewMsg').textContent = `${pick.length} parts from the CAD export · ${Object.keys(gpuMesh).length} GPUs tinted by core temperature · click any part · drag to orbit`;
const box = $('#pinfo');
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
renderer.domElement.addEventListener('click', (e) => {
  const r = renderer.domElement.getBoundingClientRect();
  mouse.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(pick.filter((o) => o.visible && o.parent.visible), false).find((h) => !h.object.material.clippingPlanes?.length || true);
  if (!hit) { box.style.display = 'none'; return; }
  const p = hit.object.userData.rec;
  const S = plant.s;
  const live = p.gpu_index !== undefined ? `<br><span class="k">Live</span> core ${S.gpu[p.gpu_index].toFixed(1)} C, inlet ${S.inlet[p.column - 1].toFixed(1)} C, ${S.gpuP[p.gpu_index].toFixed(0)} W${S.throttle[p.gpu_index] ? ' <b style="color:#ff6b6b">SLOWDOWN</b>' : ''}` : '';
  box.innerHTML = `<b>${p.name || p.node}</b><br><span class="k">${(p.kind || '').toUpperCase()} · ${p.pn || ''} · BOM ${p.bom || '-'}</span><br>
    <span class="k">Node</span> ${p.node}<br>${p.material ? `<span class="k">Material</span> ${p.material}<br>` : ''}${p.finish ? `<span class="k">Finish</span> ${p.finish}<br>` : ''}
    ${p.drawing ? `<span class="k">Drawing</span> ${p.drawing}<br>` : ''}${p.slot ? `<span class="k">Column / slot</span> C${p.column} / S${String(p.slot).padStart(2, '0')}` : ''}${live}`;
  box.style.display = 'block';
});
$('#bSkins').onclick = (e) => { const on = !hideSkins[0].visible; hideSkins.forEach((o) => { o.visible = on; }); e.target.classList.toggle('on', on); };
$('#bCoil').onclick = (e) => { const on = !coils[0].visible; coils.forEach((o) => { o.visible = on; }); e.target.classList.toggle('on', !on); };
const clip = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);
$('#bCut').onclick = (e) => {
  const on = !e.target.classList.contains('on'); e.target.classList.toggle('on', on);
  // section along the C1 mid-plane (CAD y = 0 -> after root rotation, world -z = 0)
  for (const o of c1Parts) { o.material = o.material.clone(); o.material.clippingPlanes = on ? [clip] : []; o.material.clipShadows = true; }
};
$('#bFrame').onclick = frameAll;
const steps = ASM.steps;
function applyStep(n) {
  $('#stepT').textContent = n >= steps.length ? 'complete' : n === 0 ? 'nothing' : `step ${n}: ${steps[n - 1].title}`;
  const allowed = steps.slice(0, n).flatMap((s) => s.add);
  for (const o of pick) {
    const nm = o.userData.rec.node || '';
    const stepOf = steps.findIndex((s) => s.add.some((k) => nm.includes(k)));
    const vis = stepOf < 0 ? n >= steps.length : stepOf < n;
    o.parent.visible = true;
    o.userData.stepVis = vis;
    o.visible = vis && !(hideSkins.includes(o) && !$('#bSkins').classList.contains('on')) && !(coils.includes(o) && $('#bCoil').classList.contains('on'));
  }
}
$('#stepR').max = steps.length; $('#stepR').value = steps.length; $('#stepR').oninput = (e) => applyStep(+e.target.value); applyStep(steps.length);

const set = (id, v) => { $(id).value = v; };
function syncInputs() { const S = plant.s; set('#room', S.room); set('#rh', S.rh * 100); set('#load', S.load[0] * 100); $('#roomV').textContent = S.room; $('#rhV').textContent = Math.round(S.rh * 100); $('#loadV').textContent = Math.round(S.load[0] * 100); }
syncInputs();
$('#room').oninput = (e) => { plant.s.room = +e.target.value; $('#roomV').textContent = e.target.value; };
$('#rh').oninput = (e) => { plant.s.rh = +e.target.value / 100; $('#rhV').textContent = e.target.value; };
$('#load').oninput = (e) => { plant.s.load = plant.s.load.map(() => +e.target.value / 100); $('#loadV').textContent = e.target.value; };
let paused = false, speed = 10;
$('#speed').onchange = (e) => { speed = +e.target.value; };
$('#pause').onclick = (e) => { paused = !paused; e.target.textContent = paused ? 'Run' : 'Pause'; };
$('#reset').onclick = () => { plant = M.createPlant(DB, CALC); for (let k = 0; k < 900; k++) plant.step(1); HIST.length = 0; document.querySelectorAll('[data-f]').forEach((b) => b.classList.remove('on')); syncInputs(); };
document.querySelectorAll('[data-f]').forEach((b) => b.onclick = () => {
  const S = plant.s, f = b.dataset.f, on = !b.classList.contains('on'); b.classList.toggle('on', on);
  if (f === 'chiller') S.chiller = !on; else if (f === 'tec') S.tec = !on; else if (f.startsWith('imp')) S.impFail[+f[3]] = on;
  else if (f.startsWith('crps')) S.crpsFail[+f[4]] = on; else if (f === 'clog3') S.filterClog[3] = on ? 0.7 : 0; else if (f === 'feedA') S.feedLoss.A = on;
});
document.querySelectorAll('#tabs button').forEach((b) => b.onclick = () => {
  document.querySelectorAll('#tabs button').forEach((x) => x.classList.toggle('on', x === b));
  document.querySelectorAll('.pane').forEach((p) => p.classList.toggle('on', p.id === 'p-' + b.dataset.p));
});
// GPU grid
const grid = $('#gpus'); const cells = [];
for (let c = 0; c < 4; c++) {
  const h = document.createElement('div'); h.className = 'h'; h.textContent = 'C' + (c + 1); grid.append(h);
  for (let g = 0; g < 16; g++) { const d = document.createElement('div'); d.title = `C${c + 1} slot ${g + 1}: click to fail / restore its blower`; d.onclick = () => { const i = c * 16 + g; plant.s.blowerFail[i] = !plant.s.blowerFail[i]; }; grid.append(d); cells.push(d); }
}
function tcol(t) { const k = Math.max(0, Math.min(1, (t - 40) / 50)); return `hsl(${Math.round(130 - 130 * k)},70%,${55 - 8 * k}%)`; }
function tiles() {
  const S = plant.s, mx = Math.max(...S.gpu);
  const T = [['GPU inlet', S.inlet[0].toFixed(1) + ' C'], ['Hottest core', mx.toFixed(1) + ' C'], ['Plenum', S.plenumT.toFixed(1) + ' C'], ['Plenum dP', S.plenumP.toFixed(0) + ' Pa'],
    ['Turbine', Math.round(S.demand * 100) + ' %'], ['Air', Math.round(S.flowIn) + ' m3/h'], ['Coolant', S.coolant.toFixed(1) + ' C'], ['Dew point', S.dew.toFixed(1) + ' C'],
    ['Tracing duty', (S.coilQ.reduce((a, b) => a + b, 0) / 1000).toFixed(2) + ' kW'], ['Tower', S.towerKW.toFixed(1) + ' kW'], ['Feed A', S.feedA.toFixed(1) + ' A'], ['Feed B', S.feedB.toFixed(1) + ' A']];
  $('#tiles').innerHTML = T.map(([k, v]) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');
  S.gpu.forEach((t, i) => { const d = cells[i]; d.textContent = S.blowerFail[i] ? 'X' : Math.round(t); d.style.background = S.blowerFail[i] ? '#555' : tcol(t); d.style.outline = S.throttle[i] ? '2px solid #fff' : ''; });
  $('#alarms').innerHTML = S.alarms.slice(0, 8).map((a) => `<span>${a}</span>`).join('') + (S.alarms.length > 8 ? `<span>+${S.alarms.length - 8}</span>` : '');
  $('#clock').textContent = `sim ${new Date(S.t * 1000).toISOString().substr(11, 8)}`;
  const c = CALC.design_point.coil;
  $('#coolT').innerHTML = `<tr><th colspan=3>One column, live vs design (calc.json)</th></tr>
   <tr><td>Coolant supply</td><td>${S.coolant.toFixed(2)} C</td><td class="small">${CALC.design_point.T_coolant_C} C design; floor = dew + 2 K</td></tr>
   <tr><td>Tracing coil duty C1</td><td>${(S.coilQ[0]).toFixed(0)} W</td><td class="small">${c.Q_W} W, UA ${c.UA_W_K} W/K, eps ${c.eps}</td></tr>
   <tr><td>Coil face velocity</td><td>${c.v_face_m_s} m/s</td><td class="small">${c.rows} rows x 32 passes, 12 FPI, ${c.circuits} circuits, water ${c.v_water_m_s} m/s (Re ${c.Re_water})</td></tr>
   <tr><td>GPU inlet C1..C4</td><td>${S.inlet.map((x) => x.toFixed(1)).join(' / ')} C</td><td class="small">${CALC.design_point.T_gpu_inlet_C} C design</td></tr>
   <tr><td>Air rise through each GPU</td><td>${CALC.design_point.gpu_air_dT_K} K</td><td class="small">300 W at ${DB.GPU_AIR_M3H} m3/h blower flow</td></tr>
   <tr><td>Plenum temperature</td><td>${S.plenumT.toFixed(1)} C</td><td class="small">${CALC.design_point.T_plenum_C} C design</td></tr>
   <tr><td>Plenum pressure (set)</td><td>${S.plenumP.toFixed(1)} Pa (${S.setP.toFixed(0)})</td><td class="small">holds the column interior at the plenum so the blowers see no back-pressure</td></tr>
   <tr><td>Impellers</td><td>${S.impQ.map((q) => Math.round(q)).join(' / ')} m3/h</td><td class="small">${S.impRpm.map((r) => Math.round(r)).join(' / ')} rpm, 3 x R3G310 on 56 V, N+1</td></tr>
   <tr><td>Peltier trim</td><td>${S.tec ? 'on' : 'off'}</td><td class="small">${CALC.design_point.tec_cool_W_per_col} W cooling per column, ${CALC.design_point.tec_hot_W_per_col} W hot side ducted to the plenum</td></tr>`;
  $('#pwrT').innerHTML = `<tr><th>Column</th><th>CRPS 1-4 (W)</th><th>GPU 12 V</th></tr>` + [0, 1, 2, 3].map((k) => `<tr><td>C${k + 1} (feed ${k < 2 ? 'A' : 'B'})</td><td>${S.crpsLoad.slice(k * 4, k * 4 + 4).map((w, j) => S.crpsFail[k * 4 + j] ? '<b style="color:#ff6b6b">FAIL</b>' : Math.round(w)).join(' / ')}</td><td>${(S.gpuP.slice(k * 16, k * 16 + 16).reduce((a, b) => a + b, 0) / 12.2).toFixed(0)} A</td></tr>`).join('') +
    `<tr><td>Feeds</td><td colspan=2>A ${S.feedA.toFixed(1)} A, B ${S.feedB.toFixed(1)} A per phase (limit 48 A, 80 % of 60 A); tower ${S.towerKW.toFixed(1)} kW</td></tr>`;
}
const pc = $('#plot').getContext('2d');
function plot() {
  const cv = $('#plot'); cv.width = cv.clientWidth * devicePixelRatio; cv.height = cv.clientHeight * devicePixelRatio;
  const W = cv.width, H = cv.height; pc.clearRect(0, 0, W, H);
  const lines = [['#ff4d5e', (h) => h.core], ['#ffffff', (h) => h.pl], ['#4aa3ff', (h) => h.cool], ['#3fb27f', (h) => h.inl]];
  const y = (v) => H - (v - 10) / 90 * H;
  pc.strokeStyle = '#2a2c31'; for (let v = 20; v <= 90; v += 10) { pc.beginPath(); pc.moveTo(0, y(v)); pc.lineTo(W, y(v)); pc.stroke(); }
  for (const [col, f] of lines) { pc.strokeStyle = col; pc.lineWidth = 1.5 * devicePixelRatio; pc.beginPath(); HIST.forEach((h, i) => { const x = i / 600 * W; i ? pc.lineTo(x, y(f(h))) : pc.moveTo(x, y(f(h))); }); pc.stroke(); }
}
$('#about').innerHTML = `<p><b>Rev B</b>: ${DB.n_gpus} x ${DB.GPU}. ${DB.gpus_per_column} per column in 2 groups of 8 at ${DB.SLOT_PITCH} mm pitch, cards flat, brackets to the plenum, tails to the tracing coil.</p>
<p><b>Connection</b>: ${DB.pcie_link}. Each card plugs into a PCIe x16 Gen5 slot on the CBP-8 backplane (vertical, on the column side wall). Each slot has its own TPS25985 eFuse (30 A trip) feeding the slot and the card's 12V-2x6. The backplane links redrive the x8 lanes to the MCIO 8i cable down the rear channel to the host node in the plinth arm: ${DB.HOST_BOARD} with 4 x ${DB.HOST_SWITCH}.</p>
<p><b>Retention</b>: bracket thumbscrew (6-32) into the bracket rail; tail in a lined 16-slot comb (z held, y free for insertion); hinged hold-down bar with 3 mm EPDM pads over the connector, red latch at the midspan.</p>
<p><b>Cooling</b>: room air -> grille -> MERV 8 -> tracing coil (17.5 C water, dew + 2 K floor, Peltier trim) -> 10.8 mm gap -> card blower -> bracket -> bulkhead window -> plenum (held at ${CALC.design_point.plenum_setpoint_Pa} Pa) -> 3 x R3G310 -> 18 in chimney.</p>
<p><b>Power</b>: ${DB.supply}. Per column 4 x ${DB.CRPS} (3+1) on CPD-1 -> 40 x 5 copper busbars -> 2 x CBP-8.</p>
<p class="small">Numbers: prototype/design_basis.json and thermal-fluid/calc.json. Sim-only assumptions are listed in model.js (A).</p>`;
$('#runT').onclick = async () => {
  $('#tStat').textContent = 'running...'; $('#testT').innerHTML = ''; await new Promise((r) => setTimeout(r, 30));
  const rows = []; let pass = 0;
  for (const t of M.TESTS) { const r = M.runTest(t, DB, CALC); if (r.pass) pass++; rows.push(`<tr><td class="${r.pass ? 'pass' : 'fail'}">${r.pass ? 'PASS' : 'FAIL'}</td><td><b>${r.id}</b> ${r.name}<br><span class="small">${r.detail}</span></td></tr>`); $('#testT').innerHTML = rows.join(''); await new Promise((r) => setTimeout(r, 0)); }
  $('#tStat').textContent = `${pass} / ${M.TESTS.length} pass`;
};
function resize() { const w = view.clientWidth, h = view.clientHeight; renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); }
new ResizeObserver(resize).observe(view); resize();
let last = performance.now(), acc = 0, ui = 0;
const tint = new THREE.Color();
renderer.setAnimationLoop(() => {
  const now = performance.now(), dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (!paused) { acc += dt * speed; let n = 0; while (acc >= 1 && n < 400) { plant.step(1); acc -= 1; n++; if (plant.s.t % 1 === 0) { HIST.push({ core: Math.max(...plant.s.gpu), pl: plant.s.plenumT, cool: plant.s.coolant, inl: plant.s.inlet[0] }); if (HIST.length > 600) HIST.shift(); } } }
  const S = plant.s;
  rotors.forEach((r) => { const k = +r.userData.rec.impeller - 1; r.rotation.z -= (S.impRpm[k] || 0) / 60 * 2 * Math.PI * dt * 0.05; });
  for (const [i, m] of Object.entries(gpuMesh)) { const t = S.gpu[i]; const k = Math.max(0, Math.min(1, (t - 45) / 45)); tint.setHSL(0.33 - 0.33 * k, 0.9, 0.05 + 0.10 * k); m.material.emissive.copy(S.blowerFail[i] ? tint.setRGB(0.18, 0.18, 0.18) : tint); }
  const cold = Math.max(0, Math.min(1, (S.room - S.coolant) / 10)); for (const m of coilTubes) m.material.emissive.setRGB(0, 0.12 * cold, 0.35 * cold);
  if ((ui += dt) > 0.25) { ui = 0; tiles(); plot(); }
  controls.update(); renderer.render(scene, camera);
});
tiles();
window.TWIN = { camera, controls, THREE, get plant() { return plant; }, coils, hideSkins };
L.done();
