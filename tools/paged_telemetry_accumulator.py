#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paged Telemetry Accumulator & Scan Block Table.
Transplanted from vLLM PagedAttention / Block Table architecture for multi-repository telemetry.
Enables O(1) page-level copy-on-write, deterministic chunk hashing, and atomic index commits.
"""

import hashlib
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

PAGE_SIZE_MODULES = 32
ENABLE_PAGED_SCAN_BUFFER = os.getenv("ENABLE_PAGED_SCAN_BUFFER", "1") == "1"


class PagedScanBlockTable:
    """
    Paged Scan Block Table for Multi-Repository Telemetry.
    Chunks modules into fixed-size pages (PAGE_SIZE_MODULES=32),
    hashes each page using 8-byte Blake2b digest,
    writes pages atomically via tempfile + os.replace,
    and commits a manifest block index table atomically.
    """

    PAGE_SIZE_MODULES = PAGE_SIZE_MODULES
    ENABLE_PAGED_SCAN_BUFFER = ENABLE_PAGED_SCAN_BUFFER

    def __init__(self, cache_dir: str = ".scan_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.index_file = os.path.join(self.cache_dir, "block_index.json")

    def _compute_page_hash(self, page_data: List[Dict[str, Any]]) -> str:
        serialized = json.dumps(page_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.blake2b(serialized, digest_size=8).hexdigest()

    def _atomic_write_json(self, target_path: str, data: Any):
        dir_name = os.path.dirname(target_path)
        os.makedirs(dir_name, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(data, tf, indent=2, sort_keys=True)
            temp_name = tf.name
        os.replace(temp_name, target_path)

    def write_module_blocks(self, modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Chunks incoming modules into fixed page sizes (PAGE_SIZE_MODULES),
        computes blake2b 8-byte digest for page_hash, performs atomic write via
        tempfile + os.replace, and atomically commits the block index table.
        """
        page_records = []
        total_modules = len(modules)

        if total_modules == 0:
            total_pages = 0
        else:
            total_pages = (total_modules + self.PAGE_SIZE_MODULES - 1) // self.PAGE_SIZE_MODULES

        for page_idx in range(total_pages):
            start_idx = page_idx * self.PAGE_SIZE_MODULES
            end_idx = min(start_idx + self.PAGE_SIZE_MODULES, total_modules)
            page_data = modules[start_idx:end_idx]

            page_hash = self._compute_page_hash(page_data)
            block_filename = f"block_{page_idx:04d}_{page_hash}.json"
            block_path = os.path.join(self.cache_dir, block_filename)

            # Atomic write via tempfile + os.replace
            self._atomic_write_json(block_path, page_data)

            page_records.append({
                "page_index": page_idx,
                "page_hash": page_hash,
                "block_file": block_filename,
                "module_count": len(page_data),
            })

        block_index_table = {
            "version": "1.0",
            "page_size": self.PAGE_SIZE_MODULES,
            "total_modules": total_modules,
            "total_pages": len(page_records),
            "pages": page_records,
        }

        # Atomic commit of block index table
        self._atomic_write_json(self.index_file, block_index_table)
        return block_index_table

    def read_module_blocks(self) -> List[Dict[str, Any]]:
        """
        Reconstructs or reads back modules from persisted page blocks
        according to the block index table.
        """
        if not os.path.exists(self.index_file):
            return []

        with open(self.index_file, "r", encoding="utf-8") as f:
            index_table = json.load(f)

        modules: List[Dict[str, Any]] = []
        for page_info in index_table.get("pages", []):
            block_file = page_info.get("block_file")
            block_path = os.path.join(self.cache_dir, block_file)
            if os.path.exists(block_path):
                with open(block_path, "r", encoding="utf-8") as f:
                    page_modules = json.load(f)
                    modules.extend(page_modules)

        return modules
