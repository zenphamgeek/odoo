const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const logs = [];
  page.on("console", msg => logs.push(`[${msg.type()}] ${msg.text()}`));
  page.on("pageerror", err => logs.push(`[PAGE_ERROR] ${err.message}`));

  console.log("=== 1. Auth on innoria.com ===");
  await page.goto("https://innoria.com/web/login", { waitUntil: "domcontentloaded" });
  const authRes = await page.evaluate(async () => {
    const res = await fetch("/web/session/authenticate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: { db: "innoria_prod", login: "admin", password: "admin" }
      })
    });
    return res.json();
  });
  console.log("Auth result uid:", authRes.result?.uid);

  console.log("=== 2. Navigate to /insilos/dashboards?dashboard_id=1 ===");
  await page.goto("https://innoria.com/insilos/dashboards?dashboard_id=1", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);

  const dashStyles = await page.evaluate(() => {
    const sp = document.querySelector(".o_spreadsheet_dashboard_search_panel");
    const cpSearch = document.querySelector(".o_sp_dashboard_search");
    const searchview = document.querySelector(".o_sp_dashboard_search .o_searchview");
    const cpSearchview = document.querySelector(".o_cp_searchview");
    const firstItem = document.querySelector(".o_search_panel_category_value");
    const toggleBtn = document.querySelector(".o_spreadsheet_dashboard_search_panel button");

    const getMetrics = el => {
      if (!el) return null;
      const cs = window.getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return {
        rect: { x: r.x, y: r.y, width: r.width, height: r.height, left: r.left, right: r.right },
        width: cs.width,
        minWidth: cs.minWidth,
        maxWidth: cs.maxWidth,
        padding: cs.padding,
        margin: cs.margin,
        overflow: cs.overflow,
        overflowX: cs.overflowX,
        border: cs.border,
        boxShadow: cs.boxShadow,
      };
    };

    return {
      searchPanel: getMetrics(sp),
      firstItem: getMetrics(firstItem),
      toggleBtn: getMetrics(toggleBtn),
      cpSearch: getMetrics(cpSearch),
      cpSearchview: getMetrics(cpSearchview),
      searchview: getMetrics(searchview),
      spHtmlSample: sp ? sp.outerHTML.substring(0, 300) : null,
      cpHtmlSample: cpSearchview ? cpSearchview.outerHTML.substring(0, 300) : null,
    };
  });
  console.log("Dashboard UI Metrics:\n", JSON.stringify(dashStyles, null, 2));

  console.log("=== 3. Navigate to /insilos/contacts ===");
  logs.length = 0;
  await page.goto("https://innoria.com/insilos/contacts", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);

  console.log("URL after /insilos/contacts:", page.url());
  const contactsReport = await page.evaluate(() => {
    const errorDialog = document.querySelector(".o_error_dialog");
    const notification = document.querySelector(".o_notification_manager");
    const view = document.querySelector(".o_view_controller, .o_list_view, .o_kanban_view, .o_form_view");
    const breadcrumb = document.querySelector(".breadcrumb")?.innerText;
    const bodyClasses = document.body.className;
    const homeMenu = document.querySelector(".o_home_menu");
    return {
      hasErrorDialog: !!errorDialog,
      errorDialogText: errorDialog?.innerText,
      notificationText: notification?.innerText,
      hasView: !!view,
      viewClass: view?.className,
      breadcrumb,
      bodyClasses,
      isHomeMenuVisible: homeMenu ? window.getComputedStyle(homeMenu).display !== "none" : false,
      title: document.title,
    };
  });
  console.log("Contacts Report:\n", JSON.stringify(contactsReport, null, 2));
  console.log("Contacts Console logs:", logs);

  await page.screenshot({ path: "/tmp/contacts_innoria_debug.png" });

  console.log("=== 4. Inspecting App Drawer / Apps Menu ===");
  // Open apps menu or fetch apps list from session_info
  const apps = await page.evaluate(() => {
    const userContext = window.odoo?.info || window.__odoo__session_info__;
    const homeMenu = document.querySelector(".o_home_menu");
    const appsMenuItems = Array.from(document.querySelectorAll(".o_app, .o_home_menu .o_menuitem")).map(el => ({
      name: el.innerText.trim(),
      href: el.getAttribute("href"),
      dataMenuXmlid: el.getAttribute("data-menu-xmlid"),
      dataActionId: el.getAttribute("data-action-id"),
    }));
    return {
      appsMenuItems,
    };
  });
  console.log("Apps menu items count:", apps.appsMenuItems.length);
  if (apps.appsMenuItems.length > 0) {
    console.log("First 10 apps:", apps.appsMenuItems.slice(0, 10));
  }

  await browser.close();
})();
