/**
 * Adversarial Layout Collision & Stress Challenge Suite 2
 * ==============================================================================
 * Empirical challenger harness authored by challenger_navbar_2.
 * Directly executes 4 adversarial challenge dimensions:
 *   Dimension 1: Small Viewport Stress (1024x768 and 1152x864) across 6 applications.
 *   Dimension 2: Rapid Window Resize Loop Stress (ResizeObserver loop check, memory/exceptions).
 *   Dimension 3: Dark Mode Theme Rendering, Styling Tokens & WCAG Contrast.
 *   Dimension 4: Extreme App Name Length Clamping & Ellipsis Invariance.
 *
 * Exits with code 0 on PASS, code 1 on FAIL.
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

const TARGET_APPS = [
  { code: 'HCM', name: 'Human Resources & SuccessFactors (HCM)', url: `${BASE_URL}/insilos/employees` },
  { code: 'SD', name: 'Sales & Distribution (SD)', url: `${BASE_URL}/insilos/sales` },
  { code: 'FI/CO', name: 'Financials & Controlling (FI/CO)', url: `${BASE_URL}/insilos/accounting` },
  { code: 'Logistics IDP', name: 'Logistics IDP', url: `${BASE_URL}/insilos/logistics-onboarding` },
  { code: 'Capital Markets', name: 'Capital Markets', url: `${BASE_URL}/insilos/action-5060` },
  { code: 'SAP PM', name: 'Plant Maintenance (SAP PM)', url: `${BASE_URL}/insilos/maintenance` }
];

// Helper: Calculate relative luminance for WCAG contrast
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(rgb1, rgb2) {
  const l1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function parseRgb(colorStr) {
  const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (match) {
    return {
      r: parseInt(match[1], 10),
      g: parseInt(match[2], 10),
      b: parseInt(match[3], 10),
      a: match[4] !== undefined ? parseFloat(match[4]) : 1.0
    };
  }
  return { r: 255, g: 255, b: 255, a: 1.0 };
}

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
    throw new Error(`Auth failed HTTP ${resp.status()}`);
  }
  const body = await resp.json();
  if (body.error) {
    throw new Error(`Auth RPC error: ${JSON.stringify(body.error)}`);
  }
}

async function dismissModalIfPresent(page) {
  try {
    const closeBtn = await page.$('.modal .btn-close, .modal .modal-footer button, .modal button, .modal .btn-primary');
    if (closeBtn) {
      await closeBtn.click({ force: true });
      await page.waitForTimeout(300);
    }
  } catch (_) {}
}

async function inspectNavbarLayout(page) {
  return await page.evaluate(() => {
    const navbar = document.querySelector('.o_main_navbar');
    const brandWrapper = document.querySelector('.o_menu_brand_wrapper');
    const brand = document.querySelector('.o_menu_brand');
    const sections = document.querySelector('.o_menu_sections');
    const systray = document.querySelector('.o_menu_systray');
    const moreBtn = document.querySelector('.o_menu_sections_more');

    const navRect = navbar ? navbar.getBoundingClientRect() : null;
    const brandEffective = brandWrapper || brand;
    const brandRect = brandEffective ? brandEffective.getBoundingClientRect() : null;
    const brandInnerRect = brand ? brand.getBoundingClientRect() : null;
    const sectionsRect = sections ? sections.getBoundingClientRect() : null;
    const systrayRect = systray ? systray.getBoundingClientRect() : null;

    // Check .d-none elements inside sections
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

    const sectionContainers = directNavbarChildren.filter((c) =>
      !c.classList.contains('o_menu_toggle') && !c.classList.contains('o_navbar_apps_menu')
    );
    const sectionTops = sectionContainers.map((c) => Math.round(c.getBoundingClientRect().top));
    const sectionMaxTop = sectionTops.length > 0 ? Math.max(...sectionTops) : 0;
    const sectionMinTop = sectionTops.length > 0 ? Math.min(...sectionTops) : 0;
    const sectionTopDelta = sectionMaxTop - sectionMinTop;

    const wrappedChildren = directNavbarChildren.filter((c) => {
      const r = c.getBoundingClientRect();
      return navRect ? r.top >= navRect.bottom - 2 : false;
    });

    const visibleSectionItems = sections ? Array.from(sections.children).filter((c) => {
      const cs = window.getComputedStyle(c);
      return cs.display !== 'none' && !c.classList.contains('d-none');
    }).map((c) => {
      const r = c.getBoundingClientRect();
      return {
        className: c.className,
        text: c.textContent.trim().replace(/\s+/g, ' '),
        right: r.right,
        width: r.width
      };
    }) : [];

    return {
      navRect,
      brandRect,
      brandInnerRect,
      sectionsRect,
      systrayRect,
      brokenDNone,
      dNoneCount: dNoneElements.length,
      sectionTopDelta,
      wrappedChildrenCount: wrappedChildren.length,
      navScrollWidth: navbar ? navbar.scrollWidth : 0,
      navClientWidth: navbar ? navbar.clientWidth : 0,
      docScrollWidth: document.documentElement.scrollWidth,
      windowWidth: window.innerWidth,
      hasMoreBtn: !!moreBtn,
      moreBtnVisible: moreBtn ? (window.getComputedStyle(moreBtn).display !== 'none' && moreBtn.getBoundingClientRect().width > 0) : false,
      visibleSectionItemsCount: visibleSectionItems.length,
      visibleSectionItems,
      brandTitle: brand ? brand.getAttribute('title') : null,
      brandWrapperTitle: brandWrapper ? brandWrapper.getAttribute('title') : null,
      brandStyle: brand ? {
        textOverflow: window.getComputedStyle(brand).textOverflow,
        whiteSpace: window.getComputedStyle(brand).whiteSpace,
        maxWidth: window.getComputedStyle(brand).maxWidth
      } : null,
      brandWrapperStyle: brandWrapper ? {
        maxWidth: window.getComputedStyle(brandWrapper).maxWidth
      } : null
    };
  });
}

// ----------------------------------------------------------------------------
// SUITE 1: Small Viewport Stress (1024x768 and 1152x864)
// ----------------------------------------------------------------------------
async function runSuite1_SmallViewports(browser) {
  console.log('\n================================================================================');
  console.log('CHALLENGE DIMENSION 1: SMALL VIEWPORT STRESS (1024x768, 1152x864)');
  console.log('================================================================================');

  const viewports = [
    { label: '1024x768', width: 1024, height: 768, code: '1024' },
    { label: '1152x864', width: 1152, height: 864, code: '1152' }
  ];

  const results = [];
  let allPass = true;

  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();
    await authenticateSession(page);

    for (const app of TARGET_APPS) {
      const testId = `${app.code}@${vp.label}`;
      const itemResult = { testId, vp: vp.label, app: app.code, passed: true, errors: [] };

      try {
        await page.goto(app.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForSelector('.o_main_navbar', { timeout: 20000 });
        await page.waitForTimeout(600);
        await dismissModalIfPresent(page);

        const data = await inspectNavbarLayout(page);

        // Assert 1: Bounding Box Collision
        if (data.brandRect && data.sectionsRect) {
          const overlap = data.brandRect.right - data.sectionsRect.left;
          if (overlap > 1.0) {
            itemResult.errors.push(`Brand overlap Sections: +${overlap.toFixed(1)}px`);
          }
        }
        if (data.sectionsRect && data.systrayRect) {
          const overlap = data.sectionsRect.right - data.systrayRect.left;
          if (overlap > 1.0) {
            itemResult.errors.push(`Sections overlap Systray: +${overlap.toFixed(1)}px`);
          }
        }
        if (data.systrayRect && data.visibleSectionItems) {
          for (const item of data.visibleSectionItems) {
            if (item.right > data.systrayRect.left + 1.0) {
              itemResult.errors.push(`Section item "${item.text}" right (${item.right.toFixed(1)}px) collides with Systray left (${data.systrayRect.left.toFixed(1)}px)`);
            }
          }
        }

        // Assert 2: .d-none Leaks
        if (data.brokenDNone.length > 0) {
          itemResult.errors.push(`.d-none display leak count: ${data.brokenDNone.length}`);
        }

        // Assert 3: Line Wrap
        if (data.sectionTopDelta > 1) {
          itemResult.errors.push(`Line wrap topDelta: ${data.sectionTopDelta}px`);
        }
        if (data.wrappedChildrenCount > 0) {
          itemResult.errors.push(`Wrapped children count: ${data.wrappedChildrenCount}`);
        }

        // Assert 4: Horizontal Scroll
        const navOverflow = data.navScrollWidth - data.navClientWidth;
        if (navOverflow > 1) {
          itemResult.errors.push(`Navbar horizontal scroll overflow: ${navOverflow}px`);
        }

        // Assert 5: More Dropdown Interaction (if items overflowed)
        if (data.dNoneCount > 0) {
          if (!data.hasMoreBtn || !data.moreBtnVisible) {
            itemResult.errors.push(`Overflow detected (${data.dNoneCount} items) but More button is NOT visible`);
          } else {
            // Test clicking More button
            await dismissModalIfPresent(page);
            const moreBtnLocator = page.locator('.o_menu_sections_more button, .o_menu_sections_more .dropdown-toggle').first();
            await moreBtnLocator.click({ force: true });
            await page.waitForTimeout(300);
            const dropdownMenu = await page.$('.o-dropdown--menu.dropdown-menu, .o_menu_sections_more .dropdown-menu');
            const isExpanded = await moreBtnLocator.getAttribute('aria-expanded');
            if (!dropdownMenu || isExpanded !== 'true') {
              itemResult.errors.push(`More button clicked but dropdown did not open (aria-expanded=${isExpanded})`);
            }
            // Close dropdown
            await page.keyboard.press('Escape');
            await page.waitForTimeout(200);
          }
        }

        // Capture screenshot for HCM
        if (app.code === 'HCM') {
          const ssPath = path.join(ARTIFACTS_DIR, `adversarial_small_vp_${vp.code}_hcm.png`);
          await page.screenshot({ path: ssPath, fullPage: false });
          itemResult.screenshot = ssPath;
        }

      } catch (err) {
        itemResult.errors.push(`Execution error: ${err.message}`);
      }

      if (itemResult.errors.length > 0) {
        itemResult.passed = false;
        allPass = false;
      }

      console.log(`[${itemResult.passed ? 'PASS' : 'FAIL'}] ${testId.padEnd(25)} | Errors: ${itemResult.errors.length === 0 ? 'None' : itemResult.errors.join('; ')}`);
      results.push(itemResult);
    }

    await page.close();
    await context.close();
  }

  return { name: 'Suite 1: Small Viewports (1024x768, 1152x864)', passed: allPass, results };
}

// ----------------------------------------------------------------------------
// SUITE 2: Rapid Window Resize Loop Stress Test
// ----------------------------------------------------------------------------
async function runSuite2_RapidResizeLoop(browser) {
  console.log('\n================================================================================');
  console.log('CHALLENGE DIMENSION 2: RAPID WINDOW RESIZE LOOP STRESS');
  console.log('================================================================================');

  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  await authenticateSession(page);

  const uncaughtErrors = [];
  const resizeObserverErrors = [];
  page.on('pageerror', (err) => {
    uncaughtErrors.push(err.message);
    if (err.message.includes('ResizeObserver')) {
      resizeObserverErrors.push(err.message);
    }
  });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (text.includes('ResizeObserver')) {
        resizeObserverErrors.push(text);
      }
    }
  });

  // Navigate to HCM
  await page.goto(`${BASE_URL}/insilos/employees`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.o_main_navbar', { timeout: 20000 });
  await page.waitForTimeout(600);
  await dismissModalIfPresent(page);

  // Rapid resize loop: 1920 -> 1280 -> 1440 -> 1024 -> 1152 -> 1366 -> 1920
  const loopSizes = [
    { width: 1920, height: 1080 },
    { width: 1280, height: 800 },
    { width: 1440, height: 900 },
    { width: 1024, height: 768 },
    { width: 1152, height: 864 },
    { width: 1366, height: 768 },
    { width: 1920, height: 1080 }
  ];

  const cycles = 8;
  console.log(`Starting rapid continuous window resize loop: ${cycles} cycles x ${loopSizes.length} steps (${cycles * loopSizes.length} resizes)...`);

  const startTime = Date.now();
  let resizeCount = 0;

  for (let c = 0; c < cycles; c++) {
    for (const size of loopSizes) {
      await page.setViewportSize(size);
      // Fast interval simulating continuous window dragging
      await page.waitForTimeout(30);
      resizeCount++;
    }
  }

  const loopDurationMs = Date.now() - startTime;
  console.log(`Completed ${resizeCount} resize operations in ${loopDurationMs}ms (avg ${(loopDurationMs / resizeCount).toFixed(1)}ms per resize).`);

  // Allow adaptation settling time (test settling within 150ms)
  const settlingStart = Date.now();
  await page.waitForTimeout(150);
  const settlingElapsed = Date.now() - settlingStart;

  // Now inspect final state
  const finalData = await inspectNavbarLayout(page);

  const errors = [];
  if (uncaughtErrors.length > 0) {
    errors.push(`Uncaught JavaScript exceptions: ${uncaughtErrors.join('; ')}`);
  }
  if (resizeObserverErrors.length > 0) {
    errors.push(`ResizeObserver loop errors detected: ${resizeObserverErrors.join('; ')}`);
  }
  if (finalData.brokenDNone.length > 0) {
    errors.push(`.d-none display leaks after resize loop: ${finalData.brokenDNone.length}`);
  }
  if (finalData.sectionTopDelta > 1) {
    errors.push(`Section top delta after resize loop: ${finalData.sectionTopDelta}px (wrapped)`);
  }
  if (finalData.navScrollWidth > finalData.navClientWidth) {
    errors.push(`Navbar scrollWidth > clientWidth after resize loop`);
  }

  // Capture screenshot of settled state
  const ssPath = path.join(ARTIFACTS_DIR, `adversarial_rapid_resize_settled.png`);
  await page.screenshot({ path: ssPath });

  await page.close();
  await context.close();

  const passed = errors.length === 0;
  console.log(`[${passed ? 'PASS' : 'FAIL'}] Rapid Resize Loop | Resize Count: ${resizeCount} | Errors: ${errors.length === 0 ? 'None' : errors.join('; ')}`);

  return {
    name: 'Suite 2: Rapid Window Resize Loop Stress',
    passed,
    metrics: { resizeCount, loopDurationMs, uncaughtErrorsCount: uncaughtErrors.length, resizeObserverErrorsCount: resizeObserverErrors.length },
    errors
  };
}

// ----------------------------------------------------------------------------
// SUITE 3: Dark Mode Theme Rendering, Styling Tokens & WCAG Contrast
// ----------------------------------------------------------------------------
async function runSuite3_DarkModeContrast(browser) {
  console.log('\n================================================================================');
  console.log('CHALLENGE DIMENSION 3: DARK MODE THEME RENDERING, STYLING & WCAG CONTRAST');
  console.log('================================================================================');

  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  await authenticateSession(page);

  await page.goto(`${BASE_URL}/insilos/employees`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.o_main_navbar', { timeout: 20000 });
  await page.waitForTimeout(600);
  await dismissModalIfPresent(page);

  // Activate Dark Mode
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  });
  await page.waitForTimeout(300);

  const errors = [];

  // Inspect More button computed styles in Dark Mode
  const darkModeStyles = await page.evaluate(() => {
    const moreBtn = document.querySelector('.o_menu_sections_more button, .o_menu_sections_more .dropdown-toggle');
    const sections = document.querySelector('.o_menu_sections');
    const nav = document.querySelector('.o_main_navbar');

    if (!moreBtn) return null;

    const csMore = window.getComputedStyle(moreBtn);
    const navCs = window.getComputedStyle(nav);

    return {
      moreColor: csMore.color,
      moreBg: csMore.backgroundColor,
      moreBorder: csMore.borderColor,
      moreHeight: csMore.height,
      moreRadius: csMore.borderRadius,
      navBg: navCs.backgroundColor
    };
  });

  if (!darkModeStyles) {
    errors.push('More button not found in DOM for styling inspection');
  } else {
    console.log(`  - Resting More Button Color: ${darkModeStyles.moreColor}`);
    console.log(`  - Resting More Button Background: ${darkModeStyles.moreBg}`);
    console.log(`  - Navbar Background: ${darkModeStyles.navBg}`);

    // Compute contrast of resting text against background
    const textColor = parseRgb(darkModeStyles.moreColor);
    const navBgColor = parseRgb(darkModeStyles.navBg);
    const restingContrast = getContrastRatio(textColor, navBgColor);
    console.log(`  - Resting Contrast Ratio: ${restingContrast.toFixed(2)}:1 (WCAG AA requires 4.5:1 for regular text, 3:1 for UI components)`);
    if (restingContrast < 3.0) {
      errors.push(`Resting More button contrast ratio too low: ${restingContrast.toFixed(2)}:1 < 3.0:1`);
    }

    // Now test Hover State styling
    const moreBtnHandle = await page.$('.o_menu_sections_more button, .o_menu_sections_more .dropdown-toggle');
    if (moreBtnHandle) {
      await moreBtnHandle.hover();
      await page.waitForTimeout(200);

      const hoverStyles = await page.evaluate(() => {
        const moreBtn = document.querySelector('.o_menu_sections_more button, .o_menu_sections_more .dropdown-toggle');
        const cs = window.getComputedStyle(moreBtn);
        return {
          color: cs.color,
          bg: cs.backgroundColor,
          borderColor: cs.borderColor
        };
      });

      console.log(`  - Hover More Button Color: ${hoverStyles.color}`);
      console.log(`  - Hover More Button Background: ${hoverStyles.bg}`);
      console.log(`  - Hover More Button Border: ${hoverStyles.borderColor}`);

      // Expect Tech Cyan (#00F2FE -> rgb(0, 242, 254)) in hover
      const hoverColorRgb = parseRgb(hoverStyles.color);
      const isTechCyan = (hoverColorRgb.r === 0 && hoverColorRgb.g === 242 && hoverColorRgb.b === 254);
      console.log(`  - Hover Color matches Tech Cyan #00F2FE: ${isTechCyan ? 'YES' : 'NO (' + hoverStyles.color + ')'}`);

      // Now click More button to test Dropdown Popover surface in Dark Mode
      await moreBtnHandle.click({ force: true });
      await page.waitForTimeout(300);

      const popoverStyles = await page.evaluate(() => {
        const menu = document.querySelector('.o-dropdown--menu.dropdown-menu, .o_menu_sections_more .dropdown-menu');
        if (!menu) return null;
        const csMenu = window.getComputedStyle(menu);
        const item = menu.querySelector('.o_more_dropdown_section.dropdown-item');
        const csItem = item ? window.getComputedStyle(item) : null;
        const header = menu.querySelector('.o_more_dropdown_section_group');
        const csHeader = header ? window.getComputedStyle(header) : null;

        return {
          menuBg: csMenu.backgroundColor,
          menuBorder: csMenu.borderColor,
          menuShadow: csMenu.boxShadow,
          itemColor: csItem ? csItem.color : null,
          itemBg: csItem ? csItem.backgroundColor : null,
          headerColor: csHeader ? csHeader.color : null,
          headerBg: csHeader ? csHeader.backgroundColor : null
        };
      });

      if (!popoverStyles) {
        errors.push('Dropdown menu surface not found when expanded');
      } else {
        console.log(`  - Dropdown Menu Background: ${popoverStyles.menuBg}`);
        console.log(`  - Dropdown Item Color: ${popoverStyles.itemColor}`);
        console.log(`  - Dropdown Header Color: ${popoverStyles.headerColor}`);

        // Dark background should be dark slate/navy (#141e33 -> rgb(20, 30, 51))
        const menuBg = parseRgb(popoverStyles.menuBg);
        const isDarkSurface = (menuBg.r < 40 && menuBg.g < 50 && menuBg.b < 70);
        if (!isDarkSurface) {
          errors.push(`Dropdown menu background in dark mode is not dark: ${popoverStyles.menuBg}`);
        }

        // Contrast of item text on menu background
        if (popoverStyles.itemColor) {
          const itemText = parseRgb(popoverStyles.itemColor);
          const itemContrast = getContrastRatio(itemText, menuBg);
          console.log(`  - Dropdown Item Contrast Ratio: ${itemContrast.toFixed(2)}:1 (WCAG AAA requires 7.0:1)`);
          if (itemContrast < 4.5) {
            errors.push(`Dropdown item text contrast too low: ${itemContrast.toFixed(2)}:1 < 4.5:1`);
          }
        }
      }

      // Capture screenshot in Dark Mode with dropdown open
      const ssPath = path.join(ARTIFACTS_DIR, `adversarial_dark_mode_more_hcm.png`);
      await page.screenshot({ path: ssPath });

      // Close popover
      await page.keyboard.press('Escape');
    }
  }

  await page.close();
  await context.close();

  const passed = errors.length === 0;
  console.log(`[${passed ? 'PASS' : 'FAIL'}] Dark Mode & Contrast | Errors: ${errors.length === 0 ? 'None' : errors.join('; ')}`);

  return {
    name: 'Suite 3: Dark Mode Theme Rendering & WCAG Contrast',
    passed,
    errors
  };
}

// ----------------------------------------------------------------------------
// SUITE 4: Extreme App Name Lengths Clamping & Ellipsis Invariance
// ----------------------------------------------------------------------------
async function runSuite4_ExtremeAppNameLengths(browser) {
  console.log('\n================================================================================');
  console.log('CHALLENGE DIMENSION 4: EXTREME APP NAME LENGTHS CLAMPING & ELLIPSIS');
  console.log('================================================================================');

  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  await authenticateSession(page);

  await page.goto(`${BASE_URL}/insilos/employees`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.o_main_navbar', { timeout: 20000 });
  await page.waitForTimeout(600);
  await dismissModalIfPresent(page);

  const testAppNames = [
    { label: 'Normal (37 chars)', name: 'Human Resources & SuccessFactors (HCM)' },
    { label: 'Long (68 chars)', name: 'Enterprise Integrated Multi-Modal Logistics & Freight Execution IDP' },
    { label: 'Ultra-Long (125 chars)', name: 'Global Supply Chain Planning, Advanced Production Scheduling, Distributed Manufacturing Orders & Real-Time Workshop MES' },
    { label: 'Adversarial Extreme (250 chars)', name: 'SAP S/4HANA Enterprise Resource Planning System - Global Financial Accounting, Controlling, Cost Center Allocations, Statutory Tax Compliance, Treasury Management, Asset Accounting & Consolidated Financial Statement Generation Engine for Insilos Enterprise' }
  ];

  const results = [];
  let allPass = true;

  for (const item of testAppNames) {
    const errors = [];

    // Inject extreme title into DOM brand and brand wrapper
    await page.evaluate((extremeName) => {
      const brand = document.querySelector('.o_menu_brand');
      const brandWrapper = document.querySelector('.o_menu_brand_wrapper');
      if (brand) {
        brand.textContent = extremeName;
        brand.setAttribute('title', extremeName);
      }
      if (brandWrapper) {
        brandWrapper.setAttribute('title', extremeName);
      }
      // Trigger Owl navbar adapt() by dispatching resize or calling component if available
      window.dispatchEvent(new Event('resize'));
    }, item.name);

    await page.waitForTimeout(300);

    const data = await inspectNavbarLayout(page);

    // Assert 1: Brand element width clamp: clamp(140px, 18vw, 260px)
    // On 1280px viewport, 18vw = 230.4px. Clamp max is 260px.
    if (data.brandInnerRect) {
      const width = data.brandInnerRect.width;
      console.log(`  [${item.label}] Brand width: ${width.toFixed(1)}px (Max clamp: 260px)`);
      if (width > 261.0) {
        errors.push(`Brand width exceeded 260px clamp limit: ${width.toFixed(1)}px`);
      }
    }

    // Assert 2: Brand wrapper width clamp: clamp(160px, 20vw, 280px)
    // On 1280px viewport, 20vw = 256px. Clamp max is 280px.
    if (data.brandRect) {
      const width = data.brandRect.width;
      console.log(`  [${item.label}] Brand wrapper width: ${width.toFixed(1)}px (Max clamp: 280px)`);
      if (width > 281.0) {
        errors.push(`Brand wrapper width exceeded 280px clamp limit: ${width.toFixed(1)}px`);
      }
    }

    // Assert 3: Ellipsis and nowrap CSS
    if (data.brandStyle) {
      if (data.brandStyle.textOverflow !== 'ellipsis') {
        errors.push(`Brand text-overflow is "${data.brandStyle.textOverflow}", expected "ellipsis"`);
      }
      if (data.brandStyle.whiteSpace !== 'nowrap') {
        errors.push(`Brand white-space is "${data.brandStyle.whiteSpace}", expected "nowrap"`);
      }
    }

    // Assert 4: Tooltip title preservation
    if (data.brandTitle !== item.name) {
      errors.push(`Brand tooltip title not preserved (got "${data.brandTitle}")`);
    }

    // Assert 5: Navbar containment: No collision with Sections or Systray
    if (data.brandRect && data.sectionsRect) {
      const overlap = data.brandRect.right - data.sectionsRect.left;
      if (overlap > 1.0) {
        errors.push(`Brand collides with Sections under extreme name: overlap +${overlap.toFixed(1)}px`);
      }
    }
    if (data.sectionsRect && data.systrayRect) {
      const overlap = data.sectionsRect.right - data.systrayRect.left;
      if (overlap > 1.0) {
        errors.push(`Sections collides with Systray under extreme name: overlap +${overlap.toFixed(1)}px`);
      }
    }

    // Assert 6: Single-line invariant
    if (data.sectionTopDelta > 1) {
      errors.push(`Section top delta broken: ${data.sectionTopDelta}px`);
    }

    const itemPassed = errors.length === 0;
    if (!itemPassed) allPass = false;

    console.log(`[${itemPassed ? 'PASS' : 'FAIL'}] Extreme App Name: ${item.label} | Errors: ${errors.length === 0 ? 'None' : errors.join('; ')}`);
    results.push({ label: item.label, passed: itemPassed, errors });
  }

  // Capture screenshot of adversarial extreme name
  const ssPath = path.join(ARTIFACTS_DIR, `adversarial_extreme_app_name.png`);
  await page.screenshot({ path: ssPath });

  await page.close();
  await context.close();

  return {
    name: 'Suite 4: Extreme App Name Lengths Clamping',
    passed: allPass,
    results
  };
}

// ----------------------------------------------------------------------------
// MAIN RUNNER
// ----------------------------------------------------------------------------
async function main() {
  console.log('Starting Adversarial Layout Collision & Stress Challenge Suite 2...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const suiteResults = [];

  try {
    const s1 = await runSuite1_SmallViewports(browser);
    suiteResults.push(s1);

    const s2 = await runSuite2_RapidResizeLoop(browser);
    suiteResults.push(s2);

    const s3 = await runSuite3_DarkModeContrast(browser);
    suiteResults.push(s3);

    const s4 = await runSuite4_ExtremeAppNameLengths(browser);
    suiteResults.push(s4);

  } catch (err) {
    console.error('Fatal test execution failure:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }

  console.log('\n================================================================================');
  console.log('ADVERSARIAL CHALLENGE SUITE 2 SUMMARY VERDICT');
  console.log('================================================================================');
  let overallPass = true;
  for (const s of suiteResults) {
    console.log(`- ${s.name}: ${s.passed ? 'PASSED' : 'FAILED'}`);
    if (!s.passed) overallPass = false;
  }
  console.log('================================================================================');
  console.log(`OVERALL VERDICT: ${overallPass ? 'APPROVE (SOLUTION CONFIRMED RESILIENT)' : 'CHALLENGE REJECT'}`);
  console.log('================================================================================\n');

  // Write machine readable results JSON for reporting
  const reportPath = path.join(__dirname, '..', 'tools', 'challenger_navbar_2_results.json');
  fs.writeFileSync(reportPath, JSON.stringify({ overallPass, suiteResults, timestamp: new Date().toISOString() }, null, 2));

  if (!overallPass) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
