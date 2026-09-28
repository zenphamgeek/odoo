const { chromium } = require('playwright');

async function testApp(name, path) {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (!txt.includes('favicon.ico')) {
        console.error(`  [CONSOLE ERROR]:`, txt);
        errors.push({ type: 'console', text: txt });
      }
    }
  });

  page.on('pageerror', err => {
    console.error(`  [PAGE ERROR]:`, err.stack || err.message);
    errors.push({ type: 'pageerror', text: err.stack || err.message });
  });

  page.on('response', resp => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400 && (url.endsWith('.js') || url.endsWith('.css') || url.includes('/web/assets/'))) {
      const err = `HTTP ${status} on asset: ${url}`;
      console.error(`  [ASSET ERROR]:`, err);
      errors.push({ type: 'asset', text: err });
    }
  });

  console.log(`Authenticating for ${name}...`);
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  console.log(`Navigating to ${path}...`);
  try {
    await page.goto(`http://localhost:28069${path}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  } catch (e) {
    console.log(`Navigation caught: ${e.message}`);
  }

  await page.waitForTimeout(5000);
  console.log(`URL after navigation:`, page.url());
  console.log(`Errors encountered in ${name}: ${errors.length}`);
  for (const err of errors) {
    console.log(' -', err.type, ':', err.text.slice(0, 200));
  }

  await browser.close();
}

async function run() {
  console.log('--- TESTING KITCHEN DISPLAY ---');
  await testApp('Kitchen Display', '/web#action=4757');
  console.log('\n--- TESTING ACCOUNTING ---');
  await testApp('Accounting', '/web#action=accounting');
}

run();
