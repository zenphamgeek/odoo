#!/usr/bin/env python3
"""
tools/execute_fleet_unslop_views.py
===================================
Full Codebase PDCA Unslop Engine for Insilos Enterprise & Vertical Industry Views.

Architectural Invariants & Hardening:
- Content-Addressed Idempotency: Uses UnslopLedger to skip verified clean files instantly.
- CWE-611 / CWE-776 Protection: Uses shared tools.safe_xml (multi-encoding denylist + lxml/defusedxml).
- CWE-1333 ReDoS Mitigation: Linear horizontal spacing [ \\t]* and bounded character sets {1,2000}.
- CWE-628 Type Guard: Strict isinstance check on clean_file_content.
- F1/F3 Structural Topology Invariant: Guarantees element tags and attribute keys remain 100% identical.
- F2 Two-Phase Batch Transaction: Verifies 100% of target files before committing any atomic writes.
"""

import hashlib
import logging
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.atomic_io import atomic_write_text
from tools.safe_xml import assert_markup_preserved, parse_xml_safe
from tools.unslop_ledger import UnslopLedger

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("unslop_views")

# Static rule fingerprint for content-addressed idempotency
RULE_FINGERPRINT = "unslop_v2.5_safe_xml_bounds_2000"

TARGET_FILES = [
    "enterprise/insilos_website/views/home.xml",
    "enterprise/insilos_website/views/industries.xml",
    "enterprise/insilos_website/views/platform_solutions.xml",
    "enterprise/insilos_website/views/industry_verticals.xml",
    "enterprise/insilos_website/views/resources_about_demo.xml",
    "enterprise/insilos_website/views/innoria_homepage.xml",
    "enterprise/insilos_website/views/innoria_pages.xml",
    "enterprise/insilos_website/views/interactive_3d.xml",
    "enterprise/insilos_website/views/sandbox.xml",
    "enterprise/insilos_website/views/snippets.xml",
    "enterprise/insilos_website/views/snippets_3d.xml",
    "enterprise/insilos_website/views/snippets_cctv.xml",
    "enterprise/insilos_website/views/snippets_cinematic.xml",
    "enterprise/insilos_website/views/trust_compliance.xml",
    "enterprise/insilos_website/views/brochure.xml",
    "enterprise/insilos_website/views/dossiers.xml",
    "enterprise/insilos_website/views/showcase_landing.xml",
    "enterprise/insilos_website/views/website_menu.xml",
    "enterprise/insilos_website/views/website_templates.xml",
    "enterprise/insilos_industry_showcase/views/templates.xml",
]


def clean_file_content(text: str) -> str:
    """
    Purges em-dashes, robotic slashes, and AI tells while preserving markup structure.
    Enforces strict ReDoS bounds and type-safety guards.
    """
    if not isinstance(text, str):
        raise TypeError(f"clean_file_content expects str, got {type(text).__name__}")

    # 1. Clean titles: "<t t-set="additional_title">... — ...</t>"
    def replace_title_emdash(m):
        full = m.group(0)
        return full.replace(" — ", " | ")

    text = re.sub(
        r'<t t-set="additional_title">[^<]{1,2000}</t>',
        replace_title_emdash,
        text,
    )

    # 2. Clean template name attributes: 'name="... — ..."'
    def replace_name_emdash(m):
        full = m.group(0)
        return full.replace(" — ", " | ")

    text = re.sub(
        r'<template[^>]{1,2000}name="[^"]{1,2000}"',
        replace_name_emdash,
        text,
    )

    # 3. Clean specific numbered steps: "01 — Scope" -> "01. Scope"
    text = re.sub(r'(\d{2})[ \t]*—[ \t]*', r'\1. ', text)

    # 4. Clean specific location pairs: "Hải Phòng — Vũng Tàu" -> "Hải Phòng - Vũng Tàu"
    text = re.sub(
        r'([A-Za-zÀ-ỹ0-9]+)[ \t]*—[ \t]*([A-Za-zÀ-ỹ0-9]+)',
        r'\1 - \2',
        text,
    )

    # 5. Clean remaining em-dashes: " — " -> ", " or ": "
    text = text.replace(" — ", ", ")
    text = text.replace("—", "-")

    # 6. Clean robotic slashes in token-comments: "// Insilos" -> "# Insilos"
    text = text.replace(
        '<span class="token-comment">//', '<span class="token-comment">#'
    )

    # 7. Clean specific AI copy phrases
    text = text.replace(
        "sai số không tính bằng phần trăm, nó được đo bằng",
        "sai số không tính bằng phần trăm, mà đo bằng",
    )

    # Correctness check: log if an em-dash somehow remains
    if "—" in text:
        logger.warning(
            "WARN-3: Residual em-dash detected after clean_file_content passes"
        )

    return text


