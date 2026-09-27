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
    console.log("Starting Layout Audit on Settings (Switches, Radios, and Systray)...");
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1800, height: 1100 },
        deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);
    page.setDefaultNavigationTimeout(60000);

    console.log("Authenticating...");
    await context.request.post(`${BASE}/web/session/authenticate`, {
        data: { jsonrpc: "2.0", method: "call", params: { db: DB, login: USER, password: PASS } },
    });

    console.log("Navigating to http://localhost:28069/odoo/settings ...");
    await page.goto(`${BASE}/odoo/settings`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_base_settings_view", { timeout: 45000 });
    await page.waitForSelector(".o_setting_box", { timeout: 30000 });
    await page.waitForTimeout(1500);

    // 1. Audit Top Systray (Confirm ONLY 1 Avatar 'A')
    const systray = page.locator(".o_menu_systray");
    const avatarCount = await systray.locator(".o-mail-DiscussAvatar, .o_user_avatar").count();
    console.log(`Audited Systray Avatar count: ${avatarCount} (should be 1)`);
    const shot1 = path.join(SCREENSHOT_DIR, "16_audit_systray_single_avatar.png");
    await page.screenshot({ path: shot1 });
    console.log("Saved:", shot1);

    // 2. Audit Events Tab: Toggle Switches (Confirm NO checkmark artifact under knob)
    console.log("Clicking Events tab...");
    const eventsTab = page.locator('.settings_tab .tab:has-text("Events")').first();
    if (await eventsTab.count() > 0) {
        await eventsTab.click();
        await page.waitForTimeout(1200);

        // Turn on a switch if not checked
        const firstSwitch = page.locator('.o_setting_box input[type="checkbox"]').first();
        if (await firstSwitch.count() > 0 && !(await firstSwitch.isChecked())) {
            await firstSwitch.click();
            await page.waitForTimeout(500);
        }

        const shot2 = path.join(SCREENSHOT_DIR, "16_audit_events_clean_switches.png");
        await page.screenshot({ path: shot2 });
        console.log("Saved:", shot2);
    }

    // 3. Audit General Settings Tab: Radio Buttons (Units of measure)
    console.log("Clicking General Settings tab...");
    const genTab = page.locator('.settings_tab .tab:has-text("General Settings")').first();
    if (await genTab.count() > 0) {
        await genTab.click();
        await page.waitForTimeout(1200);

        // Scroll down to Units of Measure
        const radioSection = page.locator('h2:has-text("Units of Measure")');
        if (await radioSection.count() > 0) {
            await radioSection.scrollIntoViewIfNeeded();
            await page.waitForTimeout(500);
        }

        const shot3 = path.join(SCREENSHOT_DIR, "16_audit_radios_units_of_measure.png");
        await page.screenshot({ path: shot3 });
        console.log("Saved:", shot3);
    }

    console.log("Visual Audit completed successfully!");
    await browser.close();
}

main().catch(err => {
    console.error("Audit failed:", err);
    process.exit(1);
});
