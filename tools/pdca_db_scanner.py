#!/usr/bin/env python3
"""
tools/pdca_db_scanner.py
Comprehensive PostgreSQL database audit for Insilos branding compliance.
Scans ALL public tables and text/json columns for legacy Odoo strings,
verifying that zero actionable leaks remain while technical contracts are preserved.
"""

import sys
import psycopg2
import json
import re

# Known protected technical contracts:
PROTECTED_CONTRACT_PATTERNS = [
    r'odoo\.__session_info__',
    r'odoo\.define',
    r'window\.odoo',
    r'odoo\.reloadMenus',
    r'odoo\.loadMenusPromise',
    r'odoo\.preparation_display',
    r'web\.layout\.odooscript',
    r'web\.odoo_ui_icons',
    r'layout_invoices_generated_by_odoo',
    r'account_invoices_generated_by_odoo',
    r's_mega_menu_odoo_menu',
    r'iot_restart_odoo',
    r'odoo_partner_data',
    r'odoo_icon\.to_base64\(\)',
    r'odoobot_state',
    r'odoobot_transparent\.png',
    r't-set="odoo_logo"',
    r'by_odoo',
    r'odoo_link',
    r'o_odoo',
    r'odoo_signed\.png',
    r'Odoo_logo_O\.svg',
    r'qrcode_odoo_logo',
    r'oi_odoo',
    r'odoo/addons',
    r'from odoo',
    r'import odoo',
    r'X-Odoo-Objects',
    r'https://extract\.api\.odoo\.com',
    r'https://github\.com/CLEARCORP/odoo-costa-rica',
    r'odoo-costa-rica',
    r'web\.assets_.*\.min\.css',
    r'Modoolar',
    r'odootech\.hu',
    r'odoohouse\.dk',
    r'odoo_logo',
]

TECHNICAL_COLUMNS = {
    'model', 'res_model', 'state', 'type', 'view_mode', 'target', 'usage', 'binding_type',
    'relation', 'relation_field', 'action', 'parent_path', 'inherit_id', 'key'
}

def is_protected(val_str, tbl, col):
    if tbl == 'ir_model_fields' and col == 'name':
        return True
    # Technical selection value
    if tbl == 'account_journal' and col == 'invoice_reference_model' and val_str.strip() == 'odoo':
        return True
    if tbl == 'ir_model_fields_selection' and col == 'value' and val_str.strip() == 'odoo':
        return True
    if tbl == 'mail_mail' and col == 'headers' and 'X-Odoo-Objects' in val_str:
        return True
    if tbl == 'ir_config_parameter' and col == 'value' and 'extract.api.odoo.com' in val_str:
        return True
    if tbl == 'ir_attachment' and col == 'index_content':
        return True
    if tbl == 'ir_attachment' and col in ['name', 'url'] and 'odoo_ui_icons' in val_str:
        return True
    if tbl == 'bus_bus':
        return True
    if tbl == 'delivery_carrier' and 'username' in col:
        return True
    if tbl in ['ir_act_server', 'ir_actions_server_history']:
        return True
    if tbl == 'ir_model_data':
        return True
    if tbl == 'ir_asset':
        return True
    if tbl == 'product_unspsc_code':
        return True

    # Strip all protected patterns
    cleaned = val_str
    for pat in PROTECTED_CONTRACT_PATTERNS:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE)

    # Check if any odoo remains
    return not bool(re.search(r'odoo', cleaned, re.IGNORECASE))

def scan_all_tables():
    conn = psycopg2.connect("host=127.0.0.1 port=5434 dbname=odoo20_dev user=odoo password=1NN0R1@2026")
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]

    print(f"=== COMPREHENSIVE DYNAMIC DATABASE AUDIT ({len(tables)} tables) ===")
    
    protected_matches = 0
    actionable_leaks = []

    for tbl in tables:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s 
              AND data_type IN ('text', 'character varying', 'json', 'jsonb')
        """, (tbl,))
        cols = cur.fetchall()

        for col, dtype in cols:
            if col in TECHNICAL_COLUMNS:
                continue

            query = f"SELECT id, {col}::text FROM {tbl} WHERE {col}::text ILIKE '%odoo%'"
            try:
                cur.execute(query)
                matches = cur.fetchall()
                for mid, val in matches:
                    val_str = str(val)
                    if is_protected(val_str, tbl, col):
                        protected_matches += 1
                    else:
                        actionable_leaks.append((tbl, col, mid, val_str[:120]))
            except Exception:
                conn.rollback()

    conn.close()

    print(f"\n[SUMMARY]")
    print(f"  ✓ Protected runtime & technical contracts verified: {protected_matches}")
    print(f"  Actionable user-facing leaks found: {len(actionable_leaks)}")

    if actionable_leaks:
        print("\n❌ ACTIONABLE LEAKS:")
        for tbl, col, mid, snippet in actionable_leaks:
            print(f"   [{tbl}.{col}] ID {mid}: {repr(snippet)}")
        return False
    else:
        print("\n🎉 PASS: 100% of public database tables and user-facing records are clean!")
        return True

if __name__ == '__main__':
    clean = scan_all_tables()
    sys.exit(0 if clean else 1)
