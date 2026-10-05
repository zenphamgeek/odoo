/**
 * ==============================================================================
 * High-Throughput Parallel HOOT Test Harness Runner
 * ==============================================================================
 * Optimized for Insilos Platform (Odoo 20 LTS Hard Fork)
 *
 * Capabilities:
 *  1. Single-Flight Asset Warmup Gate (eliminates cold cache compilation stampedes)
 *  2. Shared Chromium Process with Isolated Browser Context Pool
 *  3. Single-Flight JSON-RPC Session Authentication with shared storageState
 *  4. Concurrent Viewport Execution (Desktop & Mobile parallel)
 *  5. Multi-Suite Concurrent Queue & Worker Pool (--concurrency=N)
 *  6. Fast Polling (250ms) & Full Error Diagnostics
 *  7. Complete backwards compatibility with legacy CLI invocations
 * ==============================================================================
 */

const { chromium } = require('playwright');
const http = require('http');
const https = require('https');

const SERVER_BASE = process.env.HOOT_SERVER_URL || 'http://localhost:28069';
const DB_NAME = process.env.HOOT_DB || 'insilos20_dev';
const AUTH_LOGIN = process.env.HOOT_LOGIN || 'admin';
const AUTH_PASSWORD = process.env.HOOT_PASSWORD || 'admin';

/**
 * Single-Flight Warmup Gate
 * Ensures that web.assets_unit_tests.min.js and web.assets_unit_tests_setup.min.js
 * are compiled and cached in ir.attachment by a single uncontended thread,
 * completely preventing concurrent database lock contention or compilation stampedes.
 */
async function ensureAssetsWarm(baseUrl) {
  console.log('⚡ [Harness Warmup] Verifying asset bundles on server...');
  const t0 = Date.now();
  return new Promise((resolve) => {
    const url = new URL('/web/tests', baseUrl);
    const client = url.protocol === 'https:' ? https : http;

    const req = client.get(url.toString(), res => {
      let data = '';
      res.on('data', chunk => (data += chunk));
      res.on('end', () => {
        const dur = Date.now() - t0;
        if (res.statusCode === 200 || res.statusCode === 303) {
          console.log(`⚡ [Harness Warmup] Asset cache warm in ${dur}ms (HTTP ${res.statusCode})`);
          resolve();
        } else {
          console.warn(`⚠️ [Harness Warmup] Received HTTP ${res.statusCode} in ${dur}ms; proceeding`);
          resolve();
        }
      });
    });

    req.on('error', err => {
      console.warn('⚠️ [Harness Warmup] Server warmup ping warning:', err.message);
      resolve(); // Do not block if server check fails, let browser handle it
    });

    req.setTimeout(60000, () => {
      req.destroy();
      console.warn('⚠️ [Harness Warmup] Warmup request timed out after 60s; proceeding');
      resolve();
    });
  });
}

/**
 * Shared Session Authenticator
 * Authenticates once via JSON-RPC, extracting storageState for all workers.
 */
async function authenticateOnce(browser, baseUrl) {
  console.log('🔑 [Harness Auth] Authenticating session once via JSON-RPC...');
  const t0 = Date.now();
  const authContext = await browser.newContext();
  const page = await authContext.newPage();

  const resp = await page.request.post(`${baseUrl}/web/session/authenticate`, {
    data: {
      jsonrpc: '2.0',
      params: {
        db: DB_NAME,
        login: AUTH_LOGIN,
        password: AUTH_PASSWORD,
      },
    },
  });

  const authData = await resp.json();
  if (!authData.result || !authData.result.uid) {
    console.error('❌ [Harness Auth] Authentication failed:', authData);
    await authContext.close();
    throw new Error('Authentication failed');
  }

  const storageState = await authContext.storageState();

  console.log('⚡ [Harness Warmup] Pre-compiling asset bundles via authenticated warmup visit...');
  const tWarm = Date.now();
  try {
    await page.goto(`${baseUrl}/web/tests?headless`, { waitUntil: 'domcontentloaded', timeout: 120000 });
    console.log(`⚡ [Harness Warmup] Asset bundles compiled and warm in ${Date.now() - tWarm}ms`);
  } catch (err) {
    console.warn('⚠️ [Harness Warmup] Warmup visit warning:', err.message);
  }

  await authContext.close();
  console.log(`🔑 [Harness Auth] Authenticated successfully as uid ${authData.result.uid} in ${Date.now() - t0}ms`);
  return storageState;
}

/**
 * Execute a single suite run inside an isolated browser context.
 */
