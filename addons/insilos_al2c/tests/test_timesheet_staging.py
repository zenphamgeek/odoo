# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.

import base64
from odoo.tests.common import TransactionCase, new_test_user, tagged
from odoo.exceptions import UserError
from odoo import fields


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cTimesheetStaging(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Nguyen Van A',
            'work_email': 'consultant.a@inno.ai.vn',
        })
        # Create test project and task
        cls.project = cls.env['project.project'].create({
            'name': 'Innoria ERP Implementation',
            'allow_timesheets': True,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Explore Phase Architecture Workshop',
            'project_id': cls.project.id,
        })
        # Security users
        cls.pm_user = new_test_user(
            cls.env, login='test_pm_user', name='Test Project Manager',
            groups='base.group_user,project.group_project_manager'
        )
        cls.regular_user = new_test_user(
            cls.env, login='test_regular_user', name='Regular Consultant User',
            groups='base.group_user'
        )

    def test_01_body_parsing_and_deduplication(self):
        """Test parsing of structured email body and SHA-256 deduplication."""
        body = (
            "2026-10-12 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 4.5 | Solution architecture design\n"
            "2026-10-13 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 3.0 | Gap analysis session\n"
        )
        sender = 'consultant.a@inno.ai.vn'
        subject = 'Timesheet Week 41 - Nguyen Van A'
        
        fingerprint = self.env['al2c.timesheet.staging'].compute_dedup_hash(sender, subject, body)
        
        staging = self.env['al2c.timesheet.staging'].create({
            'name': subject,
            'sender_email': sender,
            'raw_email_body': body,
            'dedup_fingerprint': fingerprint,
            'submission_channel': 'email_pubsub',
        })
        
        # Trigger parsing
        staging.action_parse_content()
        
        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(staging.parse_status, 'success')
        self.assertEqual(len(staging.line_ids), 2)
        self.assertEqual(staging.total_hours, 7.5)
        self.assertEqual(staging.employee_id.id, self.employee.id)

    def test_02_csv_attachment_parsing(self):
        """Test parsing from a CSV attachment."""
        csv_text = (
            "Date,Project,Task,Hours,Description\n"
            "2026-10-14,Innoria ERP Implementation,Explore Phase Architecture Workshop,5.0,Data migration blueprint\n"
        )
        att = self.env['ir.attachment'].create({
            'name': 'timesheet_oct.csv',
            'type': 'binary',
            'raw': csv_text.encode('utf-8'),
        })
        
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Timesheet with CSV attachment',
            'sender_email': 'consultant.a@inno.ai.vn',
            'attachment_ids': [(4, att.id)],
            'submission_channel': 'email_pubsub',
        })
        staging.action_parse_content()
        
        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(len(staging.line_ids), 1)
        self.assertEqual(staging.line_ids[0].unit_amount, 5.0)
        self.assertEqual(staging.line_ids[0].name, 'Data migration blueprint')

    def test_03_sod_and_commit_to_analytic_ledger(self):
        """Test Segregation of Duties guardrail and final commit to account.analytic.line."""
        body = "2026-10-15 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 6.0 | System integration testing\n"
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Timesheet for Approval Test',
            'sender_email': 'consultant.a@inno.ai.vn',
            'raw_email_body': body,
        })
        staging.action_parse_content()
        self.assertEqual(staging.state, 'parsed')

        # 1. Regular user cannot commit
        with self.assertRaises(UserError):
            staging.with_user(self.regular_user).action_approve_and_commit()

        # 2. PM user commits successfully
        staging.with_user(self.pm_user).action_approve_and_commit()
        self.assertEqual(staging.state, 'approved')
        self.assertEqual(staging.approved_by_id.id, self.pm_user.id)
        
        # Verify committed line
        line = staging.line_ids[0]
        self.assertEqual(line.state, 'committed')
        self.assertTrue(line.analytic_line_id)
        self.assertEqual(line.analytic_line_id.unit_amount, 6.0)
        self.assertEqual(line.analytic_line_id.project_id.id, self.project.id)

    def test_04_webhook_hmac_and_replay_hardening(self):
        """Test HMAC verification, timestamp skew rejection, payload size limit, and nonce deduplication."""
        import hmac
        import hashlib
        import json
        import time
        from contextlib import contextmanager
        from unittest.mock import MagicMock
        from odoo.http import request_var
        from odoo.addons.insilos_al2c.controllers.timesheet_webhook import Al2cTimesheetWebhookController, _MAX_BODY

        controller = Al2cTimesheetWebhookController()
        test_secret = "test_webhook_secret_key_al2c_2026_xyz"
        self.env['ir.config_parameter'].sudo().set_param('insilos_al2c.timesheet_webhook_secret', test_secret)

        now = int(time.time())
        valid_payload = json.dumps({
            'sender': 'consultant.a@inno.ai.vn',
            'subject': 'Timesheet Delivery via Webhook',
            'body': '2026-10-16 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 4.0 | Webhook test\n',
            'nonce': 'unique_nonce_12345',
        }).encode('utf-8')

        sig = hmac.new(test_secret.encode('utf-8'), str(now).encode('utf-8') + b'.' + valid_payload, hashlib.sha256).hexdigest()

        @contextmanager
        def mock_request_context(data=b'', headers=None):
            m = MagicMock()
            m.httprequest.method = 'POST'
            m.httprequest.get_data.return_value = data
            m.httprequest.headers = headers or {}
            m.httprequest.environ = {}
            m.env.return_value = self.env
            token = request_var.set(m)
            try:
                yield m
            finally:
                request_var.reset(token)

        # 1. Missing secret / signature / timestamp -> 401
        with mock_request_context(data=valid_payload, headers={}):
            resp = controller.timesheet_ingest()
            self.assertEqual(resp.status_code, 401)

        # 2. Forged signature -> 401
        with mock_request_context(data=valid_payload, headers={
            'X-Signature': 'deadbeef0000111122223333444455556666777788889999aaaabbbbccccdddd',
            'X-Timestamp': str(now),
        }):
            resp = controller.timesheet_ingest()
            self.assertEqual(resp.status_code, 401)

        # 3. Timestamp skew (> 300s old or future) -> 401
        old_ts = str(now - 600)
        old_sig = hmac.new(test_secret.encode('utf-8'), old_ts.encode('utf-8') + b'.' + valid_payload, hashlib.sha256).hexdigest()
        with mock_request_context(data=valid_payload, headers={
            'X-Signature': old_sig,
            'X-Timestamp': old_ts,
        }):
            resp = controller.timesheet_ingest()
            self.assertEqual(resp.status_code, 401)

        # 4. Oversized body -> 413
        with mock_request_context(data=b'x' * (_MAX_BODY + 10), headers={
            'X-Signature': sig,
            'X-Timestamp': str(now),
        }):
            resp = controller.timesheet_ingest()
            self.assertEqual(resp.status_code, 413)

        # 5. Valid signature -> 201 Created and staged
        with mock_request_context(data=valid_payload, headers={
            'X-Signature': sig,
            'X-Timestamp': str(now),
        }):
            resp = controller.timesheet_ingest()
            self.assertEqual(resp.status_code, 201)
            data = json.loads(resp.data.decode('utf-8'))
            self.assertEqual(data['status'], 'received')
            staging = self.env['al2c.timesheet.staging'].browse(data['staging_id'])
            self.assertEqual(staging.external_nonce, 'unique_nonce_12345')
            self.assertEqual(staging.state, 'parsed')

        # 6. Replay attack with same nonce -> 200 Idempotent duplicate
        with mock_request_context(data=valid_payload, headers={
            'X-Signature': sig,
            'X-Timestamp': str(now),
        }):
            resp = controller.timesheet_ingest()
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data.decode('utf-8'))
            self.assertEqual(data['status'], 'duplicate')

