const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function main() {
    console.log('[*] Launching Chromium browser...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const page = await context.newPage();

    // 1. Capture Homepage 4 Pillars
    console.log('[*] Navigating to https://innoria.insilos.com/ ...');
    await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(4000);

    const pillarsSection = await page.$('.s_innoria_pillars_section');
    if (pillarsSection) {
        await pillarsSection.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1500);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, 'homepage_pillars_zencode_insilos.png')
        });
        console.log('[✓] Captured homepage_pillars_zencode_insilos.png');
    }

    // 2. Capture ZenCode Product Page
    console.log('[*] Navigating to https://innoria.insilos.com/zencode ...');
    await page.goto('https://innoria.insilos.com/zencode', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(3000);

    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'zencode_page_hero.png')
    });
    console.log('[✓] Captured zencode_page_hero.png');

    // Scroll to comparison matrix
    const zencodeMatrix = await page.$('table');
    if (zencodeMatrix) {
        await zencodeMatrix.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1500);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, 'zencode_page_comparison.png')
        });
        console.log('[✓] Captured zencode_page_comparison.png');
    }

    // 3. Capture INSILOS Product Page
    console.log('[*] Navigating to https://innoria.insilos.com/insilos ...');
    await page.goto('https://innoria.insilos.com/insilos', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(3000);

    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'insilos_page_hero.png')
    });
    console.log('[✓] Captured insilos_page_hero.png');

    // Scroll to 3D ERP Core / Shift section
    const erpShift = await page.$('#erp-core-3d');
    if (erpShift) {
        await erpShift.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1500);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, 'insilos_page_3d_core.png')
        });
        console.log('[✓] Captured insilos_page_3d_core.png');
    }

    // Scroll to operational tabs
    const operationalTabs = await page.$('#tab-acc');
    if (operationalTabs) {
        await operationalTabs.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1500);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, 'insilos_page_operational_tabs.png')
        });
        console.log('[✓] Captured insilos_page_operational_tabs.png');
    }

    await browser.close();
    console.log('[✓] All screenshot verification captures completed successfully.');
}

main().catch(err => {
    console.error('[!] Error during capture:', err);
    process.exit(1);
});
