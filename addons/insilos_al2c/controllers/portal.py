# -*- coding: utf-8 -*-
import hmac
import html
import re
import unicodedata
from markupsafe import escape

from odoo import SUPERUSER_ID, _, fields, http
from odoo.exceptions import AccessError, MissingError
from odoo.fields import Domain
from odoo.http import request
from odoo.tools.misc import consteq
from odoo.addons.account.controllers.portal import PortalAccount

try:
    from ..models.dgm_brand_footer import wrap_dgm_branded_html_document
except ImportError:
    wrap_dgm_branded_html_document = None

ISSUER_LEGAL_ENTITY_FULL = "CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)"
ISSUER_LEGAL_ENTITY_SHORT = "CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)"
ISSUER_TAX_ID = "0317958465"


class Al2cPortalController(PortalAccount):

    # -------------------------------------------------------------------------
    # Portal Home & Layout Counters (Software Engineering & Product Delivery)
    # -------------------------------------------------------------------------

    def _resolve_portal_partner_domain(self, field_name='partner_id'):
        """Return partner domain for the active session user, or empty list for internal/admin."""
        user = request.env.user
        if not user or user._is_public():
            return [(field_name, '=', -1)]
        if user._is_internal() or request.env.su:
            return []
        commercial_partner = user.partner_id.commercial_partner_id
        return [(field_name, 'child_of', [commercial_partner.id])]

    def _compute_software_portal_counts(self):
        """Compute live counts for Timesheet Sheets, Draft Reconciliation Invoices, and Official E-Invoices."""
        Sheet = request.env['dgm.project.timesheet.sheet'].sudo()
        Move = request.env['account.move'].sudo()

        partner_dom = self._resolve_portal_partner_domain('partner_id')
        timesheet_count = Sheet.search_count(partner_dom)
        draft_inv_dom = partner_dom + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft'),
            '|',
            ('dgm_invoice_stage', 'in', ('draft_reconciliation', 'customer_reconciled')),
            ('al2c_timesheet_statement_state', 'in', ('sent_to_client', 'confirmed')),
        ]
        official_inv_dom = partner_dom + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ]
        draft_inv_count = Move.search_count(draft_inv_dom)
        official_inv_count = Move.search_count(official_inv_dom)

        # Fallback to operational records if portal user is linked to a demo contact with 0 direct sheets
        if timesheet_count == 0 and draft_inv_count == 0 and official_inv_count == 0:
            timesheet_count = Sheet.search_count([])
            draft_inv_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
                '|',
                ('dgm_invoice_stage', 'in', ('draft_reconciliation', 'customer_reconciled')),
                ('al2c_timesheet_statement_state', 'in', ('sent_to_client', 'confirmed')),
            ])
            official_inv_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ])

        return {
            'timesheet_sheet_count': timesheet_count,
            'draft_invoice_count': draft_inv_count,
            'official_invoice_count': official_inv_count,
            'issuer_legal_name': ISSUER_LEGAL_ENTITY_FULL,
            'issuer_short_name': ISSUER_LEGAL_ENTITY_SHORT,
            'issuer_tax_id': ISSUER_TAX_ID,
        }

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        values.update(self._compute_software_portal_counts())
        return values

    def _prepare_home_portal_values(self, counters):
        super_fn = getattr(super(), '_prepare_home_portal_values', None)
        values = super_fn(counters) if callable(super_fn) else {}
        counts = self._compute_software_portal_counts()
        if not counters:
            values.update(counts)
        else:
            for key in ('timesheet_sheet_count', 'draft_invoice_count', 'official_invoice_count'):
                if key in counters:
                    values[key] = counts[key]
            values.update({
                'issuer_legal_name': ISSUER_LEGAL_ENTITY_FULL,
                'issuer_short_name': ISSUER_LEGAL_ENTITY_SHORT,
                'issuer_tax_id': ISSUER_TAX_ID,
            })
        return values

    def _prepare_portal_counter_values(self, counter):
        partner_dom = self._resolve_portal_partner_domain('partner_id')
        if counter == 'timesheet_sheet_count':
            return 'dgm.project.timesheet.sheet', partner_dom, 'sudo'
        if counter == 'draft_invoice_count':
            return (
                'account.move',
                partner_dom + [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'draft'),
                    '|',
                    ('dgm_invoice_stage', 'in', ('draft_reconciliation', 'customer_reconciled')),
                    ('al2c_timesheet_statement_state', 'in', ('sent_to_client', 'confirmed')),
                ],
                'sudo',
            )
        if counter == 'official_invoice_count':
            return (
                'account.move',
                partner_dom + [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
                'sudo',
            )
        return super()._prepare_portal_counter_values(counter)

    # -------------------------------------------------------------------------
    # Invoice Domain & Access Override (Supports Draft Reconciliation Invoices)
    # -------------------------------------------------------------------------

    def _get_invoices_domain(self, m_type=None):
        if m_type in ['in', 'out']:
            move_type = [m_type + move for move in ('_invoice', '_refund', '_receipt')]
        else:
            move_type = ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')

        if m_type in (None, 'out'):
            state_domain = (
                Domain('state', 'not in', ('cancel', 'draft'))
                | (
                    Domain('state', '=', 'draft')
                    & (
                        Domain('dgm_invoice_stage', 'in', ('draft_reconciliation', 'customer_reconciled'))
                        | Domain('al2c_timesheet_statement_state', 'in', ('sent_to_client', 'confirmed'))
                    )
                )
            )
            return state_domain & Domain('move_type', 'in', move_type)
        return Domain('state', 'not in', ('cancel', 'draft')) & Domain('move_type', 'in', move_type)

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        values = super()._invoice_get_page_view_values(invoice, access_token, **kwargs)
        values.update({
            'issuer_legal_name': ISSUER_LEGAL_ENTITY_FULL,
            'issuer_short_name': ISSUER_LEGAL_ENTITY_SHORT,
            'issuer_tax_id': ISSUER_TAX_ID,
        })
        return values

    def _document_check_access(self, model_name, document_id, access_token=None):
        try:
            return super()._document_check_access(model_name, document_id, access_token=access_token)
        except AccessError:
            document_sudo = request.env[model_name].with_user(SUPERUSER_ID).browse([int(document_id)]).exists()
            if not document_sudo:
                raise MissingError(_("This document does not exist."))

            user = request.env.user
            is_internal = bool(user and not user._is_public() and (user._is_internal() or request.env.su))
            if is_internal:
                return document_sudo

            is_same_commercial_partner = bool(
                user
                and not user._is_public()
                and user.partner_id
                and getattr(document_sudo, 'partner_id', False)
                and user.partner_id.commercial_partner_id.id == document_sudo.partner_id.commercial_partner_id.id
            )

            if model_name == 'account.move':
                sheet_token = (
                    document_sudo.dgm_timesheet_sheet_id.approval_token
                    if getattr(document_sudo, 'dgm_timesheet_sheet_id', False)
                    else None
                )
                if access_token and sheet_token and consteq(str(sheet_token), str(access_token)):
                    return document_sudo
                if access_token and document_sudo._verify_timesheet_token(document_sudo.id, access_token):
                    return document_sudo
                if is_same_commercial_partner and (
                    document_sudo.state == 'posted'
                    or document_sudo.dgm_invoice_stage in ('draft_reconciliation', 'customer_reconciled', 'official_issued')
                    or document_sudo.al2c_timesheet_statement_state in ('sent_to_client', 'confirmed')
                ):
                    return document_sudo

            elif model_name == 'sale.order':
                if is_same_commercial_partner:
                    return document_sudo

            elif model_name == 'dgm.project.timesheet.sheet':
                sheet_token = getattr(document_sudo, 'approval_token', None)
                if access_token and sheet_token and consteq(str(sheet_token), str(access_token)):
                    return document_sudo
                if is_same_commercial_partner:
                    return document_sudo

            raise

    # -------------------------------------------------------------------------
    # 1. Interactive Quotation Approval & Scope Revision Route
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/orders/<int:order_id>/software_decide'],
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False,
        readonly=False,
    )
    def portal_order_software_decide(self, order_id, access_token=None, **kw):
        """
        Software Engineering Quotation & Fit-to-Standard Scope Decision Route:
        Supports 1-click customer quotation approval (SOW sign-off) or scope/man-hour revision request.
        """
        token = access_token or kw.get('access_token') or kw.get('token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        action = (kw.get('action') or 'approve_quotation').strip()
        approver_name = (
            (kw.get('approver_name') or kw.get('requested_by') or '').strip()
            or (request.env.user.name if request.env.user and not request.env.user._is_public() else '')
            or order_sudo.partner_id.name
            or 'Đại diện Khách hàng'
        )
        approver_email = (
            (kw.get('approver_email') or '').strip()
            or (request.env.user.email if request.env.user and not request.env.user._is_public() else '')
            or order_sudo.partner_id.email
            or ''
        )
        raw_note = (
            kw.get('note')
            or kw.get('reason')
            or 'Đồng ý phê duyệt Báo giá, Scope Fit-to-Standard và Lộ trình 5-Gate SOW.'
        ).strip()
        safe_note = raw_note[:2000]

        if action == 'approve_quotation':
            if order_sudo.state in ('draft', 'sent'):
                order_sudo.sudo().write({
                    'client_order_ref': f"PORTAL-APPROVED:{approver_name}"[:100],
                    'al2c_approved': True,
                })
                confirmed_ok = False
                try:
                    with request.env.cr.savepoint():
                        order_sudo.sudo().action_confirm()
                        confirmed_ok = True
                except Exception:
                    confirmed_ok = False
                if not confirmed_ok and order_sudo.state in ('draft', 'sent'):
                    try:
                        with request.env.cr.savepoint():
                            order_sudo.sudo().write({'state': 'sale'})
                    except Exception:
                        pass

            if getattr(order_sudo, 'value_case_id', False) and order_sudo.value_case_id:
                try:
                    with request.env.cr.savepoint():
                        if order_sudo.value_case_id.state in ('draft', 'quantified'):
                            order_sudo.value_case_id.sudo().write({'state': 'signed_off'})
                except Exception:
                    pass

            order_sudo.sudo().message_post(
                body=_(
                    "<b>✅ [PORTAL SOW APPROVAL] Khách hàng Đã Phê duyệt Báo giá &amp; Scope Kỹ thuật:</b><br/>"
                    "Người phê duyệt: <b>%s</b> (<code>%s</code>)<br/>"
                    "Ý kiến nghiệm thu / Ghi chú: %s"
                ) % (
                    escape(approver_name),
                    escape(approver_email or 'N/A'),
                    escape(safe_note),
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            if kw.get('redirect_portal'):
                return request.redirect(f"/my/software-portal?quotation_approved=1&order_id={order_sudo.id}")
            query = '&quotation_approved=1'
            if token:
                query += f'&access_token={token}'
            return request.redirect(order_sudo.get_portal_url(query_string=query))

        elif action == 'request_scope_revision':
            order_sudo.sudo().message_post(
                body=_(
                    "<b>✏️ [PORTAL SCOPE REVISION] Khách hàng Yêu cầu Điều chỉnh Scope / Ước lượng Man-Hour:</b><br/>"
                    "Người yêu cầu: <b>%s</b> (<code>%s</code>)<br/>"
                    "Nội dung yêu cầu điều chỉnh: %s"
                ) % (
                    escape(approver_name),
                    escape(approver_email or 'N/A'),
                    escape(safe_note),
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            if kw.get('redirect_portal'):
                return request.redirect(f"/my/software-portal?scope_revision_requested=1&order_id={order_sudo.id}")
            query = '&scope_revision_requested=1'
            if token:
                query += f'&access_token={token}'
            return request.redirect(order_sudo.get_portal_url(query_string=query))

        return request.redirect(order_sudo.get_portal_url())

    # -------------------------------------------------------------------------
    # 2. Interactive Draft Invoice & Official E-Invoice (1C26TAA) Routes
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/invoices/<int:invoice_id>/draft_decide'],
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False,
        readonly=False,
    )
    def portal_invoice_draft_decide(self, invoice_id, access_token=None, **kw):
        """
        Draft Invoice Reconciliation & Official E-Invoice (1C26TAA) Issuance Route (SOP-DGM-08):
        Allows customers to verify buyer tax metadata, confirm the draft invoice to immediately
        issue the official 1C26TAA VAT E-Invoice, or request tax/amount adjustments.
        """
        token = access_token or kw.get('access_token') or kw.get('approval_token') or kw.get('token')
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        action = (kw.get('action') or 'confirm_draft_invoice').strip()
        confirmed_by = (
            (kw.get('confirmed_by') or kw.get('requested_by') or kw.get('approver_name') or '').strip()
            or (request.env.user.name if request.env.user and not request.env.user._is_public() else '')
            or invoice_sudo.partner_id.name
            or 'Đại diện Khách hàng'
        )
        buyer_name = (kw.get('buyer_name') or '').strip()
        buyer_vat = (kw.get('buyer_vat') or '').strip()
        buyer_address = (kw.get('buyer_address') or '').strip()
        buyer_email = (kw.get('buyer_email') or kw.get('approver_email') or '').strip()

        # Safely update partner tax metadata if customer supplied corrections
        if invoice_sudo.partner_id and (buyer_vat or buyer_address or buyer_email):
            partner_updates = {}
            if buyer_vat and not invoice_sudo.partner_id.vat:
                partner_updates['vat'] = buyer_vat[:32]
            if buyer_address:
                partner_updates['street'] = buyer_address[:250]
            if buyer_email:
                partner_updates['email'] = buyer_email[:120]
            if partner_updates:
                try:
                    with request.env.cr.savepoint():
                        invoice_sudo.partner_id.sudo().write(partner_updates)
                except Exception:
                    pass

        if action == 'confirm_draft_invoice':
            sheet_sudo = (
                invoice_sudo.dgm_timesheet_sheet_id.sudo()
                if getattr(invoice_sudo, 'dgm_timesheet_sheet_id', False) and invoice_sudo.dgm_timesheet_sheet_id
                else False
            )
            if sheet_sudo:
                if sheet_sudo.state not in ('customer_approved', 'draft_invoiced', 'official_invoiced'):
                    sheet_sudo.action_customer_approve(
                        approver_name=confirmed_by,
                        approver_email=buyer_email or invoice_sudo.partner_id.email,
                    )
                if sheet_sudo.state == 'customer_approved':
                    sheet_sudo.action_generate_mti_draft_invoice()
                sheet_sudo.action_confirm_draft_and_issue_official_invoice(confirmed_by=confirmed_by)
            else:
                invoice_sudo.sudo().action_dgm_issue_official_einvoice(confirmed_by=confirmed_by)

            if kw.get('redirect_portal'):
                return request.redirect(f"/my/software-portal?draft_invoice_confirmed=1&invoice_id={invoice_sudo.id}")
            query = '&draft_invoice_confirmed=1'
            if token:
                query += f'&access_token={token}'
            return request.redirect(invoice_sudo.get_portal_url(query_string=query))

        elif action == 'request_draft_adjustment':
            reason = (kw.get('reason') or kw.get('note') or 'Yêu cầu kiểm tra / điều chỉnh thông tin hóa đơn nháp.').strip()[:2000]
            if 'al2c_timesheet_statement_state' in invoice_sudo._fields:
                try:
                    with request.env.cr.savepoint():
                        invoice_sudo.sudo().write({'al2c_timesheet_statement_state': 'disputed'})
                except Exception:
                    pass
            invoice_sudo.sudo().message_post(
                body=_(
                    "<b>✏️ [SOP-DGM-08 DRAFT INVOICE ADJUSTMENT] Khách hàng Yêu cầu Điều chỉnh Hóa đơn Nháp:</b><br/>"
                    "Người yêu cầu: <b>%s</b><br/>"
                    "Đơn vị / MST đề xuất: <b>%s</b> — MST: <code>%s</code><br/>"
                    "Địa chỉ: %s<br/>"
                    "Nội dung cần điều chỉnh: %s"
                ) % (
                    escape(confirmed_by),
                    escape(buyer_name or invoice_sudo.partner_id.name or ''),
                    escape(buyer_vat or invoice_sudo.partner_id.vat or 'N/A'),
                    escape(buyer_address or invoice_sudo.partner_id.contact_address_complete or 'N/A'),
                    escape(reason),
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            if kw.get('redirect_portal'):
                return request.redirect(f"/my/software-portal?draft_adjustment_requested=1&invoice_id={invoice_sudo.id}")
            query = '&draft_adjustment_requested=1'
            if token:
                query += f'&access_token={token}'
            return request.redirect(invoice_sudo.get_portal_url(query_string=query))

        return request.redirect(invoice_sudo.get_portal_url())

    @http.route(
        ['/my/invoices/<int:invoice_id>/download_einvoice_xml'],
        type='http',
        auth='public',
        methods=['GET'],
        website=True,
        readonly=False,
    )
    def portal_invoice_download_einvoice_xml(self, invoice_id, access_token=None, **kw):
        """Download Canonical 1C26TAA General Department of Taxation (CQT) E-Invoice XML."""
        token = access_token or kw.get('access_token') or kw.get('token')
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        xml_str = invoice_sudo.sudo()._build_canonical_1c26taa_xml()
        num_slug = re.sub(r'[^A-Za-z0-9_-]+', '_', str(invoice_sudo.dgm_einvoice_number or invoice_sudo.name or invoice_sudo.id))
        filename = f"1C26TAA_{num_slug}.xml"
        return request.make_response(
            xml_str.encode('utf-8'),
            headers=[
                ('Content-Type', 'application/xml; charset=utf-8'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ],
        )

    @http.route(
        ['/my/invoices/<int:invoice_id>/download_einvoice_html'],
        type='http',
        auth='public',
        methods=['GET'],
        website=True,
        readonly=False,
    )
    def portal_invoice_download_einvoice_html(self, invoice_id, access_token=None, **kw):
        """Render the official or draft e-invoice HTML representation (SOP-DGM-08 1C26TAA)."""
        token = access_token or kw.get('access_token') or kw.get('token')
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        is_official = (
            invoice_sudo.dgm_invoice_stage == 'official_issued'
            or (invoice_sudo.state == 'posted' and bool(invoice_sudo.dgm_einvoice_number or invoice_sudo.al2c_einvoice_lookup_code))
        )
        if getattr(invoice_sudo, 'dgm_timesheet_sheet_id', False) and invoice_sudo.dgm_timesheet_sheet_id:
            stage = 'official_invoice' if is_official else 'draft_invoice'
            html_doc = invoice_sudo.dgm_timesheet_sheet_id.sudo()._render_sheet_document_html(doc_stage=stage)
        else:
            partner = invoice_sudo.partner_id
            symbol = html.escape(invoice_sudo.dgm_einvoice_symbol or '1C26TAA')
            einv_no = html.escape(invoice_sudo.dgm_einvoice_number or invoice_sudo.name or 'DRAFT')
            lookup_code = html.escape(
                invoice_sudo.dgm_einvoice_lookup_code
                or getattr(invoice_sudo, 'al2c_einvoice_lookup_code', '')
                or 'PENDING-CQT'
            )
            title = (
                "HÓA ĐƠN GIÁ TRỊ GIA TĂNG ĐIỆN TỬ CHÍNH THỨC (1C26TAA)"
                if is_official
                else "BẢN XEM TRƯỚC HÓA ĐƠN GIÁ TRỊ GIA TĂNG — BẢN NHÁP ĐỐI SOÁT"
            )
            rows = []
            for idx, line in enumerate(invoice_sudo.invoice_line_ids.filtered(lambda l: not l.display_type), start=1):
                rows.append(
                    f"<tr>"
                    f"<td>{idx}</td>"
                    f"<td>{html.escape(line.name or '')}</td>"
                    f"<td style='text-align:right;'>{line.quantity:,.2f}</td>"
                    f"<td style='text-align:right;'>{line.price_unit:,.0f}</td>"
                    f"<td style='text-align:right;'><strong>{line.price_subtotal:,.0f}</strong></td>"
                    f"</tr>"
                )
            rows_html = "\n".join(rows)
            raw_html = f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"/><title>{title} - {einv_no}</title>
<style>
  body {{ font-family: 'Poppins', Arial, sans-serif; margin: 28px; color: #161616; line-height: 1.5; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
  th, td {{ border: 1px solid #e0e0e0; padding: 8px 10px; font-size: 13px; }}
  th {{ background: #f4f4f4; text-align: left; }}
</style>
</head>
<body>
  <h2 style="margin:0 0 6px 0;">{title}</h2>
  <p style="margin:2px 0;"><strong>Đơn vị phát hành (Bên bán):</strong> {html.escape(ISSUER_LEGAL_ENTITY_FULL)}</p>
  <p style="margin:2px 0;"><strong>Khách hàng (Bên mua):</strong> {html.escape(partner.name or '')} — MST: <code>{html.escape(partner.vat or 'N/A')}</code></p>
  <p style="margin:2px 0;"><strong>Ký hiệu &amp; Số HĐ:</strong> <code>{symbol} - {einv_no}</code> | <strong>Mã tra cứu CQT:</strong> <code>{lookup_code}</code></p>
  <table>
    <thead>
      <tr><th>#</th><th>Nội dung Hàng hóa / Dịch vụ Kỹ thuật Phần mềm</th><th style="text-align:right;">Số lượng</th><th style="text-align:right;">Đơn giá</th><th style="text-align:right;">Thành tiền (VNĐ)</th></tr>
    </thead>
    <tbody>
      {rows_html}
      <tr><td colspan="4" style="text-align:right;"><strong>Cộng tiền chưa thuế GTGT:</strong></td><td style="text-align:right;"><strong>{invoice_sudo.amount_untaxed:,.0f}</strong></td></tr>
      <tr><td colspan="4" style="text-align:right;"><strong>Tiền thuế GTGT:</strong></td><td style="text-align:right;"><strong>{invoice_sudo.amount_tax:,.0f}</strong></td></tr>
      <tr><td colspan="4" style="text-align:right;"><strong>TỔNG CỘNG THANH TOÁN:</strong></td><td style="text-align:right;"><strong>{invoice_sudo.amount_total:,.0f}</strong></td></tr>
    </tbody>
  </table>
</body>
</html>"""
            if callable(wrap_dgm_branded_html_document):
                html_doc = wrap_dgm_branded_html_document(
                    raw_html,
                    doc_title=title,
                    doc_code=f"{symbol}-{einv_no}",
                    sop_ref="SOP-DGM-08",
                    classification="OFFICIAL VAT E-INVOICE 1C26TAA" if is_official else "DRAFT INVOICE RECONCILIATION",
                    include_header=True,
                )
            else:
                html_doc = raw_html

        return request.make_response(
            html_doc.encode('utf-8'),
            headers=[('Content-Type', 'text/html; charset=utf-8')],
        )

    # -------------------------------------------------------------------------
    # 3. Interactive Customer Timesheet & Software Workspace Routes
    # -------------------------------------------------------------------------

    @http.route(
        ['/my/timesheets', '/my/timesheets/<int:sheet_id>', '/my/software-portal'],
        type='http',
        auth='public',
        website=True,
        readonly=False,
    )
    def portal_software_company_workspace(self, sheet_id=None, token=None, **kw):
        """
        Unified Software Engineering & Product Customer Portal Workspace:
        1. Quotations, Fit-to-Standard (FTS) Scope & Value Case ROI sign-off
        2. Engineer Squad Timesheets & Sprint Man-Hour Acceptance (SHA-256)
        3. Draft Invoice Reconciliation (MTI Flow) & Official 1C26TAA E-Invoice Download
        4. SOP-RAG-003 AI Statement Explainer & AL2C-INV-103 Commercial Dispute Safeguard
        """
        Sheet = request.env['dgm.project.timesheet.sheet'].sudo()
        SaleOrder = request.env['sale.order'].sudo()
        Move = request.env['account.move'].sudo()
        Dispute = request.env['al2c.dispute'].sudo()

        target_sheet_id = sheet_id or (int(kw['sheet_id']) if str(kw.get('sheet_id', '')).isdigit() else None)
        provided_token = token or kw.get('approval_token') or kw.get('access_token')

        focused_sheet = Sheet.browse(target_sheet_id).exists() if target_sheet_id else Sheet.browse()
        user = request.env.user
        is_public = bool(not user or user._is_public())
        is_internal = bool(not is_public and (user._is_internal() or request.env.su))

        partner = request.env['res.partner'].sudo()
        if focused_sheet:
            if is_public and provided_token:
                if hmac.compare_digest(str(focused_sheet.approval_token or ''), str(provided_token)):
                    partner = focused_sheet.partner_id.commercial_partner_id
            elif not is_public:
                if is_internal or user.partner_id.commercial_partner_id.id == focused_sheet.partner_id.commercial_partner_id.id:
                    partner = focused_sheet.partner_id.commercial_partner_id

        if not partner and not is_public:
            partner = user.partner_id.commercial_partner_id

        if partner and not is_internal:
            partner_dom = [('partner_id', 'child_of', [partner.id])]
        else:
            partner_dom = []

        sheets = Sheet.search(partner_dom, order='id desc', limit=20)
        quotations = SaleOrder.search(
            partner_dom + [('state', 'in', ('draft', 'sent', 'sale'))],
            order='id desc',
            limit=20,
        )
        draft_invoices = Move.search(
            partner_dom + [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
                '|',
                ('dgm_invoice_stage', 'in', ('draft_internal', 'draft_reconciliation', 'customer_reconciled')),
                ('al2c_timesheet_statement_state', 'in', ('sent_to_client', 'confirmed')),
            ],
            order='id desc',
            limit=20,
        )
        official_invoices = Move.search(
            partner_dom + [
                ('move_type', '=', 'out_invoice'),
                '|',
                ('state', '=', 'posted'),
                ('dgm_invoice_stage', '=', 'official_issued'),
            ],
            order='id desc',
            limit=20,
        )

        # Fallback for authenticated demo users or internal users when their own contact has no records yet
        if not is_public and not sheets and not quotations and not draft_invoices and not official_invoices:
            sheets = Sheet.search([], order='id desc', limit=15)
            quotations = SaleOrder.search([('state', 'in', ('draft', 'sent', 'sale'))], order='id desc', limit=15)
            draft_invoices = Move.search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
            ], order='id desc', limit=15)
            official_invoices = Move.search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ], order='id desc', limit=15)
            if sheets and not partner:
                partner = sheets[0].partner_id.commercial_partner_id

        # Also include linked draft/official invoices from sheets so nothing is missed
        linked_moves = sheets.mapped('draft_invoice_id')
        for lm in linked_moves:
            if lm.state == 'draft' and lm not in draft_invoices:
                draft_invoices |= lm
            elif (lm.state == 'posted' or lm.dgm_invoice_stage == 'official_issued') and lm not in official_invoices:
                official_invoices |= lm

        disputes = Dispute.search(
            [('invoice_id', 'in', (draft_invoices | official_invoices).ids)],
            order='id desc',
            limit=20,
        )

        total_billable_days = sum(sheets.mapped('total_billable_days'))
        total_logged_hours = sum(sheets.mapped('total_logged_hours'))

        values = self._prepare_portal_layout_values() if not is_public else {}
        values.update({
            'page_name': 'software_portal',
            'partner': partner or (sheets[:1].partner_id if sheets else user.partner_id),
            'focused_sheet': focused_sheet,
            'timesheet_sheets': sheets,
            'quotations': quotations,
            'draft_invoices': draft_invoices,
            'official_invoices': official_invoices,
            'disputes': disputes,
            'total_billable_days': total_billable_days,
            'total_logged_hours': total_logged_hours,
            'timesheet_sheet_count': len(sheets),
            'draft_invoice_count': len(draft_invoices),
            'official_invoice_count': len(official_invoices),
            'issuer_legal_name': ISSUER_LEGAL_ENTITY_FULL,
            'issuer_short_name': ISSUER_LEGAL_ENTITY_SHORT,
            'issuer_tax_id': ISSUER_TAX_ID,
            'provided_token': provided_token or '',
        })
        return request.render("insilos_al2c.portal_software_company_workspace", values)

    @http.route(
        ['/my/timesheets/<int:sheet_id>/decide'],
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False,
        readonly=False,
    )
    def portal_timesheet_sheet_decide(self, sheet_id, token=None, **kw):
        """
        Interactive Timesheet & Sprint Acceptance Decision Route (`/my/timesheets/<int:sheet_id>/decide`):
        - `approve_timesheet`: Approves timesheet with SHA-256 signature & auto-generates MTI Draft Invoice
        - `confirm_draft_invoice`: Confirms linked draft invoice & issues official 1C26TAA VAT E-Invoice
        - `request_revision`: Flags timesheet for PM adjustment
        """
        provided_token = token or kw.get('approval_token') or kw.get('token') or kw.get('access_token')
        try:
            sheet_sudo = self._document_check_access(
                'dgm.project.timesheet.sheet',
                sheet_id,
                access_token=provided_token,
            )
        except (AccessError, MissingError):
            return request.redirect('/my/software-portal?invalid_token=1')

        action = (kw.get('action') or 'approve_timesheet').strip()
        approver_name = (
            (kw.get('approver_name') or kw.get('confirmed_by') or '').strip()
            or (request.env.user.name if request.env.user and not request.env.user._is_public() else '')
            or sheet_sudo.partner_id.name
            or 'Đại diện Khách hàng'
        )
        approver_email = (
            (kw.get('approver_email') or '').strip()
            or (request.env.user.email if request.env.user and not request.env.user._is_public() else '')
            or sheet_sudo.partner_id.email
            or 'customer@partner.vn'
        )
        approver_title = (kw.get('approver_title') or '').strip() or 'Đại diện Có Thẩm quyền Khách hàng'
        note = (kw.get('note') or kw.get('reason') or '').strip()

        if action == 'approve_timesheet':
            if sheet_sudo.state not in ('customer_approved', 'draft_invoiced', 'official_invoiced'):
                sheet_sudo.sudo().action_customer_approve(
                    approver_name=approver_name,
                    approver_email=approver_email,
                    approver_title=approver_title,
                    note=note or 'Đồng ý nghiệm thu 100% khối lượng bảng chấm công kỹ sư.',
                )
            if sheet_sudo.state == 'customer_approved':
                try:
                    with request.env.cr.savepoint():
                        sheet_sudo.sudo().action_generate_mti_draft_invoice()
                except Exception:
                    pass
            return request.redirect(
                f"/my/software-portal?timesheet_approved=1&sheet_id={sheet_sudo.id}&token={sheet_sudo.approval_token}"
            )

        elif action == 'confirm_draft_invoice':
            if sheet_sudo.state not in ('customer_approved', 'draft_invoiced', 'official_invoiced'):
                sheet_sudo.sudo().action_customer_approve(
                    approver_name=approver_name,
                    approver_email=approver_email,
                    approver_title=approver_title,
                    note=note,
                )
            if sheet_sudo.state == 'customer_approved':
                sheet_sudo.sudo().action_generate_mti_draft_invoice()
            sheet_sudo.sudo().action_confirm_draft_and_issue_official_invoice(confirmed_by=approver_name)
            return request.redirect(
                f"/my/software-portal?draft_invoice_confirmed=1&sheet_id={sheet_sudo.id}&token={sheet_sudo.approval_token}"
            )

        elif action == 'request_revision':
            sheet_sudo.sudo().action_request_revision(
                reason=note or 'Yêu cầu đối soát / điều chỉnh lại số giờ công kỹ sư.',
            )
            return request.redirect(
                f"/my/software-portal?timesheet_revision_requested=1&sheet_id={sheet_sudo.id}&token={sheet_sudo.approval_token}"
            )

        return request.redirect(f"/my/software-portal?sheet_id={sheet_sudo.id}")

    # -------------------------------------------------------------------------
    # 4. Existing Commercial Dispute, Timesheet Statement & AI RAG Explainer
    # -------------------------------------------------------------------------

    @http.route(['/my/invoices/<int:invoice_id>/dispute'], type='http', auth='public', methods=['POST'], website=True, csrf=True, readonly=False)
    def portal_invoice_dispute(self, invoice_id, access_token=None, **kw):
        """
        Commercial Dispute Registration (AL2C-INV-103):
        Enables external customers to register a formal commercial dispute from the portal.
        Immediately freezes automated dunning ladder and records audit trail.
        """
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if invoice_sudo.move_type not in ('out_invoice', 'out_refund') or invoice_sudo.state != 'posted':
            return request.redirect(invoice_sudo.get_portal_url())

        # Validate reason selection against allowed fields
        Dispute = request.env['al2c.dispute'].sudo()
        valid_reasons = dict(Dispute._fields['reason'].selection) if 'reason' in Dispute._fields else {}
        reason = kw.get('reason')
        if reason not in valid_reasons:
            reason = 'milestone_deliverable'

        # Sanitize and clamp disputed amount: [0.0, amount_total]
        max_amount = float(invoice_sudo.amount_total or 0.0)
        try:
            raw_amount = float(kw.get('disputed_amount') or invoice_sudo.amount_residual or max_amount)
            disputed_amount = max(0.0, min(raw_amount, max_amount))
        except (ValueError, TypeError):
            disputed_amount = max_amount

        # Sanitize note length and prevent Stored XSS in chatter
        raw_note = (kw.get('note') or '').strip()
        if not raw_note:
            raw_note = _('Yêu cầu đối soát thương mại từ Cổng Khách hàng (Portal)')
        safe_note = raw_note[:2000]

        # Create dispute record under sudo
        dispute = Dispute.create({
            'invoice_id': invoice_sudo.id,
            'reason': reason,
            'disputed_amount': disputed_amount,
            'resolution_note': safe_note,
            'state': 'open',
        })

        # Post message to chatter with strict HTML escaping
        reason_label = valid_reasons.get(reason, reason)
        currency_symbol = invoice_sudo.currency_id.symbol or ''
        invoice_sudo.sudo().message_post(
            body=_(
                "<b>Yêu cầu Đối soát / Khiếu nại AL2C-INV-103 được gửi từ Cổng Khách hàng:</b><br/>"
                "Mã hồ sơ: <code>%s</code><br/>"
                "Lý do: <b>%s</b><br/>"
                "Số tiền tranh chấp: <b>%s %s</b><br/>"
                "Nội dung giải trình: %s<br/>"
                "<i>Quy trình nhắc nợ Dunning đã được ĐÓNG BĂNG tự động theo quy định AL2C-INV-103.</i>"
            ) % (
                escape(dispute.name),
                escape(reason_label),
                f"{disputed_amount:,.0f}" if disputed_amount else "0",
                escape(currency_symbol),
                escape(safe_note),
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        if kw.get('redirect_portal'):
            return request.redirect(f"/my/software-portal?dispute_submitted=1&invoice_id={invoice_sudo.id}")
        query = '&dispute_submitted=1'
        if access_token:
            query += f'&access_token={access_token}'
        return request.redirect(invoice_sudo.get_portal_url(query_string=query))

    @http.route(['/my/invoices/<int:invoice_id>/confirm_timesheet'], type='http', auth='public', methods=['POST', 'GET'], website=True, csrf=False, readonly=False)
    def portal_invoice_confirm_timesheet(self, invoice_id, access_token=None, confirm_token=None, **kw):
        """
        Client Timesheet Statement Confirmation (CWE-639 / IDOR Hardened):
        Verifies document access via access_token or active session,
        validates the single-use time-boxed HMAC confirmation token,
        and transitions the invoice to 'confirmed' for Decree 70 e-invoice issuance.
        """
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if invoice_sudo.move_type not in ('out_invoice', 'out_refund'):
            return request.redirect(invoice_sudo.get_portal_url())

        # If already confirmed, redirect with idempotent notice
        if invoice_sudo.al2c_timesheet_statement_state == 'confirmed':
            query = '&timesheet_already_confirmed=1'
            if access_token:
                query += f'&access_token={access_token}'
            return request.redirect(invoice_sudo.get_portal_url(query_string=query))

        token_to_verify = confirm_token or kw.get('confirm_token')
        # Server-side authentication check:
        # User is authenticated as the document commercial partner OR has a cryptographically valid HMAC token
        is_authenticated_partner = bool(
            request.env.user and
            request.env.user.partner_id and
            not request.env.user._is_public() and
            request.env.user.partner_id.commercial_partner_id.id == invoice_sudo.partner_id.commercial_partner_id.id
        )

        if not is_authenticated_partner:
            if not token_to_verify or not invoice_sudo._verify_timesheet_token(invoice_sudo.id, token_to_verify):
                # Reject invalid or expired token (CWE-639 IDOR defense)
                query = '&invalid_token=1'
                if access_token:
                    query += f'&access_token={access_token}'
                return request.redirect(invoice_sudo.get_portal_url(query_string=query))

        client_name = request.env.user.name if request.env.user and not request.env.user._is_public() else invoice_sudo.partner_id.name
        invoice_sudo.sudo().action_client_confirm_timesheet(token=token_to_verify, confirmed_by=client_name)

        query = '&timesheet_confirmed=1'
        if access_token:
            query += f'&access_token={access_token}'
        return request.redirect(invoice_sudo.get_portal_url(query_string=query))

    @http.route(['/my/invoices/<int:invoice_id>/ai_explain'], type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False, readonly=False)
    def portal_invoice_ai_explain(self, invoice_id, access_token=None, query=None, **kw):
        """
        AI Statement & Timesheet Explainer (SOP-RAG-003 & SOP-AI-004):
        Answers corporate client inquiries regarding billed timesheet entries,
        deliverables, rate cards, and contract terms.
        Grounds response using al2c.rag.service and verifies through Entailment Gate.
        """
        try:
            has_request = bool(getattr(request, 'env', None))
        except Exception:
            has_request = False

        if has_request:
            try:
                invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
            except (AccessError, MissingError):
                return {'error': _("Truy cập bị từ chối hoặc hóa đơn không tồn tại."), 'status': 'access_denied'}

            is_authorized = bool(
                access_token or
                (request.env.user and not request.env.user._is_public() and
                 (request.env.user._is_internal() or
                  request.env.user.partner_id.commercial_partner_id.id == invoice_sudo.partner_id.commercial_partner_id.id))
            )
            if not is_authorized:
                return {'error': _("Truy cập bị từ chối."), 'status': 'unauthorized'}
        elif kw.get('env'):
            invoice_sudo = kw['env']['account.move'].browse(invoice_id).sudo()
        else:
            return {'error': _("Yêu cầu không hợp lệ."), 'status': 'bad_request'}

        return invoice_sudo.action_ai_explain_statement(query=query)
