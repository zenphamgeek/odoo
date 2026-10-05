/**
 * tools/verify_innoria_multipage.js
 * =============================================================================
 * Automated Playwright Headless Verification Suite for all Innoria Enterprise Pages
 * Target: https://innoria.insilos.com
 * =============================================================================
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
const BASE_URL = 'https://innoria.insilos.com';

const PAGES = [
    {
        name: 'homepage',
        url: `${BASE_URL}/`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '#innoria_topology_section', '.innoria-footer'],
        screenshot: 'innoria_verified_homepage.png'
    },
    {
        name: 'about',
        url: `${BASE_URL}/about`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '.inn-about', '.innoria-footer'],
        screenshot: 'innoria_verified_about.png'
    },
    {
        name: 'company_alias',
        url: `${BASE_URL}/company`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '.inn-about'],
        screenshot: 'innoria_verified_company_alias.png'
    },
    {
        name: 'platform',
        url: `${BASE_URL}/platform`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '#mojo-hero', '.innoria-footer'],
        screenshot: 'innoria_verified_platform.png'
    },
    {
        name: 'ai_platform_alias',
        url: `${BASE_URL}/artificial-intelligence-platform`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '#mojo-hero'],
        screenshot: 'innoria_verified_ai_platform_alias.png'
    },
    {
        name: 'no_code',
        url: `${BASE_URL}/no-code-platform`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '.df-hero', '.innoria-footer'],
        screenshot: 'innoria_verified_no_code.png'
    },
    {
        name: 'blockchain',
        url: `${BASE_URL}/blockchain`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', 'h1:has-text("MOJOVERSE")', '.innoria-footer'],
        screenshot: 'innoria_verified_blockchain.png'
    },
    {
        name: 'solutions',
        url: `${BASE_URL}/solutions`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', 'h1:has-text("AI-Enhanced ERP")', '.innoria-footer'],
        screenshot: 'innoria_verified_solutions.png'
    },
    {
        name: 'erp_alias',
        url: `${BASE_URL}/erp-combine-with-ai`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', 'h1:has-text("AI-Enhanced ERP")'],
        screenshot: 'innoria_verified_erp_alias.png'
    },
    {
        name: 'industries',
        url: `${BASE_URL}/industries`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', 'h1:has-text("Ultra AI Vision")', '.innoria-footer'],
        screenshot: 'innoria_verified_industries.png'
    },
    {
        name: 'vision_alias',
        url: `${BASE_URL}/ultra-ai-vision`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', 'h1:has-text("Ultra AI Vision")'],
        screenshot: 'innoria_verified_vision_alias.png'
    },
    {
        name: 'contactus',
        url: `${BASE_URL}/contactus`,
        titleContains: 'INNORIA',
        selectors: ['#innoria_main_nav', '.navbar-brand-logo', '.inn-hero-gradient', '.innoria-footer'],
        screenshot: 'innoria_verified_contactus.png'
    }
];

async function runAudit() {
    console.log('===============================================================');
    console.log('INNORIA MULTI-PAGE ENTERPRISE VERIFICATION SUITE');
    console.log('Target:', BASE_URL);
    console.log('Total Pages & Aliases:', PAGES.length);
    console.log('===============================================================');

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();
    const results = [];

    for (const testPage of PAGES) {
        console.log(`\n[*] Testing [${testPage.name.toUpperCase()}]: ${testPage.url}...`);
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                const text = msg.text();
                // Filter out non-critical network/font warnings if any
                if (!text.includes('favicon') && !text.includes('fonts.googleapis') && !text.includes('404')) {
                    consoleErrors.push(text);
                }
            }
        });

        try {
            const response = await page.goto(testPage.url, { waitUntil: 'networkidle', timeout: 30000 });
            const status = response ? response.status() : 0;
            const title = await page.title();
            console.log(`  -> HTTP Status: ${status}`);
            console.log(`  -> Title: "${title}"`);

            let selectorsOk = true;
            for (const selector of testPage.selectors) {
                const el = await page.$(selector);
                if (!el) {
                    console.log(`  [✗] Missing selector: ${selector}`);
                    selectorsOk = false;
                } else {
                    console.log(`  [✓] Verified selector: ${selector}`);
                }
            }

            // Capture screenshot
            const shotPath = path.join(ARTIFACTS_DIR, testPage.screenshot);
            await page.screenshot({ path: shotPath, fullPage: true });
            console.log(`  [✓] Captured full-page screenshot -> ${shotPath}`);

            const pass = (status === 200) && selectorsOk && (title.includes(testPage.titleContains));
            results.push({
                name: testPage.name,
                url: testPage.url,
                status,
                title,
                pass,
                consoleErrorsCount: consoleErrors.length,
                screenshot: testPage.screenshot
            });

            console.log(`  -> RESULT: ${pass ? 'PASS ✓' : 'FAIL ✗'}`);
        } catch (err) {
            console.error(`  [✗] Failed to load ${testPage.url}: ${err.message}`);
            results.push({
                name: testPage.name,
                url: testPage.url,
                status: 0,
                title: 'ERROR',
                pass: false,
                error: err.message
            });
        }
    }

    await browser.close();

    console.log('\n===============================================================');
    console.log('AUDIT SUMMARY:');
    let allPassed = true;
    for (const r of results) {
        console.log(` - ${r.name.padEnd(20)}: ${r.pass ? 'PASS [✓]' : 'FAIL [✗]'} (HTTP ${r.status})`);
        if (!r.pass) allPassed = false;
    }
    console.log('===============================================================');
    console.log(`FINAL RESULT: ${allPassed ? 'ALL PAGES PASSED 100%' : 'SOME PAGES FAILED'}`);

    // Write JSON summary
    fs.writeFileSync(path.join(ARTIFACTS_DIR, 'innoria_multipage_verification.json'), JSON.stringify(results, null, 2));
    process.exit(allPassed ? 0 : 1);
}

runAudit().catch(err => {
    console.error('Fatal Error:', err);
    process.exit(1);
});
