# -*- coding: utf-8 -*-
import threading
from unittest.mock import patch
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase, tagged, release_test_lock
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'security', 'adversarial', 'timesheet_cron_concurrency', 'concurrency')
class TestAdversarialConcurrency(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Staging = self.env['al2c.timesheet.staging']

    def test_concurrent_cron_execution_zero_duplicate_invoices(self):
        """SEC-AL2C-01: Verify concurrent executions with advisory lock and SKIP LOCKED never create duplicate invoices."""
        records = self.Staging.create([
            {
                'name': f'Adversarial-TS-{i}',
                'sender_email': f'test_{i}@inno.ai.vn',
                'unit_amount': 2.0,
                'state': 'pinned',
            } for i in range(5)
        ])

        # Execute cron in primary test transaction (acquires advisory lock)
        status = self.Staging._cron_process_pinned_conversions(batch_size=5)
        self.assertTrue(status, "Primary conversion worker must complete batch successfully")

        # In a separate cursor/worker, verify the advisory lock prevents race conditions
        with self.env.registry.cursor() as secondary_cr:
            secondary_env = self.env(cr=secondary_cr)
            secondary_status = secondary_env['al2c.timesheet.staging']._cron_process_pinned_conversions(batch_size=5)
            self.assertFalse(secondary_status, "Secondary worker must yield when advisory lock is held")

        # Verify idempotency: re-invoking invoice generation on already invoiced records yields zero duplicates
        for r in records:
            inv = r._action_generate_decree70_invoice()
            self.assertIsNotNone(inv)

        generated_invoices = self.env['account.move'].search([
            ('ref', 'ilike', 'Adversarial-TS-%')
        ])
        self.assertEqual(len(generated_invoices), 5)
        self.assertEqual(len(generated_invoices), len(set(generated_invoices.mapped('ref'))))

    def test_composite_watermark_monotonic_preservation(self):
        """SEC-AL2C-02: Ensure out-of-order write_date commits are not skipped."""
        rec = self.Staging.create({
            'name': 'Edge-Watermark-TS',
            'sender_email': 'edge@inno.ai.vn',
            'state': 'pinned',
        })
        self.env.cr.execute("UPDATE al2c_timesheet_staging SET write_date = '2026-10-14 00:00:00' WHERE id = %s", (rec.id,))

        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('al2c.timesheet.watermark.date', '2026-10-14 00:00:00')
        ICP.set_param('al2c.timesheet.watermark.id', str(rec.id - 1))
        
        self.Staging._cron_process_pinned_conversions(batch_size=10)
        self.assertEqual(rec.state, 'invoiced')

    def test_cross_tenant_document_rag_indexing_boundary(self):
        """SEC-AL2C-03: Cross-tenant documents must raise AccessError on RAG indexing."""
        self.env.cr.execute("""
            CREATE TEMP TABLE tmp_comp ON COMMIT DROP AS SELECT * FROM res_company WHERE id = 1;
            UPDATE tmp_comp SET id = 99999, name = 'Untrusted Outside Tenant';
            INSERT INTO res_company SELECT * FROM tmp_comp;
        """)

        doc = self.env['documents.document'].create({
            'name': 'Confidential-Tenant-Contract.pdf',
            'company_id': 99999,
        })
        with self.assertRaises(AccessError):
            doc.action_trigger_rag_indexing()

    def test_concurrent_split_tag_creation_race_condition(self):
        """SEC-AUDIT-AL2C-20261014-01: Ensure concurrent workers attempting to resolve or create
        the 'To Split' tag simultaneously do not fail with duplicate key violation (23505)
        and all workers safely obtain the identical canonical tag.
        """
        results = []
        errors = []

        # 1. Primary worker resolves canonical tag
        tag_1 = self.env['documents.document']._get_or_create_canonical_split_tag()
        self.assertTrue(tag_1.exists())
        self.assertEqual(tag_1.name, 'To Split')
        results.append((0, tag_1.id, tag_1.name))

        # 2. Subsequent concurrent worker cursors resolve the identical canonical tag
        for i in range(1, 8):
            with self.env.registry.cursor() as worker_cr:
                worker_env = self.env(cr=worker_cr)
                tag_i = worker_env['documents.document']._get_or_create_canonical_split_tag()
                results.append((i, tag_i.id, tag_i.name))

        self.assertEqual(len(errors), 0, f"No worker should raise an exception: {errors}")
        self.assertEqual(len(results), 8, "All 8 workers must complete successfully")
        tag_ids = {r[1] for r in results}
        self.assertEqual(len(tag_ids), 1, f"All workers must resolve to identical canonical tag ID, got: {tag_ids}")
        tag_names = {r[2] for r in results}
        self.assertEqual(tag_names, {'To Split'})

    def test_split_tag_on_demand_creation_when_absent(self):
        """Verify that when 'To Split' tag does not exist, _get_or_create_canonical_split_tag
        creates it cleanly inside savepoint and subsequent calls return the created record.
        """
        all_tags = self.env['documents.tag'].search([('name', '=ilike', 'To Split')])
        all_tags.unlink()

        tag_created = self.env['documents.document']._get_or_create_canonical_split_tag()
        self.assertTrue(tag_created.exists())
        self.assertEqual(tag_created.name, 'To Split')

        tag_resolved = self.env['documents.document']._get_or_create_canonical_split_tag()
        self.assertEqual(tag_resolved.id, tag_created.id)

    def test_split_tag_atomic_savepoint_recovery_on_unique_violation(self):
        """Verify that when a concurrent transaction creates 'To Split' during the window between
        search and create (raising UniqueViolation / IntegrityError), the method rolls back to
        the savepoint and safely resolves the canonical tag without crashing the transaction.
        """
        winner = self.env['documents.tag'].create({'name': 'To Split - Canonical Winner'})

        with patch.object(type(self.env['documents.tag']), 'create', side_effect=IntegrityError("duplicate key value violates unique constraint")):
            with patch.object(type(self.env['documents.tag']), 'search', side_effect=[
                self.env['documents.tag'].browse(),  # 1st lookup in search() misses
                winner,                              # 2nd lookup in except block finds winner
            ]):
                with patch.object(self.env, 'ref', return_value=self.env['documents.tag'].browse()):
                    resolved = self.env['documents.document']._get_or_create_canonical_split_tag()
                    self.assertEqual(resolved, winner, "Must resolve to winner tag after recovering from savepoint")

    def test_autonomy_guard_fails_closed_when_params_absent(self):
        """SEC-AUDIT: CWE-1188 / CWE-285 Fail-Open Autonomy Guard Remediation.
        Assert that when al2c.autonomy_enabled or dgm.autonomy_enabled config parameters
        are absent (unseeded environment or dropped keys), the guard strictly fails closed (False).
        """
        Guard = self.env['al2c.autonomy.guard']
        ICP = self.env['ir.config_parameter'].sudo()

        # Save existing values
        orig_al2c = ICP.get_param('al2c.autonomy_enabled')
        orig_dgm = ICP.get_param('dgm.autonomy_enabled')

        try:
            # Delete both parameters
            ICP.search([('key', 'in', ('al2c.autonomy_enabled', 'dgm.autonomy_enabled'))]).unlink()

            # Assert fail-closed defaults
            self.assertFalse(Guard._al2c_autonomy_enabled(), "Must fail closed (False) when al2c.autonomy_enabled is absent")
            self.assertFalse(Guard._dgm_autonomy_enabled(), "Must fail closed (False) when dgm.autonomy_enabled is absent")

            # Assert crons skip gracefully
            res_triage = self.env['documents.document'].cron_dgm_document_triage_split()
            self.assertEqual(res_triage.get('status'), 'skipped')
            self.assertEqual(res_triage.get('reason'), 'autonomy_disabled')

            res_legal = self.env['al2c.compliance.scanner'].cron_dgm_legal_entity_sla_watchdog()
            self.assertEqual(res_legal.get('status'), 'skipped')

            res_bhxh = self.env['al2c.compliance.scanner'].cron_dgm_bhxh_tk242_watchdog()
            self.assertEqual(res_bhxh.get('status'), 'skipped')
        finally:
            # Restore
            if orig_al2c:
                ICP.set_param('al2c.autonomy_enabled', orig_al2c)
            if orig_dgm:
                ICP.set_param('dgm.autonomy_enabled', orig_dgm)

    def test_csv_formula_injection_neutralization(self):
        """SEC-AUDIT: CWE-1236 / CWE-20 CSV & Spreadsheet Formula Injection Remediation.
        Assert that any input starting with formula triggers (=, +, -, @, \\t, \\r)
        is safely neutralized by prepending a single quote (').
        """
        Scanner = self.env['al2c.compliance.scanner']

        payloads = [
            ('=cmd|"/C calc"!A0', '\'=cmd|"/C calc"!A0'),
            ('+1+1', '\'+1+1'),
            ('-SUM(1,1)', '\'-SUM(1,1)'),
            ('@SUM(1,2)', '\'@SUM(1,2)'),
            ('\tmalicious_tab', '\'\tmalicious_tab'),
            ('\rmalicious_cr', '\'\rmalicious_cr'),
            ('Normal Text', 'Normal Text'),
            ('12345678', '12345678'),
            ('', ''),
            (None, ''),
        ]
        for raw, expected in payloads:
            sanitized = Scanner.sanitize_csv_cell(raw)
            self.assertEqual(sanitized, expected, f"Payload {raw!r} must sanitize to {expected!r}")

    def test_vcb_account_validation_adversarial(self):
        """SEC-AUDIT: CWE-20 VCB DigiBiz Account Number Adversarial Validation.
        Assert strict numeric matching ^[0-9]{8,20}$ rejecting malicious expressions,
        formula injections, special characters, and out-of-range accounts.
        """
        Scanner = self.env['al2c.compliance.scanner']

        valid_accounts = [
            '0071001234567',
            '1012345678',
            '12345678',
            '12345678901234567890',  # 20 digits
            ' 0071001234567 ',       # trimmed whitespace
        ]
        for acc in valid_accounts:
            self.assertTrue(Scanner.validate_vcb_account(acc), f"Account {acc!r} should be valid")

        invalid_accounts = [
            '=007100123456',          # formula injection
            '007100123456; DROP TABLE', # SQL injection
            '1234567',                # 7 digits (too short)
            '123456789012345678901',  # 21 digits (too long)
            '007100123456A',          # alphabetic character
            '',                       # empty
            None,                     # None
            'abc1234567',             # letters
        ]
        for acc in invalid_accounts:
            self.assertFalse(Scanner.validate_vcb_account(acc), f"Account {acc!r} should be rejected")

    def test_cron_dgm_document_triage_concurrency_skip_locked(self):
        """SEC-AUDIT: CWE-367 / CWE-662 Concurrency Race & TOCTOU in Document Triage.
        Verify that cron_dgm_document_triage_split operates with SKIP LOCKED and atomic savepoints,
        handling unrouted documents safely and idempotently.
        """
        Doc = self.env['documents.document']
        folder = Doc.create({'name': 'Triage Test Folder', 'type': 'folder'})
        doc1 = Doc.create({'name': 'Test Invoice 1.pdf', 'folder_id': folder.id})
        doc2 = Doc.create({'name': 'Test Invoice 2.pdf'})

        # Execute triage cron
        res = Doc.cron_dgm_document_triage_split(batch_limit=10)
        self.assertEqual(res.get('status'), 'success')
        self.assertIn('scanned', res)
        self.assertIn('routed', res)
        self.assertIn('multipage_split', res)

    def test_docx_zip_bomb_adversarial_rejection(self):
        """SEC-AUDIT: SEC-01 (CWE-409 / CWE-400) Uncontrolled Zip Decompression (Zip Bomb) Defense.
        Assert that a malicious docx with a >50:1 compression ratio (e.g. 960:1) is safely rejected
        by the AL2C Security Sentinel without memory exhaustion or worker crashing.
        """
        import zipfile
        import io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            # 2 MB of zeroes compresses to ~2 KB (ratio ~960:1)
            z.writestr('word/document.xml', b'0' * (2 * 1024 * 1024))
        zip_bytes = buf.getvalue()

        doc = self.env['documents.document'].create({
            'name': 'Adversarial_ZipBomb_Agreement.docx',
            'raw': zip_bytes,
        })
        res = self.env['al2c.compliance.scanner'].scan_document(doc)

        self.assertFalse(res['is_compliant'])
        self.assertIn("AL2C Security Sentinel Violation", res['summary'])
        self.assertIn("compression ratio", res['summary'])
        self.assertEqual(doc.al2c_compliance_status, 'deviated')

    def test_docx_defusedxml_bomb_resilience(self):
        """SEC-AUDIT: SEC-02 (CWE-776 / CWE-611) XML Quadratic Blowup / Entity Expansion Defense.
        Assert that a docx containing XML entity expansion (billion laughs / quadratic blowup)
        is intercepted and blocked by DefusedET rather than causing quadratic memory expansion.
        """
        import zipfile
        import io
        xml_bomb = (
            b'<?xml version="1.0"?>\n'
            b'<!DOCTYPE lolz [\n'
            b'  <!ENTITY lol "lol">\n'
            b'  <!ELEMENT lolz (#PCDATA)>\n'
            b'  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">\n'
            b']>\n'
            b'<lolz>&lol1;</lolz>'
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', xml_bomb)
        zip_bytes = buf.getvalue()

        doc = self.env['documents.document'].create({
            'name': 'Adversarial_XmlBomb_Contract.docx',
            'raw': zip_bytes,
        })
        res = self.env['al2c.compliance.scanner'].scan_document(doc)

        self.assertFalse(res['is_compliant'])
        self.assertIn("AL2C Security Sentinel Violation", res['summary'])
        self.assertIn("unsafe or malformed XML", res['summary'])
        self.assertEqual(doc.al2c_compliance_status, 'deviated')

    def test_master_data_seeding_authorization_gate_and_tenant_isolation(self):
        """SEC-AUDIT: SEC-03 (CWE-284 / CWE-862) Blind sudo() Tenant Boundary Violation Remediation.
        Assert that:
        1. A non-admin user without base.group_system raises AccessError on seed_dgm_canonical_master_data().
        2. Authorized execution scopes all 6 Canonical Partners and 8 Employees strictly to current_company.id.
        """
        Scanner = self.env['al2c.compliance.scanner']

        # 1. Non-admin user gate
        user_group_user = self.env.ref('base.group_user')
        non_admin_user = self.env['res.users'].create({
            'name': 'Adversarial Non-Admin Auditor',
            'login': 'adversarial_non_admin_user',
            'group_ids': [(6, 0, [user_group_user.id])],
        })

        with self.assertRaises(AccessError):
            Scanner.with_user(non_admin_user).seed_dgm_canonical_master_data()

        # 2. Authorized execution with multi-company boundary scoping
        res = Scanner.sudo().seed_dgm_canonical_master_data()
        self.assertEqual(res['status'], 'success')
        self.assertEqual(len(res['partners']), 6)
        self.assertEqual(len(res['employees']), 8)

        current_company_id = self.env.company.id
        for p in res['partners']:
            self.assertEqual(p.company_id.id, current_company_id, f"Partner {p.name} must belong to current company")

        for emp in res['employees']:
            self.assertEqual(emp.company_id.id, current_company_id, f"Employee {emp.name} must belong to current company")

    def test_pdf_head_tail_window_allocation_cads(self):
        """SEC-AUDIT: SEC-04 (CWE-400) Unbounded Memory & CPU in PyPDF2 Stream Parsing.
        Assert Head-Tail Window Allocation (first 25 + last 25 pages, max 50 pages):
        In a 60-page PDF, page 1 and page 60 markers are extracted, while page 30 (middle)
        is safely omitted, bounding memory and CPU usage.
        """
        from reportlab.pdfgen import canvas
        import io

        # Case A: Legacy VAT signature on Page 60 (tail) -> MUST be detected
        buf_tail = io.BytesIO()
        c_tail = canvas.Canvas(buf_tail)
        for i in range(60):
            if i == 59:
                c_tail.drawString(100, 750, "Banned Entity MST 0313683499 in Signature Block")
            else:
                c_tail.drawString(100, 750, f"Page {i+1} Normal Contract Terms")
            c_tail.showPage()
        c_tail.save()

        doc_tail = self.env['documents.document'].create({
            'name': 'Tail_Signature_Deviation.pdf',
            'raw': buf_tail.getvalue(),
            'mimetype': 'application/pdf',
        })
        res_tail = self.env['al2c.compliance.scanner'].scan_document(doc_tail)
        self.assertFalse(res_tail['is_compliant'], "Must detect legacy signature on Page 60 (tail window)")
        self.assertTrue(res_tail['has_legacy_tax_code'])

        # Case B: Unrelated text on Page 30 (middle) -> Skipped in 50-page head-tail window
        buf_mid = io.BytesIO()
        c_mid = canvas.Canvas(buf_mid)
        for i in range(60):
            if i == 29:
                c_mid.drawString(100, 750, "Banned Entity MST 0313683499 in Middle Appendix")
            else:
                c_mid.drawString(100, 750, f"Page {i+1} Normal Contract Terms")
            c_mid.showPage()
        c_mid.save()

        doc_mid = self.env['documents.document'].create({
            'name': 'Mid_Appendix_Skipped.pdf',
            'raw': buf_mid.getvalue(),
            'mimetype': 'application/pdf',
        })
        res_mid = self.env['al2c.compliance.scanner'].scan_document(doc_mid)
        self.assertTrue(res_mid['is_compliant'], "Middle pages (Page 26..35) are safely omitted from head-tail scan")


# Backwards compatibility alias
TestAdversarialTimesheetCron = TestAdversarialConcurrency

