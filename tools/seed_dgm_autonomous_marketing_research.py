#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotent Seeder for SOP-DGM-13:
Autonomous Marketing Automation, Continuous B2B Market Research,
Competitor Intelligence Battlecards & GEO Content Supply Chain
(`dgm.market.research.radar`, `dgm.marketing.automation.campaign`,
`al2c.claim.atom`, `al2c.marketing.kit`, `marketing.campaign`, `al2c.rag.chunk`,
`dgm.knowledge.sop.workflow`, `knowledge.article`, `documents.document`)
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
    _extra = [
        p
        for p in (
            "/var/lib/insilos/filestore/custom_addons",
            f"{ROOT_DIR}/odoo/addons",
            f"{ROOT_DIR}/addons",
            f"{ROOT_DIR}/enterprise",
        )
        if os.path.isdir(p)
    ]
    odoo.tools.config.parse_config(
        [
            f"--addons-path={','.join(_extra)}",
            "--data-dir=/var/lib/insilos/filestore",
            f"--db_host={os.environ.get('DB_HOST', 'pgbouncer-service')}",
            f"--db_port={os.environ.get('DB_PORT', '6432')}",
            f"--db_user={os.environ.get('DB_USER', 'insilos')}",
            f"--db_password={os.environ.get('PGPASSWORD', '')}",
        ]
    )
elif os.path.exists(_local_conf):
    odoo.tools.config.parse_config(["-c", _local_conf])
else:
    odoo.tools.config.parse_config([])

from odoo.addons.insilos_al2c.models.dgm_brand_footer import (  # noqa: E402
    wrap_dgm_branded_html_document,
)


CANONICAL_CLAIMS = [
    {
        "name": "CLAIM-SOP13-01: Dedicated Agile Squad SLA 140-180h & Mandatory SWE Skill Gate",
        "claim_type": "sla",
        "claim_text": (
            "Innoria / Digimate JSC (MST 0317958465) vận hành đội ngũ kỹ sư chuyên trách (Dedicated Agile Squad) "
            "theo chuẩn MTI Technology & Canva với định mức 140–180 giờ/tháng, 100% kỹ sư vượt qua Cổng Kỹ năng Bắt buộc "
            "(SOP-DGM-10/11) và đối soát hóa đơn nháp 2 bước trước khi phát hành HĐĐT 1C26TAA (SOP-DGM-08)."
        ),
    },
    {
        "name": "CLAIM-SOP13-02: Turnkey Software & AI Product 100% IP Handover & 99.9% Uptime SLA",
        "claim_type": "feature",
        "claim_text": (
            "Giải pháp Turnkey Custom Software & AI Product Engineering (mô hình AIfin 360-Sales) bàn giao 100% "
            "mã nguồn và quyền sở hữu trí tuệ (IP) theo 4 mốc SAP Activate + PDCA, đi kèm cam kết SLA vận hành 99.9%."
        ),
    },
    {
        "name": "CLAIM-SOP13-03: Clean-Core Enterprise ERP, Native Decree 70 E-Invoice & VCB DigiBiz Payroll",
        "claim_type": "compliance",
        "claim_text": (
            "Nền tảng Insilos Enterprise ERP (Odoo 20 Clean-Core) tích hợp gốc Hóa đơn Điện tử Nghị định 70/2025/NĐ-CP "
            "(ký hiệu 1C26TAA), bảo hiểm xã hội bắt buộc mã đơn vị TZ0857G (BHXH Quận 7) và xuất bảng lương VCB DigiBiz 11 cột."
        ),
    },
    {
        "name": "CLAIM-SOP13-04: ISO/IEC 27001 & 27701, Decree 13/2023 PDPD Partial Masking & GHS Chemical Safety",
        "claim_type": "compliance",
        "claim_text": (
            "Hệ thống GRC & Bảo vệ Dữ liệu Cá nhân tuân thủ ISO/IEC 27001, ISO/IEC 27701 và Nghị định 13/2023/NĐ-CP "
            "với cơ chế che dấu mặc định CCCD/SĐT/Tài khoản ngân hàng, mở khóa 30 giây ghi nhật ký bất biến và quản lý an toàn hóa chất GHS."
        ),
    },
    {
        "name": "CLAIM-SOP13-05: 4-Layer Grounded SOP-RAG Defense with Entailment >= 0.85 & Hybrid RRF k=60",
        "claim_type": "benchmark",
        "claim_text": (
            "Kiến trúc Sovereign AI Concierge & Internal SOP-RAG Copilot áp dụng 4 lớp phòng vệ: Chặn Prompt Injection, "
            "Lọc quyền RBAC trước khi truy xuất Hybrid RRF (k=60), Kiểm chứng Entailment >= 0.85 kèm trích dẫn SHA-256 "
            "và Bộ lọc PII tự động theo chuẩn ISO 27701."
        ),
    },
    {
        "name": "CLAIM-SOP13-06: ZenCode Enterprise Autonomous DevSecOps & 0% Export Software VAT",
        "claim_type": "pricing_rule",
        "claim_text": (
            "Dịch vụ xuất khẩu phần mềm quốc tế và ZenCode Autonomous Engineering của Digimate JSC / Innoria "
            "áp dụng thuế suất GTGT 0% cho hợp đồng xuất khẩu phần mềm ngoài lãnh thổ Việt Nam và ưu đãi thuế TNDN doanh nghiệp phần mềm."
        ),
    },
]


