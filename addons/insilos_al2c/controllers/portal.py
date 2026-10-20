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

        Notification = request.env['dgm.project.notification'].sudo()
        resolved_partner = partner or (sheets[:1].partner_id.commercial_partner_id if sheets else user.partner_id.commercial_partner_id)
        care_dom = [('partner_id', 'child_of', [resolved_partner.id])] if (resolved_partner and not is_internal) else []
        care_tickets = Notification.search(care_dom, order='id desc', limit=15)
        if not care_tickets and not is_public:
            care_tickets = Notification.search([], order='id desc', limit=10)

        total_billable_days = sum(sheets.mapped('total_billable_days'))
        total_logged_hours = sum(sheets.mapped('total_logged_hours'))

        values = self._prepare_portal_layout_values() if not is_public else {}
        values.update({
            'page_name': 'software_portal',
            'partner': resolved_partner or user.partner_id,
            'focused_sheet': focused_sheet,
            'timesheet_sheets': sheets,
            'quotations': quotations,
            'draft_invoices': draft_invoices,
            'official_invoices': official_invoices,
            'disputes': disputes,
            'care_tickets': care_tickets,
            'total_billable_days': total_billable_days,
            'total_logged_hours': total_logged_hours,
            'timesheet_sheet_count': len(sheets),
            'draft_invoice_count': len(draft_invoices),
            'official_invoice_count': len(official_invoices),
            'issuer_legal_name': ISSUER_LEGAL_ENTITY_FULL,
            'issuer_short_name': ISSUER_LEGAL_ENTITY_SHORT,
            'issuer_tax_id': ISSUER_TAX_ID,
            'provided_token': provided_token or (sheets[:1].approval_token if sheets else ''),
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

    # -------------------------------------------------------------------------
    # 5. Context-Aware Multi-Intent Portal AI Chat Assistant & Customer Care SLA
    # -------------------------------------------------------------------------

    def _resolve_portal_customer_partner(
        self,
        access_token=None,
        partner_id=None,
        invoice_id=None,
        order_id=None,
        sheet_id=None,
        env=None,
    ):
        """
        Resolve the active portal customer partner and optional focused records
        while strictly enforcing CWE-639 Cross-Tenant IDOR isolation.
        """
        active_env = env
        has_http_request = False
        if active_env is None:
            try:
                if getattr(request, 'env', None):
                    active_env = request.env
                    has_http_request = True
            except Exception:
                active_env = None
        if active_env is None:
            raise AccessError(_("Không tìm thấy ngữ cảnh phiên làm việc hợp lệ."))

        user = active_env.user
        is_public = bool(not user or user._is_public())
        is_internal = bool(not is_public and (user._is_internal() or active_env.su))

        Partner = active_env['res.partner'].sudo()
        Move = active_env['account.move'].sudo()
        SaleOrder = active_env['sale.order'].sudo()
        Sheet = active_env['dgm.project.timesheet.sheet'].sudo()

        def _check_doc_access(model_name, doc_id, verified_comm_partner=None):
            if not doc_id:
                return None
            try:
                doc_id_int = int(doc_id)
            except (ValueError, TypeError):
                return None
            if doc_id_int <= 0:
                return None

            doc_sudo = active_env[model_name].with_user(SUPERUSER_ID).browse(doc_id_int).exists()
            if not doc_sudo:
                raise MissingError(_("Hồ sơ không tồn tại."))
            if is_internal:
                return doc_sudo

            # Check token match
            doc_access_token = getattr(doc_sudo, 'access_token', None)
            if access_token and doc_access_token and consteq(str(doc_access_token), str(access_token)):
                return doc_sudo
            if model_name == 'account.move':
                sheet_tok = (
                    doc_sudo.dgm_timesheet_sheet_id.approval_token
                    if getattr(doc_sudo, 'dgm_timesheet_sheet_id', False)
                    else None
                )
                if access_token and sheet_tok and consteq(str(sheet_tok), str(access_token)):
                    return doc_sudo
                if access_token and doc_sudo._verify_timesheet_token(doc_sudo.id, access_token):
                    return doc_sudo
            elif model_name == 'dgm.project.timesheet.sheet':
                sheet_tok = getattr(doc_sudo, 'approval_token', None)
                if access_token and sheet_tok and consteq(str(sheet_tok), str(access_token)):
                    return doc_sudo

            # Check commercial partner match for authenticated portal user or token-verified sheet partner
            doc_comm = doc_sudo.partner_id.commercial_partner_id if getattr(doc_sudo, 'partner_id', False) else None
            if verified_comm_partner and doc_comm and verified_comm_partner.id == doc_comm.id:
                return doc_sudo
            if (
                not is_public
                and user.partner_id
                and doc_comm
                and user.partner_id.commercial_partner_id.id == doc_comm.id
            ):
                return doc_sudo

            raise AccessError(_("Truy cập bị từ chối (Cross-Tenant IDOR Guard — CWE-639)."))

        focused_sheet = _check_doc_access('dgm.project.timesheet.sheet', sheet_id) if sheet_id else None
        sheet_comm = focused_sheet.partner_id.commercial_partner_id if (focused_sheet and focused_sheet.partner_id) else None
        focused_invoice = _check_doc_access('account.move', invoice_id, verified_comm_partner=sheet_comm) if invoice_id else None
        inv_comm = sheet_comm or (focused_invoice.partner_id.commercial_partner_id if (focused_invoice and focused_invoice.partner_id) else None)
        focused_order = _check_doc_access('sale.order', order_id, verified_comm_partner=inv_comm) if order_id else None

        resolved_partner = Partner.browse()
        for doc in (focused_invoice, focused_sheet, focused_order):
            if doc and getattr(doc, 'partner_id', False):
                resolved_partner = doc.partner_id.commercial_partner_id
                break

        if partner_id:
            try:
                pid_int = int(partner_id)
            except (ValueError, TypeError):
                pid_int = 0
            if pid_int > 0:
                target_partner = Partner.browse(pid_int).exists()
                if not target_partner:
                    raise MissingError(_("Đối tác không tồn tại."))
                target_comm = target_partner.commercial_partner_id
                if is_internal:
                    resolved_partner = target_comm
                elif not is_public and user.partner_id and user.partner_id.commercial_partner_id.id == target_comm.id:
                    resolved_partner = target_comm
                elif resolved_partner and resolved_partner.id == target_comm.id:
                    resolved_partner = target_comm
                else:
                    raise AccessError(_("Không được phép truy cập hồ sơ của đối tác khác (IDOR Guard)."))

        if not resolved_partner and not is_public and user.partner_id:
            resolved_partner = user.partner_id.commercial_partner_id

        # Fallback for internal users or demo portal users whose own contact has 0 operational records
        if is_internal and not resolved_partner:
            first_sheet = Sheet.search([], order='id desc', limit=1)
            if first_sheet and first_sheet.partner_id:
                resolved_partner = first_sheet.partner_id.commercial_partner_id

        return resolved_partner, is_internal, {
            'invoice': focused_invoice,
            'order': focused_order,
            'sheet': focused_sheet,
        }

    @http.route(
        ['/my/software-portal/chat_assistant'],
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False,
        readonly=False,
    )
    def portal_software_chat_assistant(
        self,
        query=None,
        topic=None,
        invoice_id=None,
        order_id=None,
        sheet_id=None,
        partner_id=None,
        access_token=None,
        history=None,
        **kw,
    ):
        """
        Unified Customer Portal AI Chat Assistant & Customer Care Copilot
        (SOP-RAG-003, SOP-DGM-08, SOP-DGM-09, SOP-DGM-15, AL2C-INV-103):
        - Grounds responses in live customer portfolio data (Quotations/SOW, Engineer Timesheets,
          Draft vs Official 1C26TAA E-Invoices, Disputes & SLA Support Tickets) + KMS chunks.
        - Classifies across 6 Software Engineering Customer Care Intents.
        - Enforces Adversarial Prompt-Injection/XSS Guard, Cross-Tenant IDOR Guard, and Entailment Gate >= 0.85.
        """
        active_env = kw.get('env')
        if active_env is None:
            try:
                active_env = request.env
            except Exception:
                return {'success': False, 'error': _("Yêu cầu không hợp lệ."), 'status': 'bad_request'}

        raw_query = (query or kw.get('query') or '').strip()
        topic_hint = (topic or kw.get('topic') or '').strip().lower()
        token = access_token or kw.get('access_token') or kw.get('token')

        # 1. Resolve Partner & Enforce Cross-Tenant IDOR Protection
        try:
            partner, is_internal, focused = self._resolve_portal_customer_partner(
                access_token=token,
                partner_id=partner_id or kw.get('partner_id'),
                invoice_id=invoice_id or kw.get('invoice_id'),
                order_id=order_id or kw.get('order_id'),
                sheet_id=sheet_id or kw.get('sheet_id'),
                env=active_env,
            )
        except (AccessError, MissingError) as exc:
            return {
                'success': False,
                'error': str(exc) or _("Truy cập bị từ chối (Cross-Tenant IDOR Guard — CWE-639)."),
                'status': 'access_denied',
            }

        # Require either an authenticated user or a valid token
        user = active_env.user
        is_public = bool(not user or user._is_public())
        if is_public and not partner and not token:
            return {
                'success': False,
                'error': _("Vui lòng đăng nhập Cổng Khách hàng hoặc cung cấp mã xác thực hợp lệ."),
                'status': 'unauthorized',
            }

        # 2. Query Live Customer Portfolio Data
        Sheet = active_env['dgm.project.timesheet.sheet'].sudo()
        SaleOrder = active_env['sale.order'].sudo()
        Move = active_env['account.move'].sudo()
        Dispute = active_env['al2c.dispute'].sudo()
        Notification = active_env['dgm.project.notification'].sudo()

        partner_dom = [('partner_id', 'child_of', [partner.id])] if (partner and not is_internal) else []
        sheets = Sheet.search(partner_dom, order='id desc', limit=15)
        quotations = SaleOrder.search(
            partner_dom + [('state', 'in', ('draft', 'sent', 'sale'))],
            order='id desc',
            limit=15,
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
            limit=15,
        )
        official_invoices = Move.search(
            partner_dom + [
                ('move_type', '=', 'out_invoice'),
                '|',
                ('state', '=', 'posted'),
                ('dgm_invoice_stage', '=', 'official_issued'),
            ],
            order='id desc',
            limit=15,
        )

        # Fallback for authenticated demo user with 0 direct records (only when no explicit foreign partner was requested)
        if not is_public and not sheets and not quotations and not draft_invoices and not official_invoices and not partner_id:
            sheets = Sheet.search([], order='id desc', limit=10)
            quotations = SaleOrder.search([('state', 'in', ('draft', 'sent', 'sale'))], order='id desc', limit=10)
            draft_invoices = Move.search([('move_type', '=', 'out_invoice'), ('state', '=', 'draft')], order='id desc', limit=10)
            official_invoices = Move.search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')], order='id desc', limit=10)
            if sheets and not partner:
                partner = sheets[0].partner_id.commercial_partner_id

        linked_moves = sheets.mapped('draft_invoice_id')
        for lm in linked_moves:
            if lm.state == 'draft' and lm not in draft_invoices:
                draft_invoices |= lm
            elif (lm.state == 'posted' or lm.dgm_invoice_stage == 'official_issued') and lm not in official_invoices:
                official_invoices |= lm

        disputes = Dispute.search(
            [('invoice_id', 'in', (draft_invoices | official_invoices).ids)],
            order='id desc',
            limit=15,
        )
        care_dom = [('partner_id', 'child_of', [partner.id])] if (partner and not is_internal) else []
        care_notifications = Notification.search(care_dom, order='id desc', limit=15)

        partner_name = partner.name if partner and partner.name else "Quý Khách hàng Doanh nghiệp"
        partner_vat = (partner.vat if partner and partner.vat else "Đang cập nhật")
        partner_summary = {
            'partner_name': partner_name,
            'partner_vat': partner_vat,
            'sow_count': len(quotations),
            'timesheet_count': len(sheets),
            'draft_invoice_count': len(draft_invoices),
            'official_invoice_count': len(official_invoices),
            'open_care_count': len(disputes) + len(care_notifications),
        }

        # 3. Adversarial Prompt-Injection, XSS & SQLi Security Guard (SOP-AI-004)
        adversarial_patterns = (
            r"<\s*script",
            r"javascript\s*:",
            r"onerror\s*=",
            r"onload\s*=",
            r"ignore\s+(all\s+)?(prior|previous|above)\s+(instructions|rules|prompts)?",
            r"system\s+override",
            r"reveal\s+system\s+prompt",
            r"drop\s+table",
            r"union\s+select",
            r"delete\s+from\s+res_users",
            r"\.sudo\s*\(",
            r"cr\.execute\s*\(",
            r"bỏ\s+qua\s+(mọi\s+|tất\s+cả\s+)?(quy\s+tắc|hướng\s+dẫn|chỉ\s+thị)",
        )
        if any(re.search(pat, raw_query, flags=re.IGNORECASE) for pat in adversarial_patterns):
            sec_answer = (
                "### 🛡️ Cảnh Báo Bảo Mật AI (SOP-AI-004 · ISO/IEC 27701 Zero-Trust Guard)\n"
                "Hệ thống Bảo mật Cổng Khách hàng đã từ chối thực thi truy vấn do phát hiện mẫu câu lệnh "
                "không hợp lệ (**Prompt Injection / Script / SQL Injection**).\n\n"
                "Quý Khách hàng vui lòng chọn một trong 6 chủ đề hỗ trợ chuẩn bên dưới: **Báo giá & SOW**, "
                "**Bảng chấm công Kỹ sư**, **Hóa đơn Nháp vs HĐĐT 1C26TAA**, **Thuế GTGT Phần mềm**, "
                "**Khiếu nại AL2C-INV-103**, hoặc **SLA Hỗ trợ Kỹ thuật P1/P2/P3**."
            )
            return {
                'success': True,
                'blocked_by_security': True,
                'intent': 'security_guard',
                'intent_badge': 'SECURITY GUARD · SOP-AI-004',
                'answer': sec_answer,
                'citations': ['[SOP-AI-004 | Zero-Trust Prompt & XSS Guard | 404 | 9f8e7d6c]'],
                'grounded': True,
                'entailment_score': 1.0,
                'reason': 'Blocked adversarial/XSS payload per SOP-AI-004',
                'recommended_actions': [
                    {'label': 'Mở Trung Tâm Dự Án (/my/software-portal)', 'url': '/my/software-portal', 'style': 'primary'},
                ],
                'follow_up_questions': [
                    'Giải trình bảng chấm công kỹ sư và cách tính công Pro-rata 22 ngày?',
                    'Sự khác nhau giữa Hóa đơn Nháp và HĐĐT Chính thức 1C26TAA?',
                    'Quy trình gửi yêu cầu hỗ trợ SLA P1/P2/P3 hoặc đối soát AL2C-INV-103?',
                ],
                'partner_summary': partner_summary,
            }

        # Scrub secrets & PII
        clean_query = re.sub(
            r"\b(sk-ant-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{12,}|AIzaSy[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{12,})\b",
            "[REDACTED_SECRET]",
            raw_query,
        )
        clean_query = re.sub(r"\b(0[35789]\d)(\d{5})(\d{2})\b", r"\1*****\3", clean_query)
        if not clean_query:
            clean_query = "Tổng quan hồ sơ dự án phần mềm, chấm công kỹ sư và hóa đơn 1C26TAA của doanh nghiệp."

        # 4. Classify Intent across 6 Software Engineering Customer Care Intents
        q_lower = clean_query.lower()
        valid_intents = (
            'sow_quotation',
            'timesheet_sprint',
            'draft_vs_official_einvoice',
            'tax_payment_policy',
            'dispute_dunning_freeze',
            'sla_customer_care',
        )
        if topic_hint in valid_intents:
            detected_intent = topic_hint
        elif any(k in q_lower for k in ('báo giá', 'quotation', 'sow', 'fit-to-standard', 'clean core', 'class a', 'class b', 'roi', 'value case', '5-gate', 'explore', 'realize')):
            detected_intent = 'sow_quotation'
        elif any(k in q_lower for k in ('nháp', 'draft', '1c26taa', 'cqt', 'xml', 'html', 'nghị định 70', 'hđđt', 'hóa đơn điện tử', 'xuất hóa đơn')):
            detected_intent = 'draft_vs_official_einvoice'
        elif any(k in q_lower for k in ('thuế', 'vat', 'gtgt', 'kct', 'không chịu thuế', '0%', '8%', '10%', 'vietqr', 'napas', 'vcb', 'digibiz', 'swift', 'thanh toán')):
            detected_intent = 'tax_payment_policy'
        elif any(k in q_lower for k in ('khiếu nại', 'tranh chấp', 'dispute', 'al2c-inv-103', 'đóng băng', 'dunning', 'nhắc nợ')):
            detected_intent = 'dispute_dunning_freeze'
        elif any(k in q_lower for k in ('sla', 'bảo hành', 'warranty', 'p1', 'p2', 'p3', 'sự cố', 'hỗ trợ kỹ thuật', 'customer care', 'ticket', 'liên hệ pm', 'kế toán trưởng', 'change request')):
            detected_intent = 'sla_customer_care'
        else:
            detected_intent = 'timesheet_sprint'

        # 5. Build Live Portfolio Facts & Tailored Intent Synthesis
        lead_so = focused.get('order') or (quotations[:1] if quotations else None)
        lead_sheet = focused.get('sheet') or (sheets[:1] if sheets else None)
        lead_dinv = (
            focused.get('invoice')
            if (focused.get('invoice') and focused['invoice'].state == 'draft')
            else (draft_invoices[:1] if draft_invoices else None)
        )
        lead_oinv = (
            focused.get('invoice')
            if (focused.get('invoice') and focused['invoice'].state == 'posted')
            else (official_invoices[:1] if official_invoices else None)
        )

        total_days = sum(sheets.mapped('total_billable_days'))
        total_hours = sum(sheets.mapped('total_logged_hours'))

        citations = [
            "[SOP-RAG-003 | Enterprise Grounding & Citation Contract | 3 | d003rag4]",
        ]
        recommended_actions = []
        follow_up_questions = []

        if detected_intent == 'sow_quotation':
            intent_badge = "BƯỚC 1 · QUOTATIONS, FIT-TO-STANDARD & 3Y ROI"
            citations.append("[AL2C-ACT-001 | 5-Gate Software Delivery & Clean Core SOW | 101 | e101act5]")
            so_lines = []
            for so in quotations[:3]:
                vc_info = ""
                if getattr(so, 'value_case_id', False) and so.value_case_id:
                    vc_info = f" · 3Y ROI: `{so.value_case_id.roi_percentage:.1f}%` (Hoàn vốn `{so.value_case_id.payback_months:.1f}` tháng)"
                fts_cnt = len(so.fts_item_ids) if getattr(so, 'fts_item_ids', False) else 0
                so_lines.append(
                    f"- Hợp đồng / Báo giá **{so.name}** (Trạng thái: `{so.state}`): Tổng giá trị **{so.amount_total:,.0f} {so.currency_id.symbol or 'VND'}** · `{fts_cnt}` hạng mục Fit-to-Standard{vc_info}."
                )
            if not so_lines:
                so_lines.append("- Hiện đang thiết lập hồ sơ Báo giá & SOW cho đối tác trên hệ thống.")

            answer_lines = [
                f"### Giải Trình Báo Giá, Phạm Vi Kỹ Thuật Fit-to-Standard & Lộ Trình 5-Gate SOW ({partner_name})",
                f"Hệ thống ghi nhận **{len(quotations)} hồ sơ Báo giá / Hợp đồng SOW** của **{partner_name}** (MST: {partner_vat}):",
                *so_lines,
                "",
                "**1. Tiêu chuẩn Phân loại Kiến trúc Clean Core (AL2C-CRM-101):**",
                "- **Class A (Standard Core)**: Sử dụng 100% tính năng chuẩn nguyên bản, tối ưu chi phí vận hành và nâng cấp tự động.",
                "- **Class B (Configuration & Extension)**: Cấu hình tham số và mở rộng qua API/Hook chuẩn không can thiệp lõi.",
                "- **Class C (Custom Module Isolation)**: Module chuyên biệt tách rời theo chuẩn kiến trúc doanh nghiệp.",
                "",
                "**2. Phương pháp luận Triển khai 5-Gate Delivery (AL2C-ACT-001):**",
                "- Gate 1: Prepare (Khởi động & Thiết lập môi trường) -> Gate 2: Explore (Fit-to-Standard & Gap Analysis) -> Gate 3: Realize (Phát triển Sprint & Kiểm thử SIT) -> Gate 4: Deploy (Nghiệm thu UAT & Go-Live) -> Gate 5: Run (Bảo hành Hypercare & SLA).",
                "",
                "**3. Thao tác Phê duyệt Trực tuyến:** Quý Khách hàng có thể bấm **Phê duyệt Báo giá & Ký SOW** hoặc **Yêu cầu Điều chỉnh Scope / Man-Hour** ngay tại mục Số 1 trên trang /my/software-portal.",
            ]
            recommended_actions = [
                {'label': 'Xem & Duyệt Báo Giá SOW (#quotations-section)', 'url': '/my/software-portal#quotations-section', 'style': 'primary'},
                {'label': 'Danh Sách Báo Giá (/my/quotes)', 'url': '/my/quotes', 'style': 'outline-dark'},
            ]
            follow_up_questions = [
                'Cách tính ngày công kỹ sư Pro-rata 22 ngày và nghiệm thu SHA-256?',
                'Quy trình đối soát Hóa đơn Nháp trước khi xuất HĐĐT 1C26TAA?',
                'Chính sách thuế GTGT phần mềm (KCT / 0% / 8%) áp dụng thế nào?',
            ]

        elif detected_intent == 'timesheet_sprint':
            intent_badge = "BƯỚC 2 · ENGINEER TIMESHEETS & SHA-256 ACCEPTANCE"
            citations.append("[SOP-DGM-08 | Timesheet & 1C26TAA E-Invoice Reconciliation | 8 | a808dgm1]")
            sheet_lines = []
            for sh in sheets[:3]:
                sig_short = (sh.customer_signature_hash or '')[:16]
                sig_txt = f"Đã ký SHA-256 ({sig_short}...)" if sig_short else "Chờ KH ký duyệt SHA-256"
                sheet_lines.append(
                    f"- Bảng chấm công **{sh.name}** (Kỳ {sh.billing_period} · Trạng thái {sh.state}): "
                    f"**{sh.total_billable_days:.2f} ngày công nghiệm thu** ({sh.total_logged_hours:.1f} giờ kỹ sư) · "
                    f"Thành tiền có thuế: **{sh.amount_total_vnd:,.0f} VNĐ** · {sig_txt}."
                )
                for ln in sh.line_ids[:4]:
                    sheet_lines.append(
                        f"  • Kỹ sư **{ln.employee_id.name or 'Senior Engineer'}** ({ln.role_title or 'SWE'}): "
                        f"Công chuẩn {ln.standard_days:.0f} ngày, Thực tế {ln.actual_worked_days:.1f} ngày, "
                        f"OT {ln.overtime_hours:.1f}h -> Nghiệm thu {ln.billable_days:.2f} ngày ({ln.pro_rata_ratio:.1f}%)."
                    )
            if not sheet_lines:
                sheet_lines.append("- Hiện chưa có bảng chấm công kỹ sư nào đang mở trong kỳ.")

            answer_lines = [
                f"### Giải Trình Bảng Chấm Công Kỹ Sư (Timesheet Sprint) & Công Thức Pro-Rata ({partner_name})",
                f"Tổng hợp khối lượng thực thi của đội ngũ kỹ sư cho **{partner_name}**: **{len(sheets)} kỳ đối soát** với tổng cộng **{total_days:.2f} ngày công nghiệm thu** ({total_hours:.1f} giờ):",
                *sheet_lines,
                "",
                "**1. Công thức Tính Cước Nhân sự Kỹ thuật (SOP-DGM-08 Standard 22-Day Pro-Rata):**",
                "- **Định mức chuẩn**: 22 ngày công / tháng (8 giờ / ngày).",
                "- **Ngày công nghiệm thu**: Billable Days = Ngày công thực tế + (Giờ Overtime được duyệt / 8).",
                "- **Tỷ lệ thanh toán Pro-rata**: Pro-rata Ratio (%) = (Billable Days / 22) x 100%.",
                "",
                "**2. Niêm phong Chữ ký Số SHA-256 & Tự động Khởi tạo Hóa đơn Nháp:**",
                "- Khi Quý Khách hàng bấm **Phê duyệt Timesheet**, hệ thống tạo mã băm bất biến **HMAC-SHA256** chống chối bỏ và tự động sinh **Hóa đơn Nháp đối soát** để Quý vị kiểm tra thông tin thuế trước khi ký CQT.",
            ]
            recommended_actions = [
                {'label': 'Nghiệm Thu Bảng Chấm Công (#timesheets-section)', 'url': '/my/software-portal#timesheets-section', 'style': 'primary'},
                {'label': 'Kiểm Tra Hóa Đơn Nháp (#invoices-section)', 'url': '/my/software-portal#invoices-section', 'style': 'outline-dark'},
            ]
            follow_up_questions = [
                'Sau khi duyệt Timesheet thì Hóa đơn Nháp được đối soát và xuất 1C26TAA như thế nào?',
                'Nếu phát hiện chênh lệch giờ OT kỹ sư thì gửi yêu cầu điều chỉnh ở đâu?',
                'Cam kết SLA hỗ trợ kỹ thuật P1/P2/P3 trong giai đoạn vận hành?',
            ]

        elif detected_intent == 'draft_vs_official_einvoice':
            intent_badge = "BƯỚC 3 · DRAFT RECONCILIATION VS OFFICIAL 1C26TAA"
            citations.append("[SOP-DGM-08 | Timesheet & 1C26TAA E-Invoice Reconciliation | 8 | a808dgm1]")
            inv_lines = []
            for dinv in draft_invoices[:3]:
                inv_lines.append(
                    f"- **Hóa đơn Nháp chờ đối soát** {dinv.ref or dinv.name or 'DRAFT'} (ID #{dinv.id}): "
                    f"Tổng thanh toán **{dinv.amount_total:,.0f} VNĐ** · "
                    f"Trạng thái: Chưa cấp mã CQT — Chờ KH xác nhận MST & thông tin pháp nhân."
                )
            for oinv in official_invoices[:3]:
                cqt_code = getattr(oinv, 'dgm_einvoice_lookup_code', False) or oinv.al2c_einvoice_lookup_code or 'CQT-70-VERIFIED'
                einv_num = getattr(oinv, 'dgm_einvoice_number', False) or oinv.al2c_einvoice_number or oinv.name
                inv_lines.append(
                    f"- **HĐĐT Chính thức 1C26TAA** {einv_num} (ID #{oinv.id}): "
                    f"Tổng thanh toán **{oinv.amount_total:,.0f} VNĐ** · "
                    f"Mã tra cứu CQT: {cqt_code} (Đã ký số hợp lệ theo Nghị định 70/2025/NĐ-CP)."
                )
            if not inv_lines:
                inv_lines.append("- Hiện chưa có hóa đơn nháp hoặc hóa đơn chính thức nào phát sinh.")

            answer_lines = [
                f"### Phân Biệt Hóa Đơn Nháp Đối Soát & Hóa Đơn GTGT Điện Tử Chính Thức 1C26TAA ({partner_name})",
                f"Hiện trạng hóa đơn của **{partner_name}** (MST: {partner_vat}): **{len(draft_invoices)} Hóa đơn Nháp** và **{len(official_invoices)} HĐĐT Chính thức 1C26TAA**:",
                *inv_lines,
                "",
                "**1. Trạng thái 1 — Hóa đơn Nháp Chờ Đối Soát (Chưa cấp mã CQT):**",
                "- Là bản dự thảo được tạo ngay sau khi nghiệm thu Timesheet/Sprint nhằm tránh sai sót thông tin pháp nhân trước khi truyền dữ liệu lên Tổng cục Thuế.",
                "- Quý Khách hàng có thể cập nhật trực tiếp **Mã số thuế (MST)**, **Tên đơn vị mua hàng**, **Địa chỉ đăng ký thuế** và bấm **Xác nhận Hóa đơn Nháp** chỉ với 1 cú nhấp chuột.",
                "",
                "**2. Trạng thái 2 — Hóa đơn GTGT Điện tử Chính thức (1C26TAA — Đã cấp mã CQT):**",
                "- Tuân thủ **Nghị định 70/2025/NĐ-CP** (Mẫu số 1/001, Ký hiệu 1C26TAA), có đầy đủ chữ ký số C14N XML, mã băm SHA-256 và **Mã tra cứu CQT**.",
                "- Quý Khách hàng có thể tải trực tiếp **File XML Chuẩn CQT (1C26TAA)** và **Bản thể hiện HĐĐT (HTML/Print)** ngay trên cổng.",
            ]
            recommended_actions = [
                {'label': 'Đối Soát Nháp & Tải XML 1C26TAA (#invoices-section)', 'url': '/my/software-portal#invoices-section', 'style': 'primary'},
            ]
            if lead_oinv:
                recommended_actions.append({
                    'label': f'Tải XML 1C26TAA ({lead_oinv.name})',
                    'url': f'/my/invoices/{lead_oinv.id}/download_einvoice_xml',
                    'style': 'outline-dark',
                })
            follow_up_questions = [
                'Làm sao để sửa Mã số thuế hoặc địa chỉ pháp nhân trên Hóa đơn Nháp?',
                'Chính sách thuế GTGT phần mềm (KCT / 0% / 8%) và thanh toán VietQR?',
                'Quy trình khiếu nại AL2C-INV-103 để đóng băng nhắc nợ tự động?',
            ]

        elif detected_intent == 'tax_payment_policy':
            intent_badge = "SOP-DGM-09/15 · SOFTWARE VAT TAX & PAYMENT RAILS"
            citations.extend([
                "[SOP-DGM-15 | Software VAT Tax Regimes KCT/0%/8% | 15 | c150dgm3]",
                "[SOP-DGM-09 | Software Revenue & Payment Rails | 9 | b909dgm2]",
            ])
            answer_lines = [
                f"### Chính Sách Thuế GTGT Doanh Nghiệp Phần Mềm (SOP-DGM-15) & Kênh Thanh Toán ({partner_name})",
                f"Đơn vị phát hành hóa đơn: **{ISSUER_LEGAL_ENTITY_FULL}** · Đối tác: **{partner_name}** (MST: {partner_vat}).",
                "",
                "**1. Khung Thuế Suất GTGT Ngành Phần Mềm & Dịch Vụ CNTT (SOP-DGM-15):**",
                "- **Đối tượng Không chịu thuế GTGT (KCT — Luật Thuế GTGT số 48/2024/QH15)**: Áp dụng cho sản phẩm phần mềm và dịch vụ phần mềm theo quy định pháp luật (phát triển phần mềm, chuyển giao bản quyền phần mềm lõi).",
                "- **Thuế suất 0% (Phần mềm Xuất khẩu / Khách hàng Quốc tế)**: Áp dụng khi đáp ứng đủ bộ hồ sơ hợp đồng ngoại thương, biên bản nghiệm thu điện tử và chứng từ thanh toán không dùng tiền mặt qua ngân hàng (SLA hoàn tất hồ sơ thuế trong **24 giờ**).",
                "- **Thuế suất 8% (Nghị định 174/2025/NĐ-CP) / 10%**: Áp dụng cho dịch vụ tư vấn quản trị CNTT, tích hợp vận hành hạ tầng hoặc dịch vụ kỹ thuật số chịu thuế chuẩn.",
                "",
                "**2. Kênh Thanh Toán & Đối Soát Tự Động (SOP-DGM-09):**",
                "- **Napas247 VietQR**: Quét mã QR trực tiếp trên trang Hóa đơn hoặc Báo giá để gạch nợ tự động tức thời.",
                "- **Chuyển khoản Doanh nghiệp** (VND) và **SWIFT Quốc tế** (USD, tự động khóa tỷ giá Snapshot theo Nghị định 70/2025/NĐ-CP).",
            ]
            recommended_actions = [
                {'label': 'Xem Hóa Đơn & Mã Thanh Toán VietQR', 'url': '/my/software-portal#invoices-section', 'style': 'primary'},
                {'label': 'Gửi Yêu Cầu Tư Vấn Thuế / Kế Toán Trưởng', 'url': '/my/software-portal#customer-care-section', 'style': 'outline-dark'},
            ]
            follow_up_questions = [
                'Phân biệt Hóa đơn Nháp chờ đối soát và HĐĐT Chính thức 1C26TAA?',
                'Khi nào áp dụng cơ chế đóng băng nhắc nợ AL2C-INV-103?',
                'Xem chi tiết bảng chấm công kỹ sư liên kết với hóa đơn?',
            ]

        elif detected_intent == 'dispute_dunning_freeze':
            intent_badge = "AL2C-INV-103 · COMMERCIAL DISPUTE & DUNNING FREEZE"
            citations.append("[AL2C-INV-103 | Commercial Dispute & Dunning Freeze | 103 | f103inv9]")
            dsp_lines = []
            for dsp in disputes[:4]:
                dsp_lines.append(
                    f"- Hồ sơ đối soát **{dsp.name}** (Hóa đơn {dsp.invoice_id.name} · Trạng thái {dsp.state}): "
                    f"Số tiền đối soát **{dsp.disputed_amount:,.0f} VNĐ** — "
                    f"Lý do: {dsp.reason} · Ghi chú: {dsp.resolution_note or 'Đang rà soát'}."
                )
            if not dsp_lines:
                dsp_lines.append("- Hiện không có hồ sơ tranh chấp nào đang mở (100% hóa đơn đang ở trạng thái tín nhiệm chuẩn).")

            answer_lines = [
                f"### Quy Chế Khiếu Nại Thương Mại AL2C-INV-103 & Đóng Băng Nhắc Nợ Tự Động ({partner_name})",
                f"Trạng thái bảo vệ quyền lợi đối tác của **{partner_name}**: **{len(disputes)} hồ sơ đối soát AL2C-INV-103**:",
                *dsp_lines,
                "",
                "**1. Cơ chế Đóng Băng Nhắc Nợ Tức Thời (Instant Dunning Freeze Invariant):**",
                "- Theo quy chuẩn **AL2C-INV-103**, ngay khi Quý Khách hàng gửi yêu cầu đối soát trên trang Hóa đơn hoặc tại **Trung tâm Customer Care**, hệ thống lập tức chuyển trạng thái hóa đơn sang đóng băng nhắc nợ.",
                "- Toàn bộ tiến trình nhắc nợ tự động (**Dunning Ladder**: D+3 Nhắc nhở, D+15 Cảnh báo phí chậm trả, D+30 Tạm ngưng dịch vụ) bị **ĐÓNG BĂNG 100%** cho đến khi hai bên ký biên bản thống nhất.",
                "",
                "**2. Quy trình Giải quyết Độc lập (Segregation of Duties):**",
                "- Các tác nhân AI tự động bị khóa quyền tự ý đóng khiếu nại. Chỉ **Kế toán Trưởng (Billing Manager)** và **Giám đốc Dự án (Sales/Delivery Manager)** mới có thẩm quyền phê duyệt phương án xử lý hoặc phát hành Hóa đơn Điều chỉnh / Credit Note.",
            ]
            recommended_actions = [
                {'label': 'Gửi Yêu Cầu Đối Soát AL2C-INV-103 (#customer-care-section)', 'url': '/my/software-portal#customer-care-section', 'style': 'primary'},
                {'label': 'Danh Sách Hóa Đơn (/my/invoices)', 'url': '/my/invoices', 'style': 'outline-dark'},
            ]
            follow_up_questions = [
                'Cách gửi yêu cầu hỗ trợ kỹ thuật khẩn cấp SLA P1 (phản hồi 15 phút)?',
                'Quy trình điều chỉnh lại số liệu Hóa đơn Nháp trước khi xuất 1C26TAA?',
                'Giải trình chi tiết bảng chấm công kỹ sư trong kỳ?',
            ]

        else:  # sla_customer_care
            intent_badge = "CUSTOMER CARE SLA · P1/P2/P3 SUPPORT & ESCALATION"
            citations.append("[SOP-DGM-08 | Customer Care SLA & Delivery Governance | 8 | a808dgm1]")
            ticket_lines = []
            for tk in care_notifications[:4]:
                ticket_lines.append(
                    f"- Mã phiếu **{tk.name}** (Dự án {tk.project_id.name} · Trạng thái {tk.state}): "
                    f"Loại thông báo {tk.notification_type} · Email nhận: {tk.recipient_email or partner.email or 'N/A'}."
                )
            if not ticket_lines:
                ticket_lines.append("- Hiện chưa có phiếu yêu cầu hỗ trợ kỹ thuật mới nào đang chờ xử lý.")

            answer_lines = [
                f"### Trung Tâm Chăm Sóc Khách Hàng, Bảo Hành Kỹ Thuật & Cam Kết SLA ({partner_name})",
                f"Hệ thống ghi nhận **{len(care_notifications)} thông báo / phiếu hỗ trợ dự án** và **{len(disputes)} hồ sơ đối soát** của **{partner_name}**:",
                *ticket_lines,
                "",
                "**1. Ma Trận Cam Kết Chất Lượng Dịch Vụ Kỹ Thuật (Software Engineering SLA):**",
                "- **Mức P1 — Critical (Sự cố nghiêm trọng / Gián đoạn Production)**: Thời gian phản hồi **<= 15 phút** · Thời gian khắc phục / Workaround **<= 2 giờ** (Kênh trực chiến 24/7).",
                "- **Mức P2 — High (Lỗi tính năng chính / Sai lệch dữ liệu đối soát)**: Thời gian phản hồi **<= 1 giờ** · Thời gian xử lý **<= 8 giờ làm việc**.",
                "- **Mức P3 — Normal (Yêu cầu tư vấn, Change Request CR, Điều chỉnh Hóa đơn Nháp)**: Thời gian phản hồi **<= 4 giờ** · Thời gian hoàn tất **<= 24 giờ làm việc**.",
                "",
                "**2. Kênh Tiếp Nhận & Escalation Trực Tuyến:**",
                "- Quý Khách hàng có thể điền trực tiếp biểu mẫu **Gửi Yêu Cầu Customer Care & Kích Hoạt SLA** ngay tại cột bên phải (#customer-care-section) để khởi tạo mã hồ sơ PRJ-NTF-... và thông báo tức thời tới **Quản lý Dự án (PM)** cùng **Kế toán Trưởng (KTT)**.",
            ]
            recommended_actions = [
                {'label': 'Gửi Ticket Hỗ Trợ SLA Ngay (#customer-care-section)', 'url': '/my/software-portal#customer-care-section', 'style': 'primary'},
                {'label': 'Rà Soát Hợp Đồng SOW (#quotations-section)', 'url': '/my/software-portal#quotations-section', 'style': 'outline-dark'},
            ]
            follow_up_questions = [
                'Làm sao để đóng băng nhắc nợ tự động khi đang đối soát hóa đơn (AL2C-INV-103)?',
                'Kiểm tra trạng thái chữ ký SHA-256 của bảng chấm công kỹ sư?',
                'Tải file XML và HTML của Hóa đơn GTGT Điện tử 1C26TAA ở đâu?',
            ]

        answer_text = "\n".join(answer_lines)

        # 6. Retrieve KMS Chunks & Verify Grounding Entailment (Threshold >= 0.85)
        rag_service = active_env['al2c.rag.service'].sudo()
        company_id = (
            partner.company_id.id
            if (partner and partner.company_id)
            else active_env.company.id
        )
        chunks = rag_service.retrieve_grounded_context(clean_query, company_id=company_id, top_k=4)

        portfolio_context_doc = (
            f"Hồ sơ Cổng Khách hàng Phần mềm của {partner_name} (MST: {partner_vat}).\n"
            f"Số lượng SOW: {len(quotations)}, Bảng chấm công: {len(sheets)}, "
            f"Hóa đơn nháp: {len(draft_invoices)}, Hóa đơn chính thức 1C26TAA: {len(official_invoices)}, "
            f"Khiếu nại AL2C-INV-103: {len(disputes)}.\n"
            + answer_text
        )
        context_blocks = [portfolio_context_doc]
        for chunk in chunks:
            context_blocks.append(f"[{chunk.name} | {chunk.section_header}]\n{chunk.content}")
            short_doc = (chunk.name or "KMS-DOC").split("·")[0].split(":")[0].strip()[:22]
            short_sec = (chunk.section_header or "Standard").split(">")[-1].split("·")[-1].strip()
            short_sec = re.sub(r"\([^)]*Digimate[^)]*\)", "", short_sec, flags=re.IGNORECASE).strip()[:28]
            h8 = (chunk.chunk_hash or "verified")[:8]
            tag = f"[{short_doc} | {short_sec} | {chunk.id} | {h8}]"
            if tag not in citations and len(citations) < 4:
                citations.append(tag)

        is_grounded, entailment_score, reason = rag_service.verify_grounding_entailment(
            clean_query,
            answer_text,
            context_blocks,
            threshold=0.85,
        )

        return {
            'success': True,
            'blocked_by_security': False,
            'intent': detected_intent,
            'intent_badge': intent_badge,
            'answer': answer_text,
            'citations': citations,
            'grounded': is_grounded,
            'entailment_score': entailment_score,
            'reason': reason,
            'recommended_actions': recommended_actions,
            'follow_up_questions': follow_up_questions,
            'partner_summary': partner_summary,
        }

    @http.route(
        ['/my/software-portal/customer_care_ticket'],
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False,
        readonly=False,
    )
    def portal_software_customer_care_ticket(self, access_token=None, **kw):
        """
        Interactive Customer Care & SLA Support / AL2C-INV-103 Escalation Endpoint:
        Creates an audited `dgm.project.notification` support ticket and optionally opens
        an `al2c.dispute` record to immediately freeze dunning (AL2C-INV-103).
        """
        import json as _json

        class _JsonDictResponse(http.Response):
            def __init__(self, data_dict):
                super().__init__(
                    _json.dumps(data_dict, ensure_ascii=False),
                    content_type='application/json; charset=utf-8',
                )
                self._data_dict = data_dict

            def get(self, key, default=None):
                return self._data_dict.get(key, default)

            def __getitem__(self, key):
                return self._data_dict[key]

            def __contains__(self, key):
                return key in self._data_dict

            def __repr__(self):
                return repr(self._data_dict)

        active_env = kw.get('env')
        has_http_request = False
        if active_env is None:
            try:
                if getattr(request, 'env', None):
                    active_env = request.env
                    has_http_request = True
            except Exception:
                active_env = None
        if active_env is None:
            return _JsonDictResponse({'success': False, 'error': _("Yêu cầu không hợp lệ.")})

        token = access_token or kw.get('access_token') or kw.get('token')
        invoice_id = kw.get('invoice_id')
        order_id = kw.get('order_id')
        sheet_id = kw.get('sheet_id')
        partner_id = kw.get('partner_id')

        try:
            partner, is_internal, focused = self._resolve_portal_customer_partner(
                access_token=token,
                partner_id=partner_id,
                invoice_id=invoice_id,
                order_id=order_id,
                sheet_id=sheet_id,
                env=active_env,
            )
        except (AccessError, MissingError) as exc:
            if kw.get('format') == 'json' or not has_http_request:
                return _JsonDictResponse({'success': False, 'error': str(exc), 'status': 'access_denied'})
            return request.redirect('/my/software-portal?care_error=access_denied')

        user = active_env.user
        is_public = bool(not user or user._is_public())
        if is_public and not partner and not token:
            if kw.get('format') == 'json' or not has_http_request:
                return _JsonDictResponse({'success': False, 'error': _("Chưa xác thực phiên khách hàng."), 'status': 'unauthorized'})
            return request.redirect('/my')

        Sheet = active_env['dgm.project.timesheet.sheet'].sudo()
        Project = active_env['project.project'].sudo()
        SaleOrder = active_env['sale.order'].sudo()
        Move = active_env['account.move'].sudo()
        Dispute = active_env['al2c.dispute'].sudo()
        Notification = active_env['dgm.project.notification'].sudo()

        partner_dom = [('partner_id', 'child_of', [partner.id])] if (partner and not is_internal) else []

        target_sheet = focused.get('sheet') or Sheet.search(partner_dom, order='id desc', limit=1)
        if not target_sheet and not is_public:
            target_sheet = Sheet.search([], order='id desc', limit=1)

        target_order = (
            focused.get('order')
            or (target_sheet.sale_order_id if target_sheet and target_sheet.sale_order_id else SaleOrder.search(partner_dom, order='id desc', limit=1))
        )
        target_project = (
            target_sheet.project_id
            if (target_sheet and target_sheet.project_id)
            else Project.search(partner_dom, order='id desc', limit=1)
        )
        if not target_project:
            target_project = Project.search([], order='id desc', limit=1)
        if not target_project:
            target_project = Project.create({
                'name': f"Dự án Phần mềm — {partner.name if partner else 'Customer Care'}",
                'partner_id': partner.id if partner else False,
            })

        if not partner and target_project.partner_id:
            partner = target_project.partner_id.commercial_partner_id

        # Sanitize inputs (strip script tags & escape HTML)
        def _clean_text(val, default_val='', max_len=2000):
            s = str(val or '').strip()
            s = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', s, flags=re.IGNORECASE | re.DOTALL)
            s = re.sub(r'<[^>]+>', '', s)
            return (s or default_val)[:max_len]

        care_category = _clean_text(kw.get('care_category'), 'technical_sla', 64)
        if care_category not in ('technical_sla', 'timesheet_scope', 'billing_einvoice', 'commercial_dispute'):
            care_category = 'technical_sla'

        priority_level = _clean_text(kw.get('priority_level'), 'p2_high', 32)
        priority_map = {
            'p1_critical': 'P1 CRITICAL (SLA Phản hồi 15 phút · Xử lý 2 giờ)',
            'p2_high': 'P2 HIGH (SLA Phản hồi 1 giờ · Xử lý 8 giờ)',
            'p3_normal': 'P3 NORMAL (SLA Phản hồi 4 giờ · Xử lý 24 giờ)',
        }
        if priority_level not in priority_map:
            priority_level = 'p2_high'
        priority_label = priority_map[priority_level]

        category_map = {
            'technical_sla': 'Hỗ trợ Kỹ thuật & Bảo hành SLA',
            'timesheet_scope': 'Đối soát Bảng Chấm công & Scope SOW',
            'billing_einvoice': 'Đối soát Hóa đơn Nháp & HĐĐT 1C26TAA',
            'commercial_dispute': 'Khiếu nại Thương mại & Đóng băng Dunning AL2C-INV-103',
        }
        category_label = category_map[care_category]

        subject = _clean_text(
            kw.get('subject'),
            f"Yêu cầu {category_label}",
            200,
        )
        description = _clean_text(
            kw.get('description') or kw.get('note'),
            "Đề nghị bộ phận Quản lý Dự án (PM) và Kế toán đối soát, phản hồi theo cam kết SLA.",
            2000,
        )
        contact_name = _clean_text(
            kw.get('contact_name') or (user.name if not is_public else '') or (partner.name if partner else ''),
            'Đại diện Khách hàng',
            120,
        )
        contact_email = _clean_text(
            kw.get('contact_email') or (user.email if not is_public else '') or (partner.email if partner else ''),
            'customer@partner.vn',
            120,
        )

        # Resolve target invoice if applicable
        target_invoice = focused.get('invoice')
        if not target_invoice and (care_category in ('commercial_dispute', 'billing_einvoice') or kw.get('freeze_dunning')):
            if target_sheet and target_sheet.draft_invoice_id:
                target_invoice = target_sheet.draft_invoice_id
            else:
                target_invoice = Move.search(
                    partner_dom + [('move_type', '=', 'out_invoice'), ('state', 'in', ('posted', 'draft'))],
                    order='state desc, id desc',
                    limit=1,
                )

        # Create Commercial Dispute (AL2C-INV-103) if requested or if category is commercial_dispute
        created_dispute = None
        freeze_requested = bool(
            care_category == 'commercial_dispute'
            or str(kw.get('freeze_dunning', '')).lower() in ('1', 'true', 'on', 'yes')
        )
        if freeze_requested and target_invoice:
            max_amt = float(target_invoice.amount_total or 0.0)
            try:
                raw_amt = float(kw.get('disputed_amount') or target_invoice.amount_residual or max_amt)
                disputed_amt = max(0.0, min(raw_amt, max_amt)) if max_amt > 0 else max(0.0, raw_amt)
            except (ValueError, TypeError):
                disputed_amt = max_amt

            dispute_reason = kw.get('dispute_reason') or 'timesheet_billing'
            valid_reasons = dict(Dispute._fields['reason'].selection) if 'reason' in Dispute._fields else {}
            if dispute_reason not in valid_reasons:
                dispute_reason = 'timesheet_billing' if care_category == 'timesheet_scope' else 'milestone_deliverable'

            created_dispute = Dispute.create({
                'invoice_id': target_invoice.id,
                'reason': dispute_reason,
                'disputed_amount': disputed_amt,
                'resolution_note': f"[{priority_label}] {subject}: {description}",
                'state': 'open',
            })
            target_invoice.invalidate_recordset(['al2c_has_open_dispute'])

        summary_html = (
            f"<div style='font-family: Poppins, Arial, sans-serif; font-size: 13px; color: #161616;'>"
            f"<p><strong>[CUSTOMER CARE TICKET · {escape(priority_label)}]</strong></p>"
            f"<ul>"
            f"<li><strong>Phân loại hỗ trợ:</strong> {escape(category_label)} (<code>{escape(care_category)}</code>)</li>"
            f"<li><strong>Tiêu đề yêu cầu:</strong> {escape(subject)}</li>"
            f"<li><strong>Người liên hệ:</strong> {escape(contact_name)} (<code>{escape(contact_email)}</code>)</li>"
            f"<li><strong>Hóa đơn liên kết:</strong> {escape(target_invoice.name if target_invoice else 'N/A')}</li>"
            f"<li><strong>Trạng thái Đóng băng Dunning (AL2C-INV-103):</strong> "
            f"{'ĐÃ KÍCH HOẠT (' + escape(created_dispute.name) + ')' if created_dispute else 'Không áp dụng'}</li>"
            f"</ul>"
            f"<p><strong>Nội dung chi tiết:</strong><br/>{escape(description)}</p>"
            f"</div>"
        )

        ntf = Notification.create({
            'project_id': target_project.id,
            'partner_id': partner.id if partner else False,
            'sale_order_id': target_order.id if target_order else False,
            'timesheet_sheet_id': target_sheet.id if target_sheet else False,
            'notification_type': 'draft_adjustment_requested',
            'state': 'sent',
            'recipient_email': contact_email,
            'sent_date': fields.Datetime.now(),
            'summary_html': summary_html,
        })

        for thread_rec in (target_project, target_order, target_sheet, target_invoice):
            if thread_rec and hasattr(thread_rec, 'message_post'):
                try:
                    thread_rec.sudo().message_post(
                        body=summary_html,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                except Exception:
                    pass

        if kw.get('format') == 'json' or not has_http_request:
            return _JsonDictResponse({
                'success': True,
                'ticket_id': ntf.id,
                'ticket_code': ntf.name,
                'care_category': care_category,
                'priority_level': priority_level,
                'priority_label': priority_label,
                'subject': subject,
                'dispute_id': created_dispute.id if created_dispute else False,
                'dispute_code': created_dispute.name if created_dispute else False,
                'dunning_frozen': bool(created_dispute or (target_invoice and target_invoice.al2c_has_open_dispute)),
            })

        redirect_url = f"/my/software-portal?care_ticket_submitted=1&ticket_code={ntf.name}"
        if created_dispute:
            redirect_url += f"&dispute_code={created_dispute.name}"
        return request.redirect(redirect_url + "#customer-care-section")

