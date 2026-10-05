const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('https://innoria.insilos.com/', { waitUntil: 'networkidle' });
    const cards = await page.$$eval('.innoria-service-card', els => els.map(c => ({
        badge: c.querySelector('.service-badge')?.textContent.trim(),
        title: c.querySelector('h4')?.textContent.trim(),
        imgSrc: c.querySelector('img')?.src,
        imgComplete: c.querySelector('img')?.complete,
        imgNaturalWidth: c.querySelector('img')?.naturalWidth,
        rect: {
            x: c.getBoundingClientRect().x,
            y: c.getBoundingClientRect().y,
            width: c.getBoundingClientRect().width,
            height: c.getBoundingClientRect().height,
        }
    })));
    console.log(JSON.stringify(cards, null, 2));
    await browser.close();
})();
