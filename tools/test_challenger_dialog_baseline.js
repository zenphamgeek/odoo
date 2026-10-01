const { chromium } = require('playwright');

async function checkAssets() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  console.log('Authenticating...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  await page.goto('http://localhost:28069/web', { waitUntil: 'networkidle', timeout: 30000 });

  const styleCheck = await page.evaluate(() => {
    // Check stylesheets for insilos_dialog_restructure rules
    let hasDialogRules = false;
    let sampleRules = [];
    for (const sheet of document.styleSheets) {
      try {
        for (const rule of sheet.cssRules) {
          if (rule.selectorText && (rule.selectorText.includes('modal-header') || rule.selectorText.includes('o_technical_modal'))) {
            hasDialogRules = true;
            sampleRules.push(`${rule.selectorText} { ${rule.style.cssText} }`);
            if (sampleRules.length >= 5) break;
          }
        }
      } catch (e) {
        // Cross-origin stylesheet
      }
      if (sampleRules.length >= 5) break;
    }
    return { hasDialogRules, sampleRules };
  });

  console.log('Style check result:', JSON.stringify(styleCheck, null, 2));
  await browser.close();
}

checkAssets().catch(err => {
  console.error(err);
  process.exit(1);
});
