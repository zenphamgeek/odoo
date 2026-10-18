#!/usr/bin/env node
/**
 * Master Live Browser Playwright E2E QA Verification Suite
 * ========================================================
 * Verifies 5 complete End-to-End Customer & Employee User Journeys against live local Odoo 20 servers:
 *   - Journey 1: Public Website Routes (/, /platform, /solutions, /industries, /about, /pricing, /contactus),
 *                Header Navigation Uniqueness, IBM Carbon v11 Geometry & Poppins Sans-Serif Typography.
 *   - Journey 2: Public AI Concierge End-to-End Flow (Catalog -> Estimate -> Grounded RAG Query -> Health/Telemetry).
 *   - Journey 3: Authenticated Backend Login & HomeMenu Employee Self-Service Hub (.o_insilos_emp_dashboard),
 *                Dual-Theme Single Launcher Logo Invariant & ISO/IEC 27701 Default PII Masking.
 *   - Journey 4: Documents Multi-Level Tree & View Switcher E2E (/odoo/documents).
 *   - Journey 5: CRM Pipeline & Full-Width Form Sheet E2E (/odoo/crm) + innoria_prod (http://localhost:28070) Smoke.
 */

const { chromium } = require("playwright");

const DEV_URL = process.env.ODOO_DEV_URL || "http://localhost:28069";
const PROD_URL = process.env.ODOO_PROD_URL || "http://localhost:28070";
const ODOO_DB = process.env.ODOO_DB || "insilos20_dev";
const ODOO_LOGIN = process.env.ODOO_LOGIN || "admin";
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || "admin";

function assert(condition, message) {
    if (!condition) {
        throw new Error(`ASSERTION FAILED: ${message}`);
    }
}

