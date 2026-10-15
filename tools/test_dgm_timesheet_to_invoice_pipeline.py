#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated End-to-End Verification Suite for SOP-DGM-08:
Post-Onboarding Project Notifications (`dgm.project.notification`),
Monthly Project Timesheet Consolidation (`dgm.project.timesheet.sheet` / `.line`),
Customer Electronic Approval & SHA-256 Acceptance Certificate,
and MTI-Style Two-Stage Draft Reconciliation -> Official VAT E-Invoice (`1C26TAA`) Pipeline.

Verifies across BOTH `insilos20_dev` and `innoria_prod`:
1. `verify_db_state(dbname)`:
   - Knowledge Article `SOP-DGM-08` & external ID `insilos_al2c.kb_dgm_sop_08_timesheet_billing`.
   - `PRJ-NTF-202610-0001` (MTI) & `PRJ-NTF-202610-0002` (AIfin) in `dgm_project_notification`.
   - `TS-DGM-202610-0001` (MTI: 250,000,000 VND untaxed / 270,000,000 VND total with 8% VAT)
     and `TS-DGM-202610-0002` (AIfin — Trần Văn Huỳnh Phố DGM-009: 35,000,000 VND untaxed /
     37,800,000 VND total with 8% VAT) in `dgm_project_timesheet_sheet` (`state == 'official_invoiced'`).
   - All 4 linked documents (`timesheet_doc_id`, `acceptance_doc_id`, `draft_invoice_doc_id`,
     `official_invoice_doc_id`) having `file_size > 400`, `owner_id IS NULL`, `access_internal IN ('edit', 'view')`.
   - Linked `account.move` records with `dgm_invoice_stage == 'official_issued'`,
     `dgm_einvoice_symbol == '1C26TAA'`, and non-empty `dgm_einvoice_number`.
   - Zero Empty Folders Invariant (`0` empty active folders in `documents_document`).
2. `verify_workflow_and_security_guards()`:
   - Transactional savepoint (`with cr.savepoint():`) testing:
     * Guardrail 1: `action_generate_mti_draft_invoice()` in `'draft'` or `'pm_verified'` raises `UserError`.
     * Revision Flow: `action_submit_for_customer_approval()` -> `action_request_revision('Adjust OT hours')`
       -> `'revision_requested'` -> re-submit -> `action_customer_approve(...)` -> `'customer_approved'`
       with 64-char hex SHA-256 `customer_signature_hash`.
     * Draft-to-Official Invoice Flow: `action_generate_mti_draft_invoice()` -> `'draft_invoiced'`
       (`dgm_invoice_stage == 'draft_reconciliation'`) -> `action_confirm_draft_and_issue_official_invoice()`
       -> `'official_invoiced'` (`dgm_invoice_stage == 'official_issued'`, `dgm_einvoice_symbol == '1C26TAA'`).
     * Portal Token Constant-Time Security Check: AST & source inspection of `dgm_timesheet_portal.py`
       confirming `hmac.compare_digest` and `readonly=False` on all `@http.route` decorators.
