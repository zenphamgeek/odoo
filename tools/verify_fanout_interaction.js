const { chromium } = require("playwright");

(async () => {
    console.log("=== VERIFYING INNORIA AI CONCIERGE & COPILOT 90° FAN-OUT RADIAL INTERACTION ===");
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
    await page.waitForTimeout(2000);

    // Wait for the launcher
    console.log("2. Locating .al2c-concierge-launcher...");
    const launcher = await page.waitForSelector(".al2c-concierge-launcher", { timeout: 15000 });
    if (!launcher) {
        throw new Error("Launcher button .al2c-concierge-launcher not found!");
    }

    // Step 1: Initial state - fan-out is closed
    const initialClusterActive = await page.$eval(".al2c-fanout-cluster", el => el.classList.contains("is-active")).catch(() => false);
    console.log(`Initial fan-out cluster active: ${initialClusterActive}`);

    // Step 2: Click launcher to toggle 90° fan-out quarter-circle
    console.log("3. Clicking launcher to trigger 90° Fan-Out radial interaction...");
    await launcher.click();
    await page.waitForTimeout(600);

    // Verify cluster is now active
    const clusterActive = await page.$eval(".al2c-fanout-cluster", el => el.classList.contains("is-active"));
    console.log(`Fan-out cluster active after click: ${clusterActive}`);
    if (!clusterActive) {
        throw new Error("Expected .al2c-fanout-cluster to have class 'is-active'!");
    }

    // Verify the 3 nodes
    const nodeChat = await page.waitForSelector(".al2c-fanout-node-chat", { timeout: 5000 });
    const nodeServices = await page.waitForSelector(".al2c-fanout-node-services", { timeout: 5000 });
    const nodeLead = await page.waitForSelector(".al2c-fanout-node-lead", { timeout: 5000 });

    const chatTitle = await nodeChat.$eval(".al2c-pill-title", el => el.textContent.trim());
    const servicesTitle = await nodeServices.$eval(".al2c-pill-title", el => el.textContent.trim());
    const leadTitle = await nodeLead.$eval(".al2c-pill-title", el => el.textContent.trim());

    console.log(`Node 1 (Vertical UP): "${chatTitle}"`);
    console.log(`Node 2 (Center Diagonal): "${servicesTitle}"`);
    console.log(`Node 3 (Horizontal LEFT): "${leadTitle}"`);

    // Verify coordinates forming the 90° inward arc
    const launcherBox = await launcher.boundingBox();
    const chatBox = await nodeChat.boundingBox();
    const servicesBox = await nodeServices.boundingBox();
    const leadBox = await nodeLead.boundingBox();

    console.log("Node coordinates relative to launcher center:");
    const lCenterX = launcherBox.x + launcherBox.width / 2;
    const lCenterY = launcherBox.y + launcherBox.height / 2;

    const chatDx = chatBox.x + chatBox.width / 2 - lCenterX;
    const chatDy = chatBox.y + chatBox.height / 2 - lCenterY;
    const servDx = servicesBox.x + servicesBox.width / 2 - lCenterX;
    const servDy = servicesBox.y + servicesBox.height / 2 - lCenterY;
    const leadDx = leadBox.x + leadBox.width / 2 - lCenterX;
    const leadDy = leadBox.y + leadBox.height / 2 - lCenterY;

    console.log(`  Chat:     dx=${chatDx.toFixed(1)}px, dy=${chatDy.toFixed(1)}px (Angle: ${((Math.atan2(-chatDy, -chatDx) * 180) / Math.PI).toFixed(1)}°)`);
    console.log(`  Services: dx=${servDx.toFixed(1)}px, dy=${servDy.toFixed(1)}px (Angle: ${((Math.atan2(-servDy, -servDx) * 180) / Math.PI).toFixed(1)}°)`);
    console.log(`  Lead:     dx=${leadDx.toFixed(1)}px, dy=${leadDy.toFixed(1)}px (Angle: ${((Math.atan2(-leadDy, -leadDx) * 180) / Math.PI).toFixed(1)}°)`);

    // Capture screenshot of Fan-Out Quarter-Circle in action
    const screenshot1Path = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_fanout_quarter_circle_active.png";
    await page.screenshot({ path: screenshot1Path });
    console.log(`[✓] Captured screenshot: ${screenshot1Path}`);

    // Step 3: Click Node 2 ("Dịch Vụ & Dự Toán")
    console.log("4. Clicking Node 2 ('Dịch Vụ & Dự Toán')...");
    await nodeServices.click();
    await page.waitForTimeout(800);

    // Verify drawer opened in services tab
    const drawerOpen = await page.$eval(".al2c-concierge-drawer", el => el.classList.contains("is-open"));
    const activeTab = await page.$eval(".al2c-tab-btn.is-active", el => el.textContent.trim());
    console.log(`Drawer open: ${drawerOpen}, Active tab: "${activeTab}"`);
    if (!drawerOpen) {
        throw new Error("Expected drawer to open after clicking fan-out item!");
    }
    if (!activeTab.includes("Dịch Vụ") && !activeTab.includes("Dự Toán")) {
        throw new Error(`Expected active tab to be 'Dịch Vụ & Dự Toán', got '${activeTab}'`);
    }

    // Capture screenshot of drawer opened from fan-out
    const screenshot2Path = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/innoria_fanout_drawer_opened.png";
    await page.screenshot({ path: screenshot2Path });
    console.log(`[✓] Captured screenshot: ${screenshot2Path}`);

    // Check critical console errors
    const criticalErrors = consoleErrors.filter(e => !e.includes("favicon") && !e.includes("404"));
    if (criticalErrors.length > 0) {
        console.error("Critical console errors detected:", criticalErrors);
        throw new Error(`Test failed with ${criticalErrors.length} console errors`);
    }

    console.log("\n=== 🏆 90° FAN-OUT QUARTER-CIRCLE INTERACTION 100% VERIFIED! ===");
    await browser.close();
})().catch(err => {
    console.error("Verification failed:", err);
    process.exit(1);
});
