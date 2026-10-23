const { chromium } = require("playwright");

(async () => {
    console.log("=== VERIFYING INNORIA AI CONCIERGE: RADIAL CURVED TEXT, EXTRA WIDE BLADES & FLOAT ALWAYS ON SCREEN ===");
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);

    const consoleErrors = [];
    page.on("console", msg => {
        if (msg.type() === "error") {
            consoleErrors.push(`[CONSOLE ERROR] ${msg.text()}`);
        }
    });
    page.on("pageerror", err => {
        consoleErrors.push(`[PAGE ERROR] ${err.message}\n${err.stack}`);
    });

    const targetUrl = process.env.TARGET_URL || "http://localhost:28069/";
    console.log(`1. Navigating to ${targetUrl}...`);
    await page.goto(targetUrl, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);

    // Step 1: Verify launcher and floating fan-out cluster
    console.log("2. Verifying launcher and floating fan-out cluster (Float Always On Screen)...");
    const launcher = await page.waitForSelector(".al2c-concierge-launcher", { timeout: 15000 });
    if (!launcher) {
        throw new Error("Launcher button .al2c-concierge-launcher not found!");
    }

    const clusterInfo = await page.evaluate(() => {
        const cluster = document.querySelector(".al2c-fanout-cluster");
        const svg = document.querySelector(".al2c-fanout-svg");
        const backdrop = document.querySelector(".al2c-fanout-backdrop");
        if (!cluster || !svg) return null;
        const cStyle = window.getComputedStyle(cluster);
        return {
            opacity: cStyle.opacity,
            pointerEvents: cStyle.pointerEvents,
            viewBox: svg.getAttribute("viewBox"),
            hasBackdrop: Boolean(backdrop),
            width: cStyle.width,
            height: cStyle.height,
        };
    });

    console.log("Cluster Info:", clusterInfo);
    if (!clusterInfo) {
        throw new Error(".al2c-fanout-cluster or .al2c-fanout-svg not found in DOM!");
    }
    if (clusterInfo.opacity !== "1") {
        throw new Error(`Expected fan-out cluster to float always on screen (opacity 1), got ${clusterInfo.opacity}`);
    }
    if (clusterInfo.pointerEvents !== "none") {
        throw new Error(`Expected cluster container pointer-events to be 'none' (non-blocking), got ${clusterInfo.pointerEvents}`);
    }
    if (!clusterInfo.viewBox || !clusterInfo.viewBox.includes("420")) {
        throw new Error(`Expected SVG viewBox 0 0 420 420 (Extra Wide Blades), got ${clusterInfo.viewBox}`);
    }
    if (clusterInfo.hasBackdrop) {
        throw new Error("Found blocking .al2c-fanout-backdrop when drawer is closed! Backdrop must not block website interactions.");
    }

    // Step 2: Verify the 3 blades and Radial Curved <textPath> text
    console.log("3. Verifying the 3 extra wide blades and radial curved <textPath> labels...");
    const blade1 = await page.waitForSelector(".al2c-fan-blade-01", { timeout: 5000 });
    const blade2 = await page.waitForSelector(".al2c-fan-blade-02", { timeout: 5000 });
    const blade3 = await page.waitForSelector(".al2c-fan-blade-03", { timeout: 5000 });

    const bladesData = await page.evaluate(() => {
        const b1 = document.querySelector(".al2c-fan-blade-01");
        const b2 = document.querySelector(".al2c-fan-blade-02");
        const b3 = document.querySelector(".al2c-fan-blade-03");

        const tp1 = b1 ? b1.querySelector("textPath") : null;
        const tp2 = b2 ? b2.querySelector("textPath") : null;
        const tp3 = b3 ? b3.querySelector("textPath") : null;

        return {
            b1Text: b1 ? b1.textContent.replace(/\s+/g, " ").trim() : "",
            b2Text: b2 ? b2.textContent.replace(/\s+/g, " ").trim() : "",
            b3Text: b3 ? b3.textContent.replace(/\s+/g, " ").trim() : "",
            tp1Href: tp1 ? (tp1.getAttribute("href") || tp1.getAttribute("xlink:href")) : null,
            tp2Href: tp2 ? (tp2.getAttribute("href") || tp2.getAttribute("xlink:href")) : null,
            tp3Href: tp3 ? (tp3.getAttribute("href") || tp3.getAttribute("xlink:href")) : null,
            tp1Content: tp1 ? tp1.textContent.trim() : null,
            tp2Content: tp2 ? tp2.textContent.trim() : null,
            tp3Content: tp3 ? tp3.textContent.trim() : null,
            b1PointerEvents: b1 ? window.getComputedStyle(b1).pointerEvents : null,
        };
    });

    console.log("Blades Data:", bladesData);
    if (!bladesData.tp1Href || !bladesData.tp1Href.includes("al2cFanArc01") || bladesData.tp1Content !== "CHAT") {
        throw new Error(`Expected Blade 01 to have <textPath> href #al2cFanArc01 with text 'CHAT', got ${JSON.stringify(bladesData)}`);
    }
    if (!bladesData.tp2Href || !bladesData.tp2Href.includes("al2cFanArc02") || bladesData.tp2Content !== "DỰ TOÁN") {
        throw new Error(`Expected Blade 02 to have <textPath> href #al2cFanArc02 with text 'DỰ TOÁN', got ${JSON.stringify(bladesData)}`);
    }
    if (!bladesData.tp3Href || !bladesData.tp3Href.includes("al2cFanArc03") || bladesData.tp3Content !== "BÁO GIÁ") {
        throw new Error(`Expected Blade 03 to have <textPath> href #al2cFanArc03 with text 'BÁO GIÁ', got ${JSON.stringify(bladesData)}`);
    }
    if (bladesData.b1PointerEvents !== "auto") {
        throw new Error(`Expected blade pointer-events to be 'auto', got ${bladesData.b1PointerEvents}`);
    }

    // Capture screenshot of always floating radial fan
    const screenshot1Path = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_fanout_radial_always_floating.png";
    await page.screenshot({ path: screenshot1Path });
    console.log(`[✓] Captured screenshot: ${screenshot1Path}`);

    // Step 3: Hover over Blade 02 to verify zoom effect
    console.log("4. Hovering over Blade 02 ('DỰ TOÁN') to test zoom-out effect...");
    await blade2.hover();
    await page.waitForTimeout(400);

    const screenshot2Path = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_fanout_radial_hover_zoom.png";
    await page.screenshot({ path: screenshot2Path });
    console.log(`[✓] Captured screenshot: ${screenshot2Path}`);

    // Step 4: Click Blade 02 to open drawer in Services / Dự Toán tab
    console.log("5. Clicking Blade 02 ('DỰ TOÁN')...");
    await blade2.click();
    await page.waitForTimeout(800);

    const drawerOpen = await page.$eval(".al2c-concierge-drawer", el => el.classList.contains("is-open"));
    const activeTab = await page.$eval(".al2c-tab-btn.is-active", el => el.textContent.trim());
    const clusterHidden = await page.$eval(".al2c-fanout-cluster", el => el.classList.contains("is-drawer-open"));
    console.log(`Drawer open: ${drawerOpen}, Active tab: "${activeTab}", Cluster tucked away: ${clusterHidden}`);

    if (!drawerOpen) {
        throw new Error("Expected drawer to open after clicking Blade 02!");
    }
    if (!activeTab.includes("Dịch Vụ") && !activeTab.includes("Dự Toán")) {
        throw new Error(`Expected active tab to be 'Dịch Vụ & Dự Toán', got '${activeTab}'`);
    }
    if (!clusterHidden) {
        throw new Error("Expected .al2c-fanout-cluster to have class .is-drawer-open when drawer is open!");
    }

    const screenshot3Path = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_fanout_radial_drawer_opened.png";
    await page.screenshot({ path: screenshot3Path });
    console.log(`[✓] Captured screenshot: ${screenshot3Path}`);

    // Step 5: Close drawer via launcher button and verify fan blades return to floating state
    console.log("6. Clicking launcher button to close drawer...");
    await launcher.click();
    await page.waitForTimeout(600);

    const drawerClosed = await page.$eval(".al2c-concierge-drawer", el => !el.classList.contains("is-open"));
    const clusterReturned = await page.$eval(".al2c-fanout-cluster", el => !el.classList.contains("is-drawer-open"));
    console.log(`Drawer closed: ${drawerClosed}, Cluster returned to floating: ${clusterReturned}`);

    if (!drawerClosed || !clusterReturned) {
        throw new Error("Expected drawer to close and fan blades to return to floating state!");
    }

    // Check critical console errors
    const criticalErrors = consoleErrors.filter(e => !e.includes("favicon") && !e.includes("404"));
    if (criticalErrors.length > 0) {
        console.error("Critical console errors detected:", criticalErrors);
        throw new Error(`Test failed with ${criticalErrors.length} console errors`);
    }

    console.log("\n=== 🏆 RADIAL CURVED TEXT, EXTRA WIDE BLADES & FLOAT ALWAYS ON SCREEN 100% VERIFIED! ===");
    await browser.close();
})().catch(err => {
    console.error("Verification failed:", err);
    process.exit(1);
});
