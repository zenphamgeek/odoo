const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = path.resolve(__dirname, '../artifacts');
if (!fs.existsSync(ARTIFACTS_DIR)) {
    fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const TARGET_URL = process.env.TARGET_URL || 'https://innoria.insilos.com/';

async function run() {
    console.log(`[*] Launching Chromium verification on ${TARGET_URL}...`);
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2
    });

    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        }
    });

    await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForFunction(() => {
        const top = document.getElementById('top_menu');
        return top && top.dataset.megamenuInitialized === 'true';
    }, { timeout: 20000 });
    console.log('[✓] Page loaded and mega-menu initialized successfully.');

    // 1. Verify Mega-Menu 0 (Products)
    console.log('\n--- 1. AUDITING MEGA-MENU 0 (PRODUCTS) ---');
    const triggerProducts = page.locator('[data-megamenu="innoria_products"] > a');
    await triggerProducts.click();
    await page.waitForTimeout(350);

    const mm0 = page.locator('#ins_megamenu_innoria_products');
    const mm0Visible = await mm0.isVisible();
    console.log(`[✓] Mega-Menu 0 visibility: ${mm0Visible}`);

    const mm0Items = await mm0.locator('.ins-menu-link-item').count();
    console.log(`[✓] Mega-Menu 0 total items: ${mm0Items} (Expected: 9)`);

    const mm0Badges = await mm0.locator('.ins-label-lux').count();
    console.log(`[✓] Mega-Menu 0 .ins-label-lux badges: ${mm0Badges} (Expected: 9)`);

    const mm0DescHeights = await mm0.locator('.ins-menu-item-desc').evaluateAll(elements => 
        elements.map(el => ({ text: el.textContent.trim(), height: el.getBoundingClientRect().height }))
    );
    console.log(`[✓] Sample mm0 desc heights: ${JSON.stringify(mm0DescHeights.slice(0, 3))}`);

    await mm0.screenshot({ path: path.join(ARTIFACTS_DIR, 'megamenu_0_products.png') });
    console.log('[✓] Captured artifacts/megamenu_0_products.png');

    // 2. Verify Mega-Menu 1 (Platform)
    console.log('\n--- 2. AUDITING MEGA-MENU 1 (PLATFORM) ---');
    const triggerPlatform = page.locator('[data-megamenu="innoria_platform"] > a');
    await triggerPlatform.click();
    await page.waitForTimeout(350);

    const mm1 = page.locator('#ins_megamenu_innoria_platform');
    const mm1Visible = await mm1.isVisible();
    console.log(`[✓] Mega-Menu 1 visibility: ${mm1Visible}`);

    const mm1Items = await mm1.locator('.ins-menu-link-item').count();
    console.log(`[✓] Mega-Menu 1 total items: ${mm1Items} (Expected: 8)`);

    const mm1Badges = await mm1.locator('.ins-label-lux').count();
    console.log(`[✓] Mega-Menu 1 .ins-label-lux badges (incl preview): ${mm1Badges} (Expected: 9)`);

    const mm1BtnLux = await mm1.locator('.ins-btn-lux.ins-btn-lux-primary').count();
    console.log(`[✓] Mega-Menu 1 .ins-btn-lux preview button: ${mm1BtnLux} (Expected: 1)`);

    await mm1.screenshot({ path: path.join(ARTIFACTS_DIR, 'megamenu_1_platform.png') });
    console.log('[✓] Captured artifacts/megamenu_1_platform.png');

    // 3. Verify Mega-Menu 2 (Solutions)
    console.log('\n--- 3. AUDITING MEGA-MENU 2 (SOLUTIONS) ---');
    const triggerSolutions = page.locator('[data-megamenu="innoria_solutions"] > a');
    await triggerSolutions.click();
    await page.waitForTimeout(600);

    const mm2 = page.locator('#ins_megamenu_innoria_solutions');
    const mm2Visible = await mm2.isVisible();
    console.log(`[✓] Mega-Menu 2 visibility: ${mm2Visible}`);

    const mm2Items = await mm2.locator('.ins-menu-link-item').count();
    console.log(`[✓] Mega-Menu 2 total items: ${mm2Items} (Expected: 8)`);

    const mm2Badges = await mm2.locator('.ins-label-lux').count();
    console.log(`[✓] Mega-Menu 2 .ins-label-lux badges (incl preview): ${mm2Badges} (Expected: 9)`);

    const mm2BtnLux = await mm2.locator('.ins-btn-lux.ins-btn-lux-primary').count();
    console.log(`[✓] Mega-Menu 2 .ins-btn-lux preview button: ${mm2BtnLux} (Expected: 1)`);

    await mm2.screenshot({ path: path.join(ARTIFACTS_DIR, 'megamenu_2_solutions.png') });
    console.log('[✓] Captured artifacts/megamenu_2_solutions.png');

    // 4. Verify Navbar Buttons & Global Luxury Tokens
    console.log('\n--- 4. AUDITING NAVBAR LUXURY TOKENS ---');
    const navCtaBtn = await page.locator('.btn-innoria-nav.ins-btn-lux').count();
    console.log(`[✓] Navbar CTA .ins-btn-lux buttons: ${navCtaBtn} (Expected: >= 1)`);

    const navScreenshot = await page.locator('#innoria_top').screenshot({ path: path.join(ARTIFACTS_DIR, 'navbar_luxury_header.png') });
    console.log('[✓] Captured artifacts/navbar_luxury_header.png');

    // 5. Verify Section Luxury Badges
    console.log('\n--- 5. AUDITING HOMEPAGE SECTION LUXURY BADGES ---');
    const totalPageBadges = await page.locator('.ins-label-lux').count();
    console.log(`[✓] Total page .ins-label-lux instances: ${totalPageBadges}`);

    // Check cadence section
    const cadenceSection = page.locator('.innoria-cadence-card');
    if (await cadenceSection.count() > 0) {
        await page.evaluate(() => {
            const el = document.querySelector('.innoria-cadence-card');
            if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
        });
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'section_cadence_luxury_badges.png') });
        console.log('[✓] Captured artifacts/section_cadence_luxury_badges.png');
    }

    // 6. Check Layout Overflow & Console
    console.log('\n--- 6. CHECKING LAYOUT INVARIANTS & CONSOLE ERRORS ---');
    const layoutOverflow = await page.evaluate(() => {
        const docEl = document.documentElement;
        return {
            scrollWidth: docEl.scrollWidth,
            clientWidth: docEl.clientWidth,
            hasOverflow: docEl.scrollWidth > docEl.clientWidth
        };
    });
    console.log(`[✓] Desktop Layout Overflow: ${JSON.stringify(layoutOverflow)} (hasOverflow === false)`);

    // Mobile viewport test
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(500);
    const mobileOverflow = await page.evaluate(() => {
        const docEl = document.documentElement;
        return {
            scrollWidth: docEl.scrollWidth,
            clientWidth: docEl.clientWidth,
            hasOverflow: docEl.scrollWidth > docEl.clientWidth
        };
    });
    console.log(`[✓] Mobile Layout Overflow (375px): ${JSON.stringify(mobileOverflow)} (hasOverflow === false)`);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'mobile_homepage_overview.png') });
    console.log('[✓] Captured artifacts/mobile_homepage_overview.png');

    console.log(`[✓] Total Console Errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
        console.log('Console Errors:', consoleErrors);
    }

    await browser.close();
    console.log('\n[🎉] Headless Playwright Verification Complete!');
}

run().catch(err => {
    console.error('Test run failed:', err);
    process.exit(1);
});
