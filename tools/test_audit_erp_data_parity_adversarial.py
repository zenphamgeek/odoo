#!/usr/bin/env python3
"""
Adversarial Parity Challenger Test Suite
========================================
Empirical stress-testing and adversarial challenge harness for tools/audit_erp_data_parity.py.

Evaluates:
1. Intentional discrepancy detection (count mismatch, content mismatch, missing rows, altered totals)
2. CLI parameter & error handling (invalid host, invalid port, missing database, bad credentials)
3. Exit code invariance (0 on clean pass, 1 on any check failure or error)
4. Subsystem failure mode assertion (Commercial, Financial, Referential Integrity, Table Checksums)
5. Read-only session enforcement (SQL mutation prevention)
6. Performance benchmarking (< 1.0s target)
7. Artifact schema and cryptographic signature validation
"""

import copy
import decimal
import json
import os
import subprocess
import sys
import tempfile
import time
from unittest.mock import MagicMock, patch

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.audit_erp_data_parity import ERPParityAuditor, TABLE_SPECS


class AdversarialTestRunner:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def record(self, name: str, passed: bool, detail: str = "", elapsed_ms: float = 0.0):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "PASS"
            icon = "✅"
        else:
            self.failed_tests += 1
            status = "FAIL"
            icon = "❌"
        self.results.append({
            "name": name,
            "status": status,
            "detail": detail,
            "elapsed_ms": elapsed_ms,
        })
        print(f"  {icon} [{status}] {name:<65} ({elapsed_ms:6.1f}ms) - {detail}")

    def run_cli_command(self, args: list) -> tuple:
        cmd = [sys.executable, os.path.join(REPO_ROOT, "tools", "audit_erp_data_parity.py")] + args
        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return proc.returncode, proc.stdout, proc.stderr, elapsed_ms


