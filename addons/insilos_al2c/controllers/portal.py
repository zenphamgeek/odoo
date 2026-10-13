# -*- coding: utf-8 -*-
from markupsafe import escape
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal


class Al2cPortalController(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>/dispute'], type='http', auth='public', methods=['POST'], website=True, csrf=True)
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

        query = '&dispute_submitted=1'
        if access_token:
            query += f'&access_token={access_token}'
        return request.redirect(invoice_sudo.get_portal_url(query_string=query))

    @http.route(['/my/invoices/<int:invoice_id>/confirm_timesheet'], type='http', auth='public', methods=['POST', 'GET'], website=True, csrf=False)
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
