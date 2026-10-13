const { chromium } = require('playwright');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function safeScreenshot(page, path) {
    try {
        await page.screenshot({ path, timeout: 10000 });
        console.log(`  [✓] Saved screenshot: ${path}`);
    } catch (e) {
        console.warn(`  [!] Warning capturing screenshot ${path}: ${e.message}`);
    }
}

async function auditThemeAndLayout() {
    console.log('[*] Starting Full Width & Dark/Light Theme Audit...');
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

    const results = {
        light: {},
        dark: {},
        passed: true,
        findings: []
    };

    try {
        // --- 1. LIGHT MODE AUDIT ---
        console.log('\n--- PHASE 1: LIGHT MODE AUDIT (1440x900) ---');
        const lightContext = await browser.newContext({
            viewport: { width: 1440, height: 900 },
            colorScheme: 'light'
        });
        const lightPage = await lightContext.newPage();

        console.log('[*] Logging into innoria.com (Light Mode)...');
        await lightPage.goto('https://innoria.com/web/login');
        await lightPage.waitForSelector('input[name="login"]', { timeout: 15000 });
        await lightPage.fill('input[name="login"]', 'admin');
        await lightPage.fill('input[name="password"]', 'admin');
        await lightPage.click('button[type="submit"]');
        await lightPage.waitForSelector('.o_main_navbar, .o_navbar, .o_web_client', { timeout: 30000 });
        await lightPage.waitForTimeout(3000);

        // Ensure light mode in DOM
        await lightPage.evaluate(() => {
            document.body.classList.remove('o_dark_mode');
            document.documentElement.classList.remove('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'light');
            document.documentElement.setAttribute('data-theme', 'light');
            const linkDark = document.querySelector('link[href*="web.assets_web_dark"]');
            if (linkDark) linkDark.disabled = true;
        });
        await lightPage.waitForTimeout(1000);

        // 1A. Home Launcher Grid Audit
        console.log('[*] Auditing Home Launcher Apps Grid Width...');
        const homeApps = await lightPage.locator('.o_apps').first();
        if (await homeApps.count() > 0) {
            const box = await homeApps.boundingBox();
            console.log(`  -> .o_apps bounding width: ${box ? box.width : 'N/A'}px`);
            results.light.homeAppsWidth = box ? box.width : null;
            if (box && box.width >= 1300) {
                console.log(`  [✓] PASS: .o_apps spans full container width (${box.width}px >= 1300px)`);
            }
        }
        await safeScreenshot(lightPage, `${ARTIFACT_DIR}/home_launcher_light_audit.png`);

        // 1B. Form View Width Audit (Sales / Quotation Form)
        console.log('[*] Navigating to Sales Orders list...');
        await lightPage.goto('https://innoria.com/odoo/action-320');
        await lightPage.waitForSelector('.o_list_table, .o_data_row', { timeout: 15000 });
        await lightPage.waitForTimeout(2000);

        // Measure List View Table Width
        console.log('[*] Auditing List View Table Width...');
        const listTable = await lightPage.locator('.o_list_table').first();
        if (await listTable.count() > 0) {
            const tableBox = await listTable.boundingBox();
            console.log(`  -> .o_list_table bounding width: ${tableBox ? tableBox.width : 'N/A'}px`);
            results.light.listTableWidth = tableBox ? tableBox.width : null;
            if (tableBox && tableBox.width >= 1350) {
                console.log(`  [✓] PASS: .o_list_table spans 100% full width (${tableBox.width}px >= 1350px)`);
            }
        }
        await safeScreenshot(lightPage, `${ARTIFACT_DIR}/sales_list_light_audit.png`);

        // Click first record or Create to check Form View
        const firstRow = await lightPage.locator('.o_data_row').first();
        if (await firstRow.count() > 0) {
            console.log('[*] Opening first Sales record for Form View audit...');
            await firstRow.click();
            await lightPage.waitForSelector('.o_form_sheet', { timeout: 15000 });
            await lightPage.waitForTimeout(2000);

            const formSheet = await lightPage.locator('.o_form_sheet').first();
            if (await formSheet.count() > 0) {
                const sheetBox = await formSheet.boundingBox();
                console.log(`  -> .o_form_sheet bounding width: ${sheetBox ? sheetBox.width : 'N/A'}px`);
                results.light.formSheetWidth = sheetBox ? sheetBox.width : null;
                if (sheetBox && sheetBox.width > 1200) {
                    console.log(`  [✓] PASS: .o_form_sheet is 100% full width (${sheetBox.width}px > 1200px)!`);
                } else if (sheetBox) {
                    console.log(`  [!] Notice: .o_form_sheet width is ${sheetBox.width}px`);
                }
            }
            await safeScreenshot(lightPage, `${ARTIFACT_DIR}/sales_form_light_audit.png`);
        }

        // 1C. Action 5120 (Executive Control Tower)
        console.log('[*] Navigating to Action 5120 (Executive Control Tower)...');
        await lightPage.goto('https://innoria.com/insilos/action-5120');
        await lightPage.waitForTimeout(3000);
        await safeScreenshot(lightPage, `${ARTIFACT_DIR}/action_5120_light_audit.png`);

        // --- 2. DARK MODE AUDIT ---
        console.log('\n--- PHASE 2: DARK MODE AUDIT (1440x900) ---');
        const darkContext = await browser.newContext({
            viewport: { width: 1440, height: 900 },
            colorScheme: 'dark'
        });
        const darkPage = await darkContext.newPage();

        console.log('[*] Logging into innoria.com (Dark Mode)...');
        await darkPage.goto('https://innoria.com/web/login');
        await darkPage.waitForSelector('input[name="login"]', { timeout: 15000 });
        await darkPage.fill('input[name="login"]', 'admin');
        await darkPage.fill('input[name="password"]', 'admin');
        await darkPage.click('button[type="submit"]');
        await darkPage.waitForSelector('.o_main_navbar, .o_navbar, .o_web_client', { timeout: 30000 });
        await darkPage.waitForTimeout(3000);

        // Switch to Dark Mode in DOM
        await darkPage.evaluate(() => {
            document.body.classList.add('o_dark_mode');
            document.documentElement.classList.add('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            document.documentElement.setAttribute('data-theme', 'dark');
            const linkDark = document.querySelector('link[href*="web.assets_web_dark"]');
            if (linkDark) linkDark.disabled = false;
        });
        await darkPage.waitForTimeout(1500);

        // 2A. Dark Mode Home Launcher
        console.log('[*] Auditing Home Launcher in Dark Mode...');
        await safeScreenshot(darkPage, `${ARTIFACT_DIR}/home_launcher_dark_audit.png`);

        // 2B. Dark Mode Sales Form View & Bare White Surface Check
        console.log('[*] Navigating to Sales Form View in Dark Mode...');
        await darkPage.goto('https://innoria.com/odoo/action-320');
        await darkPage.waitForSelector('.o_list_table, .o_data_row', { timeout: 15000 });
        await darkPage.waitForTimeout(2000);
        await darkPage.evaluate(() => {
            document.body.classList.add('o_dark_mode');
            document.documentElement.classList.add('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            document.documentElement.setAttribute('data-theme', 'dark');
        });
        await safeScreenshot(darkPage, `${ARTIFACT_DIR}/sales_list_dark_audit.png`);

        const darkRow = await darkPage.locator('.o_data_row').first();
        if (await darkRow.count() > 0) {
            await darkRow.click();
            await darkPage.waitForSelector('.o_form_sheet', { timeout: 15000 });
            await darkPage.waitForTimeout(2000);
            await darkPage.evaluate(() => {
                document.body.classList.add('o_dark_mode');
                document.documentElement.classList.add('o_dark_mode');
                document.documentElement.setAttribute('data-bs-theme', 'dark');
                document.documentElement.setAttribute('data-theme', 'dark');
            });

            // Check for bare white surfaces in dark mode
            const whiteSurfaces = await darkPage.evaluate(() => {
                const elements = document.querySelectorAll('.o_form_sheet, .o_form_sheet_bg, .card, .btn, .o_statusbar_status');
                let count = 0;
                elements.forEach(el => {
                    const bg = window.getComputedStyle(el).backgroundColor;
                    if (bg === 'rgb(255, 255, 255)' || bg === '#ffffff' || bg === 'rgb(248, 250, 252)') {
                        count++;
                    }
                });
                return count;
            });
            console.log(`  -> Bare white surfaces detected in dark mode form: ${whiteSurfaces}`);
            results.dark.bareWhiteSurfaces = whiteSurfaces;

            const darkFormSheet = await darkPage.locator('.o_form_sheet').first();
            if (await darkFormSheet.count() > 0) {
                const darkSheetBox = await darkFormSheet.boundingBox();
                console.log(`  -> Dark .o_form_sheet bounding width: ${darkSheetBox ? darkSheetBox.width : 'N/A'}px`);
                results.dark.formSheetWidth = darkSheetBox ? darkSheetBox.width : null;
            }
            await safeScreenshot(darkPage, `${ARTIFACT_DIR}/sales_form_dark_audit.png`);
        }

        // 2C. Dark Mode Action 5120
        console.log('[*] Navigating to Action 5120 in Dark Mode...');
        await darkPage.goto('https://innoria.com/insilos/action-5120');
        await darkPage.waitForTimeout(3000);
        await darkPage.evaluate(() => {
            document.body.classList.add('o_dark_mode');
            document.documentElement.classList.add('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            document.documentElement.setAttribute('data-theme', 'dark');
        });
        await safeScreenshot(darkPage, `${ARTIFACT_DIR}/action_5120_dark_audit.png`);

        console.log('\n[✓] Audit Complete. Results Summary:');
        console.log(JSON.stringify(results, null, 2));

    } catch (e) {
        console.error('[!] Audit Error:', e);
    } finally {
        await browser.close();
    }
}

auditThemeAndLayout();
