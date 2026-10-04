#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 7 AUTOMATED MIGRATION ENGINE
Target: sale.order      -> order.header (DB Table: order_header)
        sale.order.line -> order.line   (DB Table: order_line)
IBM Enterprise Data Architecture Standard (Sales & Orders — OMS)
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
    log("Verifying Database Updatable View Parity for Order Header & Lines...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count checks
    cr.execute("SELECT count(*) FROM sale_order")
    cnt_so_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM order_header")
    cnt_so_tbl = cr.fetchone()[0]
    assert cnt_so_view == cnt_so_tbl, f"Order mismatch: {cnt_so_view} != {cnt_so_tbl}"
    log(f"Order Header parity confirmed: {cnt_so_tbl} records across table and view.", "OK")

    cr.execute("SELECT count(*) FROM sale_order_line")
    cnt_sol_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM order_line")
    cnt_sol_tbl = cr.fetchone()[0]
    assert cnt_sol_view == cnt_sol_tbl, f"Order Line mismatch: {cnt_sol_view} != {cnt_sol_tbl}"
    log(f"Order Line parity confirmed: {cnt_sol_tbl} records across table and view.", "OK")

    # 2. Test INSERT through Updatable Views
    cr.execute("SELECT max(id) + 1 FROM order_header")
    test_so_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_so AS 
        SELECT * FROM order_header LIMIT 1;
        UPDATE _tmp_so SET id = %s, name = '__TEST_ORDER_HEADER__', state = 'draft';
        INSERT INTO sale_order SELECT * FROM _tmp_so;
        DROP TABLE _tmp_so;
    """, (test_so_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM order_header WHERE id = %s", (test_so_id,))
    res_so = cr.fetchone()
    assert res_so is not None and res_so[0] == '__TEST_ORDER_HEADER__', "Failed to write-through sale_order view!"
    log("Order Header write-through verified via sale_order view.", "OK")

    cr.execute("SELECT max(id) + 1 FROM order_line")
    test_sol_id = cr.fetchone()[0] or 9999
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_sol AS 
        SELECT * FROM order_line LIMIT 1;
        UPDATE _tmp_sol SET id = %s, order_id = %s, name = '__TEST_ORDER_LINE__';
        INSERT INTO sale_order_line SELECT * FROM _tmp_sol;
        DROP TABLE _tmp_sol;
    """, (test_sol_id, test_so_id))
    
    cr.execute("SELECT name FROM order_line WHERE id = %s", (test_sol_id,))
    res_sol = cr.fetchone()
    assert res_sol is not None and res_sol[0] == '__TEST_ORDER_LINE__', "Failed to write-through sale_order_line view!"
    log("Order Line write-through verified via sale_order_line view.", "OK")

    # Clean up test records
    cr.execute("DELETE FROM order_line WHERE id = %s", (test_sol_id,))
    cr.execute("DELETE FROM order_header WHERE id = %s", (test_so_id,))
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
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 7 MIGRATION RUNNER")
    print("   Domains: sale.order      ──▶ order.header")
    print("            sale.order.line ──▶ order.line")
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
        log("🎉 COHORT 7 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    except Exception as e:
        log(f"Migration error encountered: {e}", "ERR")
        log("Triggering automated instant rollback...", "WARN")
        run_db_down()
        sys.exit(1)

if __name__ == "__main__":
    main()