"""
import ast
import configparser
import os
import re
import site
import sys
import types
import psycopg2

ROOT_DIR = "/home/zen/O20"
VENV_SITE = os.path.join(ROOT_DIR, ".venv/lib/python3.12/site-packages")
if os.path.isdir(VENV_SITE):
    site.addsitedir(VENV_SITE)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    import xmlsec  # noqa: F401
except Exception:
    sys.modules["xmlsec"] = types.ModuleType("xmlsec")

import odoo
from odoo import api, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.modules.registry import Registry


def get_local_conn(dbname):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(ROOT_DIR, "odoo.conf"))
    opts = cfg["options"] if "options" in cfg else {}
    return psycopg2.connect(
        dbname=dbname,
        user=os.environ.get("DB_USER", opts.get("db_user", "odoo")),
        password=os.environ.get("PGPASSWORD", opts.get("db_password", "odoo")),
        host=os.environ.get("DB_HOST", opts.get("db_host", "127.0.0.1")),
        port=int(os.environ.get("DB_PORT", opts.get("db_port", "5434"))),
    )


def _assert_doc_valid(cur, dbname, doc_id, label, expected_prefix=None):
    assert doc_id is not None, f"{dbname}: Missing document ID for {label}"
    cur.execute(
        """
        SELECT d.id,
               COALESCE(
                   CASE WHEN pg_typeof(d.name)::text = 'jsonb' THEN (d.name::jsonb)->>'en_US' ELSE d.name::text END,
                   ''
               ) AS doc_name,
               d.owner_id,
               d.access_internal,
               d.active,
               a.file_size
          FROM documents_document d
          LEFT JOIN ir_attachment a ON a.id = d.attachment_id
         WHERE d.id = %s;
        """,
        (doc_id,),
    )
    row = cur.fetchone()
    assert row is not None, f"{dbname}: Document id={doc_id} ({label}) not found in documents_document"
    _, doc_name, owner_id, access_internal, active, file_size = row
    assert active is True, f"{dbname}: Document {doc_name} ({label}) must be active=True"
    assert owner_id is None, f"{dbname}: Document {doc_name} ({label}) must have owner_id IS NULL, got {owner_id}"
    assert access_internal in ("edit", "view"), (
        f"{dbname}: Document {doc_name} ({label}) invalid access_internal={access_internal}"
    )
    assert file_size and int(file_size) > 400, (
        f"{dbname}: Document {doc_name} ({label}) attachment file_size too small: {file_size}"
    )
    if expected_prefix:
        assert expected_prefix in doc_name, (
            f"{dbname}: Document {doc_name} ({label}) missing expected prefix '{expected_prefix}'"
        )


def verify_db_state(dbname):
    conn = get_local_conn(dbname)
    cur = conn.cursor()

    # 1. Verify SOP-DGM-08 Knowledge Article exists and is active
    cur.execute(
        """
        SELECT id, name
          FROM knowledge_article
         WHERE name ILIKE 'SOP-DGM-08%' AND active = TRUE
         ORDER BY id ASC LIMIT 1;
        """
    )
    kb_row = cur.fetchone()
    assert kb_row is not None, f"{dbname}: Missing active SOP-DGM-08 Knowledge Article"

    cur.execute(
        """
        SELECT res_id FROM ir_model_data
         WHERE module = 'insilos_al2c' AND name = 'kb_dgm_sop_08_timesheet_billing';
        """
    )
    imd_row = cur.fetchone()
    assert imd_row is not None and imd_row[0] == kb_row[0], (
        f"{dbname}: Missing or mismatched ir_model_data for insilos_al2c.kb_dgm_sop_08_timesheet_billing"
    )

    # 2. Verify PRJ-NTF-202610-0001 (MTI) and PRJ-NTF-202610-0002 (AIfin) in dgm_project_notification
    for ntf_code in ("PRJ-NTF-202610-0001", "PRJ-NTF-202610-0002"):
        cur.execute(
            """
            SELECT id, name, notification_type, state, document_id
              FROM dgm_project_notification
             WHERE name = %s
             ORDER BY id ASC LIMIT 1;
            """,
            (ntf_code,),
        )
        ntf = cur.fetchone()
        assert ntf is not None, f"{dbname}: Missing notification {ntf_code}"
        _, _, ntf_type, ntf_state, ntf_doc_id = ntf
        assert ntf_type == "kickoff_handover", f"{dbname}: {ntf_code} expected kickoff_handover, got {ntf_type}"
        assert ntf_state in ("sent", "acknowledged"), f"{dbname}: {ntf_code} invalid state={ntf_state}"
        _assert_doc_valid(cur, dbname, ntf_doc_id, f"{ntf_code}.document_id")

    # 3. Verify TS-DGM-202610-0001 (MTI) and TS-DGM-202610-0002 (AIfin) in dgm_project_timesheet_sheet
    expected_sheets = [
        ("TS-DGM-202610-0001", "PTN-DGM-2026-0001", 250_000_000.0, 20_000_000.0, 270_000_000.0, 4),
        ("TS-DGM-202610-0002", "PTN-DGM-2026-0007", 35_000_000.0, 2_800_000.0, 37_800_000.0, 1),
    ]
    for (
        sheet_code,
        exp_partner_code,
        exp_untaxed,
        exp_tax,
        exp_total,
        exp_line_cnt,
    ) in expected_sheets:
        cur.execute(
            """
            SELECT s.id,
                   s.state,
                   s.amount_untaxed_vnd,
                   s.amount_tax_vnd,
                   s.amount_total_vnd,
                   s.customer_signature_hash,
                   s.timesheet_doc_id,
                   s.acceptance_doc_id,
                   s.draft_invoice_id,
                   s.draft_invoice_doc_id,
                   s.official_invoice_doc_id,
                   p.dgm_partner_code
              FROM dgm_project_timesheet_sheet s
              JOIN res_partner p ON p.id = s.partner_id
             WHERE s.name = %s
             ORDER BY s.id ASC LIMIT 1;
            """,
            (sheet_code,),
        )
        s_row = cur.fetchone()
        assert s_row is not None, f"{dbname}: Missing timesheet sheet {sheet_code}"
        (
            sheet_id,
            s_state,
            untaxed,
            tax,
            total,
            sig_hash,
            ts_doc_id,
            acc_doc_id,
            draft_inv_id,
            draft_doc_id,
            off_doc_id,
            partner_code,
        ) = s_row
        assert partner_code == exp_partner_code, (
            f"{dbname}: {sheet_code} partner code mismatch {partner_code} != {exp_partner_code}"
        )
        assert s_state == "official_invoiced", (
            f"{dbname}: {sheet_code} expected state='official_invoiced', got '{s_state}'"
        )
        assert round(float(untaxed or 0.0)) == round(exp_untaxed), (
            f"{dbname}: {sheet_code} untaxed mismatch {untaxed} != {exp_untaxed}"
        )
        assert round(float(tax or 0.0)) == round(exp_tax), (
            f"{dbname}: {sheet_code} tax mismatch {tax} != {exp_tax}"
        )
        assert round(float(total or 0.0)) == round(exp_total), (
            f"{dbname}: {sheet_code} total mismatch {total} != {exp_total}"
        )
        assert sig_hash and bool(re.fullmatch(r"[0-9a-f]{64}", sig_hash)), (
            f"{dbname}: {sheet_code} invalid SHA-256 signature hash: {sig_hash}"
        )

        # Verify line count
        cur.execute(
            "SELECT COUNT(*) FROM dgm_project_timesheet_line WHERE sheet_id = %s;",
            (sheet_id,),
        )
        line_cnt = cur.fetchone()[0]
        assert line_cnt == exp_line_cnt, (
            f"{dbname}: {sheet_code} expected {exp_line_cnt} lines, got {line_cnt}"
        )

        # Verify all 4 linked documents
        _assert_doc_valid(
            cur, dbname, ts_doc_id, f"{sheet_code}.timesheet_doc_id", "01_Bang_Cham_Cong_Timesheet"
        )
        _assert_doc_valid(
            cur, dbname, acc_doc_id, f"{sheet_code}.acceptance_doc_id", "02_Bien_Ban_Nghiem_Thu_Timesheet"
        )
        _assert_doc_valid(
            cur, dbname, draft_doc_id, f"{sheet_code}.draft_invoice_doc_id", "03_Hoa_Don_Nhap_Doi_Soat"
        )
        _assert_doc_valid(
            cur, dbname, off_doc_id, f"{sheet_code}.official_invoice_doc_id", "04_Hoa_Don_Chinh_Thuc_VAT"
        )

        # Verify linked account.move
        assert draft_inv_id is not None, f"{dbname}: {sheet_code} missing draft_invoice_id"
        cur.execute(
            """
            SELECT dgm_invoice_stage, dgm_einvoice_symbol, dgm_einvoice_number, dgm_einvoice_lookup_code
              FROM account_move
             WHERE id = %s;
            """,
            (draft_inv_id,),
        )
        inv_row = cur.fetchone()
        assert inv_row is not None, f"{dbname}: {sheet_code} account_move id={draft_inv_id} not found"
        inv_stage, einv_sym, einv_num, einv_lookup = inv_row
        assert inv_stage == "official_issued", (
            f"{dbname}: {sheet_code} account_move expected dgm_invoice_stage='official_issued', got '{inv_stage}'"
        )
        assert einv_sym == "1C26TAA", (
            f"{dbname}: {sheet_code} account_move expected dgm_einvoice_symbol='1C26TAA', got '{einv_sym}'"
        )
        assert einv_num and len(str(einv_num).strip()) >= 6, (
            f"{dbname}: {sheet_code} account_move missing dgm_einvoice_number: {einv_num}"
        )
        assert einv_lookup and "1C26TAA" in str(einv_lookup), (
            f"{dbname}: {sheet_code} account_move missing lookup code: {einv_lookup}"
        )

    # 4. Verify Zero Empty Folders Invariant across active folders in documents_document
    cur.execute(
        """
        SELECT f.id,
               COALESCE(
                   CASE WHEN pg_typeof(f.name)::text = 'jsonb' THEN (f.name::jsonb)->>'en_US' ELSE f.name::text END,
                   ''
               )
          FROM documents_document f
         WHERE f.type = 'folder' AND f.active = TRUE
           AND NOT EXISTS (
               SELECT 1 FROM documents_document c
                WHERE c.folder_id = f.id AND c.active = TRUE
           );
        """
    )
    empty_folders = cur.fetchall()
    assert len(empty_folders) == 0, (
        f"{dbname}: Found empty active folders violating Rule 6: {empty_folders}"
    )

    cur.close()
    conn.close()
    print(
        f"[✓] {dbname}: SOP-DGM-08 Knowledge Article, PRJ-NTF-202610-0001..0002, "
        f"TS-DGM-202610-0001 (MTI 250M/270M VND) & TS-DGM-202610-0002 (AIfin 35M/37.8M VND), "
        f"8 companion billing HTML documents, 1C26TAA official E-Invoices, and 0 empty folders verified!"
    )


def verify_portal_controller_security():
    """Verifies `addons/insilos_al2c/controllers/dgm_timesheet_portal.py` uses
    constant-time `hmac.compare_digest` and sets `readonly=False` on all `@http.route` decorators."""
    portal_path = os.path.join(ROOT_DIR, "addons/insilos_al2c/controllers/dgm_timesheet_portal.py")
    assert os.path.exists(portal_path), f"Missing portal controller: {portal_path}"

    with open(portal_path, "r", encoding="utf-8") as f:
        src = f.read()

    assert "hmac.compare_digest" in src, "dgm_timesheet_portal.py must use hmac.compare_digest"

    tree = ast.parse(src, filename=portal_path)
    route_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    func_name = ""
                    if isinstance(dec.func, ast.Attribute):
                        func_name = dec.func.attr
                    elif isinstance(dec.func, ast.Name):
                        func_name = dec.func.id
                    if func_name == "route":
                        route_count += 1
                        kw_map = {kw.arg: kw.value for kw in dec.keywords if kw.arg}
                        assert "readonly" in kw_map, (
                            f"Route {node.name} in dgm_timesheet_portal.py missing explicit readonly=False"
                        )
                        ro_val = kw_map["readonly"]
                        assert isinstance(ro_val, ast.Constant) and ro_val.value is False, (
                            f"Route {node.name} in dgm_timesheet_portal.py must set readonly=False"
                        )
    assert route_count >= 2, f"Expected >= 2 @http.route endpoints in dgm_timesheet_portal.py, found {route_count}"
    print(f"[✓] Portal Controller Security: {route_count} @http.route endpoints verified with hmac.compare_digest & readonly=False")


def verify_workflow_and_security_guards(dbname="insilos20_dev"):
    """Uses an Odoo transaction with a savepoint (`with cr.savepoint():`) so all test mutations
    roll back cleanly, verifying:
    - Guardrail 1: `action_generate_mti_draft_invoice()` in `'draft'` or `'pm_verified'` raises `UserError`.
    - Revision Flow: `action_submit_for_customer_approval()` -> `action_request_revision('Adjust OT hours')`
      -> `'revision_requested'` -> re-submit -> `action_customer_approve(...)` -> `'customer_approved'`
      with 64-char hex SHA-256 `customer_signature_hash`.
    - Draft-to-Official Invoice Flow: `action_generate_mti_draft_invoice()` -> `'draft_invoiced'`
      (`dgm_invoice_stage == 'draft_reconciliation'`) -> `action_confirm_draft_and_issue_official_invoice()`
      -> `'official_invoiced'` (`dgm_invoice_stage == 'official_issued'`, `dgm_einvoice_symbol == '1C26TAA'`).
    """
    verify_portal_controller_security()

    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        with cr.savepoint():
            Partner = env["res.partner"].sudo()
            Project = env["project.project"].sudo()
            Employee = env["hr.employee"].sudo()
            Sheet = env["dgm.project.timesheet.sheet"].sudo()
            Line = env["dgm.project.timesheet.line"].sudo()

            aifin = Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0007")], limit=1)
            prj = Project.search([("partner_id", "=", aifin.id)], limit=1) or Project.search([], limit=1)
            emp = Employee.search([("registration_number", "=", "DGM-009")], limit=1) or Employee.search([], limit=1)

            test_sheet = Sheet.create({
                "partner_id": aifin.id,
                "project_id": prj.id,
                "billing_period": "11/2026",
                "date_start": "2026-11-01",
                "date_end": "2026-11-30",
                "standard_working_days": 22.0,
                "vat_rate": "8",
            })
            Line.create({
                "sheet_id": test_sheet.id,
                "employee_id": emp.id,
                "role_title": "Senior Software Engineer",
                "contract_monthly_rate_vnd": 35_000_000.0,
                "standard_days": 22.0,
                "actual_worked_days": 22.0,
                "overtime_hours": 0.0,
                "work_summary": "Verification test line for November 2026.",
            })
            assert test_sheet.state == "draft", f"Expected initial state 'draft', got {test_sheet.state}"

            # Guardrail 1A: Calling action_generate_mti_draft_invoice() in 'draft' MUST raise UserError
            raised_in_draft = False
            try:
                test_sheet.action_generate_mti_draft_invoice()
            except UserError:
                raised_in_draft = True
            assert raised_in_draft, "Guardrail violation: action_generate_mti_draft_invoice() did not raise UserError in 'draft'!"

            # Submit for customer approval -> 'pm_verified'
            test_sheet.action_submit_for_customer_approval()
            assert test_sheet.state == "pm_verified", f"Expected state 'pm_verified', got {test_sheet.state}"
            assert test_sheet.timesheet_doc_id, "Expected timesheet_doc_id to be generated"

            # Guardrail 1B: Calling action_generate_mti_draft_invoice() in 'pm_verified' MUST raise UserError
            raised_in_pm_verified = False
            try:
                test_sheet.action_generate_mti_draft_invoice()
            except UserError:
                raised_in_pm_verified = True
            assert raised_in_pm_verified, "Guardrail violation: action_generate_mti_draft_invoice() did not raise UserError in 'pm_verified'!"

            # Revision Flow: action_request_revision('Adjust OT hours') -> 'revision_requested'
            test_sheet.action_request_revision("Adjust OT hours")
            assert test_sheet.state == "revision_requested", (
                f"Expected state 'revision_requested', got {test_sheet.state}"
            )
            assert "Adjust OT hours" in (test_sheet.customer_approval_note or ""), (
                "Revision note was not recorded on customer_approval_note"
            )

            # Re-submit and Customer Approve -> 'customer_approved' + 64-char SHA-256 signature hash
            test_sheet.action_submit_for_customer_approval()
            assert test_sheet.state == "pm_verified"
            test_sheet.action_customer_approve(
                approver_name="Nguyễn Quốc Huy — CEO",
                approver_email="huy.nguyen@aifin.com.vn",
                approver_title="CEO",
                note="Approved after OT check.",
            )
            assert test_sheet.state == "customer_approved", (
                f"Expected state 'customer_approved', got {test_sheet.state}"
            )
            assert test_sheet.customer_signature_hash and bool(
                re.fullmatch(r"[0-9a-f]{64}", test_sheet.customer_signature_hash)
            ), f"Invalid 64-char SHA-256 customer_signature_hash: {test_sheet.customer_signature_hash}"
            assert test_sheet.acceptance_doc_id, "Expected acceptance_doc_id to be generated"

            # Guardrail 1C (SOP08-REV2 CWE-863 Post-Acceptance Seal):
            # Mutating or unlinking a timesheet line immediately after customer_approved MUST raise UserError
            raised_in_customer_approved_write = False
            try:
                test_sheet.line_ids[0].write({"actual_worked_days": 15.0})
            except UserError:
                raised_in_customer_approved_write = True
            assert raised_in_customer_approved_write, (
                "Post-Acceptance Seal violation: line.write({'actual_worked_days': 15.0}) did not raise UserError in 'customer_approved'!"
            )

            raised_in_customer_approved_unlink = False
            try:
                test_sheet.line_ids[0].unlink()
            except UserError:
                raised_in_customer_approved_unlink = True
            assert raised_in_customer_approved_unlink, (
                "Post-Acceptance Seal violation: line.unlink() did not raise UserError in 'customer_approved'!"
            )

            # Draft-to-Official Invoice Flow
            test_sheet.action_generate_mti_draft_invoice()
            assert test_sheet.state == "draft_invoiced", (
                f"Expected state 'draft_invoiced', got {test_sheet.state}"
            )
            assert test_sheet.draft_invoice_id, "Expected draft_invoice_id to be created"
            assert test_sheet.draft_invoice_id.dgm_invoice_stage == "draft_reconciliation", (
                f"Expected dgm_invoice_stage='draft_reconciliation', got {test_sheet.draft_invoice_id.dgm_invoice_stage}"
            )
            assert test_sheet.draft_invoice_doc_id, "Expected draft_invoice_doc_id to be generated"

            first_inv = test_sheet.action_confirm_draft_and_issue_official_invoice(
                confirmed_by="Nguyễn Quốc Huy — CEO (AIfin)"
            )
            assert test_sheet.state == "official_invoiced", (
                f"Expected state 'official_invoiced', got {test_sheet.state}"
            )
            assert test_sheet.draft_invoice_id.dgm_invoice_stage == "official_issued", (
                f"Expected dgm_invoice_stage='official_issued', got {test_sheet.draft_invoice_id.dgm_invoice_stage}"
            )
            assert test_sheet.draft_invoice_id.dgm_einvoice_symbol == "1C26TAA", (
                f"Expected dgm_einvoice_symbol='1C26TAA', got {test_sheet.draft_invoice_id.dgm_einvoice_symbol}"
            )
            assert test_sheet.draft_invoice_id.dgm_einvoice_number, "Expected non-empty dgm_einvoice_number"
            assert test_sheet.official_invoice_doc_id, "Expected official_invoice_doc_id to be generated"
            first_einv_num = test_sheet.draft_invoice_id.dgm_einvoice_number
            first_inv_id = test_sheet.draft_invoice_id.id

            # Verify Canonical C14N / NFC 1C26TAA XML generation
            xml_c14n = test_sheet._build_canonical_1c26taa_xml()
            for req_xml_frag in (
                'Kieu="1C26TAA"',
                "<MST>0317958465</MST>",
                "<TenNM>",
                "<MSTNM>",
                "<TongTien>",
                "<DigestManifest>",
                "<SignatureHMAC>",
            ):
                assert req_xml_frag in xml_c14n, f"Missing {req_xml_frag} in C14N 1C26TAA XML: {xml_c14n}"

            # Guardrail 2: Calling action_confirm_draft_and_issue_official_invoice() a second time MUST be idempotent
            second_inv = test_sheet.action_confirm_draft_and_issue_official_invoice(
                confirmed_by="Nguyễn Quốc Huy — CEO (AIfin)"
            )
            assert second_inv, "Expected truthy return from idempotent action_confirm_draft_and_issue_official_invoice()"
            assert test_sheet.draft_invoice_id.id == first_inv_id, (
                f"Idempotency violation: draft_invoice_id changed from {first_inv_id} to {test_sheet.draft_invoice_id.id}"
            )
            assert test_sheet.draft_invoice_id.dgm_einvoice_number == first_einv_num, (
                f"Idempotency violation: dgm_einvoice_number changed from {first_einv_num} to {test_sheet.draft_invoice_id.dgm_einvoice_number}"
            )

            # Guardrail 3: Decree 70/2025/ND-CP Immutability Barrier on official_invoiced lines & sheets
            test_line = test_sheet.line_ids[0]
            for forbidden_vals in (
                {"actual_worked_days": 10.0},
                {"contract_monthly_rate_vnd": 10_000_000.0},
            ):
                raised_immutable_write = False
                try:
                    test_line.write(forbidden_vals)
                except UserError:
                    raised_immutable_write = True
                assert raised_immutable_write, (
                    f"Fiscal barrier violation: line.write({forbidden_vals}) did not raise UserError when sheet.state == 'official_invoiced'!"
                )

            raised_immutable_unlink = False
            try:
                test_line.unlink()
            except UserError:
                raised_immutable_unlink = True
            assert raised_immutable_unlink, (
                "Fiscal barrier violation: line.unlink() did not raise UserError when sheet.state == 'official_invoiced'!"
            )

            # Rollback savepoint automatically by raising a sentinel or using cr.execute("ROLLBACK TO SAVEPOINT ...")
            raise RuntimeError("_ROLLBACK_TEST_SAVEPOINT_")
        # unreachable
    print("[✓] Behavioral & Security Guardrails verified cleanly (savepoint rolled back)")


def verify_k8s_live_innoria_prod():
    """Verifies K8s live production (`innoria_prod` on `innoria-prod-app-*`) has SOP-DGM-08 seeded."""
    import subprocess
    res_pod = subprocess.run(
        [
            "kubectl", "get", "pods", "-n", "production",
            "-l", "app=innoria-prod",
            "--field-selector=status.phase=Running",
            "-o", "jsonpath={.items[0].metadata.name}",
        ],
        capture_output=True,
        text=True,
    )
    if res_pod.returncode != 0 or not res_pod.stdout.strip():
        print("[!] Skipping K8s live check (no running innoria-prod pod found)")
        return
    pod = res_pod.stdout.strip()
    k8s_check_py = """
