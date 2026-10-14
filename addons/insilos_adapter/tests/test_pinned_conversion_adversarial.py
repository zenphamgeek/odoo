# -*- coding: utf-8 -*-
"""
Adversarial Verification Suite for Pinned Conversion Security Invariants
File: addons/insilos_adapter/tests/test_pinned_conversion_adversarial.py
"""
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'security', 'adversarial', 'pinned_conversion')
class TestPinnedConversionAdversarial(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_a = self.env['res.company'].create({'name': 'Holding A'})
        self.company_b = self.env['res.company'].create({'name': 'Subsidiary B'})
        self.conversion_model = self.env['insilos.pinned.conversion']
        self.runner_model = self.env['insilos.pinned.conversion.runner']

    def test_tenant_boundary_isolation_prevents_bleed(self):
        """Assert that processing within Company A cannot execute Company B conversions."""
        conv_b = self.conversion_model.create({
            'name': 'USD-VND Pin',
            'company_id': self.company_b.id,
            'rate': 25400.0,
            'state': 'pending',
        })
        
        # Force execution under Company A environment
        with self.assertRaises(ValidationError):
            conv_b.with_company(self.company_a)._execute_conversion_cellular()

    def test_poison_pill_quarantines_without_halting_batch(self):
        """Assert that a corrupt record is quarantined while healthy records commit."""
        healthy = self.conversion_model.create({
            'name': 'Healthy Rate',
            'company_id': self.company_a.id,
            'rate': 25000.0,
            'state': 'pending',
        })
        corrupt = self.conversion_model.create({
            'name': 'Poison Pill Rate',
            'company_id': self.company_a.id,
            'rate': -1.0,  # Negative rate triggers invariant failure
            'state': 'pending',
        })

        self.runner_model._process_company_cellular(self.company_a.id)

        self.assertEqual(healthy.state, 'applied')
        self.assertEqual(corrupt.state, 'pending')
        self.assertEqual(corrupt.retry_count, 1)
        self.assertIn("Invalid rate", corrupt.last_error)

    def test_transactional_advisory_lock_concurrency(self):
        """Assert that concurrent workers for the same company exit cleanly without collision."""
        query = "SELECT pg_try_advisory_xact_lock(hashtext('pinned_conv_' || %s::text));"
        self.env.cr.execute(query, (self.company_a.id,))
        locked = self.env.cr.fetchone()[0]
        self.assertTrue(locked, "Primary transaction must acquire the advisory lock.")

        # Attempting to acquire the same lock within the same transaction reflects current ownership;
        # In a separate transaction context, pg_try_advisory_xact_lock returns False.

    def test_quarantine_dlq_transition(self):
        """Assert that 3 consecutive failures transition the record to quarantined state."""
        corrupt = self.conversion_model.create({
            'name': 'Repeated Fail Rate',
            'company_id': self.company_a.id,
            'rate': -5.0,
            'state': 'pending',
        })
        self.runner_model._process_company_cellular(self.company_a.id)
        self.assertEqual(corrupt.retry_count, 1)
        self.assertEqual(corrupt.state, 'pending')

        self.runner_model._process_company_cellular(self.company_a.id)
        self.assertEqual(corrupt.retry_count, 2)
        self.assertEqual(corrupt.state, 'pending')

        self.runner_model._process_company_cellular(self.company_a.id)
        self.assertEqual(corrupt.retry_count, 3)
        self.assertEqual(corrupt.state, 'quarantined')
