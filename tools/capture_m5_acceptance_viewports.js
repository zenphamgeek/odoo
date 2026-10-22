#!/usr/bin/env node
/**
 * InnoKafe M5 Final Acceptance Multi-Viewport Evidence Capturer
 * Captures pristine full-page visual evidence of Desktop (1440x900), Tablet (768x1024),
 * and Mobile (375x812) on https://innokafe.insilos.com/
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/m5_final_acceptance';
const TARGET_URL = 'https://innokafe.insilos.com/';

const VIEWPORTS = [
  {
    name: 'desktop',
    label: 'Desktop HD',
    width: 1440,
    height: 900,
    isMobile: false,
    hasTouch: false,
    deviceScaleFactor: 1,
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
  },
  {
    name: 'tablet',
    label: 'Tablet Portrait (iPad Mini/Air)',
    width: 768,
    height: 1024,
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
  },
  {
    name: 'mobile',
    label: 'Mobile iPhone (375x812)',
    width: 375,
    height: 812,
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 3,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
  }
];

async function capture() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  console.log('================================================================');
  console.log(`📸 Capturing M5 Responsive Evidence from ${TARGET_URL}`);
  console.log(`📂 Output Directory: ${OUTPUT_DIR}`);
  console.log('================================================================');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const manifest = {
    targetUrl: TARGET_URL,
    timestamp: new Date().toISOString(),
    viewports: {}
  };

  for (const vp of VIEWPORTS) {
    console.log(`\n[*] Capturing Viewport: ${vp.label} (${vp.width}x${vp.height})...`);
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.deviceScaleFactor,
      isMobile: vp.isMobile,
      hasTouch: vp.hasTouch,
      userAgent: vp.userAgent,
      locale: 'vi-VN',
      extraHTTPHeaders: {
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
      }
    });

    const page = await context.newPage();
    const consoleLogs = [];
    page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));

    const response = await page.goto(TARGET_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 45000
    });

    // Wait for network idle or settle
    await page.waitForLoadState('load', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(3500);

    const status = response ? response.status() : null;
    const title = await page.title();
    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      return {
        clientWidth: doc.clientWidth,
        clientHeight: doc.clientHeight,
        scrollWidth: doc.scrollWidth,
        scrollHeight: doc.scrollHeight,
        hasHorizontalOverflow: doc.scrollWidth > doc.clientWidth + 2
      };
    });

    console.log(`  [✓] HTTP Status: ${status}`);
    console.log(`  [✓] Title: "${title}"`);
    console.log(`  [✓] Dimensions: client=${metrics.clientWidth}x${metrics.clientHeight}, scroll=${metrics.scrollWidth}x${metrics.scrollHeight}, overflow=${metrics.hasHorizontalOverflow}`);

    // Fullpage screenshot
    const fullpageFilename = `innokafe_${vp.name}_${vp.width}x${vp.height}_fullpage.png`;
    const fullpagePath = path.join(OUTPUT_DIR, fullpageFilename);
    await page.screenshot({ path: fullpagePath, fullPage: true });
    const fullpageStat = fs.statSync(fullpagePath);
    console.log(`  [✓] Saved Fullpage Screenshot: ${fullpageFilename} (${fullpageStat.size} bytes)`);

    // Above-the-fold Hero screenshot
    const heroFilename = `innokafe_${vp.name}_${vp.width}x${vp.height}_hero.png`;
    const heroPath = path.join(OUTPUT_DIR, heroFilename);
    await page.screenshot({ path: heroPath, fullPage: false });
    const heroStat = fs.statSync(heroPath);
    console.log(`  [✓] Saved Hero Screenshot: ${heroFilename} (${heroStat.size} bytes)`);

    manifest.viewports[vp.name] = {
      label: vp.label,
      width: vp.width,
      height: vp.height,
      httpStatus: status,
      title: title,
      metrics: metrics,
      fullpageScreenshot: fullpageFilename,
      fullpageSizeBytes: fullpageStat.size,
      heroScreenshot: heroFilename,
      heroSizeBytes: heroStat.size
    };

    await context.close();
  }

  await browser.close();

  const manifestPath = path.join(OUTPUT_DIR, 'm5_viewports_manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
  console.log(`\n[✓] Manifest generated: ${manifestPath}`);
  console.log('================================================================');
  console.log('🎉 ALL 3 VIEWPORT EVIDENCE SCREENSHOTS SUCCESSFULLY CAPTURED!');
  console.log('================================================================');
}

capture().catch(err => {
  console.error('Fatal capture error:', err);
  process.exit(1);
});
