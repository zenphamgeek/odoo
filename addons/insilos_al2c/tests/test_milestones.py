# -*- coding: utf-8 -*-
from odoo import Command
from odoo.tests import TransactionCase, tagged
from .test_al2c import _isolate_dev_db, PHASES


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cMilestones(TransactionCase):
    """
    Tests for AL2C-INV-101 (Weighted Milestone Invoicing: 15/25/35/15/10)
    and AL2C-PRJ-002 (Customer Sign-Off Token on Milestones).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Client JSC',
            'email': 'client@example.com',
            'is_company': True,
        })
        cls.sku_growth = cls.env['product.product'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)

    def test_milestone_sow_weights_and_signoff_gate(self):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku_growth.id,
                'product_uom_qty': 1,
                'price_unit': self.sku_growth.list_price,
            })],
        })
        so.action_confirm()
        self.assertEqual(so.state, 'sale')

        line = so.order_line
        project = line.project_id
        self.assertTrue(project)

        milestones = project.milestone_ids.sorted('sequence')
        self.assertEqual(len(milestones), 5)
        self.assertEqual(milestones.mapped('name'), PHASES)

        # Expected SOW weights: Prepare 15%, Explore 25%, Realize 35%, Deploy 15%, Run 10%
        expected_weights = [0.15, 0.25, 0.35, 0.15, 0.10]
        for ms, expected_weight in zip(milestones, expected_weights):
            self.assertAlmostEqual(ms.quantity_percentage, expected_weight, places=2,
                                   msg=f"Milestone {ms.name} must have SOW weight {expected_weight}")

        ms_prepare = milestones[0]
        # Initially not reached, not billing eligible
        self.assertFalse(ms_prepare.is_reached)
        self.assertFalse(ms_prepare.al2c_billing_eligible)

        # Reaching milestone without signoff doc: reached is True but billing eligible is False
        ms_prepare.is_reached = True
        self.assertFalse(ms_prepare.al2c_billing_eligible, "Billing eligible requires sign-off document token")

        # Register sign-off document token (AL2C-PRJ-002)
        doc = self.env['documents.document'].create({
            'name': 'ERP_Starter_Kickoff_Acceptance.pdf',
            'mimetype': 'application/pdf',
        })
        ms_prepare.action_register_signoff(doc.id)
        self.assertTrue(ms_prepare.al2c_billing_eligible, "Milestone with signed doc is billing eligible")
        self.assertEqual(ms_prepare.al2c_signoff_document_id, doc)

        # Delivered qty is exactly 15% (0.15)
        self.assertAlmostEqual(line.qty_delivered, 0.15, places=2)

        # Invoice creation reflects exactly 15% of contract value
        invoices = so._create_invoices()
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        inv_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.sku_growth)
        self.assertAlmostEqual(inv_line.quantity, 0.15, places=2)
