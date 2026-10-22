const { chromium } = require('playwright');

async function auditHeader() {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        }
    });

    console.log('[*] Navigating to https://innoria.com/ ...');
    const response = await page.goto('https://innoria.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log(`[✓] Status: ${response.status()}`);
    await page.waitForTimeout(2000);

    const headerAudit = await page.evaluate(() => {
        const header = document.querySelector('#wrapwrap > header');
        const nav = document.querySelector('nav.navbar');
        const brand = document.querySelector('a.navbar-brand[data-name="Navbar Logo"], a.navbar-brand');
        const topMenu = document.querySelector('#top_menu');
        const ctaBtn = document.querySelector('.btn_cta, a.btn-innoria-nav');
        
        return {
            hasHeader: !!header,
            headerClasses: header ? header.className : '',
            hasNav: !!nav,
            navClasses: nav ? nav.className : '',
            hasBrandLogo: !!brand,
            brandDataName: brand ? brand.getAttribute('data-name') : null,
            hasTopMenu: !!topMenu,
            menuItemCount: topMenu ? topMenu.querySelectorAll(':scope > li').length : 0,
            hasCtaBtn: !!ctaBtn,
            ctaText: ctaBtn ? ctaBtn.innerText.trim() : null,
            overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
        };
    });

    console.log('[*] Header Audit Results:');
    console.log(JSON.stringify(headerAudit, null, 2));
    console.log(`[*] Console errors count: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
        console.log('Console Errors:', consoleErrors);
    }

    const artifactPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/live_innoria_header_verified.png';
    await page.screenshot({ path: artifactPath, clip: { x: 0, y: 0, width: 1440, height: 300 } });
    console.log(`[✓] Screenshot saved to ${artifactPath}`);

    await browser.close();
}

auditHeader().catch(err => {
    console.error('Error during audit:', err);
    process.exit(1);
});
