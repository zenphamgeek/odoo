#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/sync_app_icons_db.py
===========================
Idempotent Database Synchronization Engine for Insilos App Icons.
Synchronizes ir.ui.menu web_icon_data attachments directly from disk files.
Guarantees Strict Database Schema Invariance (zero DDL/column mutations).
"""

import argparse
import hashlib
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def compute_disk_file_hash(rel_path):
    """Resolve comma-separated module,path to absolute path and compute SHA1."""
    if not rel_path or len(rel_path.split(',')) != 2:
        return None, None
    module, path = rel_path.split(',')
    
    search_dirs = [
        os.path.join(REPO_ROOT, 'addons', module),
        os.path.join(REPO_ROOT, 'enterprise', module),
        os.path.join(REPO_ROOT, 'odoo', 'addons', module),
    ]
    for d in search_dirs:
        full_path = os.path.join(d, path)
        if os.path.isfile(full_path):
            with open(full_path, 'rb') as f:
                content = f.read()
            sha1 = hashlib.sha1(content).hexdigest()
            return full_path, sha1
    return None, None

def main():
    parser = argparse.ArgumentParser(description="Synchronize Insilos App Icons in Database")
    parser.add_argument('--verify', action='store_true', help="Verify DB attachments match disk icons without writing")
    parser.add_argument('--config', default=os.path.join(REPO_ROOT, 'insilos.conf'), help="Config file path")
    parser.add_argument('--database', default='odoo20_dev', help="Database name")
    args = parser.parse_args()

    print("================================================================================")
    print("🚀 INSILOS APP ICONS DATABASE SYNCHRONIZATION ENGINE")
    print(f"   Mode: {'VERIFY ONLY' if args.verify else 'AUTOMATIC SYNC'} | Database: {args.database}")
    print("================================================================================\n")

    import odoo
    odoo.tools.config.parse_config(['-c', args.config, '-d', args.database])
    registry = odoo.modules.registry.Registry(args.database)

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])
        print(f"[DISCOVERY] Found {len(menus)} root menu items with web_icon definitions.")

        out_of_sync = []
        synced_count = 0

        for m in menus:
            full_path, disk_sha1 = compute_disk_file_hash(m.web_icon)
            if not full_path:
                print(f"  ⚠ Warning: File not found on disk for menu {m.id} ({m.name}): {m.web_icon}")
                continue

            # Check attachment checksum
            attach = env['ir.attachment'].search([
                ('res_model', '=', 'ir.ui.menu'),
                ('res_field', '=', 'web_icon_data'),
                ('res_id', '=', m.id)
            ], limit=1)

            db_sha1 = attach.checksum if attach else None

            if db_sha1 != disk_sha1:
                out_of_sync.append((m, full_path, db_sha1, disk_sha1))
            else:
                synced_count += 1

        print(f"\n[AUDIT] In-sync icons: {synced_count}/{len(menus)}")
        print(f"[AUDIT] Out-of-sync icons: {len(out_of_sync)}/{len(menus)}")

        if args.verify:
            if out_of_sync:
                print(f"\n[FAIL] Found {len(out_of_sync)} icons out of sync with disk:")
                for m, p, db_s, disk_s in out_of_sync:
                    print(f"  - Menu {m.id} ({m.name}): DB checksum={db_s} != Disk checksum={disk_s} ({p})")
                sys.exit(1)
            else:
                print("\n🎉 [PASS] All database icon attachments are 100% synchronized with disk files!")
                sys.exit(0)

        # Synchronize out-of-sync icons
        if out_of_sync:
            print(f"\n[SYNC] Synchronizing {len(out_of_sync)} icons to PostgreSQL filestore...")
            for m, p, db_s, disk_s in out_of_sync:
                print(f"  ▶ Updating menu {m.id} ({m.name}): {m.web_icon}")
                m.write({'web_icon': m.web_icon})
            env.cr.commit()
            print("  ✓ Database transaction committed successfully!")
        else:
            print("\n✓ No database synchronization needed. All icons already up to date.")

        print("\n================================================================================")
        print("🎉 SYNCHRONIZATION COMPLETED SUCCESSFULLY (Zero Schema Mutations)")
        print("================================================================================")

if __name__ == '__main__':
    main()
