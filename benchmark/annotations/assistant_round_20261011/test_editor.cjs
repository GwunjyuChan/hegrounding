// Browser integration tests use an isolated journal, never the real reviews.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const http = require('node:http');
const {chromium} = require('playwright');

async function main() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'he-review-editor-'));
  const fixture = process.env.REVIEW_TEST_DATA || __dirname;
  const sourceNames = ['annotations.jsonl','manifest.json','human_reviews.jsonl'];
  const before = Object.fromEntries(sourceNames.map(n=>[n,fs.readFileSync(path.join(__dirname,n))]));
  for(const n of [...sourceNames,'review.html'])fs.copyFileSync(path.join(fixture,n),path.join(root,n));
  if(fs.existsSync(path.join(fixture,'images')))fs.cpSync(path.join(fixture,'images'),path.join(root,'images'),{recursive:true});
  const python = path.resolve(__dirname,'../../../.venv/bin/python');
  const server = spawn(python,[path.join(__dirname,'serve_reviews.py'),'--root',root,'--port','0'],{env:{...process.env,MPLCONFIGDIR:root}});
  let browser, proxy;
  try {
    let url = await new Promise((resolve,reject)=>{
      let text='';const timer=setTimeout(()=>reject(Error('Server start timeout')),15000);
      server.stdout.on('data',buf=>{text+=buf;const match=text.match(/http:\/\/127\.0\.0\.1:\d+\/review.html/);if(match){clearTimeout(timer);resolve(match[0]);}});
      server.on('error',reject);server.on('exit',code=>{if(code){clearTimeout(timer);reject(Error(`Server exit ${code}`));}});
    });
    if(process.env.REVIEW_TEST_PREFIX){
      const backend = new URL(url);
      // A disposable proxy exercises subpath routing without accessing the real website.
      proxy=http.createServer((req,res)=>{
        if(!req.url.startsWith('/review/')){res.writeHead(404);res.end();return;}
        const headers={...req.headers,host:backend.host};
        if(headers.origin)headers.origin=backend.origin;
        const upstream=http.request({hostname:backend.hostname,port:backend.port,path:req.url.slice('/review'.length),method:req.method,headers},reply=>{
          res.writeHead(reply.statusCode,reply.headers);reply.pipe(res);
        });
        upstream.on('error',()=>{res.writeHead(502);res.end();});req.pipe(upstream);
      });
      await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));
      url=`http://127.0.0.1:${proxy.address().port}/review/review.html`;
    }
    const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    browser=await chromium.launch({headless:true,executablePath:'/opt/pw-browsers/chromium',args:['--no-proxy-server']});
    const context=await browser.newContext({viewport:{width:1440,height:1050}});
    await context.addInitScript(()=>{try{localStorage.setItem('he-language','en');}catch{}});
    const errors=[];
    context.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));
    const p=await context.newPage();
    async function open(page,id){await page.goto(url+'#'+id);await page.waitForFunction(()=>currentImage && !document.querySelector('[data-tool=edit]').disabled);}
    async function g(page){return page.evaluate(()=>window.reviewFeature.geometry());}
    async function screen(page,point){return page.evaluate(point=>{const b=document.getElementById('viewport').getBoundingClientRect();return [b.left+tx+point[0]*scale,b.top+ty+point[1]*scale];},point);}
    async function clickMap(page,x,y){const point=await page.evaluate(([x,y])=>[current.annotation_image.width*x,current.annotation_image.height*y],[x,y]);const s=await screen(page,point);await page.mouse.click(...s);}
    async function save(page,decision='modified_accepted'){
      await page.locator('#reviewer').fill('Browser integration test');
      await page.locator('#review-notes').fill('Verified against source map in temporary test copy.');
      await page.locator(`[data-decision=${decision}]`).click();
      const response=page.waitForResponse(r=>r.url().endsWith('/api/reviews')&&r.request().method()==='POST');
      await page.locator('#review-save').click();return response;
    }
    await open(p,'MF0017');
    const original=await p.evaluate(()=>JSON.parse(JSON.stringify(current.geometry)));
    await p.locator('[data-tool=edit]').click();
    await p.locator('#focus').click();
    let s=await screen(p,original.coordinates[0]);
    await p.mouse.move(...s);await p.mouse.down();await p.mouse.move(s[0]+20,s[1]+15,{steps:5});await p.mouse.up();
    const moved=await g(p);assert.notDeepEqual(moved,original);
    assert.deepEqual(await p.evaluate(()=>current.geometry),original);
    await p.locator('#undo-geometry').click();assert.deepEqual(await g(p),original);
    await p.locator('#redo-geometry').click();assert.deepEqual(await g(p),moved);
    const edge=moved.coordinates[1].map((v,i)=>(v+moved.coordinates[2][i])/2);
    s=await screen(p,edge);await p.mouse.click(...s);
    assert.equal((await g(p)).coordinates.length,moved.coordinates.length+1);
    await p.locator('#delete-vertex').click();assert.equal((await g(p)).coordinates.length,moved.coordinates.length);
    await p.locator('#clear-geometry').click();assert.equal(await g(p),null);
    assert.equal(await p.evaluate(()=>window.geometryEditor.geometry()),null);
    await p.locator('#undo-geometry').click();assert.deepEqual(await g(p),moved);
    await p.locator('#restore-candidate').click();assert.deepEqual(await g(p),original);
    await p.locator('#undo-geometry').click();assert.deepEqual(await g(p),moved);
    assert.equal((await save(p)).status(),200);
    await p.waitForFunction(()=>document.getElementById('review-message').textContent.includes('Saved to disk'));
    await p.reload();await p.waitForFunction(()=>!document.querySelector('[data-tool=edit]').disabled);
    assert.deepEqual(await g(p),moved);
    assert.equal(await p.locator('[data-decision=modified_accepted]').getAttribute('aria-pressed'),'true');
    console.log('Vertex drag/insert/delete, undo/redo, clear/restore and persistent revision: passed');

    const second=await context.newPage();await open(second,'MF0017');
    await p.locator('#review-notes').fill('Second revision, same corrected geometry.');
    let response=p.waitForResponse(r=>r.url().endsWith('/api/reviews')&&r.request().method()==='POST');
    await p.locator('#review-save').click();assert.equal((await response).status(),200);
    await second.locator('#review-notes').fill('Stale tab must not overwrite.');
    response=second.waitForResponse(r=>r.url().endsWith('/api/reviews')&&r.request().method()==='POST');
    await second.locator('#review-save').click();assert.equal((await response).status(),409);
    assert.equal(await second.locator('#review-notes').inputValue(),'Stale tab must not overwrite.');
    await second.close({runBeforeUnload:false});
    console.log('Two-tab stale-save protection: passed');

    await p.selectOption('#event-select','MF0013');await p.waitForFunction(()=>currentImage!==null);
    await p.locator('#fit').click();await p.locator('[data-tool=point]').click();await clickMap(p,.45,.45);
    assert.equal((await g(p)).type,'point');
    await p.selectOption('#event-select','MF0014');await p.selectOption('#event-select','MF0013');
    assert.equal((await g(p)).type,'point');
    await p.waitForFunction(()=>currentImage!==null);await p.locator('#fit').click();
    await p.locator('[data-tool=line]').click();await clickMap(p,.3,.3);await clickMap(p,.6,.5);
    await p.locator('#finish-geometry').click();assert.equal((await g(p)).type,'line');
    await p.locator('[data-tool=polygon]').click();
    for(const [x,y] of [[.3,.3],[.6,.6],[.3,.6],[.6,.3]])await clickMap(p,x,y);
    await p.locator('#finish-geometry').click();assert.equal((await save(p)).status(),400);
    await p.locator('#undo-geometry').click();
    assert.equal((await g(p)).coordinates.length,3);
    assert.equal((await save(p)).status(),200);
    await p.waitForFunction(()=>document.getElementById('review-message').textContent.includes('Saved to disk'));
    await p.locator('#reference-mode').click();
    assert.equal(await p.locator('[data-tool=edit]').isDisabled(),true);
    await p.locator('#annotation-mode').click();
    await p.waitForFunction(()=>!document.querySelector('[data-tool=edit]').disabled);
    console.log('New point/line/polygon, navigation drafts, invalid polygon and reference guard: passed');

    // Rectangle tool: drag out a box, corners keep it a box, a polygon converts to its horizontal box.
    async function mapPoint(page,x,y){const point=await page.evaluate(([x,y])=>[current.annotation_image.width*x,current.annotation_image.height*y],[x,y]);return screen(page,point);}
    async function dragMap(page,from,to){const a=await mapPoint(page,...from),b=await mapPoint(page,...to);await page.mouse.move(...a);await page.mouse.down();await page.mouse.move(...b,{steps:6});await page.mouse.up();}
    const isBox=c=>c.length===4&&c.every((a,i)=>{const b=c[(i+1)%4];return (a[0]===b[0])!==(a[1]===b[1]);});
    await p.locator('#fit').click();await p.locator('#clear-geometry').click();
    await p.locator('[data-tool=rect]').click();await clickMap(p,.4,.4);
    assert.equal(await g(p),null,'a click without a drag draws no box');
    await dragMap(p,[.5,.4],[.2,.2]);
    let rect=await g(p);assert.equal(rect.type,'polygon');assert.ok(isBox(rect.coordinates));
    assert.equal(await p.locator('#editor-state').innerText(),'box');
    assert.equal(await p.locator('[data-decision=modified_accepted]').getAttribute('aria-pressed'),'true','a drawn shape selects accept-with-edits');
    assert.equal(await p.locator('#to-box').isDisabled(),true);
    const corner=rect.coordinates[2];s=await screen(p,corner);
    await p.mouse.move(...s);await p.mouse.down();await p.mouse.move(s[0]+25,s[1]+18,{steps:5});await p.mouse.up();
    rect=await g(p);assert.ok(isBox(rect.coordinates),'dragging a corner keeps a box');assert.ok(rect.coordinates[2][0]>corner[0]);
    const edgeMid=rect.coordinates[0].map((v,i)=>(v+rect.coordinates[1][i])/2);s=await screen(p,edgeMid);await p.mouse.click(...s);
    assert.equal((await g(p)).coordinates.length,4,'clicking a box edge adds no vertex');
    await p.locator('[data-tool=polygon]').click();
    for(const [x,y] of [[.3,.3],[.5,.35],[.35,.55]])await clickMap(p,x,y);
    await p.locator('#finish-geometry').click();
    const tri=await g(p);assert.equal(tri.coordinates.length,3);
    await p.locator('#to-box').click();
    const boxed=await g(p),xs=tri.coordinates.map(v=>v[0]),ys=tri.coordinates.map(v=>v[1]);
    assert.ok(isBox(boxed.coordinates));
    assert.deepEqual(boxed.coordinates[0],[Math.min(...xs),Math.min(...ys)]);assert.deepEqual(boxed.coordinates[2],[Math.max(...xs),Math.max(...ys)]);
    assert.equal((await save(p)).status(),200);
    await p.waitForFunction(()=>document.getElementById('review-message').textContent.includes('Saved to disk'));
    await p.locator('#undo-geometry').click();assert.equal((await g(p)).coordinates.length,3);
    console.log('Rectangle drawing, box corners, convert-to-box and auto accept-with-edits: passed');

    const mobile=await context.newPage();await mobile.setViewportSize({width:390,height:844});await open(mobile,'Z0003');
    assert.equal(await g(mobile),null);
    await mobile.locator('[data-tool=point]').click();await clickMap(mobile,.5,.5);
    assert.equal((await save(mobile)).status(),200);
    await mobile.waitForFunction(()=>document.getElementById('review-message').textContent.includes('Saved to disk'));
    await mobile.evaluate(()=>scrollTo(0,0));
    assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await mobile.screenshot({path:path.join(root,'mobile.png'),fullPage:true});
    await p.selectOption('#event-select','MF0017');await p.waitForFunction(()=>currentImage!==null);await p.locator('[data-tool=edit]').click();
    await p.screenshot({path:path.join(root,'desktop.png'),fullPage:true});
    assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    const pixels=await p.evaluate(()=>{const a=document.getElementById('overlay').getContext('2d').getImageData(0,0,currentImage.width,currentImage.height).data;let n=0;for(let i=3;i<a.length;i+=4)if(a[i])n++;return n;});
    assert.ok(pixels>100,'Nonblank overlay');
    const offline=await context.newPage();await offline.goto('file://'+path.join(root,'review.html'));
    assert.equal(await offline.locator('[data-tool=edit]').isDisabled(),true);
    assert.deepEqual(errors,[]);
    for(const n of sourceNames)assert.deepEqual(fs.readFileSync(path.join(__dirname,n)),before[n]);
    console.log('Mobile new geometry, layers, read-only file, real data preservation: passed');
    console.log(JSON.stringify({screenshots:root,errors}));
  } finally {
    if(browser)await browser.close();if(proxy)await new Promise(resolve=>proxy.close(resolve));server.kill('SIGTERM');
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
