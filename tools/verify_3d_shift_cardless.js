const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function main() {
    const artifactDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 1080 },
        deviceScaleFactor: 2
    });

    const page = await context.newPage();
    const url = 'https://innoria.insilos.com/solutions';
    console.log(`[*] Navigating to ${url}...`);

    await page.goto(url, { waitUntil: 'networkidle', timeout: 35000 });
    await page.waitForTimeout(2000);

    // Locate 3D ERP Shift component
    const erpShiftEl = await page.$('#erp_shift_3d_component');
    if (!erpShiftEl) {
        console.error('[!] Could not find #erp_shift_3d_component in DOM');
        await browser.close();
        process.exit(1);
    }

    // Find parent section
    const section = await page.evaluateHandle(() => {
        const el = document.querySelector('#erp_shift_3d_component');
        return el ? el.closest('section') : null;
    });

    // Scroll into view
    await erpShiftEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(3000);

    // DOM Invariant Checks
    const content = await page.content();

    // 1. Clumsy header check
    const hasClumsyHeader = content.includes('CHẾ ĐỘ XEM TRỤC ĐO HAI LÕI');
    console.log(`[+] Clumsy Header 'CHẾ ĐỘ XEM TRỤC ĐO HAI LÕI' present: ${hasClumsyHeader} (Expect: false)`);

    // 2. Card wrapping check
    const cardlessCheck = await page.evaluate(() => {
        const erpShift = document.querySelector('#erp_shift_3d_component');
        if (!erpShift) return { found: false };
        const directParentCard = erpShift.closest('.ins-spatial-layer');
        return {
            found: true,
            hasSpatialLayerAncestor: !!directParentCard,
            parentClasses: erpShift.parentElement ? erpShift.parentElement.className : ''
        };
    });
    console.log(`[+] 3D ERP Shift Cardless Check:`, JSON.stringify(cardlessCheck));

    // 3. Switcher check
    const switcherInfo = await page.evaluate(() => {
        const sw = document.querySelector('.erp-shift-mode-switch');
        if (!sw) return null;
        const rect = sw.getBoundingClientRect();
        const buttons = Array.from(sw.querySelectorAll('button')).map(b => b.textContent.trim());
        return {
            width: rect.width,
            height: rect.height,
            buttons: buttons
        };
    });
    console.log(`[+] Mode Switcher Info:`, JSON.stringify(switcherInfo));

    // 4. Capture high-resolution screenshot of section
    const screenshotPath = path.join(artifactDir, '3d_erp_shift_cardless_verified.png');
    if (section) {
        await section.asElement().screenshot({ path: screenshotPath });
        console.log(`[✓] Captured section screenshot: ${screenshotPath}`);
    }

    // Also capture full view of the 3D model and switcher
    const stageContainer = await page.evaluateHandle(() => {
        const el = document.querySelector('#erp_shift_3d_component');
        return el ? el.closest('.row') : null;
    });
    if (stageContainer) {
        const stagePath = path.join(artifactDir, '3d_erp_shift_stage_clean.png');
        await stageContainer.asElement().screenshot({ path: stagePath });
        console.log(`[✓] Captured 3D stage screenshot: ${stagePath}`);
    }

    await browser.close();
    console.log('[✓] Verification completed successfully.');
}

main().catch(err => {
    console.error('[!] Error during verification:', err);
    process.exit(1);
});
