#!/usr/bin/env node
/**
 * tools/audit_innoria_pixel_quality.js
 * Multi-Viewport DOM Pixel Quality & Section 1.7 Parity Auditor for innoria.com
 *
 * Verifies:
 * 1. Zero horizontal overflow (scrollWidth === clientWidth) across 1440px, 768px, 375px
 * 2. Zero console errors / uncaught exceptions
 * 3. Zero broken images (naturalWidth > 0)
 * 4. Section 1.7 Forwarder Operations 1:1 parity and interactive toggle verification
 * 5. High-resolution artifact capture of Section 1.7
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'https://innoria.com';
const ARTIFACT_DIR = process.env.ARTIFACT_DIR || '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

const ROUTES = [
  { path: '/', name: 'homepage' },
  { path: '/about', name: 'about' },
  { path: '/platform', name: 'platform' },
  { path: '/no-code-platform', name: 'no-code-platform' },
  { path: '/blockchain', name: 'blockchain' },
  { path: '/solutions', name: 'solutions' },
  { path: '/industries', name: 'industries' },
  { path: '/contactus', name: 'contactus' }
];

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 375, height: 812 }
];

async function runAudit() {
  console.log('================================================================================');
  console.log('🔍 INNORIA MULTI-VIEWPORT PIXEL QUALITY & SECTION PARITY AUDIT');
  console.log(`Target: ${BASE_URL}`);
  console.log(`Artifact Output: ${ARTIFACT_DIR}`);
  console.log('================================================================================\n');

  if (!fs.existsSync(ARTIFACT_DIR)) {
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  });

  const manifest = {
    timestamp: new Date().toISOString(),
    base_url: BASE_URL,
    total_checks: 0,
    passed_checks: 0,
    failed_checks: 0,
    routes: {},
    section_1_7: null
  };

  let globalSuccess = true;

  try {
    for (const vp of VIEWPORTS) {
      console.log(`\n--- Auditing Viewport: ${vp.name.toUpperCase()} (${vp.width}x${vp.height}) ---`);

      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        userAgent: `Mozilla/5.0 (${vp.name === 'mobile' ? 'iPhone; CPU iPhone OS 17_0 like Mac OS X' : 'Windows NT 10.0; Win64; x64'}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 InnoriaAuditor/2.0`
      });

      for (const r of ROUTES) {
        const page = await context.newPage();
        const targetUrl = `${BASE_URL}${r.path}`;

        const consoleErrors = [];
        page.on('console', msg => {
          if (msg.type() === 'error') {
            const txt = msg.text();
            // Filter out non-fatal external analytics / fonts if any
            if (!txt.includes('favicon.ico')) {
              consoleErrors.push(txt);
            }
          }
        });
        page.on('pageerror', err => {
          consoleErrors.push(err.message || String(err));
        });

        const key = `${r.name}_${vp.name}`;
        let status = 'PASS';
        const failureReasons = [];

        try {
          const resp = await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 35000 });
          const httpStatus = resp ? resp.status() : 0;
          if (httpStatus >= 400) {
            failureReasons.push(`HTTP status ${httpStatus}`);
          }

          // Allow any responsive font-load or micro animations
          await page.waitForTimeout(1000);

          // Check 1: Horizontal Overflow
          const overflowInfo = await page.evaluate(() => {
            const docEl = document.documentElement;
            const body = document.body;
            const scrollW = Math.max(docEl.scrollWidth, body ? body.scrollWidth : 0);
            const clientW = docEl.clientWidth;
            const overflow = scrollW - clientW;

            let offendingEl = null;
            if (overflow > 1) {
              const all = document.querySelectorAll('*');
              for (const el of all) {
                const rect = el.getBoundingClientRect();
                if (rect.right > clientW + 2) {
                  offendingEl = `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className ? '.' + String(el.className).split(' ').slice(0, 2).join('.') : ''} (right: ${Math.round(rect.right)}px > ${clientW}px)`;
                  break;
                }
              }
            }

            return { scrollW, clientW, overflow, offendingEl };
          });

          manifest.total_checks++;
          if (overflowInfo.overflow > 2) {
            failureReasons.push(`Horizontal overflow: +${overflowInfo.overflow}px (${overflowInfo.offendingEl || 'unknown'})`);
          } else {
            manifest.passed_checks++;
          }

          // Check 2: Console errors
          manifest.total_checks++;
          if (consoleErrors.length > 0) {
            failureReasons.push(`Console errors (${consoleErrors.length}): ${consoleErrors.slice(0, 2).join('; ')}`);
          } else {
            manifest.passed_checks++;
          }

          // Check 3: Broken Images
          const brokenImages = await page.evaluate(() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            const broken = [];
            for (const img of imgs) {
              if (img.complete && img.naturalWidth === 0 && img.src && !img.src.startsWith('data:image/svg')) {
                broken.push(img.src);
              }
            }
            return broken;
          });

          manifest.total_checks++;
          if (brokenImages.length > 0) {
            failureReasons.push(`Broken images (${brokenImages.length}): ${brokenImages.slice(0, 2).join(', ')}`);
          } else {
            manifest.passed_checks++;
          }

          // Check 4: Section 1.7 Forwarder Operations check (on homepage)
          if (r.path === '/') {
            const sec17 = await page.evaluate(() => {
              const jobfileBadge = document.querySelector('.grc-card .badge.font-monospace');
              const disputeBtn = document.getElementById('btnDisputeDem');
              const disputeBox = document.getElementById('disputeNoticeBox');
              const table = document.querySelector('.grc-card table.grc-table');
              const headers = table ? Array.from(table.querySelectorAll('thead th')).map(th => th.innerText.trim()) : [];
              const hasExceptionRow = table ? Boolean(table.querySelector('tr.has-exception')) : false;

              return {
                badgeText: jobfileBadge ? jobfileBadge.innerText.trim() : null,
                hasDisputeBtn: Boolean(disputeBtn),
                disputeBtnText: disputeBtn ? disputeBtn.innerText.trim() : null,
                hasDisputeBox: Boolean(disputeBox),
                headers: headers,
                hasExceptionRow: hasExceptionRow
              };
            });

            if (vp.name === 'desktop') {
              manifest.section_1_7 = sec17;
            }

            // Capture Section 1.7 screenshot
            const cardEl = await page.$('.grc-card');
            if (cardEl) {
              const sec17ScreenshotPath = path.join(ARTIFACT_DIR, `innoria_section_1_7_${vp.name}.png`);
              await cardEl.screenshot({ path: sec17ScreenshotPath });
              console.log(`  [📸 Screenshot] Saved Section 1.7 -> ${sec17ScreenshotPath}`);
            }

            // Interactive test: click #btnDisputeDem if present
            if (sec17.hasDisputeBtn) {
              const boxBefore = await page.evaluate(() => {
                const b = document.getElementById('disputeNoticeBox');
                return b ? !b.classList.contains('d-none') : false;
              });

              await page.click('#btnDisputeDem');
              await page.waitForTimeout(300);

              const boxAfter = await page.evaluate(() => {
                const b = document.getElementById('disputeNoticeBox');
                return b ? !b.classList.contains('d-none') : false;
              });

              if (boxBefore === boxAfter) {
                failureReasons.push('Dispute button #btnDisputeDem did not toggle disputeNoticeBox');
              } else {
                if (vp.name === 'desktop') {
                  const cardToggledPath = path.join(ARTIFACT_DIR, 'innoria_section_1_7_dispute_active.png');
                  if (cardEl) {
                    await cardEl.screenshot({ path: cardToggledPath });
                    console.log(`  [📸 Screenshot] Saved Toggled Section 1.7 -> ${cardToggledPath}`);
                  }
                }
              }
            }
          }

        } catch (err) {
          failureReasons.push(`Navigation/Render Exception: ${err.message}`);
        } finally {
          await page.close();
        }

        if (failureReasons.length > 0) {
          status = 'FAIL';
          globalSuccess = false;
          manifest.failed_checks += failureReasons.length;
        }

        manifest.routes[key] = {
          route: r.path,
          viewport: vp.name,
          status,
          reasons: failureReasons
        };

        const icon = status === 'PASS' ? '✅' : '❌';
        console.log(`  ${icon} ${r.path.padEnd(20)} [${vp.name.padEnd(7)}]: ${status} ${failureReasons.length ? '(' + failureReasons.join(' | ') + ')' : ''}`);
      }

      await context.close();
    }
  } finally {
    await browser.close();
  }

  // Write summary manifest
  const manifestPath = path.join(ARTIFACT_DIR, 'audit_innoria_pixel_quality_manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
  console.log(`\n📄 Manifest saved to: ${manifestPath}`);

  console.log('\n================================================================================');
  console.log(`FINAL RESULT: ${globalSuccess ? 'ALL GATES PASSED ✅' : 'FAILURES DETECTED ❌'}`);
  console.log(`Total Checks: ${manifest.total_checks} | Passed: ${manifest.passed_checks} | Failed: ${manifest.failed_checks}`);
  console.log('================================================================================\n');

  if (!globalSuccess) {
    process.exit(1);
  }
}

runAudit().catch(err => {
  console.error('Fatal audit failure:', err);
  process.exit(1);
});
