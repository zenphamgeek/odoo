const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('http://localhost:28069/web/login', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.screenshot({ 
        path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_3d_hero_showcase.png', 
        fullPage: true 
    });
    
    // Also click DB dropdown button to capture open state
    const dbBtn = await page.$('#insilosDbSelectorDropdown');
    if (dbBtn) {
        await dbBtn.click();
        await page.waitForTimeout(500);
        await page.screenshot({ 
            path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_3d_hero_showcase_db_open.png', 
            fullPage: true 
        });
    }
    await browser.close();
    console.log('Screenshots captured successfully!');
})();
