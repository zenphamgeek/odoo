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

function fetchUrl(url, cookie) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = http.request({
      hostname: u.hostname,
      port: u.port,
      path: u.pathname + u.search,
      method: 'GET',
      headers: {
        'Cookie': `session_id=${cookie}`
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, data }));
    });
    req.on('error', reject);
    req.end();
  });
}

async function runTests() {
  console.log('[PLAYWRIGHT TEST] Starting Insilos Icon Verification...');
  const sessionId = await getSessionCookie();
  console.log('✓ Acquired admin session.');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext();
  await context.addCookies([{
    name: 'session_id',
    value: sessionId,
    domain: 'localhost',
    path: '/'
  }]);

  const page = await context.newPage();
  const networkFailures = [];

  page.on('response', response => {
    const url = response.url();
    if (url.includes('/static/description/') && response.status() >= 400) {
      networkFailures.push(`${response.status()} ${url}`);
    }
  });

  // 1. Verify /insilos (Home menu / Launcher)
  console.log('\n--- 1. Testing /insilos (Launcher) ---');
  await page.goto('http://localhost:28069/insilos', { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(4000);

  const homeIcons = await page.evaluate(() => {
    const items = document.querySelectorAll('.o_app, .o_home_menu a, a.o_menuitem');
    return Array.from(items).map(item => {
      const name = item.innerText?.trim();
      const img = item.querySelector('img');
      return { name, src: img?.src };
    }).filter(i => i.src);
  });

  console.log(`Discovered ${homeIcons.length} launcher icons on /insilos.`);
  if (homeIcons.length === 0) throw new Error('No launcher icons discovered on /insilos');

  for (const icon of homeIcons) {
    if (icon.src.startsWith('data:image/svg+xml;base64,')) {
      const b64 = icon.src.replace('data:image/svg+xml;base64,', '');
      const svg = Buffer.from(b64, 'base64').toString('utf-8');
      if (!svg.includes('viewBox="0 0 256 256"')) throw new Error(`Invalid viewBox on ${icon.name}`);
      if (!svg.includes('#0B2E64') && !svg.includes('currentColor')) throw new Error(`Invalid color on ${icon.name}`);
      if (!svg.includes('opacity="0.2"')) throw new Error(`Missing duotone opacity on ${icon.name}`);
    }
  }
  console.log('✓ All launcher icons comply with Insilos signature.');

  // 2. Verify /insilos/settings
  console.log('\n--- 2. Testing /insilos/settings ---');
  await page.goto('http://localhost:28069/insilos/settings', { waitUntil: 'load', timeout: 30000 });
  await page.waitForSelector('.settings_tab .tab', { timeout: 15000 });
  await page.waitForTimeout(2000);

  const settingsIcons = await page.evaluate(() => {
    const tabs = document.querySelectorAll('.settings_tab .tab');
    return Array.from(tabs).map(t => {
      const name = t.querySelector('.app_name')?.innerText?.trim();
      const iconSpan = t.querySelector('.icon');
      const bg = iconSpan ? window.getComputedStyle(iconSpan).backgroundImage : '';
      const match = bg.match(/url\(["']?(https?:\/\/[^"'\)]+)["']?\)/);
      return { name, url: match ? match[1] : null };
    }).filter(i => i.url);
  });

  console.log(`Discovered ${settingsIcons.length} settings tab icons.`);
  if (settingsIcons.length === 0) throw new Error('No settings tab icons discovered');

  let settingsChecked = 0;
  for (const item of settingsIcons) {
    if (!item.url.endsWith('.svg')) {
      throw new Error(`Settings icon for '${item.name}' is not SVG: ${item.url}`);
    }
    const resp = await fetchUrl(item.url, sessionId);
    if (resp.status !== 200) {
      throw new Error(`Failed to fetch settings icon (${resp.status}) for '${item.name}': ${item.url}`);
    }
    const svg = resp.data;
    if (!svg.includes('viewBox="0 0 256 256"')) throw new Error(`Invalid viewBox in settings icon for '${item.name}'`);
    if (!svg.includes('#0B2E64') && !svg.includes('currentColor')) throw new Error(`Invalid color in settings icon for '${item.name}'`);
    if (!svg.includes('opacity="0.2"')) throw new Error(`Missing opacity='0.2' in settings icon for '${item.name}'`);
    settingsChecked++;
  }
  console.log(`✓ All ${settingsChecked} settings icons load canonical SVG with Insilos signature.`);

  // 3. Verify /insilos/apps
  console.log('\n--- 3. Testing /insilos/apps ---');
  await page.goto('http://localhost:28069/insilos/apps', { waitUntil: 'load', timeout: 30000 });
  await page.waitForSelector('.o_modules_kanban, .o_kanban_renderer', { timeout: 15000 });
  await page.waitForTimeout(2000);

  const appCards = await page.evaluate(() => {
    const cards = document.querySelectorAll('.o_modules_kanban .o_kanban_record, .o_modules_kanban article');
    return Array.from(cards).map(c => {
      const title = c.querySelector('h2, main')?.innerText?.trim()?.split('\n')[0];
      const img = c.querySelector('img');
      return { title, src: img?.src };
    }).filter(i => i.src);
  });

  console.log(`Discovered ${appCards.length} app cards in kanban.`);
  if (appCards.length === 0) throw new Error('No app cards discovered in apps kanban');

  let appsChecked = 0;
  for (const card of appCards) {
    if (!card.src.endsWith('.svg')) {
      throw new Error(`App icon for '${card.title}' is not SVG: ${card.src}`);
    }
    const resp = await fetchUrl(card.src, sessionId);
    if (resp.status !== 200) {
      throw new Error(`Failed to fetch app icon (${resp.status}) for '${card.title}': ${card.src}`);
    }
    const svg = resp.data;
    if (!svg.includes('viewBox="0 0 256 256"')) throw new Error(`Invalid viewBox in app icon for '${card.title}'`);
    if (!svg.includes('#0B2E64') && !svg.includes('currentColor')) throw new Error(`Invalid color in app icon for '${card.title}'`);
    if (!svg.includes('opacity="0.2"')) throw new Error(`Missing opacity='0.2' in app icon for '${card.title}'`);
    appsChecked++;
  }
  console.log(`✓ All ${appsChecked} app card icons load canonical SVG with Insilos signature.`);

  // 4. Verify /insilos/apps with Extra / All Modules (facet removed)
  console.log('\n--- 4. Testing /insilos/apps with All Modules (Extra & Fallback) ---');
  const facetRemove = await page.$('.o_searchview_facet .o_facet_remove');
  if (facetRemove) {
    await facetRemove.click();
    await page.waitForTimeout(3000);

    const allCards = await page.evaluate(() => {
      const cards = document.querySelectorAll('.o_modules_kanban .o_kanban_record, .o_modules_kanban article');
      return Array.from(cards).map(c => {
        const title = c.querySelector('h2, main')?.innerText?.trim()?.split('\n')[0];
        const img = c.querySelector('img');
        return { title, src: img?.src };
      }).filter(i => i.src);
    });

    console.log(`Discovered ${allCards.length} module cards with filter removed.`);
    let extraChecked = 0;
    for (const card of allCards.slice(0, 100)) {
      if (!card.src.endsWith('.svg')) {
        throw new Error(`Module icon for '${card.title}' is not SVG: ${card.src}`);
      }
      const resp = await fetchUrl(card.src, sessionId);
      if (resp.status !== 200) {
        throw new Error(`Failed to fetch module icon (${resp.status}) for '${card.title}': ${card.src}`);
      }
      const svg = resp.data;
      if (!svg.includes('viewBox="0 0 256 256"')) throw new Error(`Invalid viewBox in module icon for '${card.title}'`);
      if (!svg.includes('#0B2E64') && !svg.includes('currentColor')) throw new Error(`Invalid color in module icon for '${card.title}'`);
      if (!svg.includes('opacity="0.2"')) throw new Error(`Missing opacity='0.2' in module icon for '${card.title}'`);
      extraChecked++;
    }
    console.log(`✓ Verified ${extraChecked} extra/all module cards load canonical SVG with Insilos signature.`);
  }

  // 5. Verify Module Form View (icon_image binary avatar)
  console.log('\n--- 5. Testing Module Form View (icon_image avatar) ---');
  const baseResp = await fetchUrl('http://localhost:28069/web/image?model=ir.module.module&id=34&field=icon_image', sessionId);
  if (baseResp.status !== 200) {
    throw new Error(`Failed to fetch module form icon_image (${baseResp.status})`);
  }
  const formSvg = baseResp.data;
  if (!formSvg.includes('viewBox="0 0 256 256"') || (!formSvg.includes('#0B2E64') && !formSvg.includes('currentColor')) || !formSvg.includes('opacity="0.2"')) {
    throw new Error('Module form icon_image does not match Insilos SVG signature');
  }
  console.log('✓ Module form view icon_image loads canonical Insilos SVG avatar.');

  if (networkFailures.length > 0) {
    throw new Error(`Encountered ${networkFailures.length} 404/error icon requests: ${networkFailures.join(', ')}`);
  }
  console.log('✓ Zero icon network failures (all HTTP 200).');

  await browser.close();
  console.log('\n[PASS] All Playwright UI Icon tests PASSED 100%!');
}

runTests().catch(err => {
  console.error('\n[FAIL] Test failure:', err.message);
  process.exit(1);
});
