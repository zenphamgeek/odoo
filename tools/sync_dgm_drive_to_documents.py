#!/usr/bin/env python3
"""
Idempotent ORM Synchronization & Classification Engine:
Ingests all 31 folders & 163 files from info@inno.ai.vn Google Drive (/tmp/dgm_drive_sync/dgm_manifest.json)
into `documents.document` + `ir.attachment` + `documents.tag` in `insilos20_dev`,
and populates DGM (Digimate JSC / Công ty Cổ phần Người Bạn Số - MST 0317958465)
SOP Knowledge Articles (`knowledge.article`) + RAG Chunks (`al2c.rag.chunk`).
"""
import base64
import json
import mimetypes
import os
import re
import sys

sys.path.insert(0, "/home/zen/O20")
import odoo
from odoo import api, SUPERUSER_ID


def normalize_folder_segment(seg):
    return re.sub(r"\s*\(Root Shared\)\s*$", "", seg or "", flags=re.IGNORECASE).strip()


def normalize_folder_path(fpath):
    if not fpath:
        return ""
    return "/".join(normalize_folder_segment(p) for p in fpath.split("/") if p)


MANIFEST_PATH = "/tmp/dgm_drive_sync/dgm_manifest.json"
SOPS_DIR = "/tmp/dgm_drive_sync/sops"
DB_NAME = os.environ.get("DGM_TARGET_DB", "insilos20_dev")

TOP_FOLDER_MAP = {
    "DGM - ĐKTL": (
        "folder_dgm_legal",
        "01. Pháp lý & Hành chính (Legal & Corporate)",
        "edit",
        1,
    ),
    "DGM - TÀI CHÍNH": (
        "folder_dgm_finance",
        "02. Tài chính - Kế toán - Thuế (Finance & Tax)",
        "edit",
        2,
    ),
    "DGM - HỢP ĐỒNG": (
        "folder_dgm_contracts",
        "03. Hợp đồng & Thương mại (Commercial & Contracts)",
        "edit",
        3,
    ),
    "DGM - NHÂN SỰ": (
        "folder_dgm_hr",
        "04. Nhân sự & Tiền lương (HR, Payroll & BHXH)",
        "edit",
        4,
    ),
    "DGM - SỞ HỮU TRÍ TUỆ": (
        "folder_dgm_ip",
        "05. Sở hữu Trí tuệ & Sản phẩm (IP & Tech Assets)",
        "edit",
        5,
    ),
    "DGM- HÌNH ẢNH 2025": (
        "folder_dgm_brand",
        "06. Thương hiệu & Hình ảnh (Brand & Media)",
        "edit",
        6,
    ),
}

SOP_FOLDER_DEF = (
    "folder_dgm_sops",
    "07. Quy trình Chuẩn & Tự động hóa (SOP & ERP Blueprints)",
    "edit",
    7,
)

SOP_FILES = [
    "DGM_DIGIMATE_ERP_OPERATIONAL_BLUEPRINT.md",
    "COUNCIL_SYNTHESIS_MASTER_REFERENCE.md",
    "DGM_AUTONOMOUS_COMPLIANCE_AUDIT_REPORT.md",
    "SRS_AL2C_Innoria_Insilos.md",
]

TAG_DEFS = {
    "legal": ("tag_dgm_legal", "DGM > 01. Pháp lý & ĐKTL", 50),
    "finance_tax": ("tag_dgm_finance_tax", "DGM > 02. Tài chính & Quyết toán Thuế", 51),
    "invoice_out": ("tag_dgm_invoice_out", "DGM > 03. Hóa đơn Đầu ra (Canva / Xuất khẩu)", 52),
    "invoice_in": ("tag_dgm_invoice_in", "DGM > 04. Hóa đơn Đầu vào (VNPT / Viettel)", 53),
    "bhxh": ("tag_dgm_bhxh", "DGM > 05. BHXH (C12-TS · TZ0857G)", 54),
    "payroll": ("tag_dgm_payroll", "DGM > 06. Bảng lương & VCB DigiBiz", 55),
    "contract_comm": ("tag_dgm_contract_comm", "DGM > 07. Hợp đồng Thương mại (MTI / MBF / US DPA)", 56),
    "hr_records": ("tag_dgm_hr_records", "DGM > 08. Hồ sơ Nhân sự & HĐLĐ", 57),
    "ip_copyright": ("tag_dgm_ip_copyright", "DGM > 09. Sở hữu Trí tuệ (Mojo AI Copyright)", 58),
    "brand_media": ("tag_dgm_brand_media", "DGM > 10. Thương hiệu & Media", 59),
    "rev_risk": ("tag_dgm_rev_risk_control", "DGM > Khung Kiểm soát Rủi ro Doanh thu AI", 60),
    "sop_blueprint": ("tag_dgm_sop_blueprint", "DGM > 11. Quy trình Chuẩn & Blueprint ERP", 61),
}


def ensure_xmlid(env, module, name, model, res_id):
    imd = env["ir.model.data"].sudo().search([("module", "=", module), ("name", "=", name)], limit=1)
    if imd:
        imd.write({"res_id": res_id, "model": model})
    else:
        env["ir.model.data"].sudo().create({
            "module": module,
            "name": name,
            "model": model,
            "res_id": res_id,
            "noupdate": True,
        })


def get_or_create_tag(env, key):
    xmlid_name, tag_name, seq = TAG_DEFS[key]
    imd = env["ir.model.data"].sudo().search([("module", "=", "insilos_al2c"), ("name", "=", xmlid_name)], limit=1)
    if imd and imd.res_id:
        rec = env["documents.tag"].sudo().browse(imd.res_id).exists()
        if rec:
            return rec
    rec = env["documents.tag"].sudo().search([("name", "=", tag_name)], limit=1)
    if not rec:
        rec = env["documents.tag"].sudo().create({"name": tag_name, "sequence": seq})
    ensure_xmlid(env, "insilos_al2c", xmlid_name, "documents.tag", rec.id)
    return rec


