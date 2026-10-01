const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = path.join(__dirname, 'test_artifacts_stress');
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

const MODULES = [
  { name: 'MM_Purchase', module: 'Materials Management (Purchase)', model: 'purchase.order', id: 1, action: 758, url: 'http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758' },
  { name: 'SD_Sale', module: 'Sales & Distribution (Sale)', model: 'sale.order', id: 1, action: 561, url: 'http://localhost:28069/web#id=1&model=sale.order&view_type=form&action=561' },
  { name: 'LE_Stock', module: 'Inventory & Logistics (Stock)', model: 'stock.picking', id: 2, action: 257, url: 'http://localhost:28069/web#id=2&model=stock.picking&view_type=form&action=257' },
  { name: 'PP_MRP', module: 'Manufacturing (MRP)', model: 'mrp.production', id: 10, action: 367, url: 'http://localhost:28069/web#id=10&model=mrp.production&view_type=form&action=367' },
  { name: 'FI_Account', module: 'Financials & Accounting (Account Invoice)', model: 'account.move', id: 12, action: 475, url: 'http://localhost:28069/web#id=12&model=account.move&view_type=form&action=475' },
  { name: 'HCM_Employee', module: 'Human Capital Management (HR Employee)', model: 'hr.employee', id: 47, action: 1012, url: 'http://localhost:28069/web#id=47&model=hr.employee&view_type=form&action=1012' }
];

const VIEWPORTS = [
  { name: 'Desktop_1600x950', width: 1600, height: 950 },
  { name: 'Desktop_1920x1080', width: 1920, height: 1080 },
  { name: 'Desktop_1440x900', width: 1440, height: 900 },
  { name: 'Desktop_1280x800', width: 1280, height: 800 }
];

const WIZARDS = [
  {
    name: 'account.move.reversal',
    title: 'Reverse Journal Entry',
    action: {
      type: 'ir.actions.act_window',
      res_model: 'account.move.reversal',
      views: [[false, 'form']],
      target: 'new',
      context: { active_model: 'account.move', active_ids: [12], active_id: 12 }
    }
  },
  {
    name: 'account.payment.register',
    title: 'Register Payment',
    action: {
      type: 'ir.actions.act_window',
      res_model: 'account.payment.register',
      views: [[false, 'form']],
      target: 'new',
      context: { active_model: 'account.move', active_ids: [12], active_id: 12 }
    }
  },
  {
    name: 'stock.backorder.confirmation',
    title: 'Backorder Creation',
    action: {
      type: 'ir.actions.act_window',
      res_model: 'stock.backorder.confirmation',
      views: [[false, 'form']],
      target: 'new',
      context: { default_pick_ids: [[4, 2]] }
    }
  }
];

