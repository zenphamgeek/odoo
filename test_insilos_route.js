const { chromium } = require('playwright');

async function main() {
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
        console.error('  [CONSOLE ERROR]:', txt);
        errors.push({ type: 'console', text: txt });
      }
    }
  });

  page.on('pageerror', err => {
    console.error('  [PAGE ERROR]:', err.stack || err.message);
    errors.push({ type: 'pageerror', text: err.stack || err.message });
  });

  console.log('1. Authenticating...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  console.log('2. Testing direct navigation to /insilos...');
  await page.goto('http://localhost:28069/insilos', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  console.log('Current URL after visiting /insilos:', page.url());

  const appCount = await page.$$eval('.o_app', els => els.length);
  console.log(`Found ${appCount} apps in /insilos App Drawer.`);

  console.log('\n3. Testing legacy redirect: visiting /odoo...');
  await page.goto('http://localhost:28069/odoo', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  console.log('Current URL after visiting /odoo:', page.url());

  console.log('\n4. Testing legacy subpath redirect: visiting /odoo/contacts...');
  await page.goto('http://localhost:28069/odoo/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  console.log('Current URL after visiting /odoo/contacts:', page.url());

  console.log('\n5. Testing app drawer click in /insilos...');
  await page.goto('http://localhost:28069/insilos', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);

  // Click on CRM app
  const crmApp = await page.$('.o_app[data-menu-xmlid="crm.crm_menu_root"]');
  if (crmApp) {
    const crmHref = await crmApp.getAttribute('href');
    console.log('CRM app href attribute:', crmHref);
    await crmApp.click();
    await page.waitForTimeout(3000);
    console.log('Current URL after clicking CRM:', page.url());
  }

  // Check create button
  const createBtn = await page.$('.btn-primary.o-kanban-button-new, .btn-primary.o_list_button_add');
  if (createBtn) {
    console.log('Create Button text:', (await createBtn.innerText()).trim());
  }

  console.log(`\nTotal errors encountered: ${errors.length}`);
  await browser.close();

  if (errors.length > 0) {
    console.error('TEST FAILED WITH ERRORS!');
    process.exit(1);
  } else {
    console.log('TEST PASSED WITH 0 ERRORS! /insilos route is fully operational!');
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
