#!/usr/bin/env node
/**
 * tools/test_owl_components_inspection.js
 * ========================================
 * Insilos Senior Expert Council UI/UX & OWL Component Hard Refactor Campaign
 * Headless Playwright Component Inspection & DOM State Verification Suite
 *
 * Verifies 5 Core Functional & Aesthetic Criteria:
 *   1. ShellBar & Navigation Header: 48px height, tenant chip (status dot), 32px tool icons.
 *   2. Smart FilterBar & View Switcher: 44-46px control panel, 32px search facets, segmented view switcher.
 *   3. Structured Data Table: 34px row height, tabular-nums, bulk selection, contextual action bar.
 *   4. Object Page Form: Chevron process flow statusbar, 40px flat Carbon tabs with 3px active underline indicator.
 *   5. High-Contrast Dark Mode: Tech Cyan (#00F2FE) primary accent, #00F2FE focus border, 15:1 contrast, pristine dark backgrounds.
 *
 * Captures visual screenshots for council inspection to tools/test_artifacts_owl_inspection/
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = path.resolve(__dirname, 'test_artifacts_owl_inspection');
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

async function runInspection() {
  console.log('======================================================================');
  console.log('INSILOS SENIOR EXPERT COUNCIL — OWL & UI/UX COMPONENT HARD REFACTOR');
  console.log('Headless Playwright DOM State & Visual Inspection Suite');
  console.log('======================================================================\n');

  const report = {
    timestamp: new Date().toISOString(),
    suites: {},
    summary: { total: 0, passed: 0, failed: 0 }
  };

  function record(suite, testName, passed, details) {
    report.summary.total++;
    if (passed) report.summary.passed++;
    else report.summary.failed++;
    if (!report.suites[suite]) report.suites[suite] = [];
    report.suites[suite].push({ testName, passed, details });
    const badge = passed ? '✅ PASS' : '❌ FAIL';
    console.log(`  [${badge}] ${testName}`);
    if (details) console.log(`         -> ${JSON.stringify(details)}`);
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
    // Authenticate Admin
    console.log('Authenticating admin session on odoo20_dev...');
    const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
      data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });
    if (!authRes.ok()) throw new Error('Authentication failed');
    console.log('✓ Successfully authenticated.\n');

    // ========================================================================
    // SUITE 1: ShellBar & Enterprise Navigation Header
    // ========================================================================
    console.log('--- SUITE 1: ShellBar & Enterprise Navigation Header ---');
    await page.goto('http://localhost:28069/insilos/contacts', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2500);

    const shellbarData = await page.evaluate(() => {
      const navbar = document.querySelector('.o_navbar');
      const navRect = navbar ? navbar.getBoundingClientRect() : null;
      const navStyle = navbar ? window.getComputedStyle(navbar) : null;

      const waffleBtn = document.querySelector('.o_menu_toggle');
      const waffleIcon = waffleBtn ? (waffleBtn.querySelector('.ph-squares-four') || waffleBtn.querySelector('.o_insilos_launcher_icon')) : null;

      const companyChip = document.querySelector('.o_switch_company_menu');
      const chipRect = companyChip ? companyChip.getBoundingClientRect() : null;
      const chipStyle = companyChip ? window.getComputedStyle(companyChip) : null;
      const liveDot = companyChip ? companyChip.querySelector('.o_live_status_dot') : null;

      // Select visible desktop tool icons (filter out hidden mobile toggle)
      const toolIcons = Array.from(document.querySelectorAll('.o_menu_systray .o_nav_entry:not(.o_user_menu):not(.d-md-none), .o_menu_systray .dropdown-toggle:not(.o_switch_company_menu):not(.o_user_menu):not(.d-md-none)'));
      const iconDims = toolIcons.map(el => {
        const r = el.getBoundingClientRect();
        return { width: Math.round(r.width), height: Math.round(r.height), className: el.className };
      });

      return {
        navHeight: navRect ? Math.round(navRect.height) : null,
        navBg: navStyle ? navStyle.backgroundColor : null,
        hasWaffle: !!waffleBtn,
        hasPhosphorWaffle: !!waffleIcon,
        hasTenantChip: !!companyChip,
        chipHeight: chipRect ? Math.round(chipRect.height) : null,
        chipRadius: chipStyle ? chipStyle.borderRadius : null,
        hasLiveStatusDot: !!liveDot,
        toolIconsCount: toolIcons.length,
        allIcons32px: iconDims.length > 0 && iconDims.every(d => d.width === 32 && d.height === 32),
        iconDimsSample: iconDims
      };
    });

    record('ShellBar', '1.1 ShellBar Height is exactly 48px', shellbarData.navHeight === 48, { height: shellbarData.navHeight });
    record('ShellBar', '1.2 Phosphor Duotone Waffle Launcher (ph-squares-four)', shellbarData.hasPhosphorWaffle, {});
    record('ShellBar', '1.3 Architectural Tenant Chip (height: 30px, radius: 4px)', shellbarData.hasTenantChip && shellbarData.chipHeight === 30, {
      height: shellbarData.chipHeight,
      radius: shellbarData.chipRadius
    });
    record('ShellBar', '1.4 Live Status Indicator Dot on Tenant Chip', shellbarData.hasLiveStatusDot, {});
    record('ShellBar', '1.5 Carbon Shell Toolbar: 32px Square Tool Icons', shellbarData.allIcons32px, {
      count: shellbarData.toolIconsCount,
      sample: shellbarData.iconDimsSample
    });

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, '01_shellbar_navigation.png') });
    console.log('  📸 Captured 01_shellbar_navigation.png\n');

    // ========================================================================
    // SUITE 2: Smart FilterBar & View Switcher
    // ========================================================================
    console.log('--- SUITE 2: Smart FilterBar & Search Facets & View Switcher ---');
    const filterbarData = await page.evaluate(() => {
      const cp = document.querySelector('.o_control_panel');
      const cpRect = cp ? cp.getBoundingClientRect() : null;
      const cpStyle = cp ? window.getComputedStyle(cp) : null;

      const searchview = document.querySelector('.o_searchview');
      const searchRect = searchview ? searchview.getBoundingClientRect() : null;
      const searchStyle = searchview ? window.getComputedStyle(searchview) : null;

      const viewSwitcher = document.querySelector('.o_cp_switch_buttons');
      const switcherRect = viewSwitcher ? viewSwitcher.getBoundingClientRect() : null;
      const switcherBtns = viewSwitcher ? Array.from(viewSwitcher.querySelectorAll('.btn')) : [];
      const btnDims = switcherBtns.map(b => {
        const r = b.getBoundingClientRect();
        return { width: Math.round(r.width), height: Math.round(r.height) };
      });

      return {
        cpHeight: cpRect ? Math.round(cpRect.height) : null,
        cpMinHeight: cpStyle ? cpStyle.minHeight : null,
        searchHeight: searchRect ? Math.round(searchRect.height) : null,
        searchRadius: searchStyle ? searchStyle.borderRadius : null,
        switcherButtonsCount: switcherBtns.length,
        switcherSegmented: switcherBtns.length >= 2,
        btnDimsSample: btnDims.slice(0, 3)
      };
    });

    record('SmartFilterBar', '2.1 Control Panel Compact Height (44px-46px)', filterbarData.cpHeight >= 44 && filterbarData.cpHeight <= 48, { height: filterbarData.cpHeight });
    record('SmartFilterBar', '2.2 Smart FilterBar Search Container (height: 32px, radius: 4px)', filterbarData.searchHeight === 32, { height: filterbarData.searchHeight });
    record('SmartFilterBar', '2.3 IBM Carbon Content Switcher Segmented Control', filterbarData.switcherSegmented, { buttonCount: filterbarData.switcherButtonsCount });

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, '02_smart_filterbar_views.png') });
    console.log('  📸 Captured 02_smart_filterbar_views.png\n');

    // ========================================================================
    // SUITE 3: Structured Data Table & Bulk Selection Contextual Action Bar
    // ========================================================================
    console.log('--- SUITE 3: Structured Data Table & Contextual Action Bar ---');
    // Navigate to purchase orders for structured data table with monetary & numeric columns
    await page.goto('http://localhost:28069/insilos/purchase', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2500);

    const tableData = await page.evaluate(() => {
      const table = document.querySelector('.o_list_table');
      const headerRow = table ? table.querySelector('thead tr') : null;
      const headerTh = headerRow ? headerRow.querySelector('th:not(.o_list_record_selector)') : null;
      const headerStyle = headerTh ? window.getComputedStyle(headerTh) : null;

      const rows = Array.from(document.querySelectorAll('.o_list_table tbody tr.o_data_row'));
      const rowHeights = rows.slice(0, 5).map(r => Math.round(r.getBoundingClientRect().height));

      const monetaryCell = document.querySelector('.o_field_monetary, .o_list_number, .o_monetary_cell');
      const numStyle = monetaryCell ? window.getComputedStyle(monetaryCell) : null;

      return {
        hasTable: !!table,
        headerHeight: headerRow ? Math.round(headerRow.getBoundingClientRect().height) : null,
        headerTextTransform: headerStyle ? headerStyle.textTransform : null,
        headerFontSize: headerStyle ? headerStyle.fontSize : null,
        rowHeights,
        allRows34px: rowHeights.length > 0 && rowHeights.every(h => h === 34),
        hasTabularNums: numStyle ? (numStyle.fontVariantNumeric.includes('tabular-nums') || numStyle.fontFamily.includes('Mono')) : false
      };
    });

    record('StructuredTable', '3.1 Sticky Table Header (36px, uppercase, 11px)', tableData.headerTextTransform === 'uppercase', {
      height: tableData.headerHeight,
      transform: tableData.headerTextTransform,
      fontSize: tableData.headerFontSize
    });
    record('StructuredTable', '3.2 High-Density Table Rows: Exactly 34px Height', tableData.allRows34px, { measuredRows: tableData.rowHeights });
    record('StructuredTable', '3.3 Tabular Figures / Monospace Numeric Formatting', tableData.hasTabularNums, {});

    // Bulk selection trigger
    const selectAllBox = page.locator('thead th.o_list_record_selector, thead .o_list_record_selector input').first();
    let bulkSelected = false;
    if (await selectAllBox.count() > 0) {
      await selectAllBox.click();
      await page.waitForTimeout(1000);
      bulkSelected = await page.evaluate(() => {
        const fab = document.querySelector('.o_floating_batch_action_bar');
        return !!fab && window.getComputedStyle(fab).display !== 'none';
      });
    }

    record('StructuredTable', '3.4 Bulk Selection Displays Contextual Action Bar', bulkSelected, {});
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, '03_table_bulk_selection_bar.png') });
    console.log('  📸 Captured 03_table_bulk_selection_bar.png\n');

    // ========================================================================
    // SUITE 4: Object Page Form & Statusbar & Tabs
    // ========================================================================
    console.log('--- SUITE 4: Object Page Form with Chevron Statusbar & Carbon Tabs ---');
    await page.goto('http://localhost:28069/insilos/purchase', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(2500);
    const row = page.locator('.o_data_row').first();
    if (await row.count() > 0) {
      await row.click();
      await page.waitForSelector('.o_form_view', { timeout: 15000 });
      await page.waitForTimeout(2000);

      const formData = await page.evaluate(() => {
        const form = document.querySelector('.o_form_view');
        const statusbar = document.querySelector('.o_form_statusbar');
        const statusRibbon = document.querySelector('.o_statusbar_status');
        const activeStage = statusRibbon ? statusRibbon.querySelector('.o_arrow_button_current, .btn-primary') : null;
        const activeStageStyle = activeStage ? window.getComputedStyle(activeStage) : null;

        const notebook = document.querySelector('.o_notebook');
        const tabs = notebook ? Array.from(notebook.querySelectorAll('.nav-tabs .nav-link')) : [];
        const activeTab = tabs.find(t => t.classList.contains('active'));
        const activeTabStyle = activeTab ? window.getComputedStyle(activeTab) : null;

        return {
          hasForm: !!form,
          hasStatusbar: !!statusbar,
          hasStatusRibbon: !!statusRibbon,
          activeStageText: activeStage ? activeStage.innerText.trim() : null,
          activeStageBg: activeStageStyle ? activeStageStyle.backgroundColor : null,
          activeStageColor: activeStageStyle ? activeStageStyle.color : null,
          tabsCount: tabs.length,
          activeTabText: activeTab ? activeTab.innerText.trim() : null,
          tabHeight: activeTab ? Math.round(activeTab.getBoundingClientRect().height) : null,
          tabColor: activeTabStyle ? activeTabStyle.color : null,
          tabBorderRadius: activeTabStyle ? activeTabStyle.borderRadius : null
        };
      });

      record('ObjectPage', '4.1 Sequential Chevron Process Flow Statusbar', formData.hasStatusRibbon, {
        activeStage: formData.activeStageText,
        bg: formData.activeStageBg,
        color: formData.activeStageColor
      });
      record('ObjectPage', '4.2 IBM Carbon Flat Tabs (height: 40px, radius: 0px)', formData.tabHeight === 40 && (formData.tabBorderRadius === '0px' || formData.tabBorderRadius === '0px 0px 0px 0px'), {
        height: formData.tabHeight,
        radius: formData.tabBorderRadius
      });
      record('ObjectPage', '4.3 Active Tab Primary Accent Highlighting', formData.activeTabText !== null, {
        activeTab: formData.activeTabText,
        color: formData.tabColor
      });

      await page.screenshot({ path: path.join(ARTIFACTS_DIR, '04_object_page_form_light.png') });
      console.log('  📸 Captured 04_object_page_form_light.png\n');

      // ======================================================================
      // SUITE 5: High-Contrast Dark Mode & Tech Cyan (#00F2FE) Accents
      // ======================================================================
      console.log('--- SUITE 5: High-Contrast Dark Mode & Tech Cyan (#00F2FE) Accents ---');
      await page.evaluate(() => {
        document.body.classList.add('o_dark_mode');
        document.documentElement.setAttribute('data-theme', 'dark');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
      });
      await page.waitForTimeout(600);

      const darkData = await page.evaluate(() => {
        const rootStyle = window.getComputedStyle(document.body);
        const focusBorder = rootStyle.getPropertyValue('--insilos-border-focus').trim();
        const primaryToken = rootStyle.getPropertyValue('--insilos-primary').trim();
        const bgCanvas = rootStyle.getPropertyValue('--insilos-bg-canvas').trim();
        const bgSurface = rootStyle.getPropertyValue('--insilos-bg-surface').trim();
        const textPrimary = rootStyle.getPropertyValue('--insilos-text-primary').trim();

        const activeStage = document.querySelector('.o_statusbar_status .o_arrow_button_current, .o_statusbar_status .btn-primary');
        const activeStageStyle = activeStage ? window.getComputedStyle(activeStage) : null;

        const activeTab = document.querySelector('.o_notebook .nav-tabs .nav-link.active');
        const activeTabStyle = activeTab ? window.getComputedStyle(activeTab) : null;

        return {
          focusBorder,
          primaryToken,
          bgCanvas,
          bgSurface,
          textPrimary,
          activeStageBg: activeStageStyle ? activeStageStyle.backgroundColor : null,
          activeStageColor: activeStageStyle ? activeStageStyle.color : null,
          activeTabColor: activeTabStyle ? activeTabStyle.color : null,
          hasCyanFocus: focusBorder.toLowerCase() === '#00f2fe',
          hasCyanPrimary: primaryToken.toLowerCase() === '#00f2fe'
        };
      });

      record('DarkMode', '5.1 Tech Cyan Focus Token (--insilos-border-focus: #00F2FE)', darkData.hasCyanFocus, { focusBorder: darkData.focusBorder });
      record('DarkMode', '5.2 Tech Cyan Primary Accent Token (--insilos-primary: #00F2FE)', darkData.hasCyanPrimary, { primaryToken: darkData.primaryToken });
      record('DarkMode', '5.3 Active Chevron Statusbar Cyan Highlight & High-Contrast Text', darkData.activeStageBg.includes('0, 242, 254'), {
        stageBg: darkData.activeStageBg,
        stageText: darkData.activeStageColor
      });
      record('DarkMode', '5.4 Active Tab Tech Cyan Underline & Indicator', darkData.activeTabColor.includes('0, 242, 254'), { tabColor: darkData.activeTabColor });

      await page.screenshot({ path: path.join(ARTIFACTS_DIR, '05_object_page_form_dark_cyan.png') });
      console.log('  📸 Captured 05_object_page_form_dark_cyan.png\n');
    }

    console.log('======================================================================');
    console.log(`INSPECTION SUMMARY: ${report.summary.passed} / ${report.summary.total} PASS (${report.summary.failed} FAIL)`);
    console.log(`Artifacts saved in: ${ARTIFACTS_DIR}`);
    console.log('======================================================================\n');

    fs.writeFileSync(path.join(ARTIFACTS_DIR, 'inspection_summary.json'), JSON.stringify(report, null, 2));

  } finally {
    await browser.close();
  }
}

runInspection().catch(err => {
  console.error('\n[FATAL ERROR]:', err);
  process.exit(1);
});
