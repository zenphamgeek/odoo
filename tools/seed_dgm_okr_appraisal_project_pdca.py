#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotent Seeder for SOP-DGM-11:
PDCA Project Templates, 360-Degree HR Appraisals & Software Enterprise OKR Cascade
(`dgm.okr.objective`, `dgm.okr.key.result`, `dgm.hr.appraisal.sheet`, `dgm.project.pdca.template`)
across `insilos20_dev` and `innoria_prod`.
"""
import base64
import os
import site
import sys
import types

PYENV_PYTHON = "/home/zen/.pyenv/versions/3.12.13/bin/python3"
if os.path.exists(PYENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(PYENV_PYTHON):
    os.execv(PYENV_PYTHON, [PYENV_PYTHON] + sys.argv)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_SITE = os.path.join(ROOT_DIR, ".venv/lib/python3.12/site-packages")
if os.path.isdir(VENV_SITE):
    site.addsitedir(VENV_SITE)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    import xmlsec  # noqa: F401
except Exception:
    sys.modules["xmlsec"] = types.ModuleType("xmlsec")

try:
    from insilos_adapter.hook import install as install_insilos_hook
    install_insilos_hook()
except Exception:
    pass

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.tools import convert_file

_local_conf = os.path.join(ROOT_DIR, "odoo.conf")
if os.path.isdir("/var/lib/insilos/filestore"):
    _extra = [p for p in ("/var/lib/insilos/filestore/custom_addons", f"{ROOT_DIR}/odoo/addons", f"{ROOT_DIR}/addons", f"{ROOT_DIR}/enterprise", f"{ROOT_DIR}/apps") if os.path.isdir(p)]
    odoo.tools.config.parse_config([
        f"--addons-path={','.join(_extra)}",
        "--data-dir=/var/lib/insilos/filestore",
    ])
elif os.path.isfile("/etc/insilos/insilos.conf"):
    odoo.tools.config.parse_config(["-c", "/etc/insilos/insilos.conf"])
elif os.path.isfile(_local_conf):
    odoo.tools.config.parse_config(["-c", _local_conf])
else:
    odoo.tools.config.parse_config([])
if os.environ.get("DB_HOST"):
    odoo.tools.config["db_host"] = os.environ["DB_HOST"]
if os.environ.get("DB_PORT"):
    odoo.tools.config["db_port"] = int(os.environ["DB_PORT"])
if os.environ.get("DB_USER"):
    odoo.tools.config["db_user"] = os.environ["DB_USER"]
if os.environ.get("PGPASSWORD"):
    odoo.tools.config["db_password"] = os.environ["PGPASSWORD"]

from odoo.addons.insilos_al2c.models.dgm_brand_footer import (  # noqa: E402
    wrap_dgm_branded_html_document,
)

MASTER_LIBRARY_FOLDER_NAME = "Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance"

TPL_PRJ_05_FILENAME = "TPL-PRJ-05_Mau_Ke_Hoach_Du_An_Phan_Mem_PDCA_SAP_Activate.html"
TPL_PRJ_06_FILENAME = "TPL-PRJ-06_Bien_Ban_Nghiem_Thu_Sprint_UAT_Va_Go_Live_PDCA.html"
TPL_HR_07_FILENAME = "TPL-HR-07_Phieu_Danh_Gia_Nhan_Su_360_HR_Appraisal_9Box_PDCA.html"
TPL_HR_08_FILENAME = "TPL-HR-08_Bien_Ban_Hieu_Chuan_Nang_Luc_Career_Calibration_SWE.html"
TPL_OKR_01_FILENAME = "TPL-OKR-01_Khung_OKRs_Doanh_Nghiep_Phan_Mem_Digimate_Innoria_2026.html"
SOP_11_DOC_FILENAME = "SOP-DGM-11_Quy_Trinh_PDCA_Quan_Tri_Du_An_HR_Appraisals_Va_OKRs_Phan_Mem.html"


CANONICAL_PROJECT_PDCA_TEMPLATES = [
    {
        "code": "PRJ-TPL-PDCA-01",
        "name": "[TPL-PDCA-01] Khung Dự án Trọn gói Turnkey ERP & AI (SAP Activate 5-Phase + PDCA — KTT / Swarovski)",
        "delivery_methodology": "sap_activate_pdca",
        "mandatory_deliverable_codes": "TPL-PRJ-01, TPL-PRJ-02, TPL-PRJ-03, TPL-PRJ-04, TPL-PRJ-05, TPL-PRJ-06",
        "target_margin_pct": 48.0,
        "target_sla_uptime_pct": 99.95,
        "plan_phase_gate": (
            "1. Ban hành Project Charter (TPL-PRJ-01), Kiến trúc Kỹ thuật Fit-to-Standard (TPL-PRJ-02) "
            "và phân rã OKRs dự án theo quý.\n"
            "2. Thiết lập kho hồ sơ khách hàng dưới cây INNO - HỢP ĐỒNG, DỰ ÁN, KH với RBAC project_delivery."
        ),
        "do_phase_gate": (
            "1. Thực thi Sprint 2 tuần trên nền tảng Odoo 20 / OWL 3 / Sovereign Dark Mode.\n"
            "2. 100% PR phải qua cổng kiểm định tự động (audit_systemic_refactor_risks.py & unslop_scss_rigorous.py)."
        ),
        "check_phase_gate": (
            "1. Chạy bộ kiểm thử Playwright Dual-Theme E2E & Adversarial Security Gate.\n"
            "2. Ký Biên bản Kiểm thử & Nghiệm thu UAT (TPL-PRJ-03 & TPL-PRJ-06) với đại diện khách hàng."
        ),
        "act_phase_gate": (
            "1. Bàn giao Go-Live (TPL-PRJ-04), phát hành Hóa đơn GTGT Điện tử 1C26TAA.\n"
            "2. Họp Retrospective chốt bài học PDCA và cập nhật điểm KR dự án vào phiếu Appraisal 360°."
        ),
    },
    {
        "code": "PRJ-TPL-PDCA-02",
        "name": "[TPL-PDCA-02] Khung Dự án Phái cử Kỹ sư Phần mềm B2B Onsite (Agile Scrum + SLA 140-180h — MTI / AIfin)",
        "delivery_methodology": "b2b_onsite_agile",
        "mandatory_deliverable_codes": "TPL-ONB-05, TPL-PRJ-01, TPL-PRJ-05, TPL-PRJ-06",
        "target_margin_pct": 42.0,
        "target_sla_uptime_pct": 99.90,
        "plan_phase_gate": (
            "1. Hoàn tất Hồ sơ Onboarding Đối tác B2B (SOP-DGM-06: TPL-ONB-01..04) và Lệnh Phái cử Kỹ sư (TPL-ONB-05).\n"
            "2. Thiết lập định mức SLA 140–180 giờ công/tháng và gửi Thông báo Khởi động Dự án (PRJ-NTF)."
        ),
        "do_phase_gate": (
            "1. Kỹ sư Onsite ghi nhận timesheet hàng ngày và hoàn thành ≥ 95% cam kết Sprint của khách hàng.\n"
            "2. Đồng thời hoàn thành các học phần nâng cấp kỹ năng bắt buộc (SOP-DGM-10)."
        ),
        "check_phase_gate": (
            "1. Tổng hợp Bảng Chấm công Cuối kỳ (01_Bang_Cham_Cong) và gửi Portal Token cho khách hàng phê duyệt.\n"
            "2. Thu thập chữ ký điện tử SHA-256 trên Biên bản Nghiệm thu (02_Bien_Ban_Nghiem_Thu) & phản hồi CSAT 360°."
        ),
        "act_phase_gate": (
            "1. Xuất Hóa đơn Nháp Đối soát (03_Hoa_Don_Nhap) -> Phát hành Hóa đơn Chính thức 1C26TAA (04_Hoa_Don_Chinh_Thuc).\n"
            "2. Đồng bộ điểm CSAT của MTI/AIfin vào Phiếu Đánh giá 360° HR Appraisal của kỹ sư."
        ),
    },
    {
        "code": "PRJ-TPL-PDCA-03",
        "name": "[TPL-PDCA-03] Khung Dự án R&D Sản phẩm Lõi AI Agentic, Grounded RAG & Mojo Kernel (Innoria / Canva)",
        "delivery_methodology": "ai_mojo_rd",
        "mandatory_deliverable_codes": "TPL-PRJ-02, TPL-PRJ-05, TPL-PRJ-06, TPL-OKR-01",
        "target_margin_pct": 55.0,
        "target_sla_uptime_pct": 99.99,
        "plan_phase_gate": (
            "1. Xác lập giả thuyết tối ưu hóa (Benchmark Baseline) cho Mojo SIMD Kernel và Sovereign Grounded RAG.\n"
            "2. Định nghĩa Key Results về độ trễ (< 45ms) và độ chính xác trích dẫn chống ảo giác (100% Entailment)."
        ),
        "do_phase_gate": (
            "1. Phát triển kernel Mojo zero-copy interop với Python runtime và điều phối AGY Pro Fleet Swarm.\n"
            "2. Thực thi kiểm thử đơn vị và đo kiểm hiệu năng tự động."
        ),
        "check_phase_gate": (
            "1. Đối chiếu kết quả benchmark thực tế với baseline; kiểm tra độ chính xác RAG citation.\n"
            "2. Đánh giá chéo kiến trúc (Architecture Peer Review) bởi CTO & Principal Engineer."
        ),
        "act_phase_gate": (
            "1. Đóng gói phát hành vào nhân Insilos Core và cập nhật tài liệu kỹ thuật học phần SKL-AI-MOJO / SKL-AI-RAG.\n"
            "2. Ghi nhận sáng kiến kỹ thuật vào ma trận hiệu chuẩn nhân tài 9-Box."
        ),
    },
    {
        "code": "PRJ-TPL-PDCA-04",
        "name": "[TPL-PDCA-04] Khung Dự án Kiểm toán Bảo mật ISO/IEC 27001, ISO 27701 & Nghị định 13/2023/NĐ-CP (GRC PDCA)",
        "delivery_methodology": "iso_grc_audit",
        "mandatory_deliverable_codes": "TPL-ONB-03, TPL-PRJ-05, TPL-PRJ-06, TPL-HR-07",
        "target_margin_pct": 50.0,
        "target_sla_uptime_pct": 99.99,
        "plan_phase_gate": (
            "1. Lập danh mục tài sản thông tin, phân loại dữ liệu cá nhân nhạy cảm (PII) và ma trận phân quyền RBAC.\n"
            "2. Ký Cam kết Bảo mật NDA & DPA Nghị định 13/2023/NĐ-CP (TPL-ONB-03)."
        ),
        "do_phase_gate": (
            "1. Triển khai che mờ một phần (Partial Masking), cơ chế tiết lộ 30s có kiểm toán (dgm.hr.privacy_audit_log) "
            "và bộ lọc chống rò rỉ khóa bí mật trên ErrorDialog."
        ),
        "check_phase_gate": (
            "1. Thực thi 34 bài kiểm thử tấn công giả lập (tools/test_adversarial_security.py) và kiểm toán RBAC.\n"
            "2. Đảm bảo 0 bản ghi tài liệu chưa phân quyền (unmapped = 0) và 0 thư mục rỗng."
        ),
        "act_phase_gate": (
            "1. Ban hành Chứng nhận Tuân thủ Nội bộ ISO 27001/27701 hàng quý.\n"
            "2. Bắt buộc 100% nhân sự hoàn thành học phần SKL-SEC-ISO27001 (điểm đạt ≥ 90/100)."
        ),
    },
]


CANONICAL_OKR_BLUEPRINTS = [
    # --- 3 COMPANY STRATEGIC OKRs ---
    {
        "code": "OKR-2026-Q4-C01",
        "name": "Tăng trưởng Doanh thu Dịch vụ Phần mềm B2B, Turnkey ERP & Xuất khẩu Phần mềm 0% VAT",
        "okr_tier": "company",
        "parent_code": None,
        "owner_reg": "DGM-001",
        "department_name": "Ban Điều hành & Chiến lược (Executive Board)",
        "project_template_code": "PRJ-TPL-PDCA-01",
        "pdca_stage": "act",
        "pdca_retrospective": (
            "[PDCA Check & Act]: Doanh thu dịch vụ phần mềm B2B (MTI, AIfin, KTT, Swarovski, Canva) đạt 97% kế hoạch quý; "
            "100% hóa đơn đối soát MTI/AIfin chuyển đổi sang hóa đơn điện tử 1C26TAA đúng hạn."
        ),
        "krs": [
            {
                "code": "KR-2026-Q4-01",
                "name": "Đạt doanh thu dịch vụ phần mềm B2B Onsite & Turnkey ERP Quý 4/2026 ≥ 1,850 Triệu VNĐ",
                "metric_unit": "vnd_m",
                "start_value": 0.0,
                "target_value": 1850.0,
                "current_value": 1795.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "EINV-1C26TAA-Q4-REV-1795M",
            },
            {
                "code": "KR-2026-Q4-02",
                "name": "Duy trì tỷ lệ nghiệm thu Timesheet SHA-256 & phát hành Hóa đơn GTGT 1C26TAA đúng hạn đạt 100%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 100.0,
                "current_value": 99.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "TS-DGM-202610-0001..0002",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-C02",
        "name": "Xuất sắc Kỹ thuật Nền tảng Insilos Odoo 20, AI Agentic Mojo & Hoàn thành Cổng Kỹ năng Kỹ sư Phần mềm",
        "okr_tier": "company",
        "parent_code": None,
        "owner_reg": "DGM-002",
        "department_name": "Khối Công nghệ & R&D (CTO Office & Core Engineering)",
        "project_template_code": "PRJ-TPL-PDCA-03",
        "pdca_stage": "check",
        "pdca_retrospective": (
            "[PDCA Check & Act]: Hệ thống kiểm định 6 tầng đạt 0 vi phạm; 7/9 nhân sự đã hoàn tất 100% cổng kỹ năng bắt buộc, "
            "2 nhân sự (DGM-007, DGM-008) đang hoàn thiện bài lab cuối cùng."
        ),
        "krs": [
            {
                "code": "KR-2026-Q4-03",
                "name": "Đạt tỷ lệ vượt qua 6 tầng kiểm định tự động (Predictive, Dual-Theme & Adversarial Gate) 100%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 100.0,
                "current_value": 100.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-OWL3",
                "evidence_ref": "AUDIT-SYSTEMIC-ZERO-VIOLATIONS",
            },
            {
                "code": "KR-2026-Q4-04",
                "name": "Nâng tỷ lệ hoàn thành các học phần Cổng Kỹ năng Kỹ sư Phần mềm Bắt buộc toàn công ty ≥ 90%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 90.0,
                "current_value": 88.5,
                "weight": 50.0,
                "skill_code": "SKL-AI-MOJO",
                "evidence_ref": "SOP-DGM-10-SKILL-MATRIX-2026Q4",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-C03",
        "name": "Tuân thủ Tuyệt đối Pháp chế Thuế, BHXH TZ0857G, ISO/IEC 27001 & Bảo vệ Dữ liệu Cá nhân ISO 27701",
        "okr_tier": "company",
        "parent_code": None,
        "owner_reg": "DGM-003",
        "department_name": "Khối Tài chính – Kế toán – Nhân sự & Pháp chế (Finance, HR & GRC)",
        "project_template_code": "PRJ-TPL-PDCA-04",
        "pdca_stage": "act",
        "pdca_retrospective": (
            "[PDCA Check & Act]: 100% bảng lương tháng 10/2026 xuất chuẩn VCB DigiBiz 11 cột và BHXH TZ0857G; "
            "100% tài liệu trong Kho Dữ liệu Số được gắn nhãn RBAC tự động."
        ),
        "krs": [
            {
                "code": "KR-2026-Q4-05",
                "name": "Đảm bảo 100% kỳ lương BHXH TZ0857G, VCB DigiBiz 11 cột & Báo cáo Thuế đúng hạn Zero-Error",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 100.0,
                "current_value": 100.0,
                "weight": 50.0,
                "skill_code": "SKL-SEC-ISO27001",
                "evidence_ref": "VCB-DIGIBIZ-TZ0857G-2026Q4",
            },
            {
                "code": "KR-2026-Q4-06",
                "name": "Duy trì 100% tài liệu công ty & dự án được bảo vệ phân quyền RBAC và Zero-Leak PII",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 100.0,
                "current_value": 100.0,
                "weight": 50.0,
                "skill_code": "SKL-SEC-ISO27001",
                "evidence_ref": "RBAC-GEN-2026-10-16-V1",
            },
        ],
    },
    # --- 9 SQUAD & INDIVIDUAL OKRs (DGM-001 .. DGM-009) ---
    {
        "code": "OKR-2026-Q4-EXEC01",
        "name": "Điều hành Chiến lược Sản phẩm Insilos ERP & Mở rộng Đối tác Chiến lược Quốc tế (Swarovski / Canva / KTT)",
        "okr_tier": "department",
        "parent_code": "OKR-2026-Q4-C01",
        "owner_reg": "DGM-001",
        "department_name": "Ban Tổng Giám đốc (CEO Office)",
        "project_template_code": "PRJ-TPL-PDCA-01",
        "pdca_stage": "act",
        "pdca_retrospective": "Hoàn thành chuẩn hóa 11 quy trình vận hành chuẩn SOP-DGM-01..11 và kiến trúc tự chủ AL2C.",
        "krs": [
            {
                "code": "KR-2026-Q4-07",
                "name": "Ban hành và số hóa 100% bộ 11 quy trình vận hành chuẩn SOP-DGM-01..11 trên Insilos Odoo 20",
                "metric_unit": "count",
                "start_value": 0.0,
                "target_value": 11.0,
                "current_value": 11.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-OWL3",
                "evidence_ref": "SOP-DGM-01..11-COMPLETE",
            },
            {
                "code": "KR-2026-Q4-08",
                "name": "Đạt tỷ lệ hài lòng chiến lược (Executive CSAT) từ các đối tác B2B trọng điểm ≥ 98%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 98.0,
                "current_value": 98.0,
                "weight": 50.0,
                "skill_code": "SKL-SEC-ISO27001",
                "evidence_ref": "EXEC-CSAT-2026Q4-99PCT",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-AI01",
        "name": "Tối ưu Hóa Kiến trúc Mojo SIMD, Sovereign Grounded RAG & Hạ tầng K8s Zero-Downtime",
        "okr_tier": "department",
        "parent_code": "OKR-2026-Q4-C02",
        "owner_reg": "DGM-002",
        "department_name": "Khối AI, Mojo & Cloud Infrastructure",
        "project_template_code": "PRJ-TPL-PDCA-03",
        "pdca_stage": "act",
        "pdca_retrospective": "Độ trễ truy vấn RAG giảm xuống 32ms; cụm K8s vận hành ổn định 100% uptime.",
        "krs": [
            {
                "code": "KR-2026-Q4-09",
                "name": "Giảm độ trễ trung bình của Mojo SIMD & Sovereign RAG Vector Retrieval xuống ≤ 35ms",
                "metric_unit": "ms",
                "start_value": 120.0,
                "target_value": 35.0,
                "current_value": 32.0,
                "weight": 50.0,
                "skill_code": "SKL-AI-MOJO",
                "evidence_ref": "BENCH-MOJO-SIMD-32MS",
            },
            {
                "code": "KR-2026-Q4-10",
                "name": "Đạt tỷ lệ trích dẫn chuẩn xác chống ảo giác (Grounded Citation Entailment) ≥ 99%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 99.0,
                "current_value": 99.0,
                "weight": 50.0,
                "skill_code": "SKL-AI-RAG",
                "evidence_ref": "RAG-CITATION-AUDIT-99PCT",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-FIN01",
        "name": "Tự động hóa Đối soát Hóa đơn Nháp MTI/AIfin, Quản trị Hợp đồng & Hồ sơ Nhân sự Chuẩn ISO 27701",
        "okr_tier": "department",
        "parent_code": "OKR-2026-Q4-C03",
        "owner_reg": "DGM-003",
        "department_name": "Phòng Tài chính – Kế toán & Nhân sự",
        "project_template_code": "PRJ-TPL-PDCA-04",
        "pdca_stage": "act",
        "pdca_retrospective": "Chuẩn hóa toàn bộ biểu mẫu thương mại, nhân sự và đối soát hóa đơn nháp MTI/AIfin.",
        "krs": [
            {
                "code": "KR-2026-Q4-11",
                "name": "Số hóa và chuẩn hóa 100% hồ sơ Onboarding Đối tác B2B & Hợp đồng Phái cử (SOP-DGM-06/07/08)",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 100.0,
                "current_value": 100.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "PTN-DGM-2026-0001..0009",
            },
            {
                "code": "KR-2026-Q4-12",
                "name": "Hoàn thành 100% hồ sơ đánh giá KPI & Appraisal 360° cho toàn bộ nhân sự quý 4/2026",
                "metric_unit": "count",
                "start_value": 0.0,
                "target_value": 9.0,
                "current_value": 9.0,
                "weight": 50.0,
                "skill_code": "SKL-SEC-ISO27001",
                "evidence_ref": "APR-2026-Q4-DGM001..009",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-B2B01",
        "name": "Đảm bảo 100% Cam kết Giao phẩm & SLA 176h/tháng Dự án MTI Technology (HĐ DIGIMATE2401-001)",
        "okr_tier": "individual",
        "parent_code": "OKR-2026-Q4-C01",
        "owner_reg": "DGM-004",
        "department_name": "Khối Kỹ thuật B2B Onsite — MTI Technology Squad",
        "project_template_code": "PRJ-TPL-PDCA-02",
        "pdca_stage": "act",
        "pdca_retrospective": "Đạt 176/160h billable và 100% nghiệm thu từ Giám đốc Kỹ thuật MTI Technology.",
        "krs": [
            {
                "code": "KR-2026-Q4-13",
                "name": "Đạt số giờ công thực chiến được khách hàng MTI Technology nghiệm thu ≥ 176 giờ/tháng",
                "metric_unit": "hours",
                "start_value": 0.0,
                "target_value": 176.0,
                "current_value": 176.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "TS-DGM-202610-0001-DGM004",
            },
            {
                "code": "KR-2026-Q4-14",
                "name": "Đạt tỷ lệ vượt qua Code Review & Zero Production Defect trên hệ thống MTI ≥ 95%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 95.0,
                "current_value": 95.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-OWL3",
                "evidence_ref": "MTI-CR-PASS-95PCT-DGM004",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-ENG01",
        "name": "Làm chủ Kiến trúc OWL 3 Reactivity, Sovereign Dark Mode & Cổng Kiểm thử Tự động 6 Tầng",
        "okr_tier": "department",
        "parent_code": "OKR-2026-Q4-C02",
        "owner_reg": "DGM-005",
        "department_name": "Khối Kỹ thuật Nền tảng (Core Platform & WebClient Squad)",
        "project_template_code": "PRJ-TPL-PDCA-01",
        "pdca_stage": "act",
        "pdca_retrospective": "Hoàn thành kiến trúc Dual-Bundle Dark Mode và loại bỏ 100% bare hex.",
        "krs": [
            {
                "code": "KR-2026-Q4-15",
                "name": "Đạt 100% điểm kiểm định Dual-Theme Light/Dark & Zero Bare Hex trên toàn bộ phân hệ",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 100.0,
                "current_value": 100.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-SCSS-DARK",
                "evidence_ref": "UNSLOP-SCSS-ZERO-VIOLATIONS",
            },
            {
                "code": "KR-2026-Q4-16",
                "name": "Đạt tỷ lệ ổn định OWL 3 Props Guard & Không phát sinh lỗi Regression trên WebClient đạt 98%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 98.0,
                "current_value": 98.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-OWL3",
                "evidence_ref": "OWL3-HYBRID-GUARD-PASS",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-B2B02",
        "name": "Phát triển Tính năng Full-Stack Dự án MTI Technology & Duy trì Chất lượng Code ≥ 90%",
        "okr_tier": "individual",
        "parent_code": "OKR-2026-Q4-C01",
        "owner_reg": "DGM-006",
        "department_name": "Khối Kỹ thuật B2B Onsite — MTI Technology Squad",
        "project_template_code": "PRJ-TPL-PDCA-02",
        "pdca_stage": "act",
        "pdca_retrospective": "Hoàn thành 164h billable và đạt 3/3 chứng chỉ kỹ năng bắt buộc.",
        "krs": [
            {
                "code": "KR-2026-Q4-17",
                "name": "Đạt số giờ công thực chiến nghiệm thu tại dự án MTI Technology ≥ 160 giờ/tháng",
                "metric_unit": "hours",
                "start_value": 0.0,
                "target_value": 160.0,
                "current_value": 164.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "TS-DGM-202610-0001-DGM006",
            },
            {
                "code": "KR-2026-Q4-18",
                "name": "Đạt tỷ lệ hoàn thành Sprint đúng cam kết tại dự án MTI Technology ≥ 90%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 90.0,
                "current_value": 91.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-SCSS-DARK",
                "evidence_ref": "MTI-SPRINT-91PCT-DGM006",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-B2B03",
        "name": "Hoàn thành 100% Giao phẩm MTI Onsite & Chinh phục Chứng chỉ Bắt buộc SKL-ERP-OWL3",
        "okr_tier": "individual",
        "parent_code": "OKR-2026-Q4-C02",
        "owner_reg": "DGM-007",
        "department_name": "Khối Kỹ thuật B2B Onsite — MTI Technology Squad",
        "project_template_code": "PRJ-TPL-PDCA-02",
        "pdca_stage": "check",
        "pdca_retrospective": (
            "[PDCA Check]: Kết quả dự án MTI rất tốt (168h, Sprint 95%), đang hoàn thiện 6h cuối của bài lab "
            "SKL-ERP-OWL3 (18/24h) để mở khóa khỏi ô 9-Box [6] Emerging Potential lên [9] Top Talent."
        ),
        "krs": [
            {
                "code": "KR-2026-Q4-19",
                "name": "Hoàn thành ≥ 168 giờ công thực chiến nghiệm thu tại dự án MTI Technology",
                "metric_unit": "hours",
                "start_value": 0.0,
                "target_value": 168.0,
                "current_value": 168.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "TS-DGM-202610-0001-DGM007",
            },
            {
                "code": "KR-2026-Q4-20",
                "name": "Hoàn thành thời lượng đào tạo & bài lab thực chiến học phần bắt buộc SKL-ERP-OWL3 (24 giờ)",
                "metric_unit": "hours",
                "start_value": 0.0,
                "target_value": 24.0,
                "current_value": 21.6,
                "weight": 50.0,
                "skill_code": "SKL-ERP-OWL3",
                "evidence_ref": "LAB-OWL3-WIP-007",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-QA01",
        "name": "Xây dựng Bộ Kiểm thử Playwright E2E Dual-Theme & Hoàn tất Chứng chỉ SKL-QA-PLAYWRIGHT",
        "okr_tier": "individual",
        "parent_code": "OKR-2026-Q4-C02",
        "owner_reg": "DGM-008",
        "department_name": "Khối Đảm bảo Chất lượng & Giao diện (QA & UI Automation Squad)",
        "project_template_code": "PRJ-TPL-PDCA-01",
        "pdca_stage": "check",
        "pdca_retrospective": (
            "[PDCA Check]: Đã đạt chuẩn SKL-SEC-ISO27001 & SKL-ERP-SCSS-DARK; cần hoàn tất nghiệm thu "
            "SKL-QA-PLAYWRIGHT trước 15/12/2026 để mở khóa thăng cấp."
        ),
        "krs": [
            {
                "code": "KR-2026-Q4-21",
                "name": "Đạt độ bao phủ kịch bản kiểm thử tự động E2E trên các luồng nghiệp vụ cốt lõi ≥ 94%",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 94.0,
                "current_value": 94.0,
                "weight": 50.0,
                "skill_code": "SKL-ERP-SCSS-DARK",
                "evidence_ref": "E2E-COVERAGE-94PCT-DGM008",
            },
            {
                "code": "KR-2026-Q4-22",
                "name": "Hoàn thành bài lab kiểm thử tự động học phần bắt buộc SKL-QA-PLAYWRIGHT (20 giờ)",
                "metric_unit": "hours",
                "start_value": 0.0,
                "target_value": 20.0,
                "current_value": 18.0,
                "weight": 50.0,
                "skill_code": "SKL-QA-PLAYWRIGHT",
                "evidence_ref": "PLAYWRIGHT-WIP-008",
            },
        ],
    },
    {
        "code": "OKR-2026-Q4-B2B04",
        "name": "Dẫn dắt Kỹ thuật Dự án AIfin 360-Sales (HĐ DIGIMATE-AIFIN-VN_2610-001) & Đạt 100% CSAT",
        "okr_tier": "individual",
        "parent_code": "OKR-2026-Q4-C01",
        "owner_reg": "DGM-009",
        "department_name": "Khối Kỹ thuật B2B Onsite — AIfin Global Squad",
        "project_template_code": "PRJ-TPL-PDCA-02",
        "pdca_stage": "act",
        "pdca_retrospective": "Hoàn thành xuất sắc 22/22 ngày công (176h), được CEO AIfin Nguyễn Quốc Huy ký nghiệm thu 100%.",
        "krs": [
            {
                "code": "KR-2026-Q4-23",
                "name": "Đạt 176 giờ công thực chiến nghiệm thu 100% tại dự án AIfin 360-Sales",
                "metric_unit": "hours",
                "start_value": 0.0,
                "target_value": 176.0,
                "current_value": 176.0,
                "weight": 50.0,
                "skill_code": "SKL-B2B-ACTIVATE",
                "evidence_ref": "TS-DGM-202610-0002-DGM009",
            },
            {
                "code": "KR-2026-Q4-24",
                "name": "Đạt điểm đánh giá hài lòng khách hàng (AIfin CEO CSAT) ≥ 98/100",
                "metric_unit": "pct",
                "start_value": 0.0,
                "target_value": 98.0,
                "current_value": 98.0,
                "weight": 50.0,
                "skill_code": "SKL-K8S-PG",
                "evidence_ref": "AIFIN-CSAT-98PCT-DGM009",
            },
        ],
    },
]


CANONICAL_APPRAISAL_BLUEPRINTS = [
    {
        "code": "APR-2026-Q4-DGM001",
        "reg_no": "DGM-001",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Lê Xuân Hoàng (DGM-001)",
        "okr_codes": ["OKR-2026-Q4-C01", "OKR-2026-Q4-EXEC01"],
        "self_score": 98.0,
        "peer_360_score": 99.0,
        "manager_score": 99.0,
        "self_reflection": "Hoàn thành toàn diện chiến lược sản phẩm Insilos Odoo 20 và hệ thống 11 quy trình vận hành chuẩn SOP-DGM-01..11.",
        "peer_feedback": "Hội đồng Quản trị & Đối tác B2B đánh giá xuất sắc về tầm nhìn kiến trúc và tốc độ chuyển đổi số.",
        "manager_appraisal": "Xếp hạng 9-Box [9] Top Talent / Executive Leader.",
        "next_plan": "Mở rộng quy mô xuất khẩu phần mềm 0% VAT sang thị trường Châu Âu & APAC trong Quý 1/2027.",
    },
    {
        "code": "APR-2026-Q4-DGM002",
        "reg_no": "DGM-002",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Nguyễn Hoài Ân (DGM-002)",
        "okr_codes": ["OKR-2026-Q4-C02", "OKR-2026-Q4-AI01"],
        "self_score": 97.0,
        "peer_360_score": 98.5,
        "manager_score": 99.0,
        "self_reflection": "Làm chủ kiến trúc Mojo SIMD, Sovereign Grounded RAG và hạ tầng K8s Zero-Downtime.",
        "peer_feedback": "Các squad kỹ thuật đánh giá rất cao sự hỗ trợ kiến trúc và bộ công cụ kiểm định tự động.",
        "manager_appraisal": "Đạt 4/4 chứng chỉ kỹ năng bắt buộc với điểm tuyệt đối; xếp ô 9-Box [9] Top Talent.",
        "next_plan": "Triển khai thế hệ Mojo AI Kernel v2 và mở rộng cụm AGY Pro Fleet.",
    },
    {
        "code": "APR-2026-Q4-DGM003",
        "reg_no": "DGM-003",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Mai Thị Hồng Thắm (DGM-003)",
        "okr_codes": ["OKR-2026-Q4-C03", "OKR-2026-Q4-FIN01"],
        "self_score": 96.0,
        "peer_360_score": 98.0,
        "manager_score": 97.5,
        "self_reflection": "Vận hành chính xác 100% bảng lương BHXH TZ0857G, VCB DigiBiz 11 cột và đối soát hóa đơn 1C26TAA.",
        "peer_feedback": "Phòng Kế toán MTI Technology và AIfin đánh giá quy trình đối soát hóa đơn nháp rất minh bạch, chuyên nghiệp.",
        "manager_appraisal": "Đạt 100% cổng kỹ năng bảo mật ISO 27701 & FinOps; xếp ô 9-Box [9] Top Talent.",
        "next_plan": "Tự động hóa 100% báo cáo quản trị dòng tiền và quyết toán thuế năm 2026.",
    },
    {
        "code": "APR-2026-Q4-DGM004",
        "reg_no": "DGM-004",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Bùi Hữu Tài (DGM-004)",
        "okr_codes": ["OKR-2026-Q4-B2B01"],
        "self_score": 95.0,
        "peer_360_score": 96.0,
        "manager_score": 96.0,
        "self_reflection": "Hoàn thành 176h công thực chiến tại MTI Technology và 4/4 chứng chỉ kỹ năng bắt buộc.",
        "peer_feedback": "Giám đốc Kỹ thuật Tanaka Kenji (MTI Technology) đánh giá cao chất lượng microservices và thái độ làm việc.",
        "manager_appraisal": "Kỹ sư nòng cốt khối B2B Onsite; đạt chuẩn 9-Box [9] Top Talent.",
        "next_plan": "Tham gia dẫn dắt kỹ thuật nhóm kỹ sư mới tại dự án mở rộng MTI 2027.",
    },
    {
        "code": "APR-2026-Q4-DGM005",
        "reg_no": "DGM-005",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Huỳnh Trần Quang Khánh (DGM-005)",
        "okr_codes": ["OKR-2026-Q4-ENG01"],
        "self_score": 96.0,
        "peer_360_score": 97.5,
        "manager_score": 98.0,
        "self_reflection": "Hoàn thành kiến trúc OWL 3 Hybrid Reactivity, Sovereign Dark Mode và 4/4 chứng chỉ kỹ năng.",
        "peer_feedback": "Đồng nghiệp đánh giá cao các bản vá bảo vệ frozen props và hệ thống token màu chuẩn.",
        "manager_appraisal": "Tech Lead xuất sắc; xếp ô 9-Box [9] Top Talent.",
        "next_plan": "Chuẩn hóa thư viện component OWL 3 thế hệ mới cho toàn bộ phân hệ Enterprise.",
    },
    {
        "code": "APR-2026-Q4-DGM006",
        "reg_no": "DGM-006",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Ngô Thanh Lộc (DGM-006)",
        "okr_codes": ["OKR-2026-Q4-B2B02"],
        "self_score": 89.0,
        "peer_360_score": 90.0,
        "manager_score": 90.0,
        "self_reflection": "Đạt 164h công tại dự án MTI Technology và hoàn tất 3/3 học phần kỹ năng bắt buộc.",
        "peer_feedback": "Phối hợp tốt với nhóm MTI Onsite, giao phẩm ổn định đúng hạn.",
        "manager_appraisal": "Hoàn thành đầy đủ cổng kỹ năng bắt buộc, hiệu suất tốt; xếp ô 9-Box [8] High Impact Engineer.",
        "next_plan": "Đăng ký thêm học phần nâng cao SKL-K8S-PG trong Quý 1/2027 để chuẩn bị xét lên L4.",
    },
    {
        "code": "APR-2026-Q4-DGM007",
        "reg_no": "DGM-007",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Lê Cao Bảo Phúc (DGM-007)",
        "okr_codes": ["OKR-2026-Q4-B2B03"],
        "self_score": 94.0,
        "peer_360_score": 95.0,
        "manager_score": 95.0,
        "self_reflection": "Hoàn thành vượt mức 168h công tại MTI Technology; đang hoàn thiện bài lab SKL-ERP-OWL3 (18/24h).",
        "peer_feedback": "Khách hàng MTI hài lòng với tiến độ giao phẩm; cần hoàn tất chứng chỉ OWL 3 nội bộ.",
        "manager_appraisal": (
            "Điểm chuyên môn & OKR rất cao (>93đ), nhưng theo quy tắc Cổng Kỹ năng Bắt buộc (SOP-DGM-10/11), "
            "tạm thời giới hạn ở ô 9-Box [6] Emerging Potential (84.90đ) cho đến khi nghiệm thu xong SKL-ERP-OWL3."
        ),
        "next_plan": "Hoàn tất nghiệm thu SKL-ERP-OWL3 trước ngày 15/12/2026 để mở khóa tự động lên 9-Box [9] Top Talent.",
    },
    {
        "code": "APR-2026-Q4-DGM008",
        "reg_no": "DGM-008",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Thái Nguyễn Đăng Khoa (DGM-008)",
        "okr_codes": ["OKR-2026-Q4-QA01"],
        "self_score": 92.0,
        "peer_360_score": 93.0,
        "manager_score": 93.0,
        "self_reflection": "Đã hoàn thành chứng chỉ ISO 27001 và Dark Mode SCSS; đang hoàn tất bài lab SKL-QA-PLAYWRIGHT (18/20h).",
        "peer_feedback": "Hỗ trợ tích cực trong việc kiểm thử giao diện Light/Dark trên các phân hệ.",
        "manager_appraisal": (
            "Tiềm năng phát triển tốt; tạm giữ ở ô 9-Box [6] Emerging Potential (84.90đ) do còn 1 học phần "
            "bắt buộc SKL-QA-PLAYWRIGHT đang In Progress."
        ),
        "next_plan": "Nộp bài lab Playwright Dual-Theme E2E để mở khóa lên 9-Box [8]/[9] và xét nâng bậc L2.",
    },
    {
        "code": "APR-2026-Q4-DGM009",
        "reg_no": "DGM-009",
        "name": "Đánh giá 360° & Hiệu chuẩn 9-Box Quý 4/2026 — Trần Văn Huỳnh Phố (DGM-009)",
        "okr_codes": ["OKR-2026-Q4-B2B04"],
        "self_score": 96.0,
        "peer_360_score": 98.0,
        "manager_score": 97.0,
        "self_reflection": "Hoàn thành 100% khối lượng 22/22 ngày công dự án AIfin 360-Sales và đạt 4/4 chứng chỉ kỹ năng bắt buộc.",
        "peer_feedback": "Tổng Giám đốc AIfin Nguyễn Quốc Huy ký nghiệm thu tuyệt đối và đánh giá CSAT 98/100.",
        "manager_appraisal": "Kỹ sư chủ lực xuất sắc tại dự án AIfin Global; xếp ô 9-Box [9] Top Talent.",
        "next_plan": "Mở rộng kiến trúc tích hợp AI Concierge & thanh toán tự động cho giai đoạn 2 của AIfin.",
    },
]


def _ensure_doc_active(env, rec):
    if rec and not rec.active:
        env.cr.execute("UPDATE documents_document SET active = TRUE WHERE id IN %s", [tuple(rec.ids)])
        rec.invalidate_recordset(["active"])


def _resolve_folder(env, preferred_id, name_patterns, parent_id=False):
    Document = env["documents.document"].sudo()
    if preferred_id:
        folder = Document.with_context(active_test=False).browse(preferred_id).exists()
        if folder and folder.type == "folder":
            _ensure_doc_active(env, folder)
            folder.write({"owner_id": False, "access_internal": "edit"})
            return folder
    for pat in name_patterns:
        domain = [("type", "=", "folder"), ("name", "ilike", pat)]
        if parent_id:
            domain.append(("folder_id", "=", parent_id))
        folder = Document.with_context(active_test=False).search(domain, order="id asc", limit=1)
        if folder:
            _ensure_doc_active(env, folder)
            folder.write({"owner_id": False, "access_internal": "edit"})
            return folder
    return Document.browse()


def _upsert_html_doc(env, folder_id, doc_name, filename, html_str, code_marker=None):
    Document = env["documents.document"].sudo()
    Attachment = env["ir.attachment"].sudo().with_context(no_document=True)
    b64_datas = base64.b64encode(html_str.encode("utf-8"))

    existing = Document.browse()
    if code_marker:
        existing = Document.with_context(active_test=False).search([
            ("folder_id", "=", folder_id),
            ("type", "!=", "folder"),
            ("name", "ilike", code_marker),
        ], order="id asc", limit=1)
    if not existing:
        existing = Document.with_context(active_test=False).search([
            ("folder_id", "=", folder_id),
            ("type", "!=", "folder"),
            ("name", "=", doc_name),
        ], order="id asc", limit=1)

    if existing:
        _ensure_doc_active(env, existing)
        if existing.attachment_id:
            existing.attachment_id.with_context(no_document=True).write({
                "name": filename,
                "datas": b64_datas,
                "mimetype": "text/html",
            })
        else:
            att = Attachment.create({
                "name": filename,
                "type": "binary",
                "datas": b64_datas,
                "mimetype": "text/html",
                "res_model": "documents.document",
                "res_id": existing.id,
            })
            existing.write({"attachment_id": att.id})
        existing.write({
            "name": doc_name,
            "folder_id": folder_id,
            "owner_id": False,
            "access_internal": "edit",
            "access_via_link": "view",
        })
        return existing

    att = Attachment.create({
        "name": filename,
        "type": "binary",
        "datas": b64_datas,
        "mimetype": "text/html",
        "res_model": "documents.document",
        "res_id": 0,
    })
    doc = Document.create({
        "name": doc_name,
        "folder_id": folder_id,
        "owner_id": False,
        "type": "binary",
        "attachment_id": att.id,
        "access_internal": "edit",
        "access_via_link": "view",
        "active": True,
    })
    att.write({"res_id": doc.id})
    return doc


def _build_tpl_prj_05_html():
    body = """
    <section>
      <h2>MẪU KẾ HOẠCH QUẢN TRỊ DỰ ÁN PHẦN MỀM THEO VÒNG LẶP PDCA &amp; SAP ACTIVATE 5 GIAI ĐOẠN (TPL-PRJ-05)</h2>
      <p>
        Biểu mẫu chuẩn <strong>TPL-PRJ-05</strong> áp dụng bắt buộc khi khởi tạo mọi dự án phần mềm Trọn gói (Turnkey ERP/AI),
        Phái cử Kỹ sư B2B Onsite (MTI / AIfin / KTT) và Dự án R&amp;D Sản phẩm Lõi tại <strong>DIGIMATE JSC &amp; INNORIA</strong>.
      </p>
      <h3>1. Ma Trận 4 Khung Mẫu Dự Án Phần Mềm Chuẩn PDCA (`dgm.project.pdca.template`)</h3>
      <table>
        <thead>
          <tr>
            <th>Mã Khung Mẫu</th>
            <th>Loại Hình Dự Án Phần Mềm</th>
            <th>Phương Pháp Luận</th>
            <th>Biên Lợi Nhuận Mục Tiêu</th>
            <th>Cam Kết SLA</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>PRJ-TPL-PDCA-01</code></td>
            <td>Triển khai Trọn gói Turnkey ERP &amp; AI (KTT / Swarovski)</td>
            <td>SAP Activate 5-Phase + PDCA</td>
            <td>48.0%</td>
            <td>99.95%</td>
          </tr>
          <tr>
            <td><code>PRJ-TPL-PDCA-02</code></td>
            <td>Phái cử Kỹ sư Phần mềm B2B Onsite (MTI / AIfin)</td>
            <td>Agile Scrum + SLA 140–180h</td>
            <td>42.0%</td>
            <td>99.90%</td>
          </tr>
          <tr>
            <td><code>PRJ-TPL-PDCA-03</code></td>
            <td>R&amp;D Sản phẩm Lõi AI Agentic, RAG &amp; Mojo Kernel</td>
            <td>AI Benchmark &amp; SIMD Loop</td>
            <td>55.0%</td>
            <td>99.99%</td>
          </tr>
          <tr>
            <td><code>PRJ-TPL-PDCA-04</code></td>
            <td>Kiểm toán Bảo mật ISO/IEC 27001, ISO 27701 &amp; Nghị định 13</td>
            <td>GRC Security Compliance PDCA</td>
            <td>50.0%</td>
            <td>99.99%</td>
          </tr>
        </tbody>
      </table>
      <h3>2. Cổng Kiểm Soát Chất Lượng 4 Bước PDCA (Quality Gates)</h3>
      <ul>
        <li><strong>P (Plan — Prepare &amp; Explore):</strong> Ký Project Charter (<code>TPL-PRJ-01</code>), Kiến trúc Kỹ thuật (<code>TPL-PRJ-02</code>), thiết lập OKR dự án và thư mục phân quyền RBAC.</li>
        <li><strong>D (Do — Realize Sprint):</strong> Thực thi Sprint 2 tuần, chấm công Billable chính xác và vượt qua cổng Code Review tự động.</li>
        <li><strong>C (Check — UAT &amp; Security Gate):</strong> Chạy bộ kiểm thử Playwright Dual-Theme E2E, Adversarial Security Audit và ký Biên bản UAT (<code>TPL-PRJ-06</code>).</li>
        <li><strong>A (Act — Deploy, Invoice &amp; Retro):</strong> Bàn giao Go-Live, đối soát hóa đơn điện tử <code>1C26TAA</code> và cập nhật điểm KR vào kỳ đánh giá 360° HR Appraisal.</li>
      </ul>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="[TPL-PRJ-05] Mẫu Kế hoạch Quản trị Dự án Phần mềm theo Vòng lặp PDCA & SAP Activate 5 Giai đoạn (SOP-DGM-11)",
        doc_code="TPL-PRJ-05",
        sop_ref="SOP-DGM-11",
        classification="PROJECT DELIVERY GOVERNANCE • PDCA TEMPLATE",
        include_header=True,
    )


