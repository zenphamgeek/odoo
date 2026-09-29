#!/usr/bin/env python3
"""
M3 Zero-DDL Remediation Cleanup Script
Drops all auxiliary stored columns on core tables and drops the sap_movement_type table,
restoring 100% strict database schema invariance.
"""

import sys
import os

BASE_DIR = '/home/zen/O20'
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import insilos
from insilos.tools import config
config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'], setup_logging=False)
from odoo.orm.registry import Registry

columns_to_drop = [
    ('product_template', 'sap_material_type'),
    ('product_product', 'sap_material_type'),
    ('sale_order', 'sap_document_type'),
    ('sale_order', 'sap_state_label'),
    ('purchase_order', 'sap_document_type'),
    ('purchase_order', 'sap_state_label'),
    ('stock_picking', 'sap_delivery_type'),
    ('stock_picking', 'sap_movement_type'),
    ('stock_picking', 'sap_movement_desc'),
    ('stock_move', 'sap_bwart'),
    ('stock_move', 'sap_movement_type'),
    ('account_move', 'sap_billing_type'),
    ('account_analytic_account', 'co_type'),
    ('account_analytic_account', 'is_cost_center'),
    ('account_analytic_account', 'is_profit_center'),
    ('mrp_production', 'movement_type_issue'),
    ('mrp_production', 'movement_type_receipt'),
]

field_names = [
    'sap_material_type', 'sap_document_type', 'sap_state_label',
    'sap_delivery_type', 'sap_movement_type', 'sap_movement_desc',
    'sap_bwart', 'sap_billing_type', 'co_type', 'is_cost_center',
    'is_profit_center', 'movement_type_issue', 'movement_type_receipt'
]

def cleanup():
    print("=" * 80)
    print("M3 ZERO-DDL DATABASE SCHEMA REMEDIATION CLEANUP")
    print("=" * 80)
    
    registry = Registry('odoo20_dev')
    with registry.cursor() as cr:
        # 1. Drop columns on core tables
        for table, col in columns_to_drop:
            print(f"[*] Dropping column {table}.{col} ...")
            cr.execute(f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS "{col}" CASCADE;')

        # 2. Drop table sap_movement_type
        print("[*] Dropping table sap_movement_type ...")
        cr.execute('DROP TABLE IF EXISTS "sap_movement_type" CASCADE;')

        # 3. Clean up ir_model_fields store flag
        print("[*] Updating ir_model_fields to store = false ...")
        cr.execute("""
            UPDATE ir_model_fields
            SET store = false
            WHERE name = ANY(%s) OR model = 'sap.movement.type';
        """, (field_names,))

        # 4. Done
        # Commit changes
        cr.commit()
        print("[+] Schema cleanup successfully committed!")

    # Verify
    print("\n[*] Verifying database schema...")
    with registry.cursor() as cr:
        remaining_cols = 0
        tables = [
            "product_template", "product_product", "sale_order", "purchase_order",
            "stock_picking", "stock_move", "account_move", "account_analytic_account",
            "mrp_production"
        ]
        for t in tables:
            cr.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
                  AND (column_name LIKE 'sap_%%'
                       OR column_name IN ('co_type', 'is_cost_center', 'is_profit_center',
                                          'movement_type_issue', 'movement_type_receipt'))
            """, (t,))
            cols = [r[0] for r in cr.fetchall()]
            if cols:
                print(f"  [!] Table {t} still has columns: {cols}")
                remaining_cols += len(cols)
            else:
                print(f"  [OK] Table {t}: 0 auxiliary columns")

        cr.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'sap_movement_type'")
        tbls = [r[0] for r in cr.fetchall()]
        if tbls:
            print(f"  [!] Table sap_movement_type still exists: {tbls}")
        else:
            print("  [OK] Table sap_movement_type: 0 tables found")

        # Check ir_model_fields
        cr.execute("""
            SELECT count(*) FROM ir_model_fields
            WHERE (name = ANY(%s) OR model = 'sap.movement.type') AND store = true;
        """, (field_names,))
        stored_cnt = cr.fetchone()[0]
        print(f"  [OK] Stored ir_model_fields remaining: {stored_cnt}")

        if remaining_cols == 0 and not tbls and stored_cnt == 0:
            print("\n[SUCCESS] STRICT DATABASE SCHEMA INVARIANCE 100% RESTORED!")
            return True
        else:
            print("\n[FAILURE] Some columns/tables remain!")
            return False

if __name__ == '__main__':
    ok = cleanup()
    sys.exit(0 if ok else 1)
