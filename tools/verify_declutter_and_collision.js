const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const outDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/declutter_audit';
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    const routes = [
        { url: 'https://innoria.com/', name: 'homepage' },
        { url: 'https://innoria.com/solutions', name: 'solutions' },
        { url: 'https://innoria.com/platform', name: 'platform' },
        { url: 'https://innoria.com/industries', name: 'industries' }
    ];

    const results = {
        routes: {},
        clutterChecks: {},
        collisionChecks: {},
        allPassed: true
    };

    for (const route of routes) {
        console.log(`\nAuditing route: ${route.url}...`);
        try {
            await page.goto(route.url, { waitUntil: 'networkidle', timeout: 40000 });
            await page.waitForTimeout(2000);

            // 1. Check Horizontal Overflow (scrollWidth === clientWidth)
            const overflowData = await page.evaluate(() => {
                return {
                    scrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
                };
            });

            console.log(`[${route.name}] scrollWidth: ${overflowData.scrollWidth}, clientWidth: ${overflowData.clientWidth}, overflow: ${overflowData.overflow}`);
            results.routes[route.name] = overflowData;
            if (overflowData.overflow) {
                results.allPassed = false;
            }

            // 2. Check for Clutter / HUD selectors
            const clutterSelectors = [
                '.innoria-hud-control-bar',
                '.ins-hud-controls',
                '.shift-telemetry-chip',
                '.deck-footer'
            ];

            for (const sel of clutterSelectors) {
                const count = await page.$$eval(sel, els => els.filter(e => {
                    const style = window.getComputedStyle(e);
                    return style && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                }).length);
                const key = `${route.name}_${sel}`;
                results.clutterChecks[key] = count;
                if (count > 0) {
                    console.log(`[!] Found visible clutter for ${sel} on ${route.name}: count=${count}`);
                    results.allPassed = false;
                } else {
                    console.log(`[✓] Zero visible clutter for ${sel} on ${route.name}`);
                }
            }

            // 3. 3D Architecture Deck Collision Check on Homepage
            if (route.name === 'homepage') {
                const deckSection = await page.$('.s_innoria_3d_architecture_deck');
                if (deckSection) {
                    await deckSection.scrollIntoViewIfNeeded();
                    await page.waitForTimeout(1000);

                    // Hover layer 0 to test pull-out animation
                    const slab0 = await page.$('#slab-0');
                    if (slab0) {
                        await slab0.hover();
                        await page.waitForTimeout(600);
                    }

                    const collisionMetrics = await page.evaluate(() => {
                        const stage = document.querySelector('.stage-card');
                        const desc = document.querySelector('.description-column');
                        if (!stage || !desc) return null;

                        const stageRect = stage.getBoundingClientRect();
                        const descRect = desc.getBoundingClientRect();
                        const gap = descRect.left - stageRect.right;

                        // Check slabs inside stage
                        const slabs = Array.from(document.querySelectorAll('.slab-layer')).map(s => {
                            const r = s.getBoundingClientRect();
                            return { id: s.id, right: r.right, gapToDesc: descRect.left - r.right };
                        });

                        return {
                            stageRight: stageRect.right,
                            descLeft: descRect.left,
                            columnGap: gap,
                            slabs: slabs,
                            hasCollision: gap < 0 || slabs.some(s => s.gapToDesc <= 0)
                        };
                    });

                    console.log(`[homepage 3D Deck] Collision Metrics:`, JSON.stringify(collisionMetrics, null, 2));
                    results.collisionChecks['homepage_3d_deck'] = collisionMetrics;
                    if (collisionMetrics && collisionMetrics.hasCollision) {
                        results.allPassed = false;
                    }

                    await deckSection.screenshot({ path: `${outDir}/verified_3d_architecture_deck.png` });
                    console.log(`Captured verified_3d_architecture_deck.png`);
                }
            }

            // 4. Solutions Page: Check ERP Shift section
            if (route.name === 'solutions') {
                const shiftSec = await page.$('.s_innoria_3d_erp_shift');
                if (shiftSec) {
                    await shiftSec.scrollIntoViewIfNeeded();
                    await page.waitForTimeout(1000);
                    await shiftSec.screenshot({ path: `${outDir}/verified_3d_erp_shift.png` });
                    console.log(`Captured verified_3d_erp_shift.png`);
                }
                const solutionsErp = await page.$('.s_innoria_3d_solutions_erp');
                if (solutionsErp) {
                    await solutionsErp.scrollIntoViewIfNeeded();
                    await page.waitForTimeout(1000);
                    await solutionsErp.screenshot({ path: `${outDir}/verified_3d_solutions_erp.png` });
                    console.log(`Captured verified_3d_solutions_erp.png`);
                }
            }

        } catch (err) {
            console.error(`Error auditing ${route.name}:`, err.message);
            results.routes[route.name] = { error: err.message };
            results.allPassed = false;
        }
    }

    fs.writeFileSync(`${outDir}/audit_results.json`, JSON.stringify(results, null, 2));
    await browser.close();
    console.log(`\nAudit completed! Summary: allPassed = ${results.allPassed}`);
})();
