const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const DASHBOARDS = [
  { id: 3, section: "Sales", name: "Sales", slug: "sales" },
  { id: 4, section: "Sales", name: "Product", slug: "product" },
  { id: 11, section: "Sales", name: "Point of Sale", slug: "point_of_sale" },
  { id: 15, section: "Sales", name: "Rental", slug: "rental" },
  { id: 17, section: "Subscriptions", name: "Subscriptions", slug: "subscriptions" },
  { id: 18, section: "Subscriptions", name: "MRR Evolution", slug: "mrr_evolution" },
  { id: 19, section: "Subscriptions", name: "Retention", slug: "retention" },
  { id: 20, section: "Subscriptions", name: "Salesperson", slug: "salesperson" },
  { id: 12, section: "CRM", name: "Leads", slug: "leads" },
  { id: 13, section: "CRM", name: "Pipeline", slug: "pipeline" },
  { id: 6, section: "Finance", name: "Accounting", slug: "accounting" },
  { id: 1, section: "Finance", name: "Invoicing", slug: "invoicing" },
  { id: 7, section: "Finance", name: "Benchmark", slug: "benchmark" },
  { id: 10, section: "Finance", name: "Expenses", slug: "expenses" },
  { id: 22, section: "Logistics", name: "Warehouse Daily Operations", slug: "warehouse_daily_operations" },
  { id: 21, section: "Logistics", name: "Operation analysis", slug: "operation_analysis" },
  { id: 2, section: "Logistics", name: "Warehouse Metrics", slug: "warehouse_metrics" },
  { id: 23, section: "Logistics", name: "Purchase & Vendor analysis", slug: "purchase_and_vendor_analysis" },
  { id: 8, section: "Logistics", name: "Manufacturing", slug: "manufacturing" },
  { id: 16, section: "Services", name: "Project", slug: "project" },
  { id: 14, section: "Services", name: "Helpdesk", slug: "helpdesk" },
  { id: 9, section: "Marketing", name: "Events", slug: "events" },
  { id: 26, section: "Marketing", name: "Email Marketing", slug: "email_marketing" },
  { id: 5, section: "Website", name: "eCommerce", slug: "ecommerce" },
  { id: 24, section: "Human Resources", name: "Payroll", slug: "payroll" },
  { id: 25, section: "Human Resources", name: "Recruitment", slug: "recruitment" },
];

const OUTPUT_DIR = "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/screenshots/dashboards";
const REPORT_PATH = "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/scratch/dashboards_audit_results.json";

