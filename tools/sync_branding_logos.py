#!/usr/bin/env python3
"""
tools/sync_branding_logos.py
Synchronizes and verifies canonical Insilos branding logos and favicons across all modules.
Complies with doc/HARD_REFACTOR_PART_A_BRANDING_ASSETS_TAXONOMY.md.
"""

import argparse
import os
import shutil
import sys
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BRANDING_DIR = os.path.join(REPO_ROOT, 'branding')
WEB_IMG_DIR = os.path.join(REPO_ROOT, 'addons', 'web', 'static', 'img')

REQUIRED_SOURCES = {
    'h-logo-light': os.path.join(BRANDING_DIR, 'h-logo-light.svg'),
    'h-logo-dark': os.path.join(BRANDING_DIR, 'h-logo-dark.svg'),
    'icon-dark': os.path.join(BRANDING_DIR, 'icon-dark.svg'),
}

TARGET_MAPPINGS = [
    # (source_key, target_rel_path)
    ('h-logo-light', os.path.join(WEB_IMG_DIR, 'logo.svg')),
    ('h-logo-light', os.path.join(WEB_IMG_DIR, 'insilos_logo.svg')),
    ('h-logo-light', os.path.join(WEB_IMG_DIR, 'odoo_logo.svg')),
    ('h-logo-dark', os.path.join(WEB_IMG_DIR, 'logo_dark.svg')),
    ('h-logo-dark', os.path.join(WEB_IMG_DIR, 'insilos_logo_dark.svg')),
    ('h-logo-dark', os.path.join(WEB_IMG_DIR, 'odoo_logo_dark.svg')),
    ('icon-dark', os.path.join(WEB_IMG_DIR, 'favicon.svg')),
    ('icon-dark', os.path.join(WEB_IMG_DIR, 'insilos-icon.svg')),
    ('icon-dark', os.path.join(WEB_IMG_DIR, 'odoo-icon.svg')),
]