CANONICAL_RADARS = [
    {
        "code": "MKT-RES-01",
        "name": "Dedicated Agile Squad & Staff Augmentation (Onsite / Offshore — MTI & Canva Model)",
        "service_pillar": "sw_squad",
        "target_icp_segment": "fdi_tech_banking",
        "tam_vnd_billion": 18500.0,
        "sam_vnd_billion": 4200.0,
        "som_target_vnd_billion": 185.0,
        "cagr_pct": 21.5,
        "primary_competitors": "FPT Software, NashTech, KMS Technology, Savvycom",
        "competitor_weakness_matrix": (
            "1. Các công ty gia công quy mô lớn thường luân chuyển nhân sự liên tục (shadow resources), thiếu cam kết giữ nguyên Senior Engineer.\n"
            "2. Quy trình chốt công và xuất hóa đơn cứng nhắc, thiếu bước đối soát Hóa đơn Nháp chuẩn MTI trước khi phát hành HĐĐT.\n"
            "3. Thiếu cổng kiểm soát kỹ năng bắt buộc gắn trực tiếp với xếp hạng KPI và đánh giá 360°."
        ),
        "innoria_moat_proposition": (
            "• Cam kết định danh từng kỹ sư (Named Senior Engineers) với SLA 140–180h/tháng.\n"
            "• Cổng Kỹ năng Bắt buộc khóa trần Hạng B (SOP-DGM-10/11) đảm bảo 100% kỹ sư có chứng chỉ AI/Odoo/Security.\n"
            "• Quy trình nghiệm thu Timesheet có chữ ký số SHA-256 & Đối soát Hóa đơn Nháp 2 bước chuẩn MTI (SOP-DGM-08)."
        ),
        "win_rate_benchmark_pct": 46.0,
        "recommended_pricing_anchor_vnd": 65000000.0,
        "geo_keywords": (
            "dedicated software squad vietnam, staff augmentation ho chi minh, thue ky su phan mem onsite mti, "
            "agile offshore development center vietnam, innoria software engineering squad"
        ),
        "battlecard_markdown": (
            "## Battlecard MKT-RES-01: Dedicated Agile Squad vs. Traditional Outsourcers\n"
            "- **Điểm khác biệt số 1 (Quality Gate)**: 100% kỹ sư chịu sự giám sát của Cổng Kỹ năng Bắt buộc (SOP-DGM-10/11).\n"
            "- **Điểm khác biệt số 2 (Billing Transparency)**: Khách hàng duyệt Timesheet qua Portal bảo mật HMAC trước khi xuất Hóa đơn Nháp MTI.\n"
            "- **Case Study thực증**: Đội ngũ 4 Senior Engineers vận hành liên tục cho MTI Technology (250 triệu VNĐ/tháng chưa thuế)."
        ),
        "claim_idx": 0,
    },
    {
        "code": "MKT-RES-02",
        "name": "Turnkey Custom Software & AI Product Engineering (AIfin 360-Sales Blueprint)",
        "service_pillar": "sw_turnkey",
        "target_icp_segment": "sme_growth_vn",
        "tam_vnd_billion": 14200.0,
        "sam_vnd_billion": 3100.0,
        "som_target_vnd_billion": 140.0,
        "cagr_pct": 24.0,
        "primary_competitors": "CMC Global, VMO Holdings, Rikkeisoft, Boutique Dev Studios",
        "competitor_weakness_matrix": (
            "1. Các studio nhỏ bàn giao mã nguồn thiếu kiểm thử bảo mật (SAST/DAST) và không có tài liệu kiến trúc chuẩn.\n"
            "2. Rủi ro đội vốn (scope creep) do thiếu lộ trình nghiệm thu 4 mốc gắn với chu trình PDCA.\n"
            "3. Giữ lại thư viện độc quyền khiến khách hàng bị phụ thuộc nhà cung cấp (vendor lock-in)."
        ),
        "innoria_moat_proposition": (
            "• Bàn giao 100% Mã nguồn, CI/CD Pipeline và Quyền Sở hữu Trí tuệ (IP) ngay khi tất toán hợp đồng.\n"
            "• Triển khai theo 4 giai đoạn chuẩn SAP Activate + PDCA (Prepare, Explore, Realize, Deploy & Run).\n"
            "• Tích hợp sẵn dự toán tức thì ESIH trên innoria.com giúp minh bạch ngân sách ngay từ ngày đầu."
        ),
        "win_rate_benchmark_pct": 44.0,
        "recommended_pricing_anchor_vnd": 185000000.0,
        "geo_keywords": (
            "cong ty phat trien phan mem theo yeu cau tphcm, turnkey software development vietnam, "
            "xay dung he thong crm 360 sales aifin, custom enterprise web mobile app innoria"
        ),
        "battlecard_markdown": (
            "## Battlecard MKT-RES-02: Turnkey Software Engineering vs. Dev Boutiques\n"
            "- **Điểm khác biệt số 1 (Zero Lock-in)**: Bàn giao trọn gói Git repo, Docker/K8s manifests và tài liệu AST.\n"
            "- **Điểm khác biệt số 2 (Predictable Delivery)**: Quản trị theo mẫu dự án PDCA (`PRJ-TPL-02`) với tỷ lệ lỗi lọt Production <= 1.5%.\n"
            "- **Case Study thực chứng**: Dự án AIFin 360-Sales & Onsite Engineering (HĐ DIGIMATE-AIFIN-VN_2610-001)."
        ),
        "claim_idx": 1,
    },
    {
        "code": "MKT-RES-03",
        "name": "Clean-Core Enterprise ERP, E-Invoice (NĐ 70) & Statutory Payroll",
        "service_pillar": "erp",
        "target_icp_segment": "manufacturing_supply",
        "tam_vnd_billion": 22000.0,
        "sam_vnd_billion": 5400.0,
        "som_target_vnd_billion": 240.0,
        "cagr_pct": 19.8,
        "primary_competitors": "SAP B1/S4HANA, Oracle NetSuite, Base.vn, MISA AMIS",
        "competitor_weakness_matrix": (
            "1. SAP/Oracle có chi phí bản quyền và triển khai quá cao (12–18 tháng), khó tùy biến nhanh theo luật thuế Việt Nam.\n"
            "2. Các phần mềm rời rạc trong nước (SaaS đơn lẻ) gây phân mảnh dữ liệu giữa CRM, Dự án, Kho và Kế toán.\n"
            "3. Thiếu cơ chế tự động đối soát bảng lương BHXH Quận 7 (TZ0857G) và xuất file VCB DigiBiz 11 cột giữ số 0 ở đầu."
        ),
        "innoria_moat_proposition": (
            "• Kiến trúc Insilos Enterprise ERP (Odoo 20 Clean-Core) hợp nhất Sales-to-Cash, Project Timesheet, Kho & Kế toán.\n"
            "• Tích hợp gốc Hóa đơn Điện tử Nghị định 70/2025/NĐ-CP (ký hiệu 1C26TAA) và thuế GTGT 8%/10%/0%.\n"
            "• Tự động hóa toàn diện Bảng lương VN 2026 (BHXH 8%, BHYT 1.5%, BHTN 1%, Thuế TNCN 5 bậc) & Xuất VCB DigiBiz."
        ),
        "win_rate_benchmark_pct": 48.0,
        "recommended_pricing_anchor_vnd": 250000000.0,
        "geo_keywords": (
            "trien khai erp odoo 20 vietnam, phan mem erp tich hop hoa don dien tu nghi dinh 70, "
            "clean core enterprise erp vietnam, he thong quan tri doanh nghiep insilos innoria"
        ),
        "battlecard_markdown": (
            "## Battlecard MKT-RES-03: Insilos Clean-Core ERP vs. Legacy ERP & Point SaaS\n"
            "- **Điểm khác biệt số 1 (Time-to-Value)**: Triển khai hoàn chỉnh trong 6–12 tuần theo chuẩn SAP Activate (`PRJ-TPL-01`).\n"
            "- **Điểm khác biệt số 2 (VN Statutory Native)**: Tuân thủ 100% Thông tư 99/2025/TT-BTC, Nghị định 70/2025 và BHXH TZ0857G."
        ),
        "claim_idx": 2,
    },
    {
        "code": "MKT-RES-04",
        "name": "GRC, ISO/IEC 27001 & 27701, PDPD (NĐ 13/2023) & Chemical Safety",
        "service_pillar": "grc",
        "target_icp_segment": "regulated_grc_hse",
        "tam_vnd_billion": 6800.0,
        "sam_vnd_billion": 1850.0,
        "som_target_vnd_billion": 95.0,
        "cagr_pct": 28.5,
        "primary_competitors": "Big4 Advisory, OneTrust, Vanta, Tư vấn ISO Thủ công",
        "competitor_weakness_matrix": (
            "1. Các đơn vị tư vấn truyền thống chỉ cung cấp văn bản Word/Excel tĩnh, không có hệ thống phần mềm kiểm soát kỹ thuật.\n"
            "2. Các nền tảng ngoại (OneTrust/Vanta) chưa bản địa hóa hồ sơ Đánh giá Tác động Xử lý Dữ liệu Cá nhân (DPIA) theo Nghị định 13/2023/NĐ-CP.\n"
            "3. Thiếu phân hệ quản lý an toàn hóa chất công nghiệp (CAS, UN, GHS Pictograms, SDS) gắn trực tiếp với tồn kho."
        ),
        "innoria_moat_proposition": (
            "• Thực thi kỹ thuật (Technical Enforcement) ngay trong lõi ERP: Che dấu CCCD/SĐT/TK ngân hàng mặc định, mở khóa 30 giây có Audit Log.\n"
            "• Quy trình phê duyệt thay đổi hồ sơ pháp lý 2 bước (Maker -> Checker) chống tự phê duyệt (SoD).\n"
            "• Tích hợp sẵn Sổ đăng ký Hóa chất nguy hiểm, cảnh báo GHS và báo cáo tuân thủ định kỳ."
        ),
        "win_rate_benchmark_pct": 52.0,
        "recommended_pricing_anchor_vnd": 120000000.0,
        "geo_keywords": (
            "phan mem tuan thu nghi dinh 13 bao ve du lieu ca nhan, iso 27701 privacy management vietnam, "
            "he thong quan tri rui ro grc va an toan hoa chat ghs, innoria grc compliance"
        ),
        "battlecard_markdown": (
            "## Battlecard MKT-RES-04: Sovereign GRC & Privacy Hub vs. Paper-Only Consultants\n"
            "- **Điểm khác biệt số 1 (Live Technical Controls)**: Có sẵn cơ chế Partial Masking, 30s Reveal Timer & Immutable Audit Log.\n"
            "- **Điểm khác biệt số 2 (Dual-Control SoD)**: Mọi thay đổi dữ liệu trọng yếu đều qua quy trình Maker -> Checker có khóa dòng `FOR UPDATE NOWAIT`."
        ),
        "claim_idx": 3,
    },
    {
        "code": "MKT-RES-05",
        "name": "Sovereign AI Concierge, Grounded SOP-RAG & Intelligent Document Processing",
        "service_pillar": "ai",
        "target_icp_segment": "enterprise_ai_automation",
        "tam_vnd_billion": 9600.0,
        "sam_vnd_billion": 2600.0,
        "som_target_vnd_billion": 135.0,
        "cagr_pct": 34.0,
        "primary_competitors": "Microsoft Copilot Studio, FPT.AI, Kore.ai, Unverified LLM Wrappers",
        "competitor_weakness_matrix": (
            "1. Các chatbot truyền thống dựa trên kịch bản cứng nhắc hoặc dùng LLM thuần túy dễ sinh ảo giác (hallucination).\n"
            "2. Rủi ro lộ lọt tài liệu mật (lương, hợp đồng, thuế) do không có bộ lọc phân quyền RBAC ở tầng Vector/BM25.\n"
            "3. Không có mã băm kiểm chứng trích dẫn SHA-256 dẫn đến việc nhân viên áp dụng sai quy trình."
        ),
        "innoria_moat_proposition": (
            "• Kiến trúc 4-Layer Grounded SOP-RAG Defense (SOP-DGM-12): Chặn Prompt Injection -> Lọc RBAC trước khi truy xuất Hybrid RRF (k=60).\n"
            "• Cổng kiểm chứng Entailment >= 0.85 bắt buộc đính kèm trích dẫn `[Doc | Section | ID | SHA256_8]`.\n"
            "• Bộ lọc PII tự động che CCCD, SĐT, Tài khoản ngân hàng và khóa API trước khi trả kết quả."
        ),
        "win_rate_benchmark_pct": 49.0,
        "recommended_pricing_anchor_vnd": 95000000.0,
        "geo_keywords": (
            "tro ly ai doanh nghiep chong ao giac rag, grounded sop rag chatbot vietnam, "
            "intelligent document processing ocr erp vietnam, innoria ai concierge"
        ),
        "battlecard_markdown": (
            "## Battlecard MKT-RES-05: 4-Layer Grounded SOP-RAG vs. Generic AI Chatbots\n"
            "- **Điểm khác biệt số 1 (Zero Cross-Role Leakage)**: Tách biệt tuyệt đối kênh Public Website (`public_brand`) và Internal SOP Copilot.\n"
            "- **Điểm khác biệt số 2 (Cryptographic Citation)**: Mọi câu trả lời đều kèm mã băm SHA-256 đối chiếu về `knowledge.article`."
        ),
        "claim_idx": 4,
    },
    {
        "code": "MKT-RES-06",
        "name": "ZenCode Enterprise Autonomous Engineering & Global Export (0% VAT)",
        "service_pillar": "zencode",
        "target_icp_segment": "global_export_apac_us",
        "tam_vnd_billion": 16400.0,
        "sam_vnd_billion": 3900.0,
        "som_target_vnd_billion": 165.0,
        "cagr_pct": 29.2,
        "primary_competitors": "Devin Enterprise, Cursor Teams, Offshore DevOps Boutiques",
        "competitor_weakness_matrix": (
            "1. Các công cụ AI coding đơn lẻ không có quy trình kiểm toán kiến trúc đa kho mã nguồn (Multi-Repo Governance).\n"
            "2. Các đối tác nước ngoài thiếu pháp nhân xuất khẩu phần mềm chuẩn tại Việt Nam để tối ưu chi phí thuế hợp pháp.\n"
            "3. Thiếu trình biên dịch tri thức AST sang đồ thị SQLite FTS5 và sổ cái quyết định kiến trúc Bi-Temporal ADR."
        ),
        "innoria_moat_proposition": (
            "• Kết hợp đội ngũ Senior Solution Architects với dàn tác tử kỹ thuật tự hành ZenCode & Core Knowledge Compiler.\n"
            "• Áp dụng hợp pháp thuế suất GTGT 0% cho hợp đồng xuất khẩu phần mềm quốc tế (APAC, Nhật Bản, Úc, Mỹ, EU).\n"
            "• Kiểm soát chất lượng bằng 6 cổng kiểm thử tự động trước mỗi lần phát hành lên cụm Kubernetes Production."
        ),
        "win_rate_benchmark_pct": 45.0,
        "recommended_pricing_anchor_vnd": 150000000.0,
        "geo_keywords": (
            "xuat khau phan mem thue gtgt 0 phan tram, autonomous software engineering vietnam, "
            "zencode enterprise devsecops agent, offshore r&d center vietnam innoria"
        ),
        "battlecard_markdown": (
            "## Battlecard MKT-RES-06: ZenCode Autonomous Engineering & 0% Export VAT\n"
            "- **Điểm khác biệt số 1 (Tax & Commercial Efficiency)**: Hợp đồng xuất khẩu phần mềm hưởng thuế GTGT 0% kèm bộ chứng từ chuẩn.\n"
            "- **Điểm khác biệt số 2 (Bi-Temporal Knowledge Graph)**: Tự động biên dịch AST và lưu vết mọi quyết định kiến trúc (`ADR`)."
        ),
        "claim_idx": 5,
    },
]


