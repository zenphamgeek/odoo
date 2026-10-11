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

import contextlib
import fcntl
import hashlib
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

LEDGER_DB_PATH = Path(__file__).resolve().parent / "data" / "unslop_ledger.db"


class UnslopLedger:
    """
    Append-only/upsert content-addressed ledger for idempotency and auditability.
    Hardened with inter-process fcntl locks and strict 0o600 permissions.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or LEDGER_DB_PATH
        self.lock_path = self.db_path.with_suffix(".lock")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_secure_dir(self.db_path.parent)
        self._init_db()

    def _ensure_secure_dir(self, directory: Path) -> None:
        """Tighten directory permissions to 0o700 if owned by current user."""
        try:
            st = directory.stat()
            if st.st_uid == os.getuid() and (st.st_mode & 0o077):
                directory.chmod(st.st_mode & ~0o077)
        except OSError:
            pass

    def _ensure_secure_file(self, file_path: Path) -> None:
        """Ensure file permissions are 0o600 if owned by current user."""
        try:
            if file_path.exists():
                st = file_path.stat()
                if st.st_uid == os.getuid() and (st.st_mode & 0o077):
                    file_path.chmod(st.st_mode & ~0o077)
        except OSError:
            pass

    @contextlib.contextmanager
    def _flock_exclusive(self, timeout_sec: float = 30.0) -> Iterator[None]:
        """Inter-process exclusive lock using sidecar .lock file."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        self._ensure_secure_file(self.lock_path)
        start = time.time()
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (BlockingIOError, OSError):
                if time.time() - start > timeout_sec:
                    os.close(fd)
                    raise TimeoutError(
                        f"Could not acquire exclusive lock on {self.lock_path} within {timeout_sec}s"
                    )
                time.sleep(0.01)
        try:
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    @contextlib.contextmanager
    def _flock_shared(self, timeout_sec: float = 30.0) -> Iterator[None]:
        """Inter-process shared lock using sidecar .lock file."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        self._ensure_secure_file(self.lock_path)
        start = time.time()
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                break
            except (BlockingIOError, OSError):
                if time.time() - start > timeout_sec:
                    os.close(fd)
                    raise TimeoutError(
                        f"Could not acquire shared lock on {self.lock_path} within {timeout_sec}s"
                    )
                time.sleep(0.01)
        try:
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _get_connection(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path), timeout=30.0)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=30000")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    def _init_db(self) -> None:
        with self._flock_exclusive():
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
            self._ensure_secure_file(self.db_path)

    @staticmethod
    def compute_sha256(content: str | bytes) -> str:
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _validate_rel_path(rel_path: str) -> None:
        """
        Validates rel_path against path traversal (CWE-22) and NUL byte injection (CWE-626).
        """
        if not isinstance(rel_path, str):
            raise TypeError(f"rel_path must be a str, got {type(rel_path).__name__}")
        if "\x00" in rel_path:
            raise ValueError("rel_path contains forbidden NUL character (CWE-626)")
        p = Path(rel_path)
        if p.is_absolute() or rel_path.startswith("/") or rel_path.startswith("\\"):
            raise ValueError(f"rel_path must be relative, got: {rel_path}")
        if ".." in p.parts:
            raise ValueError(f"rel_path contains directory traversal ('..'): {rel_path}")

    @staticmethod
    def _validate_metadata(rule_fingerprint: str, status: str) -> None:
        """Validates metadata bounds and checks for NUL characters."""
        if not isinstance(rule_fingerprint, str) or not isinstance(status, str):
            raise TypeError("Metadata fields must be strings")
        if "\x00" in rule_fingerprint or "\x00" in status:
            raise ValueError("Metadata contains forbidden NUL character")
        if len(rule_fingerprint) > 256 or len(status) > 64:
            raise ValueError("Metadata field exceeds maximum allowed length")

    def is_clean(
        self, rel_path: str, current_sha256: str, rule_fingerprint: str
    ) -> bool:
        """
        Returns True if the current file content matches a previously verified clean
        state produced under the exact same rule fingerprint.
        """
        self._validate_rel_path(rel_path)
        self._validate_metadata(rule_fingerprint, "clean")
        with self._flock_shared():
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
        self._validate_rel_path(rel_path)
        self._validate_metadata(rule_fingerprint, status)
        now = time.time()
        with self._flock_exclusive():
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
            self._ensure_secure_file(self.db_path)

    def detect_anomalies(
        self, files: list[tuple[str, str]], *, enabled: bool = True
    ) -> list[tuple[str, Optional[str], str]]:
        """
        Negative-selection drift check (Immunology Frame).
        Flags tracked files whose current sha256 differs from the last recorded clean 'self' set.
        Args:
            files: list of (rel_path, current_sha256) tuples.
            enabled: boolean flag to toggle anomaly detection.
        Returns:
            list of (rel_path, last_clean_sha, current_sha256) for anomalous/drifted files.
        """
        if not enabled:
            return []
        anomalies = []
        with self._flock_shared():
            with self._get_connection() as con:
                for rel_path, current_sha in files:
                    self._validate_rel_path(rel_path)
                    row = con.execute(
                        "SELECT sha256_after, status FROM unslop_ledger WHERE rel_path = ?",
                        (rel_path,),
                    ).fetchone()
                    if row:
                        last_clean_sha, status = row
                        if status == "clean" and last_clean_sha != current_sha:
                            anomalies.append((rel_path, last_clean_sha, current_sha))
        return anomalies

    def get_stats(self) -> Dict[str, Any]:
        """Returns overview statistics from the unslop ledger."""
        with self._flock_shared():
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
