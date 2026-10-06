#!/usr/bin/env node
/**
 * tools/verify_routes_layout_quality.js
 * =============================================================================
 * Automated Multi-Route Playwright Layout, DOM & Quality Verification Suite
 * Targets: https://innoria.insilos.com (or configurable via --url)
 *
 * Scans 6 main routes across 3 responsive viewports:
 *  - Mobile:  375x812
 *  - Tablet:  768x1024
 *  - Desktop: 1440x900
 *
 * Acceptance Criteria Checked:
 *  1. 100% 3D components render transparent (background: transparent, border: none, box-shadow: none).
 *  2. Exactly 0 instructional text strings in DOM ("Kéo chuột", "Hover khối", "Rê chuột", "360° interactive", "Hardware 3D // 60 FPS").
 *  3. 100% scrollWidth === clientWidth on all viewports (0 horizontal overflow).
 *  4. WCAG AA/AAA contrast on body text (>= 4.5:1) and headings (>= 7:1 on dark canvas, >= 4.5:1 on light).
 *  5. 0 unhandled JavaScript exceptions in browser console.
 *
 * Exit code 0 on 100% PASS, 1 on any failure.
 * =============================================================================
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// CLI Argument Parsing
const args = process.argv.slice(2);
function getArg(flag, defaultValue) {
    const idx = args.indexOf(flag);
    if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
    return defaultValue;
}
const hasFlag = flag => args.includes(flag);

if (hasFlag('--help') || hasFlag('-h')) {
    console.log(`
Usage: node tools/verify_routes_layout_quality.js [options]

Options:
  --url <url>          Base URL to test (default: https://innoria.insilos.com)
  --route <path>       Test a single route (e.g. / or /solutions)
  --viewport <name>    Test a single viewport: mobile, tablet, desktop (default: all)
  --headed             Run browser in headed mode (default: headless)
  --verbose            Show detailed diagnostic logs for each check
  --timeout <ms>       Page load timeout in ms (default: 35000)
  --json <path>        Write JSON test report to specified path
  --help, -h           Show this help message
`);
    process.exit(0);
}

const BASE_URL = (getArg('--url', process.env.BASE_URL || 'https://innoria.insilos.com')).replace(/\/$/, '');
const SINGLE_ROUTE = getArg('--route', null);
const SINGLE_VIEWPORT = getArg('--viewport', null);
const IS_HEADLESS = !hasFlag('--headed');
const IS_VERBOSE = hasFlag('--verbose');
const TIMEOUT_MS = parseInt(getArg('--timeout', '35000'), 10);
const JSON_OUTPUT_PATH = getArg('--json', null);

// Viewports specification
const ALL_VIEWPORTS = {
    mobile: { name: 'Mobile', width: 375, height: 812, isMobile: true },
    tablet: { name: 'Tablet', width: 768, height: 1024, isMobile: false },
    desktop: { name: 'Desktop', width: 1440, height: 900, isMobile: false }
};

// 6 Main Routes Specification
const ALL_ROUTES = [
    { path: '/', name: 'Homepage (Lõi Đa Nền Tảng)' },
    { path: '/solutions', name: 'Solutions (AI-Enhanced ERP)' },
    { path: '/platform', name: 'Platform (Digiforce & Mojo AI)' },
    { path: '/industries', name: 'Industries (Ultra AI Vision)' },
    { path: '/about', name: 'About Us (Doanh Nghiệp & Đội Ngũ)' },
    { path: '/contactus', name: 'Contact Us (Tư Vấn & FAQ)' }
];

// Banned instructional text strings (case-insensitive substring match)
const BANNED_INSTRUCTION_STRINGS = [
    'Kéo chuột',
    'Hover khối',
    'Rê chuột',
    '360° interactive',
    '360°',
    'Hardware 3D // 60 FPS',
    'HARDWARE 3D // 60 FPS'
];

// Candidate selectors for 3D components
const SELECTORS_3D_COMPONENTS = [
    '.innoria-solutions-3d-stage',
    '[data-snippet="s_innoria_3d_solutions_erp"]',
    '.deck-container-3d',
    '#innoriaTopologyViewport',
    '.innoria-deck-viewport',
    '.deck-viewport',
    '.innoria-3d-deck-stage',
    '.deck-scene',
    '.hero-3d-canvas-wrap',
    '.innoria-3d-canvas'
];

// Helper: ANSI Colors
const colors = {
    reset: '\x1b[0m',
    bold: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    cyan: '\x1b[36m',
    gray: '\x1b[90m',
    magenta: '\x1b[35m'
};

/**
 * Perform comprehensive evaluation on a page
 */
