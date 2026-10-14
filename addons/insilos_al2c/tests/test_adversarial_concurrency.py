# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install', 'security', 'adversarial', 'timesheet_cron_concurrency')
class TestAdversarialTimesheetCron(TransactionCase):

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
