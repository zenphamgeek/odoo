/**
 * Verify previously timed out apps individually with dedicated timeout.
 */
const { chromium } = require('playwright');

const APPS_TO_VERIFY = [
  { name: 'Insilos IAP', href: '/insilos/action-4959' },
  { name: 'Knowledge', href: '/insilos/knowledge' },
  { name: 'Unified Operations', href: '/insilos/unified-operations' },
  { name: 'Contacts', href: '/insilos/contacts' },
  { name: 'Market Terminal', href: '/insilos/action-5108' },
  { name: 'Treasury & Market Risk', href: '/insilos/action-5098' },
  { name: 'Preferential Origin', href: '/insilos/action-insilos_preferential_origin.action_preferential_origin_scenarios' },
  { name: 'Capital Markets', href: '/insilos/action-5060' },
  { name: 'eLearning', href: '/insilos/e-learning' },
  { name: 'Social Marketing', href: '/insilos/social' },
  { name: 'Marketing Automation', href: '/insilos/marketing-automation' },
];

async function main() {
  console.log('[VERIFICATION] Testing Targeted Apps Sequentially...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  const results = [];

  for (const app of APPS_TO_VERIFY) {
    const errors = [];
    const onConsole = msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon.ico')) {
        errors.push(`[CONSOLE] ${msg.text()}`);
      }
    };
    const onPageErr = err => errors.push(`[PAGEERROR] ${err.stack || err.message}`);

    page.on('console', onConsole);
    page.on('pageerror', onPageErr);

    try {
      console.log(`Testing ${app.name} (${app.href})...`);
      await page.goto(`http://localhost:28069${app.href}`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(2000);

      // Check for error modal
      const errDialog = await page.$('.o_error_dialog');
      if (errDialog) {
        const title = await page.$eval('.o_error_dialog .modal-title', el => el.innerText).catch(() => 'Error');
        errors.push(`[DIALOG] ${title}`);
      }

      if (errors.length === 0) {
        console.log(`  ✅ PASS: ${app.name}`);
        results.push({ name: app.name, status: 'PASS' });
      } else {
        console.log(`  ❌ FAIL: ${app.name} -> ${errors.join(', ')}`);
        results.push({ name: app.name, status: 'FAIL', errors });
      }
    } catch (e) {
      console.log(`  ❌ EXCEPTION: ${app.name} -> ${e.message}`);
      results.push({ name: app.name, status: 'EXCEPTION', error: e.message });
    } finally {
      page.off('console', onConsole);
      page.off('pageerror', onPageErr);
    }
  }

  await browser.close();

  console.log('\n' + '='.repeat(50));
  console.log('TARGETED VERIFICATION SUMMARY:');
  console.log('='.repeat(50));
  let passCount = 0;
  for (const r of results) {
    console.log(`  ${r.status === 'PASS' ? '✅' : '❌'} ${r.name.padEnd(25)} : ${r.status}`);
    if (r.status === 'PASS') passCount++;
  }
  console.log('='.repeat(50));
  console.log(`Total: ${results.length} | Passed: ${passCount} | Failed: ${results.length - passCount}`);

  if (passCount !== results.length) {
    process.exit(1);
  }
}

main().catch(err => {
  console.error('[FATAL]', err);
  process.exit(1);
});
