const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('http://localhost:28069/web/login', { waitUntil: 'domcontentloaded' });
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    console.log('Current URL after login:', page.url());
    
    // Go directly to /odoo
    await page.goto('http://localhost:28069/odoo', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    console.log('URL at /odoo:', page.url());
    
    const appElements = await page.$$('.o_app, a.d-inline-block, .o_home_menu a, .o_apps a');
    console.log('Found app elements count:', appElements.length);
    
    if (appElements.length > 0) {
        const app = appElements[0];
        const data = await app.evaluate(el => {
            const img = el.querySelector('img');
            const caption = el.querySelector('.o_caption, span, div');
            return {
                outerHTML: el.outerHTML,
                rect: el.getBoundingClientRect(),
                cs: {
                    display: window.getComputedStyle(el).display,
                    flexDirection: window.getComputedStyle(el).flexDirection,
                    position: window.getComputedStyle(el).position,
                    height: window.getComputedStyle(el).height,
                    width: window.getComputedStyle(el).width,
                },
                imgRect: img ? img.getBoundingClientRect() : null,
                imgCs: img ? {
                    position: window.getComputedStyle(img).position,
                    display: window.getComputedStyle(img).display,
                    top: window.getComputedStyle(img).top,
                    width: window.getComputedStyle(img).width,
                    height: window.getComputedStyle(img).height,
                } : null,
                captionRect: caption ? caption.getBoundingClientRect() : null,
                captionCs: caption ? {
                    position: window.getComputedStyle(caption).position,
                    display: window.getComputedStyle(caption).display,
                    top: window.getComputedStyle(caption).top,
                    marginTop: window.getComputedStyle(caption).marginTop,
                } : null,
            };
        });
        console.log('App Item Data:\n', JSON.stringify(data, null, 2));
        await app.screenshot({ path: 'tools/artifacts/app_item_debug.png' });
    }
    
    await page.screenshot({ path: 'tools/artifacts/odoo_home_debug.png' });
    await browser.close();
})();
