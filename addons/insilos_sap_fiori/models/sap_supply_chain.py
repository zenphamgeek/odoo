# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
from insilos import models, fields, api, _

_logger = logging.getLogger(__name__)


# ==============================================================================
# 1. Sales & Distribution (SD)
# ==============================================================================
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = "Sales Order (SD)"

    # Party Roles (BP)
    partner_id = fields.Many2one(
        string="Sold-to Party (BP)",
        help="SAP Sold-to Party (KUNNR): The business partner who orders the goods/services.",
    )
    partner_invoice_id = fields.Many2one(
        string="Bill-to Party / Payer (BP)",
        help="SAP Bill-to Party (RE) / Payer (RG): The business partner who receives the billing document and pays.",
    )
    partner_shipping_id = fields.Many2one(
        string="Ship-to Party (BP)",
        help="SAP Ship-to Party (WE): The business partner to whom the goods are delivered.",
    )

    # State-based SD Document Lexicon
    sap_document_type = fields.Char(
        string="SD Document Category",
        compute='_compute_sap_document_type',
        store=True,
        index=True,
        help="SAP SD Document Classification based on lifecycle state (Inquiry / Quotation / Standard Sales Order).",
    )
    sap_state_label = fields.Char(
        string="SD Status Lexicon",
        compute='_compute_sap_document_type',
        store=True,
    )

    @api.depends('state', 'locked')
    def _compute_sap_document_type(self):
        for order in self:
            if order.state in ('draft', 'sent'):
                order.sap_document_type = "SD Quotation / Sales Inquiry"
                order.sap_state_label = "SD Quotation / Sales Inquiry"
            elif order.state == 'sale':
                if getattr(order, 'locked', False):
                    order.sap_document_type = "SD Completed Sales Order"
                    order.sap_state_label = "SD Completed Sales Order"
                else:
                    order.sap_document_type = "SD Standard Sales Order"
                    order.sap_state_label = "SD Standard Sales Order"
            elif order.state == 'done':
                order.sap_document_type = "SD Completed Sales Order"
                order.sap_state_label = "SD Completed Sales Order"
            elif order.state == 'cancel':
                order.sap_document_type = "SD Cancelled Sales Order"
                order.sap_state_label = "SD Cancelled Sales Order"
            else:
                order.sap_document_type = "Sales Order (SD)"
                order.sap_state_label = "Sales Order (SD)"


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = "Sales Order Line Item"

    product_id = fields.Many2one(string="Material Master (MM)")
    product_uom_qty = fields.Float(string="Order Quantity")
    price_unit = fields.Float(string="Condition Unit Price")
    price_subtotal = fields.Monetary(string="Item Net Value")


# ==============================================================================
# Customer Billing Documents (account.move)
# ==============================================================================
class AccountMove(models.Model):
    _inherit = 'account.move'

    sap_billing_type = fields.Char(
        string="Billing Document Type",
        compute='_compute_sap_billing_type',
        store=True,
        index=True,
        help="SAP Billing Document category (F2 Invoice, RE Credit Memo, LIV Vendor Invoice).",
    )

    @api.depends('move_type')
    def _compute_sap_billing_type(self):
        for move in self:
            if move.move_type == 'out_invoice':
                move.sap_billing_type = "Customer Billing Document (F2)"
            elif move.move_type == 'out_refund':
                move.sap_billing_type = "Customer Credit Memo (RE)"
            elif move.move_type == 'in_invoice':
                move.sap_billing_type = "Vendor Invoice (LIV)"
            elif move.move_type == 'in_refund':
                move.sap_billing_type = "Vendor Credit Memo"
            elif move.move_type == 'entry':
                move.sap_billing_type = "FI Accounting Document"
            else:
                move.sap_billing_type = "Billing Document"


# ==============================================================================
# 2. Materials Management (MM)
# ==============================================================================
class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'
    _description = "Purchase Requisition (Banf) / Outline Agreement"

    name = fields.Char(string="Requisition / Agreement No. (BANFN)")
    vendor_id = fields.Many2one(string="Vendor / Supplier BP")
    requisition_type = fields.Selection(
        selection=[
            ('blanket_order', 'Quantity/Value Contract'),
            ('purchase_template', 'Purchase Requisition Template'),
        ],
        string="Agreement Category",
        help="SAP Outline Agreement category (Quantity Contract MK / Value Contract WK).",
    )
    line_ids = fields.One2many(string="Requisition Line Items")


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    product_id = fields.Many2one(string="Material Master (MM)")
    product_qty = fields.Float(string="Requisition Quantity")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = "MM Purchase Order"

    partner_id = fields.Many2one(
        string="Vendor / Supplier BP",
        help="SAP Vendor / Supplier BP (LIFNR): The business partner from whom materials or services are procured.",
    )

    sap_document_type = fields.Char(
        string="Purchasing Document Category",
        compute='_compute_sap_document_type',
        store=True,
        index=True,
        help="SAP MM Purchasing Document progression (Vendor RFQ / MM Purchase Order).",
    )
    sap_state_label = fields.Char(
        string="Purchasing Status Lexicon",
        compute='_compute_sap_document_type',
        store=True,
    )

    @api.depends('state')
    def _compute_sap_document_type(self):
        for order in self:
            if order.state in ('draft', 'sent'):
                order.sap_document_type = "Vendor Request for Quotation (RFQ)"
                order.sap_state_label = "Vendor Request for Quotation (RFQ)"
            elif order.state in ('purchase', 'done'):
                order.sap_document_type = "MM Purchase Order"
                order.sap_state_label = "MM Purchase Order"
            elif order.state == 'to approve':
                order.sap_document_type = "MM Purchase Order (To Approve)"
                order.sap_state_label = "MM Purchase Order (To Approve)"
            elif order.state == 'cancel':
                order.sap_document_type = "Cancelled Purchasing Document"
                order.sap_state_label = "Cancelled Purchasing Document"
            else:
                order.sap_document_type = "MM Purchase Order"
                order.sap_state_label = "MM Purchase Order"


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = "Purchase Order Line Item"

    product_id = fields.Many2one(string="Material Master (MM)")
    product_qty = fields.Float(string="Order Quantity")
    price_unit = fields.Float(string="Net Order Price")


