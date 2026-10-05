const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const baseUrl = 'http://localhost:18069';

  await page.request.post(`${baseUrl}/web/session/authenticate`, {
    data: { jsonrpc: '2.0', params: { db: 'insilos20_dev', login: 'admin', password: 'admin' } }
  });

  const logs = [];
  page.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
  page.on('pageerror', e => logs.push(e.message));

  console.log('Navigating to /insilos/logistics-overview...');
  await page.goto(`${baseUrl}/insilos/logistics-overview`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  const errDialog = await page.$('.o_error_dialog');
  if (errDialog) {
    const text = await page.$eval('.o_error_dialog', el => el.innerText);
    console.log('[FAILED] Still has error dialog:\n', text);
  } else {
    console.log('[PASS] SUCCESS! No error dialog on /insilos/logistics-overview!');
  }
  if (logs.length) console.log('Console/Page Errors:', logs);
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/logistics_overview_verified.png' });
  await browser.close();
})();
