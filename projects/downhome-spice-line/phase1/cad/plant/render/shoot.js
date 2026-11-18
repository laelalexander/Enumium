const {chromium}=require('playwright'); const fs=require('fs');
const views = JSON.parse(fs.readFileSync(process.argv[2]));
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
for (const v of views){ const p=await b.newPage({viewport:{width:v.w||3000,height:v.h||1900}}); p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://localhost:8765/render.html#'+encodeURIComponent(JSON.stringify(v))); await p.waitForFunction(()=>window.DONE,null,{timeout:300000});
 const shot = await p.evaluate(()=>{const a=document.querySelectorAll('canvas'); const o=document.createElement('canvas'); o.width=a[0].width;o.height=a[0].height; const c=o.getContext('2d'); c.drawImage(a[0],0,0); c.drawImage(a[1],0,0); return o.toDataURL('image/png');});
 fs.writeFileSync(v.out, Buffer.from(shot.split(',')[1],'base64')); console.log('wrote',v.out); await p.close(); }
await b.close();})();
