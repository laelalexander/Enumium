// node tools/guide_pictures.js <out dir> [twin url]
// Renders one picture per assembly step from the 3D twin (python run.py guide starts the twin server for you).
// Needs: npm i playwright && npx playwright install chromium.  THREE_DIR=<path to three package> serves three.js offline.
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => {
  const OUT = process.argv[2], URL = process.argv[3] || 'http://127.0.0.1:8765/control/index.html';
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 2 });
  if (process.env.THREE_DIR) await p.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r => r.fulfill({ status: 200, contentType: 'text/javascript',
    body: fs.readFileSync(path.join(process.env.THREE_DIR, r.request().url().split('three@0.160.0/')[1])) }));
  p.on('pageerror', e => console.log('page error:', e.message));
  await p.goto(URL); await p.waitForFunction(() => window.twin && window.twin.twinBuild, null, { timeout: 60000 }); await p.waitForTimeout(2000);
  await p.addStyleTag({ content: '#hud,#viewbar{display:none!important}' });
  const vp = await p.$('#viewport');
  const steps = await p.evaluate(() => window.twin.twinBuild.steps.map(s => s.id));
  await p.evaluate(() => document.querySelector('[data-view=iso]').click()); await p.waitForTimeout(1500);
  await vp.screenshot({ path: path.join(OUT, 'step-00-overview.png') });
  for (let i = 0; i < steps.length; i++) {
    await p.evaluate(i => { const s = document.querySelector('#buildStep'); s.value = i; s.onchange(); }, i); await p.waitForTimeout(2500);
    const f = path.join(OUT, `step-${String(i + 1).padStart(2, '0')}-${steps[i]}.png`); await vp.screenshot({ path: f }); console.log(f);
  }
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
