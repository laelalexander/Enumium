// Render every step in steps.json with render.html in headless Chromium; writes step_NN.png and balloons.json.
// Usage: node shoot.mjs <base-url-of-repo-root> <out-dir>
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
import fs from 'fs';
import path from 'path';
const [base, out] = process.argv.slice(2);
const steps = JSON.parse(fs.readFileSync(path.join(out, 'steps.json'), 'utf8'));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1800, height: 1300 }, deviceScaleFactor: 1 });
page.on('console', (m) => { if (m.type() === 'error') console.log('page:', m.text()); });
await page.goto(base + 'prototype/drawings/asm/render.html');
await page.waitForFunction(() => window.ready === true, null, { timeout: 180000 });
const balloons = {};
for (const s of steps) {
  balloons[s.id] = await page.evaluate((cfg) => window.render(cfg), s.view);
  await page.waitForTimeout(150);
  await page.screenshot({ path: path.join(out, `step_${s.id}.png`) });
  console.log('rendered', s.id);
}
fs.writeFileSync(path.join(out, 'balloons.json'), JSON.stringify(balloons, null, 1));
await browser.close();
