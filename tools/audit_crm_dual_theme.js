const { chromium } = require("playwright");

(async () => {
    console.log("Starting Dual-Scheme Playwright Audit...");
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);

    // 1. Set Light Cookie & Authenticate deterministically via JSON-RPC
    await context.addCookies([{ name: "color_scheme", value: "light", domain: "localhost", path: "/" }]);
    console.log("Authenticating session...");
    await page.goto("http://localhost:28069/web/login", { waitUntil: "domcontentloaded" });
    await page.evaluate(async () => {
        await fetch("/web/session/authenticate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: { db: "insilos20_dev", login: "admin", password: "admin" }
            })
        });
    });
    await page.goto("http://localhost:28069/odoo", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_navbar", { timeout: 60000 });

    // 2. Light Mode Verification (Direct Form URL via JSON-RPC ID lookup)
    console.log("Opening CRM Pipeline Form (Light Mode)...");
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
        return (data.result && data.result[0]) || 1;
    });
    await page.goto(`http://localhost:28069/odoo/crm/${leadId}`, { waitUntil: "domcontentloaded" });
    try {
        await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 15000 });
    } catch (e) {
        await page.goto(`http://localhost:28069/web#id=${leadId}&model=crm.lead&view_type=form`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 30000 });
    }
    await page.waitForTimeout(1000);

    const lightAudit = await page.evaluate(() => {
        const form = document.querySelector(".o_form_view");
        const sheet = document.querySelector(".o_form_sheet");
        const launcher = document.querySelector(".o_navbar_apps_menu") || document.querySelector(".o_menu_toggle");
        const launcherImgs = launcher ? Array.from(launcher.querySelectorAll("img")).map(img => ({
            src: img.src.split("/").pop(),
            className: img.className,
            display: window.getComputedStyle(img).display,
            width: img.offsetWidth,
            height: img.offsetHeight
        })) : [];

        const visibleLogos = launcherImgs.filter(i => i.display !== "none" && i.width > 0);

        return {
            mode: "LIGHT",
            formBg: form ? window.getComputedStyle(form).backgroundColor : null,
            formColor: form ? window.getComputedStyle(form).color : null,
            sheetBg: sheet ? window.getComputedStyle(sheet).backgroundColor : null,
            sheetWidth: sheet ? sheet.offsetWidth : null,
            bgCanvasVar: window.getComputedStyle(document.body).getPropertyValue("--insilos-bg-canvas").trim(),
            launcherImgs,
            visibleLogoCount: visibleLogos.length,
            visibleLogos
        };
    });

    await page.screenshot({ path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/crm_form_perfect_light.png" });
    console.log("Light Mode Audit Result:", JSON.stringify(lightAudit, null, 2));

    // 3. Dark Mode Verification (Real Server Bundle Reload)
    console.log("Switching to Dark Theme (color_scheme=dark cookie + reload)...");
    await page.evaluate(() => {
        localStorage.setItem("insilos_theme", "dark");
        document.cookie = "color_scheme=dark;path=/;max-age=31536000";
    });
    await context.addCookies([{ name: "color_scheme", value: "dark", domain: "localhost", path: "/" }]);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 30000 });
    await page.waitForTimeout(1000);

    const darkAudit = await page.evaluate(() => {
        const form = document.querySelector(".o_form_view");
        const sheet = document.querySelector(".o_form_sheet");
        const tabs = document.querySelector(".nav-tabs");
        const launcher = document.querySelector(".o_navbar_apps_menu") || document.querySelector(".o_menu_toggle");
        const launcherImgs = launcher ? Array.from(launcher.querySelectorAll("img")).map(img => ({
            src: img.src.split("/").pop(),
            className: img.className,
            display: window.getComputedStyle(img).display,
            width: img.offsetWidth,
            height: img.offsetHeight
        })) : [];

        const visibleLogos = launcherImgs.filter(i => i.display !== "none" && i.width > 0);

        // Check for any bare white surfaces in dark mode
        const whiteElements = [];
        document.querySelectorAll(".o_form_view *").forEach(el => {
            const bg = window.getComputedStyle(el).backgroundColor;
            if (bg === "rgb(255, 255, 255)" && el.offsetWidth > 20 && el.offsetHeight > 20) {
                whiteElements.push({ tag: el.tagName, class: el.className, w: el.offsetWidth, h: el.offsetHeight });
            }
        });

        return {
            mode: "DARK",
            formBg: form ? window.getComputedStyle(form).backgroundColor : null,
            formColor: form ? window.getComputedStyle(form).color : null,
            sheetBg: sheet ? window.getComputedStyle(sheet).backgroundColor : null,
            sheetColor: sheet ? window.getComputedStyle(sheet).color : null,
            sheetWidth: sheet ? sheet.offsetWidth : null,
            tabsBg: tabs ? window.getComputedStyle(tabs).backgroundColor : null,
            bgCanvasVar: window.getComputedStyle(document.body).getPropertyValue("--insilos-bg-canvas").trim(),
            launcherImgs,
            visibleLogoCount: visibleLogos.length,
            visibleLogos,
            bareWhiteCount: whiteElements.length,
            whiteElements: whiteElements.slice(0, 10)
        };
    });

    await page.screenshot({ path: "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/crm_form_perfect_dark.png" });
    console.log("Dark Mode Audit Result:", JSON.stringify(darkAudit, null, 2));

    await browser.close();

    // Invariant assertions
    const errors = [];
    if (lightAudit.visibleLogoCount !== 1) {
        errors.push(`Light mode expected exactly 1 logo, got ${lightAudit.visibleLogoCount}`);
    }
    if (darkAudit.visibleLogoCount !== 1) {
        errors.push(`Dark mode expected exactly 1 logo, got ${darkAudit.visibleLogoCount}`);
    }
    if (darkAudit.bareWhiteCount > 0) {
        errors.push(`Dark mode found ${darkAudit.bareWhiteCount} bare white surfaces: ${JSON.stringify(darkAudit.whiteElements)}`);
    }
    if (lightAudit.sheetWidth < 1000) {
        errors.push(`Form sheet width is constricted (${lightAudit.sheetWidth}px < 1000px)`);
    }

    if (errors.length > 0) {
        console.error("FAIL - Invariant violations:", errors);
        process.exit(1);
    } else {
        console.log("SUCCESS - 100% Invariants Cleared: Single Logo, Full Width, Zero Bare White Surfaces!");
        process.exit(0);
    }
})();
