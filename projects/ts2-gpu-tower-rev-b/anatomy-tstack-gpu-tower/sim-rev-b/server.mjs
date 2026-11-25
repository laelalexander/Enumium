// TS-2 rev B digital twin: static server for the project root (the twin reads ../../prototype/ from sim-rev-b/public).
// Usage: node server.mjs [port]   then open http://127.0.0.1:8791/
import http from 'http'; import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const home = '/' + path.basename(here) + '/public/index.html';
const port = +(process.argv[2] || process.env.PORT || 8791);
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf', '.step': 'application/octet-stream', '.zip': 'application/zip', '.wasm': 'application/wasm' };
http.createServer((req, res) => {
  let u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (u === '/' || u === '') { res.writeHead(302, { Location: home }); return res.end(); }
  const f = path.resolve(root, '.' + u);
  if (!f.startsWith(root)) { res.writeHead(403); return res.end('forbidden'); }
  fs.stat(f, (e, st) => {
    if (e || !st.isFile()) { res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('not found: ' + u); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f).toLowerCase()] || 'application/octet-stream', 'Content-Length': st.size, 'Cache-Control': 'no-cache' });
    fs.createReadStream(f).pipe(res);
  });
}).listen(port, '127.0.0.1', () => console.log('TS-2 rev B twin: http://127.0.0.1:' + port + '/'));
