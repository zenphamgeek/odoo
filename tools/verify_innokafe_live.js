const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
const TARGET_URL = 'https://innokafe.insilos.com/';

async function verify() {
    console.log(`[*] Launching Chromium headless to audit ${TARGET_URL}...`);
    const browser = await chromium.launch({ headless: true });
    
    // 1. DESKTOP VIEWPORT AUDIT (1440x900)
    console.log('\n--- 1. DESKTOP VIEWPORT AUDIT (1440x900) ---');
    const desktopContext = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    });
    const desktopPage = await desktopContext.newPage();
    
    const consoleErrors = [];
    const failedRequests = [];

    desktopPage.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        }
    });

    desktopPage.on('requestfailed', req => {
        failedRequests.push(`${req.url()} (${req.failure()?.errorText || 'failed'})`);
    });

    const response = await desktopPage.goto(TARGET_URL, { waitUntil: 'load', timeout: 60000 });
    await desktopPage.waitForTimeout(3000);
    console.log(`[✓] Desktop HTTP Status: ${response.status()}`);

    const pageTitle = await desktopPage.title();
    console.log(`[✓] Page Title: "${pageTitle}"`);

    // Extract key headings
    const h1Text = await desktopPage.$eval('h1', el => el.innerText).catch(() => 'NO_H1');
    console.log(`[✓] Main H1: "${h1Text.replace(/\n+/g, ' ')}"`);

    // Check navbar brand
    const navbarBrand = await desktopPage.$eval('.navbar-brand, #top_menu', el => el.innerText).catch(() => 'NO_NAVBAR');
    console.log(`[✓] Navbar text sample: "${navbarBrand.slice(0, 100).replace(/\n+/g, ' ')}"`);

    // Check rogue Insilos elements
    const hasInsilosHero = await desktopPage.$eval('body', el => el.innerText.includes('Chấm Dứt Ốc Đảo Dữ Liệu')).catch(() => false);
    const hasInsilosMegamenu = await desktopPage.$eval('body', el => el.innerText.includes('Năng Lượng & Lưới Điện Thông Minh')).catch(() => false);
    console.log(`[✓] Rogue Insilos Hero present: ${hasInsilosHero} (Expected: false)`);
    console.log(`[✓] Rogue Insilos Megamenu present: ${hasInsilosMegamenu} (Expected: false)`);

    // Capture Desktop Screenshots
    const desktopHeroPath = path.join(ARTIFACT_DIR, 'innokafe_prod_verified_desktop_hero.png');
    await desktopPage.screenshot({ path: desktopHeroPath, fullPage: false });
    console.log(`[✓] Saved Desktop Hero Screenshot: ${desktopHeroPath}`);

    const desktopFullPagePath = path.join(ARTIFACT_DIR, 'innokafe_prod_verified_desktop_fullpage.png');
    await desktopPage.screenshot({ path: desktopFullPagePath, fullPage: true });
    console.log(`[✓] Saved Desktop Fullpage Screenshot: ${desktopFullPagePath}`);

    // 2. MOBILE VIEWPORT AUDIT (375x812)
    console.log('\n--- 2. MOBILE VIEWPORT AUDIT (375x812) ---');
    const mobileContext = await browser.newContext({
        viewport: { width: 375, height: 812 },
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        isMobile: true,
        hasTouch: true
    });
    const mobilePage = await mobileContext.newPage();
    const mobileResponse = await mobilePage.goto(TARGET_URL, { waitUntil: 'load', timeout: 60000 });
    await mobilePage.waitForTimeout(3000);
    console.log(`[✓] Mobile HTTP Status: ${mobileResponse.status()}`);

    const mobileHeroPath = path.join(ARTIFACT_DIR, 'innokafe_prod_verified_mobile_hero.png');
    await mobilePage.screenshot({ path: mobileHeroPath, fullPage: false });
    console.log(`[✓] Saved Mobile Hero Screenshot: ${mobileHeroPath}`);

    const mobileFullPagePath = path.join(ARTIFACT_DIR, 'innokafe_prod_verified_mobile_fullpage.png');
    await mobilePage.screenshot({ path: mobileFullPagePath, fullPage: true });
    console.log(`[✓] Saved Mobile Fullpage Screenshot: ${mobileFullPagePath}`);

    await browser.close();

    console.log('\n=== AUDIT SUMMARY ===');
    console.log(`Console Errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
        consoleErrors.forEach(err => console.log(`  - ${err}`));
    }
    console.log(`Failed Requests: ${failedRequests.length}`);
    if (failedRequests.length > 0) {
        failedRequests.forEach(req => console.log(`  - ${req}`));
    }

    const success = (
        response.status() === 200 &&
        !hasInsilosHero &&
        !hasInsilosMegamenu &&
        h1Text.includes('Cà Phê')
    );

    if (success) {
        console.log('\n🎉 ALL ACCEPTANCE CRITERIA MET WITH 100% PASS!');
    } else {
        console.log('\n❌ Verification failed against criteria.');
        process.exit(1);
    }
}

verify().catch(err => {
    console.error('Fatal audit error:', err);
    process.exit(1);
});
