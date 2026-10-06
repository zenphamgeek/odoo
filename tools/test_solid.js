const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
    const page = await context.newPage();
    console.log('Navigating to https://innoria.insilos.com/ ...');
    await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);

    const stageCard = await page.$('#stageCard');
    if (!stageCard) {
        console.error('stageCard not found!');
        await browser.close();
        return;
    }

    await stageCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);

    // 1. Capture Native Resting State
    await stageCard.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/live_deck_native_resting.png' });
    console.log('Saved live_deck_native_resting.png');

    // 2. Trigger Pulled Out on Slab 1
    await page.evaluate(() => {
        const slab1 = document.querySelector('#slab-1');
        if (slab1) {
            slab1.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        }
    });
    await page.waitForTimeout(1000);

    await stageCard.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/live_deck_native_pulled.png' });
    console.log('Saved live_deck_native_pulled.png');

    await browser.close();
    console.log('Finished successfully!');
})();