def _build_tpl_prj_06_html():
    body = """
    <section>
      <h2>BIÊN BẢN NGHIỆM THU SPRINT, KIỂM THỬ UAT, CỔNG BẢO MẬT &amp; BÀN GIAO GO-LIVE PDCA (TPL-PRJ-06)</h2>
      <p>
        Biểu mẫu <strong>TPL-PRJ-06</strong> là chứng từ bắt buộc tại bước <strong>Check (C)</strong> và <strong>Act (A)</strong>
        trong chu trình quản trị dự án phần mềm theo <strong>SOP-DGM-11</strong>, làm căn cứ mở khóa xuất Hóa đơn Nháp Đối soát
        và ghi nhận điểm hoàn thành Key Result cho đội ngũ kỹ sư.
      </p>
      <table>
        <thead>
          <tr>
            <th>Hạng Mục Kiểm Định Nghiệm Thu (PDCA Check &amp; Act Gate)</th>
            <th>Tiêu Chuẩn Đạt (Acceptance Criteria)</th>
            <th>Kết Quả Kiểm Định</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>1. Tiến độ Giao phẩm Sprint / SOW &amp; Giờ công Billable</strong></td>
            <td>Hoàn thành &ge; 95% User Stories cam kết; Bảng chấm công khớp 100% log hệ thống</td>
            <td><strong>ĐẠT CHUẨN (PASSED)</strong></td>
          </tr>
          <tr>
            <td><strong>2. Kiểm định Kiến trúc OWL 3 &amp; Sovereign Dark Mode</strong></td>
            <td>0 lỗi Console/OwlError; 0 Bare Hex; Tương thích 100% Light/Dark Mode</td>
            <td><strong>ĐẠT CHUẨN (PASSED)</strong></td>
          </tr>
          <tr>
            <td><strong>3. Kiểm toán Bảo mật ISO/IEC 27001 &amp; Nghị định 13/2023/NĐ-CP</strong></td>
            <td>Vượt qua 34 bài kiểm thử Adversarial Security; Che mờ PII &amp; Constant-Time Token</td>
            <td><strong>ĐẠT CHUẨN (PASSED)</strong></td>
          </tr>
          <tr>
            <td><strong>4. Xác nhận Hài lòng Khách hàng (Client CSAT &amp; Sign-off)</strong></td>
            <td>Khách hàng xác nhận nghiệm thu điện tử SHA-256 &amp; chấm điểm CSAT 360°</td>
            <td><strong>ĐẠT CHUẨN (PASSED)</strong></td>
          </tr>
        </tbody>
      </table>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="[TPL-PRJ-06] Biên bản Nghiệm thu Sprint, Kiểm thử UAT, Cổng Bảo mật & Bàn giao Go-Live PDCA (SOP-DGM-11)",
        doc_code="TPL-PRJ-06",
        sop_ref="SOP-DGM-11",
        classification="PROJECT ACCEPTANCE & UAT SIGN-OFF • SOP-DGM-11",
        include_header=True,
    )


def _build_tpl_hr_07_html():
    body = """
    <section>
      <h2>PHIẾU ĐÁNH GIÁ NHÂN SỰ ĐA CHIỀU 360° &amp; HIỆU CHUẨN MA TRẬN NHÂN TÀI 9-BOX (TPL-HR-07)</h2>
      <p>
        Biểu mẫu <strong>TPL-HR-07</strong> chuẩn hóa quy trình đánh giá nhân sự định kỳ (`dgm.hr.appraisal.sheet`) tại
        <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong>, tích hợp trực tiếp kết quả thực thi OKRs,
        phản hồi 360° từ khách hàng B2B (MTI, AIfin, KTT) và Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc.
      </p>
      <h3>1. Cơ Cấu Trọng Số Điểm Đánh Giá 360° (`calibrated_total_score`)</h3>
      <table>
        <thead>
          <tr>
            <th>Nguồn Đánh Giá (Appraisal Dimension)</th>
            <th>Trọng Số</th>
            <th>Trường Dữ Liệu Hệ Thống</th>
            <th>Mô Tả Tiêu Chí</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>1. Kết quả Thực thi Mục tiêu OKRs (OKR Achievement)</strong></td>
            <td><strong>35%</strong></td>
            <td><code>okr_achievement_pct</code></td>
            <td>Tỷ lệ hoàn thành các Key Results cam kết trong kỳ (chuẩn 0.00 – 1.00).</td>
          </tr>
          <tr>
            <td><strong>2. Đánh giá Chuyên môn của Tech Lead / Quản lý (Manager Appraisal)</strong></td>
            <td><strong>25%</strong></td>
            <td><code>manager_technical_score</code></td>
            <td>Chất lượng kiến trúc, năng lực giải quyết bài toán khó và kèm cặp đồng đội.</td>
          </tr>
          <tr>
            <td><strong>3. Phản hồi 360° từ Đồng nghiệp &amp; Khách hàng B2B (360° Peer &amp; Client)</strong></td>
            <td><strong>25%</strong></td>
            <td><code>peer_client_360_score</code></td>
            <td>Điểm CSAT từ đối tác B2B Onsite (MTI/AIfin/KTT) và đánh giá phối hợp liên phòng ban.</td>
          </tr>
          <tr>
            <td><strong>4. Tự Đánh giá &amp; Phản tư PDCA của Nhân sự (Self-Reflection)</strong></td>
            <td><strong>15%</strong></td>
            <td><code>self_assessment_score</code></td>
            <td>Mức độ chủ động nhận diện điểm mạnh, điểm nghẽn và đề xuất kế hoạch cải tiến quý tới.</td>
          </tr>
        </tbody>
      </table>
      <h3>2. Quy Tắc Khóa Cổng Kỹ Năng Trên Ma Trận 9-Box (`calibration_box`)</h3>
      <ul>
        <li><strong>Ô [9] Top Talent / Future Leader (`box_9_star`):</strong> Điểm hiệu chuẩn &ge; 92.0 <strong>VÀ</strong> đạt 100% kỹ năng bắt buộc (<code>skill_gate_passed = True</code>).</li>
        <li><strong>Ô [8] High Impact Engineer (`box_8_high_perf`):</strong> Điểm hiệu chuẩn 85.0 – 91.9 <strong>VÀ</strong> đạt 100% kỹ năng bắt buộc.</li>
        <li><strong>Ô [6] Emerging Potential (`box_6_emerging` — Khóa Trần Kỹ Năng):</strong> Nhân sự có năng lực thực thi cao (&ge; 75.0) nhưng <strong>chưa hoàn tất 100% học phần kỹ năng bắt buộc</strong>; điểm hiệu chuẩn bị khóa trần tại <strong>84.90</strong> cho đến khi hoàn thành chứng chỉ.</li>
        <li><strong>Ô [5] Solid Core Contributor (`box_5_core`):</strong> Điểm hiệu chuẩn 75.0 – 84.9 và đã hoàn tất cổng kỹ năng.</li>
        <li><strong>Ô [2] Action Required / PIP 30 Ngày (`box_2_pip`):</strong> Điểm hiệu chuẩn &lt; 75.0, kích hoạt kế hoạch kèm cặp cải thiện hiệu suất.</li>
      </ul>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="[TPL-HR-07] Phiếu Đánh giá Nhân sự Đa chiều 360° & Hiệu chuẩn Ma trận Nhân tài 9-Box (SOP-DGM-11)",
        doc_code="TPL-HR-07",
        sop_ref="SOP-DGM-11",
        classification="HR CONFIDENTIAL • 360 APPRAISAL & 9-BOX CALIBRATION",
        include_header=True,
    )