def classify_tags_for_entry(entry, tags_map, core_tags):
    rel = entry["rel_path"]
    name_up = entry["name"].upper()
    res_tags = []

    if rel.startswith("DGM - ĐKTL"):
        res_tags.append(tags_map["legal"].id)
        if core_tags.get("compliance"):
            res_tags.append(core_tags["compliance"].id)
        if core_tags.get("conf_confidential"):
            res_tags.append(core_tags["conf_confidential"].id)
    elif rel.startswith("DGM - TÀI CHÍNH"):
        res_tags.append(tags_map["finance_tax"].id)
        if "HOÁ ĐƠN ĐẦU RA" in rel.upper() or "CANVA" in name_up:
            res_tags.append(tags_map["invoice_out"].id)
            if core_tags.get("line_mojo"):
                res_tags.append(core_tags["line_mojo"].id)
        elif "HOÁ ĐƠN ĐẦU VÀO" in rel.upper():
            res_tags.append(tags_map["invoice_in"].id)
        elif "BHXH" in rel.upper() or "TZ0857G" in name_up:
            res_tags.append(tags_map["bhxh"].id)
        elif "LƯƠNG" in rel.upper() or "LUONG" in name_up or "DIGIBIZ" in name_up:
            res_tags.append(tags_map["payroll"].id)
        elif "RỦI RO DOANH THU" in name_up or "MOJO AI" in name_up:
            res_tags.append(tags_map["rev_risk"].id)
            if core_tags.get("line_ai"):
                res_tags.append(core_tags["line_ai"].id)
        if core_tags.get("conf_confidential"):
            res_tags.append(core_tags["conf_confidential"].id)
    elif rel.startswith("DGM - HỢP ĐỒNG"):
        res_tags.append(tags_map["contract_comm"].id)
        if core_tags.get("contract"):
            res_tags.append(core_tags["contract"].id)
        if "MBF" in rel.upper() or "MOBIAI" in name_up:
            if core_tags.get("line_ai"):
                res_tags.append(core_tags["line_ai"].id)
        elif "TÀI BÙI" in rel.upper() or "MTI" in name_up or "AIFIN" in rel.upper() or "AIFIN" in name_up:
            if core_tags.get("line_svc"):
                res_tags.append(core_tags["line_svc"].id)
            if "360-SALES" in name_up and core_tags.get("line_erp"):
                res_tags.append(core_tags["line_erp"].id)
        if core_tags.get("conf_confidential"):
            res_tags.append(core_tags["conf_confidential"].id)
    elif rel.startswith("DGM - NHÂN SỰ"):
        res_tags.append(tags_map["hr_records"].id)
        if core_tags.get("conf_confidential"):
            res_tags.append(core_tags["conf_confidential"].id)
    elif rel.startswith("DGM - SỞ HỮU TRÍ TUỆ"):
        res_tags.append(tags_map["ip_copyright"].id)
        if core_tags.get("line_mojo"):
            res_tags.append(core_tags["line_mojo"].id)
        if core_tags.get("conf_internal"):
            res_tags.append(core_tags["conf_internal"].id)
    elif rel.startswith("DGM- HÌNH ẢNH 2025"):
        res_tags.append(tags_map["brand_media"].id)
        if core_tags.get("marketing"):
            res_tags.append(core_tags["marketing"].id)
        if core_tags.get("conf_public"):
            res_tags.append(core_tags["conf_public"].id)

    return list(set(res_tags))


