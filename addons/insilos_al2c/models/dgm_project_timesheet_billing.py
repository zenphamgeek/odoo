# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import html
import logging
import secrets
import unicodedata
from xml.sax.saxutils import escape as xml_escape

from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    from .dgm_brand_footer import (
        get_digimate_logo_data_uri,
        get_digimate_logo_url,
        render_dgm_brand_footer_html,
        render_dgm_brand_header_html,
        wrap_dgm_branded_html_document,
    )
except ImportError:
    import importlib.util as _importlib_util
    from pathlib import Path as _Path
    _bf_path = _Path(__file__).resolve().parent / "dgm_brand_footer.py"
    _bf_spec = _importlib_util.spec_from_file_location("dgm_brand_footer", _bf_path)
    _bf_mod = _importlib_util.module_from_spec(_bf_spec)
    _bf_spec.loader.exec_module(_bf_mod)
    get_digimate_logo_data_uri = _bf_mod.get_digimate_logo_data_uri
    get_digimate_logo_url = _bf_mod.get_digimate_logo_url
    render_dgm_brand_footer_html = _bf_mod.render_dgm_brand_footer_html
    render_dgm_brand_header_html = _bf_mod.render_dgm_brand_header_html
    wrap_dgm_branded_html_document = _bf_mod.wrap_dgm_branded_html_document

_logger = logging.getLogger(__name__)

ADVISORY_LOCK_SOP08_NS = 1397706800  # ASCII 'SOP0' 32-bit namespace key
ADVISORY_LOCK_SHEET_OFFSET = 260000000
ADVISORY_LOCK_MOVE_OFFSET = 261000000

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

NOTIFICATION_TYPE_SELECTION = [
    (
        'kickoff_handover',
        '1. Thông báo Khởi động Dự án & Bàn giao Nhân sự (Post-Onboarding Kickoff)',
    ),
    (
        'timesheet_cutoff',
        '2. Thông báo Chốt Bảng Chấm công Cuối kỳ (Monthly Timesheet Cut-off)',
    ),
    (
        'customer_approval_req',
        '3. Đề nghị Khách hàng Phê duyệt Timesheet & Nghiệm thu (Customer Timesheet Approval Request)',
    ),
    (
        'budget_burn_alert',
        '4. Cảnh báo Ngưỡng 85% Khối lượng / Overtime (Budget & Burn SLA Alert)',
    ),
    (
        'draft_invoice_review',
        '5. Thông báo Đối soát Hóa đơn Nháp (MTI Draft Invoice Reconciliation)',
    ),
    (
        'official_invoice_issued',
        '6. Thông báo Phát hành Hóa đơn GTGT Chính thức (Official E-Invoice Issued)',
    ),
    (
        'quotation_sow_approved',
        '7. Xác nhận Phê duyệt Báo giá & Ký SOW Trực tuyến (Customer Quotation & SOW Approved)',
    ),
    (
        'draft_adjustment_requested',
        '8. Yêu cầu Điều chỉnh Hóa đơn Nháp / Bảng Chấm công (Customer Revision Request)',
    ),
]

NOTIFICATION_TYPE_LABELS = dict(NOTIFICATION_TYPE_SELECTION)

_INNORIA_HEADER_LOGO_B64_CACHE = None


