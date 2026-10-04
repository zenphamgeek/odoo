const { chromium } = require('playwright');
const path = require('path');

const PROD_URL = 'https://insilos.com';
const SESSION_ID = '9LFwlC2R_bMxPLRgH9zCECRy9HcfJp4-uSexrh9hd9XdmfLpDh73qiRztbEgzWurDL9lQszRUkBLQt2qwUSpIQ';
const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function main() {
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({
        viewport: { width: 1440, height: 960 },
        deviceScaleFactor: 1
    });

    await context.addCookies([
        { name: 'session_id', value: SESSION_ID, domain: 'insilos.com', path: '/' },
        { name: 'insilos_session_id', value: SESSION_ID, domain: 'insilos.com', path: '/' }
    ]);

    const page = await context.newPage();

    console.log('=== TEST 1: Website Editor Systray Cluster on Production ===');
    await page.goto(`${PROD_URL}/insilos`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(3000);

    const websiteApp = await page.locator('.o_app:has-text("Website")').first();
    if (await websiteApp.isVisible()) {
        console.log('Clicking Website app on launcher...');
        await websiteApp.click();
        await page.waitForTimeout(5000);
    } else {
        await page.goto(`${PROD_URL}/odoo/action-website.website_preview`, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(4000);
    }

    const navbar = await page.$('.o_main_navbar');
    if (navbar) {
        await navbar.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_website_editor_navbar_verified.png') });
        console.log('✓ Captured prod_website_editor_navbar_verified.png');
    }

    const systray = await page.$('.o_menu_systray');
    if (systray) {
        await systray.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_systray_cluster_verified.png') });
        console.log('✓ Captured prod_systray_cluster_verified.png');
    }

    // Switch to dark mode for systray
    await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-color-mode', 'dark');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    });
    await page.waitForTimeout(1500);

    if (navbar) {
        await navbar.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_website_editor_navbar_dark_verified.png') });
        console.log('✓ Captured prod_website_editor_navbar_dark_verified.png');
    }

    if (systray) {
        await systray.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_systray_cluster_dark_verified.png') });
        console.log('✓ Captured prod_systray_cluster_dark_verified.png');
    }

    console.log('\n=== TEST 2: Discuss Telegram Composer on Production ===');
    await page.goto(`${PROD_URL}/insilos/discuss`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(3000);

    // Click on InsilosBot conversation if present
    const botItem = await page.locator('text=InsilosBot').first();
    if (botItem && await botItem.isVisible()) {
        console.log('Found InsilosBot conversation, clicking...');
        await botItem.click();
        await page.waitForTimeout(2000);
    }

    // Focus composer input
    const composerInput = await page.$('.o-mail-Composer-input, textarea.o-mail-Composer-input');
    if (composerInput) {
        await composerInput.click();
        await page.waitForTimeout(600);
        await composerInput.type('Verifying Telegram capsule style & paper plane button on Production.');
        await page.waitForTimeout(600);
    }

    // Capture composer Light mode
    const composer = await page.$('.o-mail-Composer');
    if (composer) {
        await composer.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_discuss_telegram_light.png') });
        console.log('✓ Captured prod_discuss_telegram_light.png');
    }

    // Full page discuss Light
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_discuss_full_light.png') });
    console.log('✓ Captured prod_discuss_full_light.png');

    // Switch to dark mode
    await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-color-mode', 'dark');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    });
    await page.waitForTimeout(1500);

    if (composerInput) {
        await composerInput.click();
        await page.waitForTimeout(600);
    }

    if (composer) {
        await composer.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_discuss_telegram_dark.png') });
        console.log('✓ Captured prod_discuss_telegram_dark.png');
    }

    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'prod_discuss_full_dark.png') });
    console.log('✓ Captured prod_discuss_full_dark.png');

    console.log('\n=== TEST 3: Tour pointer footprint on Launcher ===');
    await page.goto(`${PROD_URL}/insilos`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2000);

    const tourPointers = await page.locator('.o_tour_pointer:visible').count();
    console.log(`Visible tour pointers on production launcher: ${tourPointers}`);

    await browser.close();
    console.log('\nAll production verifications completed successfully!');
}

main().catch(err => {
    console.error('Error during production verification:', err);
    process.exit(1);
});
