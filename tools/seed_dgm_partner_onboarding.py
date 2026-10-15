#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP-DGM-06 Idempotent Partner Onboarding, Tiering, Companion Document Templates
(`TPL-ONB-01`..`TPL-ONB-04`) & Payment Gate Seeder for DGM / Digimate JSC (`insilos20_dev` & `innoria_prod`).
"""
import base64
import html
import json
import os
import secrets
import sys
import psycopg2


CANONICAL_ONBOARDING_PARTNERS = [
    {
        "match_id": 592,
        "name": "CÔNG TY TNHH MTI TECHNOLOGY",
        "vat": "0314015511",
        "country_code": "VN",
        "email": "accounting@mti-tech.vn",
        "street": "Tòa nhà Cộng Hòa Garden, 20 Đường Cộng Hòa, Phường 12, Quận Tân Bình, TP.HCM",
        "dgm_partner_group": "strategic_b2b",
        "dgm_partner_tier": "tier_s",
        "dgm_tier_score": 100,
        "dgm_credit_limit_vnd": 2_000_000_000.0,
        "dgm_allowed_payment_rail": "vcb_digibiz",
        "dgm_provisional_code": "TMP-DGM-0001",
        "dgm_partner_code": "PTN-DGM-2026-0001",
        "dgm_onboarding_state": "approved",
    },
    {
        "match_id": None,
        "name": "Canva Pty Ltd",
        "vat": None,
        "country_code": "AU",
        "email": "pub@digimate.vn",
        "street": "110 Kippax St, Surry Hills, NSW 2010, Australia",
        "dgm_partner_group": "global_platform",
        "dgm_partner_tier": "tier_s",
        "dgm_tier_score": 100,
        "dgm_credit_limit_vnd": 2_000_000_000.0,
        "dgm_allowed_payment_rail": "swift_usd",
        "dgm_provisional_code": "TMP-DGM-0002",
        "dgm_partner_code": "PTN-DGM-2026-0002",
        "dgm_onboarding_state": "approved",
    },
    {
        "match_id": 580,
        "name": "Trung tâm Dịch vụ số MobiFone (MDS)",
        "vat": "0100686209",
        "country_code": "VN",
        "email": "mds-support@mobifone.vn",
        "street": "Tầng 6, Tòa nhà MobiFone, Số 5, Ngõ 82, Phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, TP. Hà Nội",
        "dgm_partner_group": "strategic_b2b",
        "dgm_partner_tier": "tier_s",
        "dgm_tier_score": 100,
        "dgm_credit_limit_vnd": 2_000_000_000.0,
        "dgm_allowed_payment_rail": "vcb_digibiz",
        "dgm_provisional_code": "TMP-DGM-0003",
        "dgm_partner_code": "PTN-DGM-2026-0003",
        "dgm_onboarding_state": "approved",
    },
    {
        "match_id": None,
        "name": "Temecula Valley Unified School District",
        "vat": None,
        "country_code": "US",
        "email": "privacy@tvusd.k12.ca.us",
        "street": "31350 Rancho Vista Road, Temecula, CA 92592, USA",
        "dgm_partner_group": "gov_edu",
        "dgm_partner_tier": "tier_s",
        "dgm_tier_score": 100,
        "dgm_credit_limit_vnd": 2_000_000_000.0,
        "dgm_allowed_payment_rail": "swift_usd",
        "dgm_provisional_code": "TMP-DGM-0004",
        "dgm_partner_code": "PTN-DGM-2026-0004",
        "dgm_onboarding_state": "approved",
    },
    {
        "match_id": None,
        "name": "VNPT TP.HCM (Chi nhánh Tập đoàn Bưu chính Viễn thông Việt Nam)",
        "vat": "0300954529",
        "country_code": "VN",
        "email": "cskh@vnpt.vn",
        "street": "125 Hai Bà Trưng, Phường Sài Gòn, TP.HCM",
        "dgm_partner_group": "infra_vendor",
        "dgm_partner_tier": "tier_a",
        "dgm_tier_score": 90,
        "dgm_credit_limit_vnd": 500_000_000.0,
        "dgm_allowed_payment_rail": "vcb_digibiz",
        "dgm_provisional_code": "TMP-DGM-0005",
        "dgm_partner_code": "PTN-DGM-2026-0005",
        "dgm_onboarding_state": "approved",
    },
    {
        "match_id": None,
        "name": "Viettel-CA (Viettel TP.HCM - Chi nhánh Tập đoàn Công nghiệp - Viễn thông Quân đội)",
        "vat": "0100109106-122",
        "country_code": "VN",
        "email": "sinvoice@viettel.com.vn",
        "street": "Số 285 Đường Cách Mạng Tháng Tám, Phường 12, Quận 10, TP.HCM",
        "dgm_partner_group": "infra_vendor",
        "dgm_partner_tier": "tier_a",
        "dgm_tier_score": 90,
        "dgm_credit_limit_vnd": 500_000_000.0,
        "dgm_allowed_payment_rail": "vcb_digibiz",
        "dgm_provisional_code": "TMP-DGM-0006",
        "dgm_partner_code": "PTN-DGM-2026-0006",
        "dgm_onboarding_state": "approved",
    },
    {
        "match_id": None,
        "name": "CÔNG TY CỔ PHẦN AIFIN COMPANY GLOBAL",
        "vat": "0319631994",
        "country_code": "VN",
        "email": "huy.nguyen@aifin.com.vn",
        "street": "51-53 Võ Văn Tần, Phường Xuân Hòa, Thành Phố Hồ Chí Minh, Việt Nam",
        "dgm_partner_group": "strategic_b2b",
        "dgm_partner_tier": "tier_s",
        "dgm_tier_score": 100,
        "dgm_credit_limit_vnd": 2_000_000_000.0,
        "dgm_allowed_payment_rail": "vcb_digibiz",
        "dgm_provisional_code": "TMP-DGM-0007",
        "dgm_partner_code": "PTN-DGM-2026-0007",
        "dgm_onboarding_state": "approved",
    },
]


def get_connection(dbname=None):
    dbname = dbname or os.environ.get("DB_NAME", "innoria_prod")
    user = os.environ.get("DB_USER", "odoo")
    password = os.environ.get("PGPASSWORD")
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "5434"))
    kwargs = dict(dbname=dbname, user=user, host=host, port=port)
    if password:
        kwargs["password"] = password
    return psycopg2.connect(**kwargs)


def ensure_schema_columns(cur):
    """Ensures all SOP-DGM-06 columns and M2M tables exist on `party_master` (and refreshes `res_partner` view if applicable)."""
    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'party_master';
        """
    )
    row = cur.fetchone()
    base_partner_table = "party_master" if (row and row[0] == "BASE TABLE") else "res_partner"

    partner_cols = [
        ("dgm_partner_group", "VARCHAR DEFAULT 'sme_commercial'"),
        ("dgm_partner_tier", "VARCHAR DEFAULT 'tier_c'"),
        ("dgm_tier_score", "INTEGER DEFAULT 20"),
        ("dgm_credit_limit_vnd", "DOUBLE PRECISION DEFAULT 0.0"),
        ("dgm_allowed_payment_rail", "VARCHAR DEFAULT 'vcb_digibiz'"),
        ("dgm_onboarding_state", "VARCHAR DEFAULT 'provisional'"),
        ("dgm_provisional_code", "VARCHAR"),
        ("dgm_partner_code", "VARCHAR"),
        ("dgm_sales_flex_mode", "BOOLEAN DEFAULT TRUE"),
        ("dgm_canonical_partner_id", "INTEGER"),
        ("dgm_conflict_warning", "VARCHAR"),
        ("dgm_onboarding_folder_id", "INTEGER"),
        ("dgm_onboarding_doc_count", "INTEGER DEFAULT 0"),
        ("dgm_all_companion_docs_ready", "BOOLEAN DEFAULT FALSE"),
        ("dgm_approved_by", "INTEGER"),
        ("dgm_approved_date", "TIMESTAMP WITHOUT TIME ZONE"),
        ("dgm_payment_gate_override", "BOOLEAN DEFAULT FALSE"),
    ]
    for col, col_def in partner_cols:
        cur.execute(f"ALTER TABLE public.{base_partner_table} ADD COLUMN IF NOT EXISTS {col} {col_def};")

    # If public.res_partner is a VIEW over party_master, refresh it so SELECTs against res_partner see new columns
    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'res_partner';
        """
    )
    rp_row = cur.fetchone()
    if rp_row and rp_row[0] == "VIEW" and base_partner_table == "party_master":
        cur.execute("CREATE OR REPLACE VIEW public.res_partner AS SELECT * FROM public.party_master;")

    # Ensure account_payment column
    cur.execute(
        "ALTER TABLE public.account_payment ADD COLUMN IF NOT EXISTS dgm_payment_gate_override BOOLEAN DEFAULT FALSE;"
    )

    # Ensure M2M relation table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS public.dgm_partner_onboarding_doc_rel (
            partner_id INTEGER NOT NULL,
            document_id INTEGER NOT NULL,
            PRIMARY KEY (partner_id, document_id)
        );
        """
    )
    return base_partner_table


