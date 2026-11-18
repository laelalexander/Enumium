const {chromium}=require('playwright'); const fs=require('fs');
const views = JSON.parse(fs.readFileSync(process.argv[2])); const port = process.argv[3]||8791;
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
for (const v of views){ const p=await b.newPage({viewport:{width:v.w||1600,height:v.h||1200}}); p.on('console',m=>console.log('C',m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(`http://localhost:${port}/render/render.html#`+encodeURIComponent(JSON.stringify(v))); await p.waitForFunction(()=>window.DONE,null,{timeout:300000});
 await p.screenshot({path:v.out}); console.log('wrote',v.out); await p.close(); }
await b.close();})();
