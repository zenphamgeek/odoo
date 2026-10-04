#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 5 AUTOMATED MIGRATION ENGINE
Target: product.template -> catalog.item (DB Table: catalog_item)
        product.product  -> catalog.sku  (DB Table: catalog_sku)
IBM Enterprise Data Architecture Standard (Item Master & Stock Keeping Unit)
================================================================================
"""
import sys
import subprocess
import psycopg2
from pathlib import Path

REPO_ROOT = Path("/home/zen/O20")
COHORT_DIR = Path(__file__).resolve().parent
DB_PARAMS = {
    "host": "localhost",
    "port": 5434,
    "dbname": "odoo20_dev",
    "user": "odoo",
    "password": "1NN0R1@2026"
}

def log(msg, level="INFO"):
    prefixes = {"INFO": "  •", "OK": "[✓]", "WARN": "[!]", "ERR": "[✖]"}
    print(f"{prefixes.get(level, '   ')} {msg}")

def execute_sql_file(file_path):
    sql_text = Path(file_path).read_text(encoding="utf-8")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cr = conn.cursor()
    cr.execute(sql_text)
    conn.close()

def run_db_up():
    log("Applying Phase 1 & 2: Database Migration & Metadata Injection (up.sql)...")
    execute_sql_file(COHORT_DIR / "up.sql")
    log("Database schema renamed and Updatable Compatibility Views established.", "OK")

def run_db_down():
    log("Applying Rollback: Restoring legacy schema and metadata (down.sql)...", "WARN")
    execute_sql_file(COHORT_DIR / "down.sql")
    log("Rollback completed successfully.", "OK")

def verify_db_parity():
    log("Verifying Database Updatable View Parity for Catalog Item & SKU...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count checks
    cr.execute("SELECT count(*) FROM product_template")
    cnt_tmpl_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM catalog_item")
    cnt_tmpl_tbl = cr.fetchone()[0]
    assert cnt_tmpl_view == cnt_tmpl_tbl, f"Template mismatch: {cnt_tmpl_view} != {cnt_tmpl_tbl}"
    log(f"Template parity confirmed: {cnt_tmpl_tbl} records across table and view.", "OK")

    cr.execute("SELECT count(*) FROM product_product")
    cnt_prod_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM catalog_sku")
    cnt_prod_tbl = cr.fetchone()[0]
    assert cnt_prod_view == cnt_prod_tbl, f"Product SKU mismatch: {cnt_prod_view} != {cnt_prod_tbl}"
    log(f"SKU parity confirmed: {cnt_prod_tbl} records across table and view.", "OK")

    # 2. Test INSERT through Updatable Views
    cr.execute("SELECT max(id) + 1 FROM catalog_item")
    test_tmpl_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_item AS 
        SELECT * FROM catalog_item LIMIT 1;
        UPDATE _tmp_item SET id = %s, name = '{"en_US": "__TEST_CATALOG_ITEM__"}';
        INSERT INTO product_template SELECT * FROM _tmp_item;
        DROP TABLE _tmp_item;
    """, (test_tmpl_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM catalog_item WHERE id = %s", (test_tmpl_id,))
    res_tmpl = cr.fetchone()
    assert res_tmpl is not None, "Failed to write-through product_template view!"
    log("Catalog Item write-through verified via product_template view.", "OK")

    cr.execute("SELECT max(id) + 1 FROM catalog_sku")
    test_sku_id = cr.fetchone()[0] or 9999
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_sku AS 
        SELECT * FROM catalog_sku LIMIT 1;
        UPDATE _tmp_sku SET id = %s, product_tmpl_id = %s, default_code = '__TEST_SKU__';
        INSERT INTO product_product SELECT * FROM _tmp_sku;
        DROP TABLE _tmp_sku;
    """, (test_sku_id, test_tmpl_id))
    
    cr.execute("SELECT default_code FROM catalog_sku WHERE id = %s", (test_sku_id,))
    res_sku = cr.fetchone()
    assert res_sku is not None and res_sku[0] == '__TEST_SKU__', "Failed to write-through product_product view!"
    log("Catalog SKU write-through verified via product_product view.", "OK")

    # Clean up test records
    cr.execute("DELETE FROM catalog_sku WHERE id = %s", (test_sku_id,))
    cr.execute("DELETE FROM catalog_item WHERE id = %s", (test_tmpl_id,))
    conn.close()
    log("Bidirectional write-through verified cleanly for both Item and SKU.", "OK")

def verify_server_boot():
    log("Executing Pre-flight Server Boot Verification...")
    cmd = [
        str(REPO_ROOT / ".venv" / "bin" / "python"),
        str(REPO_ROOT / "insilos-bin"),
        "-c", "insilos.conf",
        "-d", "odoo20_dev",
        "--stop-after-init"
    ]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if proc.returncode == 0:
        log("Server boot & registry preload PASSED with exit code 0.", "OK")
        return True
    else:
        log(f"Server boot FAILED with code {proc.returncode}!", "ERR")
        print(proc.stderr[-1500:])
        return False

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    print("================================================================================")
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 5 MIGRATION RUNNER")
    print("   Domains: product.template ──▶ catalog.item")
    print("            product.product  ──▶ catalog.sku")
    print("================================================================================")

    if action == "down":
        run_db_down()
        return

    try:
        run_db_up()
        verify_db_parity()
        success = verify_server_boot()
        if not success:
            raise RuntimeError("Server boot verification failed!")
        log("🎉 COHORT 5 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    except Exception as e:
        log(f"Migration error encountered: {e}", "ERR")
        log("Triggering automated instant rollback...", "WARN")
        run_db_down()
        sys.exit(1)

if __name__ == "__main__":
    main()