def build_dgm_knowledge_articles(env):
    Article = env["knowledge.article"].sudo()

    def upsert_article(xmlid_name, name, icon, parent_id, seq, body_html):
        imd = env["ir.model.data"].sudo().search(
            [("module", "=", "insilos_al2c"), ("name", "=", xmlid_name)], limit=1
        )
        art = False
        if imd and imd.res_id:
            art = Article.browse(imd.res_id).exists()
        if not art:
            art = Article.search([("name", "=", name), ("parent_id", "=", parent_id or False)], limit=1)
        vals = {
            "name": name,
            "icon": icon,
            "parent_id": parent_id or False,
            "sequence": seq,
            "internal_permission": "write",
            "body": body_html,
        }
        if art:
            art.write(vals)
        else:
            art = Article.create(vals)
        ensure_xmlid(env, "insilos_al2c", xmlid_name, "knowledge.article", art.id)
        env["al2c.rag.service"].sudo().index_knowledge_article(art)
        return art

    root_art = upsert_article(
        "kb_dgm_sop_root",
        "DGM · Quy Trình Vận Hành Chuẩn (Digimate JSC - MST 0317958465)",
        "🏛️",
        False,
        8,
        """<h1>Hệ Thống Quy Trình Vận Hành Chuẩn (SOP) — Công ty Cổ phần Người Bạn Số (Digimate JSC / DGM)</h1>
        <p><strong>Pháp nhân:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (Tên quốc tế: <em>DIGITAL MATE JOINT STOCK COMPANY</em> — Viết tắt: <strong>DIGIMATE / DGM</strong>).</p>
        <p><strong>Mã số doanh nghiệp / MST:</strong> <code>0317958465</code> (Cấp lần đầu ngày 28/07/2023 bởi Sở KH&amp;ĐT TP.HCM; cập nhật ĐKKD &amp; Chủ sở hữu hưởng lợi ngày 19/01/2026).</p>
        <p><strong>Địa chỉ trụ sở chính &amp; Nhận thông báo thuế:</strong> Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ (trước đây là Phường Tân Phú, Quận 7), TP. Hồ Chí Minh, Việt Nam.</p>
        <p><strong>Tài khoản Ngân hàng Chính:</strong> Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank) — Số TK: <code>1202703007</code> — Chủ TK: CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ.</p>
        <p><strong>Đại diện theo pháp luật:</strong> Ông <strong>Lê Xuân Hoàng</strong> (Chủ tịch HĐQT kiêm Tổng Giám đốc — tỷ lệ sở hữu 50% vốn điều lệ).</p>""",
    )

    upsert_article(
        "kb_dgm_sop_01_governance",
        "SOP-DGM-01 · Quản Trị Pháp Lý, Cổ Đông & Chủ Sở Hữu Hưởng Lợi (ĐKTL)",
        "⚖️",
        root_art.id,
        1,
        """<h1>SOP-DGM-01 · Quản Trị Hồ Sơ Pháp Lý, Cổ Đông &amp; Chủ Sở Hữu Hưởng Lợi</h1>
        <h2>1. Cơ cấu Vốn Điều lệ &amp; Cổ đông Sáng lập (300.000 cổ phần = 100%)</h2>
        <table>
            <thead><tr><th>STT</th><th>Họ và tên Cổ đông</th><th>Vai trò</th><th>Số cổ phần</th><th>Tỷ lệ sở hữu</th><th>Phân loại CSH Hưởng lợi (≥25%)</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>Ông Lê Xuân Hoàng</td><td>Chủ tịch HĐQT / Tổng Giám đốc / Đại diện Pháp luật</td><td>150.000</td><td>50%</td><td>Chủ sở hữu hưởng lợi (CCCD: 089094016917)</td></tr>
                <tr><td>2</td><td>Bà Mai Thị Hồng Thắm</td><td>Cổ đông sáng lập / Thư ký ĐHĐCĐ / Tài chính - Nhân sự</td><td>90.000</td><td>30%</td><td>Chủ sở hữu hưởng lợi (CCCD: 093197003049)</td></tr>
                <tr><td>3</td><td>Ông Nguyễn Hoài Ân</td><td>Cổ đông sáng lập / Kỹ thuật &amp; Sản phẩm</td><td>60.000</td><td>20%</td><td>Cổ đông sáng lập (&lt;25%)</td></tr>
            </tbody>
        </table>
        <h2>2. Quy trình Cập nhật Đăng ký Doanh nghiệp &amp; Lưu trữ Hồ sơ Pháp lý</h2>
        <ul>
            <li>Mọi thay đổi địa giới hành chính hoặc nội dung ĐKKD (như đợt cập nhật Phường Tân Phú, Quận 7 sang Phường Tân Mỹ, TP.HCM ngày 19/01/2026 theo Biên bản họp số <code>01/BBH-ĐHĐCĐ</code> và Quyết định số <code>0126/QĐ-ĐHĐCĐ</code>) phải lập đầy đủ bộ 5 văn bản: Thông báo thay đổi, Danh sách Chủ sở hữu hưởng lợi, Biên bản họp ĐHĐCĐ, Quyết định ĐHĐCĐ và Giấy Ủy quyền.</li>
            <li>Lưu trữ bắt buộc bản scan PDF có chữ ký &amp; dấu đỏ trong thư mục <code>01. Pháp lý &amp; Quản trị Doanh nghiệp (DGM - ĐKTL)</code> trên phân hệ Documents và đồng bộ thông tin địa chỉ trên chữ ký số Viettel-CA / hóa đơn điện tử SInvoice / cơ quan Thuế và BHXH Quận 7 (Mã đơn vị: <code>TZ0857G</code>).</li>
        </ul>""",
    )

    upsert_article(
        "kb_dgm_sop_02_revenue_risk",
        "SOP-DGM-02 · Khung Kiểm Soát Rủi Ro Doanh Thu AI & Digital Business (Mojo AI, Canva, App Store, Google Play)",
        "🛡️",
        root_art.id,
        2,
        """<h1>SOP-DGM-02 · Khung Kiểm Soát Rủi Ro Doanh Thu AI &amp; Digital Business</h1>
        <p>Áp dụng cho toàn bộ các sản phẩm AI &amp; SaaS của Digimate JSC: <strong>Mojo AI</strong>, <strong>Gen Logo</strong>, <strong>Gen QR Art</strong>, <strong>Reface</strong> trên 5 kênh thu tiền xuyên biên giới và nội địa.</p>
        <h2>1. Nguyên tắc Kiểm soát Cốt lõi (5 Chốt chặn Pháp lý &amp; Thuế)</h2>
        <ol>
            <li><strong>Định danh Pháp nhân 100%:</strong> Tài khoản PayPal Business, Apple Developer Program (Organization), Google Play Console (Organization), Google AdMob và Canva Developers Portal phải đứng tên pháp nhân <code>DIGITAL MATE JOINT STOCK COMPANY</code>, nhận tiền trực tiếp về tài khoản Vietcombank công ty (<code>1202703007</code>). Tuyệt đối không nhận doanh thu sản phẩm công ty qua tài khoản PayPal/ngân hàng cá nhân.</li>
            <li><strong>Tuân thủ Luật Thương mại Điện tử 2025 &amp; Nghị định 248/2026 (hiệu lực 01/07/2026):</strong> Nếu website có luồng <em>Pricing → Buy → PayPal → Cấp phát Credit/AI Service</em>, phải hoàn tất thủ tục Thông báo Website TMĐT bán hàng với Bộ Công Thương trước khi mở cổng thanh toán trực tiếp.</li>
            <li><strong>Truy vết Chuỗi Dữ liệu 6 Bước (End-to-End Audit Trail):</strong> <code>Transaction/Platform Event → Order/Award Notice → Commercial/VAT Invoice → Settlement Statement → Bank Credit Advice (Sổ phụ VCB) → Sổ cái Kế toán &amp; Tờ khai Thuế</code>.</li>
            <li><strong>Ghi nhận Gross vs. Net chuẩn mực:</strong> Không lấy số tiền thực nhận (Net Payout) làm doanh thu một cách máy móc đối với PayPal/Apple/Google Play; phải bóc tách Gross Sales, Platform Commission/Fee (15%–30%), Refund/Chargeback, Withholding Tax và phí ngân hàng/chênh lệch tỷ giá (FX).</li>
            <li><strong>Chỉ hạch toán trên Finalized Earnings:</strong> Với Google Play và Google AdMob, tuyệt đối không xuất hóa đơn dựa trên <em>Estimated Earnings</em>; chỉ ghi nhận doanh thu và xuất hóa đơn khi có <em>Finalized Earnings / Payout Report</em> cuối kỳ (đã trừ Invalid Traffic).</li>
        </ol>
        <h2>2. Quy trình Xuất Hóa đơn Điện tử Xuất khẩu Phần mềm 0% (Canva Pty Ltd &amp; Quốc tế)</h2>
        <ul>
            <li>Khi nhận thông báo giải thưởng/doanh thu từ <strong>Canva Pty Ltd</strong> (110 Kippax St, Surry Hills, Australia — ví dụ: <em>Canva App Adoption Awards</em> cho <code>Gen Logo</code>, <code>Gen QR Art</code>, <code>Reface</code> trị giá 2.000 USD – 14.000 USD):</li>
            <li><strong>Bước 1:</strong> Lưu trữ email thông báo hợp lệ (<code>.eml</code> từ <code>@canva.com</code> / <code>admin@payout.canva.com</code>) và Báo cáo MAU/Analytics đính kèm vào thư mục <code>Hoá đơn đầu ra</code>.</li>
            <li><strong>Bước 2:</strong> Ngay trong ngày Ngân hàng Vietcombank ghi có ngoại tệ (Credit Date — ví dụ 19/03/2025 nhận 14.000 USD), kế toán kiểm tra tỷ giá mua chuyển khoản Vietcombank tại ngày ghi có và lập Hóa đơn GTGT điện tử trên Viettel SInvoice (Ký hiệu <code>1C25TBS</code> / <code>1C26TAA</code>) trong vòng 24 giờ, tránh độ trễ giữa Ngày ghi có và Ngày xuất hóa đơn.</li>
        </ul>""",
    )

    upsert_article(
        "kb_dgm_sop_03_b2b_contracts",
        "SOP-DGM-03 · Quy Trình Hợp Đồng B2B, Chấm Công Onsite (MTI-Tech) & Hợp Tác CSP (MobiFone MobiAI, US DPA)",
        "🤝",
        root_art.id,
        3,
        """<h1>SOP-DGM-03 · Quản Trị Hợp Đồng B2B, Chấm Công Onsite (Timesheet-to-Cash) &amp; Hợp Tác CSP</h1>
        <h2>1. Luồng Dịch vụ Kỹ sư Onsite / Gia công Phần mềm (Mẫu Hợp đồng MTI Technology `DIGIMATE2401-001`)</h2>
        <ul>
            <li><strong>Định mức Giờ chuẩn &amp; Tăng ca (Overtime Rules):</strong>
                <ul>
                    <li>Khung giờ chuẩn thay đổi theo số ngày làm việc của từng tháng (ví dụ: Tháng 2: 108–128h; Tháng 3: 148–168h; Tháng 4: 140–160h; Tháng 5: 156–176h).</li>
                    <li>Dưới mức tối thiểu: Thanh toán = <code>Đơn giá giờ × Số giờ thực tế</code>.</li>
                    <li>Tăng ca trong 20 giờ đầu tiên vượt khung chuẩn: Hệ số <code>100% × Đơn giá giờ</code>.</li>
                    <li>Tăng ca vượt quá 20 giờ: Hệ số <code>150% × Đơn giá giờ</code>.</li>
                    <li>Chỉ tính tăng ca khi có phê duyệt của PM/Leader dự án và thời gian tăng ca mỗi lần &gt; 60 phút; không tính tăng ca cho thời gian ăn tối, đi sớm về trễ tự ý, hoặc fix bug/rework do lỗi chủ quan hiểu sai Spec.</li>
                </ul>
            </li>
            <li><strong>Mốc Thời gian Đối soát &amp; Thanh toán (SLA):</strong>
                <ul>
                    <li><strong>Trước ngày 05 tháng T+1:</strong> Hệ thống tự động thu thập bảng chấm công Excel đa sheet từ email gửi vào <code>info@inno.ai.vn</code> qua pipeline <code>al2c.timesheet.staging</code>, đối soát và gửi khách hàng xác nhận.</li>
                    <li><strong>Trước ngày 10 tháng T+1:</strong> Phát hành Đề nghị thanh toán kèm Hóa đơn GTGT điện tử.</li>
                    <li><strong>Ngày 10 tháng T+2 (trong vòng 40 ngày):</strong> Theo dõi thu tiền về TK Vietcombank <code>1202703007</code>.</li>
                </ul>
            </li>
            <li><strong>Quản trị Rủi ro Nhân sự Onsite:</strong> Báo trước 30 ngày làm việc khi DGM chủ động thay người (kèm 1 tuần bàn giao miễn phí); nếu khách hàng yêu cầu thay người trong 30 ngày thử thách, miễn phí tối đa 05 ngày làm việc.</li>
        </ul>
        <h2>2. Luồng Hợp tác Phân chia Doanh thu CSP Viễn thông (MobiFone MobiAI)</h2>
        <ul>
            <li>Hồ sơ đề xuất (HSĐX) nộp qua <code>http://hoptac.mobifone.vn</code> phải đính kèm: Giấy CNĐKDN (<code>0317958465</code>), Giấy chứng nhận Bản quyền tác giả phần mềm (Cục Bản quyền tác giả), Cam kết tuân thủ nghĩa vụ thuế (Mẫu số 2), và cam kết SLA xử lý phản ánh khách hàng tối đa <strong>48 giờ</strong>.</li>
        </ul>
        <h2>3. Luồng Hợp đồng Giáo dục &amp; Enterprise Quốc tế (US Student Data Privacy Agreement — CA-NDPA v1.5)</h2>
        <ul>
            <li>Với khách hàng trường học/tổ chức Hoa Kỳ (như <em>Temecula Valley Unified School District</em>): Tuân thủ nghiêm ngặt FERPA, COPPA và Nghị định 13/2023/NĐ-CP; phản hồi yêu cầu truy xuất/chỉnh sửa dữ liệu học sinh của LEA tối đa trong vòng <strong>45 ngày</strong>.</li>
        </ul>""",
    )

    upsert_article(
        "kb_dgm_sop_04_hr_payroll_bhxh",
        "SOP-DGM-04 · Quy Trình Nhân Sự, Hợp Đồng Lao Động, Bảng Lương VCB DigiBiz & BHXH (TZ0857G)",
        "👥",
        root_art.id,
        4,
        """<h1>SOP-DGM-04 · Quy Trình Quản Trị Nhân Sự, Tiền Lương VCB DigiBiz, BHXH &amp; Thuế TNCN</h1>
        <h2>1. Hồ sơ Nhân sự &amp; Hợp đồng Lao động Chuẩn (`Mau_Hop_dong_Lao_dong_DIGIMATE (2026)`)</h2>
        <ul>
            <li>Mỗi nhân sự gia nhập Công ty Cổ phần Người Bạn Số phải có thư mục hồ sơ điện tử định danh riêng trong <code>04. Nhân sự &amp; Hợp đồng Lao động</code> gồm: CCCD 2 mặt, Sổ hộ khẩu/Xác nhận cư trú, Mã số thuế cá nhân, Mã số BHXH, Tài khoản ngân hàng (VCB/ACB), Hợp đồng lao động theo mẫu 2026 (12 Điều, tích hợp chặt chẽ Điều 6 An toàn thông tin, Điều 7 Bảo mật mã nguồn/prompt/AI model và Điều 8 Sở hữu trí tuệ thuộc về DGM).</li>
            <li>Đối với nhân sự có người phụ thuộc (NPT): Lưu trữ Giấy khai sinh con / Hồ sơ chứng minh NPT kèm Giấy ủy quyền đăng ký giảm trừ gia cảnh để kế toán đăng ký với cơ quan thuế.</li>
        </ul>
        <h2>2. Quy trình Chi trả Lương Tự động qua Vietcombank DigiBiz (Ngày 03 – 10 hàng tháng)</h2>
        <ul>
            <li>Hệ thống kết xuất trực tiếp bảng kê chi lương theo đúng cấu trúc chuẩn 11 cột của <strong>VCB DigiBiz</strong> (<code>stt | so ref | so tai khoan | so cmnd | ngay cap | noi cap | ten nguoi huong | ten ngan hang | so tien | loai tien | noi dung</code>), hỗ trợ chuyển khoản liên ngân hàng đồng loạt cho cả tài khoản Vietcombank và ACB.</li>
        </ul>
        <h2>3. Kiểm soát Đối soát BHXH Hàng tháng (Mã đơn vị `TZ0857G` — BHXH Quận 7)</h2>
        <ul>
            <li>Định kỳ trước ngày 25 hàng tháng, kế toán trích nộp đầy đủ BHXH, BHYT, BHTN, BHTNLĐ-BNN và tải Thông báo kết quả đóng BHXH <strong>Mẫu C12-TS</strong> của BHXH Quận 7 lưu vào thư mục <code>BHXH</code>, tuyệt đối không để phát sinh nợ đọng chuyển kỳ sau làm phát sinh lãi chậm đóng (0,726% – 0,984%/tháng).</li>
        </ul>""",
    )

    upsert_article(
        "kb_dgm_sop_05_tax_settlement",
        "SOP-DGM-05 · Danh Mục Kiểm Tra Quyết Toán Thuế & Quản Trị Hóa Đơn Điện Tử (3 Năm 2023–2026)",
        "📊",
        root_art.id,
        5,
        """<h1>SOP-DGM-05 · Quy Trình Quyết Toán Thuế &amp; Lưu Trữ Chứng Từ Kế Toán Chuẩn Thanh Tra</h1>
        <h2>1. Bộ Hồ sơ 9 Hạng mục Bắt buộc phục vụ Quyết toán Thuế (Checklist chuẩn DGM)</h2>
        <ol>
            <li><strong>Giấy phép Đăng ký Kinh doanh (GPĐKKD):</strong> Bản gốc và các lần thay đổi (2023, 2026) kèm Điều lệ công ty.</li>
            <li><strong>Hồ sơ Đăng ký Thuế &amp; Tài khoản Ngân hàng (Mẫu 08):</strong> Thông báo tài khoản VCB <code>1202703007</code> với cơ quan thuế.</li>
            <li><strong>Báo cáo Tài chính (BCTC) các năm 2023, 2024, 2025:</strong> Đảm bảo khớp đúng số dư Sổ phụ Ngân hàng Vietcombank từ ngày thành lập (28/07/2023).</li>
            <li><strong>Tờ khai Thuế GTGT (Mẫu 01/GTGT) Quý 1, 2, 3, 4 các năm 2023, 2024, 2025:</strong> Kèm Thông báo chấp nhận hồ sơ khai thuế điện tử (ETAX) của Tổng cục Thuế.</li>
            <li><strong>Bảng lương 3 năm &amp; Chứng từ chi lương VCB DigiBiz:</strong> Khớp 100% giữa Hợp đồng lao động, Bảng chấm công, Bảng thanh toán lương và Ủy nhiệm chi ngân hàng.</li>
            <li><strong>Tờ khai Quyết toán Thuế TNCN hàng năm:</strong> Kèm hồ sơ đăng ký Người phụ thuộc (NPT) giảm trừ gia cảnh.</li>
            <li><strong>Thông báo Kết quả đóng BHXH hàng tháng (Mẫu C12-TS):</strong> Đầy đủ các kỳ 2023, 2024, 2025, 2026 của mã đơn vị <code>TZ0857G</code>.</li>
            <li><strong>Hóa đơn Điện tử Đầu ra &amp; Đầu vào:</strong> Lưu trữ cặp file gốc (<code>.pdf</code> bản thể hiện + <code>.xml</code> chữ ký số) kèm Biên bản nghiệm thu bàn giao (ví dụ: Hóa đơn VNPT <code>1K26TKA-338235</code> kèm Biên bản nghiệm thu dịch vụ FiberEco2; Hóa đơn chữ ký số Viettel-CA <code>1K23TVA-2368750</code>).</li>
            <li><strong>Hồ sơ Khám sức khỏe định kỳ cho người lao động:</strong> Đảm bảo điều kiện chi phí được trừ khi tính thuế TNDN.</li>
        </ol>""",
    )

    upsert_article(
        "kb_dgm_sop_06_ip_brand",
        "SOP-DGM-06 · Đăng Ký Bản Quyền Phần Mềm (Cục Bản Quyền Tác Giả) & Quản Trị Tài Sản Thương Hiệu",
        "💡",
        root_art.id,
        6,
        """<h1>SOP-DGM-06 · Quy Trình Đăng Ký Quyền Tác Giả Phần Mềm &amp; Quản Trị Thương Hiệu Digimate</h1>
        <h2>1. Đăng ký Bản quyền Chương trình Máy tính tại Cục Bản quyền Tác giả</h2>
        <ul>
            <li>Mọi sản phẩm phần mềm cốt lõi do DGM phát triển (như <strong>MOJO AI</strong> — hoàn thành ngày 31/03/2025, và các ứng dụng <strong>Gen Logo</strong>, <strong>Gen QR Art</strong>, <strong>Reface</strong>, <strong>Innoria ERP</strong>) phải lập hồ sơ đăng ký quyền tác giả đối với <em>Chương trình máy tính</em> (Mẫu số 01) và <em>Tác phẩm mỹ thuật ứng dụng</em> (Mẫu số 02 - đối với Logo/UI) tại Cục Bản quyền tác giả.</li>
            <li><strong>Chủ sở hữu quyền tác giả:</strong> <code>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ</code> (ĐKKD số <code>0317958465</code>). Cơ sở phát sinh quyền: Theo quyết định giao việc / Hợp đồng lao động.</li>
            <li><strong>Ý nghĩa Chiến lược &amp; Thuế:</strong> Giấy chứng nhận đăng ký quyền tác giả là chứng từ pháp lý bắt buộc để: (a) Đấu thầu/Hợp tác CSP với MobiFone MobiAI, (b) Chứng minh hoạt động <strong>Sản xuất phần mềm</strong> hưởng ưu đãi thuế TNDN và thuế suất GTGT 0% khi xuất khẩu phần mềm.</li>
        </ul>""",
    )
    return root_art


