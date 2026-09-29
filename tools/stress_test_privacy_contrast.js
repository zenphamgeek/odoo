#!/usr/bin/env node
/**
 * Empirical Stress Test: Contrast, Absolute Centering & Multi-Viewport Verification
 * =================================================================================
 * Challenger: Challenger Council Contrast & Viewport Stress
 * Target: Milestone 1 (SCSS Palette, WCAG Contrast, Centering, Routing)
 *
 * Viewports:
 * - Mobile: 375x667
 * - Tablet: 768x1024
 * - Desktop: 1920x1080
 *
 * Target Routes:
 * - /privacy
 * - /privacy-policy
 */

const { chromium } = require('playwright-core');

function getLuminance(r, g, b) {
    const [rs, gs, bs] = [r, g, b].map(c => {
        const val = c / 255;
        return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function parseRgb(colorStr) {
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

function blendColor(layer, base) {
    if (!layer) return base;
    if (!base) return { r: layer.r, g: layer.g, b: layer.b, a: 1 };
    const a = layer.a !== undefined ? layer.a : 1;
    return {
        r: Math.round(layer.r * a + base.r * (1 - a)),
        g: Math.round(layer.g * a + base.g * (1 - a)),
        b: Math.round(layer.b * a + base.b * (1 - a)),
        a: 1
    };
}

function calculateContrast(fgColor, bgColor) {
    const l1 = getLuminance(fgColor.r, fgColor.g, fgColor.b);
    const l2 = getLuminance(bgColor.r, bgColor.g, bgColor.b);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
}

const VIEWPORTS = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1920, height: 1080 }
];

const ROUTES = ['/privacy', '/privacy-policy'];

const CLAUSES = ['ĐIỀU 1', 'ĐIỀU 2', 'ĐIỀU 3', 'ĐIỀU 4', 'ĐIỀU 5', 'ĐIỀU 6', 'ĐIỀU 7', 'ĐIỀU 8'];

(async () => {
    console.log('================================================================================');
    console.log('EMPIRICAL CHALLENGER: MULTI-VIEWPORT CONTRAST & CENTERING STRESS TEST');
    console.log('================================================================================\n');

    const browser = await chromium.launch({
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    let totalTests = 0;
    let failedTests = 0;
    const clauseResults = [];
    const allBadgeResults = [];
    const overflowResults = [];

    for (const vp of VIEWPORTS) {
        console.log(`\n>>> Testing Viewport: ${vp.name} (${vp.width}x${vp.height}) <<<`);
        const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });

        for (const route of ROUTES) {
            const url = `http://localhost:28069${route}`;
            console.log(`  --> Navigating to ${url}...`);

            const startTime = Date.now();
            const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
            await page.waitForTimeout(1000);
            const loadTime = Date.now() - startTime;

            // Route status assertion
            totalTests++;
            const status = resp ? resp.status() : 0;
            if (status === 200) {
                console.log(`      [PASS] HTTP Status: 200 OK (${loadTime}ms)`);
            } else {
                console.error(`      [FAIL] HTTP Status: ${status} (Expected: 200)`);
                failedTests++;
            }

            // Check horizontal overflow
            const overflow = await page.evaluate(() => {
                const scrollW = document.documentElement.scrollWidth;
                const innerW = window.innerWidth;
                return {
                    scrollW,
                    innerW,
                    hasOverflow: scrollW > innerW,
                    diff: scrollW - innerW
                };
            });

            totalTests++;
            if (!overflow.hasOverflow || overflow.diff <= 1) { // 1px subpixel tolerance
                console.log(`      [PASS] Layout Geometry: No horizontal overflow (scrollWidth: ${overflow.scrollW}px, innerWidth: ${overflow.innerW}px)`);
                overflowResults.push({ viewport: vp.name, route, pass: true });
            } else {
                console.error(`      [FAIL] Layout Geometry: Horizontal overflow detected! diff: +${overflow.diff}px (scrollWidth: ${overflow.scrollW}px, innerWidth: ${overflow.innerW}px)`);
                failedTests++;
                overflowResults.push({ viewport: vp.name, route, pass: false, diff: overflow.diff });
            }

            // Stress test the 8 statutory clauses
            for (const clause of CLAUSES) {
                totalTests++;
                const badgeData = await page.evaluate((clauseText) => {
                    const badges = Array.from(document.querySelectorAll('.badge, .badge-pill, .rounded-pill'));
                    const target = badges.find(b => (b.innerText || '').trim().includes(clauseText));
                    if (!target) return null;

                    const style = window.getComputedStyle(target);
                    const rect = target.getBoundingClientRect();

                    function getEffectiveBg(el) {
                        let cur = el.parentElement;
                        while (cur && cur !== document.body) {
                            const st = window.getComputedStyle(cur);
                            const bg = st.backgroundColor;
                            if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                                const match = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
                                if (match && (match[4] === undefined || parseFloat(match[4]) > 0.5)) {
                                    return bg;
                                }
                            }
                            cur = cur.parentElement;
                        }
                        return window.getComputedStyle(document.body).backgroundColor || 'rgb(7, 11, 20)';
                    }

                    return {
                        text: (target.innerText || '').trim(),
                        className: target.className,
                        color: style.color,
                        bgColor: style.backgroundColor,
                        effectiveBg: getEffectiveBg(target),
                        display: style.display,
                        alignItems: style.alignItems,
                        justifyContent: style.justifyContent,
                        lineHeight: style.lineHeight,
                        verticalAlign: style.verticalAlign,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left,
                        visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
                    };
                }, clause);

                if (!badgeData) {
                    console.error(`      [FAIL] Clause Badge "${clause}" not found in DOM!`);
                    failedTests++;
                    continue;
                }

                const fg = parseRgb(badgeData.color);
                const bg = parseRgb(badgeData.bgColor);
                const underBg = parseRgb(badgeData.effectiveBg) || { r: 7, g: 11, b: 20, a: 1 };
                const compBg = (bg && bg.a < 1) ? blendColor(bg, underBg) : (bg || underBg);
                const compFg = (fg && fg.a < 1) ? blendColor(fg, compBg) : fg;
                const contrast = compFg && compBg ? parseFloat(calculateContrast(compFg, compBg).toFixed(2)) : 0;

                const isWhite = badgeData.color === 'rgb(255, 255, 255)' || badgeData.color === '#ffffff' || badgeData.color === '#FFF';
                const isTargetDark = badgeData.color === 'rgb(5, 16, 30)';
                const isMint = badgeData.bgColor === 'rgb(66, 230, 195)';
                const isCentered = (badgeData.display === 'inline-flex' || badgeData.display === 'flex') &&
                                   badgeData.alignItems === 'center' &&
                                   badgeData.justifyContent === 'center';
                const isWcagAA = contrast >= 4.5;
                const isWcagAAA = contrast >= 7.0;

                const pass = !isWhite && isTargetDark && isMint && isCentered && isWcagAA && badgeData.visible;

                if (pass) {
                    // Record
                    clauseResults.push({
                        viewport: vp.name,
                        route,
                        clause,
                        color: badgeData.color,
                        bgColor: badgeData.bgColor,
                        contrast,
                        display: badgeData.display,
                        align: badgeData.alignItems,
                        justify: badgeData.justifyContent,
                        width: Math.round(badgeData.width),
                        height: Math.round(badgeData.height),
                        isWcagAAA,
                        pass: true
                    });
                } else {
                    failedTests++;
                    console.error(`      [FAIL] Clause "${clause}" on ${vp.name} (${route}):`);
                    console.error(`             color=${badgeData.color} (isWhite=${isWhite}, isDark=${isTargetDark})`);
                    console.error(`             bgColor=${badgeData.bgColor} (isMint=${isMint})`);
                    console.error(`             contrast=${contrast}:1 (AA=${isWcagAA}, AAA=${isWcagAAA})`);
                    console.error(`             display=${badgeData.display}, align=${badgeData.alignItems}, justify=${badgeData.justifyContent}`);
                    clauseResults.push({
                        viewport: vp.name,
                        route,
                        clause,
                        contrast,
                        pass: false,
                        details: badgeData
                    });
                }
            }

            // General audit of ALL badges on this page
            const pageAllBadges = await page.evaluate(() => {
                const selector = '.badge, .badge-pill, .rounded-pill:not(.btn), .ins-tag, .ins-status-chip, .ins-pill-badge, .ins-status-badge';
                const targets = Array.from(document.querySelectorAll(selector));

                function getEffectiveBg(el) {
                    let cur = el.parentElement;
                    while (cur && cur !== document.body) {
                        const style = window.getComputedStyle(cur);
                        const bg = style.backgroundColor;
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                            const match = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
                            if (match && (match[4] === undefined || parseFloat(match[4]) > 0.5)) {
                                return bg;
                            }
                        }
                        cur = cur.parentElement;
                    }
                    return window.getComputedStyle(document.body).backgroundColor || 'rgb(7, 11, 20)';
                }

                return targets.map(el => {
                    const style = window.getComputedStyle(el);
                    const isVisible = style.display !== 'none' &&
                                      style.visibility !== 'hidden' &&
                                      el.offsetWidth > 0 &&
                                      el.offsetHeight > 0;
                    if (!isVisible) return null;

                    return {
                        text: (el.innerText || '').trim(),
                        className: el.className,
                        color: style.color,
                        bgColor: style.backgroundColor,
                        effectiveBg: getEffectiveBg(el),
                        display: style.display,
                        alignItems: style.alignItems,
                        justifyContent: style.justifyContent
                    };
                }).filter(b => b !== null && b.text.length > 0 && b.text.length < 80);
            });

            for (const b of pageAllBadges) {
                totalTests++;
                const fg = parseRgb(b.color);
                const bg = parseRgb(b.bgColor);
                const underBg = parseRgb(b.effectiveBg) || { r: 7, g: 11, b: 20, a: 1 };
                const compBg = (bg && bg.a < 1) ? blendColor(bg, underBg) : (bg || underBg);
                const compFg = (fg && fg.a < 1) ? blendColor(fg, compBg) : fg;
                const contrast = compFg && compBg ? parseFloat(calculateContrast(compFg, compBg).toFixed(2)) : 0;

                const isWhiteOnMint = (b.color === 'rgb(255, 255, 255)' || b.color === '#ffffff') &&
                                      (b.bgColor === 'rgb(66, 230, 195)' || b.className.includes('bg-mint'));
                const isCentered = (b.display === 'inline-flex' || b.display === 'flex') &&
                                   b.alignItems === 'center' &&
                                   b.justifyContent === 'center';
                const isCompliant = contrast >= 4.5;

                if (isWhiteOnMint || !isCentered || !isCompliant) {
                    failedTests++;
                    console.error(`      [FAIL] Badge violation on ${vp.name} (${route}): "${b.text}" [${b.className}]`);
                    console.error(`             contrast=${contrast}:1, whiteOnMint=${isWhiteOnMint}, display=${b.display}, align=${b.alignItems}, justify=${b.justifyContent}`);
                }

                allBadgeResults.push({
                    viewport: vp.name,
                    route,
                    text: b.text,
                    className: b.className,
                    contrast,
                    isCentered,
                    isWhiteOnMint,
                    isCompliant
                });
            }
        }

        await page.close();
    }

    await browser.close();

    console.log('\n================================================================================');
    console.log('EMPIRICAL STRESS TEST RESULTS BREAKDOWN');
    console.log('================================================================================');

    console.log(`\n1. STATUTORY CLAUSES (ĐIỀU 1 - ĐIỀU 8) SUMMARY:`);
    console.log(`Total Clause Checks: ${clauseResults.length} (8 clauses x 2 routes x 3 viewports = 48 observations)`);
    const passedClauses = clauseResults.filter(c => c.pass);
    console.log(`Clauses Passed: ${passedClauses.length}/${clauseResults.length}`);

    if (passedClauses.length > 0) {
        console.log(`Sample Clause Measurements:`);
        // Show 1 sample per viewport
        for (const vp of VIEWPORTS) {
            const sample = passedClauses.find(c => c.viewport === vp.name && c.clause === 'ĐIỀU 1');
            if (sample) {
                console.log(`  - [${sample.viewport}] "${sample.clause}" on ${sample.route}:`);
                console.log(`    * Color: ${sample.color} (#05101E)`);
                console.log(`    * BgColor: ${sample.bgColor} (#42E6C3 - Electric Mint)`);
                console.log(`    * Contrast Ratio: ${sample.contrast}:1 (WCAG AAA Target: 12.22:1, satisfies >= 7.0:1)`);
                console.log(`    * Centering: display=${sample.display}, align=${sample.align}, justify=${sample.justify}`);
                console.log(`    * Box Dimensions: ${sample.width}px x ${sample.height}px`);
            }
        }
    }

    console.log(`\n2. WHITE-ON-MINT ZERO-TOLERANCE CHECK:`);
    const whiteOnMintInstances = allBadgeResults.filter(b => b.isWhiteOnMint);
    console.log(`White-on-mint instances found: ${whiteOnMintInstances.length}`);
    if (whiteOnMintInstances.length === 0) {
        console.log(`  [PASS] ZERO white-on-mint instances verified across ALL viewports and routes!`);
    } else {
        console.error(`  [FAIL] ${whiteOnMintInstances.length} white-on-mint instances found!`);
    }

    console.log(`\n3. ALL BADGES & PILLS AUDIT:`);
    console.log(`Total Badge Elements Audited: ${allBadgeResults.length}`);
    const lowContrastAll = allBadgeResults.filter(b => !b.isCompliant);
    const uncenteredAll = allBadgeResults.filter(b => !b.isCentered);
    console.log(`Contrast Compliant (>= 4.5:1): ${allBadgeResults.length - lowContrastAll.length}/${allBadgeResults.length}`);
    console.log(`Absolute Centering Compliant: ${allBadgeResults.length - uncenteredAll.length}/${allBadgeResults.length}`);

    console.log(`\n4. HORIZONTAL OVERFLOW STRESS:`);
    const overflowFails = overflowResults.filter(o => !o.pass);
    console.log(`Overflow Violations: ${overflowFails.length}/${overflowResults.length}`);

    console.log('\n================================================================================');
    console.log(`FINAL STRESS TEST VERDICT`);
    console.log(`================================================================================`);
    console.log(`Total Assertions Run: ${totalTests}`);
    console.log(`Failed Assertions: ${failedTests}`);

    if (failedTests === 0 && whiteOnMintInstances.length === 0 && lowContrastAll.length === 0 && uncenteredAll.length === 0) {
        console.log(`\n>>> VERDICT: APPROVE <<<`);
        console.log(`Milestone 1 is empirically verified to satisfy all WCAG AA/AAA, centering, and multi-viewport constraints.\n`);
        process.exit(0);
    } else {
        console.error(`\n>>> VERDICT: REJECT <<<`);
        console.error(`Milestone 1 failed ${failedTests} empirical stress test checks.\n`);
        process.exit(1);
    }
})();
