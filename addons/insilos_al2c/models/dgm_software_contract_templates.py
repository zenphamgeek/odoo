# -*- coding: utf-8 -*-
"""
SOP-DGM-09 — Digimate Enterprise Software Contract Template Engine & Tax Incentive Compliance Suite
====================================================================================================
Provides two best-practice, multi-clause software contract suites designed strictly to qualify for
Vietnam Software Production & Software Services Tax Incentives (Ưu đãi thuế TNDN & Đối tượng không chịu
thuế GTGT theo Thông tư 13/2020/TT-BTTTT, Nghị định 71/2007/NĐ-CP, Khoản 21 Điều 4 Thông tư 219/2013/TT-BTC,
và Nghị định 70/2025/NĐ-CP):

1. Group A — Nhóm MTI & AIfin (`mti_codev`):
   "Để nhân sự tham gia cùng phát triển dự án phần mềm cho đối tác"
   (Co-Development & Dedicated Software Engineering Participation across the 7 Software Production
   Stages of Circular 13/2020/TT-BTTTT — strictly structured as Software Development Co-operation &
   Stage Processing rather than raw labor sub-leasing).
   - `TPL-SW-MTI-01`: Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm (12 Điều)
   - `TPL-SW-MTI-02`: Phụ lục Đặt hàng (SOW) Cử Nhân sự Kỹ thuật Tham gia Cùng Phát triển Dự án Phần mềm
   - `TPL-SW-MTI-03`: Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm & Hồ sơ Minh chứng Thông tư 13/2020/TT-BTTTT
   - `TPL-SW-MTI-04`: Thỏa thuận Chuyển giao Quyền Sở hữu Trí tuệ Mã nguồn & Bảo mật Dự án Phần mềm (IP & NDA)

2. Group B — Nhóm KTT Khang Trường Thịnh (`ktt_turnkey`):
   "Hợp đồng làm dịch vụ phần mềm trọn gói (Turnkey Software Development & Full-Package Implementation)"
   modeled on KTT (Khang Trường Thịnh) & Digimate 360-Sales / Enterprise ERP Turnkey Architecture.
   - `TPL-SW-KTT-01`: Hợp đồng Thiết kế, Xây dựng & Triển khai Phần mềm Trọn gói (14 Điều)
   - `TPL-SW-KTT-02`: Phụ lục 01 — Đặc tả Kỹ thuật (SRS), Ma trận Chức năng & Tiêu chí Nghiệm thu UAT Trọn gói
   - `TPL-SW-KTT-03`: Biên bản Nghiệm thu Bàn giao Hệ thống Phần mềm Trọn gói & Hồ sơ 7 Công đoạn TT 13/2020/TT-BTTTT
   - `TPL-SW-KTT-04`: Hợp đồng Dịch vụ Bảo trì, Nâng cấp & Hỗ trợ Kỹ thuật Phần mềm Hàng năm (AMC & SLA)

Every generated HTML contract is wrapped via `wrap_dgm_branded_html_document(..., include_header=True)`
so it carries both the official Google Drive Digimate Logo Header and Brand Footer.
"""
import base64
import html
import logging
import os
import re

try:
    from odoo import SUPERUSER_ID, api, fields, models, _
    from odoo.exceptions import UserError
except Exception:
    SUPERUSER_ID = 1
    UserError = RuntimeError
    _ = lambda s, **kw: s % kw if kw else s

    class _DummyApi:
        @staticmethod
        def model(fn):
            return fn

        @staticmethod
        def depends(*args):
            def _dec(fn):
                return fn
            return _dec

    class _DummyFields:
        Selection = Many2many = Integer = lambda *a, **kw: None

    class _DummyModels:
        Model = object

    api = _DummyApi()
    fields = _DummyFields()
    models = _DummyModels()

try:
    from .dgm_brand_footer import (
        get_digimate_logo_data_uri,
        render_dgm_brand_footer_html,
        render_dgm_brand_header_html,
        wrap_dgm_branded_html_document,
    )
except ImportError:
    import importlib.util as _ilu
    _bf_spec = _ilu.spec_from_file_location(
        "odoo.addons.insilos_al2c.models.dgm_brand_footer",
        os.path.join(os.path.dirname(__file__), "dgm_brand_footer.py"),
    )
    _bf_mod = _ilu.module_from_spec(_bf_spec)
    _bf_spec.loader.exec_module(_bf_mod)
    get_digimate_logo_data_uri = _bf_mod.get_digimate_logo_data_uri
    render_dgm_brand_footer_html = _bf_mod.render_dgm_brand_footer_html
    render_dgm_brand_header_html = _bf_mod.render_dgm_brand_header_html
    wrap_dgm_branded_html_document = _bf_mod.wrap_dgm_branded_html_document

_logger = logging.getLogger(__name__)


# =============================================================================
# Canonical Partner & Project Profiles (MTI, AIfin, KTT Khang Trường Thịnh)
# =============================================================================
CANONICAL_SW_PARTNER_PROFILES = {
    'MTI': {
        'profile_key': 'MTI',
        'contract_model': 'mti_codev',
        'partner_code': 'PTN-DGM-2026-0001',
        'partner_name': 'CÔNG TY TNHH MTI TECHNOLOGY',
        'partner_name_en': 'MTI TECHNOLOGY CO., LTD',
        'vat': '0314015511',
        'address': 'Tầng 14, Khối tháp E, Tòa nhà Cộng Hòa Garden, 20 Đường Cộng Hòa, Phường 12, Quận Tân Bình, TP. Hồ Chí Minh, Việt Nam',
        'representative': 'Bà Nguyễn Thị Kim Thanh',
        'rep_title': 'Phó Tổng Giám đốc (Deputy General Director)',
        'email': 'accounting@mti-tech.vn',
        'contract_no': 'DIGIMATE2401-001 / DGM-MTI-CODEV-2026',
        'appendix_no': 'PL-202610-MTI-01 (Đính kèm HĐ số DIGIMATE2401-001)',
        'project_name': 'Dự án Phát triển Phần mềm LIFE & Hệ sinh thái Y tế / Bảo hiểm Số Nhật Bản (MTI Digital Platform)',
        'work_location': 'Văn phòng MTI Technology (Tầng 14, Cộng Hòa Garden, 20 Cộng Hòa, Q. Tân Bình, TP.HCM) kết hợp Hybrid tại Trung tâm R&D Digimate',
        'payment_term_days': 40,
        'standard_window_hours': '140 – 180 giờ/tháng (Chuẩn 160 giờ/tháng)',
        'monthly_total_vnd': 250_000_000,
        'vat_policy': 'Đối tượng không chịu thuế GTGT (KCT) đối với công đoạn sản xuất/dịch vụ phần mềm theo Khoản 21 Điều 4 TT 219/2013/TT-BTC & TT 13/2020/TT-BTTTT (hoặc 8% GTGT đối với cấu phần dịch vụ kỹ thuật đi kèm theo thỏa thuận đối soát)',
        'engineers': [
            {
                'emp_code': 'DGM-004',
                'name': 'Bùi Hữu Tài',
                'role': 'Lead Software Engineer / Delivery Lead',
                'tt13_stages': 'Công đoạn 1 (Xác định yêu cầu), Công đoạn 2 (Phân tích & Thiết kế kiến trúc), Công đoạn 3 (Lập trình module lõi)',
                'hourly_rate_vnd': 390_625,
                'monthly_fee_vnd': 62_500_000,
                'std_hours': 160,
            },
            {
                'emp_code': 'DGM-005',
                'name': 'Huỳnh Trần Quang Khánh',
                'role': 'Senior Full-Stack Software Engineer',
                'tt13_stages': 'Công đoạn 2 (Thiết kế chi tiết API/DB), Công đoạn 3 (Lập trình Backend/Frontend), Công đoạn 4 (Unit Test & Code Review)',
                'hourly_rate_vnd': 390_625,
                'monthly_fee_vnd': 62_500_000,
                'std_hours': 160,
            },
            {
                'emp_code': 'DGM-006',
                'name': 'Ngô Thanh Lộc',
                'role': 'Senior Software Engineer (Backend & Microservices)',
                'tt13_stages': 'Công đoạn 3 (Viết mã lệnh & Tích hợp hệ thống), Công đoạn 4 (Kiểm thử tích hợp SIT & Hiệu chỉnh hiệu năng)',
                'hourly_rate_vnd': 390_625,
                'monthly_fee_vnd': 62_500_000,
                'std_hours': 160,
            },
            {
                'emp_code': 'DGM-007',
                'name': 'Lê Cao Bảo Phúc',
                'role': 'Software Engineer (Frontend, Mobile & Automated QA)',
                'tt13_stages': 'Công đoạn 3 (Lập trình UI/UX), Công đoạn 4 (Kiểm thử UAT), Công đoạn 5 & 6 (Đóng gói & Hướng dẫn chuyển giao)',
                'hourly_rate_vnd': 390_625,
                'monthly_fee_vnd': 62_500_000,
                'std_hours': 160,
            },
        ],
    },
    'AIFIN': {
        'profile_key': 'AIFIN',
        'contract_model': 'both',
        'partner_code': 'PTN-DGM-2026-0007',
        'partner_group': 'strategic_b2b',
        'partner_name': 'CÔNG TY CỔ PHẦN AIFIN COMPANY GLOBAL',
        'partner_name_en': 'AIFIN COMPANY GLOBAL JOINT STOCK COMPANY',
        'vat': '0319631994',
        'address': '51-53 Võ Văn Tần, Phường Xuân Hòa, Thành Phố Hồ Chí Minh, Việt Nam',
        'representative': 'Ông Nguyễn Khắc Huy',
        'rep_title': 'Giám đốc (Director)',
        'email': 'huy.nguyen@aifin.com.vn',
        'contract_no': 'DIGIMATE-AIFIN-VN_2610-001 / AIFIN-DIGIMATE/360-SALES/2026',
        'appendix_no': 'PL-2610-001 (Nhân sự Kỹ sư Trần Văn Huỳnh Phố — DGM-009)',
        'project_name': 'Dự án Phát triển Phần mềm Nền tảng Tài chính Số AIFin & Hệ thống AI/ERP 360-Sales',
        'work_location': 'Trụ sở AIFin Company Global (51-53 Võ Văn Tần, Phường Xuân Hòa, TP.HCM) & Trung tâm R&D Digimate',
        'payment_term_days': 30,
        'standard_window_hours': '140 – 180 giờ/tháng (Chuẩn 160 giờ/tháng)',
        'monthly_total_vnd': 56_000_000,
        'turnkey_total_vnd': 200_000_000,
        'vat_policy': 'Phát triển phần mềm thuộc đối tượng không chịu thuế GTGT (KCT) theo Khoản 21 Điều 4 TT 219/2013/TT-BTC & quy trình 7 công đoạn TT 13/2020/TT-BTTTT',
        'engineers': [
            {
                'emp_code': 'DGM-009',
                'name': 'Trần Văn Huỳnh Phố',
                'role': 'Senior Software Engineer (Full-Stack & AI/ERP 360-Sales)',
                'tt13_stages': 'Công đoạn 1 & 2 (Đặc tả & Thiết kế kiến trúc 1,000 CCU), Công đoạn 3 (Lập trình 360-Sales), Công đoạn 4 (Stress Test & Hiệu chỉnh)',
                'hourly_rate_vnd': 350_000,
                'monthly_fee_vnd': 56_000_000,
                'std_hours': 160,
            },
        ],
    },
    'KTT': {
        'profile_key': 'KTT',
        'contract_model': 'ktt_turnkey',
        'partner_code': 'PTN-DGM-2026-0008',
        'partner_group': 'strategic_b2b',
        'partner_name': 'CÔNG TY TNHH KHANG TRƯỜNG THỊNH',
        'partner_name_en': 'KHANG TRUONG THINH CO., LTD (KTT)',
        'vat': '0316889922',
        'address': 'TP. Hồ Chí Minh, Việt Nam',
        'representative': 'Ban Giám đốc Công ty TNHH Khang Trường Thịnh',
        'rep_title': 'Giám đốc / Đại diện theo Pháp luật (Director)',
        'email': 'accounting@khangtruongthinh.vn',
        'contract_no': 'KTT-DIGIMATE/SW-TURNKEY/2026-001',
        'appendix_no': 'PL01-SRS-UAT/KTT-DIGIMATE/2026-001',
        'project_name': 'Hệ thống Phần mềm Quản trị Kinh doanh, Danh mục Sản phẩm, Kho vận, Đơn hàng & Hoa hồng Trọn gói (KTT Enterprise Suite)',
        'work_location': 'Triển khai trên hạ tầng Cloud/On-Premise của KTT Khang Trường Thịnh & Trung tâm Phát triển Phần mềm Digimate JSC',
        'payment_term_days': 5,
        'turnkey_total_vnd': 200_000_000,
        'delivery_days': 30,
        'vat_policy': 'Sản xuất và dịch vụ phần mềm trọn gói thuộc đối tượng Không chịu thuế GTGT (KCT) theo Khoản 21 Điều 4 Thông tư 219/2013/TT-BTC và đáp ứng quy trình sản xuất phần mềm theo Thông tư 13/2020/TT-BTTTT hưởng ưu đãi thuế TNDN',
    },
}


def _fmt_vnd(amount):
    try:
        return f"{int(round(float(amount or 0))):,}".replace(",", ".") + " VNĐ"
    except Exception:
        return "0 VNĐ"


def _resolve_partner_profile(partner_data=None):
    """Resolves a partner dictionary or `res.partner` record into a complete profile dictionary."""
    if not partner_data:
        return dict(CANONICAL_SW_PARTNER_PROFILES['MTI'])

    if isinstance(partner_data, str):
        key = partner_data.strip().upper()
        if key in CANONICAL_SW_PARTNER_PROFILES:
            return dict(CANONICAL_SW_PARTNER_PROFILES[key])

    if isinstance(partner_data, dict):
        name_upper = str(partner_data.get('partner_name') or partner_data.get('name') or '').upper()
        if 'MTI' in name_upper:
            base = dict(CANONICAL_SW_PARTNER_PROFILES['MTI'])
        elif 'AIFIN' in name_upper:
            base = dict(CANONICAL_SW_PARTNER_PROFILES['AIFIN'])
        elif 'KHANG TRƯỜNG THỊNH' in name_upper or 'KHANG TRUONG THINH' in name_upper or 'KTT' in name_upper:
            base = dict(CANONICAL_SW_PARTNER_PROFILES['KTT'])
        else:
            base = dict(CANONICAL_SW_PARTNER_PROFILES['MTI'])
        for k, v in partner_data.items():
            if v is not None and v != '':
                base[k] = v
        return base

    # Odoo record (`res.partner`)
    name_str = str(getattr(partner_data, 'name', '') or '')
    name_upper = name_str.upper()
    if 'MTI' in name_upper:
        base = dict(CANONICAL_SW_PARTNER_PROFILES['MTI'])
    elif 'AIFIN' in name_upper:
        base = dict(CANONICAL_SW_PARTNER_PROFILES['AIFIN'])
    elif 'KHANG TRƯỜNG THỊNH' in name_upper or 'KHANG TRUONG THINH' in name_upper or 'KTT' in name_upper:
        base = dict(CANONICAL_SW_PARTNER_PROFILES['KTT'])
    else:
        model_pref = getattr(partner_data, 'dgm_software_contract_model', '') or 'mti_codev'
        base = dict(
            CANONICAL_SW_PARTNER_PROFILES['KTT']
            if model_pref == 'ktt_turnkey'
            else CANONICAL_SW_PARTNER_PROFILES['MTI']
        )

    if name_str:
        base['partner_name'] = name_str
    if getattr(partner_data, 'vat', False):
        base['vat'] = partner_data.vat
    if getattr(partner_data, 'street', False):
        base['address'] = partner_data.street
    if getattr(partner_data, 'email', False):
        base['email'] = partner_data.email
    code = getattr(partner_data, 'dgm_partner_code', False) or getattr(partner_data, 'dgm_provisional_code', False)
    if code:
        base['partner_code'] = code
    return base


