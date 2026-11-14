// Robot Arm desktop app server. No npm dependencies: node server.js
// Serves the bundled app (the app/ folder next to this file) on http://127.0.0.1:8766 and answers
//   /api/health          -> {"app":"robot-arm"}  (the UI uses this to show the desktop-only buttons)
//   /api/open?path=rel   -> opens a bundled file with its Windows app (Bambu Studio for .3mf, a CAD app for .step, ...)
//   /api/reveal?path=rel -> shows a bundled file or folder in Explorer
// Only files inside app/ can be served or opened. Listens on the loopback address only.
'use strict';
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
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
function send(res, code, body, type = 'application/json') {
  res.writeHead(code, { 'Content-Type': type, 'Cache-Control': 'no-store' }); res.end(typeof body === 'string' ? body : JSON.stringify(body));
}
http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x');
  try {
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
