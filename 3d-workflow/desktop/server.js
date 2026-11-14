// Robot Arm desktop app server. No npm dependencies: node server.js
// Serves the bundled app (the app/ folder next to this file) on http://127.0.0.1:8766 and answers
//   /api/health          -> {"app":"robot-arm"}  (the UI uses this to show the desktop-only buttons)
//   /api/open?path=rel   -> opens a bundled file with its Windows app (Bambu Studio for .3mf, a CAD app for .step, ...)
//   /api/reveal?path=rel -> shows a bundled file or folder in Explorer
//   /api/engine          -> is the Python design engine ready (python + cadquery), for the Build wizard
//   POST /api/engine/setup  creates venv\ next to app\ and installs app\requirements.txt into it
//   POST /api/job        -> runs the Build wizard: python run.py wizard ... in app\ (one job at a time)
//   GET  /api/job        -> {state, log, steps} for the progress view
//   POST /api/kit/save   -> copies the build kit to Documents\Robot Arm Build Kit <date> and shows it in Explorer
// Only files inside app/ can be served or opened. Listens on the loopback address only.
'use strict';
const http = require('http'), fs = require('fs'), path = require('path'), os = require('os'), { spawn, spawnSync } = require('child_process');
const PORT = Number(process.env.ROBOT_ARM_PORT || 8766);
const ROOT = path.join(__dirname, 'app');
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.csv': 'text/csv; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.pdf': 'application/pdf',
  '.stl': 'model/stl', '.obj': 'text/plain; charset=utf-8', '.step': 'application/step', '.dxf': 'application/dxf',
  '.3mf': 'model/3mf', '.ico': 'image/x-icon',
};
function inside(rel) {
  const p = path.resolve(ROOT, decodeURIComponent(rel || '').replace(/^\/+/, ''));
  if (p !== ROOT && !p.startsWith(ROOT + path.sep)) throw new Error('outside app');
  return p;
}
const VENV = path.join(__dirname, 'venv');
const venvPy = () => [path.join(VENV, 'Scripts', 'python.exe'), path.join(VENV, 'bin', 'python')].find(p => fs.existsSync(p));
function basePython() {
  for (const [cmd, pre] of [['py', ['-3']], ['python', []], ['python3', []]]) {
    const r = spawnSync(cmd, [...pre, '-c', 'import sys;print(sys.executable)'], { encoding: 'utf8', windowsHide: true });
    if (r.status === 0 && r.stdout.trim()) return r.stdout.trim();
  }
  return null;
}
function engine() {
  const py = venvPy() || basePython();
  if (!py) return { python: null, ready: false, note: 'Python 3.10+ not found' };
  const r = spawnSync(py, ['-c', 'import cadquery, serial; print("ok")'], { encoding: 'utf8', windowsHide: true, cwd: ROOT });
  return { python: py, venv: !!venvPy(), ready: r.status === 0, note: r.status === 0 ? 'ready' : 'design libraries not installed' };
}
let job = null;   // {state:'running'|'done'|'failed', log, started, kind}
function runJob(kind, steps, cwd) {   // steps: [[cmd, args], ...] run one after another
  if (job && job.state === 'running') throw new Error('a job is already running');
  const J = job = { kind, state: 'running', log: '', started: Date.now() };
  const add = d => { J.log = (J.log + d.toString('utf8')).slice(-400000); };
  const next = (i) => {
    if (i >= steps.length) { J.state = 'done'; return; }
    const [cmd, args] = steps[i];
    const p = spawn(cmd, args, { cwd, windowsHide: true, env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' } });
    p.stdout.on('data', add); p.stderr.on('data', add);
    p.on('error', e => { add(`\n${e.message}\n`); J.state = 'failed'; });
    p.on('close', c => { add(`\n[exit ${c}]\n`); if (c === 0) next(i + 1); else J.state = 'failed'; });
  };
  next(0);
  return J;
}
function readJson(req) {
  return new Promise((ok, bad) => { let b = ''; req.on('data', d => { b += d; if (b.length > 1e5) req.destroy(); }); req.on('end', () => { try { ok(JSON.parse(b || '{}')); } catch (e) { bad(e); } }); });
}
function send(res, code, body, type = 'application/json') {
  res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store' }); res.end(typeof body === 'string' ? body : JSON.stringify(body));
}
http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  try {
    const origin = req.headers.origin;
    if (origin && !/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin)) return send(res, 403, { error: 'forbidden' });
    if (u.pathname === '/api/engine' && req.method === 'GET') return send(res, 200, engine());
    if (u.pathname === '/api/engine/setup' && req.method === 'POST') {
      const py = basePython(); if (!py) return send(res, 400, { error: 'Install Python 3.12 from python.org (tick "Add to PATH"), then try again.' });
      const vpy = process.platform === 'win32' ? path.join(VENV, 'Scripts', 'python.exe') : path.join(VENV, 'bin', 'python');
      return send(res, 200, runJob('setup', [[py, ['-m', 'venv', VENV]], [vpy, ['-m', 'pip', 'install', '--upgrade', 'pip']],
        [vpy, ['-m', 'pip', 'install', '-r', path.join(ROOT, 'requirements.txt')]]], ROOT));
    }
    if (u.pathname === '/api/job' && req.method === 'GET') return send(res, 200, job || { state: 'idle', log: '' });
    if (u.pathname === '/api/job' && req.method === 'POST') {
      const o = await readJson(req), e = engine();
      const num = (v, d, lo, hi) => { const n = Number(v); return Number.isFinite(n) ? Math.min(hi, Math.max(lo, n)) : d; };
      const args = ['run.py', 'wizard', '--payload-lb', String(num(o.payload_lb, 5, 0.5, 10)), '--reach-in', String(num(o.reach_in, 39.4, 12, 48)),
        '--arms', String(Math.round(num(o.arms, 1, 1, 50))), '--bed', /^\d+x\d+x\d+$/.test(o.bed || '') ? o.bed : '256x256x256'];
      if (o.kit_only) args.push('--kit-only');
      if (!e.python) return send(res, 400, { error: e.note });
      if (!e.ready && !o.kit_only) return send(res, 400, { error: 'Set up the design engine first.' });
      return send(res, 200, runJob('wizard', [[e.python, args]], ROOT));
    }
    if (u.pathname === '/api/kit/save' && req.method === 'POST') {
      const src = path.join(ROOT, 'dist', 'kit', 'RobotArm-Build-Kit');
      if (!fs.existsSync(src)) return send(res, 404, { error: 'no build kit yet' });
      const dest = path.join(os.homedir(), 'Documents', `Robot Arm Build Kit ${new Date().toISOString().slice(0, 10)}`);
      fs.cpSync(src, dest, { recursive: true, force: true });
      if (process.platform === 'win32') spawn('explorer.exe', [path.join(dest, 'START-HERE.html')].map(p => '/select,' + p), { detached: true, stdio: 'ignore' }).unref();
      return send(res, 200, { ok: true, path: dest });
    }
    if (u.pathname === '/api/health') return send(res, 200, { app: 'robot-arm', root: ROOT });
    if (u.pathname === '/api/open' || u.pathname === '/api/reveal') {
      const p = inside(u.searchParams.get('path'));
      if (!fs.existsSync(p)) return send(res, 404, { error: 'not found' });
      if (process.platform !== 'win32') return send(res, 501, { error: 'Windows only' });
      const args = u.pathname === '/api/reveal' ? ['/select,', p] : [p];
      spawn('explorer.exe', args, { detached: true, stdio: 'ignore' }).unref();
      return send(res, 200, { ok: true });
    }
    if (u.pathname === '/') { res.writeHead(302, { Location: '/control/index.html' }); return res.end(); }
    let p = inside(u.pathname);
    if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    if (!fs.existsSync(p)) return send(res, 404, 'not found', 'text/plain');
    const type = MIME[path.extname(p).toLowerCase()] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type, 'Content-Length': fs.statSync(p).size, 'Cache-Control': 'no-cache' });
    fs.createReadStream(p).pipe(res);
  } catch (e) { send(res, 400, { error: e.message }); }
}).listen(PORT, '127.0.0.1', () => console.log(`Robot Arm app on http://127.0.0.1:${PORT}/`));
