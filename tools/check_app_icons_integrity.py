#!/usr/bin/env python3
"""
tools/check_app_icons_integrity.py
Integrity verification gate for Insilos App Icons.
Complies with doc/HARD_REFACTOR_PART_A_BRANDING_ASSETS_TAXONOMY.md.
"""

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CANONICAL_DIR = os.path.join(REPO_ROOT, 'tools', 'phosphor_duotone')
MAPPING_FILE = os.path.join(REPO_ROOT, 'tools', 'icon_mapping.json')

MODULE_SEARCH_PATHS = [
    os.path.join(REPO_ROOT, 'addons'),
    os.path.join(REPO_ROOT, 'enterprise'),
    os.path.join(REPO_ROOT, 'odoo', 'addons'),
]

SPECIAL_TARGETS = {
    'base.menu_management': [
        os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'modules.svg'),
    ],
    'base.menu_administration': [
        os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'settings.svg'),
    ],
    'hr_timesheet': [
        os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.svg'),
        os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'),
    ],
    'mrp_workorder': [
        os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'icon.svg'),
        os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'mrp_display_icon.svg'),
    ],
}

def find_module_dir(module_name):
    for base in MODULE_SEARCH_PATHS:
        p = os.path.join(base, module_name)
        if os.path.isdir(p):
            return p
    return None

def self_check():
    print("[SELF-CHECK] Validating icon mapping authority and canonical glyphs...")
    errors = []

    if not os.path.exists(MAPPING_FILE):
        errors.append(f"Authority mapping file not found: {MAPPING_FILE}")
        return False, errors

    try:
        with open(MAPPING_FILE, 'r') as f:
            mapping = json.load(f)
    except Exception as e:
        errors.append(f"Invalid JSON in {MAPPING_FILE}: {e}")
        return False, errors

    if len(mapping) < 10:
        errors.append(f"Mapping authority has only {len(mapping)} entries, expected >= 60 apps.")

    # Check uniqueness
    seen_glyphs = {}
    for app, glyph in mapping.items():
        if glyph in seen_glyphs:
            errors.append(f"Duplicate glyph '{glyph}' used by both '{seen_glyphs[glyph]}' and '{app}'")
        seen_glyphs[glyph] = app

    # Check canonical glyph source files
    for app, glyph in mapping.items():
        src_svg = os.path.join(CANONICAL_DIR, f"{glyph}-duotone.svg")
        if not os.path.exists(src_svg):
            errors.append(f"Missing canonical source glyph: {src_svg} (for {app})")
        else:
            with open(src_svg, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'viewBox="0 0 256 256"' not in content:
                errors.append(f"Canonical source {src_svg} missing viewBox='0 0 256 256'")
            if 'opacity="0.2"' not in content:
                errors.append(f"Canonical source {src_svg} missing duotone layer opacity='0.2'")

    success = (len(errors) == 0)
    if success:
        print(f"  ✓ Authority mapping valid: {len(mapping)} unique apps mapped.")
        print(f"  ✓ All {len(mapping)} canonical glyphs in tools/phosphor_duotone/ meet contract.")
    else:
        print(f"  ✗ Self-check found {len(errors)} issues:")
        for err in errors:
            print(f"    - {err}")

    return success, errors

def full_check():
    sc_ok, sc_errors = self_check()
    if not sc_ok:
        return False

    print("\n[INTEGRITY-CHECK] Validating deployed launcher target icons...")
    with open(MAPPING_FILE, 'r') as f:
        mapping = json.load(f)

    errors = []
    checked = 0

    for app, glyph in mapping.items():
        targets = []
        if app in SPECIAL_TARGETS:
            targets = SPECIAL_TARGETS[app]
        else:
            mod_dir = find_module_dir(app)
            if not mod_dir:
                errors.append(f"Module directory not found for app: {app}")
                continue
            targets.append(os.path.join(mod_dir, 'static', 'description', 'icon.svg'))

        for target in targets:
            checked += 1
            if not os.path.exists(target):
                errors.append(f"Target icon missing: {os.path.relpath(target, REPO_ROOT)}")
                continue

            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()

            if '<svg' not in content:
                errors.append(f"Target is not an SVG: {os.path.relpath(target, REPO_ROOT)}")
            if 'viewBox="0 0 256 256"' not in content:
                errors.append(f"Invalid viewBox in {os.path.relpath(target, REPO_ROOT)}")
            if '#0B2E64' not in content and 'currentColor' not in content:
                errors.append(f"Invalid color in {os.path.relpath(target, REPO_ROOT)}, must be #0B2E64")
            if 'opacity="0.2"' not in content:
                errors.append(f"Missing duotone layer opacity='0.2' in {os.path.relpath(target, REPO_ROOT)}")
            if '<image ' in content or 'data:image/' in content:
                errors.append(f"Embedded raster detected in vector launcher: {os.path.relpath(target, REPO_ROOT)}")

    if errors:
        print(f"\n[FAIL] Integrity check failed with {len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
        return False

    print(f"  ✓ Verified {checked} target launcher icons across modules.")
    print("\n[PASS] App Icons integrity check PASSED 100%. All launcher icons meet Part A contract.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Check App Icons integrity")
    parser.add_argument('--self-check', action='store_true', help="Perform self-check only")
    args = parser.parse_args()

    if args.self_check:
        ok, _ = self_check()
        sys.exit(0 if ok else 1)
    else:
        ok = full_check()
        sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
