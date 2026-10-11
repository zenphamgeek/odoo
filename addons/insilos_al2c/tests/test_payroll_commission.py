# -*- coding: utf-8 -*-
from odoo import Command
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from .test_al2c import _isolate_dev_db
from ..models.hr_payslip import calculate_vn_2026_insurance, calculate_vn_2026_pit


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cPayrollCommission(TransactionCase):
    """
    Unit & Integration Tests for:
    - Cash-Matched Sales Commission (AL2C-PAY-001)
    - 2026 Vietnamese 5-Bracket PIT & Statutory Insurance Caps (AL2C-PAY-002)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Mekong Distribution Corp',
            'is_company': True,
        })
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Senior Account Executive',
            'login': 'sales_ae_vn',
            'email': 'ae@innoria.com',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Senior Account Executive',
            'user_id': cls.sales_user.id,
            'work_email': 'ae@innoria.com',
        })
        cls.sku = cls.env['product.product'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)

    def test_2026_vietnamese_statutory_insurance_caps(self):
        # Case 1: Gross 30M VND (below social cap 46.8M and unemp cap 99.2M)
        ins_30m = calculate_vn_2026_insurance(30_000_000)
        self.assertEqual(ins_30m['bhxh'], 2_400_000)   # 8%
        self.assertEqual(ins_30m['bhyt'], 450_000)     # 1.5%
        self.assertEqual(ins_30m['bhtn'], 300_000)     # 1.0%
        self.assertEqual(ins_30m['total_insurance'], 3_150_000)

        # Case 2: Gross 60M VND (above social cap 46.8M, below unemp cap 99.2M)
        ins_60m = calculate_vn_2026_insurance(60_000_000)
        self.assertEqual(ins_60m['bhxh'], 3_744_000)   # 46.8M * 8%
        self.assertEqual(ins_60m['bhyt'], 702_000)     # 46.8M * 1.5%
        self.assertEqual(ins_60m['bhtn'], 600_000)     # 60M * 1.0%
        self.assertEqual(ins_60m['total_insurance'], 5_046_000)

        # Case 3: High earner 120M VND (above both caps 46.8M and 99.2M)
        ins_120m = calculate_vn_2026_insurance(120_000_000)
        self.assertEqual(ins_120m['bhxh'], 3_744_000)
        self.assertEqual(ins_120m['bhyt'], 702_000)
        self.assertEqual(ins_120m['bhtn'], 992_000)   # 99.2M * 1.0%
        self.assertEqual(ins_120m['total_insurance'], 5_438_000)

    def test_2026_vietnamese_5_bracket_pit_calculations(self):
        # <= 0 taxable income
        self.assertEqual(calculate_vn_2026_pit(0), 0.0)
        self.assertEqual(calculate_vn_2026_pit(-5_000_000), 0.0)

        # Bracket 1 (<= 10M VND @ 5%)
        # 8,000,000 * 5% = 400,000 VND
        self.assertEqual(calculate_vn_2026_pit(8_000_000), 400_000.0)

        # Bracket 2 (10M - 30M VND @ 10%)
        # Taxable 11,350,000: 500k + (1.35M * 10%) = 635,000 VND
        self.assertEqual(calculate_vn_2026_pit(11_350_000), 635_000.0)

        # Bracket 3 (30M - 60M VND @ 20%)
        # Taxable 33,254,000: 2.5M + (3.254M * 20%) = 3,150,800 VND
        self.assertEqual(calculate_vn_2026_pit(33_254_000), 3_150_800.0)

        # Bracket 4 (60M - 100M VND @ 30%)
        # Taxable 70,000,000: 8.5M + (10M * 30%) = 11,500,000 VND
        self.assertEqual(calculate_vn_2026_pit(70_000_000), 11_500_000.0)

        # Bracket 5 (> 100M VND @ 35%)
        # Taxable 120,000,000: 20.5M + (20M * 35%) = 27,500,000 VND
        self.assertEqual(calculate_vn_2026_pit(120_000_000), 27_500_000.0)

    def test_cash_matched_sales_commission_lifecycle(self):
        # 1. Create SO closed by AE
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.sales_user.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku.id,
                'product_uom_qty': 1,
                'price_unit': 450_000_000,
            })],
        })
        so.action_confirm()
        so.order_line.qty_delivered = 1.0

        # 2. Invoicing
        invoices = so._create_invoices()
        inv = invoices[0]
        inv.action_post()

        # Before payment, no commission entries exist
        ledger_model = self.env['al2c.commission.ledger']
        entries = ledger_model.search([('invoice_id', '=', inv.id)])
        self.assertFalse(entries, "Commission must not be created on uncollected invoice")

        # 3. Customer pays / reconciles cash
        inv.action_process_cash_matched_commission()
        entries = ledger_model.search([('invoice_id', '=', inv.id)])
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.employee_id, self.employee)
        self.assertEqual(entry.base_amount, 450_000_000)
        # Default commission rate 5% -> 22,500,000 VND
        self.assertEqual(entry.amount, 22_500_000)
        self.assertEqual(entry.state, 'pending')

        # 4. Partial Credit Note (Clawback)
        refund_move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_refund',
            'invoice_user_id': self.sales_user.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.sku.id,
                'quantity': 0.2,
                'price_unit': 450_000_000,
            })],
        })
        refund_move.action_post()
        refund_move.action_process_cash_matched_commission()

        refund_entries = ledger_model.search([('invoice_id', '=', refund_move.id)])
        self.assertEqual(len(refund_entries), 1)
        clawback = refund_entries[0]
        self.assertEqual(clawback.amount, -4_500_000, "Credit note must create negative commission clawback")

        # 5. Sync into draft payslip
        payslip = self.env['hr.payslip'].create({
            'name': 'Monthly Salary - AE',
            'employee_id': self.employee.id,
        })
        payslip.action_sync_al2c_commission()

        comm_inputs = payslip.input_line_ids.filtered(lambda l: l.code == 'COMMISSION')
        self.assertTrue(comm_inputs)
        # Net commission: 22,500,000 - 4,500,000 = 18,000,000 VND
        self.assertEqual(comm_inputs.amount, 18_000_000.0)
        self.assertEqual(entry.state, 'included')
        self.assertEqual(clawback.state, 'included')
