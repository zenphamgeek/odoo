# -*- coding: utf-8 -*-
import hmac
import html
import json

from odoo import http, _
from odoo.http import request, Response


class DgmTimesheetApprovalPortal(http.Controller):
    """
    SOP-DGM-08 Customer Timesheet Approval & MTI Draft Invoice Reconciliation Portal.
    Secured via constant-time HMAC/token verification (`hmac.compare_digest`).
    """

    def _verify_sheet_and_token(self, sheet_id, token):
        Sheet = request.env['dgm.project.timesheet.sheet'].sudo()
        sheet = Sheet.browse(sheet_id).exists()
        if not sheet:
            return None
        expected_token = str(sheet.approval_token or '')
        provided_token = str(token or '')
        if not expected_token or not provided_token:
            return None
        if not hmac.compare_digest(expected_token, provided_token):
            return None
        return sheet

    def _render_portal_page(self, sheet, banner_message=None):
        partner = sheet.partner_id
        partner_code = partner.dgm_partner_code or partner.dgm_provisional_code or 'PTN-DGM'
        decide_url = f"/insilos/timesheet_approval/{sheet.id}/{sheet.approval_token}/decide"

        rows_html = []
        for idx, line in enumerate(sheet.line_ids, start=1):
            emp_name = html.escape(line.employee_id.name or 'Engineer')
            role_title = html.escape(line.role_title or 'Senior Software Engineer')
            work_desc = html.escape(line.work_summary or '')
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

        banner_block = ''
        if banner_message:
            banner_block = (
                f"<div style='padding:12px 16px; margin-bottom:16px; border:1px solid var(--insilos-border-subtle, #16a34a); "
                f"border-radius:6px; font-weight:600;'>"
                f"{html.escape(banner_message)}"
                f"</div>"
            )

        inv_info_block = ''
        if sheet.draft_invoice_id:
            inv = sheet.draft_invoice_id
            inv_info_block = (
                f"<div style='margin-top:16px; padding:14px 18px; border:1px solid var(--insilos-border-subtle, #cbd5e1); border-radius:6px;'>"
                f"<h4 style='margin:0 0 8px 0;'>Hóa đơn Đối soát / Hóa đơn GTGT Liên kết (MTI Invoice Reconciliation)</h4>"
                f"<p style='margin:4px 0;'><strong>Trạng thái Hóa đơn:</strong> <code>{html.escape(inv.dgm_invoice_stage or '')}</code></p>"
                f"<p style='margin:4px 0;'><strong>Ký hiệu &amp; Số HĐĐT:</strong> <code>{html.escape(inv.dgm_einvoice_symbol or '1C26TAA')} - {html.escape(inv.dgm_einvoice_number or 'DRAFT')}</code></p>"
                f"<p style='margin:4px 0;'><strong>Mã tra cứu HĐĐT:</strong> <code>{html.escape(inv.dgm_einvoice_lookup_code or 'PENDING')}</code></p>"
                f"</div>"
            )

        html_doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<title>SOP-DGM-08 Customer Timesheet &amp; MTI Invoice Portal — {html.escape(sheet.name)}</title>
