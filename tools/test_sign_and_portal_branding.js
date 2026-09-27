const { chromium } = require('playwright');
const http = require('http');
const assert = require('assert');

function fetchUrl(url) {
    return new Promise((resolve, reject) => {
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
        }).on('error', reject);
    });
}

async function main() {
    console.log("=== VERIFYING SIGN PORTAL, ASSETS & ILLUSTRATIONS BRANDING ===");

    // 1. Verify insilos_signed.png served via HTTP
    console.log("1. Checking insilos_signed.png...");
    const signRes = await fetchUrl('http://localhost:28069/sign/static/img/insilos_signed.png');
    assert.strictEqual(signRes.status, 200, "insilos_signed.png must return HTTP 200");
    console.log("  ✓ insilos_signed.png served HTTP 200 OK (size: " + signRes.headers['content-length'] + " bytes)");

    // 2. Verify Odoo_logo_O.svg contains canonical Insilos emblem
    console.log("2. Checking Odoo_logo_O.svg QR code emblem...");
    const qrRes = await fetchUrl('http://localhost:28069/account/static/src/img/Odoo_logo_O.svg');
    assert.strictEqual(qrRes.status, 200, "Odoo_logo_O.svg must return HTTP 200");
    assert.ok(qrRes.body.includes('#004455'), "Odoo_logo_O.svg must contain Insilos primary #004455");
    assert.ok(qrRes.body.includes('#FF8000'), "Odoo_logo_O.svg must contain Insilos accent #FF8000");
    console.log("  ✓ Odoo_logo_O.svg served HTTP 200 OK and contains canonical Insilos colors (#004455, #FF8000)");

    // 3. Verify Attendance Kiosk tablet-cam.svg has no legacy purple
    console.log("3. Checking Attendance Kiosk illustrations for legacy purple...");
    const camRes = await fetchUrl('http://localhost:28069/hr_attendance/static/img/tablet-cam.svg');
    assert.strictEqual(camRes.status, 200, "tablet-cam.svg must return HTTP 200");
    assert.ok(!camRes.body.includes('#714B67') && !camRes.body.includes('#714b67'), "tablet-cam.svg must not contain #714B67");
    assert.ok(camRes.body.includes('#004455'), "tablet-cam.svg must contain Insilos primary #004455");
    console.log("  ✓ Attendance Kiosk tablet-cam.svg is sanitized with #004455 (0 legacy purple)");

    // 4. Verify Stock replenishment.svg has no legacy purple
    console.log("4. Checking Stock replenishment illustration...");
    const repRes = await fetchUrl('http://localhost:28069/stock/static/img/replenishment.svg');
    assert.strictEqual(repRes.status, 200, "replenishment.svg must return HTTP 200");
    assert.ok(!repRes.body.includes('#875A7B') && !repRes.body.includes('#875a7b'), "replenishment.svg must not contain #875A7B");
    assert.ok(repRes.body.includes('#004455'), "replenishment.svg must contain Insilos primary #004455");
    console.log("  ✓ Stock replenishment.svg is sanitized with #004455 (0 legacy purple)");

    // 5. Verify Base Automation automation.svg has no legacy purple
    console.log("5. Checking Base Automation illustration...");
    const autoRes = await fetchUrl('http://localhost:28069/base_automation/static/img/automation.svg');
    assert.strictEqual(autoRes.status, 200, "automation.svg must return HTTP 200");
    assert.ok(!autoRes.body.includes('#714B67') && !autoRes.body.includes('#714b67'), "automation.svg must not contain #714B67");
    assert.ok(autoRes.body.includes('#004455'), "automation.svg must contain Insilos primary #004455");
    console.log("  ✓ Base Automation automation.svg is sanitized with #004455 (0 legacy purple)");

    // 6. Playwright check on browser rendering of jobs and document sign template
    console.log("6. Checking public jobs page via Playwright...");
    const browser = await chromium.launch({
        headless: true,
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('http://localhost:28069/jobs', { waitUntil: 'domcontentloaded', timeout: 30000 });
    const text = await page.evaluate(() => document.body.innerText || '');
    assert.ok(!/\bOdoo\b/.test(text), "Jobs page text must not contain 'Odoo'");
    console.log("  ✓ Jobs page renders cleanly with zero 'Odoo' references");

    await browser.close();
    console.log("\n🎉 ALL SIGN, ASSETS, AND ILLUSTRATION CHECKS PASSED 100%!");
}

main().catch(err => {
    console.error("Test failed:", err);
    process.exit(1);
});
