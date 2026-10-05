const { chromium } = require('playwright');
const fs = require('fs');

async function verifyInnoriaHomepage() {
    console.log('[*] Launching Chromium to probe https://innoria.insilos.com ...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();
    const consoleLogs = [];
    const consoleErrors = [];

    page.on('console', msg => {
        const text = msg.text();
        const type = msg.type();
        consoleLogs.push({ type, text });
        if (type === 'error' && !text.includes('favicon.ico')) {
            consoleErrors.push(text);
        }
    });

    page.on('pageerror', err => {
        consoleErrors.push(err.message);
    });

    try {
        console.log('[*] Navigating to https://innoria.insilos.com/ ...');
        const response = await page.goto('https://innoria.insilos.com/', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        console.log(`[✓] HTTP Status: ${response.status()}`);
        if (response.status() !== 200) {
            throw new Error(`Unexpected HTTP status: ${response.status()}`);
        }

        // Wait for 3D engine and canvas initialization
        console.log('[*] Waiting for 3D topology canvas...');
        await page.waitForTimeout(3000);

        // Check DOM elements
        const title = await page.title();
        console.log(`[✓] Page Title: ${title}`);

        const viewportExists = await page.$('#innoriaTopologyViewport');
        console.log(`[✓] #innoriaTopologyViewport exists: ${!!viewportExists}`);

        const canvasCount = await page.$$eval('#innoriaTopologyViewport canvas', els => els.length);
        console.log(`[✓] 3D WebGL Canvas count: ${canvasCount}`);

        const hudButtons = await page.$$eval('.innoria-hud-btn', els => els.map(e => e.textContent.trim()));
        console.log(`[✓] HUD Buttons found: ${hudButtons.join(' | ')}`);

        // Check Cadence cards
        const cadenceCards = await page.$$eval('.innoria-cadence-card h4', els => els.map(e => e.textContent.trim()));
        console.log(`[✓] Cadence Steps: ${cadenceCards.join(' -> ')}`);

        // Check Ecosystem cards
        const ecosystemPillars = await page.$$eval('.innoria-card-ecosystem h3', els => els.map(e => e.textContent.trim()));
        console.log(`[✓] Ecosystem Pillars: ${ecosystemPillars.join(' | ')}`);

        // Test interaction: Click "DIGIFORCE" HUD button
        console.log('[*] Testing HUD interaction: click DIGIFORCE node button...');
        await page.click('[data-action="focus-node"][data-node-key="DIGIFORCE"]');
        await page.waitForTimeout(1500);

        const hudVisible = await page.$eval('#innoria-topology-hud', el => el.style.display !== 'none').catch(() => false);
        console.log(`[✓] Telemetry HUD Visible on Click: ${hudVisible}`);

        // Capture full screen proof
        const screenshotPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_3d_elevated_homepage.png';
        await page.screenshot({ path: screenshotPath, fullPage: false });
        console.log(`[✓] Captured elevated hero screenshot to: ${screenshotPath}`);

        // Capture full page screenshot
        const fullScreenshotPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_3d_elevated_fullpage.png';
        await page.screenshot({ path: fullScreenshotPath, fullPage: true });
        console.log(`[✓] Captured full page screenshot to: ${fullScreenshotPath}`);

        console.log(`\n--- Verification Summary ---`);
        console.log(`Console Errors (${consoleErrors.length}):`);
        consoleErrors.forEach(err => console.log(`  ❌ ${err}`));

        if (consoleErrors.length === 0) {
            console.log(`\n🎉 100% CLEAN: Zero console errors on https://innoria.insilos.com/!`);
        } else {
            console.log(`\n⚠️ Some console errors detected.`);
        }

    } catch (err) {
        console.error(`[✗] Verification failed:`, err);
    } finally {
        await browser.close();
    }
}

verifyInnoriaHomepage();
