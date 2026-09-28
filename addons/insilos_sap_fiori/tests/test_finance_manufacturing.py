# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSapFinanceManufacturing(TransactionCase):

    def test_01_fi_accounting_documents_lexicon(self):
        """Verify account.move and account.move.line descriptions and field strings."""
        move_model = self.env['account.move']
        self.assertEqual(move_model._description, "FI Accounting Document (BKPF)")

        move_fields = move_model.fields_get(['name', 'ref', 'date', 'invoice_date'])
        self.assertEqual(move_fields['name']['string'], "FI Document Number")
        self.assertEqual(move_fields['ref']['string'], "Reference Document (XBLNR)")
        self.assertEqual(move_fields['date']['string'], "Posting Date in General Ledger (BUDAT)")
        self.assertEqual(move_fields['invoice_date']['string'], "Document Date (BLDAT)")

        line_model = self.env['account.move.line']
        self.assertEqual(line_model._description, "FI Document Line Item (BSEG)")

        line_fields = line_model.fields_get(['account_id', 'debit', 'credit', 'analytic_distribution'])
        self.assertEqual(line_fields['account_id']['string'], "G/L Account Number (HKONT)")
        self.assertEqual(line_fields['debit']['string'], "Debit Amount (Soll)")
        self.assertEqual(line_fields['credit']['string'], "Credit Amount (Haben)")
        self.assertEqual(line_fields['analytic_distribution']['string'], "CO Account Assignment")

    def test_02_chart_of_accounts_lexicon(self):
        """Verify account.account description and field strings."""
        acc_model = self.env['account.account']
        self.assertEqual(acc_model._description, "Chart of Accounts / G/L Accounts")

        acc_fields = acc_model.fields_get(['code', 'name', 'account_type'])
        self.assertEqual(acc_fields['code']['string'], "G/L Account Number (SAKNR)")
        self.assertEqual(acc_fields['name']['string'], "G/L Account Description")
        self.assertEqual(acc_fields['account_type']['string'], "Financial Statement Category")

    def test_03_co_controlling_cost_profit_centers(self):
        """Verify account.analytic.account and account.analytic.plan descriptions, fields, and categorization."""
        analytic_model = self.env['account.analytic.account']
        self.assertEqual(analytic_model._description, "Cost Center / Profit Center")

        an_fields = analytic_model.fields_get(['name', 'code', 'plan_id', 'co_type'])
        self.assertEqual(an_fields['name']['string'], "Cost Center / Profit Center Name")
        self.assertEqual(an_fields['code']['string'], "Cost Center / Profit Center Key")
        self.assertEqual(an_fields['plan_id']['string'], "Controlling Area Plan (KOKRS)")

        plan_model = self.env['account.analytic.plan']
        self.assertEqual(plan_model._description, "Controlling Area Plan (KOKRS)")
        plan_fields = plan_model.fields_get(['name'])
        self.assertEqual(plan_fields['name']['string'], "Controlling Area Plan (KOKRS)")

        # Create a default plan for testing
        test_plan = plan_model.create({'name': 'Default Controlling Area Plan'})

        # Test Cost Center (KOSTL)
        cost_center = analytic_model.create({
            'name': 'Manufacturing Assembly Cost Center',
            'code': 'CC-MFG-001',
            'plan_id': test_plan.id,
            'co_type': 'cost_center',
        })
        self.assertEqual(cost_center.co_type, 'cost_center')
        self.assertTrue(cost_center.is_cost_center)
        self.assertFalse(cost_center.is_profit_center)

        # Test Profit Center (PRCTR)
        profit_center = analytic_model.create({
            'name': 'Electric Tow Tractors Business Unit',
            'code': 'PC-EV-001',
            'plan_id': test_plan.id,
            'co_type': 'profit_center',
        })
        self.assertEqual(profit_center.co_type, 'profit_center')
        self.assertTrue(profit_center.is_profit_center)
        self.assertFalse(profit_center.is_cost_center)

        # Test searching
        cc_search = analytic_model.search([('is_cost_center', '=', True)])
        self.assertIn(cost_center, cc_search)
        self.assertNotIn(profit_center, cc_search)

        pc_search = analytic_model.search([('is_profit_center', '=', True)])
        self.assertIn(profit_center, pc_search)
        self.assertNotIn(cost_center, pc_search)

    def test_04_statutory_financial_reports_s_alr_87012284(self):
        """Verify S_ALR_87012284 Balance Sheet, P&L, Trial Balance, and General Ledger."""
        # Actions
        bs_action = self.env.ref('account_reports.action_account_report_bs')
        self.assertEqual(bs_action.name, "Balance Sheet (S_ALR_87012284)")

        pl_action = self.env.ref('account_reports.action_account_report_pl')
        self.assertEqual(pl_action.name, "Profit and Loss Statement (S_ALR_87012284)")

        coa_action = self.env.ref('account_reports.action_account_report_coa')
        self.assertEqual(coa_action.name, "Trial Balance (S_ALR_87012301)")

        gl_action = self.env.ref('account_reports.action_account_report_general_ledger')
        self.assertEqual(gl_action.name, "General Ledger (S_ALR_87012277)")

        # Balance Sheet S_ALR_87012284 Lines
        assets_line = self.env.ref('account_reports.account_financial_report_total_assets0')
        self.assertEqual(assets_line.name, "Aktiva / Total Assets")

        cur_assets_line = self.env.ref('account_reports.account_financial_report_current_assets_view0')
        self.assertEqual(cur_assets_line.name, "Umlaufvermögen / Current Assets")

        fixed_assets_line = self.env.ref('account_reports.account_financial_report_fixed_assets_view0')
        self.assertEqual(fixed_assets_line.name, "Anlagevermögen / Fixed Assets")

        liab_line = self.env.ref('account_reports.account_financial_report_liabilities_view0')
        self.assertEqual(liab_line.name, "Passiva / Total Liabilities & Equity")

        equity_line = self.env.ref('account_reports.account_financial_report_equity0')
        self.assertEqual(equity_line.name, "Eigenkapital / Equity")

        # Profit & Loss S_ALR_87012284 Lines
        rev_line = self.env.ref('account_reports.account_financial_report_revenue0')
        self.assertEqual(rev_line.name, "Umsatzerlöse / Operating Revenue")

        cogs_line = self.env.ref('account_reports.account_financial_report_cost_sales0')
        self.assertEqual(cogs_line.name, "Herstellungskosten / Cost of Goods Sold (COGS)")

        ebit_line = self.env.ref('account_reports.account_financial_report_operating_income0')
        self.assertEqual(ebit_line.name, "Betriebsergebnis / Operating Profit (EBIT)")

    def test_05_pp_production_orders_and_movement_types(self):
        """Verify mrp.production description, field strings, and movement types."""
        mrp_model = self.env['mrp.production']
        self.assertEqual(mrp_model._description, "Production Order (PP/CO01)")

        mrp_fields = mrp_model.fields_get([
            'name', 'product_id', 'product_qty', 'move_raw_ids',
            'movement_type_issue', 'movement_type_receipt'
        ])
        self.assertEqual(mrp_fields['name']['string'], "Production Order Number (AUFNR)")
        self.assertEqual(mrp_fields['product_id']['string'], "Header Material Master")
        self.assertEqual(mrp_fields['product_qty']['string'], "Target Order Quantity")
        self.assertEqual(mrp_fields['move_raw_ids']['string'], "Component Reservations (RESB)")
        self.assertEqual(mrp_fields['movement_type_issue']['string'], "Movement Type - Issue (BWART 261)")
        self.assertEqual(mrp_fields['movement_type_receipt']['string'], "Movement Type - Receipt (BWART 101)")

        # Create test product & test production order
        tmpl = self.env['product.template'].create({
            'name': 'Electric Tow Tractor V-LIFT 2500E Assembly',
            'default_code': 'MAT-FERT-TEST-001',
            'type': 'consu',
        })
        product = tmpl.product_variant_id
        order = mrp_model.create({
            'product_id': product.id,
            'product_qty': 5.0,
        })
        self.assertEqual(order.movement_type_issue, "261")
        self.assertEqual(order.movement_type_receipt, "101")
        self.assertEqual(order.product_qty, 5.0)

    def test_06_pp_production_bom_and_workcenter(self):
        """Verify mrp.bom and mrp.workcenter descriptions and field strings."""
        bom_model = self.env['mrp.bom']
        self.assertEqual(bom_model._description, "Production BOM (CS01)")

        bom_fields = bom_model.fields_get(['product_tmpl_id', 'code', 'product_qty', 'bom_line_ids'])
        self.assertEqual(bom_fields['product_tmpl_id']['string'], "Header Material Master")
        self.assertEqual(bom_fields['code']['string'], "Alternative BOM / Reference")
        self.assertEqual(bom_fields['product_qty']['string'], "Base Quantity")
        self.assertEqual(bom_fields['bom_line_ids']['string'], "Components / BOM Line Items")

        wc_model = self.env['mrp.workcenter']
        self.assertEqual(wc_model._description, "Work Center / Routing Resource (CR01)")

        wc_fields = wc_model.fields_get([
            'name', 'code', 'costs_hour', 'time_start', 'time_stop', 'oee_target', 'oee'
        ])
        self.assertEqual(wc_fields['name']['string'], "Work Center Description")
        self.assertEqual(wc_fields['code']['string'], "Work Center Code (ARBPL)")
        self.assertEqual(wc_fields['costs_hour']['string'], "Cost Center Activity Rate / Rate per Unit")
        self.assertEqual(wc_fields['time_start']['string'], "Standard Setup Time (RUEZT)")
        self.assertEqual(wc_fields['time_stop']['string'], "Standard Teardown / Cleanup Time")
        self.assertEqual(wc_fields['oee_target']['string'], "OEE Target Ratio (%)")
        self.assertEqual(wc_fields['oee']['string'], "Overall Equipment Effectiveness (OEE)")

        # Create test work center
        workcenter = wc_model.create({
            'name': 'Fiber Laser Cutting CNC Center',
            'code': 'WC-LASER-01',
            'costs_hour': 125.0,
            'time_start': 15.0,
            'time_stop': 10.0,
            'oee_target': 92.5,
        })
        self.assertEqual(workcenter.code, 'WC-LASER-01')
        self.assertEqual(workcenter.costs_hour, 125.0)
        self.assertEqual(workcenter.time_start, 15.0)
        self.assertEqual(workcenter.time_stop, 10.0)
        self.assertEqual(workcenter.oee_target, 92.5)

    def test_07_fico_and_pp_menus(self):
        """Verify FI/CO and PP menu names."""
        fi_menu = self.env.ref('account.menu_action_move_journal_line_form')
        self.assertEqual(fi_menu.name, "FI Accounting Documents")

        billing_menu = self.env.ref('account.menu_action_move_out_invoice_type')
        self.assertEqual(billing_menu.name, "Customer Billing Documents")

        coa_menu = self.env.ref('account.menu_action_account_form')
        self.assertEqual(coa_menu.name, "Chart of Accounts / G/L Accounts")

        co_menu = self.env.ref('account.menu_analytic_accounting')
        self.assertEqual(co_menu.name, "Controlling & Cost Center Accounting (CO)")

        pp_menu = self.env.ref('mrp.menu_mrp_root')
        self.assertEqual(pp_menu.name, "Production Planning (PP)")

        mo_menu = self.env.ref('mrp.menu_mrp_production_action')
        self.assertEqual(mo_menu.name, "PP Production Orders")

        bom_menu = self.env.ref('mrp.menu_mrp_bom_form_action')
        self.assertEqual(bom_menu.name, "Production Bills of Materials")

        wc_menu = self.env.ref('mrp.menu_view_resource_search_mrp')
        self.assertEqual(wc_menu.name, "Work Centers / Routing Resources")
