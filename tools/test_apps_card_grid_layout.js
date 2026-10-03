// tools/test_apps_card_grid_layout.js
// Visual & DOM Layout Verification for App Cards Grid Layout
// Requires: npx playwright install chromium
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const CONFIG = {
  baseUrl: 'http://localhost:28069',
  appsUrl: 'http://localhost:28069/insilos/apps?db=odoo20_dev',
  credentials: { username: 'admin', password: 'admin' },
  viewport: { width: 1920, height: 1080 },
  artifactsDir: path.join(__dirname, 'artifacts'),
  minCardsToAudit: 10,
  col1Width: { min: 65, max: 96 },       // ~84px ± tolerance
  learnMoreMinWidth: 150,
  iconSize: { width: 52, height: 52 },
  iconRadius: 4,
};
// ─── Helpers ────────────────────────────────────────────────────────────────
function ensureArtifactsDir() {
  if (!fs.existsSync(CONFIG.artifactsDir)) {
    fs.mkdirSync(CONFIG.artifactsDir, { recursive: true });
  }
}
function log(msg, level = 'INFO') {
  console.log(`[${level}] ${new Date().toISOString()} — ${msg}`);
}
async function login(page) {
  log('Navigating to login page…');
  await page.goto(`${CONFIG.baseUrl}/web/login?db=odoo20_dev`, { waitUntil: 'domcontentloaded' });
  const loginField = page.locator('input[name="login"], input#login');
  const passwordField = page.locator('input[name="password"], input#password');
  const submitBtn = page.locator('button[type="submit"], .btn-primary[type="submit"]');
  if (await loginField.count() > 0) {
    await loginField.fill(CONFIG.credentials.username);
    await passwordField.fill(CONFIG.credentials.password);
    await submitBtn.click();
    await page.waitForTimeout(2000);
    log('Login submitted.');
  } else {
    log('No login form detected — may already be authenticated.');
  }
}
async function navigateToApps(page) {
  log(`Navigating to ${CONFIG.appsUrl}…`);
  await page.goto(CONFIG.appsUrl, { waitUntil: 'domcontentloaded' });
  // Handle potential redirect back to login
  if (page.url().includes('/web/login')) {
    log('Redirected to login — authenticating…');
    await login(page);
    await page.goto(CONFIG.appsUrl, { waitUntil: 'domcontentloaded' });
  }
  // Wait for kanban cards to appear
  await page.waitForSelector('.o_modules_kanban .o_kanban_record', {
    timeout: 30000,
    state: 'visible',
  });
  log('App cards rendered.');
}
async function getBoxModel(page, elementHandle) {
  return await elementHandle.boundingBox();
}
// Retrieve computed style property for an element
async function getComputedStyle(page, handle, prop) {
  return await page.evaluate(
    ([el, property]) => {
      return window.getComputedStyle(el).getPropertyValue(property);
    },
    [handle, prop]
  );
}
// ─── Card Audit ─────────────────────────────────────────────────────────────
async function auditCard(page, cardHandle, index) {
  const result = {
    cardIndex: index,
    passed: true,
    assertions: [],
  };
  function assert(name, condition, detail = '') {
    const entry = { name, passed: condition, detail };
    result.assertions.push(entry);
    if (!condition) {
      result.passed = false;
      log(`  ✗ [Card ${index}] ${name} — ${detail}`, 'FAIL');
    } else {
      log(`  ✓ [Card ${index}] ${name}`, 'PASS');
    }
  }
  // ── Icon (aside) ──────────────────────────────────────────────────────────
  let iconHandle = await cardHandle.$('aside img, .o_kanban_image img, img');
  if (!iconHandle) {
    iconHandle = await cardHandle.$('aside');
  }
  const cardBox = await getBoxModel(page, cardHandle);
  let iconBox = null;
  if (iconHandle) {
    iconBox = await getBoxModel(page, iconHandle);
    assert(
      'Icon exists',
      iconBox !== null,
      iconBox ? `at (${Math.round(iconBox.x)}, ${Math.round(iconBox.y)})` : 'not found'
    );
    if (iconBox) {
      assert(
        'Icon approx 52x52px',
        iconBox.width >= 48 && iconBox.width <= 60 &&
        iconBox.height >= 48 && iconBox.height <= 60,
        `${Math.round(iconBox.width)}x${Math.round(iconBox.height)}px`
      );
      assert(
        'Icon in left column (Col 1)',
        iconBox.x >= cardBox.x && (iconBox.x - cardBox.x) < 100,
        `icon left offset from card: ${Math.round(iconBox.x - cardBox.x)}px`
      );
    }
  } else {
    assert('Icon aside element exists', false, 'aside not found in card');
  }
  // ── Primary Action Button (Col 1, Row 3) ─────────────────────────────────
  const actionBtnHandle = await cardHandle.$(
    '.btn-primary, .badge-installed, a.btn-info, button.btn-primary, button.badge-installed'
  );
  if (actionBtnHandle) {
    const actionBox = await getBoxModel(page, actionBtnHandle);
    assert('Action button exists', actionBox !== null, 'primary action button found');
    if (actionBox && iconBox) {
      assert(
        'Action button below icon (top > icon bottom)',
        actionBox.y >= iconBox.y + iconBox.height - 4,
        `actionTop=${Math.round(actionBox.y)} iconBottom=${Math.round(iconBox.y + iconBox.height)}`
      );
      assert(
        'Action button left-aligned with icon (Col 1)',
        Math.abs(actionBox.x - iconBox.x) <= 12,
        `actionLeft=${Math.round(actionBox.x)} iconLeft=${Math.round(iconBox.x)}`
      );
      assert(
        'Action button width spans Col 1 (~80-84px)',
        actionBox.width >= CONFIG.col1Width.min && actionBox.width <= CONFIG.col1Width.max,
        `width=${Math.round(actionBox.width)}px`
      );
    }
  } else {
    // Soft warning — some cards may not have a primary action
    result.assertions.push({ name: 'Action button (Col 1)', passed: true, detail: 'no primary action (acceptable)' });
  }
  // ── Title h2 (Col 2, Row 1) ───────────────────────────────────────────────
  const titleHandle = await cardHandle.$('h2, .o_kanban_record_title, .card-title');
  if (titleHandle) {
    const titleBox = await getBoxModel(page, titleHandle);
    if (titleBox && iconBox) {
      assert(
        'Title in Col 2 (right of icon)',
        titleBox.x > iconBox.x + iconBox.width - 4,
        `titleLeft=${Math.round(titleBox.x)} iconRight=${Math.round(iconBox.x + iconBox.width)}`
      );
    }
  } else {
    assert('Title h2 exists', false, 'h2 not found');
  }
  // ── Description (Col 2, Row 2) ────────────────────────────────────────────
  const descHandle = await cardHandle.$('small.text-muted, .text-muted, p.text-muted');
  if (descHandle && iconBox) {
    const descBox = await getBoxModel(page, descHandle);
    if (descBox) {
      assert(
        'Description in Col 2 (right of icon)',
        descBox.x > iconBox.x + iconBox.width - 4,
        `descLeft=${Math.round(descBox.x)} iconRight=${Math.round(iconBox.x + iconBox.width)}`
      );
    }
  }
  // ── Learn More / Module Info button (Col 2, Row 3) ────────────────────────
  const learnMoreHandle = await cardHandle.$(
    'a.btn-info:not(.btn-primary), a[href*="apps.odoo.com"], a[href*="module"], .btn-link, a.btn:not(.btn-primary):not(.badge-installed)'
  );
  if (learnMoreHandle) {
    const learnBox = await getBoxModel(page, learnMoreHandle);
    if (learnBox) {
      assert(
        '"Learn More" button width > 150px (Col 2 full width)',
        learnBox.width > CONFIG.learnMoreMinWidth,
        `width=${Math.round(learnBox.width)}px`
      );
      if (iconBox) {
        assert(
          '"Learn More" button in Col 2 (right of icon)',
          learnBox.x >= iconBox.x + iconBox.width - 4,
          `learnLeft=${Math.round(learnBox.x)} iconRight=${Math.round(iconBox.x + iconBox.width)}`
        );
      }
    }
  } else {
    result.assertions.push({ name: 'Learn More button', passed: true, detail: 'not present on this card (acceptable)' });
  }
  // ── 3-dot dropdown — must not overlap Col 2 content ──────────────────────
  const dropdownHandle = await cardHandle.$('.o_dropdown_kanban, .o_kanban_manage_toggle_button, [data-toggle="dropdown"]');
  if (dropdownHandle) {
    const dropBox = await getBoxModel(page, dropdownHandle);
    if (dropBox && cardBox) {
      assert(
        '3-dot menu does not overlap card content area (at card edge)',
        dropBox.x + dropBox.width <= cardBox.x + cardBox.width + 4,
        `dropRight=${Math.round(dropBox.x + dropBox.width)} cardRight=${Math.round(cardBox.x + cardBox.width)}`
      );
    }
  }
  return result;
}
// ─── Full Audit Pass ─────────────────────────────────────────────────────────
async function runAudit(page, mode = 'light') {
  log(`Starting audit in ${mode} mode…`);
  const cardHandles = await page.$$('.o_modules_kanban .o_kanban_record');
  const total = cardHandles.length;
  log(`Found ${total} cards.`);
  if (total === 0) {
    throw new Error('No .o_kanban_record elements found — layout may have failed to render.');
  }
  const auditCount = Math.min(total, CONFIG.minCardsToAudit);
  const results = [];
  for (let i = 0; i < auditCount; i++) {
    log(`Auditing card ${i + 1}/${auditCount}…`);
    const cardResult = await auditCard(page, cardHandles[i], i + 1);
    results.push(cardResult);
  }
  return { mode, totalCards: total, auditedCards: auditCount, results };
}
// ─── Main ────────────────────────────────────────────────────────────────────
(async () => {
  ensureArtifactsDir();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: CONFIG.viewport });
  const page = await context.newPage();
  // Suppress console noise from the target app
  page.on('console', () => {});
  page.on('pageerror', (err) => log(`Page error: ${err.message}`, 'WARN'));
  const summary = { passed: true, audits: [] };
  try {
    // ── 1. Authenticate & navigate ─────────────────────────────────────────
    await login(page);
    await navigateToApps(page);
    // ── 2. Light mode audit ────────────────────────────────────────────────
    await page.screenshot({
      path: path.join(CONFIG.artifactsDir, 'apps_card_grid_audit_desktop.png'),
      fullPage: false,
    });
    log('Screenshot: apps_card_grid_audit_desktop.png');
    const lightAudit = await runAudit(page, 'light');
    summary.audits.push(lightAudit);
    // Close-up of first card
    const firstCardHandles = await page.$$('.o_modules_kanban .o_kanban_record');
    if (firstCardHandles.length > 0) {
      const firstCardBox = await firstCardHandles[0].boundingBox();
      if (firstCardBox) {
        await page.screenshot({
          path: path.join(CONFIG.artifactsDir, 'apps_card_closeup_verified.png'),
          clip: {
            x: Math.max(0, firstCardBox.x - 8),
            y: Math.max(0, firstCardBox.y - 8),
            width: Math.min(firstCardBox.width + 16, CONFIG.viewport.width),
            height: Math.min(firstCardBox.height + 16, CONFIG.viewport.height),
          },
        });
        log('Screenshot: apps_card_closeup_verified.png');
      }
    }
    // ── 3. Dark mode audit ─────────────────────────────────────────────────
    log('Enabling dark mode (body.o_dark_mode)…');
    await page.evaluate(() => {
      document.body.classList.add('o_dark_mode');
      // Also set color-scheme for completeness
      document.documentElement.style.colorScheme = 'dark';
    });
    // Small settle time for CSS transitions
    await page.waitForTimeout(600);
    await page.screenshot({
      path: path.join(CONFIG.artifactsDir, 'apps_card_grid_audit_dark.png'),
      fullPage: false,
    });
    log('Screenshot: apps_card_grid_audit_dark.png');
    const darkAudit = await runAudit(page, 'dark');
    summary.audits.push(darkAudit);
    // ── 4. Aggregate results ───────────────────────────────────────────────
    for (const audit of summary.audits) {
      for (const card of audit.results) {
        if (!card.passed) {
          summary.passed = false;
        }
      }
    }
    // Tally assertion counts
    summary.stats = summary.audits.map((audit) => {
      const allAssertions = audit.results.flatMap((c) => c.assertions);
      const failedAssertions = allAssertions.filter((a) => !a.passed);
      return {
        mode: audit.mode,
        totalCards: audit.totalCards,
        auditedCards: audit.auditedCards,
        totalAssertions: allAssertions.length,
        failedAssertions: failedAssertions.length,
        passedAssertions: allAssertions.length - failedAssertions.length,
        failures: failedAssertions,
      };
    });
  } catch (err) {
    log(`Fatal error: ${err.message}`, 'ERROR');
    summary.passed = false;
    summary.fatalError = err.message;
    // Capture error state screenshot
    await page.screenshot({
      path: path.join(CONFIG.artifactsDir, 'apps_card_grid_audit_error.png'),
    }).catch(() => {});
  } finally {
    await browser.close();
  }
  // ── 5. Output JSON summary ───────────────────────────────────────────────
  const jsonOutput = JSON.stringify(summary, null, 2);
  console.log('\n' + '═'.repeat(60));
  console.log('AUDIT SUMMARY');
  console.log('═'.repeat(60));
  console.log(jsonOutput);
  // Write JSON to artifacts
  fs.writeFileSync(
    path.join(CONFIG.artifactsDir, 'apps_card_grid_audit_report.json'),
    jsonOutput,
    'utf8'
  );
  if (summary.stats) {
    for (const stat of summary.stats) {
      console.log(`\n[${stat.mode.toUpperCase()} MODE]`);
      console.log(`  Cards audited   : ${stat.auditedCards} / ${stat.totalCards}`);
      console.log(`  Assertions      : ${stat.totalAssertions}`);
      console.log(`  Passed          : ${stat.passedAssertions}`);
      console.log(`  Failed          : ${stat.failedAssertions}`);
      if (stat.failures.length > 0) {
        console.log('  Failures:');
        for (const f of stat.failures) {
          console.log(`    • ${f.name}: ${f.detail}`);
        }
      }
    }
  }
  console.log('\n' + (summary.passed ? '✅ ALL ASSERTIONS PASSED' : '❌ SOME ASSERTIONS FAILED'));
  console.log(`Artifacts written to: ${CONFIG.artifactsDir}\n`);
  process.exit(summary.passed ? 0 : 1);
})();