# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
from insilos import models, fields, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = "Business Partner (BP)"

    # SAP Business Partner Core Lexicon
    name = fields.Char(string="Business Partner Name")
    ref = fields.Char(string="BP Number / Search Term")
    vat = fields.Char(string="Tax Number (Tax ID / VAT)")
    company_type = fields.Selection(string="BP Category")
    parent_id = fields.Many2one(string="Parent Business Partner")
    street = fields.Char(string="Street / House Number")
    city = fields.Char(string="City / Postal District")
    zip = fields.Char(string="Postal Code")
    country_id = fields.Many2one(string="Country Key")

    # SAP Business Partner Role Architecture (General / Customer / Vendor)
    bp_role = fields.Selection(
        selection=[
            ('general', 'General Business Partner (000000)'),
            ('customer', 'Customer (FLCU00)'),
            ('vendor', 'Vendor / Supplier (FLVN00)'),
            ('both', 'Customer & Vendor (FLCU00 / FLVN00)'),
        ],
        string="BP Role",
        compute='_compute_bp_role',
        inverse='_inverse_bp_role',
        search='_search_bp_role',
        help="SAP S/4HANA Business Partner Role classification: General (000000), Customer (FLCU00), Vendor (FLVN00).",
    )

    is_bp_customer = fields.Boolean(
        string="Customer Role (FLCU00)",
        compute='_compute_bp_role_flags',
        search='_search_bp_customer',
        help="Indicates whether this Business Partner is active in the Customer role (FLCU00).",
    )
    is_bp_vendor = fields.Boolean(
        string="Vendor Role (FLVN00)",
        compute='_compute_bp_role_flags',
        search='_search_bp_vendor',
        help="Indicates whether this Business Partner is active in the Vendor role (FLVN00).",
    )
    is_bp_general = fields.Boolean(
        string="General Role (000000)",
        compute='_compute_bp_role_flags',
        search='_search_bp_general',
        help="Indicates whether this Business Partner has the default General role without specific commercial ranks.",
    )

    @api.depends('customer_rank', 'supplier_rank')
    def _compute_bp_role(self):
        for partner in self:
            is_cust = bool(partner.customer_rank and partner.customer_rank > 0)
            is_supp = bool(partner.supplier_rank and partner.supplier_rank > 0)
            if is_cust and is_supp:
                partner.bp_role = 'both'
            elif is_cust:
                partner.bp_role = 'customer'
            elif is_supp:
                partner.bp_role = 'vendor'
            else:
                partner.bp_role = 'general'

    def _inverse_bp_role(self):
        for partner in self:
            if partner.bp_role == 'customer':
                if not partner.customer_rank:
                    partner.customer_rank = 1
                partner.supplier_rank = 0
            elif partner.bp_role == 'vendor':
                if not partner.supplier_rank:
                    partner.supplier_rank = 1
                partner.customer_rank = 0
            elif partner.bp_role == 'both':
                if not partner.customer_rank:
                    partner.customer_rank = 1
                if not partner.supplier_rank:
                    partner.supplier_rank = 1
            elif partner.bp_role == 'general':
                partner.customer_rank = 0
                partner.supplier_rank = 0

    def _search_bp_role(self, operator, value):
        if operator in ('=', '!='):
            if value == 'general':
                domain = [('customer_rank', '<=', 0), ('supplier_rank', '<=', 0)]
            elif value == 'customer':
                domain = [('customer_rank', '>', 0), ('supplier_rank', '<=', 0)]
            elif value == 'vendor':
                domain = [('customer_rank', '<=', 0), ('supplier_rank', '>', 0)]
            elif value == 'both':
                domain = [('customer_rank', '>', 0), ('supplier_rank', '>', 0)]
            else:
                domain = []
            if operator == '!=':
                domain = ['!'] + domain
            return domain
        return []

    @api.depends('customer_rank', 'supplier_rank')
    def _compute_bp_role_flags(self):
        for partner in self:
            partner.is_bp_customer = bool(partner.customer_rank and partner.customer_rank > 0)
            partner.is_bp_vendor = bool(partner.supplier_rank and partner.supplier_rank > 0)
            partner.is_bp_general = not (partner.is_bp_customer or partner.is_bp_vendor)

    def _search_bp_customer(self, operator, value):
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('customer_rank', '>', 0)]
        return [('customer_rank', '<=', 0)]

    def _search_bp_vendor(self, operator, value):
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('supplier_rank', '>', 0)]
        return [('supplier_rank', '<=', 0)]

    def _search_bp_general(self, operator, value):
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('customer_rank', '<=', 0), ('supplier_rank', '<=', 0)]
        return ['|', ('customer_rank', '>', 0), ('supplier_rank', '>', 0)]


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = "Material Master (MM)"

    # SAP Material Master Core Lexicon
    name = fields.Char(string="Material Description")
    default_code = fields.Char(string="Material Number (MATNR)")
    type = fields.Selection(string="Material Type (MTART)")
    categ_id = fields.Many2one(string="Material Group (MATKL)")
    uom_id = fields.Many2one(string="Base Unit of Measure (BUn)")
    list_price = fields.Float(string="Standard Selling Price")
    standard_price = fields.Float(string="Moving Avg / Standard Cost")

    # SAP Material Master MTART Classification
    sap_material_type = fields.Selection(
        selection=[
            ('ROH', 'Raw Materials (ROH)'),
            ('HALB', 'Semifinished Products (HALB)'),
            ('FERT', 'Finished Products (FERT)'),
            ('HAWA', 'Trading Goods (HAWA)'),
            ('DIEN', 'Services (DIEN)'),
        ],
        string="Material Type (MTART)",
        default='FERT',
        index=True,
        tracking=True,
        help="SAP Material Master Type classification:\n"
             "- ROH: Raw Materials (purchased externally, not sold)\n"
             "- HALB: Semifinished Products (manufactured internally, assembled into finished)\n"
             "- FERT: Finished Products (manufactured internally, sold)\n"
             "- HAWA: Trading Goods (purchased externally, sold directly)\n"
             "- DIEN: Services (non-physical work or consulting)",
    )

    @api.onchange('sap_material_type')
    def _onchange_sap_material_type(self):
        if self.sap_material_type == 'DIEN':
            self.type = 'service'
        elif self.sap_material_type == 'ROH':
            self.type = 'consu'
            self.purchase_ok = True
            self.sale_ok = False
        elif self.sap_material_type == 'HALB':
            self.type = 'consu'
            self.purchase_ok = True
            self.sale_ok = False
        elif self.sap_material_type == 'FERT':
            self.type = 'consu'
            self.purchase_ok = False
            self.sale_ok = True
        elif self.sap_material_type == 'HAWA':
            self.type = 'consu'
            self.purchase_ok = True
            self.sale_ok = True


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = "Material Master (MM)"

    # SAP Material Variant Core Lexicon
    name = fields.Char(string="Material Description")
    default_code = fields.Char(string="Material Number (MATNR)")
    standard_price = fields.Float(string="Moving Avg / Standard Cost")
    sap_material_type = fields.Selection(
        related='product_tmpl_id.sap_material_type',
        string="Material Type (MTART)",
        readonly=False,
        store=True,
    )


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = "Company Code (Bukrs)"

    name = fields.Char(string="Company Code Name")
    currency_id = fields.Many2one(string="Company Code Currency")


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    _description = "Plant / Distribution Center"

    name = fields.Char(string="Plant Name / Distribution Center")
    code = fields.Char(string="Plant Code (Werks)")
    company_id = fields.Many2one(string="Company Code Assignment")


class StockLocation(models.Model):
    _inherit = 'stock.location'
    _description = "Storage Location (SLoc / LGORT)"

    name = fields.Char(string="Storage Location Name")
