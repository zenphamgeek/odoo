const { chromium } = require('playwright');

async function getAppList() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  await page.goto('http://localhost:28069/insilos', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.o_app', { timeout: 20000 });

  const apps = await page.$$eval('.o_app', els =>
    els.map((e, idx) => ({
      index: idx,
      name: e.innerText.trim().split('\n')[0],
      xmlid: e.getAttribute('data-menu-xmlid'),
      href: e.getAttribute('href')
    }))
  );

  await browser.close();
  return apps;
}

async function testSingleApp(page, app, results) {
  const errors = [];

  const consoleListener = msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (!txt.includes('favicon.ico')) {
        errors.push({ type: 'console', text: txt });
      }
    }
  };

  const pageErrorListener = err => {
    errors.push({ type: 'pageerror', text: err.stack || err.message });
  };

  const responseListener = resp => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400 && (url.endsWith('.js') || url.endsWith('.css') || url.includes('/web/assets/'))) {
      errors.push({ type: 'asset', text: `HTTP ${status} on ${url}` });
    }
  };

  page.on('console', consoleListener);
  page.on('pageerror', pageErrorListener);
  page.on('response', responseListener);

  try {
    // Navigate to app
    await page.goto(`http://localhost:28069${app.href}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2500);

    // Check for error dialog safely
    try {
      const errorDialog = await page.$('.o_error_dialog, .modal:has(.o_error_dialog)');
      if (errorDialog) {
        const errTitle = await page.$eval('.o_error_dialog .modal-title', el => el.innerText).catch(() => 'Error');
        const errDetail = await page.$eval('.o_error_dialog pre, .o_error_dialog main', el => el.innerText).catch(() => '');
        errors.push({ type: 'dialog', text: `${errTitle}: ${errDetail}` });
      }
    } catch {
      // Ignored if navigation occurred
    }
  } catch (e) {
    errors.push({ type: 'exception', text: e.message });
  } finally {
    page.off('console', consoleListener);
    page.off('pageerror', pageErrorListener);
    page.off('response', responseListener);
  }

  results[app.name] = errors;
  const statusIcon = errors.length === 0 ? '✅ PASS' : `❌ FAIL (${errors.length} issues)`;
  console.log(`[${String(app.index + 1).padStart(2, ' ')}] ${app.name.padEnd(28, ' ')} : ${statusIcon}`);
}

async function main() {
  console.log('Fetching app list from Odoo...');
  const apps = await getAppList();
  console.log(`Found ${apps.length} apps. Initializing session storageState...\n`);

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  // Authenticate once and extract session state
  const authContext = await browser.newContext();
  const authPage = await authContext.newPage();
  await authPage.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });
  const storageState = await authContext.storageState();
  await authContext.close();

  console.log(`Session authenticated. Launching parallel validation (Concurrency: 4)...\n`);

  const results = {};
  const CONCURRENCY = 4;
  const queue = [...apps];

  async function worker() {
    const context = await browser.newContext({ storageState, viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    while (queue.length > 0) {
      const app = queue.shift();
      if (!app) break;
      await testSingleApp(page, app, results);
    }
    await context.close().catch(() => {});
  }

  const workers = Array.from({ length: CONCURRENCY }, () => worker());
  await Promise.all(workers);

  // If any app failed due to parallel contention or timeout, retry sequentially
  const failedApps = apps.filter(app => results[app.name] && results[app.name].length > 0);
  if (failedApps.length > 0) {
    console.log(`\nRetrying ${failedApps.length} failed/timed-out apps sequentially to rule out parallel contention...`);
    const retryContext = await browser.newContext({ storageState, viewport: { width: 1440, height: 900 } });
    const retryPage = await retryContext.newPage();
    for (const app of failedApps) {
      console.log(`Retrying [${app.name}]...`);
      await testSingleApp(retryPage, app, results);
    }
    await retryContext.close().catch(() => {});
  }

  await browser.close();

  console.log('\n======================================================');
  console.log('          PARALLEL E2E VERIFICATION REPORT           ');
  console.log('======================================================');
  let passed = 0;
  let failed = 0;
  for (const app of apps) {
    const errs = results[app.name] || [];
    if (errs.length === 0) {
      passed++;
    } else {
      failed++;
      console.log(`\n❌ App: [${app.name}] (${errs.length} errors)`);
      for (const err of errs) {
        console.log(`   - [${err.type}] ${err.text.slice(0, 180)}`);
      }
    }
  }

  console.log(`\nTotal Apps Tested : ${apps.length}`);
  console.log(`Passed (0 Errors) : ${passed}`);
  console.log(`Failed / Issues   : ${failed}`);
  console.log('======================================================');

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal runner error:', err);
  process.exit(1);
});
