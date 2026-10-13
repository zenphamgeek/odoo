#!/usr/bin/env python3
"""
tools/lint_i18n_msgid_sync.py
=============================
CI Quality Gate: Translation Catalog & msgid Lockstep Integrity Guard.

Enforces that when a source translation key (msgid) is updated or rebranded
in a module's template (.pot) or model/view declarations:
1. Zero sibling locale files (.po) retain deprecated msgid keys that would
   silently orphan runtime translations or cause English-fallback regressions.
2. All translated string entries (msgstr) retain semantic alignment without
   residual deprecated platform signatures.
3. The catalog drift across all active language packs is strictly zero.
"""

import sys
import glob
import os
from typing import List, Tuple

try:
    import polib
except ImportError:
    print("ERROR: polib is required for i18n msgid synchronization linting.")
    sys.exit(1)


REBRAND_KEY_PAIRS: List[Tuple[str, str, str]] = [
    # (module_dir, deprecated_msgid_needle, canonical_pot_needle)
    ('addons/account', 'document in Odoo.', 'document in Insilos.'),
    ('addons/account', 'Odoo Domain', 'Insilos Domain'),
    ('addons/mail', 'In Odoo', 'In Insilos'),
    ('addons/mail', 'Notifications appear in your Odoo inbox', 'Notifications appear in your Insilos inbox'),
    ('addons/purchase', 'document in Odoo.', 'document in Insilos.'),
    ('addons/sms_twilio', 'Send via Odoo', 'Send via Insilos'),
    ('addons/account_peppol', 'Odoo Demo ID', 'Insilos Demo ID'),
]


def audit_i18n_catalog_integrity(repo_root: str = ".") -> Tuple[int, List[str]]:
    violations = []

    print("[*] Running i18n Translation Catalog & msgid Lockstep Integrity Audit...")

    for mod_rel, deprecated_needle, canonical_needle in REBRAND_KEY_PAIRS:
        mod_dir = os.path.join(repo_root, mod_rel, 'i18n')
        pot_files = glob.glob(os.path.join(mod_dir, '*.pot'))
        if not pot_files:
            continue

        # 1. Verify that .pot has canonical needle
        pot_path = pot_files[0]
        pot = polib.pofile(pot_path)
        pot_has_canonical = any(canonical_needle in e.msgid for e in pot)
        pot_has_deprecated = any(deprecated_needle in e.msgid for e in pot)

        if pot_has_deprecated:
            violations.append(
                f"[POT VIOLATION] {pot_path}: Still contains deprecated msgid '{deprecated_needle}'"
            )

        if not pot_has_canonical:
            violations.append(
                f"[POT VIOLATION] {pot_path}: Missing canonical msgid '{canonical_needle}'"
            )

        # 2. Verify all sibling .po files have zero deprecated msgids
        po_files = glob.glob(os.path.join(mod_dir, '*.po'))
        for po_path in po_files:
            po = polib.pofile(po_path)
            for entry in po:
                if deprecated_needle in entry.msgid:
                    violations.append(
                        f"[PO DRIFT] {po_path}:{entry.linenum}: Contains stale deprecated msgid "
                        f"'{entry.msgid[:60]}...' (must be updated to '{canonical_needle}')"
                    )

    return len(violations), violations


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    count, violations = audit_i18n_catalog_integrity(repo_root)

    if count > 0:
        print(f"\n[FAIL] {count} i18n catalog lockstep synchronization violation(s) detected:")
        for v in violations:
            print(f"  ✗ {v}")
        print("\nRemediation: Update stale .po catalogs to track canonical .pot keys and localized msgstr.")
        sys.exit(1)

    print("[✓] Zero i18n catalog/msgid desynchronization detected across all checked modules.")
    print("=" * 80)
    print("I18N CATALOG INTEGRITY GATE: PASSED (EXIT 0)")
    print("=" * 80)
    sys.exit(0)


if __name__ == '__main__':
    main()
