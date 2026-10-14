# -*- coding: utf-8 -*-
import datetime
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'security', 'adversarial', 'pinned_conversion', 'TestAdversarialPinnedConversionWorker')
class TestAdversarialPinnedConversionWorker(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.currency_vnd = cls.env.ref('base.VND')
        cls.currency_usd = cls.env.ref('base.USD')

        # Multi-tenant isolated company with separate operating currency
        cls.company_b = cls.env['res.company'].create({
            'name': 'Tenant Beta International Corp',
            'currency_id': cls.currency_vnd.id,
            'country_id': cls.env.ref('base.vn').id,
        })

        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Client Alpha Enterprise',
            'company_id': cls.company_a.id,
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Client Beta Global',
            'company_id': cls.company_b.id,
        })

    def test_01_multi_tenant_company_isolation(self):
        """SEC-06 / SEC-05: Multi-Tenant Boundary & Company Isolation
        Ensure pinned conversions execute strictly within the respective tenant's company context,
        evaluating exchange rates against the tenant company's currency rather than the environment's default.
        """
        # Order A in Company A (Company currency: USD or VND)
        order_a = self.env['sale.order'].with_company(self.company_a).create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
        })

        # Order B in Company B (Company currency: VND)
        order_b = self.env['sale.order'].with_company(self.company_b).create({
            'partner_id': self.partner_b.id,
            'company_id': self.company_b.id,
            'currency_id': self.currency_usd.id,
            'is_pinned_rate': True,
            'state': 'draft',
        })

        # Execute conversion worker
        res = self.env['sale.order'].cron_process_pinned_conversions()
        self.assertTrue(res, "Cron worker must return True upon completion")

        order_a.invalidate_recordset()
        order_b.invalidate_recordset()

        # Both orders must have pinned_exchange_rate computed
        self.assertGreater(order_a.pinned_exchange_rate, 0.0, "Order A must have computed pinned rate")
        self.assertGreater(order_b.pinned_exchange_rate, 0.0, "Order B must have computed pinned rate")

        # Verify rate calculation is company-isolated
        expected_rate_a = self.env['res.currency']._get_conversion_rate(
            from_currency=order_a.currency_id,
            to_currency=self.company_a.currency_id,
            company=self.company_a,
            date=order_a.date_order or fields.Date.context_today(order_a),
        )
        expected_rate_b = self.env['res.currency']._get_conversion_rate(
            from_currency=order_b.currency_id,
            to_currency=self.company_b.currency_id,
            company=self.company_b,
            date=order_b.date_order or fields.Date.context_today(order_b),
        )

        self.assertAlmostEqual(order_a.pinned_exchange_rate, expected_rate_a, places=5)
        self.assertAlmostEqual(order_b.pinned_exchange_rate, expected_rate_b, places=5)

        # Leases must be cleared upon successful processing
        self.assertFalse(order_a.conversion_lease_token)
        self.assertFalse(order_a.conversion_lease_time)
        self.assertFalse(order_b.conversion_lease_token)
        self.assertFalse(order_b.conversion_lease_time)

    def test_02_deadlock_and_partial_batch_recovery(self):
        """SEC-06: Partial Batch Recovery & ACID Savepoint Guard
        Ensure an unexpected exception or deadlock in one order rolls back only that individual order's
        savepoint, allowing remaining orders in the batch to commit successfully without atomic batch abort.
        """
        so1 = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
        })
        so2 = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
        })
        so3 = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
        })

        original_execute = self.env['sale.order'].__class__._execute_pinned_conversion_logic

        def mock_execute(order_self):
            if order_self.id == so2.id:
                raise RuntimeError("Adversarial injection: Simulated deadlock or poison pill failure")
            return original_execute(order_self)

        with patch.object(self.env['sale.order'].__class__, '_execute_pinned_conversion_logic', side_effect=mock_execute, autospec=True):
            res = self.env['sale.order'].cron_process_pinned_conversions()
            self.assertTrue(res, "Cron worker must not crash when an individual order fails in savepoint")

        so1.invalidate_recordset()
        so2.invalidate_recordset()
        so3.invalidate_recordset()

        # SO1 and SO3 must be successfully processed
        self.assertGreater(so1.pinned_exchange_rate, 0.0, "Order 1 must be successfully processed")
        self.assertFalse(so1.conversion_lease_token, "Order 1 lease must be cleared")
        self.assertGreater(so3.pinned_exchange_rate, 0.0, "Order 3 must be successfully processed")
        self.assertFalse(so3.conversion_lease_token, "Order 3 lease must be cleared")

        # SO2 must be rolled back by savepoint
        self.assertEqual(so2.pinned_exchange_rate, 0.0, "Poison order rate must remain 0.0")
        self.assertFalse(so2.conversion_lease_token, "Failed order lease must be rolled back by savepoint")

    def test_03_expired_lease_reclaim(self):
        """SEC-06: Heartbeat Pinned Lease Protocol (HPLP) Expired Lease Reclaim
        Verify that orders locked by a dead/timed-out worker (conversion_lease_time < threshold)
        are safely reclaimed and converted, while orders with active unexpired leases are untouched.
        """
        now = fields.Datetime.now()

        # SO with expired lease (leased 20 minutes ago, timeout is 10 minutes)
        so_expired = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
            'conversion_lease_token': 'stale_worker_deadlock_token_99',
            'conversion_lease_time': now - datetime.timedelta(minutes=20),
        })

        # SO with active unexpired lease (expires in 5 minutes)
        so_active = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
            'conversion_lease_token': 'active_live_worker_token_42',
            'conversion_lease_time': now + datetime.timedelta(minutes=5),
        })

        # SO with no lease (fresh)
        so_fresh = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_a.id,
            'currency_id': self.currency_vnd.id,
            'is_pinned_rate': True,
            'state': 'draft',
            'conversion_lease_token': False,
            'conversion_lease_time': False,
        })

        # Execute cron
        self.env['sale.order'].cron_process_pinned_conversions()

        so_expired.invalidate_recordset()
        so_active.invalidate_recordset()
        so_fresh.invalidate_recordset()

        # Expired lease was reclaimed and completed
        self.assertGreater(so_expired.pinned_exchange_rate, 0.0, "Expired lease order must be reclaimed and processed")
        self.assertFalse(so_expired.conversion_lease_token, "Reclaimed lease token must be cleared")
        self.assertFalse(so_expired.conversion_lease_time, "Reclaimed lease time must be cleared")

        # Active lease was NOT touched or stolen
        self.assertEqual(so_active.pinned_exchange_rate, 0.0, "Active lease order must not be modified")
        self.assertEqual(so_active.conversion_lease_token, 'active_live_worker_token_42', "Active lease token must be preserved")

        # Fresh order was converted
        self.assertGreater(so_fresh.pinned_exchange_rate, 0.0, "Fresh order must be processed")
        self.assertFalse(so_fresh.conversion_lease_token, "Fresh order lease token must be cleared")
        self.assertFalse(so_fresh.conversion_lease_time, "Fresh order lease time must be cleared")