def _build_tpl_hr_08_html():
    body = """
    <section>
      <h2>BIÊN BẢN HỌP HỘI ĐỒNG HIỆU CHUẨN NĂNG LỰC &amp; XÉT THĂNG CẤP KỸ SƯ PHẦN MỀM — CAREER CALIBRATION (TPL-HR-08)</h2>
      <p>
        Biểu mẫu <strong>TPL-HR-08</strong> ghi nhận kết quả phiên họp Hiệu chuẩn Nhân tài (Talent Calibration Session)
        của Hội đồng Công nghệ &amp; Nhân sự Digimate cuối Quý 4/2026 cho toàn bộ 9 nhân sự (`DGM-001`..`DGM-009`).
      </p>
      <table>
        <thead>
          <tr>
            <th>Mã NV</th>
            <th>Họ và Tên</th>
            <th>Cấp Bậc</th>
            <th>OKR Cam Kết</th>
            <th>Cổng Kỹ Năng SWE</th>
            <th>Ô Hiệu Chuẩn 9-Box</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>DGM-001</code></td><td>Lê Xuân Hoàng</td><td>L5 Principal</td><td><code>OKR-2026-Q4-C01</code></td><td>100% Certified</td><td><strong>9-Box [9] Top Talent</strong></td></tr>
          <tr><td><code>DGM-002</code></td><td>Nguyễn Hoài Ân</td><td>L5 Principal</td><td><code>OKR-2026-Q4-C02</code></td><td>100% Certified</td><td><strong>9-Box [9] Top Talent</strong></td></tr>
          <tr><td><code>DGM-003</code></td><td>Mai Thị Hồng Thắm</td><td>L4 Lead</td><td><code>OKR-2026-Q4-C03</code></td><td>100% Certified</td><td><strong>9-Box [9] Top Talent</strong></td></tr>
          <tr><td><code>DGM-004</code></td><td>Bùi Hữu Tài</td><td>L3 Senior</td><td><code>OKR-2026-Q4-B2B01</code></td><td>100% Certified</td><td><strong>9-Box [9] Top Talent</strong></td></tr>
          <tr><td><code>DGM-005</code></td><td>Huỳnh Trần Quang Khánh</td><td>L4 Lead</td><td><code>OKR-2026-Q4-ENG01</code></td><td>100% Certified</td><td><strong>9-Box [9] Top Talent</strong></td></tr>
          <tr><td><code>DGM-006</code></td><td>Ngô Thanh Lộc</td><td>L3 Senior</td><td><code>OKR-2026-Q4-B2B02</code></td><td>100% Certified</td><td><strong>9-Box [8] High Impact</strong></td></tr>
          <tr><td><code>DGM-007</code></td><td>Lê Cao Bảo Phúc</td><td>L2 Mid</td><td><code>OKR-2026-Q4-B2B03</code></td><td>2/3 (Chờ <code>SKL-ERP-OWL3</code>)</td><td><strong>9-Box [6] Emerging (Cap 84.9)</strong></td></tr>
          <tr><td><code>DGM-008</code></td><td>Thái Nguyễn Đăng Khoa</td><td>L1 Junior</td><td><code>OKR-2026-Q4-QA01</code></td><td>2/3 (Chờ <code>SKL-QA-PLAYWRIGHT</code>)</td><td><strong>9-Box [6] Emerging (Cap 84.9)</strong></td></tr>
          <tr><td><code>DGM-009</code></td><td>Trần Văn Huỳnh Phố</td><td>L3 Senior</td><td><code>OKR-2026-Q4-B2B04</code></td><td>100% Certified</td><td><strong>9-Box [9] Top Talent</strong></td></tr>
        </tbody>
      </table>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="[TPL-HR-08] Biên bản Họp Hội đồng Hiệu chuẩn Năng lực & Xét Thăng cấp Kỹ sư Phần mềm (SOP-DGM-11)",
        doc_code="TPL-HR-08",
        sop_ref="SOP-DGM-11",
        classification="HR EXECUTIVE COMMITTEE • CAREER CALIBRATION MINUTES",
        include_header=True,
    )


def _build_tpl_okr_01_html():
    body = """
    <section>
      <h2>KHUNG MỤC TIÊU CHIẾN LƯỢC OKRs DOANH NGHIỆP PHẦN MỀM DIGIMATE &amp; INNORIA NĂM 2026 (TPL-OKR-01)</h2>
      <p>
        Tài liệu <strong>TPL-OKR-01</strong> quy định kiến trúc phân rã Mục tiêu &amp; Kết quả Then chốt (Objectives &amp; Key Results — OKRs)
        3 tầng cho doanh nghiệp phần mềm Digimate / Innoria theo phương pháp quản trị PDCA.
      </p>
      <h3>1. Ba Mục Tiêu Chiến Lược Cấp Công Ty (Company Strategic OKRs — Quý 4/2026)</h3>
      <table>
        <thead>
          <tr>
            <th>Mã OKR</th>
            <th>Mục Tiêu Chiến Lược (Objective)</th>
            <th>Kết Quả Then Chốt (Key Results)</th>
            <th>Chủ Sở Hữu</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>OKR-2026-Q4-C01</code></td>
            <td><strong>Tăng trưởng Doanh thu Dịch vụ Phần mềm B2B, Turnkey ERP &amp; Xuất khẩu 0% VAT</strong></td>
            <td><code>KR-01</code>: Doanh thu &ge; 1,850 Triệu VNĐ<br/><code>KR-02</code>: 100% Nghiệm thu SHA-256 &amp; Hóa đơn 1C26TAA đúng hạn</td>
            <td>Lê Xuân Hoàng (<code>DGM-001</code>)</td>
          </tr>
          <tr>
            <td><code>OKR-2026-Q4-C02</code></td>
            <td><strong>Xuất sắc Kỹ thuật Nền tảng Insilos Odoo 20, AI Agentic Mojo &amp; Cổng Kỹ năng SWE</strong></td>
            <td><code>KR-03</code>: 100% vượt qua 6 tầng kiểm định tự động<br/><code>KR-04</code>: &ge; 90% tỷ lệ hoàn thành Cổng Kỹ năng Bắt buộc</td>
            <td>Nguyễn Hoài Ân (<code>DGM-002</code>)</td>
          </tr>
          <tr>
            <td><code>OKR-2026-Q4-C03</code></td>
            <td><strong>Tuân thủ Tuyệt đối Pháp chế Thuế, BHXH TZ0857G, ISO/IEC 27001 &amp; ISO 27701</strong></td>
            <td><code>KR-05</code>: 100% kỳ lương VCB DigiBiz 11 cột &amp; Thuế đúng hạn<br/><code>KR-06</code>: 100% tài liệu gắn RBAC &amp; Zero-Leak PII</td>
            <td>Mai Thị Hồng Thắm (<code>DGM-003</code>)</td>
          </tr>
        </tbody>
      </table>
      <h3>2. Liên Kết Trực Tiếp Giữa OKRs, Khung Mẫu Dự Án &amp; Đánh Giá Nhân Sự 360°</h3>
      <p>
        Mỗi khi một Key Result được cập nhật qua <code>action_update_kr_checkin()</code>, hệ thống tự động tính toán lại
        <code>okr_score</code> (thang <code>0.00 – 1.00</code>), phân loại <code>confidence_level</code> (<code>on_track</code>,
        <code>at_risk</code>, <code>off_track</code>) và đồng bộ ngay lập tức sang phiếu đánh giá 360° (<code>dgm.hr.appraisal.sheet</code>)
        của nhân sự phụ trách.
      </p>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="[TPL-OKR-01] Khung Mục tiêu Chiến lược OKRs Doanh nghiệp Phần mềm Digimate & Innoria 2026 (SOP-DGM-11)",
        doc_code="TPL-OKR-01",
        sop_ref="SOP-DGM-11",
        classification="STRATEGIC PLANNING • SOFTWARE ENTERPRISE OKR FRAMEWORK",
        include_header=True,
    )


