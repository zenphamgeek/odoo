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

_CO_TYPE_CACHE = {}


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
        compute='_compute_co_type',
        inverse='_inverse_co_type',
        search='_search_co_type',
        store=False,
        help="Controlling (CO) classification: Cost Center (KOSTL) or Profit Center (PRCTR).",
    )

    is_cost_center = fields.Boolean(
        string="Cost Center (KOSTL)",
        compute='_compute_co_flags',
        search='_search_is_cost_center',
        store=False,
        help="Indicates whether this account serves as a Cost Center (KOSTL).",
    )
    is_profit_center = fields.Boolean(
        string="Profit Center (PRCTR)",
        compute='_compute_co_flags',
        search='_search_is_profit_center',
        store=False,
        help="Indicates whether this account serves as a Profit Center (PRCTR).",
    )

    @api.depends('code', 'name')
    def _compute_co_type(self):
        for acc in self:
            cached = _CO_TYPE_CACHE.get(acc.id)
            if cached:
                acc.co_type = cached
            elif acc.code and any(k in acc.code.upper() for k in ('PRCTR', 'PROFIT')):
                acc.co_type = 'profit_center'
            elif acc.name and any(k in str(acc.name).upper() for k in ('PROFIT', 'PRCTR')):
                acc.co_type = 'profit_center'
            else:
                acc.co_type = 'cost_center'

    def _inverse_co_type(self):
        for acc in self:
            if acc.co_type:
                _CO_TYPE_CACHE[acc.id] = acc.co_type

    @api.depends('co_type')
    def _compute_co_flags(self):
        for acc in self:
            acc.is_cost_center = (acc.co_type == 'cost_center')
            acc.is_profit_center = (acc.co_type == 'profit_center')

    @api.model_create_multi
    def create(self, vals_list):
        co_types = [vals.pop('co_type', None) for vals in vals_list]
        recs = super().create(vals_list)
        for rec, ct in zip(recs, co_types):
            if ct:
                _CO_TYPE_CACHE[rec.id] = ct
                rec.co_type = ct
        return recs

    def write(self, vals):
        ct = vals.pop('co_type', None)
        res = super().write(vals)
        if ct:
            for rec in self:
                _CO_TYPE_CACHE[rec.id] = ct
        return res

    def _search_co_type(self, operator, value):
        if value == 'profit_center':
            return self._search_is_profit_center(operator, True)
        elif value == 'cost_center':
            return self._search_is_cost_center(operator, True)
        return []

    def _search_is_cost_center(self, operator, value):
        is_true = (value if operator in ('=', 'in') else not value)
        pc_ids = {rid for rid, c in _CO_TYPE_CACHE.items() if c == 'profit_center'}
        try:
            self.env.cr.execute("SELECT id FROM account_analytic_account WHERE (code ILIKE '%PRCTR%' OR name::text ILIKE '%profit%')")
            pc_ids.update(r[0] for r in self.env.cr.fetchall())
        except Exception:
            pass

        if is_true:
            return [('id', 'not in', list(pc_ids))] if pc_ids else []
        else:
            return [('id', 'in', list(pc_ids))] if pc_ids else [('id', '=', False)]

    def _search_is_profit_center(self, operator, value):
        is_true = (value if operator in ('=', 'in') else not value)
        pc_ids = {rid for rid, c in _CO_TYPE_CACHE.items() if c == 'profit_center'}
        try:
            self.env.cr.execute("SELECT id FROM account_analytic_account WHERE (code ILIKE '%PRCTR%' OR name::text ILIKE '%profit%')")
            pc_ids.update(r[0] for r in self.env.cr.fetchall())
        except Exception:
            pass

        if is_true:
            return [('id', 'in', list(pc_ids))] if pc_ids else [('id', '=', False)]
        else:
            return [('id', 'not in', list(pc_ids))] if pc_ids else []


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
        compute='_compute_movement_types',
        search='_search_movement_type_issue',
        store=False,
        readonly=True,
        help="SAP Movement Type 261: Goods issue for production order reservation.",
    )
    movement_type_receipt = fields.Char(
        string="Movement Type - Receipt (BWART 101)",
        compute='_compute_movement_types',
        search='_search_movement_type_receipt',
        store=False,
        readonly=True,
        help="SAP Movement Type 101: Goods receipt from production order into unrestricted stock.",
    )

    def _compute_movement_types(self):
        for prod in self:
            prod.movement_type_issue = "261"
            prod.movement_type_receipt = "101"

    def _search_movement_type_issue(self, operator, value):
        if (operator in ('=', 'ilike', 'like') and '261' in str(value)) or (operator in ('!=', 'not ilike') and '261' not in str(value)):
            return [('id', '!=', False)]
        return [('id', '=', False)]

    def _search_movement_type_receipt(self, operator, value):
        if (operator in ('=', 'ilike', 'like') and '101' in str(value)) or (operator in ('!=', 'not ilike') and '101' not in str(value)):
            return [('id', '!=', False)]
        return [('id', '=', False)]


class StockMove(models.Model):
    _inherit = 'stock.move'

    sap_bwart = fields.Char(
        string="SAP Movement Type (BWART)",
        compute="_compute_sap_bwart",
        search="_search_sap_bwart",
        store=False,
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
                move.sap_bwart = False

    def _search_sap_bwart(self, operator, value):
        val_str = str(value)
        if '261' in val_str:
            target = [('raw_material_production_id', '!=', False)]
        elif '101' in val_str:
            target = ['|', ('production_id', '!=', False), ('purchase_line_id', '!=', False)]
        elif '601' in val_str:
            target = [('sale_line_id', '!=', False)]
        else:
            target = [('id', '!=', False)]

        if operator in ('!=', 'not in', 'not ilike'):
            return ['!'] + target
        return target


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