def run_dgm_sync(env):
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    DocAll = env["documents.document"].sudo().with_context(active_test=False)
    Doc = env["documents.document"].sudo()
    Att = env["ir.attachment"].sudo()

    canonical_folder_ids = set()
    canonical_file_ids = set()

    # 1. Ensure Root Folder: DGM · Công ty Cổ phần Người Bạn Số (Digimate JSC)
    imd_root = env["ir.model.data"].sudo().search(
        [("module", "=", "insilos_al2c"), ("name", "=", "folder_dgm_root")], limit=1
    )
    root_folder = DocAll.browse(imd_root.res_id).exists() if (imd_root and imd_root.res_id) else False
    if not root_folder:
        root_folder = DocAll.search(
            [("type", "=", "folder"), ("name", "=", "DGM · Công ty Cổ phần Người Bạn Số (Digimate JSC)")],
            limit=1,
        )
    root_vals = {
        "type": "folder",
        "name": "DGM · Công ty Cổ phần Người Bạn Số (Digimate JSC)",
        "folder_id": False,
        "owner_id": False,
        "company_id": False,
        "access_internal": "edit",
        "access_via_link": "view",
        "is_access_via_link_hidden": False,
        "sequence": 1,
        "active": True,
    }
    if root_folder:
        root_folder.write(root_vals)
    else:
        root_folder = DocAll.create(root_vals)
    ensure_xmlid(env, "insilos_al2c", "folder_dgm_root", "documents.document", root_folder.id)
    canonical_folder_ids.add(root_folder.id)

    # 2. Ensure 6 GDrive Top Category Folders + 7th SOP Category Folder
    folder_path_to_rec = {}
    for gdrive_root_name, (xmlid_name, display_name, access_int, seq) in TOP_FOLDER_MAP.items():
        imd = env["ir.model.data"].sudo().search(
            [("module", "=", "insilos_al2c"), ("name", "=", xmlid_name)], limit=1
        )
        f_rec = DocAll.browse(imd.res_id).exists() if (imd and imd.res_id) else False
        if not f_rec:
            f_rec = DocAll.search(
                [("type", "=", "folder"), ("name", "=", display_name), ("folder_id", "=", root_folder.id)],
                limit=1,
            )
        vals = {
            "type": "folder",
            "name": display_name,
            "folder_id": root_folder.id,
            "owner_id": False,
            "company_id": False,
            "access_internal": "edit",
            "access_via_link": "view",
            "is_access_via_link_hidden": False,
            "sequence": seq,
            "active": True,
        }
        if f_rec:
            f_rec.write(vals)
        else:
            f_rec = DocAll.create(vals)
        ensure_xmlid(env, "insilos_al2c", xmlid_name, "documents.document", f_rec.id)
        folder_path_to_rec[gdrive_root_name] = f_rec
        canonical_folder_ids.add(f_rec.id)

    # 7th SOP Category Folder
    sop_xmlid, sop_display_name, sop_access, sop_seq = SOP_FOLDER_DEF
    imd_sop = env["ir.model.data"].sudo().search(
        [("module", "=", "insilos_al2c"), ("name", "=", sop_xmlid)], limit=1
    )
    sop_folder = DocAll.browse(imd_sop.res_id).exists() if (imd_sop and imd_sop.res_id) else False
    if not sop_folder:
        sop_folder = DocAll.search(
            [("type", "=", "folder"), ("name", "=", sop_display_name), ("folder_id", "=", root_folder.id)],
            limit=1,
        )
    sop_vals = {
        "type": "folder",
        "name": sop_display_name,
        "folder_id": root_folder.id,
        "owner_id": False,
        "company_id": False,
        "access_internal": "edit",
        "access_via_link": "view",
        "is_access_via_link_hidden": False,
        "sequence": sop_seq,
        "active": True,
    }
    if sop_folder:
        sop_folder.write(sop_vals)
    else:
        sop_folder = DocAll.create(sop_vals)
    ensure_xmlid(env, "insilos_al2c", sop_xmlid, "documents.document", sop_folder.id)
    canonical_folder_ids.add(sop_folder.id)

    # Ensure all nested subfolders from manifest (normalizing away '(Root Shared)' suffixes)
    all_folder_paths = sorted(
        {
            normalize_folder_path(m["rel_path"])
            for m in manifest
            if m["mimeType"] == "application/vnd.google-apps.folder"
        }
        | {normalize_folder_path(m["folder_path"]) for m in manifest if m.get("folder_path")}
        | {"DGM- HÌNH ẢNH 2025/Logo"}
    )
    for seq_idx, fpath in enumerate(all_folder_paths, start=10):
        if not fpath or fpath in folder_path_to_rec:
            continue
        parts = fpath.split("/")
        parent_path = "/".join(parts[:-1])
        leaf_name = parts[-1]
        parent_rec = folder_path_to_rec.get(parent_path, root_folder)
        sub_rec = DocAll.search(
            [("type", "=", "folder"), ("name", "=", leaf_name), ("folder_id", "=", parent_rec.id)],
            limit=1,
        )
        sub_vals = {
            "type": "folder",
            "name": leaf_name,
            "folder_id": parent_rec.id,
            "owner_id": False,
            "company_id": False,
            "access_internal": "edit",
            "access_via_link": "view",
            "is_access_via_link_hidden": False,
            "sequence": seq_idx,
            "active": True,
        }
        if sub_rec:
            sub_rec.write(sub_vals)
        else:
            sub_rec = DocAll.create(sub_vals)
        folder_path_to_rec[fpath] = sub_rec
        canonical_folder_ids.add(sub_rec.id)

    # 3. Ensure Tags
    tags_map = {k: get_or_create_tag(env, k) for k in TAG_DEFS}
    core_tags = {}
    for k, xid in [
        ("contract", "insilos_al2c.tag_contract"),
        ("compliance", "insilos_al2c.tag_compliance_evidence"),
        ("marketing", "insilos_al2c.tag_marketing_asset"),
        ("conf_public", "insilos_al2c.tag_conf_public"),
        ("conf_internal", "insilos_al2c.tag_conf_internal"),
        ("conf_confidential", "insilos_al2c.tag_conf_confidential"),
        ("line_erp", "insilos_al2c.tag_line_erp"),
        ("line_ai", "insilos_al2c.tag_line_ai"),
        ("line_mojo", "insilos_al2c.tag_line_mojo"),
        ("line_svc", "insilos_al2c.tag_line_svc"),
    ]:
        core_tags[k] = env.ref(xid, raise_if_not_found=False)

    # 4. Ingest All Google Drive Files Idempotently (prioritizing canonical paths over '(Root Shared)' duplicates)
    file_entries = sorted(
        [m for m in manifest if m["mimeType"] != "application/vnd.google-apps.folder"],
        key=lambda e: (1 if "(root shared)" in (e.get("folder_path") or "").lower() else 0),
    )
    created_docs = 0
    updated_docs = 0
    seen_folder_files = set()

    for entry in file_entries:
        fid = entry["id"]
        fname = entry["name"]
        fpath = normalize_folder_path(entry.get("folder_path", ""))
        if fpath == "DGM- HÌNH ẢNH 2025" and "logo" in fname.lower():
            target_folder = folder_path_to_rec["DGM- HÌNH ẢNH 2025/Logo"]
        else:
            target_folder = folder_path_to_rec.get(fpath, root_folder)
        local_path = entry.get("local_path")
        eff_name = (
            os.path.basename(local_path)
            if (local_path and os.path.exists(local_path) and os.path.getsize(local_path) > 0)
            else fname
        )
        dedup_key = (target_folder.id, (eff_name or "").strip().lower())
        if dedup_key in seen_folder_files:
            continue
        seen_folder_files.add(dedup_key)

        tag_ids = classify_tags_for_entry(entry, tags_map, core_tags)
        gdrive_url = entry.get("webViewLink") or f"https://drive.google.com/file/d/{fid}/view"
        note_marker = f"[GDRIVE_ID:{fid}] {entry['rel_path']}"

        existing_doc = DocAll.search(
            [("create_activity_note", "ilike", f"[GDRIVE_ID:{fid}]")],
            limit=1,
        )
        if not existing_doc:
            existing_doc = DocAll.search(
                [
                    ("folder_id", "=", target_folder.id),
                    ("name", "=", fname),
                    "|",
                    ("create_activity_note", "=", False),
                    "!", ("create_activity_note", "ilike", "[GDRIVE_ID:"),
                ],
                limit=1,
            )

        if local_path and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            actual_filename = os.path.basename(local_path)
            guessed_mime, _ = mimetypes.guess_type(actual_filename)
            if not guessed_mime:
                guessed_mime = entry.get("mimeType") or "application/octet-stream"
            with open(local_path, "rb") as bf:
                raw_bytes = bf.read()

            if existing_doc:
                if existing_doc.attachment_id:
                    existing_doc.attachment_id.write({
                        "name": actual_filename,
                        "raw": raw_bytes,
                        "mimetype": guessed_mime,
                    })
                else:
                    att = Att.create({
                        "name": actual_filename,
                        "raw": raw_bytes,
                        "mimetype": guessed_mime,
                        "res_model": "documents.document",
                        "res_id": existing_doc.id,
                    })
                    existing_doc.write({"attachment_id": att.id, "type": "binary"})
                existing_doc.write({
                    "name": actual_filename,
                    "type": "binary",
                    "folder_id": target_folder.id,
                    "owner_id": False,
                    "company_id": False,
                    "access_internal": "edit",
                    "access_via_link": "view",
                    "is_access_via_link_hidden": False,
                    "tag_ids": [(6, 0, tag_ids)],
                    "create_activity_note": note_marker,
                    "active": True,
                })
                canonical_file_ids.add(existing_doc.id)
                updated_docs += 1
            else:
                att = Att.create({
                    "name": actual_filename,
                    "raw": raw_bytes,
                    "mimetype": guessed_mime,
                })
                new_doc = DocAll.create({
                    "name": actual_filename,
                    "type": "binary",
                    "attachment_id": att.id,
                    "folder_id": target_folder.id,
                    "owner_id": False,
                    "company_id": False,
                    "tag_ids": [(6, 0, tag_ids)],
                    "access_internal": "edit",
                    "access_via_link": "view",
                    "is_access_via_link_hidden": False,
                    "create_activity_note": note_marker,
                    "active": True,
                })
                att.write({"res_model": "documents.document", "res_id": new_doc.id})
                canonical_file_ids.add(new_doc.id)
                created_docs += 1
        else:
            vals = {
                "name": fname,
                "type": "url",
                "url": gdrive_url,
                "folder_id": target_folder.id,
                "owner_id": False,
                "company_id": False,
                "tag_ids": [(6, 0, tag_ids)],
                "access_internal": "edit",
                "access_via_link": "view",
                "is_access_via_link_hidden": False,
                "create_activity_note": note_marker,
                "active": True,
            }
            if existing_doc:
                existing_doc.write(vals)
                canonical_file_ids.add(existing_doc.id)
                updated_docs += 1
            else:
                new_doc = DocAll.create(vals)
                canonical_file_ids.add(new_doc.id)
                created_docs += 1

    # 5. Ingest 4 SOP Markdown Blueprints into Folder 07
    sop_tag_ids = [tags_map["sop_blueprint"].id]
    if core_tags.get("compliance"):
        sop_tag_ids.append(core_tags["compliance"].id)
    if core_tags.get("line_erp"):
        sop_tag_ids.append(core_tags["line_erp"].id)

    for sop_fname in SOP_FILES:
        sop_path = os.path.join(SOPS_DIR, sop_fname)
        if not os.path.exists(sop_path):
            fallback_path = os.path.join(
                "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf",
                sop_fname,
            )
            if os.path.exists(fallback_path):
                sop_path = fallback_path
        if not os.path.exists(sop_path):
            continue
        with open(sop_path, "rb") as sf:
            raw_bytes = sf.read()
        note_marker = f"[DGM_SOP:{sop_fname}] 07.SOP/{sop_fname}"
        existing_sop = DocAll.search(
            [
                "|",
                ("create_activity_note", "ilike", f"[DGM_SOP:{sop_fname}]"),
                "&",
                ("folder_id", "=", sop_folder.id),
                ("name", "=", sop_fname),
            ],
            limit=1,
        )
        if existing_sop:
            if existing_sop.attachment_id:
                existing_sop.attachment_id.write({
                    "name": sop_fname,
                    "raw": raw_bytes,
                    "mimetype": "text/markdown",
                })
            else:
                att = Att.create({
                    "name": sop_fname,
                    "raw": raw_bytes,
                    "mimetype": "text/markdown",
                    "res_model": "documents.document",
                    "res_id": existing_sop.id,
                })
                existing_sop.write({"attachment_id": att.id, "type": "binary"})
            existing_sop.write({
                "name": sop_fname,
                "type": "binary",
                "folder_id": sop_folder.id,
                "owner_id": False,
                "company_id": False,
                "access_internal": "edit",
                "access_via_link": "view",
                "is_access_via_link_hidden": False,
                "tag_ids": [(6, 0, sop_tag_ids)],
                "create_activity_note": note_marker,
                "active": True,
            })
            canonical_file_ids.add(existing_sop.id)
            updated_docs += 1
        else:
            att = Att.create({
                "name": sop_fname,
                "raw": raw_bytes,
                "mimetype": "text/markdown",
            })
            new_sop = DocAll.create({
                "name": sop_fname,
                "type": "binary",
                "attachment_id": att.id,
                "folder_id": sop_folder.id,
                "owner_id": False,
                "company_id": False,
                "access_internal": "edit",
                "access_via_link": "view",
                "is_access_via_link_hidden": False,
                "tag_ids": [(6, 0, sop_tag_ids)],
                "create_activity_note": note_marker,
                "active": True,
            })
            att.write({"res_model": "documents.document", "res_id": new_sop.id})
            canonical_file_ids.add(new_sop.id)
            created_docs += 1

    # Preserve SOP-DGM-06 Partner Onboarding folders and TPL-ONB companion documents
    onb_folders = DocAll.search([
        ("type", "=", "folder"),
        "|", "|",
        ("name", "ilike", "Hồ sơ On-boarding Đối tác%"),
        ("name", "ilike", "PTN-DGM-%"),
        ("name", "ilike", "TMP-DGM-%"),
    ])
    for of in onb_folders:
        canonical_folder_ids.add(of.id)
    onb_files = DocAll.search([
        ("type", "!=", "folder"),
        "|",
        ("name", "ilike", "[TPL-ONB-%"),
        ("create_activity_note", "ilike", "[DGM_ONB:%"),
    ])
    for ofile in onb_files:
        canonical_file_ids.add(ofile.id)

    # 6. Archive ALL non-canonical files and non-canonical/empty folders via SQL
    non_canonical_files = Doc.search([
        ("type", "!=", "folder"),
        ("id", "not in", list(canonical_file_ids)),
    ])
    archived_files_count = len(non_canonical_files)
    if non_canonical_files:
        env.cr.execute(
            "UPDATE documents_document SET active = FALSE WHERE id = ANY(%s)",
            (list(non_canonical_files.ids),),
        )
        env.invalidate_all()

    non_canonical_folders = Doc.search([
        ("type", "=", "folder"),
        ("id", "not in", list(canonical_folder_ids)),
    ])
    archived_folders_count = len(non_canonical_folders)
    if non_canonical_folders:
        env.cr.execute(
            "UPDATE documents_document SET active = FALSE WHERE id = ANY(%s)",
            (list(non_canonical_folders.ids),),
        )
        env.invalidate_all()

    # Bottom-up recursive check to guarantee ZERO active empty folders
    while True:
        active_folders = Doc.search([("type", "=", "folder")])
        newly_archived_ids = []
        for folder in active_folders:
            has_children = Doc.search_count([("folder_id", "=", folder.id)]) > 0
            if not has_children:
                newly_archived_ids.append(folder.id)
        if newly_archived_ids:
            archived_folders_count += len(newly_archived_ids)
            env.cr.execute(
                "UPDATE documents_document SET active = FALSE WHERE id = ANY(%s)",
                (newly_archived_ids,),
            )
            env.invalidate_all()
        else:
            break

    # 7. Build DGM SOP Knowledge Articles & Reindex RAG Chunks (if installed)
    root_art = False
    rag_stats = {}
    if "knowledge.article" in env and "al2c.rag.service" in env:
        root_art = build_dgm_knowledge_articles(env)
        rag_stats = env["al2c.rag.service"].sudo().cron_reindex_knowledge_articles(batch_limit=100)

    env.cr.commit()
    total_active_folders = Doc.search_count([("type", "=", "folder")])
    total_active_files = Doc.search_count([("type", "!=", "folder")])
    print("=== DGM SYNC COMPLETE ===")
    print(f"Root Folder ID: {root_folder.id} ({root_folder.name})")
    print(f"Total Active Folders: {total_active_folders} (Archived Empty/Legacy Folders: {archived_folders_count})")
    print(f"Total Active Files: {total_active_files} (Created: {created_docs}, Updated: {updated_docs}, Archived Dummy Files: {archived_files_count})")
    if root_art:
        print(f"DGM Knowledge Root Article ID: {root_art.id} ({root_art.name})")
        print(f"RAG Reindex Summary: {rag_stats}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db", default=DB_NAME, help="Target database name")
    parser.add_argument("-c", "--conf", default="/home/zen/O20/insilos.conf", help="Odoo config file")
    args, _ = parser.parse_known_args()

    odoo.tools.config.parse_config(["-c", args.conf, "-d", args.db])
    registry = odoo.modules.registry.Registry.new(args.db)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        run_dgm_sync(env)


if "env" in globals():
    run_dgm_sync(globals()["env"])
elif __name__ == "__main__":
    main()
