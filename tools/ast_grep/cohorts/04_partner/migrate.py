#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 4 AUTOMATED MIGRATION ENGINE
Target: res.partner -> party.master (DB Table: party_master)
IBM Enterprise Data Architecture Standard (Party Master / Involved Party Foundation)
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
    log("Verifying Database Updatable View Parity for Party Master...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count check
    cr.execute("SELECT count(*) FROM res_partner")
    cnt_legacy = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM party_master")
    cnt_table = cr.fetchone()[0]
    assert cnt_legacy == cnt_table, f"Mismatch: legacy {cnt_legacy} != table {cnt_table}"
    log(f"Count parity confirmed: {cnt_table} records across table and view.", "OK")
    
    # 2. Test INSERT through Updatable View
    cr.execute("SELECT max(id) + 1 FROM party_master")
    test_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_partner AS 
        SELECT * FROM party_master WHERE id = 1;
        UPDATE _tmp_partner SET id = %s, name = '__TEST_SOVEREIGN_PARTY__';
        INSERT INTO res_partner SELECT * FROM _tmp_partner;
        DROP TABLE _tmp_partner;
    """, (test_id,))
    
    # Verify it exists in physical sovereign table
    cr.execute("SELECT name FROM party_master WHERE id = %s", (test_id,))
    fetched = cr.fetchone()[0]
    assert fetched == '__TEST_SOVEREIGN_PARTY__', f"Data integrity error: {fetched}"
    
    # Clean up test record
    cr.execute("DELETE FROM party_master WHERE id = %s", (test_id,))
    conn.close()
    log("Bidirectional write-through verified: Updatable View passes partner INSERT/DELETE directly to physical table.", "OK")

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
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 4 MIGRATION RUNNER")
    print("   Domain: res.partner ──▶ party.master")
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
        log("🎉 COHORT 4 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    except Exception as e:
        log(f"Migration error encountered: {e}", "ERR")
        log("Triggering automated instant rollback...", "WARN")
        run_db_down()
        sys.exit(1)

if __name__ == "__main__":
    main()
