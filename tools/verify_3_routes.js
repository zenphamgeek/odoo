const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.setDefaultTimeout(30000);

  // Authenticate
  await page.goto("https://innoria.com/web/login", { waitUntil: "domcontentloaded" });
  await page.evaluate(async () => {
    await fetch("/web/session/authenticate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: { db: "innoria_prod", login: "admin", password: "admin" } })
    });
  });

  const testRoutes = [
    { name: "Knowledge", href: "/insilos/knowledge" },
    { name: "ESG", href: "/insilos/esg" },
    { name: "PP Manufacturing", href: "/insilos/manufacturing" }
  ];

  for (const r of testRoutes) {
    console.log(`Checking ${r.name} (${r.href})...`);
    await page.goto(`https://innoria.com${r.href}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    const res = await page.evaluate(() => {
      const err = document.querySelector(".o_error_dialog");
      const view = document.querySelector(".o_view_controller, .o_content, .o_knowledge_form_view, .o_esg_dashboard");
      return {
        hasError: Boolean(err),
        errorText: err ? err.innerText.slice(0, 200) : null,
        title: document.title,
        hasView: Boolean(view),
        classes: Array.from(document.body.classList).join(" ")
      };
    });
    console.log(`  Result for ${r.name}: hasError=${res.hasError}, hasView=${res.hasView}, title=${res.title}`);
    if (res.hasError) {
      console.log(`  Error text: ${res.errorText}`);
    }
    const safeName = r.name.toLowerCase().replace(/\s+/g, "_");
    await page.screenshot({ path: `/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/screenshots/verify_${safeName}.png` });
  }

  await browser.close();
  console.log("Done checking 3 routes.");
})();
