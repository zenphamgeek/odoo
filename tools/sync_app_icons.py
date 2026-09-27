#!/usr/bin/env python3
"""
tools/sync_app_icons.py
Compiles canonical Phosphor duotone glyphs with #0B2E64 and syncs them
to module launcher targets per doc/HARD_REFACTOR_PART_A_BRANDING_ASSETS_TAXONOMY.md.
"""

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
        os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'modules.png'),
    ],
    'base.menu_administration': [
        os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'settings.svg'),
        os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'settings.png'),
    ],
    'hr_timesheet': [
        os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.svg'),
        os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'),
        os.path.join(REPO_ROOT, 'enterprise', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'),
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

def compile_duotone_svg(src_svg_path):
    with open(src_svg_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace fill="currentColor" or add fill="#0B2E64"
    if 'fill="currentColor"' in content:
        content = content.replace('fill="currentColor"', 'fill="#0B2E64"')
    elif 'fill=' not in content[:content.find('>')]:
        content = content.replace('<svg ', '<svg fill="#0B2E64" ')

    # Ensure viewBox="0 0 256 256"
    if 'viewBox="0 0 256 256"' not in content:
        content = re.sub(r'viewBox="[^"]*"', 'viewBox="0 0 256 256"', content)

    # Ensure opacity="0.2" is present
    if 'opacity="0.2"' not in content:
        # add opacity="0.2" to first path if missing
        content = content.replace('<path ', '<path opacity="0.2" ', 1)

    return content

def main():
    if not os.path.exists(MAPPING_FILE):
        print(f"Error: {MAPPING_FILE} not found!")
        sys.exit(1)

    with open(MAPPING_FILE, 'r') as f:
        mapping = json.load(f)

    print(f"[SYNC APP ICONS] Processing {len(mapping)} mappings...")
    synced = 0

    for key, glyph in mapping.items():
        src_svg = os.path.join(CANONICAL_DIR, f"{glyph}-duotone.svg")
        if not os.path.exists(src_svg):
            print(f"  ✗ Missing canonical glyph: {src_svg}")
            continue

        compiled_svg = compile_duotone_svg(src_svg)

        targets = []
        if key in SPECIAL_TARGETS:
            targets = SPECIAL_TARGETS[key]
        else:
            mod_dir = find_module_dir(key)
            if mod_dir:
                desc_dir = os.path.join(mod_dir, 'static', 'description')
                targets.append(os.path.join(desc_dir, 'icon.svg'))
                # Also place in enterprise counterpart if exists
                if mod_dir.startswith(os.path.join(REPO_ROOT, 'addons')):
                    ent_dir = os.path.join(REPO_ROOT, 'enterprise', key)
                    if os.path.isdir(ent_dir):
                        targets.append(os.path.join(ent_dir, 'static', 'description', 'icon.svg'))

        for target in targets:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if target.endswith('.png'):
                import cairosvg
                png_bytes = cairosvg.svg2png(bytestring=compiled_svg.encode('utf-8'), output_width=256, output_height=256)
                with open(target, 'wb') as f:
                    f.write(png_bytes)
            else:
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(compiled_svg)
            synced += 1
            print(f"  ✓ Deployed: {os.path.relpath(target, REPO_ROOT)}")

    print(f"\n[DONE] Successfully deployed {synced} icon files across modules.")

if __name__ == '__main__':
    main()
