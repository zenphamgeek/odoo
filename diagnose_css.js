const { chromium } = require('playwright');

async function diagnose() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-seuid-sandbox']
  });

  console.log('=== TEST 1: Unauthenticated visit to http://localhost:28069/ ===');
  const context1 = await browser.newContext();
  const page1 = await context1.newPage();
  
  page1.on('console', msg => console.log('CONSOLE [' + msg.type() + ']:', msg.text()));
  page1.on('pageerror', err => console.error('PAGE ERROR:', err.stack || err.message));
  page1.on('requestfailed', req => console.error('REQ FAILED:', req.url(), req.failure()?.errorText));
  page1.on('response', resp => {
    if (resp.status() >= 400) console.error('HTTP ' + resp.status() + ':', resp.url());
  });

  const resp1 = await page1.goto('http://localhost:28069/', { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Final URL 1:', page1.url(), 'Status:', resp1?.status());
  const css1 = await page1.$$eval('link[rel="stylesheet"]', els => els.map(e => e.href));
  console.log('CSS Links on /:', css1);
  const title1 = await page1.title();
  console.log('Page Title 1:', title1);
  const html1 = await page1.content();
  if (html1.includes('Could not get content for') || html1.includes('Style error') || html1.includes('The style compilation failed')) {
    console.error('STYLE COMPILATION ERROR FOUND IN HTML CONTENT!');
    // Print snippet of error
    const match = html1.match(/<pre[^>]*>([\s\S]*?)<\/pre>/);
    if (match) console.error('Error snippet:', match[1]);
  }

  console.log('\n=== TEST 2: Authenticated visit to http://localhost:28069/ ===');
  const context2 = await browser.newContext();
  const page2 = await context2.newPage();
  page2.on('console', msg => console.log('CONSOLE [' + msg.type() + ']:', msg.text()));
  page2.on('pageerror', err => console.error('PAGE ERROR:', err.stack || err.message));
  page2.on('requestfailed', req => console.error('REQ FAILED:', req.url(), req.failure()?.errorText));
  page2.on('response', resp => {
    if (resp.status() >= 400) console.error('HTTP ' + resp.status() + ':', resp.url());
  });

  await page2.request.post('http://localhost:28069/web/session/authenticate', {
    data: {
      jsonrpc: '2.0',
      params: { db: 'odoo20_dev', login: 'admin', password: 'admin' }
    }
  });
  const resp2 = await page2.goto('http://localhost:28069/', { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Final URL 2:', page2.url(), 'Status:', resp2?.status());
  const css2 = await page2.$$eval('link[rel="stylesheet"]', els => els.map(e => e.href));
  console.log('CSS Links on / (logged in):', css2);
  const title2 = await page2.title();
  console.log('Page Title 2:', title2);
  const html2 = await page2.content();
  if (html2.includes('Could not get content for') || html2.includes('Style error') || html2.includes('The style compilation failed')) {
    console.error('STYLE COMPILATION ERROR FOUND IN HTML CONTENT (logged in)!');
    const match = html2.match(/<pre[^>]*>([\s\S]*?)<\/pre>/);
    if (match) console.error('Error snippet:', match[1]);
  }

  await browser.close();
}

diagnose().catch(console.error);
