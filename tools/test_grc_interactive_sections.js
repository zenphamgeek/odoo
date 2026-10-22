/**
 * Automated Verification Suite for INNORIA GRC Interactive Engines
 * File: tools/test_grc_interactive_sections.js
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://innoria.com/';
const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function runGrcAudit() {
    console.log('[*] Launching headless browser for GRC Verification...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        }
    });

    console.log(`[*] Navigating to ${TARGET_URL}...`);
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    const results = {
        url: TARGET_URL,
        timestamp: new Date().toISOString(),
        checks: {},
        consoleErrors: consoleErrors
    };

    // 1. Check Navbar Products Mega-Menu
    console.log('[1/6] Auditing Navbar Products Mega-Menu...');
    const productsTrigger = await page.$('.ins-has-megamenu[data-megamenu="innoria_products"]');
    const productsMenu = await page.$('#ins_megamenu_innoria_products');
    results.checks.navbarProductsTriggerExists = !!productsTrigger;
    results.checks.navbarProductsMenuExists = !!productsMenu;

    if (productsTrigger) {
        await productsTrigger.hover();
        await page.waitForTimeout(300);
        const isMenuVisible = await page.evaluate(() => {
            const menu = document.getElementById('ins_megamenu_innoria_products');
            return menu && (menu.classList.contains('is-open') || window.getComputedStyle(menu).opacity > 0);
        });
        results.checks.navbarProductsMenuRevealedOnHover = isMenuVisible;
        console.log(`    -> Products mega-menu hover revealed: ${isMenuVisible}`);
    }

    // 2. Check GRC Hero Positioning
    console.log('[2/6] Auditing Hero GRC Positioning...');
    const heroTitle = await page.textContent('.hero-main-title');
    results.checks.heroTitleContainsControlledCompliant = heroTitle.includes('Được Kiểm Soát & Tuân Thủ') || heroTitle.includes('Controlled, Compliant Operations');
    console.log(`    -> Hero GRC Title matched: ${results.checks.heroTitleContainsControlledCompliant}`);

    // 3. Audit Section 1: Trade Compliance Intelligence
    console.log('[3/6] Auditing Section 1: Trade Compliance Intelligence...');
    const tradeSec = await page.$('#innoria_trade_compliance_interactive');
    results.checks.tradeSectionExists = !!tradeSec;

    if (tradeSec) {
        await tradeSec.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);

        // Run Rules
        const btnRules = await page.$('#btnRunReconRules');
        if (btnRules) {
            await btnRules.click();
            await page.waitForTimeout(1000);

            const badgeText = await page.textContent('#reconStatusBadge');
            results.checks.reconRulesRanAndDetectedExceptions = badgeText.includes('Phát Hiện 2 Ngoại Lệ');
            console.log(`    -> Recon Rules triggered: ${results.checks.reconRulesRanAndDetectedExceptions}`);

            // Approve & Seal
            const btnApprove = await page.$('#btnApproveRecon');
            if (btnApprove && await btnApprove.isEnabled()) {
                await btnApprove.click();
                await page.waitForTimeout(500);
                const approvedText = await page.textContent('#reconStatusBadge');
                results.checks.reconApprovedAndSealed = approvedText.includes('Đã Ký Phê Duyệt');
                console.log(`    -> Recon Approval Sealed: ${results.checks.reconApprovedAndSealed}`);
            }
        }

        // Test C/O Tab
        const coTabBtn = await page.$('.grc-trade-tab-btn[data-target-pane="tradePaneCo"]');
        if (coTabBtn) {
            await coTabBtn.click();
            await page.waitForTimeout(300);

            const rvcVal = await page.textContent('#coRvcResultVal');
            results.checks.coRvcCalculated = rvcVal.includes('56.59%');

            const btnCoPreview = await page.$('#btnToggleCoPreview');
            if (btnCoPreview) {
                await btnCoPreview.click();
                await page.waitForTimeout(300);
                const isCoPreviewOpen = await page.evaluate(() => {
                    const el = document.getElementById('coFormPreviewModal');
                    return el && !el.classList.contains('d-none');
                });
                results.checks.coFormPreviewToggled = isCoPreviewOpen;
                console.log(`    -> C/O Form D Preview toggled: ${isCoPreviewOpen}`);
            }
        }

        // Test Chemical Tab
        const chemTabBtn = await page.$('.grc-trade-tab-btn[data-target-pane="tradePaneChem"]');
        if (chemTabBtn) {
            await chemTabBtn.click();
            await page.waitForTimeout(300);

            await page.fill('#chemSearchInput', 'toluene');
            await page.waitForTimeout(300);

            const visibleRows = await page.evaluate(() => {
                const rows = document.querySelectorAll('.chem-data-row');
                let count = 0;
                rows.forEach(r => { if (r.style.display !== 'none') count++; });
                return count;
            });
            results.checks.chemSearchFilterWorking = visibleRows === 1;
            console.log(`    -> Chemical CAS search filter matched 1 row: ${results.checks.chemSearchFilterWorking}`);

            // Export dataset
            await page.click('#btnExportChemDossier');
            await page.waitForTimeout(300);
            const isAlertShown = await page.evaluate(() => {
                const el = document.getElementById('chemExportAlert');
                return el && !el.classList.contains('d-none');
            });
            results.checks.chemExportAlertTriggered = isAlertShown;
        }

        // Capture Trade Section Screenshot
        const tradeScreenshotPath = path.join(ARTIFACT_DIR, 'innoria_grc_trade_compliance.png');
        await tradeSec.screenshot({ path: tradeScreenshotPath });
        console.log(`    -> Screenshot saved: ${tradeScreenshotPath}`);
    }

    // 4. Audit Section 2: Operational Compliance Intelligence
    console.log('[4/6] Auditing Section 2: Operational Compliance Intelligence...');
    const opsSec = await page.$('#innoria_operational_compliance_interactive');
    results.checks.opsSectionExists = !!opsSec;

    if (opsSec) {
        await opsSec.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);

        // Point 4 LOTO Toggle
        const pt4 = await page.$('.loto-point-item[data-point-id="4"]');
        if (pt4) {
            const toggleBtn = await pt4.$('.btn-loto-toggle');
            if (toggleBtn) {
                await toggleBtn.click();
                await page.waitForTimeout(400);

                const gasStatus = await page.textContent('#ptwGasStatus');
                results.checks.lotoAllLockedAndGasSafe = gasStatus.includes('Khí An Toàn');
                console.log(`    -> LOTO Point 4 locked & Gas Safe: ${results.checks.lotoAllLockedAndGasSafe}`);

                const btnSignPtw = await page.$('#btnSignPtw');
                if (btnSignPtw && await btnSignPtw.isEnabled()) {
                    await btnSignPtw.click();
                    await page.waitForTimeout(400);
                    const isCountdownShown = await page.evaluate(() => {
                        const el = document.getElementById('ptwCountdownBadge');
                        return el && !el.classList.contains('d-none');
                    });
                    results.checks.ptwDigitalSignOffActive = isCountdownShown;
                    console.log(`    -> e-PTW signed & countdown active: ${isCountdownShown}`);
                }
            }
        }

        // Shift Handover
        const shiftTabBtn = await page.$('.grc-ops-tab-btn[data-target-pane="opsPaneShift"]');
        if (shiftTabBtn) {
            await shiftTabBtn.click();
            await page.waitForTimeout(300);

            await page.click('#btnSignCa1');
            await page.waitForTimeout(300);
            await page.click('#btnSignCa2');
            await page.waitForTimeout(300);

            const handoverText = await page.textContent('#handoverStatusBadge');
            results.checks.shiftHandoverCompleted = handoverText.includes('BÀN GIAO CA HOÀN TẤT');
            console.log(`    -> Shift Handover completed: ${results.checks.shiftHandoverCompleted}`);
        }

        // Capture Ops Section Screenshot
        const opsScreenshotPath = path.join(ARTIFACT_DIR, 'innoria_grc_operational_compliance.png');
        await opsSec.screenshot({ path: opsScreenshotPath });
        console.log(`    -> Screenshot saved: ${opsScreenshotPath}`);
    }

    // 5. Audit Section 3: Logistics Operations Solutions
    console.log('[5/6] Auditing Section 3: Logistics Operations Solutions...');
    const logSec = await page.$('#innoria_logistics_jobfile_interactive');
    results.checks.logisticsSectionExists = !!logSec;

    if (logSec) {
        await logSec.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);

        const btnDispute = await page.$('#btnDisputeDem');
        if (btnDispute) {
            await btnDispute.click();
            await page.waitForTimeout(400);

            const isDisputeNoticeOpen = await page.evaluate(() => {
                const el = document.getElementById('disputeNoticeBox');
                return el && !el.classList.contains('d-none');
            });
            results.checks.disputeNoticeToggled = isDisputeNoticeOpen;
            console.log(`    -> Demurrage dispute notice toggled: ${isDisputeNoticeOpen}`);
        }

        // Capture Logistics Section Screenshot
        const logScreenshotPath = path.join(ARTIFACT_DIR, 'innoria_grc_logistics_cost_control.png');
        await logSec.screenshot({ path: logScreenshotPath });
        console.log(`    -> Screenshot saved: ${logScreenshotPath}`);
    }

    // 6. Fullpage Screenshot
    console.log('[6/6] Capturing Fullpage Verified Screenshot...');
    const fullpagePath = path.join(ARTIFACT_DIR, 'innoria_com_grc_verified_fullpage.png');
    await page.screenshot({ path: fullpagePath, fullPage: true });
    console.log(`    -> Fullpage saved: ${fullpagePath}`);

    await browser.close();

    const reportPath = path.join(ARTIFACT_DIR, 'INNORIA_GRC_INTERACTIVE_VERIFICATION_REPORT.json');
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2), 'utf-8');
    console.log(`[✓] Verification report written to: ${reportPath}`);
    console.log('\nAudit Summary:');
    console.log(JSON.stringify(results.checks, null, 2));
    console.log(`Console Errors: ${consoleErrors.length}`);
}

runGrcAudit().catch(err => {
    console.error('[!] Audit encountered error:', err);
    process.exit(1);
});
