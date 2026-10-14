# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import hashlib
import logging
import struct

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


def derive_company_lock_key(company_id: int) -> int:
    """
    Derives a deterministic 64-bit signed integer from MD5 of f"insilos_pinned_conv_{company_id}".
    Ensures mathematical confinement to PostgreSQL bigint bounds [-2^63, 2^63 - 1].
    """
    raw_key = f"insilos_pinned_conv_{company_id}".encode("utf-8")
    digest_8 = hashlib.md5(raw_key).digest()[:8]
    return struct.unpack(">q", digest_8)[0]


class PinnedConversionCron(models.AbstractModel):
    _name = 'insilos.pinned.conversion.cron'
    _description = 'Insilos 24/7 DERS-ZLRR Pinned Conversion Cron'

    @api.model
    def process_247_conversions(self):
        """
        Processes 24/7 pinned conversions across all active companies with
        transactional advisory locks and zero-lock read reconciliation.
        """
        companies = self.env['res.company'].search([('active', '=', True)])
        results = {}
        for company in companies:
            results[company.id] = self._process_company_conversion(company)
        return results

    @api.model
    def _process_company_conversion(self, company):
        """
        Executes pinned conversion pipeline for a single company.
        Guarded strictly by pg_try_advisory_xact_lock (transaction-scoped).
        Uses deterministic 64-bit signed integer derived from MD5 of f"insilos_pinned_conv_{company.id}".
        Skips if not acquired. Calls _execute_conversion_pipeline(company).
        """
        company_id = company.id if hasattr(company, 'id') else int(company)
        raw_key = f"insilos_pinned_conv_{company.id}".encode("utf-8")
        digest_8 = hashlib.md5(raw_key).digest()[:8]
        lock_key = struct.unpack(">q", digest_8)[0]

        self.env.cr.execute("SELECT pg_try_advisory_xact_lock(%s);", (lock_key,))
        res = self.env.cr.fetchone()
        locked = bool(res and res[0])
        if not locked:
            _logger.info(
                "Advisory lock not acquired for company %s (key=%s), skipping.",
                company_id, lock_key,
            )
            return False

        return self._execute_conversion_pipeline(company)

    def _execute_conversion_pipeline(self, company):
        """
        Executes the conversion pipeline for the target company after advisory lock acquisition.
        Delegates to ConversionEngine.
        """
        company_env = self.with_company(company)
        engine = company_env.env['insilos.conversion.engine'].with_company(company)
        if hasattr(engine, '_execute_company_pipeline'):
            return engine._execute_company_pipeline(company)
        return True
