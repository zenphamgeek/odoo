# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import hashlib
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

LOCK_NAMESPACE = "insilos_dpas_tsm_pinned_conversion"


def generate_dual_key_lock_id(company_id: int) -> int:
    """Helper function to derive dual-key lock ID."""
    namespace_hash = int(hashlib.blake2b(LOCK_NAMESPACE.encode()).hexdigest()[:8], 16) & 0xFFFFFFFF
    return (namespace_hash << 32) | (company_id & 0xFFFFFFFF)


class PinnedConversionEngine(models.AbstractModel):
    _name = 'insilos.pinned.conversion.engine'
    _description = 'Insilos DPAS-TSM Pinned Conversion Engine'

    def _generate_dual_key_lock_id(self, company_id: int) -> int:
        """
        Derives a deterministic 64-bit dual-key lock ID from a 32-bit namespace hash
        and 32-bit company ID.
        """
        namespace_hash = int(hashlib.blake2b(LOCK_NAMESPACE.encode()).hexdigest()[:8], 16) & 0xFFFFFFFF
        return (namespace_hash << 32) | (company_id & 0xFFFFFFFF)

    @api.model
    def process_pinned_conversions_cron(self):
        """
        DPAS-TSM Slot-Sensing Transactional State Machine cron execution.
        Applies dual-key advisory lock (pg_try_advisory_xact_lock) and
        tenant boundary isolation with allowed_company_ids=[company.id].
        """
        companies = self.env['res.company'].search([('active', '=', True)])
        results = {}
        for company in companies:
            cid = company.id if hasattr(company, 'id') else int(company)
            lock_id = self._generate_dual_key_lock_id(cid)

            self.env.cr.execute("SELECT pg_try_advisory_xact_lock(%s);", (lock_id,))
            res = self.env.cr.fetchone()
            acquired = bool(res and res[0])
            if not acquired:
                _logger.info(
                    "Advisory lock not acquired for company %s (lock_id=%s), skipping.",
                    cid, lock_id,
                )
                results[cid] = {'status': 'locked', 'acquired': False}
                continue

            isolated_env = self.with_context(allowed_company_ids=[company.id])
            comp_res = isolated_env._process_company_conversions_isolated(company)
            results[cid] = {'status': 'processed', 'acquired': True, 'result': comp_res}
        return results

    def _process_company_conversions_isolated(self, company):
        """
        Processes pinned conversions for an isolated company:
        - Tenant boundary isolation: ensures records belong strictly to company.
        - Decree 70 Statutory Barrier: posted/cancel invoices set statutory_locked = True.
        - Prefect-inspired Blake2b idempotency token.
        - Airflow-inspired atomic savepoint per record.
        """
        cid = company.id if hasattr(company, 'id') else int(company)

        # Enforce tenant isolation on company context
        current_allowed = self.env.context.get('allowed_company_ids')
        if current_allowed is not None and cid not in current_allowed:
            raise AccessError(_("Tenant boundary violation: Company %s not in allowed_company_ids %s") % (cid, current_allowed))

        domain = [
            ('company_id', '=', cid),
            ('state', 'in', ['draft', 'failed_retry']),
            ('statutory_locked', '=', False),
        ]
        records = self.env['account.pinned.conversion'].search(domain)
        processed = []

        for record in records:
            rec_cid = record.company_id.id if hasattr(record.company_id, 'id') else record.company_id
            if rec_cid != cid:
                raise AccessError(
                    _("Tenant boundary violation: Record %s belongs to company %s, expected %s")
                    % (record.id, rec_cid, cid)
                )

            if getattr(record, 'statutory_locked', False):
                continue

            inv = getattr(record, 'invoice_id', None)
            if inv and getattr(inv, 'state', False) in ['posted', 'cancel']:
                statutory_locked = True
                statutory_vals = {'statutory_locked': statutory_locked}
                for k, v in statutory_vals.items():
                    setattr(record, k, v)
                if hasattr(record, 'write') and callable(getattr(record, 'write')):
                    record.write(statutory_vals)
                continue

            token_payload = f"dpas_{record.id}_{cid}_{getattr(record, 'date_conversion', '')}_{getattr(record, 'rate', '')}"
            idempotency_token = hashlib.blake2b(token_payload.encode(), digest_size=8).hexdigest()

            try:
                with self.env.cr.savepoint(): record._compute_and_lock_statutory_rate(idempotency_token)
                processed.append(record.id)
            except Exception as e:
                _logger.warning("Error computing statutory rate on conversion %s: %s", record.id, e)
                error_vals = {
                    'state': 'failed_retry',
                    'last_error': str(e),
                }
                for k, v in error_vals.items():
                    setattr(record, k, v)
                if hasattr(record, 'write') and callable(getattr(record, 'write')):
                    record.write(error_vals)

        return processed
