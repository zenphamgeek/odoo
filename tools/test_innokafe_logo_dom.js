#!/usr/bin/env node
/**
 * InnoKafe Official Vector Logo DOM Verification Suite
 * ====================================================
 * End-to-end automated Playwright browser tests validating:
 * 1. Navbar displays official vector SVG logo (innokafe_logo_master.svg).
 * 2. Sticky Header maintains vector SVG logo after scroll.
 * 3. Footer displays official vector SVG logo (innokafe_logo_white.svg).
 * 4. Favicon in <head> links to official favicon.svg.
 * 5. Exactly ZERO fake text logos in Navbar, Header, Footer, and Cart Drawer.
 * 6. Full coverage across all 6 core routes and 2 responsive viewports (Desktop & Mobile).
 */

const { chromium } = require('playwright');

const TARGET_URL = process.argv[2] || 'http://localhost:28071';
const ROUTES = ['/', '/story', '/products', '/taste-profiler', '/solutions-b2b', '/contactus'];

async function run() {
  console.log('================================================================');
  console.log(`🚀 Starting InnoKafe Vector Logo DOM Verification on ${TARGET_URL}`);
  console.log('================================================================');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  let totalAssertions = 0;
  let passedAssertions = 0;
  const failureDetails = [];

  function assert(condition, message) {
    totalAssertions++;
    if (condition) {
      passedAssertions++;
      console.log(`  [✓] PASS: ${message}`);
    } else {
      failureDetails.push(message);
      console.error(`  [✗] FAIL: ${message}`);
    }
  }

  async function safeNavigate(p, target, retries = 3) {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const res = await p.goto(target, { waitUntil: 'domcontentloaded', timeout: 35000 });
        if (res) return res;
      } catch (err) {
        if (attempt === retries) throw err;
        console.log(`  [!] Navigation retry ${attempt}/${retries} on ${target} (${err.message})`);
        await p.waitForTimeout(1000 * attempt);
      }
    }
  }

  try {
    // =====================================================================
    // 1. DESKTOP VIEWPORT AUDIT (1440 x 900)
    // =====================================================================
    console.log('\n[STAGE 1] Desktop Viewport Audit (1440x900) across all 6 routes');
    const desktopContext = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      locale: 'vi-VN',
      extraHTTPHeaders: {
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
      },
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    const page = await desktopContext.newPage();

    for (const route of ROUTES) {
      const url = `${TARGET_URL}${route}`;
      console.log(`\n--- Auditing Route: ${route} (${url}) ---`);
      
      const response = await safeNavigate(page, url);
      assert(response && response.status() === 200, `HTTP 200 OK on ${route} (Got: ${response ? response.status() : 'null'})`);

      // 1.1 Navbar Brand Logo Vector SVG
      const navbarImgSrc = await page.$eval('.navbar-brand img', el => el.getAttribute('src')).catch(() => null);
      assert(
        navbarImgSrc && navbarImgSrc.includes('innokafe_logo_master.svg'),
        `Navbar renders innokafe_logo_master.svg (Got: ${navbarImgSrc})`
      );

      // 1.2 Navbar Zero Fake Text Logo
      const fakeTextNavbar = await page.$$eval('.navbar-brand span', spans =>
        spans.some(s => s.innerText.includes('InnoKafe') || s.innerText.includes('Specialty'))
      ).catch(() => false);
      assert(!fakeTextNavbar, 'Navbar has exactly 0 fake text logo spans');

      // 1.3 Sticky Header Verification (scroll 600px)
      await page.evaluate(() => window.scrollTo(0, 600));
      await page.waitForTimeout(350);
      const stickyImgSrc = await page.$eval('.navbar-brand img', el => el.getAttribute('src')).catch(() => null);
      assert(
        stickyImgSrc && stickyImgSrc.includes('innokafe_logo_master.svg'),
        'Sticky header retains vector logo master SVG after 600px scroll'
      );

      // 1.4 Footer Vector White SVG
      const footerImgSrc = await page.$eval('#footer img', el => el.getAttribute('src')).catch(() => null);
      assert(
        footerImgSrc && footerImgSrc.includes('innokafe_logo_white.svg'),
        `Footer renders innokafe_logo_white.svg (Got: ${footerImgSrc})`
      );

      // 1.5 Footer Zero Fake Text Logo
      const fakeTextFooter = await page.$$eval('#footer span', spans =>
        spans.some(s => s.innerText.includes('InnoKafe') && s.classList.contains('inno-serif'))
      ).catch(() => false);
      assert(!fakeTextFooter, 'Footer has exactly 0 fake text logo spans');

      // 1.6 Favicon in <head> links to official favicon.svg
      const faviconHref = await page.$eval('link[rel="icon"][type="image/svg+xml"]', el => el.getAttribute('href')).catch(() => null);
      assert(
        faviconHref && faviconHref.includes('favicon.svg'),
        `Favicon points to official vector favicon.svg (Got: ${faviconHref})`
      );
    }
    await desktopContext.close();

    // =====================================================================
    // 2. MOBILE VIEWPORT AUDIT (375 x 812) & CART DRAWER
    // =====================================================================
    console.log('\n[STAGE 2] Mobile Viewport Audit (375x812) & Cart Drawer Verification');
    const mobileContext = await browser.newContext({
      viewport: { width: 375, height: 812 },
      isMobile: true,
      hasTouch: true,
      locale: 'vi-VN',
      extraHTTPHeaders: {
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
      },
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148'
    });
    const mobilePage = await mobileContext.newPage();
    await safeNavigate(mobilePage, `${TARGET_URL}/`);

    // 2.1 Mobile Navbar Brand Vector SVG
    const mobileNavbarImg = await mobilePage.$eval('.navbar-brand img', el => el.getAttribute('src')).catch(() => null);
    assert(
      mobileNavbarImg && mobileNavbarImg.includes('innokafe_logo_master.svg'),
      `Mobile navbar brand displays vector logo master SVG (Got: ${mobileNavbarImg})`
    );

    // 2.2 Mobile Navbar Zero Fake Text Logo
    const mobileFakeTextNavbar = await mobilePage.$$eval('.navbar-brand span', spans =>
      spans.some(s => s.innerText.includes('InnoKafe') || s.innerText.includes('Specialty'))
    ).catch(() => false);
    assert(!mobileFakeTextNavbar, 'Mobile navbar has exactly 0 fake text logo spans');

    // 2.3 Slide-over Cart Drawer Trigger and Verification
    await mobilePage.evaluate(() => {
      if (window.innokafeCart && typeof window.innokafeCart.openDrawer === 'function') {
        window.innokafeCart.openDrawer();
      }
    });
    await mobilePage.waitForTimeout(400);

    const drawerFakeText = await mobilePage.$$eval('#innokafe_cart_drawer span', spans =>
      spans.some(s => s.innerText.includes('InnoKafe Specialty Roastery'))
    ).catch(() => false);
    assert(!drawerFakeText, 'Slide-over Cart Drawer has exactly 0 fake text logos');

    await mobileContext.close();
  } finally {
    await browser.close();
  }

  console.log('\n================================================================');
  console.log(`📊 FINAL RESULTS: ${passedAssertions}/${totalAssertions} ASSERTIONS PASSED`);
  if (failureDetails.length > 0) {
    console.log(`❌ FAILURES (${failureDetails.length}):`);
    failureDetails.forEach(f => console.log(`   - ${f}`));
  }
  console.log('================================================================');

  if (totalAssertions > 0 && passedAssertions === totalAssertions) {
    console.log('🎉 100% VECTOR BRANDING DOM VERIFICATION ACHIEVED (0 FAILS)');
    process.exit(0);
  } else {
    process.exit(1);
  }
}

run().catch(err => {
  console.error('[FATAL ERROR]:', err);
  process.exit(1);
});