def check_branding_sources():
    errors = []
    print("[CHECK] Verifying canonical branding sources...")
    for key, path in REQUIRED_SOURCES.items():
        if not os.path.exists(path):
            errors.append(f"Missing required canonical source: {path}")
        else:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '<svg' not in content:
                errors.append(f"File {path} is not a valid SVG")
            if key == 'h-logo-light' and '#004455' not in content:
                errors.append(f"{path} does not contain required canonical light color #004455")
            if (key == 'h-logo-light' or key == 'h-logo-dark') and '2333 463' not in content:
                errors.append(f"{path} does not have required viewBox '0 0 2333 463'")
            if key == 'icon-dark' and '1000 1000' not in content:
                errors.append(f"{path} does not have required viewBox '0 0 1000 1000'")

    if errors:
        print("[FAIL] Source verification failed:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("  ✓ All canonical sources in branding/ exist and meet specification.")
    return True

def sync_logos(write=False):
    if not check_branding_sources():
        sys.exit(1)

    os.makedirs(WEB_IMG_DIR, exist_ok=True)
    print(f"\n[{'SYNC' if write else 'CHECK'}] Evaluating target deployment...")

    all_matched = True
    for src_key, target_path in TARGET_MAPPINGS:
        src_path = REQUIRED_SOURCES[src_key]
        with open(src_path, 'r', encoding='utf-8') as f:
            src_data = f.read()

        target_exists = os.path.exists(target_path)
        if target_exists:
            with open(target_path, 'r', encoding='utf-8') as f:
                target_data = f.read()
            matches = (src_data == target_data)
        else:
            matches = False

        if not matches:
            all_matched = False
            if write:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(src_data)
                print(f"  → Wrote: {os.path.relpath(target_path, REPO_ROOT)}")
            else:
                print(f"  ✗ Out of sync: {os.path.relpath(target_path, REPO_ROOT)}")
        else:
            print(f"  ✓ Up to date: {os.path.relpath(target_path, REPO_ROOT)}")

    # Sync Favicons across all subsystems
    src_favicon_png = os.path.join(BRANDING_DIR, 'favicon.png')
    target_favicon_ico = os.path.join(WEB_IMG_DIR, 'favicon.ico')
    target_favicon_png = os.path.join(WEB_IMG_DIR, 'favicon.png')
    target_odoo_ios = os.path.join(WEB_IMG_DIR, 'odoo-icon-ios.png')
    target_odoo_192 = os.path.join(WEB_IMG_DIR, 'odoo-icon-192x192.png')
    target_odoo_512 = os.path.join(WEB_IMG_DIR, 'odoo-icon-512x512.png')
    pos_favicon_ico = os.path.join(REPO_ROOT, 'addons', 'point_of_sale', 'static', 'src', 'img', 'favicon.ico')
    iot_favicon_png = os.path.join(REPO_ROOT, 'addons', 'iot_drivers', 'static', 'img', 'favicon.png')
    wl_favicon_png = os.path.join(REPO_ROOT, 'addons', 'website_links', 'static', 'img', 'default_favicon.png')

    if os.path.exists(src_favicon_png):
        if write:
            shutil.copy2(src_favicon_png, target_favicon_png)
            shutil.copy2(src_favicon_png, target_odoo_ios)
            # Create proper favicon.ico from PNG
            img = Image.open(src_favicon_png).convert('RGBA')
            img.save(target_favicon_ico, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
            print(f"  → Generated: {os.path.relpath(target_favicon_ico, REPO_ROOT)} and {os.path.relpath(target_favicon_png, REPO_ROOT)}")
            
            # PWA icons (192x192, 512x512)
            icon_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
            icon_192.save(target_odoo_192, 'PNG')
            print(f"  → Generated PWA icon: {os.path.relpath(target_odoo_192, REPO_ROOT)}")
            
            icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
            icon_512.save(target_odoo_512, 'PNG')
            print(f"  → Generated PWA icon: {os.path.relpath(target_odoo_512, REPO_ROOT)}")

            # Subsystem favicons
            shutil.copy2(target_favicon_ico, pos_favicon_ico)
            print(f"  → Synced POS favicon: {os.path.relpath(pos_favicon_ico, REPO_ROOT)}")
            
            fav_100 = img.resize((100, 100), Image.Resampling.LANCZOS)
            fav_100.save(iot_favicon_png, 'PNG')
            print(f"  → Synced IoT favicon: {os.path.relpath(iot_favicon_png, REPO_ROOT)}")
            
            fav_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
            fav_16.save(wl_favicon_png, 'PNG')
            print(f"  → Synced website_links favicon: {os.path.relpath(wl_favicon_png, REPO_ROOT)}")
        else:
            for p in [target_favicon_ico, target_favicon_png, target_odoo_192, target_odoo_512, pos_favicon_ico, iot_favicon_png, wl_favicon_png]:
                if not os.path.exists(p):
                    all_matched = False
                    print(f"  ✗ Missing: {os.path.relpath(p, REPO_ROOT)}")
                else:
                    print(f"  ✓ Up to date: {os.path.relpath(p, REPO_ROOT)}")

    # Sync Horizontal Logos and Variants
    src_hlogo_png = os.path.join(BRANDING_DIR, 'h_logo.png')
    pos_logo_png = os.path.join(REPO_ROOT, 'addons', 'point_of_sale', 'static', 'src', 'img', 'logo.png')
    base_company_logo_png = os.path.join(REPO_ROOT, 'odoo', 'addons', 'base', 'static', 'img', 'res_company_logo.png')

    if os.path.exists(src_hlogo_png):
        if write:
            shutil.copy2(src_hlogo_png, os.path.join(WEB_IMG_DIR, 'logo.png'))
            shutil.copy2(src_hlogo_png, os.path.join(WEB_IMG_DIR, 'logo2.png'))
            shutil.copy2(src_hlogo_png, os.path.join(WEB_IMG_DIR, 'logo_inverse_white_206px.png'))
            print(f"  → Synced PNG logo variants to {os.path.relpath(WEB_IMG_DIR, REPO_ROOT)}")

            # Base company logo 450x120
            im_h = Image.open(src_hlogo_png).convert('RGBA')
            ratio = im_h.width / im_h.height
            target_h = 100
            target_w = int(target_h * ratio)
            if target_w > 430:
                target_w = 430
                target_h = int(target_w / ratio)
            resized_h = im_h.resize((target_w, target_h), Image.Resampling.LANCZOS)
            canvas_base = Image.new('RGBA', (450, 120), (0, 0, 0, 0))
            canvas_base.paste(resized_h, ((450 - target_w) // 2, (120 - target_h) // 2), resized_h)
            canvas_base.save(base_company_logo_png, 'PNG')
            print(f"  → Generated company default logo: {os.path.relpath(base_company_logo_png, REPO_ROOT)}")

            # POS logo 621x196
            target_pos_h = 160
            target_pos_w = int(target_pos_h * ratio)
            if target_pos_w > 590:
                target_pos_w = 590
                target_pos_h = int(target_pos_w / ratio)
            resized_pos = im_h.resize((target_pos_w, target_pos_h), Image.Resampling.LANCZOS)
            canvas_pos = Image.new('RGBA', (621, 196), (0, 0, 0, 0))
            canvas_pos.paste(resized_pos, ((621 - target_pos_w) // 2, (196 - target_pos_h) // 2), resized_pos)
            canvas_pos.save(pos_logo_png, 'PNG')
        else:
            # Sign portal badges and QR logos
            sign_badge = os.path.join(REPO_ROOT, 'enterprise', 'sign', 'static', 'img', 'odoo_signed.png')
            sign_insilos_badge = os.path.join(REPO_ROOT, 'enterprise', 'sign', 'static', 'img', 'insilos_signed.png')
            qr_logo_account = os.path.join(REPO_ROOT, 'addons', 'account', 'static', 'src', 'img', 'Odoo_logo_O.svg')
            qr_logo_sub = os.path.join(REPO_ROOT, 'addons', 'mysubscription', 'static', 'src', 'img', 'odoo_o.svg')
            for p in [os.path.join(WEB_IMG_DIR, 'logo.png'), base_company_logo_png, pos_logo_png, sign_badge, sign_insilos_badge, qr_logo_account, qr_logo_sub]:
                if not os.path.exists(p):
                    all_matched = False
                    print(f"  ✗ Missing: {os.path.relpath(p, REPO_ROOT)}")
                else:
                    print(f"  ✓ Up to date: {os.path.relpath(p, REPO_ROOT)}")

    if not write and not all_matched:
        print("\n[FAIL] Target files are missing or out of sync with canonical branding sources. Run with --write to sync.")
        return False

    print("\n[PASS] All branding logo assets are verified and synchronized.")
    return True

def update_database_branding():
    """Sync company logo, colors, and website favicon directly in PostgreSQL via Odoo ORM."""
    print("\n[DB SYNC] Connecting to Odoo ORM to synchronize branding records...")
    import odoo
    from odoo.modules.registry import Registry
    from odoo.orm.fields_binary import BinaryBytes

    config_path = os.path.join(REPO_ROOT, 'odoo.conf')
    odoo.tools.config.parse_config(['-c', config_path, '-d', 'odoo20_dev'])
    
    with Registry('odoo20_dev').cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # 1. Update company logo and colors
        logo_path = os.path.join(BRANDING_DIR, 'h_logo.png')
        with open(logo_path, 'rb') as f:
            logo_bytes = BinaryBytes(f.read(), filename='logo.png')
            
        company = env['res.company'].browse(1)
        if company.exists():
            company.write({
                'logo': logo_bytes,
                'email_secondary_color': '#004455',
                'primary_color': '#004455',
                'secondary_color': '#004455',
            })
            print(f"  ✓ Updated res.company '{company.name}': logo & primary colors -> #004455")
            
        # 2. Update website favicon
        fav_path = os.path.join(BRANDING_DIR, 'favicon.png')
        with open(fav_path, 'rb') as f:
            fav_bytes = BinaryBytes(f.read(), filename='favicon.png')
            
        website = env['website'].browse(1)
        if website.exists():
            website.write({
                'favicon': fav_bytes,
            })
            print(f"  ✓ Updated website '{website.name}' favicon -> Insilos canonical")
            
        cr.commit()
    print("  ✓ Database branding synchronization completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Synchronize Insilos branding logos and assets")
    parser.add_argument('--check', action='store_true', help="Check sources and targets without writing")
    parser.add_argument('--write', action='store_true', help="Write canonical files to targets")
    parser.add_argument('--update-db', action='store_true', help="Synchronize database company logo and website favicon")
    args = parser.parse_args()

    if args.check:
        success = sync_logos(write=False)
        sys.exit(0 if success else 1)
    elif args.write:
        sync_logos(write=True)
        if args.update_db:
            update_database_branding()
        sys.exit(0)
    elif args.update_db:
        update_database_branding()
        sys.exit(0)
    else:
        # Default behavior: run check
        success = sync_logos(write=False)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
