const { chromium } = require('playwright');

const MODULE_LISTS = [
  { name: 'MM_Purchase_List', url: 'http://localhost:28069/web#model=purchase.order&view_type=list&action=758' },
  { name: 'SD_Sale_List', url: 'http://localhost:28069/web#model=sale.order&view_type=list&action=561' },
  { name: 'LE_Stock_List', url: 'http://localhost:28069/web#model=stock.picking&view_type=list&action=257' },
  { name: 'FI_Account_List', url: 'http://localhost:28069/web#model=account.move&view_type=list&action=475' }
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

  for (const item of MODULE_LISTS) {
    console.log(`Navigating to ${item.name}...`);
    await page.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForSelector('.o_control_panel', { timeout: 30000 });
    await page.waitForTimeout(2000);

    const metrics = await page.evaluate((name) => {
      const cp = document.querySelector('.o_control_panel');
      const main = document.querySelector('.o_control_panel_main');
      const searchview = document.querySelector('.o_searchview') || document.querySelector('.o_cp_searchview');
      const switchers = document.querySelector('.o_cp_switch_buttons');
      const listTable = document.querySelector('.o_list_table');

      const cpRect = cp ? cp.getBoundingClientRect() : null;
      const mainRect = main ? main.getBoundingClientRect() : null;
      const searchRect = searchview ? searchview.getBoundingClientRect() : null;
      const switchRect = switchers ? switchers.getBoundingClientRect() : null;

      return {
        name,
        cpHeight: cpRect ? Math.round(cpRect.height) : null,
        mainLeft: mainRect ? Math.round(mainRect.x) : null,
        hasTable: !!listTable,
        searchHeight: searchRect ? Math.round(searchRect.height) : null,
        switcherHeight: switchRect ? Math.round(switchRect.height) : null
      };
    }, item.name);

    console.log('Metrics:', metrics);

    if (item.name === 'MM_Purchase_List') {
      const screenshotPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/list_view_header_light.png';
      await page.screenshot({
        path: screenshotPath,
        clip: { x: 0, y: 0, width: 1440, height: 350 }
      });
      console.log('Captured Light:', screenshotPath);

      // Dark mode
      await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        document.documentElement.setAttribute('data-theme', 'dark');
      });
      await page.waitForTimeout(1000);

      const darkScreenshotPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/list_view_header_dark.png';
      await page.screenshot({
        path: darkScreenshotPath,
        clip: { x: 0, y: 0, width: 1440, height: 350 }
      });
      console.log('Captured Dark:', darkScreenshotPath);
    }
  }

  await browser.close();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
