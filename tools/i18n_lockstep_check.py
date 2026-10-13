#!/usr/bin/env python3
"""
tools/i18n_lockstep_check.py
============================
Deterministic i18n Lockstep & Selection Stored-Key Invariance Engine.
Inspired by game-engine lockstep simulation state hashing:
1. Enforces Selection Key Immutability: selection database keys must remain immutable during rebranding.
2. Enforces POT Template Parity: every rebranded Python selection label must match an exact msgid in .pot.
3. Enforces Multi-Locale PO Lockstep: no locale .po file may retain stale/orphaned legacy msgids when .pot changes.
4. Auto-Heals Desynced Locales: with --fix, propagates updated msgids across all locales preserving translations.
"""

import os
import re
import sys
import ast
import argparse
import pathlib
from typing import Dict, List, Set, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Rebranded selection mappings: (module, relative_py_path, field_name, expected_key, expected_label, old_msgid)
REBRANDED_SELECTION_SPEC: List[Dict[str, str]] = [
    {
        "module": "account",
        "py_path": "addons/account/models/account_report.py",
        "field": "engine",
        "key": "domain",
        "label": "Insilos Domain",
        "old_msgid": "Odoo Domain",
    },
    {
        "module": "mail",
        "py_path": "addons/mail/models/res_users.py",
        "field": "notification_type",
        "key": "inbox",
        "label": "In Insilos",
        "old_msgid": "In Odoo",
    },
    {
        "module": "sms_twilio",
        "py_path": "addons/sms_twilio/models/res_company.py",
        "field": "sms_provider",
        "key": "iap",
        "label": "Send via Insilos",
        "old_msgid": "Send via Odoo",
    },
]

# Text msgid substitutions for multi-line or view help strings
REBRANDED_TEXT_SPEC: List[Dict[str, str]] = [
    {
        "module": "account",
        "old_msgid_snippet": "document in Odoo.",
        "new_msgid_snippet": "document in Insilos.",
    },
    {
        "module": "purchase",
        "old_msgid_snippet": "document in Odoo.",
        "new_msgid_snippet": "document in Insilos.",
    },
    {
        "module": "mail",
        "old_msgid_snippet": "- In Odoo: Notifications appear in your Odoo inbox.",
        "new_msgid_snippet": "- In Insilos: Notifications appear in your Insilos inbox.",
    },
]


def extract_selection_pairs(py_path: pathlib.Path) -> List[Tuple[str, str]]:
    """Extract (key, label) tuples from fields.Selection in a python source file."""
    if not py_path.exists():
        return []
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    pairs = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "Selection"
        ):
            # Check positional or keyword arguments
            candidates = list(node.args) + [kw.value for kw in node.keywords if kw.arg == "selection"]
            for arg in candidates:
                if isinstance(arg, (ast.List, ast.Tuple)):
                    for elt in arg.elts:
                        if (
                            isinstance(elt, (ast.Tuple, ast.List))
                            and len(elt.elts) >= 2
                            and isinstance(elt.elts[0], ast.Constant)
                            and isinstance(elt.elts[1], ast.Constant)
                        ):
                            pairs.append((elt.elts[0].value, elt.elts[1].value))
    return pairs


def get_pot_msgids(pot_path: pathlib.Path) -> Set[str]:
    """Extract all exact single-line msgids from a .pot file."""
    if not pot_path.exists():
        return set()
    text = pot_path.read_text(encoding="utf-8")
    return set(re.findall(r'^msgid\s+"(.*)"\s*$', text, flags=re.MULTILINE))


