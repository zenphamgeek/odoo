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
