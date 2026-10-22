const { chromium } = require('playwright');

async function inspectPreferences() {
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();

    console.log('1. Authenticating...');
    const authRes = await page.request.post('http://localhost:28069/web/session/authenticate', {
        data: {
            jsonrpc: '2.0',
            params: {
                db: process.env.HOOT_DB || 'insilos20_dev',
                login: process.env.HOOT_LOGIN || 'admin',
                password: process.env.HOOT_PASSWORD || 'admin'
            }
        }
    });
    console.log('Auth response status:', authRes.status());

    console.log('2. Navigating to /insilos...');
    await page.goto('http://localhost:28069/insilos', { waitUntil: 'networkidle', timeout: 30000 });

    console.log('3. Opening user menu...');
    const userMenuBtn = page.locator('.o_user_menu button, button.o_user_menu, .o_user_menu .dropdown-toggle, button[aria-label="User menu"]').first();
    await userMenuBtn.waitFor({ state: 'visible', timeout: 10000 });
    await userMenuBtn.click();
    await page.waitForTimeout(500);

    console.log('4. Clicking Preferences item...');
    const prefOption = page.locator('.dropdown-item:has-text("Preferences"), .dropdown-item[data-menu="settings"], [data-menu="settings"]').first();
    await prefOption.waitFor({ state: 'visible', timeout: 10000 });
    await prefOption.click();

    console.log('5. Waiting for modal...');
    await page.waitForSelector('.modal-dialog, .modal.show', { timeout: 15000 });
    await page.waitForTimeout(1500);

    const modal = page.locator('.modal-dialog, .modal.show').first();

    // Check all tabs in the modal
    const tabs = await modal.locator('.nav-link').all();
    console.log(`Found ${tabs.length} tabs in preferences modal.`);

    let allText = '';
    let allHtml = '';

    for (let i = 0; i < tabs.length; i++) {
        const tab = tabs[i];
        const tabName = (await tab.innerText()).trim();
        console.log(`--- Inspecting Tab ${i}: ${tabName} ---`);
        await tab.click();
        await page.waitForTimeout(600);

        const tabText = await modal.innerText();
        const tabHtml = await modal.innerHTML();
        allText += `\n=== TAB: ${tabName} ===\n` + tabText;
        allHtml += `\n<!-- TAB: ${tabName} -->\n` + tabHtml;

        // Take a screenshot of each tab
        await page.screenshot({ path: `pref_tab_${i}_${tabName.replace(/\s+/g, '_')}.png` });
    }

    // Also inspect all form fields, options, labels, tooltips, attributes
    const elementsAnalysis = await modal.evaluate((modalEl) => {
        const results = [];
        const allElements = modalEl.querySelectorAll('*');
        for (const el of allElements) {
            const tag = el.tagName.toLowerCase();
            const text = el.innerText || '';
            const title = el.getAttribute('title') || '';
            const placeholder = el.getAttribute('placeholder') || '';
            const tooltip = el.getAttribute('data-tooltip') || '';
            const ariaLabel = el.getAttribute('aria-label') || '';
            const value = el.value || '';
            const options = el.tagName === 'SELECT' ? Array.from(el.options).map(o => o.text).join(' | ') : '';

            const combined = `${text} ${title} ${placeholder} ${tooltip} ${ariaLabel} ${value} ${options}`;
            if (/odoo/i.test(combined)) {
                results.push({
                    tag,
                    id: el.id,
                    className: el.className,
                    text: text.slice(0, 100),
                    title,
                    placeholder,
                    tooltip,
                    ariaLabel,
                    value,
                    options,
                    outerHTML: el.outerHTML.slice(0, 200)
                });
            }
        }
        return results;
    });

    console.log(`\n=== DEEP OD00 SCAN RESULTS ===`);
    console.log(`Matching elements with "odoo": ${elementsAnalysis.length}`);
    for (const item of elementsAnalysis) {
        console.log(JSON.stringify(item, null, 2));
    }

    // Check entire modal text
    const textMatches = allText.match(/\bodoo\b/gi) || [];
    console.log(`Regex word matches for \\bodoo\\b in all tabs text: ${textMatches.length}`);
    if (textMatches.length > 0) {
        console.log('Matches found in text:', textMatches);
        const lines = allText.split('\n');
        for (const line of lines) {
            if (/odoo/i.test(line)) {
                console.log('Line:', line.trim());
            }
        }
    }

    // Check full HTML for odoo
    const htmlMatches = allHtml.match(/odoo/gi) || [];
    console.log(`Total occurrences of "odoo" in all tabs HTML: ${htmlMatches.length}`);

    await browser.close();
}

inspectPreferences().catch(err => {
    console.error('Inspection failed:', err);
    process.exit(1);
});
