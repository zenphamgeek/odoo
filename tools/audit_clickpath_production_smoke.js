#!/usr/bin/env node
/**
 * tools/audit_clickpath_production_smoke.js
 * Insilos Enterprise Real-Session Click-Path & Runtime Smoke Auditor.
 *
 * Simulates real user traversal through high-risk enterprise screens:
 *   1. WebClient Home Menu & App Launcher
 *   2. General Settings View (res.config.settings)
 *   3. Executive Control Tower Dashboard (insilos.control.tower)
 *   4. Core Business List Views (Sales, Invoicing, Contacts)
 *
 * Verifies:
 *   - Exactly 0 Uncaught Promise Errors
 *   - Exactly 0 TypeErrors
 *   - Exactly 0 JSON-RPC Server Exceptions
 *
 * Usage:
 *   node tools/audit_clickpath_production_smoke.js --url https://innoria.com --db innoria_prod
 *   node tools/audit_clickpath_production_smoke.js --url http://localhost:28069 --db odoo20_dev
 */

const { chromium } = require('playwright');

const args = process.argv.slice(2);
function getArg(flag, def) {
    const idx = args.indexOf(flag);
    return idx !== -1 && args[idx + 1] ? args[idx + 1] : def;
}

const TARGET_URL = getArg('--url', process.env.TARGET_URL || 'https://innoria.com');
const DB_NAME = getArg('--db', process.env.DB_NAME || 'innoria_prod');
const LOGIN = getArg('--login', process.env.ADMIN_LOGIN || 'admin');
const PASSWORD = getArg('--password', process.env.ADMIN_PASSWORD || 'admin');

