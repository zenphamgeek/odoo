const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function captureDeck() {
    const TARGET_URL = process.env.TARGET_URL || 'https://innoria.insilos.com/';
    const outDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
    const localArtifactDir = '/home/zen/O20/.agents/teamwork/worker_3d_physics_geometry/screenshots';
    const refinementArtifactDir = '/home/zen/O20/.agents/teamwork/worker_3d_physics_refinement/screenshots';
    
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }
    if (!fs.existsSync(localArtifactDir)) {
        fs.mkdirSync(localArtifactDir, { recursive: true });
    }
    if (!fs.existsSync(refinementArtifactDir)) {
        fs.mkdirSync(refinementArtifactDir, { recursive: true });
    }

    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-ipv6',
            '--host-resolver-rules=MAP innoria.insilos.com 172.67.156.74'
        ]
    });

    async function saveScreenshot(element, filename) {
        const p1 = path.join(outDir, filename);
        const p2 = path.join(localArtifactDir, filename);
        const p3 = path.join(refinementArtifactDir, filename);
        await element.screenshot({ path: p1 });
        try {
            fs.copyFileSync(p1, p2);
            fs.copyFileSync(p1, p3);
        } catch (e) {}
        console.log(`[✓] Saved: ${filename}`);
    }

    // =========================================================================
    // 1. DESKTOP VIEWPORT (1440 x 900)
    // =========================================================================
    console.log('\n--- CAPTURING DESKTOP VIEWPORT (1440x900) ---');
    const desktopContext = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2,
        ignoreHTTPSErrors: true
    });
    const desktopPage = await desktopContext.newPage();
    console.log(`Navigating desktop to ${TARGET_URL} ...`);
    await desktopPage.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await desktopPage.waitForTimeout(3000);

    // Scroll to #architecture_deck safely below sticky navbar
    await desktopPage.evaluate(() => {
        const el = document.getElementById('architecture_deck');
        if (el) {
            const y = el.getBoundingClientRect().top + window.pageYOffset - 90;
            window.scrollTo({ top: y, behavior: 'instant' });
        }
    });
    await desktopPage.waitForTimeout(1500);

    const desktopDeck = await desktopPage.$('#architecture_deck');
    const desktopStage = await desktopPage.$('#stageCard');

    if (desktopStage && desktopDeck) {
        // 1.1 Resting State
        await saveScreenshot(desktopStage, 'deck_3d_desktop_resting.png');
        await saveScreenshot(desktopStage, 'deck_3d_resting.png'); // legacy alias

        // 1.2 Pulled-Out States for All 4 Layers (Layer 0, 1, 2, 3)
        const layerNames = [
            'slab0_nocode',
            'slab1_services',
            'slab2_ai',
            'slab3_data_erp'
        ];

        for (let idx = 0; idx < 4; idx++) {
            await desktopPage.evaluate((i) => {
                const slab = document.getElementById(`slab-${i}`);
                if (slab) {
                    slab.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                    slab.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                }
            }, idx);
            await desktopPage.waitForTimeout(1000);
            await saveScreenshot(desktopStage, `deck_3d_desktop_${layerNames[idx]}.png`);
            if (idx === 1) {
                await saveScreenshot(desktopStage, 'deck_3d_slab1_pulled.png'); // legacy alias
            }
        }

        // Reset View back to neutral
        await desktopPage.evaluate(() => {
            const btn = document.getElementById('btnResetView');
            if (btn) btn.click();
        });
        await desktopPage.waitForTimeout(800);

        // 1.3 Exploded Mode
        await desktopPage.evaluate(() => {
            const btn = document.getElementById('btnExplode');
            if (btn) btn.click();
        });
        await desktopPage.waitForTimeout(800);
        await saveScreenshot(desktopStage, 'deck_3d_desktop_exploded.png');

        // Close Exploded Mode
        await desktopPage.evaluate(() => {
            const btn = document.getElementById('btnExplode');
            if (btn) btn.click();
        });
        await desktopPage.waitForTimeout(600);

        // 1.4 Drag Orbit State (Simulate mouse drag on stageCard)
        const box = await desktopStage.boundingBox();
        if (box) {
            const startX = box.x + box.width / 2;
            const startY = box.y + box.height / 2;
            await desktopPage.mouse.move(startX, startY);
            await desktopPage.mouse.down();
            await desktopPage.mouse.move(startX + 150, startY + 70, { steps: 15 });
            await desktopPage.mouse.up();
            await desktopPage.waitForTimeout(1000); // Wait for inertia & spring LERP
            await saveScreenshot(desktopStage, 'deck_3d_desktop_drag_orbit.png');
        }

        // 1.5 Full Section Capture
        await desktopPage.evaluate(() => {
            const btn = document.getElementById('btnResetView');
            if (btn) btn.click();
        });
        await desktopPage.waitForTimeout(600);
        await saveScreenshot(desktopDeck, 'deck_3d_desktop_full_section.png');
        await saveScreenshot(desktopDeck, 'deck_3d_full_section.png'); // legacy alias
    }
    await desktopContext.close();

    // =========================================================================
    // 2. MOBILE VIEWPORT (375 x 812)
    // =========================================================================
    console.log('\n--- CAPTURING MOBILE VIEWPORT (375x812) ---');
    const mobileContext = await browser.newContext({
        viewport: { width: 375, height: 812 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
        ignoreHTTPSErrors: true
    });
    const mobilePage = await mobileContext.newPage();
    console.log(`Navigating mobile to ${TARGET_URL} ...`);
    await mobilePage.goto(TARGET_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await mobilePage.waitForTimeout(3000);

    // Scroll to #architecture_deck safely below sticky navbar
    await mobilePage.evaluate(() => {
        const el = document.getElementById('architecture_deck');
        if (el) {
            const y = el.getBoundingClientRect().top + window.pageYOffset - 70;
            window.scrollTo({ top: y, behavior: 'instant' });
        }
    });
    await mobilePage.waitForTimeout(1500);

    const mobileDeck = await mobilePage.$('#architecture_deck');
    const mobileStage = await mobilePage.$('#stageCard');

    if (mobileStage && mobileDeck) {
        // 2.1 Mobile Resting State
        await saveScreenshot(mobileStage, 'deck_3d_mobile_resting.png');

        // 2.2 Mobile Pulled-Out States
        const layerNames = [
            'slab0_nocode',
            'slab1_services',
            'slab2_ai',
            'slab3_data_erp'
        ];

        for (let idx = 0; idx < 4; idx++) {
            await mobilePage.evaluate((i) => {
                const slab = document.getElementById(`slab-${i}`);
                if (slab) {
                    slab.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                }
            }, idx);
            await mobilePage.waitForTimeout(1000);
            await saveScreenshot(mobileStage, `deck_3d_mobile_${layerNames[idx]}.png`);
            if (idx === 1) {
                await saveScreenshot(mobileStage, 'deck_3d_mobile_pulled.png');
            }
        }

        // Reset View
        await mobilePage.evaluate(() => {
            const btn = document.getElementById('btnResetView');
            if (btn) btn.click();
        });
        await mobilePage.waitForTimeout(800);

        // 2.3 Mobile Exploded Mode
        await mobilePage.evaluate(() => {
            const btn = document.getElementById('btnExplode');
            if (btn) btn.click();
        });
        await mobilePage.waitForTimeout(800);
        await saveScreenshot(mobileStage, 'deck_3d_mobile_exploded.png');

        // Close Exploded Mode
        await mobilePage.evaluate(() => {
            const btn = document.getElementById('btnExplode');
            if (btn) btn.click();
        });
        await mobilePage.waitForTimeout(600);

        // 2.4 Mobile Drag Orbit State (Touch simulation)
        await mobilePage.evaluate(() => {
            const stage = document.getElementById('stageCard');
            if (stage) {
                const rect = stage.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                const touchStart = new Touch({ identifier: 1, target: stage, clientX: cx, clientY: cy });
                const touchMove = new Touch({ identifier: 1, target: stage, clientX: cx + 110, clientY: cy + 50 });
                stage.dispatchEvent(new TouchEvent('touchstart', { touches: [touchStart], changedTouches: [touchStart], bubbles: true }));
                window.dispatchEvent(new TouchEvent('touchmove', { touches: [touchMove], changedTouches: [touchMove], bubbles: true }));
                window.dispatchEvent(new TouchEvent('touchend', { touches: [], changedTouches: [touchMove], bubbles: true }));
            }
        });
        await mobilePage.waitForTimeout(1000);
        await saveScreenshot(mobileStage, 'deck_3d_mobile_drag_orbit.png');

        // 2.5 Mobile Full Section Capture
        await mobilePage.evaluate(() => {
            const btn = document.getElementById('btnResetView');
            if (btn) btn.click();
        });
        await mobilePage.waitForTimeout(600);
        await saveScreenshot(mobileDeck, 'deck_3d_mobile_full_section.png');
    }
    await mobileContext.close();

    await browser.close();
    console.log('\n[SUCCESS] All Desktop and Mobile 3D Deck visual captures completed cleanly!');
}

captureDeck().catch((err) => {
    console.error('Capture error:', err);
    process.exit(1);
});