(async () => {
    console.log("================================================================================");
    console.log("🚀 STARTING MASTER PLAYWRIGHT LIVE BROWSER E2E QA SUITE (5 USER JOURNEYS)");
    console.log(`   • Target Dev Server : ${DEV_URL} (${ODOO_DB})`);
    console.log(`   • Target Prod Server: ${PROD_URL} (innoria_prod)`);
    console.log("================================================================================\n");

    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });

    const uncaughtErrors = [];

    try {
        // =========================================================================
        // JOURNEY 1 & 2: Public Website & AI Concierge Context (Unauthenticated)
        // =========================================================================
        const pubContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        const pubPage = await pubContext.newPage();
        pubPage.setDefaultTimeout(60000);

        console.log("[Journey 1/5] Public Website Routes, Header Navigation Uniqueness, IBM Carbon v11 & Poppins Typography...");
        const publicRoutes = ["/", "/platform", "/solutions", "/industries", "/about", "/pricing", "/contactus"];

        for (const route of publicRoutes) {
            const fullUrl = `${DEV_URL}${route}`;
            const response = await pubPage.goto(fullUrl, { waitUntil: "domcontentloaded" });
            const status = response ? response.status() : 0;
            assert(status === 200, `Expected HTTP 200 on ${fullUrl}, got ${status}`);

            const routeAudit = await pubPage.evaluate(() => {
                const header = document.querySelector("header");
                const brandImg = header ? header.querySelector(".navbar-brand img, .logo img, img") : null;
                const logoSrc = brandImg ? brandImg.getAttribute("src") || "" : "";

                // Collect top-level visible nav links inside #top_menu (excluding dropdown toggle '#' anchors)
                const navLinks = Array.from(
                    document.querySelectorAll("header #top_menu > li > a.nav-link, header .navbar-nav > li > a.nav-link")
                ).filter((a) => {
                    const style = window.getComputedStyle(a);
                    return style.display !== "none" && style.visibility !== "hidden" && a.offsetWidth > 0;
                });

                const hrefs = navLinks
                    .map((a) => (a.getAttribute("href") || "").trim())
                    .filter((h) => h && h !== "#" && !h.startsWith("javascript:"));

                const seen = new Set();
                const duplicates = [];
                for (const h of hrefs) {
                    if (seen.has(h)) {
                        duplicates.push(h);
                    }
                    seen.add(h);
                }

                const bodyFont = window.getComputedStyle(document.body).fontFamily || "";

                // Primary CTA button check
                const primaryBtn =
                    document.querySelector("main .btn-primary, #wrap .btn-primary, .s_call_to_action .btn-primary, header .btn-primary");
                const ctaBorderRadius = primaryBtn ? window.getComputedStyle(primaryBtn).borderRadius : null;

                return {
                    logoSrc,
                    navCount: hrefs.length,
                    hrefs,
                    duplicates,
                    bodyFont,
                    ctaBorderRadius,
                };
            });

            assert(
                routeAudit.logoSrc.includes("logo_innoria_header.svg"),
                `Route ${route}: Expected header brand logo 'logo_innoria_header.svg', got '${routeAudit.logoSrc}'`
            );
            assert(
                routeAudit.duplicates.length === 0,
                `Route ${route}: Found duplicate header nav hrefs: ${JSON.stringify(routeAudit.duplicates)} (all: ${JSON.stringify(routeAudit.hrefs)})`
            );
            assert(
                routeAudit.bodyFont.toLowerCase().includes("poppins"),
                `Route ${route}: Expected computed body fontFamily to include 'Poppins', got '${routeAudit.bodyFont}'`
            );

            if (route === "/") {
                assert(
                    routeAudit.ctaBorderRadius === "0px",
                    `Route /: Expected IBM Carbon v11 primary CTA borderRadius === '0px', got '${routeAudit.ctaBorderRadius}'`
                );
            }

            console.log(
                `   ✓ ${route.padEnd(12)} -> HTTP ${status} | Logo: logo_innoria_header.svg | Nav links: ${routeAudit.navCount} (0 dupes) | Font: Poppins | CTA radius: ${routeAudit.ctaBorderRadius}`
            );
        }
        console.log("✅ [Journey 1/5] PASSED!\n");

        // =========================================================================
        // JOURNEY 2: Public AI Concierge End-to-End Flow
        // =========================================================================
        console.log("[Journey 2/5] Public AI Concierge End-to-End Flow (Catalog -> Estimate -> Grounded RAG Query -> Health)...");
        await pubPage.goto(`${DEV_URL}/`, { waitUntil: "domcontentloaded" });

        // Step 2a: Fetch /innoria/ai_concierge/services_catalog
        const catalogRes = await pubPage.evaluate(async () => {
            const r = await fetch("/innoria/ai_concierge/services_catalog", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
            });
            return await r.json();
        });
        const catalogData = catalogRes.result || {};
        assert(catalogData.status === "ok" && catalogData.success === true, `Catalog failed: ${JSON.stringify(catalogRes)}`);
        assert(
            Array.isArray(catalogData.services) && catalogData.services.length === 6,
            `Expected 6 service pillars in catalog, got ${(catalogData.services || []).length}`
        );
        assert(
            Array.isArray(catalogData.catalog_skus) && catalogData.catalog_skus.length > 0,
            `Expected non-empty catalog_skus`
        );
        assert(typeof catalogData.pct_token === "string" && catalogData.pct_token.length > 10, "Missing AB-PCT capability token");
        console.log(
            `   ✓ Step 2a (services_catalog): ${catalogData.services.length} service pillars, ${catalogData.catalog_skus.length} SKUs, PCT token issued`
        );

        // Step 2b: Call /innoria/ai_concierge/estimate_service
        const estimateRes = await pubPage.evaluate(async () => {
            const r = await fetch("/innoria/ai_concierge/estimate_service", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        service_code: "sw_squad",
                        service_type: "sw_squad",
                        scale_tier: "growth",
                        units: 4,
                        squad_size: 4,
                        duration_months: 6,
                    },
                }),
            });
            return await r.json();
        });
        const estimateData = estimateRes.result || {};
        assert(estimateData.status === "ok" && estimateData.success === true, `Estimate failed: ${JSON.stringify(estimateRes)}`);
        const totalVnd = estimateData.estimated_total_vnd || estimateData.total_vnd || 0;
        assert(totalVnd > 0, `Expected estimated_total_vnd > 0, got ${totalVnd}`);
        assert(
            typeof estimateData.pricing_token === "string" && estimateData.pricing_token.includes("."),
            `Expected ESIH pricing_token signature, got ${estimateData.pricing_token}`
        );
        console.log(
            `   ✓ Step 2b (estimate_service): sw_squad (4 eng × 6 mos) -> ${estimateData.formatted_total_vnd} (${totalVnd} VND) | ESIH token verified`
        );

        // Step 2c: Call /innoria/ai_concierge/query
        const queryRes = await pubPage.evaluate(async () => {
            const r = await fetch("/innoria/ai_concierge/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        query: "Tư vấn dịch vụ phát triển phần mềm và báo giá ERP",
                        lang: "vi",
                    },
                }),
            });
            return await r.json();
        });
        const queryData = queryRes.result || {};
        assert(queryData.success === true, `RAG Query failed: ${JSON.stringify(queryRes)}`);
        assert(
            typeof queryData.answer === "string" && queryData.answer.trim().length > 20,
            `Expected non-empty grounded answer, got '${queryData.answer}'`
        );
        assert(
            Array.isArray(queryData.citations) && queryData.citations.length > 0,
            `Expected grounded citations array, got ${JSON.stringify(queryData.citations)}`
        );
        console.log(
            `   ✓ Step 2c (query): Grounded answer (${queryData.answer.length} chars) with ${queryData.citations.length} citations`
        );

        // Step 2d: Call /innoria/ai_concierge/health
        const healthRes = await pubPage.evaluate(async () => {
            const r = await fetch("/innoria/ai_concierge/health", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
            });
            return await r.json();
        });
        const healthData = healthRes.result || {};
        assert(
            healthData.status === "ok" || healthData.status === "healthy",
            `Expected health status 'ok'/'healthy', got ${JSON.stringify(healthData)}`
        );
        assert(healthData.esih_pricing_attestation === "active", "Expected esih_pricing_attestation === 'active'");
        console.log(
            `   ✓ Step 2d (health): status=${healthData.status}, rag_chunks_active=${healthData.rag_chunks_active}, esih=${healthData.esih_pricing_attestation}`
        );
        console.log("✅ [Journey 2/5] PASSED!\n");

        await pubContext.close();

        // =========================================================================
        // JOURNEY 3, 4, 5: Authenticated Backend Context
        // =========================================================================
        const authContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        await authContext.addCookies([
            { name: "color_scheme", value: "light", domain: "localhost", path: "/" },
        ]);
        const page = await authContext.newPage();
        page.setDefaultTimeout(60000);

        page.on("pageerror", (err) => {
            const msg = String(err && err.message ? err.message : err);
            uncaughtErrors.push(msg);
        });

        console.log("[Journey 3/5] Authenticated Backend Login & HomeMenu Employee Self-Service Hub (.o_insilos_emp_dashboard)...");
        await page.goto(`${DEV_URL}/web/login`, { waitUntil: "domcontentloaded" });
        const authResult = await page.evaluate(
            async ({ db, login, password }) => {
                localStorage.setItem("insilos_theme", "light");
                document.cookie = "color_scheme=light; path=/; max-age=31536000; SameSite=Lax";
                const res = await fetch("/web/session/authenticate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: { db, login, password },
                    }),
                });
                return await res.json();
            },
            { db: ODOO_DB, login: ODOO_LOGIN, password: ODOO_PASSWORD }
        );
        assert(
            authResult && authResult.result && authResult.result.uid,
            `Authentication failed on ${DEV_URL}: ${JSON.stringify(authResult)}`
        );

        await page.goto(`${DEV_URL}/odoo`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_main_navbar, .o_navbar", { timeout: 60000 });
        await page.waitForSelector(".o_insilos_emp_dashboard", { timeout: 60000 });
        await page.waitForTimeout(1000);

        const homeAudit = await page.evaluate(() => {
            const dash = document.querySelector(".o_insilos_emp_dashboard");
            const dashVisible = dash ? dash.offsetWidth > 0 && dash.offsetHeight > 0 : false;
            const dashText = dash ? dash.innerText : "";

            const lightLogo = document.querySelector(".o_insilos_launcher_icon_light");
            const darkLogo = document.querySelector(".o_insilos_launcher_icon_dark");
            const lightDisplay = lightLogo ? window.getComputedStyle(lightLogo).display : "none";
            const darkDisplay = darkLogo ? window.getComputedStyle(darkLogo).display : "none";

            const activeLogos = [
                { name: "light", display: lightDisplay },
                { name: "dark", display: darkDisplay },
            ].filter((l) => l.display !== "none");

            return {
                dashVisible,
                hasEmployeeInfo:
                    dashText.includes("DGM-") ||
                    dashText.includes("Lê Xuân Hoàng") ||
                    dashText.includes("BHXH") ||
                    dashText.includes("TZ0857G"),
                visibleLogoCount: activeLogos.length,
                lightDisplay,
                darkDisplay,
            };
        });

        assert(homeAudit.dashVisible, "Expected .o_insilos_emp_dashboard to be visible on /odoo");
        assert(homeAudit.hasEmployeeInfo, "Expected .o_insilos_emp_dashboard to display employee profile/contract/payroll cards");
        assert(
            homeAudit.visibleLogoCount === 1 && homeAudit.lightDisplay !== "none" && homeAudit.darkDisplay === "none",
            `Expected exactly 1 visible navbar launcher logo in Light Mode (.o_insilos_launcher_icon_light visible, .o_insilos_launcher_icon_dark hidden), got count=${homeAudit.visibleLogoCount} (light=${homeAudit.lightDisplay}, dark=${homeAudit.darkDisplay})`
        );

        // Verify /insilos/employee_dashboard/data default PII masking per ISO/IEC 27701
        const empDataRes = await page.evaluate(async () => {
            const r = await fetch("/insilos/employee_dashboard/data", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
            });
            return await r.json();
        });
        const empPayload = empDataRes.result || {};
        const currEmp = empPayload.current_employee || {};
        assert(currEmp && currEmp.registration_number, `Missing current_employee in /insilos/employee_dashboard/data`);
        assert(
            String(currEmp.identification_id || "").includes("*"),
            `Expected identification_id to be masked with '*', got '${currEmp.identification_id}'`
        );
        assert(
            String(currEmp.work_phone || "").includes("*"),
            `Expected work_phone to be masked with '*', got '${currEmp.work_phone}'`
        );
        assert(
            String(currEmp.bank_acc_number || "").includes("*"),
            `Expected bank_acc_number to be masked with '*', got '${currEmp.bank_acc_number}'`
        );
        console.log(
            `   ✓ HomeMenu (.o_insilos_emp_dashboard) visible | Single Light Logo (dark=none) | Masked PII: CCCD=${currEmp.identification_id}, Phone=${currEmp.work_phone}, Bank=${currEmp.bank_acc_number}`
        );
        console.log("✅ [Journey 3/5] PASSED!\n");

        // =========================================================================
        // JOURNEY 4: Documents Multi-Level Tree & View Switcher E2E (/odoo/documents)
        // =========================================================================
        console.log("[Journey 4/5] Documents Multi-Level Tree & View Switcher E2E (/odoo/documents)...");
        await page.goto(`${DEV_URL}/odoo/documents`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_search_panel", { timeout: 60000 });
        await page.waitForSelector(".o_content", { timeout: 60000 });
        await page.waitForTimeout(1500);

        const docsTreeAudit = await page.evaluate(() => {
            const sp = document.querySelector(".o_search_panel");
            const spText = sp ? sp.innerText : "";
            const labels = Array.from(
                document.querySelectorAll(".o_search_panel .o_search_panel_label_title, .o_search_panel .o_search_panel_value")
            ).map((el) => (el.textContent || "").trim());
            return {
                found: !!sp,
                labelCount: labels.length,
                hasCompanyOrTree:
                    spText.includes("Company") ||
                    spText.includes("COMPANY") ||
                    spText.includes("DGM") ||
                    spText.includes("INNO") ||
                    labels.length >= 2,
                sampleLabels: labels.slice(0, 8),
            };
        });

        assert(docsTreeAudit.found && docsTreeAudit.hasCompanyOrTree, `Documents search panel tree missing folders: ${JSON.stringify(docsTreeAudit)}`);
        console.log(
            `   ✓ Documents .o_search_panel rendered (${docsTreeAudit.labelCount} nodes, sample: ${docsTreeAudit.sampleLabels.slice(0, 5).join(", ")})`
        );

        // Click view switcher buttons (List <-> Kanban) if present, re-querying after OWL ControlPanel re-render
        const hasSwitchers = await page.evaluate(() => {
            return !!(document.querySelector(".o_switch_view.o_list") && document.querySelector(".o_switch_view.o_kanban"));
        });
        if (hasSwitchers) {
            await page.click(".o_switch_view.o_list");
            await page.waitForSelector(".o_switch_view.o_kanban", { timeout: 15000 });
            await page.waitForTimeout(800);
            await page.click(".o_switch_view.o_kanban");
            await page.waitForSelector(".o_switch_view.o_list", { timeout: 15000 });
            await page.waitForTimeout(800);
            console.log("   ✓ Switched Documents view List (.o_switch_view.o_list) <-> Kanban (.o_switch_view.o_kanban) cleanly");
        } else {
            console.log("   ✓ Documents view active and stable");
        }

        const frozenPropErrors = uncaughtErrors.filter(
            (e) => e.includes("Cannot set property state") || e.includes("Object is not extensible")
        );
        assert(
            frozenPropErrors.length === 0,
            `Uncaught OWL reactive props error during Documents view switch: ${JSON.stringify(frozenPropErrors)}`
        );
        console.log("✅ [Journey 4/5] PASSED!\n");

        // =========================================================================
        // JOURNEY 5: CRM Pipeline & Full-Width Form Sheet E2E (/odoo/crm) + innoria_prod Smoke
        // =========================================================================
        console.log("[Journey 5/5] CRM Pipeline & Full-Width Form Sheet E2E (/odoo/crm) + innoria_prod (http://localhost:28070) Smoke...");
        await page.goto(`${DEV_URL}/odoo/crm`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector(".o_control_panel", { timeout: 60000 });
        await page.waitForSelector(".o_content", { timeout: 60000 });

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
                        kwargs: { limit: 1 },
                    },
                }),
            });
            const data = await res.json();
            return (data.result && data.result[0]) || null;
        });

        if (leadId) {
            await page.goto(`${DEV_URL}/odoo/crm/${leadId}`, { waitUntil: "domcontentloaded" });
        } else {
            await page.goto(`${DEV_URL}/odoo/crm/new`, { waitUntil: "domcontentloaded" });
        }
        try {
            await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 20000 });
        } catch (e) {
            await page.goto(`${DEV_URL}/web#id=${leadId || 1}&model=crm.lead&view_type=form`, {
                waitUntil: "domcontentloaded",
            });
            await page.waitForSelector(".o_form_view .o_form_sheet", { timeout: 30000 });
        }
        await page.waitForTimeout(1000);

        const crmFormAudit = await page.evaluate(() => {
            const sheet = document.querySelector(".o_form_sheet");
            if (!sheet) return { found: false };
            const rect = sheet.getBoundingClientRect();
            const cs = window.getComputedStyle(sheet);
            const m = (cs.backgroundColor || "").match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
            const r = m ? parseInt(m[1], 10) : 255;
            const g = m ? parseInt(m[2], 10) : 255;
            const b = m ? parseInt(m[3], 10) : 255;
            return {
                found: true,
                width: Math.round(rect.width),
                bgColor: cs.backgroundColor,
                isLightSurface: r > 220 && g > 220 && b > 220,
            };
        });

        assert(crmFormAudit.found, "CRM .o_form_sheet not found");
        assert(
            crmFormAudit.width > 900,
            `Expected CRM .o_form_sheet full-width (> 900px), got ${crmFormAudit.width}px`
        );
        assert(
            crmFormAudit.isLightSurface,
            `Expected CRM .o_form_sheet clean Light Mode surface, got ${crmFormAudit.bgColor}`
        );
        console.log(
            `   ✓ CRM Form Sheet (.o_form_sheet) width=${crmFormAudit.width}px (> 900px) | bgColor=${crmFormAudit.bgColor}`
        );

        // Verify innoria_prod (http://localhost:28070) public homepage & AI Concierge endpoint in clean context
        const prodContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        const prodPage = await prodContext.newPage();
        const prodResp = await prodPage.goto(`${PROD_URL}/`, { waitUntil: "domcontentloaded" });
        const prodStatus = prodResp ? prodResp.status() : 0;
        assert(prodStatus === 200, `Expected HTTP 200 on ${PROD_URL}/, got ${prodStatus}`);

        const prodAudit = await prodPage.evaluate(async () => {
            const header = document.querySelector("header");
            const brandImg = header ? header.querySelector(".navbar-brand img, .logo img, img") : null;
            const logoSrc = brandImg ? brandImg.getAttribute("src") || "" : "";
            const bodyFont = window.getComputedStyle(document.body).fontFamily || "";

            let healthResult = null;
            try {
                const hr = await fetch("/innoria/ai_concierge/health", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
                });
                const text = await hr.text();
                if (text.trim().startsWith("{")) {
                    const hJson = JSON.parse(text);
                    healthResult = hJson.result || null;
                }
            } catch (e) {
                // fallback to query endpoint
            }

            if (!healthResult || (!healthResult.status && !healthResult.success)) {
                const qr = await fetch("/innoria/ai_concierge/query", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: { query: "Tư vấn giải pháp ERP Innoria", lang: "vi" },
                    }),
                });
                const qJson = await qr.json();
                const qRes = qJson.result || {};
                healthResult = {
                    status: qRes.success ? "ok" : "error",
                    success: !!qRes.success,
                    answerLength: (qRes.answer || "").length,
                };
            }

            return {
                logoSrc,
                bodyFont,
                health: healthResult || {},
            };
        });

        assert(
            prodAudit.logoSrc.includes("logo_innoria_header.svg"),
            `innoria_prod (${PROD_URL}): Expected 'logo_innoria_header.svg', got '${prodAudit.logoSrc}'`
        );
        assert(
            prodAudit.bodyFont.toLowerCase().includes("poppins"),
            `innoria_prod (${PROD_URL}): Expected 'Poppins' font, got '${prodAudit.bodyFont}'`
        );
        assert(
            prodAudit.health.status === "ok" || prodAudit.health.status === "healthy" || prodAudit.health.success === true,
            `innoria_prod (${PROD_URL}): Expected AI Concierge status 'ok', got ${JSON.stringify(prodAudit.health)}`
        );
        console.log(
            `   ✓ innoria_prod (${PROD_URL}) -> HTTP ${prodStatus} | Logo: logo_innoria_header.svg | Font: Poppins | AI Concierge: ${prodAudit.health.status}`
        );
        await prodContext.close();
        console.log("✅ [Journey 5/5] PASSED!\n");

        await authContext.close();
        await browser.close();

        console.log("================================================================================");
        console.log("🎉 ALL 5 LIVE BROWSER E2E QA MASTER JOURNEYS PASSED 100% (EXIT CODE 0)!");
        console.log("================================================================================");
        process.exit(0);
    } catch (err) {
        console.error("\n❌ E2E QA SUITE FAILED:", err && err.stack ? err.stack : err);
        await browser.close();
        process.exit(1);
    }
})();
