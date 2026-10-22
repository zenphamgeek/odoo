const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

(async () => {
    console.log('=== VERIFYING EXECUTIVE ENGINEERING SERVICES WORKSTATION ===');
    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-ipv6',
            '--host-resolver-rules=MAP innoria.insilos.com 172.67.156.74'
        ]
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1.5,
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    // Listen for console logs & errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('[Browser Error]', msg.text());
        }
    });

    try {
        console.log('[*] Navigating to https://innoria.insilos.com/#innoria_engineering_services...');
        await page.goto('https://innoria.insilos.com/#innoria_engineering_services', { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(3000);

        const section = page.locator('#innoria_engineering_services');
        await section.waitFor({ timeout: 15000 });
        await section.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);

        // 1. Verify zero old white cards
        const oldCards = await page.locator('.innoria-service-card').count();
        console.log(`[✓] Old white card count: ${oldCards} (Expected: 0)`);
        if (oldCards !== 0) throw new Error('Old service cards still present!');

        // 2. Verify 4 interactive rails
        const rails = page.locator('.service-rail-item');
        const railCount = await rails.count();
        console.log(`[✓] Interactive Service Rails count: ${railCount} (Expected: 4)`);
        if (railCount !== 4) throw new Error(`Expected 4 service rails, found ${railCount}`);

        // 3. Verify Mode 0: AIaaS
        console.log('[*] Testing Mode 0: AI as a Service...');
        const mode0Pane = page.locator('.service-sandbox-pane[data-pane-index="0"]');
        await mode0Pane.waitFor({ state: 'visible' });

        // Click query CNC
        const cncBtn = page.locator('.aiaas-query-btn[data-query="cnc"]');
        await cncBtn.click();
        await page.waitForTimeout(500);

        const latencyText = await page.locator('#aiaasLatencyVal').textContent();
        console.log(`[✓] AIaaS CNC query latency: ${latencyText}`);

        // Capture Mode 0 screenshot
        const shot0 = path.join(ARTIFACT_DIR, 'services_workstation_mode0_aiaas.png');
        await section.screenshot({ path: shot0 });
        console.log(`[✓] Captured Mode 0: ${shot0}`);

        // 4. Switch to Mode 1: Digital Transformation
        console.log('[*] Testing Mode 1: Digital Transformation...');
        await rails.nth(1).evaluate(el => el.click());
        await page.waitForTimeout(600);

        const mode1Pane = page.locator('.service-sandbox-pane[data-pane-index="1"]');
        await mode1Pane.waitFor({ state: 'visible' });

        // Toggle to legacy then back to ai
        const legacyBtn = page.locator('.dx-toggle-btn[data-dx-state="legacy"]');
        await legacyBtn.evaluate(el => el.click());
        await page.waitForTimeout(300);

        const aiBtn = page.locator('.dx-toggle-btn[data-dx-state="ai"]');
        await aiBtn.evaluate(el => el.click());
        await page.waitForTimeout(300);

        const metricTime = await page.locator('#dxMetricTime').textContent();
        console.log(`[✓] DX Metric Time: ${metricTime}`);

        // Capture Mode 1 screenshot
        const shot1 = path.join(ARTIFACT_DIR, 'services_workstation_mode1_dx.png');
        await section.screenshot({ path: shot1 });
        console.log(`[✓] Captured Mode 1: ${shot1}`);

        // 5. Switch to Mode 2: Development Services (K8s)
        console.log('[*] Testing Mode 2: Development Services & K8s...');
        await rails.nth(2).evaluate(el => el.click());
        await page.waitForTimeout(600);

        const mode2Pane = page.locator('.service-sandbox-pane[data-pane-index="2"]');
        await mode2Pane.waitFor({ state: 'visible' });

        // Click stress test button
        const stressBtn = page.locator('#k8sStressBtn');
        await stressBtn.evaluate(el => el.click());
        await page.waitForTimeout(600);

        const rpsVal = await page.locator('#k8sRpsVal').textContent();
        console.log(`[✓] K8s stress test RPS: ${rpsVal}`);

        // Capture Mode 2 screenshot
        const shot2 = path.join(ARTIFACT_DIR, 'services_workstation_mode2_k8s.png');
        await section.screenshot({ path: shot2 });
        console.log(`[✓] Captured Mode 2: ${shot2}`);

        // 6. Switch to Mode 3: Dedicated ODC & Web3
        console.log('[*] Testing Mode 3: Dedicated ODC & Web3...');
        await rails.nth(3).evaluate(el => el.click());
        await page.waitForTimeout(600);

        const mode3Pane = page.locator('.service-sandbox-pane[data-pane-index="3"]');
        await mode3Pane.waitFor({ state: 'visible' });

        // Click Da Nang hub
        const danangBtn = page.locator('.odc-hub-btn[data-hub="danang"]');
        await danangBtn.evaluate(el => el.click());
        await page.waitForTimeout(300);

        const danangHeadcount = await page.locator('#odcHeadcountVal').textContent();
        console.log(`[✓] ODC Đà Nẵng Headcount: ${danangHeadcount}`);

        // Capture Mode 3 screenshot
        const shot3 = path.join(ARTIFACT_DIR, 'services_workstation_mode3_odc.png');
        await section.screenshot({ path: shot3 });
        console.log(`[✓] Captured Mode 3: ${shot3}`);

        // 7. Capture Full Page Overview with surrounding context
        const box = await section.boundingBox();
        await page.evaluate((y) => window.scrollTo({ top: Math.max(0, y - 60), behavior: 'instant' }), box.y);
        await page.waitForTimeout(600);

        const overviewShot = path.join(ARTIFACT_DIR, 'services_workstation_full_overview.png');
        await page.screenshot({ path: overviewShot });
        console.log(`[✓] Captured Full Overview: ${overviewShot}`);

        console.log('=== ALL WORKSTATION VERIFICATION CHECKS PASSED ===');
    } catch (e) {
        console.error('[!] Verification failed:', e);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
