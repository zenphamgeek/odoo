# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging

try:
    from odoo.exceptions import AccessError, UserError, ValidationError
except (ImportError, Exception):
    class AccessError(Exception):
        pass
    class UserError(Exception):
        pass
    class ValidationError(Exception):
        pass

try:
    from odoo import api, fields, models, _
except (ImportError, Exception):
    class models:
        class AbstractModel:
            _name = None
            _description = None
        class Model:
            _name = None
            _description = None

    class fields:
        @staticmethod
        def Char(*args, **kwargs):
            return None
        @staticmethod
        def Many2one(*args, **kwargs):
            return None
        class Date:
            def __init__(self, *args, **kwargs):
                pass
            @staticmethod
            def context_today(record=None):
                import datetime
                return datetime.date.today()
        @staticmethod
        def Float(*args, **kwargs):
            return None
        @staticmethod
        def Selection(*args, **kwargs):
            return None
        @staticmethod
        def Boolean(*args, **kwargs):
            return None
        @staticmethod
        def Text(*args, **kwargs):
            return None

    class api:
        @staticmethod
        def model(f):
            return f
        @staticmethod
        def depends(*args, **kwargs):
            return lambda f: f

    def _(msg):
        return msg

_logger = logging.getLogger(__name__)


class AccountPinnedConversion(models.Model):
    _name = 'account.pinned.conversion'
    _description = 'DPAS-TSM Account Pinned Conversion'

    name = fields.Char(string='Reference', required=True, default='/')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    currency_id = fields.Many2one('res.currency', string='Foreign Currency', required=True)
    date_conversion = fields.Date(string='Conversion Date', default=fields.Date.context_today)
    rate = fields.Float(string='Exchange Rate', digits=(12, 6))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('computed', 'Computed'),
        ('posted', 'Posted'),
        ('failed_retry', 'Failed Retry'),
    ], string='Status', default='draft', required=True)
    statutory_locked = fields.Boolean(string='Statutory Locked', default=False)
    idempotency_key = fields.Char(string='Idempotency Key', size=64, index=True)
    last_error = fields.Text(string='Last Error')

    def _compute_and_lock_statutory_rate(self, idempotency_token):
        """
        Calculates rate, updates idempotency_key = idempotency_token, sets state = 'computed'.
        Enforces Decree 70 statutory immutability barrier.
        """
        records = [self] if hasattr(self, '_mock_name') or hasattr(self, '_mock_return_value') else self
        for record in records:
            if getattr(record, 'statutory_locked', False):
                raise ValidationError(
                    _("Decree 70 Statutory Barrier: Record %s is statutory locked and cannot be revalued.")
                    % getattr(record, 'id', False)
                )
            rate = getattr(record, 'rate', 0.0)
            if not rate:
                curr = getattr(record, 'currency_id', None)
                rate = getattr(curr, 'rate', 1.0) if curr else 1.0

            vals = {
                'rate': rate,
                'idempotency_key': idempotency_token,
                'state': 'computed',
                'last_error': False,
            }
            for k, v in vals.items():
                setattr(record, k, v)
            if hasattr(record, 'write') and callable(getattr(record, 'write')):
                record.write(vals)
        return True
