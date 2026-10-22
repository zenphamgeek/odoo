const { chromium } = require('playwright');

async function testDismiss() {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--window-size=1440,900']
    });
    const page = await browser.newPage();
    await page.goto('https://innoria.com/web/login');
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    // Go to action-320 (Sales)
    await page.goto('https://innoria.com/odoo/action-320');
    await page.waitForTimeout(3000);

    // Check if modal dialog exists
    const modal = await page.locator('.modal.show, .o_dialog, .modal-dialog');
    if (await modal.count() > 0) {
        console.log('[!] Modal dialog detected. Attempting to discard...');
        const discardBtn = page.locator('button:has-text("Discard"), .btn-close, button.close');
        if (await discardBtn.count() > 0) {
            await discardBtn.first().click();
            console.log('[✓] Clicked Discard.');
            await page.waitForTimeout(2000);
        } else {
            await page.keyboard.press('Escape');
            console.log('[✓] Pressed Escape.');
            await page.waitForTimeout(2000);
        }
    }

    // Now inspect .o_list_table in sales
    const listTable = await page.locator('.o_list_table').first();
    if (await listTable.count() > 0) {
        const box = await listTable.boundingBox();
        console.log(`[✓] Real .o_list_table bounding width: ${box ? box.width : 'N/A'}px`);
    } else {
        console.log('No .o_list_table found.');
    }

    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/sales_list_modal_dismissed.png' });
    await browser.close();
}

testDismiss();
