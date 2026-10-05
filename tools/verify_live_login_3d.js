const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('PAGE ERROR:', msg.text());
        }
    });

    console.log('Navigating to http://localhost:28069/web/login...');
    await page.goto('http://localhost:28069/web/login', { waitUntil: 'networkidle' });

    // Wait 2 seconds for 3D animation loop
    await page.waitForTimeout(2000);

    const canvas = await page.$('#insilosLoginDigitalTwinCanvas');
    if (!canvas) {
        console.error('Canvas #insilosLoginDigitalTwinCanvas not found!');
        process.exit(1);
    }
    console.log('Canvas found!');

    // Capture the login card
    const loginCard = await page.$('.insilos_auth_portal_card') || await page.$('.insilos_login_card') || await page.$('.card');
    if (loginCard) {
        const heroPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_3d_hero_container.png';
        await loginCard.screenshot({ path: heroPath });
        console.log('Login portal card captured at:', heroPath);
    }

    // Capture full screenshot
    const fullPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_3d_hero_insilos_databases.png';
    await page.screenshot({ path: fullPath, fullPage: true });
    console.log('Full page captured at:', fullPath);

    // Capture footer block specifically
    const footerBlock = await page.$('.auth_footer_block');
    if (footerBlock) {
        const footerPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_footer_db_selector.png';
        await footerBlock.screenshot({ path: footerPath });
        console.log('Footer block captured at:', footerPath);
    }

    // Click dropdown button to verify dropup menu
    const dbBtn = await page.$('#insilosDbSelectorDropdown');
    if (dbBtn) {
        console.log('Found #insilosDbSelectorDropdown! Clicking...');
        await dbBtn.click();
        await page.waitForTimeout(500);

        if (loginCard) {
            const openCardPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_footer_db_selector_open.png';
            await loginCard.screenshot({ path: openCardPath });
            console.log('Open dropup captured at:', openCardPath);
        }
    } else {
        console.log('Single database mode: #insilosDbSelectorDropdown not present (single db link active)');
    }

    await browser.close();
    console.log('Verification finished successfully!');
})();
