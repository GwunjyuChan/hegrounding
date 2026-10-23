const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const errors = [];
  const checks = [];
  try {
    for (const [name, viewport] of Object.entries({ desktop: { width: 1440, height: 1000 }, mobile: { width: 390, height: 844 } })) {
      const page = await browser.newPage({ viewport });
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(pathToFileURL(path.join(__dirname, 'review/comparison.html')).href);
      await page.waitForFunction(() => [...document.querySelectorAll('canvas')].some(c => c.width > 0));
      const data = await page.locator('#data').textContent();
      assert.deepEqual(Object.keys(JSON.parse(data).rows), ['qwen_instruct', 'qwen_thinking', 'gpt6_astra']);
      for (let i = 1; i <= 10; i++) {
        const id = `Z${String(i).padStart(4, '0')}`;
        await page.selectOption('#event', id);
        assert.match(await page.locator('#question').textContent(), new RegExp(`^${id}`));
      }
      await page.selectOption('#event', 'Z0004');
      for (const model of ['qwen_instruct', 'qwen_thinking', 'gpt6_astra', 'all']) {
        await page.selectOption('#view', model);
        await page.locator('#native').click();
        await page.waitForTimeout(120);
        const painted = await page.locator('.panel:not([hidden]) canvas').evaluateAll(canvases => canvases.map(c => {
          const pixels = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
          const colors = new Set();
          for (let j = 0; j < pixels.length; j += 4 * 113) {
            colors.add(`${pixels[j]},${pixels[j + 1]},${pixels[j + 2]}`);
          }
          return colors.size;
        }));
        assert(painted.every(count => count > 100), `${name}/${model}: blank map`);
      }
      if (name === 'mobile') await page.selectOption('#view', 'qwen_thinking');
      await page.locator('#focus').click();
      await page.waitForTimeout(120);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}: horizontal overflow`);
      const shot = `/private/tmp/zurich-thinking-${name}.png`;
      await page.screenshot({ path: shot, fullPage: true });
      checks.push({ viewport: name, allTenQuestions: true, allModelViews: true, nonblankMaps: true, horizontalOverflow: false, screenshot: shot });
      await page.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(__dirname, 'review/browser_validation.json'), JSON.stringify({ checks, errors }, null, 2));
    console.log(JSON.stringify({ checks, errors }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
