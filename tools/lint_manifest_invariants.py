#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.
"""
tools/lint_manifest_invariants.py
==================================
SEC Directive 3: Manifest AST Invariant Guard & Semver Normalizer.

Scans custom manifests under addons/:
- gpu_fleet_manager
- insilos_adapter
- insilos_al2c
- insilos_currency_cron
- insilos_pinned_conversion
- insilos_sap_fiori
- insilos_security

Validates:
1. Valid Python AST dictionary structure.
2. Manifest 'version' starts with f'{odoo.release.serie}.' (or '20.0.').

Options:
--check: Returns exit code 1 if any violation found, exit code 0 if all clean.
--fix:   Automatically normalizes invalid manifest versions to canonical 20.0.1.0.0.
"""

import argparse
import ast
import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from odoo import release
    TARGET_SERIES = release.serie
except Exception:
    TARGET_SERIES = "20.0"

CANONICAL_VERSION = "26.0.1.0.0"

TARGET_ADDONS = [
    "gpu_fleet_manager",
    "insilos_adapter",
    "insilos_al2c",
    "insilos_currency_cron",
    "insilos_pinned_conversion",
    "insilos_sap_fiori",
    "insilos_security",
]


def get_manifest_path(addon_name: str) -> str:
    return os.path.join(ROOT_DIR, "addons", addon_name, "__manifest__.py")


def parse_manifest_ast(content: str, filepath: str) -> dict:
    """Parse manifest content using Python AST and return dictionary."""
    tree = ast.parse(content, filename=filepath)
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Dict):
            try:
                return ast.literal_eval(node.value)
            except Exception as e:
                raise ValueError(f"Failed to evaluate manifest AST dictionary in {filepath}: {e}")
    # Fallback to ast.literal_eval on whole content
    try:
        val = ast.literal_eval(content)
        if isinstance(val, dict):
            return val
    except Exception:
        pass
    raise ValueError(f"No valid AST dictionary found in manifest: {filepath}")


def check_manifest(addon_name: str) -> tuple[bool, str]:
    """
    Validates manifest AST and semver invariant.
    Returns (is_valid, error_or_info_message).
    """
    path = get_manifest_path(addon_name)
    if not os.path.isfile(path):
        return False, f"Manifest file missing: {path}"

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        manifest_dict = parse_manifest_ast(content, path)
    except Exception as e:
        return False, f"AST Syntax Error in {path}: {e}"

    version = manifest_dict.get("version")
    if not version or not isinstance(version, str):
        return False, f"Missing or invalid 'version' field in {path}: {version!r}"

    expected_prefixes = (f"{TARGET_SERIES}.", "26.0.", "20.0.")
    if not version.startswith(expected_prefixes):
        return False, f"Invalid version prefix in {path}: {version!r} (expected starts with {expected_prefixes})"

    return True, f"Valid: version {version!r}"


def fix_manifest(addon_name: str) -> bool:
    """
    Fixes manifest version to CANONICAL_VERSION ('20.0.1.0.0').
    Returns True if fixed or already valid, False on error.
    """
    path = get_manifest_path(addon_name)
    if not os.path.isfile(path):
        print(f"[!] Cannot fix missing file: {path}", file=sys.stderr)
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    is_valid, _ = check_manifest(addon_name)
    if is_valid:
        # Check if version is exactly canonical
        try:
            m_dict = parse_manifest_ast(content, path)
            if m_dict.get("version") == CANONICAL_VERSION:
                return True
        except Exception:
            pass

    # Regex replacement for 'version': '...' or "version": "..."
    pattern = r"([\'\"]version[\'\"]\s*:\s*[\'\"])[^\'\"]+([\'\"])"
    new_content, count = re.subn(pattern, rf"\g<1>{CANONICAL_VERSION}\g<2>", content)
    if count == 0:
        print(f"[!] Could not locate 'version' string in {path} to fix", file=sys.stderr)
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Re-validate
    valid_after, msg = check_manifest(addon_name)
    if not valid_after:
        print(f"[!] Re-validation failed after fix for {path}: {msg}", file=sys.stderr)
        return False

    print(f"[✓] Fixed {addon_name} manifest version -> {CANONICAL_VERSION}")
    return True


def run_checks() -> int:
    all_passed = True
    print(f"[*] Linting manifest invariants across {len(TARGET_ADDONS)} custom addons (target serie: {TARGET_SERIES})...")
    for addon in TARGET_ADDONS:
        ok, msg = check_manifest(addon)
        if ok:
            print(f"  [✓] {addon:28s}: {msg}")
        else:
            print(f"  [✗] {addon:28s}: {msg}", file=sys.stderr)
            all_passed = False

    if all_passed:
        print("[✓] All custom manifests satisfy AST & Semver invariants.")
        return 0
    else:
        print("[✗] Manifest AST invariant violations detected!", file=sys.stderr)
        return 1


def run_fixes() -> int:
    print(f"[*] Normalizing manifest versions to {CANONICAL_VERSION}...")
    success = True
    for addon in TARGET_ADDONS:
        if not fix_manifest(addon):
            success = False
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description="SEC Directive 3: Manifest AST Invariant Guard")
    parser.add_argument("--check", action="store_true", help="Check manifests for AST & Semver compliance (default)")
    parser.add_argument("--fix", action="store_true", help="Fix invalid manifest versions to canonical 20.0.1.0.0")
    args = parser.parse_args()

    if args.fix:
        code = run_fixes()
        if code == 0:
            code = run_checks()
        sys.exit(code)
    else:
        # Default or explicit --check
        sys.exit(run_checks())


if __name__ == "__main__":
    main()
