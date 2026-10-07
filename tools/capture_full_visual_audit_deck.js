#!/usr/bin/env node
/**
 * tools/capture_full_visual_audit_deck.js
 * =============================================================================
 * Captures High-Res Visual Audit Deck across Desktop (1920x1080) & Mobile (390x844)
 * for:
 *   1. / (Homepage - Liquid Spatial Hero, Cardless Solutions, YOLO HUD)
 *   2. /solutions (Autonomous ERP Core, Liquid Comparison Matrix)
 *   3. /industries (Industrial Case Studies, 101 Industries Catalog)
 *   4. /resources (Knowledge Hub, Whitepaper Cards)
 *   5. /showcase-3d (3D Interactive Architecture Suite)
 * =============================================================================
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = process.env.BASE_URL || 'http://innoria.localhost:28070';
const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

if (!fs.existsSync(ARTIFACTS_DIR)) {
    fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const ROUTES = [
    { route: '/', name: 'homepage' },
    { route: '/solutions', name: 'solutions' },
    { route: '/industries', name: 'industries' },
    { route: '/resources', name: 'resources' },
    { route: '/showcase-3d', name: 'showcase_3d' }
];

const VIEWPORTS = [
    { name: 'desktop_1920', width: 1920, height: 1080, isMobile: false },
    { name: 'mobile_390', width: 390, height: 844, isMobile: true }
];

async function captureAuditDeck() {
    console.log('================================================================================');
    console.log('📸 CAPTURING HIGH-RES VISUAL AUDIT DECK');
    console.log(`Target: ${BASE_URL}`);
    console.log(`Artifacts Output: ${ARTIFACTS_DIR}`);
    console.log('================================================================================\n');

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    for (const vp of VIEWPORTS) {
        console.log(`\n--- Viewport: ${vp.name} (${vp.width}x${vp.height}) ---`);
        const context = await browser.newContext({
            viewport: { width: vp.width, height: vp.height },
            isMobile: vp.isMobile,
            deviceScaleFactor: 2
        });
        const page = await context.newPage();

        for (const r of ROUTES) {
            const url = `${BASE_URL}${r.route}`;
            console.log(`[*] Capturing ${r.name} from ${url}...`);
            try {
                await page.goto(url, { waitUntil: 'load', timeout: 30000 });
                await page.waitForTimeout(2500); // Allow WebGL & CSS animations to settle

                const filename = `audit_${r.name}_${vp.name}.png`;
                const filepath = path.join(ARTIFACTS_DIR, filename);

                // Capture viewport view
                await page.screenshot({ path: filepath, fullPage: false });
                console.log(`[✓] Saved: ${filename}`);

                // For homepage desktop, also capture full page
                if (r.route === '/' && !vp.isMobile) {
                    const fullFilename = `audit_${r.name}_${vp.name}_fullpage.png`;
                    await page.screenshot({ path: path.join(ARTIFACTS_DIR, fullFilename), fullPage: true });
                    console.log(`[✓] Saved full page: ${fullFilename}`);
                }
            } catch (err) {
                console.error(`[-] Error capturing ${r.name}: ${err.message}`);
            }
        }
        await context.close();
    }

    await browser.close();
    console.log('\n================================================================================');
    console.log('✅ HIGH-RES VISUAL AUDIT DECK CAPTURE COMPLETE');
    console.log('================================================================================\n');
}

captureAuditDeck().catch(console.error);
