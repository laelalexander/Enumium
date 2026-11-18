const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:3456,height:2304}});
for(const f of process.argv.slice(2)){await p.setContent(fs.readFileSync(f,'utf8'));await p.screenshot({path:f.replace(/\.svg$/,'.png').replace(/.*\//,'/tmp/claude-0/-home-claude/05580e48-d4e0-5847-b4dd-c4312a2f1ccb/scratchpad/')});}
await b.close();})();
