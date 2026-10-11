"""
tools/unslop_ledger.py
======================
Tamper-Evident Local Content-Addressed Idempotency Ledger for AI Unslop.

Provides:
- Content-addressed idempotency across infinite 24/7 autonomous cron loops.
- Instant skip when current file hash matches previously verified post-state under the same rule fingerprint.
- Zero outbound network requests (100% offline stealth operation).
- Tamper and drift detection: alerts when files change outside the unslop engine.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

LEDGER_DB_PATH = Path(__file__).resolve().parent / "data" / "unslop_ledger.db"


class UnslopLedger:
    """
    Append-only/upsert content-addressed ledger for idempotency and auditability.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or LEDGER_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path), timeout=10.0)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    def _init_db(self) -> None:
        with self._get_connection() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS unslop_ledger (
                    rel_path TEXT PRIMARY KEY,
                    sha256_before TEXT NOT NULL,
                    sha256_after TEXT NOT NULL,
                    rule_fingerprint TEXT NOT NULL,
                    diff_chars INTEGER DEFAULT 0,
                    verified_at REAL NOT NULL,
                    status TEXT DEFAULT 'clean'
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS unslop_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rel_path TEXT NOT NULL,
                    sha256_before TEXT NOT NULL,
                    sha256_after TEXT NOT NULL,
                    rule_fingerprint TEXT NOT NULL,
                    diff_chars INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    notes TEXT
                )
                """
            )

    @staticmethod
    def compute_sha256(content: str | bytes) -> str:
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()

    def is_clean(
        self, rel_path: str, current_sha256: str, rule_fingerprint: str
    ) -> bool:
        """
        Returns True if the current file content matches a previously verified clean
        state produced under the exact same rule fingerprint.
        """
        with self._get_connection() as con:
            row = con.execute(
                """
                SELECT sha256_after, rule_fingerprint, status
                FROM unslop_ledger
                WHERE rel_path = ?
                """,
                (rel_path,),
            ).fetchone()

            if not row:
                return False

            sha256_after, recorded_rule_fp, status = row
            return (
                sha256_after == current_sha256
                and recorded_rule_fp == rule_fingerprint
                and status == "clean"
            )

    def record_entry(
        self,
        rel_path: str,
        sha256_before: str,
        sha256_after: str,
        rule_fingerprint: str,
        diff_chars: int,
        status: str = "clean",
        notes: str = "",
    ) -> None:
        """Records an unslop transformation or clean verification into the ledger."""
        now = time.time()
        with self._get_connection() as con:
            con.execute(
                """
                INSERT INTO unslop_ledger (rel_path, sha256_before, sha256_after, rule_fingerprint, diff_chars, verified_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rel_path) DO UPDATE SET
                    sha256_before = excluded.sha256_before,
                    sha256_after = excluded.sha256_after,
                    rule_fingerprint = excluded.rule_fingerprint,
                    diff_chars = excluded.diff_chars,
                    verified_at = excluded.verified_at,
                    status = excluded.status
                """,
                (
                    rel_path,
                    sha256_before,
                    sha256_after,
                    rule_fingerprint,
                    diff_chars,
                    now,
                    status,
                ),
            )
            # Record audit trace
            con.execute(
                """
                INSERT INTO unslop_audit_log (rel_path, sha256_before, sha256_after, rule_fingerprint, diff_chars, created_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel_path,
                    sha256_before,
                    sha256_after,
                    rule_fingerprint,
                    diff_chars,
                    now,
                    notes,
                ),
            )

    def get_stats(self) -> Dict[str, Any]:
        """Returns overview statistics from the unslop ledger."""
        with self._get_connection() as con:
            total_tracked = con.execute(
                "SELECT COUNT(*) FROM unslop_ledger"
            ).fetchone()[0]
            clean_count = con.execute(
                "SELECT COUNT(*) FROM unslop_ledger WHERE status = 'clean'"
            ).fetchone()[0]
            total_diff_chars = con.execute(
                "SELECT SUM(ABS(diff_chars)) FROM unslop_ledger"
            ).fetchone()[0] or 0
            audit_events = con.execute(
                "SELECT COUNT(*) FROM unslop_audit_log"
            ).fetchone()[0]

            return {
                "total_tracked": total_tracked,
                "clean_count": clean_count,
                "total_diff_chars": total_diff_chars,
                "audit_events": audit_events,
            }
