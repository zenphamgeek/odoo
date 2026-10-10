#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/challenger2_empirical_stress_tests.py
=============================================
Empirical Referential Integrity, Double-Entry Balance, and Stress Test Harness
Executed by Challenger 2 (Stress & Referential Integrity Challenger).

Direct PostgreSQL Read-Only Assertions:
1. Zero Orphan Records & Referential Integrity Scans across all core models.
2. Financial Double-Entry Golden Equation & Per-Move Balance Invariance.
3. Strict Parity Mode Verification (innoria_prod) -> Expect Exit Code 0, 0.00% Data Loss.
4. Superset Parity Mode Verification (innoria.insilos.com --allow-superset) -> Expect Exit Code 0, 0.00% Data Loss.
5. Adversarial Strict Mode Rejection on Superset Database -> Expect Exit Code 1.
6. Exact Mathematical Data Loss Rate Calculation (0.0000%).
7. Edge Case Mining: Soft-deleted/inactive rows, UTF-8 diacritics, decimal precision.
"""

import argparse
import decimal
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

# Connection Defaults
DB_HOST = "127.0.0.1"
DB_PORT = 5434
DB_USER = "odoo"
DB_PASS = "1NN0R1@2026"

SOURCE_DB = "odoo20_dev"
STRICT_TARGET_DB = "innoria_prod"
SUPERSET_TARGET_DB = "innoria.insilos.com"


def get_db_connection(dbname: str):
    """Establish strictly read-only connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=dbname
    )
    conn.set_session(readonly=True)
    return conn


