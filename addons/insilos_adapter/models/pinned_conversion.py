# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PinnedConversion(models.Model):
    _name = 'insilos.pinned.conversion'
    _description = 'Insilos Cellular Pinned Conversion'

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    rate = fields.Float(string='Pinned Rate', digits=(12, 6), required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('applied', 'Applied'),
        ('quarantined', 'Quarantined'),
    ], string='Status', default='draft')
    retry_count = fields.Integer(string='Retry Count', default=0)
    last_error = fields.Text(string='Quarantine Diagnostics')

    def _execute_conversion_cellular(self):
        self.ensure_one()
        if self.company_id != self.env.company:
            raise ValidationError(_("Tenant Security Violation: Execution company mismatch."))
        if self.rate <= 0.0:
            raise ValidationError(_("Invalid rate: Value must be strictly positive."))
        self.state = 'applied'

    def _quarantine_failure(self, error_message):
        """Crash-only actor quarantine: increments failure counter and marks DLQ status."""
        self.ensure_one()
        new_count = self.retry_count + 1
        state = 'quarantined' if new_count >= 3 else 'pending'
        self.write({
            'retry_count': new_count,
            'state': state,
            'last_error': error_message,
        })


class PinnedConversionRunner(models.AbstractModel):
    _name = 'insilos.pinned.conversion.runner'
    _description = 'Insilos Cellular Pinned Conversion Runner'

    @api.model
    def process_all_companies_cron(self):
        """Processes pending conversions across all active companies with cellular isolation."""
        companies = self.env['res.company'].search([('active', '=', True)])
        for company in companies:
            self._process_company_cellular(company.id)

    @api.model
    def _process_company_cellular(self, company_id):
        """Execute cellular conversion for a single company with transaction advisory lock and savepoint quarantine."""
        self.env.cr.execute("SELECT pg_try_advisory_xact_lock(hashtext('pinned_conv_' || %s::text));", (company_id,))
        res = self.env.cr.fetchone()
        locked = bool(res and res[0])
        if not locked:
            _logger.info("Advisory lock not acquired for company %s, skipping.", company_id)
            return False

        company_env = self.with_company(company_id)
        conversions = company_env.env['insilos.pinned.conversion'].search([
            ('company_id', '=', company_id),
            ('state', '=', 'pending'),
            ('retry_count', '<', 3),
        ], limit=200)

        for conversion in conversions:
            try:
                with self.env.cr.savepoint():
                    conversion._execute_conversion_cellular()
            except Exception as exc:
                _logger.warning("Failure converting record %s: %s", conversion.id, exc)
                conversion._quarantine_failure(str(exc))
        return True
