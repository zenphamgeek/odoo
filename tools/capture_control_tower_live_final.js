#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');

const TARGET_URL = 'https://innoria.com';
const DB_NAME = 'innoria_prod';
const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function main() {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const page = await context.newPage();

    console.log('[*] Authenticating on innoria_prod...');
    await page.request.post(`${TARGET_URL}/web/session/authenticate`, {
        data: {
            jsonrpc: '2.0',
            params: { db: DB_NAME, login: 'admin', password: 'admin' }
        },
        timeout: 15000
    });

    console.log('[*] Navigating to Sales Quotations...');
    await page.goto(`${TARGET_URL}/insilos/action-sale.action_quotations_with_onboarding`, {
        waitUntil: 'domcontentloaded',
        timeout: 30000
    });
    await page.waitForTimeout(4000);
    await page.waitForSelector('.o_list_view, .o_content', { timeout: 15000 });

    const salesImg = path.join(ARTIFACTS_DIR, 'sales_quotations_live_final.png');
    await page.screenshot({ path: salesImg, fullPage: true });
    console.log(`[✓] Captured Sales Quotations: ${salesImg}`);

    await browser.close();
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
