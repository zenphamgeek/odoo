const { chromium } = require('playwright');

async function capture() {
    console.log('[*] Capturing Action 5120 in true Light Mode...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const context = await browser.newContext({
            viewport: { width: 1440, height: 900 }
        });
        const page = await context.newPage();

        await page.goto('https://innoria.com/web/login');
        await page.waitForSelector('input[name="login"]');
        await page.fill('input[name="login"]', 'admin');
        await page.fill('input[name="password"]', 'admin');
        await page.click('button[type="submit"]');
        await page.waitForSelector('.o_main_navbar, .o_navbar, .o_web_client', { timeout: 30000 });
        await page.waitForTimeout(2000);

        console.log('[*] Navigating to Action 5120...');
        await page.goto('https://innoria.com/insilos/action-5120');
        await page.waitForSelector('.insilos-executive-tower, .insilos-kpi-card', { timeout: 15000 });
        await page.waitForTimeout(3000);

        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/action_5120_true_light_mode.png' });
        console.log('[✓] Successfully captured action_5120_true_light_mode.png');
    } catch (e) {
        console.error('Capture failed:', e);
    } finally {
        await browser.close();
    }
}

capture();
