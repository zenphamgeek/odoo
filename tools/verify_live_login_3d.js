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

    // Wait 2.5 seconds for 3D animation loop
    await page.waitForTimeout(2500);

    const canvas = await page.$('#insilosLoginDigitalTwinCanvas');
    if (!canvas) {
        console.error('Canvas #insilosLoginDigitalTwinCanvas not found!');
        process.exit(1);
    }
    console.log('Canvas found!');

    // Capture full screenshot
    const fullPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_3d_hero_insilos_databases.png';
    await page.screenshot({ path: fullPath, fullPage: true });
    console.log('Full page captured at:', fullPath);

    // Capture the login card / hero container
    const heroCard = await page.$('.insilos_login_card') || await page.$('.card') || await page.$('.insilos_login_3d_container');
    if (heroCard) {
        const heroPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_3d_hero_container.png';
        await heroCard.screenshot({ path: heroPath });
        console.log('Hero container captured at:', heroPath);
    }

    await browser.close();
    console.log('Verification finished successfully!');
})();