def audit_lockstep(fix: bool = False) -> Tuple[bool, List[str]]:
    """Run comprehensive lockstep audit across specs and locale files."""
    errors = []
    healed_count = 0

    print("=" * 80)
    print(" INSILOS DETERMINISTIC i18n LOCKSTEP & SELECTION INVARIANCE AUDITOR")
    print("=" * 80)

    # 1. Audit Selection Key Immutability and POT Parity
    print("[STAGE 1] Auditing Selection Key Immutability & .pot Template Parity...")
    for spec in REBRANDED_SELECTION_SPEC:
        py_file = REPO_ROOT / spec["py_path"]
        pot_file = REPO_ROOT / f"addons/{spec['module']}/i18n/{spec['module']}.pot"

        if not py_file.exists():
            errors.append(f"Missing Python file: {spec['py_path']}")
            continue
        if not pot_file.exists():
            errors.append(f"Missing POT template: {pot_file}")
            continue

        pairs = extract_selection_pairs(py_file)
        pair_dict = dict(pairs)

        # Check key immutability
        if spec["key"] not in pair_dict:
            errors.append(
                f"Selection key mutated or missing in {spec['py_path']}: expected key {spec['key']!r}"
            )
            continue

        actual_label = pair_dict[spec["key"]]
        if actual_label != spec["label"]:
            errors.append(
                f"Selection label mismatch in {spec['py_path']}: expected {spec['label']!r}, got {actual_label!r}"
            )

        # Check .pot template contains the rebranded label
        pot_msgids = get_pot_msgids(pot_file)
        if spec["label"] not in pot_msgids:
            errors.append(
                f".pot template {pot_file.name} missing msgid for rebranded label {spec['label']!r}"
            )

    if not errors:
        print("  [✓] All selection stored keys immutable; all labels match .pot msgids.")
    else:
        for e in errors:
            print(f"  [✗] {e}")

    # 2. Audit Multi-Locale .po Files for Stale / Orphaned msgids
    print("\n[STAGE 2] Auditing Multi-Locale .po Files for Orphaned msgids...")
    orphaned_found = 0

    # 2a. Selection label orphans
    for spec in REBRANDED_SELECTION_SPEC:
        old_pattern = f'msgid "{spec["old_msgid"]}"'
        new_pattern = f'msgid "{spec["label"]}"'
        i18n_dir = REPO_ROOT / f"addons/{spec['module']}/i18n"
        if not i18n_dir.exists():
            continue

        for po_path in sorted(i18n_dir.glob("*.po")):
            content = po_path.read_text(encoding="utf-8")
            if old_pattern in content:
                orphaned_found += 1
                if fix:
                    updated = content.replace(old_pattern, new_pattern)
                    po_path.write_text(updated, encoding="utf-8")
                    healed_count += 1
                else:
                    errors.append(
                        f"Orphaned msgid in {po_path.relative_to(REPO_ROOT)}: '{old_pattern}' (should be '{new_pattern}')"
                    )

    # 2b. Help text / multi-line string snippet orphans
    for text_spec in REBRANDED_TEXT_SPEC:
        old_snippet = text_spec["old_msgid_snippet"]
        new_snippet = text_spec["new_msgid_snippet"]
        i18n_dir = REPO_ROOT / f"addons/{text_spec['module']}/i18n"
        if not i18n_dir.exists():
            continue

        for po_path in sorted(i18n_dir.glob("*.po")):
            content = po_path.read_text(encoding="utf-8")
            if old_snippet in content:
                orphaned_found += 1
                if fix:
                    updated = content.replace(old_snippet, new_snippet)
                    po_path.write_text(updated, encoding="utf-8")
                    healed_count += 1
                else:
                    errors.append(
                        f"Orphaned string snippet in {po_path.relative_to(REPO_ROOT)}: contains '{old_snippet}'"
                    )

    if fix and healed_count > 0:
        print(f"  [✓] Auto-healed {healed_count} orphaned msgids across multi-locale .po files.")
        errors = [e for e in errors if not e.startswith("Orphaned")]

    if not errors:
        print(f"  [✓] Zero orphaned msgids detected across all registered modules and locales.")
    else:
        print(f"  [!] Found {len(errors)} lockstep issues.")

    print("=" * 80)
    is_clean = len(errors) == 0
    return is_clean, errors


def main():
    parser = argparse.ArgumentParser(description="Deterministic i18n Lockstep & Selection Invariance Auditor")
    parser.add_argument("--check", action="store_true", help="Fail with exit 1 if any desync is detected")
    parser.add_argument("--fix", action="store_true", help="Automatically heal orphaned msgids across .po files")
    args = parser.parse_args()

    is_clean, errors = audit_lockstep(fix=args.fix)
    if args.check and not is_clean:
        print(f"\n[FAIL] i18n lockstep audit failed with {len(errors)} error(s).")
        sys.exit(1)
    elif is_clean:
        print("\n[PASS] i18n lockstep audit passed: 100% synchronized.")
        sys.exit(0)


if __name__ == "__main__":
    main()
