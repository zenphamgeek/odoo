const { chromium } = require('playwright');

(async () => {
    console.log('[*] Launching headless browser for comprehensive 3D Deck verification...');
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
    const page = await context.newPage();

    const outputDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

    console.log('[*] Navigating to https://innoria.insilos.com/ ...');
    await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(3000);

    const stageCard = await page.$('#stageCard');
    const architectureDeck = await page.$('#architecture_deck');
    if (!stageCard || !architectureDeck) {
        console.error('[-] 3D Deck component not found!');
        await browser.close();
        process.exit(1);
    }

    await architectureDeck.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);

    // 1. Capture Full Architecture Deck Section in Resting State
    await architectureDeck.screenshot({ path: `${outputDir}/deck_full_resting.png` });
    console.log('[✓] Captured deck_full_resting.png');

    // 2. Test Pulling Slab 0 (No-Code)
    await page.evaluate(() => {
        const slab0 = document.querySelector('#slab-0');
        if (slab0) slab0.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(800);
    await stageCard.screenshot({ path: `${outputDir}/deck_slab0_pulled.png` });
    console.log('[✓] Captured deck_slab0_pulled.png');

    // 3. Test Pulling Slab 1 (Platform Services)
    await page.evaluate(() => {
        const slab1 = document.querySelector('#slab-1');
        if (slab1) slab1.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(800);
    await stageCard.screenshot({ path: `${outputDir}/deck_slab1_pulled.png` });
    console.log('[✓] Captured deck_slab1_pulled.png');

    // 4. Test Pulling Slab 2 (AI)
    await page.evaluate(() => {
        const slab2 = document.querySelector('#slab-2');
        if (slab2) slab2.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(800);
    await stageCard.screenshot({ path: `${outputDir}/deck_slab2_pulled.png` });
    console.log('[✓] Captured deck_slab2_pulled.png');

    // 5. Test Pulling Slab 3 (ERP & Data Lake)
    await page.evaluate(() => {
        const slab3 = document.querySelector('#slab-3');
        if (slab3) slab3.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(800);
    await stageCard.screenshot({ path: `${outputDir}/deck_slab3_pulled.png` });
    console.log('[✓] Captured deck_slab3_pulled.png');

    // 6. Test Exploded View
    const btnExplode = await page.$('#btnExplode');
    if (btnExplode) {
        await btnExplode.click();
        await page.waitForTimeout(1000);
        await stageCard.screenshot({ path: `${outputDir}/deck_exploded.png` });
        console.log('[✓] Captured deck_exploded.png');
        // Unexplode
        await btnExplode.click();
        await page.waitForTimeout(500);
    }

    // 7. Test Drag Orbit Interaction
    const box = await stageCard.boundingBox();
    if (box) {
        const startX = box.x + box.width / 2;
        const startY = box.y + box.height / 2;
        await page.mouse.move(startX, startY);
        await page.mouse.down();
        await page.mouse.move(startX + 120, startY - 60, { steps: 15 });
        await page.mouse.up();
        await page.waitForTimeout(800); // Allow spring inertia to settle
        await stageCard.screenshot({ path: `${outputDir}/deck_drag_orbit.png` });
        console.log('[✓] Captured deck_drag_orbit.png');
    }

    // 8. Test Reset Button
    const btnResetView = await page.$('#btnResetView');
    if (btnResetView) {
        await btnResetView.click();
        await page.waitForTimeout(800);
        await stageCard.screenshot({ path: `${outputDir}/deck_reset_settled.png` });
        console.log('[✓] Captured deck_reset_settled.png');
    }

    await browser.close();
    console.log('[✓] All interactive tests completed successfully!');
})();
