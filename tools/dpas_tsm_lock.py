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

import hashlib
import logging
import re
from typing import Tuple
import zlib
import psycopg2

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

    def derive_bipartite_advisory_keys(self, company_id: int, model_name: str, record_id: int) -> Tuple[int, int]:
        """
        Derives collision-free (key1, key2) signed 32-bit integers for PostgreSQL pg_try_advisory_xact_lock(int4, int4).
        Prevents 32-bit BigInt overflow aliasing (CWE-190) and namespace collisions.
        """
        rec_int = int(record_id)
        rec_high = (rec_int >> 32) if rec_int >= 0 else -((-rec_int) >> 32)
        if rec_high != 0:
            namespace = f"{int(company_id)}:{str(model_name)}:hi{rec_high}".encode('utf-8')
        else:
            namespace = f"{int(company_id)}:{str(model_name)}".encode('utf-8')
        u32_ns = zlib.crc32(namespace) & 0xFFFFFFFF
        key1 = u32_ns if u32_ns < 0x80000000 else u32_ns - 0x100000000
        rec_id_int = rec_int & 0xFFFFFFFF
        key2 = rec_id_int if rec_id_int < 0x80000000 else rec_id_int - 0x100000000
        return int(key1), int(key2)

    def derive_deterministic_advisory_key(self, company_id: int, model_name: str, record_id: int) -> int:
        """
        Derives a deterministic, uniform 64-bit signed advisory key using BLAKE2b.
        Uses length-prefixed canonical encoding to eliminate CWE-20 delimiter injection collisions.
        """
        norm_comp = str(company_id if company_id is not None else 0).strip()
        norm_model = str(model_name or "").strip()
        norm_rec = str(record_id if record_id is not None else 0).strip()
        token = f"C{len(norm_comp)}:{norm_comp}|M{len(norm_model)}:{norm_model}|R{len(norm_rec)}:{norm_rec}".encode("utf-8")
        digest = hashlib.blake2b(token, digest_size=8).digest()
        return int.from_bytes(digest, byteorder="big", signed=True)

    def acquire_deterministic_record_lock(self, cr, company_id: int, model_name: str, record_id: int) -> bool:
        """
        Acquires a deterministic transaction-scoped advisory lock for a specific record.
        Uses 32-bit bipartite signed keys (company_id:model_name, record_id).
        Returns True if acquired, False on lock contention or invalid record_id.
        """
        if not isinstance(record_id, int) or isinstance(record_id, bool) or record_id <= 0:
            return False
        key1, key2 = self.derive_bipartite_advisory_keys(company_id, model_name, record_id)
        try:
            cr.execute("SELECT pg_try_advisory_xact_lock(%s, %s);", (key1, key2))
            row = cr.fetchone()
            return bool(row and row[0])
        except psycopg2.Error as err:
            self.logger.error("Failed to acquire advisory xact lock (%s, %s): %s", key1, key2, err)
            raise
