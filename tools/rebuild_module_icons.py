#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/rebuild_module_icons.py
=============================
Automated rebuild mechanism for Insilos Module Icons.
Rebuilds module icons across addons, enterprise, and odoo/addons according to
the canonical Insilos Horizon-Carbon Tile (HCT) signature.
Executes in parallel with zero compatibility shims.
Complies with docs/INSILOS_ICON_STYLE_SPEC.md.
"""

import argparse
import concurrent.futures
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.generate_horizon_carbon_icons import (
    load_authority_mapping,
    find_all_modules,
    plan_all_targets,
    ensure_source_glyph,
    process_target_worker,
    check_targets_integrity,
    update_database_ir_module_icons,
    compile_hct_svg,
    compile_hct_png,
)


def main():
    parser = argparse.ArgumentParser(description="Auto Rebuild Module Icons according to Insilos Horizon-Carbon Tile signature")
    parser.add_argument('--check', action='store_true', help="Check integrity of icons only without writing")
    parser.add_argument('--update-db', action='store_true', help="Sync database ir_module_module icons")
    parser.add_argument('--workers', type=int, default=os.cpu_count() or 4, help="Parallel worker threads/processes")
    args = parser.parse_args()

    print("================================================================================")
    print("🚀 INSILOS HORIZON-CARBON TILE (HCT) REBUILD MODULE ICONS ENGINE")
    print(f"   Mode: {'CHECK ONLY' if args.check else 'PARALLEL REBUILD'} | Workers: {args.workers}")
    print("================================================================================\n")

    authority_mapping = load_authority_mapping()
    all_modules = find_all_modules()
    print(f"[REBUILD MODULE ICONS] Discovered {len(all_modules)} modules across search paths.")

    targets = plan_all_targets(all_modules, authority_mapping)
    num_svg = sum(1 for t in targets if t[4] == 'svg')
    num_png = sum(1 for t in targets if t[4] == 'png')
    print(f"[REBUILD MODULE ICONS] Planned {len(targets)} targets ({num_svg} SVG, {num_png} PNG).")

    if args.check:
        print("[CHECK] Validating icon targets integrity against Horizon-Carbon Tile specification...")
        checked, errors = check_targets_integrity(targets)
        if errors:
            print(f"  ✗ Found {len(errors)} issues across {checked} checked targets:")
            for err in errors[:25]:
                print(f"    - {err}")
            if len(errors) > 25:
                print(f"    ... and {len(errors) - 25} more.")
            sys.exit(1)
        else:
            print(f"  ✓ Integrity PASS: All {checked} targets meet the canonical Horizon-Carbon Tile signature.")
            sys.exit(0)

    # Pre-seed canonical glyph sources sequentially to prevent race conditions
    unique_glyphs = {t[1] for t in targets}
    for g in unique_glyphs:
        ensure_source_glyph(g)

    # Parallel Execution
    print(f"\n[PARALLEL EXECUTION] Rebuilding {len(targets)} targets with {args.workers} workers...")
    written_svg = 0
    written_png = 0
    skipped = 0
    errors = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(process_target_worker, targets):
            status, path = result
            if status == 'write_svg':
                written_svg += 1
            elif status == 'write_png':
                written_png += 1
            elif status == 'skip':
                skipped += 1
            elif status == 'error':
                errors.append(path)

    print(f"[DONE] Wrote {written_svg} SVGs, {written_png} PNGs, {skipped} up-to-date, {len(errors)} errors.")
    if errors:
        for err in errors[:20]:
            print(f"  ✗ {err}")
        sys.exit(1)

    if args.update_db:
        update_database_ir_module_icons()

    print("\n[SUCCESS] All module icons rebuilt according to Insilos Horizon-Carbon Tile signature.")


if __name__ == '__main__':
    main()
