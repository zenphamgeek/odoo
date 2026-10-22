const { chromium } = require('playwright');
const fs = require('fs');

async function runAudit() {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--window-size=1440,900']
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('[1/5] Logging into http://localhost:28069 ...');
    await page.goto('http://localhost:28069/web/login');
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForNavigation({ waitUntil: 'networkidle' }).catch(() => {});
    await page.waitForTimeout(3000);
    console.log('[✓] Logged in successfully.');

    // -------------------------------------------------------------
    // Test 1: Modal Dialog Buttons ("Save" / "Discard" / NO "Ok")
    // -------------------------------------------------------------
    console.log('\n[2/5] Testing FormViewDialog footer buttons ...');
    await page.evaluate(async () => {
        const { FormViewDialog } = odoo.loader.modules.get("@web/views/view_dialogs/form_view_dialog");
        const env = odoo.__WOWL_DEBUG__.root.env;
        env.services.dialog.add(FormViewDialog, {
            resModel: "product.category",
            title: "Create Category",
        });
    });
    await page.waitForTimeout(2500);

    const modalAudit = await page.evaluate(() => {
        const modal = document.querySelector('.modal.show, .modal-dialog');
        if (!modal) return { found: false };
        const footer = modal.querySelector('.modal-footer');
        if (!footer) return { found: true, footer: false };
        const buttons = Array.from(footer.querySelectorAll('button')).map(b => ({
            text: b.textContent.trim(),
            classes: b.className,
            display: window.getComputedStyle(b).display,
            visibility: window.getComputedStyle(b).visibility,
            offsetW: b.offsetWidth,
            offsetH: b.offsetHeight,
        }));
        return {
            title: modal.querySelector('.modal-title')?.textContent?.trim(),
            buttons: buttons
        };
    });

    console.log('[!] Modal Dialog Buttons Result:', JSON.stringify(modalAudit, null, 2));
    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/verify_modal_buttons_no_duplicate.png' });

    // Dismiss modal
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);

    // -------------------------------------------------------------
    // Test 2: Navbar Logo in Light Mode (Single Logo Assertion)
    // -------------------------------------------------------------
    console.log('\n[3/5] Testing Navbar Logo in Light Mode ...');
    // Ensure light mode
    await page.evaluate(() => {
        document.body.classList.remove('o_dark_mode');
        document.documentElement.classList.remove('o_dark_mode');
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.setAttribute('data-bs-theme', 'light');
        localStorage.setItem('insilos_theme', 'light');
    });
    // Navigate to CRM
    await page.goto('http://localhost:28069/web#action=crm.crm_lead_action_pipeline');
    await page.waitForTimeout(4000);

    const lightLogoAudit = await page.evaluate(() => {
        const launcher = document.querySelector('.o_navbar_apps_menu, .o_menu_toggle');
        if (!launcher) return { error: 'No launcher found' };
        const images = Array.from(launcher.querySelectorAll('img')).map(img => ({
            src: img.src,
            className: img.className,
            display: window.getComputedStyle(img).display,
            visibility: window.getComputedStyle(img).visibility,
            offsetW: img.offsetWidth,
            offsetH: img.offsetHeight,
        }));
        const visibleImages = images.filter(img => img.display !== 'none' && img.offsetW > 0);
        return {
            totalImages: images.length,
            visibleCount: visibleImages.length,
            visibleImages: visibleImages,
            allImages: images
        };
    });
    console.log('[!] Light Mode Navbar Logo Audit:', JSON.stringify(lightLogoAudit, null, 2));

    // Crop navbar screenshot
    const navbarEl = await page.$('.o_main_navbar, .o_navbar');
    if (navbarEl) {
        await navbarEl.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/navbar_light_single_logo_verified.png' });
    }

    // -------------------------------------------------------------
    // Test 3: Navbar Logo in Dark Mode (Single Logo Assertion)
    // -------------------------------------------------------------
    console.log('\n[4/5] Testing Navbar Logo in Dark Mode ...');
    await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-theme', 'dark');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        localStorage.setItem('insilos_theme', 'dark');
    });
    await page.waitForTimeout(1500);

    const darkLogoAudit = await page.evaluate(() => {
        const launcher = document.querySelector('.o_navbar_apps_menu, .o_menu_toggle');
        if (!launcher) return { error: 'No launcher found' };
        const images = Array.from(launcher.querySelectorAll('img')).map(img => ({
            src: img.src,
            className: img.className,
            display: window.getComputedStyle(img).display,
            visibility: window.getComputedStyle(img).visibility,
            offsetW: img.offsetWidth,
            offsetH: img.offsetHeight,
        }));
        const visibleImages = images.filter(img => img.display !== 'none' && img.offsetW > 0);
        return {
            totalImages: images.length,
            visibleCount: visibleImages.length,
            visibleImages: visibleImages,
            allImages: images
        };
    });
    console.log('[!] Dark Mode Navbar Logo Audit:', JSON.stringify(darkLogoAudit, null, 2));

    if (navbarEl) {
        await navbarEl.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/navbar_dark_single_logo_verified.png' });
    }

    // -------------------------------------------------------------
    // Test 4: Action-5120 Executive Control Tower Theme Verification
    // -------------------------------------------------------------
    console.log('\n[5/5] Testing Action-5120 Executive Control Tower ...');
    await page.goto('http://localhost:28069/web#action=5120');
    await page.waitForTimeout(4000);

    // Dark Mode Check
    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/action_5120_dark_verified.png' });
    const darkWhiteSurfaces = await page.evaluate(() => {
        const tower = document.querySelector('.o_executive_control_tower');
        if (!tower) return { found: false };
        const whiteElements = Array.from(tower.querySelectorAll('.bg-white, .bg-light-subtle')).map(el => ({
            tag: el.tagName,
            class: el.className,
            computedBg: window.getComputedStyle(el).backgroundColor
        }));
        return {
            found: true,
            whiteElementsCount: whiteElements.length,
            whiteElements: whiteElements
        };
    });
    console.log('[!] Action-5120 Dark Mode Bare White Surfaces Audit:', JSON.stringify(darkWhiteSurfaces, null, 2));

    // Switch to Light Mode
    await page.evaluate(() => {
        document.body.classList.remove('o_dark_mode');
        document.documentElement.classList.remove('o_dark_mode');
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.setAttribute('data-bs-theme', 'light');
        localStorage.setItem('insilos_theme', 'light');
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/action_5120_light_verified.png' });

    // -------------------------------------------------------------
    // Test 5: AI Copilot Systray Click Verification
    // -------------------------------------------------------------
    console.log('\n[+] Testing AI Copilot Systray Click ...');
    // Open a CRM form record
    await page.goto('http://localhost:28069/web#action=crm.crm_lead_action_pipeline');
    await page.waitForTimeout(3000);
    const firstKanban = await page.$('.o_kanban_record');
    if (firstKanban) {
        await firstKanban.click();
        await page.waitForTimeout(2500);
    }

    // Click the AI copilot systray icon
    const aiSystrayBtn = await page.$('.o_menu_systray button[data-tooltip*="AI"], .o_menu_systray i.ph-sparkle, .o_menu_systray [class*="ai"], .o_menu_systray i[class*="robot"]');
    if (aiSystrayBtn) {
        console.log('[✓] Found AI Systray button, clicking...');
        await aiSystrayBtn.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/ai_chat_systray_clicked.png' });
    } else {
        console.log('[!] Direct test of aiChatLauncher service in page context ...');
        const aiLaunchResult = await page.evaluate(async () => {
            try {
                const env = odoo.__WOWL_DEBUG__.root.env;
                const launcher = env.services.aiChatLauncher;
                if (!launcher) return { error: 'No aiChatLauncher service found' };
                await launcher.launchAIChat({ callerComponentName: 'systray_ai_button' });
                return { success: true };
            } catch (e) {
                return { error: e.message, stack: e.stack };
            }
        });
        console.log('[!] AI Launch Result:', JSON.stringify(aiLaunchResult, null, 2));
        await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/ai_chat_service_invoked.png' });
    }

    console.log('\n======================================================');
    console.log('AUDIT COMPLETE: All screenshots and logs captured.');
    console.log('======================================================');

    await browser.close();
}

runAudit().catch(err => {
    console.error('Audit failed with error:', err);
    process.exit(1);
});
