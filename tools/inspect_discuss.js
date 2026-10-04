const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  await page.goto('http://localhost:28069/odoo/discuss');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForSelector('.o-mail-Discuss', { timeout: 15000 });
  await page.waitForTimeout(2000);

  // Click on the conversation item for InsilosBot
  const botConv = await page.locator('text=InsilosBot').first();
  if (botConv) {
    console.log('Found InsilosBot conversation, clicking...');
    await botConv.click();
    await page.waitForTimeout(1500);
  }

  const composer = await page.$('.o-mail-Composer');
  console.log('Composer found:', !!composer);

  const textarea = await page.$('.o-mail-Composer textarea.o-mail-Composer-input');
  console.log('Textarea found:', !!textarea);

  if (textarea) {
    await textarea.focus();
    await page.waitForTimeout(800);

    const inputContainer = await page.$('.o-mail-Composer-inputContainer');
    const containerStyles = await inputContainer.evaluate(el => {
      const cs = window.getComputedStyle(el);
      return {
        border: cs.border,
        borderColor: cs.borderColor,
        outline: cs.outline,
        boxShadow: cs.boxShadow,
        borderRadius: cs.borderRadius
      };
    });
    console.log('Container focused styles:', JSON.stringify(containerStyles, null, 2));

    const textareaStyles = await textarea.evaluate(el => {
      const cs = window.getComputedStyle(el);
      return {
        border: cs.border,
        borderColor: cs.borderColor,
        outline: cs.outline,
        boxShadow: cs.boxShadow,
        borderRadius: cs.borderRadius
      };
    });
    console.log('Textarea focused styles:', JSON.stringify(textareaStyles, null, 2));

    // Also check any active elements or parent elements with borders
    const debugTree = await inputContainer.evaluate(el => {
      const results = [];
      let cur = el;
      while (cur && cur !== document.body) {
        const cs = window.getComputedStyle(cur);
        results.push({
          tag: cur.tagName,
          class: cur.className,
          border: cs.border,
          borderColor: cs.borderColor,
          outline: cs.outline,
          boxShadow: cs.boxShadow
        });
        cur = cur.parentElement;
      }
      return results;
    });
    console.log('Hierarchy styles:', JSON.stringify(debugTree, null, 2));

    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/discuss_focused_before.png' });
    console.log('Saved discuss_focused_before.png');
  }

  if (textarea) {
    await textarea.focus();
    await page.waitForTimeout(500);

    const inputContainer = await page.$('.o-mail-Composer-inputContainer');
    const containerStyles = await inputContainer.evaluate(el => {
      const cs = window.getComputedStyle(el);
      return {
        border: cs.border,
        borderColor: cs.borderColor,
        outline: cs.outline,
        boxShadow: cs.boxShadow,
        borderRadius: cs.borderRadius
      };
    });
    console.log('Container focused styles:', JSON.stringify(containerStyles, null, 2));

    const textareaStyles = await textarea.evaluate(el => {
      const cs = window.getComputedStyle(el);
      return {
        border: cs.border,
        borderColor: cs.borderColor,
        outline: cs.outline,
        boxShadow: cs.boxShadow,
        borderRadius: cs.borderRadius
      };
    });
    console.log('Textarea focused styles:', JSON.stringify(textareaStyles, null, 2));

    // Also check any active elements or parent elements with borders
    const debugTree = await inputContainer.evaluate(el => {
      const results = [];
      let cur = el;
      while (cur && cur !== document.body) {
        const cs = window.getComputedStyle(cur);
        results.push({
          tag: cur.tagName,
          class: cur.className,
          border: cs.border,
          outline: cs.outline,
          boxShadow: cs.boxShadow
        });
        cur = cur.parentElement;
      }
      return results;
    });
    console.log('Hierarchy styles:', JSON.stringify(debugTree, null, 2));

    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/discuss_focused_before.png' });
  }

  await browser.close();
})();