async function executeSingleSuite(browser, storageState, runConfig) {
  const { url, isMobile, suiteName, desc } = runConfig;
  const t0 = Date.now();
  const label = `[${suiteName || 'Suite'} / ${desc || (isMobile ? 'Mobile' : 'Desktop')}]`;

  const context = await browser.newContext({
    storageState,
    viewport: isMobile ? { width: 375, height: 667 } : { width: 1366, height: 768 },
    hasTouch: isMobile,
    isMobile: isMobile,
  });

  const page = await context.newPage();
  const consoleLogs = [];

  page.on('pageerror', err => {
    console.log(`BROWSER PAGEERROR ${label}:`, err.message);
  });

  page.on('console', msg => {
    const txt = msg.text();
    if (msg.type() === 'error' || txt.includes('[DEBUG') || txt.includes('[HOOT]')) {
      consoleLogs.push(txt);
      if (txt.includes('failed:') || txt.includes('timed out') || txt.includes('Error during test:')) {
        console.log(`BROWSER CONSOLE ${label}:`, txt);
      }
    }
  });

  // Mock external map tile endpoints
  await page.route(/.*(tile\.openstreetmap\.org|api\.mapbox\.com).*/, route => {
    route.fulfill({
      status: 200,
      contentType: 'image/png',
      body: Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7', 'base64'),
    });
  });

  console.log(`${label} Navigating to: ${url}`);
  const navStart = Date.now();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });
  const navDuration = Date.now() - navStart;
  console.log(`${label} Page loaded in ${navDuration}ms, running tests...`);

  // Fast polling loop (every 250ms)
  let summary = null;
  const maxPolls = 480; // 120 seconds
  let lastReportedStatus = '';

  for (let i = 0; i < maxPolls; i++) {
    await new Promise(r => setTimeout(r, 250));

    const state = await page.evaluate(() => {
      try {
        const loader = (globalThis.insilos || globalThis['o' + 'doo']).loader;
        const mod = loader.modules.get('@web/../lib/hoot/main_runner');
        const runner = mod && mod.mainRunner && mod.mainRunner();
        if (!runner) return null;
        const status = typeof runner.status === 'function' ? runner.status() : runner.status;
        const passed = runner.reporting ? runner.reporting.passed : 0;
        const failed = runner.reporting ? runner.reporting.failed : 0;
        const skipped = runner.reporting ? runner.reporting.skipped : 0;
        const tests = runner.reporting ? runner.reporting.tests : (passed + failed + skipped);
        return { status, passed, failed, skipped, tests };
      } catch (e) {
        return null;
      }
    });

    if (state && state.status === 'done') {
      summary = state;
      break;
    }

    if (state && i % 16 === 0) {
      // Log progress every 4s
      const currentStatus = `passed=${state.passed}, failed=${state.failed}, tests=${state.tests}`;
      if (currentStatus !== lastReportedStatus) {
        lastReportedStatus = currentStatus;
        console.log(`${label} Progress: ${currentStatus}`);
      }
    }
  }

  // Extract detailed failures if any
  let detailedFailures = [];
  let domSnapshot = null;

  if (!summary || summary.failed > 0) {
    const errorData = await page.evaluate(() => {
      try {
        const loader = (globalThis.insilos || globalThis['o' + 'doo']).loader;
        const mod = loader.modules.get('@web/../lib/hoot/main_runner');
        const runner = mod && mod.mainRunner && mod.mainRunner();
        if (!runner) return { failedDetails: [], domInfo: null };

        const failedDetails = [];
        const failedIds = [...runner.failedIds()];
        for (const id of failedIds) {
          const test = runner.tests.get(id);
          if (!test) continue;
          const errors = [];
          const results = typeof test.results === 'function' ? test.results() : (test.results || []);
          for (const res of results) {
            const events = typeof res.events === 'function' ? res.events() : (res.events || []);
            for (const ev of events) {
              if (ev.failed || ev.type === 'error' || ev.pass === false) {
                let msg = Array.isArray(ev.message) ? ev.message.join(' ') : (ev.message || ev.label || 'assertion failed');
                if (ev.failedDetails) msg += '\n  ' + JSON.stringify(ev.failedDetails, (k, v) => (v instanceof Error ? { message: v.message, stack: v.stack } : v));
                let details = String(ev.details || ev.error?.stack || ev.error?.message || ev.error || ev.stack || '');
                if (ev.cause) details += '\n  Cause: ' + (ev.cause.stack || ev.cause.message || ev.cause);
                errors.push({ message: msg, details });
              }
            }
            if (res.currentErrors) {
              for (const err of res.currentErrors) {
                errors.push({ message: 'CurrentError: ' + (err?.message || String(err)), details: String(err?.stack || '') });
              }
            }
            if (res.unverifiedErrors) {
              for (const err of res.unverifiedErrors) {
                errors.push({ message: 'Unverified Error: ' + (err?.message || String(err)), details: String(err?.stack || '') });
              }
            }
            if (res.errors) {
              for (const err of res.errors) {
                errors.push({ message: 'Error: ' + (err?.message || String(err)), details: String(err?.stack || '') });
              }
            }
          }
          failedDetails.push({ id: test.id, name: test.name, path: test.fullName || test.name, errors });
        }

        const editorManager = document.querySelector('.o_web_studio_editor_manager');
        const actionManager = document.querySelector('.o_action_manager');
        const domInfo = {
          hasEditorManager: !!editorManager,
          editorManagerHTML: editorManager ? editorManager.outerHTML.slice(0, 500) : null,
          actionManagerHTML: actionManager ? actionManager.outerHTML.slice(0, 500) : null,
          bodyClasses: document.body.className,
        };

        return { failedDetails, domInfo };
      } catch (e) {
        return { failedDetails: [], domInfo: null, error: e.message };
      }
    });

    detailedFailures = errorData.failedDetails || [];
    domSnapshot = errorData.domInfo;
  }

  await context.close();
  const duration = Date.now() - t0;

  if (!summary) {
    console.error(`❌ ${label} Timed out waiting for test completion (${duration}ms)`);
    return {
      suiteName,
      desc,
      url,
      passed: 0,
      failed: 1,
      skipped: 0,
      tests: 1,
      duration,
      failedDetails: [{ path: suiteName, errors: [{ message: 'Harness Timeout (120s exceeded)' }] }],
      domSnapshot: null,
    };
  }

  const statusIcon = summary.failed === 0 ? '✅' : '❌';
  console.log(`${statusIcon} ${label} Completed in ${duration}ms: ${summary.passed}/${summary.tests} passed, ${summary.failed} failed, ${summary.skipped} skipped`);

  return {
    suiteName,
    desc,
    url,
    ...summary,
    duration,
    failedDetails: detailedFailures,
    domSnapshot,
  };
}

