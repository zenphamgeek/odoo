#!/usr/bin/env python3
"""
tools/execute_fleet_unslop_views.py
Full Codebase PDCA Unslop Engine for Insilos Enterprise & Vertical Industry Views.
Purges:
- All em-dashes (—) across titles, subtitles, headings, and comments.
- Robotic slashes (//) in comments and labels.
- AI clichés and tells in Vietnamese and English copy.
Guarantees:
- POSIX atomic writes (atomic_write_text).
- XML well-formedness validation on 100% of modified files.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.atomic_io import atomic_write_text

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
    # 1. Clean titles: "<t t-set="additional_title">... — ...</t>"
    def replace_title_emdash(m):
        full = m.group(0)
        return full.replace(" — ", " | ")

    text = re.sub(r'<t t-set="additional_title">[^<]+</t>', replace_title_emdash, text)

    # 2. Clean template name attributes: 'name="... — ..."'
    def replace_name_emdash(m):
        full = m.group(0)
        return full.replace(" — ", " | ")

    text = re.sub(r'<template[^>]+name="[^"]+"', replace_name_emdash, text)

    # 3. Clean specific numbered steps: "01 — Scope" -> "01. Scope"
    text = re.sub(r'(\d{2})\s*—\s*', r'\1. ', text)

    # 4. Clean specific location pairs: "Hải Phòng — Vũng Tàu" -> "Hải Phòng - Vũng Tàu"
    text = re.sub(r'([A-Za-zÀ-ỹ0-9]+)\s*—\s*([A-Za-zÀ-ỹ0-9]+)', r'\1 - \2', text)

    # 5. Clean remaining em-dashes: " — " -> ", " or ": "
    text = text.replace(" — ", ", ")
    text = text.replace("—", "-")

    # 6. Clean robotic slashes in token-comments: "// Insilos" -> "# Insilos"
    text = text.replace('<span class="token-comment">//', '<span class="token-comment">#')

    # 7. Clean specific AI copy phrases
    text = text.replace("sai số không tính bằng phần trăm, nó được đo bằng",
                        "sai số không tính bằng phần trăm, mà đo bằng")

    return text

def assert_markup_preserved(before: str, after: str, rel_path: str) -> None:
    """
    F3 Guard: Fail if the transform changed anything but text or attribute character data.
    Verifies that the tag hierarchy and attribute key topology remain 100% identical.
    Encodes to UTF-8 bytes to safely handle files with XML encoding declarations (F1).
    """
    def skeleton(xml_text: str):
        root = ET.fromstring(xml_text.encode("utf-8"))
        return [(el.tag, tuple(sorted(el.attrib.keys()))) for el in root.iter()]

    before_skel = skeleton(before)
    after_skel = skeleton(after)
    if before_skel != after_skel:
        raise ValueError(f"STRUCTURAL DRIFT in {rel_path}: transform altered element/attribute topology")

def main():
    print("=== LAUNCHING FULL CODEBASE VIEW UNSLOP ENGINE ===")
    staged = []

    # Phase 1: Read, transform, validate, and check structural equivalence for ALL files.
    # NO WRITES OCCUR IN PHASE 1 (F2 Two-Phase Batch Transaction).
    for rel_path in TARGET_FILES:
        full_path = ROOT_DIR / rel_path
        if not full_path.exists():
            print(f"[!] Skipping missing file: {rel_path}")
            continue

        raw_text = full_path.read_text(encoding="utf-8")
        cleaned_text = clean_file_content(raw_text)

        if cleaned_text != raw_text:
            # F1 & F3: Encode to bytes so XML encoding declarations don't raise ValueError,
            # and verify tag/attribute topology is fully preserved.
            try:
                assert_markup_preserved(raw_text, cleaned_text, rel_path)
            except (ET.ParseError, ValueError) as e:
                print(f"[✗] VALIDATION ERROR in {rel_path}: {e}")
                print("[✗] ABORTING: Zero files written. Working tree unchanged.")
                sys.exit(1)

            staged.append((full_path, rel_path, cleaned_text, len(cleaned_text) - len(raw_text)))
        else:
            print(f"[-] No slop found in {rel_path}")

    # Phase 2: All files passed Phase 1 validation. Execute atomic writes.
    if staged:
        print(f"\n[*] Phase 1 passed (100% valid). Committing atomic writes for {len(staged)} files...")
        for full_path, rel_path, cleaned_text, diff_chars in staged:
            atomic_write_text(full_path, cleaned_text, encoding="utf-8")
            print(f"[✓] Unslop committed to {rel_path} (len diff: {diff_chars}, XML valid)")
    else:
        print("\n[✓] All target files are already clean and verified.")

    print(f"\n[✓] Full unslop completed: {len(staged)} files updated and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
