const { chromium } = require('playwright');
const { execSync } = require('child_process');

(async () => {
  console.log('='.repeat(80));
  console.log('EMPIRICAL ADVERSARIAL TEST: B2B FORM MALICIOUS PAYLOADS & SANITIZATION');
  console.log('='.repeat(80));

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  let xssTriggered = false;
  page.on('dialog', async dialog => {
    console.log('⚠️ ALERT/DIALOG DETECTED (XSS TRIGGER!):', dialog.message());
    xssTriggered = true;
    await dialog.dismiss();
  });

  const targetUrl = 'http://127.0.0.1:28071/solutions-b2b';
  console.log('Navigating to ' + targetUrl + '...');
  await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 20000 });

  // Adversarial Attack Vector Definitions:
  const sqliName = "' OR '1'='1' UNION SELECT username, password FROM res_users; --";
  const xssPartner = 'Artisan Roastery <script>window.__xss_compromised=true;alert("XSS")</script><img src="x" onerror="window.__xss_img_compromised=true;">';
  const unicodeDiacritics = "Đắk Lắk Cư M'gar Cầu Đất ☕ Cao Nguyên Buôn Ma Thuột 𝒳𝒮𝒮_𝒯𝑒𝓈𝓉";
  const longBufferNotes = 'BOUNDARY_STRESS_'.repeat(300) + ' ' + 'A'.repeat(2500); // ~7300 chars

  console.log('Injecting malicious payloads into B2B form fields...');
  await page.locator('input[name="contact_name"]').fill(sqliName);
  await page.locator('input[name="partner_name"]').fill(xssPartner);
  await page.locator('input[name="phone"]').fill('0909999888');
  await page.locator('input[name="email_from"]').fill('security_audit@innokafe.internal');
  await page.locator('input[name="street"]').fill(unicodeDiacritics);
  await page.locator('textarea[name="description"]').fill(longBufferNotes);

  console.log('Submitting form...');
  const submitBtn = page.locator('form[action*="/solutions-b2b"] button[type="submit"]').first();
  await Promise.all([
    page.waitForURL(url => url.toString().includes('submitted=1'), { timeout: 15000 }),
    submitBtn.click({ force: true })
  ]);

  await page.waitForTimeout(1500);
  const currentUrl = page.url();
  console.log('Redirected URL:', currentUrl);

  // Check if XSS executed in DOM
  const xssGlobal = await page.evaluate(() => window.__xss_compromised || window.__xss_img_compromised);
  console.log('XSS Script Execution Status:', xssGlobal ? '❌ COMPROMISED' : '✅ SECURE (0 XSS Executed)');
  console.log('XSS Dialog Triggered:', xssTriggered ? '❌ COMPROMISED' : '✅ SECURE (0 Dialogs)');

  // Check alert success message in DOM
  const successAlertCount = await page.locator('.alert-success:has-text("Đăng Ký Thành Công")').count();
  console.log('Success Alert Visible:', successAlertCount > 0 ? '✅ YES' : '❌ NO');

  await browser.close();

  // Query Database to verify lead was created and stored safely
  console.log('\nChecking PostgreSQL innokafe_prod for created CRM Lead...');
  const pythonCmd = `python3 -c "
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5434, user='odoo', password='1NN0R1@2026', dbname='innokafe_prod')
cur = conn.cursor()
cur.execute('''SELECT id, name, partner_name, contact_name, email_from, phone, street, LENGTH(description) 
               FROM crm_lead 
               WHERE email_from = 'security_audit@innokafe.internal' 
               ORDER BY id DESC LIMIT 1;''')
row = cur.fetchone()
if row:
    print('  ✅ CRM Lead Found: ID=' + str(row[0]))
    print('  Contact Name:', repr(row[3]))
    print('  Partner Name:', repr(row[2]))
    print('  Street (Unicode):', repr(row[6]))
    print('  Description Length:', row[7])
else:
    print('  ❌ Lead not found!')
conn.close()
"`;

  const dbOutput = execSync(pythonCmd, { encoding: 'utf-8' });
  console.log(dbOutput);

  if (!xssGlobal && !xssTriggered && successAlertCount > 0 && dbOutput.includes('CRM Lead Found')) {
    console.log('='.repeat(80));
    console.log('🏆 B2B MALICIOUS PAYLOAD STRESS TEST: 100% PASSED');
    console.log('='.repeat(80));
    process.exit(0);
  } else {
    console.error('B2B Malicious input test FAILED');
    process.exit(1);
  }
})();
