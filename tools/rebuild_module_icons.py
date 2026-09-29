#!/usr/bin/env python3
"""
tools/rebuild_module_icons.py
Automated rebuild mechanism for Insilos Module Icons.
Rebuilds module icons across addons, enterprise, and odoo/addons according to
the canonical Insilos signature (Phosphor duotone, #0B2E64, viewBox="0 0 256 256", opacity="0.2").
Executes in parallel with zero compatibility shims.
Complies with doc/HARD_REFACTOR_PART_A_BRANDING_ASSETS_TAXONOMY.md.
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import sys
import cairosvg

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRIMARY_CANONICAL_DIR = os.path.join(REPO_ROOT, 'tools', 'phosphor_duotone')
EXTENDED_CANONICAL_DIR = os.path.join(REPO_ROOT, 'branding', 'phosphor', 'assets', 'duotone')
MAPPING_FILE = os.path.join(REPO_ROOT, 'tools', 'icon_mapping.json')

MODULE_SEARCH_PATHS = [
    os.path.join(REPO_ROOT, 'addons'),
    os.path.join(REPO_ROOT, 'enterprise'),
    os.path.join(REPO_ROOT, 'odoo', 'addons'),
]

# Explicit glyph mappings for core / non-root modules
CORE_MODULE_MAPPING = {
    'base': 'cube',
    'sale': 'tag',
    'product': 'package',
    'product_expiry': 'barcode',
    'lunch': 'fork-knife',
    'sms': 'chat-teardrop-text',
    'snailmail': 'envelope-open',
    'pos_restaurant': 'fork-knife',
    'website_sale': 'shopping-cart',
    'website_blog': 'book-open',
    'website_forum': 'chats-teardrop',
    'website_event': 'ticket',
    'website_slides': 'graduation-cap',
    'website_livechat': 'chats-teardrop',
    'timesheet_grid': 'clock',
    'timer': 'timer',
    'spreadsheet': 'table',
    'web_studio': 'magic-wand',
    'board': 'layout',
    'gamification': 'medal',
    'iap': 'lightning',
    'data_cleaning': 'broom',
    'partner_autocomplete': 'address-book',
    'ai': 'sparkle',
    'ai_app': 'sparkle',
    'ai_documents_source': 'sparkle',
    'ai_knowledge': 'sparkle',
    'ai_website': 'sparkle',
    'mail_bot': 'robot',
    'microsoft_calendar': 'calendar',
    'google_calendar': 'calendar',
    'microsoft_outlook': 'envelope-simple',
    'google_gmail': 'envelope-simple',
    'l10n': 'globe',
    'l10n_ar': 'globe',
    'l10n_ar_website_sale': 'globe',
    'l10n_tw_reports': 'globe',
}

# Prefix / category patterns mapped to Phosphor duotone glyphs
PATTERN_RULES = [
    (r'^ai(_|$)', 'sparkle'),
    (r'^delivery_', 'truck'),
    (r'^payment_paypal', 'credit-card'),
    (r'^payment_stripe', 'credit-card'),
    (r'^payment_', 'credit-card'),
    (r'^social_facebook', 'facebook-logo'),
    (r'^social_instagram', 'instagram-logo'),
    (r'^social_linkedin', 'linkedin-logo'),
    (r'^social_twitter', 'twitter-logo'),
    (r'^social_youtube', 'youtube-logo'),
    (r'^social_', 'share-network'),
    (r'^pos_', 'storefront'),
    (r'^website_sale_', 'shopping-cart'),
    (r'^website_event_', 'ticket'),
    (r'^website_slides_', 'graduation-cap'),
    (r'^website_helpdesk_', 'lifebuoy'),
    (r'^website_crm_', 'funnel'),
    (r'^website_', 'globe'),
    (r'^helpdesk_', 'lifebuoy'),
    (r'^mrp_plm', 'git-merge'),
    (r'^mrp_maintenance', 'gear-six'),
    (r'^mrp_', 'factory'),
    (r'^stock_', 'warehouse'),
    (r'^hr_recruitment_', 'user-focus'),
    (r'^hr_payroll_', 'money'),
    (r'^hr_expense_', 'receipt'),
    (r'^hr_attendance_', 'fingerprint'),
    (r'^hr_appraisal_', 'trophy'),
    (r'^hr_holidays_', 'airplane-takeoff'),
    (r'^hr_skills', 'users'),
    (r'^hr_work_entry', 'clock-user'),
    (r'^hr_', 'users-four'),
    (r'^project_', 'kanban'),
    (r'^account_asset', 'currency-circle-dollar'),
    (r'^account_', 'file-text'),
    (r'^l10n_', 'globe'),
    (r'^theme_', 'palette'),
    (r'^test_', 'flask'),
    (r'^base_', 'cube'),
]

SPECIAL_TARGETS = {
    'base.menu_management': [
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'modules.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'modules.png'), 'png'),
    ],
    'base.menu_administration': [
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'settings.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'settings.png'), 'png'),
    ],
    'base': [
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'icon.png'), 'png'),
    ],
    'board': [
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'board.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'description', 'board.png'), 'png'),
    ],
    'hr_timesheet': [
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.png'), 'png'),
        (os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'hr_timesheet', 'static', 'description', 'icon_timesheet.svg'), 'svg'),
    ],
    'mrp_workorder': [
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'icon.png'), 'png'),
        (os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'mrp_display_icon.svg'), 'svg'),
    ],
    'l10n': [
        (os.path.join(REPO_ROOT, 'addons', 'account', 'static', 'description', 'l10n.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'account', 'static', 'description', 'l10n.png'), 'png'),
    ],
    'l10n_ar': [
        (os.path.join(REPO_ROOT, 'addons', 'l10n_ar', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'l10n_ar', 'static', 'description', 'icon.png'), 'png'),
    ],
    'l10n_ar_website_sale': [
        (os.path.join(REPO_ROOT, 'addons', 'l10n_ar_website_sale', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'addons', 'l10n_ar_website_sale', 'static', 'description', 'icon.png'), 'png'),
    ],
    'l10n_tw_reports': [
        (os.path.join(REPO_ROOT, 'enterprise', 'l10n_tw_reports', 'static', 'description', 'icon.svg'), 'svg'),
        (os.path.join(REPO_ROOT, 'enterprise', 'l10n_tw_reports', 'static', 'description', 'icon.png'), 'png'),
    ],
}

def resolve_glyph_for_module(module_name, authority_mapping):
    """Determine the canonical Phosphor duotone glyph name for a module."""
    if module_name in authority_mapping:
        return authority_mapping[module_name]
    if module_name in CORE_MODULE_MAPPING:
        return CORE_MODULE_MAPPING[module_name]
    for pattern, glyph in PATTERN_RULES:
        if re.search(pattern, module_name):
            return glyph
    return 'cube'

def ensure_source_glyph(glyph_name):
    """Ensure the canonical duotone SVG source file exists in tools/phosphor_duotone."""
    target_src = os.path.join(PRIMARY_CANONICAL_DIR, f"{glyph_name}-duotone.svg")
    if os.path.exists(target_src) and os.path.getsize(target_src) > 0:
        return target_src

    ext_src = os.path.join(EXTENDED_CANONICAL_DIR, f"{glyph_name}-duotone.svg")
    if os.path.exists(ext_src):
        os.makedirs(PRIMARY_CANONICAL_DIR, exist_ok=True)
        tmp_src = target_src + f".tmp.{os.getpid()}"
        shutil.copy2(ext_src, tmp_src)
        os.replace(tmp_src, target_src)
        return target_src

    # Fallback to cube
    cube_src = os.path.join(EXTENDED_CANONICAL_DIR, "cube-duotone.svg")
    if os.path.exists(cube_src):
        tmp_src = target_src + f".tmp.{os.getpid()}"
        shutil.copy2(cube_src, tmp_src)
        os.replace(tmp_src, target_src)
        return target_src
    raise FileNotFoundError(f"Glyph source not found for: {glyph_name}")

def compile_duotone_svg(src_svg_path):
    """Compile canonical Phosphor duotone SVG with #0B2E64, 256x256, opacity 0.2."""
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

    # Ensure opacity="0.2"
    if 'opacity="0.2"' not in content:
        content = content.replace('<path ', '<path opacity="0.2" ', 1)

    return content

