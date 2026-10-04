const { chromium } = require('playwright');
const http = require('http');

function getSession(targetUrl) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(targetUrl);
    http.get(`${targetUrl}/web/login`, (res) => {
      let data = '';
      const setCookies = res.headers['set-cookie'] || [];
      const initCookie = setCookies.map(c => c.split(';')[0]).join('; ');
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const match = data.match(/name="csrf_token" value="([^"]+)"/);
        if (!match) return reject(new Error('No CSRF token found in /web/login'));
        const csrf = match[1];
        const postData = `login=admin&password=admin&csrf_token=${csrf}&redirect=/insilos`;
        const postReq = http.request({
          hostname: parsed.hostname,
          port: parsed.port || 80,
          path: '/web/login',
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(postData),
            'Cookie': initCookie
          }
        }, (postRes) => {
          const authCookies = postRes.headers['set-cookie'] || [];
          const sessionMatch = authCookies.join('; ').match(/(session_id|insilos_session_id)=([^;]+)/);
          if (sessionMatch) resolve(sessionMatch[2]);
          else reject(new Error('No session ID in login response'));
        });
        postReq.on('error', reject);
        postReq.write(postData);
        postReq.end();
      });
    }).on('error', reject);
  });
}

(async () => {
  const sessionId = await getSession('http://localhost:28069');
  console.log('Session acquired:', sessionId);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1
  });

  await context.addCookies([
    { name: 'session_id', value: sessionId, domain: 'localhost', path: '/' },
    { name: 'insilos_session_id', value: sessionId, domain: 'localhost', path: '/' }
  ]);

  const page = await context.newPage();
  await page.goto('http://localhost:28069/insilos', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.o_apps', { timeout: 30000 });
  await page.waitForTimeout(2000);

  // Capture Light Mode
  const lightPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/local_launcher_live_verified.png';
  await page.screenshot({ path: lightPath, fullPage: false });
  console.log('Saved Light mode screenshot:', lightPath);

  // Check Expiration Panel presence
  const expPanel = await page.$('.database_expiration_panel');
  console.log('Expiration panel present in Light mode?', !!expPanel);

  // Check Field Command Bar presence
  const cmdBar = await page.$('.ins_field_command_bar');
  console.log('Executive Field Command bar present?', !!cmdBar);

  // Switch to Dark Mode
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-color-mode', 'dark');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  });
  await page.waitForTimeout(1000);

  const darkPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/local_launcher_dark_verified.png';
  await page.screenshot({ path: darkPath, fullPage: false });
  console.log('Saved Dark mode screenshot:', darkPath);

  await browser.close();
})();
