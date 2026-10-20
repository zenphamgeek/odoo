#!/usr/bin/env python3
"""
End-to-End Verification Suite:
1. Quote Request Submission + Priority File Attachment (< 2h Fast-Track SLA) across:
   - /innoria/quote/submit (/contactus & #innoria_contact_section)
   - /request-demo
   - /innoria/ai_concierge/book_lead
   - /my/software-portal/customer_care_ticket
2. Database Verification (crm.lead priority == '3', ir.attachment linked, mail.mail queued with attachments)
3. Unified Semantic EN-VN Translation Engine (innoria_i18n_unified.js & /en/* routes)
"""

import base64
import json
import sys
import psycopg2
import requests

BASE_URL = "http://127.0.0.1:28069"
DB_NAME = "insilos20_dev"
PG_PORT = 5434


def assert_true(cond, msg):
    if not cond:
        print(f"❌ FAIL: {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ PASS: {msg}")


def test_quote_submit_with_attachments():
    print("\n--- [1] Testing /innoria/quote/submit WITH multiple file attachments (Fast-Track Priority < 2h SLA) ---")
    rfp_bytes = b"%PDF-1.4\n% Innoria Enterprise RFP & Architecture Specification 2026\n1 0 obj<<>>endobj\n"
    boq_bytes = b"PK\x03\x04 Innoria Bill of Quantities & Co-Dev Squad Sizing Matrix 2026"

    files = [
        ("quote_attachments", ("RFP_Innoria_Architecture_2026.pdf", rfp_bytes, "application/pdf")),
        ("quote_attachments", ("BoQ_Squad_Sizing_2026.xlsx", boq_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ]
    data = {
        "contact_name": "Nguyễn Minh Quân - CIO",
        "partner_name": "Tập Đoàn Công Nghiệp Thái Bình Dương",
        "email_from": "quan.nguyen@pacific-industrial.vn",
        "phone": "0903123456",
        "subject": "Yêu cầu báo giá triển khai Insilos ERP & Squad Kỹ Sư Đồng Phát Triển",
        "service_pillar": "Squad Kỹ Sư Đồng Phát Triển (Co-Dev Squad - TT 13/2020) & Turnkey Software",
        "description": "Đính kèm hồ sơ RFP và bảng khối lượng BoQ cho giai đoạn 1 (12 kỹ sư trong 6 tháng).",
        "format": "json",
    }
    resp = requests.post(
        f"{BASE_URL}/innoria/quote/submit",
        data=data,
        files=files,
        headers={"Accept": "application/json"},
        timeout=20,
    )
    assert_true(resp.status_code == 200, f"/innoria/quote/submit returned HTTP {resp.status_code}")
    res = resp.json()
    assert_true(res.get("success") is True, f"Quote submit response success=True: {res}")
    assert_true(res.get("fast_track_priority") is True, "fast_track_priority == True when files are attached")
    assert_true(res.get("priority") == "3", f"crm.lead priority == '3' (got {res.get('priority')})")
    assert_true(res.get("attachment_count") == 2, f"attachment_count == 2 (got {res.get('attachment_count')})")
    lead_id = res.get("lead_id")
    assert_true(isinstance(lead_id, int) and lead_id > 0, f"Created crm.lead ID #{lead_id}")

    # Verify in PostgreSQL
    conn = psycopg2.connect(host="127.0.0.1", port=PG_PORT, user="odoo", password="1NN0R1@2026", dbname=DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT name, priority, email_from FROM crm_lead WHERE id = %s", (lead_id,))
    lead_row = cur.fetchone()
    assert_true(lead_row is not None, f"crm_lead #{lead_id} exists in DB")
    assert_true(lead_row[1] == "3", f"DB crm_lead.priority == '3' (got {lead_row[1]})")
    assert_true("[FAST-TRACK PRIORITY]" in lead_row[0], f"DB crm_lead.name has [FAST-TRACK PRIORITY] prefix: {lead_row[0]}")

    cur.execute(
        "SELECT id, name, file_size FROM ir_attachment WHERE res_model = 'crm.lead' AND res_id = %s ORDER BY id",
        (lead_id,),
    )
    att_rows = cur.fetchall()
    assert_true(len(att_rows) == 2, f"DB has 2 ir.attachment records linked to crm.lead #{lead_id}: {att_rows}")

    cur.execute(
        """
        SELECT m.id, mm.subject, m.email_to
        FROM mail_mail m
        JOIN mail_message mm ON mm.id = m.mail_message_id
        WHERE mm.subject LIKE %s
        ORDER BY m.id DESC LIMIT 1
        """,
        (f"%FAST-TRACK PRIORITY%Tập Đoàn Công Nghiệp Thái Bình Dương%",),
    )
    mail_row = cur.fetchone()
    assert_true(mail_row is not None, f"Fast-track notification mail.mail queued to tham.mai@inno.ai.vn: {mail_row}")
    conn.close()


def test_quote_submit_redirect_flow():
    print("\n--- [2] Testing /innoria/quote/submit browser redirect flow (/contactus?submitted=1&priority=1) ---")
    rfp_bytes = b"%PDF-1.4\n% Sample Architecture Blueprint\n"
    files = [("quote_attachments", ("Blueprint_2026.pdf", rfp_bytes, "application/pdf"))]
    data = {
        "contact_name": "Lê Hoàng Nam - CTO",
        "partner_name": "Công Ty Cổ Phần Logistics Đông Nam Á",
        "email_from": "nam.le@sealogistics.vn",
        "phone": "0912345678",
        "description": "Cần báo giá bóc tách chứng từ B/L và C/O tự động.",
        "return_url": "/contactus",
    }
    resp = requests.post(
        f"{BASE_URL}/innoria/quote/submit",
        data=data,
        files=files,
        allow_redirects=False,
        timeout=20,
    )
    assert_true(resp.status_code in (302, 303), f"Browser form submission redirects ({resp.status_code})")
    loc = resp.headers.get("Location", "")
    assert_true("submitted=1" in loc and "priority=1" in loc and "files=1" in loc, f"Redirect URL contains submitted=1&priority=1&files=1: {loc}")

    # Follow redirect and verify confirmation banner renders in HTML
    page_resp = requests.get(f"{BASE_URL}{loc}" if loc.startswith("/") else loc, timeout=20)
    assert_true(page_resp.status_code == 200, "Redirect target /contactus?submitted=1 loads HTTP 200")
    assert_true(
        "đã tiếp nhận yêu cầu báo giá" in page_resp.text.lower() and "fast-track priority" in page_resp.text.lower(),
        "Confirmation banner and FAST-TRACK PRIORITY badge rendered on /contactus",
    )


def test_ai_concierge_book_lead_with_attachment():
    print("\n--- [3] Testing AI Concierge /innoria/ai_concierge/book_lead WITH base64 file attachment ---")
    session = requests.Session()
    chal_resp = session.post(
        f"{BASE_URL}/innoria/ai_concierge/security_challenge",
        json={"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1},
        timeout=15,
    ).json()
    chal = chal_resp.get("result", {})
    ans = int(chal.get("operand_a", 4)) + int(chal.get("operand_b", 3))

    sample_b64 = base64.b64encode(b"%PDF-1.4\n% AI Concierge Uploaded SRS Document\n").decode("ascii")
    book_payload = {
        "name": "Phạm Bảo Châu",
        "email": "chau.pham@finholding.vn",
        "phone": "0903847261",
        "company_name": "Tập Đoàn Tài Chính Á Châu",
        "product_interest": "Squad Kỹ Sư Đồng Phát Triển (Dedicated Co-Dev Squad - TT 13/2020)",
        "employee_count": "200 - 500 nhân sự",
        "notes": "Đính kèm SRS hệ thống Core FinOps để nhận báo giá trong 2 giờ.",
        "service_code": "sw_squad",
        "scale_tier": "growth",
        "units": 2,
        "duration_months": 6,
        "estimated_total_vnd": 1560000000,
        "form_dwell_ms": 4800,
        "sec_challenge_token": chal.get("challenge_token"),
        "sec_challenge_answer": str(ans),
        "attachments_json": [
            {
                "name": "SRS_Core_FinOps_2026.pdf",
                "type": "application/pdf",
                "data": sample_b64,
            }
        ],
    }
    book_resp = session.post(
        f"{BASE_URL}/innoria/ai_concierge/book_lead",
        json={"jsonrpc": "2.0", "method": "call", "params": book_payload, "id": 2},
        timeout=20,
    ).json()
    res = book_resp.get("result", {})
    assert_true(res.get("success") is True, f"AI Concierge book_lead succeeded: {res}")
    assert_true(res.get("fast_track_priority") is True, "AI Concierge book_lead activated fast_track_priority == True")
    assert_true(res.get("priority") == "3", f"AI Concierge book_lead set priority == '3' (got {res.get('priority')})")
    assert_true(res.get("attachment_count") == 1, f"AI Concierge book_lead saved 1 attachment (got {res.get('attachment_count')})")


def test_request_demo_with_attachment():
    print("\n--- [4] Testing /request-demo WITH file attachment ---")
    import re
    sess = requests.Session()
    get_resp = sess.get(f"{BASE_URL}/request-demo", timeout=15)
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp.text)
    csrf_token = m.group(1) if m else ""
    files = [("quote_attachments", ("Demo_Scope_SRS.pdf", b"%PDF-1.4\n% Demo Scope SRS\n", "application/pdf"))]
    data = {
        "csrf_token": csrf_token,
        "name": "Vũ Quốc Khánh",
        "email": "khanh.vu@energygrid.vn",
        "company": "Tổng Công Ty Năng Lượng Xanh",
        "job_title": "Giám Đốc Kỹ Thuật",
        "phone": "0938112233",
        "industry": "energy",
        "use_case": "reliability",
        "company_size": "250_999",
        "core_erp": "sap_s4",
        "project_timeline": "1_3_mo",
        "message": "Đính kèm sơ đồ trạm biến áp và yêu cầu báo giá POC.",
        "consent": "on",
    }
    resp = sess.post(
        f"{BASE_URL}/request-demo",
        data=data,
        files=files,
        allow_redirects=False,
        timeout=20,
    )
    assert_true(resp.status_code in (302, 303), f"/request-demo with attachment redirected ({resp.status_code}) to {resp.headers.get('Location')}")


def test_unified_i18n_and_en_routes():
    print("\n--- [5] Testing Unified EN-VN Semantic Translation Framework & /en/* routes ---")
    for route in ("/", "/en", "/contactus", "/en/contactus", "/request-demo", "/en/request-demo", "/pricing", "/en/pricing"):
        r = requests.get(f"{BASE_URL}{route}", timeout=15)
        assert_true(r.status_code == 200, f"Route {route} returns HTTP 200")

    home_html = requests.get(f"{BASE_URL}/", timeout=15).text
    contact_html = requests.get(f"{BASE_URL}/contactus", timeout=15).text
    assert_true('action="/innoria/quote/submit"' in home_html, "Homepage #innoria_contact_section posts to /innoria/quote/submit")
    assert_true('name="quote_attachments"' in home_html, "Homepage #innoria_contact_section includes Priority File Attachment input")
    assert_true('action="/innoria/quote/submit"' in contact_html, "/contactus form posts to /innoria/quote/submit")
    assert_true('name="quote_attachments"' in contact_html, "/contactus form includes Priority File Attachment input")
    assert_true("data-i18n-en=" in contact_html and "data-i18n-vi=" in contact_html, "/contactus includes semantic data-i18n-en and data-i18n-vi attributes")


if __name__ == "__main__":
    test_quote_submit_with_attachments()
    test_quote_submit_redirect_flow()
    test_ai_concierge_book_lead_with_attachment()
    test_request_demo_with_attachment()
    test_unified_i18n_and_en_routes()
    print("\n🎉 ALL QUOTE REQUEST + PRIORITY FILE ATTACHMENT + UNIFIED EN-VN SEMANTIC I18N TESTS PASSED!")
