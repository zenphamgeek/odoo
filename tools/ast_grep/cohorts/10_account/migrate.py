#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 10 AUTOMATED MIGRATION ENGINE
Target: account.move      -> finance.journal.entry (DB Table: finance_journal_entry)
        account.move.line -> finance.journal.line  (DB Table: finance_journal_line)
IBM Enterprise Data Architecture Standard (Financial Accounting — BDW)
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
    log("Verifying Database Updatable View Parity for Journal Entries & Items...")
    conn = psycopg2.connect(**DB_PARAMS)
    cr = conn.cursor()
    
    # 1. Count checks
    cr.execute("SELECT count(*) FROM account_move")
    cnt_am_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM finance_journal_entry")
    cnt_am_tbl = cr.fetchone()[0]
    assert cnt_am_view == cnt_am_tbl, f"Journal Entry mismatch: {cnt_am_view} != {cnt_am_tbl}"
    log(f"Journal Entry parity confirmed: {cnt_am_tbl} records across table and view.", "OK")

    cr.execute("SELECT count(*) FROM account_move_line")
    cnt_aml_view = cr.fetchone()[0]
    cr.execute("SELECT count(*) FROM finance_journal_line")
    cnt_aml_tbl = cr.fetchone()[0]
    assert cnt_aml_view == cnt_aml_tbl, f"Journal Item mismatch: {cnt_aml_view} != {cnt_aml_tbl}"
    log(f"Journal Item parity confirmed: {cnt_aml_tbl} records across table and view.", "OK")

    # 2. Test INSERT through Updatable Views
    cr.execute("SELECT max(id) + 1 FROM finance_journal_entry")
    test_am_id = cr.fetchone()[0] or 9999
    
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_am AS 
        SELECT * FROM finance_journal_entry LIMIT 1;
        UPDATE _tmp_am SET id = %s, name = '__TEST_FINANCE_JOURNAL_ENTRY__', state = 'draft';
        INSERT INTO account_move SELECT * FROM _tmp_am;
        DROP TABLE _tmp_am;
    """, (test_am_id,))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM finance_journal_entry WHERE id = %s", (test_am_id,))
    res_am = cr.fetchone()
    assert res_am is not None and res_am[0] == '__TEST_FINANCE_JOURNAL_ENTRY__', "Failed to write-through account_move view!"
    log("Journal Entry write-through verified via account_move view.", "OK")

    cr.execute("SELECT max(id) + 1 FROM finance_journal_line")
    test_aml_id = cr.fetchone()[0] or 9999
    cr.execute("""
        CREATE TEMPORARY TABLE _tmp_aml AS 
        SELECT * FROM finance_journal_line LIMIT 1;
        UPDATE _tmp_aml SET id = %s, move_id = %s, name = '__TEST_FINANCE_JOURNAL_LINE__';
        INSERT INTO account_move_line SELECT * FROM _tmp_aml;
        DROP TABLE _tmp_aml;
    """, (test_aml_id, test_am_id))
    
    # Verify in physical sovereign table
    cr.execute("SELECT name FROM finance_journal_line WHERE id = %s", (test_aml_id,))
    res_aml = cr.fetchone()
    assert res_aml is not None and res_aml[0] == '__TEST_FINANCE_JOURNAL_LINE__', "Failed to write-through account_move_line view!"
    log("Journal Item write-through verified via account_move_line view.", "OK")

    # Clean up test rows
    cr.execute("DELETE FROM finance_journal_line WHERE id = %s", (test_aml_id,))
    cr.execute("DELETE FROM finance_journal_entry WHERE id = %s", (test_am_id,))
    conn.close()
    log("Bidirectional write-through verified cleanly for both Journal Entry and Items.", "OK")

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
    print("🚀 INSILOS SOVEREIGN HARD FORK — COHORT 10 MIGRATION RUNNER")
    print("   Domains: account.move      ──▶ finance.journal.entry")
    print("            account.move.line ──▶ finance.journal.line")
    print("================================================================================")

    if len(sys.argv) < 2 or sys.argv[1] not in ("up", "down", "check"):
        print("Usage: python3 migrate.py [up|down|check]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "up":
        run_db_up()
        verify_db_parity()
        verify_server_boot()
        log("🎉 COHORT 10 SOVEREIGN MIGRATION VERIFIED 100% PASS!", "OK")
    elif action == "down":
        run_db_down()
        verify_server_boot()
    elif action == "check":
        verify_db_parity()
        verify_server_boot()

if __name__ == "__main__":
    main()
