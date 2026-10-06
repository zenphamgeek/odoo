const { chromium } = require('playwright');
const path = require('path');

const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function captureHero() {
    console.log('[*] Launching Chromium...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
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
        console.log('[*] Navigating to http://innoria.localhost:28070/ ...');
        await page.goto('http://innoria.localhost:28070/', { waitUntil: 'networkidle', timeout: 30000 });

        // Wait for 3D canvas
        console.log('[*] Waiting for #innoriaTopologyViewport canvas...');
        await page.waitForSelector('#innoriaTopologyViewport canvas', { timeout: 15000 });
        await page.waitForTimeout(3000); // Allow animation to settle into elegant spin

        // 1. Capture Topology Mode (Logo Kinetic Sculpture & Constellation)
        const heroSection = page.locator('#innoria_hero_cover');
        const heroImgPath = path.join(ARTIFACTS_DIR, 'live_innoria_hero_cyber_master.png');
        await heroSection.screenshot({ path: heroImgPath });
        console.log(`[✓] Captured authentic logo topology hero to: ${heroImgPath}`);

        // 2. Toggle to 'Kiến Trúc Dịch Vụ' (Architecture Stack Mode)
        console.log('[*] Clicking Mode Toggle button (Kiến Trúc Dịch Vụ)...');
        const toggleBtn = page.locator('#innoriaModeToggleBtn');
        if (await toggleBtn.count() > 0) {
            await toggleBtn.click();
            await page.waitForTimeout(2000); // Camera lerp to isometric stack

            const stackImgPath = path.join(ARTIFACTS_DIR, 'live_innoria_hero_architecture_stack.png');
            await heroSection.screenshot({ path: stackImgPath });
            console.log(`[✓] Captured Architecture Stack mode to: ${stackImgPath}`);
        }

        // 3. Focus on MOJO AI node to test interactive HUD telemetry card
        console.log('[*] Clicking MOJO AI button to inspect service pod focus...');
        const mojoBtn = page.locator('button.innoria-hud-btn[data-node-key="MOJO_AI"]');
        if (await mojoBtn.count() > 0) {
            await mojoBtn.click();
            await page.waitForTimeout(2000); // Camera lerp to pod and HUD card display

            const mojoImgPath = path.join(ARTIFACTS_DIR, 'live_innoria_hero_mojo_ai_focus.png');
            await heroSection.screenshot({ path: mojoImgPath });
            console.log(`[✓] Captured MOJO AI Pod Focus & HUD to: ${mojoImgPath}`);
        }

        console.log('[✓] All hero captures completed successfully!');
    } catch (err) {
        console.error('[!] Capture error:', err);
    } finally {
        await browser.close();
    }
}

captureHero();
