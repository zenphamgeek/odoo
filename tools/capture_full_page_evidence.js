const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.0
  });

  const page = await context.newPage();

  console.log('Authenticating admin session...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  // 1. Full Form View - Light Mode
  console.log('Capturing Form View (Light Mode)...');
  await page.goto('http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });
  await page.waitForSelector('.o_control_panel', { timeout: 30000 });
  await page.waitForSelector('.o_form_statusbar', { timeout: 30000 });
  await page.waitForTimeout(2000);

  const formLightPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_form_full_light.png';
  await page.screenshot({ path: formLightPath, fullPage: false });
  console.log('Saved:', formLightPath);

  // 2. Full Form View - Dark Mode
  console.log('Capturing Form View (Dark Mode)...');
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  });
  await page.waitForTimeout(1000);

  const formDarkPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_form_full_dark.png';
  await page.screenshot({ path: formDarkPath, fullPage: false });
  console.log('Saved:', formDarkPath);

  // 3. Full List View - Light Mode
  console.log('Capturing List View (Light Mode)...');
  await page.evaluate(() => {
    document.body.classList.remove('o_dark_mode');
    document.documentElement.removeAttribute('data-bs-theme');
    document.documentElement.removeAttribute('data-theme');
  });
  await page.goto('http://localhost:28069/web#model=purchase.order&view_type=list&action=758', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });
  await page.waitForSelector('.o_control_panel', { timeout: 30000 });
  await page.waitForSelector('.o_list_table', { timeout: 30000 });
  await page.waitForTimeout(2000);

  const listLightPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_list_full_light.png';
  await page.screenshot({ path: listLightPath, fullPage: false });
  console.log('Saved:', listLightPath);

  // 4. Full List View - Dark Mode
  console.log('Capturing List View (Dark Mode)...');
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  });
  await page.waitForTimeout(1000);

  const listDarkPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/evidence_list_full_dark.png';
  await page.screenshot({ path: listDarkPath, fullPage: false });
  console.log('Saved:', listDarkPath);

  await browser.close();
  console.log('All full-page evidence screenshots captured successfully.');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
