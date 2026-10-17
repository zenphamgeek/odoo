#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch 40 (`SEC-03`): Public Brand Isolation Linter (`tools/lint_brand_isolation.py`).
Prevents internal ERP legal entity identifiers (`Digimate`, `Người Bạn Số`, `0317958465`,
`digimate_drive_logo.png`, `UNG DUNG SANG TAO`, `0313683499`) from leaking into public Website
or Portal QWeb XML templates (`CWE-200` / `CWE-359`).
"""
import glob
import os
import re
import sys
from typing import List, Tuple

FORBIDDEN_PUBLIC_BRAND_PATTERNS = [
    re.compile(r"\bDigimate\b", re.IGNORECASE),
    re.compile(r"Người\s+Bạn\s+Số", re.IGNORECASE),
    re.compile(r"\b0317958465\b"),
    re.compile(r"digimate_drive_logo\.png", re.IGNORECASE),
    re.compile(r"UNG\s+DUNG\s+SANG\s+TAO", re.IGNORECASE),
    re.compile(r"Ứng\s+Dụng\s+Sáng\s+Tạo", re.IGNORECASE),
    re.compile(r"\b0313683499\b"),
]


def scan_file_for_brand_leaks(filepath: str) -> List[Tuple[int, str]]:
    violations: List[Tuple[int, str]] = []
    if not os.path.exists(filepath):
        return violations
    with open(filepath, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            for pattern in FORBIDDEN_PUBLIC_BRAND_PATTERNS:
                if pattern.search(line):
                    violations.append((lineno, line.strip()))
    return violations


def main() -> int:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    targets = sorted(glob.glob(os.path.join(root_dir, "enterprise/insilos_website/views/*.xml")))
    portal_tpl = os.path.join(root_dir, "addons/insilos_al2c/views/portal_templates.xml")
    if os.path.exists(portal_tpl):
        targets.append(portal_tpl)

    failed = False
    for path in targets:
        leaks = scan_file_for_brand_leaks(path)
        for lineno, text in leaks:
            print(f"[BRAND LEAK] {path}:{lineno} -> {text}", file=sys.stderr)
            failed = True
    if not failed:
        print(f"[✓] Brand Isolation Linter verified 0 leaks across {len(targets)} public XML templates.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
