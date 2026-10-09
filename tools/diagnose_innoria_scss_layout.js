const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const outputDir = path.join('/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_audit');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const viewports = [
        { name: 'desktop', width: 1440, height: 900 },
        { name: 'mobile', width: 375, height: 812 }
    ];

    for (const vp of viewports) {
        console.log(`\n=== Auditing Viewport: ${vp.name} (${vp.width}x${vp.height}) ===`);
        const context = await browser.newContext({
            viewport: { width: vp.width, height: vp.height },
            deviceScaleFactor: 2
        });
        const page = await context.newPage();

        const consoleLogs = [];
        const networkErrors = [];

        page.on('console', msg => {
            consoleLogs.push({ type: msg.type(), text: msg.text() });
            if (msg.type() === 'error' || msg.type() === 'warning') {
                console.log(`[Console ${msg.type().toUpperCase()}]: ${msg.text()}`);
            }
        });

        page.on('requestfailed', req => {
            networkErrors.push({ url: req.url(), failure: req.failure() ? req.failure().errorText : 'unknown' });
            console.log(`[Request Failed]: ${req.url()} - ${req.failure() ? req.failure().errorText : ''}`);
        });

        const targetUrl = 'https://innoria.insilos.com/';
        console.log(`Navigating to ${targetUrl}...`);
        await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(3000);

        // Capture fullpage
        const fullpagePath = path.join(outputDir, `innoria_${vp.name}_fullpage.png`);
        await page.screenshot({ path: fullpagePath, fullPage: true });
        console.log(`Saved screenshot: ${fullpagePath}`);

        // Capture Hero
        const heroPath = path.join(outputDir, `innoria_${vp.name}_hero.png`);
        await page.screenshot({ path: heroPath, clip: { x: 0, y: 0, width: vp.width, height: Math.min(1000, vp.height) } });

        // Evaluate layout metrics and overflows
        const analysis = await page.evaluate(() => {
            const bodyWidth = document.body.clientWidth;
            const scrollWidth = document.documentElement.scrollWidth;
            const hasHorizontalOverflow = scrollWidth > window.innerWidth;

            // Find elements causing overflow
            const overflowingElements = [];
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.right > window.innerWidth + 1) {
                    overflowingElements.push({
                        tag: el.tagName,
                        className: el.className,
                        id: el.id,
                        right: rect.right,
                        width: rect.width,
                        windowWidth: window.innerWidth
                    });
                }
            });

            // Inspect all main sections
            const sections = [];
            document.querySelectorAll('section, header, footer').forEach(sec => {
                const rect = sec.getBoundingClientRect();
                const computed = window.getComputedStyle(sec);
                sections.push({
                    tag: sec.tagName,
                    snippet: sec.getAttribute('data-snippet'),
                    name: sec.getAttribute('data-name'),
                    className: sec.className,
                    width: rect.width,
                    height: rect.height,
                    padding: computed.padding,
                    margin: computed.margin,
                    background: computed.backgroundColor,
                    color: computed.color,
                    display: computed.display
                });
            });

            // Check for broken style tags or link stylesheet errors
            const stylesheets = [];
            document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                stylesheets.push({
                    href: link.href,
                    disabled: link.disabled
                });
            });

            // Check 3D Deck or canvas elements
            const decks = [];
            document.querySelectorAll('.s_innoria_3d_architecture_deck, [data-snippet="s_innoria_3d_architecture_deck"], .s_innoria_3d_solutions_erp, canvas, .inno-3d-scene').forEach(el => {
                const rect = el.getBoundingClientRect();
                const computed = window.getComputedStyle(el);
                decks.push({
                    tag: el.tagName,
                    className: el.className,
                    width: rect.width,
                    height: rect.height,
                    opacity: computed.opacity,
                    visibility: computed.visibility,
                    transform: computed.transform
                });
            });

            return {
                windowWidth: window.innerWidth,
                bodyWidth,
                scrollWidth,
                hasHorizontalOverflow,
                overflowingElements: overflowingElements.slice(0, 10),
                sectionsCount: sections.length,
                sections: sections.slice(0, 20),
                stylesheets,
                decks
            };
        });

        console.log(`\nAnalysis for ${vp.name}:`);
        console.log(`- Horizontal Overflow: ${analysis.hasHorizontalOverflow} (scroll: ${analysis.scrollWidth}, win: ${analysis.windowWidth})`);
        if (analysis.overflowingElements.length > 0) {
            console.log(`- Overflowing elements (${analysis.overflowingElements.length}):`);
            analysis.overflowingElements.forEach(e => console.log(`  * <${e.tag} class="${e.className}" id="${e.id}"> right=${e.right}px`));
        } else {
            console.log(`- 0 Horizontal Overflowing elements!`);
        }

        console.log(`- Total Sections: ${analysis.sectionsCount}`);
        console.log(`- 3D/Canvas Elements: ${analysis.decks.length}`);
        analysis.decks.forEach(d => console.log(`  * ${d.className} (${d.width}x${d.height}, op=${d.opacity}, vis=${d.visibility})`));

        await context.close();
    }

    await browser.close();
    console.log('\nAudit complete.');
})();
