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
        cls.vnd_currency = cls.env.ref('base.VND')
        cls.usd_currency = cls.env.ref('base.USD')
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

    def test_07_multicurrency_timesheet_staging_rate_card(self):
        """Validates multi-currency rate cards (USD/EUR) and company currency (VND) conversions in timesheet staging."""
        usd_currency = self.env.ref('base.USD')
        vnd_currency = self.env.ref('base.VND')
        staging = self.env['al2c.timesheet.staging'].create({
            'name': 'Global Delivery USD Timesheet',
            'sender_email': 'lead.consultant@inno.ai.vn',
            'currency_id': usd_currency.id,
            'company_currency_id': vnd_currency.id,
            'exchange_rate_snapshot': 25400.0,
            'state': 'parsed',
        })
        line = self.env['al2c.timesheet.staging.line'].create({
            'staging_id': staging.id,
            'date': '2026-10-13',
            'employee_id': self.consultant_emp.id,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'unit_amount': 10.0,
            'hourly_rate': 150.0,
            'currency_id': usd_currency.id,
            'company_currency_id': vnd_currency.id,
            'name': 'Senior Cloud Architect Delivery (USD)',
            'state': 'valid',
        })
        self.assertEqual(line.amount_billable, 1500.0, "10h @ $150/h must equal $1500.0")
        self.assertEqual(line.amount_billable_company_currency, 38100000.0, "$1500 @ 25,400 rate must equal 38,100,000 VND")
        staging.invalidate_recordset()
        self.assertEqual(staging.total_hours, 10.0)
        self.assertEqual(staging.total_amount_billable, 1500.0)
        self.assertEqual(staging.total_amount_billable_company_currency, 38100000.0)

    def test_08_multicurrency_invoice_statement_snapshot(self):
        """Validates statement generation, exchange rate snapshotting and Decree 70 statutory VND total."""
        vnd_currency = self.env.ref('base.VND')
        foreign_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_date': '2026-10-13',
            'invoice_line_ids': [(0, 0, {
                'name': 'AI Solution Architecture Consulting (40 hrs @ 2,540,000 VND/hr)',
                'quantity': 40.0,
                'price_unit': 2540000.0,
            })],
        })
        foreign_invoice.currency_id = vnd_currency
        self.assertTrue(foreign_invoice.al2c_is_foreign_currency, "Invoice in VND with USD company must be foreign currency")
        self.assertEqual(foreign_invoice.amount_total, 101600000.0, "Total invoice must be 101,600,000 VND")
        self.assertEqual(foreign_invoice.al2c_timesheet_hours_total, 40.0, "Total timesheet hours must be 40.0")

        # Send statement to client -> snapshots exchange rate
        foreign_invoice.action_send_timesheet_statement()
        self.assertEqual(foreign_invoice.al2c_timesheet_statement_state, 'sent_to_client')
        self.assertGreater(foreign_invoice.al2c_exchange_rate_snapshot, 0.0, "Exchange rate snapshot must be recorded")
        expected_comp = self.company.currency_id.round(101600000.0 * foreign_invoice.al2c_exchange_rate_snapshot)
        self.assertEqual(
            foreign_invoice.al2c_statement_amount_total_company_currency,
            expected_comp,
            "Statutory total in company currency must match snapshotted conversion"
        )

        # Confirm statement via 1-click token
        token = foreign_invoice.al2c_timesheet_token
        foreign_invoice.action_client_confirm_timesheet(token=token, confirmed_by='Director of Technology')
        self.assertEqual(foreign_invoice.al2c_timesheet_statement_state, 'confirmed')
        self.assertEqual(foreign_invoice.al2c_timesheet_confirmed_by, 'Director of Technology')

    def test_09_adv_missing_rate_must_fail_closed(self):
        """Verify Decree 70/2025 invariant: Disallow default 1.0 fallback on missing rate."""
        test_curr = self.env['res.currency'].create({
            'name': 'XTS',
            'symbol': 'XTS',
            'rounding': 0.01,
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'currency_id': test_curr.id,
            'invoice_date': '2026-10-13',
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting Services',
                'quantity': 10,
                'price_unit': 100.0,
            })]
        })
        invoice._compute_al2c_statement_company_currency()
        self.assertTrue(invoice.al2c_rate_unavailable, "Rate must be marked unavailable when lookup fails")
        self.assertEqual(invoice.al2c_statement_amount_total_company_currency, 0.0)

        # Expect hard failure on statement send rather than silent corruption
        with self.assertRaises(UserError):
            invoice.action_send_timesheet_statement()

    def test_10_adv_uom_dimensional_conversion(self):
        """Verify Days are converted to Hours accurately in total timesheet calculation."""
        uom_day = self.env.ref('uom.product_uom_day', raise_if_not_found=False)
        uom_hour = self.env.ref('uom.product_uom_hour', raise_if_not_found=False)
        if not uom_day or not uom_hour:
            return
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Architecture Consulting (Days)',
                    'quantity': 2,
                    'product_uom_id': uom_day.id,
                    'price_unit': 800.0,
                }),
                (0, 0, {
                    'name': 'Ad-hoc Code Review (Hours)',
                    'quantity': 4,
                    'product_uom_id': uom_hour.id,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section: Timesheet Deliverables',
                    'quantity': 0,
                })
            ]
        })
        invoice._compute_al2c_timesheet_hours_total()
        # 2 Days * 8 Hours/Day + 4 Hours = 20.0 Hours
        expected_hours = (2.0 * uom_day.factor_inv / uom_hour.factor_inv) + 4.0 if (uom_day.factor and uom_hour.factor) else 20.0
        self.assertAlmostEqual(invoice.al2c_timesheet_hours_total, expected_hours, places=1, msg="UoM dimensional conversion failed!")

    def test_11_adv_token_lease_idempotency(self):
        """Verify re-dispatching statement does not revoke existing client token."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting',
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })
        invoice.action_send_timesheet_statement()
        token_first = invoice.al2c_timesheet_token
        self.assertTrue(token_first, "Initial token was not generated.")

        # Re-send statement
        invoice.action_send_timesheet_statement()
        token_second = invoice.al2c_timesheet_token
        self.assertEqual(token_first, token_second, "Token changed on re-dispatch (violates lease idempotency).")

    def test_12_adv_negative_keyword_exclusion(self):
        """Lines containing negative/exclusion keywords are not classified as billable timesheets."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'No consulting included - software license package',
                    'quantity': 10,
                    'price_unit': 500.0,
                }),
                (0, 0, {
                    'name': 'Giảm giá tư vấn hợp đồng tháng 10',
                    'quantity': 5,
                    'price_unit': -100.0,
                }),
                (0, 0, {
                    'name': 'Senior Architect Consultation (hours)',
                    'quantity': 8,
                    'price_unit': 150.0,
                }),
            ]
        })
        invoice._compute_al2c_timesheet_hours_total()
        self.assertEqual(invoice.al2c_timesheet_hours_total, 8.0, "Negative keyword lines must be excluded from timesheets.")

    def test_13_adv_expired_token_rotates_on_redispatch(self):
        """Expired token on re-dispatch is automatically rotated to a fresh valid token."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting',
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })
        # Simulate expired token from 8 days ago
        expired_ts = int(time.time() - 86400)
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret') or 'al2c_secret_salt_2026'
        import hmac, hashlib
        msg = f"{invoice.id}:{expired_ts}"
        sig = hmac.new(secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()[:32]
        invoice.al2c_timesheet_token = f"{expired_ts}_{sig}"

        # Re-dispatch statement -> should rotate token because previous is expired
        invoice.action_send_timesheet_statement()
        self.assertNotEqual(invoice.al2c_timesheet_token, f"{expired_ts}_{sig}", "Expired token must be rotated.")
        self.assertTrue(invoice._verify_timesheet_token(invoice.id, invoice.al2c_timesheet_token), "New token must be valid.")

    def test_14_adv_same_currency_never_trips_rate_unavailable(self):
        """Same-currency invoice sets al2c_rate_unavailable = False and dispatches cleanly."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'currency_id': self.company.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Domestic IT Consulting',
                'quantity': 10,
                'price_unit': 1000000.0,
            })]
        })
        invoice._compute_al2c_statement_company_currency()
        self.assertFalse(invoice.al2c_rate_unavailable, "Same-currency invoice must never flag rate unavailable.")
        self.assertEqual(invoice.al2c_statement_amount_total_company_currency, 10000000.0)
        # Dispatch must succeed without error
        invoice.action_send_timesheet_statement()
        self.assertEqual(invoice.al2c_timesheet_statement_state, 'sent_to_client')


