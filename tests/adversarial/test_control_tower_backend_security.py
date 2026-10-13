# -*- coding: utf-8 -*-
"""Adversarial and Unit Test Suite for Insilos Executive Control Tower Backend Security.

Verifies remediation of Swarm Security Audit findings:
- SEC-01 (CRITICAL - CWE-200 / CWE-398): Zero-Mock Fallback Invariant.
  Empty subsidiary datasets must strictly aggregate to 0.0 or 0, with zero mock constants.
- SEC-02 (HIGH - CWE-400): Database-Level Aggregation Invariant (OOM DoS Guard).
  Verifies that heavy models (account.move, stock.quant, stock.picking) utilize _read_group
  aggregations rather than unbounded .search() memory instantiations.
- SEC-03 (HIGH - CWE-843 / CWE-20): Boolean Coercion & Type Confusion Bypass Guard.
  In Python isinstance(True, int) is True; strict type(req_company_id) is int check must reject
  booleans, strings, and non-positive integers with AccessError.
- SEC-04 (MEDIUM - CWE-284): Multi-Company Air-Gap Fail-Closed Enforcement.
  Queries targeting out-of-scope company IDs must immediately raise AccessError rather than
  degrading to empty sets or leaking data.
"""

import json
import unittest
from unittest.mock import MagicMock, call

from odoo.exceptions import AccessError
from odoo.addons.insilos_sap_fiori.models.insilos_control_tower import InsilosControlTower, _format_currency_vn


def _create_mock_environment(allowed_company_ids=None, current_company_id=1):
    """Helper to construct a fully functional mock Odoo environment."""
    if allowed_company_ids is None:
        allowed_company_ids = [1, 2]

    mock_env = MagicMock()
    mock_env.companies.ids = list(allowed_company_ids)
    mock_env.company.id = current_company_id

    # Registered models for the control tower
    models_dict = {}
    model_names = [
        'account.move', 'sale.order', 'stock.picking', 'stock.quant', 'product.product',
        'mrp.workcenter', 'fleet.vehicle', 'purchase.order', 'mrp.production',
        'crm.lead', 'purchase.requisition', 'quality.check'
    ]
    for name in model_names:
        mock_m = MagicMock()
        mock_m._read_group.return_value = []
        mock_m.search.return_value = []
        mock_m.search_count.return_value = 0
        mock_m.browse.return_value = []
        models_dict[name] = mock_m

    mock_env.__getitem__.side_effect = lambda name: models_dict.get(name, MagicMock())
    mock_env.__contains__.side_effect = lambda name: name in models_dict

    instance = MagicMock(spec=InsilosControlTower)
    instance.env = mock_env
    return instance, mock_env, models_dict


