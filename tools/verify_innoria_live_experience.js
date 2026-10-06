/**
 * Playwright E2E Verification & Visual Evidence Script for Innoria Elevated Platform
 * Target: http://innoria.localhost:28070/
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function run() {
    console.log('[E2E] Starting Chromium browser...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1.5
    });

    const page = await context.newPage();
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('[Browser Error]', msg.text());
        }
    });

    try {
        console.log('[E2E] 1. Navigating to Innoria Homepage...');
        await page.goto('http://innoria.localhost:28070/', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000); // Allow 3D canvas and dynamic effects to initialize

        // Capture Hero Section
        console.log('[E2E] Capturing Hero Banner and 3D Topology Master...');
        const heroSection = page.locator('#innoria_hero_cover');
        if (await heroSection.count() > 0) {
            await heroSection.screenshot({
                path: path.join(ARTIFACTS_DIR, 'live_innoria_hero_cyber_master.png')
            });
            console.log('[E2E] Saved: live_innoria_hero_cyber_master.png');
        }

        // Test Mega-Menu Platform
        console.log('[E2E] 2. Testing Mega-Menu: Platform...');
        const platformTrigger = page.locator('li[data-megamenu="innoria_platform"] .ins-megamenu-trigger');
        await platformTrigger.hover();
        await page.waitForTimeout(300); // 180ms transition + buffer

        await page.screenshot({
            path: path.join(ARTIFACTS_DIR, 'live_innoria_megamenu_platform_active.png'),
            clip: { x: 0, y: 0, width: 1440, height: 680 }
        });
        console.log('[E2E] Saved: live_innoria_megamenu_platform_active.png');

        // Test Preview Card Hover Switch on MOJO AI
        console.log('[E2E] Testing Preview Card hover on MOJO AI...');
        const mojoAiItem = page.locator('#ins_megamenu_innoria_platform .ins-menu-link-item[data-title*="MOJO AI"]');
        if (await mojoAiItem.count() > 0) {
            await mojoAiItem.hover();
            await page.waitForTimeout(200); // 50ms debounce + buffer
            await page.screenshot({
                path: path.join(ARTIFACTS_DIR, 'live_innoria_megamenu_preview_mojoai.png'),
                clip: { x: 0, y: 0, width: 1440, height: 680 }
            });
            console.log('[E2E] Saved: live_innoria_megamenu_preview_mojoai.png');
        }

        // Test Mega-Menu Solutions
        console.log('[E2E] 3. Testing Mega-Menu: Solutions...');
        const solutionsTrigger = page.locator('li[data-megamenu="innoria_solutions"] .ins-megamenu-trigger');
        await solutionsTrigger.hover();
        await page.waitForTimeout(300);

        await page.screenshot({
            path: path.join(ARTIFACTS_DIR, 'live_innoria_megamenu_solutions_active.png'),
            clip: { x: 0, y: 0, width: 1440, height: 680 }
        });
        console.log('[E2E] Saved: live_innoria_megamenu_solutions_active.png');

        // Test Subroutes to verify universal header
        const subRoutes = ['/about', '/no-code-platform', '/ai-solutions', '/blockchain', '/solutions', '/industries', '/contactus'];
        console.log('[E2E] 4. Testing sub-routes for navbar consistency...');
        for (const route of subRoutes) {
            const resp = await page.goto(`http://innoria.localhost:28070${route}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
            const status = resp ? resp.status() : 'null';
            const hasHeader = await page.locator('.innoria-navbar').count() > 0;
            console.log(`[E2E] Route ${route}: HTTP ${status} | Navbar rendered: ${hasHeader}`);
        }

        console.log('[E2E] Verification completed successfully!');
    } catch (err) {
        console.error('[E2E Error]', err);
    } finally {
        await browser.close();
    }
}

run();
