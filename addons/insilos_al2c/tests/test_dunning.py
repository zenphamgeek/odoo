# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import fields
from odoo.tests import TransactionCase, tagged
from .test_al2c import _isolate_dev_db


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cDunning(TransactionCase):
    """
    Tests for AL2C-INV-003: Automated Dunning Ladder (D+3, D+15, D+30).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Dunning Test Partner',
            'is_company': True,
        })
        cls.account_revenue = cls.env['account.account'].search([
            ('account_type', 'in', ('income_other', 'income')),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not cls.account_revenue:
            cls.account_revenue = cls.env['account.account'].search([
                ('account_type', 'in', ('income_other', 'income')),
            ], limit=1)

    def test_dunning_ladder_transitions(self):
        today = fields.Date.context_today(self)

        # 1. Invoice not due yet
        inv = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': today,
            'invoice_date_due': today + timedelta(days=14),
            'invoice_line_ids': [(0, 0, {
                'name': 'Advisory Consulting',
                'quantity': 1,
                'price_unit': 10_000_000,
                'account_id': self.account_revenue.id,
            })],
        })
        inv.action_post()
        self.assertEqual(inv.state, 'posted')
        self.assertEqual(inv.al2c_dunning_stage, 'current')

        # 2. D+5 overdue -> d3_reminder
        inv._al2c_update_dunning_stage(as_of_date=inv.invoice_date_due + timedelta(days=5))
        self.assertEqual(inv.al2c_dunning_stage, 'd3_reminder')

        # 3. D+18 overdue -> d15_warning
        inv._al2c_update_dunning_stage(as_of_date=inv.invoice_date_due + timedelta(days=18))
        self.assertEqual(inv.al2c_dunning_stage, 'd15_warning')

        # 4. D+35 overdue -> d30_suspension
        inv._al2c_update_dunning_stage(as_of_date=inv.invoice_date_due + timedelta(days=35))
        self.assertEqual(inv.al2c_dunning_stage, 'd30_suspension')
