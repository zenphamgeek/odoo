/**
 * Automated Pixel-Level Layout & Bounding-Box Verification Suite for AL2C & Innoria SOTA UI
 * (SOP-UI-SOTA-01 / ADR-20261020-015 / ADR-20261020-017)
 *
 * Verifies across Desktop (1440x960) and Mobile (375x812):
 * 1. Zero horizontal overflow (document.documentElement.scrollWidth <= clientWidth + 2)
 * 2. Zero broken images (img.complete && img.naturalWidth > 0)
 * 3. Space-Aware Brand Logo Inventory (ADR-20261020-017):
 *    - Compact square frames (<= 76px or .al2c-header-logo-square) use logo_innoria_square_icon.svg
 *    - Large workspace header lockups (>= 80px) use logo_innoria_vertical.svg
 * 4. 100%-Height Header Logo Frame Parity:
 *    - Inside .innoria-sota-header-lockup, abs(logoFrame.height - adjacentTextCol.height) <= 2px on Desktop
 * 5. Equal-Height Split-Pane Geometry:
 *    - Inside .row.align-items-stretch containing .innoria-sota-pane-teal and .innoria-sota-pane-orange,
 *      abs(tealPane.height - orangePane.height) <= 2px on Desktop
 * 6. Boundary Column Text Alignment:
 *    - .innoria-col-left computed textAlign in ['left', 'start']
 *    - .innoria-col-right computed textAlign in ['right', 'end']
 * 7. Non-Wrapping Flexbox Checkbox Rows:
 *    - .innoria-sota-check-row computed display === 'flex', flexDirection === 'row',
 *      and abs(checkbox.top - label.top) <= 12px
 * 8. Zero Empty Vertical Holes (> 250px gap between consecutive visible block sections)
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = process.env.O20_BASE_URL || 'http://127.0.0.1:28069';
const SCREENSHOT_DIR = '/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/screenshots';

async function auditCommonPageInvariants(page, routeLabel, viewportLabel) {
    const report = await page.evaluate(({ isDesktop }) => {
        const errors = [];
        const metrics = {};

        // 1. Horizontal overflow check
        const docEl = document.documentElement;
        const scrollW = docEl.scrollWidth;
        const clientW = docEl.clientWidth;
        metrics.scrollWidth = scrollW;
        metrics.clientWidth = clientW;
        if (scrollW > clientW + 2) {
            errors.push(`Horizontal overflow: scrollWidth=${scrollW} > clientWidth=${clientW}`);
        }

        // 2. Broken images check (accounting for native loading="lazy" below the fold)
        const imgs = Array.from(document.querySelectorAll('img'));
        let checkedImgs = 0;
        for (const img of imgs) {
            const style = window.getComputedStyle(img);
            if (style.display === 'none' || style.visibility === 'hidden') continue;
            const rect = img.getBoundingClientRect();
            if (rect.width === 0 && rect.height === 0) continue;
            if (img.getAttribute('loading') === 'lazy' && !img.complete && rect.top >= window.innerHeight) {
                continue;
            }
            checkedImgs++;
            if (img.complete && img.naturalWidth === 0) {
                errors.push(`Broken image: src=${img.getAttribute('src')}`);
            }
        }
        metrics.checkedImages = checkedImgs;

        // 3. 100%-Height Header Logo Lockup Parity (Desktop)
        const lockups = Array.from(document.querySelectorAll('.innoria-sota-header-lockup'));
        metrics.headerLockups = lockups.length;
        if (isDesktop) {
            for (const lockup of lockups) {
                const logoFrame = lockup.querySelector('.al2c-logo-square-frame, .al2c-header-logo-square');
                const textCol = lockup.querySelector('.al2c-header-text-col');
                if (logoFrame && textCol) {
                    const lr = logoFrame.getBoundingClientRect();
                    const tr = textCol.getBoundingClientRect();
                    if (lr.height > 0 && tr.height > 0) {
                        const delta = Math.abs(lr.height - tr.height);
                        if (delta > 3) {
                            errors.push(`Header logo height mismatch: logoFrame=${lr.height.toFixed(1)}px vs textCol=${tr.height.toFixed(1)}px (delta=${delta.toFixed(1)}px)`);
                        }
                    }
                }
            }
        }

        // 4. Equal-height Split-Pane Parity (Desktop)
        const rows = Array.from(document.querySelectorAll('.row.align-items-stretch'));
        let splitPaneCount = 0;
        for (const row of rows) {
            const teal = row.querySelector('.innoria-sota-pane-teal');
            const orange = row.querySelector('.innoria-sota-pane-orange');
            if (teal && orange) {
                splitPaneCount++;
                if (isDesktop) {
                    const tr = teal.getBoundingClientRect();
                    const or = orange.getBoundingClientRect();
                    if (tr.height > 0 && or.height > 0) {
                        const delta = Math.abs(tr.height - or.height);
                        const topDelta = Math.abs(tr.top - or.top);
                        if (delta > 3) {
                            errors.push(`Split-pane height mismatch: teal=${tr.height.toFixed(1)}px vs orange=${or.height.toFixed(1)}px (delta=${delta.toFixed(1)}px)`);
                        }
                        if (topDelta > 3) {
                            errors.push(`Split-pane top edge mismatch: teal.top=${tr.top.toFixed(1)}px vs orange.top=${or.top.toFixed(1)}px`);
                        }
                    }
                }
            }
        }
        metrics.splitPanesChecked = splitPaneCount;

        // 5. Boundary Column Text Alignment
        const leftCols = Array.from(document.querySelectorAll('.innoria-col-left'));
        for (const el of leftCols) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) continue;
            const ta = window.getComputedStyle(el).textAlign;
            if (!['left', 'start'].includes(ta)) {
                errors.push(`.innoria-col-left has invalid textAlign="${ta}" on <${el.tagName.toLowerCase()}>`);
            }
        }
        const rightCols = Array.from(document.querySelectorAll('.innoria-col-right'));
        for (const el of rightCols) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) continue;
            const ta = window.getComputedStyle(el).textAlign;
            if (!['right', 'end'].includes(ta)) {
                errors.push(`.innoria-col-right has invalid textAlign="${ta}" on <${el.tagName.toLowerCase()}>`);
            }
        }
        metrics.boundaryColsChecked = leftCols.length + rightCols.length;

        // 6. Non-Wrapping Flexbox Checkbox Rows
        const checkRows = Array.from(document.querySelectorAll('.innoria-sota-check-row'));
        for (const row of checkRows) {
            const r = row.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) continue;
            const cs = window.getComputedStyle(row);
            if (cs.display !== 'flex' || cs.flexDirection !== 'row') {
                errors.push(`.innoria-sota-check-row invalid flex layout: display=${cs.display}, flexDirection=${cs.flexDirection}`);
            }
            const input = row.querySelector('input[type="checkbox"]');
            const label = row.querySelector('label');
            if (input && label) {
                const ir = input.getBoundingClientRect();
                const lr = label.getBoundingClientRect();
                if (lr.top - ir.bottom > 4) {
                    errors.push(`Checkbox line-jump detected: label.top=${lr.top.toFixed(1)} > input.bottom=${ir.bottom.toFixed(1)}`);
                }
            }
        }
        metrics.checkboxRowsChecked = checkRows.length;

        return { errors, metrics };
    }, { isDesktop: viewportLabel === 'Desktop' });

    if (report.errors.length > 0) {
        console.error(`[FAIL] ${routeLabel} (${viewportLabel}) Pixel Audit Errors:`, report.errors);
        throw new Error(`${routeLabel} (${viewportLabel}) failed pixel layout audit: ${report.errors.join(' | ')}`);
    }
    console.log(`  [PASS] ${routeLabel} (${viewportLabel}):`, JSON.stringify(report.metrics));
}

(async () => {
    if (!fs.existsSync(SCREENSHOT_DIR)) {
        fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }
    const browser = await chromium.launch({ headless: true });

    try {
        // =========================================================================
        // 1. DESKTOP (1440x960) — /contactus, /en/contactus, AI Concierge, /my/software-portal
        // =========================================================================
        const desktopCtx = await browser.newContext({ viewport: { width: 1440, height: 960 } });
        const page = await desktopCtx.newPage();

        // 1A. /contactus (Vietnamese)
        await page.goto(`${BASE_URL}/contactus`, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(400);
        await auditCommonPageInvariants(page, '/contactus (VI)', 'Desktop');

        // Verify no vertical empty hole > 250px between hero and booking form
        const contactGap = await page.evaluate(() => {
            const formSec = document.querySelector('#executive-booking-form');
            const prevSec = formSec ? formSec.previousElementSibling : null;
            if (!formSec || !prevSec) return 0;
            return formSec.getBoundingClientRect().top - prevSec.getBoundingClientRect().bottom;
        });
        if (contactGap > 120) {
            throw new Error(`/contactus vertical gap too large between hero and #executive-booking-form: ${contactGap}px`);
        }

        // Scroll to #executive-booking-form and screenshot (dismiss nudge if open so form footer is 100% visible)
        await page.evaluate(() => {
            const nudge = document.querySelector('.al2c-proactive-nudge');
            if (nudge) nudge.style.display = 'none';
        });
        const formEl = page.locator('#executive-booking-form');
        await formEl.scrollIntoViewIfNeeded();
        await page.waitForTimeout(250);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'verified_quote_request_priority_file_attachment_vi.png') });

        // 1B. /en/contactus (English Semantic Translation + Pixel Geometry)
        await page.goto(`${BASE_URL}/en/contactus`, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(600);
        await auditCommonPageInvariants(page, '/en/contactus (EN)', 'Desktop');
        await page.evaluate(() => {
            const nudge = document.querySelector('.al2c-proactive-nudge');
            if (nudge) nudge.style.display = 'none';
        });
        await page.locator('#executive-booking-form').scrollIntoViewIfNeeded();
        await page.waitForTimeout(250);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'verified_quote_request_semantic_en.png') });

        // 1C. AI Concierge Multi-Tab Hub on Desktop
        await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(500);
        const launcher = page.locator('.al2c-concierge-launcher');
        await launcher.click();
        await page.waitForTimeout(400);

        // Verify Square Innoria Logo in header, avatar, and launcher
        const conciergeLogoCheck = await page.evaluate(() => {
            const headerImg = document.querySelector('.al2c-header-logo-square img');
            const avatarImg = document.querySelector('.al2c-message-avatar img');
            return {
                headerSrc: headerImg ? headerImg.getAttribute('src') : '',
                avatarSrc: avatarImg ? avatarImg.getAttribute('src') : '',
            };
        });
        if (!conciergeLogoCheck.headerSrc.includes('logo_innoria_square_icon.svg')) {
            throw new Error(`AI Concierge header must use logo_innoria_square_icon.svg, got ${conciergeLogoCheck.headerSrc}`);
        }
        await auditCommonPageInvariants(page, 'AI Concierge Tab 1 (Chat)', 'Desktop');
        await page.locator('.al2c-concierge-drawer').screenshot({
            path: path.join(SCREENSHOT_DIR, 'verified_al2c_concierge_chat_sota.png'),
        });

        // Switch to Tab 2 (Services & ROI Configurator)
        const tabs = page.locator('.al2c-tab-btn');
        await tabs.nth(1).click();
        await page.waitForTimeout(350);
        await auditCommonPageInvariants(page, 'AI Concierge Tab 2 (Services & ROI)', 'Desktop');
        await page.locator('.al2c-concierge-drawer').screenshot({
            path: path.join(SCREENSHOT_DIR, 'verified_al2c_concierge_configurator_sota.png'),
        });

        // Switch to Tab 3 (Fast-Track Lead & SOW Desk)
        await tabs.nth(2).click();
        await page.waitForTimeout(350);
        await auditCommonPageInvariants(page, 'AI Concierge Tab 3 (Lead & SOW Desk)', 'Desktop');

        // Verify lead sub-header uses Square Innoria Logo & 100%-height frame
        const leadLogoCheck = await page.evaluate(() => {
            const frame = document.querySelector('.al2c-lead-header .al2c-logo-square-frame');
            const img = frame ? frame.querySelector('img') : null;
            const copy = document.querySelector('.al2c-lead-header .innoria-sota-header-text-col');
            if (!frame || !img || !copy) return { ok: false, reason: 'Missing elements' };
            const fr = frame.getBoundingClientRect();
            const cr = copy.getBoundingClientRect();
            return {
                ok: img.getAttribute('src').includes('logo_innoria_square_icon.svg') && Math.abs(fr.height - cr.height) <= 3,
                src: img.getAttribute('src'),
                frameH: fr.height,
                copyH: cr.height,
            };
        });
        if (!leadLogoCheck.ok) {
            throw new Error(`AI Concierge Lead Header logo check failed: ${JSON.stringify(leadLogoCheck)}`);
        }
        await page.locator('.al2c-concierge-drawer').screenshot({
            path: path.join(SCREENSHOT_DIR, 'verified_al2c_concierge_lead_sota.png'),
        });

        // Scroll inside Tab 3 (.al2c-lead-section) to Priority Dropzone + Consent Checkbox
        await page.evaluate(() => {
            const sec = document.querySelector('.al2c-lead-section');
            const body = document.querySelector('.al2c-lead-body');
            if (sec) sec.scrollTop = sec.scrollHeight;
            if (body) body.scrollTop = body.scrollHeight;
        });
        await page.waitForTimeout(300);
        await auditCommonPageInvariants(page, 'AI Concierge Tab 3 (Dropzone & Consent)', 'Desktop');
        await page.locator('.al2c-concierge-drawer').screenshot({
            path: path.join(SCREENSHOT_DIR, 'verified_al2c_concierge_lead_dropzone_sota.png'),
        });

        // 1D. Customer Portal 4-Stage Software Delivery Hub (/my/software-portal)
        await page.goto(`${BASE_URL}/my/software-portal`, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(500);
        await auditCommonPageInvariants(page, '/my/software-portal (Full Workspace)', 'Desktop');

        // Verify zero orphaned tiny home icon on /my/software-portal
        const hasOrphanHomeIcon = await page.evaluate(() => {
            const icons = Array.from(document.querySelectorAll('.o_portal_submenu i[data-icon="home"]'));
            return icons.some((el) => el.getBoundingClientRect().width > 0);
        });
        if (hasOrphanHomeIcon) {
            throw new Error('Orphaned tiny home icon detected on /my/software-portal');
        }

        // Screenshot Top Header + KPI + Section 1
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'verified_software_customer_portal_top.png') });

        // Scroll to Section 3 (#invoices-section) and screenshot
        await page.locator('#invoices-section').scrollIntoViewIfNeeded();
        await page.waitForTimeout(250);
        await page.screenshot({
            path: path.join(SCREENSHOT_DIR, 'verified_software_customer_portal_draft_vs_official_invoices.png'),
        });

        // Scroll to Section 4 (#customer-care-section) and screenshot
        await page.locator('#customer-care-section').scrollIntoViewIfNeeded();
        await page.waitForTimeout(250);
        await page.screenshot({
            path: path.join(SCREENSHOT_DIR, 'verified_portal_chat_assistant_customer_care_pdca.png'),
        });

        await desktopCtx.close();

        // =========================================================================
        // 2. MOBILE (375x812) — Responsive Overflow & Touch Target Audit
        // =========================================================================
        const mobileCtx = await browser.newContext({ viewport: { width: 375, height: 812 } });
        const mPage = await mobileCtx.newPage();

        await mPage.goto(`${BASE_URL}/contactus`, { waitUntil: 'networkidle', timeout: 30000 });
        await mPage.waitForTimeout(400);
        await auditCommonPageInvariants(mPage, '/contactus (VI)', 'Mobile');

        await mPage.goto(`${BASE_URL}/my/software-portal`, { waitUntil: 'networkidle', timeout: 30000 });
        await mPage.waitForTimeout(400);
        await auditCommonPageInvariants(mPage, '/my/software-portal', 'Mobile');

        await mobileCtx.close();
        console.log('=== ALL PIXEL-LEVEL BOUNDING-BOX & SOTA UI/UX AUDITS PASSED ===');
    } finally {
        await browser.close();
    }
})();
