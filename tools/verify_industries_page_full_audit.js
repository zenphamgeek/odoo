/**
 * tools/verify_industries_page_full_audit.js
 * Comprehensive Playwright Audit & High-Fidelity Visual Capture for Innoria Industries Page
 * Target: https://innoria.com/industries & https://innoria.insilos.com/industries
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/sections';
if (!fs.existsSync(ARTIFACT_DIR)) {
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

(async () => {
    console.log('=== STARTING COMPREHENSIVE INNORIA INDUSTRIES PAGE AUDIT ===');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
    });

    const report = {
        timestamp: new Date().toISOString(),
        desktop: {},
        mobile: {},
        yolo_simulator: {},
        interactive_tabs: {},
        console_errors: [],
        page_errors: []
    };

    try {
        // =========================================================================
        // 1. DESKTOP VIEWPORT (1440 x 960)
        // =========================================================================
        console.log('\n--- 1. DESKTOP VIEWPORT AUDIT (1440x960) ---');
        const desktopContext = await browser.newContext({
            viewport: { width: 1440, height: 960 },
            deviceScaleFactor: 1
        });
        const page = await desktopContext.newPage();

        page.on('console', msg => {
            if (msg.type() === 'error') {
                const text = msg.text();
                if (!text.includes('favicon') && !text.includes('Failed to load resource')) {
                    report.console_errors.push(text);
                    console.error('[CONSOLE ERROR]', text);
                }
            }
        });

        page.on('pageerror', err => {
            report.page_errors.push(err.message);
            console.error('[PAGE ERROR]', err.message);
        });

        // Determine primary URL to test (fallback to innoria.insilos.com if needed)
        const targetUrl = process.env.TEST_URL || 'https://innoria.com/industries';
        console.log(`[*] Navigating to ${targetUrl}...`);
        await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 45000 });
        await page.waitForTimeout(1500);

        // Check horizontal overflow
        const overflowCheck = await page.evaluate(() => {
            return {
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
            };
        });
        console.log(`[✓] Desktop Overflow Check: scrollWidth=${overflowCheck.scrollWidth}, clientWidth=${overflowCheck.clientWidth}, hasOverflow=${overflowCheck.hasOverflow}`);
        report.desktop.overflow = overflowCheck;

        // Capture Act 1: Hero Section
        const heroSection = page.locator('section[data-name="Sovereign Industry Hero"], .ins-industries-stage section:first-of-type').first();
        if (await heroSection.count() > 0) {
            await heroSection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(500);
            const heroPath = path.join(ARTIFACT_DIR, 'industries_desktop_hero.png');
            await heroSection.screenshot({ path: heroPath });
            console.log(`[✓] Captured Hero Section: ${heroPath}`);
            report.desktop.hero_screenshot = heroPath;
        }

        // Capture Act 2: Interactive Vertical Industry Command Stage
        console.log('\n--- 2. INTERACTIVE VERTICAL COMMAND STAGE AUDIT ---');
        const stageSection = page.locator('section[data-name="Vertical Industry Command Stage"], .ins-industries-stage section:nth-of-type(2)').first();
        if (await stageSection.count() > 0) {
            await stageSection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(800);

            // Tab 1: Manufacturing & Smart MES (Default)
            const tab1Path = path.join(ARTIFACT_DIR, 'industries_tab1_manufacturing.png');
            await stageSection.screenshot({ path: tab1Path });
            console.log(`[✓] Captured Tab 1 (Manufacturing): ${tab1Path}`);

            // Tab 2: Energy & Petrochem
            console.log('[*] Switching to Tab 2: Energy & Petrochem...');
            const tab2Btn = page.locator('#tab-btn-energy, button[data-bs-target="#pane-energy"]');
            if (await tab2Btn.count() > 0) {
                await tab2Btn.click();
                await page.waitForTimeout(800);
                const tab2Path = path.join(ARTIFACT_DIR, 'industries_tab2_energy.png');
                await stageSection.screenshot({ path: tab2Path });
                console.log(`[✓] Captured Tab 2 (Energy): ${tab2Path}`);
            }

            // Tab 3: Port & Intermodal Logistics
            console.log('[*] Switching to Tab 3: Port & Intermodal Logistics...');
            const tab3Btn = page.locator('#tab-btn-maritime, button[data-bs-target="#pane-maritime"]');
            if (await tab3Btn.count() > 0) {
                await tab3Btn.click();
                await page.waitForTimeout(800);
                const tab3Path = path.join(ARTIFACT_DIR, 'industries_tab3_port.png');
                await stageSection.screenshot({ path: tab3Path });
                console.log(`[✓] Captured Tab 3 (Port): ${tab3Path}`);
            }

            // Tab 4: Pharma & GMP Cleanroom
            console.log('[*] Switching to Tab 4: Pharma & GMP Cleanroom...');
            const tab4Btn = page.locator('#tab-btn-pharma, button[data-bs-target="#pane-pharma"]');
            if (await tab4Btn.count() > 0) {
                await tab4Btn.click();
                await page.waitForTimeout(800);
                const tab4Path = path.join(ARTIFACT_DIR, 'industries_tab4_pharma.png');
                await stageSection.screenshot({ path: tab4Path });
                console.log(`[✓] Captured Tab 4 (Pharma): ${tab4Path}`);
            }

            // Tab 5: FMCG & Omnichannel
            console.log('[*] Switching to Tab 5: FMCG & Omnichannel...');
            const tab5Btn = page.locator('#tab-btn-retail, button[data-bs-target="#pane-retail"]');
            if (await tab5Btn.count() > 0) {
                await tab5Btn.click();
                await page.waitForTimeout(800);
                const tab5Path = path.join(ARTIFACT_DIR, 'industries_tab5_fmcg.png');
                await stageSection.screenshot({ path: tab5Path });
                console.log(`[✓] Captured Tab 5 (FMCG): ${tab5Path}`);
            }
        }

        // Capture Act 3: YOLO Defect Inspection Simulator
        console.log('\n--- 3. YOLO DEFECT INSPECTION SIMULATOR AUDIT ---');
        const yoloSection = page.locator('.s_innoria_yolo_inspection, section[data-name="Industrial YOLOv11x Simulator"]').first();
        if (await yoloSection.count() > 0) {
            await yoloSection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(800);

            // State 1: Mode A - CCTV Live Stream (Welding SS400)
            const yolo1Path = path.join(ARTIFACT_DIR, 'industries_yolo_mode_a_cctv.png');
            await yoloSection.screenshot({ path: yolo1Path });
            console.log(`[✓] Captured YOLO Mode A (Live CCTV): ${yolo1Path}`);

            // Switch to Mode B (Micro-Metrology Synthetic)
            console.log('[*] Switching to Mode B (Micro-Metrology Synthetic)...');
            const syntheticTab = page.locator('.ins-mode-tab-btn[data-mode="synthetic"]');
            if (await syntheticTab.count() > 0) {
                await syntheticTab.click();
                await page.waitForTimeout(600);
            }

            // State 2: PCB Electronics (Defect Injected)
            const yolo2Path = path.join(ARTIFACT_DIR, 'industries_yolo_pcb_defect.png');
            await yoloSection.screenshot({ path: yolo2Path });
            console.log(`[✓] Captured YOLO State 2 (PCB Defect): ${yolo2Path}`);

            // State 3: Toggle Defect Injection OFF (Nominal Pass)
            const toggleDefectBtn = page.locator('#toggleDefectInjection');
            if (await toggleDefectBtn.count() > 0) {
                await toggleDefectBtn.click();
                await page.waitForTimeout(600);
                const yolo3Path = path.join(ARTIFACT_DIR, 'industries_yolo_nominal_pass.png');
                await yoloSection.screenshot({ path: yolo3Path });
                console.log(`[✓] Captured YOLO State 3 (Nominal Pass): ${yolo3Path}`);

                // Toggle back ON
                await toggleDefectBtn.click();
                await page.waitForTimeout(400);
            }

            // State 4: Switch Scenario to Automotive Stamping
            const autoBtn = page.locator('[data-inspection-target="auto_stamping"]');
            if (await autoBtn.count() > 0 && await autoBtn.isVisible()) {
                await autoBtn.click();
                await page.waitForTimeout(600);
                const yolo4Path = path.join(ARTIFACT_DIR, 'industries_yolo_auto_stamping.png');
                await yoloSection.screenshot({ path: yolo4Path });
                console.log(`[✓] Captured YOLO State 4 (Auto Stamping): ${yolo4Path}`);
            }

            // State 5: Trigger Single-Frame Laser Scan
            const scanBtn = page.locator('#btnTriggerScan');
            if (await scanBtn.count() > 0) {
                await scanBtn.click();
                await page.waitForTimeout(600);
                console.log('[✓] Triggered Single-Frame Laser Scan');
            }
        }

        // Capture Act 4: Edge-to-Cloud Topology
        console.log('\n--- 4. EDGE-TO-CLOUD TOPOLOGY & CASE STUDIES AUDIT ---');
        const topologySection = page.locator('section[data-name="Edge to Cloud Topology"]').first();
        if (await topologySection.count() > 0) {
            await topologySection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(600);
            const topoPath = path.join(ARTIFACT_DIR, 'industries_desktop_topology.png');
            await topologySection.screenshot({ path: topoPath });
            console.log(`[✓] Captured Topology Section: ${topoPath}`);
        }

        // Capture Act 5: Quantitative Case Study Dossiers
        const caseStudySection = page.locator('section[data-name="Forensic Case Studies"]').first();
        if (await caseStudySection.count() > 0) {
            await caseStudySection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(600);
            const casePath = path.join(ARTIFACT_DIR, 'industries_desktop_case_studies.png');
            await caseStudySection.screenshot({ path: casePath });
            console.log(`[✓] Captured Case Studies Section: ${casePath}`);
        }

        // Capture Act 6: Executive Pilot Roadmap & CTA
        const ctaSection = page.locator('section[data-name="Industry Pilot CTA"], #vision-pilot').first();
        if (await ctaSection.count() > 0) {
            await ctaSection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(600);
            const ctaPath = path.join(ARTIFACT_DIR, 'industries_desktop_cta.png');
            await ctaSection.screenshot({ path: ctaPath });
            console.log(`[✓] Captured CTA Section: ${ctaPath}`);
        }

        // Capture Full Page Desktop
        const fullPagePath = path.join(ARTIFACT_DIR, 'industries_desktop_fullpage.png');
        await page.screenshot({ path: fullPagePath, fullPage: true });
        console.log(`[✓] Captured Full Desktop Page: ${fullPagePath}`);

        await desktopContext.close();

        // =========================================================================
        // 2. MOBILE VIEWPORT (375 x 812)
        // =========================================================================
        console.log('\n--- 5. MOBILE VIEWPORT AUDIT (375x812) ---');
        const mobileContext = await browser.newContext({
            viewport: { width: 375, height: 812 },
            deviceScaleFactor: 2,
            isMobile: true,
            hasTouch: true
        });
        const mobilePage = await mobileContext.newPage();

        await mobilePage.goto(targetUrl, { waitUntil: 'networkidle', timeout: 45000 });
        await mobilePage.waitForTimeout(1500);

        const mobileOverflow = await mobilePage.evaluate(() => {
            return {
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
            };
        });
        console.log(`[✓] Mobile Overflow Check: scrollWidth=${mobileOverflow.scrollWidth}, clientWidth=${mobileOverflow.clientWidth}, hasOverflow=${mobileOverflow.hasOverflow}`);
        report.mobile.overflow = mobileOverflow;

        const mobileHeroPath = path.join(ARTIFACT_DIR, 'industries_mobile_hero.png');
        await mobilePage.screenshot({ path: mobileHeroPath, clip: { x: 0, y: 0, width: 375, height: 812 } });
        console.log(`[✓] Captured Mobile Hero: ${mobileHeroPath}`);

        // Capture Mobile Command Stage
        const mStage = mobilePage.locator('#vertical-command-stage').first();
        if (await mStage.count() > 0) {
            await mStage.scrollIntoViewIfNeeded();
            await mobilePage.waitForTimeout(400);
            const mStagePath = path.join(ARTIFACT_DIR, 'industries_mobile_stage.png');
            await mStage.screenshot({ path: mStagePath });
            console.log(`[✓] Captured Mobile Command Stage: ${mStagePath}`);
        }

        // Capture Mobile YOLO
        const mYolo = mobilePage.locator('.s_innoria_yolo_inspection').first();
        if (await mYolo.count() > 0) {
            await mYolo.scrollIntoViewIfNeeded();
            await mobilePage.waitForTimeout(400);
            const mYoloPath = path.join(ARTIFACT_DIR, 'industries_mobile_yolo.png');
            await mYolo.screenshot({ path: mYoloPath });
            console.log(`[✓] Captured Mobile YOLO: ${mYoloPath}`);
        }

        // Capture Mobile Topology
        const mTopo = mobilePage.locator('section[data-name="Edge to Cloud Topology"]').first();
        if (await mTopo.count() > 0) {
            await mTopo.scrollIntoViewIfNeeded();
            await mobilePage.waitForTimeout(400);
            const mTopoPath = path.join(ARTIFACT_DIR, 'industries_mobile_topology.png');
            await mTopo.screenshot({ path: mTopoPath });
            console.log(`[✓] Captured Mobile Topology: ${mTopoPath}`);
        }

        // Capture Mobile Case Studies
        const mCase = mobilePage.locator('section[data-name="Forensic Case Studies"]').first();
        if (await mCase.count() > 0) {
            await mCase.scrollIntoViewIfNeeded();
            await mobilePage.waitForTimeout(400);
            const mCasePath = path.join(ARTIFACT_DIR, 'industries_mobile_case_studies.png');
            await mCase.screenshot({ path: mCasePath });
            console.log(`[✓] Captured Mobile Case Studies: ${mCasePath}`);
        }

        // Capture Mobile CTA
        const mCta = mobilePage.locator('section[data-name="Industry Pilot CTA"], #vision-pilot').first();
        if (await mCta.count() > 0) {
            await mCta.scrollIntoViewIfNeeded();
            await mobilePage.waitForTimeout(400);
            const mCtaPath = path.join(ARTIFACT_DIR, 'industries_mobile_cta.png');
            await mCta.screenshot({ path: mCtaPath });
            console.log(`[✓] Captured Mobile CTA: ${mCtaPath}`);
        }

        const mobileFullPagePath = path.join(ARTIFACT_DIR, 'industries_mobile_fullpage.png');
        await mobilePage.screenshot({ path: mobileFullPagePath, fullPage: true });
        console.log(`[✓] Captured Full Mobile Page: ${mobileFullPagePath}`);

        await mobileContext.close();

        // Write audit report summary
        const reportPath = path.join(ARTIFACT_DIR, 'industries_audit_report.json');
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`\n[✓] Audit report saved to ${reportPath}`);
        console.log('=== AUDIT COMPLETED SUCCESSFULLY ===');
    } catch (err) {
        console.error('[!] Audit error:', err);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
