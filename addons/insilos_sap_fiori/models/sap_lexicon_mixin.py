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
    'sale.order': 'Sales Order (SD)',
    'sale.order.line': 'Sales Order Line Item',
    'purchase.order': 'MM Purchase Order',
    'purchase.order.line': 'Purchase Order Line Item',
    'purchase.requisition': 'Purchase Requisition (Banf) / Outline Agreement',
    'stock.picking': 'Goods Movement / Delivery',
    'stock.move': 'Material Movement Item',
    'stock.quant': 'Physical Inventory Adjustment (MI01/MI07)',
    'account.move': 'FI Accounting Document (BKPF)',
    'account.move.line': 'FI Document Line Item (BSEG)',
    'account.account': 'Chart of Accounts / G/L Accounts',
    'account.analytic.account': 'Cost Center / Profit Center',
    'account.analytic.plan': 'Controlling Area Plan (KOKRS)',
    'mrp.production': 'Production Order (PP/CO01)',
    'mrp.bom': 'Production BOM (CS01)',
    'mrp.workcenter': 'Work Center / Routing Resource (CR01)',
    'stock.warehouse': 'Plant / Distribution Center',
    'stock.location': 'Storage Location (SLoc / LGORT)',
    'res.company': 'Company Code (Bukrs)',
}

SAP_FIELD_STRINGS = {
    'res.partner': {
        'name': 'Business Partner Name',
        'ref': 'BP Number / Search Term',
        'customer_rank': 'Customer Role Indicator',
        'supplier_rank': 'Vendor Role Indicator',
        'vat': 'Tax Number (Tax ID / VAT)',
        'company_type': 'BP Category',
        'parent_id': 'Parent Business Partner',
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
        'standard_price': 'Moving Avg / Standard Cost',
        'uom_id': 'Base Unit of Measure (BUn)',
        'uom_po_id': 'Order Unit of Measure',
    },
    'product.product': {
        'name': 'Material Description',
        'default_code': 'Material Number (MATNR)',
        'standard_price': 'Moving Avg / Standard Cost',
    },
    'res.company': {
        'name': 'Company Code Name',
        'currency_id': 'Company Code Currency',
    },
    'stock.warehouse': {
        'name': 'Plant Name / Distribution Center',
        'code': 'Plant Code (Werks)',
        'company_id': 'Company Code Assignment',
    },
    'stock.location': {
        'name': 'Storage Location Name',
    },
    'sale.order': {
        'name': 'SD Document Number',
        'partner_id': 'Sold-to Party (BP)',
        'partner_invoice_id': 'Bill-to Party / Payer (BP)',
        'partner_shipping_id': 'Ship-to Party (BP)',
        'date_order': 'Document Date',
        'validity_date': 'Quotation Valid Until',
        'order_line': 'Sales Order Items',
        'amount_total': 'Net Value + Tax',
        'payment_term_id': 'Terms of Payment',
    },
    'sale.order.line': {
        'product_id': 'Material Master (MM)',
        'product_uom_qty': 'Order Quantity',
        'price_unit': 'Condition Unit Price',
        'price_subtotal': 'Item Net Value',
    },
    'purchase.requisition': {
        'name': 'Requisition / Agreement No. (BANFN)',
        'vendor_id': 'Vendor / Supplier BP',
        'requisition_type': 'Agreement Category',
        'line_ids': 'Requisition Line Items',
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
    'purchase.order.line': {
        'product_id': 'Material Master (MM)',
        'product_qty': 'Order Quantity',
        'price_unit': 'Net Order Price',
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
    'stock.move': {
        'product_id': 'Material Master (MM)',
        'product_uom_qty': 'Scheduled Quantity',
        'quantity': 'Delivered Quantity',
        'location_id': 'Source Storage Location (SLoc)',
        'location_dest_id': 'Destination Storage Location (SLoc)',
    },
    'stock.quant': {
        'product_id': 'Material Master (MM)',
        'location_id': 'Storage Location (SLoc)',
        'quantity': 'Quantity On Hand',
        'inventory_quantity': 'Physical Counted Quantity',
        'inventory_diff_quantity': 'Count Difference',
    },
    'account.move': {
        'name': 'FI Document Number',
        'ref': 'Reference Document (XBLNR)',
        'date': 'Posting Date in General Ledger (BUDAT)',
        'invoice_date': 'Document Date (BLDAT)',
        'partner_id': 'Business Partner Account',
        'invoice_line_ids': 'Billing Document Items',
        'line_ids': 'General Ledger Line Items',
        'invoice_payment_term_id': 'Terms of Payment',
    },
    'account.move.line': {
        'account_id': 'G/L Account Number (HKONT)',
        'debit': 'Debit Amount (Soll)',
        'credit': 'Credit Amount (Haben)',
        'analytic_distribution': 'CO Account Assignment',
        'partner_id': 'Business Partner Account',
    },
    'account.account': {
        'code': 'G/L Account Number (SAKNR)',
        'name': 'G/L Account Description',
        'account_type': 'Financial Statement Category',
    },
    'account.analytic.account': {
        'name': 'Cost Center / Profit Center Name',
        'code': 'Cost Center / Profit Center Key',
        'plan_id': 'Controlling Area Plan (KOKRS)',
        'co_type': 'CO Category',
    },
    'account.analytic.plan': {
        'name': 'Controlling Area Plan (KOKRS)',
    },
    'mrp.production': {
        'name': 'Production Order Number (AUFNR)',
        'product_id': 'Header Material Master',
        'product_qty': 'Target Order Quantity',
        'move_raw_ids': 'Component Reservations (RESB)',
        'bom_id': 'Production BOM Reference',
        'date_deadline': 'Basic Finish Date',
        'workorder_ids': 'Production Operations / Routings',
        'qty_producing': 'Confirmed Quantity',
        'movement_type_issue': 'Movement Type - Issue (BWART 261)',
        'movement_type_receipt': 'Movement Type - Receipt (BWART 101)',
    },
    'mrp.bom': {
        'product_tmpl_id': 'Header Material Master',
        'code': 'Alternative BOM / Reference',
        'product_qty': 'Base Quantity',
        'bom_line_ids': 'Components / BOM Line Items',
        'operation_ids': 'Production Routing Operations',
    },
    'mrp.workcenter': {
        'name': 'Work Center Description',
        'code': 'Work Center Code (ARBPL)',
        'costs_hour': 'Cost Center Activity Rate / Rate per Unit',
        'time_start': 'Standard Setup Time (RUEZT)',
        'time_stop': 'Standard Teardown / Cleanup Time',
        'oee_target': 'OEE Target Ratio (%)',
        'oee': 'Overall Equipment Effectiveness (OEE)',
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
        """Harmonize model description and field strings in view metadata to SAP conventions."""
        res = super().get_views(views, options=options)
        sap_desc = SAP_MODEL_DESCRIPTIONS.get(self._name)
        if sap_desc and isinstance(res, dict) and 'models' in res:
            if self._name in res['models'] and isinstance(res['models'][self._name], dict):
                res['models'][self._name]['description'] = sap_desc
                model_overrides = SAP_FIELD_STRINGS.get(self._name)
                if model_overrides and 'fields' in res['models'][self._name]:
                    fields_dict = res['models'][self._name]['fields']
                    for field_name, new_string in model_overrides.items():
                        if field_name in fields_dict and isinstance(fields_dict[field_name], dict):
                            fields_dict[field_name]['string'] = new_string
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

