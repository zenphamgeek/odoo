const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  // Test 1: Desktop View
  console.log('=== Starting Desktop E2E Test ===');
  const desktopContext = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const desktopPage = await desktopContext.newPage();

  const desktopErrors = [];
  desktopPage.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('[BROWSER ERROR]', msg.text());
      desktopErrors.push(msg.text());
    }
  });
  desktopPage.on('pageerror', err => {
    console.error('[BROWSER PAGEERROR]', err.stack || err.message);
    desktopErrors.push(err.stack || err.message);
  });

  console.log('1. Authenticating via JSON-RPC...');
  const resp = await desktopPage.request.post('http://localhost:28069/web/session/authenticate', {
    data: {
      jsonrpc: '2.0',
      params: { db: 'odoo20_dev', login: 'admin', password: 'admin' }
    }
  });
  const auth = await resp.json();
  if (!auth.result?.uid) {
    throw new Error('Authentication failed: ' + JSON.stringify(auth));
  }
  console.log('Authenticated as uid:', auth.result.uid);

  console.log('2. Navigating to /web...');
  await desktopPage.goto('http://localhost:28069/web', { waitUntil: 'domcontentloaded', timeout: 60000 });
  console.log('Current URL after goto:', desktopPage.url());
  await desktopPage.waitForTimeout(3000);
  console.log('Current URL after 3s:', desktopPage.url());

  console.log('3. Waiting for Home Menu (App Switcher)...');
  await desktopPage.waitForSelector('.o_home_menu', { timeout: 15000 });
  const appCount = await desktopPage.$$eval('.o_app', els => els.length);
  console.log('Found .o_app elements:', appCount);

  console.log('4. Clicking on first app...');
  await desktopPage.click('.o_app:first-child');
  await desktopPage.waitForSelector('.o_navbar', { timeout: 15000 });
  console.log('Navbar loaded. Current URL:', desktopPage.url());

  console.log('5. Clicking home menu toggle back...');
  await desktopPage.click('.o_menu_toggle');
  await desktopPage.waitForSelector('.o_home_menu', { timeout: 15000 });
  console.log('Returned to Home Menu successfully.');

  console.log('6. Desktop Console errors:', desktopErrors);

  // Test 2: Mobile View
  console.log('\n=== Starting Mobile E2E Test ===');
  const mobileContext = await browser.newContext({
    viewport: { width: 375, height: 667 },
    hasTouch: true,
    isMobile: true,
  });
  const mobilePage = await mobileContext.newPage();

  const mobileErrors = [];
  mobilePage.on('console', msg => {
    if (msg.type() === 'error') {
      mobileErrors.push(msg.text());
    }
  });
  mobilePage.on('pageerror', err => {
    mobileErrors.push(err.stack || err.message);
  });

  console.log('1. Authenticating mobile context...');
  await mobilePage.request.post('http://localhost:28069/web/session/authenticate', {
    data: {
      jsonrpc: '2.0',
      params: { db: 'odoo20_dev', login: 'admin', password: 'admin' }
    }
  });

  console.log('2. Navigating to mobile /web...');
  await mobilePage.goto('http://localhost:28069/web', { waitUntil: 'domcontentloaded', timeout: 60000 });

  console.log('3. Waiting for mobile Home Menu...');
  await mobilePage.waitForSelector('.o_home_menu', { timeout: 15000 });
  const mobileAppCount = await mobilePage.$$eval('.o_app', els => els.length);
  console.log('Found mobile .o_app elements:', mobileAppCount);

  console.log('4. Clicking an app on mobile...');
  await mobilePage.click('.o_app:first-child');
  await mobilePage.waitForSelector('.o_navbar', { timeout: 15000 });
  console.log('Mobile Navbar loaded.');

  console.log('5. Clicking mobile menu toggle to open sidebar, then returning to Home Menu...');
  await mobilePage.click('.o_menu_toggle');
  await mobilePage.waitForSelector('.o_sidebar_topbar a.btn-primary', { timeout: 15000 });
  await mobilePage.click('.o_sidebar_topbar a.btn-primary');
  await mobilePage.waitForSelector('.o_home_menu', { timeout: 15000 });
  console.log('Returned to Home Menu on mobile successfully.');

  console.log('6. Mobile Console errors:', mobileErrors);

  // Test 3: Barcode App View
  console.log('\n=== Starting Barcode Client Action E2E Test ===');
  const barcodePage = await desktopContext.newPage();
  const barcodeErrors = [];
  barcodePage.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('[BARCODE BROWSER ERROR]', msg.text());
      barcodeErrors.push(msg.text());
    }
  });
  barcodePage.on('pageerror', err => {
    console.error('[BARCODE PAGEERROR]', err.stack || err.message);
    barcodeErrors.push(err.stack || err.message);
  });

  console.log('1. Navigating to /web/barcode...');
  await barcodePage.goto('http://localhost:28069/web/barcode', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await barcodePage.waitForTimeout(3000);
  console.log('Current URL:', barcodePage.url());

  const barcodeMainMenu = await barcodePage.$('.o_stock_barcode_main_menu');
  console.log('Found .o_stock_barcode_main_menu:', Boolean(barcodeMainMenu));
  console.log('Barcode Console errors:', barcodeErrors);

  await browser.close();

  const totalErrors = desktopErrors.length + mobileErrors.length + barcodeErrors.length;
  if (totalErrors > 0) {
    console.error(`FAILED: ${totalErrors} console errors detected!`);
    process.exit(1);
  } else {
    console.log('\nSUCCESS: All E2E smoke tests passed with 0 console errors!');
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
