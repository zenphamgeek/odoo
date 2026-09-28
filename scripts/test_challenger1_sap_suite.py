#!/usr/bin/env python3
"""
Challenger 1 Empirical Verification & Adversarial Stress Suite
Council Role: SAP Enterprise Lexicon, Document Lifecycles & Movement Types Challenger

Comprehensive verification against live database and ORM:
- Master Data: res.partner BP roles, product.template MTART types, Org Structure
- Supply Chain SD: sale.order party roles, state transitions, account.move F2/RE billing
- Supply Chain MM: purchase.requisition, purchase.order RFQ->PO, stock.picking 601/101/311
- Physical Inventory: stock.quant 701/702, sap.movement.type matrix
- Financials & Controlling FI/CO: BKPF, BSEG, G/L Accounts, Cost Center (KOSTL) / Profit Center (PRCTR)
- Production Planning PP: mrp.production AUFNR, RESB, 261 GI / 101 GR, mrp.bom CS01, mrp.workcenter ARBPL
- Adversarial edge cases and presentation layer get_views() / fields_get() interception
"""

import sys
import os
import time
import json
import traceback

BASE_DIR = '/home/zen/O20'
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import insilos
from insilos.tools import config
config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'], setup_logging=False)
from odoo.orm.registry import Registry

test_results = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "modules": {},
    "total_checks": 0,
    "passed_checks": 0,
    "failed_checks": 0,
    "failures": [],
    "verdict": "PENDING"
}

def record_check(module, check_name, passed, details=None):
    test_results["total_checks"] += 1
    if module not in test_results["modules"]:
        test_results["modules"][module] = {"passed": 0, "failed": 0, "checks": {}}
    
    if passed:
        test_results["passed_checks"] += 1
        test_results["modules"][module]["passed"] += 1
        test_results["modules"][module]["checks"][check_name] = {"status": "PASS", "details": details}
        print(f"  [PASS] {check_name}")
    else:
        test_results["failed_checks"] += 1
        test_results["modules"][module]["failed"] += 1
        test_results["modules"][module]["checks"][check_name] = {"status": "FAIL", "details": details}
        test_results["failures"].append({"module": module, "check": check_name, "details": details})
        print(f"  [FAIL] {check_name} -> {details}")

