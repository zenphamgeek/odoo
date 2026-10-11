# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cMojoUsageLedger(TransactionCase):
    """
    Test suite for AL2C-SAL-203: Mojo Consumption Ledger & 80% Prepaid Burn-Down Alert.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Da Nang AI Labs',
            'email': 'ops@danangailabs.vn',
        })
        # Customer purchases 10,000,000 Mojo tokens prepaid pack
        cls.customer.action_topup_tokens(10000000.0)

    def test_prepaid_token_setup(self):
        """Prepaid token balance initialized properly."""
        self.assertEqual(self.customer.al2c_mojo_token_balance, 10000000.0)
        self.assertEqual(self.customer.al2c_mojo_token_total_purchased, 10000000.0)
        self.assertFalse(self.customer.al2c_mojo_alert_80_sent)

    def test_idempotent_usage_ingestion(self):
        """Duplicate usage requests with identical idempotency key return existing record without double-decrementing."""
        idempotency_key = "POST-REQ-UUID-889911"
        rec1 = self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.customer.id,
            quantity=1500000.0,
            meter_type='tokens',
            idempotency_key=idempotency_key,
        )
        self.assertEqual(self.customer.al2c_mojo_token_balance, 8500000.0)

        # Re-post same payload
        rec2 = self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.customer.id,
            quantity=1500000.0,
            meter_type='tokens',
            idempotency_key=idempotency_key,
        )
        self.assertEqual(rec1.id, rec2.id)
        # Balance must remain 8,500,000 (NOT 7,000,000)
        self.assertEqual(self.customer.al2c_mojo_token_balance, 8500000.0)

    def test_negative_quantity_rejected(self):
        """Negative usage quantity is strictly rejected."""
        with self.assertRaises(UserError):
            self.env['al2c.mojo.usage.ledger'].record_usage(
                partner_id=self.customer.id,
                quantity=-50000.0,
                idempotency_key="NEG-TEST-001",
            )

    def test_80_percent_burndown_alert_trigger(self):
        """Crossing 80% token consumption threshold triggers automated alert and account activity."""
        self.assertFalse(self.customer.al2c_mojo_alert_80_sent)

        # Consume 7,500,000 tokens (75% - alert should NOT trigger yet)
        self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.customer.id,
            quantity=7500000.0,
            meter_type='tokens',
            idempotency_key="BURN-TEST-75PCT",
        )
        self.assertEqual(self.customer.al2c_mojo_token_balance, 2500000.0)
        self.assertFalse(self.customer.al2c_mojo_alert_80_sent)

        # Consume additional 1,000,000 tokens (total 8,500,000 = 85% burn - triggers alert!)
        self.env['al2c.mojo.usage.ledger'].record_usage(
            partner_id=self.customer.id,
            quantity=1000000.0,
            meter_type='tokens',
            idempotency_key="BURN-TEST-85PCT",
        )
        self.assertEqual(self.customer.al2c_mojo_token_balance, 1500000.0)
        self.assertTrue(self.customer.al2c_mojo_alert_80_sent)

        # Verify activity created for account manager
        activities = self.customer.activity_ids
        if not activities:
            activities = self.env['mail.activity'].search([
                ('res_model', 'in', ('res.partner', 'party.master')),
                ('res_id', '=', self.customer.id),
            ])
        self.assertTrue(activities, "80% burn-down alert activity must be scheduled.")
        self.assertIn("80% Burn-Down", activities[0].summary)

