/**
 * Quick targeted capture for simulation records (Case form, Quota ledger, ESG Carbon & CBAM)
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = path.resolve(__dirname, '../doc/screenshots');

async function main() {
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
    await page.request.post('http://localhost:28069/web/session/authenticate', {
      data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });

    // 1. Quota Form View
    console.log('Capturing Quota Form...');
    await page.goto('http://localhost:28069/insilos#action=insilos_chemical_trade_compliance.action_is_chemical_permit_quota&view_type=list', { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(3000);
    const row = page.locator('.o_data_row').first();
    if (await row.count() > 0) {
      await row.click();
      await page.waitForTimeout(2500);
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_chemical_quota_ledger.png') });
    console.log('✓ Saved 05_chemical_quota_ledger.png');

    // 2. IDP Case Detail Form
    console.log('Capturing IDP Case Form...');
    await page.goto('http://localhost:28069/insilos/inbound-control-tower', { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(3000);
    const caseRow = page.locator('.o_data_row').first();
    if (await caseRow.count() > 0) {
      await caseRow.click();
      await page.waitForTimeout(2500);
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_logistics_idp_case_detail.png') });
    console.log('✓ Saved 03_logistics_idp_case_detail.png');

    // 3. ESG Freight Carbon & CBAM
    console.log('Capturing ESG Freight Carbon...');
    await page.goto('http://localhost:28069/insilos#action=insilos_esg_bridge.action_is_esg_freight_carbon&view_type=list', { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(3000);
    const carbonRow = page.locator('.o_data_row').first();
    if (await carbonRow.count() > 0) {
      await carbonRow.click();
      await page.waitForTimeout(2000);
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_esg_freight_carbon.png') });
    console.log('✓ Saved 07_esg_freight_carbon.png');

    // 4. ESG CBAM Advisor
    console.log('Capturing ESG CBAM Advisor...');
    await page.goto('http://localhost:28069/insilos#action=insilos_esg_bridge.action_is_esg_cbam_advisor&view_type=list', { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(3000);
    const cbamRow = page.locator('.o_data_row').first();
    if (await cbamRow.count() > 0) {
      await cbamRow.click();
      await page.waitForTimeout(2000);
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_esg_cbam_advisor.png') });
    console.log('✓ Saved 07_esg_cbam_advisor.png');

  } catch (err) {
    console.error('Error during capture:', err);
  } finally {
    await browser.close();
  }
}

main();
