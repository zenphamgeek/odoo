const { chromium } = require('playwright');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function run() {
    console.log('[*] Capturing Sales & Distribution Form and List View in Full Width...');
    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--window-size=1440,900'
        ]
    });

    try {
        const context = await browser.newContext({
            viewport: { width: 1440, height: 900 }
        });
        const page = await context.newPage();

        await page.goto('https://innoria.com/web/login');
        await page.fill('input[name="login"]', 'admin');
        await page.fill('input[name="password"]', 'admin');
        await Promise.all([
            page.waitForNavigation(),
            page.click('button[type="submit"]')
        ]);
        console.log('[✓] Logged in. Waiting for Home Launcher...');
        await page.waitForTimeout(5000);

        // Click "Sales & Distribution (SD)" app tile
        console.log('[*] Clicking Sales & Distribution app tile...');
        const sdApp = page.locator('.o_app:has-text("Sales & Distribution"), .o_app[data-menu-xmlid*="sale"]').first();
        if (await sdApp.count() > 0) {
            await sdApp.click();
        } else {
            console.log('[*] Navigating to /odoo/action-320 directly...');
            await page.goto('https://innoria.com/odoo/action-320');
        }

        await page.waitForTimeout(3000);

        // Measure List View Table
        const listTable = page.locator('.o_list_table, .o_content table').first();
        if (await listTable.count() > 0) {
            const tableBox = await listTable.boundingBox();
            console.log(`  -> List Table bounding width: ${tableBox ? tableBox.width : 'N/A'}px`);
        }
        await page.screenshot({ path: `${ARTIFACT_DIR}/sales_list_verified_dark.png` });
        console.log('  [✓] Saved sales_list_verified_dark.png');

        // Click first record
        const firstRow = page.locator('.o_data_row').first();
        if (await firstRow.count() > 0) {
            console.log('[*] Opening first record in Form View...');
            await firstRow.click();
            await page.waitForSelector('.o_form_sheet', { timeout: 15000 });
            await page.waitForTimeout(2000);

            const formSheet = page.locator('.o_form_sheet').first();
            const sheetBox = await formSheet.boundingBox();
            console.log(`  -> Form Sheet bounding width: ${sheetBox ? sheetBox.width : 'N/A'}px`);

            await page.screenshot({ path: `${ARTIFACT_DIR}/sales_form_verified_dark.png` });
            console.log('  [✓] Saved sales_form_verified_dark.png');

            // Now test Light Mode on the Form View
            console.log('[*] Switching to Light Mode on Form View...');
            await page.evaluate(() => {
                document.body.classList.remove('o_dark_mode');
                document.documentElement.classList.remove('o_dark_mode');
                document.documentElement.setAttribute('data-bs-theme', 'light');
                document.documentElement.setAttribute('data-theme', 'light');
                const darkLinks = document.querySelectorAll('link[href*="assets_web_dark"]');
                darkLinks.forEach(l => l.disabled = true);
            });
            await page.waitForTimeout(1500);

            const lightSheetBox = await formSheet.boundingBox();
            console.log(`  -> Light Mode Form Sheet bounding width: ${lightSheetBox ? lightSheetBox.width : 'N/A'}px`);

            await page.screenshot({ path: `${ARTIFACT_DIR}/sales_form_verified_light.png` });
            console.log('  [✓] Saved sales_form_verified_light.png');
        } else {
            console.log('[-] No data rows found in list view.');
        }

    } catch (e) {
        console.error('[!] Error in run:', e);
    } finally {
        await browser.close();
    }
}

run();
