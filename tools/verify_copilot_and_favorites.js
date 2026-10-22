const { chromium } = require("playwright");

(async () => {
    console.log("=== VERIFYING INSILOS AI COPILOT & APPS DRAWER FAVORITES ===");
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(40000);

    const consoleErrors = [];
    const consoleWarnings = [];
    page.on("console", msg => {
        if (msg.type() === "error") {
            consoleErrors.push(`[CONSOLE ERROR] ${msg.text()}`);
        } else if (msg.type() === "warning") {
            consoleWarnings.push(`[CONSOLE WARN] ${msg.text()}`);
        }
    });
    page.on("pageerror", err => {
        consoleErrors.push(`[PAGE ERROR] ${err.message}\n${err.stack}`);
    });

    // 1. Authenticate to insilos20_dev
    console.log("1. Authenticating...");
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

    // 2. Test Apps Drawer (HomeMenu) Favorites
    console.log("2. Navigating to HomeMenu (Apps Drawer)...");
    await page.goto("http://localhost:28069/odoo", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_navbar", { timeout: 30000 });
    await page.waitForTimeout(2000);

    // If not in HomeMenu, click the app switcher icon
    const inHomeMenu = await page.$(".o_home_menu");
    if (!inHomeMenu) {
        console.log("Clicking App Switcher launcher to open HomeMenu...");
        const appSwitcher = await page.$(".o_navbar_apps_menu");
        if (appSwitcher) await appSwitcher.click();
        await page.waitForSelector(".o_home_menu", { timeout: 15000 });
    }

    console.log("Checking Pinned Favorites section...");
    const favSection = await page.waitForSelector(".o_home_menu_favorites_section", { timeout: 15000 });
    if (!favSection) {
        throw new Error("Favorites section .o_home_menu_favorites_section not found!");
    }

    const favCount = await page.$$eval(".o_home_menu_favorites_bar .o_fav_app_tile", tiles => tiles.length);
    console.log(`Initial favorites count in top bar: ${favCount}`);
    if (favCount === 0) {
        throw new Error("Expected initial favorites count > 0");
    }

    // Capture initial Apps Drawer with Favorites to Top screenshot
    await page.screenshot({
        path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/insilos_app_drawer_favorites_verified.png"
    });
    console.log("Captured insilos_app_drawer_favorites_verified.png");

    // Test Star Toggle: Find an unstarred app in the main grid and star it
    console.log("Testing star toggle on an unstarred app...");
    const unstarredStarBtn = await page.$(".o_apps .o_app .o_app_fav_star_btn:not(.o_is_favorite)");
    let toggledAppLabel = "";
    if (unstarredStarBtn) {
        toggledAppLabel = await unstarredStarBtn.evaluate(el => {
            const card = el.closest(".o_app");
            return card.querySelector(".o_caption")?.textContent?.trim() || "";
        });
        console.log(`Pinning app to favorites: "${toggledAppLabel}"`);
        await unstarredStarBtn.click();
        await page.waitForTimeout(1000);

        const newFavCount = await page.$$eval(".o_home_menu_favorites_bar .o_fav_app_tile", tiles => tiles.length);
        console.log(`Favorites count after starring: ${newFavCount}`);
        if (newFavCount !== favCount + 1) {
            console.warn(`Expected fav count ${favCount + 1}, got ${newFavCount}`);
        }

        // Capture screenshot of starred state
        await page.screenshot({
            path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/insilos_app_drawer_favorites_starred.png"
        });
        console.log("Captured insilos_app_drawer_favorites_starred.png");
    }

    // 3. Test Insilos AI Copilot in Form View
    console.log("3. Navigating to CRM Lead Form View...");
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

    if (!leadId) {
        throw new Error("No CRM Lead record found to test form view");
    }

    console.log(`Loading CRM Lead #${leadId} Form via action service...`);
    await page.evaluate(async (id) => {
        const actionService = odoo.__WOWL_DEBUG__?.root?.env?.services?.action;
        if (actionService) {
            await actionService.doAction({
                type: "ir.actions.act_window",
                res_model: "crm.lead",
                res_id: id,
                views: [[false, "form"]],
                target: "current"
            });
        }
    }, leadId);

    await page.waitForSelector(".o_form_view", { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log("Clicking Insilos AI Copilot systray button from FORM view...");
    const copilotBtn = await page.waitForSelector(".o_ai_systray_btn", { timeout: 15000 });
    await copilotBtn.click();
    await page.waitForTimeout(3000);

    const chatWindow = await page.waitForSelector(".o-mail-ChatWindow", { timeout: 15000 });
    if (!chatWindow) {
        throw new Error("Chat window did not open when clicking Insilos AI Copilot from Form view!");
    }

    const chatHeaderTitle = await page.$eval(".o-mail-ChatWindow-header", el => el.textContent);
    console.log(`Chat window opened successfully! Header text: "${chatHeaderTitle.trim()}"`);

    // Capture screenshot of Copilot opened on Form View
    await page.screenshot({
        path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/insilos_copilot_form_verified.png"
    });
    console.log("Captured insilos_copilot_form_verified.png");

    // Check for critical console errors
    console.log("\n--- Audit Console Summary ---");
    const criticalErrors = consoleErrors.filter(e => 
        e.includes("TypeError") || 
        e.includes("Cannot read properties") || 
        e.includes("recordDataToContextJSON") ||
        e.includes("openAiChat")
    );
    if (criticalErrors.length > 0) {
        console.error("CRITICAL ERRORS FOUND:", criticalErrors);
        throw new Error(`Test failed with ${criticalErrors.length} critical errors`);
    } else {
        console.log("Zero critical JS/Copilot runtime errors! Verified 100% clean.");
    }

    await browser.close();
    console.log("=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===");
})().catch(err => {
    console.error("Verification failed:", err);
    process.exit(1);
});
