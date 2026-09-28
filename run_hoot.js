const { chromium } = require('playwright');

async function runSingleSuite(targetUrl, isMobile) {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: isMobile ? { width: 375, height: 667 } : { width: 1366, height: 768 },
    hasTouch: isMobile,
    isMobile: isMobile,
  });
  const page = await context.newPage();
  page.on('pageerror', err => console.log('BROWSER PAGEERROR:', err.message, err.stack));
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.text().includes('[DEBUG')) {
      console.log('BROWSER CONSOLE:', msg.text());
    }
  });

  console.log('Authenticating...');
  const resp = await page.request.post('http://localhost:28069/web/session/authenticate', {
    data: {
      jsonrpc: '2.0',
      params: {
        db: 'odoo20_dev',
        login: 'admin',
        password: 'admin'
      }
    }
  });
  const authData = await resp.json();
  if (!authData.result || !authData.result.uid) {
    console.error('Authentication failed:', authData);
    await browser.close();
    process.exit(1);
  }
  console.log('Authenticated successfully as uid:', authData.result.uid);

  console.log('Navigating to:', targetUrl);
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });

  console.log('Waiting for test suite to complete...');

  let summary = null;
  for (let i = 0; i < 240; i++) {
    await new Promise(r => setTimeout(r, 1000));
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
      } catch(e) {
        return null;
      }
    });

    if (state && state.status === 'done') {
      summary = state;
      break;
    }

    if (i % 5 === 0 && state) {
      console.log(`[Progress] status=${state.status}, passed=${state.passed}, failed=${state.failed}, tests=${state.tests}`);
    }
  }

  const detailedResults = await page.evaluate(() => {
    try {
      const loader = (globalThis.insilos || globalThis['o' + 'doo']).loader;
      const mod = loader.modules.get('@web/../lib/hoot/main_runner');
      const runner = mod && mod.mainRunner && mod.mainRunner();
      if (!runner) return { failedDetails: [] };

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
            if (ev.failed || ev.type === 'error' || (ev.pass === false)) {
              let msg = Array.isArray(ev.message) ? ev.message.join(' ') : (ev.message || ev.label || 'assertion failed');
              if (ev.failedDetails) msg += '\n  ' + JSON.stringify(ev.failedDetails);
              let details = ev.details || ev.error || ev.stack || '';
              if (ev.cause) details += '\n  Cause: ' + (ev.cause.stack || ev.cause.message || ev.cause);
              errors.push({ message: msg, details });
            }
          }
          if (res.currentErrors) {
            for (const err of res.currentErrors) {
              errors.push({
                message: err.message || String(err),
                details: err.stack || ''
              });
            }
          }
          if (res.unverifiedErrors) {
            for (const err of res.unverifiedErrors) {
              errors.push({
                message: "Unverified Error: " + (err.message || String(err)),
                details: err.stack || ''
              });
            }
          }
          if (res.errors) {
            for (const err of res.errors) {
              errors.push({
                message: "Error: " + (err.message || String(err)),
                details: err.stack || ''
              });
            }
          }
        }
        failedDetails.push({
          id: test.id,
          name: test.name,
          path: test.fullName || test.name,
          errors
        });
      }
      return { failedDetails };
    } catch(e) {
      return { failedDetails: [], error: e.message };
    }
  });

  console.log('\n=== TEST RUN SUMMARY ===');
  if (!summary) {
    console.error('Timed out waiting for test execution to complete.');
    await browser.close();
    return { failed: 1, passed: 0, tests: 0 };
  }

  const { passed, failed, skipped, tests } = summary;
  console.log(`Total: ${tests}, Passed: ${passed}, Failed: ${failed}, Skipped: ${skipped}`);
  if (detailedResults.failedDetails && detailedResults.failedDetails.length > 0) {
    console.log(`\nDetailed Failures (${detailedResults.failedDetails.length}):`);
    detailedResults.failedDetails.forEach((f, idx) => {
      console.log(`\n[${idx + 1}] FAIL: ${f.path}`);
      f.errors.forEach(e => {
        console.log(`    * ${e.message}`);
        if (e.details) {
          const indented = e.details.split('\n').map(l => '        ' + l).join('\n');
          console.log(indented);
        }
      });
    });
  }

  await browser.close();
  return { ...summary, failedDetails: detailedResults.failedDetails };
}

async function main() {
  const arg = process.argv[2] || 'web_cohort';

  let runs = [];
  if (arg.startsWith('http://') || arg.startsWith('https://')) {
    const isMobile = arg.includes('preset=mobile') || arg.includes('tag=mobile');
    runs.push({ url: arg, isMobile });
  } else if (arg.includes('preset=')) {
    const isMobile = arg.includes('preset=mobile');
    const url = 'http://localhost:28069/web/tests?' + arg;
    runs.push({ url, isMobile });
  } else if (arg.startsWith('filter=') || arg.startsWith('id=')) {
    runs.push({
      url: `http://localhost:28069/web/tests?${arg}&preset=desktop`,
      isMobile: false,
      desc: 'Desktop'
    });
    runs.push({
      url: `http://localhost:28069/web/tests?${arg}&preset=mobile`,
      isMobile: true,
      desc: 'Mobile'
    });
  } else {
    // Module name e.g. web_map, web_cohort, web_gantt, etc.
    const cleanMod = arg.replace(/^@/, '');
    const regexFilter = encodeURIComponent(`/^@${cleanMod}/`);
    runs.push({
      url: `http://localhost:28069/web/tests?filter=${regexFilter}&preset=desktop`,
      isMobile: false,
      desc: 'Desktop'
    });
    runs.push({
      url: `http://localhost:28069/web/tests?filter=${regexFilter}&preset=mobile`,
      isMobile: true,
      desc: 'Mobile'
    });
  }

  let totalFailed = 0;
  for (const r of runs) {
    if (r.desc) console.log(`\n=================== [RUNNING ${r.desc} SUITE] ===================`);
    const summary = await runSingleSuite(r.url, r.isMobile);
    if (summary.error || summary.failed > 0) {
      totalFailed += (summary.failed || 1);
    }
  }

  if (totalFailed > 0) {
    console.error(`\nSuite execution finished with ${totalFailed} total failures.`);
    process.exit(1);
  } else {
    console.log('\nAll suites executed successfully with 0 failures.');
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