# ==============================================================================
# TEST 1: RAW POSTGRESQL ORPHAN & REFERENTIAL INTEGRITY SCANS
# ==============================================================================
def run_referential_integrity_scans(conn, dbname: str) -> Dict[str, Any]:
    print(f"\n--- [TEST 1] Referential Integrity & Orphan Scans on '{dbname}' ---")
    cur = conn.cursor()

    queries = {
        # Model 1: Contact (res.partner)
        "res_partner_broken_parent": """
            SELECT count(*)
            FROM res_partner p
            LEFT JOIN res_partner parent ON p.parent_id = parent.id
            WHERE p.parent_id IS NOT NULL AND parent.id IS NULL;
        """,
        "res_partner_bank_orphan_partner": """
            SELECT count(*)
            FROM res_partner_bank b
            LEFT JOIN res_partner p ON b.partner_id = p.id
            WHERE b.partner_id IS NOT NULL AND p.id IS NULL;
        """,
        "res_partner_orphan_commercial_partner": """
            SELECT count(*)
            FROM res_partner p
            LEFT JOIN res_partner cp ON p.commercial_partner_id = cp.id
            WHERE p.commercial_partner_id IS NOT NULL AND cp.id IS NULL;
        """,

        # Model 2: Commercial (sale.order & sale.order.line)
        "sale_order_line_orphan_order": """
            SELECT count(*)
            FROM sale_order_line sol
            LEFT JOIN sale_order so ON sol.order_id = so.id
            WHERE sol.order_id IS NULL OR so.id IS NULL;
        """,
        "sale_order_orphan_partner": """
            SELECT count(*)
            FROM sale_order so
            LEFT JOIN res_partner p ON so.partner_id = p.id
            WHERE so.partner_id IS NOT NULL AND p.id IS NULL;
        """,
        "sale_order_line_orphan_product": """
            SELECT count(*)
            FROM sale_order_line sol
            LEFT JOIN product_product pp ON sol.product_id = pp.id
            WHERE sol.product_id IS NOT NULL AND pp.id IS NULL;
        """,

        # Model 3: Financial Accounting (account.move & account.move.line)
        "account_move_line_orphan_move": """
            SELECT count(*)
            FROM account_move_line aml
            LEFT JOIN account_move am ON aml.move_id = am.id
            WHERE aml.move_id IS NULL OR am.id IS NULL;
        """,
        "account_move_line_orphan_account": """
            SELECT count(*)
            FROM account_move_line aml
            LEFT JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.account_id IS NOT NULL AND aa.id IS NULL;
        """,
        "account_move_line_broken_partner": """
            SELECT count(*)
            FROM account_move_line aml
            LEFT JOIN res_partner p ON aml.partner_id = p.id
            WHERE aml.partner_id IS NOT NULL AND p.id IS NULL;
        """,
        "account_move_broken_partner": """
            SELECT count(*)
            FROM account_move am
            LEFT JOIN res_partner p ON am.partner_id = p.id
            WHERE am.partner_id IS NOT NULL AND p.id IS NULL;
        """,

        # Model 4: HR & Payroll (hr.employee & hr.version & hr.department)
        "hr_employee_broken_manager": """
            SELECT count(*)
            FROM hr_employee e
            LEFT JOIN hr_employee mgr ON e.parent_id = mgr.id
            WHERE e.parent_id IS NOT NULL AND mgr.id IS NULL;
        """,
        "hr_employee_broken_version": """
            SELECT count(*)
            FROM hr_employee e
            LEFT JOIN hr_version v ON e.current_version_id = v.id
            WHERE e.current_version_id IS NOT NULL AND v.id IS NULL;
        """,
        "hr_version_orphan_employee": """
            SELECT count(*)
            FROM hr_version v
            LEFT JOIN hr_employee e ON v.employee_id = e.id
            WHERE v.employee_id IS NOT NULL AND e.id IS NULL;
        """,
        "hr_version_orphan_department": """
            SELECT count(*)
            FROM hr_version v
            LEFT JOIN hr_department d ON v.department_id = d.id
            WHERE v.department_id IS NOT NULL AND d.id IS NULL;
        """,
        "hr_department_broken_parent": """
            SELECT count(*)
            FROM hr_department d
            LEFT JOIN hr_department parent ON d.parent_id = parent.id
            WHERE d.parent_id IS NOT NULL AND parent.id IS NULL;
        """,
        "hr_department_broken_manager": """
            SELECT count(*)
            FROM hr_department d
            LEFT JOIN hr_employee mgr ON d.manager_id = mgr.id
            WHERE d.manager_id IS NOT NULL AND mgr.id IS NULL;
        """,

        # Model 5: Payroll Salary Rules & Structures
        "hr_salary_rule_orphan_category": """
            SELECT count(*)
            FROM hr_salary_rule r
            LEFT JOIN hr_salary_rule_category c ON r.category_id = c.id
            WHERE r.category_id IS NOT NULL AND c.id IS NULL;
        """,
    }

    # Optional checks if tables exist (crm.lead, project.task, hr.expense)
    optional_checks = {
        "crm_lead_orphan_partner": ("crm_lead", """
            SELECT count(*)
            FROM crm_lead l
            LEFT JOIN res_partner p ON l.partner_id = p.id
            WHERE l.partner_id IS NOT NULL AND p.id IS NULL;
        """),
        "project_task_orphan_project": ("project_task", """
            SELECT count(*)
            FROM project_task t
            LEFT JOIN project_project p ON t.project_id = p.id
            WHERE t.project_id IS NOT NULL AND p.id IS NULL;
        """),
        "hr_expense_orphan_employee": ("hr_expense", """
            SELECT count(*)
            FROM hr_expense x
            LEFT JOIN hr_employee e ON x.employee_id = e.id
            WHERE x.employee_id IS NOT NULL AND e.id IS NULL;
        """),
    }

    results = {}
    total_orphans = 0

    for name, q in queries.items():
        cur.execute(q)
        cnt = cur.fetchone()[0]
        results[name] = cnt
        total_orphans += cnt
        status = "CLEAN (0)" if cnt == 0 else f"CORRUPT ({cnt} orphans)"
        print(f"  • {name:<42}: {status}")

    for name, (tbl, q) in optional_checks.items():
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (tbl,))
        exists = cur.fetchone()[0]
        if exists:
            cur.execute(q)
            cnt = cur.fetchone()[0]
            results[name] = cnt
            total_orphans += cnt
            status = "CLEAN (0)" if cnt == 0 else f"CORRUPT ({cnt} orphans)"
            print(f"  • [OPTIONAL] {name:<31}: {status}")
        else:
            results[name] = "N/A (table not installed)"
            print(f"  • [OPTIONAL] {name:<31}: Table '{tbl}' not present in schema")

    cur.close()
    passed = (total_orphans == 0)
    print(f"  => Total Orphans Found: {total_orphans} | Result: {'PASS' if passed else 'FAIL'}")
    return {
        "database": dbname,
        "total_orphans": total_orphans,
        "details": results,
        "pass": passed,
    }