def compile_png(compiled_svg):
    """Render genuine 256x256 PNG bytes from compiled SVG."""
    return cairosvg.svg2png(bytestring=compiled_svg.encode('utf-8'), output_width=256, output_height=256)

def find_all_modules():
    """Discover all modules with a __manifest__.py in search paths."""
    modules = {}
    for base in MODULE_SEARCH_PATHS:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            mod_path = os.path.join(base, name)
            if os.path.isdir(mod_path) and os.path.isfile(os.path.join(mod_path, '__manifest__.py')):
                if name not in modules:
                    modules[name] = []
                modules[name].append(mod_path)
    return modules

def plan_targets(modules, authority_mapping):
    """Plan all target icon files (svg and png) for all modules."""
    targets = [] # list of (module_name, glyph_name, target_path, kind)

    # 1. Special targets
    for key, spec_list in SPECIAL_TARGETS.items():
        glyph = resolve_glyph_for_module(key, authority_mapping)
        for target_path, kind in spec_list:
            targets.append((key, glyph, target_path, kind))

    # 2. General module targets
    for mod_name, paths in modules.items():
        if mod_name in SPECIAL_TARGETS:
            continue
        glyph = resolve_glyph_for_module(mod_name, authority_mapping)
        for mod_dir in paths:
            desc_dir = os.path.join(mod_dir, 'static', 'description')
            # If static/description exists or module has existing icon or is in authority mapping
            has_desc = os.path.isdir(desc_dir)
            has_svg = os.path.isfile(os.path.join(desc_dir, 'icon.svg'))
            has_png = os.path.isfile(os.path.join(desc_dir, 'icon.png'))
            is_mapped = (mod_name in authority_mapping or mod_name in CORE_MODULE_MAPPING)

            if has_desc or has_svg or has_png or is_mapped:
                svg_target = os.path.join(desc_dir, 'icon.svg')
                png_target = os.path.join(desc_dir, 'icon.png')
                targets.append((mod_name, glyph, svg_target, 'svg'))
                targets.append((mod_name, glyph, png_target, 'png'))

    # Deduplicate targets by path
    dedup = {}
    for item in targets:
        dedup[item[2]] = item
    return list(dedup.values())

