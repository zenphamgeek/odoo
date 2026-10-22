"""
tools/report_gateway/outbox_processor.py
================================================================================
Safe Advisory Lock Manager & Outbox Queue Guard (SEC-02-REV & SEC-03-REV)
================================================================================
Eliminates CWE-662 (Lock Exhaustion / Connection Starvation) and CWE-362 (Race Conditions).
Uses transactional advisory locks with strict timeout guards and SKIP LOCKED concurrency.
================================================================================
"""
import zlib
import logging
from contextlib import contextmanager
from typing import List, Tuple, Any

_logger = logging.getLogger(__name__)


def compute_advisory_lock_id(db_name: str, task_key: str) -> int:
    """
    Generates deterministic signed 64-bit bigint for PostgreSQL advisory locks.
    PostgreSQL bigint is signed [-2^63, 2^63 - 1].
    """
    crc_db = zlib.crc32(db_name.encode('utf-8')) & 0xFFFFFFFF
    crc_task = zlib.crc32(task_key.encode('utf-8')) & 0xFFFFFFFF
    combined = (crc_db << 32) | crc_task
    if combined >= (1 << 63):
        combined -= (1 << 64)
    return combined


@contextmanager
def acquire_report_lock(cr, lock_id: int, timeout_ms: int = 1500):
    """
    Acquires scoped transaction-level advisory lock with strict timeout guards.
    Eliminates CWE-662 (Lock Exhaustion) and connection leakage.
    """
    # Set localized statement & lock timeouts strictly within transaction scope
    cr.execute("SET LOCAL lock_timeout = %s;", (f"{timeout_ms}ms",))
    cr.execute("SET LOCAL statement_timeout = '8000ms';")
    try:
        cr.execute("SELECT pg_try_advisory_xact_lock(%s);", (lock_id,))
        row = cr.fetchone()
        acquired = row[0] if row else False
        if not acquired:
            raise BlockingIOError(f"Advisory lock {lock_id} currently held by another worker.")
        yield
    finally:
        # Transaction-level locks release automatically on COMMIT/ROLLBACK
        pass


def fetch_pending_outbox_tasks(cr, limit: int = 25) -> List[Tuple[Any, ...]]:
    """
    Selects pending reporting tasks using SKIP LOCKED concurrency.
    Eliminates race conditions and redundant rendering jobs (CWE-362).
    """
    query = """
        SELECT id, report_model, payload
        FROM insilos_report_outbox
        WHERE status = 'PENDING'
        ORDER BY priority DESC, id ASC
        LIMIT %s
        FOR UPDATE SKIP LOCKED;
    """
    cr.execute(query, (limit,))
    return cr.fetchall()