async function auditPage(page, route, vpName, vp) {
    const routeUrl = `${BASE_URL}${route.path}`;
    const auditResult = {
        route: route.path,
        routeName: route.name,
        viewport: vpName,
        viewportSize: `${vp.width}x${vp.height}`,
        url: routeUrl,
        httpStatus: null,
        passed: false,
        checks: {
            transparency3D: { pass: true, count: 0, checked: 0, details: [] },
            zeroInstructionText: { pass: true, occurrences: 0, matches: [] },
            zeroOverflow: { pass: true, scrollWidth: 0, clientWidth: 0, overflow: 0, offenders: [] },
            wcagContrast: { pass: true, testedCount: 0, violations: [] },
            consoleErrors: { pass: true, errors: [] }
        }
    };

    const consoleErrors = [];
    const onConsole = msg => {
        if (msg.type() === 'error') {
            const txt = msg.text();
            // Filter out external third-party tracker failures if any
            if (!txt.includes('google-analytics') && !txt.includes('doubleclick')) {
                consoleErrors.push(txt);
            }
        }
    };
    const onPageError = err => {
        consoleErrors.push(err.message || String(err));
    };

    page.on('console', onConsole);
    page.on('pageerror', onPageError);

    try {
        const response = await page.goto(routeUrl, {
            waitUntil: 'domcontentloaded',
            timeout: TIMEOUT_MS
        });

        auditResult.httpStatus = response ? response.status() : null;

        // Allow dynamic DOM, 3D engines, and lazy styles to settle
        await page.waitForTimeout(2000);

        // -------------------------------------------------------------
        // Check 1: 3D Components Transparency
        // -------------------------------------------------------------
        const transparencyData = await page.evaluate((selectors) => {
            const results = [];
            const elements = [];
            for (const sel of selectors) {
                const matched = Array.from(document.querySelectorAll(sel));
                for (const el of matched) {
                    if (!elements.includes(el)) {
                        elements.push(el);
                    }
                }
            }

            for (const el of elements) {
                const style = window.getComputedStyle(el);
                const bg = style.backgroundColor;
                const borderTopW = parseFloat(style.borderTopWidth) || 0;
                const borderRightW = parseFloat(style.borderRightWidth) || 0;
                const borderBottomW = parseFloat(style.borderBottomWidth) || 0;
                const borderLeftW = parseFloat(style.borderLeftWidth) || 0;
                const totalBorderW = borderTopW + borderRightW + borderBottomW + borderLeftW;
                const borderStyle = style.borderStyle;
                const boxShadow = style.boxShadow;

                // Transparent background evaluation
                const isBgTransparent = (
                    bg === 'transparent' ||
                    bg === 'rgba(0, 0, 0, 0)' ||
                    bg.endsWith(', 0)') ||
                    bg.endsWith(', 0.0)')
                );

                // Border evaluation
                const isBorderNone = (totalBorderW === 0 || borderStyle === 'none');

                // Box-shadow evaluation
                const isShadowNone = (boxShadow === 'none' || boxShadow === '' || boxShadow === '0px 0px 0px 0px rgba(0, 0, 0, 0)');

                const isCompliant = isBgTransparent && isBorderNone && isShadowNone;

                results.push({
                    tagName: el.tagName.toLowerCase(),
                    className: el.className,
                    id: el.id,
                    bg,
                    borderStyle,
                    totalBorderW,
                    boxShadow,
                    isBgTransparent,
                    isBorderNone,
                    isShadowNone,
                    isCompliant
                });
            }

            return results;
        }, SELECTORS_3D_COMPONENTS);

        auditResult.checks.transparency3D.count = transparencyData.length;
        auditResult.checks.transparency3D.checked = transparencyData.length;
        auditResult.checks.transparency3D.details = transparencyData;
        const failed3D = transparencyData.filter(d => !d.isCompliant);
        if (failed3D.length > 0) {
            auditResult.checks.transparency3D.pass = false;
        }

        // -------------------------------------------------------------
        // Check 2: Exactly 0 Instructional Text Strings in DOM
        // -------------------------------------------------------------
        const instructionMatches = await page.evaluate((bannedList) => {
            const matches = [];
            const bodyText = document.body ? document.body.innerText : '';

            // Also check all text nodes via TreeWalker to catch hidden/offscreen nodes
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                const txt = node.textContent;
                if (!txt || !txt.trim()) continue;

                for (const banned of bannedList) {
                    if (txt.toLowerCase().includes(banned.toLowerCase())) {
                        const parent = node.parentElement;
                        matches.push({
                            bannedPhrase: banned,
                            matchedText: txt.trim().substring(0, 120),
                            tagName: parent ? parent.tagName.toLowerCase() : 'unknown',
                            className: parent ? parent.className : '',
                            id: parent ? parent.id : ''
                        });
                        break;
                    }
                }
            }

            return matches;
        }, BANNED_INSTRUCTION_STRINGS);

        auditResult.checks.zeroInstructionText.occurrences = instructionMatches.length;
        auditResult.checks.zeroInstructionText.matches = instructionMatches;
        if (instructionMatches.length > 0) {
            auditResult.checks.zeroInstructionText.pass = false;
        }

        // -------------------------------------------------------------
        // Check 3: Zero Horizontal Overflow (scrollWidth === clientWidth)
        // -------------------------------------------------------------
        const overflowData = await page.evaluate(() => {
            const docEl = document.documentElement;
            const body = document.body;

            const clientWidth = docEl.clientWidth;
            const docScrollWidth = docEl.scrollWidth;
            const bodyScrollWidth = body ? body.scrollWidth : 0;
            const effectiveScrollWidth = Math.max(docScrollWidth, bodyScrollWidth);
            const overflowDiff = Math.max(0, effectiveScrollWidth - clientWidth);

            const offenders = [];
            // Subpixel tolerance threshold: > 1px
            if (overflowDiff > 1) {
                const all = Array.from(document.querySelectorAll('*'));
                for (const el of all) {
                    const rect = el.getBoundingClientRect();
                    if (rect.right > clientWidth + 1.5) {
                        offenders.push({
                            tagName: el.tagName.toLowerCase(),
                            className: typeof el.className === 'string' ? el.className.substring(0, 100) : '',
                            id: el.id,
                            rectRight: Math.round(rect.right),
                            clientWidth: clientWidth,
                            excessPx: Math.round(rect.right - clientWidth)
                        });
                    }
                    if (offenders.length >= 8) break; // Limit to top 8 offenders
                }
            }

            return {
                clientWidth,
                docScrollWidth,
                bodyScrollWidth,
                overflowDiff,
                offenders
            };
        });

        auditResult.checks.zeroOverflow.scrollWidth = overflowData.docScrollWidth;
        auditResult.checks.zeroOverflow.clientWidth = overflowData.clientWidth;
        auditResult.checks.zeroOverflow.overflow = overflowData.overflowDiff;
        auditResult.checks.zeroOverflow.offenders = overflowData.offenders;
        if (overflowData.overflowDiff > 1) {
            auditResult.checks.zeroOverflow.pass = false;
        }

        // -------------------------------------------------------------
        // Check 4: WCAG AA/AAA Contrast Evaluation
        // -------------------------------------------------------------
        const contrastData = await page.evaluate(() => {
            function getLuminance(r, g, b) {
                const [rs, gs, bs] = [r, g, b].map(c => {
                    const val = c / 255;
                    return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
                });
                return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
            }

            function parseRgb(colorStr, fallback = { r: 255, g: 255, b: 255 }) {
                if (!colorStr || colorStr === 'transparent') return null;
                const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
                if (!match) return null;
                const alpha = match[4] !== undefined ? parseFloat(match[4]) : 1;
                return {
                    r: parseInt(match[1], 10),
                    g: parseInt(match[2], 10),
                    b: parseInt(match[3], 10),
                    a: alpha
                };
            }

            function blendColors(layer, base) {
                if (!layer) return base;
                if (!base) return { r: layer.r, g: layer.g, b: layer.b };
                const a = layer.a !== undefined ? layer.a : 1;
                return {
                    r: Math.round(layer.r * a + base.r * (1 - a)),
                    g: Math.round(layer.g * a + base.g * (1 - a)),
                    b: Math.round(layer.b * a + base.b * (1 - a))
                };
            }

            function getEffectiveBg(el) {
                let cur = el;
                let bgStack = [];

                while (cur && cur !== document.documentElement) {
                    const style = window.getComputedStyle(cur);
                    const bg = style.backgroundColor;
                    const parsed = parseRgb(bg);
                    if (parsed && parsed.a > 0) {
                        bgStack.unshift(parsed);
                        if (parsed.a >= 0.98) break;
                    }
                    cur = cur.parentElement;
                }

                let finalBg = { r: 255, g: 255, b: 255 }; // Default page canvas fallback
                for (const layer of bgStack) {
                    finalBg = blendColors(layer, finalBg);
                }
                return finalBg;
            }

            function calculateContrastRatio(fg, bg) {
                const l1 = getLuminance(fg.r, fg.g, fg.b);
                const l2 = getLuminance(bg.r, bg.g, bg.b);
                const lighter = Math.max(l1, l2);
                const darker = Math.min(l1, l2);
                return (lighter + 0.05) / (darker + 0.05);
            }

            // Target elements representing primary visual hierarchy & high-risk components
            const selector = 'h1, h2, h3, h4, h5, h6, p, .btn, .badge, .rounded-pill, .inn-faq-button, th, td, .small, a';
            const elements = Array.from(document.querySelectorAll(selector));
            const violations = [];
            let testedCount = 0;

            for (const el of elements) {
                // Must be visible with actual text content
                const text = el.innerText ? el.innerText.trim() : '';
                if (!text || text.length < 2) continue;

                // Ignore accessibility skip-to-content or screen-reader-only utility elements
                if (el.classList.contains('o_skip_to_content') ||
                    el.classList.contains('visually-hidden') ||
                    el.classList.contains('sr-only') ||
                    el.closest('.o_skip_to_content')) {
                    continue;
                }

                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                if (rect.bottom <= 0 || rect.right <= 0) continue;

                const style = window.getComputedStyle(el);
                if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity) < 0.1) continue;

                const fgParsed = parseRgb(style.color);
                if (!fgParsed) continue;

                const bg = getEffectiveBg(el);
                const ratio = calculateContrastRatio(fgParsed, bg);
                testedCount++;

                const bgLum = getLuminance(bg.r, bg.g, bg.b);
                const isHeading = /^H[1-6]$/i.test(el.tagName);
                const isDarkCanvas = bgLum < 0.2;

                const fontSize = parseFloat(style.fontSize) || 16;
                const fontWeight = parseInt(style.fontWeight, 10) || 400;
                const isBold = fontWeight >= 600 || style.fontWeight === 'bold';
                const isLargeText = (fontSize >= 24) || (fontSize >= 18.5 && isBold);

                // Thresholds per WCAG 2.1 & task contract:
                // - Headings on dark canvas: >= 7.0:1 (WCAG AAA)
                // - Large text (>= 24px or >= 18.5px bold): >= 3.0:1 (WCAG AA)
                // - Normal body text & UI labels: >= 4.5:1 (WCAG AA)
                let requiredRatio = 4.5;
                if (isHeading && isDarkCanvas) {
                    requiredRatio = 7.0;
                } else if (isLargeText && !isHeading) {
                    requiredRatio = 3.0;
                }

                if (ratio < requiredRatio) {
                    violations.push({
                        tagName: el.tagName.toLowerCase(),
                        className: typeof el.className === 'string' ? el.className.substring(0, 80) : '',
                        text: text.substring(0, 60),
                        fgColor: style.color,
                        bgColor: `rgb(${bg.r}, ${bg.g}, ${bg.b})`,
                        ratio: Math.round(ratio * 100) / 100,
                        requiredRatio: requiredRatio,
                        isHeading,
                        isDarkCanvas,
                        isLargeText
                    });
                    if (violations.length >= 15) break; // Limit report to 15
                }
            }

            return { testedCount, violations };
        });

        auditResult.checks.wcagContrast.testedCount = contrastData.testedCount;
        auditResult.checks.wcagContrast.violations = contrastData.violations;
        if (contrastData.violations.length > 0) {
            auditResult.checks.wcagContrast.pass = false;
        }

        // -------------------------------------------------------------
        // Check 5: Zero Unhandled Console Errors
        // -------------------------------------------------------------
        auditResult.checks.consoleErrors.errors = consoleErrors;
        if (consoleErrors.length > 0) {
            auditResult.checks.consoleErrors.pass = false;
        }

        // Overall status for this route & viewport
        auditResult.passed = (
            auditResult.checks.transparency3D.pass &&
            auditResult.checks.zeroInstructionText.pass &&
            auditResult.checks.zeroOverflow.pass &&
            auditResult.checks.wcagContrast.pass &&
            auditResult.checks.consoleErrors.pass &&
            auditResult.httpStatus === 200
        );

    } catch (err) {
        auditResult.passed = false;
        auditResult.error = err.message || String(err);
        consoleErrors.push(auditResult.error);
    } finally {
        page.off('console', onConsole);
        page.off('pageerror', onPageError);
    }

    return auditResult;
}

