# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
from insilos import models, api

_logger = logging.getLogger(__name__)

# ==============================================================================
# SAP Enterprise Lexicon Canonical Mapping
# ==============================================================================
SAP_MODEL_DESCRIPTIONS = {
    'res.partner': 'Business Partner (BP)',
    'product.template': 'Material Master (MM)',
    'product.product': 'Material Variant',
    'sale.order': 'SD Sales Order',
    'purchase.order': 'MM Purchase Order',
    'stock.picking': 'Goods Movement / Delivery',
    'stock.move': 'Material Movement Item',
    'account.move': 'FI Accounting Document',
    'account.account': 'G/L Account',
    'account.analytic.account': 'Cost Center / Profit Center',
    'mrp.production': 'PP Production Order',
    'mrp.bom': 'Production Bill of Materials',
    'mrp.workcenter': 'Work Center / Routing Resource',
    'stock.warehouse': 'Plant / Distribution Center',
    'stock.location': 'Storage Location (SLoc)',
    'res.company': 'Company Code (CC)',
}

SAP_FIELD_STRINGS = {
    'res.partner': {
        'name': 'Business Partner Name',
        'ref': 'BP Number / Search Term',
        'customer_rank': 'Customer Role Indicator',
        'supplier_rank': 'Vendor Role Indicator',
        'vat': 'Tax Number / Tax ID',
        'street': 'Street / House Number',
        'city': 'City / Postal District',
        'zip': 'Postal Code',
        'country_id': 'Country Key',
        'phone': 'Telephone',
        'email': 'E-Mail Address',
    },
    'product.template': {
        'name': 'Material Description',
        'default_code': 'Material Number (MATNR)',
        'type': 'Material Type (MTART)',
        'categ_id': 'Material Group (MATKL)',
        'list_price': 'Standard Selling Price',
        'standard_price': 'Moving Average / Standard Cost',
        'uom_id': 'Base Unit of Measure (BUn)',
        'uom_po_id': 'Order Unit of Measure',
    },
    'sale.order': {
        'name': 'SD Document Number',
        'partner_id': 'Sold-to Party (Customer BP)',
        'partner_invoice_id': 'Bill-to Party (BP)',
        'partner_shipping_id': 'Ship-to Party (BP)',
        'date_order': 'Document Date',
        'validity_date': 'Quotation Valid Until',
        'order_line': 'Sales Order Items',
        'amount_total': 'Net Value + Tax',
        'payment_term_id': 'Terms of Payment',
    },
    'purchase.order': {
        'name': 'MM Document Number',
        'partner_id': 'Vendor / Supplier BP',
        'date_order': 'PO Order Date',
        'date_planned': 'Scheduled Delivery Date',
        'order_line': 'Purchase Order Items',
        'amount_total': 'Gross Order Value',
        'payment_term_id': 'Terms of Payment',
    },
    'stock.picking': {
        'name': 'Delivery / Goods Movement No.',
        'partner_id': 'Delivery BP Party',
        'picking_type_id': 'Movement Type / Process',
        'location_id': 'Source Storage Location (SLoc)',
        'location_dest_id': 'Destination Storage Location (SLoc)',
        'scheduled_date': 'Planned Movement Date',
        'origin': 'Reference Document (PO/SO)',
    },
    'account.move': {
        'name': 'FI Document Number',
        'partner_id': 'Business Partner Account',
        'invoice_date': 'Billing / Invoice Date',
        'date': 'Posting Date in General Ledger',
        'invoice_line_ids': 'Billing Document Items',
        'line_ids': 'General Ledger Line Items',
        'ref': 'Reference Document (XBLNR)',
        'invoice_payment_term_id': 'Terms of Payment',
    },
    'account.account': {
        'name': 'G/L Account Description',
        'code': 'G/L Account Number',
        'account_type': 'Account Type / Statement Category',
    },
    'mrp.production': {
        'name': 'Production Order Number',
        'product_id': 'Header Material',
        'bom_id': 'Production BOM Reference',
        'date_deadline': 'Basic Finish Date',
        'workorder_ids': 'Production Operations / Routings',
        'qty_producing': 'Confirmed Quantity',
        'product_qty': 'Target Order Quantity',
    },
}


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Harmonize field labels to SAP Enterprise Lexicon."""
        res = super().fields_get(allfields=allfields, attributes=attributes)
        model_overrides = SAP_FIELD_STRINGS.get(self._name)
        if model_overrides and res:
            for field_name, new_string in model_overrides.items():
                if field_name in res and isinstance(res[field_name], dict):
                    res[field_name]['string'] = new_string
        return res

    @api.model
    def get_views(self, views, options=None):
        """Harmonize model description in view metadata to SAP conventions."""
        res = super().get_views(views, options=options)
        sap_desc = SAP_MODEL_DESCRIPTIONS.get(self._name)
        if sap_desc and isinstance(res, dict) and 'models' in res:
            if self._name in res['models'] and isinstance(res['models'][self._name], dict):
                res['models'][self._name]['description'] = sap_desc
        return res


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def update_sap_menus(self):
        """Safely updates top-level menus to SAP Enterprise Lexicon."""
        SAP_MENUS = {
            'contacts.menu_contacts': 'Business Partner (BP)',
            'sale.sale_menu_root': 'Sales & Distribution (SD)',
            'purchase.menu_purchase_root': 'Materials Management (MM)',
            'stock.menu_stock_root': 'Logistics & Inventory (MM-IM)',
            'account.menu_finance': 'Financials & Controlling (FI/CO)',
            'mrp.menu_mrp_root': 'Production Planning (PP)',
            'spreadsheet_dashboard.spreadsheet_dashboard_menu_root': 'Executive Analytics',
            'mail.menu_root_discuss': 'Enterprise Collaboration',
        }
        for xml_id, sap_name in SAP_MENUS.items():
            try:
                menu = self.env.ref(xml_id, raise_if_not_found=False)
                if menu:
                    menu.name = sap_name
            except Exception as e:
                _logger.warning("Could not rename menu %s: %s", xml_id, e)
        return True

