const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const outDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/sections';
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    console.log('Navigating to https://innoria.com/solutions...');
    await page.goto('https://innoria.com/solutions', { waitUntil: 'networkidle', timeout: 35000 });
    await page.waitForTimeout(2000);

    const shiftSec = await page.$('.s_innoria_3d_erp_shift');
    if (shiftSec) {
        await shiftSec.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);
        await shiftSec.screenshot({ path: `${outDir}/verified_3d_shift_clean.png` });
        console.log('Captured verified_3d_shift_clean.png');
    } else {
        console.log('s_innoria_3d_erp_shift not found!');
    }

    console.log('Navigating to https://innoria.com/industries...');
    await page.goto('https://innoria.com/industries', { waitUntil: 'networkidle', timeout: 35000 });
    await page.waitForTimeout(2000);

    const videoEl = await page.$('video source[src*="cctv_cam02_welding_ss400"], video[poster*="cctv_cam02_welding_poster"]');
    if (videoEl) {
        const parent = await videoEl.evaluateHandle(el => el.closest('section') || el.closest('.row') || el.parentElement.parentElement);
        await parent.asElement().scrollIntoViewIfNeeded();
        await page.waitForTimeout(1500);
        await parent.asElement().screenshot({ path: `${outDir}/verified_ai_vision_welding.png` });
        console.log('Captured verified_ai_vision_welding.png via video selector');
    } else {
        console.log('Falling back to finding hero section...');
        const visionSec = await page.$('.s_insilos_spatial_hero, section:has(video)');
        if (visionSec) {
            await visionSec.scrollIntoViewIfNeeded();
            await page.waitForTimeout(1500);
            await visionSec.screenshot({ path: `${outDir}/verified_ai_vision_welding.png` });
            console.log('Captured verified_ai_vision_welding.png via section selector');
        }
    }

    await browser.close();
    console.log('All verification captures completed successfully!');
})();