CANONICAL_CAMPAIGNS = [
    {
        "code": "AUT-CMP-01",
        "name": "ABM 4-Touch: Mở rộng Đội ngũ Kỹ sư Chuyên trách (MTI & Global R&D Squad)",
        "radar_code": "MKT-RES-01",
        "channel_mix": "abm_executive_4touch",
        "target_mql_count": 30,
        "actual_mql_count": 34,
        "target_sql_count": 12,
        "actual_sql_count": 15,
        "pipeline_revenue_vnd": 975000000.0,
        "campaign_budget_vnd": 18000000.0,
        "nurture_touch_1_day1": (
            "Ngày 1 (Pain & Hidden Cost): Phân tích chi phí ẩn khi tuyển dụng nội bộ chậm trễ và rủi ro gián đoạn Sprint tại các trung tâm R&D."
        ),
        "nurture_touch_2_day4": (
            "Ngày 4 (Architecture & Governance): Giới thiệu mô hình Dedicated Squad chuẩn MTI của Innoria với Cổng Kỹ năng Bắt buộc SOP-DGM-10/11."
        ),
        "nurture_touch_3_day8": (
            "Ngày 8 (Verified Proof): Chia sẻ quy trình chốt Timesheet chữ ký số SHA-256 & Đối soát Hóa đơn Nháp 2 bước (SOP-DGM-08)."
        ),
        "nurture_touch_4_day14": (
            "Ngày 14 (Executive CTA): Mời sử dụng công cụ dự toán ESIH trên innoria.com và phỏng vấn trực tiếp Senior Engineers trong 48h."
        ),
    },
    {
        "code": "AUT-CMP-02",
        "name": "Turnkey Software & AI Product Launchpad (AIfin 360-Sales Blueprint)",
        "radar_code": "MKT-RES-02",
        "channel_mix": "interactive_concierge_3d",
        "target_mql_count": 25,
        "actual_mql_count": 28,
        "target_sql_count": 10,
        "actual_sql_count": 12,
        "pipeline_revenue_vnd": 1110000000.0,
        "campaign_budget_vnd": 20000000.0,
        "nurture_touch_1_day1": (
            "Ngày 1: Nhận diện rủi ro trễ hạn và phụ thuộc mã nguồn khi thuê gia công phần mềm thiếu chuẩn kiến trúc."
        ),
        "nurture_touch_2_day4": (
            "Ngày 4: Khung triển khai 4 giai đoạn SAP Activate kết hợp PDCA (`PRJ-TPL-02`) và cam kết bàn giao 100% IP."
        ),
        "nurture_touch_3_day8": (
            "Ngày 8: Minh chứng thực tế từ dự án hệ thống 360-Sales cho Công ty Cổ phần AIfin Company Global."
        ),
        "nurture_touch_4_day14": (
            "Ngày 14: Nhận bản kiến trúc sơ bộ (Solution Blueprint) và báo giá cố định theo mốc nghiệm thu."
        ),
    },
    {
        "code": "AUT-CMP-03",
        "name": "Clean-Core Enterprise ERP, Hóa đơn NĐ 70 (1C26TAA) & Lương VCB DigiBiz",
        "radar_code": "MKT-RES-03",
        "channel_mix": "geo_ai_search_inbound",
        "target_mql_count": 35,
        "actual_mql_count": 40,
        "target_sql_count": 14,
        "actual_sql_count": 18,
        "pipeline_revenue_vnd": 1500000000.0,
        "campaign_budget_vnd": 22000000.0,
        "nurture_touch_1_day1": (
            "Ngày 1: Cảnh báo rủi ro sai lệch dữ liệu giữa Kế toán, Nhân sự và Hóa đơn điện tử khi vận hành nhiều phần mềm rời rạc."
        ),
        "nurture_touch_2_day4": (
            "Ngày 4: Kiến trúc Clean-Core Odoo 20 tích hợp gốc HĐĐT Nghị định 70 (`1C26TAA`), BHXH Quận 7 (`TZ0857G`) và VCB DigiBiz."
        ),
        "nurture_touch_3_day8": (
            "Ngày 8: Demo trực quan luồng tự động từ Bảng chấm công dự án -> Hóa đơn nháp -> HĐĐT chính thức và Bảng lương 5 bậc thuế TNCN."
        ),
        "nurture_touch_4_day14": (
            "Ngày 14: Đặt lịch khảo sát Fit-to-Standard và nhận lộ trình chuyển đổi ERP trong 8 tuần."
        ),
    },
    {
        "code": "AUT-CMP-04",
        "name": "Tuân thủ ISO 27001/27701, Bảo vệ Dữ liệu NĐ 13/2023 & An toàn Hóa chất",
        "radar_code": "MKT-RES-04",
        "channel_mix": "abm_executive_4touch",
        "target_mql_count": 20,
        "actual_mql_count": 24,
        "target_sql_count": 9,
        "actual_sql_count": 11,
        "pipeline_revenue_vnd": 720000000.0,
        "campaign_budget_vnd": 15000000.0,
        "nurture_touch_1_day1": (
            "Ngày 1: Các lỗi vi phạm phổ biến về lộ lọt dữ liệu cá nhân (CCCD, tài khoản lương) theo Nghị định 13/2023/NĐ-CP."
        ),
        "nurture_touch_2_day4": (
            "Ngày 4: Cơ chế Partial Masking, mở khóa 30 giây có nhật ký bất biến và quy trình phê duyệt 2 bước Maker -> Checker."
        ),
        "nurture_touch_3_day8": (
            "Ngày 8: Tích hợp đồng bộ quản trị rủi ro GRC, hồ sơ DPIA và an toàn hóa chất GHS ngay trên một nền tảng."
        ),
        "nurture_touch_4_day14": (
            "Ngày 14: Đăng ký gói rà soát tuân thủ ISO/IEC 27701 & Nghị định 13 miễn phí cho doanh nghiệp."
        ),
    },
    {
        "code": "AUT-CMP-05",
        "name": "Sovereign AI Concierge, Grounded SOP-RAG & Logistics OCR/IDP",
        "radar_code": "MKT-RES-05",
        "channel_mix": "geo_ai_search_inbound",
        "target_mql_count": 30,
        "actual_mql_count": 36,
        "target_sql_count": 12,
        "actual_sql_count": 16,
        "pipeline_revenue_vnd": 950000000.0,
        "campaign_budget_vnd": 16000000.0,
        "nurture_touch_1_day1": (
            "Ngày 1: Vì sao 80% Chatbot AI nội bộ thất bại do ảo giác (hallucination) và không kiểm soát được quyền truy cập tài liệu mật?"
        ),
        "nurture_touch_2_day4": (
            "Ngày 4: Kiến trúc 4-Layer Grounded SOP-RAG (SOP-DGM-12) với lọc quyền RBAC trước truy xuất và ngưỡng Entailment >= 0.85."
        ),
        "nurture_touch_3_day8": (
            "Ngày 8: Trải nghiệm thực tế AI Concierge trên innoria.com và Trợ lý SOP-RAG nội bộ đính kèm mã băm SHA-256."
        ),
        "nurture_touch_4_day14": (
            "Ngày 14: Triển khai thử nghiệm (PoC) chỉ mục hóa 20 quy trình SOP của doanh nghiệp trong 5 ngày làm việc."
        ),
    },
    {
        "code": "AUT-CMP-06",
        "name": "Xuất khẩu Phần mềm Quốc tế 0% GTGT & ZenCode Autonomous DevSecOps",
        "radar_code": "MKT-RES-06",
        "channel_mix": "partner_referral_ecosystem",
        "target_mql_count": 22,
        "actual_mql_count": 26,
        "target_sql_count": 10,
        "actual_sql_count": 12,
        "pipeline_revenue_vnd": 1050000000.0,
        "campaign_budget_vnd": 18000000.0,
        "nurture_touch_1_day1": (
            "Ngày 1: Bài toán tối ưu chi phí R&D và tuân thủ thuế xuyên biên giới cho các tập đoàn công nghệ tại APAC, Nhật Bản, Úc và Mỹ."
        ),
        "nurture_touch_2_day4": (
            "Ngày 4: Khung hợp đồng xuất khẩu phần mềm hưởng thuế suất GTGT 0% (`TPL-SW-03`) và quản trị chất lượng tự hành ZenCode."
        ),
        "nurture_touch_3_day8": (
            "Ngày 8: Báo cáo kiểm toán chất lượng mã nguồn tự động, biên dịch AST và sổ cái quyết định kiến trúc Bi-Temporal ADR."
        ),
        "nurture_touch_4_day14": (
            "Ngày 14: Kết nối trực tiếp với CTO & Ban Giám đốc Innoria để thiết lập trung tâm R&D chuyên trách."
        ),
    },
]


