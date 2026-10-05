const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('http://localhost:18069/insilos', { waitUntil: 'networkidle' });
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), page.click('button[type="submit"]')]);
    await page.waitForTimeout(2000);
    
    // Toggle dark mode
    await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    });
    await page.waitForTimeout(1000);
    
    let navbar = await page.$('.o_navbar');
    if (navbar) {
        await navbar.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/navbar_home_dark.png' });
    }
    
    // Click meeting rooms
    const apps = await page.$$('.o_app');
    for (const app of apps) {
        const text = await app.innerText();
        if (text.includes('Meeting Rooms')) {
            await app.click();
            break;
        }
    }
    await page.waitForTimeout(3000);
    await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    });
    await page.waitForTimeout(1000);
    
    navbar = await page.$('.o_navbar');
    if (navbar) {
        await navbar.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/navbar_module_dark.png' });
    }
    await browser.close();
    console.log('Dark mode screenshots captured successfully!');
})();
