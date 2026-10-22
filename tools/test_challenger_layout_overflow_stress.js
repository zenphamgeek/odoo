/**
 * CHALLENGER EMPIRICAL STRESS TEST SUITE: LAYOUT & OVERFLOW INTEGRITY
 * ===================================================================
 * Adversarial stress testing for:
 * 1. Responsive form layout & chatter rail behavior (<1440px vs >=1440px)
 *    - Main form sheet width >= 840px
 *    - Elimination of horizontal overflow on laptop viewports (1280px, 1366px)
 *    - Nested One2Many sub-table horizontal scrolling without page sprawl
 * 2. High-density data tables & frozen sticky columns in list views
 *    - Row heights strictly 34px (tolerance [32px-35px])
 *    - Frozen selector (left: 0, z-index: 3/5) & primary column (left: 44px, z-index: 2/4)
 *    - Stacking context under horizontal (800px) and vertical (400px) scroll
 *    - Tabular numbers and monetary right alignment
 * 3. Modal dialog wizards
 *    - Cure padding collapse: modal-body padding 20px 24px (even with .o_modal_no_body_padding)
 *    - Modal header 48px, modal footer 48px sticky
 *    - Modal buttons 32px height, 4px border-radius
 *    - Inner form sheet neutralization (0 padding, transparent bg, 0 double-carding)
 * 4. High-contrast Dark Mode compliance
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = path.join(__dirname, 'test_artifacts_layout_overflow');
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const CSS_PATH = path.join(ARTIFACTS_DIR, 'compiled_backend.css');
if (!fs.existsSync(CSS_PATH)) {
  console.error(`[FATAL] CSS file not found at ${CSS_PATH}`);
  process.exit(1);
}

const COMPILED_CSS = fs.readFileSync(CSS_PATH, 'utf-8');

// Color normalization helper
function normalizeColor(colorStr) {
  if (!colorStr) return '';
  colorStr = colorStr.trim().toLowerCase();
  if (colorStr.startsWith('#')) return colorStr;
  const rgbMatch = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (rgbMatch) {
    const r = parseInt(rgbMatch[1]).toString(16).padStart(2, '0');
    const g = parseInt(rgbMatch[2]).toString(16).padStart(2, '0');
    const b = parseInt(rgbMatch[3]).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
  }
  return colorStr;
}

async function runEmpiricalStressChallenge() {
  console.log('========================================================================');
  console.log('CHALLENGER EMPIRICAL TEST HARNESS: LAYOUT & OVERFLOW STRESS TEST');
  console.log('IBM Carbon 11 & SAP Fiori Horizon Compliance on Insilos Odoo 20');
  console.log('========================================================================\n');

  const report = {
    timestamp: new Date().toISOString(),
    tests: {},
    summary: { total: 0, passed: 0, failed: 0 }
  };

  function record(suite, name, passed, details) {
    report.summary.total++;
    if (passed) report.summary.passed++;
    else report.summary.failed++;
    if (!report.tests[suite]) report.tests[suite] = [];
    report.tests[suite].push({ name, passed, details });
    const icon = passed ? '✅ PASS' : '❌ FAIL';
    console.log(`  [${icon}] ${name}`);
    if (details) console.log(`         -> ${JSON.stringify(details)}`);
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Helper to load HTML with compiled CSS
  async function loadHtml(htmlContent, viewport = { width: 1440, height: 900 }) {
    await page.setViewportSize(viewport);
    const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stress Harness</title>
  <style>
    ${COMPILED_CSS}
  </style>
</head>
<body class="o_web_client">
  ${htmlContent}
</body>
</html>`;
    await page.setContent(fullHtml, { waitUntil: 'load' });
    await page.waitForTimeout(300);
  }

  // ==========================================================================
  // SUITE 1: Form View & Responsive Chatter Rail Layout (<1440px vs >=1440px)
  // ==========================================================================
  console.log('\n--- SUITE 1: Form View & Responsive Chatter Rail Layout (<1440px vs >=1440px) ---');

  const formViewHtml = `
  <div class="o_action_manager" style="width: 100%; height: 100vh;">
    <div class="o_form_view o_view_controller">
      <div class="o_form_statusbar">
        <div class="o_statusbar_buttons">
          <button class="btn btn-primary" type="button">Confirm</button>
          <button class="btn btn-secondary" type="button">Cancel</button>
        </div>
        <div class="o_statusbar_status o_field_widget o_readonly_modifier">
          <button class="btn o_arrow_button btn-secondary" disabled>Draft</button>
          <button class="btn o_arrow_button btn-primary" disabled>In Progress</button>
          <button class="btn o_arrow_button btn-secondary" disabled>Done</button>
        </div>
      </div>
      <div class="o_form_sheet_bg">
        <div class="o_form_sheet">
          <div class="o-form-buttonbox oe_button_box">
            <button class="btn oe_stat_button" type="button">
              <i class="o_button_icon fa fa-dollar"></i>
              <div class="o_field_widget o_stat_info">
                <span class="o_stat_value">450,000 $</span>
                <span class="o_stat_text">Total Revenue</span>
                <span class="o_kpi_trend positive">▲ +8.2%</span>
              </div>
            </button>
          </div>
          <div class="oe_title">
            <label class="o_form_label">Sales Order</label>
            <h1><input class="o_input" value="SO-2026-00429" readonly></h1>
          </div>
          <div class="o_group">
            <div class="o_inner_group">
              <div class="o_wrap_field">
                <label class="o_form_label">Customer</label>
                <div class="o_field_widget"><span>Acme Industrial Logistics Corp</span></div>
              </div>
            </div>
            <div class="o_inner_group">
              <div class="o_wrap_field">
                <label class="o_form_label">Payment Terms</label>
                <div class="o_field_widget"><span>Net 30 Days</span></div>
              </div>
            </div>
          </div>
          <div class="o_notebook">
            <ul class="nav nav-tabs">
              <li class="nav-item"><a class="nav-link active">Order Lines</a></li>
              <li class="nav-item"><a class="nav-link">Other Info</a></li>
            </ul>
            <div class="tab-content">
              <div class="tab-pane active">
                <div class="o_field_widget o_field_one2many">
                  <div class="o_list_renderer">
                    <table class="o_list_table">
                      <thead>
                        <tr>
                          <th style="min-width: 200px;">Product Name</th>
                          <th style="min-width: 120px;">Specification</th>
                          <th style="min-width: 80px;">Quantity</th>
                          <th style="min-width: 100px;">Unit Price</th>
                          <th style="min-width: 100px;">Taxes</th>
                          <th style="min-width: 120px;">Subtotal</th>
                          <th style="min-width: 150px;">Delivery Date</th>
                          <th style="min-width: 140px;">Warehouse</th>
                          <th style="min-width: 100px;">Route</th>
                          <th style="min-width: 120px;">Tracking Ref</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr class="o_data_row">
                          <td>Industrial CNC Milling Head SS400</td>
                          <td>Grade A Titanium Coating</td>
                          <td class="o_list_number">5.00</td>
                          <td class="o_monetary_cell">12,500.00 $</td>
                          <td>VAT 10%</td>
                          <td class="o_monetary_cell">62,500.00 $</td>
                          <td>2026-11-15</td>
                          <td>WH-Cát Lái-01</td>
                          <td>Direct Freight</td>
                          <td>TRK-98421034</td>
                        </tr>
                        <tr class="o_data_row">
                          <td>Hydraulic Precision Valve 24V</td>
                          <td>Pressure Rated 350 Bar</td>
                          <td class="o_list_number">20.00</td>
                          <td class="o_monetary_cell">850.00 $</td>
                          <td>VAT 10%</td>
                          <td class="o_monetary_cell">17,000.00 $</td>
                          <td>2026-11-15</td>
                          <td>WH-Cát Lái-01</td>
                          <td>Direct Freight</td>
                          <td>TRK-98421035</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="o-mail-Form-chatter o-aside">
        <div class="o-mail-Chatter-topbar">
          <div class="o-mail-Chatter-topbar-actions">
            <button class="btn btn-secondary btn-sm" type="button">Send message</button>
            <button class="btn btn-secondary btn-sm" type="button">Log note</button>
            <button class="btn btn-secondary btn-sm" type="button">Activities</button>
          </div>
        </div>
        <div class="o-mail-Chatter-content" style="padding: 16px;">
          <div class="o-mail-Message" style="margin-bottom: 12px; font-size: 13px;">
            <strong>System Automated Bot</strong>: Quotation generated successfully from CRM Opportunity.
          </div>
        </div>
      </div>
    </div>
  </div>`;

  const testViewports = [
    { width: 1920, height: 1080, name: '1920px Full HD Desktop', expectFlexDir: 'row', expectAsideWidthRange: [340, 440] },
    { width: 1600, height: 900,  name: '1600px High-Res Desktop', expectFlexDir: 'row', expectAsideWidthRange: [340, 440] },
    { width: 1440, height: 900,  name: '1440px Desktop Boundary', expectFlexDir: 'row', expectAsideWidthRange: [320, 440] },
    { width: 1439, height: 900,  name: '1439px Below Boundary Sub-Desktop', expectFlexDir: 'column', expectAsideWidth100: true },
    { width: 1366, height: 768,  name: '1366px Standard Laptop', expectFlexDir: 'column', expectAsideWidth100: true },
    { width: 1280, height: 800,  name: '1280px Compact 13" Laptop', expectFlexDir: 'column', expectAsideWidth100: true },
    { width: 1024, height: 768,  name: '1024px Tablet Landscape', expectFlexDir: 'column', expectAsideWidth100: true },
  ];

  for (const vp of testViewports) {
    await loadHtml(formViewHtml, { width: vp.width, height: vp.height });

    const metrics = await page.evaluate(() => {
      const formView = document.querySelector('.o_form_view');
      const formStyle = window.getComputedStyle(formView);
      const sheetBg = document.querySelector('.o_form_sheet_bg');
      const sheetBgStyle = window.getComputedStyle(sheetBg);
      const sheetBgRect = sheetBg.getBoundingClientRect();
      const sheet = document.querySelector('.o_form_sheet');
      const sheetStyle = window.getComputedStyle(sheet);
      const sheetRect = sheet.getBoundingClientRect();
      const aside = document.querySelector('.o-aside');
      const asideStyle = window.getComputedStyle(aside);
      const asideRect = aside.getBoundingClientRect();
      const subTable = document.querySelector('.o_list_renderer');
      const subTableRect = subTable ? subTable.getBoundingClientRect() : null;

      const bodyScrollWidth = document.body.scrollWidth;
      const bodyClientWidth = document.body.clientWidth;
      const docScrollWidth = document.documentElement.scrollWidth;
      const docClientWidth = document.documentElement.clientWidth;

      return {
        flexDirection: formStyle.flexDirection,
        sheetBg: {
          width: Math.round(sheetBgRect.width),
          minWidthCss: sheetBgStyle.minWidth,
          scrollWidth: sheetBg.scrollWidth,
          clientWidth: sheetBg.clientWidth,
          hasHorizontalScroll: sheetBg.scrollWidth > sheetBg.clientWidth + 2
        },
        sheet: {
          width: Math.round(sheetRect.width),
          minWidthCss: sheetStyle.minWidth,
          maxWidthCss: sheetStyle.maxWidth,
          left: Math.round(sheetRect.left),
          right: Math.round(sheetRect.right)
        },
        aside: {
          width: Math.round(asideRect.width),
          top: Math.round(asideRect.top),
          borderLeft: asideStyle.borderLeftWidth,
          borderTop: asideStyle.borderTopWidth
        },
        subTable: subTable ? {
          width: Math.round(subTableRect.width),
          scrollWidth: subTable.scrollWidth,
          clientWidth: subTable.clientWidth,
          isScrollableInternally: subTable.scrollWidth > subTable.clientWidth
        } : null,
        viewportOverflow: {
          hasBodyOverflow: bodyScrollWidth > bodyClientWidth,
          hasDocOverflow: docScrollWidth > docClientWidth,
          bodyScrollWidth,
          bodyClientWidth,
          docScrollWidth,
          docClientWidth
        }
      };
    });

    const screenshotPath = path.join(ARTIFACTS_DIR, `form_layout_${vp.width}px.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });

    // 1. Check flex direction
    const isFlexDirCorrect = metrics.flexDirection === vp.expectFlexDir;
    record('responsive_form', `${vp.name}: flex-direction == '${vp.expectFlexDir}'`, isFlexDirCorrect, {
      expected: vp.expectFlexDir,
      actual: metrics.flexDirection
    });

    // 2. Check sheet width >= 840px
    const isSheetWidthValid = metrics.sheet.width >= 840;
    record('responsive_form', `${vp.name}: .o_form_sheet width >= 840px (actual: ${metrics.sheet.width}px)`, isSheetWidthValid, {
      width: metrics.sheet.width,
      minWidthCss: metrics.sheet.minWidthCss,
      maxWidthCss: metrics.sheet.maxWidthCss
    });

    // 3. Check zero page-level horizontal overflow
    const hasNoPageOverflow = !metrics.viewportOverflow.hasBodyOverflow && !metrics.viewportOverflow.hasDocOverflow;
    record('responsive_form', `${vp.name}: Zero viewport horizontal overflow (scrollWidth <= clientWidth)`, hasNoPageOverflow, {
      docScrollWidth: metrics.viewportOverflow.docScrollWidth,
      docClientWidth: metrics.viewportOverflow.docClientWidth
    });

    // 4. Check aside behavior
    if (vp.expectAsideWidthRange) {
      const isAsideInRange = metrics.aside.width >= vp.expectAsideWidthRange[0] && metrics.aside.width <= vp.expectAsideWidthRange[1];
      record('responsive_form', `${vp.name}: .o-aside width between ${vp.expectAsideWidthRange[0]}px and ${vp.expectAsideWidthRange[1]}px`, isAsideInRange, {
        actualWidth: `${metrics.aside.width}px`
      });
    } else if (vp.expectAsideWidth100) {
      // In column layout, aside width should equal sheetBg width (~ viewport width)
      const isAsideFullWidth = Math.abs(metrics.aside.width - vp.width) <= 20; // accounting for vertical scrollbar
      record('responsive_form', `${vp.name}: .o-aside collapses to full width underneath sheet`, isAsideFullWidth, {
        asideWidth: `${metrics.aside.width}px`,
        viewportWidth: `${vp.width}px`
      });
    }

    // 5. Check sub-table internal scrolling
    if (metrics.subTable) {
      const isSubTableContained = metrics.subTable.width <= metrics.sheet.width;
      record('responsive_form', `${vp.name}: One2Many sub-table contained within form sheet (width: ${metrics.subTable.width}px <= ${metrics.sheet.width}px)`, isSubTableContained, {
        subTableWidth: metrics.subTable.width,
        sheetWidth: metrics.sheet.width,
        isScrollableInternally: metrics.subTable.isScrollableInternally
      });
    }
  }

  // ==========================================================================
  // SUITE 2: High-Density List View & Frozen/Sticky Columns Stress Test
  // ==========================================================================
  console.log('\n--- SUITE 2: High-Density List View & Frozen/Sticky Columns Stress Test ---');

  // Generate 25 columns and 35 rows
  let thHeaders = `
    <th class="o_list_record_selector">
      <input type="checkbox" class="form-check-input" id="check_all">
    </th>
    <th class="o_column_sortable" style="min-width: 140px;">Reference #</th>
    <th class="o_column_sortable" style="min-width: 160px;">Customer Name</th>
    <th class="o_column_sortable" style="min-width: 120px;">Order Date</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 100px;">Units</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 120px;">Unit Price</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 140px;">Subtotal Net</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 120px;">Tax Amount</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 150px;">Grand Total</th>
    <th class="o_column_sortable" style="min-width: 110px;">Status</th>
    <th class="o_column_sortable" style="min-width: 130px;">Payment State</th>
    <th class="o_column_sortable" style="min-width: 140px;">Incoterms</th>
    <th class="o_column_sortable" style="min-width: 150px;">Shipping Method</th>
    <th class="o_column_sortable" style="min-width: 130px;">Warehouse ID</th>
    <th class="o_column_sortable" style="min-width: 120px;">Salesperson</th>
    <th class="o_column_sortable" style="min-width: 140px;">Branch Code</th>
    <th class="o_column_sortable" style="min-width: 120px;">Cost Center</th>
    <th class="o_column_sortable" style="min-width: 130px;">GL Account</th>
    <th class="o_column_sortable" style="min-width: 110px;">Currency</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 130px;">FX Rate</th>
    <th class="o_column_sortable o_list_number_th" style="min-width: 150px;">Total Local Cur</th>
    <th class="o_column_sortable" style="min-width: 140px;">Carrier Ref</th>
    <th class="o_column_sortable" style="min-width: 120px;">Vessel Name</th>
    <th class="o_column_sortable" style="min-width: 130px;">Port of Loading</th>
    <th class="o_column_sortable" style="min-width: 140px;">Port of Discharge</th>
  `;

  let trRows = '';
  for (let r = 1; r <= 35; r++) {
    trRows += `
      <tr class="o_data_row" data-id="${r}">
        <td class="o_list_record_selector">
          <input type="checkbox" class="form-check-input" id="check_${r}">
        </td>
        <td style="min-width: 140px;">SO-2026-${String(r).padStart(5, '0')}</td>
        <td style="min-width: 160px;">Enterprise Client #${r}</td>
        <td style="min-width: 120px;">2026-10-07</td>
        <td class="o_list_number" style="min-width: 100px;">${(r * 2.5).toFixed(2)}</td>
        <td class="o_monetary_cell" style="min-width: 120px;">1,250.00 $</td>
        <td class="o_monetary_cell" style="min-width: 140px;">${(r * 3125).toLocaleString('en-US')}.00 $</td>
        <td class="o_monetary_cell" style="min-width: 120px;">${(r * 312.5).toLocaleString('en-US')}.00 $</td>
        <td class="o_monetary_cell" style="min-width: 150px;">${(r * 3437.5).toLocaleString('en-US')}.00 $</td>
        <td style="min-width: 110px;"><span class="badge text-bg-success">Confirmed</span></td>
        <td style="min-width: 130px;"><span class="badge text-bg-info">Paid</span></td>
        <td style="min-width: 140px;">FOB Cát Lái</td>
        <td style="min-width: 150px;">Ocean Express Direct</td>
        <td style="min-width: 130px;">WH-SGN-01</td>
        <td style="min-width: 120px;">Alex Vance</td>
        <td style="min-width: 140px;">BR-SOUTH-001</td>
        <td style="min-width: 120px;">CC-OPS-77</td>
        <td style="min-width: 130px;">511000-REV</td>
        <td style="min-width: 110px;">USD</td>
        <td class="o_list_number" style="min-width: 130px;">25,450.00</td>
        <td class="o_monetary_cell" style="min-width: 150px;">${(r * 87484375).toLocaleString('en-US')} ₫</td>
        <td style="min-width: 140px;">MSKU-9988221</td>
        <td style="min-width: 120px;">Maersk Saigon</td>
        <td style="min-width: 130px;">VNCLT</td>
        <td style="min-width: 140px;">USLAX</td>
      </tr>
    `;
  }

  const listViewHtml = `
  <div class="o_action_manager o_list_view" style="width: 100%; height: 100vh; display: flex; flex-direction: column;">
    <div class="o_control_panel" style="min-height: 44px; height: 44px; display: flex; align-items: center; padding: 0 16px;">
      <div class="o_cp_top_left" style="display: flex; gap: 8px;">
        <button class="btn btn-primary" type="button">New</button>
      </div>
      <div class="o_cp_top_right" style="margin-left: auto;">
        <span class="o_pager_value">1-35 / 35</span>
      </div>
    </div>
    <div class="o_content" style="flex: 1 1 auto; overflow: hidden; display: flex; flex-direction: column;">
      <div class="o_list_renderer" style="flex: 1 1 auto; overflow: auto; position: relative;">
        <table class="o_list_table">
          <thead>
            <tr>${thHeaders}</tr>
          </thead>
          <tbody>
            ${trRows}
          </tbody>
        </table>
      </div>
    </div>
  </div>`;

  await loadHtml(listViewHtml, { width: 1440, height: 900 });

  // 2.1 Measure initial row heights and sticky attributes
  const listInitialMetrics = await page.evaluate(() => {
    const listTable = document.querySelector('.o_list_table');
    const thead = listTable.querySelector('thead');
    const theadStyle = window.getComputedStyle(thead);

    const rows = Array.from(listTable.querySelectorAll('tbody tr.o_data_row'));
    const rowHeights = rows.map(r => Math.round(r.getBoundingClientRect().height));

    const thSelector = thead.querySelector('th.o_list_record_selector');
    const thSelectorStyle = window.getComputedStyle(thSelector);
    const thSelectorRect = thSelector.getBoundingClientRect();

    const thPrimary = thead.querySelector('th.o_list_record_selector + th');
    const thPrimaryStyle = window.getComputedStyle(thPrimary);
    const thPrimaryRect = thPrimary.getBoundingClientRect();

    const firstRow = rows[0];
    const tdSelector = firstRow.querySelector('td.o_list_record_selector');
    const tdSelectorStyle = window.getComputedStyle(tdSelector);
    const tdSelectorRect = tdSelector.getBoundingClientRect();

    const tdPrimary = firstRow.querySelector('td.o_list_record_selector + td');
    const tdPrimaryStyle = window.getComputedStyle(tdPrimary);
    const tdPrimaryRect = tdPrimary.getBoundingClientRect();

    const numCell = firstRow.querySelector('.o_list_number');
    const numStyle = window.getComputedStyle(numCell);

    const monCell = firstRow.querySelector('.o_monetary_cell');
    const monStyle = window.getComputedStyle(monCell);

    return {
      theadSticky: theadStyle.position,
      theadTop: theadStyle.top,
      theadZIndex: theadStyle.zIndex,
      rowHeights,
      thSelector: {
        position: thSelectorStyle.position,
        left: thSelectorStyle.left,
        zIndex: thSelectorStyle.zIndex,
        width: Math.round(thSelectorRect.width),
        bg: thSelectorStyle.backgroundColor
      },
      thPrimary: {
        position: thPrimaryStyle.position,
        left: thPrimaryStyle.left,
        zIndex: thPrimaryStyle.zIndex,
        width: Math.round(thPrimaryRect.width),
        bg: thPrimaryStyle.backgroundColor
      },
      tdSelector: {
        position: tdSelectorStyle.position,
        left: tdSelectorStyle.left,
        zIndex: tdSelectorStyle.zIndex,
        width: Math.round(tdSelectorRect.width),
        bg: tdSelectorStyle.backgroundColor
      },
      tdPrimary: {
        position: tdPrimaryStyle.position,
        left: tdPrimaryStyle.left,
        zIndex: tdPrimaryStyle.zIndex,
        width: Math.round(tdPrimaryRect.width),
        bg: tdPrimaryStyle.backgroundColor
      },
      numericAlignment: {
        fontFamily: numStyle.fontFamily,
        fontVariantNumeric: numStyle.fontVariantNumeric,
        textAlign: numStyle.textAlign
      },
      monetaryAlignment: {
        fontFamily: monStyle.fontFamily,
        fontVariantNumeric: monStyle.fontVariantNumeric,
        textAlign: monStyle.textAlign
      }
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '01_list_initial_render.png'), fullPage: false });

  // Verify sticky thead
  const isTheadSticky = listInitialMetrics.theadSticky === 'sticky' && listInitialMetrics.theadTop === '0px';
  record('list_density_sticky', 'Table Header sticky top: 0', isTheadSticky, {
    position: listInitialMetrics.theadSticky,
    top: listInitialMetrics.theadTop,
    zIndex: listInitialMetrics.theadZIndex
  });

  // Verify compact 34px row heights (tolerance [32px, 35px])
  const avgRowHeight = Math.round(listInitialMetrics.rowHeights.reduce((a, b) => a + b, 0) / listInitialMetrics.rowHeights.length);
  const allRowsInTolerance = listInitialMetrics.rowHeights.every(h => h >= 32 && h <= 35);
  record('list_density_sticky', `Data Row Compact Height: target 34px (average: ${avgRowHeight}px, 35/35 rows in [32px-35px])`, allRowsInTolerance, {
    averageHeight: `${avgRowHeight}px`,
    sampleHeights: listInitialMetrics.rowHeights.slice(0, 5)
  });

  // Verify Header selector column (sticky, left: 0, z-index: 5, width: 44px)
  const isThSelectorValid = listInitialMetrics.thSelector.position === 'sticky' &&
                            listInitialMetrics.thSelector.left === '0px' &&
                            parseInt(listInitialMetrics.thSelector.zIndex) >= 5 &&
                            listInitialMetrics.thSelector.width === 44;
  record('list_density_sticky', 'Header Checkbox Selector: sticky, left: 0, width: 44px, z-index >= 5', isThSelectorValid, listInitialMetrics.thSelector);

  // Verify Header primary column (sticky, left: 44px, z-index >= 4)
  const isThPrimaryValid = listInitialMetrics.thPrimary.position === 'sticky' &&
                           listInitialMetrics.thPrimary.left === '44px' &&
                           parseInt(listInitialMetrics.thPrimary.zIndex) >= 4;
  record('list_density_sticky', 'Header Primary Column: sticky, left: 44px, z-index >= 4', isThPrimaryValid, listInitialMetrics.thPrimary);

  // Verify Body selector cell (sticky, left: 0, z-index: 3, width: 44px)
  const isTdSelectorValid = listInitialMetrics.tdSelector.position === 'sticky' &&
                            listInitialMetrics.tdSelector.left === '0px' &&
                            parseInt(listInitialMetrics.tdSelector.zIndex) >= 3 &&
                            listInitialMetrics.tdSelector.width === 44;
  record('list_density_sticky', 'Body Checkbox Selector: sticky, left: 0, width: 44px, z-index >= 3', isTdSelectorValid, listInitialMetrics.tdSelector);

  // Verify Body primary cell (sticky, left: 44px, z-index: 2)
  const isTdPrimaryValid = listInitialMetrics.tdPrimary.position === 'sticky' &&
                           listInitialMetrics.tdPrimary.left === '44px' &&
                           parseInt(listInitialMetrics.tdPrimary.zIndex) >= 2;
  record('list_density_sticky', 'Body Primary Column: sticky, left: 44px, z-index >= 2', isTdPrimaryValid, listInitialMetrics.tdPrimary);

  // Verify Tabular Monospace figures on numeric & monetary columns
  const isNumericValid = listInitialMetrics.numericAlignment.textAlign === 'right' &&
                         listInitialMetrics.numericAlignment.fontVariantNumeric.includes('tabular-nums');
  record('list_density_sticky', 'Numeric Cell: text-align: right, font-variant-numeric: tabular-nums', isNumericValid, listInitialMetrics.numericAlignment);

  const isMonetaryValid = listInitialMetrics.monetaryAlignment.textAlign === 'right' &&
                          listInitialMetrics.monetaryAlignment.fontVariantNumeric.includes('tabular-nums');
  record('list_density_sticky', 'Monetary Cell: text-align: right, font-variant-numeric: tabular-nums', isMonetaryValid, listInitialMetrics.monetaryAlignment);

  // 2.2 ADVERSARIAL HORIZONTAL SCROLL STRESS TEST (Scroll 800px right)
  console.log('\n  ... Executing Adversarial Horizontal Scroll Stress Test (800px right) ...');
  await page.evaluate(() => {
    const renderer = document.querySelector('.o_list_renderer');
    renderer.scrollLeft = 800;
  });
  await page.waitForTimeout(300);

  const horizontalScrollMetrics = await page.evaluate(() => {
    const renderer = document.querySelector('.o_list_renderer');
    const rendererRect = renderer.getBoundingClientRect();

    const thead = renderer.querySelector('thead');
    const thSelector = thead.querySelector('th.o_list_record_selector');
    const thSelectorRect = thSelector.getBoundingClientRect();
    const thPrimary = thead.querySelector('th.o_list_record_selector + th');
    const thPrimaryRect = thPrimary.getBoundingClientRect();

    const row = renderer.querySelector('tbody tr.o_data_row');
    const tdSelector = row.querySelector('td.o_list_record_selector');
    const tdSelectorRect = tdSelector.getBoundingClientRect();
    const tdPrimary = row.querySelector('td.o_list_record_selector + td');
    const tdPrimaryRect = tdPrimary.getBoundingClientRect();

    return {
      scrollLeft: renderer.scrollLeft,
      thSelectorDistFromLeft: Math.round(thSelectorRect.left - rendererRect.left),
      thPrimaryDistFromLeft: Math.round(thPrimaryRect.left - rendererRect.left),
      tdSelectorDistFromLeft: Math.round(tdSelectorRect.left - rendererRect.left),
      tdPrimaryDistFromLeft: Math.round(tdPrimaryRect.left - rendererRect.left),
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '02_list_horizontal_scrolled_800px.png'), fullPage: false });

  // Frozen column 1 must remain exactly at 0px from container left (within 1px container border)
  const isThSelectorPinned = Math.abs(horizontalScrollMetrics.thSelectorDistFromLeft) <= 1;
  const isTdSelectorPinned = Math.abs(horizontalScrollMetrics.tdSelectorDistFromLeft) <= 1;
  record('list_density_sticky', 'Horizontal Scroll: Checkbox Selector frozen at x = 0px', isThSelectorPinned && isTdSelectorPinned, {
    scrollLeft: horizontalScrollMetrics.scrollLeft,
    thDist: horizontalScrollMetrics.thSelectorDistFromLeft,
    tdDist: horizontalScrollMetrics.tdSelectorDistFromLeft
  });

  // Frozen column 2 must remain exactly at 44px from container left
  const isThPrimaryPinned = Math.abs(horizontalScrollMetrics.thPrimaryDistFromLeft - 44) <= 1;
  const isTdPrimaryPinned = Math.abs(horizontalScrollMetrics.tdPrimaryDistFromLeft - 44) <= 1;
  record('list_density_sticky', 'Horizontal Scroll: Primary Data Column frozen at x = 44px', isThPrimaryPinned && isTdPrimaryPinned, {
    scrollLeft: horizontalScrollMetrics.scrollLeft,
    thDist: horizontalScrollMetrics.thPrimaryDistFromLeft,
    tdDist: horizontalScrollMetrics.tdPrimaryDistFromLeft
  });

  // 2.3 ADVERSARIAL VERTICAL SCROLL STRESS TEST (Scroll 400px down)
  console.log('\n  ... Executing Adversarial Vertical Scroll Stress Test (400px down) ...');
  await page.evaluate(() => {
    const renderer = document.querySelector('.o_list_renderer');
    renderer.scrollTop = 400;
  });
  await page.waitForTimeout(300);

  const verticalScrollMetrics = await page.evaluate(() => {
    const renderer = document.querySelector('.o_list_renderer');
    const rendererRect = renderer.getBoundingClientRect();
    const thead = renderer.querySelector('thead');
    const theadRect = thead.getBoundingClientRect();
    const thSelector = thead.querySelector('th.o_list_record_selector');
    const thSelectorRect = thSelector.getBoundingClientRect();

    return {
      scrollTop: renderer.scrollTop,
      theadDistFromTop: Math.round(theadRect.top - rendererRect.top),
      thSelectorDistFromTop: Math.round(thSelectorRect.top - rendererRect.top),
      thSelectorDistFromLeft: Math.round(thSelectorRect.left - rendererRect.left)
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '03_list_both_scrolled_800px_400px.png'), fullPage: false });

  const isTheadPinnedVertically = Math.abs(verticalScrollMetrics.theadDistFromTop) <= 1;
  record('list_density_sticky', 'Vertical Scroll: Table Header frozen at y = 0px', isTheadPinnedVertically, {
    scrollTop: verticalScrollMetrics.scrollTop,
    theadDistFromTop: verticalScrollMetrics.theadDistFromTop
  });

  const isCornerCellPinnedBoth = Math.abs(verticalScrollMetrics.thSelectorDistFromTop) <= 1 && Math.abs(verticalScrollMetrics.thSelectorDistFromLeft) <= 1;
  record('list_density_sticky', 'Bidirectional Scroll: Corner Selector Cell anchored at (0, 0)', isCornerCellPinnedBoth, {
    scrollTop: verticalScrollMetrics.scrollTop,
    distTop: verticalScrollMetrics.thSelectorDistFromTop,
    distLeft: verticalScrollMetrics.thSelectorDistFromLeft
  });

  // ==========================================================================
  // SUITE 3: Modal Dialog Wizards (Padding Collapse & Action Buttons)
  // ==========================================================================
  console.log('\n--- SUITE 3: Modal Dialog Wizards (Padding Collapse & Action Buttons) ---');

  const dialogHtml = `
  <div class="o_dialog">
    <div class="modal d-block" tabindex="-1" role="dialog" style="background: rgba(0,0,0,0.5);">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Configure Material Requirements Planning (MRP)</h5>
            <button type="button" class="btn-close" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="o_form_view">
              <div class="o_form_sheet_bg">
                <div class="o_form_sheet">
                  <div class="o_group">
                    <div class="o_inner_group">
                      <div class="o_wrap_field">
                        <label class="o_form_label">Work Center Selection</label>
                        <div class="o_field_widget"><input class="o_input" value="CNC Laser Station #03"></div>
                      </div>
                    </div>
                    <div class="o_inner_group">
                      <div class="o_wrap_field">
                        <label class="o_form_label">Target Cycle Time (s)</label>
                        <div class="o_field_widget"><input class="o_input" value="45.5"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" type="button">Discard</button>
            <button class="btn btn-primary" type="button">Confirm Schedule</button>
          </div>
        </div>
      </div>
    </div>
  </div>`;

  await loadHtml(dialogHtml, { width: 1440, height: 900 });

  const dialogMetrics = await page.evaluate(() => {
    const modalContent = document.querySelector('.modal-content');
    const header = modalContent.querySelector('.modal-header');
    const headerRect = header.getBoundingClientRect();
    const headerStyle = window.getComputedStyle(header);

    const body = modalContent.querySelector('.modal-body');
    const bodyStyle = window.getComputedStyle(body);
    const bodyRect = body.getBoundingClientRect();

    const formSheetBg = body.querySelector('.o_form_sheet_bg');
    const formSheetBgStyle = formSheetBg ? window.getComputedStyle(formSheetBg) : null;

    const formSheet = body.querySelector('.o_form_sheet');
    const formSheetStyle = formSheet ? window.getComputedStyle(formSheet) : null;

    const footer = modalContent.querySelector('.modal-footer');
    const footerRect = footer.getBoundingClientRect();
    const footerStyle = window.getComputedStyle(footer);

    const primaryBtn = footer.querySelector('.btn-primary');
    const primaryBtnStyle = window.getComputedStyle(primaryBtn);
    const primaryBtnRect = primaryBtn.getBoundingClientRect();

    const secondaryBtn = footer.querySelector('.btn-secondary');
    const secondaryBtnStyle = window.getComputedStyle(secondaryBtn);
    const secondaryBtnRect = secondaryBtn.getBoundingClientRect();

    return {
      header: {
        height: Math.round(headerRect.height),
        cssHeight: headerStyle.height,
        minHeight: headerStyle.minHeight
      },
      body: {
        paddingTop: bodyStyle.paddingTop,
        paddingRight: bodyStyle.paddingRight,
        paddingBottom: bodyStyle.paddingBottom,
        paddingLeft: bodyStyle.paddingLeft,
        overflowY: bodyStyle.overflowY,
        overflowX: bodyStyle.overflowX,
      },
      formSheetBg: formSheetBgStyle ? {
        bg: formSheetBgStyle.backgroundColor,
        paddingTop: formSheetBgStyle.paddingTop,
        paddingBottom: formSheetBgStyle.paddingBottom
      } : null,
      formSheet: formSheetStyle ? {
        bg: formSheetStyle.backgroundColor,
        border: `${formSheetStyle.borderTopWidth} ${formSheetStyle.borderTopStyle}`,
        boxShadow: formSheetStyle.boxShadow,
        padding: `${formSheetStyle.paddingTop} ${formSheetStyle.paddingRight}`
      } : null,
      footer: {
        height: Math.round(footerRect.height),
        cssHeight: footerStyle.height,
        minHeight: footerStyle.minHeight,
        position: footerStyle.position,
        bottom: footerStyle.bottom,
        zIndex: footerStyle.zIndex
      },
      primaryBtn: {
        height: Math.round(primaryBtnRect.height),
        borderRadius: primaryBtnStyle.borderRadius,
        fontSize: primaryBtnStyle.fontSize,
        bg: primaryBtnStyle.backgroundColor
      },
      secondaryBtn: {
        height: Math.round(secondaryBtnRect.height),
        borderRadius: secondaryBtnStyle.borderRadius,
        fontSize: secondaryBtnStyle.fontSize,
        bg: secondaryBtnStyle.backgroundColor
      }
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '04_modal_dialog_standard.png'), fullPage: false });

  // 3.1 Modal Header Standard (48px)
  const isHeader48 = dialogMetrics.header.height === 48;
  record('modal_dialog', 'Modal Header height strictly 48px', isHeader48, dialogMetrics.header);

  // 3.2 Modal Body Padding Standard (20px top/bottom, 24px left/right)
  const isBodyPaddingValid = dialogMetrics.body.paddingTop === '20px' &&
                             dialogMetrics.body.paddingBottom === '20px' &&
                             dialogMetrics.body.paddingLeft === '24px' &&
                             dialogMetrics.body.paddingRight === '24px';
  record('modal_dialog', 'Modal Body padding strictly 20px 24px (neutralizes padding collapse)', isBodyPaddingValid, dialogMetrics.body);

  // 3.3 Modal Body Overflow Rules (overflow-y: auto, overflow-x: hidden)
  const isBodyOverflowValid = dialogMetrics.body.overflowY === 'auto' && dialogMetrics.body.overflowX === 'hidden';
  record('modal_dialog', 'Modal Body overflow rules: overflow-y: auto, overflow-x: hidden', isBodyOverflowValid, {
    overflowY: dialogMetrics.body.overflowY,
    overflowX: dialogMetrics.body.overflowX
  });

  // 3.4 Inner Form Sheet Neutralization (transparent bg, padding 0, border none)
  const isInnerSheetNeutralized = (dialogMetrics.formSheetBg?.bg === 'rgba(0, 0, 0, 0)' || dialogMetrics.formSheetBg?.bg === 'transparent') &&
                                 (dialogMetrics.formSheet?.bg === 'rgba(0, 0, 0, 0)' || dialogMetrics.formSheet?.bg === 'transparent') &&
                                 dialogMetrics.formSheet?.padding === '0px 0px';
  record('modal_dialog', 'Inner form sheet neutralized in dialog (transparent, 0 padding, 0 double carding)', isInnerSheetNeutralized, {
    sheetBgColor: dialogMetrics.formSheetBg?.bg,
    sheetColor: dialogMetrics.formSheet?.bg,
    sheetPadding: dialogMetrics.formSheet?.padding
  });

  // 3.5 Modal Footer Standard (48px sticky footer, bottom: 0, z-index 10)
  const isFooter48Sticky = dialogMetrics.footer.height === 48 &&
                           dialogMetrics.footer.position === 'sticky' &&
                           dialogMetrics.footer.bottom === '0px';
  record('modal_dialog', 'Modal Footer height 48px, position: sticky bottom: 0', isFooter48Sticky, dialogMetrics.footer);

  // 3.6 Modal Action Buttons (32px height, 4px border-radius)
  const isPrimaryBtnValid = dialogMetrics.primaryBtn.height === 32 && dialogMetrics.primaryBtn.borderRadius === '4px';
  record('modal_dialog', 'Modal Primary Button: 32px height, 4px radius (Carbon 11 standard)', isPrimaryBtnValid, dialogMetrics.primaryBtn);

  const isSecondaryBtnValid = dialogMetrics.secondaryBtn.height === 32 && dialogMetrics.secondaryBtn.borderRadius === '4px';
  record('modal_dialog', 'Modal Secondary Button: 32px height, 4px radius', isSecondaryBtnValid, dialogMetrics.secondaryBtn);

  // 3.7 ADVERSARIAL STRESS TEST: Sheetless wizard with .o_modal_no_body_padding class
  console.log('\n  ... Executing Adversarial Test: .o_modal_no_body_padding override ...');
  const sheetlessWizardHtml = `
  <div class="o_dialog">
    <div class="modal o_modal_no_body_padding d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-md" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Database Backup</h5>
          </div>
          <div class="modal-body">
            <p>Do you want to initiate an immediate encrypted database snapshot?</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" type="button">Cancel</button>
            <button class="btn btn-primary" type="button">Backup Now</button>
          </div>
        </div>
      </div>
    </div>
  </div>`;

  await loadHtml(sheetlessWizardHtml, { width: 1440, height: 900 });

  const sheetlessMetrics = await page.evaluate(() => {
    const body = document.querySelector('.modal-body');
    const s = window.getComputedStyle(body);
    return {
      paddingTop: s.paddingTop,
      paddingBottom: s.paddingBottom,
      paddingLeft: s.paddingLeft,
      paddingRight: s.paddingRight
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '05_modal_no_body_padding_override.png'), fullPage: false });

  const isNoBodyPaddingCured = sheetlessMetrics.paddingTop === '20px' &&
                               sheetlessMetrics.paddingBottom === '20px' &&
                               sheetlessMetrics.paddingLeft === '24px' &&
                               sheetlessMetrics.paddingRight === '24px';
  record('modal_dialog', '.o_modal_no_body_padding cured: padding remains 20px 24px preventing collapse', isNoBodyPaddingCured, sheetlessMetrics);

  // ==========================================================================
  // SUITE 4: Dark Mode Theme Invariants
  // ==========================================================================
  console.log('\n--- SUITE 4: Dark Mode High-Contrast Verification ---');

  const darkModeHtml = `
  <div class="o_action_manager o_dark_mode" style="width: 100%; height: 100vh;">
    <div class="o_form_view">
      <div class="o_form_sheet_bg">
        <div class="o_form_sheet">
          <div class="oe_title">
            <label class="o_form_label">Manufacturing Order</label>
            <h1><input class="o_input" value="MO-2026-001" readonly></h1>
          </div>
        </div>
      </div>
    </div>
    <div class="o_dialog">
      <div class="modal d-block" tabindex="-1">
        <div class="modal-dialog modal-md">
          <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Dark Dialog</h5></div>
            <div class="modal-body"><p>Dark body text</p></div>
            <div class="modal-footer"><button class="btn btn-primary">Save</button></div>
          </div>
        </div>
      </div>
    </div>
  </div>`;

  await loadHtml(darkModeHtml, { width: 1440, height: 900 });
  // Add dark mode class to body as well
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  });
  await page.waitForTimeout(200);

  const darkModeMetrics = await page.evaluate(() => {
    const sheetBg = document.querySelector('.o_form_sheet_bg');
    const sheetBgStyle = window.getComputedStyle(sheetBg);
    const sheet = document.querySelector('.o_form_sheet');
    const sheetStyle = window.getComputedStyle(sheet);
    const modalContent = document.querySelector('.modal-content');
    const modalStyle = window.getComputedStyle(modalContent);

    return {
      sheetBg: sheetBgStyle.backgroundColor,
      sheet: sheetStyle.backgroundColor,
      modalContentBg: modalStyle.backgroundColor
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '06_dark_mode_compliance.png'), fullPage: false });

  const sheetBgDark = normalizeColor(darkModeMetrics.sheetBg);
  const sheetDark = normalizeColor(darkModeMetrics.sheet);
  const modalDark = normalizeColor(darkModeMetrics.modalContentBg);

  const isDarkModeValid = (sheetBgDark === '#070b14' || sheetBgDark === '#0f172a') &&
                          (sheetDark === '#141e33' || sheetDark === '#1e293b') &&
                          modalDark === '#141e33';
  record('dark_mode', 'Dark mode surfaces conform to IBM Carbon / Fiori Dark palette (#070B14 / #141E33)', isDarkModeValid, {
    sheetBg: sheetBgDark,
    sheet: sheetDark,
    modalContent: modalDark
  });

  await browser.close();

  // Save full JSON test report
  const reportPath = path.join(ARTIFACTS_DIR, 'challenger_stress_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');

  console.log('\n========================================================================');
  console.log(`STRESS TEST COMPLETE: ${report.summary.passed}/${report.summary.total} PASSED (${report.summary.failed} FAILED)`);
  console.log(`Detailed test report saved to: ${reportPath}`);
  console.log('========================================================================\n');

  if (report.summary.failed > 0) {
    process.exit(1);
  }
}

runEmpiricalStressChallenge().catch(err => {
  console.error('\n[FATAL] Error running empirical stress challenge:', err);
  process.exit(1);
});
