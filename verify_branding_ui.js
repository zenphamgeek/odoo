const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  console.log('Authenticating...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  console.log('Visiting Home App Drawer (/odoo)...');
  await page.goto('http://localhost:28069/odoo', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Check title
  const title = await page.title();
  console.log('Document title:', title);

  // 2. Check App Drawer Icons
  const appIcons = await page.$$eval('.o_app', els =>
    els.slice(0, 10).map(e => {
      const img = e.querySelector('img');
      return {
        name: e.innerText.trim().split('\n')[0],
        imgSrc: img ? img.getAttribute('src').slice(0, 60) : 'no img'
      };
    })
  );
  console.log('Sample App drawer icons:');
  for (const app of appIcons) {
    console.log(`  - ${app.name.padEnd(20)}: ${app.imgSrc}`);
  }

  // 3. Check Contacts ListView for Create button
  console.log('\nNavigating to Contacts (/odoo/contacts)...');
  await page.goto('http://localhost:28069/odoo/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  const createBtn = await page.$('.o_list_button_add, .o-kanban-button-new');
  if (createBtn) {
    const btnText = (await createBtn.innerText()).trim();
    console.log(`Create Button in Contacts view: text = "${btnText}"`);
  } else {
    console.log('Button not found directly in view');
  }

  // 4. Check CRM for Create button
  console.log('\nNavigating to CRM (/odoo/crm)...');
  await page.goto('http://localhost:28069/odoo/crm', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  const crmCreateBtn = await page.$('.o-kanban-button-new, .o_list_button_add');
  if (crmCreateBtn) {
    const btnText = (await crmCreateBtn.innerText()).trim();
    console.log(`Create Button in CRM view: text = "${btnText}"`);
  }

  await browser.close();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
