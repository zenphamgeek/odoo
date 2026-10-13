const { chromium } = require('playwright');

const HOOT_HOST = (process.env.HOOT_HOST || 'http://localhost:28069').replace(/\/+$/, '');
const HOOT_LOGIN = process.env.HOOT_LOGIN || 'admin';
const HOOT_PASSWORD = process.env.HOOT_PASSWORD || 'admin';

function validateTargetAndCredentials(host = HOOT_HOST, login = HOOT_LOGIN, password = HOOT_PASSWORD) {
    const isLocal = /^https?:\/\/(localhost|127\.0\.0\.1|::1)(:|\/|$)/i.test(host);
    if (!isLocal && (login === 'admin' && password === 'admin')) {
        throw new Error(`Refusing default admin/admin credentials against non-local host '${host}'; set HOOT_LOGIN and HOOT_PASSWORD explicitly.`);
    }
    return { host, login, password, isLocal };
}

const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+(?:\.[A-Za-z]{2,})?/gi;
const BASIC_AUTH = /(https?:\/\/[^\/\s:@]+:)[^\/\s@]+(@)/gi;
const BEARER = /(bearer\s+)[A-Za-z0-9._\-]+/gi;
const JWT = /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g;
const JWT_FALLBACK = /eyJ[A-Za-z0-9._\-]{10,}/g;
const QUERY_PARAM = /([?&](?:token|key|secret|password|passwd|pwd|session|sid)=)[^&\s]+/gi;
const SECRET_PAIR = /(password|passwd|pwd|secret|token|api[_-]?key|bearer|authorization)(\s*[:=]\s*)(?!\[REDACTED)[^\s,;]+/gi;
const HEX_HASH = /\b[A-Fa-f0-9]{32,}\b/g;

function safeRedact(value) {
    if (value === null || value === undefined) return '';
    try {
        let str = typeof value === 'string' ? value : String(value);
        return str
            .replace(BASIC_AUTH, '$1[REDACTED]$2')
            .replace(QUERY_PARAM, '$1[REDACTED]')
            .replace(BEARER, '$1[REDACTED]')
            .replace(JWT, '[REDACTED_JWT]')
            .replace(JWT_FALLBACK, '[REDACTED_JWT]')
            .replace(SECRET_PAIR, '$1$2[REDACTED_SECRET]')
            .replace(EMAIL, '[REDACTED_EMAIL]')
            .replace(HEX_HASH, '[REDACTED_HEX]')
            .replace(/\s+/g, ' ');
    } catch (_) {
        return '[REDACTED_EXCEPTION]';
    }
}

function redactContext(s) {
    return safeRedact(s);
}

function assertRedactionWorks() {
    const probes = [
        'Bearer abc123DEF456',
        'https://admin:hunter2@erp.local/web',
        'https://x/web?session=QWERTYtoken123',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
    ];
    for (const p of probes) {
        const r = safeRedact(p);
        if (/hunter2|QWERTYtoken123|abc123DEF456|eyJhbGciOi/.test(r)) {
            throw new Error(`FATAL: redaction self-test failed; refusing to run sweep (leak: ${p.slice(0, 8)}...)`);
        }
    }
}

function scanPreferencesModalText(modalText) {
    const prefLeaks = [];
    const brandPat = /\bodoo\b/gi;
    let m;
    while ((m = brandPat.exec(modalText)) !== null) {
        let start = Math.max(0, m.index - 12);
        let end = Math.min(modalText.length, m.index + m[0].length + 12);
        while (start > 0 && !/\s/.test(modalText[start - 1])) start--;
        while (end < modalText.length && !/\s/.test(modalText[end])) end++;
        prefLeaks.push(`User Preferences brand token "${m[0]}" at offset ${m.index} (ctx: "...${redactContext(modalText.slice(start, end))}...")`);
    }
    return prefLeaks;
}

async function checkPage(page, appName, url) {
    console.log(`Checking [${appName}] at ${url}...`);
    try {
        const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(1000);

        const status = response ? response.status() : 0;
        if (status >= 400) {
            console.log(`  ⚠️ HTTP status ${status} for ${url}`);
        }

        // Get visible text content
        const text = await page.evaluate(() => document.body.innerText || '');

        const patterns = [
            /\bOdoo\b/g,
            /\bODOO\b/g,
            /\bodoo\b/g
        ];

        // Allowed technical / test phrases if any (none expected on UI)
        const leaks = [];
        const seen = new Set();
        for (const pat of patterns) {
            const matches = text.match(pat);
            if (matches) {
                const lines = text.split('\n');
                for (const line of lines) {
                    if (pat.test(line)) {
                        const raw = line.trim();
                        // Deduplicate on raw unredacted string to prevent collapse of distinct secrets
                        if (!seen.has(raw)) {
                            seen.add(raw);
                            leaks.push(redactContext(raw));
                        }
                    }
                }
            }
        }

        // Check document title
        const pageTitle = await page.title();
        for (const pat of patterns) {
            if (pat.test(pageTitle) && !/insilos/i.test(pageTitle)) {
                const rawTitle = `Document Title: "${pageTitle}"`;
                if (!seen.has(rawTitle)) {
                    seen.add(rawTitle);
                    leaks.push(rawTitle);
                }
            }
        }

        // Also check if any image src or alt has legacy odoo branding
        const imgLeaks = await page.evaluate(() => {
            const badImgs = [];
            const imgs = document.querySelectorAll('img');
            for (const img of imgs) {
                const src = img.getAttribute('src') || '';
                const alt = img.getAttribute('alt') || '';
                const isBadSrc = (!src.startsWith('data:') && /odoo/i.test(src) && !/odoo_ui_icons|odoobot/i.test(src) && !src.includes('insilos'));
                const isBadAlt = (alt.toLowerCase().includes('odoo') && !alt.toLowerCase().includes('insilos'));
                if (isBadSrc || isBadAlt) {
                    badImgs.push(`img src="${src}" alt="${alt}"`);
                }
            }
            return badImgs;
        });

        if (leaks.length > 0 || imgLeaks.length > 0) {
            console.error(`  ❌ LEAKS in [${appName}]:`);
            for (const l of leaks) {
                console.error(`     Text: "${l.substring(0, 120)}"`);
            }
            for (const img of imgLeaks) {
                console.error(`     Image: ${img}`);
            }
            return { appName, url, leaks, imgLeaks, error: null };
        } else {
            console.log(`  ✅ [${appName}] is completely clean!`);
            return null;
        }
    } catch (err) {
        const safe = redactContext(err?.message ?? String(err));
        console.error(`  ⚠️ Exception checking [${appName}]:`, safe);
        return { appName, url, leaks: [], imgLeaks: [], error: safe };
    }
}

async function main() {
    assertRedactionWorks();
    validateTargetAndCredentials(HOOT_HOST, HOOT_LOGIN, HOOT_PASSWORD);

    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    let totalLeaks = 0;
    const leakDetails = [];

    // 1. Check unauthenticated public pages first in parallel
    console.log('=== CHECKING UNAUTHENTICATED PUBLIC PAGES (Parallel) ===');
    const publicRoutes = [
        ['Public Login', `${HOOT_HOST}/web/login`],
        ['Public Reset Password', `${HOOT_HOST}/web/reset_password`],
        ['Public Home', `${HOOT_HOST}/`],
        ['Public Contact Us', `${HOOT_HOST}/contactus`],
        ['Public Jobs / Careers', `${HOOT_HOST}/jobs`],
    ];

    const publicContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    for (const [name, url] of publicRoutes) {
        const p = await publicContext.newPage();
        const res = await checkPage(p, name, url);
        if (res) {
            leakDetails.push(res);
        }
        await p.close().catch(() => {});
    }
    await publicContext.close().catch(() => {});

    // 2. Authenticate as admin and extract storageState
    console.log('\n=== AUTHENTICATING AS ADMIN ===');
    const authContext = await browser.newContext();
    const authPage = await authContext.newPage();
    await authPage.request.post(`${HOOT_HOST}/web/session/authenticate`, {
        data: { jsonrpc: '2.0', params: { db: process.env.HOOT_DB || 'insilos20_dev', login: HOOT_LOGIN, password: HOOT_PASSWORD } }
    });
    const storageState = await authContext.storageState();
    await authContext.close().catch(() => {});

    // 2.1 Check User Preferences Modal Dialog (Regression Guard)
    console.log('\n=== CHECKING USER PREFERENCES MODAL DIALOG ===');
    const prefCtx = await browser.newContext({ storageState, viewport: { width: 1440, height: 900 } });
    const prefPage = await prefCtx.newPage();
    let prefCheckCompleted = false;
    try {
        await prefPage.goto(`${HOOT_HOST}/insilos`, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await prefPage.waitForSelector('.o_main_navbar, .o_navbar', { timeout: 15000 });
        const userMenuBtn = prefPage.locator('.o_user_menu button, button.o_user_menu, .o_user_menu .dropdown-toggle, button[aria-label="User menu"], .o_menu_systray .o_user_menu').first();
        await userMenuBtn.waitFor({ state: 'visible', timeout: 15000 });
        await userMenuBtn.click();
        const openMenu = prefPage.locator('.dropdown-menu.show, .o_user_menu .dropdown-menu').first();
        await openMenu.waitFor({ state: 'visible', timeout: 8000 }).catch(() => {});

        const prefOption = prefPage.locator('.dropdown-item:has-text("Preferences"), .dropdown-item[data-menu="settings"], [data-menu="settings"], .dropdown-item:has-text("Tùy chọn")').first();
        const prefAppeared = await prefOption
            .waitFor({ state: 'visible', timeout: 2500 })
            .then(() => true)
            .catch(() => false);
        if (!prefAppeared) {
            // First click likely absorbed during hydration; check if dropdown is not open before clicking to prevent toggle-close
            const isMenuOpen = await openMenu.isVisible().catch(() => false);
            if (!isMenuOpen) {
                await userMenuBtn.click().catch(() => {});
            }
            await openMenu.waitFor({ state: 'visible', timeout: 8000 }).catch(() => {});
            await prefOption.waitFor({ state: 'visible', timeout: 15000 });
        }
        await prefOption.click();
        await prefPage.waitForSelector('.modal-dialog, .modal.show', { timeout: 20000 });
        const modal = prefPage.locator('.modal-dialog, .modal.show').first();
        await modal.waitFor({ state: 'visible', timeout: 15000 });
        await modal.locator('.modal-body, .modal-content').first().waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
        const modalText = await modal.innerText();
        const prefLeaks = scanPreferencesModalText(modalText);
        if (prefLeaks.length > 0) {
            leakDetails.push({ appName: 'User Preferences Modal', url: 'preferences_dialog', leaks: prefLeaks, imgLeaks: [] });
            console.log(`  ❌ Leaks detected in User Preferences modal: ${prefLeaks.length}`);
        } else {
            console.log('  ✅ User Preferences Modal: 100% Insilos Branded (0 leaks)');
        }
        prefCheckCompleted = true;
    } catch (e) {
        // A security control that cannot assert must fail loudly, not pass silently.
        console.error('  ❌ User Preferences modal check FAILED to execute:', safeRedact(e?.message ?? String(e)));
    } finally {
        await prefPage.close().catch(() => {});
        await prefCtx.close().catch(() => {});
    }
    if (!prefCheckCompleted) {
        leakDetails.push({
            appName: 'User Preferences Modal',
            url: 'preferences_dialog',
            leaks: ['AUDIT INCONCLUSIVE: modal check did not complete; treat as failing until re-run'],
            imgLeaks: [],
        });
    }

    // 3. Check authenticated apps and menus with parallel worker pool
    console.log('\n=== CHECKING AUTHENTICATED CORE APPS (Parallel Concurrency: 3) ===');
    const authRoutes = [
        ['App Drawer', `${HOOT_HOST}/insilos`],
        ['Apps Store', `${HOOT_HOST}/insilos/apps`],
        ['Settings', `${HOOT_HOST}/insilos/settings`],
        ['CRM', `${HOOT_HOST}/insilos/crm`],
        ['Sales', `${HOOT_HOST}/insilos/sales`],
        ['Invoicing / Accounting', `${HOOT_HOST}/insilos/accounting`],
        ['Inventory', `${HOOT_HOST}/insilos/inventory`],
        ['Manufacturing', `${HOOT_HOST}/insilos/mrp`],
        ['Purchase', `${HOOT_HOST}/insilos/purchase`],
        ['Project', `${HOOT_HOST}/insilos/project`],
        ['Helpdesk', `${HOOT_HOST}/insilos/helpdesk`],
        ['Knowledge', `${HOOT_HOST}/insilos/knowledge`],
        ['Documents', `${HOOT_HOST}/insilos/documents`],
        ['Contacts', `${HOOT_HOST}/insilos/contacts`],
        ['Discuss', `${HOOT_HOST}/insilos/discuss`],
        ['Calendar', `${HOOT_HOST}/insilos/calendar`],
        ['Employees', `${HOOT_HOST}/insilos/employees`],
        ['Time Off', `${HOOT_HOST}/insilos/holidays`],
        ['Recruitment', `${HOOT_HOST}/insilos/recruitment`],
        ['Payroll', `${HOOT_HOST}/insilos/payroll`],
        ['Sign', `${HOOT_HOST}/insilos/sign`],
        ['Point of Sale', `${HOOT_HOST}/insilos/point_of_sale`],
        ['Subscriptions', `${HOOT_HOST}/insilos/sale_subscription`],
        ['Timesheets', `${HOOT_HOST}/insilos/timesheet_grid`],
        ['Field Service', `${HOOT_HOST}/insilos/industry_fsm`],
        ['Planning', `${HOOT_HOST}/insilos/planning`],
        ['Quality', `${HOOT_HOST}/insilos/quality_control`],
        ['Maintenance', `${HOOT_HOST}/insilos/maintenance`],
        ['Unified Operations Hub', `${HOOT_HOST}/insilos/unified-operations`],
        ['Logistics IDP Onboarding', `${HOOT_HOST}/insilos/logistics-onboarding`],
        ['Chemical Trade Compliance Onboarding', `${HOOT_HOST}/insilos/chemical-onboarding`],
        ['HS Tariff Sync Onboarding', `${HOOT_HOST}/insilos/hs-onboarding`],
        ['HSE Safety Compliance Onboarding', `${HOOT_HOST}/insilos/hse-onboarding`],
        ['ESG Carbon Bridge Onboarding', `${HOOT_HOST}/insilos/esg-onboarding`],
        ['PubSub Event Bridge Onboarding', `${HOOT_HOST}/insilos/pubsub-onboarding`],
        ['Logistics Overview Hub', `${HOOT_HOST}/insilos/logistics-overview`],
    ];

    const CONCURRENCY = 3;
    const queue = [...authRoutes];

    async function worker() {
        const ctx = await browser.newContext({ storageState, viewport: { width: 1440, height: 900 } });
        const p = await ctx.newPage();
        while (queue.length > 0) {
            const item = queue.shift();
            if (!item) break;
            const [name, url] = item;
            const res = await checkPage(p, name, url);
            if (res) {
                leakDetails.push(res);
            }
        }
        await ctx.close().catch(() => {});
    }

    await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

    // 4. Retry any timed-out routes sequentially to rule out server concurrency contention
    const isTimeout = (d) => (d.error && /timeout|page\.goto|target page/i.test(d.error)) || d.leaks.some(l => /timeout|page\.goto|target page/i.test(l));
    const timedOutRoutes = leakDetails.filter(isTimeout);
    if (timedOutRoutes.length > 0) {
        console.log(`\nRetrying ${timedOutRoutes.length} timed-out routes sequentially to eliminate parallel contention...`);
        let retryBrowser = browser;
        if (!browser.isConnected()) {
            retryBrowser = await chromium.launch({
                headless: true,
                executablePath: '/usr/bin/google-chrome',
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
        }
        const retryContext = await retryBrowser.newContext({ storageState, viewport: { width: 1440, height: 900 } });
        const retryPage = await retryContext.newPage();
        for (const item of timedOutRoutes) {
            console.log(`Retrying [${item.appName}]...`);
            const retryRes = await checkPage(retryPage, item.appName, item.url);
            const idx = leakDetails.indexOf(item);
            if (!retryRes) {
                leakDetails.splice(idx, 1);
            } else {
                leakDetails[idx] = retryRes;
            }
        }
        await retryContext.close().catch(() => {});
        if (retryBrowser !== browser) {
            await retryBrowser.close().catch(() => {});
        }
    }

    if (browser.isConnected()) {
        await browser.close().catch(() => {});
    }

    const realLeaks = leakDetails.filter(d => (d.leaks && d.leaks.length > 0) || (d.imgLeaks && d.imgLeaks.length > 0));
    const infraErrors = leakDetails.filter(d => d.error);
    totalLeaks = realLeaks.reduce((acc, cur) => acc + cur.leaks.length + cur.imgLeaks.length, 0);

    console.log(`\n===========================================`);
    console.log(`Comprehensive Scan Finished. Total Leaks: ${totalLeaks} | Infrastructure Errors: ${infraErrors.length}`);
    if (totalLeaks === 0 && infraErrors.length === 0) {
        console.log(`🎉 ALL CHECKED APPS AND PAGES ARE 100% BRANDED TO INSILOS!`);
        process.exit(0);
    } else {
        if (totalLeaks > 0) console.log(`⚠️ Leaks found in ${realLeaks.length} page(s).`);
        if (infraErrors.length > 0) console.log(`⚠️ Scan failures/timeouts in ${infraErrors.length} page(s).`);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(err => {
        console.error('Fatal error:', err);
        process.exit(1);
    });
}

module.exports = {
    EMAIL,
    BASIC_AUTH,
    BEARER,
    JWT,
    QUERY_PARAM,
    SECRET_PAIR,
    HEX_HASH,
    HOOT_HOST,
    HOOT_LOGIN,
    HOOT_PASSWORD,
    validateTargetAndCredentials,
    safeRedact,
    redactContext,
    assertRedactionWorks,
    scanPreferencesModalText,
    checkPage,
    main,
};