class TestControlTowerCompanyAirGapSecurity(unittest.TestCase):
    """Verifies SEC-03 (Type Confusion / Boolean Coercion) and SEC-04 (Fail-Closed Air Gap)."""

    def setUp(self):
        self.instance, self.mock_env, self.models = _create_mock_environment(
            allowed_company_ids=[1, 2], current_company_id=1
        )

    def test_sec03_boolean_true_coercion_rejected(self):
        """SEC-03: company_id=True must raise AccessError due to strict type check."""
        with self.assertRaises(AccessError) as ctx:
            InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': True})
        self.assertIn("Invalid company identifier format", str(ctx.exception))

    def test_sec03_boolean_false_coercion_rejected(self):
        """SEC-03: company_id=False must raise AccessError."""
        with self.assertRaises(AccessError) as ctx:
            InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': False})
        self.assertIn("Invalid company identifier format", str(ctx.exception))

    def test_sec03_invalid_numeric_zero_or_negative_rejected(self):
        """SEC-03: company_id=0 or negative integers must be rejected."""
        for invalid_id in [0, -1, -99]:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(AccessError) as ctx:
                    InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': invalid_id})
                self.assertIn("Invalid company identifier format", str(ctx.exception))

    def test_sec03_string_type_confusion_rejected(self):
        """SEC-03: String representations of integers or injections must be rejected."""
        for invalid_str in ["1", "true", "' OR 1=1 --", "", "None"]:
            with self.subTest(invalid_str=invalid_str):
                with self.assertRaises(AccessError) as ctx:
                    InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': invalid_str})
                self.assertIn("Invalid company identifier format", str(ctx.exception))

    def test_sec03_container_types_rejected(self):
        """SEC-03: List or dict inputs for company_id must be rejected."""
        for invalid_container in [[1], [1, 2], {"id": 1}]:
            with self.subTest(invalid_container=invalid_container):
                with self.assertRaises(AccessError) as ctx:
                    InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': invalid_container})
                self.assertIn("Invalid company identifier format", str(ctx.exception))

    def test_sec04_unauthorized_out_of_scope_company_fails_closed(self):
        """SEC-04: Requesting an unpermitted subsidiary ID must fail closed with AccessError."""
        with self.assertRaises(AccessError) as ctx:
            InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': 99999})
        self.assertIn("outside the current authorized context", str(ctx.exception))

    def test_sec04_authorized_company_scoping(self):
        """SEC-04: Authorized company ID must scope all queries to that company strictly."""
        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={'company_id': 2})
        self.assertTrue(res['success'])

        # Verify that account.move._read_group domain strictly enforced company_id in [2]
        call_args_list = self.models['account.move']._read_group.call_args_list
        for call_arg in call_args_list:
            domain = call_arg[0][0]
            company_filter = next((clause for clause in domain if clause[0] == 'company_id'), None)
            self.assertIsNotNone(company_filter, f"Domain missing company_id filter: {domain}")
            self.assertEqual(company_filter[2], [2], f"Expected target_company_ids=[2], got {company_filter[2]}")

    def test_sec04_default_scoping_to_allowed_companies(self):
        """SEC-04: When no company_id filter is specified, target_company_ids defaults to all authorized."""
        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, filters={})
        self.assertTrue(res['success'])

        call_args_list = self.models['account.move']._read_group.call_args_list
        for call_arg in call_args_list:
            domain = call_arg[0][0]
            company_filter = next((clause for clause in domain if clause[0] == 'company_id'), None)
            self.assertIsNotNone(company_filter)
            self.assertEqual(company_filter[2], [1, 2])


