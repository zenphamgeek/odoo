const { chromium } = require('playwright');

async function getTraceback() {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.goto('https://innoria.com/web/login');
    await page.waitForSelector('input[name="login"]');
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForSelector('.o_main_navbar, .o_navbar, .o_web_client', { timeout: 30000 });
    await page.waitForTimeout(2000);

    const aiIcon = await page.locator('.o_ai_systray_btn').first();
    console.log('Clicking AI icon...');
    await aiIcon.click();
    await page.waitForTimeout(3000);

    // Expand details
    const details = page.locator('.o_error_dialog details, .o_error_dialog [role="button"]:has-text("technical details"), .o_error_dialog summary').first();
    if (await details.count() > 0) {
        await details.click();
        await page.waitForTimeout(1000);
    }

    const dialogText = await page.locator('.o_error_dialog').innerText();
    console.log('=== FULL DIALOG TEXT ===\n' + dialogText);
    
    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/error_dialog_expanded.png' });

    await browser.close();
}

getTraceback().catch(console.error);
