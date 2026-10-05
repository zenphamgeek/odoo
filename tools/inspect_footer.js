const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage();
    await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const cols = await page.evaluate(() => {
        const footer = document.querySelector('.innoria-footer');
        if (!footer) return 'No footer found';
        return Array.from(footer.querySelectorAll('.col-6')).map(col => ({
            html: col.innerHTML.trim().slice(0, 200),
            h6Color: col.querySelector('h6') ? window.getComputedStyle(col.querySelector('h6')).color : null,
            linkColor: col.querySelector('a') ? window.getComputedStyle(col.querySelector('a')).color : null,
            linkDisplay: col.querySelector('a') ? window.getComputedStyle(col.querySelector('a')).display : null,
        }));
    });
    console.log(JSON.stringify(cols, null, 2));
    await browser.close();
})();