_CONTRACT_CSS = """
<style>
  .dgm-contract-wrap {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
    color: var(--insilos-text-primary, #1e293b);
    line-height: 1.62;
    font-size: 13.5px;
  }
  .dgm-national-motto {
    text-align: center;
    margin-bottom: 18px;
    padding-bottom: 12px;
    border-bottom: 1px dashed var(--insilos-border-subtle, #cbd5e1);
  }
  .dgm-national-motto .motto-vn {
    font-weight: 800;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }
  .dgm-national-motto .motto-sub {
    font-weight: 700;
    font-size: 13px;
    margin-top: 2px;
  }
  .dgm-contract-title {
    text-align: center;
    margin: 16px 0 20px 0;
  }
  .dgm-contract-title h1 {
    font-size: 19px;
    font-weight: 800;
    color: var(--insilos-text-primary, #0f172a);
    margin: 0 0 6px 0;
    text-transform: uppercase;
  }
  .dgm-contract-title .contract-sub {
    font-size: 12.5px;
    color: var(--insilos-text-secondary, #475569);
    font-weight: 600;
  }
  .dgm-tax-callout {
    background: var(--insilos-bg-subtle, #eff6ff);
    border-left: 4px solid #1d4ed8;
    border: 1px solid var(--insilos-border-subtle, #bfdbfe);
    border-left-width: 4px;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 14px 0;
    font-size: 12.8px;
  }
  .dgm-article-heading {
    font-size: 14.5px;
    font-weight: 700;
    color: var(--insilos-text-primary, #0f172a);
    margin: 20px 0 8px 0;
    padding-left: 10px;
    border-left: 4px solid #1e40af;
    text-transform: uppercase;
  }
  .dgm-clause-list {
    margin: 6px 0 12px 0;
    padding-left: 20px;
  }
  .dgm-clause-list li {
    margin-bottom: 6px;
  }
  .dgm-sig-grid {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin-top: 28px;
    page-break-inside: avoid;
  }
  .dgm-sig-box {
    width: 48%;
    border: 1px solid var(--insilos-border-subtle, #cbd5e1);
    background: var(--insilos-bg-surface, #f8fafc);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }
</style>
"""


# =============================================================================
# GROUP A — Nhóm MTI & AIfin: Bộ Mẫu Hợp Đồng "Để Nhân Sự Tham Gia Cùng Phát Triển
# Dự Án Phần Mềm Cho Đối Tác" (Chuẩn Ưu Đãi Thuế Sản Xuất & Dịch Vụ Phần Mềm)
# =============================================================================
def render_mti_codev_contract_suite(partner_data=None):
    """Renders the 4 Best-Practice Software Co-Development & Engineering Participation Contract
    Templates (`TPL-SW-MTI-01` .. `TPL-SW-MTI-04`) for MTI Technology / AIfin Group.
    """
    prof = _resolve_partner_profile(partner_data)
    p_name = html.escape(str(prof.get('partner_name') or 'CÔNG TY TNHH MTI TECHNOLOGY'))
    p_name_en = html.escape(str(prof.get('partner_name_en') or 'PARTNER COMPANY'))
    p_vat = html.escape(str(prof.get('vat') or '0314015511'))
    p_addr = html.escape(str(prof.get('address') or 'TP. Hồ Chí Minh, Việt Nam'))
    p_rep = html.escape(str(prof.get('representative') or 'Đại diện theo Pháp luật'))
    p_rep_title = html.escape(str(prof.get('rep_title') or 'Giám đốc'))
    p_email = html.escape(str(prof.get('email') or 'accounting@partner.vn'))
    p_code = html.escape(str(prof.get('partner_code') or 'PTN-DGM-2026-0001'))
    safe_code = re.sub(r'[^A-Za-z0-9_-]+', '_', str(prof.get('partner_code') or 'MTI'))
    contract_no = html.escape(str(prof.get('contract_no') or 'DIGIMATE2401-001'))
    appendix_no = html.escape(str(prof.get('appendix_no') or 'PL-202610-001'))
    project_name = html.escape(str(prof.get('project_name') or 'Dự án Phát triển Phần mềm Chuyên ngành'))
    work_loc = html.escape(str(prof.get('work_location') or 'Văn phòng Đối tác & Trung tâm R&D Digimate'))
    pay_days = int(prof.get('payment_term_days') or 40)
    monthly_total_str = _fmt_vnd(prof.get('monthly_total_vnd') or 250_000_000)

    engineers = prof.get('engineers') or CANONICAL_SW_PARTNER_PROFILES['MTI']['engineers']
    eng_rows_html = ""
    accept_rows_html = ""
    for idx, eng in enumerate(engineers, start=1):
        eng_rows_html += f"""
        <tr>
          <td>{idx}</td>
          <td><strong>{html.escape(eng['name'])}</strong><br/><code>{html.escape(eng['emp_code'])}</code></td>
          <td>{html.escape(eng['role'])}</td>
          <td>{html.escape(eng['tt13_stages'])}</td>
          <td>{eng['std_hours']} giờ (Khung 140–180h)</td>
          <td><strong>{_fmt_vnd(eng['hourly_rate_vnd'])}/giờ</strong></td>
          <td><strong>{_fmt_vnd(eng['monthly_fee_vnd'])}</strong></td>
        </tr>"""
        accept_rows_html += f"""
        <tr>
          <td>{idx}</td>
          <td><strong>{html.escape(eng['name'])}</strong> (<code>{html.escape(eng['emp_code'])}</code>)</td>
          <td>{html.escape(eng['tt13_stages'])}</td>
          <td>Commit mã nguồn Git, tài liệu thiết kế API/DB &amp; biên bản kiểm thử SIT/UAT đạt 100% yêu cầu sprint</td>
          <td>{eng['std_hours']} / {eng['std_hours']} giờ (100%)</td>
          <td><strong>{_fmt_vnd(eng['monthly_fee_vnd'])}</strong></td>
        </tr>"""

    # -------------------------------------------------------------------------
    # TPL-SW-MTI-01: Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm (12 Điều)
    # -------------------------------------------------------------------------
    body_01 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM / SOCIALIST REPUBLIC OF VIETNAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc / Independence – Freedom – Happiness</div>
  </div>

  <div class="dgm-contract-title">
    <h1>HỢP ĐỒNG KHUNG HỢP TÁC PHÁT TRIỂN DỰ ÁN PHẦN MỀM</h1>
    <div class="contract-sub">(MASTER SOFTWARE PROJECT CO-DEVELOPMENT &amp; ENGINEERING PARTICIPATION AGREEMENT)<br/>
    Mô hình: Cử Nhân sự Kỹ thuật Tham gia Cùng Phát triển Dự án Phần mềm Cho Đối tác — Chuẩn Ưu đãi Thuế Phần mềm<br/>
    Số Hợp đồng / Contract No.: <strong>{contract_no}</strong> • Mã Đối tác: <strong>{p_code}</strong></div>
  </div>

  <div class="dgm-tax-callout">
    <strong>⚖️ CĂN CỨ PHÁP LÝ &amp; ĐỊNH HƯỚNG ƯU ĐÃI THUẾ DỊCH VỤ / SẢN XUẤT PHẦN MỀM (LEGAL &amp; TAX INCENTIVE BASIS):</strong>
    <ul class="dgm-clause-list" style="margin-bottom:0;">
      <li>Căn cứ Bộ luật Dân sự số 91/2015/QH13 và Luật Thương mại số 36/2005/QH11;</li>
      <li>Căn cứ Luật Công nghệ Thông tin số 67/2006/QH11 và Nghị định số 71/2007/NĐ-CP quy định chi tiết và hướng dẫn thực hiện một số điều của Luật CNTT về công nghiệp công nghệ thông tin (Danh mục sản phẩm phần mềm và dịch vụ phần mềm);</li>
      <li>Căn cứ <strong>Thông tư số 13/2020/TT-BTTTT</strong> ngày 03/07/2020 của Bộ Thông tin và Truyền thông quy định việc xác định hoạt động sản xuất sản phẩm phần mềm đáp ứng quy trình 07 công đoạn;</li>
      <li>Căn cứ <strong>Khoản 21 Điều 4 Thông tư số 219/2013/TT-BTC</strong> của Bộ Tài chính và văn bản hợp nhất Luật Thuế TNDN về chính sách không chịu thuế GTGT (KCT) và ưu đãi thuế TNDN đối với hoạt động sản xuất sản phẩm phần mềm và cung cấp dịch vụ phần mềm;</li>
      <li>Căn cứ Nghị định số 70/2025/NĐ-CP quy định về hóa đơn, chứng từ điện tử và Nghị định số 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.</li>
    </ul>
  </div>

  <table>
    <tr>
      <th style="width:28%;">BÊN A (ĐỐI TÁC DỰ ÁN / CLIENT PARTNER)</th>
      <td>
        <strong>{p_name}</strong> ({p_name_en})<br/>
        Mã số thuế (Tax ID): <strong>{p_vat}</strong> • Mã Đối tác ERP: <strong>{p_code}</strong><br/>
        Địa chỉ trụ sở: {p_addr}<br/>
        Đại diện pháp luật: <strong>{p_rep}</strong> — Chức vụ: {p_rep_title} • Email đối soát: {p_email}
      </td>
    </tr>
    <tr>
      <th>BÊN B (ĐƠN VỊ PHÁT TRIỂN PHẦN MỀM / SOFTWARE CO-DEVELOPER)</th>
      <td>
        <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JOINT STOCK COMPANY — DIGIMATE JSC)</strong><br/>
        Mã số thuế (Tax ID): <strong>0317958465</strong> • Mã ĐV BHXH: <strong>TZ0857G</strong> • Ký hiệu HĐĐT: <strong>1C26TAA</strong><br/>
        Ngành nghề chính: Sản xuất phần mềm (Mã ngành 6201) &amp; Lập trình máy vi tính, dịch vụ phần mềm (Mã ngành 6202)<br/>
        Địa chỉ trụ sở: 344–346 Nguyễn Trọng Tuyển, Phường 2, Quận Tân Bình (Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ), TP. Hồ Chí Minh, Việt Nam<br/>
        Tài khoản thụ hưởng: <strong>1202703007</strong> — Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank — PGD Trung Sơn / CN Tân Định)<br/>
        Đại diện pháp luật: <strong>Ông Lê Xuân Hoàng</strong> — Chức vụ: Chủ tịch HĐQT kiêm Giám đốc
      </td>
    </tr>
  </table>

  <div class="dgm-article-heading">ĐIỀU 1. BẢN CHẤT HỢP TÁC PHÁT TRIỂN PHẦN MỀM &amp; NGUYÊN TẮC TUÂN THỦ THUẾ (NATURE OF SOFTWARE CO-DEVELOPMENT)</div>
  <ul class="dgm-clause-list">
    <li><strong>1.1. Bản chất dịch vụ phần mềm &amp; gia công công đoạn sản xuất phần mềm:</strong> Theo Hợp đồng này, Bên B (Digimate JSC) đảm nhận thực hiện một phần hoặc nhiều công đoạn sản xuất phần mềm và dịch vụ phần mềm cho dự án <strong>{project_name}</strong> của Bên A thông qua việc <strong>cử đội ngũ kỹ sư phần mềm, chuyên gia kiến trúc và kiểm thử thuộc biên chế chính thức của Bên B tham gia trực tiếp cùng Ban Dự án của Bên A</strong> (tại văn phòng Bên A hoặc mô hình Hybrid).</li>
    <li><strong>1.2. Phân định rõ không phải hoạt động cho thuê lại lao động:</strong> Hai Bên khẳng định rõ ràng Hợp đồng này là <strong>Hợp đồng Hợp tác Phát triển Dự án Phần mềm &amp; Gia công Công đoạn Phần mềm</strong> theo Luật Thương mại, Luật Công nghệ Thông tin và Thông tư 13/2020/TT-BTTTT; hoàn toàn không phải là hoạt động "cho thuê lại lao động" theo Bộ luật Lao động. Bên B trực tiếp quản lý quan hệ lao động, trả lương qua VCB DigiBiz, trích nộp BHXH/BHYT/BHTN (Mã đơn vị <code>TZ0857G</code>), khấu trừ thuế TNCN và chịu trách nhiệm chuyên môn về chất lượng mã nguồn, tài liệu kỹ thuật do đội ngũ kỹ sư của Bên B tạo ra trong dự án của Bên A.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 2. ÁNH XẠ 07 CÔNG ĐOẠN SẢN XUẤT PHẦN MỀM THEO THÔNG TƯ 13/2020/TT-BTTTT (7 SOFTWARE PRODUCTION STAGES)</div>
  <p>Để đảm bảo doanh thu dịch vụ và sản xuất phần mềm theo Hợp đồng này đáp ứng đầy đủ điều kiện hưởng ưu đãi thuế TNDN và chính sách thuế GTGT đối với phần mềm, công việc của đội ngũ kỹ sư Bên B tham gia dự án được chuẩn hóa và nghiệm thu theo 07 công đoạn tại Điều 3 Thông tư 13/2020/TT-BTTTT:</p>
  <table>
    <thead>
      <tr>
        <th style="width:16%;">Công đoạn TT 13/2020</th>
        <th style="width:28%;">Nội dung Công đoạn Phần mềm</th>
        <th>Hoạt động Cụ thể của Nhân sự Kỹ thuật Bên B &amp; Hồ sơ Minh chứng Thuế (Tax Audit Artifacts)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Công đoạn 1 (Bắt buộc)</strong></td>
        <td>Xác định yêu cầu (Requirement Determination)</td>
        <td>Tham gia cùng Product Owner/BA của Bên A thu thập, phân tích nghiệp vụ, làm rõ User Stories, chuẩn hóa đặc tả yêu cầu phần mềm.<br/><em>Chứng từ lưu:</em> Tài liệu SRS / Backlog Ticket / Biên bản làm rõ yêu cầu tính năng.</td>
      </tr>
      <tr>
        <td><strong>Công đoạn 2 (Bắt buộc)</strong></td>
        <td>Phân tích và thiết kế (Analysis &amp; Architecture Design)</td>
        <td>Thiết kế kiến trúc phần mềm (Microservices/ERP), thiết kế cấu trúc cơ sở dữ liệu (ERD), đặc tả giao diện API (OpenAPI/Swagger) và luồng xử lý.<br/><em>Chứng từ lưu:</em> Tài liệu Thiết kế Kỹ thuật (Technical Design Document — TDD), Sơ đồ Kiến trúc &amp; API Spec.</td>
      </tr>
      <tr>
        <td><strong>Công đoạn 3</strong></td>
        <td>Lập trình, viết mã lệnh (Programming &amp; Source Coding)</td>
        <td>Viết mã nguồn phần mềm (Backend, Frontend, Mobile, AI/Data pipeline), tối ưu thuật toán, thực hiện Pull Request và Code Review.<br/><em>Chứng từ lưu:</em> Lịch sử Git Commit / Merge Request log, danh mục Module/Feature đã lập trình trong kỳ.</td>
      </tr>
      <tr>
        <td><strong>Công đoạn 4</strong></td>
        <td>Kiểm thử, thử nghiệm phần mềm (Software Testing &amp; QA)</td>
        <td>Viết Unit Test, thực hiện kiểm thử tích hợp (SIT), kiểm thử chịu tải (Stress Test) và sửa lỗi (Bug fixing) trước khi phát hành.<br/><em>Chứng từ lưu:</em> Kịch bản Test Case, Báo cáo Kết quả Kiểm thử (Test Report) &amp; Log đóng lỗi.</td>
      </tr>
      <tr>
        <td><strong>Công đoạn 5</strong></td>
        <td>Hoàn thiện, đóng gói sản phẩm (Packaging &amp; Documentation)</td>
        <td>Đóng gói bản dựng phần mềm (Docker Image / Release Artifact / CI-CD), biên soạn tài liệu hướng dẫn cài đặt và vận hành kỹ thuật.<br/><em>Chứng từ lưu:</em> Release Notes, gói cài đặt / Container Tag &amp; Tài liệu vận hành.</td>
      </tr>
      <tr>
        <td><strong>Công đoạn 6</strong></td>
        <td>Cài đặt, chuyển giao, hướng dẫn sử dụng, bảo trì</td>
        <td>Triển khai lên môi trường Staging/Production của Bên A, chuyển giao mã nguồn/tri thức cho đội ngũ Bên A, hỗ trợ kỹ thuật sau phát hành.<br/><em>Chứng từ lưu:</em> Biên bản Chuyển giao Kỹ thuật &amp; Nhật ký triển khai.</td>
      </tr>
      <tr>
        <td><strong>Công đoạn 7</strong></td>
        <td>Phát hành sản phẩm phần mềm (Release / Deployment)</td>
        <td>Phối hợp phát hành phiên bản phần mềm phục vụ người dùng cuối / khách hàng của Bên A.<br/><em>Chứng từ lưu:</em> Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm hàng tháng (Mẫu <code>TPL-SW-MTI-03</code>).</td>
      </tr>
    </tbody>
  </table>

  <div class="dgm-article-heading">ĐIỀU 3. TIÊU CHUẨN NHÂN SỰ KỸ THUẬT THAM GIA DỰ ÁN &amp; CAM KẾT THAY THẾ LIÊN TỤC (SOP-DGM-07)</div>
  <ul class="dgm-clause-list">
    <li><strong>3.1. Tuyển chọn &amp; Thẩm định Kỹ thuật:</strong> Bên B cử các kỹ sư phần mềm đáp ứng đúng cấp bậc (Senior/Lead/Middle), ngôn ngữ lập trình và kinh nghiệm dự án theo từng Phụ lục Đặt hàng (Mẫu <code>TPL-SW-MTI-02</code>). Bên A có quyền phỏng vấn thẩm định kỹ thuật trước khi nhân sự chính thức tham gia dự án.</li>
    <li><strong>3.2. Giai đoạn Thử thách Kỹ thuật 05 Ngày Làm việc Đầu tiên:</strong> Trong vòng 30 ngày làm việc đầu tiên kể từ ngày nhân sự bắt đầu tham gia dự án, nếu nhân sự của Bên B không đáp ứng yêu cầu kỹ thuật của dự án (có thông báo bằng văn bản nêu rõ nguyên nhân chuyên môn từ Bên A), Bên B cam kết thay thế nhân sự tương đương và <strong>miễn phí 05 (năm) ngày làm việc đầu tiên</strong> trong trường hợp phải thay thế này.</li>
    <li><strong>3.3. Thay thế Nhân sự Chủ động từ Phía Bên B:</strong> Trường hợp cần điều chuyển hoặc thay thế nhân sự theo đề xuất từ phía Bên B, Bên B phải thông báo bằng văn bản/email cho Bên A trước ít nhất <strong>30 ngày làm việc</strong>, bố trí kỹ sư có trình độ tương đương trở lên và đảm bảo <strong>01 tuần (05 ngày làm việc) chuyển giao công việc (Shadowing/Handover) hoàn toàn miễn phí</strong>, không làm gián đoạn tiến độ dự án của Bên A.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 4. CƠ CHẾ XÁC ĐỊNH KHỐI LƯỢNG CÔNG ĐOẠN PHẦN MỀM &amp; ĐƠN GIÁ PHÍ DỊCH VỤ</div>
  <ul class="dgm-clause-list">
    <li><strong>4.1. Định mức Thời lượng Thực hiện Công đoạn Phần mềm Hàng tháng (Standard Monthly Engineering Window):</strong> Được xác định theo khung chuẩn từ <strong>140 giờ đến 180 giờ/tháng/kỹ sư</strong> (hoặc theo khung giờ chuẩn từng tháng lịch quy định tại Phụ lục SOW).</li>
    <li><strong>4.2. Công thức Tính phí Dịch vụ Phát triển Phần mềm Hàng tháng:</strong>
      <ul>
        <li>Nếu tổng số giờ thực hiện công đoạn phần mềm trong tháng nằm trong Khung Chuẩn ($H_{{\\min}} \\le H_{{\\text{{thực tế}}}} \\le H_{{\\max}}$): Phí dịch vụ bằng <strong>100% Phí Trọn gói Tháng Tiêu chuẩn</strong> hoặc <code>Đơn giá giờ × Số giờ chuẩn</code> theo Phụ lục.</li>
        <li>Nếu số giờ thực tế thấp hơn ngưỡng tối thiểu ($H_{{\\text{{thực tế}}}} &lt; H_{{\\min}}$): <code>Số tiền thanh toán = Đơn giá theo giờ × Số giờ thực tế nghiệm thu</code>.</li>
        <li>Nếu số giờ tăng ca trong vòng 20 giờ đầu vượt ngưỡng chuẩn ($H_{{\\max}} &lt; H_{{\\text{{thực tế}}}} \\le H_{{\\max}} + 20$): <code>01 giờ tăng ca = 100% × Đơn giá theo giờ</code>.</li>
        <li>Nếu số giờ tăng ca vượt quá 20 giờ trên ngưỡng chuẩn ($H_{{\\text{{thực tế}}}} &gt; H_{{\\max}} + 20$): <code>01 giờ tăng ca vượt mức = 150% × Đơn giá theo giờ</code>.</li>
      </ul>
    </li>
    <li><strong>4.3. Chính sách Thuế GTGT &amp; Thuế TNDN đối với Dịch vụ Phần mềm:</strong> Phí dịch vụ phát triển và gia công công đoạn phần mềm theo Hợp đồng này được phân loại theo đúng bản chất dịch vụ phần mềm quy định tại Nghị định 71/2007/NĐ-CP, Thông tư 13/2020/TT-BTTTT và Khoản 21 Điều 4 Thông tư 219/2013/TT-BTC. Tỷ lệ thuế suất GTGT trên hóa đơn điện tử (Không chịu thuế GTGT <code>KCT</code> hoặc <code>8%</code> theo Nghị định giảm thuế GTGT hiện hành đối với cấu phần dịch vụ CNTT chịu thuế) được hai Bên thống nhất rõ trên Hóa đơn Nháp trước khi phát hành chính thức.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 5. QUY TRÌNH NGHIỆM THU CÔNG ĐOẠN, ĐỐI SOÁT HÓA ĐƠN NHÁP &amp; THANH TOÁN (SOP-DGM-08)</div>
  <ul class="dgm-clause-list">
    <li><strong>5.1. Bước 1 — Chốt Khối lượng Công đoạn &amp; Timesheet (Ngày 25–30 hàng tháng):</strong> Kỹ sư Bên B và Quản lý Dự án Bên A xác nhận <em>Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm &amp; Bảng Chấm công Kỹ thuật</em> (Mẫu <code>TPL-SW-MTI-03</code>).</li>
    <li><strong>5.2. Bước 2 — Gửi Hóa đơn Nháp (Draft Invoice Review) Trước Khi Ký Số:</strong> Để tránh mọi sai sót phải hủy/điều chỉnh hóa đơn điện tử, Phòng Kế toán Bên B gửi <strong>Bản Nháp Hóa đơn GTGT (Draft Invoice)</strong> kèm Biên bản nghiệm thu cho Kế toán Bên A ({p_email}) kiểm tra tên hàng hóa dịch vụ phần mềm, mã số thuế, số tiền trước khi ký số HSM.</li>
    <li><strong>5.3. Bước 3 — Phát hành Hóa đơn Điện tử Chính thức (Ký hiệu 1C26TAA) &amp; Thanh toán:</strong> Ngay sau khi Bên A xác nhận Bản Nháp Hóa đơn (hoặc sau 02 ngày làm việc không có yêu cầu chỉnh sửa), Bên B phát hành Hóa đơn GTGT Điện tử có mã của Cơ quan Thuế (Ký hiệu <code>1C26TAA</code>). Bên A thanh toán 100% giá trị hóa đơn bằng chuyển khoản VNĐ vào tài khoản Vietcombank số <strong>1202703007</strong> của CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ trong vòng <strong>{pay_days} ngày</strong> kể từ ngày nhận đủ hồ sơ thanh toán hợp lệ.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 6. HỒ SƠ MINH CHỨNG PHỤC VỤ QUYẾT TOÁN ƯU ĐÃI THUẾ PHẦN MỀM</div>
  <p>Hai Bên cam kết phối hợp ký kết và lưu trữ đầy đủ Bộ Hồ sơ Minh chứng Quy trình Sản xuất &amp; Dịch vụ Phần mềm theo Thông tư 13/2020/TT-BTTTT gồm: (1) Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm (<code>TPL-SW-MTI-01</code>); (2) Phụ lục Đặt hàng SOW quy định rõ công đoạn phần mềm và danh sách kỹ sư tham gia (<code>TPL-SW-MTI-02</code>); (3) Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm kèm danh mục tính năng/module đã thực hiện thuộc Công đoạn 1 &amp; Công đoạn 2 trở lên (<code>TPL-SW-MTI-03</code>); và (4) Hóa đơn GTGT điện tử <code>1C26TAA</code> cùng chứng từ thanh toán không dùng tiền mặt qua ngân hàng.</p>

  <div class="dgm-article-heading">ĐIỀU 7. QUYỀN SỞ HỮU TRÍ TUỆ ĐỐI VỚI MÃ NGUỒN &amp; SẢN PHẨM PHẦN MỀM</div>
  <p>Toàn bộ mã nguồn (Source Code), cơ sở dữ liệu, tài liệu thiết kế kiến trúc, kịch bản kiểm thử và các sản phẩm phần mềm phát sinh từ quá trình đội ngũ kỹ sư Bên B tham gia phát triển dự án cho Bên A sẽ thuộc quyền sở hữu trí tuệ duy nhất của Bên A (hoặc khách hàng cuối của Bên A) ngay sau khi Bên A hoàn tất nghĩa vụ thanh toán phí dịch vụ phần mềm tương ứng của kỳ nghiệm thu đó. Bên B giữ quyền sở hữu đối với các thư viện khung dùng chung (Pre-existing Libraries / Tools) không chứa nghiệp vụ đặc thù của Bên A.</p>

  <div class="dgm-article-heading">ĐIỀU 8. BẢO MẬT THÔNG TIN (ISO/IEC 27001) &amp; BẢO VỆ DỮ LIỆU CÁ NHÂN (NGHỊ ĐỊNH 13/2023/NĐ-CP)</div>
  <p>Bên B và toàn bộ kỹ sư phần mềm được cử tham gia dự án cam kết tuân thủ nghiêm ngặt Thỏa thuận Bảo mật Thông tin (Mẫu <code>TPL-SW-MTI-04</code>), tiêu chuẩn an toàn thông tin ISO/IEC 27001, ISO/IEC 27701 và Nghị định 13/2023/NĐ-CP; tuyệt đối không sao chép trái phép mã nguồn, không đưa khóa bí mật (API Keys, Credentials) lên kho lưu trữ công cộng.</p>

  <div class="dgm-article-heading">ĐIỀU 9. CAM KẾT KHÔNG LÔI KÉO NHÂN SỰ (NON-SOLICITATION)</div>
  <p>Trong suốt thời hạn hiệu lực của Hợp đồng này và trong vòng <strong>12 (mười hai) tháng</strong> sau khi Hợp đồng hoặc Phụ lục tương ứng chấm dứt, Bên A cam kết không trực tiếp hoặc gián tiếp tuyển dụng, ký hợp đồng lao động hoặc hợp đồng dịch vụ cá nhân với bất kỳ kỹ sư phần mềm nào của Bên B đã tham gia dự án của Bên A nếu không có sự chấp thuận trước bằng văn bản của Bên B.</p>

  <div class="dgm-article-heading">ĐIỀU 10. TẠM NGƯNG, CHẤM DỨT HỢP ĐỒNG &amp; XỬ LÝ VI PHẠM</div>
  <p>Mỗi Bên có quyền thông báo bằng văn bản về việc gia hạn hoặc kết thúc từng Phụ lục dự án trước ít nhất <strong>15 ngày làm việc</strong> (hoặc 30 ngày đối với Hợp đồng Khung). Trường hợp Bên A chậm thanh toán quá 15 ngày so với hạn thanh toán tại Điều 5.3, Bên B có quyền tính lãi chậm trả theo lãi suất nợ quá hạn trung bình trên thị trường và tạm ngưng bàn giao mã nguồn kỳ tiếp theo cho đến khi công nợ được tất toán.</p>

  <div class="dgm-article-heading">ĐIỀU 11. BẤT KHẢ KHÁNG &amp; GIẢI QUYẾT TRANH CHẤP</div>
  <p>Mọi tranh chấp phát sinh từ hoặc liên quan đến Hợp đồng này trước hết được giải quyết thông qua thương lượng thiện chí giữa hai Bên trong vòng 30 ngày. Nếu không đạt được thỏa thuận, tranh chấp sẽ được đưa ra giải quyết tại Tòa án Nhân dân có thẩm quyền tại TP. Hồ Chí Minh theo pháp luật Việt Nam.</p>

  <div class="dgm-article-heading">ĐIỀU 12. ĐIỀU KHOẢN CHUNG &amp; HIỆU LỰC HỢP ĐỒNG</div>
  <p>Hợp đồng này có hiệu lực kể từ ngày ký, được lập thành 02 (hai) bản tiếng Việt (và bản đối chiếu song ngữ khi cần) có giá trị pháp lý như nhau, mỗi Bên giữ 01 (một) bản để thực hiện và lưu hồ sơ thuế.</p>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <span>{p_rep_title}</span><br/><br/><br/>
      <strong>{p_rep}</strong><br/>
      <em>(Ký tên, đóng dấu pháp nhân / Chữ ký số)</em>
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ)</strong><br/>
      <span>Chủ tịch HĐQT kiêm Giám đốc</span><br/><br/><br/>
      <strong>LÊ XUÂN HOÀNG</strong><br/>
      <em>(Đã ký số HSM Viettel-CA — MST 0317958465)</em>
    </div>
  </div>
