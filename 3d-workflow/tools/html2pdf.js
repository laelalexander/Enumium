// node tools/html2pdf.js in.html out.pdf [portrait|landscape]   (needs: npm i playwright, npx playwright install chromium)
const { chromium } = require('playwright'); const path = require('path'); const url = require('url');
(async () => {
  const [inp, out, orient] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(url.pathToFileURL(path.resolve(inp)).href, { waitUntil: 'load' });
  await p.pdf({ path: out, format: 'A4', landscape: orient === 'landscape', printBackground: true,
                margin: { top: '12mm', bottom: '12mm', left: '12mm', right: '12mm' } });
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