# ==============================================================================
# TEST 2: RAW POSTGRESQL DOUBLE-ENTRY BALANCE & FINANCIAL INVARIANTS
# ==============================================================================
def run_double_entry_balance_checks(conn, dbname: str) -> Dict[str, Any]:
    print(f"\n--- [TEST 2] Double-Entry Ledger Balance Equations on '{dbname}' ---")
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Posted moves aggregate balance
    q_posted = """
        SELECT count(*) as line_count,
               coalesce(sum(debit), 0.0) as total_debit,
               coalesce(sum(credit), 0.0) as total_credit,
               coalesce(sum(debit) - sum(credit), 0.0) as discrepancy,
               coalesce(sum(balance), 0.0) as total_balance
        FROM account_move_line
        WHERE parent_state = 'posted';
    """
    cur.execute(q_posted)
    posted_res = cur.fetchone()

    # 2. Individual move balance check
    q_unbalanced = """
        SELECT move_id,
               count(*) as lines,
               sum(debit) as d,
               sum(credit) as c,
               sum(debit) - sum(credit) as diff
        FROM account_move_line
        WHERE parent_state = 'posted'
        GROUP BY move_id
        HAVING abs(sum(debit) - sum(credit)) > 0.0001;
    """
    cur.execute(q_unbalanced)
    unbalanced_moves = cur.fetchall()

    # 3. Check balance column invariant: balance == (debit - credit)
    q_balance_col = """
        SELECT count(*)
        FROM account_move_line
        WHERE abs(balance - (debit - credit)) > 0.0001;
    """
    cur.execute(q_balance_col)
    balance_col_mismatch = cur.fetchone()["count"]

    # 4. Check move header states and totals
    q_moves = """
        SELECT count(*) as total_moves,
               count(*) FILTER (WHERE state = 'posted') as posted_moves,
               count(*) FILTER (WHERE state != 'posted') as unposted_moves,
               coalesce(sum(amount_total), 0.0) as total_invoiced,
               coalesce(sum(amount_residual), 0.0) as total_residual
        FROM account_move;
    """
    cur.execute(q_moves)
    moves_res = cur.fetchone()

    # 5. Check commercial sales orders
    q_so = """
        SELECT count(*) as order_count,
               coalesce(sum(amount_untaxed), 0.0) as untaxed,
               coalesce(sum(amount_tax), 0.0) as tax,
               coalesce(sum(amount_total), 0.0) as total
        FROM sale_order;
    """
    cur.execute(q_so)
    so_res = cur.fetchone()

    q_sol = """
        SELECT count(*) as line_count,
               coalesce(sum(product_uom_qty), 0.0) as total_qty,
               coalesce(sum(price_subtotal), 0.0) as subtotal
        FROM sale_order_line;
    """
    cur.execute(q_sol)
    sol_res = cur.fetchone()

    cur.close()

    disc = decimal.Decimal(str(posted_res["discrepancy"]))
    tot_debit = decimal.Decimal(str(posted_res["total_debit"]))
    tot_credit = decimal.Decimal(str(posted_res["total_credit"]))
    tot_so = decimal.Decimal(str(so_res["total"]))
    sol_subtotal = decimal.Decimal(str(sol_res["subtotal"]))

    pass_balance = (disc == decimal.Decimal("0.00") and len(unbalanced_moves) == 0 and balance_col_mismatch == 0)
    pass_commercial = (tot_so == decimal.Decimal("20127500000.00") and sol_subtotal == tot_so)

    print(f"  • Total Posted Lines: {posted_res['line_count']}")
    print(f"  • Total Debit:        {tot_debit:,.2f}")
    print(f"  • Total Credit:       {tot_credit:,.2f}")
    print(f"  • Net Discrepancy:    {disc:.4f} VNĐ (Assert == 0.00 VNĐ -> {'PASS' if disc == 0 else 'FAIL'})")
    print(f"  • Unbalanced Moves:   {len(unbalanced_moves)} (Assert == 0 -> {'PASS' if len(unbalanced_moves) == 0 else 'FAIL'})")
    print(f"  • Balance Invariant:  {balance_col_mismatch} (balance == debit - credit -> {'PASS' if balance_col_mismatch == 0 else 'FAIL'})")
    print(f"  • Moves Invoiced:     ₫{decimal.Decimal(str(moves_res['total_invoiced'])):,.2f} | Residual: ₫{decimal.Decimal(str(moves_res['total_residual'])):,.2f}")
    print(f"  • Sales Orders:       {so_res['order_count']} orders, {sol_res['line_count']} lines | Total: ₫{tot_so:,.2f} (Assert ₫20.1275B -> {'PASS' if pass_commercial else 'FAIL'})")

    overall_pass = pass_balance and pass_commercial
    print(f"  => Financial & Ledger Test Result: {'PASS' if overall_pass else 'FAIL'}")

    return {
        "database": dbname,
        "posted_lines": posted_res["line_count"],
        "total_debit": float(tot_debit),
        "total_credit": float(tot_credit),
        "discrepancy": float(disc),
        "unbalanced_moves_count": len(unbalanced_moves),
        "balance_invariant_mismatches": balance_col_mismatch,
        "moves_count": moves_res["total_moves"],
        "posted_moves": moves_res["posted_moves"],
        "amount_total_invoiced": float(moves_res["total_invoiced"]),
        "amount_residual": float(moves_res["total_residual"]),
        "sales_order_total": float(tot_so),
        "sales_lines_subtotal": float(sol_subtotal),
        "pass": overall_pass,
    }


