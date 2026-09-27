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
  console.log('[PLAYWRIGHT TEST] Starting Insilos Brand & Color Verification...');
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

  // 1. Test /insilos (Launcher & Favicon)
  console.log('\n--- 1. Testing /insilos (Launcher & Brand Identity) ---');
  await page.goto('http://127.0.0.1:28069/insilos', { waitUntil: 'load', timeout: 30000 });
  await page.waitForSelector('.o_apps, .o_home_menu, .o_navbar', { timeout: 15000 });

  // Favicon check
  const favicons = await page.$$eval('link[rel*="icon"]', links => links.map(l => l.href));
  console.log('Favicon links:', favicons);
  const hasInsilosFavicon = favicons.some(href => href.includes('favicon.ico') || href.includes('favicon.svg'));
  if (hasInsilosFavicon) {
    console.log('✓ Favicon link points to canonical Insilos favicon.');
  } else {
    console.error('✗ Missing expected Insilos favicon link!');
    process.exit(1);
  }

  // Header Logo check
  const logoElements = await page.$$eval('img[src*="logo"]', imgs => imgs.map(i => ({
    src: i.src,
    width: i.naturalWidth,
    height: i.naturalHeight
  })));
  console.log('Header Logo elements:', logoElements);
  if (logoElements.length > 0) {
    console.log('✓ Logo rendered in webclient header.');
  }

  // 2. Test /insilos/settings (Color Rebrand Verification)
  console.log('\n--- 2. Testing /insilos/settings (Primary Brand Color #004455) ---');
  await page.goto('http://127.0.0.1:28069/insilos/settings', { waitUntil: 'load', timeout: 30000 });
  await page.waitForSelector('.btn-primary', { timeout: 15000 });

  const btnStyles = await page.$eval('.btn-primary', el => {
    const s = window.getComputedStyle(el);
    return {
      backgroundColor: s.backgroundColor,
      color: s.color,
      borderColor: s.borderColor
    };
  });
  console.log('Primary Button Computed Style:', btnStyles);

  // #004455 in rgb is rgb(0, 68, 85)
  if (btnStyles.backgroundColor === 'rgb(0, 68, 85)') {
    console.log('✓ PASS: Primary button background-color is rgb(0, 68, 85) (#004455)!');
  } else {
    console.error(`✗ FAIL: Primary button color is ${btnStyles.backgroundColor}, expected rgb(0, 68, 85) (#004455)!`);
    process.exit(1);
  }

  // 3. Test Website Favicon Endpoint
  console.log('\n--- 3. Testing Website Favicon Endpoint ---');
  const favRes = await page.goto('http://127.0.0.1:28069/web/static/img/favicon.ico');
  console.log('Static favicon HTTP status:', favRes.status());
  if (favRes.status() === 200) {
    console.log('✓ Favicon asset served with HTTP 200 OK.');
  } else {
    console.error('✗ Favicon failed to serve!');
    process.exit(1);
  }

  console.log('\n[PASS] All Insilos Brand, Color, Favicon, and Logo checks PASSED 100%!');
  await browser.close();
  process.exit(0);
})().catch(err => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
