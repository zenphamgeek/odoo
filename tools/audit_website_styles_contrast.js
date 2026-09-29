#!/usr/bin/env node
/**
 * Insilos Enterprise Website Styles & Contrast Automated Auditor
 * =============================================================
 * Scans all badges, pills, and status chips across key routes:
 * 1. Text-to-background contrast ratio >= 4.5:1 (WCAG AA/AAA).
 * 2. Absolute vertical and horizontal center alignment (inline-flex/flex, align-items: center, justify-content: center).
 *
 * Usage: node tools/audit_website_styles_contrast.js
 */

const { chromium } = require('playwright-core');

// WCAG 2.1 Relative Luminance Calculation
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

(async () => {
    const browser = await chromium.launch({
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const routes = [
        '/',
        '/solutions',
        '/industries',
        '/resources',
        '/showcase-3d',
        '/privacy-policy'
    ];

    const results = [];
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

    for (const route of routes) {
        const url = `http://localhost:28069${route}`;
        try {
            console.log(`Auditing ${route}...`);
            const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
            await page.waitForTimeout(1500);

            if (!resp || resp.status() !== 200) {
                console.error(`Route ${route} returned status ${resp ? resp.status() : 'null'}`);
                continue;
            }

            const pageBadges = await page.evaluate(() => {
                // Query badges, pills, and chips (excluding standard CTA buttons)
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
                    // Filter out hidden elements (e.g. cart badge when count is 0)
                    const isVisible = style.display !== 'none' &&
                                      style.visibility !== 'hidden' &&
                                      el.offsetWidth > 0 &&
                                      el.offsetHeight > 0;

                    if (!isVisible) return null;

                    return {
                        text: (el.innerText || '').trim(),
                        className: el.className,
                        tagName: el.tagName,
                        color: style.color,
                        bgColor: style.backgroundColor,
                        effectiveBg: getEffectiveBg(el),
                        display: style.display,
                        alignItems: style.alignItems,
                        justifyContent: style.justifyContent,
                        verticalAlign: style.verticalAlign,
                        lineHeight: style.lineHeight
                    };
                }).filter(b => b !== null && b.text.length > 0 && b.text.length < 80);
            });

            console.log(`  Found ${pageBadges.length} visible badge/pill elements on ${route}`);

            for (const b of pageBadges) {
                const rawFg = parseRgb(b.color);
                const rawBg = parseRgb(b.bgColor);
                const underBg = parseRgb(b.effectiveBg) || { r: 7, g: 11, b: 20, a: 1 };

                // Alpha composite background over underlying canvas
                const compBg = (rawBg && rawBg.a < 1) ? blendColor(rawBg, underBg) : (rawBg || underBg);
                // Alpha composite foreground if needed
                const compFg = (rawFg && rawFg.a < 1) ? blendColor(rawFg, compBg) : rawFg;

                let contrast = 0;
                if (compFg && compBg) {
                    contrast = calculateContrast(compFg, compBg);
                }

                const isCentered = (b.display === 'inline-flex' || b.display === 'flex') &&
                                   (b.alignItems === 'center' || b.alignItems === 'safe center') &&
                                   (b.justifyContent === 'center' || b.justifyContent === 'safe center');

                results.push({
                    route,
                    ...b,
                    contrast: parseFloat(contrast.toFixed(2)),
                    isCentered
                });
            }
        } catch (e) {
            console.error(`Error auditing ${route}:`, e.message);
        }
    }

    await browser.close();

    const lowContrast = results.filter(r => r.contrast < 4.5);
    const uncentered = results.filter(r => !r.isCentered);

    console.log(`\n================ AUDIT SUMMARY ================`);
    console.log(`Total Badges/Pills Analyzed: ${results.length}`);
    console.log(`WCAG Compliant (>= 4.5:1): ${results.length - lowContrast.length}/${results.length}`);
    console.log(`Low Contrast Violations: ${lowContrast.length}`);
    console.log(`Centered Badges: ${results.length - uncentered.length}/${results.length}`);
    console.log(`Uncentered Violations: ${uncentered.length}`);

    if (lowContrast.length > 0) {
        console.log(`\nSample Low Contrast Violations:`);
        lowContrast.slice(0, 20).forEach(v => {
            console.log(`- [${v.route}] "${v.text}": contrast ${v.contrast}:1 (fg: ${v.color}, bg: ${v.bgColor} over ${v.effectiveBg}) [class: ${v.className}]`);
        });
    }

    if (uncentered.length > 0) {
        console.log(`\nSample Uncentered Violations:`);
        uncentered.slice(0, 20).forEach(v => {
            console.log(`- [${v.route}] "${v.text}": display: ${v.display}, align: ${v.alignItems}, justify: ${v.justifyContent} [class: ${v.className}]`);
        });
    }

    if (lowContrast.length === 0 && uncentered.length === 0) {
        console.log(`\n🎉 ALL CHECKS PASSED: 0 Low Contrast Violations, 0 Uncentered Violations!`);
        process.exit(0);
    } else {
        console.error(`\n❌ AUDIT FAILED: Fix the violations listed above.`);
        process.exit(1);
    }
})();
