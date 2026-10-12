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

    def _create_xlsx(self, rows):
        """Generates valid .xlsx Excel workbook in-memory using openpyxl."""
        import io
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _create_biff2_xls(self, rows):
        """Generates standard BIFF2 Excel binary content for test fixtures."""
        import struct
        data = bytearray(struct.pack('<HHHH', 0x0009, 4, 0x0002, 0x0010))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                if isinstance(val, (int, float)):
                    body = struct.pack('<HH3sd', r_idx, c_idx, b'\x00\x00\x00', float(val))
                    data += struct.pack('<HH', 0x0003, len(body)) + body
                else:
                    s = str(val).encode('latin1', errors='replace')
                    body = struct.pack('<HH3sB', r_idx, c_idx, b'\x00\x00\x00', len(s)) + s
                    data += struct.pack('<HH', 0x0004, len(body)) + body
        data += struct.pack('<HH', 0x000A, 0)
        return bytes(data)

    def test_05_excel_xlsx_attachment_parsing(self):
        """Test parsing of Excel .xlsx attachments using openpyxl."""
        rows = [
            ['Date', 'Project', 'Task', 'Hours', 'Description'],
            ['2026-10-14', 'Innoria ERP Implementation', 'Explore Phase Architecture Workshop', 5.5, 'Openpyxl Excel integration'],
            ['2026-10-15', 'Innoria ERP Implementation', 'Explore Phase Architecture Workshop', 2.5, 'Sprint review session'],
        ]
        xlsx_bytes = self._create_xlsx(rows)
        att = self.env['ir.attachment'].create({
            'name': 'timesheet_consultant.xlsx',
            'type': 'binary',
            'raw': xlsx_bytes,
        })

        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Timesheet with XLSX attachment',
            'sender_email': 'consultant.a@inno.ai.vn',
            'attachment_ids': [(4, att.id)],
            'submission_channel': 'email_pubsub',
        })
        staging.action_parse_content()

        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(staging.parse_status, 'success')
        self.assertEqual(len(staging.line_ids), 2)
        self.assertEqual(staging.total_hours, 8.0)
        self.assertEqual(staging.line_ids[0].name, 'Openpyxl Excel integration')
        self.assertEqual(staging.line_ids[0].unit_amount, 5.5)
        self.assertEqual(staging.line_ids[1].unit_amount, 2.5)

    def test_06_excel_xls_attachment_parsing(self):
        """Test parsing of legacy Excel .xls attachments using xlrd."""
        rows = [
            ['Date', 'Project', 'Task', 'Hours', 'Description'],
            ['2026-10-16', 'Innoria ERP Implementation', 'Explore Phase Architecture Workshop', 4.0, 'Legacy XLS timesheet import'],
        ]
        xls_bytes = self._create_biff2_xls(rows)
        att = self.env['ir.attachment'].create({
            'name': 'timesheet_legacy.xls',
            'type': 'binary',
            'raw': xls_bytes,
        })

        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Timesheet with XLS attachment',
            'sender_email': 'consultant.a@inno.ai.vn',
            'attachment_ids': [(4, att.id)],
            'submission_channel': 'email_pubsub',
        })
        staging.action_parse_content()

        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(len(staging.line_ids), 1)
        self.assertEqual(staging.total_hours, 4.0)
        self.assertEqual(staging.line_ids[0].name, 'Legacy XLS timesheet import')

    def test_07_multi_tier_consultant_resolution(self):
        """Test multi-tier consultant resolution: hr.employee -> res.users -> res.partner."""
        staging_model = self.env['al2c.timesheet.staging']

        # Tier 1: Directly by hr.employee work_email
        emp_t1 = self.env['hr.employee'].create({
            'name': 'Consultant Tier 1',
            'work_email': 'tier1.consultant@inno.ai.vn',
        })
        res_t1 = staging_model._resolve_consultant('tier1.consultant@inno.ai.vn')
        self.assertEqual(res_t1.id, emp_t1.id)

        # Tier 2: Via res.users email / login linked to hr.employee
        user_t2 = new_test_user(
            self.env, login='tier2_user@inno.ai.vn', name='Tier 2 User',
            email='tier2_user@inno.ai.vn', groups='base.group_user'
        )
        emp_t2 = self.env['hr.employee'].create({
            'name': 'Consultant Tier 2',
            'user_id': user_t2.id,
            'work_email': 'different_work_email@inno.ai.vn',
        })
        res_t2 = staging_model._resolve_consultant('tier2_user@inno.ai.vn')
        self.assertEqual(res_t2.id, emp_t2.id)

        # Tier 3: Via res.partner email linked to hr.employee work_contact_id
        partner_t3 = self.env['res.partner'].create({
            'name': 'Partner Tier 3',
            'email': 'tier3_partner@inno.ai.vn',
        })
        emp_t3 = self.env['hr.employee'].create({
            'name': 'Consultant Tier 3',
            'work_contact_id': partner_t3.id,
        })
        res_t3 = staging_model._resolve_consultant('tier3_partner@inno.ai.vn')
        self.assertEqual(res_t3.id, emp_t3.id)

    def test_08_row_level_duplicate_detection_and_partial_commit(self):
        """Test row-level duplicate detection against account.analytic.line and intra-batch collisions."""
        # 1. Existing timesheet already committed in account.analytic.line
        self.env['account.analytic.line'].create({
            'name': 'Previously committed work',
            'project_id': self.project.id,
            'task_id': self.task.id,
            'employee_id': self.employee.id,
            'date': fields.Date.from_string('2026-10-20'),
            'unit_amount': 3.5,
        })

        # 2. Submission contains:
        # Row 1: Duplicate against existing analytic line (date: 2026-10-20, task, employee)
        # Row 2: Unique valid line (date: 2026-10-21, task, employee)
        # Row 3: Intra-batch duplicate matching Row 2 (date: 2026-10-21, task, employee)
        body = (
            "2026-10-20 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 3.5 | Row duplicate with existing AAL\n"
            "2026-10-21 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 4.0 | New unique line\n"
            "2026-10-21 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 4.0 | Intra-batch collision with row 2\n"
        )
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Duplicate Detection Batch Test',
            'sender_email': 'consultant.a@inno.ai.vn',
            'raw_email_body': body,
            'submission_channel': 'email_pubsub',
        })
        staging.action_parse_content()

        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(staging.parse_status, 'partial_error')
        self.assertEqual(len(staging.line_ids), 3)

        duplicates = staging.line_ids.filtered(lambda l: l.state == 'duplicate')
        valids = staging.line_ids.filtered(lambda l: l.state == 'valid')
        self.assertEqual(len(duplicates), 2)
        self.assertEqual(len(valids), 1)

        # Only the valid line should count toward total_hours
        self.assertEqual(staging.total_hours, 4.0)

        # 3. Manager 1-click approval commits ONLY valid lines, cleanly skipping duplicates
        staging.with_user(self.pm_user).action_approve_and_commit()
        self.assertEqual(staging.state, 'approved')

        committed_line = staging.line_ids.filtered(lambda l: l.state == 'committed')
        self.assertEqual(len(committed_line), 1)
        self.assertTrue(committed_line.analytic_line_id)
        self.assertEqual(committed_line.analytic_line_id.unit_amount, 4.0)

    def test_09_message_new_email_gateway_ingestion(self):
        """Test inbound email gateway routing via message_new() with XLSX attachment."""
        rows = [
            ['Date', 'Project', 'Task', 'Hours', 'Description'],
            ['2026-10-22', 'Innoria ERP Implementation', 'Explore Phase Architecture Workshop', 6.0, 'Email gateway XLSX delivery'],
        ]
        xlsx_bytes = self._create_xlsx(rows)

        msg_dict = {
            'message_id': '<test_email_gw_12345@inno.ai.vn>',
            'from': 'Nguyen Van A <consultant.a@inno.ai.vn>',
            'email_from': 'consultant.a@inno.ai.vn',
            'to': 'info@inno.ai.vn',
            'subject': 'Weekly Timesheet Submission - Week 42',
            'body': 'Dear PM,\nPlease find attached my timesheet for Week 42.\nBest regards,\nNguyen Van A',
            'attachments': [
                ('timesheet_w42.xlsx', xlsx_bytes)
            ]
        }

        staging = self.env['al2c.timesheet.staging'].message_new(msg_dict)

        self.assertEqual(staging.name, 'Weekly Timesheet Submission - Week 42')
        self.assertEqual(staging.sender_email, 'consultant.a@inno.ai.vn')
        self.assertEqual(staging.employee_id.id, self.employee.id)
        self.assertEqual(staging.submission_channel, 'email_pubsub')
        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(staging.parse_status, 'success')
        self.assertEqual(len(staging.line_ids), 1)
        self.assertEqual(staging.line_ids[0].unit_amount, 6.0)
        self.assertEqual(staging.line_ids[0].name, 'Email gateway XLSX delivery')

    def test_10_all_duplicates_approval_rejection(self):
        """Test that if all rows in a batch are duplicates, approval raises UserError."""
        # Pre-seed an analytic line
        self.env['account.analytic.line'].create({
            'name': 'Existing committed task',
            'project_id': self.project.id,
            'task_id': self.task.id,
            'employee_id': self.employee.id,
            'date': fields.Date.from_string('2026-10-25'),
            'unit_amount': 5.0,
        })

        body = "2026-10-25 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 5.0 | Duplicate task submission\n"
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'All Duplicate Batch Test',
            'sender_email': 'consultant.a@inno.ai.vn',
            'raw_email_body': body,
        })
        staging.action_parse_content()

        self.assertEqual(staging.state, 'parsed')
        self.assertEqual(len(staging.line_ids), 1)
        self.assertEqual(staging.line_ids[0].state, 'duplicate')

        with self.assertRaises(UserError):
            staging.with_user(self.pm_user).action_approve_and_commit()

