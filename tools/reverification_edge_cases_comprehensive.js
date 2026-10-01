#!/usr/bin/env node
/**
 * tools/reverification_edge_cases_comprehensive.js
 * ================================================
 * Exhaustive Empirical Reverification Harness for UI/UX & OWL Component Council
 * Tests all 6 required edge cases:
 *   1. Floating Action Bar lifecycle (dynamic appear on select, disappear on deselect & discard)
 *   2. Live status indicator dot presence & transitions on offline/online events
 *   3. Navbar brand logo and title have 0px overlap with menu sections across viewports
 *   4. Dark mode chatter has dark background #0f172a (not white)
 *   5. ShellBar height locked at 48px
 *   6. Table row height locked at 34px across 90+ rows
 */

const { chromium } = require('playwright');

async function runComprehensiveVerification() {
  console.log('======================================================================');
  console.log('EXHAUSTIVE EMPIRICAL REVERIFICATION HARNESS');
  console.log('======================================================================\n');

  const report = [];
  function assertCheck(id, description, passed, details) {
    report.push({ id, description, passed: !!passed, details });
    const mark = passed ? '✅ PASS' : '❌ FAIL';
    console.log(`[${mark}] ${id}: ${description}`);
    if (details) console.log(`       Details: ${JSON.stringify(details)}`);
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
    // Auth
    console.log('Authenticating session on odoo20_dev...');
    const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
      data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });
    if (!authRes.ok()) throw new Error('Authentication failed');
    console.log('✓ Successfully authenticated.\n');

    // -------------------------------------------------------------------------
    // EDGE CASE 1: ShellBar height locked at 48px
    // -------------------------------------------------------------------------
    console.log('--- EDGE CASE 1: ShellBar Height Locked at 48px ---');
    await page.goto('http://localhost:28069/insilos/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_navbar', { timeout: 15000 });
    await page.waitForTimeout(1000);

    const navData = await page.evaluate(() => {
      const nav = document.querySelector('.o_navbar');
      const r = nav ? nav.getBoundingClientRect() : null;
      const s = nav ? window.getComputedStyle(nav) : null;
      return {
        height: r ? Math.round(r.height) : null,
        minHeight: s ? s.minHeight : null,
        maxHeight: s ? s.maxHeight : null
      };
    });
    assertCheck('EC-01', 'ShellBar height is exactly 48px locked', navData.height === 48, navData);

    // -------------------------------------------------------------------------
    // EDGE CASE 2: Navbar brand logo and title have 0px overlap with menu sections
    // -------------------------------------------------------------------------
    console.log('\n--- EDGE CASE 2: Navbar Brand Logo and Title Overlap (0px) ---');
    const viewports = [
      { name: '1920x1080 (FHD)', w: 1920, h: 1080 },
      { name: '1440x900 (Desktop)', w: 1440, h: 900 },
      { name: '1280x800 (Laptop)', w: 1280, h: 800 }
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.w, height: vp.h });
      await page.waitForTimeout(500);

      const overlapData = await page.evaluate(() => {
        const brand = document.querySelector('.o_menu_brand');
        const brandRect = brand ? brand.getBoundingClientRect() : null;
        const logo = document.querySelector('.o_insilos_brand_logo');
        const logoRect = logo ? logo.getBoundingClientRect() : null;
        const sections = document.querySelector('.o_menu_sections');
        const firstEntry = sections ? sections.querySelector('.o_nav_entry, a, button') : null;
        const firstEntryRect = firstEntry ? firstEntry.getBoundingClientRect() : null;

        let overlap = 0;
        if (brandRect && firstEntryRect && brandRect.width > 0 && firstEntryRect.width > 0) {
          if (brandRect.right > firstEntryRect.left) {
            overlap = Math.round(brandRect.right - firstEntryRect.left);
          }
        }

        const waffleIcon = document.querySelector('.o_menu_toggle .ph-squares-four');

        return {
          brandRight: brandRect ? Math.round(brandRect.right) : null,
          sectionsLeft: firstEntryRect ? Math.round(firstEntryRect.left) : null,
          overlapPx: overlap,
          hasWaffle: !!waffleIcon,
          hasLogo: !!logo && (logoRect ? logoRect.width > 0 : false)
        };
      });

      assertCheck(`EC-02-${vp.name}`, `[${vp.name}] 0px brand overlap with menu sections`, overlapData.overlapPx === 0, overlapData);
    }
    await page.setViewportSize({ width: 1440, height: 900 });

    // -------------------------------------------------------------------------
    // EDGE CASE 3: Live status indicator dot present & dynamic transitions
    // -------------------------------------------------------------------------
    console.log('\n--- EDGE CASE 3: Live Status Indicator Dot in DOM & Dynamic Transitions ---');
    const dotInitial = await page.evaluate(() => {
      const chip = document.querySelector('.o_switch_company_menu');
      const dot = chip ? chip.querySelector('.o_live_status_dot') : null;
      if (!dot) return { exists: false };
      const s = window.getComputedStyle(dot);
      return {
        exists: true,
        className: dot.className,
        bgColor: s.backgroundColor,
        isLive: dot.classList.contains('o_status_live')
      };
    });
    assertCheck('EC-03-DOM', 'Live status indicator dot is present in DOM', dotInitial.exists, dotInitial);
    assertCheck('EC-03-LIVE', 'Initial online state is green (o_status_live, rgb(16, 126, 62))',
      dotInitial.isLive && dotInitial.bgColor === 'rgb(16, 126, 62)', dotInitial);

    // Trigger offline
    await context.setOffline(true);
    await page.evaluate(() => window.dispatchEvent(new Event('offline')));
    await page.waitForTimeout(600);

    const dotOffline = await page.evaluate(() => {
      const dot = document.querySelector('.o_switch_company_menu .o_live_status_dot');
      const s = dot ? window.getComputedStyle(dot) : null;
      return {
        className: dot ? dot.className : null,
        bgColor: s ? s.backgroundColor : null,
        isOffline: dot ? dot.classList.contains('o_status_offline') : false
      };
    });
    assertCheck('EC-03-OFFLINE', 'Dispatched offline event transitions dot to red (o_status_offline, rgb(187, 0, 0))',
      dotOffline.isOffline && dotOffline.bgColor === 'rgb(187, 0, 0)', dotOffline);

    // Trigger online
    await context.setOffline(false);
    await page.evaluate(() => window.dispatchEvent(new Event('online')));
    await page.waitForTimeout(600);

    const dotRestored = await page.evaluate(() => {
      const dot = document.querySelector('.o_switch_company_menu .o_live_status_dot');
      const s = dot ? window.getComputedStyle(dot) : null;
      return {
        className: dot ? dot.className : null,
        bgColor: s ? s.backgroundColor : null,
        isLive: dot ? dot.classList.contains('o_status_live') : false
      };
    });
    assertCheck('EC-03-RESTORE', 'Dispatched online event transitions dot back to green (o_status_live)',
      dotRestored.isLive && dotRestored.bgColor === 'rgb(16, 126, 62)', dotRestored);

    // -------------------------------------------------------------------------
    // EDGE CASE 4: Floating Action Bar dynamically appears on selection & disappears on deselection
    // -------------------------------------------------------------------------
    console.log('\n--- EDGE CASE 4: Floating Action Bar Dynamic Lifecycle ---');
    // Test 4A: In web.ListView (/insilos/contacts)
    console.log('Testing FAB in standard web.ListView (/insilos/contacts)...');
    let fabCount0 = await page.locator('.o_floating_batch_action_bar').count();
    assertCheck('EC-04-INIT-0', 'FAB is not mounted when 0 rows selected', fabCount0 === 0, { count: fabCount0 });

    const contactRow1 = page.locator('.o_list_table tbody tr.o_data_row .o_list_record_selector input').first();
    await contactRow1.click();
    await page.waitForTimeout(600);

    const fabMounted1 = await page.evaluate(() => {
      const fab = document.querySelector('.o_floating_batch_action_bar');
      if (!fab) return { exists: false };
      const s = window.getComputedStyle(fab);
      const countEl = fab.querySelector('.o_selected_count');
      const approve = fab.querySelector('.is-floating-btn-approve, .btn-primary');
      const exportBtn = fab.querySelector('.is-floating-btn-export, .ph-download-simple');
      const discard = fab.querySelector('.is-floating-btn-close, .ph-x');
      return {
        exists: true,
        position: s.position,
        bottom: s.bottom,
        zIndex: s.zIndex,
        countText: countEl ? countEl.innerText.trim() : null,
        hasApprove: !!approve,
        hasExport: !!exportBtn,
        hasDiscard: !!discard
      };
    });
    assertCheck('EC-04-SELECT-1', 'Selecting row 1 mounts FAB with count 1, fixed positioning, and actions',
      fabMounted1.exists && fabMounted1.countText === '1' && fabMounted1.position === 'fixed' && fabMounted1.hasApprove,
      fabMounted1);

    const contactRow2 = page.locator('.o_list_table tbody tr.o_data_row .o_list_record_selector input').nth(1);
    await contactRow2.click();
    await page.waitForTimeout(400);

    const count2Text = await page.locator('.o_floating_batch_action_bar .o_selected_count').innerText();
    assertCheck('EC-04-SELECT-2', 'Selecting row 2 dynamically increments FAB count to 2', count2Text === '2', { count: count2Text });

    // Deselect via FAB discard button
    const discardBtn = page.locator('.o_floating_batch_action_bar .is-floating-btn-close, .o_floating_batch_action_bar .ph-x').first();
    await discardBtn.click();
    await page.waitForTimeout(600);

    const fabAfterDiscard = await page.locator('.o_floating_batch_action_bar').count();
    const checkedBoxesAfterDiscard = await page.locator('.o_list_table tbody tr.o_data_row .o_list_record_selector input:checked').count();
    assertCheck('EC-04-DISCARD', 'Clicking FAB Discard button unchecks rows and unmounts FAB completely',
      fabAfterDiscard === 0 && checkedBoxesAfterDiscard === 0,
      { fabCount: fabAfterDiscard, checkedBoxes: checkedBoxesAfterDiscard });

    // Test row uncheck deselection
    await contactRow1.click();
    await page.waitForTimeout(500);
    assertCheck('EC-04-RESELECT', 'Re-selecting row 1 displays FAB again', (await page.locator('.o_floating_batch_action_bar').count()) === 1);
    await contactRow1.click();
    await page.waitForTimeout(500);
    assertCheck('EC-04-DESELECT-UNMOUNT', 'Unchecking row 1 unmounts FAB completely', (await page.locator('.o_floating_batch_action_bar').count()) === 0);

    // Test 4B: In purchase.ListView (/insilos/purchase)
    console.log('Testing FAB in purchase.ListView (/insilos/purchase)...');
    await page.goto('http://localhost:28069/insilos/purchase', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_list_table', { timeout: 15000 });
    await page.waitForTimeout(1500);

    const purchaseRow1 = page.locator('.o_list_table tbody tr.o_data_row .o_list_record_selector input').first();
    await purchaseRow1.click();
    await page.waitForTimeout(600);

    const purchaseFab = await page.evaluate(() => {
      const fab = document.querySelector('.o_floating_batch_action_bar');
      if (!fab) return { exists: false };
      const countEl = fab.querySelector('.o_selected_count');
      return { exists: true, countText: countEl ? countEl.innerText.trim() : null };
    });
    assertCheck('EC-04-PURCHASE-MOUNT', 'FAB mounts cleanly in purchase.ListView on record selection',
      purchaseFab.exists && purchaseFab.countText === '1', purchaseFab);

    await purchaseRow1.click();
    await page.waitForTimeout(500);
    assertCheck('EC-04-PURCHASE-UNMOUNT', 'FAB unmounts in purchase.ListView when record deselected',
      (await page.locator('.o_floating_batch_action_bar').count()) === 0);

    // -------------------------------------------------------------------------
    // EDGE CASE 5: Table row height locked at exactly 34px
    // -------------------------------------------------------------------------
    console.log('\n--- EDGE CASE 5: Table Row Height Locked at 34px ---');
    // Audit purchase table rows
    const purchaseRowsHeight = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('.o_list_table tbody tr.o_data_row'));
      const heights = rows.map(r => Math.round(r.getBoundingClientRect().height));
      const non34 = heights.filter(h => h !== 34);
      return { total: heights.length, non34Count: non34.length, heightsSample: heights.slice(0, 5) };
    });
    assertCheck('EC-05-PURCHASE', '100% of /insilos/purchase rows are strictly 34px (0 deviations)',
      purchaseRowsHeight.total > 0 && purchaseRowsHeight.non34Count === 0, purchaseRowsHeight);

    // Audit contacts table rows (70+ records)
    await page.goto('http://localhost:28069/insilos/contacts', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_list_table', { timeout: 15000 });
    await page.waitForTimeout(1500);

    const contactRowsHeight = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('.o_list_table tbody tr.o_data_row'));
      const heights = rows.map(r => Math.round(r.getBoundingClientRect().height));
      const non34 = heights.filter(h => h !== 34);
      return { total: heights.length, non34Count: non34.length, heightsSample: heights.slice(0, 5) };
    });
    assertCheck('EC-05-CONTACTS', `100% of /insilos/contacts rows are strictly 34px (0 deviations across ${contactRowsHeight.total} rows)`,
      contactRowsHeight.total > 20 && contactRowsHeight.non34Count === 0, contactRowsHeight);

    // -------------------------------------------------------------------------
    // EDGE CASE 6: Dark mode chatter has dark background #0f172a (not white)
    // -------------------------------------------------------------------------
    console.log('\n--- EDGE CASE 6: Dark Mode Chatter Background (#0f172a) ---');
    await page.goto('http://localhost:28069/insilos/purchase', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.o_list_table', { timeout: 15000 });
    await page.waitForTimeout(2000);

    const firstDataRow = page.locator('.o_data_row').first();
    await firstDataRow.click();
    await page.waitForSelector('.o_form_view', { timeout: 15000 });
    await page.waitForTimeout(2000);

    // Apply dark mode
    await page.evaluate(() => {
      document.body.classList.add('o_dark_mode');
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.setAttribute('data-bs-theme', 'dark');
    });
    await page.waitForTimeout(800);

    const darkChatterData = await page.evaluate(() => {
      const chatter = document.querySelector('.o-mail-Chatter, .o-mail-ChatterContainer, .o_ChatterContainer');
      const topbar = document.querySelector('.o-mail-Chatter-topbar');
      const chatterStyle = chatter ? window.getComputedStyle(chatter) : null;
      const topbarStyle = topbar ? window.getComputedStyle(topbar) : null;

      return {
        hasChatter: !!chatter,
        chatterClass: chatter ? chatter.className : null,
        chatterBg: chatterStyle ? chatterStyle.backgroundColor : null,
        topbarBg: topbarStyle ? topbarStyle.backgroundColor : null
      };
    });

    assertCheck('EC-06-FOUND', 'Modern chatter component found on form view', darkChatterData.hasChatter, darkChatterData);
    assertCheck('EC-06-DARK-BG', 'Dark mode chatter has dark background #0f172a (rgb(15, 23, 42)), not white',
      darkChatterData.chatterBg === 'rgb(15, 23, 42)',
      darkChatterData);

    // -------------------------------------------------------------------------
    // Summary
    // -------------------------------------------------------------------------
    console.log('\n======================================================================');
    const totalPassed = report.filter(r => r.passed).length;
    const totalFailed = report.filter(r => !r.passed).length;
    console.log(`EXHAUSTIVE REVERIFICATION SUMMARY: ${totalPassed} / ${report.length} PASS (${totalFailed} FAIL)`);
    console.log('======================================================================\n');

    await browser.close();
    return { total: report.length, passed: totalPassed, failed: totalFailed, report };

  } catch (err) {
    console.error('Fatal execution error:', err);
    await browser.close();
    throw err;
  }
}

runComprehensiveVerification().then(res => {
  if (res.failed > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}).catch(err => {
  console.error(err);
  process.exit(1);
});