</div>"""

    doc_01 = wrap_dgm_branded_html_document(
        body_01,
        title=f"TPL-SW-MTI-01 Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm — {prof.get('partner_name')}",
        doc_code="TPL-SW-MTI-01",
        sop_ref="SOP-DGM-09",
        classification="B2B SOFTWARE CO-DEV CONTRACT (TT 13/2020 TAX INCENTIVE)",
        include_header=True,
    )

    # -------------------------------------------------------------------------
    # TPL-SW-MTI-02: Phụ lục Đặt hàng (SOW) Cử Nhân sự Kỹ thuật Tham gia Dự án Phần mềm
    # -------------------------------------------------------------------------
    body_02 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc</div>
  </div>

  <div class="dgm-contract-title">
    <h1>PHỤ LỤC HỢP ĐỒNG (STATEMENT OF WORK — SOW)<br/>CỬ NHÂN SỰ KỸ THUẬT THAM GIA CÙNG PHÁT TRIỂN DỰ ÁN PHẦN MỀM</h1>
    <div class="contract-sub">Số Phụ lục / Appendix No.: <strong>{appendix_no}</strong> • Đính kèm Hợp đồng số: <strong>{contract_no}</strong></div>
  </div>

  <table>
    <tr><th style="width:28%;">Bên A (Đối tác Dự án)</th><td><strong>{p_name}</strong> — MST: <strong>{p_vat}</strong> ({p_code})</td></tr>
    <tr><th>Bên B (Đơn vị Phần mềm)</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: <strong>0317958465</strong></td></tr>
    <tr><th>Tên Dự án Phần mềm Tham gia</th><td><strong>{project_name}</strong></td></tr>
    <tr><th>Địa điểm &amp; Mô hình Phối hợp</th><td>{work_loc}</td></tr>
    <tr><th>Khung Giờ Chuẩn Hàng tháng</th><td><strong>{html.escape(str(prof.get('standard_window_hours') or '140 – 180 giờ/tháng'))}</strong></td></tr>
  </table>

  <div class="dgm-article-heading">1. DANH SÁCH KỸ SƯ PHẦN MỀM DIGIMATE THAM GIA DỰ ÁN &amp; PHÂN CÔNG CÔNG ĐOẠN TT 13/2020/TT-BTTTT</div>
  <table>
    <thead>
      <tr>
        <th style="width:5%;">STT</th>
        <th style="width:18%;">Họ tên Kỹ sư &amp; Mã NV</th>
        <th style="width:18%;">Vị trí Chuyên môn</th>
        <th style="width:27%;">Công đoạn Sản xuất Phần mềm Đảm nhận (TT 13/2020/TT-BTTTT)</th>
        <th style="width:11%;">Định mức Giờ</th>
        <th style="width:10%;">Đơn giá Giờ</th>
        <th style="width:11%;">Phí Chuẩn/Tháng</th>
      </tr>
    </thead>
    <tbody>
      {eng_rows_html}
    </tbody>
    <tfoot>
      <tr>
        <th colspan="6" style="text-align:right;">TỔNG GIÁ TRỊ DỊCH VỤ PHÁT TRIỂN PHẦN MỀM TIÊU CHUẨN / THÁNG (CHƯA GTGT):</th>
        <th><strong>{monthly_total_str}</strong></th>
      </tr>
    </tfoot>
  </table>

  <div class="dgm-article-heading">2. NỘI DUNG SẢN PHẨM BÀN GIAO TRONG KỲ (SOFTWARE STAGE DELIVERABLES)</div>
  <ul class="dgm-clause-list">
    <li><strong>Công đoạn 1 &amp; 2 (Xác định yêu cầu &amp; Phân tích thiết kế):</strong> Hồ sơ phân tích yêu cầu nghiệp vụ (Requirement Spec), thiết kế kiến trúc cơ sở dữ liệu, tài liệu đặc tả API và luồng tích hợp hệ thống của dự án <strong>{project_name}</strong>.</li>
    <li><strong>Công đoạn 3 &amp; 4 (Lập trình viết mã lệnh &amp; Kiểm thử hiệu chỉnh):</strong> Mã nguồn (Source Code) hoàn chỉnh được commit trên nhánh kho lưu trữ Git của dự án, vượt qua Code Review, Unit Test và kiểm thử tích hợp (SIT/UAT).</li>
    <li><strong>Công đoạn 5 &amp; 6 (Đóng gói, cài đặt &amp; chuyển giao):</strong> Bản dựng phần mềm đóng gói (Build/Release package) và tài liệu hướng dẫn vận hành cho từng Sprint/Tháng.</li>
  </ul>

  <div class="dgm-article-heading">3. CƠ CHẾ TÍNH PHÍ THEO KHUNG GIỜ THÁNG, CHÍNH SÁCH THUẾ &amp; CAM KẾT SLA</div>
  <p>Việc nghiệm thu khối lượng công đoạn phần mềm thực hiện vào cuối mỗi tháng dương lịch dựa trên <em>Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm</em> (<code>TPL-SW-MTI-03</code>), đáp ứng đầy đủ điều kiện sản xuất và dịch vụ phần mềm theo <strong>Thông tư 13/2020/TT-BTTTT</strong>, <strong>Nghị định 71/2007/NĐ-CP</strong> và Khoản 21 Điều 4 <strong>Thông tư 219/2013/TT-BTC</strong>. Mọi điều khoản khác tuân thủ theo Hợp đồng Khung số <strong>{contract_no}</strong>.</p>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <strong>{p_rep}</strong> — {p_rep_title}
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (DIGIMATE JSC)</strong><br/>
      <strong>LÊ XUÂN HOÀNG</strong> — Chủ tịch HĐQT kiêm Giám đốc
    </div>
  </div>
</div>"""

    doc_02 = wrap_dgm_branded_html_document(
        body_02,
        title=f"TPL-SW-MTI-02 Phụ lục SOW Cử Nhân sự Tham gia Phát triển Dự án Phần mềm — {prof.get('partner_name')}",
        doc_code="TPL-SW-MTI-02",
        sop_ref="SOP-DGM-09",
        classification="B2B SOFTWARE SOW APPENDIX (TT 13/2020)",
        include_header=True,
    )

    # -------------------------------------------------------------------------
    # TPL-SW-MTI-03: Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm & Hồ sơ Minh chứng TT 13/2020
    # -------------------------------------------------------------------------
    body_03 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc</div>
  </div>

  <div class="dgm-contract-title">
    <h1>BIÊN BẢN NGHIỆM THU CÔNG ĐOẠN PHÁT TRIỂN PHẦN MỀM<br/>&amp; HỒ SƠ MINH CHỨNG QUY TRÌNH THÔNG TƯ 13/2020/TT-BTTTT</h1>
    <div class="contract-sub">(SOFTWARE DEVELOPMENT STAGE ACCEPTANCE CERTIFICATE &amp; CIRCULAR 13/2020 TAX INCENTIVE DOSSIER)<br/>
    Kèm theo Hợp đồng số: <strong>{contract_no}</strong> • Phụ lục số: <strong>{appendix_no}</strong></div>
  </div>

  <div class="dgm-tax-callout">
    <strong>📌 CHỨNG TỪ GỐC PHỤC VỤ QUYẾT TOÁN ƯU ĐÃI THUẾ TNDN &amp; GTGT DỊCH VỤ PHẦN MỀM (ĐIỀU 4 THÔNG TƯ 13/2020/TT-BTTTT • NGHỊ ĐỊNH 71/2007/NĐ-CP • THÔNG TƯ 219/2013/TT-BTC):</strong><br/>
    Biên bản này xác nhận Bên B (Digimate JSC — MST <code>0317958465</code>) đã trực tiếp thực hiện các tác nghiệp thuộc <strong>Công đoạn 1 (Xác định yêu cầu)</strong>, <strong>Công đoạn 2 (Phân tích và thiết kế)</strong>, kết hợp với <strong>Công đoạn 3 (Lập trình, viết mã lệnh)</strong> và <strong>Công đoạn 4 (Kiểm thử, hiệu chỉnh phần mềm)</strong> cho dự án phần mềm của Bên A, đủ điều kiện xác định hoạt động sản xuất và dịch vụ phần mềm hưởng ưu đãi thuế theo quy định hiện hành.
  </div>

  <table>
    <tr><th style="width:28%;">Bên A (Chủ Dự án Phần mềm)</th><td><strong>{p_name}</strong> — MST: <strong>{p_vat}</strong></td></tr>
    <tr><th>Bên B (Đơn vị Thực hiện Công đoạn PM)</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: <strong>0317958465</strong></td></tr>
    <tr><th>Dự án Phần mềm Nghiệm thu</th><td><strong>{project_name}</strong></td></tr>
  </table>

  <div class="dgm-article-heading">I. BẢNG NGHIỆM THU TÁC NGHIỆP 07 CÔNG ĐOẠN SẢN XUẤT PHẦN MỀM (THÔNG TƯ 13/2020/TT-BTTTT)</div>
  <table>
    <thead>
      <tr>
        <th style="width:18%;">Công đoạn TT 13/2020</th>
        <th style="width:27%;">Tác nghiệp Phần mềm Đã Thực hiện</th>
        <th style="width:37%;">Sản phẩm / Tài liệu Minh chứng Bàn giao (Deliverables)</th>
        <th style="width:18%;">Đánh giá Nghiệm thu</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Công đoạn 1</strong><br/>Xác định yêu cầu</td>
        <td>Làm rõ yêu cầu nghiệp vụ, xây dựng đặc tả User Stories &amp; tiêu chí chấp nhận (Acceptance Criteria) cho các phân hệ trong Sprint.</td>
        <td>Đặc tả Yêu cầu Phần mềm (SRS / Sprint Backlog Spec) đã được Product Owner Bên A phê duyệt.</td>
        <td><strong>ĐẠT (100%)</strong></td>
      </tr>
      <tr>
        <td><strong>Công đoạn 2</strong><br/>Phân tích &amp; Thiết kế</td>
        <td>Thiết kế kiến trúc dữ liệu (Database Schema), đặc tả REST/gRPC API và luồng xử lý bảo mật.</td>
        <td>Tài liệu Thiết kế Kỹ thuật (Technical Architecture &amp; API Spec) lưu trữ trên hệ thống quản lý dự án.</td>
        <td><strong>ĐẠT (100%)</strong></td>
      </tr>
      <tr>
        <td><strong>Công đoạn 3</strong><br/>Lập trình mã lệnh</td>
        <td>Viết mã nguồn phần mềm, xây dựng các module nghiệp vụ, tích hợp API và tối ưu hóa truy vấn.</td>
        <td>Mã nguồn (Source Code) trên Git Repository của dự án (100% Merge Request đã qua Code Review).</td>
        <td><strong>ĐẠT (100%)</strong></td>
      </tr>
      <tr>
        <td><strong>Công đoạn 4</strong><br/>Kiểm thử phần mềm</td>
        <td>Thực hiện kiểm thử đơn vị (Unit Test), kiểm thử tích hợp (SIT) và hiệu chỉnh lỗi (Bug fixing).</td>
        <td>Báo cáo Kết quả Kiểm thử (QA/SIT Test Report): 0 lỗi nghiêm trọng (Fatal = 0, Major = 0).</td>
        <td><strong>ĐẠT (100%)</strong></td>
      </tr>
    </tbody>
  </table>

  <div class="dgm-article-heading">II. BẢNG TỔNG HỢP KHỐI LƯỢNG CÔNG ĐOẠN CỦA ĐỘI NGŨ KỸ SƯ THAM GIA &amp; GIÁ TRỊ NGHIỆM THU</div>
  <table>
    <thead>
      <tr>
        <th style="width:5%;">STT</th>
        <th style="width:20%;">Kỹ sư Phần mềm Tham gia</th>
        <th style="width:25%;">Công đoạn Đảm nhận</th>
        <th style="width:24%;">Kết quả Đầu ra Phần mềm</th>
        <th style="width:13%;">Khối lượng Giờ</th>
        <th style="width:13%;">Thành tiền (VNĐ)</th>
      </tr>
    </thead>
    <tbody>
      {accept_rows_html}
    </tbody>
    <tfoot>
      <tr>
        <th colspan="5" style="text-align:right;">TỔNG GIÁ TRỊ CÔNG ĐOẠN PHẦN MỀM NGHIỆM THU ĐỦ ĐIỀU KIỆN XUẤT HÓA ĐƠN (1C26TAA):</th>
        <th><strong>{monthly_total_str}</strong></th>
      </tr>
    </tfoot>
  </table>

  <div class="dgm-article-heading">III. KẾT LUẬN NGHIỆM THU &amp; ĐỀ NGHỊ PHÁT HÀNH HÓA ĐƠN ĐIỆN TỬ (SOP-DGM-08)</div>
  <p>Hai Bên thống nhất nghiệm thu 100% khối lượng công đoạn phát triển phần mềm nêu trên. Biên bản này là căn cứ pháp lý và hồ sơ minh chứng Thông tư 13/2020/TT-BTTTT để Bên B gửi <strong>Hóa đơn Nháp đối soát</strong> và phát hành <strong>Hóa đơn GTGT Điện tử chính thức (Ký hiệu 1C26TAA)</strong> để Bên A thanh toán qua tài khoản Vietcombank số <strong>1202703007</strong> của CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ.</p>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN NGHIỆM THU BÊN A ({p_name})</strong><br/>
      <strong>{p_rep}</strong> — {p_rep_title}
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN NGHIỆM THU BÊN B (DIGIMATE JSC)</strong><br/>
      <strong>LÊ XUÂN HOÀNG</strong> — Chủ tịch HĐQT kiêm Giám đốc
    </div>
  </div>
