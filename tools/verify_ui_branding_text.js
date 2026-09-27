const { chromium } = require('playwright');

async function checkPage(page, appName, url) {
    console.log(`\nChecking [${appName}] at ${url}...`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);

    // Get visible text content
    const text = await page.evaluate(() => {
        return document.body.innerText;
    });

    const patterns = [
        /\bOdoo\b/g,
        /\bODOO\b/g,
        /\bodoo\b/g
    ];

    const leaks = [];
    for (const pat of patterns) {
        const matches = text.match(pat);
        if (matches) {
            // Find context lines
            const lines = text.split('\n');
            for (const line of lines) {
                if (pat.test(line)) {
                    leaks.push(line.trim());
                }
            }
        }
    }

    if (leaks.length > 0) {
        console.error(`  ❌ LEAKS in [${appName}]:`);
        for (const l of leaks) {
            console.error(`     "${l.substring(0, 100)}"`);
        }
        return leaks;
    } else {
        console.log(`  ✅ [${appName}] is completely clean of visual Odoo text!`);
        return [];
    }
}

async function main() {
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

    // Authenticate
    await page.request.post('http://localhost:28069/web/session/authenticate', {
        data: { jsonrpc: '2.0', params: { db: 'odoo20_dev', login: 'admin', password: 'admin' } }
    });

    const routesToCheck = [
        ['App Drawer', 'http://localhost:28069/insilos'],
        ['CRM', 'http://localhost:28069/insilos/crm'],
        ['Contacts', 'http://localhost:28069/insilos/contacts'],
        ['Discuss', 'http://localhost:28069/insilos/discuss'],
        ['Knowledge', 'http://localhost:28069/insilos/knowledge'],
        ['Documents', 'http://localhost:28069/insilos/documents'],
        ['Accounting', 'http://localhost:28069/insilos/accounting'],
        ['Settings', 'http://localhost:28069/insilos/settings'],
    ];

    let totalLeaks = 0;
    for (const [name, url] of routesToCheck) {
        const leaks = await checkPage(page, name, url);
        totalLeaks += leaks.length;
    }

    await browser.close();

    console.log(`\n===========================================`);
    console.log(`Visual Scan Finished. Total Leaks Found: ${totalLeaks}`);
    if (totalLeaks === 0) {
        console.log(`🎉 ALL CHECKED APPS ARE 100% BRANDED TO INSILOS!`);
    } else {
        console.log(`⚠️ Some leaks require attention.`);
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
