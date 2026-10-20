#!/usr/bin/env python3
"""
Unified Autonomous Lead-to-Cash (AL2C) End-to-End & SOTA UI/UX Verification Suite.

Verifies:
1. CSS/DOM & Brand DNA Invariants (SOP-UI-SOTA-01 / ADR-20261020-015 / ADR-20261020-016):
   - Zero legacy SAP Blue (#0070F2) or generic blue (#0f62fe) across AL2C widgets & portal views
   - Canonical Innoria Brand Palette (#005F73 Deep Teal, #0ABBDB Cyan, #003333 Forest Teal, #FF8000 Solar Orange)
   - Primary 'Poppins' sans-serif font stack across AI Concierge and Customer Portal
   - 100%-Height Vertical Logo Frame (.al2c-logo-square-frame with logo_innoria_vertical.svg)
   - Boundary Column Text Alignment (.innoria-col-left left-aligned, .innoria-col-right right-aligned)
   - Zero Checkbox Line-Jump (.innoria-sota-check-row flex non-wrapping layout)
2. Stage 1: Public Quote Request + Priority File Attachment + EN/VI Semantic Translation
   (/contactus, /en/contactus, /innoria/quote/request)
3. Stage 2: AI Concierge Multi-Tab Hub (Chat, Services Configurator, ROI Calculator, Fast-Track Book Lead with File Attachment)
   (/innoria/ai_concierge/query, /innoria/ai_concierge/calculate_roi, /innoria/ai_concierge/book_lead)
4. Stage 3 & 4: Customer Portal (/my/home & /my/software-portal) 4-Stage Delivery Hub:
   - SOW Quotation review & e-Signature approval
   - Engineer Timesheet SHA-256 verification & sign-off
   - Draft vs Official 1C26TAA E-Invoice XML/HTML preview
   - Grounded Portal AI Copilot (/my/software-portal/chat_assistant)
   - Customer Care SLA Desk & AL2C-INV-103 Dunning Freeze (/my/software-portal/customer_care_ticket)
"""
import base64
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import http.cookiejar

BASE_URL = os.environ.get("O20_BASE_URL", "http://127.0.0.1:28069")
ROOT_DIR = "/home/zen/O20"