def _build_sop_dgm_11_html():
    body = """
    <section>
      <h2>SOP-DGM-11: QUY TRÌNH VÒNG LẶP PDCA QUẢN TRỊ DỰ ÁN PHẦN MỀM, ĐÁNH GIÁ NHÂN SỰ 360° (HR APPRAISALS 9-BOX) &amp; TRIỂN KHAI OKRs DOANH NGHIỆP PHẦN MỀM</h2>
      <p>
        <strong>Mã Quy trình:</strong> <code>SOP-DGM-11</code> •
        <strong>Pháp nhân:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465 • Mã ĐV BHXH: TZ0857G)
      </p>
      <h3>I. Kiến Trúc Vòng Lặp PDCA Hợp Nhất (Plan – Do – Check – Act)</h3>
      <ol>
        <li><strong>PLAN (Hoạch định):</strong> Thiết lập 3 OKR Cấp Công ty và 9 OKR Cấp Squad/Cá nhân (<code>dgm.okr.objective</code>, 24 <code>dgm.okr.key.result</code>), gắn với 4 Khung Mẫu Dự án Phần mềm (<code>dgm.project.pdca.template</code>: <code>PRJ-TPL-PDCA-01..04</code>).</li>
        <li><strong>DO (Thực thi):</strong> Đội ngũ kỹ sư triển khai Sprint dự án (Turnkey ERP, B2B Onsite MTI/AIfin, R&amp;D AI/Mojo, GRC ISO 27001) và thực hành các chuyên đề nâng cấp kỹ năng bắt buộc (<code>dgm.hr.employee.skill.gate</code>).</li>
        <li><strong>CHECK (Đo lường &amp; Kiểm toán):</strong> Cập nhật tiến độ KR (<code>action_update_kr_checkin</code>), kiểm định tự động 6 tầng, thu thập chữ ký nghiệm thu khách hàng SHA-256 và đánh giá đa chiều 360° (<code>dgm.hr.appraisal.sheet</code>).</li>
        <li><strong>ACT (Chuẩn hóa &amp; Đãi ngộ):</strong> Hội đồng Hiệu chuẩn Nhân tài xếp hạng ma trận <strong>9-Box</strong> (<code>box_9_star</code>, <code>box_8_high_perf</code>, <code>box_6_emerging</code>, <code>box_5_core</code>, <code>box_2_pip</code>), mở khóa thưởng hiệu suất và thăng cấp khi hoàn tất 100% Cổng Kỹ năng Bắt buộc.</li>
      </ol>
      <h3>II. Danh Mục 6 Biểu Mẫu &amp; Quy Trình Chuẩn Ban Hành Kèm Theo</h3>
      <ul>
        <li><code>TPL-PRJ-05</code>: Mẫu Kế hoạch Dự án Phần mềm PDCA &amp; SAP Activate</li>
        <li><code>TPL-PRJ-06</code>: Biên bản Nghiệm thu Sprint, UAT &amp; Go-Live PDCA</li>
        <li><code>TPL-HR-07</code>: Phiếu Đánh giá Nhân sự 360° &amp; Ma trận 9-Box PDCA</li>
        <li><code>TPL-HR-08</code>: Biên bản Hiệu chuẩn Năng lực &amp; Xét Thăng cấp Kỹ sư Phần mềm</li>
        <li><code>TPL-OKR-01</code>: Khung OKRs Doanh nghiệp Phần mềm Digimate &amp; Innoria 2026</li>
        <li><code>SOP-DGM-11</code>: Quy trình Chuẩn PDCA Quản trị Dự án, HR Appraisals &amp; OKRs Phần mềm</li>
      </ul>
    </section>
    """
    return wrap_dgm_branded_html_document(
        body_html=body,
        title="SOP-DGM-11: Quy trình PDCA Quản trị Dự án Phần mềm, Đánh giá Nhân sự 360° (HR Appraisals) & OKRs Doanh nghiệp Phần mềm",
        doc_code="SOP-DGM-11",
        sop_ref="SOP-DGM-11",
        classification="CORPORATE GOVERNANCE • PDCA PROJECT, APPRAISAL & OKR SOP",
        include_header=True,
    )


