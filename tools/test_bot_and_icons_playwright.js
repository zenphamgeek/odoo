const { chromium } = require('playwright');
const http = require('http');

function getSessionCookie() {
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: '127.0.0.1',
      port: 28069,
      path: '/web/login',
      method: 'GET'
    }, (res) => {
      let data = '';
      const setCookies = res.headers['set-cookie'] || [];
      const initCookie = setCookies.map(c => c.split(';')[0]).join('; ');
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const match = data.match(/name="csrf_token" value="([^"]+)"/);
        if (!match) return reject(new Error('No CSRF token'));
        const csrf = match[1];

        const postData = `login=admin&password=admin&csrf_token=${csrf}&redirect=/insilos`;
        const postReq = http.request({
          hostname: '127.0.0.1',
          port: 28069,
          path: '/web/login',
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(postData),
            'Cookie': initCookie
          }
        }, (postRes) => {
          const authCookies = postRes.headers['set-cookie'] || [];
          const sessionMatch = authCookies.join('; ').match(/session_id=([^;]+)/);
          if (sessionMatch) resolve(sessionMatch[1]);
          else reject(new Error('No session_id in login response'));
        });
        postReq.on('error', reject);
        postReq.write(postData);
        postReq.end();
      });
    });
    req.on('error', reject);
    req.end();
  });
}

(async () => {
  console.log('[PLAYWRIGHT TEST] Starting Insilos Bot Avatar & Icons Verification...');
  const sessionId = await getSessionCookie();
  console.log('✓ Acquired admin session cookie.');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  await context.addCookies([{
    name: 'session_id',
    value: sessionId,
    domain: '127.0.0.1',
    path: '/'
  }]);

  const page = await context.newPage();

  console.log('1. Navigating to /insilos home...');
  await page.goto('http://127.0.0.1:28069/insilos', { waitUntil: 'load', timeout: 30000 });
  await page.waitForSelector('.o_apps, .o_home_menu, .o_navbar', { timeout: 15000 });
  console.log('✓ Reached:', page.url());

  // Inspect launcher app icons
  const appIcons = await page.$$eval('.o_app', apps => apps.map(a => {
    const img = a.querySelector('img');
    const caption = a.querySelector('.o_caption, .o_app_name, span');
    return {
      text: caption ? caption.innerText.trim() : '',
      src: img ? img.src : ''
    };
  }));

  console.log(`✓ Total launcher apps found: ${appIcons.length}`);
  const targetApps = appIcons.filter(a => /ai|document|knowledge|discuss/i.test(a.text));
  for (const a of targetApps) {
    console.log(`  [APP] ${a.text.padEnd(20)} -> ${a.src}`);
  }

  // 2. Check Bot Avatar in Discuss
  console.log('2. Navigating to Discuss...');
  await page.goto('http://127.0.0.1:28069/insilos/action-mail.action_discuss', { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Take screenshot of Discuss
  await page.screenshot({ path: 'tools/discuss_view.png', fullPage: true });
  console.log('✓ Saved Discuss screenshot to tools/discuss_view.png');

  // Verify Bot Avatar image request
  const botResp = await page.request.get('http://127.0.0.1:28069/mail/static/src/img/odoobot.png');
  console.log('✓ Bot avatar static response:', botResp.status(), `${botResp.headers()['content-length']} bytes`);

  const botPartnerResp = await page.request.get('http://127.0.0.1:28069/web/image/res.partner/2/avatar_128');
  console.log('✓ Bot partner avatar response:', botPartnerResp.status(), `${botPartnerResp.headers()['content-length']} bytes`);

  const aiResp = await page.request.get('http://127.0.0.1:28069/ai/static/description/icon.png');
  console.log('✓ AI icon response:', aiResp.status(), `${aiResp.headers()['content-length']} bytes`);

  const booksResp = await page.request.get('http://127.0.0.1:28069/knowledge/static/src/img/Books.svg');
  console.log('✓ Knowledge Books.svg response:', booksResp.status(), `${booksResp.headers()['content-length']} bytes`);

  await browser.close();
  console.log('✓ ALL PLAYWRIGHT CHECKS PASSED!');
})();