def _build_sop_13_inner_html():
    return """
    <div class="sec">
        <div class="sec-title">1. Mục Đích &amp; Nguyên Tắc Chuỗi Cung Ứng Marketing Kiểm Chứng 100% Claim Atom</div>
        <p>Quy trình <strong>SOP-DGM-13</strong> thiết lập hệ thống <strong>Tự động hóa Marketing 24/7 (`Autonomous Marketing Automation`), Nghiên cứu Thị trường B2B Liên tục (`Market Research Radar`), Tình báo Đối thủ (`Competitive Battlecards`) và Tối ưu hóa Công cụ Tìm kiếm AI (`GEO`)</strong> của <strong>Công ty Cổ phần Digimate (Innoria — MST: 0317958465)</strong>:</p>
        <ul>
            <li><strong>Định lượng Thị trường Liên tục (`dgm.market.research.radar` — `MKT-RES-01..06`):</strong> Đo lường quy mô TAM (`87,500 Tỷ VNĐ`), SAM (`21,050 Tỷ VNĐ`), SOM mục tiêu Innoria (`960 Tỷ VNĐ`), tốc độ tăng trưởng CAGR và ma trận điểm yếu của đối thủ cạnh tranh trên 6 trụ cột dịch vụ.</li>
            <li><strong>Chống Ảo giác Nội dung Quảng cáo (`100% Claim Atom Grounding`):</strong> Mọi học liệu (`al2c.marketing.kit`), Battlecard và kịch bản email bắt buộc lắp ghép từ các <code>al2c.claim.atom</code> đã được kiểm chứng (<code>verification_state = 'verified'</code>) kèm chữ ký băm <code>SHA-256</code>.</li>
            <li><strong>Tích hợp Kho Tri thức SOP-RAG (`al2c.rag.chunk`):</strong> Toàn bộ 6 Battlecard và hồ sơ nghiên cứu thị trường được tự động nạp vào chỉ mục RAG (<code>dgm_rbac_profile = 'crm_sales'</code>) để đội ngũ Kinh doanh &amp; Ban Giám đốc tra cứu tức thì.</li>
        </ul>
    </div>
    <div class="sec">
        <div class="sec-title">2. Ma Trận 6 Hồ Sơ Nghiên Cứu Thị Trường &amp; Battlecard (`MKT-RES-01` .. `MKT-RES-06`)</div>
        <table>
            <thead>
                <tr>
                    <th>Mã Radar</th>
                    <th>Trụ cột Dịch vụ</th>
                    <th>TAM / SAM / SOM (Tỷ VNĐ)</th>
                    <th>CAGR</th>
                    <th>Đối thủ Chính</th>
                    <th>Win-Rate Mục tiêu</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><strong>MKT-RES-01</strong></td><td>Dedicated Agile Squad &amp; Staff Augmentation</td><td>18,500 / 4,200 / 185</td><td>21.5%</td><td>FPT Software, NashTech, KMS, Savvycom</td><td>46.0%</td></tr>
                <tr><td><strong>MKT-RES-02</strong></td><td>Turnkey Custom Software &amp; AI Product</td><td>14,200 / 3,100 / 140</td><td>24.0%</td><td>CMC Global, VMO, Rikkeisoft, Studios</td><td>44.0%</td></tr>
                <tr><td><strong>MKT-RES-03</strong></td><td>Clean-Core Enterprise ERP, NĐ 70 &amp; Payroll</td><td>22,000 / 5,400 / 240</td><td>19.8%</td><td>SAP B1/S4, NetSuite, Base.vn, MISA</td><td>48.0%</td></tr>
                <tr><td><strong>MKT-RES-04</strong></td><td>GRC, ISO 27001/27701, PDPD NĐ 13 &amp; HSE</td><td>6,800 / 1,850 / 95</td><td>28.5%</td><td>Big4 Advisory, OneTrust, Vanta</td><td>52.0%</td></tr>
                <tr><td><strong>MKT-RES-05</strong></td><td>Sovereign AI Concierge, SOP-RAG &amp; IDP</td><td>9,600 / 2,600 / 135</td><td>34.0%</td><td>Copilot Studio, FPT.AI, Kore.ai</td><td>49.0%</td></tr>
                <tr><td><strong>MKT-RES-06</strong></td><td>ZenCode Autonomous Engineering &amp; 0% Export</td><td>16,400 / 3,900 / 165</td><td>29.2%</td><td>Devin Enterprise, Cursor Teams</td><td>45.0%</td></tr>
            </tbody>
        </table>
    </div>
    <div class="sec">
        <div class="sec-title">3. Chu Trình Vận Hành Chiến Dịch Tự Hành 4-Touch ABM (`AUT-CMP-01` .. `AUT-CMP-06`)</div>
        <p>Daemon định kỳ <code>ir_cron_dgm_autonomous_marketing_research</code> chạy tự động mỗi <strong>6 giờ</strong> (tôn trọng công tắc an toàn kép <code>al2c.autonomy_enabled</code> &amp; <code>dgm.autonomy_enabled</code>), thực hiện đồng bộ nghiên cứu thị trường, phân luồng cơ hội B2B (<code>crm.lead</code>) vào 6 chiến dịch tự hành và cập nhật chỉ số chuyển đổi <code>MQL -&gt; SQL</code>, doanh thu Pipeline và hệ số hoàn vốn <code>ROI (x)</code>.</p>
    </div>
    """


