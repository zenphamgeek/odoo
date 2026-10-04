const { chromium } = require('playwright');

const PROD_URL = 'https://insilos.com';
const SESSION_ID = 'dUSQObL14_9IBFIvt-Xu6oarsBClYQBCVdN58NcHAGU36HBNjXKayZxEcK2OTk2RF_M4bfkykx1ceiLU2ORTTg';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1
  });

  await context.addCookies([
    { name: 'session_id', value: SESSION_ID, domain: 'insilos.com', path: '/' },
    { name: 'insilos_session_id', value: SESSION_ID, domain: 'insilos.com', path: '/' }
  ]);

  const page = await context.newPage();
  console.log('Navigating to https://insilos.com/insilos ...');
  await page.goto('https://insilos.com/insilos', { waitUntil: 'domcontentloaded', timeout: 45000 });
  
  // Wait for apps to load
  await page.waitForSelector('.o_apps', { timeout: 30000 });
  await page.waitForTimeout(3000);

  // Check Expiration Panel
  const expPanel = await page.$('.database_expiration_panel');
  console.log('Production Expiration panel present in Light mode?', !!expPanel);

  // Capture Light Mode
  const lightPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/prod_launcher_live_verified_perfect.png';
  await page.screenshot({ path: lightPath });
  console.log('Saved Light mode screenshot:', lightPath);

  // Switch to Dark Mode
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-color-mode', 'dark');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  });
  await page.waitForTimeout(1500);

  // Capture Dark Mode
  const darkPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/prod_launcher_dark_verified.png';
  await page.screenshot({ path: darkPath });
  console.log('Saved Dark mode screenshot:', darkPath);

  // Analyze pixels of Marketing Automation, Apps, Settings icons in Dark Mode
  const iconAnalysis = await page.evaluate(() => {
    const apps = Array.from(document.querySelectorAll('.o_app'));
    const results = [];
    for (const app of apps) {
      const name = app.querySelector('.o_caption')?.textContent?.trim();
      const img = app.querySelector('img.o_app_icon');
      if (img) {
        results.push({ name, src: img.src });
      }
    }
    return results;
  });
  console.log('Found', iconAnalysis.length, 'rendered launcher apps.');

  await browser.close();
})();
