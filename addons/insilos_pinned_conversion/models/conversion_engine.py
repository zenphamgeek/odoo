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

    class api:
        @staticmethod
        def model(f):
            return f

    def _(msg):
        return msg

_logger = logging.getLogger(__name__)


class ConversionEngine(models.AbstractModel):
    _name = 'insilos.conversion.engine'
    _description = 'Insilos DERS-ZLRR Conversion Engine'

    @api.model
    def _revalue_contract_invoices(self, company, currency_id, pinned_rate):
        """
        Revalue contract invoices for a specific company and currency using pinned rate.
        Enforces Decree 70 Statutory Barrier:
        - Only draft invoices (state == 'draft')
        - EDI state must be in [False, 'to_send']
        - Never touches posted or EDI-signed invoices
        - Checks inv.company_id.id == company.id, else raises AccessError.
        """
        company_env = self.with_company(company)
        cid = currency_id.id if hasattr(currency_id, 'id') else currency_id
        target_company_id = company.id if hasattr(company, 'id') else company

        domain = [
            ('company_id', '=', target_company_id),
            ('currency_id', '=', cid),
            ('state', '=', 'draft'),
        ]
        invoices = company_env.env['account.move'].search(domain)
        revalued_entries = []

        for inv in invoices:
            inv_company_id = inv.company_id.id if hasattr(inv.company_id, 'id') else inv.company_id
            if inv.company_id.id != company.id:
                raise AccessError(
                    _("Decree 70 Multi-Company Boundary Violation: Invoice %s company %s mismatch with %s")
                    % (inv.id, inv_company_id, target_company_id)
                )

            edi_state = getattr(inv, 'edi_state', False)
            if not (inv.state == 'draft' and edi_state in [False, 'to_send']):
                raise ValidationError(
                    _("Decree 70 Statutory Barrier: Revaluation prohibited for non-draft or EDI-signed invoice %s (state=%s, edi_state=%s)")
                    % (inv.id, inv.state, edi_state)
                )

            entry = company_env._apply_revaluation_entry(inv, pinned_rate)
            revalued_entries.append((inv.id, entry))

        return revalued_entries

    def _apply_revaluation_entry(self, invoice, pinned_rate):
        """
        Applies a revaluation entry for an individual invoice.
        Enforces Decree 70 statutory barrier and multi-company boundary.
        """
        current_company = self.env.company
        inv_company_id = invoice.company_id.id if hasattr(invoice.company_id, 'id') else invoice.company_id
        curr_company_id = current_company.id if hasattr(current_company, 'id') else current_company

        if inv_company_id != curr_company_id:
            raise AccessError(
                _("Decree 70 Multi-Company Boundary Violation: Invoice %s company mismatch (%s != %s)")
                % (invoice.id, inv_company_id, curr_company_id)
            )

        edi_state = getattr(invoice, 'edi_state', False)
        if not (invoice.state == 'draft' and edi_state in [False, 'to_send']):
            raise ValidationError(
                _("Decree 70 Statutory Barrier: Cannot revalue posted or EDI-signed invoice %s (state=%s, edi_state=%s)")
                % (invoice.id, invoice.state, edi_state)
            )

        base_amount = getattr(invoice, 'amount_total', 0.0) or 0.0
        gain_loss_amount = round(base_amount * (pinned_rate - 1.0), 4)

        journal_helper = self.env['insilos.conversion.journal.helper'].with_company(current_company)
        return journal_helper.create_exchange_adjustment_entry(invoice, gain_loss_amount)

    def _execute_company_pipeline(self, company):
        """Standard hook for cron execution pipeline."""
        return True