class TestControlTowerZeroMockInvariant(unittest.TestCase):
    """Verifies SEC-01: Zero-Mock Fallback Invariant."""

    def setUp(self):
        self.instance, self.mock_env, self.models = _create_mock_environment(
            allowed_company_ids=[1], current_company_id=1
        )

    def test_sec01_empty_dataset_zero_mock_payload(self):
        """SEC-01: Empty datasets must aggregate strictly to 0.0 or 0 across all financial/inventory KPIs."""
        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})
        self.assertTrue(res['success'])

        kpis = res['kpis']
        self.assertEqual(kpis['net_revenue']['value'], 0.0)
        self.assertEqual(kpis['net_revenue']['pipeline_booked'], 0.0)
        self.assertEqual(kpis['procurement_tco']['value'], 0.0)
        self.assertEqual(kpis['procurement_tco']['tco_savings_annual'], 0.0)
        self.assertEqual(kpis['procurement_tco']['tco_savings_period'], 0.0)
        self.assertEqual(kpis['operating_cash_flow']['value'], 0.0)
        self.assertEqual(kpis['days_on_hand']['value'], 0.0)
        self.assertEqual(kpis['days_on_hand']['inventory_valuation'], 0.0)
        self.assertEqual(kpis['days_on_hand']['inventory_units'], 0.0)
        self.assertEqual(kpis['days_on_hand']['distinct_skus'], 0)

        # Industrial MES & Logistics zero state
        self.assertEqual(res['industrial_mes']['total_energy_shift_kwh'], 0.0)
        self.assertEqual(res['logistics_hub']['container_moves']['potential_penalty_averted'], 0.0)
        self.assertEqual(res['logistics_hub']['container_moves']['potential_penalty_formatted'], "0 ₫")

    def test_sec01_banned_mock_constants_absence(self):
        """SEC-01: Proves absolute absence of mock constants anywhere in the serialized payload."""
        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})
        payload_str = json.dumps(res, default=str)

        banned_constants = [
            '1860500000',     # Old mock net revenue ($1.86B)
            '20127500000',    # Old mock booked pipeline ($20.1B)
            '615300000',      # Old mock spend ($615M)
            '68767',          # Old mock inventory units
            '4250000000',     # Old mock inventory valuation ($4.25B)
            '1245250000',     # Old mock net cash flow ($1.24B)
            '2029050000',     # Old mock annual TCO savings ($2.02B)
            '₫2,029,050,000', # Old hardcoded formatted TCO string
        ]

        leaked = [b for b in banned_constants if b in payload_str]
        self.assertEqual(leaked, [], f"Detected leaked mock constants in payload: {leaked}")

    def test_sec01_dynamic_tco_formatting(self):
        """SEC-01: Verify that tco_savings_annual_formatted dynamically formats 0.0 rather than hardcoded string."""
        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})
        formatted = res['kpis']['procurement_tco']['tco_savings_annual_formatted']
        self.assertEqual(formatted, "0 ₫ / Năm")

    def test_sec01_empty_sparklines_flatten_to_zero(self):
        """SEC-01: Under empty data, sparklines must flatten to zero points without division by zero."""
        for tf in ['today', '7d', 'month', 'quarter', 'fy2026']:
            with self.subTest(timeframe=tf):
                res = InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe=tf, filters={'company_id': 1})
                rev_sparkline = res['kpis']['net_revenue']['sparkline']
                self.assertIn("points", rev_sparkline)
                self.assertTrue(all(p == 0.0 for p in rev_sparkline["points"]))
                self.assertEqual(rev_sparkline["min"], 0.0)
                self.assertEqual(rev_sparkline["max"], 0.0)
                # Verify SVG path generation succeeded
                self.assertTrue(rev_sparkline["line_d"].startswith("M "))

    def test_sec01_process_pipeline_actual_counts(self):
        """SEC-01: Process pipelines must report true counts without arbitrary mock padding (e.g. max(count, 18))."""
        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})
        pipelines = res['process_pipelines']

        for pipe_key, stages in pipelines.items():
            for stage in stages:
                self.assertEqual(stage['count'], 0, f"Stage {stage['stage']} in {pipe_key} had non-zero count: {stage['count']}")


class TestControlTowerDatabaseAggregationPerformance(unittest.TestCase):
    """Verifies SEC-02: Database-level Aggregation Invariant (OOM DoS Guard)."""

    def setUp(self):
        self.instance, self.mock_env, self.models = _create_mock_environment(
            allowed_company_ids=[1], current_company_id=1
        )

    def test_sec02_read_group_aggregation_used_for_account_moves(self):
        """SEC-02: account.move must be queried via _read_group with amount_untaxed_signed:sum, never .search()."""
        InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})

        # .search() on account.move must NEVER be called (only search_count for billing stage)
        self.assertEqual(self.models['account.move'].search.call_count, 0)
        self.assertGreaterEqual(self.models['account.move']._read_group.call_count, 2)

        # Check that aggregates specified amount_untaxed_signed:sum
        for call_arg in self.models['account.move']._read_group.call_args_list:
            aggregates = call_arg[1].get('aggregates') or (call_arg[0][1] if len(call_arg[0]) > 1 else None)
            self.assertEqual(aggregates, ['amount_untaxed_signed:sum'])

    def test_sec02_read_group_aggregation_used_for_stock_quants(self):
        """SEC-02: stock.quant must be aggregated via _read_group, preventing millions of recordset instantiations."""
        InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})

        # .search() on stock.quant must NEVER be called
        self.assertEqual(self.models['stock.quant'].search.call_count, 0)
        self.assertGreaterEqual(self.models['stock.quant']._read_group.call_count, 1)

        # First call must aggregate quantity:sum and product_id:count_distinct
        first_call = self.models['stock.quant']._read_group.call_args_list[0]
        aggregates = first_call[1].get('aggregates') or (first_call[0][1] if len(first_call[0]) > 1 else None)
        self.assertEqual(aggregates, ['quantity:sum', 'product_id:count_distinct'])

    def test_sec02_read_group_aggregation_used_for_stock_pickings(self):
        """SEC-02: stock.picking OTIF metric must use _read_group with __count, never unbounded .search()."""
        InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})

        self.assertEqual(self.models['stock.picking'].search.call_count, 0)
        self.assertGreaterEqual(self.models['stock.picking']._read_group.call_count, 1)

        otif_call = self.models['stock.picking']._read_group.call_args_list[0]
        aggregates = otif_call[1].get('aggregates') or (otif_call[0][1] if len(otif_call[0]) > 1 else None)
        self.assertEqual(aggregates, ['__count'])