def run_tests():
    runner = AdversarialTestRunner()
    print("=" * 90)
    print("🔥 EMPIRICAL ADVERSARIAL STRESS TEST: tools/audit_erp_data_parity.py")
    print("=" * 90)

    # -------------------------------------------------------------------------
    # Category 1: Baseline Parity & Expected Clean Runs
    # -------------------------------------------------------------------------
    print("\n--- Category 1: Baseline Clean Parity Runs ---")

    # 1.1 Strict 1:1 against innoria_prod
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria_prod"])
    p1 = (code == 0) and ("[FORENSIC AUDIT PASS]" in out) and ("100.00% Parity Confirmed" in out)
    runner.record(
        "1.1 Strict 1:1 Parity: odoo20_dev vs innoria_prod",
        p1,
        f"Exit code {code}, elapsed: {el:.1f}ms",
        el,
    )

    # 1.2 Superset parity against innoria.insilos.com
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria.insilos.com", "--allow-superset"])
    p2 = (code == 0) and ("[FORENSIC AUDIT PASS]" in out) and ("SUPERSET VERIFIED" in out or "100.00% Parity Confirmed" in out)
    runner.record(
        "1.2 Superset Parity: odoo20_dev vs innoria.insilos.com",
        p2,
        f"Exit code {code}, elapsed: {el:.1f}ms",
        el,
    )

    # -------------------------------------------------------------------------
    # Category 2: Intentional Discrepancy Detection (Must Fail with Exit Code 1)
    # -------------------------------------------------------------------------
    print("\n--- Category 2: Intentional Discrepancy Detection ---")

    # 2.1 Count mismatch in strict mode (target has 247 partners, source has 91)
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria.insilos.com", "--verbose"])
    p21 = (code == 1) and ("[FORENSIC AUDIT FAIL]" in out) and ("COUNT MISMATCH" in out)
    runner.record(
        "2.1 Intentional Discrepancy: Count mismatch (Strict mode against superset)",
        p21,
        f"Caught count mismatch, exit code {code}",
        el,
    )

    # 2.2 Content mismatch via --no-tenant-override (ID 1 company name differs)
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria_prod", "--no-tenant-override", "--verbose"])
    p22 = (code == 1) and ("[FORENSIC AUDIT FAIL]" in out) and ("MISMATCHED 1 ROWS" in out)
    runner.record(
        "2.2 Intentional Discrepancy: Content mismatch (No tenant override)",
        p22,
        f"Caught row mismatch on ID 1, exit code {code}",
        el,
    )

    # 2.3 Inverted source/target missing records (Target missing 156 records even with superset)
    code, out, err, el = runner.run_cli_command(["--source", "innoria.insilos.com", "--target", "odoo20_dev", "--allow-superset", "--verbose"])
    p23 = (code == 1) and ("[FORENSIC AUDIT FAIL]" in out) and ("MISSING 156 SOURCE ROWS" in out)
    runner.record(
        "2.3 Intentional Discrepancy: Missing records (Inverted source/target)",
        p23,
        f"Caught missing source records in target, exit code {code}",
        el,
    )

    # -------------------------------------------------------------------------
    # Category 3: CLI Parameter & Connection Error Handling (Must Exit Non-Zero)
    # -------------------------------------------------------------------------
    print("\n--- Category 3: CLI Parameter & Connection Error Handling ---")

    # 3.1 Invalid port (e.g. 59999)
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria_prod", "--port", "59999"])
    p31 = (code != 0) and ("Connection refused" in err or "Connection refused" in out or code == 1)
    runner.record(
        "3.1 CLI Error: Invalid port connection failure",
        p31,
        f"Exited with code {code} on closed port",
        el,
    )

    # 3.2 Non-existent source database
    code, out, err, el = runner.run_cli_command(["--source", "non_existent_source_db_999", "--target", "innoria_prod"])
    p32 = (code != 0) and ("does not exist" in err or "does not exist" in out or code == 1)
    runner.record(
        "3.2 CLI Error: Non-existent source database",
        p32,
        f"Exited with code {code} on missing source database",
        el,
    )

    # 3.3 Non-existent target database
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "non_existent_target_db_888"])
    p33 = (code != 0) and ("does not exist" in err or "does not exist" in out or code == 1)
    runner.record(
        "3.3 CLI Error: Non-existent target database",
        p33,
        f"Exited with code {code} on missing target database",
        el,
    )

    # 3.4 Invalid host / Unresolvable hostname
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria_prod", "--host", "invalid_host_address.unknown"])
    p34 = (code != 0) and ("could not translate host name" in err or code == 1)
    runner.record(
        "3.4 CLI Error: Unresolvable host name",
        p34,
        f"Exited with code {code} on invalid host",
        el,
    )

    # 3.5 Invalid credentials (wrong password)
    code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria_prod", "--password", "completely_wrong_pass_000"])
    p35 = (code != 0) and ("password authentication failed" in err or code == 1)
    runner.record(
        "3.5 CLI Error: Invalid password authentication failure",
        p35,
        f"Exited with code {code} on auth failure",
        el,
    )

    # -------------------------------------------------------------------------
    # Category 4: In-Memory Subsystem Stress & Failure Mode Invariant Tests
    # -------------------------------------------------------------------------
    print("\n--- Category 4: Subsystem Failure Mode Assertions ---")

    auditor = ERPParityAuditor(
        source_db="odoo20_dev",
        target_db="innoria_prod",
        host="127.0.0.1",
        port=5434,
        user="odoo",
        password=os.environ.get("PGPASSWORD", ""),
    )
    auditor.connect()

    try:
        # 4.1 Verify Read-Only Transaction Enforcement
        t_start = time.perf_counter()
        read_only_blocked = False
        try:
            cur = auditor.conn_source.cursor()
            cur.execute("CREATE TEMP TABLE _test_ro_violation (id int);")
            auditor.conn_source.commit()
        except Exception as e:
            read_only_blocked = "read-only" in str(e).lower()
            auditor.conn_source.rollback()
        t_el = (time.perf_counter() - t_start) * 1000.0
        runner.record(
            "4.1 Security Invariance: Read-only session prevents SQL mutation",
            read_only_blocked,
            "PostgreSQL rejected DDL/DML on read-only session",
            t_el,
        )

        # 4.2 Commercial Subsystem Mismatch Simulation: Altered SO Untaxed Amount
        t_start = time.perf_counter()
        orig_conn_target = auditor.conn_target
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            {"count": 2, "untaxed": decimal.Decimal("999999.00"), "tax": 0.0, "total": decimal.Decimal("999999.00"), "curr_cnt": 1},
            {"count": 4, "total_qty": 105.0, "sum_subtotal": decimal.Decimal("20127500000.00")},
        ]
        mock_conn.cursor.return_value = mock_cur
        auditor.conn_target = mock_conn
        auditor.results["overall_pass"] = True
        auditor.audit_commercial()
        p42 = (auditor.results["overall_pass"] is False) and (auditor.results["commercial"]["pass"] is False)
        t_el = (time.perf_counter() - t_start) * 1000.0
        runner.record(
            "4.2 Commercial Failure: Tampered SO total triggers commercial failure",
            p42,
            f"overall_pass={auditor.results['overall_pass']}, commercial_pass={auditor.results['commercial']['pass']}",
            t_el,
        )

        # 4.3 Financial Accounting Double-Entry Discrepancy Simulation: debit != credit
        t_start = time.perf_counter()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            # move summary
            {"count": 18, "total": 3263380000.0, "residual": decimal.Decimal("2723380000.00"), "out_inv": 3, "in_inv": 3, "entries": 12, "posted_cnt": 18, "not_paid_cnt": 3},
            # balance summary with non-zero discrepancy (100.00 VNĐ)
            {"total_debit": 1000.0, "total_credit": 900.0, "discrepancy": decimal.Decimal("100.00")},
        ]
        mock_cur.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cur
        auditor.conn_target = mock_conn
        auditor.results["overall_pass"] = True
        auditor.audit_accounting()
        p43 = (auditor.results["overall_pass"] is False) and (auditor.results["financial"]["pass"] is False)
        t_el = (time.perf_counter() - t_start) * 1000.0
        runner.record(
            "4.3 Accounting Failure: Double-entry imbalance (100 VNĐ) caught",
            p43,
            f"overall_pass={auditor.results['overall_pass']}, financial_pass={auditor.results['financial']['pass']}",
            t_el,
        )

        # 4.4 Financial Accounting Individual Unbalanced Move Simulation
        t_start = time.perf_counter()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            {"count": 18, "total": 3263380000.0, "residual": decimal.Decimal("2723380000.00"), "out_inv": 3, "in_inv": 3, "entries": 12, "posted_cnt": 18, "not_paid_cnt": 3},
            {"total_debit": 1000.0, "total_credit": 1000.0, "discrepancy": decimal.Decimal("0.00")},
        ]
        # 1 unbalanced move found
        mock_cur.fetchall.return_value = [{"move_id": 99, "diff": decimal.Decimal("50.00")}]
        mock_conn.cursor.return_value = mock_cur
        auditor.conn_target = mock_conn
        auditor.results["overall_pass"] = True
        auditor.audit_accounting()
        p44 = (auditor.results["overall_pass"] is False) and (auditor.results["financial"]["unbalanced_moves_count"] == 1)
        t_el = (time.perf_counter() - t_start) * 1000.0
        runner.record(
            "4.4 Accounting Failure: Individual unbalanced move flagged",
            p44,
            f"overall_pass={auditor.results['overall_pass']}, unbalanced={auditor.results['financial']['unbalanced_moves_count']}",
            t_el,
        )

        # 4.5 Referential Integrity Orphan Simulation
        t_start = time.perf_counter()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        # 6 checks: simulate 1 orphan sale order line
        mock_cur.fetchone.side_effect = [(1,), (0,), (0,), (0,), (0,), (0,)]
        mock_conn.cursor.return_value = mock_cur
        auditor.conn_target = mock_conn
        auditor.results["overall_pass"] = True
        auditor.audit_referential_integrity()
        p45 = (auditor.results["overall_pass"] is False) and (auditor.results["referential"]["total_orphans"] == 1)
        t_el = (time.perf_counter() - t_start) * 1000.0
        runner.record(
            "4.5 Referential Integrity Failure: Orphan record caught",
            p45,
            f"overall_pass={auditor.results['overall_pass']}, total_orphans={auditor.results['referential']['total_orphans']}",
            t_el,
        )

        # 4.6 Table Data Corruption Simulation: altered field in target row
        t_start = time.perf_counter()
        # Use real fetch for source, mock target with corrupted row
        real_fetch = auditor._fetch_table_data
        def mock_fetch_fn(conn, table, fields, order_by):
            data = real_fetch(auditor.conn_source, table, fields, order_by)
            if conn == auditor.conn_target and table == "res_partner":
                corrupted = copy.deepcopy(data)
                if 2 in corrupted:
                    corrupted[2]["email"] = "corrupted_email@adversarial_test.org"
                return corrupted
            return data

        with patch.object(auditor, "_fetch_table_data", side_effect=mock_fetch_fn):
            auditor.results["overall_pass"] = True
            auditor.audit_tables()
            p46 = (auditor.results["overall_pass"] is False) and (auditor.results["tables"]["res_partner"]["pass"] is False)
        t_el = (time.perf_counter() - t_start) * 1000.0
        runner.record(
            "4.6 Table Integrity Failure: Altered partner email triggers hash mismatch",
            p46,
            f"overall_pass={auditor.results['overall_pass']}, res_partner_pass={auditor.results['tables']['res_partner']['pass']}",
            t_el,
        )

        # Restore real connection
        auditor.conn_target = orig_conn_target

    finally:
        auditor.close()

    # -------------------------------------------------------------------------
    # Category 5: Output Artifact & Cryptographic Digest Integrity
    # -------------------------------------------------------------------------
    print("\n--- Category 5: Output Artifact & Digest Integrity ---")

    # 5.1 Clean run artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_md = os.path.join(tmpdir, "test_report.md")
        tmp_json = os.path.join(tmpdir, "test_manifest.json")

        code, out, err, el = runner.run_cli_command([
            "--source", "odoo20_dev",
            "--target", "innoria_prod",
            "--output-md", tmp_md,
            "--output-json", tmp_json,
        ])

        md_exists = os.path.exists(tmp_md) and os.path.getsize(tmp_md) > 1000
        json_exists = os.path.exists(tmp_json) and os.path.getsize(tmp_json) > 1000

        valid_json = False
        digest_valid = False
        loss_rate_zero = False
        tables_count_12 = False

        if json_exists:
            with open(tmp_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid_json = True
            sig = data.get("forensic_certificate", {}).get("digital_signature_sha256")
            digest_valid = bool(sig and len(sig) == 64)
            loss_rate_zero = (data.get("overall_summary", {}).get("data_loss_rate_pct") == 0.0)
            tables_count_12 = (data.get("overall_summary", {}).get("tables_audited_count") == 12)

        p51 = (code == 0) and md_exists and valid_json and digest_valid and loss_rate_zero and tables_count_12
        runner.record(
            "5.1 Artifact Integrity: Clean run custom paths, Markdown & JSON manifest",
            p51,
            f"MD={md_exists}, JSON={valid_json}, SigLen=64, LossRate=0.0%, Tables=12",
            el,
        )

    # 5.2 Failed run artifacts (Must reflect FAIL status in report and manifest)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_fail_md = os.path.join(tmpdir, "fail_report.md")
        tmp_fail_json = os.path.join(tmpdir, "fail_manifest.json")

        code, out, err, el = runner.run_cli_command([
            "--source", "odoo20_dev",
            "--target", "innoria.insilos.com",
            "--output-md", tmp_fail_md,
            "--output-json", tmp_fail_json,
        ])

        md_has_fail = False
        json_has_fail = False
        if os.path.exists(tmp_fail_md):
            with open(tmp_fail_md, "r", encoding="utf-8") as f:
                md_text = f.read()
            md_has_fail = "❌ AUDIT FAILED" in md_text

        if os.path.exists(tmp_fail_json):
            with open(tmp_fail_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            json_has_fail = (
                data.get("overall_summary", {}).get("status") == "FAIL" and
                data.get("forensic_certificate", {}).get("audit_status") == "FAILED"
            )

        p52 = (code == 1) and md_has_fail and json_has_fail
        runner.record(
            "5.2 Artifact Integrity: Failed run correctly records FAIL status & banner",
            p52,
            f"ExitCode={code}, md_fail_banner={md_has_fail}, json_fail_status={json_has_fail}",
            el,
        )

    # 5.3 CLI Flag Handling: --help and unknown options
    code_help, out_help, _, el_help = runner.run_cli_command(["--help"])
    code_inv, _, err_inv, el_inv = runner.run_cli_command(["--unrecognized-option-test"])
    p53 = (code_help == 0 and "ERP Forensic Data Parity" in out_help) and (code_inv == 2 and "unrecognized arguments" in err_inv)
    runner.record(
        "5.3 CLI Flag Handling: --help displays usage, invalid args exit 2",
        p53,
        f"HelpCode={code_help}, InvalidArgCode={code_inv}",
        el_help + el_inv,
    )

    # -------------------------------------------------------------------------
    # Category 6: Performance Benchmarking (10 Executions, Target < 1.0s)
    # -------------------------------------------------------------------------
    print("\n--- Category 6: Performance Stress Benchmarking (10 Iterations) ---")

    latencies = []
    all_runs_sub_second = True

    for i in range(10):
        code, out, err, el = runner.run_cli_command(["--source", "odoo20_dev", "--target", "innoria_prod"])
        latencies.append(el)
        if el >= 1000.0 or code != 0:
            all_runs_sub_second = False

    min_l = min(latencies)
    max_l = max(latencies)
    avg_l = sum(latencies) / len(latencies)
    p95_l = sorted(latencies)[int(len(latencies) * 0.95)]

    p6 = all_runs_sub_second and (max_l < 1000.0)
    runner.record(
        "6.1 Performance Benchmark: 10/10 runs under 1.0s target",
        p6,
        f"Min: {min_l:.1f}ms | Avg: {avg_l:.1f}ms | P95: {p95_l:.1f}ms | Max: {max_l:.1f}ms",
        avg_l,
    )

    # -------------------------------------------------------------------------
    # Final Verdict & Report Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print(f"📊 SUMMARY: {runner.passed_tests}/{runner.total_tests} Tests Passed")
    print("=" * 90)

    overall_success = (runner.failed_tests == 0)
    verdict = "APPROVE" if overall_success else "REJECT"
    print(f"Final Adversarial Challenger Verdict: **{verdict}**\n")

    return overall_success, runner.results


if __name__ == "__main__":
    success, _ = run_tests()
    sys.exit(0 if success else 1)
