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

def clean_file_content(filepath: str, text: str) -> str:
    original = text

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
    text = text.replace("Doanh nghiệp không thiếu phần mềm, họ bị giam cầm trong những ốc đảo rời rạc.",
                        "Doanh nghiệp không thiếu phần mềm, họ bị giam cầm trong những ốc đảo rời rạc.")
    text = text.replace("sai số không tính bằng phần trăm, nó được đo bằng",
                        "sai số không tính bằng phần trăm, mà đo bằng")

    return text

def main():
    print("=== LAUNCHING FULL CODEBASE VIEW UNSLOP ENGINE ===")
    total_modified = 0

    for rel_path in TARGET_FILES:
        full_path = ROOT_DIR / rel_path
        if not full_path.exists():
            print(f"[!] Skipping missing file: {rel_path}")
            continue

        raw_text = full_path.read_text(encoding="utf-8")
        cleaned_text = clean_file_content(rel_path, raw_text)

        if cleaned_text != raw_text:
            # Validate XML before writing
            try:
                ET.fromstring(cleaned_text)
            except ET.ParseError as e:
                print(f"[✗] XML VALIDATION ERROR in {rel_path}: {e}")
                sys.exit(1)

            # Atomic write with permission preservation
            atomic_write_text(full_path, cleaned_text, encoding="utf-8")
            diff_chars = len(cleaned_text) - len(raw_text)
            print(f"[✓] Unslop applied cleanly to {rel_path} (len diff: {diff_chars}, XML valid)")
            total_modified += 1
        else:
            print(f"[-] No slop found in {rel_path}")

    print(f"\n[✓] Full unslop completed: {total_modified} files updated and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