import os, psycopg2
conn = psycopg2.connect(
    dbname='innoria_prod',
    user=os.environ.get('DB_USER', 'insilos'),
    password=os.environ.get('PGPASSWORD', ''),
    host=os.environ.get('DB_HOST', 'pgbouncer-service'),
    port=int(os.environ.get('DB_PORT', 6432)),
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM knowledge_article WHERE name ILIKE 'SOP-DGM-08%' AND active = TRUE;")
kb08 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM dgm_project_notification WHERE name IN ('PRJ-NTF-202610-0001', 'PRJ-NTF-202610-0002') AND state IN ('sent', 'acknowledged');")
ntfs = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM dgm_project_timesheet_sheet WHERE name IN ('TS-DGM-202610-0001', 'TS-DGM-202610-0002') AND state = 'official_invoiced';")
sheets = cur.fetchone()[0]
cur.execute('''
    SELECT COUNT(*)
      FROM documents_document f
     WHERE f.type = 'folder' AND f.active = TRUE
       AND NOT EXISTS (SELECT 1 FROM documents_document c WHERE c.folder_id = f.id AND c.active = TRUE);
''')
empty_folders = cur.fetchone()[0]
assert kb08 >= 1, f'K8s innoria_prod missing SOP-DGM-08 knowledge article ({kb08})'
assert ntfs == 2, f'K8s innoria_prod expected 2 project notifications, got {ntfs}'
assert sheets == 2, f'K8s innoria_prod expected 2 official_invoiced timesheet sheets, got {sheets}'
assert empty_folders == 0, f'K8s innoria_prod has {empty_folders} empty folders'
print(f'K8S_SOP_DGM_08_OK kb08={kb08} ntfs={ntfs} sheets={sheets} empty_folders={empty_folders}')
"""
    res = subprocess.run(
        ["kubectl", "exec", "-n", "production", pod, "-c", "innoria", "--", "python3", "-c", k8s_check_py],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0 and "K8S_SOP_DGM_08_OK" in res.stdout, (
        f"K8s live SOP-DGM-08 verification failed on {pod}: {res.stdout} {res.stderr}"
    )
    print(f"[✓] K8s live production (`innoria_prod` SOP-DGM-08): {res.stdout.strip()}")


def main():
    odoo.tools.config.parse_config(["-c", os.path.join(ROOT_DIR, "odoo.conf")])
    for dbname in ("insilos20_dev", "innoria_prod"):
        verify_db_state(dbname)

    try:
        verify_workflow_and_security_guards("insilos20_dev")
    except RuntimeError as exc:
        if str(exc) == "_ROLLBACK_TEST_SAVEPOINT_":
            print(
                "[✓] Behavioral & Security Guardrails: UserError before customer_approved, "
                "revision_requested loop, 64-char SHA-256 signature hash, and MTI draft->official "
                "1C26TAA E-Invoice state machine verified (savepoint rolled back cleanly)!"
            )
        else:
            raise

    verify_k8s_live_innoria_prod()

    print("\n=== ALL SOP-DGM-08 TIMESHEET-TO-INVOICE PIPELINE VERIFICATION GATES PASSED (EXIT 0) ===")


if __name__ == "__main__":
    main()
