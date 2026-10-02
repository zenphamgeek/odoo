const { chromium } = require('playwright');
const path = require('path');

const MODULES = [
  { name: 'MM_Purchase', url: 'http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758' },
  { name: 'SD_Sale', url: 'http://localhost:28069/web#id=1&model=sale.order&view_type=form&action=561' },
  { name: 'LE_Stock', url: 'http://localhost:28069/web#id=2&model=stock.picking&view_type=form&action=257' },
  { name: 'PP_MRP', url: 'http://localhost:28069/web#id=10&model=mrp.production&view_type=form&action=367' },
  { name: 'FI_Account', url: 'http://localhost:28069/web#id=12&model=account.move&view_type=form&action=475' },
  { name: 'HCM_Employee', url: 'http://localhost:28069/web#id=47&model=hr.employee&view_type=form&action=1012' }
];

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

  console.log('Authenticating session...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  const results = [];

  for (const m of MODULES) {
    console.log(`Testing ${m.name}...`);
    await page.goto(m.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForSelector('.o_control_panel', { timeout: 30000 });
    await page.waitForTimeout(2000);

    const data = await page.evaluate((modName) => {
      const cp = document.querySelector('.o_control_panel');
      const main = document.querySelector('.o_control_panel_main');
      const sb = document.querySelector('.o_form_statusbar');
      const chatter = document.querySelector('.o-mail-Chatter-topbar');

      const cpRect = cp ? cp.getBoundingClientRect() : null;
      const mainRect = main ? main.getBoundingClientRect() : null;
      const sbRect = sb ? sb.getBoundingClientRect() : null;
      const chatterRect = chatter ? chatter.getBoundingClientRect() : null;

      const baselineError = (sbRect && chatterRect) ? Math.abs(sbRect.y - chatterRect.y) : 0;

      return {
        module: modName,
        cpHeight: cpRect ? Math.round(cpRect.height) : null,
        mainLeft: mainRect ? Math.round(mainRect.x) : null,
        sbHeight: sbRect ? Math.round(sbRect.height) : null,
        baselineError: baselineError
      };
    }, m.name);

    results.push(data);
    console.log(`  -> ${JSON.stringify(data)}`);
  }

  console.log('\n--- ALL MODULES SUMMARY ---');
  console.log(JSON.stringify(results, null, 2));

  await browser.close();
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
