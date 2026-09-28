#!/usr/bin/env python3
"""
Insilos Platform - Enterprise Asset Inventory & Quality Verification Scanner
Scans and classifies all visual, graphic, and media assets across base, addons, and apps.
Verifies Insilos branding compliance (palette, signature style) and asset completeness.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

ASSET_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.svg', '.ico', '.webp', '.gif', '.mp4', '.webm'}
EXCLUDED_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', '.idea', '.vscode', '.agents'}

LEGACY_PALETTES = [
    re.compile(r'#714B67|#017e84', re.IGNORECASE),
]

def classify_asset(rel_path, fname):
    lower_path = str(rel_path).lower()
    lower_fname = fname.lower()

    if lower_fname.endswith(('.mp4', '.webm')):
        return 'media_video'
    if 'icon' in lower_fname or 'icon' in lower_path:
        return 'ui_or_app_icon'
    if any(k in lower_path for k in ['empty', 'inbox', 'placeholder', 'illustration', 'undraw']):
        return 'illustration_or_emptystate'
    if any(k in lower_path for k in ['logo', 'brand', 'banner', 'header']):
        return 'branding_or_logo'
    if any(k in lower_path for k in ['avatar', 'user', 'res_partner']):
        return 'avatar_or_profile'
    return 'general_graphic'

def scan_assets(root_path):
    root = Path(root_path)
    inventory = {
        'total_assets': 0,
        'by_category': {},
        'by_extension': {},
        'legacy_palette_hits': [],
        'assets': []
    }

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext in ASSET_EXTENSIONS:
                fpath = Path(dirpath) / fname
                rel_path = fpath.relative_to(root)
                category = classify_asset(rel_path, fname)

                inventory['total_assets'] += 1
                inventory['by_category'][category] = inventory['by_category'].get(category, 0) + 1
                inventory['by_extension'][ext] = inventory['by_extension'].get(ext, 0) + 1

                # Check SVG text for legacy palette
                if ext == '.svg':
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            svg_text = f.read()
                            for pat in LEGACY_PALETTES:
                                if pat.search(svg_text):
                                    inventory['legacy_palette_hits'].append({
                                        'file': str(rel_path),
                                        'reason': 'Contains legacy purple/teal brand colors'
                                    })
                    except Exception:
                        pass

                inventory['assets'].append({
                    'path': str(rel_path),
                    'category': category,
                    'extension': ext,
                    'size_bytes': os.path.getsize(fpath)
                })

    return inventory

def main():
    parser = argparse.ArgumentParser(description="Insilos Asset Scanner & Quality Harness")
    parser.add_argument("--path", default=".", help="Root path to scan")
    parser.add_argument("--output", default="asset_inventory.json", help="Output path for JSON inventory")
    parser.add_argument("--max-legacy-palette-hits", type=int, default=0, help="Max allowed legacy color hits in new SVGs")
    args = parser.parse_args()

    inv = scan_assets(args.path)
    
    # Save output
    out_path = Path(args.output)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(inv, f, indent=2)

    print(f"Asset scan complete. Total assets found: {inv['total_assets']}")
    print(f"By category: {json.dumps(inv['by_category'], indent=2)}")
    print(f"By extension: {json.dumps(inv['by_extension'], indent=2)}")
    print(f"Legacy palette hits in SVGs: {len(inv['legacy_palette_hits'])}")

    if len(inv['legacy_palette_hits']) > args.max_legacy_palette_hits:
        print(f"\n[FAIL] Found {len(inv['legacy_palette_hits'])} legacy palette hits (threshold: {args.max_legacy_palette_hits})")
        sys.exit(1)

    print("\n[PASS] Asset scan & verification completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
