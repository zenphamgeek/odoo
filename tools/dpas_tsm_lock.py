#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/dpas_tsm_lock.py
======================
Dual-Key CRC32 Advisory Lock & Savepoint Rollback Barrier (Patch 18.2).
Provides:
- 31-bit positive CRC32 dual-partition key derivation
- Transaction-scoped advisory lock with SAVEPOINT rollback barrier
"""

import logging
import zlib
from typing import Tuple

_logger = logging.getLogger(__name__)


class DPASTSMTransactionManager:
    """
    DPAS-TSM Transactional State Machine Manager with Dual-Key CRC32
    Advisory Locking and Savepoint Rollback Barrier.
    """

    SAVEPOINT_NAME = "sp_dism_trl_lock"

    def __init__(self):
        self.logger = _logger

    def derive_partition_keys(self, company_id: int, subsystem_key: str) -> Tuple[int, int]:
        """
        Derives dual 31-bit positive integer keys from company_id and subsystem_key.
        """
        key1 = zlib.crc32(f"insilos.tenant.{company_id}".encode("utf-8")) & 0x7FFFFFFF
        key2 = zlib.crc32(f"insilos.subsystem.{subsystem_key}".encode("utf-8")) & 0x7FFFFFFF
        return key1, key2

    def acquire_partitioned_lock(self, cr, company_id: int, subsystem_key: str) -> bool:
        """
        Acquires a dual-partition PostgreSQL transaction advisory lock with
        an isolated SAVEPOINT rollback barrier.
        Returns True if acquired, False on lock contention.
        Rolls back to savepoint on contention or failure.
        """
        key1, key2 = self.derive_partition_keys(company_id, subsystem_key)
        cr.execute(f"SAVEPOINT {self.SAVEPOINT_NAME}")
        try:
            cr.execute("SELECT pg_try_advisory_xact_lock(%s, %s)", (key1, key2))
            row = cr.fetchone()
            locked = bool(row and row[0])
            if not locked:
                cr.execute(f"ROLLBACK TO SAVEPOINT {self.SAVEPOINT_NAME}")
                return False
            cr.execute(f"RELEASE SAVEPOINT {self.SAVEPOINT_NAME}")
            return True
        except Exception:
            cr.execute(f"ROLLBACK TO SAVEPOINT {self.SAVEPOINT_NAME}")
            raise

    def derive_deterministic_advisory_key(self, company_id: int, model_name: str, record_id: int) -> int:
        """
        Derives deterministic 64-bit bipartite packed advisory key from company_id, model_name, and record_id.
        """
        import binascii
        model_token = binascii.crc32(str(model_name).encode('utf-8')) & 0xFFFF
        bounded_company = int(company_id) & 0x7FFF
        bounded_record = int(record_id) & 0xFFFFFFFF
        packed_key = (bounded_company << 48) | (model_token << 32) | bounded_record
        return packed_key

    def acquire_deterministic_record_lock(self, cr, company_id: int, model_name: str, record_id: int) -> bool:
        """
        Acquires a deterministic transaction-scoped advisory lock for a specific record
        with a flat SAVEPOINT rollback barrier.
        Returns True if acquired, False on lock contention.
        Rolls back to savepoint on contention or failure.
        """
        lock_key = self.derive_deterministic_advisory_key(company_id, model_name, record_id)
        savepoint_name = f"flat_sp_{record_id}"
        cr.execute(f"SAVEPOINT {savepoint_name};")
        try:
            cr.execute("SELECT pg_try_advisory_xact_lock(%s);", (lock_key,))
            row = cr.fetchone()
            locked = bool(row and row[0])
            if not locked:
                cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
                return False
            cr.execute(f"RELEASE SAVEPOINT {savepoint_name};")
            return True
        except Exception:
            cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
            raise
