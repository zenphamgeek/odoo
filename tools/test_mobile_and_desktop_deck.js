const { chromium } = require('playwright');

(async () => {
    console.log('[*] Testing Desktop & Mobile 3D Deck with Touch Orbit...');
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const outputDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

    // 1. Mobile iPhone Test
    console.log('[*] Testing Mobile Viewport (375x812, hasTouch: true)...');
    const mobileContext = await browser.newContext({
        viewport: { width: 375, height: 812 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true
    });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await mobilePage.waitForTimeout(3000);

    const mobileStage = await mobilePage.$('#stageCard');
    if (mobileStage) {
        await mobileStage.scrollIntoViewIfNeeded();
        await mobilePage.waitForTimeout(800);
        await mobileStage.screenshot({ path: `${outputDir}/deck_mobile_resting.png` });
        console.log('[✓] Captured deck_mobile_resting.png');

        // Test touch tap on Slab 1
        await mobilePage.evaluate(() => {
            const slab1 = document.querySelector('#slab-1');
            if (slab1) slab1.dispatchEvent(new Event('touchstart', { bubbles: true }));
        });
        await mobilePage.waitForTimeout(800);
        await mobileStage.screenshot({ path: `${outputDir}/deck_mobile_slab1_tapped.png` });
        console.log('[✓] Captured deck_mobile_slab1_tapped.png');
    }
    await mobileContext.close();

    // 2. Desktop Full Architecture Deck
    console.log('[*] Testing Desktop Viewport (1440x900)...');
    const desktopContext = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2
    });
    const desktopPage = await desktopContext.newPage();
    await desktopPage.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await desktopPage.waitForTimeout(3000);

    const desktopDeck = await desktopPage.$('#architecture_deck');
    if (desktopDeck) {
        await desktopDeck.scrollIntoViewIfNeeded();
        await desktopPage.waitForTimeout(800);
        await desktopDeck.screenshot({ path: `${outputDir}/deck_desktop_final_resting.png` });
        console.log('[✓] Captured deck_desktop_final_resting.png');

        // Select Slab 2 (AI)
        await desktopPage.evaluate(() => {
            const slab2 = document.querySelector('#slab-2');
            if (slab2) slab2.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        });
        await desktopPage.waitForTimeout(800);
        await desktopDeck.screenshot({ path: `${outputDir}/deck_desktop_final_slab2_ai.png` });
        console.log('[✓] Captured deck_desktop_final_slab2_ai.png');
    }
    await desktopContext.close();

    await browser.close();
    console.log('[✓] Mobile and Desktop test completed successfully!');
})();
