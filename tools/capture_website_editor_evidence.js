const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1600, height: 960 } });
  const page = await context.newPage();

  console.log('Logging in...');
  await page.goto('http://localhost:28069/web/login', { waitUntil: 'domcontentloaded' });
  await page.fill('input[name="login"]', 'admin');
  await page.fill('input[name="password"]', 'admin');
  await page.click('form.oe_login_form button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'domcontentloaded' });

  console.log('Navigating to editor wrapper: http://localhost:28069/@/ ...');
  await page.goto('http://localhost:28069/@/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(4000);

  console.log('Clicking Edit button: button.o-website-btn-custo-primary ...');
  await page.click('button.o-website-btn-custo-primary');
  
  // Wait for the snippet panel / editor toolbar to appear
  console.log('Waiting for editor toolbar and snippet blocks...');
  await page.waitForTimeout(5000);

  // Take screenshot of editor with snippet panel open
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_website_builder_light.png' });
  console.log('Captured evidence_website_builder_light.png');

  // Let's see if we can find custom snippets tab or scroll the snippet panel
  const snippetList = await page.evaluate(() => {
    const thumbs = Array.from(document.querySelectorAll('img[src*="snippets_thumbs"], .o_we_snippet_area, [data-snippet]'));
    return thumbs.map(t => t.src || t.getAttribute('data-snippet'));
  });
  console.log('Snippet elements found in DOM:', snippetList.length);

  // Dark mode
  await page.evaluate(() => document.body.classList.add('o_dark_mode'));
  // also add to iframe if present
  for (const f of page.frames()) {
    try {
      await f.evaluate(() => document.body.classList.add('o_dark_mode'));
    } catch (e) {}
  }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_website_builder_dark.png' });
  console.log('Captured evidence_website_builder_dark.png');

  await browser.close();
  console.log('Finished capturing website builder evidence.');
})();
