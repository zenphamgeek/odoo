const { chromium } = require('playwright');
const path = require('path');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function run() {
    console.log('[*] Launching Chromium browser for targeted Innoria Hero & 3D Deck verification...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const page = await context.newPage();

    page.on('console', msg => {
        console.log(`[Browser Console ${msg.type()}] ${msg.text()}`);
    });

    console.log('[*] Navigating to http://innoria.localhost:28070/ ...');
    await page.goto('http://innoria.localhost:28070/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    const heroSection = page.locator('#innoria_hero_cover');
    await heroSection.waitFor({ state: 'visible', timeout: 10000 });
    const heroBox = await heroSection.boundingBox();

    // Check if slider instance exists
    const sliderReady = await page.evaluate(() => {
        return !!window.innoriaHeroSlider;
    });
    console.log('[*] window.innoriaHeroSlider exists:', sliderReady);

    // 1. Capture Slide 0: DIGIFORCE
    console.log('[*] Switching to Slide 0 (DIGIFORCE)...');
    await page.evaluate(() => {
        if (window.innoriaHeroSlider) window.innoriaHeroSlider.goToSlide(0);
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_hero_slide0_digiforce.png'),
        clip: heroBox || undefined
    });
    console.log('[✓] Captured local_hero_slide0_digiforce.png');

    // 2. Capture Slide 1: MOJO AI
    console.log('[*] Switching to Slide 1 (MOJO AI)...');
    await page.evaluate(() => {
        if (window.innoriaHeroSlider) window.innoriaHeroSlider.goToSlide(1);
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_hero_slide1_mojo_ai.png'),
        clip: heroBox || undefined
    });
    console.log('[✓] Captured local_hero_slide1_mojo_ai.png');

    // 3. Capture Slide 2: MOJOVERSE
    console.log('[*] Switching to Slide 2 (MOJOVERSE)...');
    await page.evaluate(() => {
        if (window.innoriaHeroSlider) window.innoriaHeroSlider.goToSlide(2);
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_hero_slide2_mojoverse.png'),
        clip: heroBox || undefined
    });
    console.log('[✓] Captured local_hero_slide2_mojoverse.png');

    // 4. Capture Slide 3: INTELLIGENT ERP
    console.log('[*] Switching to Slide 3 (INTELLIGENT ERP)...');
    await page.evaluate(() => {
        if (window.innoriaHeroSlider) window.innoriaHeroSlider.goToSlide(3);
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_hero_slide3_intelligent_erp.png'),
        clip: heroBox || undefined
    });
    console.log('[✓] Captured local_hero_slide3_intelligent_erp.png');

    // 5. Test HUD controls (Play/Pause & Next)
    console.log('[*] Testing HUD Next button...');
    await page.click('#heroNextBtn');
    await page.waitForTimeout(800);
    const currIndexAfterNext = await page.evaluate(() => window.innoriaHeroSlider ? window.innoriaHeroSlider.currentIndex : -1);
    console.log('[✓] Current slide index after clicking Next:', currIndexAfterNext);

    // =========================================================================
    // 3D ARCHITECTURE DECK VERIFICATION
    // =========================================================================
    console.log('[*] Scrolling to 3D Architecture Deck...');
    const deckSection = page.locator('#architecture_deck');
    await deckSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1500);
    const deckBox = await deckSection.boundingBox();

    // Default State (All 4 summary cards visible, all slabs in deck)
    await page.evaluate(() => {
        const resetBtn = document.querySelector('#btnResetView');
        if (resetBtn) resetBtn.click();
    });
    await page.waitForTimeout(800);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_3d_deck_default_dark.png'),
        clip: deckBox || undefined
    });
    console.log('[✓] Captured local_3d_deck_default_dark.png');

    // Layer 0: Hover Slab 0 (No-Code Platform) -> Pull out slab & show Deep Panel 0
    console.log('[*] Triggering Layer 0 (No-Code Platform) pull-out...');
    await page.evaluate(() => {
        const slab0 = document.querySelector('#slab-0');
        if (slab0) slab0.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_3d_deck_hover_slab0_nocode.png'),
        clip: deckBox || undefined
    });
    console.log('[✓] Captured local_3d_deck_hover_slab0_nocode.png');

    // Layer 1: Hover Slab 1 (Platform Services) -> Pull out slab & show Deep Panel 1
    console.log('[*] Triggering Layer 1 (Platform Services) pull-out...');
    await page.evaluate(() => {
        const slab1 = document.querySelector('#slab-1');
        if (slab1) slab1.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_3d_deck_hover_slab1_services.png'),
        clip: deckBox || undefined
    });
    console.log('[✓] Captured local_3d_deck_hover_slab1_services.png');

    // Layer 2: Hover Slab 2 (Artificial Intelligence) -> Pull out slab & show Deep Panel 2
    console.log('[*] Triggering Layer 2 (Artificial Intelligence) pull-out...');
    await page.evaluate(() => {
        const slab2 = document.querySelector('#slab-2');
        if (slab2) slab2.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_3d_deck_hover_slab2_ai.png'),
        clip: deckBox || undefined
    });
    console.log('[✓] Captured local_3d_deck_hover_slab2_ai.png');

    // Layer 3: Hover Slab 3 (Data Lake & Core ERP) -> Pull out slab & show Deep Panel 3
    console.log('[*] Triggering Layer 3 (Data Lake & Core ERP) pull-out...');
    await page.evaluate(() => {
        const slab3 = document.querySelector('#slab-3');
        if (slab3) slab3.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    });
    await page.waitForTimeout(1000);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'local_3d_deck_hover_slab3_data_erp.png'),
        clip: deckBox || undefined
    });
    console.log('[✓] Captured local_3d_deck_hover_slab3_data_erp.png');

    // Reset back to summary cards
    await page.evaluate(() => {
        const resetBtn = document.querySelector('#btnResetView');
        if (resetBtn) resetBtn.click();
    });
    await page.waitForTimeout(600);

    await browser.close();
    console.log('[✓] ALL CAPTURES AND VERIFICATIONS COMPLETED SUCCESSFULLY!');
}

run().catch(err => {
    console.error('Fatal test error:', err);
    process.exit(1);
});
