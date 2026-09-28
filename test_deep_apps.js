const { chromium } = require('playwright');

const APPS = [
  { name: 'CRM', path: '/insilos/crm' },
  { name: 'Sales', path: '/insilos/sales' },
  { name: 'Accounting', path: '/insilos/accounting' },
  { name: 'Subscriptions', path: '/insilos/subscriptions' },
  { name: 'Project', path: '/insilos/project' },
  { name: 'Inventory', path: '/insilos/inventory' },
  { name: 'Purchase', path: '/insilos/purchase' },
  { name: 'Employees', path: '/insilos/employees' },
  { name: 'Helpdesk', path: '/insilos/helpdesk' },
  { name: 'Documents', path: '/insilos/documents' },
  { name: 'Knowledge', path: '/insilos/knowledge' },
  { name: 'Planning', path: '/insilos/planning' },
  { name: 'Timesheets', path: '/insilos/timesheet' },
  { name: 'WhatsApp', path: '/insilos/whatsapp' },
  { name: 'Barcode', path: '/insilos/barcode' },
];

async function run() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  const failedApps = {};
  let currentApp = 'INIT';

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      console.error(`[CONSOLE ERROR in ${currentApp}]:`, text);
      if (!failedApps[currentApp]) failedApps[currentApp] = [];
      failedApps[currentApp].push(text);
    }
  });

  page.on('pageerror', err => {
    const text = err.stack || err.message;
    console.error(`[PAGE ERROR in ${currentApp}]:`, text);
    if (!failedApps[currentApp]) failedApps[currentApp] = [];
    failedApps[currentApp].push(text);
  });

  page.on('response', resp => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400 && (url.endsWith('.js') || url.endsWith('.css') || url.includes('/web/assets/'))) {
      const err = `HTTP ${status} on asset: ${url}`;
      console.error(`[ASSET ERROR in ${currentApp}]:`, err);
      if (!failedApps[currentApp]) failedApps[currentApp] = [];
      failedApps[currentApp].push(err);
    }
  });

  console.log('Authenticating...');
  const authResp = await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: {
      jsonrpc: '2.0',
      params: { db: 'odoo20_dev', login: 'admin', password: 'admin' }
    }
  });
  const authResult = await authResp.json();
  if (!authResult.result?.uid) {
    throw new Error('Authentication failed: ' + JSON.stringify(authResult));
  }
  console.log('Authenticated UID:', authResult.result.uid);

  // Test 1: Desktop Home Menu
  currentApp = 'Desktop Home Menu';
  console.log(`\n---> Testing ${currentApp}...`);
  await page.goto('http://localhost:28069/web', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2000);
  const homeApps = await page.$$('.o_app');
  console.log(`Home menu apps found: ${homeApps.length}`);
  if (!failedApps[currentApp] || failedApps[currentApp].length === 0) {
    console.log(`[PASS] ${currentApp} loaded cleanly with 0 errors!`);
  }

  // Test 2: Major Applications
  for (const app of APPS) {
    currentApp = app.name;
    console.log(`\n---> Testing ${app.name} (${app.path})...`);
    try {
      await page.goto(`http://localhost:28069${app.path}`, {
        waitUntil: 'domcontentloaded',
        timeout: 60000
      });
      await page.waitForTimeout(3000);

      const hasErrorDialog = await page.$('.o_error_dialog');
      if (hasErrorDialog) {
        const errorText = await page.$eval('.o_error_dialog', el => el.innerText);
        console.error(`[ERROR DIALOG in ${app.name}]:`, errorText);
        if (!failedApps[app.name]) failedApps[app.name] = [];
        failedApps[app.name].push(`Error Dialog: ${errorText}`);
      }

      if (!failedApps[app.name] || failedApps[app.name].length === 0) {
        console.log(`[PASS] ${app.name} loaded cleanly with 0 errors!`);
      } else {
        console.error('[FAIL] ' + app.name + ' had ' + failedApps[app.name].length + ' errors!');
      }
    } catch (e) {
      console.error(`[EXCEPTION in ${app.name}]:`, e.message);
      if (!failedApps[app.name]) failedApps[app.name] = [];
      failedApps[app.name].push(e.message);
    }
  }

  // Test 3: Mobile View
  currentApp = 'Mobile View';
  console.log(`\n---> Testing ${currentApp}...`);
  const mobileContext = await browser.newContext({
    viewport: { width: 375, height: 667 },
    hasTouch: true,
    isMobile: true
  });
  const mobilePage = await mobileContext.newPage();
  mobilePage.on('console', msg => {
    if (msg.type() === 'error') {
      console.error(`[CONSOLE ERROR in Mobile]:`, msg.text());
      if (!failedApps['Mobile View']) failedApps['Mobile View'] = [];
      failedApps['Mobile View'].push(msg.text());
    }
  });
  mobilePage.on('pageerror', err => {
    console.error('[PAGE ERROR in Mobile]: ' + (err.stack || err.message));
    if (!failedApps['Mobile View']) failedApps['Mobile View'] = [];
    failedApps['Mobile View'].push(err.stack || err.message);
  });

  await mobilePage.request.post('http://localhost:28069/web/session/authenticate', {
    data: {
      jsonrpc: '2.0',
      params: { db: 'odoo20_dev', login: 'admin', password: 'admin' }
    }
  });
  await mobilePage.goto('http://localhost:28069/web', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await mobilePage.waitForTimeout(2000);
  await mobilePage.click('.o_app:first-child');
  await mobilePage.waitForTimeout(2000);
  if (!failedApps['Mobile View'] || failedApps['Mobile View'].length === 0) {
    console.log(`[PASS] Mobile View passed cleanly with 0 errors!`);
  }

  await browser.close();

  console.log('\n================= SUMMARY =================');
  const errorEntries = Object.entries(failedApps).filter(([_, errs]) => errs.length > 0);
  if (errorEntries.length === 0) {
    console.log('ALL TESTS PASSED WITH 0 CONSOLE / RUNTIME ERRORS!');
    process.exit(0);
  } else {
    console.error(`FAILED: ${errorEntries.length} sections had errors:`);
    for (const [name, errs] of errorEntries) {
      console.error(`\n--- App: ${name} (${errs.length} errors) ---`);
      errs.forEach(e => console.error('  *', e));
    }
    process.exit(1);
  }
}

run().catch(err => {
  console.error('Fatal runner error:', err);
  process.exit(1);
});