def render_companion_docs_for_seed(p):
    code = p["dgm_partner_code"]
    safe_code = code.replace("-", "_")
    p_name = html.escape(p["name"])
    p_vat = html.escape(p["vat"] or "N/A (Cross-Border / Miễn MST)")
    p_street = html.escape(p["street"] or "")
    p_email = html.escape(p["email"] or "finance@digimate.vn")
    credit_str = f"{p['dgm_credit_limit_vnd']:,.0f} VND"

    base_style = """
    <style>
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; color: #0f172a; line-height: 1.55; padding: 28px; max-width: 920px; margin: 0 auto; }
        .header-box { border-bottom: 3px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; background: #dbeafe; color: #1e40af; }
        table { width: 100%; border-collapse: collapse; margin: 14px 0; }
        th, td { border: 1px solid #cbd5e1; padding: 9px 12px; text-align: left; font-size: 13.5px; }
        th { background: #f1f5f9; font-weight: 600; width: 32%; }
        h1 { font-size: 20px; color: #1e3a8a; margin: 6px 0; }
        h2 { font-size: 15px; color: #0f172a; margin-top: 18px; border-left: 4px solid #2563eb; padding-left: 8px; }
    </style>
    """

    doc_01 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-01 KYC &amp; Tiering - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong><br/>MST: <strong>0317958465</strong> • Đ/c: Số 52 Đường B4, Phường Tây Thạnh (KDC CityLand, Phường Tân Mỹ), TP.HCM</div>
        <div class="badge">TPL-ONB-01 • SOP-DGM-06</div>
    </div>
    <h1>PHIẾU KHAI BÁO KYC, ĐÁNH GIÁ TÍN NHIỆM &amp; XẾP HẠNG ĐỐI TÁC</h1>
    <table>
        <tr><th>Mã Đối tác Chính thức</th><td><strong>{code}</strong> (Mã tạm Sales: <code>{p['dgm_provisional_code']}</code>)</td></tr>
        <tr><th>Tên Pháp nhân Đối tác</th><td><strong>{p_name}</strong></td></tr>
        <tr><th>Mã số thuế / Định danh</th><td><strong>{p_vat}</strong> ({p['country_code']})</td></tr>
        <tr><th>Địa chỉ Trụ sở</th><td>{p_street}</td></tr>
        <tr><th>Email Nhận Hóa đơn Điện tử</th><td>{p_email}</td></tr>
        <tr><th>Nhóm Đối tác (Partner Group)</th><td><code>{p['dgm_partner_group']}</code></td></tr>
        <tr><th>Xếp hạng Đối tác (Partner Tier)</th><td><strong>{p['dgm_partner_tier'].upper()}</strong> ({p['dgm_tier_score']}/100 điểm)</td></tr>
        <tr><th>Hạn mức Công nợ (Credit Limit)</th><td><strong>{credit_str}</strong></td></tr>
        <tr><th>Kênh Thanh toán Chuẩn</th><td><code>{p['dgm_allowed_payment_rail']}</code></td></tr>
    </table>
