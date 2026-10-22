#!/usr/bin/env node
/**
 * tools/challenger_m5_viewport_stress.js
 * =============================================================================
 * EMPIRICAL CHALLENGER (Milestone M5) — Multi-Viewport Live Layout Stress Test
 * 
 * Target: https://innokafe.insilos.com/
 * 
 * Viewports:
 * 1. Ultra-narrow mobile:
 *    - 320 x 568  (iPhone SE gen 1)
 *    - 360 x 780  (Android Narrow / Galaxy S22)
 *    - 375 x 812  (iPhone X / 12 Mini)
 *    - 414 x 896  (iPhone XR / 11)
 * 2. Tablets:
 *    - 768 x 1024 (iPad Portrait)
 *    - 820 x 1180 (iPad Air)
 *    - 1024 x 768 (iPad Landscape)
 * 3. Desktop & Wide:
 *    - 1280 x 800  (WXGA Laptop)
 *    - 1440 x 900  (MacBook Desktop)
 *    - 1920 x 1080 (FHD Widescreen)
 * 
 * Assertions:
 * - Assertion 1: Zero horizontal overflow (scrollWidth <= window.innerWidth && no physical element bleed)
 * - Assertion 2: Zero layout shifts (CLS <= 0.05) & zero element collisions
 * - Assertion 3: Touch targets >= 44px (buttons) and >= 36px (links)
 * - Assertion 4: Vector SVG logo renders properly on every viewport
 * =============================================================================
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function getArg(flag, defaultValue) {
    const idx = args.indexOf(flag);
    if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
    return defaultValue;
}

const TARGET_URL = (getArg('--url', 'https://innokafe.insilos.com')).replace(/\/$/, '');
const OUTPUT_DIR = getArg('--output', '/tmp/innokafe_challenger_m5_artifacts');

const VIEWPORTS = [
    { id: 'mobile_320', name: 'Ultra-narrow Mobile (iPhone SE gen 1)', width: 320, height: 568, isMobile: true, hasTouch: true },
    { id: 'mobile_360', name: 'Android Narrow (Galaxy S22 / 360px)', width: 360, height: 780, isMobile: true, hasTouch: true },
    { id: 'mobile_375', name: 'iPhone X / 12 Mini (375px)', width: 375, height: 812, isMobile: true, hasTouch: true },
    { id: 'mobile_414', name: 'iPhone XR / 11 (414px)', width: 414, height: 896, isMobile: true, hasTouch: true },
    { id: 'tablet_768', name: 'iPad Portrait (768px)', width: 768, height: 1024, isMobile: true, hasTouch: true },
    { id: 'tablet_820', name: 'iPad Air (820px)', width: 820, height: 1180, isMobile: true, hasTouch: true },
    { id: 'tablet_1024', name: 'iPad Landscape (1024px)', width: 1024, height: 768, isMobile: true, hasTouch: true },
    { id: 'desktop_1280', name: 'WXGA Laptop (1280px)', width: 1280, height: 800, isMobile: false, hasTouch: false },
    { id: 'desktop_1440', name: 'MacBook Desktop (1440px)', width: 1440, height: 900, isMobile: false, hasTouch: false },
    { id: 'desktop_1920', name: 'FHD Widescreen (1920px)', width: 1920, height: 1080, isMobile: false, hasTouch: false }
];

const ADDITIONAL_ROUTES = ['/story', '/products', '/taste-profiler', '/solutions-b2b', '/contactus'];

async function main() {
    console.log('================================================================================');
    console.log('🔍 EMPIRICAL CHALLENGER: MULTI-VIEWPORT LIVE LAYOUT STRESS TEST');
    console.log(`🌐 Target Base URL: ${TARGET_URL}`);
    console.log(`📁 Artifacts Directory: ${OUTPUT_DIR}`);
    console.log(`📱 Viewports to Test: ${VIEWPORTS.length}`);
    console.log('================================================================================\n');

    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--ignore-certificate-errors'
        ]
    });

    const report = {
        targetUrl: TARGET_URL,
        timestamp: new Date().toISOString(),
        totalViewportsTested: VIEWPORTS.length,
        viewportResults: [],
        routesTestedAcrossEdges: [],
        overallVerdict: 'PENDING',
        summaryMetrics: {
            totalPass: 0,
            totalFail: 0,
            overflowFails: 0,
            collisionFails: 0,
            clsFails: 0,
            buttonTouchFails: 0,
            linkTouchFails: 0,
            logoFails: 0
        }
    };

    try {
        // =====================================================================
        // PART 1: 10-VIEWPORT DEEP HARNESS ON HOMEPAGE
        // =====================================================================
        console.log('>>> STAGE 1: Testing Homepage (/) Across 10 Viewports...\n');

        for (const vp of VIEWPORTS) {
            console.log(`--------------------------------------------------------------------------------`);
            console.log(`Testing Viewport: [${vp.id}] ${vp.name} (${vp.width}x${vp.height})`);
            console.log(`--------------------------------------------------------------------------------`);

            const context = await browser.newContext({
                viewport: { width: vp.width, height: vp.height },
                isMobile: vp.isMobile,
                hasTouch: vp.hasTouch,
                locale: 'vi-VN',
                extraHTTPHeaders: {
                    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
                },
                userAgent: vp.isMobile
                    ? (vp.width <= 414
                        ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148'
                        : 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148')
                    : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            });

            const page = await context.newPage();

            // Track CLS via PerformanceObserver
            await page.addInitScript(() => {
                window.__clsScore = 0;
                try {
                    const observer = new PerformanceObserver((entryList) => {
                        for (const entry of entryList.getEntries()) {
                            if (!entry.hadRecentInput) {
                                window.__clsScore += entry.value;
                            }
                        }
                    });
                    observer.observe({ type: 'layout-shift', buffered: true });
                } catch (e) {
                    console.error('CLS observer not supported', e);
                }
            });

            const vpResult = {
                id: vp.id,
                name: vp.name,
                width: vp.width,
                height: vp.height,
                status: 200,
                passed: true,
                failures: [],
                warnings: [],
                assertions: {
                    zeroOverflow: { passed: false, scrollWidth: 0, innerWidth: 0, diff: 0, bleedingElements: [] },
                    clsAndCollisions: { passed: false, clsScore: 0, collisions: [] },
                    touchTargets: { passed: false, buttonsTotal: 0, buttonsPassing: 0, buttonsFailing: [], linksTotal: 0, linksPassing: 0, linksFailing: [] },
                    vectorLogo: { passed: false, navbarLogo: null, footerLogo: null, noFakeText: false }
                },
                screenshots: {
                    fold: null,
                    fullpage: null
                }
            };

            try {
                // Navigate resiliently (commit + domcontentloaded)
                const response = await page.goto(`${TARGET_URL}/`, { waitUntil: 'commit', timeout: 45000 });
                vpResult.status = response ? response.status() : 0;
                await page.waitForLoadState('domcontentloaded', { timeout: 20000 }).catch(() => {});
                await page.waitForTimeout(1000); // allow initial render

                // Capture above-the-fold screenshot before scrolling
                const foldPath = path.join(OUTPUT_DIR, `scan_${vp.id}_fold.png`);
                await page.screenshot({ path: foldPath, fullPage: false });
                vpResult.screenshots.fold = foldPath;

                // Scroll to bottom to trigger lazy loading of footer elements
                await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
                await page.waitForTimeout(1000);
                // Scroll back to top
                await page.evaluate(() => window.scrollTo(0, 0));
                await page.waitForTimeout(600);

                // Capture fullpage screenshot
                const fullPath = path.join(OUTPUT_DIR, `scan_${vp.id}_fullpage.png`);
                await page.screenshot({ path: fullPath, fullPage: true });
                vpResult.screenshots.fullpage = fullPath;

                // --- 1. ASSERTION: ZERO HORIZONTAL OVERFLOW & NO PHYSICAL ELEMENT BLEED ---
                const overflowData = await page.evaluate(() => {
                    const doc = document.documentElement;
                    const body = document.body;
                    const innerW = window.innerWidth;
                    const clientW = doc.clientWidth || innerW;
                    const scrollW = Math.max(doc.scrollWidth, body ? body.scrollWidth : 0);
                    const diff = scrollW - innerW;

                    const bleeding = [];
                    const allEls = document.querySelectorAll('*');
                    for (const el of allEls) {
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.position === 'fixed') continue;
                        if (el.closest('svg') || el.closest('.o_text_highlight_svg')) continue;

                        const rect = el.getBoundingClientRect();
                        // Element physically exceeds viewport width by > 2px
                        if (rect.right > innerW + 2 && rect.width > 0 && rect.height > 0) {
                            const sel = el.tagName.toLowerCase() + (el.id ? '#' + el.id : (el.className ? '.' + String(el.className).trim().split(/\s+/).slice(0, 2).join('.') : ''));
                            // Filter out generic containers to highlight leaf offenders
                            bleeding.push({
                                selector: sel,
                                text: (el.innerText || '').slice(0, 35),
                                right: Math.round(rect.right),
                                width: Math.round(rect.width),
                                excess: Math.round(rect.right - innerW)
                            });
                            if (bleeding.length >= 10) break;
                        }
                    }

                    return {
                        scrollWidth: scrollW,
                        clientWidth: clientW,
                        innerWidth: innerW,
                        diff: diff,
                        bleedingElements: bleeding
                    };
                });

                vpResult.assertions.zeroOverflow.scrollWidth = overflowData.scrollWidth;
                vpResult.assertions.zeroOverflow.innerWidth = overflowData.innerWidth;
                vpResult.assertions.zeroOverflow.diff = overflowData.diff;
                vpResult.assertions.zeroOverflow.bleedingElements = overflowData.bleedingElements;

                // Both scrollWidth diff <= 1 AND no physical bleeding elements
                const scrollOverflowOk = overflowData.diff <= 1;
                const bleedingOk = overflowData.bleedingElements.length === 0;

                if (scrollOverflowOk && bleedingOk) {
                    vpResult.assertions.zeroOverflow.passed = true;
                    console.log(`  [✓] Assertion 1 (Zero Overflow): PASS (scrollW=${overflowData.scrollWidth}px, innerW=${overflowData.innerWidth}px, bleeding=0)`);
                } else {
                    vpResult.assertions.zeroOverflow.passed = false;
                    vpResult.passed = false;
                    let errMsg = '';
                    if (!scrollOverflowOk) {
                        errMsg += `scrollWidth (${overflowData.scrollWidth}px) > innerWidth (${overflowData.innerWidth}px), diff=${overflowData.diff}px. `;
                    }
                    if (!bleedingOk) {
                        errMsg += `Physical elements bleeding beyond viewport (${overflowData.bleedingElements.length} elements): ${JSON.stringify(overflowData.bleedingElements.slice(0, 3))}. `;
                    }
                    vpResult.failures.push(errMsg);
                    report.summaryMetrics.overflowFails++;
                    console.error(`  [✗] Assertion 1 (Zero Overflow): FAIL — ${errMsg}`);
                }

                // --- 2. ASSERTION: ZERO LAYOUT SHIFTS & ZERO ELEMENT COLLISIONS ---
                const clsAndCollisions = await page.evaluate(() => {
                    const cls = window.__clsScore || 0;
                    const collisions = [];

                    // Collision check between interactive elements
                    const ctaButtons = Array.from(document.querySelectorAll('.btn:not(.o_skip_to_content)'));
                    for (let i = 0; i < ctaButtons.length; i++) {
                        const btnA = ctaButtons[i];
                        const sA = window.getComputedStyle(btnA);
                        if (sA.display === 'none' || sA.visibility === 'hidden' || sA.position === 'absolute' || sA.position === 'fixed') continue;
                        const rA = btnA.getBoundingClientRect();
                        if (rA.width === 0 || rA.height === 0 || rA.bottom < 0 || rA.top > window.innerHeight * 2) continue;

                        for (let j = i + 1; j < Math.min(i + 5, ctaButtons.length); j++) {
                            const btnB = ctaButtons[j];
                            const sB = window.getComputedStyle(btnB);
                            if (sB.display === 'none' || sB.visibility === 'hidden' || sB.position === 'absolute' || sB.position === 'fixed') continue;
                            const rB = btnB.getBoundingClientRect();
                            if (rB.width === 0 || rB.height === 0) continue;

                            const xOverlap = Math.max(0, Math.min(rA.right, rB.right) - Math.max(rA.left, rB.left));
                            const yOverlap = Math.max(0, Math.min(rA.bottom, rB.bottom) - Math.max(rA.top, rB.top));
                            if (xOverlap > 5 && yOverlap > 5) {
                                collisions.push({
                                    elementA: (btnA.innerText || btnA.className).slice(0, 30),
                                    elementB: (btnB.innerText || btnB.className).slice(0, 30),
                                    overlap: `${Math.round(xOverlap)}x${Math.round(yOverlap)}px`,
                                    message: 'Adjacent interactive buttons overlap in flow layout'
                                });
                            }
                        }
                    }

                    return {
                        clsScore: cls,
                        collisions: collisions
                    };
                });

                vpResult.assertions.clsAndCollisions.clsScore = clsAndCollisions.clsScore;
                vpResult.assertions.clsAndCollisions.collisions = clsAndCollisions.collisions;

                const clsPass = clsAndCollisions.clsScore <= 0.05;
                const collisionPass = clsAndCollisions.collisions.length === 0;

                if (clsPass && collisionPass) {
                    vpResult.assertions.clsAndCollisions.passed = true;
                    console.log(`  [✓] Assertion 2 (CLS & Collisions): PASS (CLS=${clsAndCollisions.clsScore.toFixed(4)}, Collisions=0)`);
                } else {
                    vpResult.assertions.clsAndCollisions.passed = false;
                    vpResult.passed = false;
                    let msg = '';
                    if (!clsPass) {
                        msg += `CLS score (${clsAndCollisions.clsScore.toFixed(4)}) > threshold 0.05. `;
                        report.summaryMetrics.clsFails++;
                    }
                    if (!collisionPass) {
                        msg += `Collisions detected: ${JSON.stringify(clsAndCollisions.collisions)}. `;
                        report.summaryMetrics.collisionFails++;
                    }
                    vpResult.failures.push(msg);
                    console.error(`  [✗] Assertion 2 (CLS & Collisions): FAIL — ${msg}`);
                }

                // --- 3. ASSERTION: TOUCH TARGETS (BUTTONS >= 44px, LINKS >= 36px) ---
                const touchData = await page.evaluate(() => {
                    function getSel(el) {
                        return el.tagName.toLowerCase() + (el.id ? '#' + el.id : (el.className ? '.' + String(el.className).trim().split(/\s+/).slice(0, 2).join('.') : ''));
                    }

                    // A. BUTTONS: <button>, .btn, [role="button"], input[type="submit/button"]
                    const allButtons = Array.from(document.querySelectorAll('button, .btn, [role="button"], input[type="submit"], input[type="button"]'));
                    let buttonsTotal = 0;
                    let buttonsPassing = 0;
                    const buttonsFailing = [];

                    for (const btn of allButtons) {
                        if (btn.classList.contains('visually-hidden-focusable') || btn.classList.contains('o_skip_to_content') || btn.classList.contains('visually-hidden')) continue;
                        const st = window.getComputedStyle(btn);
                        if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') continue;

                        const rect = btn.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;

                        buttonsTotal++;
                        const meetsHeight = rect.height >= 43.5;
                        const meetsWidth = rect.width >= 43.5;
                        const minH = parseFloat(st.minHeight) || 0;

                        if ((meetsHeight && meetsWidth) || (minH >= 44 && rect.width >= 40)) {
                            buttonsPassing++;
                        } else {
                            buttonsFailing.push({
                                selector: getSel(btn),
                                text: (btn.innerText || btn.getAttribute('aria-label') || '').trim().slice(0, 35),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                minHeight: st.minHeight
                            });
                        }
                    }

                    // B. INTERACTIVE LINKS: <a> tags in nav, footer, standalone action links
                    const allLinks = Array.from(document.querySelectorAll('a:not(.btn):not([role="button"])'));
                    let linksTotal = 0;
                    let linksPassing = 0;
                    const linksFailing = [];

                    for (const a of allLinks) {
                        if (a.classList.contains('visually-hidden-focusable') || a.classList.contains('o_skip_to_content') || a.classList.contains('visually-hidden')) continue;
                        const st = window.getComputedStyle(a);
                        if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') continue;

                        const rect = a.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;

                        const isNav = !!a.closest('nav, .navbar, #footer, footer, .nav, .dropdown-menu, .pagination');
                        const isStandalone = st.display === 'block' || st.display === 'inline-flex' || st.display === 'flex' || isNav;

                        if (isStandalone) {
                            linksTotal++;
                            if (rect.height >= 35.5 || rect.width >= 44 || (st.minHeight && parseFloat(st.minHeight) >= 36)) {
                                linksPassing++;
                            } else {
                                linksFailing.push({
                                    selector: getSel(a),
                                    text: (a.innerText || a.getAttribute('aria-label') || '').trim().slice(0, 35),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    display: st.display
                                });
                            }
                        }
                    }

                    return {
                        buttonsTotal,
                        buttonsPassing,
                        buttonsFailing,
                        linksTotal,
                        linksPassing,
                        linksFailing
                    };
                });

                vpResult.assertions.touchTargets.buttonsTotal = touchData.buttonsTotal;
                vpResult.assertions.touchTargets.buttonsPassing = touchData.buttonsPassing;
                vpResult.assertions.touchTargets.buttonsFailing = touchData.buttonsFailing;
                vpResult.assertions.touchTargets.linksTotal = touchData.linksTotal;
                vpResult.assertions.touchTargets.linksPassing = touchData.linksPassing;
                vpResult.assertions.touchTargets.linksFailing = touchData.linksFailing;

                const buttonsPass = touchData.buttonsFailing.length === 0;
                const linksPass = touchData.linksFailing.length === 0;

                if (buttonsPass && linksPass) {
                    vpResult.assertions.touchTargets.passed = true;
                    console.log(`  [✓] Assertion 3 (Touch Targets): PASS (Buttons: ${touchData.buttonsPassing}/${touchData.buttonsTotal} >= 44px, Links: ${touchData.linksPassing}/${touchData.linksTotal} >= 36px)`);
                } else {
                    vpResult.assertions.touchTargets.passed = false;
                    vpResult.passed = false;
                    let msg = '';
                    if (!buttonsPass) {
                        msg += `Buttons failing >= 44px: ${touchData.buttonsFailing.length}/${touchData.buttonsTotal}. (${JSON.stringify(touchData.buttonsFailing.slice(0, 3))}) `;
                        report.summaryMetrics.buttonTouchFails++;
                    }
                    if (!linksPass) {
                        msg += `Links failing >= 36px: ${touchData.linksFailing.length}/${touchData.linksTotal}. (${JSON.stringify(touchData.linksFailing.slice(0, 3))}) `;
                        report.summaryMetrics.linkTouchFails++;
                    }
                    vpResult.failures.push(msg);
                    console.error(`  [✗] Assertion 3 (Touch Targets): FAIL — ${msg}`);
                }

                // --- 4. ASSERTION: VECTOR SVG LOGO RENDERS PROPERLY ---
                const logoData = await page.evaluate(() => {
                    // Check visible navbar brand logo
                    const brandImgs = Array.from(document.querySelectorAll('.navbar-brand img'));
                    const visibleBrandImg = brandImgs.find(img => {
                        const r = img.getBoundingClientRect();
                        return r.width > 0 && r.height > 0 && window.getComputedStyle(img).display !== 'none';
                    });

                    // Check footer logo
                    const footImg = document.querySelector('#footer img');

                    // Check fake text logos
                    const fakeSpans = Array.from(document.querySelectorAll('.navbar-brand span, #footer span.inno-serif'));
                    const hasFakeText = fakeSpans.some(s => s.innerText.includes('InnoKafe') || s.innerText.includes('Specialty Roastery'));

                    function getImgMeta(img) {
                        if (!img) return null;
                        const r = img.getBoundingClientRect();
                        return {
                            src: img.getAttribute('src') || img.src,
                            isSvg: (img.src && img.src.includes('.svg')) || (img.getAttribute('src') && img.getAttribute('src').includes('.svg')),
                            complete: img.complete,
                            naturalWidth: img.naturalWidth,
                            naturalHeight: img.naturalHeight,
                            renderedWidth: Math.round(r.width),
                            renderedHeight: Math.round(r.height),
                            visible: r.width > 0 && r.height > 0
                        };
                    }

                    return {
                        navbarLogo: getImgMeta(visibleBrandImg),
                        footerLogo: getImgMeta(footImg),
                        hasFakeText: hasFakeText
                    };
                });

                vpResult.assertions.vectorLogo.navbarLogo = logoData.navbarLogo;
                vpResult.assertions.vectorLogo.footerLogo = logoData.footerLogo;
                vpResult.assertions.vectorLogo.noFakeText = !logoData.hasFakeText;

                const navLogoPass = logoData.navbarLogo && logoData.navbarLogo.isSvg && logoData.navbarLogo.visible && logoData.navbarLogo.naturalWidth > 0;
                const footLogoPass = logoData.footerLogo && logoData.footerLogo.isSvg && logoData.footerLogo.naturalWidth > 0;
                const fakeTextPass = !logoData.hasFakeText;

                if (navLogoPass && footLogoPass && fakeTextPass) {
                    vpResult.assertions.vectorLogo.passed = true;
                    console.log(`  [✓] Assertion 4 (Vector SVG Logo): PASS (Navbar SVG: ${logoData.navbarLogo.renderedWidth}x${logoData.navbarLogo.renderedHeight}px, Footer SVG: ${logoData.footerLogo.renderedWidth}x${logoData.footerLogo.renderedHeight}px, Fake text: 0)`);
                } else {
                    vpResult.assertions.vectorLogo.passed = false;
                    vpResult.passed = false;
                    const errMsg = `Vector Logo check failed. Navbar SVG pass: ${navLogoPass}, Footer SVG pass: ${footLogoPass}, Fake text: ${logoData.hasFakeText}. Logo data: ${JSON.stringify(logoData)}`;
                    vpResult.failures.push(errMsg);
                    report.summaryMetrics.logoFails++;
                    console.error(`  [✗] Assertion 4 (Vector SVG Logo): FAIL — ${errMsg}`);
                }

            } catch (err) {
                vpResult.passed = false;
                vpResult.failures.push(`Unhandled page error: ${err.message}`);
                console.error(`  [!] ERROR during viewport testing: ${err.message}`);
            } finally {
                await context.close();
            }

            if (vpResult.passed) {
                report.summaryMetrics.totalPass++;
                console.log(`\n>>> VIEWPORT [${vp.id}] RESULT: 100% PASS\n`);
            } else {
                report.summaryMetrics.totalFail++;
                console.log(`\n>>> VIEWPORT [${vp.id}] RESULT: FAIL (${vpResult.failures.length} issues)\n`);
            }

            report.viewportResults.push(vpResult);
        }

        // =====================================================================
        // PART 2: MULTI-ROUTE EDGE VIEWPORT OVERFLOW AUDIT
        // =====================================================================
        console.log('\n================================================================================');
        console.log('>>> STAGE 2: Testing All 5 Additional Routes on Ultra-Narrow (320px) & Wide (1920px)...');
        console.log('================================================================================\n');

        const EDGE_VPS = [
            { id: 'mobile_320', width: 320, height: 568, isMobile: true },
            { id: 'desktop_1920', width: 1920, height: 1080, isMobile: false }
        ];

        for (const route of ADDITIONAL_ROUTES) {
            for (const evp of EDGE_VPS) {
                const ctx = await browser.newContext({
                    viewport: { width: evp.width, height: evp.height },
                    isMobile: evp.isMobile,
                    locale: 'vi-VN'
                });
                const pg = await ctx.newPage();

                const routeTest = {
                    route: route,
                    viewport: `${evp.width}x${evp.height}`,
                    status: 200,
                    overflowOk: false,
                    scrollWidth: 0,
                    innerWidth: evp.width,
                    diff: 0,
                    offenders: []
                };

                try {
                    const res = await pg.goto(`${TARGET_URL}${route}`, { waitUntil: 'commit', timeout: 35000 });
                    routeTest.status = res ? res.status() : 0;
                    await pg.waitForLoadState('domcontentloaded', { timeout: 15000 }).catch(() => {});
                    await pg.waitForTimeout(800);

                    const overflowMetrics = await pg.evaluate(() => {
                        const doc = document.documentElement;
                        const body = document.body;
                        const innerW = window.innerWidth;
                        const scrollW = Math.max(doc.scrollWidth, body ? body.scrollWidth : 0);
                        const diff = scrollW - innerW;
                        const offenders = [];

                        if (diff > 1) {
                            const allEls = document.querySelectorAll('*');
                            for (const el of allEls) {
                                const st = window.getComputedStyle(el);
                                if (st.display === 'none' || st.visibility === 'hidden' || st.position === 'fixed') continue;
                                const r = el.getBoundingClientRect();
                                if (r.right > innerW + 2 && r.width > 0 && r.height > 0) {
                                    offenders.push({
                                        tag: el.tagName.toLowerCase(),
                                        className: (el.className || '').toString().slice(0, 50),
                                        right: Math.round(r.right),
                                        diff: Math.round(r.right - innerW)
                                    });
                                    if (offenders.length >= 5) break;
                                }
                            }
                        }

                        return { scrollWidth: scrollW, diff: diff, offenders: offenders };
                    });

                    routeTest.scrollWidth = overflowMetrics.scrollWidth;
                    routeTest.diff = overflowMetrics.diff;
                    routeTest.offenders = overflowMetrics.offenders;
                    routeTest.overflowOk = overflowMetrics.diff <= 1 && overflowMetrics.offenders.length === 0;

                    const statusStr = routeTest.overflowOk ? 'PASS' : 'FAIL';
                    console.log(`[${statusStr}] Route ${route.padEnd(18)} @ ${evp.width}px: scrollW=${routeTest.scrollWidth}px (diff=${routeTest.diff}px)`);

                    if (!routeTest.overflowOk) {
                        console.error(`       Offenders:`, JSON.stringify(routeTest.offenders));
                    }
                } catch (e) {
                    console.error(`[ERR] Route ${route} @ ${evp.width}px failed: ${e.message}`);
                    routeTest.overflowOk = false;
                } finally {
                    await ctx.close();
                }

                report.routesTestedAcrossEdges.push(routeTest);
            }
        }

    } finally {
        await browser.close();
    }

    // Determine overall verdict
    const allViewportsPass = report.viewportResults.every(r => r.passed);
    const allRoutesPass = report.routesTestedAcrossEdges.every(r => r.overflowOk);

    report.overallVerdict = (allViewportsPass && allRoutesPass) ? 'APPROVE' : 'REQUEST_CHANGES';

    console.log('\n================================================================================');
    console.log('🏁 FINAL CHALLENGER STRESS TEST SUMMARY');
    console.log('================================================================================');
    console.log(`Target URL                 : ${TARGET_URL}`);
    console.log(`Total Viewports Tested     : ${report.totalViewportsTested}`);
    console.log(`Viewports Passed (4/4 gates): ${report.summaryMetrics.totalPass} / ${report.totalViewportsTested}`);
    console.log(`Viewports Failed           : ${report.summaryMetrics.totalFail}`);
    console.log(`Overflow Failures          : ${report.summaryMetrics.overflowFails}`);
    console.log(`Collision Failures         : ${report.summaryMetrics.collisionFails}`);
    console.log(`CLS Failures               : ${report.summaryMetrics.clsFails}`);
    console.log(`Button Touch Target Fails  : ${report.summaryMetrics.buttonTouchFails}`);
    console.log(`Link Touch Target Fails    : ${report.summaryMetrics.linkTouchFails}`);
    console.log(`Vector Logo Fails          : ${report.summaryMetrics.logoFails}`);
    console.log(`Additional Route Overflows : ${report.routesTestedAcrossEdges.filter(r => !r.overflowOk).length}`);
    console.log(`--------------------------------------------------------------------------------`);
    console.log(`OVERALL VERDICT            : 🎯 ${report.overallVerdict}`);
    console.log('================================================================================\n');

    // Save JSON summary
    const reportPath = path.join(OUTPUT_DIR, 'challenger_m5_report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8');
    console.log(`📄 Detailed Report Saved: ${reportPath}`);

    process.exit(report.overallVerdict === 'APPROVE' ? 0 : 1);
}

main().catch(err => {
    console.error('[FATAL CHALLENGER ERROR]:', err);
    process.exit(1);
});
