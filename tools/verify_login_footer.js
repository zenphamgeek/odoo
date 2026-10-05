const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('http://localhost:28069/web/login');
  await page.waitForTimeout(2000);

  // Check if link exists
  const linkText = await page.evaluate(() => {
    const el = document.querySelector('a[href*="utm_medium=auth"]');
    return el ? el.textContent.trim() : null;
  });
  console.log('Link found in DOM:', linkText);

  // Screenshot the entire login page
  await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_footer_clean.png' });
  console.log('Saved login_footer_clean.png');

  // Also screenshot specifically the bottom area of the login card
  const card = await page.$('.card, .card-body, form');
  if (card) {
    await card.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/login_card_footer_clean.png' });
    console.log('Saved login_card_footer_clean.png');
  }

  await browser.close();
})();
