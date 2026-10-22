/**
 * tools/capture_all_innoria_com_routes.js
 * Multi-route visual crawler & DOM section extractor for innoria.com
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://innoria.com';
const OUTPUT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/audit_innoria_com_routes';

const ROUTES = [
  { route: '/', name: 'homepage' },
  { route: '/about', name: 'about' },
  { route: '/platform', name: 'platform' },
  { route: '/no-code-platform', name: 'no-code-platform' },
  { route: '/blockchain', name: 'blockchain' },
  { route: '/solutions', name: 'solutions' },
  { route: '/industries', name: 'industries' },
  { route: '/contactus', name: 'contactus' }
];

async function main() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 InsilosAuditor/2.0'
  });

  const manifest = {
    crawl_timestamp: new Date().toISOString(),
    base_url: BASE_URL,
    routes: []
  };

  for (const item of ROUTES) {
    const page = await context.newPage();
    const targetUrl = `${BASE_URL}${item.route}`;
    console.log(`[Crawling] ${targetUrl} ...`);

    const routeDir = path.join(OUTPUT_DIR, item.name);
    if (!fs.existsSync(routeDir)) {
      fs.mkdirSync(routeDir, { recursive: true });
    }

    try {
      const response = await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 30000 });
      const status = response ? response.status() : null;

      // Wait a moment for dynamic widgets or webfonts
      await page.waitForTimeout(1500);

      // Take fold screenshot
      const foldPath = path.join(routeDir, 'fold.png');
      await page.screenshot({ path: foldPath, fullPage: false });

      // Take fullpage screenshot
      const fullPath = path.join(routeDir, 'fullpage.png');
      await page.screenshot({ path: fullPath, fullPage: true });

      // Extract section manifest
      const sections = await page.evaluate(() => {
        const results = [];
        const sectionEls = document.querySelectorAll('section');
        sectionEls.forEach((sec, idx) => {
          const rect = sec.getBoundingClientRect();
          const headings = Array.from(sec.querySelectorAll('h1, h2, h3, h4, .section-title, .display')).map(h => h.innerText.trim()).filter(Boolean);
          const eyebrow = sec.querySelector('.eyebrow, .ins-col-eyebrow, .badge')?.innerText?.trim() || '';
          const snippet = sec.getAttribute('data-snippet') || '';
          const name = sec.getAttribute('data-name') || '';
          const id = sec.id || '';
          const classes = sec.className || '';
          const textExcerpt = sec.innerText.slice(0, 300).replace(/\s+/g, ' ').trim();

          results.push({
            index: idx + 1,
            id,
            name,
            snippet,
            classes,
            eyebrow,
            headings: headings.slice(0, 3),
            textExcerpt,
            dimensions: {
              width: Math.round(rect.width),
              height: Math.round(rect.height),
              top: Math.round(rect.top + window.scrollY)
            }
          });
        });
        return results;
      });

      manifest.routes.push({
        name: item.name,
        route: item.route,
        url: targetUrl,
        http_status: status,
        fold_image: foldPath,
        fullpage_image: fullPath,
        section_count: sections.length,
        sections: sections
      });

      console.log(`[Success] ${item.name} (${sections.length} sections captured)`);
    } catch (err) {
      console.error(`[Error] Failed to crawl ${item.name}:`, err.message);
      manifest.routes.push({
        name: item.name,
        route: item.route,
        url: targetUrl,
        error: err.message
      });
    } finally {
      await page.close();
    }
  }

  await browser.close();

  const manifestPath = path.join(OUTPUT_DIR, 'innoria_routes_audit_manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
  console.log(`[Done] Manifest saved to ${manifestPath}`);
}

main().catch(err => {
  console.error('[Fatal Error]', err);
  process.exit(1);
});