def _build_tpl_mkt_01_inner_html():
    return """
    <div class="sec">
        <div class="sec-title">1. Cấu Trúc Battlecard Thắng Thầu B2B &amp; Từ Khóa GEO (`TPL-MKT-01`)</div>
        <p>Biểu mẫu <strong>TPL-MKT-01</strong> chuẩn hóa hồ sơ Tình báo Cạnh tranh (Competitive Battlecard) và kịch bản nuôi dưỡng khách hàng doanh nghiệp <strong>4-Touch ABM</strong> cho đội ngũ Kinh doanh &amp; Giải pháp của <strong>Digimate JSC / Innoria</strong>:</p>
        <table>
            <thead>
                <tr>
                    <th>Điểm chạm (Touchpoint)</th>
                    <th>Thời점 Gửi</th>
                    <th>Mục tiêu Chuyển đổi</th>
                    <th>Tài liệu &amp; Công cụ Đính kèm</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><strong>Touch 1 — Pain &amp; Cost</strong></td><td>Ngày 1</td><td>Nhận diện chi phí ẩn &amp; rủi ro vận hành thủ công</td><td>Executive Solution Brief (`al2c.marketing.kit`)</td></tr>
                <tr><td><strong>Touch 2 — Clean-Core &amp; Legal</strong></td><td>Ngày 4</td><td>Chứng minh kiến trúc Clean-Core &amp; tuân thủ NĐ 70 / NĐ 13</td><td>Battlecard So sánh Đối thủ (`MKT-RES-01..06`)</td></tr>
                <tr><td><strong>Touch 3 — Verified Case Study</strong></td><td>Ngày 8</td><td>Minh chứng thực chiến từ hợp đồng MTI, Canva, AIfin</td><td>Hồ sơ Nghiệm thu &amp; SLA 140–180h (`SOP-DGM-08`)</td></tr>
                <tr><td><strong>Touch 4 — ESIH &amp; Architect Call</strong></td><td>Ngày 14</td><td>Chuyển đổi MQL thành SQL &amp; Tạo Báo giá trên CRM</td><td>Công cụ Dự toán ESIH (`innoria.com`)</td></tr>
            </tbody>
        </table>
    </div>
    """


