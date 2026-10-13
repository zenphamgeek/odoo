const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function main() {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        locale: 'en-US'
    });
    const page = await context.newPage();

    console.log('Navigating to http://localhost:28069/web/login...');
    await page.goto('http://localhost:28069/web/login', { waitUntil: 'networkidle', timeout: 30000 });

    console.log('Logging in as admin...');
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');

    console.log('Waiting for WebClient home / navbar...');
    await page.waitForSelector('.o_main_navbar, .o_navbar', { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log('Locating user menu toggle...');
    // Look for user menu in navbar/systray
    const userMenuBtn = await page.locator('.o_user_menu button, .o_user_menu .dropdown-toggle, button[aria-label="User menu"], .o_menu_systray .o_user_menu').first();
    await userMenuBtn.click();
    await page.waitForTimeout(1000);

    console.log('Clicking Preferences...');
    // In user dropdown, find Preferences option (data-menu="settings" or text containing Preferences / Tùy chọn)
    const prefOption = await page.locator('.dropdown-menu .dropdown-item:has-text("Preferences"), .dropdown-menu .dropdown-item[data-menu="settings"], .dropdown-menu .dropdown-item:has-text("Tùy chọn")').first();
    await prefOption.click();

    console.log('Waiting for Preferences modal dialog...');
    await page.waitForSelector('.modal-dialog, .modal.show', { timeout: 15000 });
    await page.waitForTimeout(2000);

    // Extract modal dialog content
    const modal = page.locator('.modal-dialog, .modal.show').first();
    const modalText = await modal.innerText();
    console.log('=== Modal Dialog Content Snippet ===');
    console.log(modalText.substring(0, 500));

    // Check for "In Odoo" or "Trong Odoo"
    const hasInOdoo = /in\s+odoo/i.test(modalText);
    const hasInInsilos = /in\s+insilos/i.test(modalText);
    const hasTrongOdoo = /trong\s+odoo/i.test(modalText);
    const hasTrongInsilos = /trong\s+insilos/i.test(modalText);

    console.log('\n=== Brand Detection Results ===');
    console.log('Contains "In Odoo":', hasInOdoo);
    console.log('Contains "In Insilos":', hasInInsilos);
    console.log('Contains "Trong Odoo":', hasTrongOdoo);
    console.log('Contains "Trong Insilos":', hasTrongInsilos);

    // Take screenshot
    const screenshotPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/user_preferences_verified.png';
    await modal.screenshot({ path: screenshotPath });
    console.log(`Saved screenshot to: ${screenshotPath}`);

    // Radio selection check
    const radioLabels = await modal.locator('label, .form-check-label, .o_radio_item').allInnerTexts();
    console.log('Radio/Form labels:', radioLabels.filter(t => /email|insilos|odoo/i.test(t)));

    await browser.close();

    if (hasInOdoo || hasTrongOdoo) {
        console.error('FAIL: Brand leak detected in User Preferences modal!');
        process.exit(1);
    }

    if (!hasInInsilos && !hasTrongInsilos) {
        console.warn('WARNING: Neither "In Insilos" nor "Trong Insilos" was found in modal text.');
    } else {
        console.log('SUCCESS: "In Insilos" verified in User Preferences modal!');
    }
}

main().catch(err => {
    console.error('Script Error:', err);
    process.exit(1);
});
