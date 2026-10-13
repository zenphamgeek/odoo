# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Al2cMojoUsageLedger(models.Model):
    _name = 'al2c.mojo.usage.ledger'
    _description = 'Mojo AI Consumption & Token Usage Ledger'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Usage Reference',
        default=lambda self: self.env['ir.sequence'].next_by_code('al2c.mojo.usage.ledger') or 'USAGE',
        copy=False,
    )
    idempotency_key = fields.Char(
        string='Idempotency Key',
        required=True,
        index=True,
        help='Unique token/request identifier from Mojo pod or gateway to ensure strictly once processing.',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
        ondelete='cascade',
    )
    subscription_id = fields.Many2one(
        'sale.order',
        string='Subscription Order',
        domain=[('is_subscription', '=', True)],
        index=True,
    )
    meter_type = fields.Selection([
        ('tokens', 'LLM Inference Tokens'),
        ('api_requests', 'API Calls'),
        ('gpu_seconds', 'GPU Compute Seconds'),
    ], string='Meter Type', required=True, default='tokens')

    quantity = fields.Float(
        string='Quantity Consumed',
        required=True,
        digits=(16, 2),
    )
    unit_price = fields.Monetary(
        string='Unit Rate (VND)',
        currency_field='currency_id',
        default=0.0,
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    date = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('applied', 'Applied to Balance'),
        ('billed', 'Invoiced as Overage'),
    ], string='Status', default='applied', required=True)

    _idempotency_key_uniq = models.Constraint(
        'unique(idempotency_key)',
        'Idempotency key must be unique to prevent duplicate billing!',
    )
    _sql_constraints = [
        ('idempotency_key_uniq', 'unique(idempotency_key)', 'Idempotency key must be unique to prevent duplicate billing!'),
    ]

    def _register_hook(self):
        super()._register_hook()
        self._assert_idempotency_constraint()

    @api.model
    def _assert_idempotency_constraint(self):
        """Fail-closed boot check: ensures unique constraint physically exists in PostgreSQL."""
        self.env.cr.execute("""
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'al2c_mojo_usage_ledger'
        """)
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute("""
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'al2c_mojo_usage_ledger'::regclass
              AND conname LIKE '%idempotency_key_uniq%'
              AND contype = 'u'
        """)
        if not self.env.cr.fetchone():
            raise ValidationError(
                "FAIL-CLOSED: idempotency uniqueness constraint missing on al2c_mojo_usage_ledger; "
                "refusing to operate ledger without duplicate-billing guard."
            )

    @api.constrains('quantity')
    def _check_quantity_non_negative(self):
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError(_("Negative consumption quantity is strictly prohibited."))

    @api.depends('quantity', 'unit_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.quantity * rec.unit_price

    @api.model
    def record_usage(self, partner_id, quantity, meter_type='tokens', idempotency_key=None, subscription_id=None, unit_price=0.0):
        """
        Ingest a usage measurement from Mojo app runtime.
        Idempotent: Re-submitting the same idempotency_key returns the existing record without double-decrementing.
        Negative quantities are rejected.
        Burns down partner's prepaid token balance and triggers 80% burn-down alert when threshold is crossed.
        """
        if quantity < 0:
            raise UserError(_("Negative consumption quantity rejected."))

        if not idempotency_key:
            idempotency_key = f"MTR-{fields.Datetime.now().timestamp()}-{partner_id}-{quantity}"

        # Idempotency check
        existing = self.search([('idempotency_key', '=', idempotency_key)], limit=1)
        if existing:
            return existing

        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists():
            raise UserError(_("Customer partner does not exist."))

        vals = {
            'partner_id': partner.id,
            'subscription_id': subscription_id,
            'meter_type': meter_type,
            'quantity': quantity,
            'unit_price': unit_price,
            'idempotency_key': idempotency_key,
            'state': 'applied',
        }
        usage_rec = self.create(vals)

        # Decrement prepaid token balance
        if meter_type == 'tokens':
            partner.sudo().write({
                'al2c_mojo_token_balance': partner.al2c_mojo_token_balance - quantity,
            })

            # Check 80% prepaid burn-down alert
            if partner.al2c_mojo_token_total_purchased > 0:
                consumed = partner.al2c_mojo_token_total_purchased - partner.al2c_mojo_token_balance
                burn_pct = consumed / partner.al2c_mojo_token_total_purchased
                if burn_pct >= 0.80 and not partner.al2c_mojo_alert_80_sent:
                    partner.sudo().write({'al2c_mojo_alert_80_sent': True})
                    partner.message_post(
                        body=_("⚠️ <b>Mojo Prepaid Token Burn-Down Alert:</b> Customer has consumed %.1f%% of prepaid token pack.<br/>"
                               "• <b>Total Purchased:</b> %s tokens<br/>"
                               "• <b>Remaining Balance:</b> %s tokens<br/>"
                               "Autonomous top-up proposal generated for account manager.") % (
                            burn_pct * 100.0,
                            f"{partner.al2c_mojo_token_total_purchased:,.0f}",
                            f"{partner.al2c_mojo_token_balance:,.0f}",
                        )
                    )
                    # Schedule top-up activity
                    partner.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_("Mojo Token Pack 80% Burn-Down: Send Top-Up Proposal"),
                        note=_("Customer token balance is at %.1f%% burn-down. Proactively offer MOJO-TOKENS pack expansion.") % (burn_pct * 100.0),
                        user_id=partner.user_id.id if partner.user_id else self.env.user.id,
                    )

        return usage_rec


class ResPartner(models.Model):
    _inherit = 'res.partner'

    al2c_mojo_token_balance = fields.Float(
        string='Remaining Mojo Tokens',
        default=0.0,
        tracking=True,
        help='Available balance of prepaid Mojo LLM inference tokens.',
    )
    al2c_mojo_token_total_purchased = fields.Float(
        string='Total Mojo Tokens Purchased',
        default=0.0,
        tracking=True,
    )
    al2c_mojo_alert_80_sent = fields.Boolean(
        string='80% Usage Alert Dispatched',
        default=False,
        tracking=True,
    )

    def action_topup_tokens(self, tokens_qty):
        """Top up partner token credits and reset alert flag."""
        self.ensure_one()
        if tokens_qty <= 0:
            raise UserError(_("Top-up token quantity must be strictly positive."))
        self.write({
            'al2c_mojo_token_balance': self.al2c_mojo_token_balance + tokens_qty,
            'al2c_mojo_token_total_purchased': self.al2c_mojo_token_total_purchased + tokens_qty,
            'al2c_mojo_alert_80_sent': False,
        })
        self.message_post(
            body=_("Mojo Token Credit Applied: Added %s tokens. New balance: %s tokens.") % (
                f"{tokens_qty:,.0f}", f"{self.al2c_mojo_token_balance:,.0f}"
            )
        )
        return True
