# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Test Suite.

import time
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestAl2cTimesheetBillingConfirmation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Corporation A',
            'email': 'client.rep@clientcorp.vn',
            'is_company': True,
        })
        cls.company = cls.env.company
        cls.consultant_emp = cls.env['hr.employee'].create({
            'name': 'Verified Consultant Lead',
            'work_email': 'lead.consultant@inno.ai.vn',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'ERP Implementation Saigon Newport',
            'partner_id': cls.partner.id,
            'allow_timesheets': True,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Realize Phase Core Configuration',
            'project_id': cls.project.id,
        })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': '2026-10-13',
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting Services (T&M)',
                'quantity': 40.0,
                'price_unit': 2000000.0,
            })],
        })

    def test_01_token_generation_and_verification(self):
        """Validates HMAC signature and expiry for timesheet confirmation token (CWE-639 IDOR defense)."""
        move = self.invoice
        token = move._generate_timesheet_token(move.id, expires_in_days=7)
        self.assertTrue(token, "Token must be non-empty")
        self.assertIn('_', token, "Token must contain timestamp-signature delimiter")

        # 1. Valid token succeeds
        self.assertTrue(move._verify_timesheet_token(move.id, token), "Valid token must verify successfully")

        # 2. Tampered token fails
        tampered_token = token[:-4] + "ffff"
        self.assertFalse(move._verify_timesheet_token(move.id, tampered_token), "Tampered token must fail verification")

        # 3. Wrong move ID fails (prevents token reuse across invoices)
        self.assertFalse(move._verify_timesheet_token(move.id + 9999, token), "Token scoped to wrong move must fail")

        # 4. Expired token fails
        expired_token = f"{int(time.time() - 3600)}_fakesig"
        self.assertFalse(move._verify_timesheet_token(move.id, expired_token), "Expired token must fail verification")

        # 5. Malformed tokens fail safely
        self.assertFalse(move._verify_timesheet_token(move.id, None))
        self.assertFalse(move._verify_timesheet_token(move.id, ""))
        self.assertFalse(move._verify_timesheet_token(move.id, "invalid_shape_without_proper_delimiter_and_hash"))

    def test_02_action_send_timesheet_statement(self):
        """action_send_timesheet_statement sets state to sent_to_client and generates token."""
        move = self.invoice
        move.action_send_timesheet_statement()
        self.assertEqual(move.al2c_timesheet_statement_state, 'sent_to_client')
        self.assertTrue(move.al2c_timesheet_token)
        self.assertTrue(move._verify_timesheet_token(move.id, move.al2c_timesheet_token))

    def test_03_action_client_confirm_timesheet(self):
        """action_client_confirm_timesheet transitions to confirmed with audit trail."""
        move = self.invoice
        move.action_send_timesheet_statement()
        token = move.al2c_timesheet_token

        # Confirm with valid token
        move.action_client_confirm_timesheet(token=token, confirmed_by='Nguyen Van Khach')
        self.assertEqual(move.al2c_timesheet_statement_state, 'confirmed')
        self.assertTrue(move.al2c_timesheet_confirmed_date)
        self.assertEqual(move.al2c_timesheet_confirmed_by, 'Nguyen Van Khach')

        # Idempotent confirmation call preserves confirmed state
        move.action_client_confirm_timesheet(token=token, confirmed_by='Nguyen Van Khach')
        self.assertEqual(move.al2c_timesheet_statement_state, 'confirmed')

    def test_04_tampered_token_raises_error(self):
        """action_client_confirm_timesheet raises UserError when token is tampered."""
        move = self.invoice.copy()
        move.action_send_timesheet_statement()
        with self.assertRaises(UserError):
            move.action_client_confirm_timesheet(token='invalid_token_12345')

    def test_05_quarantined_staging_cannot_be_approved(self):
        """Quarantined timesheet submissions (CWE-346 / CWE-20) are blocked from being approved."""
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Quarantine Invariant Test',
            'sender_email': 'attacker@unverified-external-domain.xyz',
            'is_quarantined': True,
            'dmarc_status': 'fail',
            'state': 'parsed',
        })
        self.env['al2c.timesheet.staging.line'].create({
            'staging_id': staging.id,
            'date': '2026-10-13',
            'employee_id': self.consultant_emp.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'unit_amount': 8.0,
            'name': 'Unauthorized consultation hours',
            'state': 'valid',
        })
        # Attempting to commit quarantined staging must raise UserError
        with self.assertRaises(UserError):
            staging.action_approve_and_commit()

    def test_06_dmarc_fail_triggers_quarantine(self):
        """Inbound email with DMARC failure is quarantined automatically in message_new."""
        msg_dict = {
            'email_from': 'spoofed.lead@inno.ai.vn',
            'subject': 'Spoofed Timesheet Submission',
            'body': '2026-10-13,ERP Implementation Saigon Newport,Realize Phase Core Configuration,8.0,Core config',
            'headers': {
                'Authentication-Results': 'mx.google.com; dmarc=fail (p=REJECT dis=REJECT) header.from=inno.ai.vn; spf=fail',
            }
        }
        staging = self.env['al2c.timesheet.staging'].message_new(msg_dict)
        self.assertTrue(staging.is_quarantined, "DMARC failure must trigger quarantine")
        self.assertEqual(staging.dmarc_status, 'fail', "dmarc_status must record 'fail'")