</div>"""

    doc_03 = wrap_dgm_branded_html_document(
        body_03,
        title=f"TPL-SW-MTI-03 Biên bản Nghiệm thu Công đoạn Phần mềm TT 13/2020 — {prof.get('partner_name')}",
        doc_code="TPL-SW-MTI-03",
        sop_ref="SOP-DGM-09",
        classification="B2B TAX INCENTIVE ACCEPTANCE RECORD (TT 13/2020)",
        include_header=True,
    )

    # -------------------------------------------------------------------------
    # TPL-SW-MTI-04: Thỏa thuận Sở hữu Trí tuệ Mã nguồn & Bảo mật Dự án Phần mềm (IP & NDA)
    # -------------------------------------------------------------------------
    body_04 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc</div>
  </div>

  <div class="dgm-contract-title">
    <h1>THỎA THUẬN CHUYỂN GIAO QUYỀN SỞ HỮU TRÍ TUỆ MÃ NGUỒN<br/>&amp; BẢO MẬT DỰ ÁN PHẦN MỀM (SOFTWARE IP ASSIGNMENT &amp; NDA)</h1>
    <div class="contract-sub">Đính kèm Hợp đồng Hợp tác Phát triển Dự án Phần mềm số: <strong>{contract_no}</strong> • Đối tác: <strong>{p_name}</strong></div>
  </div>

  <div class="dgm-article-heading">ĐIỀU 1. CAM KẾT MÃ NGUỒN SẠCH (CLEAN-ROOM SOFTWARE &amp; OPEN-SOURCE COMPLIANCE)</div>
  <p>Bên B (Digimate JSC) và các kỹ sư phần mềm tham gia dự án <strong>{project_name}</strong> theo quy trình 7 công đoạn sản xuất phần mềm (<strong>Thông tư 13/2020/TT-BTTTT</strong>, <strong>Nghị định 71/2007/NĐ-CP</strong> và <strong>Thông tư 219/2013/TT-BTC</strong>) cam kết toàn bộ mã nguồn được viết mới hoặc sử dụng các thư viện mã nguồn mở có giấy phép thương mại tương thích (MIT, Apache 2.0, BSD), không vi phạm bản quyền của bất kỳ bên thứ ba nào và không cài đặt bất kỳ đoạn mã độc, cửa hậu (Backdoor) hoặc cơ chế khóa trái phép nào.</p>

  <div class="dgm-article-heading">ĐIỀU 2. CHUYỂN GIAO TOÀN BỘ QUYỀN TÁC GIẢ &amp; QUYỀN SỞ HỮU MÃ NGUỒN (IP ASSIGNMENT)</div>
  <p>Ngay khi Bên A hoàn thành thanh toán phí dịch vụ phần mềm của từng kỳ nghiệm thu theo Điều 5 Hợp đồng Khung, toàn bộ quyền tài sản thuộc quyền tác giả và quyền sở hữu công nghiệp đối với các đoạn mã lệnh, cấu trúc cơ sở dữ liệu, tài liệu thiết kế kiến trúc được tạo ra trong kỳ đó tự động chuyển giao toàn vẹn, không hủy ngang cho Bên A.</p>

  <div class="dgm-article-heading">ĐIỀU 3. BẢO MẬT KỸ THUẬT CHO NHÂN SỰ THAM GIA DỰ ÁN (ISO/IEC 27001 &amp; NGHỊ ĐỊNH 13/2023/NĐ-CP)</div>
  <ul class="dgm-clause-list">
    <li>Mỗi kỹ sư phần mềm của Bên B khi tham gia dự án tại văn phòng Bên A đều ký Cam kết Bảo mật Cá nhân (Individual Engineer NDA) và tuân thủ chính sách kiểm soát truy cập (VPN, MFA, Git SSH Key, VDI) của Bên A.</li>
    <li>Khi kết thúc dự án hoặc thay thế nhân sự, kỹ sư bàn giao lại toàn bộ tài khoản, thiết bị và xóa bỏ hoàn toàn bản sao mã nguồn cục bộ dưới sự giám sát của Quản lý Kỹ thuật hai Bên.</li>
  </ul>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <strong>{p_rep}</strong> — {p_rep_title}
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (DIGIMATE JSC)</strong><br/>
      <strong>LÊ XUÂN HOÀNG</strong> — Chủ tịch HĐQT kiêm Giám đốc
    </div>
  </div>
</div>"""

    doc_04 = wrap_dgm_branded_html_document(
        body_04,
        title=f"TPL-SW-MTI-04 Thỏa thuận Sở hữu Trí tuệ Mã nguồn & Bảo mật Dự án Phần mềm — {prof.get('partner_name')}",
        doc_code="TPL-SW-MTI-04",
        sop_ref="SOP-DGM-09",
        classification="B2B SOFTWARE IP & NDA CONFIDENTIAL",
        include_header=True,
    )

    return [
        {
            'code': 'TPL-SW-MTI-01',
            'tpl_code': 'TPL-SW-MTI-01',
            'contract_group': 'mti_codev',
            'filename': f"01_HD_Khung_Hop_Tac_Phat_Trien_Du_An_Phan_Mem_{safe_code}.html",
            'name': f"[TPL-SW-MTI-01] Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm (Nhân sự Tham gia Dự án • Chuẩn Ưu đãi Phần mềm TT 13/2020) — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-MTI-01] Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm (Nhân sự Tham gia Dự án • Chuẩn Ưu đãi Phần mềm TT 13/2020) — {prof.get('partner_name')}",
            'html': doc_01,
        },
        {
            'code': 'TPL-SW-MTI-02',
            'tpl_code': 'TPL-SW-MTI-02',
            'contract_group': 'mti_codev',
            'filename': f"02_Phu_Luc_SOW_Cu_Nhan_Su_Tham_Gia_Du_An_PM_{safe_code}.html",
            'name': f"[TPL-SW-MTI-02] Phụ lục Đặt hàng (SOW) Cử Nhân sự Kỹ thuật Tham gia Cùng Phát triển Dự án Phần mềm — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-MTI-02] Phụ lục Đặt hàng (SOW) Cử Nhân sự Kỹ thuật Tham gia Cùng Phát triển Dự án Phần mềm — {prof.get('partner_name')}",
            'html': doc_02,
        },
        {
            'code': 'TPL-SW-MTI-03',
            'tpl_code': 'TPL-SW-MTI-03',
            'contract_group': 'mti_codev',
            'filename': f"03_Bien_Ban_Nghiem_Thu_Cong_Doan_PM_TT13_{safe_code}.html",
            'name': f"[TPL-SW-MTI-03] Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm & Hồ sơ Minh chứng TT 13/2020/TT-BTTTT — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-MTI-03] Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm & Hồ sơ Minh chứng TT 13/2020/TT-BTTTT — {prof.get('partner_name')}",
            'html': doc_03,
        },
        {
            'code': 'TPL-SW-MTI-04',
            'tpl_code': 'TPL-SW-MTI-04',
            'contract_group': 'mti_codev',
            'filename': f"04_Thoa_Thuan_So_Huu_Tri_Tue_Ma_Nguon_NDA_{safe_code}.html",
            'name': f"[TPL-SW-MTI-04] Thỏa thuận Chuyển giao Quyền Sở hữu Trí tuệ Mã nguồn & Bảo mật Dự án Phần mềm — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-MTI-04] Thỏa thuận Chuyển giao Quyền Sở hữu Trí tuệ Mã nguồn & Bảo mật Dự án Phần mềm — {prof.get('partner_name')}",
            'html': doc_04,
        },
    ]


