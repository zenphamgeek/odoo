const { chromium } = require('playwright');

async function run() {
    console.log('[*] Capturing Action 5120 in REAL Light Mode via user settings...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const context = await browser.newContext({
            colorScheme: 'light',
            viewport: { width: 1440, height: 900 }
        });
        const page = await context.newPage();

        // 1. Login
        await page.goto('https://innoria.com/web/login');
        await page.waitForSelector('input[name="login"]', { timeout: 15000 });
        await page.fill('input[name="login"]', 'admin');
        await page.fill('input[name="password"]', 'admin');
        await page.click('button[type="submit"]');
        await page.waitForSelector('.o_main_navbar, .o_navbar, .o_web_client', { timeout: 30000 });
        await page.waitForTimeout(2000);

        // 2. Set user setting to 'light'
        console.log('[*] Switching color_scheme to light...');
        await page.evaluate(async () => {
            const env = owl.__info__.getEnv(document.querySelector('.o_web_client'));
            if (env.services.user && env.services.user.setUserSettings) {
                await env.services.user.setUserSettings('color_scheme', 'light');
            }
        });
        await page.waitForTimeout(3000);

        // 3. Navigate to Action 5120
        console.log('[*] Navigating to Action 5120 in Light Mode...');
        await page.goto('https://innoria.com/insilos/action-5120');
        await page.waitForSelector('.insilos-executive-tower, .insilos-kpi-card', { timeout: 15000 });
        await page.waitForTimeout(3000);

        // Capture Light Mode screenshot
        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/action_5120_real_light_mode.png' });
        console.log('[✓] Successfully captured action_5120_real_light_mode.png');

        // 4. Restore user setting back to 'dark'
        console.log('[*] Restoring color_scheme to dark...');
        await page.evaluate(async () => {
            const env = owl.__info__.getEnv(document.querySelector('.o_web_client'));
            if (env.services.user && env.services.user.setUserSettings) {
                await env.services.user.setUserSettings('color_scheme', 'dark');
            }
        });
        await page.waitForTimeout(2000);

    } catch (err) {
        console.error('[!] Failed:', err);
    } finally {
        await browser.close();
    }
}

run();
