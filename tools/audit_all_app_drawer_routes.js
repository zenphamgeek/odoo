const { chromium } = require("playwright");
const fs = require("fs");

(async () => {
  console.log("=== BẮT ĐẦU KIỂM TRA TOÀN BỘ CÁC ROUTES URL TRONG APPS DRAWER ===");
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.setDefaultTimeout(30000);

  // 1. Authenticate
  console.log("[Auth] Đăng nhập vào https://innoria.com...");
  await page.goto("https://innoria.com/web/login", { waitUntil: "domcontentloaded" });
  await page.evaluate(async () => {
    await fetch("/web/session/authenticate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: { db: "innoria_prod", login: "admin", password: "admin" } })
    });
  });

  // 2. Open Home Menu
  console.log("[HomeMenu] Mở Apps Drawer...");
  await page.goto("https://innoria.com/insilos", { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".o_home_menu", { timeout: 15000 });

  // Get all app items
  const apps = await page.evaluate(() => {
    const appElements = Array.from(document.querySelectorAll(".o_app, .o_home_menu .o_menuitem"));
    return appElements.map((el, idx) => ({
      index: idx,
      name: el.innerText.trim().split("\n")[0],
      href: el.getAttribute("href") || "",
      xmlid: el.getAttribute("data-menu-xmlid") || "",
      actionId: el.getAttribute("data-action-id") || "",
      menuId: el.getAttribute("data-menu-id") || "",
    })).filter(a => a.name);
  });

  console.log(`Tìm thấy ${apps.length} ứng dụng trong Apps Drawer:`);
  apps.forEach((a, i) => console.log(`  [${i + 1}/${apps.length}] ${a.name} (menuId: ${a.menuId}, actionId: ${a.actionId}, xmlid: ${a.xmlid}, href: ${a.href})`));

  const results = [];

  for (let i = 0; i < apps.length; i++) {
    const app = apps[i];
    console.log(`\n--- Kiểm tra [${i + 1}/${apps.length}]: ${app.name} (${app.href}) ---`);
    
    if (!app.href) {
      console.log(`  [WARN] App không có href`);
      results.push({ ...app, success: false, error: "No href" });
      continue;
    }

    const targetUrl = `https://innoria.com${app.href}`;
    await page.goto(targetUrl, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    const checkResult = await page.evaluate(() => {
      const errorDialog = document.querySelector(".o_error_dialog");
      const title = document.title;
      const url = window.location.href;
      const hasView = !!document.querySelector(".o_view_controller, .o_action, .o_list_view, .o_kanban_view, .o_form_view, .o-spreadsheet, .o_client_action");
      const hasHomeMenu = document.querySelector(".o_home_menu") && window.getComputedStyle(document.querySelector(".o_home_menu")).display !== "none";
      return {
        url,
        title,
        hasError: !!errorDialog,
        errorText: errorDialog?.innerText || null,
        hasView,
        hasHomeMenu,
      };
    });

    const isSuccess = !checkResult.hasError && (checkResult.hasView || !checkResult.hasHomeMenu);
    console.log(`  URL: ${checkResult.url} | Title: ${checkResult.title} | Error: ${checkResult.hasError ? checkResult.errorText.replace(/\n/g, ' ') : 'None'} | Success: ${isSuccess}`);
    results.push({ ...app, ...checkResult, success: isSuccess });
  }

  const successCount = results.filter(r => r.success).length;
  const failureCount = results.filter(r => !r.success).length;
  console.log(`\n========================================`);
  console.log(`KẾT QUẢ KIỂM TRA APPS DRAWER:`);
  console.log(`  Tổng số Apps: ${results.length}`);
  console.log(`  Thành công:   ${successCount}`);
  console.log(`  Thất bại:     ${failureCount}`);
  console.log(`========================================`);

  if (failureCount > 0) {
    console.log("Các app thất bại:");
    results.filter(r => !r.success).forEach(r => {
      console.log(`  - ${r.name}: ${r.error || r.errorText}`);
    });
  }

  fs.writeFileSync("/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/scratch/app_drawer_audit_results.json", JSON.stringify(results, null, 2));

  await browser.close();
})();
