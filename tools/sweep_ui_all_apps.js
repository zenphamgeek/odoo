const { chromium } = require('playwright');

async function checkPage(page, appName, url) {
    console.log(`Checking [${appName}] at ${url}...`);
    try {
        const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);

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
        for (const pat of patterns) {
            const matches = text.match(pat);
            if (matches) {
                const lines = text.split('\n');
                for (const line of lines) {
                    if (pat.test(line)) {
                        const trimmed = line.trim();
                        // Avoid duplicates
                        if (!leaks.includes(trimmed)) {
                            leaks.push(trimmed);
                        }
                    }
                }
            }
        }

        // Check document title
        const pageTitle = await page.title();
        for (const pat of patterns) {
            if (pat.test(pageTitle) && !/insilos/i.test(pageTitle)) {
                leaks.push(`Document Title: "${pageTitle}"`);
            }
        }

        // Also check if any image src or alt has legacy odoo branding
        const imgLeaks = await page.evaluate(() => {
            const badImgs = [];
            const imgs = document.querySelectorAll('img');
            for (const img of imgs) {
                const src = img.getAttribute('src') || '';
                const alt = img.getAttribute('alt') || '';
                const isBadSrc = (/odoo/i.test(src) && !/odoo_ui_icons|odoobot/i.test(src) && !src.includes('insilos'));
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
            return { appName, url, leaks, imgLeaks };
        } else {
            console.log(`  ✅ [${appName}] is completely clean!`);
            return null;
        }
    } catch (err) {
        console.error(`  ⚠️ Exception checking [${appName}]:`, err.message);
        return { appName, url, leaks: [err.message], imgLeaks: [] };
    }
}

async function main() {
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

    // 1. Check unauthenticated public pages first
    console.log('=== CHECKING UNAUTHENTICATED PUBLIC PAGES ===');
    const publicRoutes = [
        ['Public Login', 'http://localhost:28069/web/login'],
        ['Public Reset Password', 'http://localhost:28069/web/reset_password'],
        ['Public Home', 'http://localhost:28069/'],
        ['Public Contact Us', 'http://localhost:28069/contactus'],
        ['Public Jobs / Careers', 'http://localhost:28069/jobs'],
    ];

    let totalLeaks = 0;
    const leakDetails = [];

    for (const [name, url] of publicRoutes) {
        const res = await checkPage(page, name, url);
        if (res) {
            totalLeaks += (res.leaks.length + res.imgLeaks.length);
            leakDetails.push(res);
        }
    }

    // 2. Authenticate as admin
    console.log('\n=== AUTHENTICATING AS ADMIN ===');
    await page.request.post('http://localhost:28069/web/session/authenticate', {
        data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });

    // 3. Check authenticated apps and menus
    console.log('\n=== CHECKING AUTHENTICATED CORE APPS ===');
    const authRoutes = [
        ['App Drawer', 'http://localhost:28069/insilos'],
        ['Apps Store', 'http://localhost:28069/insilos/apps'],
        ['Settings', 'http://localhost:28069/insilos/settings'],
        ['CRM', 'http://localhost:28069/insilos/crm'],
        ['Sales', 'http://localhost:28069/insilos/sales'],
        ['Invoicing / Accounting', 'http://localhost:28069/insilos/accounting'],
        ['Inventory', 'http://localhost:28069/insilos/inventory'],
        ['Manufacturing', 'http://localhost:28069/insilos/mrp'],
        ['Purchase', 'http://localhost:28069/insilos/purchase'],
        ['Project', 'http://localhost:28069/insilos/project'],
        ['Helpdesk', 'http://localhost:28069/insilos/helpdesk'],
        ['Knowledge', 'http://localhost:28069/insilos/knowledge'],
        ['Documents', 'http://localhost:28069/insilos/documents'],
        ['Contacts', 'http://localhost:28069/insilos/contacts'],
        ['Discuss', 'http://localhost:28069/insilos/discuss'],
        ['Calendar', 'http://localhost:28069/insilos/calendar'],
        ['Employees', 'http://localhost:28069/insilos/employees'],
        ['Time Off', 'http://localhost:28069/insilos/holidays'],
        ['Recruitment', 'http://localhost:28069/insilos/recruitment'],
        ['Payroll', 'http://localhost:28069/insilos/payroll'],
        ['Sign', 'http://localhost:28069/insilos/sign'],
        ['Point of Sale', 'http://localhost:28069/insilos/point_of_sale'],
        ['Subscriptions', 'http://localhost:28069/insilos/sale_subscription'],
        ['Timesheets', 'http://localhost:28069/insilos/timesheet_grid'],
        ['Field Service', 'http://localhost:28069/insilos/industry_fsm'],
        ['Planning', 'http://localhost:28069/insilos/planning'],
        ['Quality', 'http://localhost:28069/insilos/quality_control'],
        ['Maintenance', 'http://localhost:28069/insilos/maintenance'],
    ];

    for (const [name, url] of authRoutes) {
        const res = await checkPage(page, name, url);
        if (res) {
            totalLeaks += (res.leaks.length + res.imgLeaks.length);
            leakDetails.push(res);
        }
    }

    await browser.close();

    console.log(`\n===========================================`);
    console.log(`Comprehensive Scan Finished. Total Leaks: ${totalLeaks}`);
    if (totalLeaks === 0) {
        console.log(`🎉 ALL CHECKED APPS AND PAGES ARE 100% BRANDED TO INSILOS!`);
        process.exit(0);
    } else {
        console.log(`⚠️ Leaks found in ${leakDetails.length} page(s).`);
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
