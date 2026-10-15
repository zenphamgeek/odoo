# -*- coding: utf-8 -*-
import base64
import html
import re

from odoo import api, models, _

try:
    from .dgm_brand_footer import (
        render_dgm_brand_header_html,
        render_dgm_brand_footer_html,
        wrap_dgm_branded_html_document,
    )
except ImportError:
    import importlib.util as _ilu
    import os as _os
    _bf_spec = _ilu.spec_from_file_location(
        "dgm_brand_footer",
        _os.path.join(_os.path.dirname(__file__), "dgm_brand_footer.py"),
    )
    _bf_mod = _ilu.module_from_spec(_bf_spec)
    _bf_spec.loader.exec_module(_bf_mod)
    render_dgm_brand_header_html = _bf_mod.render_dgm_brand_header_html
    render_dgm_brand_footer_html = _bf_mod.render_dgm_brand_footer_html
    wrap_dgm_branded_html_document = _bf_mod.wrap_dgm_branded_html_document

HR_TEMPLATE_DEFINITIONS = {
    'TPL-HR-01': {
        'sop_ref': 'SOP-DGM-04',
        'filename_prefix': '01_Hop_Dong_Lao_Dong_Chuan_TPL_HR_01',
        'title': 'Hợp đồng Lao động / Hợp đồng Thử việc Chuẩn (Standard Employment & Probation Contract — SOP-DGM-04)',
        'classification': 'HR CONFIDENTIAL • LABOR CONTRACT',
    },
    'TPL-HR-02': {
        'sop_ref': 'SOP-DGM-04 / ISO-27701',
        'filename_prefix': '02_Cam_Ket_Bao_Mat_Va_SHTT_NDA_TPL_HR_02',
        'title': 'Cam kết Bảo mật Thông tin & Sở hữu Trí tuệ Nhân sự (Employee NDA & IP Assignment Agreement — ISO/IEC 27701)',
        'classification': 'HR CONFIDENTIAL • ISO/IEC 27701 NDA',
    },
    'TPL-HR-03': {
        'sop_ref': 'SOP-DGM-04',
        'filename_prefix': '03_Checklist_Hoi_Nhap_Nhan_Su_5_Buoc_TPL_HR_03',
        'title': 'Biên bản Bàn giao & Checklist Hội nhập Nhân sự Mới 5 Bước (5-Step Onboarding Checklist — SOP-DGM-04)',
        'classification': 'INTERNAL HR • ONBOARDING CHECKLIST',
    },
    'TPL-HR-04': {
        'sop_ref': 'SOP-DGM-03/04',
        'filename_prefix': '04_Bien_Ban_Ban_Giao_Thanh_Ly_5_Cong_TPL_HR_04',
        'title': 'Biên bản Bàn giao Công việc, Tài sản & Thanh lý Hợp đồng 5 Cổng (5-Gate Offboarding & Clearance Certificate — SOP-DGM-03/04)',
        'classification': 'HR CONFIDENTIAL • OFFBOARDING CLEARANCE',
    },
    'TPL-HR-05': {
        'sop_ref': 'SOP-DGM-02',
        'filename_prefix': '05_Phieu_Luong_Chuan_BHXH_TZ0857G_TPL_HR_05',
        'title': 'Phiếu Lương Chuẩn & Bảng Kê Khấu trừ Bảo hiểm Bắt buộc / Thuế TNCN (Monthly Statutory Payslip & BHXH TZ0857G / PIT / VCB DigiBiz Statement — SOP-DGM-02)',
        'classification': 'STRICTLY CONFIDENTIAL • PAYROLL & PIT',
    },
}


