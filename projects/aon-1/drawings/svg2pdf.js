// SVG sheets (ARCH D 36 x 24 in) -> one PDF each, same name. Usage: node svg2pdf.js a.svg b.svg ...
const {chromium} = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  for (const f of process.argv.slice(2)) {
    const svg = fs.readFileSync(f, 'utf8');
    await p.setContent(`<html><head><style>@page{size:36in 24in;margin:0}html,body{margin:0}svg{width:36in;height:24in;display:block}</style></head><body>${svg}</body></html>`);
    await p.pdf({path: f.replace(/\.svg$/, '.pdf'), width: '36in', height: '24in', printBackground: true, pageRanges: '1'});
  }
  await b.close(); })();
