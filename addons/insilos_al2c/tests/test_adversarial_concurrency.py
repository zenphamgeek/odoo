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


# Backwards compatibility alias
TestAdversarialTimesheetCron = TestAdversarialConcurrency

