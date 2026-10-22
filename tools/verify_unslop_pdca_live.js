/**
 * tools/verify_unslop_pdca_live.js
 * Automated Playwright live auditor for PDCA Unslop and IBM Carbon 11 Design System standards.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
const BASE_URL = 'https://innoria.com';

async function verify() {
    console.log(`[PDCA AUDIT] Launching Chromium headless to audit ${BASE_URL}...`);
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const results = {
        timestamp: new Date().toISOString(),
        pages: {}
    };

    const routes = ['/', '/platform', '/solutions'];

    for (const route of routes) {
        const url = `${BASE_URL}${route}`;
        const page = await context.newPage();
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        console.log(`\n--> Auditing ${url}...`);
        const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 35000 });
        const httpStatus = resp.status();
        await page.waitForTimeout(2000);

        // Check horizontal overflow
        const overflow = await page.evaluate(() => {
            return document.documentElement.scrollWidth > document.documentElement.clientWidth;
        });

        // Check specific unslop tokens depending on page
        const unslopChecks = {};
        if (route === '/') {
            const bodyText = await page.innerText('body');
            unslopChecks.realTimeTelemetry = bodyText.includes('REAL-TIME');
            unslopChecks.operationalLatency = bodyText.includes('ĐỘ TRỄ VẬN HÀNH');
            unslopChecks.no60FpsSlop = !bodyText.includes('60 FPS');
            unslopChecks.noP99LatencySlop = !bodyText.includes('P99 LATENCY:');
        } else if (route === '/platform') {
            const terminalBorderRadius = await page.evaluate(() => {
                const el = document.querySelector('.mojo-terminal');
                return el ? window.getComputedStyle(el).borderRadius : null;
            });
            const quoteBorderRadius = await page.evaluate(() => {
                const el = document.querySelector('.mojo-quote-container');
                return el ? window.getComputedStyle(el).borderRadius : null;
            });
            const quoteBorderLeft = await page.evaluate(() => {
                const el = document.querySelector('.mojo-quote-container');
                return el ? window.getComputedStyle(el).borderLeftWidth : null;
            });
            unslopChecks.terminalBorderRadius = terminalBorderRadius;
            unslopChecks.quoteBorderRadius = quoteBorderRadius;
            unslopChecks.quoteBorderLeft = quoteBorderLeft;
        } else if (route === '/solutions') {
            const bodyText = await page.innerText('body');
            unslopChecks.noDotPha = !bodyText.includes('Sự khác biệt đột phá giữa');
            unslopChecks.hasUnslopQuote = bodyText.includes('sàn sản xuất CNC, bãi container cảng biển và sổ cái tài chính');
        }

        const screenshotPath = path.join(ARTIFACT_DIR, `live_unslop_${route.replace('/', '') || 'homepage'}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: false });
        console.log(`[Screenshot Saved] -> ${screenshotPath}`);

        results.pages[route] = {
            httpStatus,
            consoleErrorsCount: consoleErrors.length,
            consoleErrors,
            horizontalOverflow: overflow,
            unslopChecks,
            screenshot: screenshotPath
        };

        console.log(`Results for ${route}: HTTP ${httpStatus}, ${consoleErrors.length} console errors, Overflow: ${overflow}`);
        console.log(`Unslop checks:`, unslopChecks);
        await page.close();
    }

    await browser.close();

    const reportPath = path.join(ARTIFACT_DIR, 'live_unslop_audit_report.json');
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
    console.log(`\n[PDCA AUDIT COMPLETED] Report written to ${reportPath}`);
}

verify().catch(err => {
    console.error('Audit failed with error:', err);
    process.exit(1);
});