# =============================================================================
# GROUP B — Nhóm KTT (Khang Trường Thịnh): Bộ Mẫu Hợp Đồng Dịch Vụ Phần Mềm Trọn Gói
# (Turnkey Software Development & Full-Package Implementation — Chuẩn Ưu Đãi Phần Mềm)
# =============================================================================
def render_ktt_turnkey_contract_suite(partner_data=None):
    """Renders the 4 Best-Practice Turnkey Software Package Contract Templates
    (`TPL-SW-KTT-01` .. `TPL-SW-KTT-04`) modeled on KTT (Khang Trường Thịnh) & 360-Sales.
    """
    prof = _resolve_partner_profile(partner_data or 'KTT')
    if prof.get('profile_key') == 'MTI' and not isinstance(partner_data, dict):
        prof = dict(CANONICAL_SW_PARTNER_PROFILES['KTT'])

    p_name = html.escape(str(prof.get('partner_name') or 'CÔNG TY TNHH KHANG TRƯỜNG THỊNH'))
    p_name_en = html.escape(str(prof.get('partner_name_en') or 'KHANG TRUONG THINH CO., LTD (KTT)'))
    p_vat = html.escape(str(prof.get('vat') or '0316889922'))
    p_addr = html.escape(str(prof.get('address') or 'TP. Hồ Chí Minh, Việt Nam'))
    p_rep = html.escape(str(prof.get('representative') or 'Ban Giám đốc Công ty TNHH Khang Trường Thịnh'))
    p_rep_title = html.escape(str(prof.get('rep_title') or 'Giám đốc'))
    p_email = html.escape(str(prof.get('email') or 'accounting@khangtruongthinh.vn'))
    p_code = html.escape(str(prof.get('partner_code') or 'PTN-DGM-2026-0008'))
    safe_code = re.sub(r'[^A-Za-z0-9_-]+', '_', str(prof.get('partner_code') or 'KTT'))
    contract_no = html.escape(str(prof.get('contract_no') or 'KTT-DIGIMATE/SW-TURNKEY/2026-001'))
    appendix_no = html.escape(str(prof.get('appendix_no') or 'PL01-SRS-UAT/KTT-DIGIMATE/2026-001'))
    project_name = html.escape(
        str(
            prof.get('project_name')
            or 'Hệ thống Phần mềm Quản trị Kinh doanh, Danh mục Sản phẩm, Kho vận, Đơn hàng & Hoa hồng Trọn gói (KTT Enterprise Suite)'
        )
    )
    total_vnd = float(prof.get('turnkey_total_vnd') or 200_000_000)
    total_str = _fmt_vnd(total_vnd)
    m1_30 = _fmt_vnd(total_vnd * 0.30)
    m2_40 = _fmt_vnd(total_vnd * 0.40)
    m3_30 = _fmt_vnd(total_vnd * 0.30)
    opt_a_65 = _fmt_vnd(total_vnd * 0.65)
    opt_a_35 = _fmt_vnd(total_vnd * 0.35)
    amc_annual = _fmt_vnd(total_vnd * 0.15)

    # -------------------------------------------------------------------------
    # TPL-SW-KTT-01: Hợp đồng Thiết kế, Xây dựng & Triển khai Phần mềm Trọn gói (14 Điều)
    # -------------------------------------------------------------------------
    body_ktt_01 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM / SOCIALIST REPUBLIC OF VIETNAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc / Independence – Freedom – Happiness</div>
  </div>

  <div class="dgm-contract-title">
    <h1>HỢP ĐỒNG THIẾT KẾ, XÂY DỰNG &amp; TRIỂN KHAI PHẦN MỀM TRỌN GÓI</h1>
    <div class="contract-sub">(TURNKEY SOFTWARE DEVELOPMENT &amp; FULL-PACKAGE IMPLEMENTATION CONTRACT)<br/>
    Nhóm Khách hàng Điển hình: <strong>KTT — Khang Trường Thịnh</strong> • Chuẩn 07 Công đoạn Thông tư 13/2020/TT-BTTTT &amp; Không Chịu Thuế GTGT (KCT)<br/>
    Số Hợp đồng / Contract No.: <strong>{contract_no}</strong> • Mã Đối tác: <strong>{p_code}</strong></div>
  </div>

  <div class="dgm-tax-callout">
    <strong>⚖️ CĂN CỨ PHÁP LÝ &amp; CHÍNH SÁCH ƯU ĐÃI THUẾ DỊCH VỤ PHẦN MỀM TRỌN GÓI:</strong>
    <ul class="dgm-clause-list" style="margin-bottom:0;">
      <li>Căn cứ Bộ luật Dân sự số 91/2015/QH13 và Luật Thương mại số 36/2005/QH11;</li>
      <li>Căn cứ Luật Công nghệ Thông tin số 67/2006/QH11, Nghị định số 71/2007/NĐ-CP và <strong>Thông tư số 13/2020/TT-BTTTT</strong> ngày 03/07/2020 quy định quy trình 07 công đoạn sản xuất sản phẩm phần mềm;</li>
      <li>Căn cứ <strong>Khoản 21 Điều 4 Thông tư số 219/2013/TT-BTC</strong> của Bộ Tài chính: <em>Phần mềm máy tính và dịch vụ phần mềm theo quy định của pháp luật thuộc đối tượng không chịu thuế giá trị gia tăng (KCT)</em>; đồng thời doanh thu sản xuất phần mềm đáp ứng quy trình Thông tư 13/2020/TT-BTTTT được hưởng ưu đãi thuế TNDN theo quy định.</li>
    </ul>
  </div>

  <table>
    <tr>
      <th style="width:28%;">BÊN A (KHÁCH HÀNG ĐẶT HÀNG PHẦN MỀM TRỌN GÓI)</th>
      <td>
        <strong>{p_name}</strong> ({p_name_en})<br/>
        Mã số thuế (Tax ID): <strong>{p_vat}</strong> • Mã Đối tác ERP: <strong>{p_code}</strong><br/>
        Địa chỉ trụ sở: {p_addr}<br/>
        Đại diện pháp luật: <strong>{p_rep}</strong> — Chức vụ: {p_rep_title} • Email nhận HĐĐT: {p_email}
      </td>
    </tr>
    <tr>
      <th>BÊN B (ĐƠN VỊ SẢN XUẤT &amp; TRIỂN KHAI PHẦN MỀM TRỌN GÓI)</th>
      <td>
        <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JOINT STOCK COMPANY — DIGIMATE JSC)</strong><br/>
        Mã số thuế (Tax ID): <strong>0317958465</strong> • Mã ĐV BHXH: <strong>TZ0857G</strong> • Ký hiệu HĐĐT: <strong>1C26TAA</strong><br/>
        Địa chỉ trụ sở: 344–346 Nguyễn Trọng Tuyển, Phường 2, Quận Tân Bình (Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ), TP. Hồ Chí Minh, Việt Nam<br/>
        Tài khoản thụ hưởng: <strong>1202703007</strong> — Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank — PGD Trung Sơn / CN Tân Định)<br/>
        Đại diện pháp luật: <strong>Ông Lê Xuân Hoàng</strong> — Chức vụ: Chủ tịch HĐQT kiêm Giám đốc
      </td>
    </tr>
  </table>

  <div class="dgm-article-heading">ĐIỀU 1. ĐỐI TƯỢNG HỢP ĐỒNG &amp; QUY TRÌNH SẢN XUẤT PHẦN MỀM 07 CÔNG ĐOẠN</div>
  <p>Bên A đồng ý đặt hàng và Bên B đồng ý nhận thực hiện trọn gói (Turnkey Package) việc khảo sát, phân tích, thiết kế kiến trúc, lập trình, kiểm thử, đóng gói, cài đặt, đào tạo và bàn giao đưa vào vận hành chính thức hệ thống phần mềm: <strong>{project_name}</strong> theo đầy đủ 07 công đoạn sản xuất phần mềm quy định tại Điều 3 Thông tư 13/2020/TT-BTTTT.</p>

  <div class="dgm-article-heading">ĐIỀU 2. PHẠM VI PHÂN HỆ CHỨC NĂNG TRỌN GÓI (CORE SOFTWARE MODULES)</div>
  <p>Hệ thống phần mềm trọn gói bao gồm các phân hệ nghiệp vụ chính được quy định chi tiết tại Phụ lục 01 (Mẫu <code>TPL-SW-KTT-02</code>):</p>
  <ul class="dgm-clause-list">
    <li><strong>Phân hệ 1 — Quản lý Danh mục &amp; Sản phẩm (Product &amp; Catalog Management):</strong> Tạo/sửa/phân cấp danh mục sản phẩm, thiết lập bảng giá linh hoạt, quản lý đơn vị tính và quy đổi đa cấp, quản lý trạng thái vòng đời sản phẩm.</li>
    <li><strong>Phân hệ 2 — Quản lý Kho vận &amp; Tồn kho Thời gian thực (Warehouse &amp; Inventory Management):</strong> Quản lý đa kho/địa điểm lưu hàng, phiếu nhập kho, phiếu xuất kho, yêu cầu điều chuyển kho và truy vết lịch sử biến động tồn kho gắn liền với từng đơn hàng.</li>
    <li><strong>Phân hệ 3 — Quản lý Báo giá, Đơn hàng &amp; Khách hàng B2B/B2C (Order-to-Cash &amp; CRM):</strong> Quy trình lên báo giá nhanh, phê duyệt đơn hàng, theo dõi công nợ và lịch sử giao dịch khách hàng.</li>
    <li><strong>Phân hệ 4 — Quản lý Chính sách &amp; Tính toán Hoa hồng Tự động (Sales Commission Engine):</strong> Thiết lập công thức hoa hồng theo doanh số/nhóm hàng, kích hoạt/tạm ngưng chính sách hoa hồng, tự động tính toán và đối soát trạng thái hoa hồng cho đội ngũ bán hàng.</li>
    <li><strong>Phân hệ 5 — Báo cáo Quản trị Điều hành &amp; Phân quyền Bảo mật (Executive Dashboard &amp; RBAC):</strong> Phân quyền theo vai trò (Role-Based Access Control), nhật ký kiểm toán (Audit Log) và xuất báo cáo Excel/PDF.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 3. LỘ TRÌNH THỰC HIỆN 05 GIAI ĐOẠN (ÁNH XẠ THÔNG TƯ 13/2020/TT-BTTTT)</div>
  <table>
    <thead>
      <tr>
        <th style="width:16%;">Giai đoạn</th>
        <th style="width:24%;">Ánh xạ Công đoạn TT 13/2020</th>
        <th style="width:42%;">Nội dung Thực hiện &amp; Sản phẩm Bàn giao (Deliverables)</th>
        <th style="width:18%;">Thời lượng Dự kiến</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Giai đoạn 1</strong></td>
        <td>Công đoạn 1: Xác định yêu cầu</td>
        <td>Khảo sát quy trình nghiệp vụ của Bên A, chốt Tài liệu Đặc tả Yêu cầu Phần mềm (SRS) &amp; Wireframe/Prototype giao diện.</td>
        <td>05 ngày làm việc</td>
      </tr>
      <tr>
        <td><strong>Giai đoạn 2</strong></td>
        <td>Công đoạn 2 &amp; 3: Phân tích, thiết kế &amp; Lập trình lõi</td>
        <td>Thiết kế kiến trúc CSDL (ERD), API Spec và lập trình các phân hệ lõi (Danh mục, Kho, Đơn hàng, Hoa hồng).</td>
        <td>15 ngày làm việc</td>
      </tr>
      <tr>
        <td><strong>Giai đoạn 3</strong></td>
        <td>Công đoạn 4: Kiểm thử nội bộ (SIT)</td>
        <td>Kiểm thử tích hợp hệ thống (SIT), kiểm thử bảo mật &amp; hiệu năng, bàn giao môi trường Staging cho Bên A.</td>
        <td>05 ngày làm việc</td>
      </tr>
      <tr>
        <td><strong>Giai đoạn 4</strong></td>
        <td>Công đoạn 4 &amp; 6: Kiểm thử UAT &amp; Đào tạo</td>
        <td>Phối hợp cùng Bên A thực hiện kiểm thử chấp nhận người dùng (UAT), hiệu chỉnh lỗi và đào tạo quản trị viên/người dùng cuối.</td>
        <td>03 ngày làm việc</td>
      </tr>
      <tr>
        <td><strong>Giai đoạn 5</strong></td>
        <td>Công đoạn 5, 6 &amp; 7: Đóng gói, Cài đặt &amp; Phát hành Go-Live</td>
        <td>Đóng gói bản phát hành chính thức, cài đặt lên môi trường Production, bàn giao tài liệu &amp; ký Biên bản Nghiệm thu Tổng thể.</td>
        <td>02 ngày làm việc<br/>(Tổng: <strong>30 ngày LV</strong>)</td>
      </tr>
    </tbody>
  </table>

  <div class="dgm-article-heading">ĐIỀU 4. GIÁ TRỊ HỢP ĐỒNG TRỌN GÓI, ƯU ĐÃI THUẾ PHẦN MỀM &amp; TIẾN ĐỘ THANH TOÁN</div>
  <ul class="dgm-clause-list">
    <li><strong>4.1. Tổng giá trị Hợp đồng Trọn gói:</strong> <strong>{total_str}</strong> (<em>Bằng chữ: Hai trăm triệu đồng chẵn</em>).
      <ul>
        <li>Chi phí sản xuất, thiết kế và phát triển phần mềm trọn gói: <strong>{total_str}</strong>.</li>
        <li>Thuế suất thuế GTGT: <strong>Đối tượng không chịu thuế GTGT (KCT)</strong> theo Khoản 21 Điều 4 Thông tư 219/2013/TT-BTC (Phần mềm máy tính và dịch vụ phần mềm thuộc đối tượng không chịu thuế GTGT).</li>
      </ul>
    </li>
    <li><strong>4.2. Tiến độ Thanh toán theo Cột mốc Nghiệm thu (Milestone Payment Schedule):</strong> Hai Bên áp dụng một trong hai phương án lộ trình thanh toán dưới đây theo thỏa thuận tại Phụ lục:
      <ul>
        <li><strong>Phương án Chuẩn 03 Đợt (30% – 40% – 30%):</strong>
          <br/>• <em>Đợt 1 (Tạm ứng 30% — {m1_30}):</em> Thanh toán trong vòng 03 ngày làm việc kể từ ngày ký Hợp đồng.
          <br/>• <em>Đợt 2 (Nghiệm thu Kỹ thuật &amp; Bản dựng UAT 40% — {m2_40}):</em> Thanh toán trong vòng 05 ngày làm việc kể từ ngày Bên B bàn giao hệ thống lên môi trường UAT và ký xác nhận hoàn thành Giai đoạn 3.
          <br/>• <em>Đợt 3 (Nghiệm thu Bàn giao Tổng thể Go-Live 30% — {m3_30}):</em> Thanh toán trong vòng 05 ngày làm việc kể từ ngày hai Bên ký Biên bản Nghiệm thu Bàn giao Hệ thống Phần mềm Trọn gói (Mẫu <code>TPL-SW-KTT-03</code>) và Bên B phát hành Hóa đơn điện tử <code>1C26TAA</code>.
        </li>
        <li><strong>Phương án Nhanh Fast-Track 02 Đợt (65% – 35% cho dự án ≤ 30 ngày làm việc):</strong>
          <br/>• <em>Đợt 1 (65% — {opt_a_65}):</em> Thanh toán trong vòng 03 ngày làm việc kể từ ngày ký Hợp đồng.
          <br/>• <em>Đợt 2 (35% — {opt_a_35}):</em> Thanh toán trong vòng 05 ngày làm việc kể từ ngày ký Biên bản Nghiệm thu và Bàn giao tổng thể.
        </li>
      </ul>
    </li>
    <li><strong>4.3. Quy trình Đối soát Hóa đơn Nháp trước khi Ký số (SOP-DGM-08):</strong> Trước khi phát hành Hóa đơn Điện tử chính thức (Ký hiệu <code>1C26TAA</code>), Bên B gửi Bản Nháp Hóa đơn (Draft Invoice) để Kế toán Bên A xác nhận thông tin pháp nhân, mã số thuế và nội dung dịch vụ phần mềm không chịu thuế GTGT (KCT).</li>
    <li><strong>4.4. Thông tin Tài khoản Nhận Thanh toán:</strong> Chuyển khoản 100% bằng VNĐ vào tài khoản: <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ</strong> — Số tài khoản: <strong>1202703007</strong> tại <strong>Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank — PGD Trung Sơn / CN Tân Định)</strong>.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 5. TIÊU CHÍ NGHIỆM THU CHẤT LƯỢNG PHẦN MỀM (UAT QUALITY THRESHOLDS)</div>
  <p>Hệ thống phần mềm được coi là đạt tiêu chuẩn nghiệm thu UAT khi đáp ứng đồng thời ngưỡng chất lượng sau:</p>
  <ul class="dgm-clause-list">
    <li><strong>Lỗi Nghiêm trọng (Fatal Defects — Mức 1):</strong> <strong>0 lỗi</strong> (Lỗi gây dừng hệ thống bất thường, mất dữ liệu hoặc lộ lọt bảo mật — thời gian phản hồi xử lý ngay lập tức).</li>
    <li><strong>Lỗi Lớn (Major Defects — Mức 2):</strong> <strong>0 lỗi</strong> (Lỗi ngăn chặn một quy trình nghiệp vụ chính hoạt động mà không có giải pháp thay thế — thời gian xử lý trong vòng 24 giờ).</li>
    <li><strong>Lỗi Nhỏ (Minor Defects — Mức 3):</strong> <strong>Tối đa ≤ 05 lỗi</strong> không ảnh hưởng đến vận hành cốt lõi và có lịch cam kết khắc phục trong vòng 48 giờ.</li>
    <li><strong>Lỗi Giao diện / Tinh chỉnh (Cosmetic — Mức 4):</strong> Không chặn nghiệm thu UAT, được xử lý hoàn tất trong vòng &lt; 07 ngày.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 6. CƠ CHẾ NGHIỆM THU TỰ ĐỘNG BẢO VỆ TIẾN ĐỘ (DEEMED ACCEPTANCE GUARDRAIL)</div>
  <p>Sau khi Bên B bàn giao sản phẩm phần mềm của từng giai đoạn kèm Hồ sơ đề nghị nghiệm thu, Bên A có trách nhiệm kiểm tra và phản hồi danh sách lỗi (nếu có) bằng văn bản/email trong vòng <strong>05 (năm) ngày làm việc</strong>. Quá thời hạn 05 ngày làm việc nêu trên mà Bên A không có văn bản phản hồi danh sách lỗi thuộc phạm vi SRS hoặc đã đưa phần mềm vào sử dụng thực tế (Production), thì giai đoạn/sản phẩm phần mềm đó được <strong>mặc nhiên công nhận là đã nghiệm thu đạt yêu cầu (Deemed Accepted)</strong> và làm căn cứ pháp lý để Bên B xuất hóa đơn yêu cầu thanh toán.</p>

  <div class="dgm-article-heading">ĐIỀU 7. QUẢN LÝ YÊU CẦU THAY ĐỔI PHẠM VI (CHANGE REQUEST — CCB GOVERNANCE)</div>
  <ul class="dgm-clause-list">
    <li>Mọi yêu cầu thêm mới hoặc thay đổi tính năng ngoài phạm vi Tài liệu Đặc tả Kỹ thuật (SRS — Phụ lục 01) đã ký sẽ được lập thành <strong>Phiếu Yêu cầu Thay đổi (Change Request — CR)</strong> thông qua Ban Kiểm soát Thay đổi (CCB) của hai Bên.</li>
    <li><strong>Thay đổi nhỏ (Minor CR &lt; 04 giờ công):</strong> Bên B có thể xem xét hỗ trợ miễn phí theo thiện chí hợp tác.</li>
    <li><strong>Thay đổi lớn (Major CR ≥ 04 giờ công hoặc thay đổi cấu trúc CSDL/luồng nghiệp vụ):</strong> Trưởng nhóm dự án Bên B sẽ báo giá số ngày công (Man-days) và thời gian gia hạn tiến độ. Bên A xem xét phê duyệt bằng văn bản trong vòng 48 giờ trước khi Bên B triển khai.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 8. TRÁCH NHIỆM PHỐI HỢP CỦA HAI BÊN (24-HOUR FEEDBACK SLA)</div>
  <ul class="dgm-clause-list">
    <li><strong>Trách nhiệm Bên A:</strong> Cử Đầu mối Quản lý Dự án (Project Sponsor/PM) có thẩm quyền quyết định nghiệp vụ; cung cấp dữ liệu danh mục mẫu, môi trường nghiệm thu và phản hồi các câu hỏi làm rõ nghiệp vụ của Bên B trong vòng <strong>24 giờ làm việc</strong>. Mọi sự chậm trễ cung cấp thông tin/dữ liệu từ Bên A sẽ được cộng tương ứng vào thời hạn thực hiện Hợp đồng của Bên B.</li>
    <li><strong>Trách nhiệm Bên B:</strong> Bố trí đội ngũ Quản lý Dự án (PM), Kiến trúc sư Phần mềm, Kỹ sư Lập trình và Kiểm thử (QA) đủ năng lực; báo cáo tiến độ định kỳ hàng tuần và đảm bảo chất lượng phần mềm theo đúng tiêu chuẩn tại Điều 5.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 9. BÀN GIAO MÃ NGUỒN, TÀI LIỆU &amp; QUYỀN SỞ HỮU TRÍ TUỆ</div>
  <p>Sau khi Bên A hoàn tất thanh toán đủ <strong>100% tổng giá trị Hợp đồng</strong>, Bên B thực hiện bàn giao toàn bộ: (1) Bộ cài đặt / Mã nguồn phần mềm ứng dụng phát triển riêng cho Bên A; (2) Tài khoản Quản trị cao nhất (Super Admin); và (3) Tài liệu Hướng dẫn Sử dụng &amp; Quản trị Hệ thống. Trước thời điểm Bên A thanh toán đủ 100%, toàn bộ quyền sở hữu trí tuệ đối với phần mềm vẫn thuộc về Bên B.</p>

  <div class="dgm-article-heading">ĐIỀU 10. BẢO HÀNH PHẦN MỀM MIỄN PHÍ (90 NGÀY ĐẦU BẢO HÀNH KHẮC PHỤC LỖI CHUYÊN SÂU &amp; 12 THÁNG BẢO HÀNH TỔNG THỂ) &amp; DỊCH VỤ BẢO TRÌ MỞ RỘNG (AMC)</div>
  <ul class="dgm-clause-list">
    <li><strong>10.1. Thời hạn Bảo hành Miễn phí (90-Day Intensive Bug-Fix Warranty &amp; 12-Month Full Warranty):</strong> Cam kết <strong>90 ngày đầu bảo hành khắc phục lỗi khẩn cấp (90-day Bug-Fix Warranty)</strong> sau Go-Live và tổng thời hạn bảo hành miễn phí <strong>12 (mười hai) tháng</strong> kể từ ngày ký Biên bản Nghiệm thu Bàn giao Tổng thể (hoặc ngày nghiệm thu mặc nhiên tại Điều 6).</li>
    <li><strong>10.2. Phạm vi Bảo hành:</strong> Khắc phục miễn phí 100% các lỗi lập trình (Software Bugs) làm phần mềm hoạt động sai lệch so với Tài liệu Đặc tả SRS đã phê duyệt. Bảo hành không bao gồm các lỗi do người dùng thao tác sai, tự ý can thiệp cơ sở dữ liệu/mã nguồn, sự cố hạ tầng máy chủ của bên thứ ba hoặc yêu cầu phát triển tính năng mới.</li>
    <li><strong>10.3. Hợp đồng Bảo trì Hàng năm (AMC):</strong> Sau khi hết thời hạn bảo hành 12 tháng, hai Bên có thể ký Hợp đồng Dịch vụ Bảo trì &amp; Nâng cấp Phần mềm Hàng năm theo Mẫu <code>TPL-SW-KTT-04</code>.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 11. BẢO MẬT THÔNG TIN (ISO/IEC 27001) &amp; BẢO VỆ DỮ LIỆU (NGHỊ ĐỊNH 13/2023/NĐ-CP)</div>
  <p>Mỗi Bên cam kết giữ bí mật tuyệt đối toàn bộ dữ liệu kinh doanh, danh sách khách hàng, bảng giá, chính sách hoa hồng và bí quyết kỹ thuật của Bên kia theo tiêu chuẩn ISO/IEC 27001 và Nghị định 13/2023/NĐ-CP; hoàn trả hoặc hủy an toàn dữ liệu thử nghiệm ngay sau khi kết thúc dự án.</p>

  <div class="dgm-article-heading">ĐIỀU 12–14. PHẠT VI PHẠM, BẤT KHẢ KHÁNG, GIẢI QUYẾT TRANH CHẤP &amp; HIỆU LỰC THANH LÝ TỰ ĐỘNG</div>
  <p>Hợp đồng này có hiệu lực kể từ ngày ký và <strong>tự động có giá trị như Biên bản Thanh lý Hợp đồng</strong> sau khi hai Bên đã hoàn thành đầy đủ nghĩa vụ bàn giao, nghiệm thu, thanh toán 100% giá trị Hợp đồng và hết thời hạn bảo hành mà không có tranh chấp nào phát sinh.</p>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <span>{p_rep_title}</span><br/><br/><br/>
      <strong>{p_rep}</strong><br/>
      <em>(Ký tên, đóng dấu pháp nhân / Chữ ký số)</em>
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ)</strong><br/>
      <span>Chủ tịch HĐQT kiêm Giám đốc</span><br/><br/><br/>
      <strong>LÊ XUÂN HOÀNG</strong><br/>
      <em>(Đã ký số HSM Viettel-CA — MST 0317958465)</em>
    </div>
  </div>
