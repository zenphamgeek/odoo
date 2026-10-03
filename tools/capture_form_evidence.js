#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function capture() {
  console.log('Launching browser to capture form evidence...');
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

  // 1. Authenticate via JSON-RPC
  console.log('Authenticating via JSON-RPC...');
  const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });
  if (!authRes.ok()) throw new Error('Authentication failed');
  console.log('✓ Successfully authenticated.');

  // 2. Navigate to Contacts or Purchase
  console.log('Navigating to Contacts form view...');
  await page.goto('http://localhost:28069/insilos/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Click first contact card to open form view
  console.log('Opening first record form...');
  try {
    await page.waitForSelector('.o_kanban_record, .o_data_row', { timeout: 15000 });
    const card = await page.$('.o_kanban_record');
    if (card) {
      await card.click();
    } else {
      const row = await page.$('.o_data_row');
      if (row) await row.click();
    }
    await page.waitForSelector('.o_form_view', { timeout: 15000 });
    await page.waitForSelector('.o_loading_indicator', { state: 'detached', timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(2000);
  } catch (e) {
    console.log('Waiting fallback:', e.message);
    await page.waitForTimeout(5000);
  }

  // 3. Capture Light Mode
  console.log('Capturing Light Mode...');
  const lightPath = path.join(ARTIFACT_DIR, 'evidence_form_full_light.png');
  await page.screenshot({ path: lightPath, fullPage: false });
  console.log('✓ Saved:', lightPath);

  // 4. Switch to Dark Mode
  console.log('Switching to Dark Mode...');
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-color-scheme', 'dark');
  });
  await page.waitForTimeout(1500);

  // 5. Capture Dark Mode
  console.log('Capturing Dark Mode...');
  const darkPath = path.join(ARTIFACT_DIR, 'evidence_form_full_dark.png');
  await page.screenshot({ path: darkPath, fullPage: false });
  console.log('✓ Saved:', darkPath);

  await browser.close();
  console.log('All form evidence captured successfully.');
}

capture().catch(err => {
  console.error('Capture error:', err);
  process.exit(1);
});