<style>
  body {{
    font-family: 'Inter', Arial, sans-serif;
    color: var(--insilos-text-primary, #1e293b);
    background: var(--insilos-bg-canvas, transparent);
    margin: 24px auto;
    max-width: 1080px;
    padding: 0 16px;
    line-height: 1.5;
  }}
  .portal-card {{
    border: 1px solid var(--insilos-border-subtle, #cbd5e1);
    border-radius: 10px;
    padding: 24px;
    background: var(--insilos-bg-card, transparent);
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 16px;
  }}
  th, td {{
    border: 1px solid var(--insilos-border-subtle, #cbd5e1);
    padding: 8px 12px;
    font-size: 13px;
  }}
  th {{
    background: var(--insilos-bg-subtle, #e2e8f0);
    text-align: left;
  }}
  .form-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-top: 20px;
  }}
  .action-box {{
    border: 1px solid var(--insilos-border-subtle, #cbd5e1);
    border-radius: 8px;
    padding: 16px;
    background: var(--insilos-bg-surface, transparent);
  }}
  input, textarea {{
    width: 100%;
    box-sizing: border-box;
    padding: 8px 10px;
    margin: 6px 0 10px 0;
    border: 1px solid var(--insilos-border-subtle, #94a3b8);
    border-radius: 4px;
  }}
  button {{
    padding: 9px 16px;
    border-radius: 6px;
    border: 1px solid var(--insilos-border-subtle, #2563eb);
    cursor: pointer;
    font-weight: 600;
  }}
</style>
</head>
<body>
  <div class="portal-card">
    <h2 style="margin-top:0;">CỔNG PHÊ DUYỆT BẢNG CHẤM CÔNG &amp; ĐỐI SOÁT HÓA ĐƠN NHÁP (SOP-DGM-08)</h2>
    <p><strong>Đơn vị Cung cấp:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC) — MST: 0317958465</p>
    {banner_block}
    <table>
      <tbody>
        <tr>
          <th style="width:22%;">Mã Bảng Chấm công</th>
          <td style="width:28%;"><strong>{html.escape(sheet.name)}</strong></td>
          <th style="width:22%;">Kỳ Đối soát</th>
          <td style="width:28%;"><strong>{html.escape(sheet.billing_period or '')}</strong></td>
        </tr>
        <tr>
          <th>Khách hàng / Đối tác</th>
          <td><strong>{html.escape(partner.name or '')}</strong> ({html.escape(partner_code)})</td>
          <th>Dự án &amp; Hợp đồng</th>
          <td>{html.escape(sheet.project_id.name or '')} / {html.escape(sheet.sale_order_id.name if sheet.sale_order_id else 'N/A')}</td>
        </tr>
        <tr>
          <th>Trạng thái Hiện tại</th>
          <td><code>{html.escape(sheet.state or '')}</code></td>
          <th>Chữ ký Băm SHA-256</th>
          <td><code>{html.escape(sheet.customer_signature_hash or 'PENDING')}</code></td>
        </tr>
      </tbody>
    </table>

    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Nhân sự Kỹ thuật</th>
          <th>Nội dung Công việc &amp; Deliverables</th>
          <th style="text-align:right;">Công chuẩn</th>
          <th style="text-align:right;">Công thực tế</th>
          <th style="text-align:right;">Giờ OT</th>
          <th style="text-align:right;">Công nghiệm thu</th>
          <th style="text-align:right;">Đơn giá tháng</th>
          <th style="text-align:right;">Thành tiền (VNĐ)</th>
        </tr>
      </thead>
      <tbody>
        {lines_tbody}
        <tr>
          <td colspan="8" style="text-align:right;"><strong>Cộng tiền dịch vụ chưa thuế (VNĐ):</strong></td>
          <td style="text-align:right;"><strong>{sheet.amount_untaxed_vnd:,.0f}</strong></td>
        </tr>
        <tr>
          <td colspan="8" style="text-align:right;"><strong>Thuế GTGT ({html.escape(sheet.vat_rate or '8')}%):</strong></td>
          <td style="text-align:right;"><strong>{sheet.amount_tax_vnd:,.0f}</strong></td>
        </tr>
        <tr>
          <td colspan="8" style="text-align:right;"><strong>TỔNG CỘNG THANH TOÁN (VNĐ):</strong></td>
          <td style="text-align:right;"><strong>{sheet.amount_total_vnd:,.0f}</strong></td>
        </tr>
      </tbody>
    </table>

    {inv_info_block}

    <div class="form-grid">
      <div class="action-box">
        <h4 style="margin-top:0;">1. Phê duyệt Timesheet &amp; Nghiệm thu Khối lượng</h4>
        <form method="POST" action="{html.escape(decide_url)}">
          <input type="hidden" name="action" value="approve_timesheet"/>
          <label>Họ tên Người đại diện phê duyệt:</label>
          <input type="text" name="approver_name" value="{html.escape(sheet.customer_approver_name or partner.name or '')}" required="required"/>
          <label>Email Người phê duyệt:</label>
          <input type="email" name="approver_email" value="{html.escape(sheet.customer_approver_email or partner.email or '')}"/>
          <label>Chức danh:</label>
          <input type="text" name="approver_title" value="{html.escape(sheet.customer_approver_title or 'Đại diện Có Thẩm quyền')}"/>
          <label>Ý kiến nghiệm thu:</label>
          <textarea name="note" rows="2">{html.escape(sheet.customer_approval_note or 'Đồng ý nghiệm thu 100% khối lượng bảng chấm công.')}</textarea>
          <button type="submit">✅ Xác nhận Phê duyệt Timesheet</button>
        </form>
      </div>

      <div class="action-box">
        <h4 style="margin-top:0;">2. Xác nhận Hóa đơn Nháp &amp; Đề nghị Xuất HĐĐT Chính thức</h4>
        <form method="POST" action="{html.escape(decide_url)}">
          <input type="hidden" name="action" value="confirm_draft_invoice"/>
          <label>Người xác nhận Hóa đơn Nháp (KH):</label>
          <input type="text" name="confirmed_by" value="{html.escape(sheet.customer_approver_name or partner.name or '')}" required="required"/>
          <button type="submit">🧾 Xác nhận Hóa đơn Nháp &amp; Phát hành HĐĐT</button>
        </form>

        <hr style="margin:16px 0;"/>
        <h4 style="margin-top:0;">3. Yêu cầu Điều chỉnh Số liệu Timesheet</h4>
        <form method="POST" action="{html.escape(decide_url)}">
          <input type="hidden" name="action" value="request_revision"/>
          <label>Lý do yêu cầu điều chỉnh:</label>
          <textarea name="reason" rows="2" placeholder="Nhập nội dung cần đối soát lại..."></textarea>
          <button type="submit">⚠️ Gửi Yêu cầu Điều chỉnh</button>
        </form>
      </div>
    </div>
  </div>
</body>
</html>"""
        return Response(html_doc, status=200, content_type='text/html; charset=utf-8')

    @http.route(
        '/insilos/timesheet_approval/<int:sheet_id>/<string:token>',
        type='http',
        auth='public',
        website=False,
        readonly=False,
        csrf=False,
    )
    def view_timesheet_approval_portal(self, sheet_id, token, **kw):
        sheet = self._verify_sheet_and_token(sheet_id, token)
        if not sheet:
            return Response(
                "403 Forbidden — Invalid or expired timesheet approval token.",
                status=403,
                content_type='text/plain; charset=utf-8',
            )
        return self._render_portal_page(sheet)

    @http.route(
        '/insilos/timesheet_approval/<int:sheet_id>/<string:token>/decide',
        type='http',
        auth='public',
        methods=['POST'],
        website=False,
        readonly=False,
        csrf=False,
    )
    def decide_timesheet_approval_portal(self, sheet_id, token, **kw):
        sheet = self._verify_sheet_and_token(sheet_id, token)
        if not sheet:
            return Response(
                "403 Forbidden — Invalid or expired timesheet approval token.",
                status=403,
                content_type='text/plain; charset=utf-8',
            )

        action = (kw.get('action') or 'approve_timesheet').strip()
        msg = ''
        if action == 'approve_timesheet':
            sheet.sudo().action_customer_approve(
                approver_name=kw.get('approver_name'),
                approver_email=kw.get('approver_email'),
                approver_title=kw.get('approver_title'),
                note=kw.get('note'),
            )
            msg = f"Đã phê duyệt Bảng chấm công {sheet.name} thành công (SHA-256: {sheet.customer_signature_hash})."
        elif action == 'request_revision':
            sheet.sudo().action_request_revision(
                reason=kw.get('reason') or kw.get('note'),
            )
            msg = f"Đã ghi nhận yêu cầu điều chỉnh cho Bảng chấm công {sheet.name}."
        elif action == 'confirm_draft_invoice':
            sheet.sudo().action_confirm_draft_and_issue_official_invoice(
                confirmed_by=kw.get('confirmed_by') or kw.get('approver_name'),
            )
            msg = f"Đã xác nhận Hóa đơn Nháp và phát hành Hóa đơn GTGT Chính thức cho {sheet.name}."
        else:
            return Response(
                f"400 Bad Request — Unsupported action: {action}",
                status=400,
                content_type='text/plain; charset=utf-8',
            )

        if kw.get('format') == 'json':
            payload = {
                'ok': True,
                'sheet_id': sheet.id,
                'sheet_name': sheet.name,
                'state': sheet.state,
                'signature_hash': sheet.customer_signature_hash,
                'message': msg,
            }
            return Response(
                json.dumps(payload),
                status=200,
                content_type='application/json; charset=utf-8',
            )

        return self._render_portal_page(sheet, banner_message=msg)
