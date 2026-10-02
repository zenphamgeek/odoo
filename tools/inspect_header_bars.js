const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

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

  console.log('Authenticating admin session...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  console.log('Navigating to Purchase Order form...');
  await page.goto('http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });
  console.log('Waiting for .o_control_panel...');
  await page.waitForSelector('.o_control_panel', { timeout: 30000 });
  await page.waitForSelector('.o_form_statusbar', { timeout: 30000 });
  await page.waitForTimeout(2000);

  // Take screenshot of the top header bars
  const screenshotPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/header_bars_current.png';
  await page.screenshot({
    path: screenshotPath,
    clip: { x: 0, y: 0, width: 1440, height: 350 }
  });
  console.log(`Saved screenshot to ${screenshotPath}`);

  // Inspect the elements in header bars
  const headerInfo = await page.evaluate(() => {
    function getBox(selector) {
      const el = document.querySelector(selector);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return {
        selector,
        x: r.x, y: r.y, width: r.width, height: r.height,
        bg: style.backgroundColor,
        color: style.color,
        display: style.display,
        border: style.border
      };
    }

    return {
      navbar: getBox('.o_navbar'),
      controlPanel: getBox('.o_control_panel'),
      breadcrumbs: getBox('.o_breadcrumb'),
      cpButtons: getBox('.o_cp_buttons'),
      buttonBox: getBox('.o-form-buttonbox') || getBox('.oe_button_box'),
      pager: getBox('.o_pager'),
      statusbar: getBox('.o_form_statusbar'),
      statusbarButtons: getBox('.o_statusbar_buttons'),
      statusbarStatus: getBox('.o_statusbar_status'),
      formSheet: getBox('.o_form_sheet'),
      docTitle: getBox('.oe_title'),
      chatterTopbar: getBox('.o-mail-Chatter-topbar')
    };
  });

  console.log('Header Info:', JSON.stringify(headerInfo, null, 2));

  await browser.close();
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
