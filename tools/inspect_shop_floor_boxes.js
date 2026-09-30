const { chromium } = require('playwright');
const http = require('http');

function getSessionCookie() {
  return new Promise((resolve) => {
    http.get('http://127.0.0.1:28069/web/login', (res) => {
      let data = '';
      const setCookies = res.headers['set-cookie'] || [];
      const initCookie = setCookies.map(c => c.split(';')[0]).join('; ');
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const match = data.match(/name="csrf_token" value="([^"]+)"/);
        const csrf = match[1];
        const postData = 'login=admin&password=admin&csrf_token=' + csrf + '&redirect=/insilos/shop-floor';
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
          const sessionMatch = authCookies.join('; ').match(/(session_id|insilos_session_id)=([^;]+)/);
          resolve(sessionMatch[2]);
        });
        postReq.write(postData);
        postReq.end();
      });
    });
  });
}

(async () => {
  const sid = await getSessionCookie();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  await context.addCookies([
    { name: 'session_id', value: sid, domain: 'localhost', path: '/' },
    { name: 'insilos_session_id', value: sid, domain: 'localhost', path: '/' }
  ]);
  const page = await context.newPage();
  await page.goto('http://localhost:28069/insilos/shop-floor', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  
  const img = await page.$('img[src*="op_sidebar"]');
  console.log('Image element found:', !!img);
  if (img) {
    console.log('Image box:', await img.boundingBox());
  }
  for (let i = 1; i <= 5; i++) {
    const ann = await page.$('.o_annotation_' + i);
    console.log(`Annotation ${i} box:`, await ann?.boundingBox());
  }
  await browser.close();
})();
