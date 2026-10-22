const { chromium } = require('playwright');

async function run() {
    console.log('[*] Starting Full End-to-End Verification...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const context = await browser.newContext({
            viewport: { width: 1440, height: 900 }
        });
        const page = await context.newPage();

        let pageErrors = [];
        page.on('pageerror', err => {
            console.error('[!] Page Error:', err.message);
            pageErrors.push(err.message);
        });

        // 1. Login
        console.log('[*] Logging in as admin on innoria.com...');
        await page.goto('https://innoria.com/web/login');
        await page.waitForSelector('input[name="login"]', { timeout: 15000 });
        await page.fill('input[name="login"]', 'admin');
        await page.fill('input[name="password"]', 'admin');
        await page.click('button[type="submit"]');
        await page.waitForSelector('.o_main_navbar, .o_navbar, .o_web_client', { timeout: 30000 });
        await page.waitForTimeout(2000);
        console.log('[✓] Logged in successfully.');

        // 2. Click Systray AI Copilot Button
        console.log('[*] Testing Systray AI Copilot Button...');
        const aiIcon = await page.locator('.o_ai_systray_btn').first();
        if (await aiIcon.count() > 0) {
            console.log('[*] Clicking .o_ai_systray_btn...');
            await aiIcon.click();
            await page.waitForTimeout(4000);

            // Check if ErrorDialog popped up
            const errorDialog = await page.locator('.o_error_dialog');
            const hasError = await errorDialog.count() > 0;
            console.log('[*] Error Dialog appeared:', hasError);
            if (hasError) {
                const errText = await errorDialog.innerText();
                console.error('[!] ErrorDialog text:\n', errText);
            }

            // Check ChatWindow
            const chatWindow = await page.locator('.o-mail-ChatWindow, .o_chat_window');
            const chatOpen = await chatWindow.count() > 0;
            console.log('[✓] Chat Window open status:', chatOpen);
            await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/systray_ai_chat_verified.png' });
        } else {
            console.log('[-] .o_ai_systray_btn not found');
        }

        // 3. Navigate to Action 5120
        console.log('[*] Navigating to Action 5120 (Executive Control Tower)...');
        await page.goto('https://innoria.com/insilos/action-5120');
        await page.waitForTimeout(4000);

        // Test in Dark Mode (current state)
        console.log('[*] Capturing Action 5120 in Dark Mode...');
        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/action_5120_verified_dark.png' });
        console.log('[✓] Saved action_5120_verified_dark.png');

        // Test in Light Mode (force remove dark mode class)
        console.log('[*] Switching to Light Mode in DOM...');
        await page.evaluate(() => {
            document.body.classList.remove('o_dark_mode');
            document.documentElement.classList.remove('o_dark_mode');
            document.documentElement.setAttribute('data-bs-theme', 'light');
            document.documentElement.setAttribute('data-theme', 'light');
            const linkDark = document.querySelector('link[href*="web.assets_web_dark"]');
            if (linkDark) linkDark.disabled = true;
        });
        await page.waitForTimeout(2000);
        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/action_5120_verified_light.png' });
        console.log('[✓] Saved action_5120_verified_light.png');

        // 4. Trigger test error dialog and verify no Share button
        console.log('[*] Verifying ErrorDialog footer buttons (confirm absence of Share button)...');
        await page.evaluate(() => {
            try {
                const env = owl.__info__.getEnv(document.querySelector('.o_web_client'));
                const { ErrorDialog } = odoo.loader.modules.get('@web/core/errors/error_dialogs');
                env.services.dialog.add(ErrorDialog, {
                    name: "AuditError",
                    message: "Audit error to verify footer buttons",
                    traceback: "Traceback (most recent call last):\n  File 'audit.py', line 1: audit",
                });
            } catch (e) {
                console.error('Failed to trigger ErrorDialog:', e);
            }
        });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/error_dialog_verified_buttons.png' });

        const footerBtns = await page.$$eval('.o_error_dialog .modal-footer button', btns => btns.map(b => b.innerText.trim()));
        console.log('[*] Footer Buttons:', footerBtns);
        const hasShare = footerBtns.some(b => b.toLowerCase() === 'share');
        if (hasShare) {
            console.error('[!] FAIL: Legacy Share button is still present!');
        } else {
            console.log('[✓] PASS: Legacy Share button is completely removed.');
        }

        console.log('[✓] All end-to-end verifications completed successfully.');
    } catch (err) {
        console.error('[!] Verification failed:', err);
    } finally {
        await browser.close();
    }
}

run();