</div>"""

    doc_ktt_01 = wrap_dgm_branded_html_document(
        body_ktt_01,
        title=f"TPL-SW-KTT-01 Hợp đồng Dịch vụ Phần mềm Trọn gói — {prof.get('partner_name')}",
        doc_code="TPL-SW-KTT-01",
        sop_ref="SOP-DGM-09",
        classification="B2B TURNKEY SOFTWARE CONTRACT (TT 13/2020 TAX INCENTIVE)",
        include_header=True,
    )

    # -------------------------------------------------------------------------
    # TPL-SW-KTT-02: Phụ lục 01 — Đặc tả Kỹ thuật (SRS), Ma trận Chức năng & Tiêu chí UAT Trọn gói
    # -------------------------------------------------------------------------
    body_ktt_02 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc</div>
  </div>

  <div class="dgm-contract-title">
    <h1>PHỤ LỤC 01: ĐẶC TẢ KỸ THUẬT PHẦN MỀM (SRS), MA TRẬN CHỨC NĂNG<br/>&amp; TIÊU CHÍ NGHIỆM THU UAT TRỌN GÓI</h1>
    <div class="contract-sub">Số Phụ lục: <strong>{appendix_no}</strong> • Đính kèm Hợp đồng Phần mềm Trọn gói số: <strong>{contract_no}</strong></div>
  </div>

  <table>
    <tr><th style="width:28%;">Khách hàng (Bên A)</th><td><strong>{p_name}</strong> — MST: <strong>{p_vat}</strong> ({p_code})</td></tr>
    <tr><th>Đơn vị Phát triển (Bên B)</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: <strong>0317958465</strong></td></tr>
    <tr><th>Hệ thống Phần mềm</th><td><strong>{project_name}</strong></td></tr>
  </table>

  <div class="dgm-article-heading">1. MA TRẬN CHỨC NĂNG PHẦN MỀM TRỌN GÓI (FUNCTIONAL SCOPE MATRIX)</div>
  <table>
    <thead>
      <tr>
        <th style="width:6%;">STT</th>
        <th style="width:24%;">Phân hệ Chức năng</th>
        <th style="width:48%;">Mô tả Chi tiết Tính năng Nghiệp vụ (Functional Requirements)</th>
        <th style="width:22%;">Công đoạn TT 13/2020 &amp; Kịch bản UAT</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td><strong>Quản lý Danh mục &amp; Sản phẩm</strong></td>
        <td>
          • Tạo mới, chỉnh sửa, phân nhóm cây danh mục sản phẩm;<br/>
          • Hiển thị, tìm kiếm, lọc và phân trang sản phẩm;<br/>
          • Thiết lập bảng giá bán buôn/bán lẻ, quản lý đơn vị tính &amp; quy đổi;<br/>
          • Quản lý trạng thái sản phẩm (Đang kinh doanh / Ngừng kinh doanh).
        </td>
        <td>Công đoạn 1, 2, 3, 4<br/><code>UAT-CAT-01..08</code> (Bắt buộc Pass 100%)</td>
      </tr>
      <tr>
        <td>2</td>
        <td><strong>Quản lý Kho vận &amp; Xuất Nhập Tồn</strong></td>
        <td>
          • Tạo mới kho, chỉnh sửa thông tin kho và địa điểm lưu hàng;<br/>
          • Ghi nhận phiếu nhập kho, phiếu xuất kho theo số lượng thực tế;<br/>
          • Tạo yêu cầu xuất kho gắn với đơn hàng và xem lịch sử biến động kho.
        </td>
        <td>Công đoạn 1, 2, 3, 4<br/><code>UAT-INV-01..06</code> (Bắt buộc Pass 100%)</td>
      </tr>
      <tr>
        <td>3</td>
        <td><strong>Quản lý Đơn hàng &amp; Lịch sử Giao dịch</strong></td>
        <td>
          • Khởi tạo báo giá/đơn đặt hàng, kiểm tra tồn kho khả dụng;<br/>
          • Theo dõi trạng thái xử lý đơn hàng và lịch sử giao dịch khách hàng;<br/>
          • Xuất dữ liệu đối soát kế toán.
        </td>
        <td>Công đoạn 1, 2, 3, 4<br/><code>UAT-ORD-01..06</code> (Bắt buộc Pass 100%)</td>
      </tr>
      <tr>
        <td>4</td>
        <td><strong>Quản lý Chính sách &amp; Hoa hồng Bán hàng</strong></td>
        <td>
          • Thiết lập quy tắc tính hoa hồng cho nhân viên/đại lý bán hàng;<br/>
          • Kích hoạt hoặc ngừng áp dụng chính sách hoa hồng theo kỳ;<br/>
          • Tự động tính toán và quản lý trạng thái phê duyệt hoa hồng.
        </td>
        <td>Công đoạn 1, 2, 3, 4<br/><code>UAT-COM-01..05</code> (Bắt buộc Pass 100%)</td>
      </tr>
    </tbody>
  </table>

  <div class="dgm-article-heading">2. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL &amp; SECURITY REQUIREMENTS)</div>
  <ul class="dgm-clause-list">
    <li><strong>Hiệu năng &amp; Chịu tải:</strong> Thời gian phản hồi trung bình của các trang danh sách và tra cứu &le; 1.5 giây ở mức tải tiêu chuẩn; hỗ trợ mở rộng linh hoạt trên hạ tầng Container/Cloud.</li>
    <li><strong>An toàn Thông tin:</strong> Mã hóa mật khẩu chuẩn Argon2/Bcrypt, phân quyền RBAC theo phòng ban, kết nối HTTPS/TLS 1.3 và tự động sao lưu cơ sở dữ liệu hàng ngày.</li>
  </ul>

  <div class="dgm-article-heading">3. BIỂU PHÍ ƯỚC LƯỢNG YÊU CẦU THAY ĐỔI NGOÀI PHẠM VI (CHANGE REQUEST RATE CARD) &amp; CHUẨN THUẾ PHẦN MỀM</div>
  <p>Mọi tính năng phát sinh ngoài danh mục tại Mục 1 được tính theo đơn giá nhân công kỹ sư phần mềm chuẩn là <strong>2.800.000 VNĐ/Man-day (350.000 VNĐ/giờ)</strong>, đáp ứng quy trình 7 công đoạn sản xuất phần mềm theo <strong>Thông tư 13/2020/TT-BTTTT</strong>, <strong>Nghị định 71/2007/NĐ-CP</strong> và Khoản 21 Điều 4 <strong>Thông tư 219/2013/TT-BTC</strong>, và chỉ thực hiện sau khi có xác nhận phê duyệt CR bằng văn bản của Bên A.</p>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <strong>{p_rep}</strong> — {p_rep_title}
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (DIGIMATE JSC)</strong><br/>
      <strong>LÊ XUÂN HOÀNG</strong> — Chủ tịch HĐQT kiêm Giám đốc
    </div>
  </div>
</div>"""

    doc_ktt_02 = wrap_dgm_branded_html_document(
        body_ktt_02,
        title=f"TPL-SW-KTT-02 Phụ lục Đặc tả Kỹ thuật SRS & Tiêu chí UAT Trọn gói — {prof.get('partner_name')}",
        doc_code="TPL-SW-KTT-02",
        sop_ref="SOP-DGM-09",
        classification="B2B TURNKEY SRS & UAT SPECIFICATION",
        include_header=True,
    )

    # -------------------------------------------------------------------------
    # TPL-SW-KTT-03: Biên bản Nghiệm thu Bàn giao Hệ thống Phần mềm Trọn gói & Hồ sơ 7 Công đoạn TT 13/2020
    # -------------------------------------------------------------------------
    body_ktt_03 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc</div>
  </div>

  <div class="dgm-contract-title">
    <h1>BIÊN BẢN NGHIỆM THU BÀN GIAO HỆ THỐNG PHẦN MỀM TRỌN GÓI<br/>&amp; XÁC NHẬN HOÀN THÀNH 07 CÔNG ĐOẠN THÔNG TƯ 13/2020/TT-BTTTT</h1>
    <div class="contract-sub">(FINAL TURNKEY SOFTWARE ACCEPTANCE, HANDOVER &amp; CIRCULAR 13/2020 COMPLIANCE CERTIFICATE)<br/>
    Căn cứ Hợp đồng số: <strong>{contract_no}</strong> • Phụ lục SRS số: <strong>{appendix_no}</strong></div>
  </div>

  <table>
    <tr><th style="width:28%;">Bên A (Đơn vị Nghiệm thu &amp; Nhận Bàn giao)</th><td><strong>{p_name}</strong> — MST: <strong>{p_vat}</strong></td></tr>
    <tr><th>Bên B (Đơn vị Sản xuất &amp; Bàn giao Phần mềm)</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: <strong>0317958465</strong></td></tr>
    <tr><th>Tên Hệ thống Phần mềm Bàn giao</th><td><strong>{project_name}</strong></td></tr>
  </table>

  <div class="dgm-article-heading">I. KẾT QUẢ NGHIỆM THU 07 CÔNG ĐOẠN SẢN XUẤT PHẦN MỀM (THÔNG TƯ 13/2020/TT-BTTTT)</div>
  <table>
    <thead>
      <tr>
        <th style="width:22%;">Công đoạn TT 13/2020</th>
        <th style="width:43%;">Hồ sơ &amp; Sản phẩm Phần mềm Đã Bàn giao</th>
        <th style="width:20%;">Kết quả Kiểm tra UAT</th>
        <th style="width:15%;">Kết luận</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>1. Xác định yêu cầu</strong></td>
        <td>Tài liệu Đặc tả Yêu cầu Phần mềm (SRS) &amp; Prototype giao diện đã ký duyệt.</td>
        <td>Đúng 100% phạm vi Hợp đồng</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
      <tr>
        <td><strong>2. Phân tích &amp; Thiết kế</strong></td>
        <td>Tài liệu Thiết kế Kiến trúc Hệ thống, Sơ đồ CSDL (ERD) &amp; Đặc tả API.</td>
        <td>Đầy đủ tài liệu kỹ thuật</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
      <tr>
        <td><strong>3. Lập trình mã lệnh</strong></td>
        <td>Bộ mã nguồn hoàn chỉnh của 04 phân hệ (Danh mục, Kho vận, Đơn hàng, Hoa hồng).</td>
        <td>Hoàn thành 100% tính năng</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
      <tr>
        <td><strong>4. Kiểm thử phần mềm</strong></td>
        <td>Biên bản Kiểm thử Chấp nhận Người dùng (UAT Test Report): 25/25 kịch bản Pass.</td>
        <td>Fatal = 0, Major = 0</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
      <tr>
        <td><strong>5. Hoàn thiện, đóng gói</strong></td>
        <td>Gói cài đặt Production Release &amp; Tài liệu Hướng dẫn Sử dụng / Quản trị.</td>
        <td>Đã đóng gói chuẩn</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
      <tr>
        <td><strong>6. Cài đặt, chuyển giao</strong></td>
        <td>Đã cài đặt lên máy chủ Production, bàn giao tài khoản Super Admin &amp; đào tạo nhân sự Bên A.</td>
        <td>Đã hoàn tất chuyển giao</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
      <tr>
        <td><strong>7. Phát hành sản phẩm</strong></td>
        <td>Hệ thống phần mềm chính thức vận hành thực tế (Go-Live) phục vụ hoạt động kinh doanh của Bên A.</td>
        <td>Vận hành ổn định</td>
        <td><strong>ĐẠT</strong></td>
      </tr>
    </tbody>
  </table>

  <div class="dgm-article-heading">II. XÁC NHẬN GIÁ TRỊ QUYẾT TOÁN, PHÁT HÀNH HÓA ĐƠN 1C26TAA &amp; BẮT ĐẦU BẢO HÀNH 12 THÁNG</div>
  <ul class="dgm-clause-list">
    <li><strong>Tổng giá trị Hợp đồng Phần mềm Trọn gói nghiệm thu:</strong> <strong>{total_str}</strong> (<em>Đối tượng không chịu thuế GTGT — KCT theo <strong>Thông tư 13/2020/TT-BTTTT</strong>, <strong>Nghị định 71/2007/NĐ-CP</strong> và Khoản 21 Điều 4 <strong>Thông tư 219/2013/TT-BTC</strong></em>).</li>
    <li><strong>Xác nhận xuất Hóa đơn Điện tử:</strong> Bên A xác nhận đồng ý thông tin trên Bản Nháp Hóa đơn để Bên B phát hành <strong>Hóa đơn GTGT Điện tử chính thức (Ký hiệu 1C26TAA)</strong> và thanh toán toàn bộ giá trị còn lại vào tài khoản Vietcombank số <strong>1202703007</strong> của CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ trong vòng 05 ngày làm việc.</li>
    <li><strong>Kích hoạt Bảo hành Phần mềm:</strong> Thời hạn bảo hành miễn phí 12 tháng chính thức bắt đầu kể từ ngày ký Biên bản này.</li>
  </ul>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <strong>{p_rep}</strong> — {p_rep_title}
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (DIGIMATE JSC)</strong><br/>
      <strong>LÊ XUÂN HOÀNG</strong> — Chủ tịch HĐQT kiêm Giám đốc
    </div>
  </div>
