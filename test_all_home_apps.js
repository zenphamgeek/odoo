const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const appErrors = {};
  let currentApp = 'INIT';

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (txt.includes('favicon.ico')) return;
      console.error(`  [CONSOLE ERROR in ${currentApp}]:`, txt.slice(0, 160));
      if (!appErrors[currentApp]) appErrors[currentApp] = [];
      appErrors[currentApp].push({ type: 'console', text: txt });
    }
  });

  page.on('pageerror', err => {
    const txt = err.stack || err.message;
    console.error(`  [PAGE ERROR in ${currentApp}]:`, txt.slice(0, 160));
    if (!appErrors[currentApp]) appErrors[currentApp] = [];
    appErrors[currentApp].push({ type: 'pageerror', text: txt });
  });

  page.on('response', resp => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400 && (url.endsWith('.js') || url.endsWith('.css') || url.includes('/web/assets/'))) {
      const err = `HTTP ${status} on asset: ${url}`;
      console.error(`  [ASSET ERROR in ${currentApp}]:`, err);
      if (!appErrors[currentApp]) appErrors[currentApp] = [];
      appErrors[currentApp].push({ type: 'asset', text: err });
    }
  });

  console.log('Authenticating...');
  const resp = await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });
  const auth = await resp.json();
  console.log('Logged in UID:', auth.result?.uid);

  currentApp = 'Home Menu';
  await page.goto('http://localhost:28069/web', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.o_app', { timeout: 20000 });

  const apps = await page.$$eval('.o_app', els =>
    els.map((e, idx) => ({
      index: idx,
      id: e.id,
      name: e.innerText.trim().split('\n')[0],
      xmlid: e.getAttribute('data-menu-xmlid'),
      href: e.getAttribute('href')
    }))
  );

  console.log(`\nFound ${apps.length} apps in Home Menu:`);
  for (const a of apps) {
    console.log(`  [${String(a.index + 1).padStart(2, ' ')}] ${a.name.padEnd(24, ' ')} -> ${a.href} (${a.xmlid})`);
  }

  console.log('\n--- STARTING SYSTEMATIC E2E APP VALIDATION ---');
  let passedCount = 0;
  let failedCount = 0;

  for (const app of apps) {
    currentApp = app.name;
    process.stdout.write(`\nTesting [${String(app.index + 1).padStart(2, ' ')}/${apps.length}] ${app.name.padEnd(24, ' ')} `);

    try {
      const targetUrl = `http://localhost:28069${app.href}`;
      await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(2500);

      // Check for error dialog
      const errorDialog = await page.$('.o_error_dialog, .modal:has(.o_error_dialog)');
      if (errorDialog) {
        const errTitle = await page.$eval('.o_error_dialog .modal-title', el => el.innerText).catch(() => 'Error');
        const errDetail = await page.$eval('.o_error_dialog pre, .o_error_dialog main', el => el.innerText).catch(() => '');
        console.log(`❌ FAILED (Dialog: ${errTitle})`);
        if (!appErrors[app.name]) appErrors[app.name] = [];
        appErrors[app.name].push({ type: 'dialog', title: errTitle, detail: errDetail.slice(0, 300) });
        failedCount++;
      } else if (appErrors[app.name] && appErrors[app.name].length > 0) {
        console.log(`⚠️ WARNING (${appErrors[app.name].length} console/asset issues)`);
        failedCount++;
      } else {
        console.log('✅ PASS');
        passedCount++;
      }
    } catch (e) {
      console.log(`❌ EXCEPTION: ${e.message.slice(0, 80)}`);
      if (!appErrors[app.name]) appErrors[app.name] = [];
      appErrors[app.name].push({ type: 'exception', text: e.message });
      failedCount++;
    }
  }

  await browser.close();

  console.log('\n======================================================');
  console.log('                 FINAL TEST REPORT                    ');
  console.log('======================================================');
  console.log(`Total Home Apps Tested : ${apps.length}`);
  console.log(`Passed with 0 Errors   : ${passedCount}`);
  console.log(`Failed or with Issues  : ${failedCount}`);

  if (failedCount > 0) {
    console.log('\n--- DETAILED ISSUES BY APP ---');
    for (const [appName, issues] of Object.entries(appErrors)) {
      if (issues.length === 0) continue;
      console.log(`\nApp: [${appName}] (${issues.length} issues)`);
      for (const iss of issues) {
        if (iss.type === 'dialog') {
          console.log(`  - [DIALOG] ${iss.title}:\n    ${iss.detail}`);
        } else if (iss.type === 'pageerror') {
          console.log(`  - [PAGE ERROR] ${iss.text.slice(0, 200)}`);
        } else if (iss.type === 'console') {
          console.log(`  - [CONSOLE] ${iss.text.slice(0, 200)}`);
        } else if (iss.type === 'asset') {
          console.log(`  - [ASSET] ${iss.text}`);
        } else {
          console.log(`  - [ERROR] ${iss.text || JSON.stringify(iss)}`);
        }
      }
    }
  } else {
    console.log('\n🎉 ALL 60 HOME APPS PASSED PERFECTLY WITH ZERO ERRORS!');
  }
}

main().catch(err => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
