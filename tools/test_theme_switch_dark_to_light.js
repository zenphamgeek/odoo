const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE_URL = process.env.ODOO_URL || "http://localhost:28069";
const ODOO_DB = process.env.ODOO_DB || "insilos20_dev";
const ODOO_LOGIN = process.env.ODOO_LOGIN || "admin";
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || "admin";
const SCREENSHOT_DIR =
    process.env.SCREENSHOT_DIR ||
    "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/screenshots";

fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function evaluateSections(page, selectors) {
    return await page.evaluate((sels) => {
        function parseColor(str) {
            if (!str) return null;
            const m = str.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)/i);
            if (!m) return null;
            return {
                r: parseInt(m[1], 10),
                g: parseInt(m[2], 10),
                b: parseInt(m[3], 10),
                a: m[4] !== undefined ? parseFloat(m[4]) : 1,
            };
        }

        function srgbToLinear(c) {
            const v = c / 255;
            return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        }

        function luminance({ r, g, b }) {
            return 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
        }

        function resolveEffectiveBg(el) {
            const layers = [];
            let curr = el;
            while (curr && curr.nodeType === 1) {
                const cs = window.getComputedStyle(curr);
                const parsed = parseColor(cs.backgroundColor);
                if (parsed && parsed.a > 0) {
                    layers.push(parsed);
                    if (parsed.a >= 0.99) break;
                }
                curr = curr.parentElement;
            }
            const isDarkRoot =
                document.documentElement.classList.contains("o_dark_mode") ||
                document.body.classList.contains("o_dark_mode") ||
                document.documentElement.getAttribute("data-bs-theme") === "dark";
            let base = isDarkRoot ? { r: 7, g: 11, b: 20 } : { r: 244, g: 246, b: 248 };
            for (let i = layers.length - 1; i >= 0; i--) {
                const fg = layers[i];
                const a = fg.a;
                base = {
                    r: Math.round(fg.r * a + base.r * (1 - a)),
                    g: Math.round(fg.g * a + base.g * (1 - a)),
                    b: Math.round(fg.b * a + base.b * (1 - a)),
                };
            }
            return base;
        }

        function resolveTextColor(el) {
            // Find a representative text element inside the section (such as breadcrumb, link, caption, or header)
            const textCandidate =
                el.querySelector(
                    ".o_last_breadcrumb_item, .o_breadcrumb_item, .o_menu_brand, .o_nav_entry, .o_search_panel_section_header, .o_caption, h1, h2, h3, .o_kanban_record_title, span"
                ) || el;
            const cs = window.getComputedStyle(textCandidate);
            return parseColor(cs.color) || { r: 15, g: 23, b: 42, a: 1 };
        }

        const out = {};
        for (const sel of sels) {
            const el = document.querySelector(sel);
            if (!el) {
                out[sel] = { found: false };
                continue;
            }
            const bgRgb = resolveEffectiveBg(el);
            const fgRgb = resolveTextColor(el);
            out[sel] = {
                found: true,
                bgRgb: `rgb(${bgRgb.r}, ${bgRgb.g}, ${bgRgb.b})`,
                bgLuminance: Number(luminance(bgRgb).toFixed(4)),
                fgRgb: `rgb(${fgRgb.r}, ${fgRgb.g}, ${fgRgb.b})`,
                textLuminance: Number(luminance(fgRgb).toFixed(4)),
            };
        }
        return {
            cookie: document.cookie,
            localStorageTheme: localStorage.getItem("insilos_theme"),
            htmlDarkClass: document.documentElement.classList.contains("o_dark_mode"),
            bodyDarkClass: document.body.classList.contains("o_dark_mode"),
            stylesheets: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map((l) =>
                l.getAttribute("href")
            ),
            sections: out,
        };
    }, selectors);
}

