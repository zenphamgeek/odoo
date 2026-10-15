# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import hashlib
import logging
import struct
from typing import Tuple
import zlib

try:
    import psycopg2
    try:
        from psycopg2.errors import TransactionRollbackError
    except ImportError:
        try:
            from psycopg2.extensions import TransactionRollbackError
        except ImportError:
            class TransactionRollbackError(Exception):
                pass
except ImportError:
    class _MockPsycopg2:
        class OperationalError(Exception):
            pass
        class TransactionRollbackError(Exception):
            pass
    psycopg2 = _MockPsycopg2()
    TransactionRollbackError = psycopg2.TransactionRollbackError

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

    def _generate_bipartite_advisory_keys(self, company_id: int, model_name: str, record_id: int) -> Tuple[int, int]:
        c_norm = str(int(company_id) if company_id else 0)
        m_norm = str(model_name or '').strip()
        r_norm = str(int(record_id) if record_id else 0)
        token = f"{len(c_norm)}:{c_norm}|{len(m_norm)}:{m_norm}|{len(r_norm)}:{r_norm}".encode("utf-8")
        digest = hashlib.blake2b(token, digest_size=8).digest()
        key1, key2 = struct.unpack(">ii", digest)
        return int(key1), int(key2)

    def _generate_deterministic_advisory_key(self, company_id: int, model_name: str, record_id: int) -> int:
        try:
            norm_company = int(company_id) if company_id is not None else 0
        except (ValueError, TypeError):
            norm_company = str(company_id).strip()
        norm_model = str(model_name).strip()
        try:
            norm_record = int(record_id) if record_id is not None else 0
        except (ValueError, TypeError):
            norm_record = str(record_id).strip()
        c_str, m_str, r_str = str(norm_company), str(norm_model), str(norm_record)
        token = f"{len(c_str)}:{c_str}|{len(m_str)}:{m_str}|{len(r_str)}:{r_str}".encode("utf-8")
        digest = hashlib.blake2b(token, digest_size=8).digest()
        return int.from_bytes(digest, byteorder="big", signed=True)

    def _flush_orm_cache(self):
        """Safely invalidates the thread-local ORM cache across Odoo versions."""
        if hasattr(self.env, 'clear'):
            self.env.clear()
        if hasattr(self.env, 'invalidate_all'):
            self.env.invalidate_all()

    def _process_pinned_batch_safe(self, batch_records, max_batch_size=50):
        if len(batch_records) > max_batch_size:
            batch_records = batch_records[:max_batch_size]
        processed = []
        errors = []
        for record in batch_records:
            rec_id = getattr(record, 'id', None)
            if not isinstance(rec_id, int) or isinstance(rec_id, bool) or rec_id <= 0:
                errors.append((rec_id, "INVALID_RECORD_IDENTIFIER"))
                continue
            try:
                with self.env.cr.savepoint():
                    # Multi-tenant boundary check: ensure record_company is valid singleton or positive integer
                    raw_company = getattr(record, 'company_id', None)
                    if isinstance(raw_company, int) and raw_company > 0:
                        record_company = raw_company
                    elif raw_company and getattr(raw_company, 'id', False):
                        record_company = raw_company
                    else:
                        record_company = self.env.company

                    scoped_rec = record.with_company(record_company) if hasattr(record, 'with_company') else record
                    res = scoped_rec._execute_conversion() if hasattr(scoped_rec, '_execute_conversion') else getattr(scoped_rec, 'id', None)
                    processed.append(res)
            except (exceptions.UserError, exceptions.ValidationError) as e:
                if hasattr(self.env, 'clear'):
                    self.env.clear()
                if hasattr(self.env, 'invalidate_all'):
                    self.env.invalidate_all()
                _logger.warning("Validation failure in record %s: %s", rec_id, e)
                errors.append((rec_id, str(e)))
            except (psycopg2.OperationalError, getattr(getattr(psycopg2, 'extensions', None), 'TransactionRollbackError', TransactionRollbackError), TransactionRollbackError) as db_err:
                if hasattr(self.env, 'clear'):
                    self.env.clear()
                if hasattr(self.env, 'invalidate_all'):
                    self.env.invalidate_all()
                _logger.error("Database concurrency conflict on record %s: %s", rec_id, db_err)
                errors.append((rec_id, f"DB_CONCURRENCY_ABORT: {db_err}"))
                break  # Circuit breaker: Halt batch on DB deadlocks/serialization failures
            except Exception as unhandled_err:
                if hasattr(self.env, 'clear'):
                    self.env.clear()
                if hasattr(self.env, 'invalidate_all'):
                    self.env.invalidate_all()
                _logger.critical("Unexpected failure during conversion of record %s: %s", rec_id, unhandled_err)
                errors.append((rec_id, "CRITICAL_INTERNAL_ERROR"))
                break  # Circuit breaker: Halt batch on critical unexpected errors
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