def seed_database(dbname):
    print(f"\n=== Seeding SOP-DGM-13 Autonomous Marketing & Market Research Radar in `{dbname}` ===")
    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        reg.init_models(
            cr,
            [
                "al2c.claim.atom",
                "al2c.marketing.kit",
                "al2c.rag.chunk",
                "dgm.knowledge.sop.workflow",
                "dgm.market.research.radar",
                "dgm.marketing.automation.campaign",
            ],
            {"module": "insilos_al2c"},
        )
        for rel_path in (
            "security/ir.access.csv",
            "views/dgm_autonomous_marketing_research_views.xml",
            "data/ir_cron_data.xml",
        ):
            full_p = os.path.join(ROOT_DIR, "addons/insilos_al2c", rel_path)
            if os.path.exists(full_p):
                convert_file(env, "insilos_al2c", rel_path, {}, mode="init", noupdate=False)
        if hasattr(reg, "_ensure_sovereign_bridges"):
            reg._ensure_sovereign_bridges(cr)

        IrConfig = env["ir.config_parameter"].sudo()
        IrConfig.set_param("al2c.autonomy_enabled", "True")
        IrConfig.set_param("dgm.autonomy_enabled", "True")

        sop_13_html = wrap_dgm_branded_html_document(
            body_html=_build_sop_13_inner_html(),
            doc_code="SOP-DGM-13",
            doc_title="QUY TRÌNH TỰ ĐỘNG HÓA MARKETING 24/7, NGHIÊN CỨU THỊ TRƯỜNG B2B, BATTLECARD ĐỐI THỦ & GEO",
            doc_subtitle="AUTONOMOUS MARKETING AUTOMATION, B2B MARKET RESEARCH RADAR, BATTLECARDS & GEO SUPPLY CHAIN",
            effective_date="17/10/2026",
        )
        tpl_mkt_01_html = wrap_dgm_branded_html_document(
            body_html=_build_tpl_mkt_01_inner_html(),
            doc_code="TPL-MKT-01",
            doc_title="BÁO CÁO NGHIÊN CỨU THỊ TRƯỜNG TAM/SAM/SOM, BATTLECARD ĐỐI THỦ & KỊCH BẢN 4-TOUCH ABM",
            doc_subtitle="B2B MARKET SIZING REPORT, COMPETITIVE BATTLECARD MATRIX & 4-TOUCH ABM PLAYBOOK",
            effective_date="17/10/2026",
        )

        # 1. Seed SOP-DGM-13 Knowledge Article
        Article = env["knowledge.article"].sudo()
        root_art = Article.search([("name", "ilike", "DGM · Quy Trình Vận Hành Chuẩn%"), ("active", "=", True)], limit=1)
        if not root_art:
            root_art = Article.search([("parent_id", "=", False), ("active", "=", True)], limit=1)

        sop_13_title = (
            "SOP-DGM-13: Quy Trình Tự Động Hóa Marketing, Nghiên Cứu Thị Trường B2B Liên Tục, "
            "Battlecard Đối Thủ & Tối Ưu Công Cụ AI (GEO)"
        )
        sop_13_art = Article.search([("name", "ilike", "SOP-DGM-13%"), ("active", "=", True)], limit=1)
        art_vals = {
            "name": sop_13_title,
            "parent_id": root_art.id if root_art else False,
            "body": sop_13_html,
            "internal_permission": "write",
            "is_article_item": False,
            "active": True,
        }
        if sop_13_art:
            sop_13_art.write(art_vals)
        else:
            sop_13_art = Article.create(art_vals)
        env.flush_all()
        cr.execute(
            "UPDATE knowledge_article SET body = %s, active = TRUE WHERE id = %s",
            (sop_13_html, sop_13_art.id),
        )
        sop_13_art.invalidate_recordset(["body", "active"])

        # 2. Seed KMS-SOP-13 in `dgm.knowledge.sop.workflow` & index into `al2c.rag.chunk`
        Workflow = env["dgm.knowledge.sop.workflow"].sudo()
        ceo_emp = env["hr.employee"].sudo().search([("registration_number", "=", "DGM-001")], limit=1)
        cto_emp = env["hr.employee"].sudo().search([("registration_number", "=", "DGM-002")], limit=1)
        sales_emp = env["hr.employee"].sudo().search([("registration_number", "=", "DGM-003")], limit=1) or ceo_emp

        wf_13 = Workflow.search([("code", "=", "KMS-SOP-13")], limit=1)
        wf_vals = {
            "code": "KMS-SOP-13",
            "sop_code": "SOP-DGM-13",
            "name": sop_13_title,
            "category": "sop_governance",
            "knowledge_article_id": sop_13_art.id,
            "rbac_profile": "company_common",
            "confidentiality_level": "internal",
            "visibility_channel": "internal_only",
            "reviewer_employee_id": (cto_emp or ceo_emp).id if (cto_emp or ceo_emp) else False,
            "approver_employee_id": ceo_emp.id if ceo_emp else False,
            "summary_markdown": (
                "Quy trình SOP-DGM-13 vận hành hệ thống Tự động hóa Marketing 24/7 (`dgm.marketing.automation.campaign` — AUT-CMP-01..06), "
                "Nghiên cứu Thị trường B2B liên tục (`dgm.market.research.radar` — MKT-RES-01..06 với tổng TAM 87,500 Tỷ VNĐ, "
                "SAM 21,050 Tỷ VNĐ, SOM mục tiêu 960 Tỷ VNĐ), Battlecard so sánh đối thủ, tối ưu từ khóa GEO cho công cụ tìm kiếm AI "
                "và kiểm chứng 100% Claim Atom (`al2c.claim.atom`) trước khi xuất bản học liệu `al2c.marketing.kit`."
            ),
            "min_entailment_threshold": 0.85,
            "active": True,
        }
        if wf_13:
            wf_13.write(wf_vals)
        else:
            wf_13 = Workflow.create(wf_vals)
        wf_13.action_submit_tech_review()
        wf_13.action_approve_compliance()
        wf_13.action_index_to_sop_rag()

        # 3. Seed 6 Verified Canonical Claim Atoms for SOP-DGM-13
        ClaimAtom = env["al2c.claim.atom"].sudo()
        ProductTemplate = env["product.template"].sudo()
        skus = ProductTemplate.search([("sale_ok", "=", True)], order="id asc", limit=6)
        default_sku = skus[:1]

        seeded_atoms = []
        for idx, c_def in enumerate(CANONICAL_CLAIMS):
            sku = skus[idx] if idx < len(skus) else default_sku
            norm_hash = ClaimAtom._compute_claim_hash if hasattr(ClaimAtom, "_compute_claim_hash") else None
            existing_atom = ClaimAtom.search([("name", "=", c_def["name"])], limit=1)
            if not existing_atom:
                import hashlib as _hl
                target_hash = _hl.sha256(c_def["claim_text"].strip().lower().encode("utf-8")).hexdigest()
                existing_atom = ClaimAtom.search([("claim_hash", "=", target_hash)], limit=1)
            atom_vals = {
                "name": c_def["name"],
                "claim_type": c_def["claim_type"],
                "claim_text": c_def["claim_text"],
                "source_article_id": sop_13_art.id,
                "sku_id": sku.id if sku else False,
                "verification_state": "verified",
                "verified_by_uid": SUPERUSER_ID,
                "verified_date": odoo.fields.Datetime.now(),
                "active": True,
            }
            if existing_atom:
                existing_atom.write(atom_vals)
                atom_rec = existing_atom
            else:
                atom_rec = ClaimAtom.create(atom_vals)
            seeded_atoms.append(atom_rec)

        # 4. Seed 6 Market Research Radars (`MKT-RES-01` .. `MKT-RES-06`)
        Radar = env["dgm.market.research.radar"].sudo()
        radar_by_code = {}
        for r_def in CANONICAL_RADARS:
            r_vals = dict(r_def)
            claim_idx = r_vals.pop("claim_idx", 0)
            linked_atom = seeded_atoms[claim_idx] if claim_idx < len(seeded_atoms) else seeded_atoms[0]
            r_vals["claim_atom_ids"] = [(6, 0, [linked_atom.id])]
            r_vals["active"] = True

            rad = Radar.search([("code", "=", r_def["code"])], limit=1)
            if rad:
                rad.write(r_vals)
            else:
                rad = Radar.create(r_vals)
            rad.action_synthesize_and_verify_radar()
            radar_by_code[r_def["code"]] = rad

        # 5. Seed 6 Autonomous Marketing Campaigns (`AUT-CMP-01` .. `AUT-CMP-06`) & Execute Cron
        Campaign = env["dgm.marketing.automation.campaign"].sudo()
        for c_def in CANONICAL_CAMPAIGNS:
            c_vals = dict(c_def)
            r_code = c_vals.pop("radar_code")
            rad = radar_by_code[r_code]
            c_vals["research_radar_id"] = rad.id
            c_vals["owner_employee_id"] = (sales_emp or ceo_emp).id if (sales_emp or ceo_emp) else False
            c_vals["autonomy_mode"] = "autonomous_on"
            c_vals["active"] = True

            camp = Campaign.search([("code", "=", c_def["code"])], limit=1)
            if camp:
                camp.write(c_vals)
            else:
                camp = Campaign.create(c_vals)
            camp.action_activate_autonomous_campaign()

        scan_summary = Campaign.cron_dgm_autonomous_marketing_and_research()

        # 6. Seed 2 Branded HTML Documents (`SOP-DGM-13` & `TPL-MKT-01`) in `documents.document`
        Document = env["documents.document"].sudo()
        Attachment = env["ir.attachment"].sudo()

        gov_folder = Document.search(
            [("type", "=", "folder"), ("active", "=", True), ("name", "ilike", "%Quản trị Doanh nghiệp%")],
            limit=1,
        )
        mkt_folder = Document.search(
            [("type", "=", "folder"), ("active", "=", True), ("name", "ilike", "%Hợp đồng%")],
            limit=1,
        ) or gov_folder
        if not gov_folder:
            gov_folder = Document.search([("type", "=", "folder"), ("active", "=", True)], limit=1)
        if not mkt_folder:
            mkt_folder = gov_folder

        doc_specs = [
            (
                "SOP-DGM-13_Quy_Trinh_Tu_Dong_Hoa_Marketing_Nghien_Cuu_Thi_Truong_B2B_Va_GEO_Innoria.html",
                sop_13_html,
                gov_folder,
            ),
            (
                "TPL-MKT-01_Bao_Cao_Nghien_Cuu_Thi_Truong_Battlecard_Doi_Thu_Va_Kich_Ban_4_Touch_ABM.html",
                tpl_mkt_01_html,
                mkt_folder,
            ),
        ]
        for fname, html_str, folder in doc_specs:
            raw_bytes = html_str.encode("utf-8")
            b64_datas = base64.b64encode(raw_bytes)
            existing_doc = Document.search([("type", "!=", "folder"), ("name", "=", fname)], limit=1)
            if existing_doc:
                if existing_doc.attachment_id:
                    existing_doc.attachment_id.write({"datas": b64_datas, "mimetype": "text/html"})
                else:
                    att = Attachment.create(
                        {
                            "name": fname,
                            "datas": b64_datas,
                            "mimetype": "text/html",
                            "res_model": "documents.document",
                            "res_id": existing_doc.id,
                        }
                    )
                    existing_doc.attachment_id = att.id
                existing_doc.write(
                    {
                        "folder_id": folder.id if folder else False,
                        "owner_id": False,
                        "access_internal": "edit",
                        "active": True,
                    }
                )
                doc_rec = existing_doc
            else:
                att = Attachment.create(
                    {
                        "name": fname,
                        "datas": b64_datas,
                        "mimetype": "text/html",
                    }
                )
                doc_rec = Document.create(
                    {
                        "name": fname,
                        "attachment_id": att.id,
                        "folder_id": folder.id if folder else False,
                        "type": "binary",
                        "owner_id": False,
                        "access_internal": "edit",
                        "active": True,
                    }
                )
                att.write({"res_model": "documents.document", "res_id": doc_rec.id})
            wf_13.document_id = doc_rec.id

        if hasattr(Document, "apply_dgm_inno_rbac_matrix"):
            Document.apply_dgm_inno_rbac_matrix()

        # Enforce Zero Empty Folders Invariant
        all_folders = Document.search([("type", "=", "folder"), ("active", "=", True)])
        for fld in all_folders:
            child_count = Document.search_count([("folder_id", "=", fld.id), ("active", "=", True)])
            if child_count == 0:
                fld.active = False

        # Purge stale web.assets_% and warm web.assets_web.min.js & .min.css
        env["ir.attachment"].sudo().search([("name", "like", "web.assets_%")]).unlink()
        try:
            bundle = env["ir.qweb"].sudo()._get_asset_bundle("web.assets_web", css=True, js=True)
            bundle.js()
            bundle.css()
        except Exception as exc:
            print(f"  [!] Warning warming web.assets_web: {exc}")

        cr.commit()
        print(
            f"[✓] `{dbname}` SOP-DGM-13 seeded: 6 Radars (`MKT-RES-01..06`), 6 Autonomous Campaigns (`AUT-CMP-01..06`), "
            f"Scan={scan_summary}"
        )


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev", "innoria_prod"]
    for db in targets:
        seed_database(db)
    print("\n=== ALL SOP-DGM-13 AUTONOMOUS MARKETING & MARKET RESEARCH SEEDING COMPLETED (EXIT 0) ===")


if __name__ == "__main__":
    main()
