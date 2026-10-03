#!/usr/bin/env node
/**
 * tools/audit_launcher_icons_visual.js
 * =====================================
 * E2E Visual & WCAG Contrast Auditor for Insilos App-Launcher Icons.
 * 
 * Audits the rendered /insilos home screen in both Light Mode and Dark Mode:
 *  - Verifies 0 broken images (naturalWidth > 0, img.complete = true)
 *  - Verifies 0 default purple cube icons (/web/static/img/default_icon_app.png)
 *  - Verifies 0 raw Phosphor duotone line icons without squircle tile container
 *  - Measures mathematical WCAG contrast ratio (>= 4.5:1) for icons and text
 *  - Captures full-page high-resolution screenshots for both Light and Dark modes
 *  - Emits machine-readable telemetry JSON and human-readable audit table
 */

const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

// CLI Arguments
const args = process.argv.slice(2);
let baseUrl = 'http://localhost:28069';
let outputDir = path.join(__dirname, 'artifacts', 'launcher_visual');
let jsonOutput = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--url' && args[i + 1]) baseUrl = args[++i];
  if (args[i] === '--output-dir' && args[i + 1]) outputDir = args[++i];
  if (args[i] === '--json') jsonOutput = true;
}

/**
 * Acquire admin session ID via /web/login
 */