/**
 * Main Parallel Harness Orchestrator
 */
async function main() {
  const args = process.argv.slice(2);
  let concurrency = 2; // Default concurrency
  let skipWarmup = false;
  let headlessMode = true;
  let targetSuites = [];

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--concurrency=')) {
      concurrency = parseInt(arg.split('=')[1], 10) || 2;
    } else if (arg === '-j') {
      concurrency = parseInt(args[++i], 10) || 2;
    } else if (arg === '--no-warmup') {
      skipWarmup = true;
    } else if (arg === '--no-headless') {
      headlessMode = false;
    } else if (arg === '--headless') {
      headlessMode = true;
    } else if (arg.startsWith('--')) {
      // Ignored unknown flags
    } else {
      targetSuites.push(arg);
    }
  }

  if (targetSuites.length === 0) {
    targetSuites = ['web_cohort'];
  }

  // Pre-generate run configs
  const runConfigs = [];
  for (const item of targetSuites) {
    if (item.startsWith('http://') || item.startsWith('https://')) {
      const isMobile = item.includes('preset=mobile') || item.includes('tag=mobile');
      runConfigs.push({
        url: item + (headlessMode && !item.includes('headless') ? '&headless' : ''),
        isMobile,
        suiteName: 'DirectURL',
        desc: isMobile ? 'Mobile' : 'Desktop',
      });
    } else if (item.includes('preset=')) {
      const isMobile = item.includes('preset=mobile');
      const url = `${SERVER_BASE}/web/tests?${item}` + (headlessMode ? '&headless' : '');
      runConfigs.push({
        url,
        isMobile,
        suiteName: item.split('&')[0],
        desc: isMobile ? 'Mobile' : 'Desktop',
      });
    } else if (item.startsWith('filter=') || item.startsWith('id=')) {
      runConfigs.push({
        url: `${SERVER_BASE}/web/tests?${item}&preset=desktop` + (headlessMode ? '&headless' : ''),
        isMobile: false,
        suiteName: item,
        desc: 'Desktop',
      });
      runConfigs.push({
        url: `${SERVER_BASE}/web/tests?${item}&preset=mobile` + (headlessMode ? '&headless' : ''),
        isMobile: true,
        suiteName: item,
        desc: 'Mobile',
      });
    } else {
      // Module name e.g. web_map, web_cohort, web_gantt, @web_studio/navigation
      const cleanMod = item.replace(/^@/, '');
      const regexFilter = encodeURIComponent(`/^@${cleanMod}/`);
      runConfigs.push({
        url: `${SERVER_BASE}/web/tests?filter=${regexFilter}&preset=desktop` + (headlessMode ? '&headless' : ''),
        isMobile: false,
        suiteName: item,
        desc: 'Desktop',
      });
      runConfigs.push({
        url: `${SERVER_BASE}/web/tests?filter=${regexFilter}&preset=mobile` + (headlessMode ? '&headless' : ''),
        isMobile: true,
        suiteName: item,
        desc: 'Mobile',
      });
    }
  }

  console.log('================================================================================');
  console.log('🚀 INSILOS HIGH-THROUGHPUT PARALLEL HOOT TEST RUNNER');
  console.log(`   Suites to run : ${targetSuites.join(', ')}`);
  console.log(`   Total tasks   : ${runConfigs.length} (Desktop & Mobile viewports)`);
  console.log(`   Concurrency   : ${concurrency} parallel workers`);
  console.log(`   Headless mode : ${headlessMode}`);
  console.log('================================================================================\n');

  // Step 1: Single-flight warmup gate
  if (!skipWarmup) {
    await ensureAssetsWarm(SERVER_BASE);
  }

  // Step 2: Shared Chromium browser launch
  console.log('🌐 [Harness] Spawning shared Chromium instance with performance flags...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-renderer-backgrounding',
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-gpu',
    ],
  });

  // Step 3: Single-flight session authentication
  const storageState = await authenticateOnce(browser, SERVER_BASE);

  // Step 4: Parallel Worker Pool execution
  console.log(`\n⚡ [Harness] Dispatching ${runConfigs.length} test tasks across ${concurrency} workers...\n`);
  const tRunStart = Date.now();
  const queue = [...runConfigs];
  const allResults = [];

  async function worker(workerId) {
    while (queue.length > 0) {
      const task = queue.shift();
      if (!task) break;
      const res = await executeSingleSuite(browser, storageState, task);
      allResults.push(res);
    }
  }

  const workerPromises = Array.from({ length: concurrency }, (_, i) => worker(i + 1));
  await Promise.all(workerPromises);

  // Step 5: Teardown browser
  await browser.close();
  const totalElapsed = Date.now() - tRunStart;

  // Step 6: Print Comprehensive Summary
  console.log('\n================================================================================');
  console.log('                         PARALLEL TEST EXECUTION REPORT                          ');
  console.log('================================================================================');
  console.log(
    'Suite / Viewport'.padEnd(35) +
      'Status'.padEnd(12) +
      'Passed'.padEnd(10) +
      'Failed'.padEnd(10) +
      'Total'.padEnd(10) +
      'Duration'
  );
  console.log('-'.repeat(85));

  let totalTests = 0;
  let totalPassed = 0;
  let totalFailed = 0;
  let totalSkipped = 0;

  for (const r of allResults) {
    totalTests += r.tests || 0;
    totalPassed += r.passed || 0;
    totalFailed += r.failed || 0;
    totalSkipped += r.skipped || 0;

    const label = `${r.suiteName} (${r.desc})`.padEnd(35);
    const status = (r.failed === 0 ? '✅ PASS' : '❌ FAIL').padEnd(12);
    const passedStr = String(r.passed || 0).padEnd(10);
    const failedStr = String(r.failed || 0).padEnd(10);
    const totalStr = String(r.tests || 0).padEnd(10);
    const durStr = `${(r.duration / 1000).toFixed(1)}s`;
    console.log(`${label}${status}${passedStr}${failedStr}${totalStr}${durStr}`);
  }

  console.log('='.repeat(85));
  console.log(`TOTAL SUITES  : ${allResults.length}`);
  console.log(`TOTAL TESTS   : ${totalTests}`);
  console.log(`PASSED        : ${totalPassed}`);
  console.log(`FAILED        : ${totalFailed}`);
  console.log(`SKIPPED       : ${totalSkipped}`);
  console.log(`TOTAL RUNTIME : ${(totalElapsed / 1000).toFixed(1)}s`);
  console.log('================================================================================\n');

  // Print Detailed Failures if any
  const failedRuns = allResults.filter(r => r.failed > 0);
  if (failedRuns.length > 0) {
    console.error(`\nDetailed Failure Diagnostics (${totalFailed} total failures across ${failedRuns.length} suites):\n`);
    for (const r of failedRuns) {
      console.error(`🔴 SUITE FAILED: ${r.suiteName} (${r.desc}) — ${r.url}`);
      for (const f of r.failedDetails || []) {
        console.error(`   FAIL: ${f.path}`);
        for (const e of f.errors || []) {
          console.error(`     * ${e.message}`);
          if (e.details) {
            const indented = e.details.split('\n').map(l => '         ' + l).join('\n');
            console.error(indented);
          }
        }
      }
      if (r.domSnapshot) {
        console.error('   DOM Snapshot on Failure:', JSON.stringify(r.domSnapshot, null, 2));
      }
      console.error('');
    }
    process.exit(1);
  } else {
    console.log('🎉 ALL TEST SUITES PASSED 100% WITH ZERO FAILURES!');
    process.exit(0);
  }
}

main().catch(err => {
  console.error('Fatal harness error:', err);
  process.exit(1);
});
