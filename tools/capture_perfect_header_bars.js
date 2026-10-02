const { chromium } = require('playwright');

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

  console.log('Navigating to Purchase Order form...');
  await page.goto('http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });
  await page.waitForSelector('.o_control_panel', { timeout: 30000 });
  await page.waitForSelector('.o_form_statusbar', { timeout: 30000 });
  await page.waitForTimeout(2000);

  // Capture Light Mode
  const lightPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/header_bars_perfect_light.png';
  await page.screenshot({
    path: lightPath,
    clip: { x: 0, y: 0, width: 1440, height: 350 }
  });
  console.log('Saved Light Mode to:', lightPath);

  // Enable Dark Mode
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  });
  await page.waitForTimeout(1000);

  // Capture Dark Mode
  const darkPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/header_bars_perfect_dark.png';
  await page.screenshot({
    path: darkPath,
    clip: { x: 0, y: 0, width: 1440, height: 350 }
  });
  console.log('Saved Dark Mode to:', darkPath);

  // Measure key layout metrics
  const metrics = await page.evaluate(() => {
    const cp = document.querySelector('.o_control_panel');
    const main = document.querySelector('.o_control_panel_main');
    const breadcrumb = document.querySelector('.o_breadcrumb');
    const statButtons = document.querySelector('.o-form-buttonbox') || document.querySelector('.oe_button_box');
    const statusbar = document.querySelector('.o_form_statusbar');
    const chatterTopbar = document.querySelector('.o-mail-Chatter-topbar');

    return {
      controlPanelHeight: cp ? cp.getBoundingClientRect().height : null,
      controlPanelWidth: cp ? cp.getBoundingClientRect().width : null,
      mainLeftMargin: main ? main.getBoundingClientRect().x : null,
      breadcrumbHeight: breadcrumb ? breadcrumb.getBoundingClientRect().height : null,
      statButtonHeight: statButtons ? statButtons.getBoundingClientRect().height : null,
      statusbarY: statusbar ? statusbar.getBoundingClientRect().y : null,
      chatterTopbarY: chatterTopbar ? chatterTopbar.getBoundingClientRect().y : null,
      baselineErrorPx: (statusbar && chatterTopbar) ? Math.abs(statusbar.getBoundingClientRect().y - chatterTopbar.getBoundingClientRect().y) : null
    };
  });

  console.log('Layout Metrics:', JSON.stringify(metrics, null, 2));

  await browser.close();
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
