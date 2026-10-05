const { chromium } = require('playwright');

async function testRoute(urlPath) {
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
  page.on('console', msg => {
    if (msg.type() === 'error') logs.push(`[CONSOLE] ${msg.text()}`);
  });
  page.on('pageerror', err => logs.push(`[PAGEERROR] ${err.message}`));

  console.log(`\n=================== Testing ${urlPath} ===================`);
  await page.goto(`${baseUrl}${urlPath}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  const errDialog = await page.$('.o_error_dialog');
  if (errDialog) {
    const text = await page.$eval('.o_error_dialog', el => el.innerText);
    console.log(`[FAILED] Error dialog found on ${urlPath}:\n`, text);
  } else {
    console.log(`[PASS] ${urlPath} loaded cleanly!`);
  }
  if (logs.length > 0) {
    console.log('Console/Page Errors:', logs);
  }
  await browser.close();
}

async function main() {
  const routes = [
    '/insilos/unified-operations',
    '/insilos/logistics-onboarding',
    '/insilos/chemical-onboarding',
    '/insilos/hs-onboarding',
    '/insilos/hse-onboarding',
    '/insilos/esg-onboarding',
    '/insilos/pubsub-onboarding',
    '/insilos/logistics-overview'
  ];
  for (const r of routes) {
    await testRoute(r);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