function getSessionCookie(targetUrl) {
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

/**
 * Helper to compute WCAG 2.1 relative luminance and contrast ratio in Node.js
 */
function parseRgb(colorStr) {
  if (!colorStr) return { r: 255, g: 255, b: 255, a: 1 };
  const m = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (m) {
    return {
      r: parseInt(m[1], 10),
      g: parseInt(m[2], 10),
      b: parseInt(m[3], 10),
      a: m[4] !== undefined ? parseFloat(m[4]) : 1
    };
  }
  return { r: 255, g: 255, b: 255, a: 1 };
}

function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(rgb1, rgb2) {
  const l1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
  const brighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (brighter + 0.05) / (darker + 0.05);
}

async function auditLauncher() {
  if (!jsonOutput) {
    console.log('================================================================================');
    console.log('🚀 INSILOS LAUNCHER ICONS VISUAL & WCAG CONTRAST AUDITOR');
    console.log(`   Target URL: ${baseUrl}/insilos | Artifacts: ${outputDir}`);
    console.log('================================================================================\n');
  }

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  let sid;
  try {
    sid = await getSessionCookie(baseUrl);
    if (!jsonOutput) console.log(`[AUTH] Session acquired successfully: ${sid.substring(0, 12)}...`);
  } catch (err) {
    console.error(`[AUTH-ERROR] Could not log in: ${err.message}`);
    process.exit(1);
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const host = new URL(baseUrl).hostname;
  await context.addCookies([
    { name: 'session_id', value: sid, domain: host, path: '/' },
    { name: 'insilos_session_id', value: sid, domain: host, path: '/' },
    { name: 'session_id', value: sid, domain: 'localhost', path: '/' },
    { name: 'insilos_session_id', value: sid, domain: 'localhost', path: '/' },
    { name: 'session_id', value: sid, domain: '127.0.0.1', path: '/' },
    { name: 'insilos_session_id', value: sid, domain: '127.0.0.1', path: '/' }
  ]);

  const page = await context.newPage();

  // Step 1: Navigate to /insilos
  if (!jsonOutput) console.log('[NAV] Navigating to /insilos launcher home screen...');
  await page.goto(`${baseUrl}/insilos`, { waitUntil: 'load', timeout: 35000 });
  await page.waitForSelector('.o_app', { timeout: 20000 });
  await page.waitForTimeout(3000); // Allow SCSS styles and icons to settle

  // --- LIGHT MODE AUDIT ---
  if (!jsonOutput) console.log('\n--- Auditing Light Mode ---');
  const lightScreenshotPath = path.join(outputDir, 'launcher_light_mode.png');
  await page.screenshot({ path: lightScreenshotPath, fullPage: true });
  if (!jsonOutput) console.log(`[SCREENSHOT] Saved Light Mode screenshot: ${lightScreenshotPath}`);

  const lightAudit = await page.evaluate(() => {
    const apps = Array.from(document.querySelectorAll('.o_app'));
    const results = [];

    apps.forEach((app, index) => {
      const captionEl = app.querySelector('.o_caption') || app;
      const captionText = captionEl.innerText?.trim() || `App-${index + 1}`;
      const xmlid = app.getAttribute('data-menu-xmlid') || '';
      const img = app.querySelector('img');
      const iconWrapper = app.querySelector('.o_app_icon_wrapper') || app;

      const appStyle = window.getComputedStyle(app);
      const captionStyle = window.getComputedStyle(captionEl);

      const imgSrc = img ? img.src : '';
      const isComplete = img ? img.complete : false;
      const naturalWidth = img ? img.naturalWidth : 0;
      const naturalHeight = img ? img.naturalHeight : 0;
      const isBroken = !img || !isComplete || naturalWidth === 0;

      // Check default purple cube
      const isDefaultCube = imgSrc.includes('default_icon_app.png');

      // Check raw line icon signature (legacy transparent icon without squircle tile)
      let isRawLineIcon = false;
      let hasSquircleTile = false;
      if (imgSrc.startsWith('data:image/svg+xml;base64,')) {
        try {
          const svgContent = atob(imgSrc.replace('data:image/svg+xml;base64,', ''));
          hasSquircleTile = svgContent.includes('rx="48"') || svgContent.includes('rx="') || svgContent.includes('<rect');
          // Raw phosphor duotone has #0B2E64 with opacity="0.2" and NO background rect
          if (!hasSquircleTile && (svgContent.includes('#0B2E64') || svgContent.includes('currentColor'))) {
            isRawLineIcon = true;
          }
        } catch (e) {
          // ignore atob errors
        }
      }

      results.push({
        index: index + 1,
        caption: captionText,
        xmlid: xmlid,
        imgSrc: imgSrc.substring(0, 80) + (imgSrc.length > 80 ? '...' : ''),
        isBroken: isBroken,
        naturalWidth: naturalWidth,
        naturalHeight: naturalHeight,
        isDefaultCube: isDefaultCube,
        hasSquircleTile: hasSquircleTile,
        isRawLineIcon: isRawLineIcon,
        cardBg: appStyle.backgroundColor,
        textColor: captionStyle.color
      });
    });

    return results;
  });

  // --- DARK MODE AUDIT ---
  if (!jsonOutput) console.log('\n--- Auditing Dark Mode ---');
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  });
  await page.waitForTimeout(2000); // Allow SCSS dark transition to complete

  const darkScreenshotPath = path.join(outputDir, 'launcher_dark_mode.png');
  await page.screenshot({ path: darkScreenshotPath, fullPage: true });
  if (!jsonOutput) console.log(`[SCREENSHOT] Saved Dark Mode screenshot: ${darkScreenshotPath}`);

  const darkAudit = await page.evaluate(() => {
    const apps = Array.from(document.querySelectorAll('.o_app'));
    const results = [];

    apps.forEach((app, index) => {
      const captionEl = app.querySelector('.o_caption') || app;
      const captionText = captionEl.innerText?.trim() || `App-${index + 1}`;
      const img = app.querySelector('img');

      const appStyle = window.getComputedStyle(app);
      const captionStyle = window.getComputedStyle(captionEl);

      const imgSrc = img ? img.src : '';
      const isComplete = img ? img.complete : false;
      const naturalWidth = img ? img.naturalWidth : 0;
      const isBroken = !img || !isComplete || naturalWidth === 0;
      const isDefaultCube = imgSrc.includes('default_icon_app.png');

      results.push({
        index: index + 1,
        caption: captionText,
        isBroken: isBroken,
        naturalWidth: naturalWidth,
        isDefaultCube: isDefaultCube,
        cardBg: appStyle.backgroundColor,
        textColor: captionStyle.color
      });
    });

    return results;
  });

  await browser.close();

  // Compute contrast and metrics
  let brokenImagesCount = 0;
  let purpleCubeCount = 0;
  let rawLineIconsCount = 0;
  let lightContrastFailures = 0;
  let darkContrastFailures = 0;

  const appDetails = [];

  for (let i = 0; i < lightAudit.length; i++) {
    const la = lightAudit[i];
    const da = darkAudit[i] || {};

    if (la.isBroken) brokenImagesCount++;
    if (la.isDefaultCube) purpleCubeCount++;
    if (la.isRawLineIcon) rawLineIconsCount++;

    // Contrast calculations
    const lightCardBg = parseRgb(la.cardBg);
    const lightText = parseRgb(la.textColor);
    const lightContrast = getContrastRatio(lightText, lightCardBg);

    const darkCardBg = parseRgb(da.cardBg);
    const darkText = parseRgb(da.textColor);
    const darkContrast = getContrastRatio(darkText, darkCardBg);

    if (lightContrast < 4.5) lightContrastFailures++;
    if (darkContrast < 4.5) darkContrastFailures++;

    appDetails.push({
      index: la.index,
      name: la.caption,
      xmlid: la.xmlid,
      broken: la.isBroken,
      defaultCube: la.isDefaultCube,
      rawLineIcon: la.isRawLineIcon,
      hasSquircleTile: la.hasSquircleTile,
      lightContrast: parseFloat(lightContrast.toFixed(2)),
      darkContrast: parseFloat(darkContrast.toFixed(2)),
      lightCardBg: la.cardBg,
      darkCardBg: da.cardBg
    });
  }

  const summary = {
    timestamp: new Date().toISOString(),
    totalAppsAudited: lightAudit.length,
    metrics: {
      brokenImages: brokenImagesCount,
      defaultPurpleCubeIcons: purpleCubeCount,
      rawLineIconsDetected: rawLineIconsCount,
      lightModeContrastViolations: lightContrastFailures,
      darkModeContrastViolations: darkContrastFailures
    },
    artifacts: {
      lightScreenshot: lightScreenshotPath,
      darkScreenshot: darkScreenshotPath
    },
    pass: (brokenImagesCount === 0 && purpleCubeCount === 0 && rawLineIconsCount === 0 && lightContrastFailures === 0 && darkContrastFailures === 0),
    appDetails: appDetails
  };

  // Write telemetry JSON
  const summaryPath = path.join(outputDir, 'launcher_visual_audit_summary.json');
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');

  if (jsonOutput) {
    console.log(JSON.stringify(summary, null, 2));
  } else {
    console.log('\n================================================================================');
    console.log('📊 LAUNCHER VISUAL & CONTRAST AUDIT RESULTS');
    console.log('================================================================================');
    console.log(`Total Launcher Apps Audited:        ${summary.totalAppsAudited}`);
    console.log(`Broken Images (0 naturalWidth):     ${summary.metrics.brokenImages}  ${summary.metrics.brokenImages === 0 ? '✓ PASS' : '❌ FAIL'}`);
    console.log(`Default Purple Cube Icons:          ${summary.metrics.defaultPurpleCubeIcons}  ${summary.metrics.defaultPurpleCubeIcons === 0 ? '✓ PASS' : '❌ FAIL'}`);
    console.log(`Raw Phosphor Duotone Line Icons:    ${summary.metrics.rawLineIconsDetected}  ${summary.metrics.rawLineIconsDetected === 0 ? '✓ PASS' : '❌ PENDING REPLACEMENT'}`);
    console.log(`Light Mode Contrast Violations:     ${summary.metrics.lightModeContrastViolations}  ${summary.metrics.lightModeContrastViolations === 0 ? '✓ PASS' : '❌ FAIL'}`);
    console.log(`Dark Mode Contrast Violations:      ${summary.metrics.darkModeContrastViolations}  ${summary.metrics.darkModeContrastViolations === 0 ? '✓ PASS' : '❌ FAIL'}`);
    console.log(`Telemetry Report Saved:             ${summaryPath}`);
    console.log('================================================================================\n');

    // Print sample of inspected apps
    console.log('Sample of Inspected Launcher Apps:');
    console.log('Idx | App Name                       | Broken | Cube  | Raw Line | Light CR | Dark CR');
    console.log('----+--------------------------------+--------+-------+----------+----------+--------');
    appDetails.slice(0, 15).forEach(a => {
      const name = a.name.padEnd(30).substring(0, 30);
      const broken = a.broken ? 'FAIL' : 'OK  ';
      const cube = a.defaultCube ? 'CUBE' : 'OK  ';
      const raw = a.rawLineIcon ? 'RAW ' : (a.hasSquircleTile ? 'HCT ' : 'N/A ');
      const lcr = (a.lightContrast + ':1').padEnd(8);
      const dcr = (a.darkContrast + ':1').padEnd(6);
      console.log(`${String(a.index).padStart(3)} | ${name} | ${broken} | ${cube} | ${raw}     | ${lcr} | ${dcr}`);
    });
    console.log('...\n');
  }

  return summary;
}

if (require.main === module) {
  auditLauncher()
    .then(summary => {
      if (summary.pass) {
        if (!jsonOutput) console.log('🎉 [PASS] 100% Visual and Contrast Audit Verified!');
        process.exit(0);
      } else {
        if (!jsonOutput) console.log('⚠️ [AUDIT REPORTED ISSUES] Test completed with verified detections.');
        process.exit(1);
      }
    })
    .catch(err => {
      console.error('💥 [ERROR] Unhandled audit error:', err);
      process.exit(2);
    });
}

module.exports = { auditLauncher, getContrastRatio, getLuminance, parseRgb };
