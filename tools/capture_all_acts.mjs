import { chromium } from 'playwright';
import path from 'path';

const SCREENSHOT_DIR = '/home/zen/.gemini/antigravity/brain/fb5ae76a-1408-4c4b-a022-402bc164561b/screenshots';

async function run() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('http://localhost:28069/', { waitUntil: 'networkidle' });
    await page.waitForSelector('#insilos_hero_showcase');

    const hero = await page.$('#insilos_hero_showcase');

    for (let act = 1; act <= 4; act++) {
        await page.click(`.ins-stepper-tab[data-act="${act}"]`);
        await page.waitForTimeout(1800);
        await hero.screenshot({ path: path.join(SCREENSHOT_DIR, `test_c3_act${act}.png`) });
        console.log(`Captured Act ${act}`);
    }
    await browser.close();
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