def run_suite():
    print("=" * 80)
    print("CHALLENGER 1: EMPIRICAL VERIFICATION OF SAP ENTERPRISE LEXICON & LIFECYCLES")
    print("=" * 80)

    t0 = time.time()
    registry = Registry('odoo20_dev')
    t_reg = time.time() - t0
    print(f"[*] Registry loaded in {t_reg:.3f}s\n")

    with registry.cursor() as cr:
        env = insilos.api.Environment(cr, insilos.SUPERUSER_ID, {})
        # Rollback initial transaction so we work in clean savepoint
        cr.rollback()

        # ======================================================================
        # MODULE 1: MASTER DATA EMPIRICAL CHALLENGE
        # ======================================================================
        print("--- [MODULE 1] Master Data: Business Partner (BP) & Material Master (MM) ---")
        mod = "MasterData"

        # 1.1 res.partner model description and fields_get
        partner_model = env['res.partner']
        desc = partner_model._description
        record_check(mod, "res_partner_description", desc == "Business Partner (BP)", f"Got: {desc}")

        p_fields = partner_model.fields_get(['name', 'ref', 'vat', 'company_type', 'bp_role', 'customer_rank', 'supplier_rank'])
        record_check(mod, "bp_field_name", p_fields.get('name', {}).get('string') == "Business Partner Name", f"Got: {p_fields.get('name', {}).get('string')}")
        record_check(mod, "bp_field_ref", p_fields.get('ref', {}).get('string') == "BP Number / Search Term", f"Got: {p_fields.get('ref', {}).get('string')}")
        record_check(mod, "bp_field_role", p_fields.get('bp_role', {}).get('string') == "BP Role", f"Got: {p_fields.get('bp_role', {}).get('string')}")

        # 1.2 BP Role state transitions and bidirectional inverse
        with env.cr.savepoint():
            bp_test = partner_model.create({'name': 'Challenger BP Test Entity', 'ref': 'BP-CH-001'})
            
            # Initial state: General
            record_check(mod, "bp_role_initial_general", bp_test.bp_role == 'general' and bp_test.is_bp_general, f"Role: {bp_test.bp_role}")
            
            # Transition to Customer
            bp_test.bp_role = 'customer'
            record_check(mod, "bp_role_set_customer", bp_test.customer_rank >= 1 and bp_test.supplier_rank == 0 and bp_test.is_bp_customer and bp_test.bp_role == 'customer',
                         f"cust_rank={bp_test.customer_rank}, supp_rank={bp_test.supplier_rank}, role={bp_test.bp_role}")

            # Transition to Vendor
            bp_test.bp_role = 'vendor'
            record_check(mod, "bp_role_set_vendor", bp_test.supplier_rank >= 1 and bp_test.customer_rank == 0 and bp_test.is_bp_vendor and bp_test.bp_role == 'vendor',
                         f"cust_rank={bp_test.customer_rank}, supp_rank={bp_test.supplier_rank}, role={bp_test.bp_role}")

            # Transition to Both
            bp_test.bp_role = 'both'
            record_check(mod, "bp_role_set_both", bp_test.customer_rank >= 1 and bp_test.supplier_rank >= 1 and bp_test.bp_role == 'both',
                         f"cust_rank={bp_test.customer_rank}, supp_rank={bp_test.supplier_rank}, role={bp_test.bp_role}")

            # Transition back to General
            bp_test.bp_role = 'general'
            record_check(mod, "bp_role_revert_general", bp_test.customer_rank == 0 and bp_test.supplier_rank == 0 and bp_test.bp_role == 'general',
                         f"cust_rank={bp_test.customer_rank}, supp_rank={bp_test.supplier_rank}, role={bp_test.bp_role}")

            # Direct method tests
            m_gen = partner_model._search_bp_role('=', 'general')
            m_cust = partner_model._search_bp_role('=', 'customer')
            record_check(mod, "bp_role_direct_method_equals", bool(m_gen) and bool(m_cust), f"gen={m_gen}, cust={m_cust}")

            # ORM domain search (exposes Odoo 20 domain optimizer bug where '=' becomes 'in')
            s_gen = partner_model.search([('id', '=', bp_test.id), ('bp_role', '=', 'general')])
            s_cust = partner_model.search([('id', '=', bp_test.id), ('bp_role', '=', 'customer')])
            record_check(mod, "bp_role_search_domain_orm", bool(s_gen) and not bool(s_cust),
                         f"s_gen={bool(s_gen)}, s_cust={bool(s_cust)} (Bug: _search_bp_role drops 'in' operator)")

            # is_bp_customer search (exposes inverted logic when operator is 'in')
            s_is_cust = partner_model.search([('id', '=', bp_test.id), ('is_bp_customer', '=', True)])
            record_check(mod, "is_bp_customer_search_orm", not bool(s_is_cust),
                         f"s_is_cust={bool(s_is_cust)} (Bug: _search_bp_customer defaults to <= 0 on 'in' operator)")

        # 1.3 Material Master (product.template & product.product)
        tmpl_model = env['product.template']
        record_check(mod, "product_template_description", tmpl_model._description == "Material Master (MM)", f"Got: {tmpl_model._description}")

        t_fields = tmpl_model.fields_get(['name', 'default_code', 'type', 'sap_material_type', 'standard_price'])
        record_check(mod, "mm_field_name", t_fields.get('name', {}).get('string') == "Material Description", f"Got: {t_fields.get('name', {}).get('string')}")
        record_check(mod, "mm_field_code", t_fields.get('default_code', {}).get('string') == "Material Number (MATNR)", f"Got: {t_fields.get('default_code', {}).get('string')}")
        record_check(mod, "mm_field_type", t_fields.get('sap_material_type', {}).get('string') == "Material Type (MTART)", f"Got: {t_fields.get('sap_material_type', {}).get('string')}")

        # Test Material Master Types (ROH, HALB, FERT, HAWA, DIEN)
        with env.cr.savepoint():
            for m_type in ['ROH', 'HALB', 'FERT', 'HAWA', 'DIEN']:
                mat = tmpl_model.create({
                    'name': f'Challenger Material {m_type}',
                    'default_code': f'MAT-{m_type}-99',
                    'sap_material_type': m_type,
                })
                var = mat.product_variant_id
                record_check(mod, f"mm_type_{m_type}_creation", mat.sap_material_type == m_type and var.sap_material_type == m_type,
                             f"tmpl={mat.sap_material_type}, var={var.sap_material_type}")

        # 1.4 Org Structure (Company Code, Plant, Storage Location)
        comp_model = env['res.company']
        wh_model = env['stock.warehouse']
        loc_model = env['stock.location']
        record_check(mod, "org_company_code_desc", comp_model._description == "Company Code (Bukrs)", f"Got: {comp_model._description}")
        record_check(mod, "org_plant_desc", wh_model._description == "Plant / Distribution Center", f"Got: {wh_model._description}")
        record_check(mod, "org_sloc_desc", loc_model._description == "Storage Location (SLoc / LGORT)", f"Got: {loc_model._description}")


        # ======================================================================
        # MODULE 2: SUPPLY CHAIN SD & BILLING DOCUMENTS
        # ======================================================================
        print("\n--- [MODULE 2] Sales & Distribution (SD) & Billing Documents ---")
        mod = "SupplyChainSD"

        so_model = env['sale.order']
        record_check(mod, "sale_order_description", so_model._description == "Sales Order (SD)", f"Got: {so_model._description}")

        so_fields = so_model.fields_get(['name', 'partner_id', 'partner_invoice_id', 'partner_shipping_id', 'sap_document_type'])
        record_check(mod, "so_field_sold_to", so_fields.get('partner_id', {}).get('string') == "Sold-to Party (BP)", f"Got: {so_fields.get('partner_id', {}).get('string')}")
        record_check(mod, "so_field_bill_to", so_fields.get('partner_invoice_id', {}).get('string') == "Bill-to Party / Payer (BP)", f"Got: {so_fields.get('partner_invoice_id', {}).get('string')}")
        record_check(mod, "so_field_ship_to", so_fields.get('partner_shipping_id', {}).get('string') == "Ship-to Party (BP)", f"Got: {so_fields.get('partner_shipping_id', {}).get('string')}")

        # Test Party Roles and State Progression
        with env.cr.savepoint():
            bp_sold = partner_model.create({'name': 'Sold-To Customer', 'customer_rank': 1})
            bp_bill = partner_model.create({'name': 'Bill-To Payer', 'customer_rank': 1})
            bp_ship = partner_model.create({'name': 'Ship-To Consignee', 'customer_rank': 1})
            prod = env['product.product'].search([('type', '=', 'consu')], limit=1)
            if not prod:
                prod = tmpl_model.create({'name': 'Test Consu', 'type': 'consu'}).product_variant_id

            so = so_model.create({
                'partner_id': bp_sold.id,
                'partner_invoice_id': bp_bill.id,
                'partner_shipping_id': bp_ship.id,
                'order_line': [(0, 0, {
                    'product_id': prod.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100.0,
                })]
            })

            # Check distinct party roles
            record_check(mod, "so_party_roles_assigned", so.partner_id.id == bp_sold.id and so.partner_invoice_id.id == bp_bill.id and so.partner_shipping_id.id == bp_ship.id,
                         f"sold={so.partner_id.id}, bill={so.partner_invoice_id.id}, ship={so.partner_shipping_id.id}")

            # Check Quotation State
            record_check(mod, "so_state_quotation", so.sap_document_type == "SD Quotation / Sales Inquiry", f"Doc type: {so.sap_document_type}")

            # Check Standard Sales Order State (Confirmation)
            so.state = 'sale'
            record_check(mod, "so_state_standard_order", so.sap_document_type == "SD Standard Sales Order", f"Doc type: {so.sap_document_type}")

            # Check Completed Sales Order (Locked)
            so.locked = True
            record_check(mod, "so_state_completed_order", so.sap_document_type == "SD Completed Sales Order", f"Doc type: {so.sap_document_type}")

            # Check Cancelled State
            so.locked = False
            so.state = 'cancel'
            record_check(mod, "so_state_cancelled_order", so.sap_document_type == "SD Cancelled Sales Order", f"Doc type: {so.sap_document_type}")

        # Customer Billing Documents (F2) & Credit Memos (RE)
        inv_model = env['account.move']
        with env.cr.savepoint():
            f2_inv = inv_model.create({
                'move_type': 'out_invoice',
                'partner_id': bp_sold.id,
                'invoice_date': '2026-09-28',
                'invoice_line_ids': [(0, 0, {'product_id': prod.id, 'quantity': 5, 'price_unit': 50.0})]
            })
            record_check(mod, "billing_doc_f2", f2_inv.sap_billing_type == "Customer Billing Document (F2)", f"Got: {f2_inv.sap_billing_type}")

            re_memo = inv_model.create({
                'move_type': 'out_refund',
                'partner_id': bp_sold.id,
                'invoice_date': '2026-09-28',
                'invoice_line_ids': [(0, 0, {'product_id': prod.id, 'quantity': 1, 'price_unit': 50.0})]
            })
            record_check(mod, "billing_credit_memo_re", re_memo.sap_billing_type == "Customer Credit Memo (RE)", f"Got: {re_memo.sap_billing_type}")


        # ======================================================================
        # MODULE 3: MATERIALS MANAGEMENT (MM) & GOODS MOVEMENTS
        # ======================================================================
        print("\n--- [MODULE 3] Materials Management (MM) & Movement Types ---")
        mod = "SupplyChainMM"

        # 3.1 Purchase Orders RFQ -> MM PO
        po_model = env['purchase.order']
        record_check(mod, "purchase_order_description", po_model._description == "MM Purchase Order", f"Got: {po_model._description}")

        with env.cr.savepoint():
            vendor = partner_model.create({'name': 'Test Supplier GmbH', 'supplier_rank': 1})
            po = po_model.create({
                'partner_id': vendor.id,
                'order_line': [(0, 0, {'product_id': prod.id, 'product_qty': 20.0, 'price_unit': 30.0})]
            })
            record_check(mod, "po_state_rfq", po.sap_document_type == "Vendor Request for Quotation (RFQ)", f"Got: {po.sap_document_type}")

            po.button_confirm()
            record_check(mod, "po_state_confirmed", po.sap_document_type == "MM Purchase Order", f"Got: {po.sap_document_type}")

        # 3.2 Goods Movements (601 Outbound Delivery/PGI, 101 Inbound Delivery/GR, 311 Transfer Posting)
        pick_model = env['stock.picking']
        record_check(mod, "stock_picking_description", pick_model._description == "Goods Movement / Delivery", f"Got: {pick_model._description}")

        pt_out = env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        pt_in = env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        pt_int = env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

        with env.cr.savepoint():
            # Outbound Delivery 601
            if pt_out:
                p_out = pick_model.create({
                    'picking_type_id': pt_out.id,
                    'location_id': pt_out.default_location_src_id.id,
                    'location_dest_id': pt_out.default_location_dest_id.id,
                })
                record_check(mod, "movement_type_601_pgi", p_out.sap_movement_type == "601" and "601" in (p_out.sap_movement_desc or "") and "Outbound" in p_out.sap_delivery_type,
                             f"bwart={p_out.sap_movement_type}, desc={p_out.sap_movement_desc}, deliv={p_out.sap_delivery_type}")
            else:
                record_check(mod, "movement_type_601_pgi", False, "No outgoing picking type found")

            # Inbound Delivery 101
            if pt_in:
                p_in = pick_model.create({
                    'picking_type_id': pt_in.id,
                    'location_id': pt_in.default_location_src_id.id,
                    'location_dest_id': pt_in.default_location_dest_id.id,
                })
                record_check(mod, "movement_type_101_gr", p_in.sap_movement_type == "101" and "101" in (p_in.sap_movement_desc or "") and "Inbound" in p_in.sap_delivery_type,
                             f"bwart={p_in.sap_movement_type}, desc={p_in.sap_movement_desc}, deliv={p_in.sap_delivery_type}")
            else:
                record_check(mod, "movement_type_101_gr", False, "No incoming picking type found")

            # Transfer Posting 311
            if pt_int:
                p_int = pick_model.create({
                    'picking_type_id': pt_int.id,
                    'location_id': pt_int.default_location_src_id.id,
                    'location_dest_id': pt_int.default_location_dest_id.id,
                })
                record_check(mod, "movement_type_311_transfer", p_int.sap_movement_type == "311" and "311" in (p_int.sap_movement_desc or "") and "Transfer" in p_int.sap_delivery_type,
                             f"bwart={p_int.sap_movement_type}, desc={p_int.sap_movement_desc}, deliv={p_int.sap_delivery_type}")
            else:
                record_check(mod, "movement_type_311_transfer", False, "No internal picking type found")

        # 3.3 Physical Inventory (701 Surplus, 702 Deficit)
        quant_model = env['stock.quant']
        record_check(mod, "stock_quant_description", quant_model._description == "Physical Inventory Adjustment (MI01/MI07)", f"Got: {quant_model._description}")

        with env.cr.savepoint():
            # Check if material master ROH sets is_storable=True
            mat_roh_check = tmpl_model.create({'name': 'ROH Storable Check', 'sap_material_type': 'ROH'})
            record_check(mod, "mm_roh_is_storable_flag", mat_roh_check.is_storable is True,
                         f"is_storable={mat_roh_check.is_storable} (Note: Odoo 20 requires is_storable=True for inventory tracking)")

            loc = env.ref('stock.stock_location_stock', raise_if_not_found=False) or env['stock.location'].search([('usage', '=', 'internal')], limit=1)
            storable_tmpl = tmpl_model.create({
                'name': 'Storable Titanium Bolt for Physical Inventory',
                'type': 'consu',
                'is_storable': True,
            })
            storable_prod = storable_tmpl.product_variant_id

            quant = quant_model.create({
                'product_id': storable_prod.id,
                'location_id': loc.id,
                'quantity': 50.0,
            })
            # Surplus: inventory_diff > 0 -> 701
            quant.inventory_quantity = 55.0
            record_check(mod, "physical_inv_701_surplus", quant.sap_movement_type == "701" and "701" in (quant.sap_movement_desc or ""),
                         f"diff={quant.inventory_diff_quantity}, bwart={quant.sap_movement_type}")

            # Deficit: inventory_diff < 0 -> 702
            quant.inventory_quantity = 40.0
            record_check(mod, "physical_inv_702_deficit", quant.sap_movement_type == "702" and "702" in (quant.sap_movement_desc or ""),
                         f"diff={quant.inventory_diff_quantity}, bwart={quant.sap_movement_type}")

        # 3.4 sap.movement.type matrix table
        matrix_model = env['sap.movement.type']
        matrix_codes = ['101', '102', '261', '301', '311', '601', '701', '702']
        for c in matrix_codes:
            rec = matrix_model.search([('code', '=', c)], limit=1)
            record_check(mod, f"movement_matrix_{c}_exists", bool(rec) and bool(rec.process_category) and bool(rec.sap_tcode),
                         f"found={bool(rec)}, category={rec.process_category if rec else None}, tcode={rec.sap_tcode if rec else None}")


        # ======================================================================
        # MODULE 4: FINANCIAL ACCOUNTING & CONTROLLING (FI/CO)
        # ======================================================================
        print("\n--- [MODULE 4] Financial Accounting (FI) & Controlling (CO) ---")
        mod = "FinanceControlling"

        # 4.1 BKPF and BSEG
        move_model = env['account.move']
        record_check(mod, "bkpf_model_description", move_model._description == "FI Accounting Document (BKPF)", f"Got: {move_model._description}")

        line_model = env['account.move.line']
        record_check(mod, "bseg_model_description", line_model._description == "FI Document Line Item (BSEG)", f"Got: {line_model._description}")

        bkpf_fields = move_model.fields_get(['name', 'ref', 'date', 'invoice_date'])
        record_check(mod, "bkpf_field_budat", bkpf_fields.get('date', {}).get('string') == "Posting Date in General Ledger (BUDAT)", f"Got: {bkpf_fields.get('date', {}).get('string')}")
        record_check(mod, "bkpf_field_xblnr", bkpf_fields.get('ref', {}).get('string') == "Reference Document (XBLNR)", f"Got: {bkpf_fields.get('ref', {}).get('string')}")

        bseg_fields = line_model.fields_get(['account_id', 'debit', 'credit', 'analytic_distribution'])
        record_check(mod, "bseg_field_hkont", bseg_fields.get('account_id', {}).get('string') == "G/L Account Number (HKONT)", f"Got: {bseg_fields.get('account_id', {}).get('string')}")
        record_check(mod, "bseg_field_soll", bseg_fields.get('debit', {}).get('string') == "Debit Amount (Soll)", f"Got: {bseg_fields.get('debit', {}).get('string')}")
        record_check(mod, "bseg_field_haben", bseg_fields.get('credit', {}).get('string') == "Credit Amount (Haben)", f"Got: {bseg_fields.get('credit', {}).get('string')}")

        # 4.2 Chart of Accounts / G/L Accounts
        acc_model = env['account.account']
        record_check(mod, "chart_of_accounts_desc", acc_model._description == "Chart of Accounts / G/L Accounts", f"Got: {acc_model._description}")
        acc_fields = acc_model.fields_get(['code', 'name'])
        record_check(mod, "gl_account_field_saknr", acc_fields.get('code', {}).get('string') == "G/L Account Number (SAKNR)", f"Got: {acc_fields.get('code', {}).get('string')}")

        # 4.3 Controlling: Cost Centers (KOSTL) vs Profit Centers (PRCTR)
        an_model = env['account.analytic.account']
        record_check(mod, "analytic_account_desc", an_model._description == "Cost Center / Profit Center", f"Got: {an_model._description}")

        plan_model = env['account.analytic.plan']
        record_check(mod, "analytic_plan_kokrs_desc", plan_model._description == "Controlling Area Plan (KOKRS)", f"Got: {plan_model._description}")

        with env.cr.savepoint():
            test_plan = plan_model.create({'name': 'Challenger KOKRS Plan'})
            cc = an_model.create({'name': 'Manufacturing CC', 'code': 'KOSTL-01', 'plan_id': test_plan.id, 'co_type': 'cost_center'})
            pc = an_model.create({'name': 'Automotive Division PC', 'code': 'PRCTR-01', 'plan_id': test_plan.id, 'co_type': 'profit_center'})

            record_check(mod, "cost_center_kostl_flags", cc.is_cost_center and not cc.is_profit_center and cc.co_type == 'cost_center',
                         f"is_cc={cc.is_cost_center}, is_pc={cc.is_profit_center}")
            record_check(mod, "profit_center_prctr_flags", pc.is_profit_center and not pc.is_cost_center and pc.co_type == 'profit_center',
                         f"is_cc={pc.is_cost_center}, is_pc={pc.is_profit_center}")

            # Test search domain
            cc_res = an_model.search([('id', 'in', [cc.id, pc.id]), ('is_cost_center', '=', True)])
            record_check(mod, "cost_center_search", cc in cc_res and pc not in cc_res, f"Found: {cc_res.ids}")

        # 4.4 S_ALR_87012284 Financial Statements Actions
        bs_act = env.ref('account_reports.action_account_report_bs', raise_if_not_found=False)
        pl_act = env.ref('account_reports.action_account_report_pl', raise_if_not_found=False)
        record_check(mod, "report_bs_s_alr_87012284", bs_act and "S_ALR_87012284" in bs_act.name, f"Got: {bs_act.name if bs_act else None}")
        record_check(mod, "report_pl_s_alr_87012284", pl_act and "S_ALR_87012284" in pl_act.name, f"Got: {pl_act.name if pl_act else None}")


        # ======================================================================
        # MODULE 5: PRODUCTION PLANNING (PP)
        # ======================================================================
        print("\n--- [MODULE 5] Production Planning (PP) ---")
        mod = "ProductionPlanning"

        mrp_model = env['mrp.production']
        record_check(mod, "mrp_production_description", mrp_model._description == "Production Order (PP/CO01)", f"Got: {mrp_model._description}")

        mrp_fields = mrp_model.fields_get(['name', 'product_id', 'product_qty', 'move_raw_ids', 'movement_type_issue', 'movement_type_receipt'])
        record_check(mod, "mrp_field_aufnr", mrp_fields.get('name', {}).get('string') == "Production Order Number (AUFNR)", f"Got: {mrp_fields.get('name', {}).get('string')}")
        record_check(mod, "mrp_field_resb", mrp_fields.get('move_raw_ids', {}).get('string') == "Component Reservations (RESB)", f"Got: {mrp_fields.get('move_raw_ids', {}).get('string')}")
        record_check(mod, "mrp_field_bwart_261", mrp_fields.get('movement_type_issue', {}).get('string') == "Movement Type - Issue (BWART 261)", f"Got: {mrp_fields.get('movement_type_issue', {}).get('string')}")
        record_check(mod, "mrp_field_bwart_101", mrp_fields.get('movement_type_receipt', {}).get('string') == "Movement Type - Receipt (BWART 101)", f"Got: {mrp_fields.get('movement_type_receipt', {}).get('string')}")

        with env.cr.savepoint():
            mo = mrp_model.create({'product_id': prod.id, 'product_qty': 10.0})
            record_check(mod, "mrp_order_movement_defaults", mo.movement_type_issue == "261" and mo.movement_type_receipt == "101",
                         f"issue={mo.movement_type_issue}, receipt={mo.movement_type_receipt}")

        # BOM (CS01)
        bom_model = env['mrp.bom']
        record_check(mod, "bom_model_description", bom_model._description == "Production BOM (CS01)", f"Got: {bom_model._description}")

        # Work Center (CR01 / ARBPL)
        wc_model = env['mrp.workcenter']
        record_check(mod, "workcenter_model_description", wc_model._description == "Work Center / Routing Resource (CR01)", f"Got: {wc_model._description}")
        wc_fields = wc_model.fields_get(['code', 'time_start', 'costs_hour', 'oee'])
        record_check(mod, "wc_field_arbpl", wc_fields.get('code', {}).get('string') == "Work Center Code (ARBPL)", f"Got: {wc_fields.get('code', {}).get('string')}")
        record_check(mod, "wc_field_ruezt", wc_fields.get('time_start', {}).get('string') == "Standard Setup Time (RUEZT)", f"Got: {wc_fields.get('time_start', {}).get('string')}")


        # ======================================================================
        # MODULE 6: ADVERSARIAL STRESS TESTING & EDGE CASES
        # ======================================================================
        print("\n--- [MODULE 6] Adversarial Challenge & Presentation Interception ---")
        mod = "AdversarialStress"

        # 6.1 get_views() dynamic view metadata injection
        # Does get_views() correctly inject SAP labels into form and list views?
        views_so = so_model.get_views([(False, 'list'), (False, 'form')])
        so_meta_desc = views_so.get('models', {}).get('sale.order', {}).get('description')
        so_meta_field = views_so.get('models', {}).get('sale.order', {}).get('fields', {}).get('partner_id', {}).get('string')
        record_check(mod, "view_metadata_sale_order", so_meta_desc == "Sales Order (SD)" and so_meta_field == "Sold-to Party (BP)",
                     f"desc={so_meta_desc}, partner_field={so_meta_field}")

        views_bp = partner_model.get_views([(False, 'form')])
        bp_meta_desc = views_bp.get('models', {}).get('res.partner', {}).get('description')
        bp_meta_field = views_bp.get('models', {}).get('res.partner', {}).get('fields', {}).get('ref', {}).get('string')
        record_check(mod, "view_metadata_partner", bp_meta_desc == "Business Partner (BP)" and bp_meta_field == "BP Number / Search Term",
                     f"desc={bp_meta_desc}, ref_field={bp_meta_field}")

        # 6.2 Edge case: stock.picking without picking_type_id (DB constraint & fallback verification)
        not_null_enforced = False
        try:
            with env.cr.savepoint():
                pick_model.create({
                    'picking_type_id': False,
                    'location_id': loc.id,
                    'location_dest_id': loc.id,
                })
        except Exception:
            not_null_enforced = True
        record_check(mod, "edge_picking_not_null_enforced", not_null_enforced,
                     "PostgreSQL correctly enforces NOT NULL on picking_type_id")

        # Test picking with non-standard picking type code
        with env.cr.savepoint():
            custom_pt = env['stock.picking.type'].search([('code', 'not in', ('outgoing', 'incoming', 'internal'))], limit=1)
            if not custom_pt:
                custom_pt = env['stock.picking.type'].create({
                    'name': 'Custom Dropship Movement',
                    'code': 'dropship',
                    'sequence_code': 'DROP',
                })
            custom_pick = pick_model.create({
                'picking_type_id': custom_pt.id,
                'location_id': loc.id,
                'location_dest_id': loc.id,
            })
            record_check(mod, "edge_picking_custom_fallback", custom_pick.sap_movement_type == "N/A" and "Movement" in custom_pick.sap_delivery_type,
                         f"bwart={custom_pick.sap_movement_type}, delivery_type={custom_pick.sap_delivery_type}")

        # 6.3 Edge case: stock.quant difference = 0.0
        with env.cr.savepoint():
            zero_quant = quant_model.create({
                'product_id': storable_prod.id,
                'location_id': loc.id,
                'quantity': 100.0,
            })
            zero_quant.inventory_quantity = 100.0 # diff = 0.0
            record_check(mod, "edge_quant_zero_diff", zero_quant.sap_movement_type == "701",
                         f"diff={zero_quant.inventory_diff_quantity}, bwart={zero_quant.sap_movement_type}")

        # 6.4 Top-level menu naming verification
        menu_checks = {
            'contacts.menu_contacts': 'Business Partner (BP)',
            'sale.sale_menu_root': 'Sales & Distribution (SD)',
            'purchase.menu_purchase_root': 'Materials Management (MM)',
            'stock.menu_stock_root': 'Logistics & Inventory (MM-IM)',
            'account.menu_finance': 'Financials & Controlling (FI/CO)',
            'mrp.menu_mrp_root': 'Production Planning (PP)',
        }
        for xml_id, exp_name in menu_checks.items():
            menu = env.ref(xml_id, raise_if_not_found=False)
            record_check(mod, f"menu_{xml_id}", menu and menu.name == exp_name, f"Got: {menu.name if menu else None} (Expected: {exp_name})")

        cr.rollback()

    # Final verdict calculation
    total = test_results["total_checks"]
    passed = test_results["passed_checks"]
    failed = test_results["failed_checks"]
    test_results["verdict"] = "PASS" if failed == 0 and total > 0 else "FAIL"

    print("\n" + "=" * 80)
    print(f"SUITE COMPLETED: {passed}/{total} Checks PASSED ({failed} Failures) — VERDICT: {test_results['verdict']}")
    print("=" * 80)

    # Output results json to stdout / file
    with open('/home/zen/O20/scripts/challenger1_results.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)
    print("[*] Saved detailed test results to /home/zen/O20/scripts/challenger1_results.json")

    return failed == 0

if __name__ == '__main__':
    success = run_suite()
    sys.exit(0 if success else 1)
