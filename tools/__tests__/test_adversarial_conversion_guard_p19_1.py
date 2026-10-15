#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/__tests__/test_adversarial_conversion_guard_p19_1.py
==========================================================
Patch 19.1 Adversarial Security Test Suite for Cryptographic Struct Bipartite
Partitioning (CSBP-32x2), Length-Prefixed Canonical Tokens, Delimiter Injection
Resistance, and Dual Cache Purge Execution.
"""

import importlib.util
import os
import sys
from unittest.mock import MagicMock

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

GUARD_PATH = os.path.join(ROOT_DIR, "addons/insilos_adapter/models/cron_conversion_guard.py")


def _get_guard_instance():
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.insilos_adapter.models.cron_conversion_guard", GUARD_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    guard = mod.InsilosConversionGuard.__new__(mod.InsilosConversionGuard)
    return guard, mod.exceptions, mod.psycopg2


def test_bipartite_keys_signed_32bit_bounds():
    """
    Verify keys fit strictly within PostgreSQL int4 bounds (-2147483648 <= k <= 2147483647).
    Test extreme cases:
      - (1, "res.partner", 42)
      - (0, "", 0)
      - (999999, "sale.order.line", 9223372036854775807)
      - (None, "account.move", None)
    """
    guard, _, _ = _get_guard_instance()

    extreme_cases = [
        (1, "res.partner", 42),
        (0, "", 0),
        (999999, "sale.order.line", 9223372036854775807),
        (None, "account.move", None),
    ]

    for comp, model, rec in extreme_cases:
        k1, k2 = guard._generate_bipartite_advisory_keys(comp, model, rec)
        assert -2147483648 <= k1 <= 2147483647, f"Key1 out of int4 bounds for ({comp}, {model}, {rec}): {k1}"
        assert -2147483648 <= k2 <= 2147483647, f"Key2 out of int4 bounds for ({comp}, {model}, {rec}): {k2}"
        assert isinstance(k1, int), f"Key1 must be int, got {type(k1)}"
        assert isinstance(k2, int), f"Key2 must be int, got {type(k2)}"

        # Also verify 64-bit deterministic key bounds
        k_det = guard._generate_deterministic_advisory_key(comp, model, rec)
        assert -9223372036854775808 <= k_det <= 9223372036854775807, f"Deterministic key out of int8 bounds: {k_det}"
        assert isinstance(k_det, int)


def test_delimiter_injection_resistance():
    """
    Verify namespace tokens with colons and pipes do not produce identical keys:
      k1_a, k2_a = guard._generate_bipartite_advisory_keys(1, "res.partner:special", 10)
      k1_b, k2_b = guard._generate_bipartite_advisory_keys(10, "partner:special", 1)
      assert (k1_a, k2_a) != (k1_b, k2_b)
    """
    guard, _, _ = _get_guard_instance()

    k1_a, k2_a = guard._generate_bipartite_advisory_keys(1, "res.partner:special", 10)
    k1_b, k2_b = guard._generate_bipartite_advisory_keys(10, "partner:special", 1)
    assert (k1_a, k2_a) != (k1_b, k2_b), (
        f"Critical Failure: Delimiter colon injection caused key collision! ({k1_a}, {k2_a}) == ({k1_b}, {k2_b})"
    )

    # Additional adversarial delimiter injections with pipes and colons
    k1_c, k2_c = guard._generate_bipartite_advisory_keys(1, "res|partner", 10)
    k1_d, k2_d = guard._generate_bipartite_advisory_keys(10, "partner", 1)
    assert (k1_c, k2_c) != (k1_d, k2_d), "Pipe injection collision detected"

    # Deterministic advisory key delimiter injection resistance
    det_a = guard._generate_deterministic_advisory_key("1:res", "partner", 10)
    det_b = guard._generate_deterministic_advisory_key("1", "res:partner", 10)
    assert det_a != det_b, f"Deterministic key colon injection collision: {det_a} == {det_b}"

    det_c = guard._generate_deterministic_advisory_key(1, "model|name", 10)
    det_d = guard._generate_deterministic_advisory_key("1|model", "name", 10)
    assert det_c != det_d, f"Deterministic key pipe injection collision: {det_c} == {det_d}"


def test_savepoint_cache_invalidation_invoked():
    """
    Mock record raising ValidationError. Assert BOTH mock_env.clear() and mock_env.invalidate_all() are called.
    """
    guard, exceptions, psycopg2 = _get_guard_instance()

    mock_env = MagicMock()
    mock_cr = MagicMock()
    mock_env.cr = mock_cr
    mock_env.company = MagicMock(id=1)
    mock_env.clear = MagicMock()
    mock_env.invalidate_all = MagicMock()
    guard.env = mock_env

    class FailingRecord:
        def __init__(self, rec_id=42, exc=None):
            self.id = rec_id
            self.company_id = 1
            self.exc = exc or exceptions.ValidationError("Simulated constraint violation")

        def with_company(self, c):
            return self

        def _execute_conversion(self):
            raise self.exc

    # 1. ValidationError triggers sequential dual purge
    rec_val_err = FailingRecord(42, exceptions.ValidationError("Validation error occurred"))
    proc, errors = guard._process_pinned_batch_safe([rec_val_err])
    assert proc == []
    assert len(errors) == 1
    assert errors[0] == (42, "Validation error occurred")
    mock_env.clear.assert_called_once()
    mock_env.invalidate_all.assert_called_once()

    # 2. OperationalError / concurrency conflict triggers sequential dual purge
    mock_env.clear.reset_mock()
    mock_env.invalidate_all.reset_mock()
    db_err_cls = getattr(psycopg2, "OperationalError", RuntimeError)
    rec_db_err = FailingRecord(43, db_err_cls("deadlock detected"))
    proc, errors = guard._process_pinned_batch_safe([rec_db_err])
    assert proc == []
    assert len(errors) == 1
    assert "DB_CONCURRENCY_ABORT" in errors[0][1]
    mock_env.clear.assert_called_once()
    mock_env.invalidate_all.assert_called_once()

    # 3. Generic Exception triggers sequential dual purge
    mock_env.clear.reset_mock()
    mock_env.invalidate_all.reset_mock()
    rec_unhandled = FailingRecord(44, RuntimeError("Catastrophic disk corruption"))
    proc, errors = guard._process_pinned_batch_safe([rec_unhandled])
    assert proc == []
    assert len(errors) == 1
    assert errors[0] == (44, "CRITICAL_INTERNAL_ERROR")
    mock_env.clear.assert_called_once()
    mock_env.invalidate_all.assert_called_once()


def run_all_tests():
    test_bipartite_keys_signed_32bit_bounds()
    test_delimiter_injection_resistance()
    test_savepoint_cache_invalidation_invoked()
    print("[✓] All tests in test_adversarial_conversion_guard_p19_1.py passed successfully!")


if __name__ == "__main__":
    run_all_tests()
