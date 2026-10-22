const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

    for (const path of ['/', '/solutions']) {
        console.log(`\n=== CHECKING CONTRAST ON ${path} (1440x900) ===`);
        await page.goto(`https://innoria.com${path}`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);

        const violations = await page.evaluate(() => {
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
                return { r: parseInt(match[1], 10), g: parseInt(match[2], 10), b: parseInt(match[3], 10), a: alpha };
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
                let finalBg = { r: 255, g: 255, b: 255 };
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

            const selector = 'h1, h2, h3, h4, h5, h6, p, .btn, .badge, .rounded-pill, .inn-faq-button, th, td, .small, a';
            const elements = Array.from(document.querySelectorAll(selector));
            const viols = [];

            for (const el of elements) {
                const text = el.innerText ? el.innerText.trim() : '';
                if (!text || text.length < 2) continue;
                if (el.classList.contains('o_skip_to_content') || el.classList.contains('visually-hidden') || el.closest('.o_skip_to_content')) continue;

                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0 || rect.bottom <= 0 || rect.right <= 0) continue;

                const style = window.getComputedStyle(el);
                if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity) < 0.1) continue;

                const fgParsed = parseRgb(style.color);
                if (!fgParsed) continue;

                const bg = getEffectiveBg(el);
                const ratio = calculateContrastRatio(fgParsed, bg);

                const bgLum = getLuminance(bg.r, bg.g, bg.b);
                const isHeading = /^H[1-6]$/i.test(el.tagName);
                const isDarkCanvas = bgLum < 0.2;
                const fontSize = parseFloat(style.fontSize) || 16;
                const fontWeight = parseInt(style.fontWeight, 10) || 400;
                const isBold = fontWeight >= 600 || style.fontWeight === 'bold';
                const isLargeText = (fontSize >= 24) || (fontSize >= 18.5 && isBold);

                let requiredRatio = 4.5;
                if (isHeading && isDarkCanvas) {
                    requiredRatio = 7.0;
                } else if (isLargeText && !isHeading) {
                    requiredRatio = 3.0;
                }

                if (ratio < requiredRatio) {
                    viols.push({
                        tag: el.tagName,
                        cls: el.className,
                        id: el.id,
                        text: text.substring(0, 80),
                        fg: style.color,
                        bg: `rgb(${bg.r},${bg.g},${bg.b})`,
                        ratio: Math.round(ratio * 100) / 100,
                        requiredRatio,
                        isHeading,
                        isDarkCanvas,
                        outerHTML: el.outerHTML.substring(0, 150)
                    });
                }
            }
            return viols;
        });

        console.log(`Found ${violations.length} violations:`);
        violations.forEach((v, i) => {
            console.log(`[${i+1}] <${v.tag}> ${v.text}`);
            console.log(`    fg: ${v.fg}, bg: ${v.bg}, ratio: ${v.ratio} vs req: ${v.requiredRatio} (isHeading: ${v.isHeading}, isDark: ${v.isDarkCanvas})`);
            console.log(`    class: ${v.cls}`);
            console.log(`    html: ${v.outerHTML}`);
        });
    }

    await browser.close();
})();