</body></html>"""

    doc_02 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-02 Mutual NDA ISO27001 - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong><br/>MST: <strong>0317958465</strong> • ISO/IEC 27001 &amp; ISO/IEC 27701 Privacy Governance</div>
        <div class="badge">TPL-ONB-02 • NDA</div>
    </div>
    <h1>THỎA THUẬN BẢO MẬT THÔNG TIN SONG NGỮ (MUTUAL NDA — ISO/IEC 27001 &amp; NĐ 13/2023/NĐ-CP)</h1>
    <table>
        <tr><th>Bên A</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: <strong>0317958465</strong></td></tr>
        <tr><th>Bên B</th><td><strong>{p_name}</strong> — MST: <strong>{p_vat}</strong> — Mã Partner: <strong>{code}</strong></td></tr>
    </table>
    <p>Hai Bên cam kết bảo mật toàn bộ dữ liệu thương mại, mã nguồn, tài liệu kỹ thuật và dữ liệu cá nhân theo chuẩn ISO/IEC 27001, ISO/IEC 27701 và Nghị định 13/2023/NĐ-CP.</p>
</body></html>"""

    staff_aug_block = ""
    if code == "PTN-DGM-2026-0007":
        staff_aug_block = """
        <h2>PHỤ LỤC CUNG ỨNG &amp; THUÊ NHÂN SỰ KỸ THUẬT (MTI STAFF AUGMENTATION MODEL — HĐ DIGIMATE-AIFIN-VN_2610-001)</h2>
        <table>
            <tr><th>Đại diện Pháp luật Bên A (AIfin)</th><td><strong>Ông Nguyễn Khắc Huy</strong> — Chức vụ: <strong>GIÁM ĐỐC</strong></td></tr>
            <tr><th>Hợp đồng Cung ứng Nhân sự</th><td><strong>DIGIMATE-AIFIN-VN_2610-001</strong> &amp; Phụ lục <strong>2610-001</strong> (Hiệu lực: 01/10/2026 – 30/09/2027)</td></tr>
            <tr><th>Nhân sự Kỹ thuật Biệt phái</th><td><strong>Ông Trần Văn Huỳnh Phố</strong> — Mã NV: <strong>DGM-009</strong> (Legacy: <code>NV-00074</code>) • CCCD: <code>079098014567</code> • Email: <code>pho.tran@inno.ai.vn</code></td></tr>
            <tr><th>Chức danh &amp; Đơn giá Dịch vụ</th><td><strong>Kỹ sư Phần mềm Senior (AIfin Onsite)</strong> • Đơn giá: <strong>350,000 VND/giờ</strong> (<strong>56,000,000 VND/tháng</strong> tiêu chuẩn 160h)</td></tr>
            <tr><th>Khung giờ chuẩn &amp; OT (MTI SLA)</th><td>Khung giờ chuẩn: <strong>140 – 180 giờ/tháng</strong> • OT &gt;180h: <strong>100%</strong> (ngày thường) / <strong>150%</strong> (cuối tuần &amp; Lễ) • Thay thế nhân sự: báo trước 30 ngày, miễn phí 05 ngày thử việc</td></tr>
            <tr><th>Hợp đồng Giải pháp 360-Sales</th><td><strong>AIFIN-DIGIMATE/360-SALES/2026</strong> (Ký ngày 11/09/2026 • Giá trị: <strong>200,000,000 VND</strong> • Đợt 1: 65% = 130,000,000 VND • Đợt 2: 35% = 70,000,000 VND)</td></tr>
            <tr><th>Điều khoản Thanh toán</th><td>Chuyển khoản vào TK VCB <strong>1202703007</strong> (PGD Trung Sơn) của CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ trong vòng <strong>40 ngày làm việc (Net 40)</strong></td></tr>
        </table>
        """

    doc_03 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-03 Master Commercial Frame - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong><br/>MST: <strong>0317958465</strong> • Tài khoản VCB: <strong>1202703007</strong></div>
        <div class="badge">TPL-ONB-03 • MSA &amp; SLA</div>
    </div>
    <h1>HỢP ĐỒNG NGUYÊN TẮC / KHUNG THƯƠNG MẠI &amp; SLA ({code})</h1>
    <table>
        <tr><th>Đối tác</th><td><strong>{p_name}</strong> ({p_vat})</td></tr>
        <tr><th>Phân nhóm &amp; Hạng</th><td><code>{p['dgm_partner_group']}</code> • <strong>{p['dgm_partner_tier'].upper()}</strong></td></tr>
        <tr><th>Hạn mức &amp; Kênh Thanh toán</th><td><strong>{credit_str}</strong> • <code>{p['dgm_allowed_payment_rail']}</code></td></tr>
    </table>
    {staff_aug_block}
    <p>Tuân thủ quy định xuất hóa đơn điện tử Nghị định 70/2025/NĐ-CP (Ký hiệu 1C26TAA) và kiểm soát đối soát công nợ tự động.</p>
