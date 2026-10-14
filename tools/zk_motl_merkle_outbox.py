#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/zk_motl_merkle_outbox.py
==============================
ZK-MOTL Cryptographic Merkle Outbox with Item-Level Quarantine (Patch 18.3).
Provides:
- RFC 8785 Canonical JSON hashing
- Cryptographic chained outbox ledger (seq, payload, prev_hash, record_hash)
- Item-level quarantine on Byzantine bit-flip / tamper detection
- Non-aborting batch verification and binary Merkle root attestation
"""

import hashlib
import json
from typing import Any, Dict, List, Tuple


def canonical_dumps(payload: dict) -> bytes:
    """
    Serializes a dictionary payload according to RFC 8785 Canonical JSON rules
    (sorted keys, compact delimiters, UTF-8 encoding).
    """
    return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')


def compute_record_hash(prev_hash: str, payload: dict) -> str:
    """
    Computes cryptographic SHA-256 digest binding prev_hash and canonical payload.
    """
    return hashlib.sha256(prev_hash.encode('utf-8') + canonical_dumps(payload)).hexdigest()


def compute_merkle_root(records_or_hashes: list) -> str:
    """
    Computes binary Merkle tree root from a list of records or hash strings.
    If the list is empty, returns sha256("") digest.
    """
    if not records_or_hashes:
        return hashlib.sha256(b"").hexdigest()

    current_level = [
        item["record_hash"] if isinstance(item, dict) and "record_hash" in item else item
        for item in records_or_hashes
    ]

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            next_level.append(hashlib.sha256((left + right).encode('utf-8')).hexdigest())
        current_level = next_level

    return current_level[0]


class ZKMOTLOutboxManager:
    """
    Cryptographic Outbox Manager with Item-Level Quarantine and Merkle Attestation.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, genesis_hash: str = GENESIS_HASH):
        self.genesis_hash = genesis_hash
        self.last_hash = genesis_hash
        self.seq = 0
        self.records: List[Dict[str, Any]] = []
        self.committed_records: List[Dict[str, Any]] = []
        self.quarantined_records: List[Dict[str, Any]] = []

    def append_record(self, payload: dict) -> dict:
        """
        Appends a record to the local outbox sequence, computing cryptographic record_hash.
        """
        self.seq += 1
        prev_hash = self.last_hash
        rec_hash = compute_record_hash(prev_hash, payload)
        record = {
            "seq": self.seq,
            "payload": payload,
            "prev_hash": prev_hash,
            "record_hash": rec_hash,
        }
        self.last_hash = rec_hash
        self.records.append(record)
        return record

    def verify_and_commit_batch(self, records: list) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Verifies each record's integrity by recomputing record_hash against prev_hash & payload.
        Corrupted/tampered records are isolated to quarantined list at item-level granularity.
        Valid peer records continue and get committed without aborting the entire batch.
        Returns:
            (committed_records, quarantined_records)
        """
        committed = []
        quarantined = []

        for record in records:
            prev_h = record.get("prev_hash", "")
            payload = record.get("payload", {})
            claimed_hash = record.get("record_hash", "")

            expected_hash = compute_record_hash(prev_h, payload)
            if expected_hash != claimed_hash:
                quarantined.append(record)
            else:
                committed.append(record)
                self.committed_records.append(record)

        self.quarantined_records.extend(quarantined)
        return (committed, quarantined)

    def get_merkle_root(self, records: list = None) -> str:
        """
        Returns binary Merkle root for the given records or self.committed_records.
        """
        target = records if records is not None else self.committed_records
        return compute_merkle_root(target)

    @property
    def merkle_root(self) -> str:
        return self.get_merkle_root()

    compute_merkle_root = staticmethod(compute_merkle_root)
