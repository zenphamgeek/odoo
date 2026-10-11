# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


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

    def action_cancel_einvoice(self, reason=None):
        """Cancel statutory e-invoice under Decree 70/2025."""
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

            # Cash-matched base: untaxed signed amount
            base_amount = move.amount_untaxed_signed
            commission_amt = round(base_amount * (rate / 100.0), 0)

            sale_order = move.line_ids.sale_line_ids.order_id[:1] or False

            Ledger.create({
                'employee_id': employee.id,
                'invoice_id': move.id,
                'sale_order_id': sale_order.id if sale_order else False,
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
