# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


def calculate_vn_2026_insurance(gross_salary):
    """
    Calculate statutory mandatory employee insurance under 2026 Vietnam regulations:
    - Base Salary (Mức lương cơ sở): 2,340,000 VND
    - Cap for BHXH (Social Insurance) & BHYT (Health Insurance): 20 x 2,340,000 = 46,800,000 VND
    - Cap for BHTN (Unemployment Insurance): 20 x 4,960,000 (Region 1 min wage) = 99,200,000 VND
    - Rates: BHXH 8%, BHYT 1.5%, BHTN 1%
    """
    cap_social_health = 46_800_000.0
    cap_unemployment = 99_200_000.0

    base_sh = min(gross_salary, cap_social_health)
    base_unemp = min(gross_salary, cap_unemployment)

    bhxh = round(base_sh * 0.08, 0)
    bhyt = round(base_sh * 0.015, 0)
    bhtn = round(base_unemp * 0.01, 0)
    total_ins = bhxh + bhyt + bhtn

    return {
        'bhxh': bhxh,
        'bhyt': bhyt,
        'bhtn': bhtn,
        'total_insurance': total_ins,
    }


def calculate_vn_2026_pit(taxable_income):
    """
    Calculate progressive Personal Income Tax (PIT) under Vietnam's 2026 5-bracket schedule:
    Bracket 1: <= 10,000,000 VND -> 5%
    Bracket 2: 10,000,001 - 30,000,000 VND -> 10% (0.5M + excess * 10%)
    Bracket 3: 30,000,001 - 60,000,000 VND -> 20% (2.5M + excess * 20%)
    Bracket 4: 60,000,001 - 100,000,000 VND -> 30% (8.5M + excess * 30%)
    Bracket 5: > 100,000,000 VND -> 35% (20.5M + excess * 35%)
    """
    if taxable_income <= 0:
        return 0.0

    tntt = float(taxable_income)
    if tntt <= 10_000_000:
        return round(tntt * 0.05, 0)
    elif tntt <= 30_000_000:
        return round(500_000 + (tntt - 10_000_000) * 0.10, 0)
    elif tntt <= 60_000_000:
        return round(2_500_000 + (tntt - 30_000_000) * 0.20, 0)
    elif tntt <= 100_000_000:
        return round(8_500_000 + (tntt - 60_000_000) * 0.30, 0)
    else:
        return round(20_500_000 + (tntt - 100_000_000) * 0.35, 0)


class Al2cCommissionLedger(models.Model):
    _name = 'al2c.commission.ledger'
    _description = 'Cash-Matched Sales Commission Ledger'
    _order = 'date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Sales Representative',
        required=True,
        index=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Customer Invoice / Refund',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Origin Sales Order',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    base_amount = fields.Monetary(
        string='Untaxed Collected Base',
        required=True,
        help='Signed untaxed amount collected (negative for credit note refunds)',
    )
    rate = fields.Float(
        string='Commission Rate (%)',
        default=5.0,
    )
    amount = fields.Monetary(
        string='Commission Amount',
        required=True,
        help='Calculated commission amount (negative on clawback)',
    )
    date = fields.Date(
        string='Collection Date',
        default=fields.Date.context_today,
        required=True,
    )
    move_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Credit Note (Clawback)'),
    ], string='Invoice Type', default='out_invoice', required=True)

    state = fields.Selection([
        ('pending', 'Pending Payslip Sync'),
        ('included', 'Included in Payslip'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True, index=True)

    payslip_id = fields.Many2one(
        'hr.payslip',
        string='Settled Payslip',
        copy=False,
    )


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    al2c_commission_ledger_ids = fields.One2many(
        'al2c.commission.ledger',
        'payslip_id',
        string='Settled Commission Entries',
    )

    def action_sync_al2c_commission(self):
        """
        Pull pending cash-matched commission entries and clawbacks into payslip inputs.
        """
        Ledger = self.env['al2c.commission.ledger']
        InputType = self.env['hr.payslip.input.type']

        comm_type = InputType.search([('code', '=', 'COMMISSION')], limit=1)
        if not comm_type:
            # Create input type if missing
            country = self.env.company.country_id or self.env.ref('base.vn', raise_if_not_found=False)
            comm_type = InputType.create({
                'name': 'Cash-Matched Sales Commission',
                'code': 'COMMISSION',
                'country_id': country.id if country else False,
            })

        for payslip in self:
            if payslip.state not in ('draft', 'verify'):
                continue

            pending_entries = Ledger.search([
                ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'pending'),
                ('date', '<=', payslip.date_to or fields.Date.today()),
            ])

            if not pending_entries:
                continue

            total_commission = sum(pending_entries.mapped('amount'))
            
            # Find or create input line
            input_line = payslip.input_line_ids.filtered(lambda l: l.code == 'COMMISSION')
            input_name = f"Cash-Matched Commission ({len(pending_entries)} invoices/refunds)"
            if input_line:
                input_line.write({
                    'amount': total_commission,
                    'name': input_name,
                })
            else:
                payslip.write({
                    'input_line_ids': [(0, 0, {
                        'input_type_id': comm_type.id,
                        'name': input_name,
                        'amount': total_commission,
                    })]
                })

            pending_entries.write({
                'state': 'included',
                'payslip_id': payslip.id,
            })

            payslip.message_post(
                body=f"<b>AL2C Commission Synced:</b> {total_commission:,.0f} VND ({len(pending_entries)} transactions).",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return True

    def _get_al2c_vn_insurance(self, gross_amount):
        """Helper for Vietnamese salary rules to compute mandatory employee insurance."""
        ins = calculate_vn_2026_insurance(gross_amount)
        return ins['total_insurance']

    def _get_al2c_vn_pit(self, gross_amount, insurance_amount, deduction_amount):
        """Helper for Vietnamese salary rules to compute 2026 5-bracket PIT."""
        taxable = gross_amount - abs(insurance_amount) - abs(deduction_amount)
        return calculate_vn_2026_pit(taxable)

    def action_payslip_done(self):
        """AL2C-GOV-204 / AL2C-PAY-003: Human Disbursement Boundary."""
        self.env['al2c.autonomy.guard']._al2c_check_method_allowed('hr.payslip', 'action_payslip_done')
        return super().action_payslip_done()