</body></html>"""

    doc_04 = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"/><title>TPL-ONB-04 Payment Gate Approval Cert - {p_name}</title>{base_style}</head>
<body>
    <div class="header-box">
        <div><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong><br/>MST: <strong>0317958465</strong> • Cổng Kiểm soát Thanh toán Nội bộ (SOP-DGM-06)</div>
        <div class="badge">TPL-ONB-04 • PAYMENT GATE CERT</div>
    </div>
    <h1>CHỨNG NHẬN PHÊ DUYỆT MÃ ĐỐI TÁC &amp; CỔNG THANH TOÁN ({code})</h1>
    <table>
        <tr><th>Mã Đối tác Chính thức</th><td><strong>{code}</strong> (Trạng thái: <strong>APPROVED</strong>)</td></tr>
        <tr><th>Đối tác</th><td><strong>{p_name}</strong> (MST: <strong>{p_vat}</strong>)</td></tr>
        <tr><th>Kênh Thanh toán Phê duyệt</th><td><code>{p['dgm_allowed_payment_rail']}</code></td></tr>
        <tr><th>Người Phê duyệt</th><td>Lê Xuân Hoàng (Chủ tịch HĐQT &amp; TGĐ) &amp; Mai Thị Hồng Thắm (CFO)</td></tr>
    </table>
    <p>Đã hoàn tất 4/4 chứng từ On-boarding bắt buộc (TPL-ONB-01..04). Mở khóa toàn bộ quy trình thanh toán và đối soát công nợ.</p>
</body></html>"""

    return [
        ("TPL-ONB-01", f"01_KYC_Tiering_Dossier_{safe_code}.html", f"[TPL-ONB-01] Phiếu Khai báo KYC & Xếp hạng Đối tác — {p['name']} ({code})", doc_01),
        ("TPL-ONB-02", f"02_Mutual_NDA_ISO27001_{safe_code}.html", f"[TPL-ONB-02] Thỏa thuận Bảo mật Song ngữ NDA ISO 27001 — {p['name']} ({code})", doc_02),
        ("TPL-ONB-03", f"03_Master_Commercial_Frame_{safe_code}.html", f"[TPL-ONB-03] Hợp đồng Nguyên tắc & Khung Thương mại SLA — {p['name']} ({code})", doc_03),
        ("TPL-ONB-04", f"04_Payment_Gate_Approval_Cert_{safe_code}.html", f"[TPL-ONB-04] Chứng nhận Phê duyệt Mã Partner & Cổng Thanh toán — {p['name']} ({code})", doc_04),
    ]