# ==============================================================================
# TEST 3: RAW POSTGRESQL DATA LOSS RATE & DIRECT ID SET COMPARISON
# ==============================================================================
def run_data_loss_rate_validation(conn_src, conn_tgt, tgt_name: str, allow_superset: bool = False) -> Dict[str, Any]:
    print(f"\n--- [TEST 3] Direct ID Set Analysis & Data Loss Rate (Source vs '{tgt_name}') ---")
    tables_to_check = [
        "res_partner",
        "res_partner_bank",
        "hr_employee",
        "hr_version",
        "hr_department",
        "hr_salary_rule",
        "hr_payroll_structure",
        "hr_payslip",
        "sale_order",
        "sale_order_line",
        "account_move",
        "account_move_line",
    ]

    cur_src = conn_src.cursor()
    cur_tgt = conn_tgt.cursor()

    total_src_records = 0
    total_missing_records = 0
    table_stats = {}

    for tbl in tables_to_check:
        cur_src.execute(f"SELECT id FROM {tbl} ORDER BY id;")
        src_ids = set(r[0] for r in cur_src.fetchall())
        cur_tgt.execute(f"SELECT id FROM {tbl} ORDER BY id;")
        tgt_ids = set(r[0] for r in cur_tgt.fetchall())

        src_count = len(src_ids)
        tgt_count = len(tgt_ids)
        total_src_records += src_count

        missing_in_target = src_ids - tgt_ids
        missing_count = len(missing_in_target)
        total_missing_records += missing_count

        extra_in_target = tgt_ids - src_ids
        extra_count = len(extra_in_target)

        if allow_superset:
            tbl_pass = (missing_count == 0)
        else:
            tbl_pass = (missing_count == 0 and extra_count == 0)

        status_str = "PASS" if tbl_pass else "FAIL"
        superset_str = f"(+{extra_count} extra)" if extra_count > 0 else ""
        print(f"  • {tbl:<22}: src={src_count:>3}, tgt={tgt_count:>3}, missing={missing_count:>2} {superset_str} -> {status_str}")

        table_stats[tbl] = {
            "source_count": src_count,
            "target_count": tgt_count,
            "missing_in_target": missing_count,
            "extra_in_target": extra_count,
            "missing_ids": list(missing_in_target),
            "pass": tbl_pass,
        }

    cur_src.close()
    cur_tgt.close()

    loss_rate = (total_missing_records / total_src_records * 100.0) if total_src_records > 0 else 0.0
    loss_rate_exact = round(loss_rate, 4)

    print(f"  => Total Source Records: {total_src_records}")
    print(f"  => Total Missing in Target: {total_missing_records}")
    print(f"  => Exact Data Loss Rate: {loss_rate_exact:.4f}% (Assert == 0.0000% -> {'PASS' if loss_rate_exact == 0.0 else 'FAIL'})")

    all_tables_pass = all(s["pass"] for s in table_stats.values())
    return {
        "target": tgt_name,
        "allow_superset": allow_superset,
        "total_source_records": total_src_records,
        "total_missing_records": total_missing_records,
        "data_loss_rate_pct": loss_rate_exact,
        "table_stats": table_stats,
        "pass": (loss_rate_exact == 0.0 and (all_tables_pass or allow_superset and total_missing_records == 0)),
    }