# ==============================================================================
# Goods Deliveries & Movements (stock.picking & stock.move)
# ==============================================================================
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = "Goods Movement / Delivery"

    sap_delivery_type = fields.Char(
        string="Delivery Category",
        compute='_compute_sap_delivery_info',
        store=True,
        index=True,
        help="SAP Logistics Document Category (Outbound Delivery / Inbound Delivery / Transfer Posting).",
    )
    sap_movement_type = fields.Char(
        string="Movement Type (BWART)",
        compute='_compute_sap_delivery_info',
        store=True,
        index=True,
        help="SAP Standard Movement Type (BWART): 601 Outbound Delivery, 101 Goods Receipt for PO, 311 SLoc Transfer.",
    )
    sap_movement_desc = fields.Char(
        string="Movement Description",
        compute='_compute_sap_delivery_info',
        store=True,
    )

    @api.depends('picking_type_id', 'picking_type_id.code')
    def _compute_sap_delivery_info(self):
        for picking in self:
            code = picking.picking_type_id.code or picking.picking_type_code
            if code == 'outgoing':
                picking.sap_delivery_type = "Outbound Delivery / Post Goods Issue"
                picking.sap_movement_type = "601"
                picking.sap_movement_desc = "Movement Type 601 (Goods Issue for Outbound Delivery)"
            elif code == 'incoming':
                picking.sap_delivery_type = "Inbound Delivery / Goods Receipt"
                picking.sap_movement_type = "101"
                picking.sap_movement_desc = "Movement Type 101 (Goods Receipt for Purchase Order)"
            elif code == 'internal':
                picking.sap_delivery_type = "Transfer Posting (SLoc / Plant)"
                picking.sap_movement_type = "311"
                picking.sap_movement_desc = "Movement Type 311 (Transfer Posting SLoc to SLoc)"
            else:
                picking.sap_delivery_type = "Goods Movement / Delivery"
                picking.sap_movement_type = "N/A"
                picking.sap_movement_desc = "Standard Material Movement"


class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = "Material Movement Item"

    product_id = fields.Many2one(string="Material Master (MM)")
    product_uom_qty = fields.Float(string="Scheduled Quantity")
    quantity = fields.Float(string="Delivered Quantity")
    location_id = fields.Many2one(string="Source Storage Location (SLoc)")
    location_dest_id = fields.Many2one(string="Destination Storage Location (SLoc)")
    sap_movement_type = fields.Char(
        string="Movement Type (BWART)",
        compute='_compute_sap_movement_type',
        store=True,
    )

    @api.depends('picking_id.sap_movement_type')
    def _compute_sap_movement_type(self):
        for move in self:
            move.sap_movement_type = move.picking_id.sap_movement_type or 'N/A'


# ==============================================================================
# Physical Inventory Adjustments & Movement Types (stock.quant)
# ==============================================================================
class StockQuant(models.Model):
    _inherit = 'stock.quant'
    _description = "Physical Inventory Adjustment (MI01/MI07)"

    sap_movement_type = fields.Char(
        string="Movement Type (BWART)",
        compute='_compute_sap_movement_type',
        help="SAP Physical Inventory Movement Type: 701 Surplus / 702 Deficit.",
    )
    sap_movement_desc = fields.Char(
        string="Movement Description",
        compute='_compute_sap_movement_type',
    )

    @api.depends('inventory_diff_quantity')
    def _compute_sap_movement_type(self):
        for quant in self:
            if quant.inventory_diff_quantity < 0:
                quant.sap_movement_type = "702"
                quant.sap_movement_desc = "702 - Physical Inventory Difference: Book Deficit Posting"
            else:
                quant.sap_movement_type = "701"
                quant.sap_movement_desc = "701 - Physical Inventory Difference: Book Surplus Posting"


# ==============================================================================
# SAP Movement Types Matrix Reference Table
# ==============================================================================
class SapMovementType(models.Model):
    _name = 'sap.movement.type'
    _description = "SAP Stock Movement Type (BWART)"
    _order = 'code asc'

    code = fields.Char(string="Movement Type (BWART)", required=True, index=True)
    name = fields.Char(string="Movement Description", required=True)
    process_category = fields.Selection([
        ('GR', 'Goods Receipt'),
        ('GI', 'Goods Issue'),
        ('TP', 'Transfer Posting'),
        ('PI', 'Physical Inventory'),
    ], string="Process Category", required=True)
    source_location_desc = fields.Char(string="Source Location Context")
    dest_location_desc = fields.Char(string="Destination Location Context")
    sap_tcode = fields.Char(string="SAP Transaction Code")
    description = fields.Text(string="Business Description")