class TestControlTowerWithRealAggregatedData(unittest.TestCase):
    """Verifies metric calculations when database returns actual populated aggregate values."""

    def setUp(self):
        self.instance, self.mock_env, self.models = _create_mock_environment(
            allowed_company_ids=[1], current_company_id=1
        )

    def test_real_data_aggregations_and_currency_formatting(self):
        """Verify calculations when database returns actual populated aggregate tuples."""
        # 1. Revenue: 5,250,000,000 VND
        self.models['account.move']._read_group.side_effect = [
            [(5_250_000_000.0,)],  # net revenue
            [(-1_750_000_000.0,)], # procurement spend (signed negative)
        ]
        # 2. Booked pipeline: 12,000,000,000 VND
        self.models['sale.order']._read_group.return_value = [(12_000_000_000.0,)]
        # 3. Pickings count: 120
        self.models['stock.picking']._read_group.return_value = [(120,)]

        # 4. Stock quant: total 50,000 units across 10 SKUs
        mock_product_1 = MagicMock(id=101, standard_price=20000.0)
        mock_product_2 = MagicMock(id=102, standard_price=50000.0)
        self.models['product.product'].browse.return_value = [mock_product_1, mock_product_2]

        def quant_read_group(domain, aggregates=None, groupby=None):
            if groupby == ['product_id']:
                return [
                    (mock_product_1, 30000.0),
                    (mock_product_2, 20000.0),
                ]
            return [(50000.0, 10)]

        self.models['stock.quant']._read_group.side_effect = quant_read_group

        res = InsilosControlTower.get_executive_kpi_metrics(self.instance, timeframe='7d', filters={'company_id': 1})
        kpis = res['kpis']

        # Revenue
        self.assertEqual(kpis['net_revenue']['value'], 5_250_000_000.0)
        self.assertEqual(kpis['net_revenue']['value_formatted'], "5.250 Tỷ ₫")
        self.assertEqual(kpis['net_revenue']['pipeline_booked'], 12_000_000_000.0)
        self.assertEqual(kpis['net_revenue']['pipeline_formatted'], "12.000 Tỷ ₫")

        # Spend
        self.assertEqual(kpis['procurement_tco']['value'], 1_750_000_000.0)
        self.assertEqual(kpis['procurement_tco']['value_formatted'], "1.750 Tỷ ₫")
        expected_tco_annual = round(1_750_000_000.0 * 0.033, 0)
        self.assertEqual(kpis['procurement_tco']['tco_savings_annual'], expected_tco_annual)

        # OCF = 5.25B - 1.75B = 3.5B
        self.assertEqual(kpis['operating_cash_flow']['value'], 3_500_000_000.0)
        self.assertEqual(kpis['operating_cash_flow']['value_formatted'], "+3.500 Tỷ ₫")

        # Inventory: 30k * 20k + 20k * 50k = 600M + 1000M = 1.6B
        self.assertEqual(kpis['days_on_hand']['inventory_units'], 50000.0)
        self.assertEqual(kpis['days_on_hand']['distinct_skus'], 10)
        self.assertEqual(kpis['days_on_hand']['inventory_valuation'], 1_600_000_000.0)
        self.assertEqual(kpis['days_on_hand']['value'], 18.5)

        # OTIF
        self.assertEqual(kpis['otif_delivery']['value'], 99.2)


if __name__ == '__main__':
    unittest.main()