class DgmHrDocumentTemplates(models.Model):
    _inherit = 'hr.employee'

    def _extract_employee_template_context(self):
        """Extracts safe, partially masked employee metadata (per ISO/IEC 27701 & Decree 13/2023/ND-CP)
        or returns canonical master template placeholders when invoked on an empty recordset.
        """
        try:
            emp = self[:1]
        except TypeError:
            emp = self
        if not emp:
            return {
                'emp_name': 'Họ và Tên Nhân sự (Employee Full Name)',
                'emp_code': 'DGM-EMP-2026',
                'job_title': 'Kỹ sư Phần mềm / Chuyên viên (Software Engineer / Specialist)',
                'dept_name': 'Khối Công nghệ & Sản phẩm (Engineering & Product)',
                'work_email': 'employee@digimate.vn',
                'masked_id': '079******888',
                'masked_phone': '090*****88',
                'masked_bank': '10****8899 (Vietcombank)',
                'gross_wage': 35_000_000.0,
                'insurance_base': 35_000_000.0,
            }

        raw_id = str(getattr(emp, 'identification_id', '') or '').strip()
        if len(raw_id) >= 6:
            masked_id = f"{raw_id[:3]}******{raw_id[-3:]}"
        else:
            masked_id = raw_id or '079******917'

        raw_phone = str(getattr(emp, 'work_phone', '') or getattr(emp, 'mobile_phone', '') or '').strip()
        if len(raw_phone) >= 5:
            masked_phone = f"{raw_phone[:3]}*****{raw_phone[-2:]}"
        else:
            masked_phone = raw_phone or '090*****01'

        bank_acc = ''
        if getattr(emp, 'bank_account_id', False) and emp.bank_account_id.acc_number:
            acc_no = str(emp.bank_account_id.acc_number).strip()
            masked_bank = f"{acc_no[:2]}****{acc_no[-4:]}" if len(acc_no) >= 6 else acc_no
        else:
            masked_bank = '13****8161 (VCB DigiBiz)'

        gross_wage = 35_000_000.0
        if getattr(emp, 'version_id', False) and getattr(emp.version_id, 'wage', 0.0):
            gross_wage = float(emp.version_id.wage)

        emp_id_num = emp.id if isinstance(emp.id, int) and emp.id > 0 else 1
        return {
            'emp_name': emp.name or 'Nhân sự Digimate',
            'emp_code': f"DGM-EMP-{emp_id_num:04d}",
            'job_title': emp.job_title or (emp.job_id.name if emp.job_id else 'Senior Software Engineer'),
            'dept_name': emp.department_id.name if emp.department_id else 'Khối Kỹ thuật & Giải pháp',
            'work_email': emp.work_email or 'hr@digimate.vn',
            'masked_id': masked_id,
            'masked_phone': masked_phone,
            'masked_bank': masked_bank,
            'gross_wage': gross_wage,
            'insurance_base': min(gross_wage, 46_800_000.0),
        }

    def render_dgm_hr_template_html(self, template_code='TPL-HR-01'):
        """Renders any of the 5 standardized HR document templates (`TPL-HR-01`..`TPL-HR-05`)
        with the official Digimate Brand Header & Footer containing the Google Drive Logo.
        """
        code = str(template_code or 'TPL-HR-01').strip().upper()
        if code not in HR_TEMPLATE_DEFINITIONS:
            code = 'TPL-HR-01'

        meta = HR_TEMPLATE_DEFINITIONS[code]
        if hasattr(self, '_extract_employee_template_context'):
            ctx = self._extract_employee_template_context()
        else:
            ctx = DgmHrDocumentTemplates._extract_employee_template_context(self)

        emp_name = html.escape(ctx['emp_name'])
        emp_code = html.escape(ctx['emp_code'])
        job_title = html.escape(ctx['job_title'])
        dept_name = html.escape(ctx['dept_name'])
        work_email = html.escape(ctx['work_email'])
        masked_id = html.escape(ctx['masked_id'])
        masked_phone = html.escape(ctx['masked_phone'])
        masked_bank = html.escape(ctx['masked_bank'])
        gross = ctx['gross_wage']
        ins_base = ctx['insurance_base']

        bhxh_emp = round(ins_base * 0.08)
        bhyt_emp = round(ins_base * 0.015)
        bhtn_emp = round(ins_base * 0.01)
        total_ins_emp = bhxh_emp + bhyt_emp + bhtn_emp
        taxable_income = max(0.0, gross - total_ins_emp - 11_000_000.0)
        est_pit = round(taxable_income * 0.10) if taxable_income > 0 else 0.0
        net_pay = gross - total_ins_emp - est_pit

        if code == 'TPL-HR-01':
            inner_html = f"""
            <h2>HỢP ĐỒNG LAO ĐỘNG &amp; PHỤ LỤC THỬ VIỆC CHUẨN (SOP-DGM-04)</h2>
            <table>
              <tbody>
                <tr><th style="width:32%;">Người Sử dụng Lao động (Bên A)</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: 0317958465 • Mã ĐV BHXH: TZ0857G</td></tr>
                <tr><th>Người Lao động (Bên B)</th><td><strong>{emp_name}</strong> (Mã NS: <code>{emp_code}</code>)</td></tr>
                <tr><th>CCCD / Định danh (ISO 27701 Masked)</th><td><code>{masked_id}</code> • Điện thoại: <code>{masked_phone}</code> • Email: <code>{work_email}</code></td></tr>
                <tr><th>Chức danh &amp; Đơn vị</th><td><strong>{job_title}</strong> — {dept_name}</td></tr>
                <tr><th>Mức lương Gross &amp; Chế độ BHXH</th><td><strong>{gross:,.0f} VNĐ/tháng</strong> (Đóng BHXH 8%, BHYT 1.5%, BHTN 1% theo đơn vị <code>TZ0857G</code>)</td></tr>
                <tr><th>Tài khoản nhận lương VCB DigiBiz</th><td><code>{masked_bank}</code> (Chuẩn định dạng 11 cột VCB DigiBiz Text <code>@</code>)</td></tr>
              </tbody>
            </table>
            <p><strong>Điều khoản Quản trị:</strong> Mọi thay đổi thông tin pháp lý, CCCD, tài khoản ngân hàng hoặc mức lương sau khi Hợp đồng có hiệu lực bắt buộc thực hiện qua quy trình phê duyệt 2 bước (Maker → Checker) trên Cổng Nhân sự Tự phục vụ (SOP-DGM-04).</p>
            """
        elif code == 'TPL-HR-02':
            inner_html = f"""
            <h2>CAM KẾT BẢO MẬT THÔNG TIN &amp; SỞ HỮU TRÍ TUỆ NHÂN SỰ (NDA &amp; IP ASSIGNMENT)</h2>
            <table>
              <tbody>
                <tr><th style="width:32%;">Pháp nhân Chủ quản</th><td><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong> — MST: 0317958465</td></tr>
                <tr><th>Nhân sự Cam kết</th><td><strong>{emp_name}</strong> (Mã NS: <code>{emp_code}</code> • Chức danh: {job_title})</td></tr>
                <tr><th>Tiêu chuẩn Tuân thủ</th><td><strong>ISO/IEC 27001:2022</strong>, <strong>ISO/IEC 27701</strong> &amp; <strong>Nghị định 13/2023/NĐ-CP</strong> về Bảo vệ Dữ liệu Cá nhân</td></tr>
              </tbody>
            </table>
            <ul>
              <li><strong>Bảo mật Mã nguồn &amp; Dữ liệu Khách hàng:</strong> Tuyệt đối không sao chép, phát tán mã nguồn, tài liệu kiến trúc hoặc thông tin đối tác ra ngoài môi trường được cấp quyền.</li>
              <li><strong>Zero-Leak PII &amp; Khóa Bí mật:</strong> Tuân thủ cơ chế ẩn danh một phần (Partial Masking) và không đưa API Key, Token, mật khẩu vào nhật ký hoặc tài liệu công khai.</li>
              <li><strong>Quyền Sở hữu Trí tuệ:</strong> Toàn bộ sản phẩm phần mềm, tài liệu thiết kế và sáng chế phát sinh trong quá trình làm việc thuộc quyền sở hữu của Digimate JSC.</li>
            </ul>
            """
        elif code == 'TPL-HR-03':
            inner_html = f"""
            <h2>CHECKLIST HỘI NHẬP NHÂN SỰ MỚI 5 BƯỚC (5-STEP ONBOARDING CHECKLIST — SOP-DGM-04)</h2>
            <p>Nhân sự: <strong>{emp_name}</strong> (<code>{emp_code}</code>) — Vị trí: <strong>{job_title}</strong> ({dept_name})</p>
            <table>
              <thead>
                <tr><th>Bước</th><th>Hạng mục Hội nhập (Onboarding Gate)</th><th>Đơn vị Phụ trách</th><th>Trạng thái Chuẩn</th></tr>
              </thead>
              <tbody>
                <tr><td><strong>Bước 1</strong></td><td>Xác thực Hồ sơ Pháp lý, CCCD, MST TNCN &amp; Tài khoản VCB DigiBiz</td><td>HR &amp; Admin</td><td>✓ Hoàn tất</td></tr>
                <tr><td><strong>Bước 2</strong></td><td>Ký kết Hợp đồng Thử việc / HĐLĐ (TPL-HR-01) &amp; Cam kết NDA/IP (TPL-HR-02)</td><td>HR &amp; Legal</td><td>✓ Hoàn tất</td></tr>
                <tr><td><strong>Bước 3</strong></td><td>Cấp phát Tài khoản SSO, Email Doanh nghiệp &amp; Quyền truy cập Dự án</td><td>IT Security</td><td>✓ Hoàn tất</td></tr>
                <tr><td><strong>Bước 4</strong></td><td>Đào tạo Quy trình Chuẩn SOP-DGM-01..08 &amp; Bảo mật ISO/IEC 27701</td><td>PMO / Compliance</td><td>✓ Hoàn tất</td></tr>
                <tr><td><strong>Bước 5</strong></td><td>Bàn giao Mục tiêu KPI Thử việc &amp; Phân công Dự án (Kickoff Handover)</td><td>Direct Manager</td><td>✓ Hoàn tất</td></tr>
              </tbody>
            </table>
            """
        elif code == 'TPL-HR-04':
            inner_html = f"""
            <h2>BIÊN BẢN BÀN GIAO &amp; THANH LÝ HỢP ĐỒNG 5 CỔNG (5-GATE OFFBOARDING CLEARANCE — SOP-DGM-03/04)</h2>
            <p>Nhân sự: <strong>{emp_name}</strong> (<code>{emp_code}</code>) — Chức danh: <strong>{job_title}</strong> ({dept_name})</p>
            <table>
              <thead>
                <tr><th>Cổng Kiểm soát</th><th>Nội dung Nghiệm thu Bàn giao trước khi Giải ngân Quyết toán</th><th>Bộ phận Xác nhận</th></tr>
              </thead>
              <tbody>
                <tr><td><strong>Gate 1 (Work &amp; Code)</strong></td><td>Bàn giao toàn bộ mã nguồn, tài liệu kỹ thuật, tiến độ Timesheet dự án đang phụ trách</td><td>Project Manager</td></tr>
                <tr><td><strong>Gate 2 (IT &amp; Access)</strong></td><td>Thu hồi quyền truy cập Git, Cloud, VPN, Email &amp; Xác nhận xóa dữ liệu cục bộ theo NDA</td><td>IT Security</td></tr>
                <tr><td><strong>Gate 3 (Assets)</strong></td><td>Bàn giao thiết bị phần cứng (Laptop, Thẻ từ, Thiết bị тестирование) nguyên trạng</td><td>HR &amp; Admin</td></tr>
                <tr><td><strong>Gate 4 (Finance &amp; Tax)</strong></td><td>Đối soát tạm ứng, công nợ nội bộ, quyết toán thuế TNCN &amp; chốt sổ BHXH <code>TZ0857G</code></td><td>Finance &amp; Accounting</td></tr>
                <tr><td><strong>Gate 5 (Final Settlement)</strong></td><td>Phê duyệt Quyết định Chấm dứt HĐLĐ &amp; Chi trả lương kỳ cuối qua VCB DigiBiz</td><td>CEO / HR Director</td></tr>
              </tbody>
            </table>
            """
        else:
            inner_html = f"""
            <h2>PHIẾU LƯƠNG CHUẨN &amp; BẢNG KÊ BẢO HIỂM BẮT BUỘC / THUẾ TNCN (SOP-DGM-02)</h2>
            <p>Nhân sự: <strong>{emp_name}</strong> (<code>{emp_code}</code>) — Chức danh: <strong>{job_title}</strong> • Đơn vị BHXH: <code>TZ0857G</code></p>
            <table>
              <thead>
                <tr><th>Khoản mục Lương &amp; Khấu trừ Luật định (Statutory VN Payroll 2026)</th><th style="text-align:right;">Tỷ lệ / Định mức</th><th style="text-align:right;">Số tiền (VNĐ)</th></tr>
              </thead>
              <tbody>
                <tr><td><strong>1. Tổng Thu nhập theo Hợp đồng (Gross Salary)</strong></td><td style="text-align:right;">100%</td><td style="text-align:right;"><strong>{gross:,.0f}</strong></td></tr>
                <tr><td>2. Khấu trừ Bảo hiểm Xã hội bắt buộc (BHXH — NLĐ đóng)</td><td style="text-align:right;">8.0%</td><td style="text-align:right;">-{bhxh_emp:,.0f}</td></tr>
                <tr><td>3. Khấu trừ Bảo hiểm Y tế bắt buộc (BHYT — NLĐ đóng)</td><td style="text-align:right;">1.5%</td><td style="text-align:right;">-{bhyt_emp:,.0f}</td></tr>
                <tr><td>4. Khấu trừ Bảo hiểm Thất nghiệp (BHTN — NLĐ đóng)</td><td style="text-align:right;">1.0%</td><td style="text-align:right;">-{bhtn_emp:,.0f}</td></tr>
                <tr><td>5. Thuế Thu nhập Cá nhân tạm tính (Biểu lũy tiến 5 bậc 2026)</td><td style="text-align:right;">5-Bracket PIT</td><td style="text-align:right;">-{est_pit:,.0f}</td></tr>
                <tr><td><strong>6. THỰC LĨNH CHUYỂN KHOẢN VCB DIGIBIZ (NET TAKE-HOME PAY)</strong></td><td style="text-align:right;"><code>{masked_bank}</code></td><td style="text-align:right;"><strong>{net_pay:,.0f}</strong></td></tr>
              </tbody>
            </table>
            """

        return wrap_dgm_branded_html_document(
            body_html=inner_html,
            title=meta['title'],
            doc_code=code,
            sop_ref=meta['sop_ref'],
            classification=meta['classification'],
            include_header=True,
        )

    def action_generate_hr_standard_documents(self):
        """Generates or refreshes the 5 standardized HR documents (`TPL-HR-01`..`TPL-HR-05`)
        in `documents.document` under `01. Hành chính - Nhân sự (HR & Admin)` with the official
        Digimate Google Drive Logo Brand Header & Footer.
        """
        Document = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo()

        hr_folder = Document.browse(3224).exists()
        if not hr_folder or hr_folder.type != 'folder' or not hr_folder.active:
            hr_folder = Document.search([
                ('type', '=', 'folder'),
                ('active', '=', True),
                ('name', 'ilike', '01. Hành chính'),
            ], order='id asc', limit=1)
        if not hr_folder:
            hr_folder = Document.search([
                ('type', '=', 'folder'),
                ('active', '=', True),
            ], order='id asc', limit=1)

        folder_id = hr_folder.id if hr_folder else False
        target_records = self if self else [self.browse()]
        generated_docs = Document.browse()

        for emp in target_records:
            emp_suffix = ''
            if emp and emp.id:
                clean_emp = re.sub(r'[^0-9A-Za-z_\-]', '_', emp.name or f"EMP_{emp.id}")
                emp_suffix = f"_{clean_emp}"

            for tpl_code, meta in HR_TEMPLATE_DEFINITIONS.items():
                html_str = emp.render_dgm_hr_template_html(template_code=tpl_code)
                b64_datas = base64.b64encode(html_str.encode('utf-8'))
                fname = f"{meta['filename_prefix']}{emp_suffix}.html"
                doc_title = (
                    f"[{tpl_code}] {meta['title']} — {emp.name}"
                    if (emp and emp.id)
                    else f"[{tpl_code}] {meta['title']}"
                )

                existing = Document.search([
                    ('folder_id', '=', folder_id),
                    ('name', 'ilike', f"[{tpl_code}]"),
                    ('type', '!=', 'folder'),
                    ('active', '=', True),
                ], order='id asc', limit=1)

                if existing:
                    if existing.attachment_id:
                        existing.attachment_id.write({
                            'name': fname,
                            'datas': b64_datas,
                            'mimetype': 'text/html',
                        })
                    else:
                        att = Attachment.create({
                            'name': fname,
                            'datas': b64_datas,
                            'mimetype': 'text/html',
                            'res_model': 'documents.document',
                            'res_id': existing.id,
                        })
                        existing.write({'attachment_id': att.id})
                    existing.write({
                        'name': doc_title,
                        'owner_id': False,
                        'access_internal': 'edit',
                    })
                    generated_docs |= existing
                else:
                    att = Attachment.create({
                        'name': fname,
                        'datas': b64_datas,
                        'mimetype': 'text/html',
                        'res_model': 'hr.employee' if (emp and emp.id) else 'documents.document',
                        'res_id': emp.id if (emp and emp.id) else 0,
                    })
                    new_doc = Document.create({
                        'name': doc_title,
                        'folder_id': folder_id,
                        'owner_id': False,
                        'type': 'binary',
                        'attachment_id': att.id,
                        'access_internal': 'edit',
                        'access_via_link': 'view',
                        'active': True,
                    })
                    generated_docs |= new_doc

        return generated_docs
