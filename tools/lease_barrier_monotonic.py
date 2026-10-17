#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch 40 (`SEC-02`): Monotonic Fencing Leases with Cryptographic Lamport Witness (`MFL-CLW`).
Replaces wall-clock `time.time()` lease checks with `time.monotonic()` and monotonic fencing tokens
to prevent split-brain savepoint corruption under NTP clock skew (`CWE-367` / `CWE-662`).
"""
import hashlib
import threading
import time
from typing import Dict, Optional, Tuple


class MonotonicFencingTokenError(RuntimeError):
    """Raised when a stale or expired fencing token attempts to mutate state or commit a savepoint."""


class MonotonicLeaseSavepointBarrier:
    """Enforces lease validity using `time.monotonic()` and strictly increasing fencing tokens (`MFL-CLW`)."""

    def __init__(self, lease_duration_sec: float = 30.0):
        self.lease_duration_sec = float(lease_duration_sec)
        self._lock = threading.Lock()
        self._current_fencing_token: int = 0
        self._lease_expiry_monotonic: float = 0.0
        self._active_owner: Optional[str] = None
        self._lamport_witness_chain: str = hashlib.sha256(b"INSILOS_MFL_CLW_GENESIS").hexdigest()

    def acquire_lease(self, owner_id: str) -> Tuple[int, float]:
        owner = str(owner_id or "").strip()
        if not owner:
            raise MonotonicFencingTokenError("owner_id must be a non-empty string.")
        with self._lock:
            now_mono = time.monotonic()
            if self._active_owner is not None and now_mono < self._lease_expiry_monotonic:
                if self._active_owner != owner:
                    raise MonotonicFencingTokenError(
                        f"Lease currently held by {self._active_owner} until {self._lease_expiry_monotonic:.3f}"
                    )
            self._current_fencing_token += 1
            self._active_owner = owner
            self._lease_expiry_monotonic = now_mono + self.lease_duration_sec
            frame = f"{self._lamport_witness_chain}|{self._current_fencing_token}|{owner}".encode("utf-8")
            self._lamport_witness_chain = hashlib.sha256(frame).hexdigest()
            return self._current_fencing_token, self._lease_expiry_monotonic

    def validate_action(self, owner_id: str, fencing_token: int) -> bool:
        with self._lock:
            now_mono = time.monotonic()
            if int(fencing_token) != self._current_fencing_token:
                raise MonotonicFencingTokenError(
                    f"Stale fencing token {fencing_token} < current {self._current_fencing_token}. Split-brain prevented."
                )
            if self._active_owner != str(owner_id or "").strip():
                raise MonotonicFencingTokenError(
                    f"Invalid lease owner {owner_id} (expected {self._active_owner})."
                )
            if now_mono >= self._lease_expiry_monotonic:
                raise MonotonicFencingTokenError(
                    f"Lease expired at monotonic {self._lease_expiry_monotonic:.3f} (now: {now_mono:.3f})."
                )
            return True

    def release_lease(self, owner_id: str, fencing_token: int) -> None:
        with self._lock:
            if self._active_owner == str(owner_id or "").strip() and int(fencing_token) == self._current_fencing_token:
                self._active_owner = None
                self._lease_expiry_monotonic = 0.0

    @property
    def lamport_witness_hash(self) -> str:
        return self._lamport_witness_chain