# ==============================================================================
# TEST 4: CLI AUDIT ENGINE EXECUTION TESTS
# ==============================================================================
def run_cli_audit_tests() -> Dict[str, Any]:
    print("\n--- [TEST 4] Execution of tools/audit_erp_data_parity.py ---")
    cli_results = {}

    # Test 4.1: Strict Mode against innoria_prod
    cmd_strict = [
        "python3", "tools/audit_erp_data_parity.py",
        "--source", SOURCE_DB,
        "--target", STRICT_TARGET_DB,
        "--output-md", "/tmp/challenger2_strict_report.md",
        "--output-json", "/tmp/challenger2_strict_manifest.json",
        "--verbose"
    ]
    print("  Executing Test 4.1: Strict Mode against innoria_prod...")
    t0 = time.perf_counter()
    res_strict = subprocess.run(cmd_strict, capture_output=True, text=True)
    t_strict = time.perf_counter() - t0
    pass_strict = (res_strict.returncode == 0 and "100.00% Parity Confirmed. Zero Data Loss" in res_strict.stdout)
    print(f"    Exit Code: {res_strict.returncode} | Time: {t_strict:.2f}s | Result: {'PASS' if pass_strict else 'FAIL'}")
    cli_results["strict_mode"] = {
        "command": " ".join(cmd_strict),
        "exit_code": res_strict.returncode,
        "time_seconds": round(t_strict, 3),
        "pass": pass_strict,
    }

    # Test 4.2: Superset Mode against innoria.insilos.com with --allow-superset
    cmd_superset = [
        "python3", "tools/audit_erp_data_parity.py",
        "--source", SOURCE_DB,
        "--target", SUPERSET_TARGET_DB,
        "--allow-superset",
        "--output-md", "/tmp/challenger2_superset_report.md",
        "--output-json", "/tmp/challenger2_superset_manifest.json",
        "--verbose"
    ]
    print("  Executing Test 4.2: Superset Mode against innoria.insilos.com with --allow-superset...")
    t0 = time.perf_counter()
    res_superset = subprocess.run(cmd_superset, capture_output=True, text=True)
    t_superset = time.perf_counter() - t0
    pass_superset = (res_superset.returncode == 0 and "100.00% Parity Confirmed. Zero Data Loss" in res_superset.stdout)
    print(f"    Exit Code: {res_superset.returncode} | Time: {t_superset:.2f}s | Result: {'PASS' if pass_superset else 'FAIL'}")
    cli_results["superset_mode_allowed"] = {
        "command": " ".join(cmd_superset),
        "exit_code": res_superset.returncode,
        "time_seconds": round(t_superset, 3),
        "pass": pass_superset,
    }

    # Test 4.3: Adversarial Rejection: Superset target WITHOUT --allow-superset
    cmd_reject = [
        "python3", "tools/audit_erp_data_parity.py",
        "--source", SOURCE_DB,
        "--target", SUPERSET_TARGET_DB,
        "--output-md", "/tmp/challenger2_reject_report.md",
        "--output-json", "/tmp/challenger2_reject_manifest.json",
        "--verbose"
    ]
    print("  Executing Test 4.3 (Adversarial): Superset target WITHOUT --allow-superset (Expect Failure)...")
    t0 = time.perf_counter()
    res_reject = subprocess.run(cmd_reject, capture_output=True, text=True)
    t_reject = time.perf_counter() - t0
    # Must exit non-zero (exit code 1) because table count mismatches in strict mode
    pass_reject = (res_reject.returncode != 0 and "COUNT MISMATCH" in res_reject.stdout)
    print(f"    Exit Code: {res_reject.returncode} (Expected 1) | Time: {t_reject:.2f}s | Result: {'PASS' if pass_reject else 'FAIL'}")
    cli_results["adversarial_superset_rejection"] = {
        "command": " ".join(cmd_reject),
        "exit_code": res_reject.returncode,
        "time_seconds": round(t_reject, 3),
        "detected_count_mismatch": "COUNT MISMATCH" in res_reject.stdout,
        "pass": pass_reject,
    }

    overall_cli_pass = pass_strict and pass_superset and pass_reject
    return {
        "tests": cli_results,
        "pass": overall_cli_pass,
    }


