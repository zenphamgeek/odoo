const { chromium } = require('playwright');

async function testModalButtons() {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--window-size=1440,900']
    });
    const page = await browser.newPage();
    
    // Login to local instance
    await page.goto('http://localhost:28069/web/login');
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForNavigation();
    await page.waitForTimeout(3000);

    console.log('[✓] Logged into http://localhost:28069');

    // Trigger FormViewDialog for product.category
    await page.evaluate(async () => {
        const { FormViewDialog } = odoo.loader.modules.get("@web/views/view_dialogs/form_view_dialog");
        const env = odoo.__WOWL_DEBUG__.root.env;
        env.services.dialog.add(FormViewDialog, {
            resModel: "product.category",
            title: "Create Category",
        });
    });

    await page.waitForTimeout(3000);

    // Inspect modal footer buttons
    const footerButtons = await page.evaluate(() => {
        const modal = document.querySelector('.modal.show, .modal-dialog');
        if (!modal) return null;
        const footer = modal.querySelector('.modal-footer');
        if (!footer) return { found: false };
        const buttons = Array.from(footer.querySelectorAll('button')).map(b => ({
            tag: b.tagName,
            text: b.textContent.trim(),
            classes: b.className,
            display: window.getComputedStyle(b).display,
            visibility: window.getComputedStyle(b).visibility,
            width: b.offsetWidth,
            height: b.offsetHeight,
        }));
        return {
            title: modal.querySelector('.modal-title')?.textContent?.trim(),
            buttons: buttons
        };
    });

    console.log('[!] Modal Inspection Result:', JSON.stringify(footerButtons, null, 2));

    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/modal_buttons_current_state.png' });

    await browser.close();
}

testModalButtons().catch(err => {
    console.error('Error running testModalButtons:', err);
    process.exit(1);
});