def seed_database(dbname):
    print(f"\n=== Seeding SOP-DGM-11 Project PDCA Templates, 360° HR Appraisals & Software OKRs in `{dbname}` ===")
    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        # 1. Initialize models in schema
        reg.init_models(
            cr,
            [
                "dgm.okr.objective",
                "dgm.okr.key.result",
                "dgm.hr.appraisal.sheet",
                "dgm.project.pdca.template",
                "hr.employee",
            ],
            {"module": "insilos_al2c"},
            install=True,
        )

        env = api.Environment(cr, SUPERUSER_ID, {"no_document": True})

        # 2. Load security/ir.access.csv and views/dgm_okr_appraisal_project_views.xml
        for rel_path in (
            "security/ir.access.csv",
            "views/dgm_okr_appraisal_project_views.xml",
        ):
            full_path = os.path.join(ROOT_DIR, "addons/insilos_al2c", rel_path)
            if os.path.isfile(full_path):
                convert_file(
                    env,
                    "insilos_al2c",
                    rel_path,
                    {},
                    mode="init",
                    noupdate=False,
                    kind="data",
                )

        # Ensure SOP-DGM-10 baseline exists and canonical skill gates are idempotently restored
        KpiEval = env["dgm.hr.kpi.evaluation"].sudo()
        if hasattr(KpiEval, "seed_dgm_kpi_and_skill_framework"):
            KpiEval.seed_dgm_kpi_and_skill_framework()

        Employee = env["hr.employee"].sudo()
        SkillTrack = env["dgm.hr.skill.track"].sudo()
        OkrObj = env["dgm.okr.objective"].sudo()
        OkrKr = env["dgm.okr.key.result"].sudo()
        Appraisal = env["dgm.hr.appraisal.sheet"].sudo()
        PdcaTpl = env["dgm.project.pdca.template"].sudo()
        Project = env["project.project"].sudo()
        Stage = env["project.task.type"].sudo()

        # Resolve folders
        hr_folder = _resolve_folder(
            env,
            preferred_id=3224 if dbname == "insilos20_dev" else 208,
            name_patterns=["03 · Nhân Sự", "01. Pháp lý & Hành chính", "01. Hành chính"],
        )
        sop_folder = _resolve_folder(
            env,
            preferred_id=4704 if dbname == "insilos20_dev" else 214,
            name_patterns=["02 · Quy Trình", "07. Quy trình Chuẩn & Tự động hóa", "07. Quy trình"],
        )
        prj_folder = _resolve_folder(
            env,
            preferred_id=False,
            name_patterns=["06 · Dự Án & Khách Hàng", "03. Hợp đồng & Thương mại", "INNO - HỢP ĐỒNG"],
        )
        if not prj_folder:
            prj_folder = sop_folder
        lib_folder = _resolve_folder(
            env,
            preferred_id=4942 if dbname == "insilos20_dev" else 526,
            name_patterns=[MASTER_LIBRARY_FOLDER_NAME, "Bộ Mẫu Biểu Chuẩn Digimate"],
            parent_id=sop_folder.id if sop_folder else False,
        )

        # 3. Seed 5 canonical PDCA / SAP Activate stages and 4 Project PDCA Templates
        pdca_stage_names = [
            (10, "1. Plan & Prepare"),
            (20, "2. Explore & Architecture"),
            (30, "3. Do / Realize Sprint"),
            (40, "4. Check / UAT & Security Gate"),
            (50, "5. Act / Deploy & Run SLA"),
        ]
        stage_ids = []
        for seq, st_name in pdca_stage_names:
            st = Stage.search([("name", "=", st_name)], limit=1)
            if not st:
                st = Stage.create({"name": st_name, "sequence": seq})
            stage_ids.append(st.id)

        for tpl_bp in CANONICAL_PROJECT_PDCA_TEMPLATES:
            proj_name = tpl_bp["name"]
            proj = Project.with_context(active_test=False).search([("name", "=", proj_name)], limit=1)
            proj_vals = {
                "name": proj_name,
                "allow_timesheets": True,
                "active": True,
                "type_ids": [(6, 0, stage_ids)],
            }
            if "is_template" in Project._fields:
                proj_vals["is_template"] = True
            if prj_folder and "documents_folder_id" in Project._fields:
                proj_vals["documents_folder_id"] = prj_folder.id
            if proj:
                proj.with_context(no_create_folder=True).write(proj_vals)
            else:
                proj = Project.with_context(mail_create_nosubscribe=True, no_create_folder=True).create(proj_vals)

            existing_tpl = PdcaTpl.search([("code", "=", tpl_bp["code"])], limit=1)
            tpl_vals = {
                "code": tpl_bp["code"],
                "name": tpl_bp["name"],
                "delivery_methodology": tpl_bp["delivery_methodology"],
                "linked_project_id": proj.id,
                "plan_phase_gate": tpl_bp["plan_phase_gate"],
                "do_phase_gate": tpl_bp["do_phase_gate"],
                "check_phase_gate": tpl_bp["check_phase_gate"],
                "act_phase_gate": tpl_bp["act_phase_gate"],
                "mandatory_deliverable_codes": tpl_bp["mandatory_deliverable_codes"],
                "target_margin_pct": tpl_bp["target_margin_pct"],
                "target_sla_uptime_pct": tpl_bp["target_sla_uptime_pct"],
                "active": True,
            }
            if existing_tpl:
                existing_tpl.write(tpl_vals)
            else:
                PdcaTpl.create(tpl_vals)

        # Map employees & skill tracks
        all_emps = Employee.search([("active", "=", True)])
        emp_by_reg = {e.registration_number: e for e in all_emps if e.registration_number}
        all_tracks = SkillTrack.search([("active", "=", True)])
        track_by_code = {t.code: t for t in all_tracks if t.code}

        # 4. Seed 12 Canonical Software Enterprise OKRs & 24 Key Results
        obj_by_code = {}
        for okr_bp in CANONICAL_OKR_BLUEPRINTS:
            owner = emp_by_reg.get(okr_bp["owner_reg"])
            parent_obj = obj_by_code.get(okr_bp["parent_code"]) if okr_bp.get("parent_code") else False
            obj_vals = {
                "code": okr_bp["code"],
                "name": okr_bp["name"],
                "period_code": "2026-Q4",
                "okr_tier": okr_bp["okr_tier"],
                "parent_objective_id": parent_obj.id if parent_obj else False,
                "owner_employee_id": owner.id if owner else False,
                "department_name": okr_bp["department_name"],
                "project_template_code": okr_bp["project_template_code"],
                "pdca_stage": okr_bp["pdca_stage"],
                "pdca_retrospective": okr_bp["pdca_retrospective"],
                "active": True,
            }
            existing_obj = OkrObj.search([("code", "=", okr_bp["code"])], limit=1)
            if existing_obj:
                existing_obj.write(obj_vals)
                obj_rec = existing_obj
            else:
                obj_rec = OkrObj.create(obj_vals)
            obj_by_code[okr_bp["code"]] = obj_rec

            for kr_bp in okr_bp["krs"]:
                skill_rec = track_by_code.get(kr_bp.get("skill_code"))
                kr_vals = {
                    "code": kr_bp["code"],
                    "name": kr_bp["name"],
                    "objective_id": obj_rec.id,
                    "owner_employee_id": owner.id if owner else False,
                    "metric_unit": kr_bp["metric_unit"],
                    "start_value": kr_bp["start_value"],
                    "target_value": kr_bp["target_value"],
                    "current_value": kr_bp["current_value"],
                    "weight": kr_bp["weight"],
                    "linked_skill_track_id": skill_rec.id if skill_rec else False,
                    "evidence_ref": kr_bp["evidence_ref"],
                }
                existing_kr = OkrKr.search([("code", "=", kr_bp["code"])], limit=1)
                if existing_kr:
                    existing_kr.write(kr_vals)
                    kr_rec = existing_kr
                else:
                    kr_rec = OkrKr.create(kr_vals)
                kr_rec._compute_kr_progress()

            obj_rec._compute_okr_metrics()

        # 5. Seed 9 Canonical 360-Degree HR Appraisal Sheets (APR-2026-Q4-DGM001..009)
        for ap_bp in CANONICAL_APPRAISAL_BLUEPRINTS:
            emp = emp_by_reg.get(ap_bp["reg_no"])
            if not emp:
                continue
            kpi_ev = KpiEval.search([
                ("employee_id", "=", emp.id),
                ("period_code", "=", "2026-Q4"),
            ], limit=1)
            linked_objs = [obj_by_code[c].id for c in ap_bp["okr_codes"] if c in obj_by_code]
            ap_vals = {
                "code": ap_bp["code"],
                "name": ap_bp["name"],
                "employee_id": emp.id,
                "period_code": "2026-Q4",
                "kpi_evaluation_id": kpi_ev.id if kpi_ev else False,
                "okr_objective_ids": [(6, 0, linked_objs)],
                "self_assessment_score": ap_bp["self_score"],
                "peer_client_360_score": ap_bp["peer_360_score"],
                "manager_technical_score": ap_bp["manager_score"],
                "self_reflection_text": ap_bp["self_reflection"],
                "peer_client_feedback_text": ap_bp["peer_feedback"],
                "manager_appraisal_text": ap_bp["manager_appraisal"],
                "pdca_next_quarter_plan": ap_bp["next_plan"],
                "state": "signed_off",
                "active": True,
            }
            existing_ap = Appraisal.search([("code", "=", ap_bp["code"])], limit=1)
            if existing_ap:
                existing_ap.write(ap_vals)
                ap_rec = existing_ap
            else:
                ap_rec = Appraisal.create(ap_vals)
            ap_rec._compute_appraisal_calibration()

        # 6. Seed 6 Standardized Branded HTML Templates in documents.document
        tpl_docs_spec = [
            (TPL_PRJ_05_FILENAME, _build_tpl_prj_05_html(), "TPL-PRJ-05", [prj_folder, lib_folder]),
            (TPL_PRJ_06_FILENAME, _build_tpl_prj_06_html(), "TPL-PRJ-06", [prj_folder, lib_folder]),
            (TPL_HR_07_FILENAME, _build_tpl_hr_07_html(), "TPL-HR-07", [hr_folder, lib_folder]),
            (TPL_HR_08_FILENAME, _build_tpl_hr_08_html(), "TPL-HR-08", [hr_folder, lib_folder]),
            (TPL_OKR_01_FILENAME, _build_tpl_okr_01_html(), "TPL-OKR-01", [sop_folder, lib_folder]),
            (SOP_11_DOC_FILENAME, _build_sop_dgm_11_html(), "SOP-DGM-11", [sop_folder, lib_folder]),
        ]
        for fname, html_content, marker, folders in tpl_docs_spec:
            for target_folder in folders:
                if target_folder:
                    _upsert_html_doc(
                        env,
                        folder_id=target_folder.id,
                        doc_name=fname,
                        filename=fname,
                        html_str=html_content,
                        code_marker=marker,
                    )
            # Also ensure any pre-existing document with the same name or marker in any folder is upgraded
            b64_datas = base64.b64encode(html_content.encode("utf-8"))
            all_matching = env["documents.document"].sudo().with_context(active_test=False).search([
                ("type", "!=", "folder"),
                "|",
                ("name", "=", fname),
                ("name", "ilike", f"{marker}%"),
            ])
            for mdoc in all_matching:
                _ensure_doc_active(env, mdoc)
                if mdoc.attachment_id:
                    mdoc.attachment_id.with_context(no_document=True).write({
                        "name": fname,
                        "datas": b64_datas,
                        "mimetype": "text/html",
                    })
                else:
                    att = env["ir.attachment"].sudo().with_context(no_document=True).create({
                        "name": fname,
                        "type": "binary",
                        "datas": b64_datas,
                        "mimetype": "text/html",
                        "res_model": "documents.document",
                        "res_id": mdoc.id,
                    })
                    mdoc.write({"attachment_id": att.id})
                mdoc.write({
                    "owner_id": False,
                    "access_internal": "edit",
                    "access_via_link": "view",
                })

        # 7. Seed SOP-DGM-11 Knowledge Article with Drive Logo Brand Footer
        sop_11_html = _build_sop_dgm_11_html()
        if "knowledge.article" in env:
            Article = env["knowledge.article"].sudo()
            dgm_root = Article.search([("name", "ilike", "DGM · Quy Trình Vận Hành Chuẩn%")], order="id asc", limit=1)
            kb_11 = Article.search([("name", "ilike", "SOP-DGM-11%")], order="id asc", limit=1)
            kb_title = (
                "SOP-DGM-11: Quy trình PDCA Quản trị Dự án Phần mềm, Đánh giá Nhân sự 360° "
                "(HR Appraisals 9-Box) & Triển khai OKRs Doanh nghiệp Phần mềm"
            )
            if not kb_11:
                kb_11 = Article.create({
                    "name": kb_title,
                    "parent_id": dgm_root.id if dgm_root else False,
                    "body": sop_11_html,
                    "internal_permission": "write",
                    "is_article_visible_by_everyone": True,
                    "active": True,
                })
            else:
                kb_11.write({
                    "name": kb_title,
                    "parent_id": dgm_root.id if dgm_root else kb_11.parent_id.id,
                    "active": True,
                })
            env.flush_all()
            cr.execute(
                "UPDATE knowledge_article SET body = %s, active = TRUE WHERE id = %s",
                (sop_11_html, kb_11.id),
            )
            kb_11.invalidate_recordset(["body", "active"])

            IrModelData = env["ir.model.data"].sudo()
            imd = IrModelData.search([
                ("module", "=", "insilos_al2c"),
                ("name", "=", "kb_dgm_sop_11_okr_appraisal_pdca"),
            ], limit=1)
            if not imd:
                IrModelData.create({
                    "module": "insilos_al2c",
                    "name": "kb_dgm_sop_11_okr_appraisal_pdca",
                    "model": "knowledge.article",
                    "res_id": kb_11.id,
                    "noupdate": True,
                })

        # 8. Reconcile RBAC Matrix & Enforce Zero Empty Folders Invariant
        Document = env["documents.document"].sudo()
        for _ in range(5):
            cr.execute(
                """
                SELECT f.id
                  FROM documents_document f
                 WHERE f.type = 'folder' AND f.active = TRUE
                   AND NOT EXISTS (
                       SELECT 1 FROM documents_document c
                        WHERE c.folder_id = f.id AND c.active = TRUE
                   );
                """
            )
            empty_ids = [r[0] for r in cr.fetchall()]
            if not empty_ids:
                break
            Document.browse(empty_ids).write({"active": False})

        if hasattr(Document, "apply_dgm_inno_rbac_matrix"):
            Document.apply_dgm_inno_rbac_matrix()

        cr.commit()

    print(f"[✓] `{dbname}` SOP-DGM-11 Project PDCA Templates, 360° Appraisals & OKRs seeded and committed.")


def main():
    db_list = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev", "innoria_prod"]
    for dbname in db_list:
        seed_database(dbname)
    print("\n=== ALL SOP-DGM-11 PDCA PROJECT, APPRAISAL & OKR SEEDING COMPLETED (EXIT 0) ===")


if __name__ == "__main__":
    main()
