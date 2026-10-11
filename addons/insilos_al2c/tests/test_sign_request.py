# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from .test_al2c import _isolate_dev_db


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cSignRequestDeviation(TransactionCase):
    """
    Unit & Integration Tests for Contract Clause Deviation Scanner (AL2C-SGN-002).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Enterprise Client Ltd',
            'email': 'legal@enterpriseclient.vn',
            'is_company': True,
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'General Counsel Lead',
            'login': 'gc_lead',
            'email': 'gc@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('sales_team.group_sale_manager').id,
                cls.env.ref('sign.group_sign_user').id,
            ])],
        })
        cls.agent_user = cls.env['res.users'].create({
            'name': 'Junior Legal Agent',
            'login': 'legal_agent',
            'email': 'agent@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('sign.group_sign_user').id,
            ])],
        })
        # Create standard sign template
        cls.sign_template = cls.env['sign.template'].create({
            'name': 'Standard Enterprise MSA',
        })

    def test_standard_contract_scan_passes(self):
        req = self.env['sign.request'].create({
            'reference': 'Enterprise Agreement',
            'template_id': self.sign_template.id,
            'message': 'Please review and execute standard agreement with capped liability.',
        })
        req.action_scan_contract_deviations()
        self.assertFalse(req.al2c_has_deviation)
        self.assertEqual(req.al2c_clause_status, 'standard')

    def test_redline_with_unlimited_liability_detected(self):
        req = self.env['sign.request'].create({
            'reference': 'Enterprise Agreement',
            'template_id': self.sign_template.id,
            'message': 'Customer modified Section 8: unlimited liability for software defects.',
        })
        req.action_scan_contract_deviations()
        self.assertTrue(req.al2c_has_deviation)
        self.assertEqual(req.al2c_clause_status, 'deviated')
        self.assertIn('unlimited liability', req.al2c_deviation_summary)

        # Check GC activity scheduled
        activities = req.activity_ids.filtered(
            lambda a: 'General Counsel Approval Required' in (a.summary or '')
        )
        self.assertTrue(activities, "A General Counsel activity must be scheduled on deviation")

    def test_redline_with_excessive_penalties_detected(self):
        req = self.env['sign.request'].create({
            'reference': 'Enterprise Agreement',
            'template_id': self.sign_template.id,
        })
        redline_text = "Vendor shall pay liquidated damages of 25% and accept consequential damages."
        req.action_scan_contract_deviations(redline_text=redline_text)
        self.assertTrue(req.al2c_has_deviation)
        self.assertIn('liquidated damages', req.al2c_deviation_summary)
        self.assertIn('consequential damages', req.al2c_deviation_summary)

    def test_unauthorized_agent_cannot_self_approve_deviation(self):
        req = self.env['sign.request'].create({
            'reference': 'Enterprise Agreement',
            'template_id': self.sign_template.id,
            'message': 'Requires unlimited liability.',
        })
        req.action_scan_contract_deviations()

        with self.assertRaises(UserError):
            req.with_user(self.agent_user).action_approve_deviations()

    def test_manager_approves_deviation(self):
        req = self.env['sign.request'].create({
            'reference': 'Enterprise Agreement',
            'template_id': self.sign_template.id,
            'message': 'Demands gross negligence carveout.',
        })
        req.action_scan_contract_deviations()
        self.assertEqual(req.al2c_clause_status, 'deviated')

        req.with_user(self.manager_user).action_approve_deviations(note="Approved per Board Exception #41")
        self.assertEqual(req.al2c_clause_status, 'approved')
        self.assertEqual(req.al2c_gc_approval_user_id, self.manager_user)

    def test_signing_guard_blocks_unapproved_deviations(self):
        req = self.env['sign.request'].create({
            'reference': 'Enterprise Agreement',
            'template_id': self.sign_template.id,
            'message': 'Includes unlimited liability.',
        })
        req.action_scan_contract_deviations()

        with self.assertRaises(UserError):
            req._check_al2c_clause_guard()
