/**
 * Challenger Adversarial Stress Test: WebClient Header Navbar Layout
 * ==============================================================================
 * Independent empirical stress harness by challenger_navbar_1.
 * Tests:
 * 1. Rapid Continuous Dynamic Resizing (1920 -> 1024 -> 1920 in 50px increments).
 * 2. Extreme Viewports (1024x768 iPad/POS, 1152x864, 1200x800).
 * 3. Bounding-Box Math Verification across all breakpoints.
 * 4. DOM Injection of ultra-long App Brand Title (100 chars) to test clamp robustness.
 * ==============================================================================
 */

const { chromium } = require('playwright');

const BASE_URL = process.env.INSILOS_URL || 'http://localhost:28069';
const DB_NAME = process.env.INSILOS_DB || 'odoo20_dev';
const LOGIN = process.env.INSILOS_LOGIN || 'admin';
const PASSWORD = process.env.INSILOS_PASSWORD || 'admin';

async function main() {
  console.log('=== CHALLENGER ADVERSARIAL STRESS TEST HARNESS ===');
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.0
  });

  const page = await context.newPage();

  console.log('[*] Authenticating admin session...');
  const resp = await page.request.post(`${BASE_URL}/web/session/authenticate`, {
    data: {
      jsonrpc: '2.0',
      params: { db: DB_NAME, login: LOGIN, password: PASSWORD }
    }
  });
  if (!resp.ok()) throw new Error('Auth failed');

  console.log('[+] Navigating to HCM route...');
  await page.goto(`${BASE_URL}/insilos/employees`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForSelector('.o_main_navbar', { timeout: 20000 });
  await page.waitForTimeout(1000);

  // Helper to extract DOM geometry
  async function getGeometry() {
    return await page.evaluate(() => {
      const navbar = document.querySelector('.o_main_navbar');
      const brandWrapper = document.querySelector('.o_menu_brand_wrapper') || document.querySelector('.o_menu_brand');
      const sections = document.querySelector('.o_menu_sections');
      const systray = document.querySelector('.o_menu_systray');
      const moreBtn = document.querySelector('.o_menu_sections_more');

      const navR = navbar ? navbar.getBoundingClientRect() : null;
      const brandR = brandWrapper ? brandWrapper.getBoundingClientRect() : null;
      const secR = sections ? sections.getBoundingClientRect() : null;
      const sysR = systray ? systray.getBoundingClientRect() : null;

      const visibleSecChildren = sections ? Array.from(sections.children).filter(c => {
        const cs = window.getComputedStyle(c);
        const r = c.getBoundingClientRect();
        return cs.display !== 'none' && r.width > 0;
      }).map(c => ({
        text: c.textContent.trim().replace(/\s+/g, ' '),
        rect: c.getBoundingClientRect()
      })) : [];

      const brokenDNone = sections ? Array.from(sections.querySelectorAll('.d-none')).filter(el => {
        const cs = window.getComputedStyle(el);
        return cs.display !== 'none';
      }) : [];

      return {
        navR,
        brandR,
        secR,
        sysR,
        visibleSecChildren,
        brokenDNoneCount: brokenDNone.length,
        navScrollW: navbar ? navbar.scrollWidth : 0,
        navClientW: navbar ? navbar.clientWidth : 0,
        docScrollW: document.documentElement.scrollWidth,
        windowW: window.innerWidth,
        hasMoreBtn: !!moreBtn,
        moreVisible: moreBtn ? (window.getComputedStyle(moreBtn).display !== 'none') : false
      };
    });
  }

  // --- STRESS TEST 1: Rapid Continuous Dynamic Resizing ---
  console.log('\n[TEST 1] Rapid Continuous Dynamic Resizing (1920 -> 1024 -> 1920)...');
  const widths = [1920, 1750, 1600, 1440, 1366, 1280, 1200, 1152, 1100, 1024, 1100, 1280, 1440, 1920];
  let resizeViolations = 0;

  for (const w of widths) {
    await page.setViewportSize({ width: w, height: 800 });
    // Rapid resize: give 150ms for debounce
    await page.waitForTimeout(150);
    const geom = await getGeometry();

    // Check collision
    const brandToSec = (geom.brandR && geom.secR) ? (geom.brandR.right - geom.secR.left) : 0;
    const secToSys = (geom.secR && geom.sysR) ? (geom.secR.right - geom.sysR.left) : 0;
    const sysRightOver = (geom.sysR) ? (geom.sysR.right - w) : 0;
    const navOverflow = geom.navScrollW - geom.navClientW;

    if (brandToSec > 1.0 || secToSys > 1.0 || sysRightOver > 1.0 || navOverflow > 1.0 || geom.brokenDNoneCount > 0) {
      console.error(`  FAIL at width ${w}px: brandToSec=${brandToSec.toFixed(1)}, secToSys=${secToSys.toFixed(1)}, sysRightOver=${sysRightOver.toFixed(1)}, navOverflow=${navOverflow}, brokenDNone=${geom.brokenDNoneCount}`);
      resizeViolations++;
    } else {
      process.stdout.write(`  [PASS ${w}px: brandW=${geom.brandR ? geom.brandR.width.toFixed(0) : 0}px, visSec=${geom.visibleSecChildren.length}, more=${geom.moreVisible}] `);
    }
  }
  console.log(`\nResize stress test finished: ${resizeViolations === 0 ? 'ALL PASSED' : `${resizeViolations} VIOLATIONS`}`);

  // --- STRESS TEST 2: Compact Viewport Boundaries (1024x768, 1152x864) ---
  console.log('\n[TEST 2] Compact Boundary Viewports (1024x768 & 1152x864)...');
  for (const [vw, vh] of [[1024, 768], [1152, 864]]) {
    await page.setViewportSize({ width: vw, height: vh });
    await page.waitForTimeout(300);
    const geom = await getGeometry();

    const brandToSec = (geom.brandR && geom.secR) ? (geom.brandR.right - geom.secR.left) : 0;
    const secToSys = (geom.secR && geom.sysR) ? (geom.secR.right - geom.sysR.left) : 0;
    const sysRightOver = (geom.sysR) ? (geom.sysR.right - vw) : 0;
    const navOverflow = geom.navScrollW - geom.navClientW;

    console.log(`  Viewport ${vw}x${vh}: BrandWidth=${geom.brandR ? geom.brandR.width.toFixed(1) : 0}px, VisibleSections=${geom.visibleSecChildren.length}, MoreVisible=${geom.moreVisible}, SecRight=${geom.secR ? geom.secR.right.toFixed(1) : 0}px, SysLeft=${geom.sysR ? geom.sysR.left.toFixed(1) : 0}px`);

    if (brandToSec > 1.0 || secToSys > 1.0 || sysRightOver > 1.0 || navOverflow > 1.0) {
      console.error(`  FAIL at ${vw}x${vh}!`);
      resizeViolations++;
    } else {
      console.log(`  PASS at ${vw}x${vh}: Zero collision, zero overflow.`);
    }
  }

  // --- STRESS TEST 3: Extreme App Title Injection ---
  console.log('\n[TEST 3] Extreme App Title Injection (100 characters)...');
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.evaluate(() => {
    const brand = document.querySelector('.o_menu_brand');
    if (brand) {
      brand.textContent = 'Ultra Long Strategic Enterprise Resource Planning & Human Capital Excellence Suite (SAP/Insilos Mega Platform Edition)';
    }
    // Trigger adapt
    window.dispatchEvent(new Event('resize'));
  });
  await page.waitForTimeout(300);
  const geomExtreme = await getGeometry();
  console.log(`  Extreme Title Brand Width: ${geomExtreme.brandR ? geomExtreme.brandR.width.toFixed(1) : 0}px (CSS Clamp max: 260px)`);
  const brandClamped = geomExtreme.brandR && geomExtreme.brandR.width <= 261;
  const extremeSecToSys = (geomExtreme.secR && geomExtreme.sysR) ? (geomExtreme.secR.right - geomExtreme.sysR.left) : 0;
  console.log(`  Brand Clamped <= 260px: ${brandClamped ? 'YES' : 'NO'}`);
  console.log(`  Sections to Systray Overlap: ${extremeSecToSys.toFixed(1)}px`);
  if (!brandClamped || extremeSecToSys > 1.0) {
    console.error('  FAIL on extreme title clamping!');
    resizeViolations++;
  } else {
    console.log('  PASS on extreme title clamping: CSS clamp prevents expansion, zero collision preserved.');
  }

  await browser.close();
  console.log('\n==================================================');
  if (resizeViolations === 0) {
    console.log('ALL ADVERSARIAL STRESS TESTS PASSED CLEANLY (0 FAILS)');
    process.exit(0);
  } else {
    console.error(`ADVERSARIAL STRESS TESTS FAILED: ${resizeViolations} failures`);
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Stress test exception:', err);
  process.exit(1);
});
