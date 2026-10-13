const { chromium } = require('playwright');
const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

(async () => {
    console.log('[*] Starting Market Terminal Verification...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--window-size=1440,900']
    });

    try {
        const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        const page = await context.newPage();

        console.log('[*] Logging in as admin...');
        await page.goto('https://innoria.com/web/login');
        await page.fill('input[name="login"]', 'admin');
        await page.fill('input[name="password"]', 'admin');
        await page.click('button[type="submit"]');

        await page.waitForSelector('.o_navbar, .o_main_navbar, .o_web_client', { timeout: 25000 });
        await page.waitForFunction(() => window.odoo && window.odoo.__WOWL_DEBUG__ && window.odoo.__WOWL_DEBUG__.root, { timeout: 25000 });

        // Dismiss any lingering modal if present
        const modal = await page.locator('.modal.show, .o_dialog, .modal-dialog');
        if (await modal.count() > 0) {
            console.log('[!] Modal dialog detected. Discarding...');
            const discardBtn = page.locator('button:has-text("Discard"), .btn-close, button.close');
            if (await discardBtn.count() > 0) {
                await discardBtn.first().click();
            } else {
                await page.keyboard.press('Escape');
            }
            await page.waitForTimeout(1500);
        }

        console.log('[*] Triggering Market Terminal SPA Action...');
        await page.evaluate(() => {
            return window.odoo.__WOWL_DEBUG__.root.env.services.action.doAction('insilos_market_terminal.action_market_terminal');
        });
        await page.waitForTimeout(4000);

        // Ensure dark mode classes
        await page.evaluate(() => {
            document.body.classList.add('o_dark_mode');
            document.documentElement.classList.add('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            document.documentElement.setAttribute('data-theme', 'dark');
            const linkDark = document.querySelector('link[href*="web.assets_web_dark"], link[href*="web.assets_web.min.css"]');
            if (linkDark) linkDark.href = '/web/assets/1/e7faa70/web.assets_web_dark.min.css';
        });
        await page.waitForTimeout(2000);

        const container = page.locator('.w_market_terminal').first();
        if (await container.count() > 0) {
            const box = await container.boundingBox();
            console.log('[Dark] Market Terminal Container Bounding Box:', JSON.stringify(box));
        }

        // Check canvas element and background
        const canvasAudit = await page.evaluate(() => {
            const canvases = document.querySelectorAll('.w_market_terminal canvas');
            const results = [];
            canvases.forEach((c, idx) => {
                const rect = c.getBoundingClientRect();
                results.push({ idx, width: rect.width, height: rect.height });
            });
            return results;
        });
        console.log('[Dark] Canvases found:', JSON.stringify(canvasAudit));

        await page.screenshot({ path: `${ARTIFACT_DIR}/market_terminal_dark_verified.png` });
        console.log(`[✓] Saved ${ARTIFACT_DIR}/market_terminal_dark_verified.png`);

        // Now test Light Mode
        console.log('[*] Switching to Light Mode...');
        await page.evaluate(() => {
            document.body.classList.remove('o_dark_mode');
            document.documentElement.classList.remove('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'light');
            document.documentElement.setAttribute('data-theme', 'light');
            const linkDark = document.querySelector('link[href*="web.assets_web_dark"]');
            if (linkDark) linkDark.href = '/web/assets/1/2b252cc/web.assets_web.min.css';
        });
        await page.waitForTimeout(2000);

        if (await container.count() > 0) {
            const boxLight = await container.boundingBox();
            console.log('[Light] Market Terminal Container Bounding Box:', JSON.stringify(boxLight));
        }

        await page.screenshot({ path: `${ARTIFACT_DIR}/market_terminal_light_verified.png` });
        console.log(`[✓] Saved ${ARTIFACT_DIR}/market_terminal_light_verified.png`);

    } catch (e) {
        console.error('[!] Error during Market Terminal verification:', e.message);
    } finally {
        await browser.close();
        console.log('[✓] Verification script finished.');
    }
})();
