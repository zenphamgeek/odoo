const { chromium } = require("playwright");

(async () => {
    console.log("Starting Dual-Scheme Playwright Audit...");
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);

    // 1. Set Light Cookie & Authenticate
    await context.addCookies([{ name: "color_scheme", value: "light", domain: "localhost", path: "/" }]);
    console.log("Navigating to login...");
    await page.goto("http://localhost:28069/web/login", { waitUntil: "domcontentloaded" });
    await page.fill("input[name=\"login\"]", "admin");
    await page.fill("input[name=\"password\"]", "admin");
    await Promise.all([
        page.waitForNavigation({ waitUntil: "domcontentloaded" }),
        page.click("button[type=\"submit\"]")
    ]);
    await page.waitForSelector(".o_navbar", { timeout: 20000 });

    // 2. Light Mode Verification
    console.log("Opening CRM Pipeline (Light Mode)...");
    await page.goto("http://localhost:28069/web#action=crm.crm_lead_action_pipeline", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_kanban_record", { timeout: 20000 });

    const card = await page.$(".o_kanban_record");
    if (card) {
        await card.click();
    }
    await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 20000 });
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
    await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 20000 });
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
