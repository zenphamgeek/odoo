# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSapMasterData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_business_partner_lexicon_and_roles(self):
        """Verify res.partner model description, field strings, and BP roles."""
        partner_model = self.env['res.partner']
        self.assertEqual(partner_model._description, "Business Partner (BP)")

        # Verify fields_get strings
        fields_info = partner_model.fields_get([
            'name', 'ref', 'vat', 'company_type', 'parent_id',
            'street', 'city', 'zip', 'country_id', 'bp_role'
        ])
        self.assertEqual(fields_info['name']['string'], "Business Partner Name")
        self.assertEqual(fields_info['ref']['string'], "BP Number / Search Term")
        self.assertEqual(fields_info['vat']['string'], "Tax Number (Tax ID / VAT)")
        self.assertEqual(fields_info['company_type']['string'], "BP Category")
        self.assertEqual(fields_info['parent_id']['string'], "Parent Business Partner")
        self.assertEqual(fields_info['street']['string'], "Street / House Number")
        self.assertEqual(fields_info['city']['string'], "City / Postal District")
        self.assertEqual(fields_info['zip']['string'], "Postal Code")
        self.assertEqual(fields_info['country_id']['string'], "Country Key")

        # Test General BP Role
        general_partner = partner_model.create({
            'name': 'General Partner Test',
            'ref': 'BP-GEN-001',
        })
        self.assertEqual(general_partner.bp_role, 'general')
        self.assertTrue(general_partner.is_bp_general)
        self.assertFalse(general_partner.is_bp_customer)
        self.assertFalse(general_partner.is_bp_vendor)

        # Test Customer BP Role
        customer_partner = partner_model.create({
            'name': 'Customer Partner Test',
            'ref': 'BP-CUST-001',
            'customer_rank': 1,
        })
        self.assertEqual(customer_partner.bp_role, 'customer')
        self.assertTrue(customer_partner.is_bp_customer)
        self.assertFalse(customer_partner.is_bp_general)

        # Test Vendor BP Role
        vendor_partner = partner_model.create({
            'name': 'Vendor Partner Test',
            'ref': 'BP-VEND-001',
            'supplier_rank': 1,
        })
        self.assertEqual(vendor_partner.bp_role, 'vendor')
        self.assertTrue(vendor_partner.is_bp_vendor)
        self.assertFalse(vendor_partner.is_bp_general)

        # Test setting bp_role inverse
        general_partner.bp_role = 'customer'
        self.assertGreaterEqual(general_partner.customer_rank, 1)
        self.assertEqual(general_partner.supplier_rank, 0)
        self.assertEqual(general_partner.bp_role, 'customer')

        general_partner.bp_role = 'vendor'
        self.assertGreaterEqual(general_partner.supplier_rank, 1)
        self.assertEqual(general_partner.customer_rank, 0)
        self.assertEqual(general_partner.bp_role, 'vendor')

        general_partner.bp_role = 'both'
        self.assertGreaterEqual(general_partner.customer_rank, 1)
        self.assertGreaterEqual(general_partner.supplier_rank, 1)
        self.assertEqual(general_partner.bp_role, 'both')

        general_partner.bp_role = 'general'
        self.assertEqual(general_partner.customer_rank, 0)
        self.assertEqual(general_partner.supplier_rank, 0)
        self.assertEqual(general_partner.bp_role, 'general')

    def test_02_material_master_lexicon_and_types(self):
        """Verify product.template and product.product description, fields, and types."""
        tmpl_model = self.env['product.template']
        self.assertEqual(tmpl_model._description, "Material Master (MM)")

        fields_info = tmpl_model.fields_get([
            'name', 'default_code', 'type', 'categ_id',
            'uom_id', 'list_price', 'standard_price', 'sap_material_type'
        ])
        self.assertEqual(fields_info['name']['string'], "Material Description")
        self.assertEqual(fields_info['default_code']['string'], "Material Number (MATNR)")
        self.assertEqual(fields_info['type']['string'], "Material Type (MTART)")
        self.assertEqual(fields_info['categ_id']['string'], "Material Group (MATKL)")
        self.assertEqual(fields_info['uom_id']['string'], "Base Unit of Measure (BUn)")
        self.assertEqual(fields_info['list_price']['string'], "Standard Selling Price")
        self.assertEqual(fields_info['standard_price']['string'], "Moving Avg / Standard Cost")

        # Test Material Creation with SAP Material Types
        mat_roh = tmpl_model.create({
            'name': 'Cold Rolled Steel Coil SS400',
            'default_code': 'MAT-ROH-001',
            'sap_material_type': 'ROH',
        })
        self.assertEqual(mat_roh.sap_material_type, 'ROH')
        self.assertEqual(mat_roh.product_variant_id.sap_material_type, 'ROH')

        mat_fert = tmpl_model.create({
            'name': 'Electric Tow Tractor V-LIFT 2500E',
            'default_code': 'MAT-FERT-001',
            'sap_material_type': 'FERT',
        })
        self.assertEqual(mat_fert.sap_material_type, 'FERT')

    def test_03_organizational_structure_lexicon(self):
        """Verify Company Code, Plant, and Storage Location models and fields."""
        company_model = self.env['res.company']
        self.assertEqual(company_model._description, "Company Code (Bukrs)")
        comp_fields = company_model.fields_get(['name', 'currency_id'])
        self.assertEqual(comp_fields['name']['string'], "Company Code Name")
        self.assertEqual(comp_fields['currency_id']['string'], "Company Code Currency")

        wh_model = self.env['stock.warehouse']
        self.assertEqual(wh_model._description, "Plant / Distribution Center")
        wh_fields = wh_model.fields_get(['name', 'code', 'company_id'])
        self.assertEqual(wh_fields['name']['string'], "Plant Name / Distribution Center")
        self.assertEqual(wh_fields['code']['string'], "Plant Code (Werks)")
        self.assertEqual(wh_fields['company_id']['string'], "Company Code Assignment")

        loc_model = self.env['stock.location']
        self.assertEqual(loc_model._description, "Storage Location (SLoc / LGORT)")
        loc_fields = loc_model.fields_get(['name'])
        self.assertEqual(loc_fields['name']['string'], "Storage Location Name")

    def test_04_declarative_menus_and_actions(self):
        """Verify declarative XML updates for menus and actions."""
        # Menus
        contacts_menu = self.env.ref('contacts.menu_contacts')
        self.assertEqual(contacts_menu.name, "Business Partner (BP)")

        sale_menu = self.env.ref('sale.sale_menu_root')
        self.assertEqual(sale_menu.name, "Sales & Distribution (SD)")

        purchase_menu = self.env.ref('purchase.menu_purchase_root')
        self.assertEqual(purchase_menu.name, "Materials Management (MM)")

        stock_menu = self.env.ref('stock.menu_stock_root')
        self.assertEqual(stock_menu.name, "Logistics & Inventory (MM-IM)")

        account_menu = self.env.ref('account.menu_finance')
        self.assertEqual(account_menu.name, "Financials & Controlling (FI/CO)")

        mrp_menu = self.env.ref('mrp.menu_mrp_root')
        self.assertEqual(mrp_menu.name, "Production Planning (PP)")

        # Actions
        contacts_action = self.env.ref('contacts.action_contacts')
        self.assertEqual(contacts_action.name, "Business Partners (BP)")

        product_action = self.env.ref('product.product_template_action')
        self.assertEqual(product_action.name, "Material Master (MM)")

        company_action = self.env.ref('base.action_res_company_form')
        self.assertEqual(company_action.name, "Company Codes (Bukrs)")
