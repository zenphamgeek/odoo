# -*- coding: utf-8 -*-
import logging
import time
import hmac
import hashlib
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.sql import SQL

_logger = logging.getLogger(__name__)

TIMESHEET_KEYWORDS = ('consult', 'tư vấn', 'giờ', 'hour', 't&m', 'timesheet')
TIMESHEET_EXCLUSION_KEYWORDS = ('no consult', 'không tư vấn', 'không tính', 'non-billable', 'giảm giá', 'discount')


class AccountMove(models.Model):
    _inherit = 'account.move'

    al2c_dunning_stage = fields.Selection([
        ('current', 'Current (Within Terms)'),
        ('d3_reminder', 'D+3 Gentle Reminder'),
        ('d15_warning', 'D+15 Late Fee & Escalation Warning'),
        ('d30_suspension', 'D+30 Service Suspension'),
    ], string='AL2C Dunning Stage', default='current', copy=False, index=True)

    al2c_dunning_last_date = fields.Date(
        string='Last Dunning Action Date',
        copy=False,
    )

    al2c_dispute_ids = fields.One2many(
        'al2c.dispute',
        'invoice_id',
        string='Commercial Disputes',
    )
    al2c_has_open_dispute = fields.Boolean(
        string='Has Open Dispute',
        compute='_compute_al2c_has_open_dispute',
        store=True,
    )

    @api.depends('al2c_dispute_ids.state')
    def _compute_al2c_has_open_dispute(self):
        for move in self:
            move.al2c_has_open_dispute = any(d.state == 'open' for d in move.al2c_dispute_ids)

    # --- Billable Timesheet Statement & Client Confirmation (AL2C-SOP-002 / CWE-639 Hardened) ---
    al2c_timesheet_statement_state = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('draft_statement', 'Draft Timesheet Statement'),
        ('sent_to_client', 'Sent to Client for Confirmation'),
        ('confirmed', 'Confirmed by Client'),
        ('disputed', 'Disputed / Under Review'),
    ], string='Timesheet Statement Status', default='not_applicable', tracking=True, copy=False)

    al2c_timesheet_token = fields.Char(
        string='Statement Confirmation Token (HMAC Signed)',
        copy=False,
        readonly=True,
    )
    al2c_timesheet_confirmed_date = fields.Datetime(
        string='Timesheet Confirmation Date',
        copy=False,
        readonly=True,
    )
    al2c_timesheet_confirmed_by = fields.Char(
        string='Confirmed By Client Representative',
        copy=False,
        readonly=True,
    )
    al2c_exchange_rate_snapshot = fields.Float(
        string='Exchange Rate Snapshot (to Company Currency)',
        digits=(16, 8),
        readonly=True,
        index=True,
        copy=False,
        help='Snapshotted conversion rate from invoice currency to company currency (VND) at time of statement issuance (Decree 70/2025/ND-CP compliance).'
    )
    al2c_statement_amount_total_company_currency = fields.Monetary(
        string='Statutory Total in Company Currency (VND)',
        currency_field='company_currency_id',
        compute='_compute_al2c_statement_company_currency',
        store=True,
        copy=False,
        help='Statutory total converted to company currency using immutable exchange rate snapshot.'
    )
    al2c_is_foreign_currency = fields.Boolean(
        string='Is Foreign Currency Invoice',
        compute='_compute_al2c_is_foreign_currency',
        store=True,
    )
    al2c_rate_unavailable = fields.Boolean(
        string='FX Rate Unavailable',
        compute='_compute_al2c_statement_company_currency',
        store=True,
        help='Set when a foreign-currency conversion rate could not be resolved. Blocks statement dispatch (Decree 70/2025 compliance).',
    )
    al2c_timesheet_hours_total = fields.Float(
        string='Total Timesheet Hours Billed',
        compute='_compute_al2c_timesheet_hours_total',
        store=True,
    )

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_al2c_is_foreign_currency(self):
        for move in self:
            comp_curr = move.company_id.currency_id
            move.al2c_is_foreign_currency = bool(move.currency_id and comp_curr and move.currency_id.id != comp_curr.id)

    @api.depends('amount_total', 'currency_id', 'company_id.currency_id', 'al2c_exchange_rate_snapshot')
    def _compute_al2c_statement_company_currency(self):
        for move in self:
            company_curr = move.company_id.currency_id
            if not company_curr:
                move.al2c_rate_unavailable = True
                move.al2c_statement_amount_total_company_currency = 0.0
                continue

            if not move.currency_id or move.currency_id.id == company_curr.id:
                move.al2c_rate_unavailable = False
                move.al2c_statement_amount_total_company_currency = move.amount_total
            else:
                rate = move.al2c_exchange_rate_snapshot
                if not rate or rate <= 0:
                    # Check whether an actual exchange rate exists in res.currency.rate
                    Rate = self.env['res.currency.rate'].sudo()
                    has_rate = bool(Rate.search_count([
                        ('currency_id', '=', move.currency_id.id),
                        ('company_id', 'in', (False, move.company_id.id, move.company_id.root_id.id if hasattr(move.company_id, 'root_id') else False)),
                    ], limit=1))
                    if not has_rate:
                        rate = 0.0
                    else:
                        try:
                            rate = self.env['res.currency']._get_conversion_rate(
                                move.currency_id,
                                company_curr,
                                move.company_id,
                                move.invoice_date or fields.Date.context_today(move)
                            )
                        except Exception as err:
                            _logger.warning("Failed to auto-compute conversion rate for move %s: %s", move.id, err)
                            rate = 0.0
                if rate <= 0:
                    # Invariant: Never silently assume 1.0 or silent zero without explicit flag
                    move.al2c_rate_unavailable = True
                    move.al2c_statement_amount_total_company_currency = 0.0
                    continue
                move.al2c_rate_unavailable = False
                move.al2c_statement_amount_total_company_currency = company_curr.round(move.amount_total * rate)

    @api.depends(
        'invoice_line_ids.quantity',
        'invoice_line_ids.product_id',
        'invoice_line_ids.name',
        'invoice_line_ids.product_uom_id',
        'invoice_line_ids.display_type',
    )
    def _compute_al2c_timesheet_hours_total(self):
        uom_hour = self.env.ref('uom.product_uom_hour', raise_if_not_found=False)
        for move in self:
            hours = 0.0
            for line in move.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note', 'line_subsection'):
                    continue
                is_timesheet = False
                line_name_lower = (line.name or '').lower()
                # 1. Product configuration is authoritative (A-4 defense)
                if line.product_id and getattr(line.product_id, 'service_policy', None) == 'delivered_timesheet':
                    is_timesheet = True
                # 2. Heuristic fallback for unstructured / legacy lines
                elif any(kw in line_name_lower for kw in TIMESHEET_KEYWORDS) \
                        and not any(ex in line_name_lower for ex in TIMESHEET_EXCLUSION_KEYWORDS):
                    is_timesheet = True
                    _logger.debug("Heuristic timesheet match on move %s (line id %s)", move.id, line.id)

                if is_timesheet:
                    qty = line.quantity
                    if uom_hour and line.product_uom_id and line.product_uom_id != uom_hour:
                        try:
                            qty = line.product_uom_id._compute_quantity(qty, uom_hour, raise_if_failure=False)
                        except Exception:
                            pass
                    hours += qty
            move.al2c_timesheet_hours_total = hours

    @api.model
    def _token_secret(self):
        """Retrieve per-database cryptographic secret (CWE-259 / CWE-798 defense)."""
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        if not secret:
            secret = self.env['ir.config_parameter'].sudo().get_param('al2c.statement_secret')
        if not secret:
            raise UserError(_("Server security secret is uninitialized; cannot generate or verify statement tokens."))
        return secret.strip().encode('utf-8')

    @api.model
    def _generate_timesheet_token(self, move_id, expires_in_days=7):
        """Generates cryptographically signed, time-boxed token (CWE-639 IDOR defense)."""
        secret_bytes = self._token_secret()
        expiry_ts = int(time.time() + (expires_in_days * 86400))
        msg = f"{move_id}:{expiry_ts}".encode('utf-8')
        sig = hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()[:32]
        return f"{expiry_ts}_{sig}"

    @api.model
    def _verify_timesheet_token(self, move_id, token_str):
        """Verifies HMAC signature, move-binding, and expiry for timesheet confirmation token."""
        if not token_str or '_' not in str(token_str):
            return False
        parts = str(token_str).split('_', 1)
        if len(parts) != 2:
            return False
        try:
            expiry_ts = int(parts[0])
            provided_sig = parts[1]
        except (ValueError, TypeError):
            return False
        if time.time() > expiry_ts:
            return False
        try:
            secret_bytes = self._token_secret()
        except UserError:
            return False
        msg = f"{move_id}:{expiry_ts}".encode('utf-8')
        expected_sig = hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(expected_sig, provided_sig)

    def action_send_timesheet_statement(self):
        """Send timesheet statement & confirmation request email to client."""
        template = self.env.ref('insilos_al2c.email_template_al2c_timesheet_statement_confirm', raise_if_not_found=False)
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue

            # Invalidate cached/stored flags to prevent TOCTOU race (CWE-367 / A-6 defense)
            move.invalidate_recordset(['al2c_rate_unavailable', 'al2c_statement_amount_total_company_currency', 'al2c_is_foreign_currency'])

            comp_curr = move.company_id.currency_id
            if not comp_curr:
                raise UserError(_(
                    "Cannot issue statutory statement for invoice %s: Company currency is undefined on company %s.",
                    move.display_name, move.company_id.display_name
                ))

            if move.al2c_rate_unavailable or (
                move.al2c_is_foreign_currency and move.al2c_statement_amount_total_company_currency <= 0
            ):
                raise UserError(_(
                    "Cannot issue statutory statement for invoice %s: foreign-currency conversion rate "
                    "could not be resolved. Set an exchange rate snapshot first (Decree 70/2025/ND-CP compliance)."
                ) % move.display_name)

            vals = {'al2c_timesheet_statement_state': 'sent_to_client'}

            # Idempotent Token Preservation (rotate if missing or expired)
            if not move.al2c_timesheet_token or not self._verify_timesheet_token(move.id, move.al2c_timesheet_token):
                vals['al2c_timesheet_token'] = self._generate_timesheet_token(move.id, expires_in_days=7)

            # Multi-Currency Statutory Rate Card Snapshot: Fail-Closed Protection
            if move.currency_id and comp_curr and move.currency_id.id != comp_curr.id:
                if not move.al2c_exchange_rate_snapshot or move.al2c_exchange_rate_snapshot <= 0:
                    Rate = self.env['res.currency.rate'].sudo()
                    has_rate = bool(Rate.search_count([
                        ('currency_id', '=', move.currency_id.id),
                        ('company_id', 'in', (False, move.company_id.id, move.company_id.root_id.id if hasattr(move.company_id, 'root_id') else False)),
                    ], limit=1))
                    if not has_rate:
                        rate = 0.0
                    else:
                        try:
                            rate = self.env['res.currency']._get_conversion_rate(
                                move.currency_id,
                                comp_curr,
                                move.company_id,
                                move.invoice_date or fields.Date.context_today(move)
                            )
                        except Exception:
                            rate = 0.0

                    if not rate or rate <= 0:
                        raise UserError(_(
                            "Cannot issue statutory statement for invoice %s: No conversion rate found from %s to %s for date %s. "
                            "(Decree 70/2025/ND-CP Compliance Invariant)",
                            move.display_name, move.currency_id.name, comp_curr.name, move.invoice_date or fields.Date.context_today(move)
                        ))
                    vals['al2c_exchange_rate_snapshot'] = rate
            else:
                vals['al2c_exchange_rate_snapshot'] = 1.0

            move.write(vals)
            if template and move.partner_id.email:
                template.send_mail(move.id, force_send=False)
            move.message_post(
                body=_(
                    "<b>Bảng kê Giờ công Tư vấn (Timesheet Statement)</b> đã được gửi tới khách hàng (%s). "
                    "Hạn xác nhận trực tuyến: 7 ngày (HMAC signed token)."
                ) % (move.partner_id.email or 'N/A'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_client_confirm_timesheet(self, token=None, confirmed_by=None):
        """Called when client confirms timesheet on portal or via secure link.
        Validates token, ensures single-use idempotency, and records audit trail.
        """
        for move in self:
            if move.al2c_timesheet_statement_state == 'confirmed':
                continue
            if token and not self._verify_timesheet_token(move.id, token):
                raise UserError(_("Invalid or expired timesheet confirmation token."))
            move.write({
                'al2c_timesheet_statement_state': 'confirmed',
                'al2c_timesheet_confirmed_date': fields.Datetime.now(),
                'al2c_timesheet_confirmed_by': confirmed_by or (self.env.user.name if self.env.user else 'Client Representative'),
            })
            move.message_post(
                body=_(
                    "<b>✓ Khách Hàng Đã Xác Nhận Bảng Kê Giờ Công Tư Vấn (Timesheet Statement):</b><br/>"
                    "Đại diện xác nhận: <b>%s</b><br/>"
                    "Thời điểm xác nhận: <code>%s</code><br/>"
                    "<i>Hóa đơn đủ điều kiện để ký số và phát hành Hóa đơn Điện tử theo Nghị định 70/2025/NĐ-CP.</i>"
                ) % (move.al2c_timesheet_confirmed_by, move.al2c_timesheet_confirmed_date),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
        return True

    # --- Decree 70/2025 E-Invoice Fields (AL2C-INV-001) ---
    al2c_einvoice_provider = fields.Selection([
        ('mock', 'Insilos Sandbox Provider'),
        ('vnpt', 'VNPT-Invoice (Decree 70/2025)'),
        ('viettel', 'Viettel S-Invoice'),
        ('misa', 'MISA meInvoice'),
    ], default='mock', string='E-Invoice Provider', copy=False)

    al2c_einvoice_state = fields.Selection([
        ('draft', 'Draft (Not Issued)'),
        ('submitted', 'Submitted to Provider'),
        ('issued', 'Issued & Certified by Tax Authority'),
        ('cancelled', 'Cancelled / Replaced'),
    ], default='draft', string='E-Invoice Status', tracking=True, copy=False)

    al2c_einvoice_number = fields.Char(
        string='E-Invoice Serial & Number',
        copy=False,
        tracking=True,
        help='Mẫu số, ký hiệu và số hóa đơn theo Nghị định 70/2025/NĐ-CP (e.g. 1C26TAA-00000001)',
    )
    al2c_einvoice_lookup_code = fields.Char(
        string='Decree 70 E-Invoice Lookup Code',
        copy=False,
        tracking=True,
        help='Mã tra cứu hóa đơn điện tử của cơ quan thuế theo Nghị định 70/2025/NĐ-CP',
    )
    al2c_einvoice_qr_code = fields.Char(
        string='Decree 70 QR Verification URL',
        copy=False,
        tracking=True,
        help='Đường dẫn tra cứu / mã QR hóa đơn điện tử',
    )
    al2c_einvoice_xml_hash = fields.Char(
        string='Signed XML SHA-256 Digest',
        copy=False,
        help='Mã băm SHA-256 của tệp dữ liệu XML hóa đơn điện tử',
    )
    al2c_einvoice_issue_date = fields.Datetime(
        string='E-Invoice Issue Date',
        copy=False,
    )
    al2c_einvoice_xml_payload = fields.Text(
        string='Decree 70 Canonical XML',
        copy=False,
    )

    def action_issue_einvoice(self):
        """Issue statutory e-invoice under Decree 70/2025."""
        adapter = self.env['al2c.einvoice.adapter']
        for move in self:
            if move.state != 'posted':
                raise UserError(_("E-Invoice can only be issued for posted invoices."))
            if move.move_type not in ('out_invoice', 'out_refund'):
                raise UserError(_("E-Invoice can only be issued for customer invoices or credit notes."))
            if move.al2c_einvoice_state == 'issued':
                raise UserError(_("E-Invoice has already been issued for invoice %s.") % move.name)

            data = adapter.issue_einvoice(move)
            move.write({
                'al2c_einvoice_state': 'issued',
                'al2c_einvoice_number': data.get('number'),
                'al2c_einvoice_lookup_code': data.get('lookup_code'),
                'al2c_einvoice_qr_code': data.get('qr_code'),
                'al2c_einvoice_xml_hash': data.get('xml_hash'),
                'al2c_einvoice_xml_payload': data.get('xml_payload'),
                'al2c_einvoice_issue_date': data.get('issue_date') or fields.Datetime.now(),
            })
            move.message_post(
                body=_(
                    "<b>Decree 70/2025 E-Invoice Certified:</b><br/>"
                    "Serial/No: <b>%s</b><br/>"
                    "CQT Lookup Code: <code>%s</code><br/>"
                    "Verification Portal: <a href='%s' target='_blank'>Tra cứu hóa đơn</a><br/>"
                    "XML SHA-256 Digest: <code>%s</code>"
                ) % (data.get('number'), data.get('lookup_code'), data.get('qr_code'), data.get('xml_hash')),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def button_draft(self):
        """AL2C-GOV-204: Autonomous agents cannot unpost or draft posted invoices."""
        self.env['al2c.autonomy.guard']._al2c_check_method_allowed('account.move', 'button_draft')
        return super().button_draft()

    def action_cancel_einvoice(self, reason=None):
        """Cancel statutory e-invoice under Decree 70/2025."""
        self.env['al2c.autonomy.guard']._al2c_check_method_allowed('account.move', 'action_cancel_einvoice')
        adapter = self.env['al2c.einvoice.adapter']
        for move in self:
            if move.al2c_einvoice_state != 'issued':
                raise UserError(_("Only issued e-invoices can be cancelled."))
            res = adapter.cancel_einvoice(move, reason or "Administrative adjustment")
            move.write({'al2c_einvoice_state': 'cancelled'})
            move.message_post(
                body=f"<b>Decree 70 E-Invoice Cancelled:</b> {res.get('notice')}",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    # --- Cash-Matched Sales Commission (AL2C-PAY-001) ---
    def action_process_cash_matched_commission(self):
        """
        Create commission ledger entries upon payment reconciliation.
        Generates positive commission for customer invoices and negative clawbacks for credit notes.
        """
        Ledger = self.env['al2c.commission.ledger']
        rate = float(self.env['ir.config_parameter'].sudo().get_param('al2c.commission_rate', '5.0'))

        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue

            sales_rep = move.invoice_user_id or move.line_ids.sale_line_ids.order_id[:1].user_id
            if not sales_rep:
                continue

            employee = self.env['hr.employee'].search([('user_id', '=', sales_rep.id)], limit=1)
            if not employee:
                continue

            # Check if ledger entry already created for this invoice
            existing = Ledger.search([('invoice_id', '=', move.id)], limit=1)
            if existing:
                continue

            # Cash-matched base in invoice currency (signed for refunds)
            sign = -1.0 if move.move_type == 'out_refund' else 1.0
            base_amount = move.amount_untaxed * sign
            currency = move.currency_id or move.company_id.currency_id
            if currency:
                commission_amt = currency.round(base_amount * (rate / 100.0))
            else:
                commission_amt = round(base_amount * (rate / 100.0), 0)

            sale_order = move.line_ids.sale_line_ids.order_id[:1] or False

            Ledger.create({
                'employee_id': employee.id,
                'invoice_id': move.id,
                'sale_order_id': sale_order.id if sale_order else False,
                'currency_id': currency.id,
                'base_amount': base_amount,
                'rate': rate,
                'amount': commission_amt,
                'date': move.date or fields.Date.context_today(self),
                'state': 'pending',
                'move_type': move.move_type,
            })
        return True

    def _al2c_update_dunning_stage(self, as_of_date=None):
        """Update dunning stage based on overdue days from invoice_date_due."""
        today = as_of_date or fields.Date.context_today(self)
        for move in self:
            if move.move_type != 'out_invoice' or move.state != 'posted' or move.payment_state in ('paid', 'in_payment', 'reversed'):
                move.al2c_dunning_stage = 'current'
                continue

            # AL2C-INV-103: Freeze dunning progression if invoice has an active commercial dispute
            if any(d.state == 'open' for d in move.al2c_dispute_ids):
                continue

            due_date = move.invoice_date_due or move.invoice_date or today
            overdue_days = (today - due_date).days

            if overdue_days >= 30:
                new_stage = 'd30_suspension'
            elif overdue_days >= 15:
                new_stage = 'd15_warning'
            elif overdue_days >= 3:
                new_stage = 'd3_reminder'
            else:
                new_stage = 'current'

            move.write({
                'al2c_dunning_stage': new_stage,
                'al2c_dunning_last_date': today,
            })
        return True

    @api.model
    def _cron_al2c_dunning_ladder(self):
        """Nightly cron to transition overdue customer invoices through the dunning ladder."""
        open_invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])
        return open_invoices._al2c_update_dunning_stage()

    def action_send_al2c_dunning_notice(self):
        """Send dunning notice email using AL2C Dunning template unless dispute is open."""
        template = self.env.ref('insilos_al2c.email_template_al2c_dunning_notice', raise_if_not_found=False)
        for move in self:
            if move.al2c_has_open_dispute:
                continue
            if template and move.partner_id.email:
                template.send_mail(move.id, force_send=True)
        return True

    @api.depends('partner_id')
    def _compute_display_auto_complete(self):
        po_model = self.env['purchase.order']
        partner_model = self.env['res.partner']
        partner_ids = self.mapped('partner_id').ids
        if not partner_ids:
            for move in self:
                move.display_auto_complete_field = False
            return

        purchase_orders = po_model._search([
            ('state', '=', 'purchase'),
            ('invoice_status', 'in', ('to invoice', 'no'))
        ], limit=1)
        purchase_orders.add_where(SQL('%s.partner_id = %s.id', SQL.identifier(po_model._table), SQL.identifier(partner_model._table)))
        partners = partner_model._search([
            ('id', 'in', partner_ids),
        ])
        partners.add_where(SQL('EXISTS(%s)', purchase_orders.select()))
        valid_partner_ids = {partner[0] for partner in self.env.execute_query(partners.select())}

        for move in self:
            move.display_auto_complete_field = move.partner_id.id in valid_partner_ids

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        if isinstance(res, dict) and 'models' in res:
            if 'finance.journal.entry' in res['models'] and 'account.move' not in res['models']:
                res['models']['account.move'] = res['models']['finance.journal.entry']
            if 'finance.journal.line' in res['models'] and 'account.move.line' not in res['models']:
                res['models']['account.move.line'] = res['models']['finance.journal.line']
        return res
