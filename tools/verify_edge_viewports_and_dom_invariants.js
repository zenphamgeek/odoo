#!/usr/bin/env node
/**
 * tools/verify_edge_viewports_and_dom_invariants.js
 * =============================================================================
 * Adversarial Scan of DOM Text Invariants, Edge Viewports & Overflow
 *
 * Edge Viewports Tested:
 *  - 320 x 568  (Ultra-small mobile, iPhone SE 1st gen)
 *  - 414 x 896  (Mobile, iPhone 11 / XR / Plus)
 *  - 820 x 1180 (Tablet, iPad Air 4th / 5th gen)
 *  - 1920 x 1080 (Wide desktop, Full HD)
 *
 * 6 Main Routes Tested:
 *  - /
 *  - /solutions
 *  - /platform
 *  - /industries
 *  - /about
 *  - /contactus
 *
 * Invariants Tested:
 *  1. Zero horizontal overflow: scrollWidth === clientWidth (<= 1px subpixel margin)
 *  2. Zero banned instructional phrases across raw templates & rendered DOM:
 *     - "Kéo chuột"
 *     - "Hover khối"
 *     - "Rê chuột"
 *     - "360° interactive"
 *     - "Hardware 3D // 60 FPS"
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

const BASE_URL = (getArg('--url', process.env.BASE_URL || 'http://innoria.localhost:28070')).replace(/\/$/, '');
const TIMEOUT_MS = parseInt(getArg('--timeout', '40000'), 10);

const EDGE_VIEWPORTS = [
    { name: 'Ultra-small mobile (320px)', width: 320, height: 568, isMobile: true },
    { name: 'Mobile (414px)', width: 414, height: 896, isMobile: true },
    { name: 'Tablet (820px)', width: 820, height: 1180, isMobile: false },
    { name: 'Wide Desktop (1920px)', width: 1920, height: 1080, isMobile: false }
];

const ROUTES = [
    { path: '/', name: 'Homepage' },
    { path: '/solutions', name: 'Solutions' },
    { path: '/platform', name: 'Platform' },
    { path: '/industries', name: 'Industries' },
    { path: '/about', name: 'About Us' },
    { path: '/contactus', name: 'Contact Us' }
];

const BANNED_PATTERNS = [
    { label: 'Kéo chuột', regex: /kéo\s*chuột/i },
    { label: 'Hover khối', regex: /hover\s*khối/i },
    { label: 'Rê chuột', regex: /rê\s*chuột/i },
    { label: '360° interactive', regex: /360[°\s]*interactive/i },
    { label: 'Hardware 3D // 60 FPS', regex: /hardware\s*3d\s*\/\/\s*60\s*fps/i }
];

async function scanRawTemplates() {
    console.log('\n======================================================================');
    console.log('1. RAW TEMPLATES ADVERSARIAL SCAN');
    console.log('======================================================================');

    const viewsDir = path.join(__dirname, '..', 'enterprise', 'insilos_website', 'views');
    const targetFiles = [
        'innoria_homepage.xml',
        'innoria_pages.xml',
        'snippets_3d.xml'
    ];

    let totalViolations = 0;

    for (const file of targetFiles) {
        const filePath = path.join(viewsDir, file);
        if (!fs.existsSync(filePath)) {
            console.log(`[WARN] File not found: ${filePath}`);
            continue;
        }

        const content = fs.readFileSync(filePath, 'utf8');
        const lines = content.split('\n');

        let fileViolations = 0;
        lines.forEach((line, lineNum) => {
            for (const pattern of BANNED_PATTERNS) {
                if (pattern.regex.test(line)) {
                    // Check if it's in a comment explaining banned strings or in test code
                    console.log(`[FAIL] ${file}:${lineNum + 1} matches "${pattern.label}":\n  ${line.trim()}`);
                    fileViolations++;
                    totalViolations++;
                }
            }
        });

        if (fileViolations === 0) {
            console.log(`[PASS] ${file}: 0 matches for all banned instructional phrases.`);
        }
    }

    return totalViolations;
}

async function runAdversarialAudit() {
    const rawViolations = await scanRawTemplates();

    console.log('\n======================================================================');
    console.log(`2. EDGE VIEWPORT & RENDERED DOM AUDIT ON: ${BASE_URL}`);
    console.log('======================================================================');

    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security'
        ]
    });

    const report = {
        baseUrl: BASE_URL,
        timestamp: new Date().toISOString(),
        totalRoutes: ROUTES.length,
        totalViewports: EDGE_VIEWPORTS.length,
        combinationsTested: 0,
        overflowPasses: 0,
        overflowFails: 0,
        bannedTextMatches: 0,
        consoleErrors: 0,
        results: []
    };

    let overallSuccess = (rawViolations === 0);

    try {
        for (const vp of EDGE_VIEWPORTS) {
            console.log(`\n----------------------------------------------------------------------`);
            console.log(`Testing Viewport: ${vp.name} (${vp.width}x${vp.height})`);
            console.log(`----------------------------------------------------------------------`);

            for (const route of ROUTES) {
                report.combinationsTested++;
                const fullUrl = `${BASE_URL}${route.path}`;
                const pageResult = {
                    route: route.path,
                    routeName: route.name,
                    viewport: vp.name,
                    width: vp.width,
                    height: vp.height,
                    overflowOk: false,
                    scrollWidth: 0,
                    clientWidth: 0,
                    overflowDiff: 0,
                    offenders: [],
                    bannedTextDetections: [],
                    consoleErrors: []
                };

                const context = await browser.newContext({
                    viewport: { width: vp.width, height: vp.height },
                    isMobile: vp.isMobile,
                    userAgent: vp.isMobile
                        ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
                        : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                });

                const page = await context.newPage();

                page.on('console', msg => {
                    if (msg.type() === 'error') {
                        const txt = msg.text();
                        // Ignore harmless favicon or tracker 404s
                        if (!txt.includes('favicon.ico')) {
                            pageResult.consoleErrors.push(txt);
                        }
                    }
                });

                try {
                    await page.goto(fullUrl, { waitUntil: 'load', timeout: TIMEOUT_MS });
                    await page.waitForTimeout(1000); // Allow layout stabilization & dynamic scripts

                    // Measure overflow
                    const overflowMetrics = await page.evaluate(() => {
                        const doc = document.documentElement;
                        const body = document.body;
                        const scrollW = Math.max(doc.scrollWidth, body ? body.scrollWidth : 0);
                        const clientW = doc.clientWidth || window.innerWidth;
                        const diff = scrollW - clientW;

                        // Find overflowing elements if any
                        const offenders = [];
                        if (diff > 1) {
                            const allElements = document.querySelectorAll('*');
                            for (const el of allElements) {
                                const rect = el.getBoundingClientRect();
                                if (rect.right > clientW + 1.5 && rect.width > 0 && rect.height > 0) {
                                    const style = window.getComputedStyle(el);
                                    if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                                        offenders.push({
                                            tag: el.tagName.toLowerCase(),
                                            id: el.id || null,
                                            className: (el.className || '').toString().slice(0, 100),
                                            right: Math.round(rect.right),
                                            width: Math.round(rect.width)
                                        });
                                    }
                                }
                            }
                        }

                        return {
                            scrollWidth: scrollW,
                            clientWidth: clientW,
                            diff: diff,
                            offenders: offenders.slice(0, 5) // top 5
                        };
                    });

                    pageResult.scrollWidth = overflowMetrics.scrollWidth;
                    pageResult.clientWidth = overflowMetrics.clientWidth;
                    pageResult.overflowDiff = overflowMetrics.diff;
                    pageResult.offenders = overflowMetrics.offenders;

                    if (overflowMetrics.diff <= 1) {
                        pageResult.overflowOk = true;
                        report.overflowPasses++;
                    } else {
                        pageResult.overflowOk = false;
                        report.overflowFails++;
                        overallSuccess = false;
                    }

                    // Scan rendered DOM for banned instructional text
                    const domTextMatches = await page.evaluate((patterns) => {
                        const matches = [];
                        const textContent = (document.body ? document.body.innerText : '') + ' ' + (document.title || '');

                        for (const p of patterns) {
                            const re = new RegExp(p.regexSource, 'i');
                            if (re.test(textContent)) {
                                matches.push({
                                    label: p.label,
                                    context: 'document.body.innerText'
                                });
                            }
                        }

                        // Also scan all text nodes via TreeWalker to catch hidden/aria/detached strings
                        const walker = document.createTreeWalker(
                            document.body || document.documentElement,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );

                        let node;
                        while ((node = walker.nextNode())) {
                            const val = node.nodeValue;
                            if (!val || val.trim().length === 0) continue;
                            for (const p of patterns) {
                                const re = new RegExp(p.regexSource, 'i');
                                if (re.test(val)) {
                                    // avoid duplicate if already logged
                                    const parentTag = node.parentElement ? node.parentElement.tagName.toLowerCase() : 'unknown';
                                    const parentCls = node.parentElement ? (node.parentElement.className || '') : '';
                                    matches.push({
                                        label: p.label,
                                        snippet: val.trim().slice(0, 100),
                                        parent: `${parentTag}.${parentCls}`
                                    });
                                }
                            }
                        }

                        return matches;
                    }, BANNED_PATTERNS.map(p => ({ label: p.label, regexSource: p.regex.source })));

                    pageResult.bannedTextDetections = domTextMatches;
                    if (domTextMatches.length > 0) {
                        report.bannedTextMatches += domTextMatches.length;
                        overallSuccess = false;
                    }

                    const statusStr = (pageResult.overflowOk && domTextMatches.length === 0) ? 'PASS' : 'FAIL';
                    console.log(`[${statusStr}] ${route.path.padEnd(16)} | Width: ${pageResult.clientWidth}px, Scroll: ${pageResult.scrollWidth}px (diff: ${pageResult.overflowDiff}px) | Banned text: ${domTextMatches.length}`);

                    if (!pageResult.overflowOk) {
                        console.log(`       -> Overflow Offenders:`, JSON.stringify(pageResult.offenders));
                    }
                    if (domTextMatches.length > 0) {
                        console.log(`       -> Banned Text Matches:`, JSON.stringify(domTextMatches));
                    }

                } catch (err) {
                    console.log(`[ERR] ${route.path.padEnd(16)}: ${err.message}`);
                    pageResult.consoleErrors.push(err.message);
                    overallSuccess = false;
                } finally {
                    await context.close();
                }

                report.results.push(pageResult);
            }
        }
    } finally {
        await browser.close();
    }

    console.log('\n======================================================================');
    console.log('AUDIT SUMMARY');
    console.log('======================================================================');
    console.log(`Total Route x Viewport combinations: ${report.combinationsTested}`);
    console.log(`Overflow Passes: ${report.overflowPasses} / ${report.combinationsTested}`);
    console.log(`Overflow Failures: ${report.overflowFails}`);
    console.log(`Banned Text Detections: ${report.bannedTextMatches}`);
    console.log(`Raw Template Violations: ${rawViolations}`);
    console.log(`Overall Result: ${overallSuccess ? '100% PASS (APPROVE)' : 'FAIL (REQUEST_CHANGES)'}`);
    console.log('======================================================================\n');

    return overallSuccess ? 0 : 1;
}

runAdversarialAudit().then(code => {
    process.exit(code);
}).catch(err => {
    console.error('Fatal audit failure:', err);
    process.exit(1);
});
