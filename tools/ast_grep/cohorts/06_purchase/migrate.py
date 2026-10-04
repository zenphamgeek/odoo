#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 6 AUTOMATED MIGRATION ENGINE
Target: purchase.order      -> procurement.order      (DB Table: procurement_order)
        purchase.order.line -> procurement.order.line (DB Table: procurement_order_line)
IBM Enterprise Data Architecture Standard (Procurement & SCM)
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
    log("Verifying Database Updatable View Parity for Procurement Order & Lines...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count checks
    cr.execute("SELECT count(*) FROM purchase_order")
    cnt_po_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM procurement_order")
    cnt_po_tbl = cr.fetchone()[0]
    assert cnt_po_view == cnt_po_tbl, f"Order mismatch: {cnt_po_view} != {cnt_po_tbl}"
    log(f"Procurement Order parity confirmed: {cnt_po_tbl} records across table and view.", "OK")

    cr.execute("SELECT count(*) FROM purchase_order_line")
    cnt_pol_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM procurement_order_line")
    cnt_pol_tbl = cr.fetchone()[0]
    assert cnt_pol_view == cnt_pol_tbl, f"Order Line mismatch: {cnt_pol_view} != {cnt_pol_tbl}"
    log(f"Procurement Order Line parity confirmed: {cnt_pol_tbl} records across table and view.", "OK")

    # 2. Test INSERT through Updatable Views
    cr.execute("SELECT max(id) + 1 FROM procurement_order")
    test_po_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_po AS 
        SELECT * FROM procurement_order LIMIT 1;
        UPDATE _tmp_po SET id = %s, name = '__TEST_PROCUREMENT_ORDER__', state = 'draft';
        INSERT INTO purchase_order SELECT * FROM _tmp_po;
        DROP TABLE _tmp_po;
    """, (test_po_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM procurement_order WHERE id = %s", (test_po_id,))
    res_po = cr.fetchone()
    assert res_po is not None and res_po[0] == '__TEST_PROCUREMENT_ORDER__', "Failed to write-through purchase_order view!"
    log("Procurement Order write-through verified via purchase_order view.", "OK")

    cr.execute("SELECT max(id) + 1 FROM procurement_order_line")
    test_pol_id = cr.fetchone()[0] or 9999
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_pol AS 
        SELECT * FROM procurement_order_line LIMIT 1;
        UPDATE _tmp_pol SET id = %s, order_id = %s, name = '__TEST_PROCUREMENT_LINE__';
        INSERT INTO purchase_order_line SELECT * FROM _tmp_pol;
        DROP TABLE _tmp_pol;
    """, (test_pol_id, test_po_id))
    
    cr.execute("SELECT name FROM procurement_order_line WHERE id = %s", (test_pol_id,))
    res_pol = cr.fetchone()
    assert res_pol is not None and res_pol[0] == '__TEST_PROCUREMENT_LINE__', "Failed to write-through purchase_order_line view!"
    log("Procurement Order Line write-through verified via purchase_order_line view.", "OK")

    # Clean up test records
    cr.execute("DELETE FROM procurement_order_line WHERE id = %s", (test_pol_id,))
    cr.execute("DELETE FROM procurement_order WHERE id = %s", (test_po_id,))
    conn.close()
    log("Bidirectional write-through verified cleanly for both Order and Lines.", "OK")

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
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 6 MIGRATION RUNNER")
    print("   Domains: purchase.order      ──▶ procurement.order")
    print("            purchase.order.line ──▶ procurement.order.line")
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
        log("🎉 COHORT 6 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    except Exception as e:
        log(f"Migration error encountered: {e}", "ERR")
        log("Triggering automated instant rollback...", "WARN")
        run_db_down()
        sys.exit(1)

if __name__ == "__main__":
    main()
