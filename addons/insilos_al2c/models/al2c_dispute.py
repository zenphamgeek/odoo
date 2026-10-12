# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

ALLOWED_DISPUTE_MANAGERS = ('account.group_account_manager', 'sales_team.group_sale_manager')


class Al2cDispute(models.Model):
    """
    Commercial Dispute Management (AL2C-INV-103):
    Records customer billing disagreements and pauses automated dunning ladder
    (preventing aggressive legal notices or suspension for disputed invoices).
    """
    _name = 'al2c.dispute'
    _description = 'AL2C Customer Invoice Dispute'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'al2c.autonomy.guard']
    _order = 'opened_date desc, id desc'

    name = fields.Char(string='Dispute Reference', required=True, default=lambda self: _('New Dispute'))
    invoice_id = fields.Many2one(
        'account.move',
        string='Disputed Invoice',
        required=True,
        domain="[('move_type', '=', 'out_invoice')]",
        ondelete='cascade',
        tracking=True,
    )
    partner_id = fields.Many2one('res.partner', related='invoice_id.partner_id', store=True, string='Customer')

    reason = fields.Selection([
        ('milestone_deliverable', 'Disputed Milestone Quality / Deliverable Gap'),
        ('timesheet_billing', 'Timesheet Hours Unapproved or Exceeded SOW'),
        ('rate_mismatch', 'Rate or Discount Discrepancy'),
        ('administrative', 'Tax ID / Legal Entity Administrative Mismatch'),
    ], string='Dispute Reason', required=True, tracking=True)

    disputed_amount = fields.Monetary(
        string='Disputed Amount',
        currency_field='company_currency',
        required=True,
        tracking=True,
    )
    company_currency = fields.Many2one('res.currency', related='invoice_id.currency_id')

    state = fields.Selection([
        ('open', 'Open (Dunning Frozen)'),
        ('resolved', 'Resolved (Dunning Resumed)'),
        ('credit_note_issued', 'Closed via Credit Note'),
        ('cancelled', 'Dispute Cancelled / Withdrawn'),
    ], string='Status', default='open', tracking=True)

    opened_date = fields.Date(string='Date Opened', default=fields.Date.context_today, tracking=True)
    resolution_date = fields.Date(string='Resolution Date', tracking=True)
    resolution_note = fields.Text(string='Resolution Agreement Notes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == _('New Dispute'):
                rec.name = f"DISP-{rec.invoice_id.name or 'INV'}-{rec.id}"
            rec.invoice_id.message_post(
                body=_(
                    "<b>Commercial Dispute Opened:</b> Ref <code>%s</code> for amount %s. "
                    "Autonomous dunning ladder is now frozen on this invoice."
                ) % (rec.name, rec.disputed_amount)
            )
        return records

    def _check_dispute_manager_rights(self):
        if self.env.su:
            return
        if self.env.user.has_group('insilos_al2c.group_al2c_agent'):
            raise AccessError(_("Autonomous agents are prohibited from resolving disputes or lifting dunning freezes (Segregation of Duties)."))
        is_billing_mgr = self.env.user.has_group('account.group_account_manager')
        is_sale_mgr = self.env.user.has_group('sales_team.group_sale_manager')
        if not (is_billing_mgr or is_sale_mgr):
            raise AccessError(_("Only Billing Managers (account.group_account_manager) or Sales Managers (sales_team.group_sale_manager) can resolve, cancel, or modify commercial disputes and lift dunning freezes."))

    def write(self, vals):
        sensitive_fields = {'state', 'resolution_date', 'resolution_note', 'disputed_amount', 'invoice_id'}
        if sensitive_fields.intersection(vals.keys()):
            self._check_dispute_manager_rights()
        return super().write(vals)

    def unlink(self):
        self._check_dispute_manager_rights()
        return super().unlink()

    def action_resolve_dispute(self, note=None):
        self._check_dispute_manager_rights()
        self._al2c_check_method_allowed('al2c.dispute', 'action_resolve_dispute')
        for rec in self:
            rec.write({
                'state': 'resolved',
                'resolution_date': fields.Date.context_today(self),
                'resolution_note': note or rec.resolution_note,
            })
            rec.invoice_id.message_post(
                body=_("<b>Commercial Dispute Resolved:</b> %s. Autonomous dunning operations resumed.") % (note or _("Agreed settlement reached"))
            )
        return True

    def action_cancel_dispute(self):
        self._check_dispute_manager_rights()
        self._al2c_check_method_allowed('al2c.dispute', 'action_cancel_dispute')
        for rec in self:
            rec.write({
                'state': 'cancelled',
                'resolution_date': fields.Date.context_today(self),
            })
            rec.invoice_id.message_post(
                body=_("<b>Commercial Dispute Cancelled / Withdrawn:</b> Dunning operations resumed.")
            )
        return True
