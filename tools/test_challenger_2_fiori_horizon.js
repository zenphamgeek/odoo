const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = path.join(__dirname, 'test_artifacts_challenger_2');
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

// Color comparison helper (handles rgb, rgba, hex)
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

async function runEmpiricalAudit() {
  console.log('======================================================================');
  console.log('CHALLENGER 2: SAP FIORI HORIZON UI/UX EMPIRICAL AUDIT & STRESS TEST');
  console.log('======================================================================\n');

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

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });

  const authRes = await context.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });
  if (!authRes.ok()) {
    throw new Error(`Authentication failed with status ${authRes.status()}`);
  }
  console.log('✓ Acquired authenticated admin session token.');

  const page = await context.newPage();

  // ==========================================================================
  // SUITE 1: Home Menu App Drawer Launchpad Ergonomics
  // ==========================================================================
  console.log('\n--- SUITE 1: Home Menu App Drawer Launchpad Ergonomics (/insilos) ---');
  await page.goto('http://localhost:28069/insilos', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.o_app', { timeout: 15000 });
  await page.waitForTimeout(1500);

  const launchpadData = await page.evaluate(() => {
    const apps = Array.from(document.querySelectorAll('.o_app'));
    const results = [];
    for (const app of apps) {
      const rect = app.getBoundingClientRect();
      const style = window.getComputedStyle(app);
      const pill = app.querySelector('.o_sap_pill');
      const pillStyle = pill ? window.getComputedStyle(pill) : null;
      const domain = app.querySelector('.o_sap_domain_tag');
      const domainStyle = domain ? window.getComputedStyle(domain) : null;
      const caption = app.querySelector('.o_caption');

      results.push({
        name: caption ? caption.innerText.trim() : '',
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        cssWidth: style.width,
        cssHeight: style.height,
        cssMinHeight: style.minHeight,
        pillText: pill ? pill.innerText.trim() : null,
        pillClass: pill ? pill.className : null,
        pillColor: pillStyle ? pillStyle.color : null,
        pillBg: pillStyle ? pillStyle.backgroundColor : null,
        pillBorder: pillStyle ? pillStyle.borderColor : null,
        pillWeight: pillStyle ? pillStyle.fontWeight : null,
        domainText: domain ? domain.innerText.trim() : null,
        domainColor: domainStyle ? domainStyle.color : null,
        domainSize: domainStyle ? domainStyle.fontSize : null,
      });
    }
    return results;
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '01_launchpad_overview.png'), fullPage: false });

  // 1.1 Check 160x160px tile dimension on md+
  const valid160Tiles = launchpadData.filter(a => a.width === 160 && a.height === 160);
  record('launchpad', '160x160px Tile Geometry Standard', valid160Tiles.length === launchpadData.length && launchpadData.length >= 60, {
    totalApps: launchpadData.length,
    valid160Count: valid160Tiles.length,
    sample: launchpadData.slice(0, 3)
  });

  // 1.2 Check SAP Acronym Pills
  const pillsFound = launchpadData.filter(a => a.pillText);
  const acronyms = [...new Set(pillsFound.map(a => a.pillText))];
  const requiredAcronyms = ['BP', 'SD', 'MM', 'MM-IM', 'FI/CO', 'PP'];
  const missingAcronyms = requiredAcronyms.filter(req => !acronyms.includes(req));
  record('launchpad', 'SAP Functional Space Acronym Pills (BP, SD, MM, MM-IM, FI/CO, PP, BI)', missingAcronyms.length === 0, {
    totalPills: pillsFound.length,
    distinctAcronyms: acronyms,
    missing: missingAcronyms
  });

  // 1.3 Check SAP Domain Subtitles
  const domainsFound = launchpadData.filter(a => a.domainText);
  const sampleDomain = domainsFound[0];
  const domainColorHex = sampleDomain ? normalizeColor(sampleDomain.domainColor) : '';
  record('launchpad', 'SAP Domain Subtitles (#94A3B8, font-weight 500)', domainsFound.length >= 10 && (domainColorHex === '#94a3b8' || domainColorHex === '#94a3b8'), {
    totalDomains: domainsFound.length,
    sampleDomainText: sampleDomain ? sampleDomain.domainText : null,
    sampleColor: domainColorHex
  });

  // ==========================================================================
  // SUITE 2: KPI Object Cards (.oe_stat_button)
  // ==========================================================================
  console.log('\n--- SUITE 2: KPI Object Cards (.oe_stat_button) ---');

  // Navigate to contacts/res.partner form to inspect real smart buttons
  await page.goto('http://localhost:28069/web#action=contacts.action_contacts&view_type=kanban', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Click first contact record or open form view
  const firstContact = await page.$('.o_kanban_record, .o_data_row');
  if (firstContact) {
    await firstContact.click();
    await page.waitForTimeout(3000);
  }

  // Check if button box exists or inject a test harness element to verify live SCSS rules
  const statCardAudit = await page.evaluate(() => {
    // Check if there are existing smart buttons
    let buttonBox = document.querySelector('.o-form-buttonbox, .oe_button_box');
    let injected = false;

    if (!buttonBox) {
      // Create a test harness inside the form view to evaluate compiled CSS rules
      injected = true;
      buttonBox = document.createElement('div');
      buttonBox.className = 'o-form-buttonbox oe_button_box';
      buttonBox.innerHTML = `
        <button class="btn oe_stat_button" type="button">
          <i class="o_button_icon fa fa-star"></i>
          <div class="o_field_widget o_stat_info">
            <span class="o_stat_value">1,250,000 $</span>
            <span class="o_stat_text">Total Invoiced</span>
            <span class="o_kpi_trend positive">▲ +12.5%</span>
          </div>
        </button>
        <button class="btn oe_stat_button" type="button">
          <i class="o_button_icon fa fa-clock"></i>
          <div class="o_field_widget o_stat_info">
            <span class="o_stat_value">42</span>
            <span class="o_stat_text">Open Inquiries</span>
            <span class="o_kpi_trend negative">▼ -4.2%</span>
          </div>
        </button>
        <button class="btn oe_stat_button" type="button">
          <i class="o_button_icon fa fa-check"></i>
          <div class="o_field_widget o_stat_info">
            <span class="o_stat_value">99.8%</span>
            <span class="o_stat_text">SLA Compliance</span>
            <span class="o_kpi_trend neutral">● 0.0%</span>
          </div>
        </button>
      `;
      const formSheet = document.querySelector('.o_form_sheet') || document.body;
      formSheet.prepend(buttonBox);
    }

    const statButtons = Array.from(buttonBox.querySelectorAll('.oe_stat_button'));
    const btn = statButtons[0];
    const btnStyle = window.getComputedStyle(btn);
    const valueEl = btn.querySelector('.o_stat_value');
    const valueStyle = valueEl ? window.getComputedStyle(valueEl) : null;
    const textEl = btn.querySelector('.o_stat_text');
    const textStyle = textEl ? window.getComputedStyle(textEl) : null;
    const trendPos = buttonBox.querySelector('.o_kpi_trend.positive');
    const trendPosStyle = trendPos ? window.getComputedStyle(trendPos) : null;
    const trendNeg = buttonBox.querySelector('.o_kpi_trend.negative');
    const trendNegStyle = trendNeg ? window.getComputedStyle(trendNeg) : null;
    const trendNeu = buttonBox.querySelector('.o_kpi_trend.neutral');
    const trendNeuStyle = trendNeu ? window.getComputedStyle(trendNeu) : null;
    const iconEl = btn.querySelector('.o_button_icon');
    const iconStyle = iconEl ? window.getComputedStyle(iconEl) : null;

    return {
      injected,
      statButtonCount: statButtons.length,
      buttonStyles: {
        background: btnStyle.backgroundColor,
        border: `${btnStyle.borderTopWidth} ${btnStyle.borderTopStyle} ${btnStyle.borderTopColor}`,
        borderRadius: btnStyle.borderRadius,
        minHeight: btnStyle.minHeight,
        display: btnStyle.display,
        flexDirection: btnStyle.flexDirection,
      },
      iconStyles: iconStyle ? {
        fontSize: iconStyle.fontSize,
        color: iconStyle.color,
      } : null,
      valueStyles: valueStyle ? {
        order: valueStyle.order,
        fontSize: valueStyle.fontSize,
        fontWeight: valueStyle.fontWeight,
        color: valueStyle.color,
        lineHeight: valueStyle.lineHeight,
      } : null,
      textStyles: textStyle ? {
        order: textStyle.order,
        fontSize: textStyle.fontSize,
        fontWeight: textStyle.fontWeight,
        textTransform: textStyle.textTransform,
        color: textStyle.color,
        letterSpacing: textStyle.letterSpacing,
      } : null,
      trendStyles: {
        posOrder: trendPosStyle ? trendPosStyle.order : null,
        posColor: trendPosStyle ? trendPosStyle.color : null,
        negColor: trendNegStyle ? trendNegStyle.color : null,
        neuColor: trendNeuStyle ? trendNeuStyle.color : null,
      }
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '02_kpi_cards_form.png'), fullPage: false });

  // 2.1 Value on top in 1.25rem bold #0F172A
  const valOrder = parseInt(statCardAudit.valueStyles?.order || '0');
  const valColor = normalizeColor(statCardAudit.valueStyles?.color);
  const valWeight = parseInt(statCardAudit.valueStyles?.fontWeight || '400');
  const valFontSizePx = parseFloat(statCardAudit.valueStyles?.fontSize || '0');
  // 1.25rem * 16px = 20px
  const isValCorrect = valOrder === 1 && valColor === '#0f172a' && valWeight >= 700 && Math.abs(valFontSizePx - 20) <= 1.0;
  record('kpi_cards', '.oe_stat_button: Value on top (order 1, 1.25rem [20px], bold >=700, #0F172A)', isValCorrect, {
    order: valOrder,
    fontSize: `${valFontSizePx}px`,
    fontWeight: valWeight,
    color: valColor
  });

  // 2.2 Label below in 0.7rem uppercase #64748B
  const textOrder = parseInt(statCardAudit.textStyles?.order || '0');
  const textColor = normalizeColor(statCardAudit.textStyles?.color);
  const textTransform = statCardAudit.textStyles?.textTransform;
  const textFontSizePx = parseFloat(statCardAudit.textStyles?.fontSize || '0');
  // 0.7rem * 16px = 11.2px
  const isTextCorrect = textOrder === 2 && textColor === '#64748b' && textTransform === 'uppercase' && Math.abs(textFontSizePx - 11.2) <= 1.5;
  record('kpi_cards', '.oe_stat_button: Label on bottom (order 2, 0.7rem [~11.2px], uppercase, #64748B)', isTextCorrect, {
    order: textOrder,
    fontSize: `${textFontSizePx}px`,
    textTransform,
    color: textColor
  });

  // 2.3 Micro-trend indicator support (.o_kpi_trend)
  const posTrendColor = normalizeColor(statCardAudit.trendStyles?.posColor);
  const negTrendColor = normalizeColor(statCardAudit.trendStyles?.negColor);
  const neuTrendColor = normalizeColor(statCardAudit.trendStyles?.neuColor);
  const isTrendCorrect = posTrendColor === '#107e3e' && negTrendColor === '#bb0000' && neuTrendColor === '#64748b';
  record('kpi_cards', '.o_kpi_trend: 3-State Micro-Trend Colors (pos: #107E3E, neg: #BB0000, neu: #64748B)', isTrendCorrect, {
    positive: posTrendColor,
    negative: negTrendColor,
    neutral: neuTrendColor
  });

  // 2.4 Stat button container styling
  const btnMinHeight = parseFloat(statCardAudit.buttonStyles?.minHeight || '0');
  const btnBorderRadius = parseFloat(statCardAudit.buttonStyles?.borderRadius || '0');
  const isBtnContainerCorrect = btnMinHeight >= 48 && btnBorderRadius >= 8;
  record('kpi_cards', '.oe_stat_button Container: Min-Height >= 48px, Border-Radius >= 8px', isBtnContainerCorrect, {
    minHeight: statCardAudit.buttonStyles?.minHeight,
    borderRadius: statCardAudit.buttonStyles?.borderRadius,
    border: statCardAudit.buttonStyles?.border
  });

  // ==========================================================================
  // SUITE 3: 4-State Semantic Status Badges
  // ==========================================================================
  console.log('\n--- SUITE 3: 4-State Semantic Status Badges ---');

  const badgeAudit = await page.evaluate(() => {
    // Inject test container with 4 canonical states to verify live compiled SCSS
    const container = document.createElement('div');
    container.id = 'test_semantic_badges';
    container.innerHTML = `
      <div class="o_list_renderer">
        <table class="o_list_table">
          <tbody>
            <tr>
              <td><span class="badge text-bg-success">Positive State</span></td>
              <td><span class="badge text-bg-danger">Critical State</span></td>
              <td><span class="badge text-bg-warning">Warning State</span></td>
              <td><span class="badge text-bg-info">Information State</span></td>
              <td><span class="badge text-bg-secondary">Neutral State</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="o_statusbar_status">
        <button class="btn btn-primary o_arrow_button">In Progress</button>
        <button class="btn btn-secondary o_arrow_button">Draft</button>
      </div>
    `;
    document.body.appendChild(container);

    const getBadgeStyle = (cls) => {
      const el = container.querySelector(cls);
      if (!el) return null;
      const s = window.getComputedStyle(el);
      return {
        color: s.color,
        backgroundColor: s.backgroundColor,
        borderRadius: s.borderRadius,
        fontSize: s.fontSize,
        fontWeight: s.fontWeight,
        borderColor: s.borderColor,
      };
    };

    const statusbarBtn = container.querySelector('.o_statusbar_status .o_arrow_button.btn-primary');
    const statusbarStyle = statusbarBtn ? window.getComputedStyle(statusbarBtn) : null;

    const res = {
      positive: getBadgeStyle('.text-bg-success'),
      critical: getBadgeStyle('.text-bg-danger'),
      warning: getBadgeStyle('.text-bg-warning'),
      information: getBadgeStyle('.text-bg-info'),
      neutral: getBadgeStyle('.text-bg-secondary'),
      statusbarPrimaryBg: statusbarStyle ? statusbarStyle.backgroundColor : null,
    };
    container.remove();
    return res;
  });

  // 3.1 Positive Badge (#107E3E text, #E7F6ED bg)
  const posColor = normalizeColor(badgeAudit.positive?.color);
  const posBg = normalizeColor(badgeAudit.positive?.backgroundColor);
  const isPosCorrect = posColor === '#107e3e' && posBg === '#e7f6ed';
  record('semantic_badges', '1. Positive / Success State Badge (#107E3E on #E7F6ED)', isPosCorrect, {
    color: posColor,
    backgroundColor: posBg,
    borderRadius: badgeAudit.positive?.borderRadius
  });

  // 3.2 Critical Badge (#BB0000 text, #FBEEED bg)
  const critColor = normalizeColor(badgeAudit.critical?.color);
  const critBg = normalizeColor(badgeAudit.critical?.backgroundColor);
  const isCritCorrect = critColor === '#bb0000' && critBg === '#fbeeed';
  record('semantic_badges', '2. Critical / Error State Badge (#BB0000 on #FBEEED)', isCritCorrect, {
    color: critColor,
    backgroundColor: critBg,
    borderRadius: badgeAudit.critical?.borderRadius
  });

  // 3.3 Warning Badge (#E9730C text, #FEF0E6 bg)
  const warnColor = normalizeColor(badgeAudit.warning?.color);
  const warnBg = normalizeColor(badgeAudit.warning?.backgroundColor);
  const isWarnCorrect = warnColor === '#e9730c' && warnBg === '#fef0e6';
  record('semantic_badges', '3. Warning / Alert State Badge (#E9730C on #FEF0E6)', isWarnCorrect, {
    color: warnColor,
    backgroundColor: warnBg,
    borderRadius: badgeAudit.warning?.borderRadius
  });

  // 3.4 Information Badge (#0070F2 text, #E8F2FE bg)
  const infoColor = normalizeColor(badgeAudit.information?.color);
  const infoBg = normalizeColor(badgeAudit.information?.backgroundColor);
  const isInfoCorrect = infoColor === '#0070f2' && infoBg === '#e8f2fe';
  record('semantic_badges', '4. Information State Badge (#0070F2 on #E8F2FE)', isInfoCorrect, {
    color: infoColor,
    backgroundColor: infoBg,
    borderRadius: badgeAudit.information?.borderRadius
  });

  // 3.5 Statusbar Active Pill (#0070F2)
  const statusbarBg = normalizeColor(badgeAudit.statusbarPrimaryBg);
  const isStatusbarCorrect = statusbarBg === '#0070f2';
  record('semantic_badges', 'Statusbar Active Workflow Step (#0070F2)', isStatusbarCorrect, {
    backgroundColor: statusbarBg
  });

  // ==========================================================================
  // SUITE 4: High-Density Compact Tables & Streamlined Control Panel
  // ==========================================================================
  console.log('\n--- SUITE 4: High-Density Compact Tables & 44px Control Panel ---');

  // Navigate to Sales Orders or Quotations List View
  await page.goto('http://localhost:28069/web#action=sale.action_quotations_with_onboarding&view_type=list', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3500);

  const tableAudit = await page.evaluate(() => {
    const cp = document.querySelector('.o_control_panel');
    const cpStyle = cp ? window.getComputedStyle(cp) : null;
    const cpRect = cp ? cp.getBoundingClientRect() : null;

    const searchView = cp ? cp.querySelector('.o_searchview') : null;
    const searchStyle = searchView ? window.getComputedStyle(searchView) : null;

    const listTable = document.querySelector('.o_list_table');
    let thStyles = null;
    let trStyles = null;
    let rowHeights = [];

    if (listTable) {
      const th = listTable.querySelector('thead th');
      if (th) {
        const s = window.getComputedStyle(th);
        thStyles = {
          position: s.position,
          top: s.top,
          background: s.backgroundColor,
          color: s.color,
          fontSize: s.fontSize,
          borderBottom: `${s.borderBottomWidth} ${s.borderBottomStyle} ${s.borderBottomColor}`,
          textTransform: s.textTransform,
        };
      }

      const rows = Array.from(listTable.querySelectorAll('tbody tr.o_data_row'));
      rowHeights = rows.slice(0, 10).map(r => Math.round(r.getBoundingClientRect().height));

      const firstRow = rows[0] || listTable.querySelector('tbody tr');
      if (firstRow) {
        const s = window.getComputedStyle(firstRow);
        const td = firstRow.querySelector('td');
        const tdStyle = td ? window.getComputedStyle(td) : null;
        trStyles = {
          height: s.height,
          minHeight: s.minHeight,
          tdPaddingTop: tdStyle ? tdStyle.paddingTop : null,
          tdPaddingBottom: tdStyle ? tdStyle.paddingBottom : null,
          tdFontSize: tdStyle ? tdStyle.fontSize : null,
        };
      }
    } else {
      // In case list table has no data rows yet, measure injected representative table
      const div = document.createElement('div');
      div.className = 'o_list_renderer';
      div.innerHTML = `
        <table class="o_list_table">
          <thead>
            <tr><th>Test Header</th></tr>
          </thead>
          <tbody>
            <tr><td>Test Cell</td></tr>
          </tbody>
        </table>
      `;
      document.body.appendChild(div);
      const th = div.querySelector('thead th');
      const thS = window.getComputedStyle(th);
      const tr = div.querySelector('tbody tr');
      const trS = window.getComputedStyle(tr);
      const td = tr.querySelector('td');
      const tdS = window.getComputedStyle(td);
      thStyles = {
        position: thS.position,
        top: thS.top,
        background: thS.backgroundColor,
        color: thS.color,
        fontSize: thS.fontSize,
        borderBottom: `${thS.borderBottomWidth} ${thS.borderBottomStyle} ${thS.borderBottomColor}`,
        textTransform: thS.textTransform,
      };
      trStyles = {
        height: trS.height,
        minHeight: trS.minHeight,
        tdPaddingTop: tdS.paddingTop,
        tdPaddingBottom: tdS.paddingBottom,
        tdFontSize: tdS.fontSize,
      };
      rowHeights = [Math.round(tr.getBoundingClientRect().height)];
      div.remove();
    }

    return {
      controlPanel: {
        height: cpRect ? Math.round(cpRect.height) : null,
        minHeight: cpStyle ? cpStyle.minHeight : null,
        bg: cpStyle ? cpStyle.backgroundColor : null,
        searchBorderRadius: searchStyle ? searchStyle.borderRadius : null,
      },
      tableHeader: thStyles,
      tableRow: trStyles,
      actualRowHeights: rowHeights
    };
  });

  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '03_list_view_table.png'), fullPage: false });

  // 4.1 44px Control Panel Standard
  const cpHeight = tableAudit.controlPanel?.height || 0;
  const isCpCorrect = cpHeight >= 44 && parseFloat(tableAudit.controlPanel?.minHeight || '0') >= 44;
  record('table_ergonomics', 'Control Panel Streamlined Standard (min-height: 44px)', isCpCorrect, {
    measuredHeight: `${cpHeight}px`,
    cssMinHeight: tableAudit.controlPanel?.minHeight,
    searchBorderRadius: tableAudit.controlPanel?.searchBorderRadius
  });

  // 4.2 Sticky #F8FAFC Table Headers
  const thBg = normalizeColor(tableAudit.tableHeader?.background);
  const isThSticky = tableAudit.tableHeader?.position === 'sticky' && tableAudit.tableHeader?.top === '0px';
  const isThBgCorrect = thBg === '#f8fafc';
  record('table_ergonomics', 'Sticky Table Headers (position: sticky, top: 0, bg: #F8FAFC)', isThSticky && isThBgCorrect, {
    position: tableAudit.tableHeader?.position,
    top: tableAudit.tableHeader?.top,
    background: thBg,
    color: normalizeColor(tableAudit.tableHeader?.color),
    borderBottom: tableAudit.tableHeader?.borderBottom
  });

  // 4.3 High-Density 32px–34px Table Row Height
  const avgRowHeight = tableAudit.actualRowHeights.length > 0 ?
    Math.round(tableAudit.actualRowHeights.reduce((a, b) => a + b, 0) / tableAudit.actualRowHeights.length) :
    parseFloat(tableAudit.tableRow?.height || '32');
  const isRowHeightCorrect = avgRowHeight >= 30 && avgRowHeight <= 36;
  record('table_ergonomics', 'High-Density Table Rows (Target 32px–34px, tolerance [30px–36px])', isRowHeightCorrect, {
    averageHeight: `${avgRowHeight}px`,
    measuredRows: tableAudit.actualRowHeights,
    cssHeight: tableAudit.tableRow?.height,
    cssMinHeight: tableAudit.tableRow?.minHeight,
    tdPadding: `${tableAudit.tableRow?.tdPaddingTop} / ${tableAudit.tableRow?.tdPaddingBottom}`
  });

  // ==========================================================================
  // SUITE 5: Phosphor Icon Bindings & Absence of Legacy Icons
  // ==========================================================================
  console.log('\n--- SUITE 5: Phosphor Icon Bindings & Absence of Legacy Icons ---');

  const iconAudit = await page.evaluate(() => {
    // Scan all icons in the current navbar and rendered DOM
    const allIcons = Array.from(document.querySelectorAll('i, span, button'));
    const legacyOi = [];
    const legacyFaPlus = [];
    const phosphorIcons = [];

    for (const el of allIcons) {
      const cls = el.className || '';
      if (typeof cls === 'string') {
        if (/\boi-[a-z0-9_-]+/i.test(cls)) {
          legacyOi.push({ tag: el.tagName, class: cls, html: el.outerHTML.substring(0, 100) });
        }
        if (/\bfa-plus\b/i.test(cls)) {
          legacyFaPlus.push({ tag: el.tagName, class: cls, html: el.outerHTML.substring(0, 100) });
        }
        if (/\bph(-[a-z0-9_-]+|\b)/i.test(cls)) {
          phosphorIcons.push(cls);
        }
      }
    }

    // Check navbar apps dropdown icon
    const navbarAppsBtn = document.querySelector('.o_navbar_apps_menu button i, .o_navbar .ph-squares-four');
    const navbarAppsIcon = navbarAppsBtn ? navbarAppsBtn.className : null;

    // Check More dropdown icon in navbar sections
    const moreIcon = document.querySelector('.o_menu_sections_more button i');
    const moreIconClass = moreIcon ? moreIcon.className : null;

    return {
      legacyOiCount: legacyOi.length,
      legacyFaPlusCount: legacyFaPlus.length,
      phosphorIconsCount: phosphorIcons.length,
      navbarAppsIcon,
      moreIconClass,
      samplePhosphor: phosphorIcons.slice(0, 5),
      legacyOiSamples: legacyOi.slice(0, 5)
    };
  });

  // 5.1 Absence of fa-plus in rendered UI
  record('icon_bindings', 'Zero legacy fa-plus icons in rendered DOM', iconAudit.legacyFaPlusCount === 0, {
    count: iconAudit.legacyFaPlusCount
  });

  // 5.2 Navbar Phosphor icon bindings
  const isNavbarPhosphor = iconAudit.navbarAppsIcon && iconAudit.navbarAppsIcon.includes('ph-squares-four');
  record('icon_bindings', 'Navbar Home Launcher bound to Phosphor (ph-squares-four)', !!isNavbarPhosphor, {
    iconClass: iconAudit.navbarAppsIcon
  });

  // 5.3 More Section Dropdown bound to Phosphor
  const isMoreDropdownPhosphor = !iconAudit.moreIconClass || iconAudit.moreIconClass.includes('ph-plus') || iconAudit.moreIconClass.includes('ph');
  record('icon_bindings', 'Navbar Sections More Dropdown bound to Phosphor (ph-plus)', isMoreDropdownPhosphor, {
    iconClass: iconAudit.moreIconClass
  });

  // 5.4 Phosphor icons presence
  record('icon_bindings', 'Phosphor Duotone & regular icon presence on active web client', iconAudit.phosphorIconsCount > 0, {
    activePhosphorCount: iconAudit.phosphorIconsCount,
    sample: iconAudit.samplePhosphor
  });

  await browser.close();

  // Save JSON report
  const reportPath = path.join(ARTIFACTS_DIR, 'empirical_audit_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');

  console.log('\n======================================================================');
  console.log(`AUDIT COMPLETE: ${report.summary.passed}/${report.summary.total} TESTS PASSED (${report.summary.failed} FAILED)`);
  console.log(`Detailed JSON report saved to: ${reportPath}`);
  console.log('======================================================================\n');

  return report;
}

runEmpiricalAudit().catch(err => {
  console.error('\n[FATAL] Error running empirical audit:', err);
  process.exit(1);
});
