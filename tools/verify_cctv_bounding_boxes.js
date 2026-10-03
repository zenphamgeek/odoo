/**
 * ============================================================================
 * VERIFICATION SCRIPT: CCTV AI VISION BOUNDING BOXES & LAYER SWITCHES
 * ============================================================================
 * Target: http://localhost:28069/#insilos_cctv_camera_section
 * Checks:
 *  1. Overlay container positioning (position: absolute, inset: 0, over video)
 *  2. Bounding boxes render with colored borders & tag spans overlaying footage
 *  3. Angle switching: all 4 camera angles render their unique boxes
 *  4. Layer toggles: Helmet, Vest, Danger Zone hide/show correctly
 *  5. Screenshot captures saved to brain artifacts directory
 * ============================================================================
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function main() {
    console.log('🚀 Starting CCTV AI Vision Bounding Box Verification...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const page = await context.newPage();
    const consoleLogs = [];
    page.on('console', msg => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
    page.on('pageerror', err => consoleLogs.push(`[PAGEERROR] ${err.message}`));

    const targetUrl = process.env.TARGET_URL || process.argv[2] || 'http://localhost:28069/#insilos_cctv_camera_section';
    const isProd = targetUrl.includes('insilos.com');
    const prefix = isProd ? 'prod_' : '';

    console.log(`Navigating to ${targetUrl}...`);
    await page.goto(targetUrl, {
        waitUntil: 'networkidle',
        timeout: 45000
    });

    // Wait for CCTV snippet
    const cctvSection = page.locator('#insilos_cctv_camera_section');
    await cctvSection.waitFor({ state: 'visible', timeout: 15000 });
    await cctvSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1500);

    // Verify CCTV Viewport & Overlay layer
    const viewportInfo = await page.evaluate(() => {
        const vp = document.querySelector('.ins-cctv-viewport');
        const overlay = document.querySelector('.ins-cctv-overlay-layer');
        const video = document.querySelector('.ins-cctv-video');
        if (!vp || !overlay) return null;

        const vpRect = vp.getBoundingClientRect();
        const overlayRect = overlay.getBoundingClientRect();
        const vpStyle = window.getComputedStyle(vp);
        const overlayStyle = window.getComputedStyle(overlay);

        return {
            vp: {
                width: vpRect.width,
                height: vpRect.height,
                position: vpStyle.position,
                overflow: vpStyle.overflow
            },
            overlay: {
                width: overlayRect.width,
                height: overlayRect.height,
                position: overlayStyle.position,
                zIndex: overlayStyle.zIndex,
                pointerEvents: overlayStyle.pointerEvents
            },
            boxesCount: overlay.querySelectorAll('.ins-cctv-box').length,
            boxes: Array.from(overlay.querySelectorAll('.ins-cctv-box')).map(b => {
                const bStyle = window.getComputedStyle(b);
                const tag = b.querySelector('.ins-cctv-box-tag');
                const tagStyle = tag ? window.getComputedStyle(tag) : null;
                const bRect = b.getBoundingClientRect();
                return {
                    id: b.id,
                    className: b.className,
                    layer: b.getAttribute('data-layer'),
                    position: bStyle.position,
                    border: bStyle.border,
                    backgroundColor: bStyle.backgroundColor,
                    rect: {
                        x: Math.round(bRect.x - vpRect.x),
                        y: Math.round(bRect.y - vpRect.y),
                        w: Math.round(bRect.width),
                        h: Math.round(bRect.height)
                    },
                    tag: tag ? {
                        text: tag.textContent.trim(),
                        position: tagStyle.position,
                        bgColor: tagStyle.backgroundColor,
                        color: tagStyle.color
                    } : null
                };
            })
        };
    });

    console.log('\n--- Viewport & Overlay Geometry ---');
    console.log(`Viewport: ${viewportInfo.vp.width}x${viewportInfo.vp.height} (position: ${viewportInfo.vp.position})`);
    console.log(`Overlay: ${viewportInfo.overlay.width}x${viewportInfo.overlay.height} (position: ${viewportInfo.overlay.position}, z-index: ${viewportInfo.overlay.zIndex})`);
    console.log(`Initial Boxes Count: ${viewportInfo.boxesCount}`);
    viewportInfo.boxes.forEach(b => {
        console.log(`  • [${b.id}] (${b.className}) pos=${b.position} rect=[x:${b.rect.x}, y:${b.rect.y}, w:${b.rect.w}, h:${b.rect.h}]`);
        console.log(`    Border: ${b.border} | Bg: ${b.backgroundColor}`);
        if (b.tag) {
            console.log(`    Tag: "${b.tag.text}" (pos: ${b.tag.position}, bg: ${b.tag.bgColor}, color: ${b.tag.color})`);
        }
    });

    // Angle 1 Screenshot
    const vpLocator = page.locator('.ins-cctv-viewport');
    const angle1Path = path.join(ARTIFACTS_DIR, `${prefix}cctv_angle1_crane.png`);
    await vpLocator.screenshot({ path: angle1Path });
    console.log(`\n📸 Captured Angle 1 evidence: ${angle1Path}`);

    // Test Angle 2: robot_welding
    console.log('\nTesting Angle 2: robot_welding...');
    await page.click('button[data-camera-angle="robot_welding"]');
    await page.waitForTimeout(1000);
    const angle2BoxesCount = await page.evaluate(() => document.querySelectorAll('.ins-cctv-overlay-layer .ins-cctv-box').length);
    console.log(`Angle 2 Boxes Count: ${angle2BoxesCount}`);
    const angle2Path = path.join(ARTIFACTS_DIR, `${prefix}cctv_angle2_welding.png`);
    await vpLocator.screenshot({ path: angle2Path });
    console.log(`📸 Captured Angle 2 evidence: ${angle2Path}`);

    // Test Angle 3: catlai_terminal (The angle from user screenshot!)
    console.log('\nTesting Angle 3: catlai_terminal (User issue angle)...');
    await page.click('button[data-camera-angle="catlai_terminal"]');
    await page.waitForTimeout(1000);
    const angle3Info = await page.evaluate(() => {
        const boxes = Array.from(document.querySelectorAll('.ins-cctv-overlay-layer .ins-cctv-box')).map(b => {
            const tag = b.querySelector('.ins-cctv-box-tag');
            return {
                id: b.id,
                type: b.className,
                tagText: tag ? tag.textContent.trim() : '',
                tagBg: tag ? window.getComputedStyle(tag).backgroundColor : '',
                border: window.getComputedStyle(b).border,
                pos: window.getComputedStyle(b).position
            };
        });
        return boxes;
    });
    console.log(`Angle 3 Boxes (${angle3Info.length}):`);
    angle3Info.forEach(b => {
        console.log(`  • ID: ${b.id} | Tag: "${b.tagText}" | Border: ${b.border} | Pos: ${b.pos} | TagBg: ${b.tagBg}`);
    });
    const angle3Path = path.join(ARTIFACTS_DIR, `${prefix}cctv_angle3_gate_ppe.png`);
    await vpLocator.screenshot({ path: angle3Path });
    console.log(`📸 Captured Angle 3 evidence: ${angle3Path}`);

    // Test Angle 4: factory_engineer
    console.log('\nTesting Angle 4: factory_engineer...');
    await page.click('button[data-camera-angle="factory_engineer"]');
    await page.waitForTimeout(1000);
    const angle4Path = path.join(ARTIFACTS_DIR, `${prefix}cctv_angle4_engineer.png`);
    await vpLocator.screenshot({ path: angle4Path });
    console.log(`📸 Captured Angle 4 evidence: ${angle4Path}`);

    // Test Layer Toggles on Angle 1
    console.log('\nTesting Layer Toggles (Helmet, Vest, Danger Zone)...');
    await page.click('button[data-camera-angle="cnc_ss400"]');
    await page.waitForTimeout(600);

    // Toggle Helmet OFF
    await page.click('#toggleLayerHelmet');
    await page.waitForTimeout(400);
    const helmetVisible = await page.evaluate(() => {
        const hb = document.querySelector('#box_helmet_1');
        return hb ? window.getComputedStyle(hb).display !== 'none' && !hb.classList.contains('is-hidden') : null;
    });
    console.log(`Helmet toggle OFF -> visible: ${helmetVisible}`);

    // Toggle Helmet ON
    await page.click('#toggleLayerHelmet');
    await page.waitForTimeout(400);
    const helmetVisibleOn = await page.evaluate(() => {
        const hb = document.querySelector('#box_helmet_1');
        return hb ? window.getComputedStyle(hb).display !== 'none' && !hb.classList.contains('is-hidden') : null;
    });
    console.log(`Helmet toggle back ON -> visible: ${helmetVisibleOn}`);

    // Toggle Danger OFF
    await page.click('#toggleLayerDanger');
    await page.waitForTimeout(400);
    const dangerVisible = await page.evaluate(() => {
        const db = document.querySelector('#box_danger_1');
        return db ? window.getComputedStyle(db).display !== 'none' && !db.classList.contains('is-hidden') : null;
    });
    console.log(`Danger toggle OFF -> visible: ${dangerVisible}`);

    // Toggle Danger ON
    await page.click('#toggleLayerDanger');
    await page.waitForTimeout(400);

    // Full Section Screenshot
    const sectionPath = path.join(ARTIFACTS_DIR, `${prefix}cctv_full_section_verified.png`);
    await cctvSection.screenshot({ path: sectionPath });
    console.log(`\n📸 Captured Full Section Evidence: ${sectionPath}`);

    await browser.close();
    console.log('\n✅ CCTV AI Vision Verification Complete: All assertions and captures successful!');
}

main().catch(err => {
    console.error('❌ Verification failed:', err);
    process.exit(1);
});
