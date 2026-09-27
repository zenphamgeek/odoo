/**
 * Automated Marketing Screenshot Capture for Insilos Enterprise Suite
 * Uses Playwright Chromium with 1600x960 viewport (deviceScaleFactor: 1.5).
 * Navigates using 'load' event and UI interactions to avoid longpolling hangs.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.resolve(__dirname, '../doc/screenshots');

async function main() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  console.log('🚀 Starting Marketing Screenshot Capture Pipeline...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1600, height: 960 },
    deviceScaleFactor: 1.5,
  });

  const page = await context.newPage();

  try {
    // 1. Authenticate
    console.log('[1/7] Authenticating as Administrator...');
    const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
      data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });
    if (!authRes.ok()) throw new Error('Authentication failed');

    // 2. Capture Launcher Home View
    console.log('[2/7] Capturing Insilos Enterprise App Launcher...');
    await page.goto('http://localhost:28069/insilos', { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_insilos_launcher_apps.png') });
    console.log('  ✓ Saved 01_insilos_launcher_apps.png');

    // Helper to click an app from home screen
    async function openApp(appName) {
      await page.goto('http://localhost:28069/insilos', { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(2000);
      const appEl = page.locator(`.o_app:has-text("${appName}")`).first();
      if (await appEl.count() > 0) {
        await appEl.click();
        await page.waitForTimeout(3000);
        return true;
      }
      return false;
    }

    // 3. Capture Logistics IDP
    console.log('[3/7] Capturing Logistics IDP Control Tower & Case Detail...');
    if (await openApp('Logistics IDP')) {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_logistics_idp_control_tower.png') });
      console.log('  ✓ Saved 02_logistics_idp_control_tower.png');

      const firstRow = page.locator('.o_data_row, .o_kanban_record').first();
      if (await firstRow.count() > 0) {
        await firstRow.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_logistics_idp_case_detail.png') });
        console.log('  ✓ Saved 03_logistics_idp_case_detail.png');
      }
    }

    // 4. Capture Chemical Trade Compliance
    console.log('[4/7] Capturing Chemical Trade Compliance...');
    if (await openApp('Chemical Trade Compliance') || await openApp('Tuân thủ Hóa chất')) {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_chemical_compliance_dossier.png') });
      console.log('  ✓ Saved 04_chemical_compliance_dossier.png');

      // Click on Quota menu item if visible
      const quotaMenu = page.locator('a:has-text("Quota"), a:has-text("Hạn ngạch")').first();
      if (await quotaMenu.count() > 0) {
        await quotaMenu.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_chemical_quota_ledger.png') });
        console.log('  ✓ Saved 05_chemical_quota_ledger.png');
      }
    }

    // 5. Capture Preferential Origin FTA
    console.log('[5/7] Capturing Preferential Origin FTA Decision Support...');
    if (await openApp('Preferential Origin') || await openApp('Xuất xứ FTA')) {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_preferential_origin_fta.png') });
      console.log('  ✓ Saved 06_preferential_origin_fta.png');
    }

    // 6. Capture ESG Bridge Cockpit
    console.log('[6/7] Capturing ESG Bridge Sustainability Cockpit...');
    if (await openApp('ESG Bridge') || await openApp('Báo cáo ESG')) {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_esg_bridge_cockpit.png') });
      console.log('  ✓ Saved 07_esg_bridge_cockpit.png');
    }

    // 7. Capture Market Terminal
    console.log('[7/7] Capturing Market Terminal Financial Cockpit...');
    if (await openApp('Market Terminal') || await openApp('Thị trường')) {
      await page.waitForTimeout(3000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_market_terminal_tradingview.png') });
      console.log('  ✓ Saved 08_market_terminal_tradingview.png');
    }

    console.log('\n✨ All Marketing Screenshots captured successfully in doc/screenshots/ !');

  } catch (err) {
    console.error('❌ Error during capture:', err);
  } finally {
    await browser.close();
  }
}

main();
