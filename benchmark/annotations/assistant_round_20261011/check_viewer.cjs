const {chromium} = require('playwright');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

(async () => {
  const browser = await chromium.launch({headless:true,executablePath:'/opt/pw-browsers/chromium',args:['--no-proxy-server']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:960},deviceScaleFactor:1});
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    const url = pathToFileURL(path.join(__dirname,'review.html')).href;
    await page.goto(url, {waitUntil:'load'});
    const events = JSON.parse(fs.readFileSync(path.join(__dirname,'decisions.json'),'utf8'));
    async function ready(id) {
      await page.waitForFunction(eventId => document.getElementById('event-title').textContent===eventId && document.getElementById('map-image').complete && document.getElementById('map-image').naturalWidth>0, id);
      await page.locator('#map-image').evaluate(img=>img.decode());
      await page.waitForFunction(() => document.getElementById('overlay').width === document.getElementById('map-image').naturalWidth);
    }
    for (const event of events) {
      await page.selectOption('#event-select',event.event_id);
      await ready(event.event_id);
      const sample = await page.evaluate(() => {
        const canvas=document.getElementById('overlay'), p=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
        let nonzero=0;for(let i=3;i<p.length;i+=4)if(p[i])nonzero++;
        const img=document.getElementById('map-image'),small=document.createElement('canvas');small.width=32;small.height=32;
        const c=small.getContext('2d');c.drawImage(img,0,0,32,32);const px=c.getImageData(0,0,32,32).data;
        const colors=new Set();for(let i=0;i<px.length;i+=4)colors.add(`${px[i]},${px[i+1]},${px[i+2]}`);
        return {nonzero,colors:colors.size,width:img.naturalWidth,height:img.naturalHeight};
      });
      assert(sample.colors>30, `${event.event_id}: blank map`);
      assert.equal(sample.nonzero>0,!!event.geometry, `${event.event_id}: overlay state`);
    }
    await page.selectOption('#event-select','Z0004'); await ready('Z0004');
    await page.click('#focus');
    await page.screenshot({path:'/private/tmp/annotation-review-desktop.png',fullPage:true});
    await page.click('#show-overlay');
    assert.equal(await page.locator('#overlay').evaluate(c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)),false);
    await page.click('#show-overlay');
    await page.click('#native'); assert.equal(await page.locator('#zoom-value').innerText(),'100%');
    await page.click('#reference-mode');
    await page.waitForFunction(()=>document.getElementById('map-image').naturalWidth===2177);
    await ready('Z0004');
    assert.equal(await page.locator('#focus').isDisabled(),true);
    assert.equal(await page.locator('#overlay').evaluate(c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)),false);
    await page.click('#annotation-mode');
    await page.waitForFunction(()=>document.getElementById('map-image').naturalWidth===1538);
    await page.selectOption('#status-filter','source_conflict');
    assert.equal(await page.locator('#event-select option').count(),0);  // 2026-10-21: the three source conflicts were rewritten from source text
    await page.selectOption('#map-filter','benchmark/atlas/assets/2ae3fca4eb15dced41f82401.png');
    assert(await page.locator('#empty').isVisible()); assert(await page.locator('#next').isDisabled());
    await page.selectOption('#status-filter','proposed'); assert.equal(await page.locator('#event-select option').count(),4);
    await ready('Z0004');
    await page.setViewportSize({width:390,height:844});
    await page.click('#fit');
    await page.screenshot({path:'/private/tmp/annotation-review-mobile.png',fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'mobile horizontal overflow');
    const controls=await page.locator('.toolbar').first().boundingBox();const map=await page.locator('#viewport').boundingBox();
    assert(controls.y+controls.height<=map.y+1,'toolbar overlaps map');
    await page.locator('#viewport').hover(); await page.mouse.wheel(0,-300);
    await page.waitForTimeout(100);
    const zoomBefore=await page.locator('#zoom-value').innerText();assert.notEqual(zoomBefore,'0%');
    assert.deepEqual(errors,[]);
    const result = {events_checked:events.length,desktop:'1440x960',mobile:'390x844',overlay_checks:'passed',map_pixels:'nonblank',filter_reference_toggle:'passed',horizontal_overflow:false,page_errors:errors,decisions_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'decisions.json'))).digest('hex'),screenshots:['/private/tmp/annotation-review-desktop.png','/private/tmp/annotation-review-mobile.png']};
    fs.writeFileSync(path.join(__dirname,'browser_validation.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
