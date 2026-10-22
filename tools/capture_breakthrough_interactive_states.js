const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
    console.log('[*] Initializing Playwright for Breakthrough Interactive States Capture...');
    const artifactDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/sections';
    if (!fs.existsSync(artifactDir)) {
        fs.mkdirSync(artifactDir, { recursive: true });
    }

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2
    });

    console.log('[*] Navigating to https://innoria.com/...');
    await page.goto('https://innoria.com/', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForTimeout(2500);

    // 1. Trade Compliance: Resting State
    console.log('[*] Capturing Trade Compliance (Resting State)...');
    const elTrade = await page.$('#innoria_trade_compliance_interactive');
    if (elTrade) {
        await elTrade.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);
        await elTrade.screenshot({ path: path.join(artifactDir, 'breakthrough_authority_cascade_resting.png') });
        console.log('[✓] Saved breakthrough_authority_cascade_resting.png');

        // 2. Trigger Simulation: Click "Mô Phỏng Né Thuế (P4 Override)"
        const btnSimRisk = await page.$('#btnSimulateOverride');
        if (btnSimRisk) {
            console.log('[*] Clicking #btnSimulateOverride to trigger Authority Cascade rejection...');
            await btnSimRisk.click();
            await page.waitForTimeout(1200);
            await elTrade.screenshot({ path: path.join(artifactDir, 'breakthrough_authority_cascade_rejected.png') });
            console.log('[✓] Saved breakthrough_authority_cascade_rejected.png');
        }
    }

    // 3. Logistics Landed-Cost Waterfall Container: EVFTA 0%
    console.log('[*] Capturing Logistics Landed-Cost Waterfall Container (EVFTA 0%)...');
    const elWaterfall = await page.$('.inn-waterfall-container');
    if (elWaterfall) {
        await elWaterfall.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);
        await elWaterfall.screenshot({ path: path.join(artifactDir, 'breakthrough_landed_cost_evfta.png') });
        console.log('[✓] Saved breakthrough_landed_cost_evfta.png');

        // 4. Click MFN Button
        const btnMFN = await page.$('#btnWaterfallMfn');
        if (btnMFN) {
            console.log('[*] Clicking #btnWaterfallMfn to switch to MFN 10% tariff...');
            await btnMFN.click();
            await page.waitForTimeout(1200);
            await elWaterfall.screenshot({ path: path.join(artifactDir, 'breakthrough_landed_cost_mfn.png') });
            console.log('[✓] Saved breakthrough_landed_cost_mfn.png');
        }
    } else {
        console.warn('[-] Could not find .inn-waterfall-container');
    }

    // 5. Operational Compliance: Breakthrough 3 - Live LOTO Isolation Topology
    console.log('[*] Capturing Operational Compliance: LOTO Topology...');
    const tabBtnPtw = await page.$('button[data-target-pane="opsPanePtw"]');
    if (tabBtnPtw) {
        await tabBtnPtw.scrollIntoViewIfNeeded();
        await tabBtnPtw.click();
        await page.waitForTimeout(500);
    }

    const elPtwPane = await page.$('#opsPanePtw');
    if (elPtwPane) {
        await elPtwPane.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1500);
        await elPtwPane.screenshot({ path: path.join(artifactDir, 'breakthrough_loto_topology_resting.png') });
        console.log('[✓] Saved breakthrough_loto_topology_resting.png (resting state)');

        // Click SVG Node 4 or LOTO toggle on Point 4 to isolate High-Pressure N2 line
        const node4 = await page.$('#svgNode4');
        if (node4) {
            console.log('[*] Clicking #svgNode4 to attach LOTO Lock #L-8824 and isolate N2 line...');
            await node4.click();
            await page.waitForTimeout(1200);
            await elPtwPane.screenshot({ path: path.join(artifactDir, 'breakthrough_loto_topology_isolated.png') });
            console.log('[✓] Saved breakthrough_loto_topology_isolated.png');

            // Click #btnSignPtw to stamp bilateral digital approval
            const btnSignPtw = await page.$('#btnSignPtw');
            if (btnSignPtw) {
                console.log('[*] Clicking #btnSignPtw for Bilateral Cryptographic Sign-Off...');
                await btnSignPtw.click();
                await page.waitForTimeout(1500);
                await elPtwPane.screenshot({ path: path.join(artifactDir, 'breakthrough_loto_bilateral_signed.png') });
                console.log('[✓] Saved breakthrough_loto_bilateral_signed.png');
            }
        }
    } else {
        console.warn('[-] Could not find #opsPanePtw');
    }

    // 6. Navigate to Solutions Page for Dual-Pane Paradigm Shift
    console.log('[*] Navigating to https://innoria.com/solutions...');
    await page.goto('https://innoria.com/solutions', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForTimeout(2500);

    const elDualPane = await page.$('.inn-dual-pane-grid');
    if (elDualPane) {
        await elDualPane.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);
        await elDualPane.screenshot({ path: path.join(artifactDir, 'breakthrough_dual_pane_paradigm_shift.png') });
        console.log('[✓] Saved breakthrough_dual_pane_paradigm_shift.png');
    }

    // 7. Navigate to Platform Page for Breakthrough 5: Live Agent Swarm Terminal
    console.log('[*] Navigating to https://innoria.com/platform...');
    await page.goto('https://innoria.com/platform', { waitUntil: 'domcontentloaded', timeout: 35000 });
    await page.waitForTimeout(2500);

    const elTerminal = await page.$('.mojo-terminal');
    if (elTerminal) {
        await elTerminal.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);

        // Click customs preset: Tờ Khai Lệch HS
        const btnPresetCustoms = await page.$('button[data-preset="customs"]');
        if (btnPresetCustoms) {
            console.log('[*] Clicking preset: 2. Khai Báo Lệch HS...');
            await btnPresetCustoms.click();
            await page.waitForTimeout(600);
        }

        // Click run button
        const btnRunSwarm = await page.$('#mojo-btn-run');
        if (btnRunSwarm) {
            console.log('[*] Clicking #mojo-btn-run to trigger 5-Agent Swarm execution...');
            await btnRunSwarm.click();
            // Wait for 5 sequential steps to finish + seal generation
            await page.waitForTimeout(3000);
            await elTerminal.screenshot({ path: path.join(artifactDir, 'breakthrough_agent_swarm_terminal.png') });
            console.log('[✓] Saved breakthrough_agent_swarm_terminal.png');
        }
    } else {
        console.warn('[-] Could not find .mojo-terminal');
    }

    await browser.close();
    console.log('[🎉] All Breakthrough Interactive States captured successfully!');
})();