def seed_partner_onboarding(dbname=None):
    conn = get_connection(dbname)
    cur = conn.cursor()

    base_partner_table = ensure_schema_columns(cur)

    # Locate DGM Root Folder & 03. Hợp đồng & Thương mại Folder
    cur.execute(
        """
        SELECT id, parent_path FROM documents_document
         WHERE type = 'folder' AND active = TRUE
           AND (name->>'en_US' ILIKE '03. Hợp đồng%' OR name->>'vi_VN' ILIKE '03. Hợp đồng%')
         ORDER BY id ASC LIMIT 1;
        """
    )
    contracts_row = cur.fetchone()
    if not contracts_row:
        cur.execute(
            """
            SELECT id, parent_path FROM documents_document
             WHERE type = 'folder' AND active = TRUE AND folder_id IS NULL
             ORDER BY id ASC LIMIT 1;
            """
        )
        contracts_row = cur.fetchone()

    contracts_folder_id, contracts_parent_path = contracts_row[0], (contracts_row[1] or f"{contracts_row[0]}/")

    # Locate or create `Hồ sơ On-boarding Đối tác (Partner KYC & MSA)` folder under `03. Hợp đồng & Thương mại`
    hub_name = "Hồ sơ On-boarding Đối tác (Partner KYC & MSA)"
    cur.execute(
        """
        SELECT id FROM documents_document
         WHERE type = 'folder' AND folder_id = %s
           AND (name->>'en_US' = %s OR name->>'vi_VN' = %s)
         ORDER BY id ASC LIMIT 1;
        """,
        (contracts_folder_id, hub_name, hub_name),
    )
    hub_row = cur.fetchone()
    if hub_row:
        hub_folder_id = hub_row[0]
        hub_parent_path = f"{contracts_parent_path}{hub_folder_id}/"
        cur.execute(
            """
            UPDATE documents_document
               SET active = TRUE,
                   owner_id = NULL,
                   company_id = NULL,
                   access_internal = 'edit',
                   access_via_link = 'view',
                   parent_path = %s,
                   write_date = NOW()
             WHERE id = %s;
            """,
            (hub_parent_path, hub_folder_id),
        )
    else:
        token = secrets.token_urlsafe(16)
        name_json = json.dumps({"en_US": hub_name, "vi_VN": hub_name})
        cur.execute(
            """
            INSERT INTO documents_document (
                name, type, folder_id, owner_id, company_id,
                access_internal, access_via_link, is_access_via_link_hidden,
                active, sequence, document_token, create_uid, write_uid, create_date, write_date
            ) VALUES (
                %s::jsonb, 'folder', %s, NULL, NULL,
                'edit', 'view', FALSE,
                TRUE, 5, %s, 1, 1, NOW(), NOW()
            ) RETURNING id;
            """,
            (name_json, contracts_folder_id, token),
        )
        hub_folder_id = cur.fetchone()[0]
        hub_parent_path = f"{contracts_parent_path}{hub_folder_id}/"
        cur.execute(
            "UPDATE documents_document SET parent_path = %s WHERE id = %s;",
            (hub_parent_path, hub_folder_id),
        )

    # Seed the 6 canonical DGM partners and their 4 companion documents each
    seeded_summary = []
    for p in CANONICAL_ONBOARDING_PARTNERS:
        pid = None
        if p["vat"]:
            cur.execute(f"SELECT id FROM public.{base_partner_table} WHERE vat = %s ORDER BY id ASC LIMIT 1;", (p["vat"],))
            r = cur.fetchone()
            if r:
                pid = r[0]
        if not pid:
            cur.execute(
                f"SELECT id FROM public.{base_partner_table} WHERE LOWER(TRIM(name)) = LOWER(%s) ORDER BY id ASC LIMIT 1;",
                (p["name"],),
            )
            r = cur.fetchone()
            if r:
                pid = r[0]
        if not pid:
            # Partial name match for VNPT / Viettel-CA / MobiFone
            prefix = p["name"].split("(")[0].strip()
            cur.execute(
                f"SELECT id FROM public.{base_partner_table} WHERE name ILIKE %s ORDER BY id ASC LIMIT 1;",
                (f"%{prefix}%",),
            )
            r = cur.fetchone()
            if r:
                pid = r[0]
        if not pid and p["match_id"]:
            cur.execute(f"SELECT id FROM public.{base_partner_table} WHERE id = %s;", (p["match_id"],))
            r = cur.fetchone()
            if r:
                pid = r[0]

        if not pid:
            raise RuntimeError(f"Canonical partner not found in {dbname}: {p['name']} (run seed_dgm_master_data.py first)")

        # Create or update Partner Subfolder under hub_folder_id
        subfolder_name = f"{p['dgm_partner_code']} · {p['name']}"
        cur.execute(
            """
            SELECT id FROM documents_document
             WHERE type = 'folder' AND folder_id = %s
               AND (partner_id = %s OR name->>'en_US' ILIKE %s)
             ORDER BY id ASC LIMIT 1;
            """,
            (hub_folder_id, pid, f"%{p['dgm_partner_code']}%"),
        )
        sf_row = cur.fetchone()
        if sf_row:
            p_folder_id = sf_row[0]
            p_parent_path = f"{hub_parent_path}{p_folder_id}/"
            sf_json = json.dumps({"en_US": subfolder_name, "vi_VN": subfolder_name})
            cur.execute(
                """
                UPDATE documents_document
                   SET name = %s::jsonb,
                       partner_id = %s,
                       owner_id = NULL,
                       company_id = NULL,
                       access_internal = 'edit',
                       access_via_link = 'view',
                       active = TRUE,
                       parent_path = %s,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (sf_json, pid, p_parent_path, p_folder_id),
            )
        else:
            token = secrets.token_urlsafe(16)
            sf_json = json.dumps({"en_US": subfolder_name, "vi_VN": subfolder_name})
            cur.execute(
                """
                INSERT INTO documents_document (
                    name, type, folder_id, partner_id, owner_id, company_id,
                    access_internal, access_via_link, is_access_via_link_hidden,
                    active, sequence, document_token, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s::jsonb, 'folder', %s, %s, NULL, NULL,
                    'edit', 'view', FALSE,
                    TRUE, 10, %s, 1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (sf_json, hub_folder_id, pid, token),
            )
            p_folder_id = cur.fetchone()[0]
            p_parent_path = f"{hub_parent_path}{p_folder_id}/"
            cur.execute(
                "UPDATE documents_document SET parent_path = %s WHERE id = %s;",
                (p_parent_path, p_folder_id),
            )

        # Generate the 4 companion documents inside p_folder_id
        import hashlib
        templates = render_companion_docs_for_seed(p)
        doc_ids = []
        for tpl_code, filename, doc_name, html_str in templates:
            raw_bytes = html_str.encode("utf-8")
            file_size = len(raw_bytes)
            checksum = hashlib.sha1(raw_bytes).hexdigest()
            doc_json = json.dumps({"en_US": doc_name, "vi_VN": doc_name})

            cur.execute(
                """
                SELECT id, attachment_id FROM documents_document
                 WHERE folder_id = %s AND type != 'folder'
                   AND name->>'en_US' ILIKE %s
                 ORDER BY id ASC LIMIT 1;
                """,
                (p_folder_id, f"%[{tpl_code}]%"),
            )
            d_row = cur.fetchone()
            if d_row:
                doc_id, att_id = d_row
                doc_path = f"{p_parent_path}{doc_id}/"
                cur.execute(
                    """
                    UPDATE documents_document
                       SET name = %s::jsonb,
                           partner_id = %s,
                           owner_id = NULL,
                           company_id = NULL,
                           access_internal = 'edit',
                           access_via_link = 'view',
                           file_extension = 'html',
                           file_size = %s,
                           active = TRUE,
                           parent_path = %s,
                           write_date = NOW()
                     WHERE id = %s;
                    """,
                    (doc_json, pid, file_size, doc_path, doc_id),
                )
                if att_id:
                    cur.execute(
                        """
                        UPDATE ir_attachment
                           SET name = %s,
                               mimetype = 'text/html',
                               file_size = %s,
                               checksum = %s,
                               db_datas = %s,
                               index_content = %s,
                               write_date = NOW()
                         WHERE id = %s;
                        """,
                        (filename, file_size, checksum, psycopg2.Binary(raw_bytes), html_str, att_id),
                    )
            else:
                cur.execute(
                    """
                    INSERT INTO ir_attachment (
                        name, res_model, res_id, company_id, type, mimetype,
                        file_size, checksum, db_datas, index_content,
                        public, create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, 'res.partner', %s, 1, 'binary', 'text/html',
                        %s, %s, %s, %s,
                        FALSE, 1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (filename, pid, file_size, checksum, psycopg2.Binary(raw_bytes), html_str),
                )
                att_id = cur.fetchone()[0]
                token = secrets.token_urlsafe(16)
                cur.execute(
                    """
                    INSERT INTO documents_document (
                        name, type, folder_id, attachment_id, partner_id,
                        owner_id, company_id, access_internal, access_via_link,
                        is_access_via_link_hidden, file_extension, file_size,
                        active, document_token, create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s::jsonb, 'binary', %s, %s, %s,
                        NULL, NULL, 'edit', 'view',
                        FALSE, 'html', %s,
                        TRUE, %s, 1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (doc_json, p_folder_id, att_id, pid, file_size, token),
                )
                doc_id = cur.fetchone()[0]
                doc_path = f"{p_parent_path}{doc_id}/"
                cur.execute(
                    "UPDATE documents_document SET parent_path = %s WHERE id = %s;",
                    (doc_path, doc_id),
                )
                cur.execute(
                    "UPDATE ir_attachment SET res_model = 'documents.document', res_id = %s WHERE id = %s;",
                    (doc_id, att_id),
                )
            doc_ids.append(doc_id)

        # Link M2M dgm_partner_onboarding_doc_rel
        cur.execute("DELETE FROM public.dgm_partner_onboarding_doc_rel WHERE partner_id = %s;", (pid,))
        for did in doc_ids:
            cur.execute(
                """
                INSERT INTO public.dgm_partner_onboarding_doc_rel (partner_id, document_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (pid, did),
            )

        # Update partner onboarding fields
        cur.execute(
            f"""
            UPDATE public.{base_partner_table}
               SET dgm_partner_group = %s,
                   dgm_partner_tier = %s,
                   dgm_tier_score = %s,
                   dgm_credit_limit_vnd = %s,
                   dgm_allowed_payment_rail = %s,
                   dgm_provisional_code = %s,
                   dgm_partner_code = %s,
                   dgm_onboarding_state = %s,
                   dgm_sales_flex_mode = TRUE,
                   dgm_onboarding_folder_id = %s,
                   dgm_onboarding_doc_count = 4,
                   dgm_all_companion_docs_ready = TRUE,
                   dgm_approved_by = 2,
                   dgm_approved_date = COALESCE(dgm_approved_date, NOW()),
                   email = COALESCE(email, %s),
                   write_date = NOW()
             WHERE id = %s;
            """,
            (
                p["dgm_partner_group"],
                p["dgm_partner_tier"],
                p["dgm_tier_score"],
                p["dgm_credit_limit_vnd"],
                p["dgm_allowed_payment_rail"],
                p["dgm_provisional_code"],
                p["dgm_partner_code"],
                p["dgm_onboarding_state"],
                p_folder_id,
                p["email"],
                pid,
            ),
        )
        seeded_summary.append((pid, p["dgm_partner_code"], p["name"], p["dgm_partner_group"], p["dgm_partner_tier"], len(doc_ids)))

        # For AIfin (PTN-DGM-2026-0007), also ensure the dedicated B2B Staff Augmentation Project & Confirmed Sale Order exist
        if p["dgm_partner_code"] == "PTN-DGM-2026-0007":
            prj_name = "AIFin 360-Sales & Onsite Engineering (Trần Văn Huỳnh Phố - DGM-009)"
            cur.execute(
                "SELECT id FROM project_project WHERE partner_id = %s OR name->>'en_US' ILIKE 'AIFin 360-Sales%%' ORDER BY id ASC LIMIT 1;",
                (pid,),
            )
            prj_row = cur.fetchone()
            prj_json = json.dumps({"en_US": prj_name, "vi_VN": prj_name})
            if prj_row:
                aifin_prj_id = prj_row[0]
                cur.execute(
                    "UPDATE project_project SET name = %s::jsonb, partner_id = %s, active = TRUE, write_date = NOW() WHERE id = %s;",
                    (prj_json, pid, aifin_prj_id),
                )
            else:
                cur.execute("SELECT id FROM ir_model WHERE model = 'project.task' LIMIT 1;")
                task_model_id = (cur.fetchone() or [1])[0]
                cur.execute(
                    """
                    INSERT INTO mail_alias (
                        alias_model_id, alias_contact, alias_defaults, create_uid, write_uid, create_date, write_date
                    ) VALUES (%s, 'everyone', '{}', 1, 1, NOW(), NOW())
                    RETURNING id;
                    """,
                    (task_model_id,),
                )
                prj_alias_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO project_project (
                        name, label_tasks, partner_id, company_id, user_id, alias_id,
                        privacy_visibility, last_update_status, billing_type, fleet_classification,
                        active, sequence, allow_timesheets, allow_billable,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s::jsonb, '{"en_US": "Tasks", "vi_VN": "Nhiệm vụ"}'::jsonb, %s, 1, 2, %s,
                        'portal', 'to_define', 'not_billable', 'unknown',
                        TRUE, 15, TRUE, TRUE,
                        1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (prj_json, pid, prj_alias_id),
                )
                aifin_prj_id = cur.fetchone()[0]

            # Find product_id for DGM-ONSITE-STD (or fallback to any service product)
            cur.execute("SELECT id FROM product_product WHERE default_code = 'DGM-ONSITE-STD' LIMIT 1;")
            prod_row = cur.fetchone()
            if not prod_row:
                cur.execute("SELECT id FROM product_product ORDER BY id ASC LIMIT 1;")
                prod_row = cur.fetchone()
            prod_id = prod_row[0]

            # Find VND currency_id and pricelist_id
            cur.execute("SELECT id FROM res_currency WHERE name = 'VND' LIMIT 1;")
            vnd_row = cur.fetchone()
            vnd_id = vnd_row[0] if vnd_row else 23
            cur.execute("SELECT id FROM product_pricelist WHERE currency_id = %s ORDER BY id ASC LIMIT 1;", (vnd_id,))
            pl_row = cur.fetchone()
            if not pl_row:
                cur.execute("SELECT id FROM product_pricelist ORDER BY id ASC LIMIT 1;")
                pl_row = cur.fetchone()
            pl_id = pl_row[0] if pl_row else 1

            cur.execute(
                "SELECT id FROM sale_order WHERE client_order_ref = 'DIGIMATE-AIFIN-VN_2610-001' OR (partner_id = %s AND state = 'sale') ORDER BY id ASC LIMIT 1;",
                (pid,),
            )
            so_row = cur.fetchone()
            if so_row:
                so_id = so_row[0]
                cur.execute(
                    """
                    UPDATE sale_order
                       SET partner_id = %s,
                           partner_invoice_id = %s,
                           partner_shipping_id = %s,
                           client_order_ref = 'DIGIMATE-AIFIN-VN_2610-001',
                           state = 'sale',
                           project_id = %s,
                           amount_untaxed = 256000000.0,
                           amount_tax = 0.0,
                           amount_total = 256000000.0,
                           write_date = NOW()
                     WHERE id = %s;
                    """,
                    (pid, pid, pid, aifin_prj_id, so_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sale_order (
                        name, company_id, partner_id, partner_invoice_id, partner_shipping_id,
                        pricelist_id, currency_id, currency_rate, user_id, team_id,
                        client_order_ref, state, document_tax_mode, invoice_status, picking_policy, warehouse_id,
                        date_order, validity_date, amount_untaxed, amount_tax, amount_total,
                        project_id, require_signature, require_payment, prepayment_percent,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        'SO-DGM-AIFIN-2610', 1, %s, %s, %s,
                        %s, %s, 1.0, 2, 1,
                        'DIGIMATE-AIFIN-VN_2610-001', 'sale', 'tax_excluded', 'to invoice', 'direct', 1,
                        '2026-10-01 09:00:00', '2027-09-30', 256000000.0, 0.0, 256000000.0,
                        %s, TRUE, FALSE, 0.0,
                        1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (pid, pid, pid, pl_id, vnd_id, aifin_prj_id),
                )
                so_id = cur.fetchone()[0]

            # Upsert the 2 canonical sale_order_line rows (Staff Augmentation Trần Văn Huỳnh Phố + 360-Sales Platform)
            cur.execute("DELETE FROM sale_order_line WHERE order_id = %s;", (so_id,))
            lines_to_insert = [
                (
                    10,
                    "Onsite Engineering Services — Project AIFin 360-Sales (Partner: DIGIMATE) — Trần Văn Huỳnh Phố (DGM-009 / PhoTVH) [HĐ DIGIMATE-AIFIN-VN_2610-001 & Phụ lục 2610-001 • Khung 140-180h/tháng]",
                    160.0,
                    350000.0,
                    56000000.0,
                ),
                (
                    20,
                    "Phát triển Hệ thống Phần mềm Quản lý Bán hàng & Đội ngũ Kinh doanh 360-Sales (Web App, Mobile App, Zalo MiniApp, AI Call Coaching) [HĐ AIFIN-DIGIMATE/360-SALES/2026]",
                    1.0,
                    200000000.0,
                    200000000.0,
                ),
            ]
            for seq_no, line_name, qty, p_unit, subtotal in lines_to_insert:
                cur.execute(
                    """
                    INSERT INTO sale_order_line (
                        order_id, sequence, company_id, currency_id, order_partner_id,
                        salesman_id, product_id, name, product_uom_qty, product_uom_id,
                        price_unit, discount, price_subtotal, price_tax, price_total,
                        price_reduce_taxexcl, price_reduce_taxinc,
                        qty_delivered, qty_invoiced, qty_to_invoice,
                        untaxed_amount_invoiced, untaxed_amount_to_invoice,
                        state, invoice_status, customer_lead, is_service, project_id,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, %s, 1, %s, %s,
                        2, %s, %s, %s, 4,
                        %s, 0.0, %s, 0.0, %s,
                        %s, %s,
                        %s, 0.0, %s,
                        0.0, %s,
                        'sale', 'to invoice', 0.0, TRUE, %s,
                        1, 1, NOW(), NOW()
                    );
                    """,
                    (
                        so_id, seq_no, vnd_id, pid,
                        prod_id, line_name, qty,
                        p_unit, subtotal, subtotal,
                        p_unit, p_unit,
                        qty, qty,
                        subtotal,
                        aifin_prj_id,
                    ),
                )

    # Ensure SOP-DGM-06 Knowledge Article exists under DGM SOP Root
    sop_title = "SOP-DGM-06: Quy trình On-boarding Đối tác, Xếp hạng Tier & Cổng Kiểm soát Thanh toán Không Nghẽn Sales"
    sop_body = (
        '<div class="dgm-sop-container">'
        '<h1>SOP-DGM-06: Quy trình On-boarding Đối tác, Xếp hạng Tier &amp; Cổng Kiểm soát Thanh toán Không Nghẽn Sales</h1>'
        '<p><strong>Pháp nhân áp dụng:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC) — MST: <strong>0317958465</strong> — '
        'Đ/c: Số 52 Đường B4, Phường Tây Thạnh (Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ), TP.HCM.</p>'
        '<ul>'
        '<li><strong>Track 1 (Provisional Sales Unblocked):</strong> Cấp ngay mã tạm <code>TMP-DGM-XXXX</code> để Sales báo giá, xác nhận đơn hàng (<code>sale.order.action_confirm</code>) và thu tiền cọc không bị nghẽn.</li>'
        '<li><strong>Track 2 (Companion Docs &amp; Payment Gate):</strong> Tự động khởi tạo 4 biểu mẫu <code>TPL-ONB-01..04</code> (KYC, NDA ISO 27001, MSA/SLA, Payment Gate Cert) và cấp mã chính thức <code>PTN-DGM-2026-XXXX</code> trước kỳ chi thanh toán (Outbound Payment).</li>'
        '</ul></div>'
    )
    cur.execute(
        "SELECT id, parent_path FROM knowledge_article WHERE name ILIKE 'DGM · Quy Trình Vận Hành Chuẩn%' ORDER BY id ASC LIMIT 1;"
    )
    kb_root = cur.fetchone()
    root_kb_id = kb_root[0] if kb_root else None
    cur.execute("SELECT id FROM knowledge_article WHERE name ILIKE 'SOP-DGM-06%' ORDER BY id ASC LIMIT 1;")
    kb_row = cur.fetchone()
    if kb_row:
        cur.execute(
            """
            UPDATE knowledge_article
               SET name = %s,
                   body = %s,
                   parent_id = COALESCE(%s, parent_id),
                   root_article_id = COALESCE(%s, root_article_id),
                   internal_permission = 'write',
                   active = TRUE,
                   write_date = NOW()
             WHERE id = %s;
            """,
            (sop_title, sop_body, root_kb_id, root_kb_id, kb_row[0]),
        )
    else:
        cur.execute(
            """
            INSERT INTO knowledge_article (
                name, icon, body, parent_id, root_article_id,
                internal_permission, category, sequence, active,
                is_article_visible_by_everyone, create_uid, write_uid, create_date, write_date
            ) VALUES (
                %s, '🤝', %s, %s, %s,
                'write', 'workspace', 140, TRUE,
                TRUE, 1, 1, NOW(), NOW()
            );
            """,
            (sop_title, sop_body, root_kb_id, root_kb_id),
        )

    conn.commit()
    print(f"=== SOP-DGM-06 PARTNER ONBOARDING SEED SUMMARY ({dbname or os.environ.get('DB_NAME', 'innoria_prod')}) ===")
    for item in seeded_summary:
        print(f"  [✓] Partner ID={item[0]} | Code={item[1]} | {item[2]} | Group={item[3]} | Tier={item[4]} | Docs={item[5]}/4")
    cur.close()
    conn.close()


if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DB_NAME", "innoria_prod")
    seed_partner_onboarding(target_db)
