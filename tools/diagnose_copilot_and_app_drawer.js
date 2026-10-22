const { chromium } = require("playwright");

(async () => {
    console.log("Starting Copilot and App Drawer Diagnostic...");
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

    const networkEvents = [];
    page.on("requestfailed", req => {
        networkEvents.push(`[REQ_FAIL] ${req.url()} - ${req.failure()?.errorText}`);
    });
    page.on("response", res => {
        if (res.status() >= 400) {
            networkEvents.push(`[HTTP_${res.status()}] ${res.url()}`);
        }
    });

    console.log("Authenticating session...");
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

    await page.goto("http://localhost:28069/odoo", { waitUntil: "networkidle" });
    await page.waitForSelector(".o_navbar", { timeout: 30000 });
    console.log("✓ Logged in and .o_navbar ready");

    // 1. Check Insilos AI Copilot button
    const copilotBtn = await page.$(".o_ai_systray_btn");
    console.log("Copilot button found in DOM:", !!copilotBtn);
    if (copilotBtn) {
        console.log("Clicking Copilot button...");
        await copilotBtn.click();
        await page.waitForTimeout(3000);
    }

    console.log("\n--- Console Messages after Copilot Click ---");
    consoleMessages.forEach(m => console.log(m));

    console.log("\n--- Network Error Events ---");
    networkEvents.forEach(e => console.log(e));

    // Check if chat window or discuss opened
    const chatWindow = await page.$(".o-mail-ChatWindow");
    console.log("Chat window (.o-mail-ChatWindow) rendered:", !!chatWindow);

    const chatHub = await page.$(".o-mail-ChatHub");
    console.log("Chat hub (.o-mail-ChatHub) rendered:", !!chatHub);

    // 2. Check Apps Drawer (HomeMenu / App Drawer)
    console.log("\n--- Checking Apps Drawer / HomeMenu ---");
    const appDrawerBtn = await page.$(".o_navbar_apps_menu button, .o_menu_toggle");
    console.log("App drawer toggle button found:", !!appDrawerBtn);
    if (appDrawerBtn) {
        await appDrawerBtn.click();
        await page.waitForTimeout(1500);
        const homeMenu = await page.$(".o_home_menu");
        console.log(".o_home_menu visible after click:", !!homeMenu);
    }

    await browser.close();
    console.log("Diagnostic complete.");
})().catch(err => {
    console.error("Fatal diagnostic error:", err);
    process.exit(1);
});