# ==============================================================================
# TEST 5: ADVERSARIAL EDGE CASE MINING
# ==============================================================================
def run_edge_case_mining(conn_src, conn_tgt) -> Dict[str, Any]:
    print("\n--- [TEST 5] Adversarial Edge Case Mining ---")
    cur_src = conn_src.cursor(cursor_factory=RealDictCursor)
    cur_tgt = conn_tgt.cursor(cursor_factory=RealDictCursor)

    edge_results = {}

    # Edge Case 1: Inactive / Soft-deleted rows
    cur_src.execute("SELECT count(*) as cnt FROM res_partner WHERE active = false;")
    inact_p_src = cur_src.fetchone()["cnt"]
    cur_tgt.execute("SELECT count(*) as cnt FROM res_partner WHERE active = false;")
    inact_p_tgt = cur_tgt.fetchone()["cnt"]
    edge_results["inactive_partners"] = {
        "src": inact_p_src,
        "tgt": inact_p_tgt,
        "match": (inact_p_src == inact_p_tgt),
    }
    print(f"  • Inactive Partners: src={inact_p_src}, tgt={inact_p_tgt} -> {'PASS' if inact_p_src == inact_p_tgt else 'FAIL'}")

    # Edge Case 2: UTF-8 Diacritics Invariance on Key Names
    sample_names = [
        "Tổng Công ty Tân Cảng Sài Gòn (Saigon Newport - SNP)",
        "Công ty CP Thép Hòa Phát Dung Quất",
        "Công ty CP Cơ Khí Chế Tạo V-LIFT",
        "Công ty CP Tập đoàn Hòa Phát - Chi nhánh Thép & Ống thép Hưng Yên",
    ]
    cur_src.execute("SELECT id, name FROM res_partner WHERE name IN %s;", (tuple(sample_names),))
    src_names = {r["name"]: r["id"] for r in cur_src.fetchall()}
    cur_tgt.execute("SELECT id, name FROM res_partner WHERE name IN %s;", (tuple(sample_names),))
    tgt_names = {r["name"]: r["id"] for r in cur_tgt.fetchall()}
    utf8_match = (src_names == tgt_names)
    edge_results["utf8_diacritics"] = {
        "expected_names_count": len(sample_names),
        "source_found": len(src_names),
        "target_found": len(tgt_names),
        "match": utf8_match,
    }
    print(f"  • UTF-8 Vietnamese Diacritics: {len(tgt_names)}/{len(sample_names)} exact matches -> {'PASS' if utf8_match else 'FAIL'}")

    # Edge Case 3: Decimal Precision & Fractional Values
    cur_tgt.execute("""
        SELECT count(*) as fraction_lines
        FROM account_move_line
        WHERE (debit != round(debit, 2)) OR (credit != round(credit, 2));
    """)
    fraction_lines = cur_tgt.fetchone()["fraction_lines"]
    edge_results["decimal_precision_cents"] = {
        "fractional_sub_cent_lines": fraction_lines,
        "clean": (fraction_lines == 0),
    }
    print(f"  • Sub-cent Fractional Discrepancies: {fraction_lines} -> {'PASS' if fraction_lines == 0 else 'FAIL'}")

    # Edge Case 4: Currency ID Invariance
    cur_tgt.execute("SELECT DISTINCT currency_id FROM sale_order;")
    so_currencies = [r["currency_id"] for r in cur_tgt.fetchall()]
    edge_results["sale_order_currency"] = {
        "currency_ids": so_currencies,
        "clean": (so_currencies == [23]),  # VND currency ID
    }
    print(f"  • Sales Order Currency IDs: {so_currencies} (ID 23 = VND) -> {'PASS' if so_currencies == [23] else 'FAIL'}")

    cur_src.close()
    cur_tgt.close()

    all_edge_pass = (
        edge_results["inactive_partners"]["match"]
        and edge_results["utf8_diacritics"]["match"]
        and edge_results["decimal_precision_cents"]["clean"]
        and edge_results["sale_order_currency"]["clean"]
    )
    return {
        "results": edge_results,
        "pass": all_edge_pass,
    }


