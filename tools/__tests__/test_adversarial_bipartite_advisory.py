#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/__tests__/test_adversarial_bipartite_advisory.py
======================================================
Adversarial Security Test Suite for 32-Bit Bipartite Advisory Keys,
PostgreSQL int4 Boundary Conditions, and Savepoint Cache Guards (Patch 19).
"""

import os
import sys
from unittest.mock import MagicMock

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.dpas_tsm_lock import DPASTSMTransactionManager


def test_no_model_hash_collision_across_enterprise_models():
    """
    Verify distinct enterprise models ('account.move', 'res.partner', 'sale.order',
    'purchase.order', 'stock.picking', 'account.payment', 'product.template', 'crm.lead')
    do not collide in 32-bit bipartite namespace.
    """
    mgr = DPASTSMTransactionManager()
    enterprise_models = [
        'account.move',
        'res.partner',
        'sale.order',
        'purchase.order',
        'stock.picking',
        'account.payment',
        'product.template',
        'crm.lead',
    ]

    # Verify that within any given company, all enterprise models have distinct namespace hashes
    for company_id in [1, 2, 5, 10, 100, 999]:
        seen_keys = {}
        for model in enterprise_models:
            key1, _ = mgr.derive_bipartite_advisory_keys(company_id, model, 1)
            assert -2147483648 <= key1 <= 2147483647, f"Key1 {key1} out of signed 32-bit range"
            assert key1 not in seen_keys, (
                f"Collision detected between '{model}' and '{seen_keys.get(key1)}' "
                f"for company_id={company_id}: key1={key1}"
            )
            seen_keys[key1] = model

    # Verify across 50 companies and all 8 models (400 namespaces) zero collision
    all_seen = set()
    for company_id in range(1, 51):
        for model in enterprise_models:
            k1, _ = mgr.derive_bipartite_advisory_keys(company_id, model, 42)
            all_seen.add((company_id, model, k1))

    unique_namespaces = {(comp, mod) for comp, mod, _ in all_seen}
    unique_k1s = {k1 for _, _, k1 in all_seen}
    assert len(unique_k1s) == len(unique_namespaces), (
        f"Namespace collision across enterprise models: {len(unique_namespaces)} expected, "
        f"got {len(unique_k1s)} unique keys"
    )


def test_postgresql_int4_boundary_conditions():
    """
    Verify extreme boundary cases (0, 2147483647, 4294967295) always produce signed 32-bit ints
    in [-2147483648, 2147483647].
    """
    mgr = DPASTSMTransactionManager()
    boundary_record_ids = [
        0,
        1,
        2147483647,      # 0x7FFFFFFF (max int4)
        2147483648,      # 0x80000000 (overflows uint32 to negative int4)
        4294967295,      # 0xFFFFFFFF (-1 in signed int4)
        -1,
        -2147483648,     # -0x80000000 (min int4)
    ]

    for rec_id in boundary_record_ids:
        key1, key2 = mgr.derive_bipartite_advisory_keys(1, "account.move", rec_id)
        assert -2147483648 <= key1 <= 2147483647, f"Key1 {key1} out of signed 32-bit range for rec_id={rec_id}"
        assert -2147483648 <= key2 <= 2147483647, f"Key2 {key2} out of signed 32-bit range for rec_id={rec_id}"
        assert isinstance(key1, int)
        assert isinstance(key2, int)

    # Specific required cases: 0, 2147483647, 4294967295
    _, k2_zero = mgr.derive_bipartite_advisory_keys(1, "account.move", 0)
    assert k2_zero == 0
    _, k2_max_i32 = mgr.derive_bipartite_advisory_keys(1, "account.move", 2147483647)
    assert k2_max_i32 == 2147483647
    _, k2_max_u32 = mgr.derive_bipartite_advisory_keys(1, "account.move", 4294967295)
    assert k2_max_u32 == -1


def test_cron_conversion_guard_bipartite_and_batch_safe():
    """
    Verify _generate_bipartite_advisory_keys on InsilosConversionGuard produces int4 keys.
    Verify _process_pinned_batch_safe rejects non-int record IDs ('INVALID_RECORD_IDENTIFIER'),
    uses cr.savepoint(), clears cache on error, and triggers circuit breaker on db concurrency abort.
    """
    guard_path = os.path.join(ROOT_DIR, "addons/insilos_adapter/models/cron_conversion_guard.py")
    try:
        from odoo.addons.insilos_adapter.models.cron_conversion_guard import InsilosConversionGuard, exceptions
        import psycopg2
    except Exception:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "odoo.addons.insilos_adapter.models.cron_conversion_guard", guard_path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        InsilosConversionGuard = mod.InsilosConversionGuard
        exceptions = mod.exceptions
        psycopg2 = mod.psycopg2

    guard = InsilosConversionGuard.__new__(InsilosConversionGuard)

    # 1. Verify _generate_bipartite_advisory_keys produces int4 keys
    for comp in [1, 5, 100]:
        for model in ['account.move', 'res.partner', 'sale.order']:
            for rec in [0, 42, 2147483647, 4294967295]:
                k1, k2 = guard._generate_bipartite_advisory_keys(comp, model, rec)
                assert -2147483648 <= k1 <= 2147483647, f"Key1 {k1} out of signed 32-bit range"
                assert -2147483648 <= k2 <= 2147483647, f"Key2 {k2} out of signed 32-bit range"
                assert isinstance(k1, int)
                assert isinstance(k2, int)

    # 2. Verify _process_pinned_batch_safe
    mock_env = MagicMock()
    mock_cr = MagicMock()
    mock_env.cr = mock_cr
    mock_env.company = MagicMock(id=1)
    mock_env.clear = MagicMock()
    guard.env = mock_env

    class DummyRecord:
        def __init__(self, rec_id, return_val=None, exc=None):
            self.id = rec_id
            self.company_id = 1
            self.return_val = return_val
            self.exc = exc
            self.executed = False

        def with_company(self, company):
            return self

        def _execute_conversion(self):
            self.executed = True
            if self.exc:
                raise self.exc
            return self.return_val if self.return_val is not None else f"res_{self.id}"

    # 2a. Rejects non-int record IDs ('INVALID_RECORD_IDENTIFIER')
    rec_bad_str = DummyRecord("invalid_string_id")
    rec_bad_none = DummyRecord(None)
    rec_valid_1 = DummyRecord(101, return_val="CONVERTED_101")

    proc, errors = guard._process_pinned_batch_safe([rec_bad_str, rec_bad_none, rec_valid_1])
    assert proc == ["CONVERTED_101"]
    assert len(errors) == 2
    assert errors[0] == ("invalid_string_id", "INVALID_RECORD_IDENTIFIER")
    assert errors[1] == (None, "INVALID_RECORD_IDENTIFIER")

    # 2b. Uses cr.savepoint()
    assert mock_cr.savepoint.call_count >= 1

    # 2c. Clears cache on error (UserError / ValidationError)
    mock_cr.reset_mock()
    mock_env.clear.reset_mock()
    rec_user_err = DummyRecord(102, exc=exceptions.UserError("Business constraint violation"))
    rec_valid_2 = DummyRecord(103, return_val="CONVERTED_103")

    proc, errors = guard._process_pinned_batch_safe([rec_user_err, rec_valid_2])
    assert proc == ["CONVERTED_103"]
    assert len(errors) == 1
    assert errors[0] == (102, "Business constraint violation")
    assert mock_env.clear.call_count >= 1

    # 2d. Circuit breaker on db concurrency abort (OperationalError / TransactionRollbackError)
    mock_cr.reset_mock()
    mock_env.clear.reset_mock()
    db_err_class = getattr(psycopg2, "OperationalError", RuntimeError)
    rec_db_err = DummyRecord(201, exc=db_err_class("deadlock detected"))
    rec_blocked = DummyRecord(202, return_val="SHOULD_NOT_EXECUTE")

    proc, errors = guard._process_pinned_batch_safe([rec_db_err, rec_blocked])
    assert proc == []
    assert len(errors) == 1
    assert errors[0][0] == 201
    assert "DB_CONCURRENCY_ABORT" in errors[0][1]
    assert "deadlock detected" in errors[0][1]
    assert mock_env.clear.call_count >= 1
    assert not rec_blocked.executed, "Circuit breaker failed to halt batch on DB concurrency abort"

    # 2e. Circuit breaker on generic exception
    mock_cr.reset_mock()
    mock_env.clear.reset_mock()
    rec_fatal = DummyRecord(301, exc=RuntimeError("Catastrophic disk corruption"))
    rec_blocked_2 = DummyRecord(302, return_val="SHOULD_NOT_EXECUTE")

    proc, errors = guard._process_pinned_batch_safe([rec_fatal, rec_blocked_2])
    assert proc == []
    assert len(errors) == 1
    assert errors[0] == (301, "CRITICAL_INTERNAL_ERROR")
    assert mock_env.clear.call_count >= 1
    assert not rec_blocked_2.executed


if __name__ == "__main__":
    test_no_model_hash_collision_across_enterprise_models()
    test_postgresql_int4_boundary_conditions()
    test_cron_conversion_guard_bipartite_and_batch_safe()
    print("[✓] All tests in test_adversarial_bipartite_advisory.py passed successfully!")
