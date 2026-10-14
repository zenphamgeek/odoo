# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import hashlib
import logging

try:
    from odoo import models, exceptions, _
except Exception:
    class _MockModels:
        class AbstractModel:
            pass
    models = _MockModels()

    class _MockExceptions:
        class AccessError(Exception):
            pass
        class UserError(Exception):
            pass
        class ValidationError(Exception):
            pass
    exceptions = _MockExceptions()

    def _(msg):
        return msg

_logger = logging.getLogger(__name__)

ADVISORY_DOMAIN_SALT = 0x494E5349


class InsilosConversionGuard(models.AbstractModel):
    _name = 'insilos.conversion.guard'
    _description = 'Insilos Zero-Blocking Ephemeral Splay-Locking Guard'

    ADVISORY_DOMAIN_SALT = 0x494E5349

    def _compute_lock_keys(self, company_id, batch_slug):
        key1 = (ADVISORY_DOMAIN_SALT ^ int(company_id)) & 0x7FFFFFFF
        hash_digest = hashlib.sha256(batch_slug.encode('utf-8')).digest()
        key2 = int.from_bytes(hash_digest[:4], byteorder='big', signed=True)
        return key1, key2

    def _generate_deterministic_advisory_key(self, company_id: int, model_name: str, record_id: int) -> int:
        import binascii
        model_token = binascii.crc32(str(model_name).encode('utf-8')) & 0xFFFF
        bounded_company = int(company_id) & 0x7FFF
        bounded_record = int(record_id) & 0xFFFFFFFF
        packed_key = (bounded_company << 48) | (model_token << 32) | bounded_record
        return packed_key

    def _process_pinned_batch_safe(self, batch_records, max_batch_size=50):
        if len(batch_records) > max_batch_size:
            batch_records = batch_records[:max_batch_size]
        processed = []
        errors = []
        for record in batch_records:
            savepoint_name = f"flat_sp_{getattr(record, 'id', 'item')}"
            self.env.cr.execute(f"SAVEPOINT {savepoint_name};")
            try:
                record_company = getattr(record, 'company_id', None) or self.env.company
                if hasattr(record, 'with_company'):
                    scoped_rec = record.with_company(record_company)
                else:
                    scoped_rec = record
                res = scoped_rec._execute_conversion() if hasattr(scoped_rec, '_execute_conversion') else getattr(scoped_rec, 'id', None)
                self.env.cr.execute(f"RELEASE SAVEPOINT {savepoint_name};")
                processed.append(res)
            except (exceptions.UserError, exceptions.ValidationError) as e:
                self.env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
                errors.append((getattr(record, 'id', None), str(e)))
            except Exception as unhandled_err:
                self.env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
                errors.append((getattr(record, 'id', None), "CRITICAL_INTERNAL_ERROR"))
                break  # Circuit breaker: Halt batch on unexpected failure
        return processed, errors

    def execute_splayed_conversion(self, company_id, batch_slug, conversion_func, *args, **kwargs):
        key1, key2 = self._compute_lock_keys(company_id, batch_slug)
        cr = self.env.cr
        cr.execute("SELECT pg_try_advisory_xact_lock(%s, %s);", (key1, key2))
        res = cr.fetchone()
        acquired = res[0] if res else False
        if not acquired:
            return {
                'status': 'splayed',
                'reason': 'Partition locked by concurrent worker',
                'processed': 0,
            }
        with cr.savepoint():
            result = conversion_func(*args, **kwargs)
            return {
                'status': 'completed',
                'result': result,
            }

    def assert_decree70_statutory_invariant(self, move_id):
        if hasattr(move_id, 'state'):
            move = move_id
        elif hasattr(self, 'env') and self.env and 'account.move' in self.env:
            move = self.env['account.move'].browse(move_id)
        else:
            move = move_id

        if getattr(move, 'state', None) == 'posted':
            has_einvoice = bool(
                getattr(move, 'einvoice_status', False) or getattr(move, 'decree70_signed', False)
            )
            move_name = getattr(move, 'name', str(move_id))
            if has_einvoice:
                raise exceptions.AccessError(
                    _("Statutory Violation (Decree 70/2025/ND-CP): Account move %s is sealed as an official electronic invoice. Direct currency rate alteration is illegal. You must issue a formal Decree 70 Adjustment Invoice (Hóa đơn điều chỉnh).") % move_name
                )
            else:
                raise exceptions.UserError(
                    _("Statutory Invariant Error: Move %s is posted. Period currency revaluation must use Circular 200 differential ledger (Account 413).") % move_name
                )
        return True
