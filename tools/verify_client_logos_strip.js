const { chromium } = require('playwright');
const path = require('path');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

(async () => {
    console.log('=== VERIFYING CLIENT LOGO STRIP ON INNORIA HOMEPAGE ===');
    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-ipv6',
            '--host-resolver-rules=MAP innoria.insilos.com 172.67.156.74'
        ]
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2,
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    try {
        console.log('[*] Navigating to https://innoria.insilos.com/...');
        await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(3000);

        const strip = page.locator('.innoria-client-strip');
        await strip.waitFor({ timeout: 15000 });

        // Scroll to strip
        await strip.scrollIntoViewIfNeeded();
        await page.waitForTimeout(800);

        // Verify Innoria logo is NOT present
        const innoriaLogoCount = await page.locator('.innoria-client-strip img[src*="innoria_logo"]').count();
        console.log(`[✓] Innoria logo count inside client strip: ${innoriaLogoCount} (Expected: 0)`);
        if (innoriaLogoCount !== 0) {
            throw new Error(`Innoria logo still found in client strip! Count: ${innoriaLogoCount}`);
        }

        // Verify exactly 3 client strip images
        const clientImages = page.locator('.innoria-client-strip .client-logo-img');
        const imgCount = await clientImages.count();
        console.log(`[✓] Client logo strip count: ${imgCount} (Expected: 3)`);
        if (imgCount !== 3) {
            throw new Error(`Expected exactly 3 client strip images, found ${imgCount}`);
        }

        // Check computed height of the logo images
        const heights = [];
        for (let i = 0; i < imgCount; i++) {
            const h = await clientImages.nth(i).evaluate(el => el.clientHeight);
            const w = await clientImages.nth(i).evaluate(el => el.clientWidth);
            const src = await clientImages.nth(i).getAttribute('src');
            heights.push({ src: path.basename(src), width: w, height: h });
        }
        console.log('[✓] Logo image dimensions:', heights);

        // Capture Desktop screenshot
        const desktopShot = path.join(ARTIFACT_DIR, 'client_logos_desktop_verified.png');
        await strip.screenshot({ path: desktopShot });
        console.log(`[✓] Captured desktop screenshot: ${desktopShot}`);

        // Capture in page context
        const box = await strip.boundingBox();
        await page.evaluate((y) => window.scrollTo({ top: y - 100, behavior: 'instant' }), box.y);
        await page.waitForTimeout(500);
        const inPageShot = path.join(ARTIFACT_DIR, 'client_logos_in_page_context.png');
        await page.screenshot({ path: inPageShot });
        console.log(`[✓] Captured in-page context screenshot: ${inPageShot}`);

        console.log('=== CLIENT LOGO VERIFICATION SUCCESSFUL ===');
    } catch (e) {
        console.error('[!] Verification failed:', e);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
