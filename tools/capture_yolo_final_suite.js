const { chromium } = require('playwright');
const path = require('path');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

(async () => {
    console.log('=== CAPTURING FINAL SUITE FOR YOLO DEFECT INSPECTION SIMULATOR ===');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1
    });

    const page = await context.newPage();

    try {
        await page.goto('https://innoria.insilos.com/industries', { waitUntil: 'networkidle', timeout: 45000 });
        const sec = page.locator('#innoria_yolo_simulator_section');
        await sec.waitFor({ timeout: 15000 });

        const box = await sec.boundingBox();
        console.log('[*] Section Bounding Box:', box);

        // Smooth scroll to position section perfectly in viewport
        await page.evaluate((y) => window.scrollTo({ top: y - 70, behavior: 'instant' }), box.y);
        await page.waitForTimeout(1000);

        // Capture State 1: PCB Electronics (Defect Injected)
        console.log('[*] Capturing State 1: PCB Electronics (Defect Injected)...');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'yolo_final_state1_pcb_defect.png') });

        // Capture State 2: Nominal Pass Mode (Toggle OFF)
        console.log('[*] Capturing State 2: Nominal Pass Mode...');
        await page.click('#toggleDefectInjection');
        await page.waitForTimeout(600);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'yolo_final_state2_nominal_pass.png') });

        // Toggle back ON
        await page.click('#toggleDefectInjection');
        await page.waitForTimeout(300);

        // Capture State 3: Automotive Stamping
        console.log('[*] Capturing State 3: Automotive Stamping...');
        await page.click('[data-inspection-target="auto_stamping"]');
        await page.waitForTimeout(800);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'yolo_final_state3_auto_stamping.png') });

        // Capture State 4: Solar Silicon Wafer
        console.log('[*] Capturing State 4: Solar Silicon Wafer...');
        await page.click('[data-inspection-target="solar_wafer"]');
        await page.waitForTimeout(800);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'yolo_final_state4_solar_wafer.png') });

        // Capture State 5: Weld Seam SS400
        console.log('[*] Capturing State 5: Weld Seam SS400...');
        await page.click('[data-inspection-target="weld_seam"]');
        await page.waitForTimeout(800);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, 'yolo_final_state5_weld_seam.png') });

        console.log('=== ALL 5 HIGH-RES SCREENSHOTS CAPTURED SUCCESSFULLY ===');
    } catch (e) {
        console.error('[!] Error:', e);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
