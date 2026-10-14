# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
import math

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


class ConversionJournalHelper(models.AbstractModel):
    _name = 'insilos.conversion.journal.helper'
    _description = 'Insilos Pinned Conversion Journal Helper'

    @api.model
    def create_exchange_adjustment_entry(self, invoice, gain_loss_amount, total_debit=None, total_credit=None):
        """
        Creates an exchange adjustment entry with double-entry balance check inside a savepoint.
        Uses savepoint f"pinned_conv_sp_{invoice.id}".
        Performs double-entry debit/credit balance check with math.isclose(total_debit, total_credit, abs_tol=1e-4).
        Raises ValidationError if unbalanced.
        On exception: evicts cache via self.env.invalidate_all() and raises.
        """
        try:
            with self.env.cr.savepoint(f"pinned_conv_sp_{invoice.id}"):
                if total_debit is None:
                    total_debit = abs(float(gain_loss_amount))
                if total_credit is None:
                    total_credit = abs(float(gain_loss_amount))

                if not math.isclose(total_debit, total_credit, abs_tol=1e-4):
                    raise ValidationError(
                        _("Double-entry unbalanced: total debit (%s) != total credit (%s)")
                        % (total_debit, total_credit)
                    )

                entry_vals = {
                    'invoice_id': invoice.id,
                    'company_id': invoice.company_id.id if hasattr(invoice.company_id, 'id') else invoice.company_id,
                    'gain_loss_amount': gain_loss_amount,
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'state': 'draft',
                }
                return entry_vals
        except Exception as exc:
            _logger.warning(
                "Exchange adjustment failure on invoice %s: %s; invalidating environment cache.",
                invoice.id, exc,
            )
            self.env.invalidate_all()
            raise
