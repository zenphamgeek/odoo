#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 8 AUTOMATED MIGRATION ENGINE
Target: stock.picking -> logistics.transfer (DB Table: logistics_transfer)
        stock.move    -> logistics.movement (DB Table: logistics_movement)
IBM Enterprise Data Architecture Standard (Logistics & Inventory)
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
    log("Verifying Database Updatable View Parity for Logistics Transfer & Movements...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count checks
    cr.execute("SELECT count(*) FROM stock_picking")
    cnt_sp_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM logistics_transfer")
    cnt_sp_tbl = cr.fetchone()[0]
    assert cnt_sp_view == cnt_sp_tbl, f"Transfer mismatch: {cnt_sp_view} != {cnt_sp_tbl}"
    log(f"Logistics Transfer parity confirmed: {cnt_sp_tbl} records across table and view.", "OK")

    cr.execute("SELECT count(*) FROM stock_move")
    cnt_sm_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM logistics_movement")
    cnt_sm_tbl = cr.fetchone()[0]
    assert cnt_sm_view == cnt_sm_tbl, f"Movement mismatch: {cnt_sm_view} != {cnt_sm_tbl}"
    log(f"Logistics Movement parity confirmed: {cnt_sm_tbl} records across table and view.", "OK")

    # 2. Test INSERT through Updatable Views
    cr.execute("SELECT max(id) + 1 FROM logistics_transfer")
    test_sp_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_sp AS 
        SELECT * FROM logistics_transfer LIMIT 1;
        UPDATE _tmp_sp SET id = %s, name = '__TEST_LOGISTICS_TRANSFER__', state = 'draft';
        INSERT INTO stock_picking SELECT * FROM _tmp_sp;
        DROP TABLE _tmp_sp;
    """, (test_sp_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM logistics_transfer WHERE id = %s", (test_sp_id,))
    res_sp = cr.fetchone()
    assert res_sp is not None and res_sp[0] == '__TEST_LOGISTICS_TRANSFER__', "Failed to write-through stock_picking view!"
    log("Logistics Transfer write-through verified via stock_picking view.", "OK")

    cr.execute("SELECT max(id) + 1 FROM logistics_movement")
    test_sm_id = cr.fetchone()[0] or 9999
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_sm AS 
        SELECT * FROM logistics_movement LIMIT 1;
        UPDATE _tmp_sm SET id = %s, picking_id = %s, reference = '__TEST_LOGISTICS_MOVEMENT__', state = 'draft';
        INSERT INTO stock_move SELECT * FROM _tmp_sm;
        DROP TABLE _tmp_sm;
    """, (test_sm_id, test_sp_id))
    
    # Verify in physical sovereign table
    cr.execute("SELECT reference FROM logistics_movement WHERE id = %s", (test_sm_id,))
    res_sm = cr.fetchone()
    assert res_sm is not None and res_sm[0] == '__TEST_LOGISTICS_MOVEMENT__', "Failed to write-through stock_move view!"
    log("Logistics Movement write-through verified via stock_move view.", "OK")

    # Clean up test rows
    cr.execute("DELETE FROM logistics_movement WHERE id = %s", (test_sm_id,))
    cr.execute("DELETE FROM logistics_transfer WHERE id = %s", (test_sp_id,))
    conn.close()
    log("Bidirectional write-through verified cleanly for both Transfer and Movements.", "OK")

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
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 8 MIGRATION RUNNER")
    print("   Domains: stock.picking ──▶ logistics.transfer")
    print("            stock.move    ──▶ logistics.movement")
    print("================================================================================")

    if len(sys.argv) < 2 or sys.argv[1] not in ("up", "down", "check"):
        print("Usage: python3 migrate.py [up|down|check]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "up":
        run_db_up()
        verify_db_parity()
        verify_server_boot()
        log("🎉 COHORT 8 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    elif action == "down":
        run_db_down()
        verify_server_boot()
    elif action == "check":
        verify_db_parity()
        verify_server_boot()

if __name__ == "__main__":
    main()