def assert_sota_ui_ux_static_invariants():
    print("=== [1/4] Auditing AL2C SOTA UI/UX Static & Brand DNA Invariants ===")
    concierge_scss = os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/scss/ai_concierge_widget.scss")
    concierge_dark_scss = os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/scss/ai_concierge_widget.dark.scss")
    concierge_xml = os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/xml/ai_concierge_widget.xml")
    portal_scss = os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/scss/portal_branding.scss")
    portal_xml = os.path.join(ROOT_DIR, "addons/insilos_al2c/views/portal_templates.xml")

    for path in (concierge_scss, concierge_dark_scss, concierge_xml, portal_scss, portal_xml):
        assert os.path.exists(path), f"Missing required AL2C file: {path}"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        lower = content.lower()
        assert "#0070f2" not in lower, f"Legacy SAP Blue #0070F2 found in {path}"
        assert "#0f62fe" not in lower, f"Legacy generic blue #0f62fe found in {path}"

    with open(concierge_scss, "r", encoding="utf-8") as f:
        c_scss = f.read()
    assert "#005F73" in c_scss and "#0ABBDB" in c_scss and "#FF8000" in c_scss, (
        "ai_concierge_widget.scss must define canonical Innoria palette (#005F73, #0ABBDB, #FF8000)"
    )
    assert "'Poppins'" in c_scss, "ai_concierge_widget.scss must enforce 'Poppins' primary typography"
    assert ".al2c-logo-square-frame" in c_scss and "align-self: stretch !important" in c_scss, (
        "ai_concierge_widget.scss must enforce 100%-height .al2c-logo-square-frame parity"
    )
    assert ".innoria-col-left" in c_scss and ".innoria-col-right" in c_scss, (
        "ai_concierge_widget.scss must enforce boundary column text alignment (.innoria-col-left / .innoria-col-right)"
    )
    assert ".innoria-sota-check-row" in c_scss and "flex-direction: row !important" in c_scss, (
        "ai_concierge_widget.scss must enforce non-wrapping flex checkbox rows (.innoria-sota-check-row)"
    )

    with open(concierge_xml, "r", encoding="utf-8") as f:
        c_xml = f.read()
    assert "logo_innoria_square_icon.svg" in c_xml and "al2c-header-logo-square" in c_xml and "al2c-logo-square-frame" in c_xml, (
        "ai_concierge_widget.xml must render logo_innoria_square_icon.svg inside .al2c-header-logo-square and .al2c-logo-square-frame"
    )
    assert "innoria-priority-dropzone" in c_xml and "innoria-dropzone-header-row" in c_xml, (
        "ai_concierge_widget.xml must render .innoria-priority-dropzone with boundary header row"
    )
    assert "innoria-sota-check-row" in c_xml, (
        "ai_concierge_widget.xml must wrap consent checkbox in .innoria-sota-check-row"
    )

    with open(portal_xml, "r", encoding="utf-8") as f:
        p_xml = f.read()
    assert 't-set="no_breadcrumbs" t-value="True"' in p_xml and "portal_breadcrumbs_inherit_al2c" in p_xml, (
        "portal_templates.xml must suppress orphaned breadcrumbs on /my/software-portal and upgrade portal.portal_breadcrumbs"
    )

    contactus_xml = os.path.join(ROOT_DIR, "enterprise/insilos_website/views/innoria_pages.xml")
    with open(contactus_xml, "r", encoding="utf-8") as f:
        cu_xml = f.read()
    assert "innoria-sota-pane-teal" in cu_xml and "innoria-sota-pane-orange" in cu_xml and "row g-4 align-items-stretch" in cu_xml, (
        "innoria_pages.xml (#executive-booking-form) must enforce equal-height split-pane cards (.innoria-sota-pane-teal + .innoria-sota-pane-orange)"
    )

    with open(portal_scss, "r", encoding="utf-8") as f:
        p_scss = f.read()
    assert "#005F73" in p_scss and "#0ABBDB" in p_scss and "#FF8000" in p_scss, (
        "portal_branding.scss must enforce canonical Innoria brand palette"
    )
    assert "'Poppins'" in p_scss, "portal_branding.scss must enforce 'Poppins' typography"
    print("  [PASS] All AL2C & Website static SCSS & XML files satisfy SOP-UI-SOTA-01 & ADR-20261020-017 invariants.")


def jsonrpc_call(opener, path, params=None):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "call",
        "params": params or {},
        "id": 1,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=20) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    assert "error" not in body, f"JSON-RPC error on {path}: {body.get('error')}"
    return body.get("result")