/**
 * Main Execution Runner
 */
async function run() {
    console.log(`\n${colors.bold}${colors.cyan}==============================================================================${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}  INNORIA PLATFORM MULTI-ROUTE QUALITY & RESPONSIVE LAYOUT VERIFICATION SUITE ${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}==============================================================================${colors.reset}`);
    console.log(`${colors.gray}Target Base URL: ${BASE_URL}${colors.reset}`);
    console.log(`${colors.gray}Headless Mode:   ${IS_HEADLESS ? 'YES' : 'NO'}${colors.reset}`);
    console.log(`${colors.gray}Timeout SLA:     ${TIMEOUT_MS}ms${colors.reset}\n`);

    const routesToTest = SINGLE_ROUTE
        ? ALL_ROUTES.filter(r => r.path === SINGLE_ROUTE)
        : ALL_ROUTES;

    if (routesToTest.length === 0) {
        console.error(`${colors.red}Error: Specified route "${SINGLE_ROUTE}" not found in routes manifest.${colors.reset}`);
        process.exit(1);
    }

    const viewportsToTest = SINGLE_VIEWPORT
        ? { [SINGLE_VIEWPORT]: ALL_VIEWPORTS[SINGLE_VIEWPORT] }
        : ALL_VIEWPORTS;

    if (Object.keys(viewportsToTest).length === 0 || !Object.values(viewportsToTest)[0]) {
        console.error(`${colors.red}Error: Specified viewport "${SINGLE_VIEWPORT}" invalid. Must be mobile, tablet, or desktop.${colors.reset}`);
        process.exit(1);
    }

    const browser = await chromium.launch({
        headless: IS_HEADLESS,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
    });

    const allResults = [];
    let totalChecksFailed = 0;

    for (const [vpKey, vp] of Object.entries(viewportsToTest)) {
        console.log(`${colors.bold}${colors.magenta}>>> Scanning Viewport: ${vp.name.toUpperCase()} (${vp.width}x${vp.height})${colors.reset}`);

        const context = await browser.newContext({
            viewport: { width: vp.width, height: vp.height },
            isMobile: vp.isMobile,
            ignoreHTTPSErrors: true
        });

        const page = await context.newPage();

        for (const route of routesToTest) {
            process.stdout.write(`  [..] Auditing ${route.path.padEnd(12)} (${route.name}) ... `);
            const res = await auditPage(page, route, vpKey, vp);
            allResults.push(res);

            if (res.passed) {
                console.log(`${colors.green}✓ PASS${colors.reset}`);
            } else {
                console.log(`${colors.red}✗ FAIL${colors.reset}`);
                totalChecksFailed++;
                if (IS_VERBOSE) {
                    if (!res.checks.transparency3D.pass) {
                        console.log(`       ${colors.yellow}└─ 3D Transparency Fail:${colors.reset} Non-transparent containers: ${res.checks.transparency3D.details.filter(d => !d.isCompliant).map(d => `<${d.tagName} .${d.className}>`).join(', ')}`);
                    }
                    if (!res.checks.zeroInstructionText.pass) {
                        console.log(`       ${colors.yellow}└─ Instruction Text Fail:${colors.reset} Found ${res.checks.zeroInstructionText.occurrences} instances: ${res.checks.zeroInstructionText.matches.map(m => `"${m.bannedPhrase}" in <${m.tagName}>`).join('; ')}`);
                    }
                    if (!res.checks.zeroOverflow.pass) {
                        console.log(`       ${colors.yellow}└─ Overflow Fail:${colors.reset} scrollWidth ${res.checks.zeroOverflow.scrollWidth} > clientWidth ${res.checks.zeroOverflow.clientWidth} (+${res.checks.zeroOverflow.overflow}px)`);
                    }
                    if (!res.checks.wcagContrast.pass) {
                        console.log(`       ${colors.yellow}└─ Contrast Fail:${colors.reset} ${res.checks.wcagContrast.violations.length} violations:`);
                        for (const v of res.checks.wcagContrast.violations) {
                            console.log(`          • [${v.tagName.toUpperCase()}] "${v.text}": ratio ${v.ratio}:1 (required ${v.requiredRatio}:1, fg: ${v.fgColor}, bg: ${v.bgColor})`);
                        }
                    }
                    if (!res.checks.consoleErrors.pass) {
                        console.log(`       ${colors.yellow}└─ Console Errors:${colors.reset} ${res.checks.consoleErrors.errors.join(' | ')}`);
                    }
                }
            }
        }

        await context.close();
    }

    await browser.close();

    // -----------------------------------------------------------------
    // Render Comprehensive Diagnostic Summary Table
    // -----------------------------------------------------------------
    console.log(`\n${colors.bold}${colors.cyan}========================================================================================================${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}                                     DIAGNOSTIC VERIFICATION MATRIX                                     ${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}========================================================================================================${colors.reset}`);

    const header = `| ${'Route'.padEnd(12)} | ${'Viewport'.padEnd(8)} | ${'3D Transp'.padEnd(13)} | ${'Zero Inst'.padEnd(11)} | ${'Zero Overflow'.padEnd(15)} | ${'Contrast'.padEnd(12)} | ${'Console'.padEnd(10)} | ${'Result'.padEnd(6)} |`;
    const sep = `|${'-'.repeat(14)}|${'-'.repeat(10)}|${'-'.repeat(15)}|${'-'.repeat(13)}|${'-'.repeat(17)}|${'-'.repeat(14)}|${'-'.repeat(12)}|${'-'.repeat(8)}|`;

    console.log(header);
    console.log(sep);

    for (const r of allResults) {
        const c3D = r.checks.transparency3D.pass
            ? (r.checks.transparency3D.count > 0 ? `${colors.green}PASS (${r.checks.transparency3D.count})${colors.reset}` : `${colors.gray}N/A${colors.reset}`)
            : `${colors.red}FAIL (${r.checks.transparency3D.details.filter(d => !d.isCompliant).length})${colors.reset}`;

        const cInst = r.checks.zeroInstructionText.pass
            ? `${colors.green}PASS (0)${colors.reset}`
            : `${colors.red}FAIL (${r.checks.zeroInstructionText.occurrences})${colors.reset}`;

        const cOver = r.checks.zeroOverflow.pass
            ? `${colors.green}PASS (0px)${colors.reset}`
            : `${colors.red}FAIL (+${r.checks.zeroOverflow.overflow}px)${colors.reset}`;

        const cCont = r.checks.wcagContrast.pass
            ? `${colors.green}PASS${colors.reset}`
            : `${colors.red}FAIL (${r.checks.wcagContrast.violations.length})${colors.reset}`;

        const cCons = r.checks.consoleErrors.pass
            ? `${colors.green}PASS (0)${colors.reset}`
            : `${colors.red}FAIL (${r.checks.consoleErrors.errors.length})${colors.reset}`;

        const resStr = r.passed
            ? `${colors.bold}${colors.green}PASS${colors.reset}`
            : `${colors.bold}${colors.red}FAIL${colors.reset}`;

        console.log(`| ${r.route.padEnd(12)} | ${r.viewport.padEnd(8)} | ${c3D.padEnd(22)} | ${cInst.padEnd(20)} | ${cOver.padEnd(24)} | ${cCont.padEnd(21)} | ${cCons.padEnd(19)} | ${resStr.padEnd(15)} |`);
    }

    console.log(sep);

    // Summary Totals
    const totalRuns = allResults.length;
    const passedRuns = allResults.filter(r => r.passed).length;
    console.log(`\n${colors.bold}SUMMARY:${colors.reset} ${passedRuns}/${totalRuns} combinations passed (100% required for gate acceptance).`);

    // Write JSON report if requested
    if (JSON_OUTPUT_PATH) {
        const dir = path.dirname(JSON_OUTPUT_PATH);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(JSON_OUTPUT_PATH, JSON.stringify({
            timestamp: new Date().toISOString(),
            baseUrl: BASE_URL,
            totalRuns,
            passedRuns,
            allResults
        }, null, 2));
        console.log(`${colors.gray}Wrote full JSON diagnostic report to: ${JSON_OUTPUT_PATH}${colors.reset}`);
    }

    if (totalChecksFailed > 0) {
        console.log(`\n${colors.red}${colors.bold}[FAIL] Verification failed with ${totalChecksFailed} route/viewport defects detected.${colors.reset}\n`);
        process.exit(1);
    } else {
        console.log(`\n${colors.green}${colors.bold}[SUCCESS] All routes and viewports passed 100% with zero defects.${colors.reset}\n`);
        process.exit(0);
    }
}

// Execute
run().catch(err => {
    console.error(`\n${colors.red}Fatal Execution Error:${colors.reset}`, err);
    process.exit(1);
});
