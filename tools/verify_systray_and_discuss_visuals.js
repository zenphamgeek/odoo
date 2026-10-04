const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function main() {
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    console.log('1. Authenticating admin session on odoo20_dev...');
    const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
        data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });
    if (!authRes.ok()) throw new Error('Authentication failed');
    console.log('✓ Successfully authenticated.\n');

    const artifactDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

    console.log('2. Navigating to Website Preview / Editor ...');
    await page.goto('http://localhost:28069/insilos/website', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(4000);

    // Screenshot of navbar
    const navbar = await page.$('.o_main_navbar, .o_navbar');
    if (navbar) {
        await navbar.screenshot({ path: path.join(artifactDir, 'website_editor_navbar_verified.png') });
        console.log('✓ Saved website_editor_navbar_verified.png');
    }
    
    // Screenshot of systray cluster
    const systray = await page.$('.o_menu_systray');
    if (systray) {
        await systray.screenshot({ path: path.join(artifactDir, 'systray_cluster_verified.png') });
        console.log('✓ Saved systray_cluster_verified.png');
    }

    // Inspect geometry of Published vs User Menu
    const clusterMetrics = await page.evaluate(() => {
        const userMenu = document.querySelector('.o_user_menu');
        const publish = document.querySelector('.o_website_publish_container');
        const mobile = document.querySelector('.o_mobile_preview');
        const newBtn = document.querySelector('.o_new_content_container');
        const editBtn = document.querySelector('.o_edit_website_container');

        const rect = el => el ? el.getBoundingClientRect() : null;
        return {
            userMenu: rect(userMenu),
            publish: rect(publish),
            mobile: rect(mobile),
            newBtn: rect(newBtn),
            editBtn: rect(editBtn),
        };
    });
    console.log('Cluster layout metrics:', JSON.stringify(clusterMetrics, null, 2));

    // Full page screenshot of website preview
    await page.screenshot({ path: path.join(artifactDir, 'website_preview_live_verified.png') });
    console.log('✓ Saved website_preview_live_verified.png');

    console.log('\n3. Navigating to Discuss ...');
    await page.goto('http://localhost:28069/insilos/discuss', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);

    // Focus composer to see Telegram focus ring
    const composerInput = await page.$('.o-mail-Composer-input, textarea.o-mail-Composer-input, .o-mail-Composer-html');
    if (composerInput) {
        await composerInput.click();
        await page.waitForTimeout(600);
    }

    // Capture composer container
    const composer = await page.$('.o-mail-Composer');
    if (composer) {
        await composer.screenshot({ path: path.join(artifactDir, 'discuss_composer_verified.png') });
        console.log('✓ Saved discuss_composer_verified.png');
    }

    // Full Discuss screenshot
    await page.screenshot({ path: path.join(artifactDir, 'discuss_live_verified.png') });
    console.log('✓ Saved discuss_live_verified.png');

    console.log('\n4. Navigating to App Launcher ...');
    await page.goto('http://localhost:28069/insilos', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    const tourPointerCount = await page.locator('.o_tour_pointer:visible').count();
    console.log(`Visible tour pointers on launcher: ${tourPointerCount}`);

    await page.screenshot({ path: path.join(artifactDir, 'launcher_live_verified_notour.png') });
    console.log('✓ Saved launcher_live_verified_notour.png');

    await browser.close();
    console.log('\nAll visual verifications completed successfully!');
}

main().catch(err => {
    console.error('Error during verification:', err);
    process.exit(1);
});