async function runSmokeAudit() {
    console.log('=' .repeat(78));
    console.log(`[*] STARTING REAL-SESSION CLICK-PATH SMOKE AUDIT`);
    console.log(`Target URL: ${TARGET_URL} | Database: ${DB_NAME}`);
    console.log('='.repeat(78));

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });

    const capturedErrors = [];
    const rpcErrors = [];

    // Authenticate
    console.log(`\n[*] 1. Authenticating as '${LOGIN}' on ${DB_NAME}...`);
    const authPage = await context.newPage();

    let authSuccess = false;
    try {
        const authRes = await authPage.request.post(`${TARGET_URL}/web/session/authenticate`, {
            data: {
                jsonrpc: '2.0',
                params: { db: DB_NAME, login: LOGIN, password: PASSWORD }
            },
            timeout: 15000
        });
        const authData = await authRes.json();
        if (authData.result && authData.result.uid) {
            console.log(`[✓] Authenticated successfully! UID: ${authData.result.uid}, User: ${authData.result.name}`);
            authSuccess = true;
        } else {
            console.log(`[!] Auth response did not return UID:`, JSON.stringify(authData.error || authData));
        }
    } catch (e) {
        console.log(`[!] Direct JSON-RPC auth failed (${e.message}), attempting web login form...`);
    }

    if (!authSuccess) {
        try {
            await authPage.goto(`${TARGET_URL}/web/login`, { waitUntil: 'networkidle', timeout: 20000 });
            await authPage.fill('input[name="login"]', LOGIN);
            await authPage.fill('input[name="password"]', PASSWORD);
            await authPage.click('button[type="submit"]');
            await authPage.waitForLoadState('networkidle', { timeout: 20000 });
            console.log(`[✓] Web login form submitted.`);
        } catch (e) {
            console.log(`[!] Form login error: ${e.message}`);
        }
    }

    const testPage = await context.newPage();

    // Attach listeners for unhandled runtime exceptions
    testPage.on('pageerror', (err) => {
        const msg = `[PAGE_ERROR] ${err.message}`;
        console.error(`  ${msg}`);
        capturedErrors.push(msg);
    });

    testPage.on('console', (msg) => {
        if (msg.type() === 'error') {
            const txt = msg.text();
            // Filter non-fatal 404 or benign telemetry/network asset failures
            if (!txt.includes('favicon.ico') && !txt.includes('Failed to load resource') && !txt.includes('status of 404')) {
                console.error(`  [CONSOLE_ERROR] ${txt.slice(0, 160)}`);
                capturedErrors.push(txt);
            }
        }
    });

    testPage.on('response', async (res) => {
        const url = res.url();
        if (url.includes('/web/dataset/call_kw') || url.includes('/web/dataset/call_button')) {
            try {
                const ct = res.headers()['content-type'] || '';
                if (ct.includes('application/json')) {
                    const json = await res.json();
                    if (json.error) {
                        const debugInfo = json.error.data?.debug || json.error.data?.message || json.error.message || JSON.stringify(json.error);
                        const errMsg = `[RPC_ERROR] ${url}: ${json.error.message}\n--- TRACEBACK ---\n${debugInfo}\n----------------`;
                        console.error(`  ${errMsg}`);
                        rpcErrors.push(errMsg);
                    }
                }
            } catch (_) {}
        }
    });

    const steps = [
        {
            name: 'WebClient Home Menu & ShellBar',
            url: `${TARGET_URL}/web`,
            selector: '.o_web_client',
            waitMs: 3000
        },
        {
            name: 'General Settings Form View (Monster Field Check)',
            url: `${TARGET_URL}/insilos/action-base_setup.action_general_configuration`,
            selector: '.o_base_settings_view, .o_form_view, .o_settings_container',
            waitMs: 10000
        },
        {
            name: 'Executive Control Tower Dashboard (KPI & Sparklines Check)',
            url: `${TARGET_URL}/insilos/action-insilos_sap_fiori.action_insilos_executive_control_tower`,
            selector: '.o_executive_control_tower, .o_control_tower_grid, .o_fiori_ovp_grid',
            waitMs: 5000
        },
        {
            name: 'Sales Quotations List View',
            url: `${TARGET_URL}/insilos/action-sale.action_quotations_with_onboarding`,
            selector: '.o_list_view, .o_content',
            waitMs: 4000
        },
        {
            name: 'Customer Invoices List View',
            url: `${TARGET_URL}/insilos/action-account.action_move_out_invoice_type`,
            selector: '.o_list_view, .o_content',
            waitMs: 4000
        }
    ];

    console.log('\n--- 2. EXECUTING LIVE CLICK-PATH TRAVERSAL ---');
    let passedSteps = 0;

    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        console.log(`\n[STEP ${i + 1}/${steps.length}] Navigating to: ${step.name}`);
        console.log(`  URL: ${step.url}`);
        const tStart = Date.now();

        try {
            await testPage.goto(step.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
            try {
                await testPage.waitForLoadState('load', { timeout: 10000 });
            } catch (_) {}
            await testPage.waitForTimeout(step.waitMs);

            // Wait for key element
            const el = await testPage.waitForSelector(step.selector, { timeout: 15000 }).catch(() => null);
            const duration = ((Date.now() - tStart) / 1000).toFixed(2);

            if (el) {
                console.log(`  [✓] Verified view rendered successfully (${duration}s)`);
                passedSteps++;
            } else {
                console.log(`  [✗] View failed to render expected selector '${step.selector}' (${duration}s)`);
                capturedErrors.push(`Selector '${step.selector}' not rendered on ${step.name}`);
            }
        } catch (e) {
            console.error(`  [✗] Navigation failed: ${e.message}`);
            capturedErrors.push(`Navigation failed on ${step.name}: ${e.message}`);
        }
    }

    await browser.close();

    console.log('\n' + '='.repeat(78));
    console.log('SMOKE AUDIT SUMMARY:');
    console.log(`Steps Completed: ${passedSteps}/${steps.length}`);
    console.log(`Uncaught Page Errors: ${capturedErrors.length}`);
    console.log(`JSON-RPC Server Errors: ${rpcErrors.length}`);

    if (capturedErrors.length > 0 || rpcErrors.length > 0) {
        console.log('\n[!] SMOKE AUDIT FAILED WITH RUNTIME DEFECTS:');
        capturedErrors.forEach((e, idx) => console.log(`  Err ${idx + 1}: ${e}`));
        rpcErrors.forEach((e, idx) => console.log(`  RPC ${idx + 1}: ${e}`));
        console.log('='.repeat(78));
        process.exit(1);
    } else {
        console.log('\n[🎉] SMOKE AUDIT 100% PASS: Zero runtime exceptions detected on live session!');
        console.log('='.repeat(78));
        process.exit(0);
    }
}

runSmokeAudit().catch((err) => {
    console.error('Fatal Runner Error:', err);
    process.exit(1);
});
