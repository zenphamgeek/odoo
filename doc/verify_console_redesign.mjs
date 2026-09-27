import { chromium } from "playwright";

const BASE = "http://localhost:28069";
const DB = "odoo20_dev";
const USER = "admin";
const PASS = "admin";

async function main() {
    console.log("Launching Chromium...");
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1800, height: 1100 },
        deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);
    page.setDefaultNavigationTimeout(60000);

    page.on("console", msg => console.log(`[BROWSER ${msg.type()}]:`, msg.text()));
    page.on("pageerror", err => console.error("[BROWSER ERROR]:", err));

    console.log("Authenticating via JSON-RPC API...");
    const authResponse = await context.request.post(`${BASE}/web/session/authenticate`, {
        data: { jsonrpc: "2.0", method: "call", params: { db: DB, login: USER, password: PASS } },
    });
    const authResult = (await authResponse.json()).result;
    console.log("Authenticated! UID:", authResult?.uid);

    const cookies = await context.cookies();
    console.log("Session cookies:", cookies.map(c => `${c.name}=${c.value.substring(0, 10)}...`));

    // 1. Test /insilos/settings
    console.log("Navigating to http://localhost:28069/insilos/settings ...");
    await page.goto(`${BASE}/insilos/settings`, { waitUntil: "domcontentloaded" });
    console.log("Page navigated! Current URL:", page.url());

    // Wait for the Settings Hub OWL 3 component to render
    console.log("Waiting for .is-settings-hub selector...");
    await page.waitForSelector(".is-settings-hub", { timeout: 30000 });
    console.log("Settings Hub component mounted!");

    // Wait for settings data to load
    await page.waitForSelector('.is-nav-item', { timeout: 10000 });
    await page.waitForTimeout(1000);

    // Capture Settings Hub in default dark mode
    await page.screenshot({ path: "doc/screenshots/09_insilos_settings_hub_dark.png" });
    console.log("Saved doc/screenshots/09_insilos_settings_hub_dark.png");

    // Click on AI & Intelligence tab
    console.log("Clicking AI & Intelligence tab...");
    const aiTab = page.locator('.is-nav-item:has-text("AI & Intelligence")');
    await aiTab.click();
    await page.waitForTimeout(600);

    // Modify a field to trigger the Floating Dock
    console.log("Modifying OCR endpoint to trigger floating dock...");
    const ocrInput = page.locator('.is-hub-content input[type="text"]').last();
    await ocrInput.fill("https://vision-cluster-01.internal.insilos.com/v2");
    await page.waitForTimeout(600);

    // Check if dock is visible
    const dockVisible = await page.locator(".is-settings-dock").isVisible();
    console.log("Floating bottom dock visible:", dockVisible);
    await page.screenshot({ path: "doc/screenshots/09_insilos_settings_hub_dock.png" });
    console.log("Saved doc/screenshots/09_insilos_settings_hub_dock.png");

    // Toggle theme to Light
    console.log("Toggling theme to Light mode...");
    await page.click(".is-theme-toggle");
    await page.waitForTimeout(600);
    await page.screenshot({ path: "doc/screenshots/09_insilos_settings_hub_light.png" });
    console.log("Saved doc/screenshots/09_insilos_settings_hub_light.png");

    // Switch back to Dark
    await page.click(".is-theme-toggle");
    await page.waitForTimeout(400);

    // Discard changes
    await page.click(".is-btn-discard");
    await page.waitForTimeout(400);

    // 2. Test /insilos/apps
    console.log("Navigating to http://localhost:28069/insilos/apps ...");
    await page.goto(`${BASE}/insilos/apps`, { waitUntil: "domcontentloaded" });
    console.log("Apps page loaded! Current URL:", page.url());

    await page.waitForSelector(".is-apps-marketplace", { timeout: 30000 });
    console.log("Apps Marketplace component mounted!");

    await page.waitForSelector(".is-app-card", { timeout: 10000 });
    const cardCount = await page.locator(".is-app-card").count();
    console.log(`Found ${cardCount} app cards in marketplace!`);

    await page.screenshot({ path: "doc/screenshots/10_insilos_apps_marketplace_all.png" });
    console.log("Saved doc/screenshots/10_insilos_apps_marketplace_all.png");

    // Filter by AI & Autonomous
    console.log("Filtering by AI & Autonomous...");
    const aiPill = page.locator('.is-pill:has-text("AI & Autonomous")');
    await aiPill.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: "doc/screenshots/10_insilos_apps_marketplace_ai.png" });
    console.log("Saved doc/screenshots/10_insilos_apps_marketplace_ai.png");

    // Click on Global Trade & Logistics
    console.log("Filtering by Global Trade & Logistics...");
    const tradePill = page.locator('.is-pill:has-text("Global Trade & Logistics")');
    await tradePill.click();
    await page.waitForTimeout(600);

    // Open detail drawer for first card
    console.log("Opening detail drawer for first trade app...");
    await page.locator(".is-app-card").first().click();
    await page.waitForSelector(".is-app-drawer", { timeout: 5000 });
    await page.waitForTimeout(600);
    await page.screenshot({ path: "doc/screenshots/10_insilos_apps_marketplace_drawer.png" });
    console.log("Saved doc/screenshots/10_insilos_apps_marketplace_drawer.png");

    // Close drawer
    await page.click(".is-btn-close");
    await page.waitForTimeout(400);

    console.log("All automated tests completed successfully!");
    await browser.close();
}

main().catch(err => {
    console.error("Test execution failed:", err);
    process.exit(1);
});
