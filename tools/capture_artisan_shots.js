const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  
  await page.goto('http://localhost:28071/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  
  await page.screenshot({ path: '/home/zen/O20/artifacts/innokafe_e2e/home_full_artisan.png', fullPage: true });
  
  const hero = await page.$('.inno-artisan-hero');
  if (hero) {
    await hero.screenshot({ path: '/home/zen/O20/artifacts/innokafe_e2e/home_hero_artisan.png' });
  }

  const passportSection = await page.$('#specialty_beans');
  if (passportSection) {
    await passportSection.screenshot({ path: '/home/zen/O20/artifacts/innokafe_e2e/home_passport_section.png' });
  }

  const roastLab = await page.$('.inno-roast-lab');
  if (roastLab) {
    await roastLab.screenshot({ path: '/home/zen/O20/artifacts/innokafe_e2e/home_roast_lab.png' });
  }

  await browser.close();
  console.log('Screenshots captured successfully!');
})();