# ==============================================================================
# MAIN TEST HARNESS
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Challenger 2 Empirical Stress Test Harness")
    parser.add_argument("--output", default="tools/challenger2_stress_results.json", help="Path for JSON output")
    args = parser.parse_args()

    print("=" * 80)
    print("🛡️  CHALLENGER 2: EMPIRICAL REFERENTIAL INTEGRITY & STRESS HARNESS")
    print(f"   Target Instances: '{SOURCE_DB}' vs '{STRICT_TARGET_DB}' & '{SUPERSET_TARGET_DB}'")
    print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 80)

    start_total = time.perf_counter()

    # Establish connections
    conn_src = get_db_connection(SOURCE_DB)
    conn_strict = get_db_connection(STRICT_TARGET_DB)
    conn_superset = get_db_connection(SUPERSET_TARGET_DB)

    try:
        # 1. Referential Integrity Scans on all DBs
        ref_strict = run_referential_integrity_scans(conn_strict, STRICT_TARGET_DB)
        ref_superset = run_referential_integrity_scans(conn_superset, SUPERSET_TARGET_DB)
        ref_src = run_referential_integrity_scans(conn_src, SOURCE_DB)

        # 2. Double-Entry Balance Equation Checks
        bal_strict = run_double_entry_balance_checks(conn_strict, STRICT_TARGET_DB)
        bal_superset = run_double_entry_balance_checks(conn_superset, SUPERSET_TARGET_DB)
        bal_src = run_double_entry_balance_checks(conn_src, SOURCE_DB)

        # 3. Direct ID Set Comparison & Data Loss Rate
        loss_strict = run_data_loss_rate_validation(conn_src, conn_strict, STRICT_TARGET_DB, allow_superset=False)
        loss_superset = run_data_loss_rate_validation(conn_src, conn_superset, SUPERSET_TARGET_DB, allow_superset=True)

        # 4. CLI Auditing Engine Verification
        cli_audit = run_cli_audit_tests()

        # 5. Adversarial Edge Case Mining
        edge_cases = run_edge_case_mining(conn_src, conn_strict)

    finally:
        conn_src.close()
        conn_strict.close()
        conn_superset.close()

    duration = time.perf_counter() - start_total

    # Evaluate Overall Verdict
    tests_summary = {
        "referential_integrity_source": ref_src["pass"],
        "referential_integrity_strict_target": ref_strict["pass"],
        "referential_integrity_superset_target": ref_superset["pass"],
        "double_entry_balance_source": bal_src["pass"],
        "double_entry_balance_strict_target": bal_strict["pass"],
        "double_entry_balance_superset_target": bal_superset["pass"],
        "data_loss_rate_strict_0_pct": loss_strict["pass"],
        "data_loss_rate_superset_0_pct": loss_superset["pass"],
        "cli_audit_engine_tests": cli_audit["pass"],
        "adversarial_edge_cases": edge_cases["pass"],
    }

    overall_pass = all(tests_summary.values())
    verdict = "APPROVE" if overall_pass else "REJECT"

    output_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent": "Challenger 2 (Stress & Referential Integrity Challenger)",
        "duration_seconds": round(duration, 3),
        "overall_verdict": verdict,
        "test_evaluations": tests_summary,
        "details": {
            "referential_integrity": {
                "source": ref_src,
                "strict_target": ref_strict,
                "superset_target": ref_superset,
            },
            "double_entry_balance": {
                "source": bal_src,
                "strict_target": bal_strict,
                "superset_target": bal_superset,
            },
            "data_loss_validation": {
                "strict_target": loss_strict,
                "superset_target": loss_superset,
            },
            "cli_audit_tests": cli_audit,
            "edge_case_mining": edge_cases,
        },
    }

    out_file = os.path.join("/home/zen/O20", args.output)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("🏆 CHALLENGER 2 EMPIRICAL STRESS TEST SUMMARY")
    print(f"   Total Execution Time: {duration:.2f}s")
    for tname, tpassed in tests_summary.items():
        print(f"   • {tname:<40}: {'✅ PASS' if tpassed else '❌ FAIL'}")
    print(f"\n   FINAL VERDICT: {'🎉 ' + verdict if overall_pass else '❌ ' + verdict}")
    print(f"   Results saved to: {out_file}")
    print("=" * 80)

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
