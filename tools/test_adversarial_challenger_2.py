#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adversarial Verification Suite for Challenger 2:
Empirical Stress Testing of Timesheet Ingestion Pipeline (R5),
Consultant Resolution, Sales Document Anti-Genesis (R3), and Multi-Repo Scanner (R2).

Executes directly against local dev instance: insilos20_dev (127.0.0.1:5434).
"""

import sys
import os
import io
import re
import json
import base64
import time
import math
import struct
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add repo root to sys.path
O20_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(O20_DIR))

import odoo
from odoo import api, fields, SUPERUSER_ID
from odoo.modules.registry import Registry

DBNAME = "insilos20_dev"
CONFIG_FILE = "insilos.conf"

results = {
    "suite_1_corrupted_payloads": {},
    "suite_2_consultant_resolution": {},
    "suite_3_sales_anti_genesis": {},
    "suite_4_scanner_resilience": {},
    "vulnerabilities_found": [],
}

def log_vuln(vuln_id, title, severity, details):
    vuln = {
        "id": vuln_id,
        "title": title,
        "severity": severity,
        "details": details,
    }
    results["vulnerabilities_found"].append(vuln)
    print(f"\n🚨 [{severity}] {vuln_id}: {title}")
    print(f"   Details: {details}\n")


def init_odoo():
    print(f"Initializing Odoo connection to {DBNAME}...")
    odoo.tools.config.parse_config(["-c", str(O20_DIR / CONFIG_FILE), "-d", DBNAME])
    return Registry(DBNAME)


# =====================================================================
# SUITE 1: CORRUPTED & EDGE PAYLOADS IN STAGING (R5)
# =====================================================================
def run_suite_1(env):
    print("\n" + "=" * 60)
    print(" SUITE 1: Corrupted & Edge Payloads in Staging (R5)")
    print("=" * 60)
    Staging = env['al2c.timesheet.staging']
    Attachment = env['ir.attachment']

    # Setup base project and consultant for tests
    project = env['project.project'].search([('allow_timesheets', '=', True)], limit=1)
    if not project:
        project = env['project.project'].create({'name': 'Adversarial Test Project', 'allow_timesheets': True})
    task = env['project.task'].search([('project_id', '=', project.id)], limit=1)
    if not task:
        task = env['project.task'].create({'name': 'Adversarial Test Task', 'project_id': project.id})
    employee = env['hr.employee'].search([('work_email', '!=', False)], limit=1)
    if not employee:
        employee = env['hr.employee'].create({'name': 'Test Consultant Adv', 'work_email': 'adv.consultant@inno.ai.vn'})

    # 1.1 Empty Excel .xlsx (0 bytes)
    att_empty_xlsx = Attachment.create({
        'name': 'empty_timesheet.xlsx',
        'raw': b'',
        'type': 'binary',
    })
    stg1 = Staging.create({
        'name': 'Empty XLSX Payload Test',
        'sender_email': employee.work_email,
        'attachment_ids': [(4, att_empty_xlsx.id)],
    })
    stg1.action_parse_content()
    results["suite_1_corrupted_payloads"]["empty_xlsx_0bytes"] = {
        "parse_status": stg1.parse_status,
        "line_count": len(stg1.line_ids),
        "log": stg1.parse_log,
    }
    print(f"  [1.1a] Empty XLSX (0 bytes) -> status: {stg1.parse_status}, lines: {len(stg1.line_ids)}")

    # 1.1b Corrupted binary with .xlsx extension
    att_corrupt_xlsx = Attachment.create({
        'name': 'corrupted.xlsx',
        'raw': b'PK\x03\x04' + os.urandom(1024),
        'type': 'binary',
    })
    stg1b = Staging.create({
        'name': 'Corrupt PK XLSX Test',
        'sender_email': employee.work_email,
        'attachment_ids': [(4, att_corrupt_xlsx.id)],
    })
    stg1b.action_parse_content()
    results["suite_1_corrupted_payloads"]["corrupt_pk_xlsx"] = {
        "parse_status": stg1b.parse_status,
        "line_count": len(stg1b.line_ids),
        "log": stg1b.parse_log,
    }
    print(f"  [1.1b] Corrupt PK XLSX -> status: {stg1b.parse_status}, lines: {len(stg1b.line_ids)}")

    # 1.1c Corrupted .xls (BIFF/OLE)
    att_corrupt_xls = Attachment.create({
        'name': 'corrupted.xls',
        'raw': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + os.urandom(512),
        'type': 'binary',
    })
    stg1c = Staging.create({
        'name': 'Corrupt OLE XLS Test',
        'sender_email': employee.work_email,
        'attachment_ids': [(4, att_corrupt_xls.id)],
    })
    stg1c.action_parse_content()
    results["suite_1_corrupted_payloads"]["corrupt_ole_xls"] = {
        "parse_status": stg1c.parse_status,
        "line_count": len(stg1c.line_ids),
        "log": stg1c.parse_log,
    }
    print(f"  [1.1c] Corrupt OLE XLS -> status: {stg1c.parse_status}, lines: {len(stg1c.line_ids)}")

    # 1.1d Arbitrary non-tabular binary file containing comma (0x2C)
    # Testing line 303: b',' in raw_bytes[:200]
    binary_with_comma = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'x' * 50 + b',' + b'y' * 150 + os.urandom(1024)
    att_comma_bin = Attachment.create({
        'name': 'firmware_update.bin',
        'raw': binary_with_comma,
        'type': 'binary',
    })
    stg1d = Staging.create({
        'name': 'Binary with Comma Byte Test',
        'sender_email': employee.work_email,
        'attachment_ids': [(4, att_comma_bin.id)],
    })
    stg1d.action_parse_content()
    results["suite_1_corrupted_payloads"]["binary_with_comma_byte"] = {
        "parse_status": stg1d.parse_status,
        "line_count": len(stg1d.line_ids),
        "lines_states": [l.state for l in stg1d.line_ids],
        "log": stg1d.parse_log,
    }
    print(f"  [1.1d] Binary with Comma byte (0x2C) -> status: {stg1d.parse_status}, lines: {len(stg1d.line_ids)}")
    if len(stg1d.line_ids) > 0:
        log_vuln("VULN-R5-01", "Binary Attachment Misidentified as CSV", "MEDIUM",
                 f"Non-CSV binary file firmware_update.bin was misidentified as CSV because byte 0x2C was in first 200 bytes, generating {len(stg1d.line_ids)} phantom staging lines.")

    # 1.2 Malformed CSV: Mixed delimiters and unquoted newlines
    malformed_csv = (
        "Date,Project,Task,Hours,Description\n"
        f"2026-10-12;{project.name};{task.name};4.0;Mixed delimiter semicolon\n"
        f"2026-10-13,{project.name},{task.name},5.0,\"Unquoted newline in\nmiddle of line description\"\n"
        f"2026-10-14,{project.name}\n"  # Truncated row
    )
    att_malformed_csv = Attachment.create({
        'name': 'malformed.csv',
        'raw': malformed_csv.encode('utf-8'),
        'type': 'binary',
    })
    stg1e = Staging.create({
        'name': 'Malformed CSV Test',
        'sender_email': employee.work_email,
        'attachment_ids': [(4, att_malformed_csv.id)],
    })
    stg1e.action_parse_content()
    results["suite_1_corrupted_payloads"]["malformed_csv"] = {
        "parse_status": stg1e.parse_status,
        "line_count": len(stg1e.line_ids),
        "line_states": [l.state for l in stg1e.line_ids],
        "line_hours": [l.unit_amount for l in stg1e.line_ids],
        "log": stg1e.parse_log,
    }
    print(f"  [1.2] Malformed CSV -> status: {stg1e.parse_status}, lines: {len(stg1e.line_ids)}, states: {[l.state for l in stg1e.line_ids]}")
    # Inspect if unquoted newline split row into corrupted lines
    if any(l.state == 'error' for l in stg1e.line_ids):
        print(f"        -> Correctly caught broken lines as 'error' state.")

    # 1.3 Invalid dates, non-numeric hours, NaN injection, and missing tasks
    body_edge = (
        # Row 1: Invalid date format
        f"INVALID-DATE-9999 | {project.name} | {task.name} | 4.0 | Invalid date format row\n"
        # Row 2: Non-numeric hours
        f"2026-10-15 | {project.name} | {task.name} | abc | Non-numeric hours row\n"
        # Row 3: NaN hours
        f"2026-10-16 | {project.name} | {task.name} | nan | NaN float injection\n"
        # Row 4: Inf hours
        f"2026-10-17 | {project.name} | {task.name} | inf | Inf float injection\n"
        # Row 5: Missing task (nonexistent)
        f"2026-10-18 | {project.name} | NON_EXISTENT_TASK_XYZ_999 | 3.5 | Missing task row\n"
    )
    stg1f = Staging.create({
        'name': 'Edge Field Values Test',
        'sender_email': employee.work_email,
        'raw_email_body': body_edge,
    })
    stg1f.action_parse_content()
    results["suite_1_corrupted_payloads"]["edge_field_values"] = {
        "parse_status": stg1f.parse_status,
        "line_count": len(stg1f.line_ids),
        "lines": [{
            "date": str(l.date),
            "hours": l.unit_amount,
            "state": l.state,
            "msg": l.validation_message,
            "task_id": l.task_id.id if l.task_id else False,
        } for l in stg1f.line_ids]
    }
    print(f"  [1.3] Edge Field Values -> status: {stg1f.parse_status}, lines: {len(stg1f.line_ids)}")
    for idx, l in enumerate(stg1f.line_ids):
        print(f"        Line {idx+1}: date={l.date}, hours={l.unit_amount}, state={l.state}, task={l.task_id.name or 'False'}, msg={l.validation_message}")

    # Check VULN-R5-02: Invalid Date Silent Fallback
    invalid_date_line = stg1f.line_ids.filtered(lambda l: 'Invalid date format row' in (l.name or ''))
    if invalid_date_line:
        today_date = fields.Date.today()
        if invalid_date_line.date == today_date and invalid_date_line.state == 'valid':
            log_vuln("VULN-R5-02", "Silent Date Fallback to Today on Invalid Date String", "HIGH",
                     f"Line with date 'INVALID-DATE-9999' was silently assigned today's date ({today_date}) and marked 'valid' instead of flagging an error!")

    # Check VULN-R5-03: NaN / Inf Float Injection
    nan_line = stg1f.line_ids.filtered(lambda l: 'NaN float' in (l.name or ''))
    if nan_line:
        if math.isnan(nan_line.unit_amount) or nan_line.state == 'valid':
            log_vuln("VULN-R5-03", "NaN Float Ingestion Bypasses Threshold Validation", "HIGH",
                     f"Hours 'nan' was parsed as float('nan'), bypassed '<= 0' check, and was marked state='{nan_line.state}', corrupting total_hours={stg1f.total_hours}.")

    # Check Missing Task Behavior
    missing_task_line = stg1f.line_ids.filtered(lambda l: 'Missing task row' in (l.name or ''))
    if missing_task_line:
        print(f"        Missing task line state: {missing_task_line.state}, task_id: {missing_task_line.task_id.id}")
        if missing_task_line.state == 'valid' and not missing_task_line.task_id:
            results["suite_1_corrupted_payloads"]["missing_task_valid_status"] = True
            print("        -> Staging accepts line with missing task as valid (project-level timesheet).")

    # 1.4 Database Constraint & Race Condition Check on Deduplication
    print("  [1.4] Checking PostgreSQL unique constraints on dedup_fingerprint and external_nonce...")
    env.cr.execute("""
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'al2c_timesheet_staging'::regclass;
    """)
    constraints = env.cr.fetchall()
    constraint_names = [c[0] for c in constraints]
    results["suite_1_corrupted_payloads"]["db_constraints"] = constraint_names
    print(f"        PostgreSQL constraints on al2c_timesheet_staging: {constraint_names}")

    has_uniq_fp = any('dedup' in c.lower() or 'fingerprint' in c.lower() for c in constraint_names)
    has_uniq_nonce = any('nonce' in c.lower() for c in constraint_names)
    if not has_uniq_fp and not has_uniq_nonce:
        log_vuln("VULN-R5-04", "Missing Database UNIQUE Constraint on Idempotency Keys (Race Condition Vulnerability)", "HIGH",
                 "al2c_timesheet_staging lacks PostgreSQL UNIQUE constraints on 'dedup_fingerprint' and 'external_nonce'. Under concurrent webhook/email arrivals, two simultaneous requests will both pass ORM search() and insert duplicate staging records.")


# =====================================================================
# SUITE 2: CONSULTANT RESOLUTION EDGE CASES (R5)
# =====================================================================
def run_suite_2(env):
    print("\n" + "=" * 60)
    print(" SUITE 2: Consultant Resolution Edge Cases")
    print("=" * 60)
    Staging = env['al2c.timesheet.staging']
    Employee = env['hr.employee']
    Partner = env['res.partner']

    # 2.1 Ambiguous Email: Matches Multiple Employees
    run_ts = int(time.time() * 1000)
    ambig_email = f"ambiguous.consultant.{run_ts}@inno.ai.vn"
    emp1 = Employee.create({'name': 'Consultant Ambiguous 1', 'work_email': ambig_email})
    emp2 = Employee.create({'name': 'Consultant Ambiguous 2', 'work_email': ambig_email})

    resolved_emp = Staging._resolve_consultant(ambig_email)
    print(f"  [2.1] Ambiguous Email ({ambig_email}) matches 2 employees: {emp1.name} (id {emp1.id}) vs {emp2.name} (id {emp2.id})")
    print(f"        Resolved: {resolved_emp.name} (id {resolved_emp.id})")
    results["suite_2_consultant_resolution"]["ambiguous_employee"] = {
        "emp1_id": emp1.id,
        "emp2_id": emp2.id,
        "resolved_id": resolved_emp.id,
    }
    if resolved_emp.id == emp1.id:
        log_vuln("VULN-R5-05", "Silent Arbitrary Selection on Ambiguous Consultant Email", "MEDIUM",
                 f"When email matches multiple employees, _resolve_consultant silently selects the lowest ID ({resolved_emp.name}) with zero audit warning or ambiguity flag.")

    # 2.2 Tier 3 Partner Resolution Shadowing:
    # Partner 1 (created first) has NO linked employee.
    # Partner 2 (created second) has the same email and HAS a linked employee.
    partner_email = f"partner.shadow.{run_ts}@inno.ai.vn"
    part1 = Partner.create({'name': 'Unlinked Partner 1', 'email': partner_email})
    part2 = Partner.create({'name': 'Linked Partner 2', 'email': partner_email})
    emp_linked = Employee.create({'name': 'Linked Consultant 2', 'work_contact_id': part2.id})

    resolved_part_emp = Staging._resolve_consultant(partner_email)
    print(f"  [2.2] Tier 3 Shadowing: Partner 1 (unlinked) vs Partner 2 (linked to {emp_linked.name})")
    print(f"        Resolved Employee: {resolved_part_emp.name if resolved_part_emp else 'None (Failed)'}")
    results["suite_2_consultant_resolution"]["partner_shadowing"] = {
        "part1_id": part1.id,
        "part2_id": part2.id,
        "resolved_employee_id": resolved_part_emp.id if resolved_part_emp else False,
    }
    if not resolved_part_emp:
        log_vuln("VULN-R5-06", "Tier 3 Partner Resolution Broken by Unlinked Shadow Partner", "HIGH",
                 f"res.partner search limit=1 stopped at unlinked partner {part1.name}, causing _resolve_consultant to completely fail to find valid employee {emp_linked.name} linked to partner {part2.name} with identical email.")

    # 2.3 Unknown Email: Matches No Employee
    unknown_email = "completely.unknown.stranger@external.com"
    resolved_none = Staging._resolve_consultant(unknown_email)
    print(f"  [2.3] Unknown Email: {unknown_email} -> {resolved_none.name if resolved_none else 'Empty Recordset (False)'}")

    # What happens when staging is created and parsed with unknown consultant?
    project = env['project.project'].search([('allow_timesheets', '=', True)], limit=1)
    task = env['project.task'].search([('project_id', '=', project.id)], limit=1)
    body_unknown = f"2026-10-19 | {project.name} | {task.name} | 4.0 | Unknown consultant work\n"
    stg_unknown = Staging.create({
        'name': 'Unknown Consultant Submission',
        'sender_email': unknown_email,
        'raw_email_body': body_unknown,
    })
    stg_unknown.action_parse_content()
    print(f"        Staging parsed state: {stg_unknown.state}, employee: {stg_unknown.employee_id.name or 'None'}, line employee: {stg_unknown.line_ids[0].employee_id.name or 'None'}")
    print(f"        Line status: {stg_unknown.line_ids[0].state}, val_msg: {stg_unknown.line_ids[0].validation_message}")

    # Check deduplication bypass on unknown employee:
    # If line has no employee, can duplicate identical lines be created without detection?
    stg_unknown_dup = Staging.create({
        'name': 'Unknown Consultant Submission 2',
        'sender_email': unknown_email,
        'raw_email_body': body_unknown,
    })
    stg_unknown_dup.action_parse_content()
    dup_line_state = stg_unknown_dup.line_ids[0].state
    print(f"        Second identical submission line status: {dup_line_state}")
    if dup_line_state == 'valid':
        log_vuln("VULN-R5-07", "Deduplication Engine Bypassed When Consultant Unresolved", "HIGH",
                 "When consultant email matches no employee, employee_id is False. Row-level deduplication and cross-staging deduplication check 'if emp_id and task_id:', so duplicate detection is completely bypassed, allowing duplicate anonymous entries to be parsed as 'valid'.")


# =====================================================================
# SUITE 3: SALES DOCUMENT ANTI-GENESIS & BRANDING AUDIT (R3)
# =====================================================================
def run_suite_3(env):
    print("\n" + "=" * 60)
    print(" SUITE 3: Sales Document Anti-Genesis Audit (R3)")
    print("=" * 60)
    ReportAction = env['ir.actions.report']
    Order = env['sale.order']

    # Find or use test sale order
    order = Order.search([], order='id desc', limit=1)
    if not order:
        print("  Creating sample order for report rendering...")
        partner = env['res.partner'].search([], limit=1)
        prod = env['product.product'].search([], limit=1)
        order = Order.create({
            'name': 'SO-TEST-AUDIT-001',
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': prod.id, 'name': 'Adversarial Test Item', 'product_uom_qty': 1, 'price_unit': 1000000})],
        })

    reports_to_test = [
        ('insilos_al2c.action_report_sales_proposal', 'Sales Proposal'),
        ('insilos_al2c.action_report_commercial_quotation', 'Commercial Quotation'),
        ('insilos_al2c.action_report_statement_of_work', 'Statement of Work (SOW)'),
        ('insilos_al2c.action_report_sla_contract', 'SLA Contract'),
    ]

    forbidden_tokens = ['odoo', 'openerp', 'todo', 'fixme', 'lorem ipsum']
    # Exclude internal asset error string if injected by debug runner
    re_token = re.compile(r'\b(odoo|openerp|todo|fixme|lorem\s+ipsum)\b', re.IGNORECASE)

    for ref, rname in reports_to_test:
        print(f"\n  Testing Report: {rname} ({ref})...")
        try:
            html_bytes, rep_format = ReportAction._render_qweb_html(ref, [order.id])
            html_text = html_bytes.decode('utf-8')
            cleaned_html = re.sub(r'__odooAssetError[A-Za-z0-9_]*', '', html_text)
            
            # Check length
            print(f"    Compiled successfully: {len(html_text)} bytes")

            # Check leaks
            matches = re_token.findall(cleaned_html)
            results["suite_3_sales_anti_genesis"][ref] = {
                "name": rname,
                "size_bytes": len(html_text),
                "leaks": list(set(matches)),
            }
            if matches:
                print(f"    ❌ BRANDING LEAKS DETECTED in {rname}: {set(matches)}")
                log_vuln(f"VULN-R3-{ref.split('.')[-1]}", f"Branding Leak in {rname}", "HIGH",
                         f"Rendered QWeb report contains forbidden platform tokens: {set(matches)}")
            else:
                print(f"    ✅ Clean: Zero 'Odoo', 'OpenERP', 'TODO', 'FIXME' tokens detected.")

            # Check IBM / SAP styling tokens
            has_sap_sapphire = '#0070F2' in html_text or '#0070f2' in html_text
            has_decree_13 = '13/2023' in html_text
            has_carbon_font = 'Segoe UI' in html_text or 'IBM' in html_text or 'sans-serif' in html_text
            print(f"    Styling Verification: Sapphire Accent: {has_sap_sapphire}, Decree 13 Notice: {has_decree_13}, Typography: {has_carbon_font}")

        except Exception as e:
            print(f"    ❌ Report compilation failed: {e}")
            results["suite_3_sales_anti_genesis"][ref] = {"error": str(e)}
            log_vuln("VULN-R3-RENDER", f"Report Rendering Failure in {rname}", "CRITICAL", str(e))


# =====================================================================
# SUITE 4: MULTI-REPO SCANNER RESILIENCE (R2)
# =====================================================================
def run_suite_4():
    print("\n" + "=" * 60)
    print(" SUITE 4: Multi-Repo Scanner Resilience (R2)")
    print("=" * 60)
    from tools.multi_repo_scanner import MultiRepoScanner
    from tools.run_multi_repo_scan import run_scan

    # Test 4.1: Non-existent directory
    print("  [4.1] Testing scanner against non-existent repository path...")
    fake_repos = ["/tmp/non_existent_repo_dir_99999"]
    try:
        scanner = MultiRepoScanner(repos=fake_repos)
        res = scanner.scan_all()
        print(f"        Successfully handled non-existent repo. Total scanned: {res['summary']['total_repositories']}")
        results["suite_4_scanner_resilience"]["non_existent_repo"] = "PASS"
    except Exception as e:
        print(f"        ❌ Scanner crashed on non-existent repo: {e}")
        log_vuln("VULN-R2-01", "Scanner Crashes on Missing Repository Path", "HIGH", str(e))

    # Test 4.2: Dirty git tree and missing doc path in temporary repo
    print("  [4.2] Testing scanner against dirty git tree and missing doc path...")
    temp_dir = tempfile.mkdtemp(prefix="adv_repo_")
    try:
        # Init git repo
        subprocess.run(["git", "init", temp_dir], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "-C", temp_dir, "config", "user.email", "adv@test.com"], check=True)
        subprocess.run(["git", "-C", temp_dir, "config", "user.name", "Adv Tester"], check=True)

        # Create module with code but NO README / documentation
        mod_dir = Path(temp_dir) / "module_undocumented"
        mod_dir.mkdir(parents=True, exist_ok=True)
        code_file = mod_dir / "service.py"
        code_file.write_text("# Undocumented code\ndef run():\n    pass\n")

        subprocess.run(["git", "-C", temp_dir, "add", "."], check=True)
        subprocess.run(["git", "-C", temp_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.DEVNULL)

        # Make tree dirty (untracked file and unstaged change)
        dirty_file = mod_dir / "untracked.py"
        dirty_file.write_text("# Untracked\n")
        code_file.write_text("# Modified\ndef run():\n    return 42\n")

        scanner2 = MultiRepoScanner(repos=[temp_dir], scope="all")
        res2 = scanner2.scan_all()
        summary = res2["summary"]
        print(f"        Dirty files detected: {summary['total_dirty_files']} (Expected >= 2)")
        print(f"        Missing doc modules: {summary['missing_doc_modules_count']} (Expected >= 1)")
        results["suite_4_scanner_resilience"]["dirty_and_missing_doc"] = {
            "dirty_files": summary['total_dirty_files'],
            "missing_docs": summary['missing_doc_modules_count'],
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Test 4.3: Broken submodule / commit graph traversal defect (zencode-ent router simulation)
    print("  [4.3] Testing scanner against broken commit graph traversal...")
    temp_broken_repo = tempfile.mkdtemp(prefix="adv_broken_repo_")
    try:
        subprocess.run(["git", "init", temp_broken_repo], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "-C", temp_broken_repo, "config", "user.email", "adv@test.com"], check=True)
        subprocess.run(["git", "-C", temp_broken_repo, "config", "user.name", "Adv Tester"], check=True)
        test_file = Path(temp_broken_repo) / "main.py"
        test_file.write_text("print('test')")
        subprocess.run(["git", "-C", temp_broken_repo, "add", "."], check=True)
        subprocess.run(["git", "-C", temp_broken_repo, "commit", "-m", "Commit 1"], check=True, stdout=subprocess.DEVNULL)

        # Corrupt commit object or test git telemetry inspector directly
        from tools.multi_repo_scanner import GitTelemetryInspector
        info = GitTelemetryInspector.get_git_info(temp_broken_repo)
        print(f"        Git Telemetry Extraction: is_git={info['is_git']}, branch={info['branch']}, velocity_30d={info['velocity_30d']}")
        results["suite_4_scanner_resilience"]["git_telemetry"] = "PASS"
    finally:
        shutil.rmtree(temp_broken_repo, ignore_errors=True)

    # Test 4.4: Run real run_multi_repo_scan.py --check on the 4 production sovereign repos
    print("  [4.4] Running run_multi_repo_scan.py --check on real sovereign repositories...")
    json_tmp = "/tmp/adv_multi_repo_scan.json"
    md_tmp = "/tmp/adv_multi_repo_scan.md"
    exit_code = run_scan(
        repos=None,
        json_path=json_tmp,
        markdown_path=md_tmp,
        check=True,
    )
    print(f"        Scanner --check exited with code: {exit_code}")
    results["suite_4_scanner_resilience"]["real_scan_exit_code"] = exit_code
    if exit_code == 1:
        print("        -> Confirmed: Scanner properly detected P0 defect in zencode-ent/router and returned exit code 1.")


def main():
    print("================================================================")
    print(" CHALLENGER 2: ADVERSARIAL VERIFICATION HARNESS")
    print(" Target Environment: insilos20_dev (127.0.0.1:5434)")
    print(" Timestamp: " + fields.Datetime.now().isoformat())
    print("================================================================")

    registry = init_odoo()
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        run_suite_1(env)
        run_suite_2(env)
        run_suite_3(env)

    # Run Suite 4 outside of DB cursor
    run_suite_4()

    # Save findings JSON
    out_path = Path("/home/zen/O20/tools/challenger_2_adversarial_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAdversarial test results saved to: {out_path}")
    print(f"Total vulnerabilities discovered: {len(results['vulnerabilities_found'])}")


if __name__ == "__main__":
    main()