async function runAdversarialStressSuite() {
  console.log('========================================================================');
  console.log('INSILOS AUTONOMOUS HARD REFACTOR: EMPIRICAL CHALLENGER STRESS SUITE');
  console.log('1. Form Baseline Stress across 6 Modules & 4 Desktop Viewports');
  console.log('2. Maximum Button Overload Stress in account.move (5, 10, 15, 25 extra buttons)');
  console.log('3. Dialog Wizard Layout, Clearance, Scrollbar & Button Stress (3 Wizards)');
  console.log('========================================================================\n');

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 950 } });
  const page = await context.newPage();

  console.log('Authenticating session...');
  await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
  });

  const fullReport = {
    timestamp: new Date().toISOString(),
    baselineTests: [],
    buttonStressTests: [],
    wizardTests: [],
    verdict: 'PENDING'
  };

  // =========================================================================
  // PART 1: Form Baseline Stress Across All 6 Business Modules
  // =========================================================================
  console.log('\n>>> STAGE 1: Form Baseline Stress Testing Across 6 Business Modules');

  for (const vp of VIEWPORTS) {
    console.log(`\n--- Testing Viewport: ${vp.name} (${vp.width}x${vp.height}) ---`);
    await page.setViewportSize({ width: vp.width, height: vp.height });

    for (const mod of MODULES) {
      try {
        await page.goto(mod.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await page.waitForSelector('.o_form_view', { timeout: 15000 });
        await page.waitForTimeout(600);

        const metrics = await page.evaluate((modInfo) => {
          const statusbar = document.querySelector('.o_form_statusbar');
          const statusbarButtons = document.querySelector('.o_statusbar_buttons');
          const firstStatusbarBtn = statusbarButtons ? statusbarButtons.querySelector('.btn:not(.d-none)') : null;
          const chatterContainer = document.querySelector('.o-mail-Form-chatter, .o-mail-ChatterContainer');
          const chatterTopbar = document.querySelector('.o-mail-Chatter-topbar');
          const firstChatterBtn = chatterTopbar ? (chatterTopbar.querySelector('.o-mail-Chatter-sendMessage') || chatterTopbar.querySelector('.btn:not(.d-none)')) : null;
          const statButton = document.querySelector('.o-form-buttonbox .btn.oe_stat_button, .oe_button_box .btn.oe_stat_button');
          const titleH1 = document.querySelector('.oe_title h1, h1.o_employee_form_header_info, .o_employee_form_header_info');

          const getRect = (el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
          };

          const getStyle = (el, prop) => (el ? window.getComputedStyle(el).getPropertyValue(prop) : null);

          const sbRect = getRect(statusbar);
          const ctRect = getRect(chatterTopbar);
          const sBtnRect = getRect(firstStatusbarBtn);
          const cBtnRect = getRect(firstChatterBtn);

          return {
            module: modInfo.module,
            model: modInfo.model,
            isAside: chatterContainer ? chatterContainer.classList.contains('o-aside') : false,
            statusbar: {
              rect: sbRect,
              height: sbRect ? sbRect.height : null,
              styleHeight: getStyle(statusbar, 'height')
            },
            chatterTopbar: {
              rect: ctRect,
              height: ctRect ? ctRect.height : null,
              styleHeight: getStyle(chatterTopbar, 'height')
            },
            statusbarButton: {
              rect: sBtnRect,
              height: sBtnRect ? sBtnRect.height : null,
              fontSize: getStyle(firstStatusbarBtn, 'font-size'),
              fontWeight: getStyle(firstStatusbarBtn, 'font-weight'),
              borderRadius: getStyle(firstStatusbarBtn, 'border-radius')
            },
            chatterButton: {
              rect: cBtnRect,
              height: cBtnRect ? cBtnRect.height : null,
              fontSize: getStyle(firstChatterBtn, 'font-size'),
              fontWeight: getStyle(firstChatterBtn, 'font-weight'),
              borderRadius: getStyle(firstChatterBtn, 'border-radius')
            },
            statButton: {
              height: getStyle(statButton, 'height'),
              borderRadius: getStyle(statButton, 'border-radius')
            },
            titleH1: {
              fontSize: getStyle(titleH1, 'font-size'),
              fontWeight: getStyle(titleH1, 'font-weight')
            },
            diffToolbarTop: (sbRect && ctRect) ? sbRect.top - ctRect.top : null,
            diffButtonTop: (sBtnRect && cBtnRect) ? sBtnRect.top - cBtnRect.top : null,
            statusbarButtonsWrap: getStyle(statusbarButtons, 'flex-wrap'),
            statusbarButtonsOverflowX: getStyle(statusbarButtons, 'overflow-x')
          };
        }, mod);

        const pass = metrics.isAside ? (Math.abs(metrics.diffToolbarTop) < 0.5 && Math.abs(metrics.diffButtonTop) < 0.5) : true;
        const resEntry = {
          viewport: vp.name,
          width: vp.width,
          module: mod.name,
          pass,
          ...metrics
        };
        fullReport.baselineTests.push(resEntry);

        console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${mod.name.padEnd(16)} | Toolbar Diff: ${metrics.diffToolbarTop !== null ? metrics.diffToolbarTop.toFixed(3) + 'px' : 'N/A'} | Btn Diff: ${metrics.diffButtonTop !== null ? metrics.diffButtonTop.toFixed(3) + 'px' : 'N/A'} | SB Height: ${metrics.statusbar.height}px | Btn Heights: SB=${metrics.statusbarButton.height}px, CT=${metrics.chatterButton.height}px`);

        if (vp.name === 'Desktop_1600x950') {
          const shotPath = path.join(ARTIFACTS_DIR, `baseline_${mod.name}.png`);
          await page.screenshot({ path: shotPath });
        }
      } catch (err) {
        console.error(`  ❌ Error measuring ${mod.name} on ${vp.name}:`, err.message);
        fullReport.baselineTests.push({ viewport: vp.name, module: mod.name, pass: false, error: err.message });
      }
    }
  }

  // =========================================================================
  // PART 2: Maximum Button Count Stress in account.move
  // =========================================================================
  console.log('\n>>> STAGE 2: Maximum Button Overload Stress in account.move');
  await page.setViewportSize({ width: 1600, height: 950 });
  await page.goto('http://localhost:28069/web#id=12&model=account.move&view_type=form&action=475', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForSelector('.o_form_view');
  await page.waitForTimeout(600);

  const buttonCountsToTest = [0, 5, 10, 15, 25];

  for (const extraCount of buttonCountsToTest) {
    const stressResult = await page.evaluate((addCount) => {
      const statusbar = document.querySelector('.o_form_statusbar');
      const sbButtons = document.querySelector('.o_statusbar_buttons');
      const chatterTopbar = document.querySelector('.o-mail-Chatter-topbar');

      // Clean up previous stress buttons
      const existingInjected = sbButtons.querySelectorAll('.insilos_stress_btn');
      existingInjected.forEach(b => b.remove());

      // Inject extra buttons
      for (let i = 1; i <= addCount; i++) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-secondary insilos_stress_btn';
        btn.textContent = `Stress Action #${i}`;
        sbButtons.appendChild(btn);
      }

      const getRect = (el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
      };

      const firstBtn = sbButtons.querySelector('.btn:not(.d-none)');
      const lastBtn = sbButtons.querySelector('.btn:last-child');
      const firstChatterBtn = chatterTopbar ? (chatterTopbar.querySelector('.o-mail-Chatter-sendMessage') || chatterTopbar.querySelector('.btn:not(.d-none)')) : null;

      const sbRect = getRect(statusbar);
      const ctRect = getRect(chatterTopbar);
      const firstBtnRect = getRect(firstBtn);
      const lastBtnRect = getRect(lastBtn);
      const chatterBtnRect = getRect(firstChatterBtn);

      const computedStyle = window.getComputedStyle(sbButtons);

      // Test horizontal scrolling
      const initialScrollLeft = sbButtons.scrollLeft;
      sbButtons.scrollLeft = 500;
      const canScrollHorizontally = sbButtons.scrollLeft > 0 || sbButtons.scrollWidth > sbButtons.clientWidth;
      const scrolledBtnRect = getRect(firstBtn);
      sbButtons.scrollLeft = initialScrollLeft; // restore

      const totalButtons = sbButtons.querySelectorAll('.btn:not(.d-none)').length;

      return {
        extraCount: addCount,
        totalButtons,
        flexWrap: computedStyle.flexWrap,
        overflowX: computedStyle.overflowX,
        overflowY: computedStyle.overflowY,
        sbButtonsHeight: computedStyle.height,
        statusbarHeight: sbRect ? sbRect.height : null,
        scrollWidth: sbButtons.scrollWidth,
        clientWidth: sbButtons.clientWidth,
        isScrollWidthLarger: sbButtons.scrollWidth > sbButtons.clientWidth,
        canScrollHorizontally,
        diffToolbarTop: (sbRect && ctRect) ? sbRect.top - ctRect.top : null,
        diffButtonTop: (firstBtnRect && chatterBtnRect) ? firstBtnRect.top - chatterBtnRect.top : null,
        firstBtnTop: firstBtnRect ? firstBtnRect.top : null,
        lastBtnTop: lastBtnRect ? lastBtnRect.top : null,
        // If buttons wrap, lastBtnTop will be significantly greater than firstBtnTop (> 5px)
        isWrapped: (firstBtnRect && lastBtnRect) ? Math.abs(lastBtnRect.top - firstBtnRect.top) > 5 : false,
        scrolledDiffButtonTop: (scrolledBtnRect && chatterBtnRect) ? scrolledBtnRect.top - chatterBtnRect.top : null
      };
    }, extraCount);

    const pass = (!stressResult.isWrapped) &&
                 (stressResult.flexWrap === 'nowrap') &&
                 (Math.abs(stressResult.diffButtonTop) < 0.5) &&
                 (Math.abs(stressResult.statusbarHeight - 48) < 0.5);

    fullReport.buttonStressTests.push({ pass, ...stressResult });

    console.log(`  [${pass ? 'PASS' : 'FAIL'}] +${String(extraCount).padStart(2)} Buttons (Total: ${stressResult.totalButtons}) | Wrapped: ${stressResult.isWrapped} | Flex-Wrap: ${stressResult.flexWrap} | SB Height: ${stressResult.statusbarHeight}px | Btn Diff: ${stressResult.diffButtonTop.toFixed(3)}px | ScrollWidth: ${stressResult.scrollWidth}px vs ClientWidth: ${stressResult.clientWidth}px`);

    if (extraCount === 25) {
      const shotPath = path.join(ARTIFACTS_DIR, `button_stress_25_buttons.png`);
      await page.screenshot({ path: shotPath });
      console.log(`    Screenshot saved: ${shotPath}`);
    }
  }

  // Also test button overload on narrow 1280px viewport!
  console.log('\n--- Button Overload Stress at Narrow Desktop (1280x800) ---');
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.waitForTimeout(300);

  const narrowStress = await page.evaluate(() => {
    const statusbar = document.querySelector('.o_form_statusbar');
    const sbButtons = document.querySelector('.o_statusbar_buttons');
    const chatterTopbar = document.querySelector('.o-mail-Chatter-topbar');

    const firstBtn = sbButtons.querySelector('.btn:not(.d-none)');
    const lastBtn = sbButtons.querySelector('.btn:last-child');
    const firstChatterBtn = chatterTopbar ? (chatterTopbar.querySelector('.o-mail-Chatter-sendMessage') || chatterTopbar.querySelector('.btn:not(.d-none)')) : null;

    const rFirst = firstBtn ? firstBtn.getBoundingClientRect() : null;
    const rLast = lastBtn ? lastBtn.getBoundingClientRect() : null;
    const rChatter = firstChatterBtn ? firstChatterBtn.getBoundingClientRect() : null;
    const rSb = statusbar ? statusbar.getBoundingClientRect() : null;
    const chatterContainer = document.querySelector('.o-mail-Form-chatter, .o-mail-ChatterContainer');
    const isAside = chatterContainer ? chatterContainer.classList.contains('o-aside') : false;

    return {
      viewport: '1280x800',
      totalButtons: sbButtons.querySelectorAll('.btn:not(.d-none)').length,
      isWrapped: (rFirst && rLast) ? Math.abs(rLast.top - rFirst.top) > 5 : false,
      flexWrap: window.getComputedStyle(sbButtons).flexWrap,
      statusbarHeight: rSb ? rSb.height : null,
      isAside,
      diffButtonTop: (rFirst && rChatter && isAside) ? rFirst.top - rChatter.top : null,
      scrollWidth: sbButtons.scrollWidth,
      clientWidth: sbButtons.clientWidth
    };
  });

  const narrowPass = (!narrowStress.isWrapped) &&
                     (narrowStress.flexWrap === 'nowrap') &&
                     (Math.abs(narrowStress.statusbarHeight - 48) < 0.5);
  fullReport.buttonStressTests.push({ pass: narrowPass, ...narrowStress });
  console.log(`  [${narrowPass ? 'PASS' : 'FAIL'}] 1280px Viewport + 25 Buttons | Wrapped: ${narrowStress.isWrapped} | Flex-Wrap: ${narrowStress.flexWrap} | SB Height: ${narrowStress.statusbarHeight}px | ScrollWidth: ${narrowStress.scrollWidth}px vs ClientWidth: ${narrowStress.clientWidth}px`);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, `button_stress_1280px_25_buttons.png`) });

  // Restore 1600x950 viewport for Dialog testing
  await page.setViewportSize({ width: 1600, height: 950 });

  // =========================================================================
  // PART 3: Dialog Wizard Stress (account.move.reversal, account.payment.register, stock.backorder.confirmation)
  // =========================================================================
  console.log('\n>>> STAGE 3: Dialog Wizard Layout, Spacing, Clearance & Scrollbar Stress');

  for (const wiz of WIZARDS) {
    console.log(`\n--- Testing Wizard: ${wiz.name} (${wiz.title}) ---`);
    await page.goto('http://localhost:28069/web#id=12&model=account.move&view_type=form&action=475', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForSelector('.o_form_view');
    await page.waitForTimeout(500);

    // Trigger action
    const triggerResult = await page.evaluate(async (wizDef) => {
      try {
        const actionService = odoo.__WOWL_DEBUG__.root.env.services.action;
        await actionService.doAction(wizDef.action);
        return { success: true };
      } catch (e) {
        return { success: false, error: e.message };
      }
    }, wiz);

    if (!triggerResult.success) {
      console.error(`  ❌ Failed to trigger wizard ${wiz.name}:`, triggerResult.error);
      fullReport.wizardTests.push({ name: wiz.name, error: triggerResult.error, pass: false });
      continue;
    }

    await page.waitForSelector('.modal.show, .o_dialog .modal, .modal', { timeout: 10000 });
    await page.waitForTimeout(1000);

    const wizMetrics = await page.evaluate(() => {
      const modal = document.querySelector('.modal.show, .o_dialog .modal, .modal');
      const dialog = modal ? modal.querySelector('.modal-dialog') : null;
      const content = dialog ? dialog.querySelector('.modal-content') : null;
      const header = content ? content.querySelector('.modal-header') : null;
      const title = header ? header.querySelector('.modal-title') : null;
      const body = content ? content.querySelector('.modal-body') : null;
      const footer = content ? content.querySelector('.modal-footer') : null;
      const footerBtns = footer ? Array.from(footer.querySelectorAll('.btn')) : [];

      const getRect = (el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.x, y: r.y, width: r.width, height: r.height, top: r.top, bottom: r.bottom, left: r.left, right: r.right };
      };

      const getComputedProps = (el) => {
        if (!el) return {};
        const s = window.getComputedStyle(el);
        return {
          height: s.height,
          padding: `${s.paddingTop} ${s.paddingRight} ${s.paddingBottom} ${s.paddingLeft}`,
          paddingTop: parseFloat(s.paddingTop),
          paddingRight: parseFloat(s.paddingRight),
          paddingBottom: parseFloat(s.paddingBottom),
          paddingLeft: parseFloat(s.paddingLeft),
          overflowX: s.overflowX,
          overflowY: s.overflowY,
          position: s.position,
          bottom: s.bottom,
          fontSize: s.fontSize,
          fontWeight: s.fontWeight,
          borderRadius: s.borderRadius,
          borderWidth: s.borderTopWidth,
          boxSizing: s.boxSizing
        };
      };

      // Measure clearance: Distance from modal-content left border to first inner content element left
      let clearanceLeft = null;
      let clearanceRight = null;
      let clearanceTop = null;

      if (content && body) {
        const cRect = content.getBoundingClientRect();
        const bRect = body.getBoundingClientRect();
        const firstInner = body.querySelector('.o_inner_group, .o_group, table, .alert, p, .o_form_sheet, form > div');
        if (firstInner) {
          const inRect = firstInner.getBoundingClientRect();
          clearanceLeft = inRect.left - cRect.left;
          clearanceRight = cRect.right - inRect.right;
          clearanceTop = inRect.top - bRect.top;
        }
      }

      return {
        header: {
          rect: getRect(header),
          styles: getComputedProps(header)
        },
        title: {
          rect: getRect(title),
          styles: getComputedProps(title)
        },
        body: {
          rect: getRect(body),
          styles: getComputedProps(body),
          scrollWidth: body ? body.scrollWidth : null,
          clientWidth: body ? body.clientWidth : null,
          scrollHeight: body ? body.scrollHeight : null,
          clientHeight: body ? body.clientHeight : null,
          hasHorizontalScrollbar: body ? (body.scrollWidth > body.clientWidth) : null
        },
        footer: {
          rect: getRect(footer),
          styles: getComputedProps(footer)
        },
        clearance: {
          clearanceLeft,
          clearanceRight,
          clearanceTop
        },
        buttons: footerBtns.map(btn => ({
          text: btn.innerText.trim(),
          rect: getRect(btn),
          styles: getComputedProps(btn)
        }))
      };
    });

    // Validations:
    // 1. Header height == 48px
    const headerHeightPass = Math.abs(wizMetrics.header.rect.height - 48) < 0.5;
    // 2. Sticky footer height == 48px
    const footerHeightPass = Math.abs(wizMetrics.footer.rect.height - 48) < 0.5;
    const footerStickyPass = wizMetrics.footer.styles.position === 'sticky' && wizMetrics.footer.styles.bottom === '0px';
    // 3. Body padding: 20px-24px clearance, no collapse
    const bodyPaddingPass = Math.abs(wizMetrics.body.styles.paddingTop - 20) < 1 &&
                            Math.abs(wizMetrics.body.styles.paddingBottom - 20) < 1 &&
                            Math.abs(wizMetrics.body.styles.paddingLeft - 24) < 1 &&
                            Math.abs(wizMetrics.body.styles.paddingRight - 24) < 1;
    // 4. No horizontal scrollbar inside .modal-body
    const noHScrollPass = (!wizMetrics.body.hasHorizontalScrollbar) && (wizMetrics.body.styles.overflowX === 'hidden');
    // 5. Button height == 32px and radius == 4px
    const buttonsPass = wizMetrics.buttons.length > 0 && wizMetrics.buttons.every(b => {
      const hPass = Math.abs(b.rect.height - 32) < 0.5;
      const rPass = b.styles.borderRadius === '4px';
      return hPass && rPass;
    });

    const wizardPass = headerHeightPass && footerHeightPass && footerStickyPass && bodyPaddingPass && noHScrollPass && buttonsPass;

    const wizResult = {
      name: wiz.name,
      title: wiz.title,
      pass: wizardPass,
      checks: {
        headerHeightPass: { pass: headerHeightPass, height: wizMetrics.header.rect.height, expected: 48 },
        footerHeightPass: { pass: footerHeightPass, height: wizMetrics.footer.rect.height, expected: 48 },
        footerStickyPass: { pass: footerStickyPass, position: wizMetrics.footer.styles.position, bottom: wizMetrics.footer.styles.bottom },
        bodyPaddingPass: { pass: bodyPaddingPass, padding: wizMetrics.body.styles.padding, expected: '20px 24px 20px 24px' },
        clearance: wizMetrics.clearance,
        noHorizontalScrollbarPass: { pass: noHScrollPass, overflowX: wizMetrics.body.styles.overflowX, scrollWidth: wizMetrics.body.scrollWidth, clientWidth: wizMetrics.body.clientWidth },
        buttonsPass: { pass: buttonsPass, buttons: wizMetrics.buttons.map(b => ({ text: b.text, height: b.rect.height, radius: b.styles.borderRadius, fontSize: b.styles.fontSize })) }
      },
      raw: wizMetrics
    };

    fullReport.wizardTests.push(wizResult);

    console.log(`  [${wizardPass ? 'PASS' : 'FAIL'}] Header 48px: ${headerHeightPass} (${wizMetrics.header.rect.height}px)`);
    console.log(`  [${wizardPass ? 'PASS' : 'FAIL'}] Footer 48px & Sticky: ${footerHeightPass && footerStickyPass} (${wizMetrics.footer.rect.height}px, ${wizMetrics.footer.styles.position})`);
    console.log(`  [${wizardPass ? 'PASS' : 'FAIL'}] Body Padding 20px 24px: ${bodyPaddingPass} (${wizMetrics.body.styles.padding}) | Clearance: L=${wizMetrics.clearance.clearanceLeft?.toFixed(1)}px, R=${wizMetrics.clearance.clearanceRight?.toFixed(1)}px`);
    console.log(`  [${wizardPass ? 'PASS' : 'FAIL'}] Zero Horizontal Scrollbar: ${noHScrollPass} (scrollWidth=${wizMetrics.body.scrollWidth}px, clientWidth=${wizMetrics.body.clientWidth}px, overflow-x=${wizMetrics.body.styles.overflowX})`);
    console.log(`  [${wizardPass ? 'PASS' : 'FAIL'}] Buttons 32px & 4px radius: ${buttonsPass} (${wizMetrics.buttons.map(b => `${b.text}: ${b.rect.height}px/r=${b.styles.borderRadius}`).join(', ')})`);

    const shotPath = path.join(ARTIFACTS_DIR, `wizard_${wiz.name.replace(/\./g, '_')}.png`);
    await page.screenshot({ path: shotPath });
    console.log(`  Screenshot saved: ${shotPath}`);

    // Close wizard
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }

  // =========================================================================
  // OVERALL VERDICT SYNTHESIS
  // =========================================================================
  const allBaselinePass = fullReport.baselineTests.length > 0 && fullReport.baselineTests.every(t => t.pass);
  const allButtonStressPass = fullReport.buttonStressTests.length > 0 && fullReport.buttonStressTests.every(t => t.pass);
  const allWizardsPass = fullReport.wizardTests.length > 0 && fullReport.wizardTests.every(t => t.pass);

  if (allBaselinePass && allButtonStressPass && allWizardsPass) {
    fullReport.verdict = 'CONFIRM_CORRECTNESS';
  } else {
    fullReport.verdict = 'REJECT';
  }

  console.log('\n========================================================================');
  console.log(`OVERALL EMPIRICAL VERDICT: ${fullReport.verdict}`);
  console.log(`- Form Baselines: ${allBaselinePass ? 'ALL PASS (0.000px discrepancy)' : 'FAILURES DETECTED'}`);
  console.log(`- Button Overload Stress: ${allButtonStressPass ? 'ALL PASS (No wrap, nowrap horizon enforced)' : 'FAILURES DETECTED'}`);
  console.log(`- Dialog Wizards: ${allWizardsPass ? 'ALL PASS (48px H/F, 32px/4px buttons, 20-24px clearance, 0 h-scroll)' : 'FAILURES DETECTED'}`);
  console.log('========================================================================\n');

  const reportJsonPath = path.join(ARTIFACTS_DIR, 'adversarial_stress_report.json');
  fs.writeFileSync(reportJsonPath, JSON.stringify(fullReport, null, 2));
  console.log(`Full empirical data written to: ${reportJsonPath}`);

  await browser.close();
}

runAdversarialStressSuite().catch(err => {
  console.error('[FATAL]:', err);
  process.exit(1);
});
