import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCREENSHOT_DIR = path.resolve(__dirname, "screenshots");

const BASE = "http://localhost:28069";
const DB = "odoo20_dev";
const USER = "admin";
const PASS = "admin";

async function main() {
    console.log("Launching Chromium for Restructured UI/UX Verification...");
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1800, height: 1100 },
        deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);
    page.setDefaultNavigationTimeout(60000);

    page.on("console", msg => {
        const text = msg.text();
        if (text.includes("favicon.ico") || text.includes("websocket")) return;
        console.log(`[BROWSER ${msg.type()}]:`, text);
    });
    page.on("pageerror", err => console.error("[BROWSER ERROR]:", err));

    console.log("Authenticating via JSON-RPC API...");
    const authResponse = await context.request.post(`${BASE}/web/session/authenticate`, {
        data: { jsonrpc: "2.0", method: "call", params: { db: DB, login: USER, password: PASS } },
    });
    const authResult = (await authResponse.json()).result;
    console.log("Authenticated! UID:", authResult?.uid);

    // -------------------------------------------------------------------------
    // 1. Verify Restructured Settings Hub (/odoo/settings)
    // -------------------------------------------------------------------------
    console.log("Navigating to http://localhost:28069/odoo/settings ...");
    await page.goto(`${BASE}/odoo/settings`, { waitUntil: "domcontentloaded" });
    console.log("Waiting for .o_base_settings_view and .o_setting_box...");
    await page.waitForSelector(".o_base_settings_view", { timeout: 45000 });
    await page.waitForSelector(".o_setting_box", { timeout: 30000 });
    await page.waitForTimeout(1500);

    const shot1 = path.join(SCREENSHOT_DIR, "11_restructured_settings_light.png");
    console.log("Saving screenshot:", shot1);
    await page.screenshot({ path: shot1 });

    // Click on another tab in the sidebar
    console.log("Switching tab to CRM / Sales...");
    const crmTab = page.locator('.settings_tab .tab:has-text("CRM"), .settings_tab .tab:has-text("Sales")').first();
    if (await crmTab.count() > 0) {
        await crmTab.click();
        await page.waitForTimeout(1000);
        console.log("Tab switched successfully!");
    }

    // Toggle dark mode class to verify dark theme
    console.log("Testing Dark Mode appearance on Settings...");
    await page.evaluate(() => document.body.classList.add("o_dark_mode"));
    await page.waitForTimeout(600);
    const shot2 = path.join(SCREENSHOT_DIR, "11_restructured_settings_dark.png");
    await page.screenshot({ path: shot2 });
    console.log("Saved screenshot:", shot2);
    await page.evaluate(() => document.body.classList.remove("o_dark_mode"));

    // -------------------------------------------------------------------------
    // 2. Verify Restructured Apps Marketplace (/odoo/apps)
    // -------------------------------------------------------------------------
    console.log("Navigating to http://localhost:28069/odoo/apps ...");
    await page.goto(`${BASE}/odoo/apps`, { waitUntil: "domcontentloaded" });
    console.log("Waiting for .o_modules_kanban and .o_kanban_record...");
    await page.waitForSelector(".o_modules_kanban", { timeout: 45000 });
    await page.waitForSelector(".o_kanban_record", { timeout: 30000 });
    await page.waitForTimeout(1500);

    const appCount = await page.locator(".o_kanban_record").count();
    console.log(`Found ${appCount} app cards in Kanban!`);

    const shot3 = path.join(SCREENSHOT_DIR, "12_restructured_apps_kanban.png");
    console.log("Saving screenshot:", shot3);
    await page.screenshot({ path: shot3 });

    // Test SearchPanel category filter
    console.log("Clicking a Category in SearchPanel...");
    const visibleCategory = page.locator(".o_search_panel .list-group-item").nth(1);
    if (await visibleCategory.count() > 0) {
        const catName = await visibleCategory.innerText();
        console.log(`Filtering by category: ${catName.trim().split("\n")[0]}`);
        await visibleCategory.click({ force: true });
        await page.waitForTimeout(1200);
        const shot4 = path.join(SCREENSHOT_DIR, "12_restructured_apps_filtered.png");
        await page.screenshot({ path: shot4 });
        console.log("Saved screenshot:", shot4);
    }

    console.log("All UI/UX restructure verification tests finished successfully!");
    await browser.close();
}

main().catch(err => {
    console.error("Test failed:", err);
    process.exit(1);
});