</div>"""

    doc_ktt_03 = wrap_dgm_branded_html_document(
        body_ktt_03,
        title=f"TPL-SW-KTT-03 Biên bản Nghiệm thu Bàn giao Phần mềm Trọn gói & Hồ sơ TT 13/2020 — {prof.get('partner_name')}",
        doc_code="TPL-SW-KTT-03",
        sop_ref="SOP-DGM-09",
        classification="B2B TURNKEY ACCEPTANCE & HANDOVER CERTIFICATE",
        include_header=True,
    )

    # -------------------------------------------------------------------------
    # TPL-SW-KTT-04: Hợp đồng Dịch vụ Bảo trì, Nâng cấp & Hỗ trợ Kỹ thuật Phần mềm Hàng năm (AMC)
    # -------------------------------------------------------------------------
    body_ktt_04 = f"""{_CONTRACT_CSS}
<div class="dgm-contract-wrap">
  <div class="dgm-national-motto">
    <div class="motto-vn">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div class="motto-sub">Độc lập – Tự do – Hạnh phúc</div>
  </div>

  <div class="dgm-contract-title">
    <h1>HỢP ĐỒNG DỊCH VỤ BẢO TRÌ, NÂNG CẤP &amp; HỖ TRỢ KỸ THUẬT PHẦN MỀM HÀNG NĂM</h1>
    <div class="contract-sub">(ANNUAL SOFTWARE MAINTENANCE, UPGRADE &amp; SLA SUPPORT CONTRACT — AMC)<br/>
    Áp dụng sau thời hạn bảo hành cho Hệ thống Phần mềm Trọn gói của <strong>{p_name}</strong></div>
  </div>

  <div class="dgm-article-heading">ĐIỀU 1. PHẠM VI DỊCH VỤ PHẦN MỀM BẢO TRÌ &amp; QUẢN TRỊ ĐỊNH KỲ (NGHỊ ĐỊNH 71/2007/NĐ-CP)</div>
  <ul class="dgm-clause-list">
    <li><strong>1.1. Bảo trì Thích nghi &amp; Bảo mật (Preventive &amp; Security Maintenance):</strong> Cập nhật bản vá bảo mật định kỳ hàng quý, tối ưu hóa chỉ mục cơ sở dữ liệu (Database Indexing &amp; Vacuum), kiểm tra tính toàn vẹn của bản sao lưu (Backup Restoration Drill).</li>
    <li><strong>1.2. Hỗ trợ Kỹ thuật &amp; Xử lý Sự cố theo Cam kết SLA:</strong>
      <ul>
        <li><strong>Sự cố Mức 1 (Khẩn cấp — Hệ thống ngưng hoạt động):</strong> Phản hồi trong vòng <strong>30 phút</strong>, khắc phục/khôi phục dịch vụ trong vòng <strong>&le; 02 giờ</strong>.</li>
        <li><strong>Sự cố Mức 2 (Cao — Ảnh hưởng phân hệ nghiệp vụ chính):</strong> Phản hồi trong vòng <strong>01 giờ</strong>, khắc phục trong vòng <strong>&le; 04 giờ làm việc</strong>.</li>
        <li><strong>Sự cố Mức 3 (Trung bình/Thấp — Hỗ trợ tra cứu &amp; tinh chỉnh nhỏ):</strong> Phản hồi trong vòng <strong>04 giờ</strong>, xử lý trong vòng <strong>&le; 24 giờ làm việc</strong>.</li>
      </ul>
    </li>
    <li><strong>1.3. Quỹ Giờ Nâng cấp Tính năng Nhỏ Đi kèm:</strong> Bao gồm miễn phí <strong>16 giờ công kỹ sư/quý</strong> để tinh chỉnh mẫu báo cáo, biểu mẫu in ấn hoặc tham số nghiệp vụ cho Bên A.</li>
  </ul>

  <div class="dgm-article-heading">ĐIỀU 2. PHÍ DỊCH VỤ BẢO TRÌ PHẦN MỀM HÀNG NĂM &amp; CHÍNH SÁCH THUẾ</div>
  <p>Phí dịch vụ bảo trì phần mềm trọn gói hàng năm bằng <strong>15% giá trị phần mềm gốc ({amc_annual}/năm)</strong>, thuộc danh mục dịch vụ phần mềm và phát hành bản nâng cấp công đoạn phần mềm theo <strong>Thông tư 13/2020/TT-BTTTT</strong>, Khoản 3 Điều 9 <strong>Nghị định 71/2007/NĐ-CP</strong> và Khoản 21 Điều 4 <strong>Thông tư 219/2013/TT-BTC</strong>, thanh toán định kỳ 06 tháng hoặc 12 tháng/lần qua tài khoản Vietcombank số <strong>1202703007</strong> của CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ.</p>

  <div class="dgm-sig-grid">
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN A ({p_name})</strong><br/>
      <strong>{p_rep}</strong> — {p_rep_title}
    </div>
    <div class="dgm-sig-box">
      <strong>ĐẠI DIỆN BÊN B (DIGIMATE JSC)</strong><br/>
      <strong>LÊ XUÂN HOÀNG</strong> — Chủ tịch HĐQT kiêm Giám đốc
    </div>
  </div>
