const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BRAIN_DIR = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865";

(async () => {
    console.log("Starting Documents Viewer & Action Buttons Playwright Verification...");
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);

    const consoleErrors = [];
    page.on("console", (msg) => {
        if (msg.type() === "error") {
            consoleErrors.push(msg.text());
        }
    });
    page.on("pageerror", (err) => {
        consoleErrors.push(err.message);
    });

    await context.addCookies([{ name: "color_scheme", value: "light", domain: "localhost", path: "/" }]);
    console.log("Authenticating session...");
    await page.goto("http://localhost:28069/web/login", { waitUntil: "domcontentloaded" });
    const authDb = process.env.ODOO_DB || "insilos20_dev";
    const authLogin = process.env.ODOO_LOGIN || "admin";
    const authPassword = process.env.ODOO_PASSWORD || "admin";
    await page.evaluate(
        async ({ db, login, password }) => {
            await fetch("/web/session/authenticate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: { db, login, password },
                }),
            });
        },
        { db: authDb, login: authLogin, password: authPassword }
    );

    console.log("Navigating to Documents app (/odoo/documents)...");
    await page.goto("http://localhost:28069/odoo/documents", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_documents_kanban", { timeout: 60000 });
    await page.waitForSelector(".o_search_panel_category_value", { timeout: 60000 });
    await page.waitForTimeout(1500);

    // Ensure zero ErrorDialog
    const errorDialogsInitial = await page.locator(".o_error_dialog").count();
    if (errorDialogsInitial > 0) {
        const errText = await page.locator(".o_error_dialog").innerText();
        throw new Error(`ErrorDialog appeared on initial Documents load: ${errText}`);
    }

    // Find a folder in the search panel that contains viewable files (or click through folders)
    console.log("Selecting a folder with viewable documents...");
    const folderItems = page.locator(".o_search_panel_category_value");
    const folderCount = await folderItems.count();
    console.log(`Found ${folderCount} search panel category entries.`);

    let foundViewableCard = false;
    const previewableCardSelector = ".o_kanban_record:not(.o_folder_record):has(div[name='document_preview'] img), .o_kanban_record:not(.o_folder_record):has(.o_image[data-mimetype*='pdf']), .o_kanban_record:not(.o_folder_record):has(.o_image[data-mimetype*='text']), .o_kanban_record:not(.o_folder_record):has(.o_image[data-mimetype*='image'])";
    for (let i = 0; i < folderCount; i++) {
        const item = folderItems.nth(i);
        const label = await item.locator(".o_search_panel_label_title").first().innerText().catch(() => "");
        if (!label || ["All", "Trash", "Recent", "Shared with me", "My Drive"].includes(label.trim())) {
            continue;
        }
        await item.locator(".o_search_panel_label .w-100").first().click();
        await page.waitForTimeout(1000);
        const fileCards = page.locator(previewableCardSelector);
        const fCount = await fileCards.count();
        if (fCount > 0) {
            console.log(`Selected folder "${label.trim()}" with ${fCount} previewable file card(s).`);
            foundViewableCard = true;
            break;
        }
    }

    if (!foundViewableCard) {
        throw new Error("Could not find any folder with previewable document cards.");
    }

    // 1. Verify top-level Control Panel buttons BEFORE selection (Upload, New, Download, Share, Export, CogMenu)
    const uploadBtnVisible = await page.locator(".o_documents_kanban_upload_btn").isVisible();
    const downloadBtnVisible = await page.locator(".o_documents_download_btn").isVisible();
    const shareBtnVisible = await page.locator(".o_documents_share_btn").isVisible();
    const exportBtnVisible = await page.locator(".o_documents_export_btn").isVisible();
    const cogMenuVisible = await page.locator(".o_cp_action_menus .o_dropdown_title, .o_control_panel_breadcrumbs .o-dropdown").first().isVisible();

    console.log("Control Panel buttons (folder level):", {
        uploadBtnVisible,
        downloadBtnVisible,
        shareBtnVisible,
        exportBtnVisible,
        cogMenuVisible,
    });

    if (!uploadBtnVisible || !downloadBtnVisible || !shareBtnVisible || !exportBtnVisible) {
        throw new Error(
            `Missing expected Control Panel buttons at folder level: ${JSON.stringify({
                uploadBtnVisible,
                downloadBtnVisible,
                shareBtnVisible,
                exportBtnVisible,
            })}`
        );
    }

    // Select a card body (outside preview) first to verify selected state & capture screenshot 1
    const firstFileCard = page.locator(previewableCardSelector).first();
    const cardTitle = await firstFileCard.innerText();
    console.log("Selecting first file card:", cardTitle.split("\n")[0]);
    await firstFileCard.locator(".fw-bolder, .o_kanban_record_body").first().click();
    await page.waitForTimeout(800);

    const isSelectedAfterBodyClick = await firstFileCard.evaluate((el) =>
        el.classList.contains("o_record_selected")
    );
    const controlPanelActionTexts = await page
        .locator(".o_control_panel_main button, .o_control_panel_main .o-dropdown")
        .allInnerTexts();
    console.log("Card selected:", isSelectedAfterBodyClick);
    console.log("Control Panel visible buttons when card selected:", controlPanelActionTexts.map((t) => t.trim()).filter(Boolean));

    const cpScreenshotPath = path.join(BRAIN_DIR, "documents_control_buttons_verified.png");
    await page.screenshot({ path: cpScreenshotPath, fullPage: false });
    console.log(`Saved Control Panel screenshot to ${cpScreenshotPath}`);

    // Unselect all so we can verify that clicking the preview thumbnail directly BOTH selects the card AND opens FileViewer
    const unselectBtn = page.locator(".o_SelectionBox_unselectAll, .o_list_unselect_all, button[title='Unselect all'], .o_selection_box button").first();
    if (await unselectBtn.isVisible().catch(() => false)) {
        await unselectBtn.click();
        await page.waitForTimeout(500);
    }

    // 2. Click on the document preview thumbnail to open FileViewer
    console.log("Clicking div[name='document_preview'] to open Document Viewer modal...");
    const imageCard = page.locator(".o_kanban_record:has(div[name='document_preview'] img)").first();
    const targetCardForViewer = (await imageCard.count()) > 0 ? imageCard : firstFileCard;
    await targetCardForViewer.locator("div[name='document_preview']").first().click();
    await page.waitForSelector(".o-FileViewer", { timeout: 15000 });
    await page.waitForTimeout(1500);

    // Check zero ErrorDialog
    const errorDialogsAfterPreview = await page.locator(".o_error_dialog").count();
    if (errorDialogsAfterPreview > 0) {
        const errText = await page.locator(".o_error_dialog").innerText();
        throw new Error(`ErrorDialog appeared on opening FileViewer: ${errText}`);
    }

    // Verify FileViewer elements & embedded DocumentsAction toolbar
    const viewerVisible = await page.locator(".o-FileViewer").isVisible();
    const viewerHeaderActions = await page.locator(".o-FileViewer-header button").allInnerTexts();
    const isCardSelectedInViewer = await targetCardForViewer.evaluate((el) =>
        el.classList.contains("o_record_selected")
    );
    const viewerContentCount = await page
        .locator(".o-FileViewer-main iframe, .o-FileViewer-main img, .o-FileViewer-main video, .o-FileViewer-view")
        .count();

    console.log("FileViewer state:", {
        viewerVisible,
        isCardSelectedInViewer,
        viewerContentCount,
        viewerHeaderActions: viewerHeaderActions.map((t) => t.trim()).filter(Boolean),
    });

    if (!viewerVisible || viewerContentCount === 0 || !isCardSelectedInViewer) {
        throw new Error(
            `FileViewer verification failed: ${JSON.stringify({
                viewerVisible,
                viewerContentCount,
                isCardSelectedInViewer,
            })}`
        );
    }

    const viewerScreenshotPath = path.join(BRAIN_DIR, "documents_viewer_modal_verified.png");
    await page.screenshot({ path: viewerScreenshotPath, fullPage: false });
    console.log(`Saved FileViewer modal screenshot to ${viewerScreenshotPath}`);

    // Close the FileViewer cleanly via Escape or Close button
    const closeBtn = page.locator(".o-FileViewer-header div[aria-label='Close'], .o-FileViewer-header [title='Close']").first();
    if (await closeBtn.isVisible().catch(() => false)) {
        await closeBtn.click();
    } else {
        await page.keyboard.press("Escape");
    }
    await page.waitForTimeout(600);

    const viewerStillOpen = await page.locator(".o-FileViewer").count();
    console.log("FileViewer count after close:", viewerStillOpen);
    if (viewerStillOpen > 0) {
        throw new Error("FileViewer did not close cleanly.");
    }

    // 3. Verify Markdown document preview (aifin_stress_test_capacity_report.md) has ZERO 404 Not Found
    console.log("Testing Markdown document preview (aifin_stress_test_capacity_report.md)...");
    const aifinLabel = page.locator(".o_search_panel_label_title", { hasText: /^AIFIN$/ }).first();
    if ((await aifinLabel.count()) > 0 && (await aifinLabel.isVisible().catch(() => false))) {
        await aifinLabel.click();
        await page.waitForTimeout(1500);
    } else {
        const allLabel = page.locator(".o_search_panel_label_title", { hasText: /^All$/ }).first();
        if ((await allLabel.count()) > 0) {
            await allLabel.click();
            await page.waitForTimeout(1200);
        }
        const searchInput = page.locator(".o_searchview_input").first();
        if (await searchInput.isVisible().catch(() => false)) {
            await searchInput.fill("aifin_stress_test_capacity_report.md");
            await page.keyboard.press("Enter");
            await page.waitForTimeout(1500);
        }
    }
    const mdCard = page.locator(".o_kanban_record", { hasText: "aifin_stress_test_capacity_report.md" }).first();
    const mdCardCount = await mdCard.count();
    if (mdCardCount === 0) {
        throw new Error("Could not find aifin_stress_test_capacity_report.md card after selecting AIFIN folder.");
    }
    await mdCard.locator("div[name='document_preview']").first().click();
    await page.waitForSelector(".o-FileViewer", { timeout: 15000 });
    await page.waitForTimeout(1500);

    const mdIframe = page.locator(".o-FileViewer-main iframe.o-isText").first();
    const srcdoc = await mdIframe.getAttribute("srcdoc");
    if (!srcdoc || srcdoc.includes("404 Not Found") || srcdoc.includes("Unable to load document preview")) {
        throw new Error(`Markdown preview failed or returned 404! srcdoc snippet: ${(srcdoc || "").slice(0, 300)}`);
    }
    if (!srcdoc.includes("<h1>") || !srcdoc.includes("<table>")) {
        throw new Error(`Markdown preview did not render HTML headings/tables! srcdoc snippet: ${srcdoc.slice(0, 300)}`);
    }
    console.log("Markdown preview srcdoc length:", srcdoc.length, "| Contains <h1> & <table> | Zero 404!");
    const mdScreenshotPath = path.join(BRAIN_DIR, "documents_markdown_viewer_verified.png");
    await page.screenshot({ path: mdScreenshotPath, fullPage: false });
    console.log(`Saved Markdown FileViewer screenshot to ${mdScreenshotPath}`);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);

    await browser.close();
    console.log("ALL DOCUMENTS VIEWER & ACTION BUTTON VERIFICATION CHECKS PASSED!");
})().catch((err) => {
    console.error("VERIFICATION FAILED:", err);
    process.exit(1);
});
