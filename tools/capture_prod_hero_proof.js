const { chromium } = require('playwright');
const path = require('path');

const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function captureProdHero() {
    console.log('[*] Launching Chromium with host resolver rule to cluster ingress...');
    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--host-resolver-rules=MAP innoria.insilos.com 164.152.166.109'
        ]
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1.5,
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('[Prod Browser Error]', msg.text());
        }
    });

    try {
        console.log('[*] Navigating to http://innoria.insilos.com/ (waiting for domcontentloaded)...');
        await page.goto('http://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 35000 });
        console.log('[✓] Page loaded. Title:', await page.title());

        // Wait for 3D canvas
        console.log('[*] Waiting for #innoriaTopologyViewport canvas on production...');
        await page.waitForSelector('#innoriaTopologyViewport canvas', { timeout: 20000 });
        console.log('[✓] 3D canvas detected! Waiting 3.5s for dynamic animation to spin...');
        await page.waitForTimeout(3500);

        const heroSection = page.locator('#innoria_hero_cover');

        // 1. Capture Topology Mode (Logo Kinetic Sculpture & Constellation)
        const heroImgPath = path.join(ARTIFACTS_DIR, 'prod_innoria_hero_cyber_master.png');
        await heroSection.screenshot({ path: heroImgPath });
        console.log(`[✓] Captured production logo topology hero to: ${heroImgPath}`);

        // Also update live_innoria_hero_cyber_master.png artifact with the production proof
        const masterPath = path.join(ARTIFACTS_DIR, 'live_innoria_hero_cyber_master.png');
        await heroSection.screenshot({ path: masterPath });
        console.log(`[✓] Updated live_innoria_hero_cyber_master.png artifact to: ${masterPath}`);

        // 2. Toggle to 'Kiến Trúc Dịch Vụ' (Architecture Stack Mode)
        console.log('[*] Clicking Mode Toggle button (Kiến Trúc Dịch Vụ) on production...');
        const toggleBtn = page.locator('#innoriaModeToggleBtn');
        if (await toggleBtn.count() > 0) {
            await toggleBtn.click();
            await page.waitForTimeout(2500);

            const stackImgPath = path.join(ARTIFACTS_DIR, 'prod_innoria_hero_architecture_stack.png');
            await heroSection.screenshot({ path: stackImgPath });
            console.log(`[✓] Captured production Architecture Stack mode to: ${stackImgPath}`);
        }

        // 3. Focus on MOJO AI node to test interactive HUD telemetry card
        console.log('[*] Clicking MOJO AI button on production...');
        const mojoBtn = page.locator('button.innoria-hud-btn[data-node-key="MOJO_AI"]');
        if (await mojoBtn.count() > 0) {
            await mojoBtn.click();
            await page.waitForTimeout(2500);

            const mojoImgPath = path.join(ARTIFACTS_DIR, 'prod_innoria_hero_mojo_ai_focus.png');
            await heroSection.screenshot({ path: mojoImgPath });
            console.log(`[✓] Captured production MOJO AI Pod Focus & HUD to: ${mojoImgPath}`);
        }

        console.log('[✓] All production hero captures completed successfully!');
    } catch (err) {
        console.error('[!] Production capture error:', err);
    } finally {
        await browser.close();
    }
}

captureProdHero();
