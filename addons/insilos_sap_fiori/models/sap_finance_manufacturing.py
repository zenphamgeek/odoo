# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
from insilos import models, fields, api

_logger = logging.getLogger(__name__)


# ==============================================================================
# Financial Accounting (FI)
# ==============================================================================

class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = "FI Accounting Document (BKPF)"

    # SAP FI Document Header Lexicon
    name = fields.Char(string="FI Document Number")
    ref = fields.Char(string="Reference Document (XBLNR)")
    date = fields.Date(string="Posting Date in General Ledger (BUDAT)")
    invoice_date = fields.Date(string="Document Date (BLDAT)")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _description = "FI Document Line Item (BSEG)"

    # SAP FI Document Line Items Lexicon
    account_id = fields.Many2one(string="G/L Account Number (HKONT)")
    debit = fields.Monetary(string="Debit Amount (Soll)")
    credit = fields.Monetary(string="Credit Amount (Haben)")
    analytic_distribution = fields.Json(string="CO Account Assignment")


class AccountAccount(models.Model):
    _inherit = 'account.account'
    _description = "Chart of Accounts / G/L Accounts"

    # SAP G/L Account Master Lexicon
    code = fields.Char(string="G/L Account Number (SAKNR)")
    name = fields.Char(string="G/L Account Description")
    account_type = fields.Selection(string="Financial Statement Category")


# ==============================================================================
# Controlling (CO)
# ==============================================================================

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    _description = "Cost Center / Profit Center"

    name = fields.Char(string="Cost Center / Profit Center Name")
    code = fields.Char(string="Cost Center / Profit Center Key")
    plan_id = fields.Many2one(string="Controlling Area Plan (KOKRS)")

    co_type = fields.Selection(
        selection=[
            ('cost_center', 'Cost Center (KOSTL)'),
            ('profit_center', 'Profit Center (PRCTR)'),
        ],
        string="CO Category",
        default='cost_center',
        index=True,
        tracking=True,
        help="Controlling (CO) classification: Cost Center (KOSTL) or Profit Center (PRCTR).",
    )

    is_cost_center = fields.Boolean(
        string="Cost Center (KOSTL)",
        compute='_compute_co_flags',
        store=True,
        index=True,
        help="Indicates whether this account serves as a Cost Center (KOSTL).",
    )
    is_profit_center = fields.Boolean(
        string="Profit Center (PRCTR)",
        compute='_compute_co_flags',
        store=True,
        index=True,
        help="Indicates whether this account serves as a Profit Center (PRCTR).",
    )

    @api.depends('co_type')
    def _compute_co_flags(self):
        for acc in self:
            acc.is_cost_center = (acc.co_type == 'cost_center')
            acc.is_profit_center = (acc.co_type == 'profit_center')



class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'
    _description = "Controlling Area Plan (KOKRS)"

    name = fields.Char(string="Controlling Area Plan (KOKRS)")


# ==============================================================================
# Production Planning (PP)
# ==============================================================================

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _description = "Production Order (PP/CO01)"

    name = fields.Char(string="Production Order Number (AUFNR)")
    product_id = fields.Many2one(string="Header Material Master")
    product_qty = fields.Float(string="Target Order Quantity")
    move_raw_ids = fields.One2many(string="Component Reservations (RESB)")

    movement_type_issue = fields.Char(
        string="Movement Type - Issue (BWART 261)",
        default="261",
        readonly=True,
        help="SAP Movement Type 261: Goods issue for production order reservation.",
    )
    movement_type_receipt = fields.Char(
        string="Movement Type - Receipt (BWART 101)",
        default="101",
        readonly=True,
        help="SAP Movement Type 101: Goods receipt from production order into unrestricted stock.",
    )


class StockMove(models.Model):
    _inherit = 'stock.move'

    sap_bwart = fields.Char(
        string="SAP Movement Type (BWART)",
        compute="_compute_sap_bwart",
        store=True,
        index=True,
        help="SAP Inventory Movement Type: 261 (Goods Issue for Order), 101 (Goods Receipt from Production / PO), 601 (Outbound Delivery), etc."
    )

    @api.depends('raw_material_production_id', 'production_id')
    def _compute_sap_bwart(self):
        for move in self:
            if move.raw_material_production_id:
                move.sap_bwart = '261'
            elif move.production_id:
                move.sap_bwart = '101'
            elif hasattr(move, 'purchase_line_id') and move.purchase_line_id:
                move.sap_bwart = '101'
            elif hasattr(move, 'sale_line_id') and move.sale_line_id:
                move.sap_bwart = '601'
            else:
                move.sap_bwart = move.sap_bwart or False


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    _description = "Production BOM (CS01)"

    product_tmpl_id = fields.Many2one(string="Header Material Master")
    code = fields.Char(string="Alternative BOM / Reference")
    product_qty = fields.Float(string="Base Quantity")
    bom_line_ids = fields.One2many(string="Components / BOM Line Items")


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'
    _description = "Work Center / Routing Resource (CR01)"

    name = fields.Char(string="Work Center Description")
    code = fields.Char(string="Work Center Code (ARBPL)")
    costs_hour = fields.Float(string="Cost Center Activity Rate / Rate per Unit")
    time_start = fields.Float(string="Standard Setup Time (RUEZT)")
    time_stop = fields.Float(string="Standard Teardown / Cleanup Time")
    oee_target = fields.Float(string="OEE Target Ratio (%)")
    oee = fields.Float(string="Overall Equipment Effectiveness (OEE)")
