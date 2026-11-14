// node tools/ga.js <3d-workflow dir> <out.json> [stl dir]      (needs: npm i playwright, npx playwright install chromium)
// Opens the 3D twin (control/index.html) in a headless browser at the GA pose and writes:
//  - out.json: hidden-line views (PNG data URLs, black lines on white) of the whole assembled table, made from the same
//    meshes the app shows: part outlines (part changes), creases (normal changes) and steps (depth jumps); plus, per part,
//    a visible pixel for its balloon, and the scale. arm/asmsheets.py turns it into ASM-001.
//  - [stl dir]: every part as an STL in its assembled position (world mm, Z up), for the Anatomy live 3D viewer.
const { chromium } = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path');
const [rootArg, out, stlDir] = process.argv.slice(2); const root = require('path').resolve(rootArg);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.stl': 'model/stl', '.svg': 'image/svg+xml', '.png': 'image/png', '.txt': 'text/plain' };
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!f.startsWith(path.resolve(root)) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
});
(async () => {
  await new Promise(res => srv.listen(0, '127.0.0.1', res));
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 800 } });
  p.on('console', m => { if (m.text().startsWith('ga ')) console.log(m.text()); });
  p.on('pageerror', e => console.error('page:', e.message));
  await p.goto(`http://127.0.0.1:${srv.address().port}/control/index.html`);
  await p.waitForFunction(() => window.twin && window.twin.scene, null, { timeout: 120000 });
  const res = await p.evaluate(async ({ wantStl }) => {
    const THREE = await import('three');
    const T = window.twin;
    T.moveTo({ yaw: 0, shoulder: 0, elbow: 0, wrist: 0, gripper: 20 });             // in simulation this drives the simulated controller
    const tip = () => { const v = new THREE.Vector3(); T.tcp.getWorldPosition(v); return v; };
    for (let i = 0, last = null; i < 400; i++) {            // wait until the simulated arm stops moving
      await new Promise(r => setTimeout(r, 100)); const v = tip();
      if (last && v.distanceTo(last) < 0.01 && i > 10) break; last = v;
    }
    T.scene.updateMatrixWorld(true);
    // parts: every tagged object, one id per catalog key
    const keys = [], parts = [];
    for (const [key, c] of T.catalog) {
      if (!c.objs.length || key === 'payload' || key === 'harness') continue;
      keys.push(key); const id = keys.length;
      for (const o of c.objs) o.traverse(m => { if (m.isMesh && m.userData.partRoot === o) parts.push({ m, id, key, root: o }); });
    }
    const seen = new Set(); const meshes = parts.filter(x => !seen.has(x.m) && seen.add(x.m));
    const isVisible = o => { for (let q = o; q; q = q.parent) if (!q.visible) return false; return true; };
    const bad = [];
    const draw = meshes.filter(x => {
      if (!isVisible(x.m)) return false;
      const bb = new THREE.Box3().setFromObject(x.m), sz = bb.getSize(new THREE.Vector3());
      const ok = [bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z].every(Number.isFinite) && sz.length() < 5000;
      if (!ok) bad.push(x.key); x.bb = bb; return ok;
    });
    if (bad.length) console.log('ga skipped (no finite geometry):', [...new Set(bad)].join(' '));
    const box = new THREE.Box3(); draw.forEach(x => box.union(x.bb));
    console.log('ga parts', keys.length, 'meshes', meshes.length, 'drawn', draw.length, JSON.stringify(box));
    const R = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
    const sc = new THREE.Scene();
    const PX = 3;                                            // px per mm of paper in the PNG
    const views = {};
    const VIEWS = { FRONT: { dir: [0, -1, 0], up: [0, 0, 1] }, TOP: { dir: [0, 0, 1], up: [0, 1, 0] }, RIGHT: { dir: [1, 0, 0], up: [0, 0, 1] } };
    const scale = 0.1;                                       // 1:10
    for (const [name, v] of Object.entries(VIEWS)) {
      const d = new THREE.Vector3(...v.dir), up = new THREE.Vector3(...v.up), rt = new THREE.Vector3().crossVectors(up, d).normalize();
      const corners = []; for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) corners.push(new THREE.Vector3(x, y, z));
      const u = corners.map(c => c.dot(rt)), w = corners.map(c => c.dot(up)), dd = corners.map(c => c.dot(d));
      const u0 = Math.min(...u) - 20, u1 = Math.max(...u) + 20, w0 = Math.min(...w) - 20, w1 = Math.max(...w) + 20, d1 = Math.max(...dd) + 50, d0 = Math.min(...dd) - 50;
      const k = PX * scale; const Wp = Math.round((u1 - u0) * k), Hp = Math.round((w1 - w0) * k);
      const cam = new THREE.OrthographicCamera(u0, u1, w1, w0, 1, d1 - d0 + 1);
      // place the camera so screen-right = rt and screen-up = up exactly; ortho bounds already in (rt, up) coords
      cam.position.set(0, 0, 0).addScaledVector(d, d1 + 1); cam.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(rt, up, d)); cam.updateMatrixWorld(true);
      R.setSize(Wp, Hp, false); R.setPixelRatio(1);
      const rtg = new THREE.WebGLRenderTarget(Wp, Hp);
      const pass = (matFor) => {
        sc.clear(); for (const x of draw) { const c = new THREE.Mesh(x.m.geometry, matFor(x)); x.m.matrixWorld.decompose(c.position, c.quaternion, c.scale); sc.add(c); }
        sc.background = new THREE.Color(0, 0, 0); R.setRenderTarget(rtg); R.render(sc, cam); const buf = new Uint8Array(Wp * Hp * 4); R.readRenderTargetPixels(rtg, 0, 0, Wp, Hp, buf); R.setRenderTarget(null); return buf;
      };
      const idMat = {}; const ID = pass(x => idMat[x.id] || (idMat[x.id] = new THREE.MeshBasicMaterial({ color: new THREE.Color(((x.id >> 0) & 255) / 255, ((x.id * 7) & 255) / 255, 1), side: THREE.DoubleSide })));
      const nm = new THREE.MeshNormalMaterial({ side: THREE.DoubleSide }); const N = pass(() => nm);
      const dm = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side: THREE.DoubleSide }); const D = pass(() => dm);
      const depth = i => (D[i] / 255 / (256 ** 3) + D[i + 1] / 255 / (256 ** 2) + D[i + 2] / 255 / 256 + D[i + 3] / 255) * (d1 - d0);
      const idAt = i => ID[i + 2] ? ID[i] : 0;
      const edge = new Uint8Array(Wp * Hp), pix = {};
      for (let y = 0; y < Hp; y++) for (let x = 0; x < Wp; x++) {
        const i = (y * Wp + x) * 4, a = idAt(i);
        if (a) { const s = pix[a] || (pix[a] = { n: 0, sx: 0, sy: 0, pts: [] }); s.n++; s.sx += x; s.sy += y; if ((x + y * 7) % 23 === 0) s.pts.push([x, y]); }
        let e = false;
        for (const [dx, dy] of [[1, 0], [0, 1]]) {
          if (x + dx >= Wp || y + dy >= Hp) continue; const j = ((y + dy) * Wp + x + dx) * 4, b = idAt(j);
          if (a !== b) { e = true; break; }
          if (!a) continue;
          const dot = ((N[i] - 128) * (N[j] - 128) + (N[i + 1] - 128) * (N[j + 1] - 128) + (N[i + 2] - 128) * (N[j + 2] - 128)) / (127 * 127);
          if (dot < 0.86 || Math.abs(depth(i) - depth(j)) > 4) { e = true; break; }
        }
        if (e) edge[(Hp - 1 - y) * Wp + x] = 1;                   // GL rows are bottom-up
      }
      const cv = document.createElement('canvas'); cv.width = Wp; cv.height = Hp; const g = cv.getContext('2d'); const im = g.createImageData(Wp, Hp);
      for (let i = 0; i < Wp * Hp; i++) { const v = edge[i] ? 0 : 255; im.data[4 * i] = im.data[4 * i + 1] = im.data[4 * i + 2] = v; im.data[4 * i + 3] = edge[i] ? 255 : 0; }
      g.putImageData(im, 0, 0);
      const anchors = {};
      for (const [a, s] of Object.entries(pix)) {                   // the visible pixel nearest the part's visible centroid
        const cx = s.sx / s.n, cy = s.sy / s.n; let best = null, bd = 1e18;
        for (const [x, y] of s.pts) { const dd2 = (x - cx) ** 2 + (y - cy) ** 2; if (dd2 < bd) { bd = dd2; best = [x, y]; } }
        if (best) anchors[keys[a - 1]] = { x: best[0] / PX, y: (Hp - 1 - best[1]) / PX, area: s.n / PX / PX };
      }
      const P = (X, Y, Z) => { const q = new THREE.Vector3(X, Y, Z); return { x: (q.dot(rt) - u0) * scale, y: (w1 - q.dot(up)) * scale }; };
      views[name] = { png: cv.toDataURL('image/png'), w: Wp / PX, h: Hp / PX, anchors, origin: P(0, 0, 0), u0, w1 };
      rtg.dispose();
    }
    // key world points (mm) for dimensions
    const wp = o => { const v = new THREE.Vector3(); o.getWorldPosition(v); return [v.x, v.y, v.z]; };
    const pts = { shoulder: wp(T.S.H), elbow: wp(T.E.H), wrist: wp(T.W.H), tcp: wp(T.tcp), bbox: [box.min.toArray(), box.max.toArray()] };
    // assembled STLs
    const stls = {};
    if (wantStl) {
      const { STLExporter } = await import('three/addons/exporters/STLExporter.js');
      const ex = new STLExporter();
      const byKey = {}; for (const x of draw) (byKey[x.key] = byKey[x.key] || []).push(x.m);
      for (const [key, ms] of Object.entries(byKey)) {
        const g = new THREE.Group(); for (const m of ms) { const c = new THREE.Mesh(m.geometry); m.matrixWorld.decompose(c.position, c.quaternion, c.scale); g.add(c); }
        const dv = ex.parse(g, { binary: true }); const u8 = new Uint8Array(dv.buffer); let bin = ''; for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); stls[key] = btoa(bin);
      }
    }
    const names = {}; for (const k of keys) { const c = T.catalog.get(k); names[k] = { name: c.name, cat: c.cat, qty: c.qty, note: c.note || "", n: c.n || c.objs.length }; }
    return { scale, views, pts, names, stls };
  }, { wantStl: !!stlDir });
  if (stlDir) {
    fs.mkdirSync(stlDir, { recursive: true });
    for (const f of fs.readdirSync(stlDir)) if (f.endsWith('.stl')) fs.unlinkSync(path.join(stlDir, f));
    for (const [k, s] of Object.entries(res.stls)) fs.writeFileSync(path.join(stlDir, `${k.replace(/[^\w.-]/g, '_')}.stl`), Buffer.from(s, 'base64'));
  }
  delete res.stls;
  fs.writeFileSync(out, JSON.stringify(res));
  await b.close(); srv.close();
  console.log(`ga: ${Object.keys(res.views).length} views, ${Object.keys(res.names).length} parts${stlDir ? `, STLs in ${stlDir}` : ''}`);
})().catch(e => { console.error(e.message); process.exit(1); });
