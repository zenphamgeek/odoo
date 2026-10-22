const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    // Collect console logs and errors
    const logs = [];
    page.on('console', msg => logs.push(`[${msg.type()}] ${msg.text()}`));
    page.on('pageerror', err => logs.push(`[PAGE_ERROR] ${err.message}`));

    console.log("=== 1. Checking /web/login ===");
    await page.goto("http://localhost:28069/web/login");
    await page.fill('input[name="login"]', 'zeninall@gmail.com');
    await page.fill('input[name="password"]', 'Zen@123456');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    console.log("=== 2. Navigating to /insilos/dashboards?dashboard_id=3 ===");
    await page.goto("http://localhost:28069/insilos/dashboards?dashboard_id=3");
    await page.waitForTimeout(4000);

    // Inspect search panel and search bar
    const spInfo = await page.evaluate(() => {
        const sp = document.querySelector('.o_spreadsheet_dashboard_search_panel');
        const sections = document.querySelectorAll('.o_spreadsheet_dashboard_search_panel .o_search_panel_section');
        const searchview = document.querySelector('.o_sp_dashboard_search .o_searchview');
        const cpSearchview = document.querySelector('.o_cp_searchview');
        const input = document.querySelector('.o_sp_dashboard_search input');
        
        const getStyle = el => el ? {
            width: window.getComputedStyle(el).width,
            maxWidth: window.getComputedStyle(el).maxWidth,
            minWidth: window.getComputedStyle(el).minWidth,
            boxSizing: window.getComputedStyle(el).boxSizing,
            border: window.getComputedStyle(el).border,
            boxShadow: window.getComputedStyle(el).boxShadow,
            outline: window.getComputedStyle(el).outline,
            padding: window.getComputedStyle(el).padding,
            margin: window.getComputedStyle(el).margin,
            rect: el.getBoundingClientRect(),
        } : null;

        return {
            searchPanel: getStyle(sp),
            cpSearchview: getStyle(cpSearchview),
            searchview: getStyle(searchview),
            input: getStyle(input),
            sectionsCount: sections.length,
            spOuterHtml: sp ? sp.outerHTML.substring(0, 400) : null,
            cpSearchviewHtml: cpSearchview ? cpSearchview.outerHTML.substring(0, 500) : null,
        };
    });

    console.log("Search Panel & Search Bar Info:", JSON.stringify(spInfo, null, 2));

    await page.screenshot({ path: '/tmp/test_dashboard_local.png' });

    console.log("=== 3. Navigating to /insilos/contacts ===");
    logs.length = 0; // Clear logs
    const contactsResp = await page.goto("http://localhost:28069/insilos/contacts");
    await page.waitForTimeout(4000);

    const currentUrl = page.url();
    console.log("URL after /insilos/contacts:", currentUrl);
    console.log("Page title:", await page.title());

    const contactsDom = await page.evaluate(() => {
        return {
            hasClientAction: !!document.querySelector('.o_action_manager'),
            hasErrorDialog: !!document.querySelector('.o_error_dialog'),
            errorDialogText: document.querySelector('.o_error_dialog')?.innerText,
            breadcrumb: document.querySelector('.breadcrumb')?.innerText,
            hasListView: !!document.querySelector('.o_list_view'),
            hasKanbanView: !!document.querySelector('.o_kanban_view'),
            bodyClass: document.body.className,
        };
    });
    console.log("Contacts DOM info:", JSON.stringify(contactsDom, null, 2));
    console.log("Contacts Console logs:", logs);

    await page.screenshot({ path: '/tmp/test_contacts_local.png' });

    await browser.close();
})();
