const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
const BASE_URL = 'http://localhost:18069';

const ROUTES = [
    { name: 'unified_operations', url: `${BASE_URL}/insilos/unified-operations`, title: 'Unified Operations Hub' },
    { name: 'logistics_onboarding', url: `${BASE_URL}/insilos/logistics-onboarding`, title: 'Logistics IDP Onboarding' },
    { name: 'chemical_onboarding', url: `${BASE_URL}/insilos/chemical-onboarding`, title: 'Chemical Compliance Onboarding' },
    { name: 'hs_onboarding', url: `${BASE_URL}/insilos/hs-onboarding`, title: 'HS Tariff Sync Onboarding' },
    { name: 'hse_onboarding', url: `${BASE_URL}/insilos/hse-onboarding`, title: 'HSE Compliance Onboarding' },
    { name: 'esg_onboarding', url: `${BASE_URL}/insilos/esg-onboarding`, title: 'ESG Radar Onboarding' },
    { name: 'pubsub_onboarding', url: `${BASE_URL}/insilos/pubsub-onboarding`, title: 'Pub/Sub EDA Onboarding' },
    { name: 'logistics_overview', url: `${BASE_URL}/insilos/logistics-overview`, title: 'Logistics Overview Dashboard' },
];

async function authenticate() {
    console.log(`Authenticating session via JSON-RPC on ${BASE_URL}...`);
    const resp = await fetch(`${BASE_URL}/web/session/authenticate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: {
                db: 'insilos20_dev',
                login: 'admin',
                password: 'admin'
            }
        })
    });

    const setCookies = resp.headers.get('set-cookie') || '';
    const mSession = setCookies.match(/session_id=([^;]+)/);
    const mInsilosSession = setCookies.match(/insilos_session_id=([^;]+)/);
    const sessionId = (mInsilosSession ? mInsilosSession[1] : (mSession ? mSession[1] : null));

    if (!sessionId) {
        throw new Error(`Failed to extract session cookie from response. Set-Cookie: ${setCookies}`);
    }
    console.log(`Session authenticated successfully. Cookie prefix: ${sessionId.substring(0, 12)}...`);
    return sessionId;
}

async function runAudit() {
    console.log(`\n======================================================`);
    console.log(`Starting Insilos UI Consistency Visual Audit`);
    console.log(`Scope: ${ROUTES.length} routes in Light & Dark Mode`);
    console.log(`======================================================\n`);

    const sessionId = await authenticate();

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 1,
    });

    await context.addCookies([
        { name: 'session_id', value: sessionId, domain: 'localhost', path: '/' },
        { name: 'insilos_session_id', value: sessionId, domain: 'localhost', path: '/' },
        { name: 'frontend_lang', value: 'en_US', domain: 'localhost', path: '/' }
    ]);

    const page = await context.newPage();

    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error(`[Console Error]:`, msg.text());
            errors.push(msg.text());
        }
    });

    const results = [];

    try {
        for (const route of ROUTES) {
            console.log(`\n>>> Auditing: ${route.title} (${route.url})`);

            // Navigate to route
            await page.goto(route.url, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(4000);

            // Ensure Light Mode first
            await page.evaluate(() => {
                document.body.classList.remove('o_dark_mode');
                document.documentElement.setAttribute('data-bs-theme', 'light');
            });
            await page.waitForTimeout(300);

            // Check for dialog/error popups
            const errorDialog = await page.$('.o_dialog_error, .o_error_dialog, .modal.show .modal-title:has-text("Error")');
            if (errorDialog) {
                const dialogText = await errorDialog.innerText();
                console.error(`ERROR DIALOG on ${route.name}:`, dialogText);
                results.push({ name: route.name, status: 'ERROR_DIALOG', detail: dialogText });
                continue;
            }

            // Light screenshot
            const lightScreenshot = path.join(ARTIFACT_DIR, `audit_${route.name}_light.png`);
            await page.screenshot({ path: lightScreenshot, fullPage: true });

            // Extract layout metrics
            const metrics = await page.evaluate(() => {
                const sheet = document.querySelector('.o_form_sheet');
                const sheetBg = document.querySelector('.o_form_sheet_bg');
                const hero = document.querySelector('.insilos_hub_hero');
                const cards = document.querySelectorAll('.insilos_hub_card');
                const footerCards = document.querySelectorAll('.insilos_hub_footer_card');
                const title = document.querySelector('.insilos_hub_title, h2');
                
                return {
                    windowWidth: window.innerWidth + 'px',
                    sheetWidth: sheet ? window.getComputedStyle(sheet).width : null,
                    sheetMaxWidth: sheet ? window.getComputedStyle(sheet).maxWidth : null,
                    sheetBgWidth: sheetBg ? window.getComputedStyle(sheetBg).width : null,
                    heroWidth: hero ? window.getComputedStyle(hero).width : null,
                    hasHero: !!hero,
                    cardsCount: cards.length,
                    footerCardsCount: footerCards.length,
                    titleText: title ? title.innerText.trim() : null,
                };
            });

            // Dark Mode
            await page.evaluate(() => {
                document.body.classList.add('o_dark_mode');
                document.documentElement.setAttribute('data-bs-theme', 'dark');
            });
            await page.waitForTimeout(400);

            const darkScreenshot = path.join(ARTIFACT_DIR, `audit_${route.name}_dark.png`);
            await page.screenshot({ path: darkScreenshot, fullPage: true });

            console.log(`[PASS] ${route.name}: Cards=${metrics.cardsCount}, FooterCards=${metrics.footerCardsCount}, MaxWidth=${metrics.sheetMaxWidth}`);

            results.push({
                name: route.name,
                status: 'SUCCESS',
                metrics,
                lightScreenshot,
                darkScreenshot
            });
        }

        console.log(`\n======================================================`);
        console.log(`AUDIT EXECUTION SUMMARY REPORT`);
        console.log(`======================================================`);
        console.table(results.map(r => ({
            Route: r.name,
            Status: r.status,
            Cards: r.metrics ? r.metrics.cardsCount : 'N/A',
            SheetWidth: r.metrics ? r.metrics.sheetWidth : 'N/A',
            HeroWidth: r.metrics ? r.metrics.heroWidth : 'N/A',
            MaxWidth: r.metrics ? r.metrics.sheetMaxWidth : 'N/A'
        })));

        fs.writeFileSync(
            path.join(ARTIFACT_DIR, 'audit_summary_results.json'),
            JSON.stringify(results, null, 2)
        );

    } catch (err) {
        console.error(`Audit failed with exception:`, err);
    } finally {
        await browser.close();
    }
}

runAudit();