(async () => {
    console.log(`[Patch 27] Starting Dark -> Light E2E Theme Switch Verification against ${BASE_URL}...`);
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });
    const parsedUrl = new URL(BASE_URL);
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);

    try {
        // 1. Start in Dark Mode and authenticate
        await page.goto(`${BASE_URL}/web/login`, { waitUntil: "domcontentloaded" });
        await page.evaluate(
            async ({ db, login, password }) => {
                localStorage.setItem("insilos_theme", "dark");
                document.cookie = "color_scheme=dark; path=/; max-age=31536000; SameSite=Lax";
                await fetch("/web/session/authenticate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: { db, login, password },
                    }),
                });
            },
            { db: ODOO_DB, login: ODOO_LOGIN, password: ODOO_PASSWORD }
        );

        // Navigate to /odoo/documents in Dark Mode
        console.log("[1/4] Navigating to /odoo/documents in Dark Mode...");
        await page.goto(`${BASE_URL}/odoo/documents`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_main_navbar", { timeout: 45000 });
        await page.waitForSelector(".o_control_panel", { timeout: 45000 });
        await page.waitForSelector(".o_search_panel", { timeout: 45000 });
        await page.waitForSelector(".o_content", { timeout: 45000 });
        await page.waitForTimeout(1000);

        const darkDocsState = await evaluateSections(page, [
            ".o_main_navbar",
            ".o_control_panel",
            ".o_search_panel",
            ".o_content",
        ]);
        console.log("Dark Mode (/odoo/documents) Audit:", JSON.stringify(darkDocsState, null, 2));

        for (const sel of [".o_main_navbar", ".o_control_panel", ".o_search_panel", ".o_content"]) {
            const sec = darkDocsState.sections[sel];
            if (!sec || !sec.found) {
                throw new Error(`Dark Mode check failed: selector ${sel} not found on /odoo/documents`);
            }
            if (sec.bgLuminance >= 0.15) {
                throw new Error(
                    `Dark Mode check failed: ${sel} bgLuminance=${sec.bgLuminance} (${sec.bgRgb}) expected < 0.15`
                );
            }
        }

        // 2. Click UserMenu and switch Dark -> Light via the UI toggle button
        console.log("[2/4] Clicking UserMenu -> Light theme toggle button...");
        await page.click("button.o_user_menu");
        const lightBtnSelector =
            '.is-theme-btn:has-text("Light"), .o_theme_segment_btn:has-text("Light")';
        await page.waitForSelector(lightBtnSelector, { timeout: 15000 });
        await Promise.all([
            page.waitForNavigation({ waitUntil: "domcontentloaded", timeout: 45000 }),
            page.click(lightBtnSelector),
        ]);
        await page.waitForSelector(".o_main_navbar", { timeout: 45000 });
        await page.waitForSelector(".o_control_panel", { timeout: 45000 });
        await page.waitForSelector(".o_search_panel", { timeout: 45000 });
        await page.waitForSelector(".o_content", { timeout: 45000 });
        await page.waitForTimeout(1200);

        const lightDocsState = await evaluateSections(page, [
            ".o_main_navbar",
            ".o_control_panel",
            ".o_search_panel",
            ".o_content",
        ]);
        console.log("Light Mode (/odoo/documents) Audit:", JSON.stringify(lightDocsState, null, 2));

        for (const sel of [".o_main_navbar", ".o_control_panel", ".o_search_panel", ".o_content"]) {
            const sec = lightDocsState.sections[sel];
            if (!sec || !sec.found) {
                throw new Error(`Light Mode check failed: selector ${sel} not found on /odoo/documents`);
            }
            if (sec.bgLuminance <= 0.85) {
                throw new Error(
                    `Light Mode check failed on /odoo/documents: ${sel} bgLuminance=${sec.bgLuminance} (${sec.bgRgb}) expected > 0.85`
                );
            }
            if (sec.textLuminance >= 0.25) {
                throw new Error(
                    `Light Mode check failed on /odoo/documents: ${sel} textLuminance=${sec.textLuminance} (${sec.fgRgb}) expected < 0.25`
                );
            }
        }

        const docsShotPath = path.join(SCREENSHOT_DIR, "verified_theme_dark_to_light_documents.png");
        await page.screenshot({ path: docsShotPath });
        console.log(`Saved screenshot: ${docsShotPath}`);

        // 3. Navigate to /odoo (HomeMenu / Employee Dashboard) in Light Mode
        console.log("[3/4] Verifying /odoo (HomeMenu / Employee Dashboard) in Light Mode...");
        await page.goto(`${BASE_URL}/odoo`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_main_navbar", { timeout: 45000 });
        await page.waitForSelector(".o_home_menu, .o_insilos_emp_dashboard", { timeout: 45000 });
        await page.waitForTimeout(1200);

        const homeSelector = (await page.$(".o_insilos_emp_dashboard"))
            ? ".o_insilos_emp_dashboard"
            : ".o_home_menu";
        const lightHomeState = await evaluateSections(page, [".o_main_navbar", homeSelector]);
        console.log("Light Mode (/odoo HomeMenu) Audit:", JSON.stringify(lightHomeState, null, 2));

        for (const sel of [".o_main_navbar", homeSelector]) {
            const sec = lightHomeState.sections[sel];
            if (!sec || !sec.found) {
                throw new Error(`Light Mode check failed: selector ${sel} not found on /odoo`);
            }
            if (sec.bgLuminance <= 0.85) {
                throw new Error(
                    `Light Mode check failed on /odoo: ${sel} bgLuminance=${sec.bgLuminance} (${sec.bgRgb}) expected > 0.85`
                );
            }
            if (sec.textLuminance >= 0.25) {
                throw new Error(
                    `Light Mode check failed on /odoo: ${sel} textLuminance=${sec.textLuminance} (${sec.fgRgb}) expected < 0.25`
                );
            }
        }

        const homeShotPath = path.join(SCREENSHOT_DIR, "verified_theme_dark_to_light_homemenu.png");
        await page.screenshot({ path: homeShotPath });
        console.log(`Saved screenshot: ${homeShotPath}`);

        // 4. Navigate to /odoo/crm in Light Mode
        console.log("[4/4] Verifying /odoo/crm in Light Mode...");
        await page.goto(`${BASE_URL}/odoo/crm`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_main_navbar", { timeout: 45000 });
        await page.waitForSelector(".o_control_panel", { timeout: 45000 });
        await page.waitForSelector(".o_content", { timeout: 45000 });
        await page.waitForTimeout(1200);

        const lightCrmState = await evaluateSections(page, [
            ".o_main_navbar",
            ".o_control_panel",
            ".o_content",
        ]);
        console.log("Light Mode (/odoo/crm) Audit:", JSON.stringify(lightCrmState, null, 2));

        for (const sel of [".o_main_navbar", ".o_control_panel", ".o_content"]) {
            const sec = lightCrmState.sections[sel];
            if (!sec || !sec.found) {
                throw new Error(`Light Mode check failed: selector ${sel} not found on /odoo/crm`);
            }
            if (sec.bgLuminance <= 0.85) {
                throw new Error(
                    `Light Mode check failed on /odoo/crm: ${sel} bgLuminance=${sec.bgLuminance} (${sec.bgRgb}) expected > 0.85`
                );
            }
            if (sec.textLuminance >= 0.25) {
                throw new Error(
                    `Light Mode check failed on /odoo/crm: ${sel} textLuminance=${sec.textLuminance} (${sec.fgRgb}) expected < 0.25`
                );
            }
        }

        const crmShotPath = path.join(SCREENSHOT_DIR, "verified_theme_dark_to_light_crm.png");
        await page.screenshot({ path: crmShotPath });
        console.log(`Saved screenshot: ${crmShotPath}`);

        console.log("[🎉] ALL DARK -> LIGHT THEME SWITCH E2E LUMINANCE & SCREENSHOT CHECKS PASSED!");
    } finally {
        await browser.close();
    }
})();
