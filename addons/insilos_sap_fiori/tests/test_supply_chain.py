# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSapSupplyChain(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['res.partner']
        cls.product_model = cls.env['product.product']

        # Setup standard test Business Partners
        cls.sold_to_bp = cls.partner_model.create({
            'name': 'ACME Industrial Sold-To AG',
            'ref': 'BP-SD-001',
            'customer_rank': 1,
        })
        cls.bill_to_bp = cls.partner_model.create({
            'name': 'ACME Shared Services Payer AG',
            'ref': 'BP-SD-002',
            'customer_rank': 1,
        })
        cls.ship_to_bp = cls.partner_model.create({
            'name': 'ACME Plant Werk 01 Ship-To AG',
            'ref': 'BP-SD-003',
            'customer_rank': 1,
        })
        cls.vendor_bp = cls.partner_model.create({
            'name': 'Global Raw Materials Supplier GmbH',
            'ref': 'BP-MM-001',
            'supplier_rank': 1,
        })

        # Setup test Material Master
        cls.material_tmpl = cls.env['product.template'].create({
            'name': 'Titanium Grade 5 Hex Bolt M12x50',
            'default_code': 'MAT-BOLT-M12',
            'list_price': 15.0,
            'standard_price': 8.5,
            'type': 'consu',
            'is_storable': True,
        })
        cls.material_product = cls.material_tmpl.product_variant_id

    # ==========================================================================
    # 1. Sales & Distribution (SD)
    # ==========================================================================
    def test_01_sale_order_lexicon_and_party_roles(self):
        """Verify sale.order and sale.order.line model descriptions, BP party roles, and field strings."""
        order_model = self.env['sale.order']
        self.assertEqual(order_model._description, "Sales Order (SD)")

        # Verify header field strings
        so_fields = order_model.fields_get([
            'name', 'partner_id', 'partner_invoice_id', 'partner_shipping_id',
            'date_order', 'validity_date', 'order_line', 'amount_total', 'payment_term_id'
        ])
        self.assertEqual(so_fields['name']['string'], "SD Document Number")
        self.assertEqual(so_fields['partner_id']['string'], "Sold-to Party (BP)")
        self.assertEqual(so_fields['partner_invoice_id']['string'], "Bill-to Party / Payer (BP)")
        self.assertEqual(so_fields['partner_shipping_id']['string'], "Ship-to Party (BP)")
        self.assertEqual(so_fields['date_order']['string'], "Document Date")
        self.assertEqual(so_fields['validity_date']['string'], "Quotation Valid Until")
        self.assertEqual(so_fields['order_line']['string'], "Sales Order Items")
        self.assertEqual(so_fields['amount_total']['string'], "Net Value + Tax")
        self.assertEqual(so_fields['payment_term_id']['string'], "Terms of Payment")

        # Verify line item model description and field strings
        line_model = self.env['sale.order.line']
        self.assertEqual(line_model._description, "Sales Order Line Item")

        line_fields = line_model.fields_get([
            'product_id', 'product_uom_qty', 'price_unit', 'price_subtotal'
        ])
        self.assertEqual(line_fields['product_id']['string'], "Material Master (MM)")
        self.assertEqual(line_fields['product_uom_qty']['string'], "Order Quantity")
        self.assertEqual(line_fields['price_unit']['string'], "Condition Unit Price")
        self.assertEqual(line_fields['price_subtotal']['string'], "Item Net Value")

    def test_02_sale_order_state_progression_and_document_types(self):
        """Verify state-based SD document taxonomy progression (Inquiry/Quotation -> Standard Sales Order)."""
        order = self.env['sale.order'].create({
            'partner_id': self.sold_to_bp.id,
            'partner_invoice_id': self.bill_to_bp.id,
            'partner_shipping_id': self.ship_to_bp.id,
            'order_line': [(0, 0, {
                'product_id': self.material_product.id,
                'product_uom_qty': 100.0,
                'price_unit': 15.0,
            })],
        })

        # Draft / Quotation state
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.sap_document_type, "SD Quotation / Sales Inquiry")
        self.assertEqual(order.sap_state_label, "SD Quotation / Sales Inquiry")

        # Sent state
        order.state = 'sent'
        self.assertEqual(order.sap_document_type, "SD Quotation / Sales Inquiry")

        # Confirmed sales order state
        order.state = 'sale'
        self.assertEqual(order.sap_document_type, "SD Standard Sales Order")
        self.assertEqual(order.sap_state_label, "SD Standard Sales Order")

        # Locked / Completed state
        order.locked = True
        self.assertEqual(order.sap_document_type, "SD Completed Sales Order")
        self.assertEqual(order.sap_state_label, "SD Completed Sales Order")

        # Cancelled state
        order.locked = False
        order.state = 'cancel'
        self.assertEqual(order.sap_document_type, "SD Cancelled Sales Order")
        self.assertEqual(order.sap_state_label, "SD Cancelled Sales Order")

    # ==========================================================================
    # Customer Billing Documents (account.move)
    # ==========================================================================
    def test_03_customer_billing_documents_lexicon(self):
        """Verify customer billing documents (F2) and credit memos (RE) computation and declarative actions."""
        move_model = self.env['account.move']

        # F2 Customer Billing Document (out_invoice)
        customer_invoice = move_model.create({
            'move_type': 'out_invoice',
            'partner_id': self.sold_to_bp.id,
            'invoice_date': '2026-09-28',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.material_product.id,
                'quantity': 50.0,
                'price_unit': 15.0,
            })],
        })
        self.assertEqual(customer_invoice.sap_billing_type, "Customer Billing Document (F2)")

        # RE Customer Credit Memo (out_refund)
        customer_credit_memo = move_model.create({
            'move_type': 'out_refund',
            'partner_id': self.sold_to_bp.id,
            'invoice_date': '2026-09-28',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.material_product.id,
                'quantity': 10.0,
                'price_unit': 15.0,
            })],
        })
        self.assertEqual(customer_credit_memo.sap_billing_type, "Customer Credit Memo (RE)")

        # Verify Declarative Actions & Menus
        out_invoice_action = self.env.ref('account.action_move_out_invoice', raise_if_not_found=False)
        if out_invoice_action:
            self.assertEqual(out_invoice_action.name, "Customer Billing Documents")

        out_refund_action = self.env.ref('account.action_move_out_refund_type_non_legacy', raise_if_not_found=False)
        if out_refund_action:
            self.assertEqual(out_refund_action.name, "Customer Credit Memos")

        out_refund_menu = self.env.ref('account.menu_action_move_out_refund_type', raise_if_not_found=False)
        if out_refund_menu:
            self.assertEqual(out_refund_menu.name, "Customer Credit Memos")

    # ==========================================================================
    # 2. Materials Management (MM)
    # ==========================================================================
    def test_04_purchase_requisition_and_outline_agreements(self):
        """Verify purchase.requisition model description, selection lexicon, and BANFN field strings."""
        req_model = self.env['purchase.requisition']
        self.assertEqual(req_model._description, "Purchase Requisition (Banf) / Outline Agreement")

        req_fields = req_model.fields_get(['name', 'vendor_id', 'requisition_type', 'line_ids'])
        self.assertEqual(req_fields['name']['string'], "Requisition / Agreement No. (BANFN)")
        self.assertEqual(req_fields['vendor_id']['string'], "Vendor / Supplier BP")
        self.assertEqual(req_fields['requisition_type']['string'], "Agreement Category")
        self.assertEqual(req_fields['line_ids']['string'], "Requisition Line Items")

        # Verify selection for blanket_order contains "Quantity/Value Contract"
        selection_dict = dict(req_fields['requisition_type']['selection'])
        self.assertIn('blanket_order', selection_dict)
        self.assertEqual(selection_dict['blanket_order'], "Quantity/Value Contract")

        # Create Outline Agreement / Contract
        contract = req_model.create({
            'vendor_id': self.vendor_bp.id,
            'requisition_type': 'blanket_order',
            'line_ids': [(0, 0, {
                'product_id': self.material_product.id,
                'product_qty': 500.0,
            })],
        })
        self.assertEqual(contract.requisition_type, 'blanket_order')
        self.assertTrue(contract.name)

        # Verify Declarative Actions & Menus
        pr_action = self.env.ref('purchase_requisition.action_purchase_requisition', raise_if_not_found=False)
        if pr_action:
            self.assertEqual(pr_action.name, "Purchase Requisitions & Outline Agreements")

        pr_menu = self.env.ref('purchase_requisition.menu_purchase_requisition_pro_mgt', raise_if_not_found=False)
        if pr_menu:
            self.assertEqual(pr_menu.name, "Purchase Requisitions & Agreements")

    def test_05_purchase_order_lexicon_and_progression(self):
        """Verify purchase.order model description, vendor partner role, and RFQ -> PO state progression."""
        po_model = self.env['purchase.order']
        self.assertEqual(po_model._description, "MM Purchase Order")

        po_fields = po_model.fields_get([
            'name', 'partner_id', 'date_order', 'date_planned', 'order_line', 'amount_total', 'payment_term_id'
        ])
        self.assertEqual(po_fields['name']['string'], "MM Document Number")
        self.assertEqual(po_fields['partner_id']['string'], "Vendor / Supplier BP")
        self.assertEqual(po_fields['date_order']['string'], "PO Order Date")
        self.assertEqual(po_fields['date_planned']['string'], "Scheduled Delivery Date")
        self.assertEqual(po_fields['order_line']['string'], "Purchase Order Items")
        self.assertEqual(po_fields['amount_total']['string'], "Gross Order Value")
        self.assertEqual(po_fields['payment_term_id']['string'], "Terms of Payment")

        line_model = self.env['purchase.order.line']
        self.assertEqual(line_model._description, "Purchase Order Line Item")
        line_fields = line_model.fields_get(['product_id', 'product_qty', 'price_unit'])
        self.assertEqual(line_fields['product_id']['string'], "Material Master (MM)")
        self.assertEqual(line_fields['product_qty']['string'], "Order Quantity")
        self.assertEqual(line_fields['price_unit']['string'], "Net Order Price")

        # Create Vendor RFQ
        po = po_model.create({
            'partner_id': self.vendor_bp.id,
            'order_line': [(0, 0, {
                'product_id': self.material_product.id,
                'product_qty': 200.0,
                'price_unit': 8.5,
            })],
        })

        # Draft / RFQ State
        self.assertEqual(po.state, 'draft')
        self.assertEqual(po.sap_document_type, "Vendor Request for Quotation (RFQ)")
        self.assertEqual(po.sap_state_label, "Vendor Request for Quotation (RFQ)")

        # Sent State
        po.state = 'sent'
        self.assertEqual(po.sap_document_type, "Vendor Request for Quotation (RFQ)")

        # Confirmed PO State
        po.button_confirm()
        self.assertIn(po.state, ('purchase', 'done'))
        self.assertEqual(po.sap_document_type, "MM Purchase Order")
        self.assertEqual(po.sap_state_label, "MM Purchase Order")

        # Declarative Actions & Menus
        rfq_action = self.env.ref('purchase.purchase_rfq', raise_if_not_found=False)
        if rfq_action:
            self.assertEqual(rfq_action.name, "Vendor Requests for Quotation (RFQs)")

        po_action = self.env.ref('purchase.purchase_form_action', raise_if_not_found=False)
        if po_action:
            self.assertEqual(po_action.name, "MM Purchase Orders")

    # ==========================================================================
    # Logistics Deliveries & Goods Movements (stock.picking & stock.move)
    # ==========================================================================
    def test_06_stock_picking_movement_types_and_deliveries(self):
        """Verify stock.picking movement annotations (101, 601, 311) and stock.move descriptions."""
        picking_model = self.env['stock.picking']
        self.assertEqual(picking_model._description, "Goods Movement / Delivery")

        # Check stock.move model description and field strings
        move_model = self.env['stock.move']
        self.assertEqual(move_model._description, "Material Movement Item")
        move_fields = move_model.fields_get([
            'product_id', 'product_uom_qty', 'quantity', 'location_id', 'location_dest_id'
        ])
        self.assertEqual(move_fields['product_id']['string'], "Material Master (MM)")
        self.assertEqual(move_fields['product_uom_qty']['string'], "Scheduled Quantity")
        self.assertEqual(move_fields['quantity']['string'], "Delivered Quantity")
        self.assertEqual(move_fields['location_id']['string'], "Source Storage Location (SLoc)")
        self.assertEqual(move_fields['location_dest_id']['string'], "Destination Storage Location (SLoc)")

        # Find Picking Types for incoming and outgoing
        picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        picking_type_in = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        picking_type_int = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

        # 1. Outbound Delivery / Post Goods Issue (601)
        if picking_type_out:
            picking_out = picking_model.create({
                'picking_type_id': picking_type_out.id,
                'location_id': picking_type_out.default_location_src_id.id,
                'location_dest_id': picking_type_out.default_location_dest_id.id,
                'partner_id': self.ship_to_bp.id,
            })
            self.assertEqual(picking_out.sap_delivery_type, "Outbound Delivery / Post Goods Issue")
            self.assertEqual(picking_out.sap_movement_type, "601")
            self.assertIn("601", picking_out.sap_movement_desc)

        # 2. Inbound Delivery / Goods Receipt (101)
        if picking_type_in:
            picking_in = picking_model.create({
                'picking_type_id': picking_type_in.id,
                'location_id': picking_type_in.default_location_src_id.id,
                'location_dest_id': picking_type_in.default_location_dest_id.id,
                'partner_id': self.vendor_bp.id,
            })
            self.assertEqual(picking_in.sap_delivery_type, "Inbound Delivery / Goods Receipt")
            self.assertEqual(picking_in.sap_movement_type, "101")
            self.assertIn("101", picking_in.sap_movement_desc)

        # 3. Transfer Posting (311)
        if picking_type_int:
            picking_int = picking_model.create({
                'picking_type_id': picking_type_int.id,
                'location_id': picking_type_int.default_location_src_id.id,
                'location_dest_id': picking_type_int.default_location_dest_id.id,
            })
            self.assertEqual(picking_int.sap_delivery_type, "Transfer Posting (SLoc / Plant)")
            self.assertEqual(picking_int.sap_movement_type, "311")
            self.assertIn("311", picking_int.sap_movement_desc)

        # Verify Declarative Menus & Actions
        in_action = self.env.ref('stock.action_picking_tree_incoming', raise_if_not_found=False)
        if in_action:
            self.assertEqual(in_action.name, "Inbound Deliveries / Goods Receipts")

        out_action = self.env.ref('stock.action_picking_tree_outgoing', raise_if_not_found=False)
        if out_action:
            self.assertEqual(out_action.name, "Outbound Deliveries / Post Goods Issues")

    # ==========================================================================
    # Physical Inventory Adjustments & Movement Types (stock.quant)
    # ==========================================================================
    def test_07_physical_inventory_movement_types(self):
        """Verify stock.quant model description, field strings, and movement types (701 surplus, 702 deficit)."""
        quant_model = self.env['stock.quant']
        self.assertEqual(quant_model._description, "Physical Inventory Adjustment (MI01/MI07)")

        quant_fields = quant_model.fields_get([
            'product_id', 'location_id', 'quantity', 'inventory_quantity', 'inventory_diff_quantity'
        ])
        self.assertEqual(quant_fields['product_id']['string'], "Material Master (MM)")
        self.assertEqual(quant_fields['location_id']['string'], "Storage Location (SLoc)")
        self.assertEqual(quant_fields['quantity']['string'], "Quantity On Hand")
        self.assertEqual(quant_fields['inventory_quantity']['string'], "Physical Counted Quantity")
        self.assertEqual(quant_fields['inventory_diff_quantity']['string'], "Count Difference")

        # Test movement type computation
        location = self.env.ref('stock.stock_location_stock')
        quant = quant_model.create({
            'product_id': self.material_product.id,
            'location_id': location.id,
            'quantity': 100.0,
        })

        # Inventory Diff > 0 -> Surplus 701
        quant.inventory_quantity = 110.0
        self.assertGreater(quant.inventory_diff_quantity, 0)
        self.assertEqual(quant.sap_movement_type, "701")
        self.assertIn("701", quant.sap_movement_desc)

        # Inventory Diff < 0 -> Deficit 702
        quant.inventory_quantity = 90.0
        self.assertLess(quant.inventory_diff_quantity, 0)
        self.assertEqual(quant.sap_movement_type, "702")
        self.assertIn("702", quant.sap_movement_desc)

        # Declarative Menus & Actions
        pi_action = self.env.ref('stock.action_view_inventory_tree', raise_if_not_found=False)
        if pi_action:
            self.assertEqual(pi_action.name, "Physical Inventory Adjustments (MI01/MI07)")

        pi_menu = self.env.ref('stock.menu_action_inventory_tree', raise_if_not_found=False)
        if pi_menu:
            self.assertEqual(pi_menu.name, "Physical Inventory Adjustments (MI01/MI07)")

    # ==========================================================================
    # SAP Movement Types Reference Matrix (sap.movement.type)
    # ==========================================================================
    def test_08_sap_movement_type_matrix_records(self):
        """Verify all standard SAP BWART movement type matrix records exist and are correctly configured."""
        matrix_model = self.env['sap.movement.type']
        expected_codes = {
            '101': ('GR', 'MIGO / VL31N'),
            '102': ('GR', 'MIGO'),
            '261': ('GI', 'MIGO / MB1A'),
            '301': ('TP', 'MIGO / MB1B'),
            '311': ('TP', 'MIGO / MB1B'),
            '601': ('GI', 'VL01N / VL02N'),
            '701': ('PI', 'MI07'),
            '702': ('PI', 'MI07'),
        }

        for code, (category, tcode) in expected_codes.items():
            record = matrix_model.search([('code', '=', code)], limit=1)
            self.assertTrue(record, f"Movement Type {code} must exist in sap.movement.type matrix")
            self.assertEqual(record.process_category, category)
            self.assertEqual(record.sap_tcode, tcode)
            self.assertTrue(record.name)
            self.assertTrue(record.source_location_desc)
            self.assertTrue(record.dest_location_desc)
