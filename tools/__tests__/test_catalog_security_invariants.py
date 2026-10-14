#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catalog Security Invariants Test Suite (`test_catalog_security_invariants.py`)
=============================================================================
Enforces Decree 70 export tax boundaries, Circular 219 VAT classification constraints,
explicit keyword signature invariants on service templates, and multi-company template
bleed isolation across AL2C product catalogs.
"""

import ast
import unittest
from pathlib import Path

from tools.al2c_catalog_lint import (
    EXPORT_ELIGIBLE_SKUS,
    SKUS,
    Lint,
    _p,
    m2o,
)


class TestCatalogSecurityInvariants(unittest.TestCase):
    """Enforces catalog security invariants and anti-bleed multi-company isolation."""

    def test_explicit_keyword_signature_enforcement(self):
        """Ensure SKUs with service_tracking='task_in_project' have explicit 'template' attribute and is boolean."""
        # 1. Inspect SKUS dictionary entries
        task_in_project_skus = [
            code for code, spec in SKUS.items()
            if spec.get('service_tracking') == 'task_in_project'
        ]
        self.assertGreaterEqual(len(task_in_project_skus), 3, "Expected at least 3 task_in_project SKUs")
        for code in task_in_project_skus:
            spec = SKUS[code]
            self.assertIn('template', spec, f"SKU {code} missing 'template' attribute")
            self.assertIsInstance(spec['template'], bool, f"SKU {code} template attribute must be boolean")
            self.assertTrue(spec['template'], f"SKU {code} with task_in_project must require template=True")

        # 2. Verify _p helper signature accepts keyword args 'template' and 'tmpl'
        p1 = _p('delivery', 'timesheet', 'task_in_project', template=True)
        self.assertIs(p1['template'], True)
        self.assertIsInstance(p1['template'], bool)

        p2 = _p('delivery', 'timesheet', 'task_in_project', tmpl=True)
        self.assertIs(p2['template'], True)
        self.assertIsInstance(p2['template'], bool)

        p3 = _p('delivery', 'timesheet', 'task_in_project', template=False)
        self.assertIs(p3['template'], False)
        self.assertIsInstance(p3['template'], bool)

        p4 = _p('delivery', 'timesheet', 'task_in_project')
        self.assertIs(p4['template'], False)
        self.assertIsInstance(p4['template'], bool)

        # 3. Verify AST of tools/al2c_catalog_lint.py has explicit keyword 'template=True' on DGM-ONSITE SKUs
        lint_file = Path(__file__).resolve().parent.parent / "al2c_catalog_lint.py"
        source = lint_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        skus_assign = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'SKUS':
                        skus_assign = node.value
                        break
        self.assertIsNotNone(skus_assign, "Could not locate SKUS assignment in al2c_catalog_lint.py")
        self.assertIsInstance(skus_assign, ast.Dict)

        target_codes = {'DGM-ONSITE-STD', 'DGM-ONSITE-OT100', 'DGM-ONSITE-OT150'}
        found_target_codes = set()
        for k, v in zip(skus_assign.keys, skus_assign.values):
            if isinstance(k, ast.Constant) and k.value in target_codes:
                found_target_codes.add(k.value)
                self.assertIsInstance(v, ast.Call, f"Expected call expression for {k.value}")
                kw_names = [kw.arg for kw in v.keywords]
                self.assertIn(
                    'template',
                    kw_names,
                    f"SKU {k.value} must use explicit keyword argument template=True in AST"
                )
        self.assertEqual(found_target_codes, target_codes, "All DGM-ONSITE SKUs must be verified in AST")

    def test_decree70_vat_class_boundaries(self):
        """Domestic SKUs ('DGM-ONSITE-STD', 'AMS-GOLD', etc.) must not be in EXPORT_ELIGIBLE_SKUS."""
        self.assertIsInstance(EXPORT_ELIGIBLE_SKUS, set)
        self.assertEqual(
            EXPORT_ELIGIBLE_SKUS,
            {'DGM-CANVA-AWARD', 'DGM-ADMOB-REV'},
            "EXPORT_ELIGIBLE_SKUS must strictly contain only Decree 70 eligible cross-border export SKUs"
        )

        domestic_skus = [
            'DGM-ONSITE-STD',
            'DGM-ONSITE-OT100',
            'DGM-ONSITE-OT150',
            'AMS-GOLD',
            'AMS-SILVER',
            'AMS-BRONZE',
            'ERP-STARTER',
            'ERP-GROWTH',
            'ERP-ENT',
            'TRAINING-DAY',
            'CONSULT-HOUR',
            'GRC-ESSENTIALS',
        ]
        for sku in domestic_skus:
            self.assertNotIn(
                sku,
                EXPORT_ELIGIBLE_SKUS,
                f"Domestic SKU {sku} illegally present in EXPORT_ELIGIBLE_SKUS (violates Decree 70 / Circular 219)"
            )

    def test_multi_company_template_bleed_detection(self):
        """Verify cross-company template logic detects divergence."""
        class MockBackend:
            def has_model(self, model):
                return False

        # Divergent company test: SKU company 1 != template company 2
        lint_fail = Lint(MockBackend())
        sku_code = 'DGM-ONSITE-STD'
        bleed_record = {
            'default_code': sku_code,
            'type': 'service',
            'invoice_policy': 'delivery',
            'service_type': 'timesheet',
            'service_tracking': 'task_in_project',
            'recurring_invoice': False,
            'al2c_vat_class': 'vat_10',
            'company_id': 1,
            'project_template_id': {'id': 101, 'company_id': 2},
            'project_id': False,
            'categ_id': False,
            'al2c_knowledge_article_id': 10,
        }
        errors = lint_fail.skus(by_code={sku_code: bleed_record})
        self.assertIn(sku_code, errors)
        bleed_errors = [e for e in errors[sku_code] if 'Cross-company template bleed' in e]
        self.assertTrue(
            len(bleed_errors) > 0,
            f"Expected cross-company template bleed error for {sku_code}, got: {errors[sku_code]}"
        )
        self.assertIn("company 1 != template company 2", bleed_errors[0])

        # Isolated company test: SKU company 1 == template company 1
        lint_pass = Lint(MockBackend())
        isolated_record = dict(bleed_record)
        isolated_record['project_template_id'] = {'id': 101, 'company_id': 1}
        pass_errors = lint_pass.skus(by_code={sku_code: isolated_record})
        if sku_code in pass_errors:
            bleed_errors_pass = [e for e in pass_errors[sku_code] if 'Cross-company template bleed' in e]
            self.assertEqual(len(bleed_errors_pass), 0, "Clean multi-company isolation triggered false positive")

    def test_vat_0_illegal_for_domestic_skus(self):
        """Simulate Lint.skus() logic on domestic SKU with vat_0 and assert error is raised."""
        class MockBackend:
            def has_model(self, model):
                return False

        lint = Lint(MockBackend())
        domestic_code = 'DGM-ONSITE-STD'
        record_domestic_vat_0 = {
            'default_code': domestic_code,
            'type': 'service',
            'invoice_policy': 'delivery',
            'service_type': 'timesheet',
            'service_tracking': 'task_in_project',
            'recurring_invoice': False,
            'al2c_vat_class': 'vat_0',
            'company_id': 1,
            'project_template_id': {'id': 101, 'company_id': 1},
            'project_id': False,
            'categ_id': False,
            'al2c_knowledge_article_id': 10,
        }
        errors = lint.skus(by_code={domestic_code: record_domestic_vat_0})
        self.assertIn(domestic_code, errors)
        vat_0_errors = [e for e in errors[domestic_code] if 'violates Circular 219' in e]
        self.assertTrue(
            len(vat_0_errors) > 0,
            f"Expected Circular 219 violation error for domestic SKU with vat_0, got: {errors[domestic_code]}"
        )
        self.assertIn(
            f"al2c_vat_class=vat_0 illegal for non-export SKU {domestic_code} (violates Circular 219)",
            vat_0_errors[0]
        )

        # Confirm export-eligible SKU with vat_0 does NOT raise Circular 219 violation
        export_code = 'DGM-CANVA-AWARD'
        record_export_vat_0 = {
            'default_code': export_code,
            'type': 'service',
            'invoice_policy': 'order',
            'service_type': 'manual',
            'service_tracking': 'no',
            'recurring_invoice': False,
            'al2c_vat_class': 'vat_0',
            'company_id': 1,
            'project_template_id': False,
            'project_id': False,
            'categ_id': False,
            'al2c_knowledge_article_id': 10,
        }
        lint_export = Lint(MockBackend())
        export_errors = lint_export.skus(by_code={export_code: record_export_vat_0})
        if export_code in export_errors:
            export_vat_0_errors = [e for e in export_errors[export_code] if 'violates Circular 219' in e]
            self.assertEqual(len(export_vat_0_errors), 0, "Export-eligible SKU triggered false-positive Circular 219 error")


if __name__ == "__main__":
    unittest.main()