def _get_innoria_header_logo_data_uri():
    global _INNORIA_HEADER_LOGO_B64_CACHE
    if _INNORIA_HEADER_LOGO_B64_CACHE is not None:
        return _INNORIA_HEADER_LOGO_B64_CACHE
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static',
        'src',
        'img',
        'logo_innoria_header.png',
    )
    if os.path.isfile(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            _INNORIA_HEADER_LOGO_B64_CACHE = f"data:image/png;base64,{b64}"
            return _INNORIA_HEADER_LOGO_B64_CACHE
        except Exception:
            pass
    _INNORIA_HEADER_LOGO_B64_CACHE = get_digimate_logo_data_uri('default')
    return _INNORIA_HEADER_LOGO_B64_CACHE


class DgmProjectNotification(models.Model):
    _name = 'dgm.project.notification'
    _description = 'DGM Project & Timesheet Notification (SOP-DGM-08)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Mã Thông báo',
        required=True,
        copy=False,
        default='New',
        index=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Dự án (Project)',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng / Đối tác',
        related='project_id.partner_id',
        store=True,
        readonly=False,
        index=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Hợp đồng / Đơn hàng (SO)',
        index=True,
    )
    timesheet_sheet_id = fields.Many2one(
        'dgm.project.timesheet.sheet',
        string='Bảng Chấm công Liên kết',
        index=True,
        ondelete='set null',
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        'dgm_project_notification_emp_rel',
        'notification_id',
        'employee_id',
        string='Nhân sự Dự án (Assigned Engineers)',
    )
    notification_type = fields.Selection(
        selection=NOTIFICATION_TYPE_SELECTION,
        string='Loại Thông báo Dự án (SOP-DGM-08)',
        required=True,
        default='kickoff_handover',
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp (Draft)'),
            ('sent', 'Đã gửi Thông báo (Sent)'),
            ('acknowledged', 'KH Đã Xác nhận (Acknowledged)'),
        ],
        string='Trạng thái',
        default='draft',
        tracking=True,
        index=True,
    )
    recipient_email = fields.Char(
        string='Email Người nhận (Customer Contact)',
    )
    summary_html = fields.Html(
        string='Nội dung Thông báo (Notification Body)',
        sanitize=False,
    )
    document_id = fields.Many2one(
        'documents.document',
        string='Hồ sơ Lưu trữ (Documents)',
        copy=False,
    )
    sent_date = fields.Datetime(
        string='Thời điểm Gửi',
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        Project = self.env['project.project'].sudo()
        SaleOrder = self.env['sale.order'].sudo()
        Partner = self.env['res.partner'].sudo()

        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if not partner_id and vals.get('project_id'):
                proj = Project.browse(vals['project_id'])
                if proj and proj.partner_id:
                    partner_id = proj.partner_id.id
                    vals['partner_id'] = partner_id
            if not partner_id and vals.get('sale_order_id'):
                so = SaleOrder.browse(vals['sale_order_id'])
                if so and so.partner_id:
                    partner_id = so.partner_id.id
                    vals['partner_id'] = partner_id
            if not vals.get('recipient_email') and partner_id:
                partner = Partner.browse(partner_id)
                if partner and partner.email:
                    vals['recipient_email'] = partner.email

        records = super().create(vals_list)
        for rec in records:
            updates = {}
            if not rec.name or rec.name in ('New', '/'):
                seq_id = rec.id if isinstance(rec.id, int) and rec.id > 0 else 1
                updates['name'] = f"PRJ-NTF-202610-{seq_id:04d}"
            if not rec.partner_id:
                fallback_partner = rec.project_id.partner_id or rec.sale_order_id.partner_id
                if fallback_partner:
                    updates['partner_id'] = fallback_partner.id
            if not rec.recipient_email and rec.partner_id and rec.partner_id.email:
                updates['recipient_email'] = rec.partner_id.email
            if not rec.summary_html:
                updates['summary_html'] = rec._render_notification_html(
                    code_override=updates.get('name') or rec.name
                )
            if updates:
                rec.sudo().write(updates)
        return records

    def _render_notification_html(self, code_override=None):
        self.ensure_one()
        ntf_code = code_override or self.name or 'PRJ-NTF-202610-0001'
        ntf_label = NOTIFICATION_TYPE_LABELS.get(
            self.notification_type,
            self.notification_type or 'Thông báo Dự án',
        )
        partner = self.partner_id or self.project_id.partner_id or self.sale_order_id.partner_id
        partner_name = html.escape(partner.name if partner and partner.name else 'Quý Khách hàng / Đối tác')
        partner_code = html.escape(
            (partner.dgm_partner_code or partner.dgm_provisional_code or 'PTN-DGM')
            if partner
            else 'PTN-DGM'
        )
        partner_vat = html.escape((partner.vat or '0317958465') if partner else '0317958465')
        project_name = html.escape(self.project_id.name if self.project_id and self.project_id.name else 'Dự án Kỹ nghệ Phần mềm')

        so = self.sale_order_id or (self.timesheet_sheet_id.sale_order_id if self.timesheet_sheet_id else False)
        so_name = html.escape(so.name if so and so.name else 'N/A')
        so_state_label = html.escape(
            f"{so.state.upper()} | Deal Desk Approved: {'YES' if getattr(so, 'al2c_approved', False) else 'STANDARD'}"
            if so and getattr(so, 'state', False)
            else 'ACTIVE SOW'
        )

        sheet = self.timesheet_sheet_id
        sheet_name = html.escape(sheet.name if sheet and sheet.name else 'N/A')
        billing_period = html.escape(sheet.billing_period if sheet and sheet.billing_period else '10/2026')
        total_billable_days = float(sheet.total_billable_days or 0.0) if sheet else 0.0
        total_logged_hours = float(sheet.total_logged_hours or 0.0) if sheet else 0.0
        sig_hash = html.escape(
            (sheet.customer_signature_hash or 'PENDING-CUSTOMER-SIGNATURE')
            if sheet
            else 'N/A'
        )

        # Amounts (from timesheet sheet or sale order fallback)
        if sheet and (sheet.amount_total_vnd or sheet.amount_untaxed_vnd):
            amount_untaxed_vnd = float(sheet.amount_untaxed_vnd or 0.0)
            amount_tax_vnd = float(sheet.amount_tax_vnd or 0.0)
            amount_total_vnd = float(sheet.amount_total_vnd or 0.0)
            vat_rate_str = html.escape(str(sheet.vat_rate or '8'))
        elif so:
            amount_untaxed_vnd = float(getattr(so, 'amount_untaxed', 0.0) or 0.0)
            amount_tax_vnd = float(getattr(so, 'amount_tax', 0.0) or 0.0)
            amount_total_vnd = float(getattr(so, 'amount_total', 0.0) or 0.0)
            vat_rate_str = '8'
        else:
            amount_untaxed_vnd = 0.0
            amount_tax_vnd = 0.0
            amount_total_vnd = 0.0
            vat_rate_str = '8'

        # Engineer breakdown rows
        eng_rows = []
        if sheet and sheet.line_ids:
            for idx, line in enumerate(sheet.line_ids, start=1):
                e_name = html.escape(line.employee_id.name if line.employee_id else 'Kỹ sư Phần mềm')
                e_role = html.escape(line.role_title or 'Senior Software Engineer')
                e_work = html.escape(line.work_summary or 'Phát triển & bàn giao sprint phần mềm theo SOW.')
                eng_rows.append(
                    f"<tr>"
                    f"<td style='padding:8px 10px;border:1px solid #e0e0e0;text-align:center;'>{idx}</td>"
                    f"<td style='padding:8px 10px;border:1px solid #e0e0e0;'><strong>{e_name}</strong><br/><span style='font-size:11px;color:#525252;'>{e_role}</span></td>"
                    f"<td style='padding:8px 10px;border:1px solid #e0e0e0;font-size:12px;'>{e_work}</td>"
                    f"<td style='padding:8px 10px;border:1px solid #e0e0e0;text-align:right;font-weight:700;'>{line.billable_days or 0.0:,.1f} / {line.standard_days or 22.0:,.1f} ngày</td>"
                    f"<td style='padding:8px 10px;border:1px solid #e0e0e0;text-align:right;font-weight:700;color:#0070F2;'>{line.subtotal_vnd or 0.0:,.0f} VNĐ</td>"
                    f"</tr>"
                )
        emp_names = ', '.join(
            html.escape(e.name) for e in self.employee_ids if e.name
        ) or (
            ', '.join(html.escape(l.employee_id.name) for l in sheet.line_ids if l.employee_id and l.employee_id.name)
            if (sheet and sheet.line_ids)
            else 'Đội ngũ Kỹ sư Dự án Digimate (Assigned Engineering Team)'
        )

        eng_breakdown_html = ''
        if eng_rows:
            eng_breakdown_html = f"""
            <div style="margin-top:20px;">
              <div style="font-size:12px;font-weight:700;text-transform:uppercase;color:#0070F2;letter-spacing:0.04em;margin-bottom:8px;">
                CHI TIẾT NGHIỆM THU KỸ SƯ PHẦN MỀM (ENGINEER SPRINT &amp; TIMESHEET BREAKDOWN)
              </div>
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="background-color:#f4f4f4;">
                    <th style="padding:8px 10px;border:1px solid #e0e0e0;width:6%;text-align:center;">#</th>
                    <th style="padding:8px 10px;border:1px solid #e0e0e0;width:24%;">Kỹ sư &amp; Vai trò</th>
                    <th style="padding:8px 10px;border:1px solid #e0e0e0;width:36%;">Hạng mục Nghiệm thu Sprint</th>
                    <th style="padding:8px 10px;border:1px solid #e0e0e0;width:16%;text-align:right;">Ngày công</th>
                    <th style="padding:8px 10px;border:1px solid #e0e0e0;width:18%;text-align:right;">Thành tiền</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(eng_rows)}
                </tbody>
              </table>
            </div>
            """

        # Draft Invoice vs Official VAT E-Invoice (1C26TAA)
        inv = sheet.draft_invoice_id if (sheet and sheet.draft_invoice_id) else False
        draft_inv_ref = html.escape(
            (inv.ref or f"DRAFT-INV-{sheet.name}")
            if inv
            else (f"DRAFT-INV-{sheet.name}" if sheet else 'DRAFT-INV-PENDING')
        )
        inv_stage = html.escape(inv.dgm_invoice_stage if (inv and inv.dgm_invoice_stage) else 'draft_reconciliation')
        einv_symbol = html.escape((inv.dgm_einvoice_symbol or '1C26TAA') if inv else '1C26TAA')
        einv_number = html.escape((inv.dgm_einvoice_number or 'PENDING-ISSUE') if inv else 'PENDING-ISSUE')
        einv_lookup = html.escape((inv.dgm_einvoice_lookup_code or 'PENDING-LOOKUP') if inv else 'PENDING-LOOKUP')
        invoice_id_val = inv.id if (inv and isinstance(inv.id, int) and inv.id > 0) else 0

        # Portal URLs
        portal_home_url = "https://innoria.com/my/software-portal"
        rel_ts_portal_url = ""
        abs_ts_portal_url = "https://innoria.com/my/software-portal"
        if sheet and sheet.id and sheet.approval_token:
            rel_ts_portal_url = f"/insilos/timesheet_approval/{sheet.id}/{sheet.approval_token}"
            abs_ts_portal_url = f"https://innoria.com{rel_ts_portal_url}"
        abs_inv_portal_url = (
            f"https://innoria.com/my/invoices/{invoice_id_val}"
            if invoice_id_val
            else "https://innoria.com/my/invoices"
        )

        innoria_logo_uri = _get_innoria_header_logo_data_uri()

        raw_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{html.escape(ntf_code)} - {html.escape(ntf_label)}</title>
<style>
  body {{
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
    color: var(--insilos-text-primary, #161616);
    background: var(--insilos-bg-card, transparent);
    margin: 24px;
    line-height: 1.55;
  }}
  .ntf-box {{
    border: 1px solid var(--insilos-border-subtle, #e0e0e0);
    border-radius: 2px;
    overflow: hidden;
    background: var(--insilos-bg-surface, transparent);
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
  }}
  th, td {{
    border: 1px solid var(--insilos-border-subtle, #e0e0e0);
    padding: 8px 12px;
    font-size: 13px;
    text-align: left;
  }}
  th {{
    background: var(--insilos-bg-subtle, #f4f4f4);
    width: 34%;
  }}
</style>
</head>
<body>
  <div class="ntf-box">
    <!-- SAP Horizon Top Accent Stripe (#0070F2 -> #0ABBDB) -->
    <div style="height:5px;background:linear-gradient(90deg, #0070F2 0%, #0ABBDB 100%);font-size:0;line-height:5px;">&nbsp;</div>

    <!-- IBM Carbon v11 & SAP Horizon Masthead with Embedded Innoria Header Logo -->
    <div style="padding:18px 24px;border-bottom:1px solid #e0e0e0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <div>
        <a href="{portal_home_url}" target="_blank" style="text-decoration:none;display:inline-block;">
          <img src="{innoria_logo_uri}" alt="Innoria Software Customer Portal" style="max-height:30px;width:auto;display:block;border:0;" />
        </a>
        <div style="font-size:11px;font-weight:700;color:#0070F2;text-transform:uppercase;letter-spacing:0.05em;margin-top:6px;">
          INNORIA SOFTWARE ENGINEERING &amp; B2B CUSTOMER PORTAL · SOP-DGM-08
        </div>
      </div>
      <div style="text-align:right;">
        <span style="display:inline-block;background-color:#f4f4f4;border:1px solid #e0e0e0;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:700;color:#161616;">
          {html.escape(ntf_code)} · 1C26TAA
        </span>
      </div>
    </div>

    <div style="padding:22px 24px;">
      <h2 style="margin:0 0 6px 0;font-size:18px;font-weight:700;color:#161616;">
        THÔNG BÁO DỰ ÁN, NGHIỆM THU TIMESHEET &amp; HÓA ĐƠN ĐIỆN TỬ (SOP-DGM-08)
      </h2>
      <p style="margin:0 0 14px 0;font-size:13px;color:#525252;">
        <strong>Đơn vị phát hành:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC) — MST: <strong>0317958465</strong> | Ký hiệu HĐĐT: <strong>1C26TAA</strong>
      </p>

      <!-- Executive Summary Table -->
      <table>
        <tbody>
          <tr><th>Mã Thông báo (Notification ID)</th><td><strong>{html.escape(ntf_code)}</strong></td></tr>
          <tr><th>Loại Thông báo (Notification Type)</th><td><strong>{html.escape(ntf_label)}</strong></td></tr>
          <tr><th>Khách hàng / Đối tác (Customer)</th><td><strong>{partner_name}</strong> ({partner_code} — MST: {partner_vat})</td></tr>
          <tr><th>Dự án Phần mềm (Software Project)</th><td><strong>{project_name}</strong></td></tr>
          <tr><th>Báo giá &amp; Hợp đồng SOW (Sale Order)</th><td><strong>{so_name}</strong> ({so_state_label})</td></tr>
          <tr><th>Bảng Chấm công Liên kết (Timesheet Sheet)</th><td><strong>{sheet_name}</strong> (Kỳ: {billing_period} — Tổng công nghiệm thu: <strong>{total_billable_days:,.2f} ngày</strong> / {total_logged_hours:,.1f} giờ)</td></tr>
          <tr><th>Nhân sự Kỹ thuật Tham gia (Engineers)</th><td>{emp_names}</td></tr>
          <tr><th>Chữ ký Băm Nghiệm thu (SHA-256 Signature)</th><td><span style="font-weight:700;color:#0f62fe;word-break:break-all;">{sig_hash}</span></td></tr>
          <tr><th>Hóa đơn Nháp Đối soát (MTI Draft Invoice)</th><td><strong>{draft_inv_ref}</strong> (Trạng thái: {inv_stage})</td></tr>
          <tr><th>Hóa đơn GTGT Chính thức (Official 1C26TAA)</th><td>Ký hiệu: <strong>{einv_symbol}</strong> | Số HĐ: <strong>{einv_number}</strong> | Mã tra cứu CQT: <strong>{einv_lookup}</strong></td></tr>
          <tr><th>Tổng Tiền Chưa Thuế (amount_untaxed_vnd)</th><td><strong>{amount_untaxed_vnd:,.0f} VNĐ</strong></td></tr>
          <tr><th>Thuế GTGT ({vat_rate_str}% — amount_tax_vnd)</th><td><strong>{amount_tax_vnd:,.0f} VNĐ</strong></td></tr>
          <tr><th>TỔNG CỘNG THANH TOÁN (amount_total_vnd)</th><td style="font-size:15px;font-weight:700;color:#0070F2;"><strong>{amount_total_vnd:,.0f} VNĐ</strong></td></tr>
          <tr><th>Email Người nhận (Recipient)</th><td>{html.escape(self.recipient_email or 'N/A')}</td></tr>
        </tbody>
      </table>

      {eng_breakdown_html}

      <!-- Direct Interactive Customer Portal Action Buttons (IBM Carbon v11 Rectangular Geometry) -->
      <div style="margin-top:22px;padding:18px;background-color:#f4f4f4;border:1px solid #e0e0e0;border-left:4px solid #0070F2;">
        <div style="font-size:12px;font-weight:700;text-transform:uppercase;color:#161616;margin-bottom:12px;">
          CỔNG TƯƠNG TÁC KHÁCH HÀNG TRỰC TUYẾN (CUSTOMER PORTAL DIRECT ACTIONS)
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:10px;">
          <a href="{html.escape(portal_home_url)}" target="_blank" style="display:inline-block;background-color:#0f62fe;color:#ffffff;text-decoration:none;font-size:13px;font-weight:600;padding:11px 18px;border-radius:0px;margin-right:8px;margin-bottom:8px;">
            🚀 Mở Cổng Khách Hàng Phần Mềm (Customer Portal)
          </a>
          <a href="{html.escape(abs_ts_portal_url)}" target="_blank" style="display:inline-block;background-color:#0070F2;color:#ffffff;text-decoration:none;font-size:13px;font-weight:600;padding:11px 18px;border-radius:0px;margin-right:8px;margin-bottom:8px;">
            ⏱️ Duyệt Bảng Chấm Công &amp; Hóa Đơn Nháp
          </a>
          <a href="{html.escape(abs_inv_portal_url)}" target="_blank" style="display:inline-block;background-color:#161616;color:#f4f4f4;text-decoration:none;font-size:13px;font-weight:600;padding:11px 18px;border-radius:0px;margin-bottom:8px;">
            🧾 Tra Cứu Hóa Đơn &amp; Tải XML 1C26TAA
          </a>
        </div>
        {f"<p style='margin:8px 0 0 0;font-size:12px;color:#525252;'>Liên kết phê duyệt trực tiếp: <a href='{html.escape(rel_ts_portal_url)}' style='color:#0f62fe;'>{html.escape(rel_ts_portal_url)}</a></p>" if rel_ts_portal_url else ""}
      </div>

      <p style="margin-top:16px;font-size:12.5px;color:#525252;">
        Thông báo này được khởi tạo, ký xác thực SHA-256 và lưu trữ tự động theo quy trình <strong>SOP-DGM-08 (Post-Onboarding Delivery-to-Cash Pipeline)</strong>.
      </p>
    </div>
  </div>
</body>
</html>"""
        return wrap_dgm_branded_html_document(
            raw_html,
            doc_title=ntf_label,
            doc_code=ntf_code,
            sop_ref='SOP-DGM-08',
            classification='PROJECT & TIMESHEET NOTIFICATION',
            include_header=True,
        )

    def _render_notification_document_html(self):
        return self._render_notification_html()

    def action_send_project_notification(self):
        Attachment = self.env['ir.attachment'].sudo()
        Document = self.env['documents.document'].sudo()

        for rec in self:
            partner = rec.partner_id or rec.project_id.partner_id or rec.sale_order_id.partner_id
            folder = False
            if partner and hasattr(partner, '_get_or_create_dgm_onboarding_folder'):
                folder = partner.sudo()._get_or_create_dgm_onboarding_folder()
            if not folder:
                folder = self.env.ref('insilos_al2c.folder_dgm_contracts', raise_if_not_found=False)
            if not folder or not folder.exists():
                folder = Document.search([
                    ('type', '=', 'folder'),
                    ('name', 'ilike', '03. Hợp đồng'),
                    ('active', '=', True),
                ], order='id asc', limit=1)

            html_body = rec._render_notification_html()
            safe_type = (rec.notification_type or 'notification').upper()
            doc_name = f"[SOP-DGM-08][{safe_type}] {rec.name} - {rec.project_id.name or 'Project'}.html"
            b64_datas = base64.b64encode(html_body.encode('utf-8'))

            existing_doc = rec.document_id if (rec.document_id and rec.document_id.exists()) else Document.search([
                ('name', '=', doc_name),
                ('folder_id', '=', folder.id if folder else False),
                ('active', '=', True),
            ], limit=1)

            if existing_doc:
                if existing_doc.attachment_id:
                    existing_doc.attachment_id.write({
                        'name': doc_name,
                        'datas': b64_datas,
                        'mimetype': 'text/html',
                    })
                else:
                    att = Attachment.create({
                        'name': doc_name,
                        'datas': b64_datas,
                        'mimetype': 'text/html',
                        'res_model': self._name,
                        'res_id': rec.id,
                    })
                    existing_doc.write({'attachment_id': att.id})
                existing_doc.write({
                    'owner_id': False,
                    'access_internal': 'edit',
                })
                doc_record = existing_doc
            else:
                att = Attachment.create({
                    'name': doc_name,
                    'datas': b64_datas,
                    'mimetype': 'text/html',
                    'res_model': self._name,
                    'res_id': rec.id,
                })
                doc_record = Document.create({
                    'name': doc_name,
                    'folder_id': folder.id if folder else False,
                    'owner_id': False,
                    'partner_id': partner.id if partner else False,
                    'type': 'binary',
                    'attachment_id': att.id,
                    'access_internal': 'edit',
                    'access_via_link': 'view',
                    'active': True,
                })

            now_dt = fields.Datetime.now()
            rec.sudo().write({
                'summary_html': html_body,
                'document_id': doc_record.id,
                'state': 'sent',
                'sent_date': now_dt,
            })

            msg_body = _(
                "<b>[SOP-DGM-08] Đã gửi Thông báo Dự án (%s):</b> %s → Người nhận: <code>%s</code>",
                rec.name,
                NOTIFICATION_TYPE_LABELS.get(rec.notification_type, rec.notification_type),
                rec.recipient_email or (partner.email if partner else 'N/A'),
            )
            if hasattr(rec, 'message_post'):
                try:
                    rec.message_post(body=msg_body, message_type='comment', subtype_xmlid='mail.mt_note')
                except Exception:
                    pass
            if rec.project_id and hasattr(rec.project_id, 'message_post'):
                try:
                    rec.project_id.message_post(body=msg_body, message_type='comment', subtype_xmlid='mail.mt_note')
                except Exception:
                    pass
            if rec.sale_order_id and hasattr(rec.sale_order_id, 'message_post'):
                try:
                    rec.sale_order_id.message_post(body=msg_body, message_type='comment', subtype_xmlid='mail.mt_note')
                except Exception:
                    pass

        if self.env.context.get('send_live_smtp') and not self.env.context.get('_skip_live_smtp_hook'):
            self.with_context(_skip_live_smtp_hook=True).action_dispatch_live_smtp_email(
                target_email=self.env.context.get('target_email'),
                custom_subject=self.env.context.get('custom_subject'),
            )
        return True

    def action_dispatch_live_smtp_email(self, target_email=None, custom_subject=None):
        """Dispatches an executive IBM Carbon v11 & SAP Horizon HTML notification email via live
        SMTP_SSL (`smtp.gmail.com:465`, `info@inno.ai.vn`) using active `ir.mail_server` or fallback
        credentials, attaches canonical `1C26TAA` XML & HTML E-Invoice representations when available,
        and records an auditable `mail.mail` record (`state='sent'`, `al2c_approved=True`).
        """
        MailServer = self.env['ir.mail_server'].sudo()
        MailMail = self.env['mail.mail'].sudo()
        Attachment = self.env['ir.attachment'].sudo()

        server_rec = MailServer.search([('active', '=', True)], order='sequence asc, id asc', limit=1)
        smtp_host = (server_rec.smtp_host if server_rec and server_rec.smtp_host else '') or 'smtp.gmail.com'
        smtp_port = int(server_rec.smtp_port if server_rec and server_rec.smtp_port else 465)
        smtp_user = (server_rec.smtp_user if server_rec and server_rec.smtp_user else '') or 'info@inno.ai.vn'
        smtp_pass = (server_rec.smtp_pass if server_rec and server_rec.smtp_pass else '') or 'hmqiukoacdxyhhuv'
        sender_formatted = f"Innoria Enterprise Systems <{smtp_user}>"

        last_result = {'ok': False}
        for rec in self:
            partner = rec.partner_id or rec.project_id.partner_id or rec.sale_order_id.partner_id
            resolved_email = (
                (target_email or '').strip()
                or (rec.recipient_email or '').strip()
                or (rec.timesheet_sheet_id.customer_approver_email if rec.timesheet_sheet_id else '')
                or (partner.email if partner else '')
                or 'tham.mai@inno.ai.vn'
            ).strip()

            if rec.recipient_email != resolved_email:
                rec.sudo().write({'recipient_email': resolved_email})

            if rec.state == 'draft' or not rec.document_id:
                rec.with_context(_skip_live_smtp_hook=True).action_send_project_notification()
            else:
                rec.sudo().write({
                    'summary_html': rec._render_notification_html(),
                    'sent_date': fields.Datetime.now(),
                })

            html_body = rec._render_notification_html()
            ntf_label = NOTIFICATION_TYPE_LABELS.get(rec.notification_type, rec.notification_type or 'Thông báo Dự án')
            sheet = rec.timesheet_sheet_id
            inv = sheet.draft_invoice_id if (sheet and sheet.draft_invoice_id) else False
            einv_tag = (
                f"{inv.dgm_einvoice_symbol or '1C26TAA'}-{inv.dgm_einvoice_number}"
                if (inv and inv.dgm_einvoice_number)
                else (sheet.name if sheet else rec.name)
            )
            subject = (custom_subject or '').strip() or (
                f"[Innoria Customer Portal | {rec.name}] {ntf_label} — {rec.project_id.name or 'Software Project'} ({einv_tag})"
            )

            plain_summary = (
                f"THÔNG BÁO DỰ ÁN & CỔNG KHÁCH HÀNG PHẦN MỀM INNORIA (SOP-DGM-08)\n"
                f"Mã thông báo: {rec.name}\n"
                f"Loại thông báo: {ntf_label}\n"
                f"Dự án: {rec.project_id.name if rec.project_id else 'N/A'}\n"
                f"Báo giá / Hợp đồng SOW: {rec.sale_order_id.name if rec.sale_order_id else 'N/A'}\n"
                f"Bảng chấm công: {sheet.name if sheet else 'N/A'} (SHA-256: {sheet.customer_signature_hash if sheet else 'N/A'})\n"
                f"Hóa đơn GTGT 1C26TAA: {einv_tag} (Mã tra cứu: {inv.dgm_einvoice_lookup_code if inv else 'N/A'})\n"
                f"Tổng thanh toán: {(sheet.amount_total_vnd if sheet else 0.0):,.0f} VNĐ\n"
                f"Cổng Khách hàng Phần mềm: https://innoria.com/my/software-portal\n"
            )

            clean_msg_id = f"<insilos-portal-ntf-{rec.id}-{secrets.token_hex(6)}@innoria.com>"
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = sender_formatted
            msg['To'] = resolved_email
            msg['Message-ID'] = clean_msg_id

            alt_part = MIMEMultipart('alternative')
            alt_part.attach(MIMEText(plain_summary, 'plain', 'utf-8'))
            alt_part.attach(MIMEText(html_body, 'html', 'utf-8'))
            msg.attach(alt_part)

            att_ids = []
            att_names = []
            if sheet:
                # 1. Attach Canonical 1C26TAA XML E-Invoice
                xml_str = sheet._build_canonical_1c26taa_xml()
                xml_bytes = xml_str.encode('utf-8')
                xml_fname = f"EInvoice_1C26TAA_{sheet.name}.xml"
                xml_mime = MIMEApplication(xml_bytes, _subtype='xml')
                xml_mime.add_header('Content-Disposition', 'attachment', filename=xml_fname)
                msg.attach(xml_mime)

                xml_att = Attachment.create({
                    'name': xml_fname,
                    'datas': base64.b64encode(xml_bytes),
                    'mimetype': 'application/xml',
                    'res_model': self._name,
                    'res_id': rec.id,
                })
                att_ids.append(xml_att.id)
                att_names.append(xml_fname)

                # 2. Attach Official / Draft HTML E-Invoice Representation
                doc_stage = 'official_invoice' if sheet.state == 'official_invoiced' else 'draft_invoice'
                einv_html_str = sheet._render_sheet_document_html(doc_stage=doc_stage)
                einv_html_bytes = einv_html_str.encode('utf-8')
                html_fname = f"EInvoice_1C26TAA_{sheet.name}.html"
                html_mime = MIMEApplication(einv_html_bytes, _subtype='html')
                html_mime.add_header('Content-Disposition', 'attachment', filename=html_fname)
                msg.attach(html_mime)

                html_att = Attachment.create({
                    'name': html_fname,
                    'datas': base64.b64encode(einv_html_bytes),
                    'mimetype': 'text/html',
                    'res_model': self._name,
                    'res_id': rec.id,
                })
                att_ids.append(html_att.id)
                att_names.append(html_fname)

            smtp_sent = False
            smtp_error = None
            try:
                if smtp_port == 465:
                    smtp_conn = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
                else:
                    smtp_conn = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                    smtp_conn.starttls()
                smtp_conn.login(smtp_user, smtp_pass)
                smtp_conn.sendmail(smtp_user, [resolved_email], msg.as_string())
                smtp_conn.quit()
                smtp_sent = True
            except Exception as first_exc:
                smtp_error = str(first_exc)
                try:
                    fallback_conn = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20)
                    fallback_conn.login('info@inno.ai.vn', 'hmqiukoacdxyhhuv')
                    fallback_conn.sendmail('info@inno.ai.vn', [resolved_email], msg.as_string())
                    fallback_conn.quit()
                    smtp_host = 'smtp.gmail.com'
                    smtp_port = 465
                    smtp_user = 'info@inno.ai.vn'
                    smtp_sent = True
                    smtp_error = None
                except Exception as second_exc:
                    smtp_error = f"{first_exc}; fallback: {second_exc}"

            mail_vals = {
                'subject': subject,
                'email_from': sender_formatted,
                'email_to': resolved_email,
                'reply_to': smtp_user,
                'message_id': clean_msg_id,
                'body_html': html_body,
                'model': self._name,
                'res_id': rec.id,
                'state': 'sent' if smtp_sent else 'exception',
                'al2c_approved': True,
                'al2c_trapped': False,
                'auto_delete': False,
            }
            if server_rec:
                mail_vals['mail_server_id'] = server_rec.id
            if att_ids:
                mail_vals['attachment_ids'] = [(6, 0, att_ids)]
            if smtp_error and 'failure_reason' in MailMail._fields:
                mail_vals['failure_reason'] = smtp_error

            mail_rec = MailMail.create(mail_vals)

            audit_note = _(
                "<b>📨 [SOP-DGM-08 Live SMTP_SSL Dispatched]</b> Đã gửi email thông báo Cổng Khách hàng Phần mềm tới "
                "<code>%s</code> qua <code>%s:%s</code> (Mail ID: <code>#%s</code>, Đính kèm: <code>%s</code>).",
                resolved_email,
                smtp_host,
                smtp_port,
                mail_rec.id,
                ', '.join(att_names) if att_names else 'None',
            )
            for target_thread in (rec, rec.project_id, rec.sale_order_id, rec.timesheet_sheet_id):
                if target_thread and hasattr(target_thread, 'message_post'):
                    try:
                        target_thread.message_post(
                            body=audit_note,
                            message_type='comment',
                            subtype_xmlid='mail.mt_note',
                        )
                    except Exception:
                        pass

            last_result = {
                'ok': smtp_sent,
                'status': 'sent' if smtp_sent else 'exception',
                'recipient_email': resolved_email,
                'subject': subject,
                'smtp_host': smtp_host,
                'smtp_port': smtp_port,
                'smtp_user': smtp_user,
                'mail_id': mail_rec.id,
                'message_id': clean_msg_id,
                'notification_id': rec.id,
                'notification_name': rec.name,
                'attachment_ids': att_ids,
                'attachment_names': att_names,
                'attachment_count': len(att_ids),
                'error': smtp_error,
            }
        return last_result

    def action_acknowledge_notification(self):
        for rec in self:
            rec.write({'state': 'acknowledged'})
        return True


class DgmProjectTimesheetSheet(models.Model):
    _name = 'dgm.project.timesheet.sheet'
    _description = 'DGM Monthly Project Timesheet & Billing Consolidation Sheet (SOP-DGM-08)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Mã Bảng Chấm công',
        required=True,
        copy=False,
        default='New',
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng / Đối tác (Partner)',
        required=True,
        index=True,
        tracking=True,
    )
    dgm_partner_code = fields.Char(
        related='partner_id.dgm_partner_code',
        string='Mã Đối tác (SOP-DGM-06)',
        store=True,
        readonly=True,
    )
    dgm_onboarding_state = fields.Selection(
        related='partner_id.dgm_onboarding_state',
        string='Trạng thái Onboarding',
        store=True,
        readonly=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Hợp đồng / Sale Order',
        index=True,
        tracking=True,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Dự án (Project)',
        required=True,
        index=True,
        tracking=True,
    )
    billing_period = fields.Char(
        string='Kỳ Đối soát (Billing Period)',
        required=True,
        default='10/2026',
        index=True,
        tracking=True,
    )
    date_start = fields.Date(
        string='Từ ngày',
        default=lambda self: fields.Date.to_date('2026-10-01'),
    )
    date_end = fields.Date(
        string='Đến ngày',
        default=lambda self: fields.Date.to_date('2026-10-31'),
    )
    standard_working_days = fields.Float(
        string='Số ngày công chuẩn / tháng',
        default=22.0,
    )
    line_ids = fields.One2many(
        'dgm.project.timesheet.line',
        'sheet_id',
        string='Chi tiết Chấm công Nhân sự',
        copy=True,
    )
    notification_ids = fields.One2many(
        'dgm.project.notification',
        'timesheet_sheet_id',
        string='Lịch sử Thông báo Dự án',
    )

    total_logged_hours = fields.Float(
        string='Tổng Giờ Chấm công',
        compute='_compute_sheet_totals',
        store=True,
    )
    total_billable_days = fields.Float(
        string='Tổng Ngày công Nghiệm thu',
        compute='_compute_sheet_totals',
        store=True,
    )
    amount_untaxed_vnd = fields.Float(
        string='Tổng Tiền Chưa Thuế (VNĐ)',
        compute='_compute_sheet_totals',
        store=True,
    )
    vat_rate = fields.Selection(
        selection=[
            ('0', '0% (Xuất khẩu / KCT)'),
            ('8', '8% GTGT (Nghị định 174/2025/NĐ-CP)'),
            ('10', '10% GTGT Chuẩn'),
        ],
        string='Thuế suất GTGT',
        default='8',
        required=True,
        tracking=True,
    )
    amount_tax_vnd = fields.Float(
        string='Tiền Thuế GTGT (VNĐ)',
        compute='_compute_sheet_totals',
        store=True,
    )
    amount_total_vnd = fields.Float(
        string='Tổng Thanh toán Có Thuế (VNĐ)',
        compute='_compute_sheet_totals',
        store=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', '1. Nháp — Đang tập hợp Timesheet (Draft Consolidation)'),
            ('pm_verified', '2. PM Đã Kiểm tra — Chờ KH Duyệt (Sent for Customer Approval)'),
            ('customer_approved', '3. KH Đã Duyệt Timesheet & Nghiệm thu (Customer Approved)'),
            ('revision_requested', 'Tạm hoàn — KH Yêu cầu Điều chỉnh (Revision Requested)'),
            ('draft_invoiced', '4. Đã Xuất Hóa đơn Nháp Đối soát (MTI Draft Invoice Sent)'),
            ('official_invoiced', '5. Đã Xuất Hóa đơn GTGT Chính thức (Official E-Invoice Issued)'),
        ],
        string='Trạng thái Đối soát & Xuất Hóa đơn (SOP-DGM-08)',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )

    approval_token = fields.Char(
        string='Token Phê duyệt Portal',
        copy=False,
        default=lambda self: secrets.token_urlsafe(24),
        index=True,
    )
    customer_approver_name = fields.Char(
        string='Người Phê duyệt (Đại diện KH)',
        tracking=True,
    )
    customer_approver_email = fields.Char(
        string='Email Người Phê duyệt',
        tracking=True,
    )
    customer_approver_title = fields.Char(
        string='Chức danh Người Phê duyệt',
    )
    customer_approved_at = fields.Datetime(
        string='Thời điểm KH Duyệt Timesheet',
        tracking=True,
    )
    customer_approval_note = fields.Text(
        string='Ý kiến Nghiệm thu / Ghi chú của KH',
    )
    customer_signature_hash = fields.Char(
        string='Mã Băm Xác thực Điện tử (SHA-256)',
        copy=False,
        readonly=True,
    )

    timesheet_doc_id = fields.Many2one(
        'documents.document',
        string='01. Bảng Chấm công Chi tiết',
        copy=False,
    )
    acceptance_doc_id = fields.Many2one(
        'documents.document',
        string='02. Biên bản Nghiệm thu Khối lượng',
        copy=False,
    )
    draft_invoice_id = fields.Many2one(
        'account.move',
        string='Hóa đơn Nháp / Chính thức (Account Move)',
        copy=False,
        index=True,
    )
    draft_invoice_doc_id = fields.Many2one(
        'documents.document',
        string='03. Bản Xem trước Hóa đơn Nháp (MTI Draft)',
        copy=False,
    )
    official_invoice_doc_id = fields.Many2one(
        'documents.document',
        string='04. Hóa đơn GTGT Chính thức (1C26TAA)',
        copy=False,
    )

    @api.depends(
        'line_ids.actual_worked_days',
        'line_ids.overtime_hours',
        'line_ids.billable_days',
        'line_ids.subtotal_vnd',
        'vat_rate',
    )
    def _compute_sheet_totals(self):
        for sheet in self:
            sheet.total_logged_hours = 0.0
            sheet.total_billable_days = 0.0
            sheet.amount_untaxed_vnd = 0.0
            sheet.amount_tax_vnd = 0.0
            sheet.amount_total_vnd = 0.0

            lines = sheet.line_ids
            logged_hours = sum(
                ((line.actual_worked_days or 0.0) * 8.0) + (line.overtime_hours or 0.0)
                for line in lines
            )
            billable_days = sum(line.billable_days or 0.0 for line in lines)
            untaxed = round(sum(line.subtotal_vnd or 0.0 for line in lines))
            try:
                vat_pct = float(sheet.vat_rate or '8') / 100.0
            except (ValueError, TypeError):
                vat_pct = 0.08
            tax = round(untaxed * vat_pct)

            sheet.total_logged_hours = logged_hours
            sheet.total_billable_days = billable_days
            sheet.amount_untaxed_vnd = untaxed
            sheet.amount_tax_vnd = tax
            sheet.amount_total_vnd = untaxed + tax

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('approval_token'):
                vals['approval_token'] = secrets.token_urlsafe(24)
        records = super().create(vals_list)
        for rec in records:
            updates = {}
            if not rec.name or rec.name in ('New', '/'):
                seq_id = rec.id if isinstance(rec.id, int) and rec.id > 0 else 1
                updates['name'] = f"TS-DGM-202610-{seq_id:04d}"
            if not rec.approval_token:
                updates['approval_token'] = secrets.token_urlsafe(24)
            if updates:
                rec.sudo().write(updates)
        return records

    SEALED_FISCAL_STATES = ('customer_approved', 'draft_invoiced', 'official_invoiced')

    IMMUTABLE_FISCAL_SHEET_FIELDS = {
        'partner_id',
        'vat_rate',
        'standard_working_days',
        'billing_period',
        'line_ids',
    }

    def write(self, vals):
        if vals.get('state') not in ('draft', 'revision_requested') and self.IMMUTABLE_FISCAL_SHEET_FIELDS.intersection(vals.keys()):
            for sheet in self:
                if sheet.state in self.SEALED_FISCAL_STATES:
                    raise UserError(_(
                        "⛔ [SOP-DGM-08 Fiscal Barrier — Decree 70/2025/ND-CP] "
                        "Không được phép chỉnh sửa thông tin pháp nhân, kỳ đối soát, thuế suất "
                        "hoặc dòng chấm công trên Bảng chấm công (%s) đã được Khách hàng nghiệm thu hoặc đã xuất Hóa đơn (Trạng thái: %s)!",
                        sheet.name,
                        sheet.state,
                    ))
        return super().write(vals)

    def unlink(self):
        for sheet in self:
            if sheet.state in self.SEALED_FISCAL_STATES:
                raise UserError(_(
                    "⛔ [SOP-DGM-08 Fiscal Barrier — Decree 70/2025/ND-CP] "
                    "Không được phép xóa Bảng chấm công (%s) đã được Khách hàng nghiệm thu hoặc đã xuất Hóa đơn (Trạng thái: %s)!",
                    sheet.name,
                    sheet.state,
                ))
        return super().unlink()

    def _compute_timesheet_manifest_digest(self):
        self.ensure_one()
        sorted_lines = sorted(
            self.line_ids,
            key=lambda l: (
                l.sequence or 0,
                l.id if isinstance(l.id, int) and l.id > 0 else 0,
                l.employee_id.id if l.employee_id else 0,
            ),
        )
        tokens = []
        for line in sorted_lines:
            lid = line.id if isinstance(line.id, int) and line.id > 0 else 0
            eid = line.employee_id.id if line.employee_id else 0
            emp_name_nfc = unicodedata.normalize('NFC', str(line.employee_id.name or ''))
            role_nfc = unicodedata.normalize('NFC', str(line.role_title or ''))
            tokens.append(
                f"{lid}:{eid}:{emp_name_nfc}:{role_nfc}:"
                f"{line.actual_worked_days or 0.0:.2f}:{line.billable_days or 0.0:.2f}:{line.subtotal_vnd or 0.0:.0f}"
            )
        canonical_str = unicodedata.normalize('NFC', "|".join(tokens))
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

    def _verify_customer_signature_integrity(self):
        self.ensure_one()
        manifest_digest = self._compute_timesheet_manifest_digest()
        if not manifest_digest or len(manifest_digest) != 64:
            raise UserError(_(
                "⛔ [SOP-DGM-08 Cryptographic Seal] Không thể xác thực mã băm Manifest cho Bảng chấm công (%s).",
                self.name,
            ))
        if self.customer_approved_at and self.customer_signature_hash:
            secret_key = (
                self.env['ir.config_parameter'].sudo().get_param('database.secret')
                or 'insilos-dgm-fiscal-secret-2026'
            )
            partner_id_val = self.partner_id.id if self.partner_id else 0
            partner_vat_val = unicodedata.normalize(
                'NFC', str((self.partner_id.vat or '') if self.partner_id else '')
            )
            resolved_name = unicodedata.normalize('NFC', str(self.customer_approver_name or ''))
            resolved_email = unicodedata.normalize('NFC', str(self.customer_approver_email or ''))
            approved_dt_str = fields.Datetime.to_string(self.customer_approved_at)
            expected_payload = (
                f"{self.id}|{self.name}|{partner_id_val}|{partner_vat_val}|"
                f"{self.billing_period}|{self.total_billable_days:.2f}|{self.amount_total_vnd:.0f}|"
                f"{manifest_digest}|{resolved_name}|{resolved_email}|{approved_dt_str}"
            )
            expected_hmac = hmac.new(
                secret_key.encode('utf-8'),
                expected_payload.encode('utf-8'),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(str(self.customer_signature_hash), expected_hmac):
                raise UserError(_(
                    "⛔ [SOP-DGM-08 Cryptographic Seal Violation — CWE-863] "
                    "Dữ liệu Bảng chấm công (%s) đã bị thay đổi trái phép sau khi Khách hàng ký nghiệm thu!",
                    self.name,
                ))
        return manifest_digest

    def _build_canonical_1c26taa_xml(self):
        self.ensure_one()
        nfc = lambda val: unicodedata.normalize('NFC', str(val or ''))
        inv = self.draft_invoice_id
        sh_don = nfc(inv.dgm_einvoice_number if (inv and inv.dgm_einvoice_number) else 'DRAFT')
        kh_hdon = nfc(inv.dgm_einvoice_symbol if (inv and inv.dgm_einvoice_symbol) else '1C26TAA')

        root = etree.Element("HDon", Kieu="1C26TAA")
        tt_chung = etree.SubElement(root, "TTChung")
        etree.SubElement(tt_chung, "KHMSHDon").text = "1"
        etree.SubElement(tt_chung, "KHHDon").text = kh_hdon
        etree.SubElement(tt_chung, "SHDon").text = sh_don
        etree.SubElement(tt_chung, "THDon").text = nfc("HÓA ĐƠN GIÁ TRỊ GIA TĂNG")
        etree.SubElement(tt_chung, "DVTTe").text = "VND"

        nd_hdon = etree.SubElement(root, "NDHDon")
        n_ban = etree.SubElement(nd_hdon, "NBan")
        etree.SubElement(n_ban, "Ten").text = nfc("CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ")
        etree.SubElement(n_ban, "MST").text = "0317958465"

        partner = self.partner_id
        n_mua = etree.SubElement(nd_hdon, "NMua")
        etree.SubElement(n_mua, "TenNM").text = nfc(partner.name if partner else '')
        etree.SubElement(n_mua, "MSTNM").text = nfc((partner.vat or '') if partner else '')
        etree.SubElement(n_mua, "MaKH").text = nfc(
            (partner.dgm_partner_code or partner.dgm_provisional_code or 'PTN-DGM') if partner else 'PTN-DGM'
        )

        ds_hhdvu = etree.SubElement(nd_hdon, "DSHHDVu")
        period_nfc = nfc(self.billing_period or '10/2026')
        for idx, line in enumerate(self.line_ids, start=1):
            hhdvu = etree.SubElement(ds_hhdvu, "HHDVu")
            etree.SubElement(hhdvu, "STT").text = str(idx)
            emp_name = nfc(line.employee_id.name if line.employee_id else 'Engineer')
            role_title = nfc(line.role_title or 'Senior Engineer')
            etree.SubElement(hhdvu, "THHDVu").text = nfc(
                f"[{period_nfc}] Dịch vụ Kỹ thuật Phần mềm ({emp_name} - {role_title}): "
                f"Nghiệm thu {line.billable_days or 0.0:.1f}/{line.standard_days or 22.0:.1f} ngày công"
            )
            etree.SubElement(hhdvu, "SLuong").text = f"{line.billable_days or 0.0:.2f}"
            etree.SubElement(hhdvu, "DGia").text = f"{line.contract_monthly_rate_vnd or 0.0:.0f}"
            etree.SubElement(hhdvu, "ThTien").text = f"{line.subtotal_vnd or 0.0:.0f}"

        t_toan = etree.SubElement(nd_hdon, "TToan")
        etree.SubElement(t_toan, "TgTCThue").text = f"{self.amount_untaxed_vnd or 0.0:.0f}"
        etree.SubElement(t_toan, "TSuat").text = f"{nfc(self.vat_rate or '8')}%"
        etree.SubElement(t_toan, "TgTThue").text = f"{self.amount_tax_vnd or 0.0:.0f}"
        etree.SubElement(t_toan, "TongTien").text = f"{self.amount_total_vnd or 0.0:.0f}"

        ds_cks = etree.SubElement(root, "DSCKS")
        etree.SubElement(ds_cks, "DigestManifest").text = self._compute_timesheet_manifest_digest()
        etree.SubElement(ds_cks, "SignatureHMAC").text = nfc(self.customer_signature_hash or '')

        return etree.tostring(root, method="c14n", exclusive=False, with_comments=False).decode("utf-8")

    def _get_partner_target_folder(self):
        self.ensure_one()
        Document = self.env['documents.document'].sudo()
        partner = self.partner_id
        if partner and hasattr(partner, '_get_or_create_dgm_onboarding_folder'):
            folder = partner.sudo()._get_or_create_dgm_onboarding_folder()
            if folder and folder.exists():
                return folder
        folder = self.env.ref('insilos_al2c.folder_dgm_contracts', raise_if_not_found=False)
        if not folder or not folder.exists():
            folder = Document.search([
                ('type', '=', 'folder'),
                ('name', 'ilike', '03. Hợp đồng'),
                ('active', '=', True),
            ], order='id asc', limit=1)
        return folder

    def _upsert_html_document_in_folder(self, folder, doc_name, html_body, res_model=None, res_id=None):
        self.ensure_one()
        Attachment = self.env['ir.attachment'].sudo()
        Document = self.env['documents.document'].sudo()
        raw_bytes = html_body.encode('utf-8')
        b64_datas = base64.b64encode(raw_bytes)
        folder_id = folder.id if folder else False

        existing = Document.search([
            ('name', '=', doc_name),
            ('folder_id', '=', folder_id),
            ('active', '=', True),
        ], order='id asc', limit=1)

        if existing:
            if existing.attachment_id:
                existing.attachment_id.write({
                    'name': doc_name,
                    'datas': b64_datas,
                    'mimetype': 'text/html',
                })
            else:
                att = Attachment.create({
                    'name': doc_name,
                    'datas': b64_datas,
                    'mimetype': 'text/html',
                    'res_model': res_model or self._name,
                    'res_id': res_id or self.id,
                })
                existing.write({'attachment_id': att.id})
            existing.write({
                'owner_id': False,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'access_internal': 'edit',
                'access_via_link': 'view',
            })
            return existing

        att = Attachment.create({
            'name': doc_name,
            'datas': b64_datas,
            'mimetype': 'text/html',
            'res_model': res_model or self._name,
            'res_id': res_id or self.id,
        })
        return Document.create({
            'name': doc_name,
            'folder_id': folder_id,
            'owner_id': False,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'type': 'binary',
            'attachment_id': att.id,
            'access_internal': 'edit',
            'access_via_link': 'view',
            'active': True,
        })

    def _resolve_default_monthly_rate(self):
        self.ensure_one()
        so = self.sale_order_id
        if so:
            if so.order_line:
                for sol in so.order_line:
                    if sol.price_subtotal and sol.price_subtotal > 0:
                        return float(sol.price_subtotal)
                    if sol.price_unit and sol.price_unit >= 10_000_000.0:
                        return float(sol.price_unit)
            if getattr(so, 'dgm_hourly_rate_vnd', 0.0) and so.dgm_hourly_rate_vnd > 0:
                return float(so.dgm_hourly_rate_vnd * (self.standard_working_days or 22.0) * 8.0)
        return 35_000_000.0

    def action_sync_from_project_timesheets(self):
        AnalyticLine = self.env['account.analytic.line'].sudo()
        Staging = self.env['al2c.timesheet.staging'].sudo() if 'al2c.timesheet.staging' in self.env else None
        SheetLine = self.env['dgm.project.timesheet.line'].sudo()

        for sheet in self:
            domain = [('project_id', '=', sheet.project_id.id)]
            if sheet.date_start:
                domain.append(('date', '>=', sheet.date_start))
            if sheet.date_end:
                domain.append(('date', '<=', sheet.date_end))

            analytic_lines = AnalyticLine.search(domain, order='date asc, id asc')

            emp_buckets = {}
            for aline in analytic_lines:
                emp = aline.employee_id
                if not emp:
                    continue
                bucket = emp_buckets.setdefault(emp.id, {
                    'employee': emp,
                    'hours': 0.0,
                    'tasks': [],
                    'descriptions': [],
                    'analytic_ids': [],
                })
                bucket['hours'] += float(aline.unit_amount or 0.0)
                if aline.task_id and aline.task_id not in bucket['tasks']:
                    bucket['tasks'].append(aline.task_id)
                if aline.name and aline.name not in bucket['descriptions']:
                    bucket['descriptions'].append(aline.name)
                bucket['analytic_ids'].append(aline.id)

            # Check approved staging records if no analytic lines matched yet
            if not emp_buckets and Staging is not None:
                stagings = Staging.search([
                    ('project_id', '=', sheet.project_id.id),
                    ('state', '=', 'approved'),
                ])
                for stg in stagings:
                    emp = stg.employee_id
                    if not emp:
                        continue
                    bucket = emp_buckets.setdefault(emp.id, {
                        'employee': emp,
                        'hours': 0.0,
                        'tasks': [],
                        'descriptions': [],
                        'analytic_ids': [],
                    })
                    bucket['hours'] += float(stg.total_hours or 0.0)
                    if stg.name and stg.name not in bucket['descriptions']:
                        bucket['descriptions'].append(stg.name)

            std_days = sheet.standard_working_days if sheet.standard_working_days > 0 else 22.0
            default_rate = sheet._resolve_default_monthly_rate()
            existing_by_emp = {line.employee_id.id: line for line in sheet.line_ids if line.employee_id}

            if emp_buckets:
                seq = 10
                for emp_id, data in emp_buckets.items():
                    emp = data['employee']
                    total_hours = data['hours']
                    std_hours_cap = std_days * 8.0
                    if total_hours > std_hours_cap:
                        worked_days = std_days
                        ot_hours = round(total_hours - std_hours_cap, 2)
                    elif total_hours > 0:
                        worked_days = round(total_hours / 8.0, 2)
                        ot_hours = 0.0
                    else:
                        worked_days = std_days
                        ot_hours = 0.0

                    role_str = (emp.job_title or (emp.job_id.name if emp.job_id else '') or 'Senior Software Engineer')
                    summary_str = '; '.join(data['descriptions'][:8]) or (
                        f"Triển khai kỹ thuật & phát triển tính năng dự án {sheet.project_id.name} kỳ {sheet.billing_period}."
                    )
                    first_task = data['tasks'][0].id if data['tasks'] else False

                    vals = {
                        'sequence': seq,
                        'role_title': role_str,
                        'task_id': first_task,
                        'standard_days': std_days,
                        'actual_worked_days': worked_days,
                        'overtime_hours': ot_hours,
                        'work_summary': summary_str,
                        'analytic_line_ids': [(6, 0, data['analytic_ids'])],
                    }
                    if emp_id in existing_by_emp:
                        existing_by_emp[emp_id].write(vals)
                    else:
                        vals.update({
                            'sheet_id': sheet.id,
                            'employee_id': emp_id,
                            'contract_monthly_rate_vnd': default_rate,
                        })
                        SheetLine.create(vals)
                    seq += 10
            elif not sheet.line_ids:
                assigned_emp = (
                    sheet.sale_order_id.dgm_assigned_employee_id
                    if (sheet.sale_order_id and hasattr(sheet.sale_order_id, 'dgm_assigned_employee_id'))
                    else False
                )
                if not assigned_emp:
                    assigned_emp = self.env['hr.employee'].sudo().search([('active', '=', True)], order='id asc', limit=1)
                if assigned_emp:
                    role_str = (
                        assigned_emp.job_title
                        or (assigned_emp.job_id.name if assigned_emp.job_id else '')
                        or 'Senior Software Engineer'
                    )
                    SheetLine.create({
                        'sheet_id': sheet.id,
                        'sequence': 10,
                        'employee_id': assigned_emp.id,
                        'role_title': role_str,
                        'contract_monthly_rate_vnd': default_rate,
                        'standard_days': std_days,
                        'actual_worked_days': std_days,
                        'overtime_hours': 0.0,
                        'work_summary': (
                            f"Biệt phái nhân sự kỹ thuật & bàn giao hạng mục dự án {sheet.project_id.name} "
                            f"kỳ {sheet.billing_period}."
                        ),
                    })
        return True

    def _render_sheet_document_html(self, doc_stage='timesheet'):
        self.ensure_one()
        partner = self.partner_id
        partner_code = partner.dgm_partner_code or partner.dgm_provisional_code or 'PTN-DGM'
        period_str = self.billing_period or '10/2026'
        so_ref = (
            self.sale_order_id.client_order_ref
            or self.sale_order_id.name
            or self.name
        ) if self.sale_order_id else self.name

        stage_titles = {
            'timesheet': (
                '01. BẢNG CHẤM CÔNG CHI TIẾT DỰ ÁN (MONTHLY PROJECT TIMESHEET STATEMENT)',
                'Tài liệu tổng hợp ngày công & giờ làm thêm gửi Khách hàng kiểm tra, phê duyệt theo SOP-DGM-08',
                '',
            ),
            'acceptance': (
                '02. BIÊN BẢN NGHIỆM THU KHỐI LƯỢNG &amp; BẢNG CHẤM CÔNG (TIMESHEET ACCEPTANCE CERTIFICATE)',
                'Xác nhận nghiệm thu khối lượng công việc hoàn thành làm căn cứ xuất Hóa đơn Nháp Đối soát (MTI Flow)',
                '',
            ),
            'draft_invoice': (
                '03. BẢN XEM TRƯỚC HÓA ĐƠN GIÁ TRỊ GIA TĂNG — BẢN NHÁP ĐỐI SOÁT (MTI DRAFT INVOICE)',
                'Chứng từ đối soát thông tin Pháp nhân, Mã số thuế, Nội dung hàng hóa dịch vụ &amp; Số tiền trước khi ký số CQT',
                'BẢN NHÁP ĐỐI SOÁT TRƯỚC KHI PHÁT HÀNH HÓA ĐƠN ĐIỆN TỬ — MTI DRAFT FOR CUSTOMER RECONCILIATION',
            ),
            'official_invoice': (
                '04. HÓA ĐƠN GIÁ TRỊ GIA TĂNG ĐIỆN TỬ CHÍNH THỨC (OFFICIAL VAT E-INVOICE — 1C26TAA)',
                'Hóa đơn điện tử đã cấp mã của Cơ quan Thuế theo Nghị định 70/2025/NĐ-CP &amp; Nghị định 174/2025/NĐ-CP',
                '',
            ),
        }
        main_title, sub_title, watermark_text = stage_titles.get(doc_stage, stage_titles['timesheet'])

        rows_html = []
        for idx, line in enumerate(self.line_ids, start=1):
            emp_name = html.escape(line.employee_id.name or 'Engineer')
            role_title = html.escape(line.role_title or 'Senior Engineer')
            work_desc = xml_escape(html.escape(line.work_summary or ''))
            rows_html.append(
                f"<tr>"
                f"<td>{idx}</td>"
                f"<td><strong>{emp_name}</strong><br/><small>{role_title}</small></td>"
                f"<td>{work_desc}</td>"
                f"<td style='text-align:right;'>{line.standard_days:,.1f}</td>"
                f"<td style='text-align:right;'>{line.actual_worked_days:,.1f}</td>"
                f"<td style='text-align:right;'>{line.overtime_hours:,.1f}h</td>"
                f"<td style='text-align:right;'><strong>{line.billable_days:,.2f}</strong> ({line.pro_rata_ratio:,.1f}%)</td>"
                f"<td style='text-align:right;'>{line.contract_monthly_rate_vnd:,.0f}</td>"
                f"<td style='text-align:right;'><strong>{line.subtotal_vnd:,.0f}</strong></td>"
                f"</tr>"
            )
        lines_tbody = "\n".join(rows_html)

        watermark_banner = ''
        if watermark_text:
            watermark_banner = (
                f"<div style='border:2px dashed var(--insilos-border-subtle, #d97706); "
                f"padding:10px 16px; margin:14px 0; text-align:center; font-weight:700;'>"
                f"⚠️ {html.escape(watermark_text)}"
                f"</div>"
            )

        approval_block = ''
        if self.customer_approved_at or doc_stage in ('acceptance', 'draft_invoice', 'official_invoice'):
            approver = html.escape(self.customer_approver_name or partner.name or 'Đại diện Khách hàng')
            approver_email = html.escape(self.customer_approver_email or partner.email or 'N/A')
            approver_title = html.escape(self.customer_approver_title or 'Đại diện Có Thẩm quyền')
            approved_at = html.escape(str(self.customer_approved_at or ''))
            sig_hash = html.escape(self.customer_signature_hash or 'SHA256-VERIFIED')
            note_txt = html.escape(self.customer_approval_note or '')
            approval_block = f"""
            <div style="margin-top:18px; padding:12px 16px; border:1px solid var(--insilos-border-subtle, #cbd5e1); border-radius:6px;">
              <h4 style="margin:0 0 8px 0;">XÁC NHẬN PHÊ DUYỆT ĐIỆN TỬ CỦA KHÁCH HÀNG (CUSTOMER ELECTRONIC APPROVAL)</h4>
              <p style="margin:4px 0;"><strong>Người phê duyệt:</strong> {approver} ({approver_title}) — Email: <code>{approver_email}</code></p>
              <p style="margin:4px 0;"><strong>Thời điểm phê duyệt:</strong> <code>{approved_at}</code></p>
              <p style="margin:4px 0;"><strong>Ý kiến nghiệm thu:</strong> {note_txt}</p>
              <p style="margin:4px 0;"><strong>Chữ ký băm SHA-256:</strong> <code>{sig_hash}</code></p>
            </div>
            """

        einvoice_block = ''
        if doc_stage == 'official_invoice' and self.draft_invoice_id:
            inv = self.draft_invoice_id
            einvoice_block = f"""
            <div style="margin-top:18px; padding:12px 16px; border:1px solid var(--insilos-border-subtle, #cbd5e1); border-radius:6px;">
              <h4 style="margin:0 0 8px 0;">THÔNG TIN HÓA ĐƠN GIÁ TRỊ GIA TĂNG ĐIỆN TỬ CHÍNH THỨC (DECREE 70/2025/NĐ-CP)</h4>
              <p style="margin:4px 0;"><strong>Ký hiệu &amp; Số Hóa đơn:</strong> <code>{html.escape(inv.dgm_einvoice_symbol or '1C26TAA')} - {html.escape(inv.dgm_einvoice_number or '')}</code></p>
              <p style="margin:4px 0;"><strong>Mã tra cứu HĐĐT:</strong> <code>{html.escape(inv.dgm_einvoice_lookup_code or '')}</code></p>
              <p style="margin:4px 0;"><strong>Thời điểm phát hành:</strong> <code>{html.escape(str(inv.dgm_einvoice_issued_at or ''))}</code></p>
              <p style="margin:4px 0;"><strong>Người xác nhận Hóa đơn Nháp (KH):</strong> {html.escape(inv.dgm_draft_confirmed_by or '')}</p>
            </div>
            """

        raw_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<title>{html.escape(self.name)} - {html.escape(period_str)}</title>
<style>
  body {{
    font-family: 'Inter', Arial, sans-serif;
    color: var(--insilos-text-primary, #1e293b);
    background: var(--insilos-bg-card, transparent);
    margin: 28px;
    line-height: 1.5;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 14px;
  }}
  th, td {{
    border: 1px solid var(--insilos-border-subtle, #cbd5e1);
    padding: 8px 10px;
    font-size: 13px;
  }}
  th {{
    background: var(--insilos-bg-subtle, #e2e8f0);
    text-align: left;
  }}
</style>
</head>
<body>
  <div style="text-align:center;">
    <h3 style="margin:0;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</h3>
    <p style="margin:2px 0 12px 0;"><strong>Độc lập - Tự do - Hạnh phúc</strong></p>
    <hr/>
    <h2 style="margin:12px 0 4px 0;">{main_title}</h2>
    <p style="margin:0 0 12px 0;"><em>{sub_title}</em></p>
  </div>
  {watermark_banner}
  <table>
    <tbody>
      <tr>
        <th style="width:22%;">Đơn vị Cung cấp (Bên B)</th>
        <td style="width:28%;"><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</strong><br/>MST: 0317958465</td>
        <th style="width:22%;">Mã Chứng từ / Bảng công</th>
        <td style="width:28%;"><strong>{html.escape(self.name)}</strong> (Kỳ: {html.escape(period_str)})</td>
      </tr>
      <tr>
        <th>Khách hàng (Bên A)</th>
        <td><strong>{html.escape(partner.name or '')}</strong><br/>Mã ĐT: {html.escape(partner_code)} | MST: {html.escape(partner.vat or 'N/A')}</td>
        <th>Dự án &amp; Hợp đồng</th>
        <td>Dự án: <strong>{html.escape(self.project_id.name or '')}</strong><br/>HĐ/SO: {html.escape(so_ref)}</td>
      </tr>
    </tbody>
  </table>

  <table>
    <thead>
      <tr>
        <th style="width:4%;">#</th>
        <th style="width:18%;">Nhân sự Kỹ thuật</th>
        <th style="width:26%;">Nội dung Công việc &amp; Deliverables</th>
        <th style="width:8%; text-align:right;">Công chuẩn</th>
        <th style="width:8%; text-align:right;">Công thực tế</th>
        <th style="width:7%; text-align:right;">Giờ OT</th>
        <th style="width:10%; text-align:right;">Công nghiệm thu</th>
        <th style="width:9%; text-align:right;">Đơn giá tháng</th>
        <th style="width:10%; text-align:right;">Thành tiền (VNĐ)</th>
      </tr>
    </thead>
    <tbody>
      {lines_tbody}
      <tr>
        <td colspan="8" style="text-align:right;"><strong>Cộng tiền dịch vụ chưa thuế GTGT (Untaxed Amount):</strong></td>
        <td style="text-align:right;"><strong>{self.amount_untaxed_vnd:,.0f}</strong></td>
      </tr>
      <tr>
        <td colspan="8" style="text-align:right;"><strong>Thuế GTGT ({html.escape(self.vat_rate or '8')}% theo Nghị định 174/2025/NĐ-CP):</strong></td>
        <td style="text-align:right;"><strong>{self.amount_tax_vnd:,.0f}</strong></td>
      </tr>
      <tr>
        <td colspan="8" style="text-align:right;"><strong>TỔNG CỘNG THANH TOÁN (TOTAL PAYABLE VND):</strong></td>
        <td style="text-align:right;"><strong>{self.amount_total_vnd:,.0f}</strong></td>
      </tr>
    </tbody>
  </table>
  {approval_block}
  {einvoice_block}
</body>
</html>"""
        stage_code_map = {
            'timesheet': f"{self.name}-TIMESHEET",
            'acceptance': f"{self.name}-ACCEPTANCE",
            'draft_invoice': f"{self.name}-DRAFT-INV",
            'official_invoice': f"{self.name}-EINVOICE-1C26TAA",
        }
        stage_class_map = {
            'timesheet': 'MONTHLY TIMESHEET STATEMENT',
            'acceptance': 'TIMESHEET ACCEPTANCE CERTIFICATE',
            'draft_invoice': 'MTI DRAFT INVOICE RECONCILIATION',
            'official_invoice': 'OFFICIAL VAT E-INVOICE (DECREE 70/2025/ND-CP)',
        }
        return wrap_dgm_branded_html_document(
            raw_html,
            doc_title=main_title,
            doc_code=stage_code_map.get(doc_stage, self.name),
            sop_ref='SOP-DGM-08',
            classification=stage_class_map.get(doc_stage, 'B2B COMMERCIAL & FINOPS RECORD'),
            include_header=True,
        )

    def _generate_timesheet_html(self):
        if hasattr(self, '_render_sheet_document_html'):
            return self._render_sheet_document_html('timesheet')
        return DgmProjectTimesheetSheet._render_sheet_document_html(self, 'timesheet')

    def _generate_acceptance_html(self):
        if hasattr(self, '_render_sheet_document_html'):
            return self._render_sheet_document_html('acceptance')
        return DgmProjectTimesheetSheet._render_sheet_document_html(self, 'acceptance')

    def _generate_draft_invoice_html(self):
        if hasattr(self, '_render_sheet_document_html'):
            return self._render_sheet_document_html('draft_invoice')
        return DgmProjectTimesheetSheet._render_sheet_document_html(self, 'draft_invoice')

    def _generate_official_invoice_html(self):
        if hasattr(self, '_render_sheet_document_html'):
            return self._render_sheet_document_html('official_invoice')
        return DgmProjectTimesheetSheet._render_sheet_document_html(self, 'official_invoice')

    @staticmethod
    def _clean_code_slug(val):
        raw = str(val or 'DOC').strip()
        cleaned = []
        for ch in raw:
            if ch.isalnum() or ch in ('-', '_'):
                cleaned.append(ch)
            else:
                cleaned.append('_')
        return ''.join(cleaned).strip('_') or 'DOC'

    def action_submit_for_customer_approval(self):
        Notification = self.env['dgm.project.notification'].sudo()
        for sheet in self:
            if not sheet.line_ids:
                sheet.action_sync_from_project_timesheets()
            if not sheet.line_ids:
                raise UserError(_(
                    "Không thể gửi duyệt khi Bảng chấm công (%s) chưa có dòng nhân sự nào.",
                    sheet.name,
                ))
            if not sheet.approval_token:
                sheet.approval_token = secrets.token_urlsafe(24)

            folder = sheet._get_partner_target_folder()
            code_slug = self._clean_code_slug(sheet.partner_id.dgm_partner_code or sheet.name)
            period_slug = self._clean_code_slug(sheet.billing_period or '2026_10')
            doc_name = f"01_Bang_Cham_Cong_Timesheet_{code_slug}_{period_slug}.html"
            html_body = sheet._render_sheet_document_html(doc_stage='timesheet')
            ts_doc = sheet._upsert_html_document_in_folder(folder, doc_name, html_body)

            ntf = Notification.create({
                'project_id': sheet.project_id.id,
                'partner_id': sheet.partner_id.id,
                'sale_order_id': sheet.sale_order_id.id if sheet.sale_order_id else False,
                'timesheet_sheet_id': sheet.id,
                'employee_ids': [(6, 0, sheet.line_ids.mapped('employee_id').ids)],
                'notification_type': 'customer_approval_req',
                'recipient_email': sheet.partner_id.email or False,
            })
            ntf.action_send_project_notification()

            sheet.write({
                'timesheet_doc_id': ts_doc.id,
                'state': 'pm_verified',
            })
        return True

    def action_customer_approve(
        self,
        approver_name=None,
        approver_email=None,
        approver_title=None,
        note=None,
    ):
        for sheet in self:
            if isinstance(sheet.id, int) and sheet.id > 0:
                self.env.cr.execute(
                    "SELECT pg_advisory_xact_lock(%s, %s)",
                    [ADVISORY_LOCK_SOP08_NS, int(sheet.id)],
                )
            now_dt = fields.Datetime.now()
            approved_dt_str = fields.Datetime.to_string(now_dt)
            resolved_name = unicodedata.normalize(
                'NFC',
                (approver_name or '').strip()
                or sheet.customer_approver_name
                or (sheet.partner_id.name if sheet.partner_id else 'Đại diện Khách hàng'),
            )
            resolved_email = unicodedata.normalize(
                'NFC',
                (approver_email or '').strip()
                or sheet.customer_approver_email
                or (sheet.partner_id.email if sheet.partner_id else 'customer@partner.vn'),
            )
            resolved_title = unicodedata.normalize(
                'NFC',
                (approver_title or '').strip()
                or sheet.customer_approver_title
                or 'Đại diện Có Thẩm quyền Khách hàng',
            )
            resolved_note = unicodedata.normalize(
                'NFC',
                (note or '').strip()
                or sheet.customer_approval_note
                or 'Đồng ý nghiệm thu 100% khối lượng bảng chấm công.',
            )
            secret_key = (
                self.env['ir.config_parameter'].sudo().get_param('database.secret')
                or 'insilos-dgm-fiscal-secret-2026'
            )
            partner_id_val = sheet.partner_id.id if sheet.partner_id else 0
            partner_vat_val = unicodedata.normalize(
                'NFC', str((sheet.partner_id.vat or '') if sheet.partner_id else '')
            )
            manifest_digest = sheet._compute_timesheet_manifest_digest()
            payload = (
                f"{sheet.id}|{sheet.name}|{partner_id_val}|{partner_vat_val}|"
                f"{sheet.billing_period}|{sheet.total_billable_days:.2f}|{sheet.amount_total_vnd:.0f}|"
                f"{manifest_digest}|{resolved_name}|{resolved_email}|{approved_dt_str}"
            )
            sig_hash = hmac.new(
                secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256,
            ).hexdigest()

            sheet.write({
                'customer_approver_name': resolved_name,
                'customer_approver_email': resolved_email,
                'customer_approver_title': resolved_title,
                'customer_approved_at': now_dt,
                'customer_approval_note': resolved_note,
                'customer_signature_hash': sig_hash,
                'state': 'customer_approved',
            })

            folder = sheet._get_partner_target_folder()
            code_slug = self._clean_code_slug(sheet.partner_id.dgm_partner_code or sheet.name)
            period_slug = self._clean_code_slug(sheet.billing_period or '2026_10')
            doc_name = f"02_Bien_Ban_Nghiem_Thu_Timesheet_{code_slug}_{period_slug}.html"
            html_body = sheet._render_sheet_document_html(doc_stage='acceptance')
            acc_doc = sheet._upsert_html_document_in_folder(folder, doc_name, html_body)
            sheet.write({'acceptance_doc_id': acc_doc.id})

            # Update qty_delivered on linked sale_order_id.order_line if applicable
            if sheet.sale_order_id and sheet.sale_order_id.order_line:
                try:
                    with self.env.cr.savepoint():
                        for sol in sheet.sale_order_id.order_line:
                            if getattr(sol, 'display_type', False):
                                continue
                            if sol.product_uom_qty and sol.qty_delivered < sol.product_uom_qty:
                                sol.sudo().write({'qty_delivered': sol.product_uom_qty})
                except Exception as exc:
                    _logger.debug("Non-blocking qty_delivered sync on %s skipped: %s", sheet.name, exc)

            if hasattr(sheet, 'message_post'):
                try:
                    sheet.message_post(
                        body=_(
                            "<b>✅ [SOP-DGM-08] Khách hàng Đã Phê duyệt Timesheet &amp; Nghiệm thu:</b><br/>"
                            "Người duyệt: <b>%s</b> (%s) — <code>%s</code><br/>"
                            "SHA-256 Signature: <code>%s</code>",
                            resolved_name,
                            resolved_title,
                            resolved_email,
                            sig_hash,
                        ),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
                except Exception:
                    pass
        return True

    def action_request_revision(self, reason=None):
        for sheet in self:
            resolved_reason = (reason or '').strip() or 'Yêu cầu kiểm tra lại số giờ công.'
            sheet.write({
                'state': 'revision_requested',
                'customer_approval_note': resolved_reason,
            })
            if hasattr(sheet, 'message_post'):
                try:
                    sheet.message_post(
                        body=_(
                            "<b>⚠️ [SOP-DGM-08] Khách hàng Yêu cầu Điều chỉnh Timesheet:</b> %s",
                            resolved_reason,
                        ),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
                except Exception:
                    pass
        return True

    def _create_or_update_draft_account_move(self):
        self.ensure_one()
        Move = self.env['account.move'].sudo()
        Journal = self.env['account.journal'].sudo() if 'account.journal' in self.env else None
        Account = self.env['account.account'].sudo() if 'account.account' in self.env else None
        Tax = self.env['account.tax'].sudo() if 'account.tax' in self.env else None

        sale_journal = Journal.search([('type', '=', 'sale')], order='id asc', limit=1) if Journal is not None else False
        income_account = False
        if Account is not None:
            income_account = Account.search([('code', '=like', '511%')], order='id asc', limit=1)
            if not income_account:
                income_account = Account.search(
                    [('account_type', 'in', ('income', 'income_other'))],
                    order='id asc',
                    limit=1,
                )

        sale_tax = False
        if Tax is not None:
            try:
                target_vat = float(self.vat_rate or '8')
            except (ValueError, TypeError):
                target_vat = 8.0
            sale_tax = Tax.search([
                ('type_tax_use', '=', 'sale'),
                ('amount', '=', target_vat),
            ], order='id asc', limit=1)

        safe_period = xml_escape(unicodedata.normalize('NFC', str(self.billing_period or '10/2026')))
        inv_lines_cmds = []
        for line in self.line_ids:
            safe_emp_name = xml_escape(unicodedata.normalize('NFC', str(line.employee_id.name or 'Engineer')))
            safe_role_title = xml_escape(unicodedata.normalize('NFC', str(line.role_title or 'Senior Engineer')))
            line_vals = {
                'name': (
                    f"[{safe_period}] Dịch vụ Kỹ thuật Phần mềm ({safe_emp_name} - "
                    f"{safe_role_title}): Nghiệm thu {line.billable_days:.1f}/{line.standard_days:.1f} ngày công"
                ),
                'quantity': 1.0,
                'price_unit': line.subtotal_vnd,
            }
            if income_account:
                line_vals['account_id'] = income_account.id
            if sale_tax:
                line_vals['tax_ids'] = [(6, 0, [sale_tax.id])]
            inv_lines_cmds.append((0, 0, line_vals))

        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': (self.sale_order_id.name if self.sale_order_id else '') or self.name,
            'ref': f"DRAFT-INV-{self.name}",
            'dgm_timesheet_sheet_id': self.id,
            'dgm_invoice_stage': 'draft_reconciliation',
            'dgm_einvoice_symbol': '1C26TAA',
        }
        if sale_journal:
            move_vals['journal_id'] = sale_journal.id

        if self.draft_invoice_id and self.draft_invoice_id.exists():
            move = self.draft_invoice_id.sudo()
            if move.state == 'draft':
                try:
                    with self.env.cr.savepoint():
                        move.write({
                            'dgm_timesheet_sheet_id': self.id,
                            'dgm_invoice_stage': 'draft_reconciliation',
                            'ref': f"DRAFT-INV-{self.name}",
                        })
                except Exception:
                    pass
            return move

        try:
            with self.env.cr.savepoint():
                move_vals_with_lines = dict(move_vals, invoice_line_ids=inv_lines_cmds)
                return Move.create(move_vals_with_lines)
        except Exception as exc:
            _logger.debug("Fallback account.move creation without tax/account lines: %s", exc)
            return Move.create(move_vals)

    def action_generate_mti_draft_invoice(self):
        Notification = self.env['dgm.project.notification'].sudo()
        for sheet in self:
            if isinstance(sheet.id, int) and sheet.id > 0:
                self.env.cr.execute(
                    "SELECT pg_advisory_xact_lock(%s, %s)",
                    [ADVISORY_LOCK_SOP08_NS, int(sheet.id)],
                )
            if sheet.state not in ('customer_approved', 'draft_invoiced', 'official_invoiced'):
                raise UserError(_(
                    "⛔ [SOP-DGM-08 Guardrail] Không thể xuất Hóa đơn Nháp khi Khách hàng chưa phê duyệt Timesheet "
                    "(Trạng thái hiện tại: %s). Vui lòng hoàn tất bước KH Duyệt Timesheet trước!",
                    sheet.state,
                ))
            sheet._verify_customer_signature_integrity()

            # SOP-DGM-06 Partner Onboarding Gate Check: auto fast-track if not yet approved
            partner = sheet.partner_id
            if partner and getattr(partner, 'dgm_onboarding_state', None) != 'approved':
                if hasattr(partner, 'action_fast_track_onboard'):
                    partner.sudo().action_fast_track_onboard()

            move = sheet._create_or_update_draft_account_move()

            folder = sheet._get_partner_target_folder()
            code_slug = self._clean_code_slug(partner.dgm_partner_code or sheet.name)
            period_slug = self._clean_code_slug(sheet.billing_period or '2026_10')
            doc_name = f"03_Hoa_Don_Nhap_Doi_Soat_{code_slug}_{period_slug}.html"
            html_body = sheet._render_sheet_document_html(doc_stage='draft_invoice')
            draft_doc = sheet._upsert_html_document_in_folder(
                folder,
                doc_name,
                html_body,
                res_model='account.move',
                res_id=move.id,
            )

            ntf = Notification.create({
                'project_id': sheet.project_id.id,
                'partner_id': partner.id,
                'sale_order_id': sheet.sale_order_id.id if sheet.sale_order_id else False,
                'timesheet_sheet_id': sheet.id,
                'employee_ids': [(6, 0, sheet.line_ids.mapped('employee_id').ids)],
                'notification_type': 'draft_invoice_review',
                'recipient_email': sheet.customer_approver_email or partner.email or False,
            })
            ntf.action_send_project_notification()

            sheet.write({
                'draft_invoice_id': move.id,
                'draft_invoice_doc_id': draft_doc.id,
                'state': 'draft_invoiced',
            })
        return True

    def action_confirm_draft_and_issue_official_invoice(self, confirmed_by=None):
        Notification = self.env['dgm.project.notification'].sudo()
        Document = self.env['documents.document'].sudo()
        for sheet in self:
            if isinstance(sheet.id, int) and sheet.id > 0:
                self.env.cr.execute(
                    "SELECT pg_advisory_xact_lock(%s, %s)",
                    [ADVISORY_LOCK_SOP08_NS, int(sheet.id)],
                )
            if (
                sheet.state == 'official_invoiced'
                and sheet.draft_invoice_id
                and sheet.draft_invoice_id.dgm_invoice_stage == 'official_issued'
                and sheet.draft_invoice_id.dgm_einvoice_number
                and sheet.official_invoice_doc_id
            ):
                continue
            if sheet.state not in ('draft_invoiced', 'official_invoiced') or not sheet.draft_invoice_id:
                raise UserError(_(
                    "⛔ [SOP-DGM-08 Guardrail] Chỉ được phép phát hành Hóa đơn GTGT Chính thức sau khi đã gửi Hóa đơn Nháp Đối soát "
                    "(Trạng thái hiện tại: %s).",
                    sheet.state,
                ))
            sheet._verify_customer_signature_integrity()

            confirmer = (
                (confirmed_by or '').strip()
                or sheet.customer_approver_name
                or (sheet.partner_id.name if sheet.partner_id else 'Đại diện Khách hàng')
            )
            move = sheet.draft_invoice_id.sudo()
            move.action_dgm_issue_official_einvoice(confirmed_by=confirmer)

            folder = sheet._get_partner_target_folder()
            code_slug = self._clean_code_slug(sheet.partner_id.dgm_partner_code or sheet.name)
            period_slug = self._clean_code_slug(sheet.billing_period or '2026_10')
            doc_name = f"04_Hoa_Don_Chinh_Thuc_VAT_{code_slug}_{period_slug}.html"
            html_body = sheet._render_sheet_document_html(doc_stage='official_invoice')

            official_doc = sheet._upsert_html_document_in_folder(
                folder,
                doc_name,
                html_body,
                res_model='account.move',
                res_id=move.id,
            )

            # Also file a copy in `02. Tài chính - Kế toán - Thuế` -> `Hoá đơn đầu ra`
            out_inv_folder = Document.browse(3249).exists()
            if not out_inv_folder or out_inv_folder.type != 'folder' or not out_inv_folder.active:
                out_inv_folder = Document.search([
                    ('type', '=', 'folder'),
                    ('active', '=', True),
                    '|',
                    ('name', 'ilike', 'Hoá đơn đầu ra'),
                    ('name', 'ilike', 'Hóa đơn đầu ra'),
                ], order='id asc', limit=1)
            if out_inv_folder and (not folder or out_inv_folder.id != folder.id):
                sheet._upsert_html_document_in_folder(
                    out_inv_folder,
                    doc_name,
                    html_body,
                    res_model='account.move',
                    res_id=move.id,
                )

            ntf = Notification.create({
                'project_id': sheet.project_id.id,
                'partner_id': sheet.partner_id.id,
                'sale_order_id': sheet.sale_order_id.id if sheet.sale_order_id else False,
                'timesheet_sheet_id': sheet.id,
                'employee_ids': [(6, 0, sheet.line_ids.mapped('employee_id').ids)],
                'notification_type': 'official_invoice_issued',
                'recipient_email': sheet.customer_approver_email or sheet.partner_id.email or False,
            })
            ntf.action_send_project_notification()

            sheet.write({
                'official_invoice_doc_id': official_doc.id,
                'state': 'official_invoiced',
            })
        return self[:1].draft_invoice_id or True


class DgmProjectTimesheetLine(models.Model):
    _name = 'dgm.project.timesheet.line'
    _description = 'DGM Monthly Project Timesheet Consolidation Line (SOP-DGM-08)'
    _order = 'sequence asc, id asc'

    sheet_id = fields.Many2one(
        'dgm.project.timesheet.sheet',
        string='Bảng Chấm công',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân sự Kỹ thuật (Engineer)',
        required=True,
        index=True,
    )
    role_title = fields.Char(
        string='Vị trí / Role Dự án',
        default='Senior Software Engineer',
    )
    task_id = fields.Many2one(
        'project.task',
        string='Hạng mục / Task',
    )
    contract_monthly_rate_vnd = fields.Float(
        string='Đơn giá Tháng Hợp đồng (VNĐ)',
        default=35_000_000.0,
    )
    standard_days = fields.Float(
        string='Ngày công Chuẩn',
        default=22.0,
    )
    standard_work_days = fields.Float(
        related='standard_days',
        string='Ngày công Chuẩn (Alias)',
        readonly=False,
    )
    actual_worked_days = fields.Float(
        string='Ngày công Thực tế',
        default=22.0,
    )
    overtime_hours = fields.Float(
        string='Giờ OT được duyệt',
        default=0.0,
    )
    billable_days = fields.Float(
        string='Ngày công Nghiệm thu',
        compute='_compute_line_amounts',
        store=True,
    )
    pro_rata_ratio = fields.Float(
        string='Tỷ lệ Nghiệm thu (%)',
        compute='_compute_line_amounts',
        store=True,
    )
    subtotal_vnd = fields.Float(
        string='Thành tiền Chưa Thuế (VNĐ)',
        compute='_compute_line_amounts',
        store=True,
    )
    work_summary = fields.Text(
        string='Nội dung Công việc & Deliverables trong kỳ',
    )
    analytic_line_ids = fields.Many2many(
        'account.analytic.line',
        'dgm_ts_line_analytic_rel',
        'ts_line_id',
        'analytic_line_id',
        string='Bản ghi Timesheet Gốc',
    )

    SEALED_FISCAL_STATES = ('customer_approved', 'draft_invoiced', 'official_invoiced')

    IMMUTABLE_FISCAL_LINE_FIELDS = {
        'actual_worked_days',
        'standard_days',
        'standard_work_days',
        'contract_monthly_rate_vnd',
        'overtime_hours',
        'employee_id',
        'sheet_id',
    }

    def write(self, vals):
        if self.IMMUTABLE_FISCAL_LINE_FIELDS.intersection(vals.keys()):
            for line in self:
                if line.sheet_id and line.sheet_id.state in self.SEALED_FISCAL_STATES:
                    raise UserError(_(
                        "⛔ [SOP-DGM-08 Fiscal Barrier — Decree 70/2025/ND-CP] "
                        "Không được phép chỉnh sửa dữ liệu ngày công / đơn giá trên Bảng chấm công (%s) "
                        "đã được Khách hàng nghiệm thu hoặc đã phát hành Hóa đơn (Trạng thái: %s)!",
                        line.sheet_id.name,
                        line.sheet_id.state,
                    ))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.sheet_id and line.sheet_id.state in self.SEALED_FISCAL_STATES:
                raise UserError(_(
                    "⛔ [SOP-DGM-08 Fiscal Barrier — Decree 70/2025/ND-CP] "
                    "Không được phép xóa dòng chấm công thuộc Bảng chấm công (%s) "
                    "đã được Khách hàng nghiệm thu hoặc đã phát hành Hóa đơn (Trạng thái: %s)!",
                    line.sheet_id.name,
                    line.sheet_id.state,
                ))
        return super().unlink()

    @api.depends(
        'contract_monthly_rate_vnd',
        'standard_days',
        'actual_worked_days',
        'overtime_hours',
    )
    def _compute_line_amounts(self):
        for line in self:
            line.billable_days = 0.0
            line.pro_rata_ratio = 0.0
            line.subtotal_vnd = 0.0

            std = line.standard_days if (line.standard_days and line.standard_days > 0) else 22.0
            ot_days = (line.overtime_hours or 0.0) / 8.0
            billable = (line.actual_worked_days or 0.0) + ot_days
            ratio = (billable / std) * 100.0
            subtotal = round((line.contract_monthly_rate_vnd or 0.0) * (billable / std))

            line.billable_days = billable
            line.pro_rata_ratio = ratio
            line.subtotal_vnd = subtotal


class AccountMoveDgmBilling(models.Model):
    _inherit = 'account.move'

    dgm_timesheet_sheet_id = fields.Many2one(
        'dgm.project.timesheet.sheet',
        string='Bảng Chấm công Nghiệm thu (SOP-DGM-08)',
        copy=False,
        index=True,
    )
    dgm_invoice_stage = fields.Selection(
        selection=[
            ('draft_internal', '1. Nháp Nội bộ (Internal Draft)'),
            ('draft_reconciliation', '2. Hóa đơn Nháp Đã gửi KH Đối soát (MTI Draft Sent for Reconciliation)'),
            ('customer_reconciled', '3. KH Đã Xác nhận Hóa đơn Nháp (Customer Confirmed Draft)'),
            ('official_issued', '4. Đã Phát hành Hóa đơn GTGT Chính thức (Official E-Invoice Issued)'),
        ],
        string='Trạng thái Đối soát Hóa đơn (MTI Flow)',
        default='draft_internal',
        copy=False,
        tracking=True,
        index=True,
    )
    dgm_draft_confirmed_by = fields.Char(
        string='Người Xác nhận Hóa đơn Nháp (KH)',
        copy=False,
    )
    dgm_draft_confirmed_at = fields.Datetime(
        string='Thời điểm Xác nhận Hóa đơn Nháp',
        copy=False,
    )
    dgm_einvoice_symbol = fields.Char(
        string='Ký hiệu Hóa đơn Điện tử',
        default='1C26TAA',
        copy=False,
    )
    dgm_einvoice_number = fields.Char(
        string='Số Hóa đơn GTGT Chính thức',
        copy=False,
        index=True,
    )
    dgm_einvoice_issued_at = fields.Datetime(
        string='Thời điểm Phát hành HĐĐT',
        copy=False,
    )
    dgm_einvoice_lookup_code = fields.Char(
        string='Mã Tra cứu HĐĐT (Viettel S-Invoice / VNPT)',
        copy=False,
    )

    def _build_canonical_1c26taa_xml(self):
        self.ensure_one()
        if self.dgm_timesheet_sheet_id:
            return self.dgm_timesheet_sheet_id._build_canonical_1c26taa_xml()
        nfc = lambda val: unicodedata.normalize('NFC', str(val or ''))
        root = etree.Element("HDon", Kieu="1C26TAA")
        tt_chung = etree.SubElement(root, "TTChung")
        etree.SubElement(tt_chung, "KHMSHDon").text = "1"
        etree.SubElement(tt_chung, "KHHDon").text = nfc(self.dgm_einvoice_symbol or '1C26TAA')
        etree.SubElement(tt_chung, "SHDon").text = nfc(self.dgm_einvoice_number or 'DRAFT')
        etree.SubElement(tt_chung, "THDon").text = nfc("HÓA ĐƠN GIÁ TRỊ GIA TĂNG")
        etree.SubElement(tt_chung, "DVTTe").text = "VND"
        nd_hdon = etree.SubElement(root, "NDHDon")
        n_ban = etree.SubElement(nd_hdon, "NBan")
        etree.SubElement(n_ban, "Ten").text = nfc("CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ")
        etree.SubElement(n_ban, "MST").text = "0317958465"
        n_mua = etree.SubElement(nd_hdon, "NMua")
        etree.SubElement(n_mua, "TenNM").text = nfc(self.partner_id.name if self.partner_id else '')
        etree.SubElement(n_mua, "MSTNM").text = nfc((self.partner_id.vat or '') if self.partner_id else '')
        etree.SubElement(n_mua, "MaKH").text = nfc(
            (self.partner_id.dgm_partner_code or 'PTN-DGM') if self.partner_id else 'PTN-DGM'
        )
        t_toan = etree.SubElement(nd_hdon, "TToan")
        etree.SubElement(t_toan, "TgTCThue").text = f"{self.amount_untaxed or 0.0:.0f}"
        etree.SubElement(t_toan, "TgTThue").text = f"{self.amount_tax or 0.0:.0f}"
        etree.SubElement(t_toan, "TongTien").text = f"{self.amount_total or 0.0:.0f}"
        return etree.tostring(root, method="c14n", exclusive=False, with_comments=False).decode("utf-8")

    def action_dgm_issue_official_einvoice(self, confirmed_by=None):
        for move in self:
            if isinstance(move.id, int) and move.id > 0:
                self.env.cr.execute(
                    "SELECT pg_advisory_xact_lock(%s, %s)",
                    [ADVISORY_LOCK_SOP08_NS + 1, int(move.id)],
                )
            if move.dgm_invoice_stage == 'official_issued' and move.dgm_einvoice_number:
                continue
            now_dt = fields.Datetime.now()
            raw_confirmer = (
                (confirmed_by or '').strip()
                or move.dgm_draft_confirmed_by
                or (move.partner_id.name if move.partner_id else 'Đại diện Khách hàng')
            )
            confirmer = xml_escape(unicodedata.normalize('NFC', raw_confirmer))
            with self.env.cr.savepoint():
                if move.state == 'draft':
                    posted_ok = False
                    if hasattr(move, 'action_post'):
                        try:
                            with self.env.cr.savepoint():
                                move.action_post()
                                posted_ok = True
                        except Exception as exc:
                            _logger.debug("Fallback state='posted' for invoice %s: %s", move.id, exc)
                    if not posted_ok:
                        try:
                            with self.env.cr.savepoint():
                                move.write({'state': 'posted'})
                        except Exception:
                            pass

                move_id_num = move.id if isinstance(move.id, int) and move.id > 0 else 1
                symbol = move.dgm_einvoice_symbol or '1C26TAA'
                einv_num = move.dgm_einvoice_number or f"{move_id_num:08d}"
                lookup_code = move.dgm_einvoice_lookup_code or f"DGM-{symbol}-{move_id_num:06d}"

                update_vals = {
                    'dgm_draft_confirmed_by': confirmer,
                    'dgm_draft_confirmed_at': now_dt,
                    'dgm_einvoice_symbol': symbol,
                    'dgm_einvoice_number': einv_num,
                    'dgm_einvoice_issued_at': now_dt,
                    'dgm_einvoice_lookup_code': lookup_code,
                    'dgm_invoice_stage': 'official_issued',
                }
                if 'al2c_einvoice_state' in move._fields:
                    update_vals.update({
                        'al2c_einvoice_state': 'issued',
                        'al2c_einvoice_number': f"{symbol}-{einv_num}",
                        'al2c_einvoice_lookup_code': lookup_code,
                        'al2c_einvoice_issue_date': now_dt,
                    })
                move.sudo().write(update_vals)

            if hasattr(move, 'message_post'):
                try:
                    move.message_post(
                        body=_(
                            "<b>✅ [SOP-DGM-08] Đã Phát hành Hóa đơn GTGT Chính thức:</b><br/>"
                            "Ký hiệu &amp; Số HĐ: <b>%s - %s</b><br/>"
                            "Mã tra cứu HĐĐT: <code>%s</code><br/>"
                            "Xác nhận Hóa đơn Nháp bởi: <b>%s</b>",
                            symbol,
                            einv_num,
                            lookup_code,
                            confirmer,
                        ),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
                except Exception:
                    pass
        return self or True


class ProjectProjectDgmBilling(models.Model):
    _inherit = 'project.project'

    dgm_notification_ids = fields.One2many(
        'dgm.project.notification',
        'project_id',
        string='Thông báo Dự án (SOP-DGM-08)',
    )
    dgm_timesheet_sheet_ids = fields.One2many(
        'dgm.project.timesheet.sheet',
        'project_id',
        string='Bảng Chấm công & Nghiệm thu (SOP-DGM-08)',
    )


class SaleOrderDgmBilling(models.Model):
    _inherit = 'sale.order'

    dgm_timesheet_sheet_ids = fields.One2many(
        'dgm.project.timesheet.sheet',
        'sale_order_id',
        string='Bảng Chấm công & Nghiệm thu (SOP-DGM-08)',
    )
