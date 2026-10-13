# -*- coding: utf-8 -*-
"""Adversarial and Unit Test Suite for MRP Template Classifier & Eager Dereference Guard.

Verifies:
- F1/F2: MrpBomLine._skip_bom_line, MrpBomByproduct._skip_byproduct_line, and
  MrpRoutingWorkcenter._skip_operation_line do NOT eagerly access product._name
  or product._fields on falsy / None / False / empty recordset products.
- F3: Centralized MrpBom._is_template_record handles standard and duck-typed models.
- F4: catalog.item and duck-typed template fallbacks return expected classification.
"""

import unittest
from unittest.mock import MagicMock

from odoo.addons.mrp.models.mrp_bom import MrpBom, MrpBomLine, MrpBomByproduct
from odoo.addons.mrp.models.mrp_routing import MrpRoutingWorkcenter


class MockEmptyRecordset:
    """Simulates an Odoo empty recordset which evaluates to False in boolean context."""
    def __bool__(self):
        return False

    def __len__(self):
        return 0


class MockRecord:
    """Mock Odoo record with configurable _name and _fields."""
    def __init__(self, name, fields=None):
        self._name = name
        self._fields = fields or {}

    def __bool__(self):
        return True


class TestMrpBomIsTemplateRecord(unittest.TestCase):
    """Unit tests for centralized MrpBom._is_template_record."""

    def setUp(self):
        self.bom_model = MagicMock(spec=MrpBom)

    def test_falsy_inputs_return_false(self):
        """Falsy inputs (False, None, empty containers) must safely return False."""
        falsy_cases = [False, None, "", 0, (), [], {}, MockEmptyRecordset()]
        for case in falsy_cases:
            with self.subTest(case=case):
                result = MrpBom._is_template_record(self.bom_model, case)
                self.assertFalse(result, f"Expected False for falsy input: {case!r}")

    def test_product_template_returns_true(self):
        """Standard product.template records must return True."""
        record = MockRecord('product.template', {'name': None, 'product_tmpl_id': None})
        self.assertTrue(MrpBom._is_template_record(self.bom_model, record))

    def test_catalog_item_returns_true(self):
        """catalog.item records (Odoo Catalog integration) must return True."""
        record = MockRecord('catalog.item', {'name': None})
        self.assertTrue(MrpBom._is_template_record(self.bom_model, record))

    def test_product_product_variant_returns_false(self):
        """Standard product.product variant records must return False."""
        record = MockRecord('product.product', {
            'product_tmpl_id': None,
            'name': None,
        })
        self.assertFalse(MrpBom._is_template_record(self.bom_model, record))

    def test_duck_typed_custom_template_returns_true(self):
        """Duck-typed model with product_variant_ids but no product_tmpl_id is a template."""
        record = MockRecord('custom.catalog.template', {
            'product_variant_ids': None,
            'name': None,
        })
        self.assertTrue(MrpBom._is_template_record(self.bom_model, record))

    def test_duck_typed_custom_variant_returns_false(self):
        """Duck-typed model with product_tmpl_id is a variant, not a template."""
        record = MockRecord('custom.catalog.variant', {
            'product_tmpl_id': None,
            'product_variant_ids': None,
            'name': None,
        })
        self.assertFalse(MrpBom._is_template_record(self.bom_model, record))

    def test_duck_typed_unrelated_model_returns_false(self):
        """Unrelated model without variant fields must return False."""
        record = MockRecord('res.partner', {'name': None, 'email': None})
        self.assertFalse(MrpBom._is_template_record(self.bom_model, record))

    def test_object_lacking_fields_attr_returns_false(self):
        """Object lacking _fields attribute must not crash with AttributeError."""
        class BareObj:
            _name = 'bare.object'
        bare_obj = BareObj()
        result = MrpBom._is_template_record(self.bom_model, bare_obj)
        self.assertFalse(result)


class TestMrpBomLineSkipBomLine(unittest.TestCase):
    """Adversarial tests for MrpBomLine._skip_bom_line."""

    def setUp(self):
        self.line = MagicMock(spec=MrpBomLine)
        self.line.ensure_one = MagicMock()
        self.bom_mock = MagicMock(spec=MrpBom)
        self.bom_mock._is_template_record.side_effect = lambda rec: MrpBom._is_template_record(self.bom_mock, rec)
        self.line.env = {'mrp.bom': self.bom_mock}
        self.line.bom_product_template_attribute_value_ids = MagicMock()

    def test_falsy_product_short_circuits_without_attribute_error(self):
        """Falsy product must return False without AttributeError or calling _skip_for_no_variant."""
        falsy_cases = [False, None, MockEmptyRecordset()]
        for case in falsy_cases:
            with self.subTest(case=case):
                self.bom_mock.reset_mock()
                result = MrpBomLine._skip_bom_line(self.line, case)
                self.assertFalse(result)
                self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_template_product_returns_false(self):
        """Template product must return False and not invoke _skip_for_no_variant."""
        template_cases = [
            MockRecord('product.template'),
            MockRecord('catalog.item'),
            MockRecord('custom.tmpl', {'product_variant_ids': None}),
        ]
        for tmpl in template_cases:
            with self.subTest(tmpl=tmpl._name):
                self.bom_mock.reset_mock()
                result = MrpBomLine._skip_bom_line(self.line, tmpl)
                self.assertFalse(result)
                self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_variant_product_delegates_to_skip_for_no_variant(self):
        """Variant product must delegate to mrp.bom._skip_for_no_variant."""
        variant = MockRecord('product.product', {'product_tmpl_id': None})
        self.bom_mock._skip_for_no_variant.return_value = True

        result = MrpBomLine._skip_bom_line(self.line, variant, never_attribute_values='NEVER_VALS')
        self.assertTrue(result)
        self.bom_mock._skip_for_no_variant.assert_called_once_with(
            variant,
            self.line.bom_product_template_attribute_value_ids,
            'NEVER_VALS'
        )