</div>"""

    doc_ktt_04 = wrap_dgm_branded_html_document(
        body_ktt_04,
        title=f"TPL-SW-KTT-04 Hợp đồng Bảo trì & Nâng cấp Phần mềm Hàng năm (AMC) — {prof.get('partner_name')}",
        doc_code="TPL-SW-KTT-04",
        sop_ref="SOP-DGM-09",
        classification="B2B SOFTWARE AMC & SLA CONTRACT",
        include_header=True,
    )

    return [
        {
            'code': 'TPL-SW-KTT-01',
            'tpl_code': 'TPL-SW-KTT-01',
            'contract_group': 'ktt_turnkey',
            'filename': f"01_HD_Dich_Vu_Phan_Mem_Tron_Goi_KTT_{safe_code}.html",
            'name': f"[TPL-SW-KTT-01] Hợp đồng Thiết kế, Xây dựng & Triển khai Phần mềm Trọn gói (Chuẩn KTT Khang Trường Thịnh • TT 13/2020) — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-KTT-01] Hợp đồng Thiết kế, Xây dựng & Triển khai Phần mềm Trọn gói (Chuẩn KTT Khang Trường Thịnh • TT 13/2020) — {prof.get('partner_name')}",
            'html': doc_ktt_01,
        },
        {
            'code': 'TPL-SW-KTT-02',
            'tpl_code': 'TPL-SW-KTT-02',
            'contract_group': 'ktt_turnkey',
            'filename': f"02_Phu_Luc_Dac_Ta_Ky_Thuat_SRS_UAT_KTT_{safe_code}.html",
            'name': f"[TPL-SW-KTT-02] Phụ lục 01: Đặc tả Kỹ thuật (SRS), Ma trận Chức năng & Tiêu chí Nghiệm thu UAT Trọn gói — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-KTT-02] Phụ lục 01: Đặc tả Kỹ thuật (SRS), Ma trận Chức năng & Tiêu chí Nghiệm thu UAT Trọn gói — {prof.get('partner_name')}",
            'html': doc_ktt_02,
        },
        {
            'code': 'TPL-SW-KTT-03',
            'tpl_code': 'TPL-SW-KTT-03',
            'contract_group': 'ktt_turnkey',
            'filename': f"03_Bien_Ban_Nghiem_Thu_Ban_Giao_Phan_Mem_Tron_Goi_KTT_{safe_code}.html",
            'name': f"[TPL-SW-KTT-03] Biên bản Nghiệm thu Bàn giao Hệ thống Phần mềm Trọn gói & Hồ sơ 7 Công đoạn TT 13/2020/TT-BTTTT — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-KTT-03] Biên bản Nghiệm thu Bàn giao Hệ thống Phần mềm Trọn gói & Hồ sơ 7 Công đoạn TT 13/2020/TT-BTTTT — {prof.get('partner_name')}",
            'html': doc_ktt_03,
        },
        {
            'code': 'TPL-SW-KTT-04',
            'tpl_code': 'TPL-SW-KTT-04',
            'contract_group': 'ktt_turnkey',
            'filename': f"04_HD_Bao_Tri_Nang_Cap_Phan_Mem_AMC_KTT_{safe_code}.html",
            'name': f"[TPL-SW-KTT-04] Hợp đồng Dịch vụ Bảo trì, Nâng cấp & Hỗ trợ Kỹ thuật Phần mềm Hàng năm (AMC & SLA) — {prof.get('partner_name')}",
            'doc_name': f"[TPL-SW-KTT-04] Hợp đồng Dịch vụ Bảo trì, Nâng cấp & Hỗ trợ Kỹ thuật Phần mềm Hàng năm (AMC & SLA) — {prof.get('partner_name')}",
            'html': doc_ktt_04,
        },
    ]


def render_all_master_software_contract_templates(mti_partner=None, ktt_partner=None):
    """Returns all 8 Master Software Contract Templates (`TPL-SW-MTI-01..04` & `TPL-SW-KTT-01..04`)."""
    suites = []
    suites.extend(render_mti_codev_contract_suite(mti_partner or 'MTI'))
    suites.extend(render_ktt_turnkey_contract_suite(ktt_partner or 'KTT'))
    return suites


def _ensure_doc_and_ancestors_active(env, doc_records):
    """Unarchives a `documents.document` recordset and all its ancestor folders via SQL
    so `documents.document.write` never raises UserError on archived parent chains.
    """
    if not doc_records:
        return
    all_ids = set()
    seen = set()
    queue = list(doc_records.with_context(active_test=False) if hasattr(doc_records, 'with_context') else doc_records)
    while queue:
        rec = queue.pop(0)
        rec_id = getattr(rec, 'id', None)
        if not rec_id or not isinstance(rec_id, int) or rec_id in seen:
            continue
        seen.add(rec_id)
        all_ids.add(rec_id)
        parent = getattr(rec, 'folder_id', None)
        if parent and getattr(parent, 'id', None) and parent.id not in seen:
            queue.append(parent.with_context(active_test=False) if hasattr(parent, 'with_context') else parent)
    if all_ids and hasattr(env, 'cr') and env.cr and hasattr(env.cr, 'execute'):
        env.cr.execute(
            "UPDATE documents_document SET active = TRUE, owner_id = NULL, access_internal = 'edit' WHERE id = ANY(%s)",
            (list(all_ids),),
        )
        if hasattr(env, 'invalidate_all'):
            env.invalidate_all()


# =============================================================================
# Odoo Model Extension on `res.partner` (`SOP-DGM-09`)
# =============================================================================
if not __name__.startswith('odoo.addons.'):
    __name__ = 'odoo.addons.insilos_al2c.models.dgm_software_contract_templates'


class ResPartnerSoftwareContracts(models.Model):
    _inherit = 'res.partner'

    dgm_software_contract_model = fields.Selection(
        selection=[
            (
                'mti_codev',
                'Nhóm MTI/AIfin — Cử Nhân sự Tham gia Cùng Phát triển Dự án Phần mềm (Chuẩn Ưu đãi Phần mềm TT 13/2020)',
            ),
            (
                'ktt_turnkey',
                'Nhóm KTT Khang Trường Thịnh — Dịch vụ Thiết kế & Xây dựng Phần mềm Trọn gói (Turnkey Software Package)',
            ),
            (
                'both',
                'Kết hợp Cả 2 Mô hình (Nhân sự Cùng Phát triển Dự án + Dịch vụ Phần mềm Trọn gói)',
            ),
        ],
        string='Mô hình Hợp đồng Phần mềm (SOP-DGM-09)',
        default='mti_codev',
        tracking=True,
    )

    dgm_software_contract_doc_ids = fields.Many2many(
        'documents.document',
        'dgm_partner_sw_contract_doc_rel',
        'partner_id',
        'document_id',
        string='Bộ Hợp đồng Phần mềm Chuẩn (SOP-DGM-09)',
        copy=False,
    )

    dgm_software_contract_doc_count = fields.Integer(
        string='Số Mẫu Hợp đồng Phần mềm',
        compute='_compute_dgm_software_contract_docs',
        store=True,
    )

    @api.depends('dgm_software_contract_doc_ids', 'dgm_software_contract_doc_ids.active')
    def _compute_dgm_software_contract_docs(self):
        for partner in self:
            active_docs = partner.dgm_software_contract_doc_ids.filtered(lambda d: d.active and d.type != 'folder')
            partner.dgm_software_contract_doc_count = len(active_docs)

    def _render_mti_codev_software_templates(self):
        """Renders the 4 MTI/AIfin Software Co-Development Contract Templates (`TPL-SW-MTI-01..04`)."""
        target = self[:1] if self else 'MTI'
        return render_mti_codev_contract_suite(target)

    def _render_ktt_turnkey_software_templates(self):
        """Renders the 4 KTT Khang Trường Thịnh Turnkey Software Contract Templates (`TPL-SW-KTT-01..04`)."""
        target = self[:1] if self else 'KTT'
        return render_ktt_turnkey_contract_suite(target)

    @api.model
    def render_all_master_software_contract_templates(self, mti_partner=None, ktt_partner=None):
        """Renders all 8 Master Software Contract Templates (`TPL-SW-MTI-01..04` & `TPL-SW-KTT-01..04`)."""
        return render_all_master_software_contract_templates(mti_partner=mti_partner, ktt_partner=ktt_partner)

    def _get_or_create_dgm_software_contract_folder(self, sub_group_name=None):
        """Resolves or creates the partner's dedicated Software Contract folder under
        `03. Hợp đồng & Thương mại (Commercial & Contracts)` with `owner_id = False` and `access_internal = 'edit'`.
        """
        self.ensure_one()
        Doc = self.env['documents.document'].sudo()
        comm_root = self.env.ref('insilos_al2c.folder_dgm_03_contracts', raise_if_not_found=False)
        if not comm_root or not comm_root.exists():
            comm_root = Doc.with_context(active_test=False).search([
                ('type', '=', 'folder'),
                ('name', 'ilike', '03. Hợp đồng'),
            ], order='id asc', limit=1)
        if not comm_root:
            comm_root = Doc.create({
                'name': '03. Hợp đồng & Thương mại (Commercial & Contracts)',
                'type': 'folder',
                'access_internal': 'edit',
                'access_via_link': 'none',
                'owner_id': False,
                'company_id': False,
                'active': True,
            })
        else:
            _ensure_doc_and_ancestors_active(self.env, comm_root)
            comm_root.write({
                'owner_id': False,
                'access_internal': 'edit',
            })

        group_title = sub_group_name or (
            'Hợp đồng Dịch vụ Phần mềm Trọn gói (Nhóm KTT Khang Trường Thịnh — Turnkey)'
            if self.dgm_software_contract_model == 'ktt_turnkey'
            else 'Hợp đồng Cử Nhân sự Cùng Phát triển Dự án Phần mềm (Nhóm MTI & AIfin — TT 13/2020)'
        )
        group_folder = Doc.with_context(active_test=False).search([
            ('type', '=', 'folder'),
            ('folder_id', '=', comm_root.id),
            ('name', '=', group_title),
        ], order='id asc', limit=1)
        if not group_folder:
            group_folder = Doc.create({
                'name': group_title,
                'type': 'folder',
                'folder_id': comm_root.id,
                'access_internal': 'edit',
                'access_via_link': 'none',
                'owner_id': False,
                'company_id': False,
                'active': True,
            })
        else:
            _ensure_doc_and_ancestors_active(self.env, group_folder)
            group_folder.write({
                'folder_id': comm_root.id,
                'owner_id': False,
                'access_internal': 'edit',
            })

        code_label = self.dgm_partner_code or self.dgm_provisional_code or f"TMP-DGM-{self.id:04d}"
        partner_folder_name = f"{code_label} — {self.name}"
        partner_folder = Doc.with_context(active_test=False).search([
            ('type', '=', 'folder'),
            ('folder_id', '=', group_folder.id),
            ('partner_id', '=', self.id),
        ], order='id asc', limit=1)
        if not partner_folder:
            partner_folder = Doc.create({
                'name': partner_folder_name,
                'type': 'folder',
                'folder_id': group_folder.id,
                'partner_id': self.id,
                'access_internal': 'edit',
                'access_via_link': 'none',
                'owner_id': False,
                'company_id': False,
                'active': True,
            })
        else:
            _ensure_doc_and_ancestors_active(self.env, partner_folder)
            partner_folder.write({
                'name': partner_folder_name,
                'folder_id': group_folder.id,
                'partner_id': self.id,
                'owner_id': False,
                'access_internal': 'edit',
            })

        return partner_folder

    def _get_or_create_dgm_sw_contract_folder(self, sub_group_name=None):
        """Alias for `_get_or_create_dgm_software_contract_folder`."""
        return self._get_or_create_dgm_software_contract_folder(sub_group_name=sub_group_name)

    def _upsert_sw_contract_doc_in_folder(self, folder_id, doc_name, html_body, filename=None, tpl_code=None):
        """Upserts an HTML software contract document in `documents.document` ensuring `owner_id = False`
        and `access_internal = 'edit'` (Rule 6).
        """
        self.ensure_one()
        Doc = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo().with_context(no_document=True)
        tag_comm = self.env.ref('insilos_al2c.tag_dgm_contract_comm', raise_if_not_found=False)

        raw_bytes = html_body.encode('utf-8') if isinstance(html_body, str) else html_body
        b64_datas = base64.b64encode(raw_bytes)
        fname = filename or f"{re.sub(r'[^A-Za-z0-9_-]+', '_', tpl_code or 'SW_CONTRACT')}.html"
        m_code = re.search(r'\[(TPL-SW-[A-Z0-9-]+)\]', doc_name or '')
        prefix_marker = f"[{tpl_code}]" if tpl_code else (f"[{m_code.group(1)}]" if m_code else None)

        existing_doc = Doc.browse()
        if prefix_marker:
            existing_doc = Doc.with_context(active_test=False).search([
                ('folder_id', '=', folder_id),
                ('name', 'ilike', prefix_marker),
                ('type', '!=', 'folder'),
            ], order='id asc', limit=1)
        if not existing_doc:
            existing_doc = Doc.with_context(active_test=False).search([
                ('folder_id', '=', folder_id),
                ('name', '=', doc_name),
                ('type', '!=', 'folder'),
            ], order='id asc', limit=1)

        if existing_doc:
            _ensure_doc_and_ancestors_active(self.env, existing_doc)
            if existing_doc.attachment_id:
                existing_doc.attachment_id.with_context(no_document=True).write({
                    'name': fname,
                    'datas': b64_datas,
                    'mimetype': 'text/html',
                })
            else:
                att = Attachment.create({
                    'name': fname,
                    'res_model': 'documents.document',
                    'res_id': existing_doc.id,
                    'type': 'binary',
                    'datas': b64_datas,
                    'mimetype': 'text/html',
                })
                existing_doc.write({'attachment_id': att.id})
            existing_doc.write({
                'name': doc_name,
                'folder_id': folder_id,
                'partner_id': self.id,
                'access_internal': 'edit',
                'owner_id': False,
            })
            return existing_doc

        att = Attachment.create({
            'name': fname,
            'res_model': 'res.partner',
            'res_id': self.id,
            'type': 'binary',
            'datas': b64_datas,
            'mimetype': 'text/html',
        })
        create_vals = {
            'name': doc_name,
            'folder_id': folder_id,
            'attachment_id': att.id,
            'partner_id': self.id,
            'type': 'binary',
            'access_internal': 'edit',
            'access_via_link': 'view',
            'owner_id': False,
            'company_id': False,
            'active': True,
        }
        if tag_comm and tag_comm.exists():
            create_vals['tag_ids'] = [(4, tag_comm.id)]
        doc_rec = Doc.create(create_vals)
        att.with_context(no_document=True).write({'res_model': 'documents.document', 'res_id': doc_rec.id})
        return doc_rec

    def action_generate_software_contract_templates(self, model_type=None):
        """Idempotently generates the Group A (`TPL-SW-MTI-01..04`) and/or Group B (`TPL-SW-KTT-01..04`)
        software contract suites for the partner and stores them in Odoo Documents.
        """
        for partner in self:
            if not (partner.id and isinstance(partner.id, int) and partner.id > 0):
                raise UserError(_("Invalid partner ID for software contract generation."))

            mode = model_type or partner.dgm_software_contract_model or 'mti_codev'
            if not model_type:
                name_upper = (partner.name or '').upper()
                if 'KHANG TRƯỜNG THỊNH' in name_upper or 'KHANG TRUONG THINH' in name_upper or 'KTT' in name_upper:
                    mode = 'ktt_turnkey'
                elif 'AIFIN' in name_upper and mode == 'mti_codev':
                    mode = 'both'

            suites = []
            if mode in ('mti_codev', 'both'):
                suites.extend(render_mti_codev_contract_suite(partner))
            if mode in ('ktt_turnkey', 'both'):
                suites.extend(render_ktt_turnkey_contract_suite(partner))

            doc_ids = []
            for tpl in suites:
                sub_group = (
                    'Hợp đồng Dịch vụ Phần mềm Trọn gói (Nhóm KTT Khang Trường Thịnh — Turnkey)'
                    if tpl['contract_group'] == 'ktt_turnkey'
                    else 'Hợp đồng Cử Nhân sự Cùng Phát triển Dự án Phần mềm (Nhóm MTI & AIfin — TT 13/2020)'
                )
                folder = partner._get_or_create_dgm_software_contract_folder(sub_group_name=sub_group)
                doc_rec = partner._upsert_sw_contract_doc_in_folder(
                    folder_id=folder.id,
                    doc_name=tpl['doc_name'],
                    html_body=tpl['html'],
                    filename=tpl['filename'],
                    tpl_code=tpl['tpl_code'],
                )
                doc_ids.append(doc_rec.id)

            partner.sudo().write({
                'dgm_software_contract_model': mode,
                'dgm_software_contract_doc_ids': [(6, 0, doc_ids)],
            })
            partner._compute_dgm_software_contract_docs()

        return True

    @api.model
    def ensure_ktt_khang_truong_thinh_partner(self):
        """Idempotently ensures `CÔNG TY TNHH KHANG TRƯỜNG THỊNH` (`PTN-DGM-2026-0008`, VAT `0316889922`,
        `dgm_partner_group='strategic_b2b'`, `dgm_onboarding_state='approved'`) exists as a canonical
        Turnkey Software Package customer in `res.partner`, generates its 4 `TPL-ONB-01..04` companion
        onboarding documents, and generates its 4-document Turnkey Software Contract Suite (`TPL-SW-KTT-01..04`).
        """
        Partner = self.env['res.partner'].sudo()
        Country = self.env['res.country'].sudo()
        vn_country = Country.search([('code', '=', 'VN')], limit=1)
        ktt_prof = CANONICAL_SW_PARTNER_PROFILES['KTT']
        ktt = Partner.search([
            '|', '|', '|',
            ('dgm_partner_code', '=', 'PTN-DGM-2026-0008'),
            ('vat', '=', '0316889922'),
            ('vat', '=', '0316892450'),
            ('name', 'ilike', 'KHANG TRƯỜNG THỊNH'),
        ], order='id asc', limit=1)
        vals = {
            'name': ktt_prof['partner_name'],
            'company_type': 'company',
            'is_company': True,
            'vat': '0316889922',
            'street': ktt_prof['address'],
            'email': ktt_prof['email'],
            'customer_rank': 1,
            'dgm_partner_code': 'PTN-DGM-2026-0008',
            'dgm_partner_group': 'strategic_b2b',
            'dgm_onboarding_state': 'approved',
            'dgm_software_contract_model': 'ktt_turnkey',
            'active': True,
        }
        if vn_country:
            vals['country_id'] = vn_country.id

        if not ktt:
            ktt = Partner.create(vals)
        else:
            ktt.write(vals)

        if not ktt.dgm_provisional_code or not str(ktt.dgm_provisional_code).startswith('TMP-DGM-'):
            ktt.write({'dgm_provisional_code': f"TMP-DGM-{ktt.id:04d}"})

        if hasattr(ktt, '_compute_dgm_tier_and_terms'):
            ktt._compute_dgm_tier_and_terms()
        if hasattr(ktt, 'action_generate_onboarding_documents') and ktt.dgm_onboarding_doc_count < 4:
            ktt.action_generate_onboarding_documents()
        if hasattr(ktt, '_compute_dgm_onboarding_docs'):
            ktt._compute_dgm_onboarding_docs()

        ktt.write({
            'dgm_partner_code': 'PTN-DGM-2026-0008',
            'dgm_partner_group': 'strategic_b2b',
            'dgm_partner_tier': 'tier_s',
            'dgm_credit_limit_vnd': 2_000_000_000.0,
            'dgm_allowed_payment_rail': 'vcb_digibiz',
            'dgm_onboarding_state': 'approved',
            'dgm_software_contract_model': 'ktt_turnkey',
        })
        ktt.action_generate_software_contract_templates(model_type='ktt_turnkey')
        return ktt

