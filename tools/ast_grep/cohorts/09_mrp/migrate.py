#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 9 AUTOMATED MIGRATION ENGINE
Target: mrp.production -> manufacturing.order (DB Table: manufacturing_order)
        mrp.bom        -> manufacturing.bom   (DB Table: manufacturing_bom)
IBM Enterprise Data Architecture Standard (Manufacturing & MES)
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
    log("Verifying Database Updatable View Parity for Manufacturing Orders & BOMs...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count checks
    cr.execute("SELECT count(*) FROM mrp_production")
    cnt_mo_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM manufacturing_order")
    cnt_mo_tbl = cr.fetchone()[0]
    assert cnt_mo_view == cnt_mo_tbl, f"Manufacturing Order mismatch: {cnt_mo_view} != {cnt_mo_tbl}"
    log(f"Manufacturing Order parity confirmed: {cnt_mo_tbl} records across table and view.", "OK")

    cr.execute("SELECT count(*) FROM mrp_bom")
    cnt_bom_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM manufacturing_bom")
    cnt_bom_tbl = cr.fetchone()[0]
    assert cnt_bom_view == cnt_bom_tbl, f"BOM mismatch: {cnt_bom_view} != {cnt_bom_tbl}"
    log(f"Manufacturing BOM parity confirmed: {cnt_bom_tbl} records across table and view.", "OK")

    # 2. Test INSERT through Updatable Views
    cr.execute("SELECT max(id) + 1 FROM manufacturing_order")
    test_mo_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_mo AS 
        SELECT * FROM manufacturing_order LIMIT 1;
        UPDATE _tmp_mo SET id = %s, name = '__TEST_MANUFACTURING_ORDER__', state = 'draft';
        INSERT INTO mrp_production SELECT * FROM _tmp_mo;
        DROP TABLE _tmp_mo;
    """, (test_mo_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM manufacturing_order WHERE id = %s", (test_mo_id,))
    res_mo = cr.fetchone()
    assert res_mo is not None and res_mo[0] == '__TEST_MANUFACTURING_ORDER__', "Failed to write-through mrp_production view!"
    log("Manufacturing Order write-through verified via mrp_production view.", "OK")

    cr.execute("SELECT max(id) + 1 FROM manufacturing_bom")
    test_bom_id = cr.fetchone()[0] or 9999
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_bom AS 
        SELECT * FROM manufacturing_bom LIMIT 1;
        UPDATE _tmp_bom SET id = %s, code = '__TEST_BOM__', active = true;
        INSERT INTO mrp_bom SELECT * FROM _tmp_bom;
        DROP TABLE _tmp_bom;
    """, (test_bom_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT code FROM manufacturing_bom WHERE id = %s", (test_bom_id,))
    res_bom = cr.fetchone()
    assert res_bom is not None and res_bom[0] == '__TEST_BOM__', "Failed to write-through mrp_bom view!"
    log("Manufacturing BOM write-through verified via mrp_bom view.", "OK")

    # Clean up test rows
    cr.execute("DELETE FROM manufacturing_order WHERE id = %s", (test_mo_id,))
    cr.execute("DELETE FROM manufacturing_bom WHERE id = %s", (test_bom_id,))
    conn.close()
    log("Bidirectional write-through verified cleanly for both Production Order and BOM.", "OK")

def verify_server_boot():
    log("Executing Pre-flight Server Boot Verification...")
    cmd = [
        str(REPO_ROOT / ".venv" / "bin" / "python"),
        str(REPO_ROOT / "insilos-bin"),
        "-c", "insilos.conf",
        "-d", "odoo20_dev",
        "--stop-after-init"
    ]
    res = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        log(f"Pre-flight server boot FAILED with code {res.returncode}!", "ERR")
        print(res.stderr[-2000:])
        sys.exit(res.returncode)
    log("Server boot & registry preload PASSED with exit code 0.", "OK")

def main():
    print("================================================================================")
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 9 MIGRATION RUNNER")
    print("   Domains: mrp.production ──▶ manufacturing.order")
    print("            mrp.bom        ──▶ manufacturing.bom")
    print("================================================================================")

    if len(sys.argv) < 2 or sys.argv[1] not in ("up", "down", "check"):
        print("Usage: python3 migrate.py [up|down|check]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "up":
        run_db_up()
        verify_db_parity()
        verify_server_boot()
        log("🎉 COHORT 9 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    elif action == "down":
        run_db_down()
        verify_server_boot()
    elif action == "check":
        verify_db_parity()
        verify_server_boot()

if __name__ == "__main__":
    main()
