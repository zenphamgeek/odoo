#!/usr/bin/env node
/**
 * tools/adversarial_owl_challenger_test.js
 * ========================================
 * Empirical Adversarial Test Harness by Challenger 1
 * Stress-tests OWL components, DOM states, edge cases, and visual regressions.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const OUT_DIR = path.resolve(__dirname, 'test_artifacts_challenger');
if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

function calculateLuminance(r, g, b) {
  const a = [r, g, b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

function getContrastRatio(rgb1, rgb2) {
  const lum1 = calculateLuminance(rgb1.r, rgb1.g, rgb1.b);
  const lum2 = calculateLuminance(rgb2.r, rgb2.g, rgb2.b);
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return (brightest + 0.05) / (darkest + 0.05);
}

function parseRgb(colorStr) {
  const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (match) {
    return { r: parseInt(match[1]), g: parseInt(match[2]), b: parseInt(match[3]) };
  }
  if (colorStr.startsWith('#')) {
    let hex = colorStr.slice(1);
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    return {
      r: parseInt(hex.substring(0, 2), 16),
      g: parseInt(hex.substring(2, 4), 16),
      b: parseInt(hex.substring(4, 6), 16)
    };
  }
  return { r: 0, g: 0, b: 0 };
}

async function runAdversarialAudit() {
  console.log('======================================================================');
  console.log('EMPIRICAL ADVERSARIAL CHALLENGER AUDIT: OWL & UI/UX HARD REFACTOR');
  console.log('======================================================================\n');

  const findings = [];
  function addFinding(severity, id, title, description, empiricalEvidence) {
    findings.push({ severity, id, title, description, empiricalEvidence });
    console.log(`[${severity}] ${id}: ${title}`);
    console.log(`  Evidence: ${JSON.stringify(empiricalEvidence, null, 2)}\n`);
  }

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

  try {
    // 1. Authenticate
    console.log('Authenticating session...');
    const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
      data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });
    if (!authRes.ok()) throw new Error('Auth failed');
    console.log('Auth OK.\n');

    // =========================================================================
    // TEST 1: ShellBar Elements & Overlap Analysis
    // =========================================================================
    console.log('>>> [TEST 1] ShellBar Layout & Overlap Analysis...');
    await page.goto('http://localhost:28069/insilos/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_navbar', { timeout: 15000 });
    await page.waitForTimeout(2000);

    const navAudit = await page.evaluate(() => {
      const navbar = document.querySelector('.o_navbar');
      const navRect = navbar ? navbar.getBoundingClientRect() : null;
      const waffleIcon = document.querySelector('.o_menu_toggle .ph-squares-four, .o_navbar_apps_menu .ph-squares-four');
      const waffleClass = waffleIcon ? waffleIcon.className : null;

      // Check brand and sections layout
      const brand = document.querySelector('.o_menu_brand');
      const brandRect = brand ? brand.getBoundingClientRect() : null;
      const brandVisible = brand ? window.getComputedStyle(brand).display !== 'none' : false;
      const brandText = brand ? brand.innerText.trim() : null;

      const brandLogo = document.querySelector('.o_insilos_brand_logo');
      const logoRect = brandLogo ? brandLogo.getBoundingClientRect() : null;

      const brandSeparator = document.querySelector('.o_menu_brand_separator');
      const sepRect = brandSeparator ? brandSeparator.getBoundingClientRect() : null;

      const sections = document.querySelector('.o_menu_sections');
      const sectionsRect = sections ? sections.getBoundingClientRect() : null;
      const firstSection = sections ? sections.querySelector('.o_nav_entry, a, button') : null;
      const firstSectionRect = firstSection ? firstSection.getBoundingClientRect() : null;
      const firstSectionText = firstSection ? firstSection.innerText.trim() : null;

      // Check bounding box collisions
      let brandCollidesWithSections = false;
      let overlapPx = 0;
      if (brandRect && firstSectionRect && brandVisible) {
        if (brandRect.right > firstSectionRect.left) {
          brandCollidesWithSections = true;
          overlapPx = brandRect.right - firstSectionRect.left;
        }
      }

      return {
        navHeight: navRect ? navRect.height : null,
        waffleClass,
        brandText,
        brandRect,
        logoRect,
        sepRect,
        firstSectionText,
        firstSectionRect,
        brandCollidesWithSections,
        overlapPx,
        navbarHtmlSnippet: navbar ? navbar.querySelector('.o_navbar_apps_menu, .o_menu_brand, .o_menu_sections')?.outerHTML : null
      };
    });

    console.log('Nav Audit Data:', JSON.stringify(navAudit, null, 2));

    if (navAudit.brandCollidesWithSections || navAudit.overlapPx > 0) {
      addFinding('CRITICAL', 'BUG-NAV-01', 'Navbar Brand Overlaps With Menu Sections',
        'The app brand title overlaps directly with the first section menu item due to layout CSS or redundant DOM rendering.',
        navAudit
      );
    }

    if (!navAudit.waffleClass || !navAudit.waffleClass.includes('ph-duotone')) {
      addFinding('HIGH', 'BUG-ICON-01', 'Phosphor Waffle Icon Missing Duotone Variant',
        `Waffle icon has class "${navAudit.waffleClass}" instead of expected "ph-duotone ph-squares-four".`,
        { waffleClass: navAudit.waffleClass }
      );
    }

    if (navAudit.navHeight !== 48) {
      addFinding('HIGH', 'BUG-NAV-02', 'ShellBar Height Not 48px',
        `ShellBar height measured ${navAudit.navHeight}px instead of 48px.`,
        { height: navAudit.navHeight }
      );
    }

    await page.screenshot({ path: path.join(OUT_DIR, '01_adv_shellbar.png') });

    // =========================================================================
    // TEST 2: Live Status Indicator Reactivity to Connection State
    // =========================================================================
    console.log('\n>>> [TEST 2] Live Status Indicator Reactivity...');
    const liveDotAudit = await page.evaluate(() => {
      const chip = document.querySelector('.o_switch_company_menu');
      const dot = chip ? chip.querySelector('.o_live_status_dot') : null;
      const dotStyle = dot ? window.getComputedStyle(dot) : null;

      const dotClassInitial = dot ? dot.className : null;
      const dotBgInitial = dotStyle ? dotStyle.backgroundColor : null;

      // Simulate offline via OfflinePlugin or DOM dispatch
      // Check if dot has classes
      return {
        hasChip: !!chip,
        hasDot: !!dot,
        dotClassInitial,
        dotBgInitial
      };
    });

    console.log('Live Dot Initial:', JSON.stringify(liveDotAudit, null, 2));

    // Now simulate offline network condition in browser context
    await context.setOffline(true);
    await page.evaluate(() => {
      window.dispatchEvent(new Event('offline'));
    });
    await page.waitForTimeout(1000);

    const liveDotOffline = await page.evaluate(() => {
      const dot = document.querySelector('.o_switch_company_menu .o_live_status_dot');
      const dotStyle = dot ? window.getComputedStyle(dot) : null;
      return {
        dotClassOffline: dot ? dot.className : null,
        dotBgOffline: dotStyle ? dotStyle.backgroundColor : null,
        isOfflineClass: dot ? dot.classList.contains('o_status_offline') : false
      };
    });
    console.log('Live Dot Offline:', JSON.stringify(liveDotOffline, null, 2));

    // Restore online
    await context.setOffline(false);
    await page.evaluate(() => {
      window.dispatchEvent(new Event('online'));
    });
    await page.waitForTimeout(1000);

    const liveDotOnlineAgain = await page.evaluate(() => {
      const dot = document.querySelector('.o_switch_company_menu .o_live_status_dot');
      const dotStyle = dot ? window.getComputedStyle(dot) : null;
      return {
        dotClassOnline: dot ? dot.className : null,
        dotBgOnline: dotStyle ? dotStyle.backgroundColor : null,
        isLiveClass: dot ? dot.classList.contains('o_status_live') : false
      };
    });
    console.log('Live Dot Online Again:', JSON.stringify(liveDotOnlineAgain, null, 2));

    if (!liveDotAudit.hasDot) {
      addFinding('HIGH', 'BUG-STAT-01', 'Live Status Indicator Dot DOM Element Missing',
        'No .o_live_status_dot element found inside .o_switch_company_menu.',
        liveDotAudit
      );
    } else if (!liveDotOffline.isOfflineClass) {
      addFinding('MEDIUM', 'BUG-STAT-02', 'Live Status Dot Does Not React to Offline Event',
        'When network transitions to offline, .o_status_offline was not applied to .o_live_status_dot.',
        { liveDotInitial: liveDotAudit, liveDotOffline }
      );
    }

    // =========================================================================
    // TEST 3: Floating Action Bar Existence & Behavior in ListView
    // =========================================================================
    console.log('\n>>> [TEST 3] Floating Action Bar Existence & Interactivity...');
    await page.goto('http://localhost:28069/insilos/purchase', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_list_table', { timeout: 15000 });
    await page.waitForTimeout(2000);

    // Initial state: 0 rows selected
    const fabInitial = await page.evaluate(() => {
      const bar = document.querySelector('.o_floating_batch_action_bar');
      return {
        barExistsInitial: !!bar,
        barVisibleInitial: bar ? window.getComputedStyle(bar).display !== 'none' : false
      };
    });

    // Select row 1
    const firstCheckbox = page.locator('.o_list_table tbody tr.o_data_row .o_list_record_selector input').first();
    await firstCheckbox.click();
    await page.waitForTimeout(1000);

    const fabSelected1 = await page.evaluate(() => {
      const bar = document.querySelector('.o_floating_batch_action_bar');
      const barRect = bar ? bar.getBoundingClientRect() : null;
      const barStyle = bar ? window.getComputedStyle(bar) : null;
      const countEl = bar ? bar.querySelector('.o_selected_count') : null;
      const countText = countEl ? countEl.innerText.trim() : null;

      const approveBtn = bar ? bar.querySelector('.btn-primary') : null;
      const exportBtn = bar ? bar.querySelector('.ph-download-simple') : null;
      const discardBtn = bar ? bar.querySelector('.ph-x') : null;

      return {
        barExists: !!bar,
        barRect: barRect ? { top: barRect.top, left: barRect.left, bottom: barRect.bottom, width: barRect.width, height: barRect.height } : null,
        position: barStyle ? barStyle.position : null,
        display: barStyle ? barStyle.display : null,
        zIndex: barStyle ? barStyle.zIndex : null,
        countText,
        hasApprove: !!approveBtn,
        hasExport: !!exportBtn,
        hasDiscard: !!discardBtn,
        windowHeight: window.innerHeight
      };
    });

    console.log('FAB Selected 1:', JSON.stringify(fabSelected1, null, 2));
    await page.screenshot({ path: path.join(OUT_DIR, '02_adv_fab_selected.png') });

    if (!fabSelected1.barExists) {
      addFinding('CRITICAL', 'BUG-FAB-01', 'Contextual Floating Action Bar Missing When Rows Selected',
        'When rows in ListView are selected, .o_floating_batch_action_bar is not mounted in the DOM.',
        { fabInitial, fabSelected1 }
      );
    } else {
      // Check if position is fixed at bottom
      const isFixedAtBottom = fabSelected1.position === 'fixed' && fabSelected1.barRect.bottom <= (fabSelected1.windowHeight + 10);
      if (!isFixedAtBottom) {
        addFinding('HIGH', 'BUG-FAB-02', 'Floating Action Bar Not Fixed at Viewport Bottom',
          `Floating action bar has position ${fabSelected1.position} and rect bottom ${fabSelected1.barRect?.bottom} vs window ${fabSelected1.windowHeight}.`,
          fabSelected1
        );
      }

      // Now deselect row
      await firstCheckbox.click();
      await page.waitForTimeout(800);

      const fabDeselected = await page.evaluate(() => {
        const bar = document.querySelector('.o_floating_batch_action_bar');
        return {
          barExistsAfterDeselect: !!bar,
          barVisible: bar ? window.getComputedStyle(bar).display !== 'none' : false
        };
      });

      console.log('FAB Deselected:', JSON.stringify(fabDeselected, null, 2));

      if (fabDeselected.barExistsAfterDeselect && fabDeselected.barVisible) {
        addFinding('HIGH', 'BUG-FAB-03', 'Floating Action Bar Does Not Disappear on Deselect',
          'Floating action bar remains mounted and visible after deselecting all rows.',
          fabDeselected
        );
      }
    }

    // =========================================================================
    // TEST 4: Table Row Height (34px) Across All Rows & Data Views
    // =========================================================================
    console.log('\n>>> [TEST 4] Comprehensive Table Row Height Stress Test...');
    // Audit purchase rows
    const purchaseRowsHeight = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('.o_list_table tbody tr.o_data_row'));
      return rows.map((r, i) => {
        const h = Math.round(r.getBoundingClientRect().height);
        const cells = Array.from(r.querySelectorAll('td')).map(td => Math.round(td.getBoundingClientRect().height));
        return { index: i, height: h, cellHeights: cells };
      });
    });

    const non34PurchaseRows = purchaseRowsHeight.filter(r => r.height !== 34);
    console.log(`Purchase rows total: ${purchaseRowsHeight.length}, non-34px count: ${non34PurchaseRows.length}`);

    // Audit contacts rows (different content: badges, avatars, text)
    await page.goto('http://localhost:28069/insilos/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_list_table', { timeout: 15000 });
    await page.waitForTimeout(2000);

    const contactRowsHeight = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('.o_list_table tbody tr.o_data_row'));
      return rows.map((r, i) => {
        const h = Math.round(r.getBoundingClientRect().height);
        const cells = Array.from(r.querySelectorAll('td')).map(td => Math.round(td.getBoundingClientRect().height));
        const badge = r.querySelector('.badge, .o_tag');
        const badgeH = badge ? Math.round(badge.getBoundingClientRect().height) : null;
        return { index: i, height: h, badgeH, cellHeights: cells };
      });
    });

    const non34ContactRows = contactRowsHeight.filter(r => r.height !== 34);
    console.log(`Contact rows total: ${contactRowsHeight.length}, non-34px count: ${non34ContactRows.length}`);

    if (non34PurchaseRows.length > 0 || non34ContactRows.length > 0) {
      addFinding('HIGH', 'BUG-ROW-01', 'Table Row Height Not Exactly 34px',
        'Some data rows deviate from the required 34px height.',
        { non34PurchaseRows: non34PurchaseRows.slice(0, 5), non34ContactRows: non34ContactRows.slice(0, 5) }
      );
    }

    // =========================================================================
    // TEST 5: Chevron Statusbar Interlocking Geometry & Active Accent
    // =========================================================================
    console.log('\n>>> [TEST 5] Chevron Statusbar Interlocking Geometry...');
    await page.goto('http://localhost:28069/insilos/purchase', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_list_table', { timeout: 15000 });
    await page.waitForTimeout(2000);
    const row = page.locator('.o_data_row').first();
    await row.click();
    await page.waitForSelector('.o_form_view', { timeout: 15000 });
    await page.waitForTimeout(1500);

    const chevronAudit = await page.evaluate(() => {
      const statusRibbon = document.querySelector('.o_statusbar_status');
      if (!statusRibbon) return { error: 'No status ribbon found' };

      const buttons = Array.from(statusRibbon.querySelectorAll('.btn'));
      const btnData = buttons.map(b => {
        const style = window.getComputedStyle(b);
        const rect = b.getBoundingClientRect();
        return {
          text: b.innerText.trim(),
          className: b.className,
          clipPath: style.clipPath,
          marginLeft: style.marginLeft,
          marginRight: style.marginRight,
          zIndex: style.zIndex,
          bg: style.backgroundColor,
          color: style.color,
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          left: Math.round(rect.left),
          right: Math.round(rect.right)
        };
      });

      // Check if buttons visually overlap / nest
      let hasOverlap = false;
      for (let i = 0; i < btnData.length - 1; i++) {
        // If row-reverse, earlier DOM element appears to the right
        // Check if there is negative margin or polygon clipPath
      }

      return {
        ribbonDisplay: window.getComputedStyle(statusRibbon).display,
        ribbonFlexFlow: window.getComputedStyle(statusRibbon).flexFlow,
        buttonsCount: buttons.length,
        btnData
      };
    });

    console.log('Chevron Audit Data:', JSON.stringify(chevronAudit, null, 2));

    const visibleButtons = (chevronAudit.btnData || []).filter(b => b.width > 0 && !b.className.includes('d-none'));
    const allButtonsHaveClipPath = visibleButtons.length > 0 &&
      visibleButtons.every(b => b.clipPath && b.clipPath !== 'none');

    if (!allButtonsHaveClipPath) {
      addFinding('HIGH', 'BUG-CHEV-01', 'Statusbar Buttons Lack Interlocking Polygon ClipPath',
        'Statusbar buttons do not have valid polygon clip-paths applied.',
        chevronAudit
      );
    }

    // =========================================================================
    // TEST 6: Carbon Content Tabs 3px Bottom Indicator & Interactivity
    // =========================================================================
    console.log('\n>>> [TEST 6] Carbon Content Tabs 3px Indicator & Tab Switching...');
    const tabsAudit = await page.evaluate(async () => {
      const navTabs = document.querySelector('.o_notebook .nav-tabs');
      if (!navTabs) return { error: 'No nav-tabs found' };

      const tabLinks = Array.from(navTabs.querySelectorAll('.nav-link'));
      const initialActive = tabLinks.find(t => t.classList.contains('active'));
      const activeStyle = initialActive ? window.getComputedStyle(initialActive) : null;
      const afterStyle = initialActive ? window.getComputedStyle(initialActive, '::after') : null;

      return {
        tabCount: tabLinks.length,
        initialActiveText: initialActive ? initialActive.innerText.trim() : null,
        tabBorderRadius: activeStyle ? activeStyle.borderRadius : null,
        tabHeight: initialActive ? Math.round(initialActive.getBoundingClientRect().height) : null,
        afterHeight: afterStyle ? afterStyle.height : null,
        afterBg: afterStyle ? afterStyle.backgroundColor : null,
        afterPosition: afterStyle ? afterStyle.position : null,
        afterBottom: afterStyle ? afterStyle.bottom : null
      };
    });

    console.log('Tabs Audit Data:', JSON.stringify(tabsAudit, null, 2));

    if (tabsAudit.afterHeight !== '3px') {
      addFinding('HIGH', 'BUG-TAB-01', 'Active Tab Indicator Line Is Not Flat 3px',
        `Active tab ::after indicator measured ${tabsAudit.afterHeight} instead of 3px.`,
        tabsAudit
      );
    }

    // Click Tab 2 (e.g. Other Info)
    const secondTab = page.locator('.o_notebook .nav-tabs .nav-link').nth(1);
    if (await secondTab.count() > 0) {
      await secondTab.click();
      await page.waitForTimeout(500);

      const tab2Audit = await page.evaluate(() => {
        const active = document.querySelector('.o_notebook .nav-tabs .nav-link.active');
        const afterStyle = active ? window.getComputedStyle(active, '::after') : null;
        return {
          tab2ActiveText: active ? active.innerText.trim() : null,
          tab2AfterHeight: afterStyle ? afterStyle.height : null
        };
      });
      console.log('Tab 2 Audit Data:', JSON.stringify(tab2Audit, null, 2));

      if (tab2Audit.tab2AfterHeight !== '3px') {
        addFinding('MEDIUM', 'BUG-TAB-02', 'Switched Tab Indicator Line Is Not Flat 3px',
          `After switching tab, active indicator measured ${tab2Audit.tab2AfterHeight} instead of 3px.`,
          tab2Audit
        );
      }
    }

    // =========================================================================
    // TEST 7: Dark Mode Contrast & Full Page Theme Uniformity
    // =========================================================================
    console.log('\n>>> [TEST 7] Dark Mode Tech Cyan & Full Page Theme Uniformity...');
    await page.evaluate(() => {
      document.body.classList.add('o_dark_mode');
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.setAttribute('data-bs-theme', 'dark');
    });
    await page.waitForTimeout(800);

    const darkModeAudit = await page.evaluate(() => {
      const bodyStyle = window.getComputedStyle(document.body);
      const bgCanvas = bodyStyle.backgroundColor;

      const activeStage = document.querySelector('.o_statusbar_status .o_arrow_button_current, .o_statusbar_status .btn-primary');
      const stageStyle = activeStage ? window.getComputedStyle(activeStage) : null;
      const stageBg = stageStyle ? stageStyle.backgroundColor : null;
      const stageText = stageStyle ? stageStyle.color : null;

      // Active tab
      const activeTab = document.querySelector('.o_notebook .nav-tabs .nav-link.active');
      const tabStyle = activeTab ? window.getComputedStyle(activeTab) : null;
      const tabAfter = activeTab ? window.getComputedStyle(activeTab, '::after') : null;
      const tabAfterBg = tabAfter ? tabAfter.backgroundColor : null;

      // Chatter inspect
      const chatter = document.querySelector('.o-mail-Chatter, .o_ChatterContainer');
      const chatterStyle = chatter ? window.getComputedStyle(chatter) : null;
      const chatterBg = chatterStyle ? chatterStyle.backgroundColor : null;

      return {
        bodyBg: bgCanvas,
        stageBg,
        stageText,
        tabTextColor: tabStyle ? tabStyle.color : null,
        tabAfterBg,
        chatterBg
      };
    });

    console.log('Dark Mode Audit Data:', JSON.stringify(darkModeAudit, null, 2));

    // Calculate contrast of active stage text against its background
    if (darkModeAudit.stageBg && darkModeAudit.stageText) {
      const bgRgb = parseRgb(darkModeAudit.stageBg);
      const textRgb = parseRgb(darkModeAudit.stageText);
      const contrast = getContrastRatio(bgRgb, textRgb);
      console.log(`Active stage contrast ratio: ${contrast.toFixed(2)}:1`);

      if (contrast < 7.0) {
        addFinding('HIGH', 'BUG-DARK-01', 'Active Stage Dark Mode Contrast Below 7:1 (WCAG AAA)',
          `Contrast ratio was ${contrast.toFixed(2)}:1 (< 7:1) between text ${darkModeAudit.stageText} and bg ${darkModeAudit.stageBg}.`,
          { contrast: contrast.toFixed(2), bg: darkModeAudit.stageBg, text: darkModeAudit.stageText }
        );
      }
    }

    // Check chatter background in dark mode
    if (darkModeAudit.chatterBg) {
      const chatterRgb = parseRgb(darkModeAudit.chatterBg);
      // Pure white is rgb(255, 255, 255)
      if (chatterRgb.r > 240 && chatterRgb.g > 240 && chatterRgb.b > 240) {
        addFinding('HIGH', 'BUG-DARK-02', 'Chatter Background Remains Stark White in Dark Mode',
          `Chatter background is ${darkModeAudit.chatterBg}, failing full dark theme integration.`,
          { chatterBg: darkModeAudit.chatterBg }
        );
      }
    }

    await page.screenshot({ path: path.join(OUT_DIR, '03_adv_dark_mode.png') });

    // Output all findings
    console.log('\n======================================================================');
    console.log(`ADVERSARIAL CHALLENGER AUDIT COMPLETE: ${findings.length} FINDINGS`);
    console.log('======================================================================\n');

    fs.writeFileSync(path.join(OUT_DIR, 'challenger_findings.json'), JSON.stringify(findings, null, 2));

  } finally {
    await browser.close();
  }
}

runAdversarialAudit().catch(err => {
  console.error('Fatal error during adversarial audit:', err);
  process.exit(1);
});
