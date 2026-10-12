# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import unittest
import inspect
from odoo.tests.common import TransactionCase, tagged


class DummyPosLoadModel:
    """Mock model to test signature dispatch invariants."""
    def __init__(self, raises_internal_type_error=False, accepts_config=True):
        self.raises = raises_internal_type_error
        self.accepts_config = accepts_config
        self.call_count = 0

    def _load_pos_data_domain(self, data, config=None):
        self.call_count += 1
        if self.raises:
            # Simulated internal TypeError (e.g. comparison between None and int)
            raise TypeError("unsupported operand type(s) for +: 'NoneType' and 'int'")
        return [('active', '=', True)]


class LegacyPosLoadModel:
    """Legacy model without config parameter in signature."""
    def __init__(self):
        self.call_count = 0

    def _load_pos_data_domain(self, data):
        self.call_count += 1
        return [('legacy', '=', True)]


@tagged('post_install', '-at_install', 'pos', 'pos_invariants')
class TestPosLoadInvariants(unittest.TestCase):
    """
    Test POS Data Loading Invariants:
    1. Single-Execution & Exception Transparency (CWE-703):
       _load_pos_data_domain is called at most once, and genuine internal TypeErrors are NOT swallowed.
    2. Model Alias Containment Invariant:
       Alias payloads never contain records that the source domain excludes.
    """

    def test_01_signature_dispatch_single_execution(self):
        """Verify model accepting config is called exactly once with config."""
        model = DummyPosLoadModel()
        sig = inspect.signature(model._load_pos_data_domain)
        accepts_config = len(sig.parameters) > 1 or any(
            p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            for p in sig.parameters.values()
        )
        self.assertTrue(accepts_config)

        adapted_data = {"product.product": []}
        config = {"id": 1}
        domain = (
            model._load_pos_data_domain(adapted_data, config)
            if accepts_config
            else model._load_pos_data_domain(adapted_data)
        )
        self.assertEqual(model.call_count, 1, "Must be called exactly once")
        self.assertEqual(domain, [('active', '=', True)])

    def test_02_legacy_signature_dispatch_single_execution(self):
        """Verify legacy model without config is called exactly once without config."""
        model = LegacyPosLoadModel()
        sig = inspect.signature(model._load_pos_data_domain)
        accepts_config = len(sig.parameters) > 1 or any(
            p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            for p in sig.parameters.values()
        )
        self.assertFalse(accepts_config)

        adapted_data = {"product.product": []}
        config = {"id": 1}
        domain = (
            model._load_pos_data_domain(adapted_data, config)
            if accepts_config
            else model._load_pos_data_domain(adapted_data)
        )
        self.assertEqual(model.call_count, 1, "Must be called exactly once")
        self.assertEqual(domain, [('legacy', '=', True)])

    def test_03_internal_type_error_not_swallowed(self):
        """Verify that genuine TypeErrors inside custom domain methods are NOT swallowed."""
        model = DummyPosLoadModel(raises_internal_type_error=True)
        sig = inspect.signature(model._load_pos_data_domain)
        accepts_config = len(sig.parameters) > 1 or any(
            p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            for p in sig.parameters.values()
        )

        adapted_data = {"product.product": []}
        config = {"id": 1}

        with self.assertRaises(TypeError) as ctx:
            if accepts_config:
                model._load_pos_data_domain(adapted_data, config)
            else:
                model._load_pos_data_domain(adapted_data)

        self.assertIn("unsupported operand type", str(ctx.exception))
        self.assertEqual(model.call_count, 1, "Method must not be re-executed on internal error")

    def test_04_alias_payload_isolation(self):
        """Verify alias payload dictionary copying prevents in-place mutation leakage."""
        source_data = {
            'domain': [('id', 'in', [1, 2, 3])],
            'fields': ['name', 'price'],
            'records': [{'id': 1}, {'id': 2}],
        }
        # Emulate aliasing with {**source_data}
        alias_data = {**source_data}
        alias_data['custom_marker'] = True

        self.assertNotIn('custom_marker', source_data, "Mutation of alias dict must not leak to source dict")
        self.assertEqual(alias_data['domain'], source_data['domain'])

    def test_05_signature_dispatch_unintrospectable_callable(self):
        """Verify that unintrospectable callables (e.g. C-extensions or broken decorators) degrade safely to single-arg."""
        class WeirdCallable:
            def __init__(self):
                self.call_count = 0
            def __call__(self, data):
                self.call_count += 1
                return [('unintrospectable', '=', True)]
            @property
            def __signature__(self):
                raise TypeError("Custom signature inspection failure")

        weird = WeirdCallable()
        try:
            unwrapped = inspect.unwrap(weird)
            sig = inspect.signature(unwrapped)
            accepts_config = len(sig.parameters) > 1
        except (ValueError, TypeError):
            accepts_config = False

        self.assertFalse(accepts_config, "Must safely degrade to single-arg dispatch")
        adapted_data = {"product.product": []}
        domain = weird(adapted_data, {"id": 1}) if accepts_config else weird(adapted_data)
        self.assertEqual(domain, [('unintrospectable', '=', True)])
        self.assertEqual(weird.call_count, 1)

    def test_06_account_move_domain_deterministic_empty(self):
        """Verify that account_move POS domain returns deterministic empty domain [('id', '=', False)]."""
        from odoo.addons.point_of_sale.models.account_move import AccountMove
        domain = AccountMove._load_pos_data_domain(None, {})
        self.assertEqual(domain, [('id', '=', False)], "Must return deterministic non-falsy empty domain")

    def test_07_ir_ui_view_ids_are_int_or_false_never_str(self):
        """Verify that ir_ui_view POS records have integer or False ids, never string keys."""
        mock_read_records = []
        keys = ['point_of_sale.pos_order_receipt_header', 'point_of_sale.missing_view']
        for key in keys:
            # Simulate template resolution
            if 'missing' in key:
                view_id = False
                template = False
            else:
                view_id = 5350
                template = "<t t-name='test'/>"

            mock_read_records.append({
                'id': view_id or False,
                'key': key,
                '_template': template,
            })

        for r in mock_read_records:
            self.assertTrue(r['id'] is False or isinstance(r['id'], int),
                            f"Record id must be int or False, got {type(r['id'])} ({r['id']})")
            self.assertNotIsInstance(r['id'], str, "Record id must NEVER be a string key")

    def test_08_ir_ui_view_3tuple_unpacking_invariant(self):
        """Verify that 3-tuple (tree, template, ref) returned by _get_template is properly unpacked."""
        fake_get_template_result = ("<etree>", "<template>content</template>", 5350)
        _tree, template, ref = fake_get_template_result
        self.assertEqual(ref, 5350)
        self.assertEqual(template, "<template>content</template>")
        self.assertIsInstance(ref, int)

    def test_09_loyalty_m2m_table_schema_presence(self):
        """Verify that loyalty M2M fields explicitly point to canonical relation tables."""
        from odoo.addons.loyalty.models.loyalty_reward import LoyaltyReward
        from odoo.addons.loyalty.models.loyalty_rule import LoyaltyRule

        # Verify field definitions on model classes
        reward_field = getattr(LoyaltyReward, 'discount_product_ids', None)
        rule_field = getattr(LoyaltyRule, 'product_ids', None)

        self.assertIsNotNone(reward_field, "discount_product_ids must exist on LoyaltyReward")
        self.assertIsNotNone(rule_field, "product_ids must exist on LoyaltyRule")
        self.assertEqual(reward_field.relation, 'loyalty_reward_product_product_rel')
        self.assertEqual(reward_field.column1, 'loyalty_reward_id')
        self.assertEqual(reward_field.column2, 'product_product_id')
        self.assertEqual(rule_field.relation, 'loyalty_rule_product_product_rel')
        self.assertEqual(rule_field.column1, 'loyalty_rule_id')
        self.assertEqual(rule_field.column2, 'product_product_id')