class TestMrpBomByproductSkipByproductLine(unittest.TestCase):
    """Adversarial tests for MrpBomByproduct._skip_byproduct_line."""

    def setUp(self):
        self.byproduct = MagicMock(spec=MrpBomByproduct)
        self.byproduct.ensure_one = MagicMock()
        self.bom_mock = MagicMock(spec=MrpBom)
        self.bom_mock._is_template_record.side_effect = lambda rec: MrpBom._is_template_record(self.bom_mock, rec)
        self.byproduct.env = {'mrp.bom': self.bom_mock}
        self.byproduct.bom_product_template_attribute_value_ids = MagicMock()

    def test_falsy_product_short_circuits_without_attribute_error(self):
        """Falsy product must return False without calling _skip_for_no_variant."""
        falsy_cases = [False, None, MockEmptyRecordset()]
        for case in falsy_cases:
            with self.subTest(case=case):
                self.bom_mock.reset_mock()
                result = MrpBomByproduct._skip_byproduct_line(self.byproduct, case)
                self.assertFalse(result)
                self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_template_product_returns_false(self):
        """Template product must return False."""
        template_cases = [
            MockRecord('product.template'),
            MockRecord('catalog.item'),
        ]
        for tmpl in template_cases:
            with self.subTest(tmpl=tmpl._name):
                self.bom_mock.reset_mock()
                result = MrpBomByproduct._skip_byproduct_line(self.byproduct, tmpl)
                self.assertFalse(result)
                self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_variant_product_delegates_to_skip_for_no_variant(self):
        """Variant product must delegate to mrp.bom._skip_for_no_variant."""
        variant = MockRecord('product.product', {'product_tmpl_id': None})
        self.bom_mock._skip_for_no_variant.return_value = False

        result = MrpBomByproduct._skip_byproduct_line(self.byproduct, variant)
        self.assertFalse(result)
        self.bom_mock._skip_for_no_variant.assert_called_once()


class TestMrpRoutingWorkcenterSkipOperationLine(unittest.TestCase):
    """Adversarial tests for MrpRoutingWorkcenter._skip_operation_line."""

    def setUp(self):
        self.op = MagicMock(spec=MrpRoutingWorkcenter)
        self.op.ensure_one = MagicMock()
        self.op.active = True
        self.bom_mock = MagicMock(spec=MrpBom)
        self.bom_mock._is_template_record.side_effect = lambda rec: MrpBom._is_template_record(self.bom_mock, rec)
        self.op.env = {'mrp.bom': self.bom_mock}
        self.op.bom_product_template_attribute_value_ids = MagicMock()

    def test_inactive_operation_line_returns_true(self):
        """Archived operation lines must return True regardless of product."""
        self.op.active = False
        result = MrpRoutingWorkcenter._skip_operation_line(self.op, False)
        self.assertTrue(result)
        self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_falsy_product_short_circuits_without_attribute_error(self):
        """Active operation with falsy product must return False without AttributeError."""
        falsy_cases = [False, None, MockEmptyRecordset()]
        for case in falsy_cases:
            with self.subTest(case=case):
                self.bom_mock.reset_mock()
                result = MrpRoutingWorkcenter._skip_operation_line(self.op, case)
                self.assertFalse(result)
                self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_template_product_returns_false(self):
        """Active operation with template product must return False."""
        template_cases = [
            MockRecord('product.template'),
            MockRecord('catalog.item'),
        ]
        for tmpl in template_cases:
            with self.subTest(tmpl=tmpl._name):
                self.bom_mock.reset_mock()
                result = MrpRoutingWorkcenter._skip_operation_line(self.op, tmpl)
                self.assertFalse(result)
                self.bom_mock._skip_for_no_variant.assert_not_called()

    def test_variant_product_delegates_to_skip_for_no_variant(self):
        """Active operation with variant product must delegate to _skip_for_no_variant."""
        variant = MockRecord('product.product', {'product_tmpl_id': None})
        self.bom_mock._skip_for_no_variant.return_value = True

        result = MrpRoutingWorkcenter._skip_operation_line(self.op, variant)
        self.assertTrue(result)
        self.bom_mock._skip_for_no_variant.assert_called_once()


if __name__ == '__main__':
    unittest.main()
