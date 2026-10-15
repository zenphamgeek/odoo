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
        cur.execute("SAVEPOINT sp_rp_view;")
        try:
            cur.execute("CREATE OR REPLACE VIEW public.res_partner AS SELECT * FROM public.party_master;")
            cur.execute("RELEASE SAVEPOINT sp_rp_view;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_rp_view;")

    # Ensure SOP-DGM-07 columns on order_header / sale_order
    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'order_header';
        """
    )
    oh_row = cur.fetchone()
    base_so_table = "order_header" if (oh_row and oh_row[0] == "BASE TABLE") else "sale_order"
    so_cols = [
        ("dgm_is_staff_augmentation", "BOOLEAN DEFAULT FALSE"),
        ("dgm_assigned_employee_id", "INTEGER"),
        ("dgm_min_monthly_hours", "DOUBLE PRECISION DEFAULT 140.0"),
        ("dgm_max_standard_hours", "DOUBLE PRECISION DEFAULT 180.0"),
        ("dgm_hourly_rate_vnd", "DOUBLE PRECISION DEFAULT 350000.0"),
        ("dgm_payment_term_days", "INTEGER DEFAULT 40"),
        ("dgm_replacement_notice_days", "INTEGER DEFAULT 30"),
        ("dgm_free_trial_days", "INTEGER DEFAULT 5"),
    ]
    for col, col_def in so_cols:
        cur.execute("SAVEPOINT sp_so_col;")
        try:
            cur.execute(f"ALTER TABLE public.{base_so_table} ADD COLUMN IF NOT EXISTS {col} {col_def};")
            cur.execute("RELEASE SAVEPOINT sp_so_col;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_so_col;")

    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'sale_order';
        """
    )
    so_view_row = cur.fetchone()
    if so_view_row and so_view_row[0] == "VIEW" and base_so_table == "order_header":
        cur.execute("SAVEPOINT sp_so_view;")
        try:
            cur.execute("CREATE OR REPLACE VIEW public.sale_order AS SELECT * FROM public.order_header;")
            cur.execute("RELEASE SAVEPOINT sp_so_view;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_so_view;")

    # Refresh product_template view if backed by catalog_item
    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'catalog_item';
        """
    )
    ci_row = cur.fetchone()
    if ci_row and ci_row[0] == "BASE TABLE":
        for col, col_def in [
            ("al2c_product_line", "VARCHAR"),
            ("al2c_vat_class", "VARCHAR DEFAULT 'kct'"),
            ("al2c_knowledge_article_id", "INTEGER"),
        ]:
            cur.execute("SAVEPOINT sp_ci_col;")
            try:
                cur.execute(f"ALTER TABLE public.catalog_item ADD COLUMN IF NOT EXISTS {col} {col_def};")
                cur.execute("RELEASE SAVEPOINT sp_ci_col;")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT sp_ci_col;")
        cur.execute(
            """
            SELECT table_type FROM information_schema.tables
             WHERE table_schema = 'public' AND table_name = 'product_template';
            """
        )
        pt_row = cur.fetchone()
        if pt_row and pt_row[0] == "VIEW":
            cur.execute("SAVEPOINT sp_pt_view;")
            try:
                cur.execute("CREATE OR REPLACE VIEW public.product_template AS SELECT * FROM public.catalog_item;")
                cur.execute("RELEASE SAVEPOINT sp_pt_view;")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT sp_pt_view;")

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

            # Find or seed SOP-DGM-07 SKUs first so AIfin's SO lines reference SVC-ONSITE-SR and ERP-360-SALES
            cur.execute("SELECT id FROM product_category WHERE name::text ILIKE '%Onsite%' OR name::text ILIKE '%Services%' ORDER BY id DESC LIMIT 1;")
            cat_svc_row = cur.fetchone()
            cat_svc_id = cat_svc_row[0] if cat_svc_row else 1
            cur.execute("SELECT id FROM product_category WHERE name::text ILIKE '%ERP%' ORDER BY id DESC LIMIT 1;")
            cat_erp_row = cur.fetchone()
            cat_erp_id = cat_erp_row[0] if cat_erp_row else cat_svc_id

            cur.execute("SELECT id FROM uom_uom WHERE name->>'en_US' ILIKE 'Hour%' OR id = 4 ORDER BY (CASE WHEN id = 4 THEN 0 ELSE 1 END) LIMIT 1;")
            uom_hour_id = (cur.fetchone() or [4])[0]
            cur.execute("SELECT id FROM uom_uom WHERE name->>'en_US' ILIKE 'Unit%' OR id = 1 ORDER BY (CASE WHEN id = 1 THEN 0 ELSE 1 END) LIMIT 1;")
            uom_unit_id = (cur.fetchone() or [1])[0]

            cur.execute("SELECT id FROM res_currency WHERE name = 'VND' LIMIT 1;")
            vnd_row = cur.fetchone()
            vnd_id = vnd_row[0] if vnd_row else 23
            cur.execute("SELECT id FROM product_pricelist WHERE currency_id = %s ORDER BY id ASC LIMIT 1;", (vnd_id,))
            pl_row = cur.fetchone()
            if not pl_row:
                cur.execute("SELECT id FROM product_pricelist ORDER BY id ASC LIMIT 1;")
                pl_row = cur.fetchone()
            pl_id = pl_row[0] if pl_row else 1

            sop07_skus = [
                {
                    "xmlid": "product_svc_onsite_sr",
                    "code": "SVC-ONSITE-SR",
                    "name": "Dịch vụ Kỹ sư Phần mềm Senior Biệt phái (Staff Augmentation 140-180h)",
                    "categ_id": cat_svc_id,
                    "uom_id": uom_hour_id,
                    "price": 350000.0,
                    "service_type": "timesheet",
                    "service_tracking": "task_in_project",
                    "line": "svc",
                    "vat_class": "vat_8",
                    "desc": "Dịch vụ cung ứng nhân sự kỹ thuật trình độ Senior Biệt phái (Onsite/Remote) theo chuẩn Hợp đồng MTI Technology & AIfin (Khung 140-180h/tháng, OT 100%/150%, Net 40).",
                },
                {
                    "xmlid": "product_svc_onsite_mid",
                    "code": "SVC-ONSITE-MID",
                    "name": "Dịch vụ Kỹ sư Phần mềm Mid-Level Biệt phái (Staff Augmentation 140-180h)",
                    "categ_id": cat_svc_id,
                    "uom_id": uom_hour_id,
                    "price": 250000.0,
                    "service_type": "timesheet",
                    "service_tracking": "task_in_project",
                    "line": "svc",
                    "vat_class": "vat_8",
                    "desc": "Dịch vụ cung ứng nhân sự kỹ thuật trình độ Mid-Level Biệt phái (Khung 140-180h/tháng, thay thế báo trước 30 ngày kèm 05 ngày thử việc miễn phí).",
                },
                {
                    "xmlid": "product_erp_360_sales",
                    "code": "ERP-360-SALES",
                    "name": "Hệ thống Quản trị Bán hàng & Đội ngũ Kinh doanh 360-Sales (Web, Mobile, Zalo MiniApp, AI Call Coaching)",
                    "categ_id": cat_erp_id,
                    "uom_id": uom_unit_id,
                    "price": 200000000.0,
                    "service_type": "milestones",
                    "service_tracking": "project_only",
                    "line": "erp",
                    "vat_class": "kct",
                    "desc": "Giải pháp quản trị bán hàng đa kênh 360-Sales (Web Admin, Mobile App iOS/Android, Zalo MiniApp, AI Call Recording & Coaching, Quản lý KPI & Hoa hồng).",
                },
            ]

            sku_variant_map = {}
            for s in sop07_skus:
                name_json = json.dumps({"en_US": s["name"], "vi_VN": s["name"]})
                desc_json = json.dumps({"en_US": s["desc"], "vi_VN": s["desc"]})
                cur.execute("SELECT id FROM catalog_item WHERE default_code = %s ORDER BY id ASC LIMIT 1;", (s["code"],))
                ci_row = cur.fetchone()
                if ci_row:
                    tmpl_id = ci_row[0]
                    cur.execute(
                        """
                        UPDATE catalog_item
                           SET name = %s::jsonb,
                               categ_id = %s,
                               uom_id = %s,
                               list_price = %s,
                               type = 'service',
                               sale_ok = TRUE,
                               purchase_ok = FALSE,
                               active = TRUE,
                               invoice_policy = 'delivery',
                               service_type = %s,
                               service_tracking = %s,
                               al2c_product_line = %s,
                               al2c_vat_class = %s,
                               description_sale = %s::jsonb,
                               write_date = NOW()
                         WHERE id = %s;
                        """,
                        (
                            name_json, s["categ_id"], s["uom_id"], s["price"],
                            s["service_type"], s["service_tracking"], s["line"], s["vat_class"],
                            desc_json, tmpl_id,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO catalog_item (
                            name, default_code, categ_id, uom_id, list_price,
                            type, sale_ok, purchase_ok, active,
                            invoice_policy, service_type, service_tracking,
                            al2c_product_line, al2c_vat_class, description_sale,
                            base_unit_count, urbanpiper_meal_type,
                            create_uid, write_uid, create_date, write_date
                        ) VALUES (
                            %s::jsonb, %s, %s, %s, %s,
                            'service', TRUE, FALSE, TRUE,
                            'delivery', %s, %s,
                            %s, %s, %s::jsonb,
                            0, 'none',
                            1, 1, NOW(), NOW()
                        ) RETURNING id;
                        """,
                        (
                            name_json, s["code"], s["categ_id"], s["uom_id"], s["price"],
                            s["service_type"], s["service_tracking"],
                            s["line"], s["vat_class"], desc_json,
                        ),
                    )
                    tmpl_id = cur.fetchone()[0]

                cur.execute("SELECT id FROM catalog_sku WHERE product_tmpl_id = %s ORDER BY id ASC LIMIT 1;", (tmpl_id,))
                cs_row = cur.fetchone()
                if cs_row:
                    var_id = cs_row[0]
                    cur.execute(
                        """
                        UPDATE catalog_sku
                           SET default_code = %s,
                               lst_price = %s,
                               active = TRUE,
                               write_date = NOW()
                         WHERE id = %s;
                        """,
                        (s["code"], s["price"], var_id),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO catalog_sku (
                            product_tmpl_id, default_code, lst_price, base_unit_count,
                            active, create_uid, write_uid, create_date, write_date
                        ) VALUES (
                            %s, %s, %s, 0,
                            TRUE, 1, 1, NOW(), NOW()
                        ) RETURNING id;
                        """,
                        (tmpl_id, s["code"], s["price"]),
                    )
                    var_id = cur.fetchone()[0]
                sku_variant_map[s["code"]] = var_id

                # Upsert ir_model_data for template & variant
                for imd_name, imd_model, imd_res_id in [
                    (s["xmlid"], "product.template", tmpl_id),
                    (f"{s['xmlid']}_variant", "product.product", var_id),
                ]:
                    cur.execute(
                        "SELECT id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = %s LIMIT 1;",
                        (imd_name,),
                    )
                    imd_r = cur.fetchone()
                    if imd_r:
                        cur.execute(
                            "UPDATE ir_model_data SET model = %s, res_id = %s, write_date = NOW() WHERE id = %s;",
                            (imd_model, imd_res_id, imd_r[0]),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO ir_model_data (module, name, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
                            VALUES ('insilos_al2c', %s, %s, %s, FALSE, 1, 1, NOW(), NOW());
                            """,
                            (imd_name, imd_model, imd_res_id),
                        )

                # Upsert product_pricelist_item in VND pricelist
                cur.execute(
                    "SELECT id FROM product_pricelist_item WHERE pricelist_id = %s AND product_tmpl_id = %s LIMIT 1;",
                    (pl_id, tmpl_id),
                )
                pli_r = cur.fetchone()
                if pli_r:
                    cur.execute(
                        "UPDATE product_pricelist_item SET compute_price = 'fixed', fixed_price = %s, write_date = NOW() WHERE id = %s;",
                        (s["price"], pli_r[0]),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO product_pricelist_item (
                            pricelist_id, company_id, currency_id, applied_on, base,
                            compute_price, product_tmpl_id, fixed_price, min_quantity,
                            create_uid, write_uid, create_date, write_date
                        ) VALUES (
                            %s, 1, %s, '1_product', 'list_price',
                            'fixed', %s, %s, 0.0,
                            1, 1, NOW(), NOW()
                        );
                        """,
                        (pl_id, vnd_id, tmpl_id, s["price"]),
                    )

            # Upsert sale_tpl_staff_augmentation quotation template
            sot_name = "Hợp đồng Thuê Nhân sự Kỹ thuật B2B (MTI / AIfin Staff Augmentation — Khung 140-180h)"
            sot_note = (
                "<p>ĐIỀU KHOẢN THƯƠNG MẠI CHUẨN (SOP-DGM-07): Khung giờ chuẩn 140–180 giờ/tháng; "
                "OT ngày thường 100%, OT cuối tuần/lễ 150%; Thanh toán Net 40 ngày làm việc; "
                "Thay thế nhân sự báo trước 30 ngày kèm 05 ngày làm việc thử việc miễn phí.</p>"
            )
            sot_name_json = json.dumps({"en_US": sot_name, "vi_VN": sot_name})
            sot_note_json = json.dumps({"en_US": sot_note, "vi_VN": sot_note})
            cur.execute(
                "SELECT id FROM sale_order_template WHERE name->>'en_US' = %s OR name->>'vi_VN' = %s LIMIT 1;",
                (sot_name, sot_name),
            )
            sot_r = cur.fetchone()
            if sot_r:
                sot_id = sot_r[0]
                cur.execute(
                    "UPDATE sale_order_template SET name = %s::jsonb, note = %s::jsonb, active = TRUE, write_date = NOW() WHERE id = %s;",
                    (sot_name_json, sot_note_json, sot_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sale_order_template (
                        company_id, sequence, template_type, name, note,
                        active, require_signature, share_template, prepayment_percent,
                        duration_value, duration_unit, is_unlimited,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        1, 25, 'quotation', %s::jsonb, %s::jsonb,
                        TRUE, TRUE, TRUE, 0.0,
                        1, 'month', TRUE,
                        1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (sot_name_json, sot_note_json),
                )
                sot_id = cur.fetchone()[0]

            cur.execute(
                "SELECT id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = 'sale_tpl_staff_augmentation' LIMIT 1;"
            )
            sot_imd = cur.fetchone()
            if sot_imd:
                cur.execute(
                    "UPDATE ir_model_data SET model = 'sale.order.template', res_id = %s, write_date = NOW() WHERE id = %s;",
                    (sot_id, sot_imd[0]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO ir_model_data (module, name, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
                    VALUES ('insilos_al2c', 'sale_tpl_staff_augmentation', 'sale.order.template', %s, FALSE, 1, 1, NOW(), NOW());
                    """,
                    (sot_id,),
                )

            cur.execute("SELECT id FROM catalog_sku WHERE default_code = 'CONSULT-HOUR' LIMIT 1;")
            consult_var_id = (cur.fetchone() or [sku_variant_map["SVC-ONSITE-SR"]])[0]
            cur.execute("DELETE FROM sale_order_template_line WHERE sale_order_template_id = %s;", (sot_id,))
            for seq_l, p_var_id, l_desc, l_qty in [
                (10, sku_variant_map["SVC-ONSITE-SR"], "Kỹ sư Phần mềm Senior Biệt phái (Cam kết SLA 140–180 giờ/tháng — Tạm tính chuẩn 160 giờ)", 160.0),
                (20, consult_var_id, "Giờ Tư vấn Kiến trúc Giải pháp & Code Review (Solution Architect Oversight)", 16.0),
            ]:
                cur.execute(
                    """
                    INSERT INTO sale_order_template_line (
                        sale_order_template_id, sequence, company_id, product_id,
                        name, product_uom_qty, product_uom_id,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, %s, 1, %s,
                        %s::jsonb, %s, %s,
                        1, 1, NOW(), NOW()
                    );
                    """,
                    (sot_id, seq_l, p_var_id, json.dumps({"en_US": l_desc, "vi_VN": l_desc}), l_qty, uom_hour_id),
                )

            # Find DGM-009 employee_id (Trần Văn Huỳnh Phố)
            cur.execute("SELECT id FROM hr_employee WHERE registration_number = 'DGM-009' OR name ILIKE '%Trần Văn Huỳnh Phố%' ORDER BY id ASC LIMIT 1;")
            emp_pho_row = cur.fetchone()
            emp_pho_id = emp_pho_row[0] if emp_pho_row else None

            prod_sr_id = sku_variant_map["SVC-ONSITE-SR"]
            prod_360_id = sku_variant_map["ERP-360-SALES"]

            cur.execute(
                "SELECT table_type FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'order_header';"
            )
            oh_check = cur.fetchone()
            so_tbl = "order_header" if (oh_check and oh_check[0] == "BASE TABLE") else "sale_order"

            cur.execute(
                f"SELECT id FROM {so_tbl} WHERE client_order_ref = 'DIGIMATE-AIFIN-VN_2610-001' OR (partner_id = %s AND state = 'sale') ORDER BY id ASC LIMIT 1;",
                (pid,),
            )
            so_row = cur.fetchone()
            if so_row:
                so_id = so_row[0]
                cur.execute(
                    f"""
                    UPDATE {so_tbl}
                       SET partner_id = %s,
                           partner_invoice_id = %s,
                           partner_shipping_id = %s,
                           client_order_ref = 'DIGIMATE-AIFIN-VN_2610-001',
                           state = 'sale',
                           project_id = %s,
                           dgm_is_staff_augmentation = TRUE,
                           dgm_assigned_employee_id = %s,
                           dgm_min_monthly_hours = 140.0,
                           dgm_max_standard_hours = 180.0,
                           dgm_hourly_rate_vnd = 350000.0,
                           dgm_payment_term_days = 40,
                           dgm_replacement_notice_days = 30,
                           dgm_free_trial_days = 5,
                           amount_untaxed = 256000000.0,
                           amount_tax = 0.0,
                           amount_total = 256000000.0,
                           write_date = NOW()
                     WHERE id = %s;
                    """,
                    (pid, pid, pid, aifin_prj_id, emp_pho_id, so_id),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO {so_tbl} (
                        name, company_id, partner_id, partner_invoice_id, partner_shipping_id,
                        pricelist_id, currency_id, currency_rate, user_id, team_id,
                        client_order_ref, state, document_tax_mode, invoice_status, picking_policy, warehouse_id,
                        date_order, validity_date, amount_untaxed, amount_tax, amount_total,
                        project_id, dgm_is_staff_augmentation, dgm_assigned_employee_id,
                        dgm_min_monthly_hours, dgm_max_standard_hours, dgm_hourly_rate_vnd,
                        dgm_payment_term_days, dgm_replacement_notice_days, dgm_free_trial_days,
                        require_signature, require_payment, prepayment_percent,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        'SO-DGM-AIFIN-2610', 1, %s, %s, %s,
                        %s, %s, 1.0, 2, 1,
                        'DIGIMATE-AIFIN-VN_2610-001', 'sale', 'tax_excluded', 'to invoice', 'direct', 1,
                        '2026-10-01 09:00:00', '2027-09-30', 256000000.0, 0.0, 256000000.0,
                        %s, TRUE, %s,
                        140.0, 180.0, 350000.0,
                        40, 30, 5,
                        TRUE, FALSE, 0.0,
                        1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (pid, pid, pid, pl_id, vnd_id, aifin_prj_id, emp_pho_id),
                )
                so_id = cur.fetchone()[0]

            # Upsert the 2 canonical sale_order_line rows (SVC-ONSITE-SR Trần Văn Huỳnh Phố + ERP-360-SALES Platform)
            cur.execute("DELETE FROM sale_order_line WHERE order_id = %s;", (so_id,))
            lines_to_insert = [
                (
                    10,
                    prod_sr_id,
                    uom_hour_id,
                    "Onsite Engineering Services — Project AIFin 360-Sales (Partner: DIGIMATE) — Trần Văn Huỳnh Phố (DGM-009 / PhoTVH) [HĐ DIGIMATE-AIFIN-VN_2610-001 & Phụ lục 2610-001 • Khung 140-180h/tháng]",
                    160.0,
                    350000.0,
                    56000000.0,
                ),
                (
                    20,
                    prod_360_id,
                    uom_unit_id,
                    "Phát triển Hệ thống Phần mềm Quản lý Bán hàng & Đội ngũ Kinh doanh 360-Sales (Web App, Mobile App, Zalo MiniApp, AI Call Coaching) [HĐ AIFIN-DIGIMATE/360-SALES/2026]",
                    1.0,
                    200000000.0,
                    200000000.0,
                ),
            ]
            for seq_no, line_prod_id, line_uom_id, line_name, qty, p_unit, subtotal in lines_to_insert:
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
                        2, %s, %s, %s, %s,
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
                        line_prod_id, line_name, qty, line_uom_id,
                        p_unit, subtotal, subtotal,
                        p_unit, p_unit,
                        qty, qty,
                        subtotal,
                        aifin_prj_id,
                    ),
                )

    # Ensure SOP-DGM-06 & SOP-DGM-07 Knowledge Articles exist under DGM SOP Root
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

    sop07_title = "SOP-DGM-07: Quy trình Quản trị Hợp đồng Thuê Nhân sự Kỹ thuật B2B (MTI / AIfin), Đối soát Khung giờ 140–180h & Nghiệm thu Thanh toán Net 40"
    sop07_body = (
        '<div class="o_knowledge_behavior_anchor">'
        '<h1>SOP-DGM-07: QUY TRÌNH QUẢN TRỊ HỢP ĐỒNG BIỆT PHÁI NHÂN SỰ KỸ THUẬT (STAFF AUGMENTATION 140–180H &amp; NET 40)</h1>'
        '<p><strong>Mã tài liệu:</strong> SOP-DGM-07 | <strong>Phiên bản:</strong> 1.0 (2026) | <strong>Áp dụng:</strong> Khối Kinh doanh B2B, Khối Delivery, Kế toán &amp; Pháp chế (Chuẩn hóa từ Hợp đồng MTI Technology &amp; AIfin)</p>'
        '<ul>'
        '<li><strong>SKU Kỹ sư Senior Biệt phái (<code>SVC-ONSITE-SR</code>):</strong> 350,000 VNĐ/giờ (~56,000,000 VNĐ/tháng chuẩn 160h).</li>'
        '<li><strong>SKU Kỹ sư Mid-Level Biệt phái (<code>SVC-ONSITE-MID</code>):</strong> 250,000 VNĐ/giờ (~40,000,000 VNĐ/tháng chuẩn 160h).</li>'
        '<li><strong>SKU Giải pháp 360-Sales (<code>ERP-360-SALES</code>):</strong> 200,000,000 VNĐ/gói (Triển khai theo Milestone: Web, Mobile, Zalo MiniApp, AI Call Coaching).</li>'
        '<li><strong>Khung SLA 140–180 giờ/tháng:</strong> OT ngày thường 100%, OT cuối tuần/lễ 150%, Thanh toán Net 40 ngày làm việc, Thay thế nhân sự báo trước 30 ngày kèm 05 ngày làm việc thử việc miễn phí (40 giờ).</li>'
        '</ul></div>'
    )
    cur.execute("SELECT id FROM knowledge_article WHERE name ILIKE 'SOP-DGM-07%' ORDER BY id ASC LIMIT 1;")
    kb07_row = cur.fetchone()
    if kb07_row:
        kb07_id = kb07_row[0]
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
            (sop07_title, sop07_body, root_kb_id, root_kb_id, kb07_id),
        )
    else:
        cur.execute(
            """
            INSERT INTO knowledge_article (
                name, icon, body, parent_id, root_article_id,
                internal_permission, category, sequence, active,
                is_article_visible_by_everyone, create_uid, write_uid, create_date, write_date
            ) VALUES (
                %s, '👨‍💻', %s, %s, %s,
                'write', 'workspace', 150, TRUE,
                TRUE, 1, 1, NOW(), NOW()
            ) RETURNING id;
            """,
            (sop07_title, sop07_body, root_kb_id, root_kb_id),
        )
        kb07_id = cur.fetchone()[0]

    cur.execute(
        "SELECT id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = 'kb_dgm_sop_07_staff_augmentation' LIMIT 1;"
    )
    kb07_imd = cur.fetchone()
    if kb07_imd:
        cur.execute(
            "UPDATE ir_model_data SET model = 'knowledge.article', res_id = %s, write_date = NOW() WHERE id = %s;",
            (kb07_id, kb07_imd[0]),
        )
    else:
        cur.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
            VALUES ('insilos_al2c', 'kb_dgm_sop_07_staff_augmentation', 'knowledge.article', %s, FALSE, 1, 1, NOW(), NOW());
            """,
            (kb07_id,),
        )

    conn.commit()
    print(f"=== SOP-DGM-06 & SOP-DGM-07 PARTNER ONBOARDING + STAFF AUGMENTATION SEED SUMMARY ({dbname or os.environ.get('DB_NAME', 'innoria_prod')}) ===")
    for item in seeded_summary:
        print(f"  [✓] Partner ID={item[0]} | Code={item[1]} | {item[2]} | Group={item[3]} | Tier={item[4]} | Docs={item[5]}/4")
    print("  [✓] Seeded SKUs: SVC-ONSITE-SR (350,000 VND/h), SVC-ONSITE-MID (250,000 VND/h), ERP-360-SALES (200,000,000 VND)")
    print("  [✓] Seeded Quotation Template: sale_tpl_staff_augmentation & Knowledge Article: SOP-DGM-07")
    cur.close()
    conn.close()


if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DB_NAME", "innoria_prod")
    seed_partner_onboarding(target_db)