def main() -> int:
    print("=== LAUNCHING FULL CODEBASE VIEW UNSLOP ENGINE ===")
    ledger = UnslopLedger()
    staged = []
    skipped_clean = 0

    # Phase 1: Read, check ledger idempotency, transform, validate structural equivalence.
    # NO WRITES OCCUR IN PHASE 1 (F2 Two-Phase Batch Transaction).
    for rel_path in TARGET_FILES:
        full_path = ROOT_DIR / rel_path
        if not full_path.exists():
            print(f"[!] Skipping missing file: {rel_path}")
            continue

        raw_text = full_path.read_text(encoding="utf-8")
        current_sha = UnslopLedger.compute_sha256(raw_text)

        # Content-addressed idempotency check: skip if already verified clean under current rules
        if ledger.is_clean(rel_path, current_sha, RULE_FINGERPRINT):
            skipped_clean += 1
            continue

        cleaned_text = clean_file_content(raw_text)

        if cleaned_text != raw_text:
            # F1 & F3: Encode to bytes so XML encoding declarations don't raise ValueError,
            # and verify tag/attribute topology is fully preserved.
            try:
                assert_markup_preserved(raw_text, cleaned_text, rel_path)
            except Exception as e:
                print(f"[✗] VALIDATION ERROR in {rel_path}: {e}")
                print("[✗] ABORTING: Zero files written. Working tree unchanged.")
                return 1

            post_sha = UnslopLedger.compute_sha256(cleaned_text)
            diff_chars = len(cleaned_text) - len(raw_text)
            staged.append(
                (full_path, rel_path, cleaned_text, current_sha, post_sha, diff_chars)
            )
        else:
            # File is already clean in source: record in ledger to accelerate future runs
            ledger.record_entry(
                rel_path=rel_path,
                sha256_before=current_sha,
                sha256_after=current_sha,
                rule_fingerprint=RULE_FINGERPRINT,
                diff_chars=0,
                status="clean",
                notes="Verified clean during scan",
            )
            print(f"[-] No slop found in {rel_path} (ledger recorded)")

    if skipped_clean > 0:
        print(
            f"[*] Content-Addressed Ledger: {skipped_clean} files skipped (verified clean under {RULE_FINGERPRINT})"
        )

    # Phase 2: All files passed Phase 1 validation. Execute atomic writes and update ledger.
    if staged:
        print(
            f"\n[*] Phase 1 passed (100% valid). Committing atomic writes for {len(staged)} files..."
        )
        for (
            full_path,
            rel_path,
            cleaned_text,
            sha_before,
            sha_after,
            diff_chars,
        ) in staged:
            atomic_write_text(full_path, cleaned_text, encoding="utf-8")
            ledger.record_entry(
                rel_path=rel_path,
                sha256_before=sha_before,
                sha256_after=sha_after,
                rule_fingerprint=RULE_FINGERPRINT,
                diff_chars=diff_chars,
                status="clean",
                notes="Automated unslop atomic write",
            )
            print(
                f"[✓] Unslop committed to {rel_path} (len diff: {diff_chars}, XML valid)"
            )
    else:
        print("\n[✓] All target files are already clean and verified.")

    stats = ledger.get_stats()
    print(
        f"\n[✓] Full unslop completed: {len(staged)} files updated, "
        f"{stats['clean_count']} total clean files tracked in tamper-evident ledger."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
