/**
 * Automated Layout Collision Audit Suite
 * ==============================================================================
 * Headless Playwright test suite validating zero-tolerance layout integrity
 * across the WebClient Header Navigation Bar (web.NavBar / EnterpriseNavBar).
 *
 * Test Matrix:
 * - 4 Standard Enterprise Viewports: 1280x800, 1366x768, 1440x900, 1920x1080
 * - 6 Target Applications: HCM, SD, FI/CO, Logistics IDP, Capital Markets, SAP PM
 * Total: 24 test passes.
 *
 * Zero-Tolerance Assertions:
 * 1. 0px Bounding-Box Collision: Brand right <= Sections left, Sections right <= Systray left,
 *    every visible child right <= Systray left, every .d-none element computes to display: none.
 * 2. 0px Line Wrap (No 2nd Line): All direct section layout containers share identical top offset
 *    (delta <= 1px), no child wrapped to line 2 (top < navRect.bottom), container height strictly 46px-50px.
 * 3. Zero Horizontal Scroll: navbar.scrollWidth <= navbar.clientWidth, doc.scrollWidth <= window.innerWidth.
 * 4. Systray Intact & Right-Aligned: systray.right <= viewport.width, flex display,
 *    company switcher, AI assistant, user menu visible.
 * 5. More Dropdown Parity: When sections overflow, .o_menu_sections_more is present,
 *    clicking opens popover dropdown, hidden sections exist inside the menu.
 *
 * Visual Artifacts:
 * - artifacts/hcm_menu_verified_<viewport>.png
 * ==============================================================================
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = path.join(__dirname, '..', 'artifacts');
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const BASE_URL = process.env.INSILOS_URL || 'http://localhost:28069';
const DB_NAME = process.env.INSILOS_DB || 'odoo20_dev';
const LOGIN = process.env.INSILOS_LOGIN || 'admin';
const PASSWORD = process.env.INSILOS_PASSWORD || 'admin';

const VIEWPORTS = [
  { key: '1280', label: '1280x800', width: 1280, height: 800, profile: 'Compact Enterprise Laptop' },
  { key: '1366', label: '1366x768', width: 1366, height: 768, profile: 'Standard Corporate Screen (HD)' },
  { key: '1440', label: '1440x900', width: 1440, height: 900, profile: 'Medium Desktop / MacBook Retina' },
  { key: '1920', label: '1920x1080', width: 1920, height: 1080, profile: 'Full HD Desktop' }
];

const TARGET_APPS = [
  {
    code: 'HCM',
    name: 'Human Resources & SuccessFactors (HCM)',
    url: `${BASE_URL}/insilos/employees`,
    xmlid: 'hr.menu_hr_root'
  },
  {
    code: 'SD',
    name: 'Sales & Distribution (SD)',
    url: `${BASE_URL}/insilos/sales`,
    xmlid: 'sale.sale_menu_root'
  },
  {
    code: 'FI/CO',
    name: 'Financials & Controlling (FI/CO)',
    url: `${BASE_URL}/insilos/accounting`,
    xmlid: 'account.menu_finance'
  },
  {
    code: 'Logistics IDP',
    name: 'Logistics IDP',
    url: `${BASE_URL}/insilos/logistics-onboarding`,
    xmlid: 'insilos_logistics_idp.menu_logistics_idp_root'
  },
  {
    code: 'Capital Markets',
    name: 'Capital Markets',
    url: `${BASE_URL}/insilos/action-5060`,
    xmlid: 'insilos_capital_markets_decision_governance.menu_capital_root'
  },
  {
    code: 'SAP PM',
    name: 'Plant Maintenance (SAP PM)',
    url: `${BASE_URL}/insilos/maintenance`,
    xmlid: 'maintenance.menu_maintenance_title'
  }
];

async function authenticateSession(page) {
  const resp = await page.request.post(`${BASE_URL}/web/session/authenticate`, {
    data: {
      jsonrpc: '2.0',
      params: {
        db: DB_NAME,
        login: LOGIN,
        password: PASSWORD
      }
    }
  });
  if (!resp.ok()) {
    throw new Error(`Authentication endpoint returned HTTP ${resp.status()}`);
  }
  const body = await resp.json();
  if (body.error) {
    throw new Error(`Authentication RPC error: ${JSON.stringify(body.error)}`);
  }
}

async function auditSinglePass(page, vp, app) {
  const testId = `${app.code}@${vp.label}`;
  const passResult = {
    testId,
    appCode: app.code,
    appName: app.name,
    viewport: vp.label,
    passed: true,
    failures: [],
    metrics: {}
  };

  await page.setViewportSize({ width: vp.width, height: vp.height });
  await page.goto(app.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForSelector('.o_main_navbar', { timeout: 20000 });

  // Allow Owl reactive adapt() and ResizeObserver debounce to settle
  await page.waitForTimeout(600);

  // Dismiss any transient error/notification dialog (e.g. Calendar View warning on sales route)
  const modalCloseBtn = await page.$('.modal .btn-close, .modal .modal-footer button, .modal button');
  if (modalCloseBtn) {
    try {
      await modalCloseBtn.click();
      await page.waitForTimeout(300);
    } catch (_) {}
  }

  // Evaluate DOM metrics and zero-tolerance assertions inside browser context
  const domData = await page.evaluate((viewportConfig) => {
    const navbar = document.querySelector('.o_main_navbar');
    const brandWrapper = document.querySelector('.o_menu_brand_wrapper');
    const brand = document.querySelector('.o_menu_brand');
    const sections = document.querySelector('.o_menu_sections');
    const systray = document.querySelector('.o_menu_systray');
    const moreBtn = document.querySelector('.o_menu_sections_more');

    const navRect = navbar ? navbar.getBoundingClientRect() : null;
    const brandEffective = brandWrapper || brand;
    const brandRect = brandEffective ? brandEffective.getBoundingClientRect() : null;
    const sectionsRect = sections ? sections.getBoundingClientRect() : null;
    const systrayRect = systray ? systray.getBoundingClientRect() : null;

    // Check visible children in sections
    const sectionChildren = sections ? Array.from(sections.children) : [];
    const childrenMetrics = sectionChildren.map((c) => {
      const cs = window.getComputedStyle(c);
      const r = c.getBoundingClientRect();
      const isDNoneClass = c.classList.contains('d-none');
      const isVisible = cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0;
      return {
        className: c.className,
        text: c.textContent.trim().replace(/\s+/g, ' '),
        display: cs.display,
        isDNoneClass,
        isVisible,
        rect: { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, left: r.left }
      };
    });

    // Check all .d-none elements inside sections
    const dNoneElements = sections ? Array.from(sections.querySelectorAll('.d-none')) : [];
    const brokenDNone = dNoneElements.map((el) => {
      const cs = window.getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return {
        text: el.textContent.trim().replace(/\s+/g, ' '),
        display: cs.display,
        width: r.width,
        height: r.height
      };
    }).filter((item) => item.display !== 'none' || item.width > 0);

    // Direct visible children of navbar
    const directNavbarChildren = navbar ? Array.from(navbar.children).filter((c) => {
      const cs = window.getComputedStyle(c);
      return cs.display !== 'none' && cs.visibility !== 'hidden' && c.getBoundingClientRect().height > 0;
    }) : [];

    // Structural section containers (Brand Wrapper, Sections, Systray)
    const sectionContainers = directNavbarChildren.filter((c) =>
      !c.classList.contains('o_menu_toggle') && !c.classList.contains('o_navbar_apps_menu')
    );
    const sectionTops = sectionContainers.map((c) => Math.round(c.getBoundingClientRect().top));
    const sectionMaxTop = sectionTops.length > 0 ? Math.max(...sectionTops) : 0;
    const sectionMinTop = sectionTops.length > 0 ? Math.min(...sectionTops) : 0;
    const sectionTopDelta = sectionMaxTop - sectionMinTop;

    // Check if any direct visible child wrapped to line 2 (top pushed below row boundary)
    const wrappedChildren = directNavbarChildren.filter((c) => {
      const r = c.getBoundingClientRect();
      return navRect ? r.top >= navRect.bottom - 2 : false;
    });

    // Check systray subcomponents
    const companyMenu = document.querySelector('.o_switch_company_menu');
    const aiAssistant = document.querySelector('.o_ai_systray_btn, .o_ai_assistant_systray');
    const userMenu = document.querySelector('.o_user_menu');

    return {
      navRect,
      brandRect,
      sectionsRect,
      systrayRect,
      childrenMetrics,
      brokenDNone,
      dNoneCount: dNoneElements.length,
      sectionTops,
      sectionTopDelta,
      wrappedChildrenCount: wrappedChildren.length,
      navScrollWidth: navbar ? navbar.scrollWidth : 0,
      navClientWidth: navbar ? navbar.clientWidth : 0,
      docScrollWidth: document.documentElement.scrollWidth,
      windowWidth: window.innerWidth,
      hasMoreBtn: !!moreBtn,
      moreBtnVisible: moreBtn ? (window.getComputedStyle(moreBtn).display !== 'none' && moreBtn.getBoundingClientRect().width > 0) : false,
      systrayDisplay: systray ? window.getComputedStyle(systray).display : null,
      companyMenuFound: !!companyMenu,
      aiAssistantFound: !!aiAssistant,
      userMenuFound: !!userMenu
    };
  }, vp);

  passResult.metrics = domData;

  // --------------------------------------------------------------------------
  // Assertion 1: 0px Bounding-Box Collision & .d-none Computed Invariance
  // --------------------------------------------------------------------------
  if (domData.brandRect && domData.sectionsRect) {
    const brandToSectionsOverlap = domData.brandRect.right - domData.sectionsRect.left;
    if (brandToSectionsOverlap > 1.0) {
      passResult.failures.push(
        `Brand collides with Sections: brand.right (${domData.brandRect.right.toFixed(1)}px) > sections.left (${domData.sectionsRect.left.toFixed(1)}px), overlap = +${brandToSectionsOverlap.toFixed(1)}px`
      );
    }
  }

  if (domData.sectionsRect && domData.systrayRect) {
    const sectionsToSystrayOverlap = domData.sectionsRect.right - domData.systrayRect.left;
    if (sectionsToSystrayOverlap > 1.0) {
      passResult.failures.push(
        `Sections container collides with Systray: sections.right (${domData.sectionsRect.right.toFixed(1)}px) > systray.left (${domData.systrayRect.left.toFixed(1)}px), overlap = +${sectionsToSystrayOverlap.toFixed(1)}px`
      );
    }
  }

  if (domData.systrayRect) {
    const visibleChildren = domData.childrenMetrics.filter((c) => c.isVisible);
    for (const child of visibleChildren) {
      const childOverlap = child.rect.right - domData.systrayRect.left;
      if (childOverlap > 1.0) {
        passResult.failures.push(
          `Section child '${child.text}' collides with Systray: child.right (${child.rect.right.toFixed(1)}px) > systray.left (${domData.systrayRect.left.toFixed(1)}px), overlap = +${childOverlap.toFixed(1)}px`
        );
      }
    }
  }

  if (domData.brokenDNone.length > 0) {
    passResult.failures.push(
      `${domData.brokenDNone.length} element(s) with class .d-none failed to collapse (display !== none): ${domData.brokenDNone.map((b) => `'${b.text}' (${b.display}, width: ${b.width}px)`).join(', ')}`
    );
  }

  // --------------------------------------------------------------------------
  // Assertion 2: 0px Line Wrap (No 2nd Line, Nominal 48px Height)
  // --------------------------------------------------------------------------
  if (domData.sectionTopDelta > 1.0) {
    passResult.failures.push(
      `Navbar section containers top offset mismatch: top delta = ${domData.sectionTopDelta}px`
    );
  }

  if (domData.wrappedChildrenCount > 0) {
    passResult.failures.push(
      `Navbar wrapped to second line: ${domData.wrappedChildrenCount} direct children pushed below row boundary`
    );
  }

  if (domData.navRect) {
    const navHeight = domData.navRect.height;
    if (navHeight < 46.0 || navHeight > 50.0) {
      passResult.failures.push(
        `Navbar height out of specification: ${navHeight.toFixed(1)}px (expected between 46px and 50px, nominal 48px)`
      );
    }
  }

  // --------------------------------------------------------------------------
  // Assertion 3: Zero Horizontal Scrollbar / Overflow
  // --------------------------------------------------------------------------
  if (domData.navScrollWidth > domData.navClientWidth) {
    const navOverflow = domData.navScrollWidth - domData.navClientWidth;
    passResult.failures.push(
      `Navbar horizontal scroll overflow: scrollWidth (${domData.navScrollWidth}px) > clientWidth (${domData.navClientWidth}px), overflow = +${navOverflow}px`
    );
  }

  if (domData.docScrollWidth > domData.windowWidth) {
    const docOverflow = domData.docScrollWidth - domData.windowWidth;
    passResult.failures.push(
      `Document horizontal overflow: scrollWidth (${domData.docScrollWidth}px) > windowWidth (${domData.windowWidth}px), overflow = +${docOverflow}px`
    );
  }

  // --------------------------------------------------------------------------
  // Assertion 4: Systray Intact & Right-Aligned
  // --------------------------------------------------------------------------
  if (domData.systrayRect) {
    const systrayOverflow = domData.systrayRect.right - vp.width;
    if (systrayOverflow > 1.0) {
      passResult.failures.push(
        `Systray exceeds viewport right boundary: systray.right (${domData.systrayRect.right.toFixed(1)}px) > viewport.width (${vp.width}px), overflow = +${systrayOverflow.toFixed(1)}px`
      );
    }
  } else {
    passResult.failures.push(`Systray element (.o_menu_systray) not found in DOM`);
  }

  if (domData.systrayDisplay !== 'flex') {
    passResult.failures.push(
      `Systray display is '${domData.systrayDisplay}', expected 'flex'`
    );
  }

  if (!domData.companyMenuFound) {
    passResult.failures.push(`Systray component: Company switcher (.o_switch_company_menu) not found`);
  }
  if (!domData.aiAssistantFound) {
    passResult.failures.push(`Systray component: AI Assistant (.o_ai_systray_btn) not found`);
  }
  if (!domData.userMenuFound) {
    passResult.failures.push(`Systray component: User avatar menu (.o_user_menu) not found`);
  }

  // --------------------------------------------------------------------------
  // Assertion 5: More Dropdown Interaction & Content Parity
  // --------------------------------------------------------------------------
  if (domData.dNoneCount > 0) {
    // When sections overflow, .o_menu_sections_more MUST be present and visible
    if (!domData.hasMoreBtn || !domData.moreBtnVisible) {
      passResult.failures.push(
        `Sections overflowed (${domData.dNoneCount} hidden items), but .o_menu_sections_more is not visible`
      );
    } else {
      // Test interactive clicking of More dropdown
      try {
        const moreBtnLocator = page.locator('.o_menu_sections_more button, .o_menu_sections_more .dropdown-toggle').first();
        await moreBtnLocator.click({ force: true });
        await page.waitForTimeout(300);

        const dropdownData = await page.evaluate(() => {
          const btn = document.querySelector('.o_menu_sections_more button, .o_menu_sections_more .dropdown-toggle');
          const popover = document.querySelector('.o-dropdown--menu, .dropdown-menu, .o_popover');
          const items = popover ? Array.from(popover.querySelectorAll('.dropdown-item, .o_more_dropdown_section, .o_nav_entry')).map((i) =>
            i.textContent.trim().replace(/\s+/g, ' ')
          ) : [];
          return {
            expanded: btn ? btn.getAttribute('aria-expanded') : null,
            hasPopover: !!popover,
            items
          };
        });

        if (dropdownData.expanded !== 'true') {
          passResult.failures.push(
            `More dropdown button aria-expanded was '${dropdownData.expanded}', expected 'true'`
          );
        }
        if (!dropdownData.hasPopover || dropdownData.items.length === 0) {
          passResult.failures.push(`More dropdown opened but contains 0 items or popover was not attached`);
        }

        // Close dropdown via Escape key to restore clean DOM state
        await page.keyboard.press('Escape');
        await page.waitForTimeout(200);
      } catch (clickErr) {
        passResult.failures.push(`Failed to interact with More dropdown: ${clickErr.message}`);
      }
    }
  }

  passResult.passed = passResult.failures.length === 0;

  // Visual screenshot capture for HCM app
  if (app.code === 'HCM') {
    const screenshotPath = path.join(ARTIFACTS_DIR, `hcm_menu_verified_${vp.key}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });
    passResult.screenshot = screenshotPath;
  }

  // Capture failure snapshot if assertions failed
  if (!passResult.passed) {
    const failurePath = path.join(ARTIFACTS_DIR, `failure_${app.code}_${vp.key}.png`);
    await page.screenshot({ path: failurePath, fullPage: false });
    passResult.failureScreenshot = failurePath;
  }

  return passResult;
}

async function runLayoutCollisionAuditSuite() {
  console.log('================================================================================');
  console.log('AUTOMATED HEADER MENU LAYOUT COLLISION AUDIT SUITE (PLAYWRIGHT)');
  console.log('Zero-Tolerance Enterprise Bounding-Box Verification (SAP / Carbon Standard)');
  console.log('Target Server: ' + BASE_URL + ' | Database: ' + DB_NAME);
  console.log('Matrix: ' + VIEWPORTS.length + ' Viewports x ' + TARGET_APPS.length + ' Applications = 24 Passes');
  console.log('================================================================================\n');

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

  console.log('[*] Authenticating administrative session...');
  await authenticateSession(page);
  console.log('[+] Session authenticated successfully.\n');

  const startTime = Date.now();
  const allResults = [];
  let passedCount = 0;
  let failedCount = 0;

  for (const vp of VIEWPORTS) {
    console.log(`\n>>> VIEWPORT: ${vp.label} (${vp.profile})`);
    console.log('-'.repeat(80));

    for (const app of TARGET_APPS) {
      process.stdout.write(`  [TEST] ${app.code.padEnd(16)} | ${vp.label} ... `);
      try {
        const result = await auditSinglePass(page, vp, app);
        allResults.push(result);

        if (result.passed) {
          passedCount++;
          console.log('\x1b[32mPASS\x1b[0m (0px collision, 0px wrap, 0px overflow)');
        } else {
          failedCount++;
          console.log('\x1b[31mFAIL\x1b[0m');
          for (const f of result.failures) {
            console.log(`         \x1b[31m- ${f}\x1b[0m`);
          }
        }
      } catch (err) {
        failedCount++;
        const errResult = {
          testId: `${app.code}@${vp.label}`,
          appCode: app.code,
          appName: app.name,
          viewport: vp.label,
          passed: false,
          failures: [`Execution exception: ${err.message}`]
        };
        allResults.push(errResult);
        console.log(`\x1b[31mERROR: ${err.message}\x1b[0m`);
      }
    }
  }

  await browser.close();
  const totalDuration = ((Date.now() - startTime) / 1000).toFixed(2);

  // Print Structured ASCII Summary Matrix
  console.log('\n================================================================================');
  console.log('LAYOUT COLLISION AUDIT SUMMARY MATRIX');
  console.log('================================================================================');
  console.log(
    '| ' +
    'Application'.padEnd(18) + ' | ' +
    '1280x800'.padEnd(10) + ' | ' +
    '1366x768'.padEnd(10) + ' | ' +
    '1440x900'.padEnd(10) + ' | ' +
    '1920x1080'.padEnd(10) + ' | ' +
    'Overall'.padEnd(8) + ' |'
  );
  console.log('|' + '-'.repeat(20) + '|' + '-'.repeat(12) + '|' + '-'.repeat(12) + '|' + '-'.repeat(12) + '|' + '-'.repeat(12) + '|' + '-'.repeat(10) + '|');

  for (const app of TARGET_APPS) {
    const vpStatuses = VIEWPORTS.map((vp) => {
      const match = allResults.find((r) => r.appCode === app.code && r.viewport === vp.label);
      return match && match.passed ? 'PASS' : 'FAIL';
    });
    const appPassed = vpStatuses.every((s) => s === 'PASS');
    const statusCol = appPassed ? '\x1b[32mPASS\x1b[0m' : '\x1b[31mFAIL\x1b[0m';

    console.log(
      '| ' +
      app.code.padEnd(18) + ' | ' +
      (vpStatuses[0] === 'PASS' ? '\x1b[32mPASS\x1b[0m      ' : '\x1b[31mFAIL\x1b[0m      ') + ' | ' +
      (vpStatuses[1] === 'PASS' ? '\x1b[32mPASS\x1b[0m      ' : '\x1b[31mFAIL\x1b[0m      ') + ' | ' +
      (vpStatuses[2] === 'PASS' ? '\x1b[32mPASS\x1b[0m      ' : '\x1b[31mFAIL\x1b[0m      ') + ' | ' +
      (vpStatuses[3] === 'PASS' ? '\x1b[32mPASS\x1b[0m      ' : '\x1b[31mFAIL\x1b[0m      ') + ' | ' +
      statusCol.padEnd(16) + ' |'
    );
  }
  console.log('================================================================================');
  console.log(`Total Passes: ${allResults.length} | Passed: ${passedCount} | Failed: ${failedCount} | Duration: ${totalDuration}s`);
  console.log('================================================================================\n');

  // Print Structured JSON Report
  const jsonReport = {
    suite: 'Automated Header Menu Layout Collision Audit',
    timestamp: new Date().toISOString(),
    totalDurationSeconds: parseFloat(totalDuration),
    summary: {
      total: allResults.length,
      passed: passedCount,
      failed: failedCount,
      rate: `${((passedCount / allResults.length) * 100).toFixed(1)}%`
    },
    results: allResults.map((r) => ({
      testId: r.testId,
      app: r.appCode,
      viewport: r.viewport,
      passed: r.passed,
      failures: r.failures,
      screenshot: r.screenshot || null
    }))
  };

  console.log('--- STRUCTURED JSON REPORT ---');
  console.log(JSON.stringify(jsonReport, null, 2));

  // Exit with zero if all 24 passes succeed, code 1 if any failed
  if (failedCount > 0) {
    console.error(`\n[FATAL] Layout audit failed with ${failedCount} assertion defect(s).`);
    process.exit(1);
  } else {
    console.log(`\n[SUCCESS] All 24 layout passes verified with 0px collision, 0px wrap, and 0px overflow.`);
    process.exit(0);
  }
}

runLayoutCollisionAuditSuite().catch((err) => {
  console.error('[FATAL] Unhandled audit error:', err);
  process.exit(1);
});
