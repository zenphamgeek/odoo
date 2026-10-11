# -*- coding: utf-8 -*-
from odoo import Command
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from .test_al2c import _isolate_dev_db


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cEinvoiceAdapter(TransactionCase):
    """
    Unit & Integration Tests for Decree 70/2025 Statutory E-Invoice Adapter Interface (AL2C-INV-001).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Saigon Tech Services JSC',
            'vat': '0309998888',
            'street': '72 Le Thanh Ton, District 1, Ho Chi Minh City',
            'is_company': True,
        })
        cls.sku = cls.env['product.product'].search([('default_code', '=', 'ERP-STARTER')], limit=1)

    def _create_and_post_invoice(self):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.sku.id,
                'product_uom_qty': 1,
                'price_unit': self.sku.list_price,
            })],
        })
        so.action_confirm()
        # Mark delivered to allow invoicing
        so.order_line.qty_delivered = 1.0
        invoices = so._create_invoices()
        inv = invoices[0]
        inv.action_post()
        return inv

    def test_draft_invoice_cannot_issue_einvoice(self):
        inv = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
        })
        with self.assertRaises(UserError):
            inv.action_issue_einvoice()

    def test_decree_70_einvoice_issuance_sandbox(self):
        inv = self._create_and_post_invoice()
        self.assertEqual(inv.state, 'posted')
        self.assertEqual(inv.al2c_einvoice_state, 'draft')

        # Issue statutory Decree 70/2025 E-Invoice
        inv.action_issue_einvoice()

        self.assertEqual(inv.al2c_einvoice_state, 'issued')
        self.assertTrue(inv.al2c_einvoice_number.startswith('1C26TAA-'))
        self.assertTrue(len(inv.al2c_einvoice_lookup_code) >= 32)
        self.assertTrue(inv.al2c_einvoice_lookup_code.startswith('00'))
        self.assertIn('https://hoadondientu.gdt.gov.vn/tra-cuu', inv.al2c_einvoice_qr_code)
        self.assertEqual(len(inv.al2c_einvoice_xml_hash), 64, "SHA-256 hash must be 64 hexadecimal characters")

        # Verify XML payload structure
        xml = inv.al2c_einvoice_xml_payload
        self.assertIn('<HDon', xml)
        self.assertIn('<PBan>2.1.0</PBan>', xml)
        self.assertIn('<THDon>HÓA ĐƠN GIÁ TRỊ GIA TĂNG</THDon>', xml)
        self.assertIn(self.partner.vat, xml)

    def test_duplicate_einvoice_issuance_prevented(self):
        inv = self._create_and_post_invoice()
        inv.action_issue_einvoice()
        self.assertEqual(inv.al2c_einvoice_state, 'issued')

        with self.assertRaises(UserError):
            inv.action_issue_einvoice()

    def test_cancel_einvoice(self):
        inv = self._create_and_post_invoice()
        inv.action_issue_einvoice()
        self.assertEqual(inv.al2c_einvoice_state, 'issued')

        inv.action_cancel_einvoice(reason="Customer requested corporate name correction")
        self.assertEqual(inv.al2c_einvoice_state, 'cancelled')