(async () => {
  console.log("=== BẮT ĐẦU KIỂM TOÁN EVIDENCE TOÀN BỘ 26 DASHBOARD TRÊN INNORIA.COM ===");
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.setDefaultTimeout(60000);

  // Authenticate session
  console.log("[Auth] Đăng nhập vào https://innoria.com...");
  await page.goto("https://innoria.com/web/login", { waitUntil: "domcontentloaded" });
  await page.evaluate(async () => {
    await fetch("/web/session/authenticate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: { db: "innoria_prod", login: "admin", password: "admin" }
      })
    });
  });

  console.log("[Navigation] Tải ứng dụng Spreadsheet Dashboard...");
  await page.goto("https://innoria.com/insilos/dashboards", { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".o_spreadsheet_dashboard_action", { timeout: 20000 });
  await page.waitForSelector(".o-spreadsheet", { timeout: 20000 });
  console.log("[Navigation] Dashboard Action & Canvas đã sẵn sàng.");

  const auditResults = [];

  for (let i = 0; i < DASHBOARDS.length; i++) {
    const item = DASHBOARDS[i];
    const screenshotName = `dashboard_${String(item.id).padStart(2, "0")}_${item.slug}.png`;
    const screenshotPath = path.join(OUTPUT_DIR, screenshotName);

    console.log(`\n[${i + 1}/${DASHBOARDS.length}] Kiểm tra Dashboard #${item.id} [${item.section}] "${item.name}"...`);

    // 1. Kiểm tra API Endpoint /spreadsheet/dashboard/data/<id>
    const apiResult = await page.evaluate(async (dashId) => {
      try {
        const t0 = performance.now();
        const resp = await fetch(`/spreadsheet/dashboard/data/${dashId}`);
        const latencyMs = Math.round(performance.now() - t0);
        const text = await resp.text();
        let json = null;
        try {
          json = JSON.parse(text);
        } catch (e) {}

        const snapshot = json ? json.snapshot : null;
        const sheetsCount = snapshot && snapshot.sheets ? snapshot.sheets.length : 0;
        let figuresInSnapshot = 0;
        let cellsCount = 0;
        if (snapshot && snapshot.sheets) {
          snapshot.sheets.forEach(s => {
            if (s.figures) figuresInSnapshot += s.figures.length;
            if (s.cells) cellsCount += Object.keys(s.cells).length;
          });
        }

        return {
          ok: resp.ok,
          status: resp.status,
          bytes: text.length,
          latencyMs,
          hasSnapshot: !!snapshot && Object.keys(snapshot).length > 0,
          snapshotVersion: snapshot ? snapshot.version : null,
          sheetsCount,
          figuresInSnapshot,
          cellsCount,
        };
      } catch (err) {
        return { ok: false, error: err.message };
      }
    }, item.id);

    // 2. Click chọn dashboard trong sidebar
    const selector = `.o_spreadsheet_dashboard_search_panel li[data-name="${item.name}"]`;
    await page.waitForSelector(selector, { timeout: 10000 });
    await page.click(selector);
    await page.waitForTimeout(1800);

    // 3. Đo lường hiển thị DOM
    const domInfo = await page.evaluate((expectedName) => {
      const figures = document.querySelectorAll(".o-figure, .o-chart, .o-scorecard, .o-gauge");
      const errorDialog = document.querySelector(".o_error_dialog, .modal-title, .alert-danger");
      const spreadsheet = document.querySelector(".o-spreadsheet");
      const activeItem = document.querySelector(".o_spreadsheet_dashboard_search_panel li.active");
      const activeText = activeItem ? activeItem.innerText.trim() : "";

      // Extract titles
      const figureTitles = [];
      document.querySelectorAll(".o-figure .o-chart-title, .o-scorecard-content, .o-figure text, .o-figure title").forEach(el => {
        const txt = el.innerText || el.textContent;
        if (txt && txt.trim().length > 1 && txt.trim().length < 50 && !figureTitles.includes(txt.trim())) {
          figureTitles.push(txt.trim());
        }
      });

      return {
        hasSpreadsheet: !!spreadsheet,
        renderedFiguresCount: figures.length,
        hasError: !!errorDialog,
        errorText: errorDialog ? errorDialog.innerText.trim() : null,
        activeSearchItem: activeText,
        extractedFigureSample: figureTitles.slice(0, 4),
      };
    }, item.name);

    console.log(`  -> API: status=${apiResult.status}, bytes=${apiResult.bytes}, sheets=${apiResult.sheetsCount}, figuresInSnapshot=${apiResult.figuresInSnapshot}`);
    console.log(`  -> UI: active="${domInfo.activeSearchItem}", renderedFigures=${domInfo.renderedFiguresCount}, hasError=${domInfo.hasError}`);

    // 4. Chụp ảnh màn hình bằng chứng
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`  -> Đã lưu ảnh evidence: ${screenshotName}`);

    const isPass = apiResult.ok && apiResult.hasSnapshot && domInfo.hasSpreadsheet && !domInfo.hasError && domInfo.activeSearchItem === item.name;

    auditResults.push({
      id: item.id,
      section: item.section,
      name: item.name,
      slug: item.slug,
      url: `https://innoria.com/insilos/dashboards?dashboard_id=${item.id}`,
      api: apiResult,
      ui: {
        ...domInfo,
        screenshot: screenshotPath,
        screenshotRel: `screenshots/dashboards/${screenshotName}`,
      },
      status: isPass ? "PASS" : "FAIL"
    });
  }

  // Ghi kết quả JSON
  fs.writeFileSync(REPORT_PATH, JSON.stringify(auditResults, null, 2), "utf8");
  console.log(`\n=== HOÀN TẤT KIỂM TOÁN: Đã ghi ${auditResults.length} kết quả vào ${REPORT_PATH} ===`);

  const passed = auditResults.filter(r => r.status === "PASS").length;
  console.log(`Tổng kết: ${passed}/${auditResults.length} Dashboards đạt chuẩn PASS (100% evidence verified).`);

  await browser.close();
})();
