#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/dism_advisory_lock.py
===========================
Hardened Transaction-Scoped Dual-Key Advisory Lock Manager (Patch 16.1 / 17).
Provides:
- Deterministic dual-partition key derivation using HMAC-BLAKE2s and 31-bit tenant masks.
- Transaction-scoped PostgreSQL advisory locks (pg_try_advisory_xact_lock).
- Contention handling with fail-closed BlockingIOError or safe boolean yield.
"""

import hashlib
import hmac
from contextlib import contextmanager
from typing import Tuple

GLOBAL_ADVISORY_SALT = b"insilos_genesis_v20_dpas_salt"


def derive_dual_partition_keys(tenant_id: int, resource_name: str) -> Tuple[int, int]:
    """
    Derives a dual-key pair (key1, key2) for PostgreSQL advisory locking:
    - key1: Positive 31-bit integer tenant partition space (tenant_id & 0x7FFFFFFF).
    - key2: Signed 32-bit integer HMAC-BLAKE2s digest of resource_name.
    """
    if not isinstance(tenant_id, int) or isinstance(tenant_id, bool) or tenant_id <= 0:
        raise ValueError(f"Invalid tenant_id for lock partitioning: {tenant_id}")
    if not isinstance(resource_name, str) or not resource_name:
        raise ValueError(f"Invalid resource_name for lock partitioning: {resource_name}")

    key1 = tenant_id & 0x7FFFFFFF
    digest = hmac.new(GLOBAL_ADVISORY_SALT, resource_name.encode("utf-8"), hashlib.blake2s).digest()
    key2 = int.from_bytes(digest[:4], byteorder="big", signed=True)
    return (key1, key2)


@contextmanager
def transaction_advisory_guard(cr, tenant_id: int, resource_name: str, raise_on_busy: bool = True):
    """
    Transaction-scoped advisory lock context manager.
    Acquires pg_try_advisory_xact_lock(key1, key2).
    If busy:
        - raises BlockingIOError if raise_on_busy=True
        - yields False if raise_on_busy=False
    Locks are automatically released on transaction commit/abort by PostgreSQL.
    """
    key1, key2 = derive_dual_partition_keys(tenant_id, resource_name)
    cr.execute("SELECT pg_try_advisory_xact_lock(%s, %s);", (key1, key2))
    row = cr.fetchone()
    acquired = bool(row and row[0])
    if not acquired:
        if raise_on_busy:
            raise BlockingIOError(f"Resource '{resource_name}' locked by concurrent transaction in tenant {tenant_id}")
        yield False
        return
    try:
        yield True
    finally:
        pass
