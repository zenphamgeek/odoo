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
  console.log('Navigating to https://insilos.com/odoo/discuss ...');
  await page.goto('https://insilos.com/odoo/discuss', { waitUntil: 'domcontentloaded', timeout: 45000 });
  
  await page.waitForSelector('.o-mail-Discuss', { timeout: 20000 });
  await page.waitForTimeout(2000);

  // Click on the conversation item for InsilosBot
  const botConv = await page.locator('text=InsilosBot').first();
  if (botConv) {
    console.log('Found InsilosBot conversation, clicking...');
    await botConv.click();
    await page.waitForTimeout(2000);
  }

  // Find composer textarea
  const textarea = await page.$('.o-mail-Composer textarea.o-mail-Composer-input');
  if (textarea) {
    console.log('Focusing composer textarea and typing test message...');
    await textarea.focus();
    await page.waitForTimeout(500);
    await textarea.type('Hello InsilosBot! Testing the new Flat SVG avatar and capsule focus ring.');
    await page.waitForTimeout(1000);
  } else {
    console.log('Composer textarea not found in current view.');
  }

  // Light Mode Screenshot
  const lightPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/prod_discuss_verified_light.png';
  await page.screenshot({ path: lightPath });
  console.log('Saved Light mode screenshot:', lightPath);

  // Switch to Dark Mode
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-color-mode', 'dark');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  });
  await page.waitForTimeout(1500);

  // Re-focus composer in dark mode
  if (textarea) {
    await textarea.focus();
    await page.waitForTimeout(500);
  }

  // Dark Mode Screenshot
  const darkPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/prod_discuss_verified_dark.png';
  await page.screenshot({ path: darkPath });
  console.log('Saved Dark mode screenshot:', darkPath);

  await browser.close();
})();
