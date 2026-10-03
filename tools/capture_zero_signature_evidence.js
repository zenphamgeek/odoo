const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });
  
  // Login
  await page.goto('http://localhost:28069/web/login', { waitUntil: 'domcontentloaded' });
  await page.fill('input[name="login"]', 'admin');
  await page.fill('input[name="password"]', 'admin');
  await page.click('form.oe_login_form button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'domcontentloaded' });
  
  console.log('Logged in successfully');
  
  // 1. List View
  await page.goto('http://localhost:28069/odoo/action-338', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  
  // Focus search to test border
  const searchInput = await page.locator('.o_searchview_input, input[placeholder*="Search"]').first();
  if (await searchInput.count() > 0) {
    await searchInput.focus();
    await page.waitForTimeout(500);
  }
  
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_list_full_light.png' });
  console.log('Captured evidence_list_full_light.png');
  
  // Dark mode list view
  await page.evaluate(() => document.body.classList.add('o_dark_mode'));
  await page.waitForTimeout(500);
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_list_full_dark.png' });
  console.log('Captured evidence_list_full_dark.png');
  
  // Remove dark mode
  await page.evaluate(() => document.body.classList.remove('o_dark_mode'));
  
  // 2. Form View
  await page.goto('http://localhost:28069/odoo/action-338/1', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3500);
  
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_form_full_light.png' });
  console.log('Captured evidence_form_full_light.png');
  
  // Dark mode form view
  await page.evaluate(() => document.body.classList.add('o_dark_mode'));
  await page.waitForTimeout(500);
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_form_full_dark.png' });
  console.log('Captured evidence_form_full_dark.png');
  
  await browser.close();
  console.log('All evidence captured successfully');
})();