def test_ai_concierge_endpoints():
    print("=== [2/5] Testing AI Concierge Live HTTP JSON-RPC Endpoints (Query, Estimate, Book Lead + Attachment) ===")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Query endpoint
    res_q = jsonrpc_call(
        opener,
        "/innoria/ai_concierge/query",
        {
            "query": "Tư vấn thuê đội kỹ sư phần mềm đồng phát triển Squad theo Thông tư 13/2020 và đối soát timesheet?",
        },
    )
    assert res_q and res_q.get("success") is True, f"Unexpected query response: {res_q}"
    assert res_q.get("answer"), "AI Concierge answer should not be empty"
    assert res_q.get("grounded") is True, "AI Concierge answer should be grounded"
    print("  [PASS] /innoria/ai_concierge/query returned grounded response with service cards.")

    # 2. Estimate Service endpoint
    res_est = jsonrpc_call(
        opener,
        "/innoria/ai_concierge/estimate_service",
        {
            "service_code": "sw_squad",
            "scale_tier": "growth",
            "units": 4,
            "duration_months": 6,
        },
    )
    assert res_est and res_est.get("status") == "ok" and res_est.get("success") is True, (
        f"Unexpected estimate_service response: {res_est}"
    )
    assert res_est.get("estimated_total_vnd", 0) > 0, "Estimated total VND should be positive"
    print(
        f"  [PASS] /innoria/ai_concierge/estimate_service: total={res_est.get('formatted_total_vnd')}, "
        f"monthly={res_est.get('formatted_monthly_vnd')}"
    )

    # 3. Book Lead with Priority File Attachment
    sample_pdf_b64 = base64.b64encode(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF").decode("ascii")
    res_lead = jsonrpc_call(
        opener,
        "/innoria/ai_concierge/book_lead",
        {
            "name": "Trần Minh Quân",
            "email": "quan.tran@fintech-vietnam.vn",
            "phone": "0909888777",
            "company_name": "Công ty Cổ phần Công nghệ Tài chính Việt Nam",
            "product_interest": "Squad Kỹ Sư Đồng Phát Triển (Dedicated Co-Dev Squad - TT 13/2020)",
            "employee_count": "200 - 500 nhân sự",
            "notes": "Priority RFP attachment for 250-user ERP + RAG deployment",
            "service_code": "sw_squad",
            "scale_tier": "growth",
            "units": 4,
            "duration_months": 6,
            "attachments": [
                {
                    "name": "RFP_Enterprise_ERP_2026.pdf",
                    "type": "application/pdf",
                    "data": sample_pdf_b64,
                }
            ],
        },
    )
    assert res_lead and res_lead.get("success") is True, f"Unexpected book_lead response: {res_lead}"
    assert res_lead.get("lead_id"), "book_lead must return created lead_id"
    saved_att = res_lead.get("attachments_saved", res_lead.get("attachment_count", 0))
    assert saved_att >= 1, f"book_lead must persist uploaded priority attachment: {res_lead}"
    print(
        f"  [PASS] /innoria/ai_concierge/book_lead created lead_id={res_lead.get('lead_id')} "
        f"with attachments_saved={saved_att}."
    )


def run_sub_suite(script_rel_path):
    script_abs = os.path.join(ROOT_DIR, script_rel_path)
    res = subprocess.run([sys.executable, script_abs], cwd=ROOT_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        raise AssertionError(f"Sub-suite {script_rel_path} failed with exit code {res.returncode}")
    print(f"  [PASS] {script_rel_path} passed (exit code 0).")


def run_node_suite(script_rel_path):
    script_abs = os.path.join(ROOT_DIR, script_rel_path)
    env = dict(os.environ)
    env["NODE_PATH"] = os.path.join(ROOT_DIR, "node_modules")
    res = subprocess.run(["node", script_abs], cwd=ROOT_DIR, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        raise AssertionError(f"Node suite {script_rel_path} failed with exit code {res.returncode}")
    print(res.stdout.strip())
    print(f"  [PASS] {script_rel_path} passed (exit code 0).")


def main():
    assert_sota_ui_ux_static_invariants()
    test_ai_concierge_endpoints()
    print("=== [3/6] Running Website AI Concierge & Marketing Campaign Suite ===")
    run_sub_suite("tools/test_website_concierge_and_marketing.py")
    print("=== [4/6] Running Quote Attachment + EN/VI Semantic Translation Suite ===")
    run_sub_suite("tools/test_quote_attachment_and_i18n.py")
    print("=== [5/6] Running Customer Portal, Grounded AI Copilot & SLA Dunning Freeze Suites ===")
    run_sub_suite("tools/test_portal_chat_assistant_pdca.py")
    run_sub_suite("tools/test_customer_portal_and_mail_tham_mai.py")
    print("=== [6/6] Running Automated Playwright Pixel-Level Layout & Bounding-Box Audit ===")
    run_node_suite("tools/test_al2c_pixel_layout_audit.js")
    print("\nALL AL2C FULL UI/UX, PIXEL-LEVEL LAYOUT & END-TO-END SUITES PASSED (EXIT CODE 0).")


if __name__ == "__main__":
    main()