def process_target(item):
    """Worker task: compile and write a single target file atomically."""
    mod_name, glyph, target_path, kind = item
    try:
        src_svg = ensure_source_glyph(glyph)
        compiled_svg = compile_duotone_svg(src_svg)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        tmp_target = target_path + f".tmp.{os.getpid()}"

        if kind == 'svg':
            # Check if identical to avoid unnecessary write
            if os.path.exists(target_path):
                with open(target_path, 'r', encoding='utf-8') as f:
                    if f.read() == compiled_svg:
                        return ('skip', target_path)
            with open(tmp_target, 'w', encoding='utf-8') as f:
                f.write(compiled_svg)
            os.replace(tmp_target, target_path)
            return ('write_svg', target_path)

        elif kind == 'png':
            png_bytes = compile_png(compiled_svg)
            if os.path.exists(target_path):
                with open(target_path, 'rb') as f:
                    if f.read() == png_bytes:
                        return ('skip', target_path)
            with open(tmp_target, 'wb') as f:
                f.write(png_bytes)
            os.replace(tmp_target, target_path)
            return ('write_png', target_path)

    except Exception as e:
        return ('error', f"{target_path}: {e}")

def update_database_icons():
    """Update ir_module_module icon column for all modules in DB."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5434,
            dbname='odoo20_dev',
            user='odoo',
            password='1NN0R1@2026'
        )
        cur = conn.cursor()
        print("\n[DB SYNC] Connected to PostgreSQL. Updating ir_module_module icons...")

        # 1. Fetch all modules
        cur.execute("SELECT name FROM ir_module_module;")
        rows = cur.fetchall()

        all_modules = find_all_modules()
        updated_canonical = 0
        updated_fallback = 0

        # Try to use canonical Odoo module loader for 100% fidelity
        use_odoo_loader = False
        try:
            import odoo.tools.config as config
            from odoo.modules.module import get_module_icon, initialize_sys_path
            conf_name = 'insilos.conf' if os.path.exists(os.path.join(REPO_ROOT, 'insilos.conf')) else 'odoo.conf'
            config.parse_config(['-c', os.path.join(REPO_ROOT, conf_name), '-d', 'odoo20_dev'])
            initialize_sys_path()
            use_odoo_loader = True
        except Exception:
            use_odoo_loader = False

        for (mname,) in rows:
            if use_odoo_loader:
                new_icon = get_module_icon(mname)
            else:
                has_svg = False
                if mname in all_modules:
                    for p in all_modules[mname]:
                        if os.path.isfile(os.path.join(p, 'static', 'description', 'icon.svg')):
                            has_svg = True
                            break
                new_icon = f"/{mname}/static/description/icon.svg" if has_svg else "/base/static/description/icon.svg"

            cur.execute("UPDATE ir_module_module SET icon = %s WHERE name = %s AND (icon IS NULL OR icon != %s);", (new_icon, mname, new_icon))
            if cur.rowcount > 0:
                if "/base/static/description/icon.svg" in new_icon:
                    updated_fallback += 1
                else:
                    updated_canonical += 1

        conn.commit()
        cur.close()
        conn.close()
        print(f"  ✓ DB update complete: {updated_canonical} module custom icons, {updated_fallback} fallback canonical SVGs.")
        return True
    except Exception as e:
        print(f"  ✗ DB sync error: {e}")
        return False

def check_integrity(targets):
    """Check integrity of all planned targets without modifying files."""
    errors = []
    checked = 0
    for mod_name, glyph, target_path, kind in targets:
        checked += 1
        if not os.path.exists(target_path):
            errors.append(f"Missing target: {os.path.relpath(target_path, REPO_ROOT)}")
            continue

        if kind == 'svg':
            with open(target_path, 'r', encoding='utf-8') as f:
                c = f.read()
            if 'viewBox="0 0 256 256"' not in c:
                errors.append(f"Invalid viewBox in: {os.path.relpath(target_path, REPO_ROOT)}")
            if '#0B2E64' not in c and 'currentColor' not in c:
                errors.append(f"Invalid color in: {os.path.relpath(target_path, REPO_ROOT)}")
            if 'opacity="0.2"' not in c:
                errors.append(f"Missing opacity='0.2' in: {os.path.relpath(target_path, REPO_ROOT)}")
            if '<image ' in c or 'data:image/' in c:
                errors.append(f"Embedded raster in SVG: {os.path.relpath(target_path, REPO_ROOT)}")

        elif kind == 'png':
            with open(target_path, 'rb') as f:
                header = f.read(8)
            if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                errors.append(f"Not a genuine PNG binary: {os.path.relpath(target_path, REPO_ROOT)}")

    return checked, errors

def main():
    parser = argparse.ArgumentParser(description="Auto Rebuild Module Icons according to Insilos signature")
    parser.add_argument('--check', action='store_true', help="Check integrity of icons only")
    parser.add_argument('--update-db', action='store_true', help="Sync database ir_module_module icons")
    parser.add_argument('--workers', type=int, default=os.cpu_count() or 4, help="Parallel worker threads/processes")
    args = parser.parse_args()

    authority_mapping = {}
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            authority_mapping = json.load(f)

    all_modules = find_all_modules()
    print(f"[REBUILD MODULE ICONS] Discovered {len(all_modules)} modules across search paths.")

    targets = plan_targets(all_modules, authority_mapping)
    print(f"[REBUILD MODULE ICONS] Planned {len(targets)} targets ({sum(1 for t in targets if t[3]=='svg')} SVG, {sum(1 for t in targets if t[3]=='png')} PNG).")

    if args.check:
        print("[CHECK] Validating icon targets integrity...")
        checked, errors = check_integrity(targets)
        if errors:
            print(f"  ✗ Found {len(errors)} issues across {checked} checked targets:")
            for err in errors[:25]:
                print(f"    - {err}")
            if len(errors) > 25:
                print(f"    ... and {len(errors) - 25} more.")
            sys.exit(1)
        else:
            print(f"  ✓ Integrity PASS: All {checked} targets meet the canonical Insilos signature.")
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
        for result in executor.map(process_target, targets):
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
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)

    # Update DB if requested or by default
    if args.update_db:
        update_database_icons()

    print("\n[SUCCESS] All module icons rebuilt according to Insilos signature.")

if __name__ == '__main__':
    main()
