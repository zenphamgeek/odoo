const { chromium } = require("playwright");
const path = require("path");

(async () => {
    console.log("Testing Copilot Click in both Form and Non-Form Views...");
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);

    const consoleMessages = [];
    page.on("console", msg => {
        consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    });
    page.on("pageerror", err => {
        consoleMessages.push(`[PAGE_ERROR] ${err.message}\n${err.stack}`);
    });

    // 1. Authenticate
    await page.goto("http://localhost:28069/web/login", { waitUntil: "domcontentloaded" });
    const authDb = process.env.ODOO_DB || "insilos20_dev";
    const authLogin = process.env.ODOO_LOGIN || "admin";
    const authPassword = process.env.ODOO_PASSWORD || "admin";
    await page.evaluate(async ({ db, login, password }) => {
        await fetch("/web/session/authenticate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: { db, login, password }
            })
        });
    }, { db: authDb, login: authLogin, password: authPassword });

    // 2. Test 1: Click from Non-Form View (WebClient root / kanban / list)
    console.log("Navigating to WebClient...");
    await page.goto("http://localhost:28069/odoo", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_navbar", { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log("Checking current view type...");
    const currentViewInfo = await page.evaluate(() => {
        const actionService = odoo.__WOWL_DEBUG__?.root?.env?.services?.action;
        return {
            controller: actionService?.currentController?.view?.type || "none",
            resModel: actionService?.currentController?.props?.resModel || "none"
        };
    });
    console.log("Current view info:", currentViewInfo);

    console.log("Clicking Insilos AI Copilot button from non-form view...");
    const copilotBtn = await page.$(".o_ai_systray_btn");
    if (!copilotBtn) {
        throw new Error("Copilot button .o_ai_systray_btn not found");
    }
    await copilotBtn.click();
    await page.waitForTimeout(4000);

    const chatWindowNonForm = await page.$(".o-mail-ChatWindow");
    console.log("Chat window opened from non-form view:", !!chatWindowNonForm);
    await page.screenshot({ path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/copilot_non_form_click.png" });

    // 3. Test 2: Navigate to a Form View and click Copilot
    console.log("Navigating to CRM Form View...");
    const leadId = await page.evaluate(async () => {
        const res = await fetch("/web/dataset/call_kw/crm.lead/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    model: "crm.lead",
                    method: "search",
                    args: [[]],
                    kwargs: { limit: 1 }
                }
            })
        });
        const data = await res.json();
        return data.result?.[0];
    });

    if (leadId) {
        console.log(`Navigating to CRM Lead #${leadId} Form...`);
        await page.goto(`http://localhost:28069/odoo/action-crm.crm_lead_all_leads/${leadId}`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_form_view", { timeout: 30000 });
        await page.waitForTimeout(3000);

        console.log("Clicking Insilos AI Copilot button from FORM view...");
        const copilotBtnForm = await page.$(".o_ai_systray_btn");
        await copilotBtnForm.click();
        await page.waitForTimeout(4000);

        const chatWindowForm = await page.$(".o-mail-ChatWindow");
        console.log("Chat window opened from FORM view:", !!chatWindowForm);
        await page.screenshot({ path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/copilot_form_click.png" });
    }

    console.log("\n--- All Console Messages Captured ---");
    consoleMessages.forEach(m => console.log(m));

    await browser.close();
    console.log("Test finished.");
})().catch(err => {
    console.error("Test failed:", err);
    process.exit(1);
});
