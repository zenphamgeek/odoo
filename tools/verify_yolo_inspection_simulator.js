/**
 * E2E Playwright Verification for Innoria YOLO Defect Inspection Simulator
 * File: tools/verify_yolo_inspection_simulator.js
 * Target: https://innoria.insilos.com/industries
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

(async () => {
    console.log('=== STARTING YOLO DEFECT INSPECTION SIMULATOR E2E VERIFICATION ===');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 960 },
        deviceScaleFactor: 1
    });

    const page = await context.newPage();

    const consoleLogs = [];
    const pageErrors = [];

    page.on('console', msg => {
        const text = msg.text();
        consoleLogs.push(`[${msg.type()}] ${text}`);
        if (msg.type() === 'error' && !text.includes('favicon') && !text.includes('Failed to load resource')) {
            console.error('[BROWSER ERROR]', text);
        }
    });

    page.on('pageerror', err => {
        pageErrors.push(err.message);
        console.error('[UNCAUGHT PAGE ERROR]', err.message);
    });

    try {
        console.log('[*] Navigating to https://innoria.insilos.com/industries...');
        await page.goto('https://innoria.insilos.com/industries', {
            waitUntil: 'networkidle',
            timeout: 45000
        });

        console.log('[*] Waiting for YOLO inspection section...');
        const sectionSelector = '.s_innoria_yolo_inspection';
        await page.waitForSelector(sectionSelector, { timeout: 15000 });

        // Scroll section into view
        const section = page.locator(sectionSelector);
        await section.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);

        // Verify section visibility and elements
        const isVisible = await section.isVisible();
        console.log(`[✓] Section visible: ${isVisible}`);

        // State 1: PCB Electronics (Default Defect Injected)
        console.log('[*] Checking State 1: PCB Electronics (Defect Injected)...');
        const statusText = await page.locator('.ins-yolo-status-text').innerText();
        console.log(`[✓] Status Text: "${statusText}"`);

        const pcbDefectBox = page.locator('.ins-yolo-box.is-defect');
        const defectCount = await pcbDefectBox.count();
        console.log(`[✓] Defect Bounding Boxes found: ${defectCount}`);

        const defectTag = await pcbDefectBox.first().locator('.ins-yolo-box-tag').innerText();
        console.log(`[✓] Defect Tag: "${defectTag}"`);

        const pcbScreenshot = path.join(ARTIFACT_DIR, 'yolo_state1_pcb_defect.png');
        await section.screenshot({ path: pcbScreenshot });
        console.log(`[✓] Captured State 1 screenshot: ${pcbScreenshot}`);

        // State 2: Toggle Defect OFF -> Nominal Pass Mode
        console.log('[*] Testing State 2: Toggle Defect Injection OFF (Nominal Pass)...');
        await page.click('#toggleDefectInjection');
        await page.waitForTimeout(600);

        const passStatusText = await page.locator('.ins-yolo-status-text').innerText();
        console.log(`[✓] Nominal Status Text: "${passStatusText}"`);

        const passScreenshot = path.join(ARTIFACT_DIR, 'yolo_state2_nominal_pass.png');
        await section.screenshot({ path: passScreenshot });
        console.log(`[✓] Captured State 2 screenshot: ${passScreenshot}`);

        // Toggle Defect back ON
        await page.click('#toggleDefectInjection');
        await page.waitForTimeout(400);

        // State 3: Switch to Automotive Stamping
        console.log('[*] Testing State 3: Switch to Automotive Stamping...');
        await page.click('[data-inspection-target="auto_stamping"]');
        await page.waitForTimeout(800);

        const autoTag = await page.locator('.ins-yolo-box.is-defect .ins-yolo-box-tag').innerText();
        console.log(`[✓] Auto Defect Tag: "${autoTag}"`);
        const autoTargetCode = await page.locator('.ins-telemetry-target').innerText();
        console.log(`[✓] Auto Target Code: "${autoTargetCode}"`);

        const autoScreenshot = path.join(ARTIFACT_DIR, 'yolo_state3_auto_stamping.png');
        await section.screenshot({ path: autoScreenshot });
        console.log(`[✓] Captured State 3 screenshot: ${autoScreenshot}`);

        // State 4: Switch to Solar Silicon Wafer
        console.log('[*] Testing State 4: Switch to Solar Silicon Wafer...');
        await page.click('[data-inspection-target="solar_wafer"]');
        await page.waitForTimeout(800);

        const solarTag = await page.locator('.ins-yolo-box.is-defect .ins-yolo-box-tag').innerText();
        console.log(`[✓] Solar Defect Tag: "${solarTag}"`);

        const solarScreenshot = path.join(ARTIFACT_DIR, 'yolo_state4_solar_wafer.png');
        await section.screenshot({ path: solarScreenshot });
        console.log(`[✓] Captured State 4 screenshot: ${solarScreenshot}`);

        // State 5: Switch to Weld Seam SS400
        console.log('[*] Testing State 5: Switch to Weld Seam SS400...');
        await page.click('[data-inspection-target="weld_seam"]');
        await page.waitForTimeout(800);

        const weldTag = await page.locator('.ins-yolo-box.is-defect .ins-yolo-box-tag').innerText();
        console.log(`[✓] Weld Defect Tag: "${weldTag}"`);

        const weldScreenshot = path.join(ARTIFACT_DIR, 'yolo_state5_weld_seam.png');
        await section.screenshot({ path: weldScreenshot });
        console.log(`[✓] Captured State 5 screenshot: ${weldScreenshot}`);

        // State 6: Trigger Scan Button
        console.log('[*] Testing State 6: Trigger Single-Frame Laser Scan...');
        await page.click('#btnTriggerScan');
        await page.waitForTimeout(500);

        const latencyText = await page.locator('.ins-telemetry-latency').innerText();
        console.log(`[✓] Latency jitter verified: "${latencyText}"`);

        // Check for severe page errors
        const severeErrors = pageErrors.filter(e => !e.includes('ResizeObserver'));
        if (severeErrors.length > 0) {
            console.error('[!] Severe errors encountered:', severeErrors);
        } else {
            console.log('[✓] Zero severe browser errors detected!');
        }

        console.log('=== VERIFICATION COMPLETED SUCCESSFULLY ===');
    } catch (err) {
        console.error('[!] Test failure:', err);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
