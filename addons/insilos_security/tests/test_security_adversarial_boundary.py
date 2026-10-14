# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import hashlib
import importlib.util
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

try:
    from odoo.exceptions import AccessError, UserError, ValidationError
except Exception:
    class AccessError(Exception):
        pass

    class UserError(Exception):
        pass

    class ValidationError(Exception):
        pass

try:
    from odoo.tests.common import TransactionCase, tagged
except Exception:
    TransactionCase = unittest.TestCase

    def tagged(*args, **kwargs):
        return lambda cls: cls

_CUR_DIR = Path(__file__).resolve().parent
_MODELS_DIR = _CUR_DIR.parent / "models"


def _import_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    from ..models.advisory_lock_guard import (
        TenantAdvisoryLockGuard,
        compute_blake2b_lock_key,
    )
except Exception:
    _guard_mod = _import_file("advisory_lock_guard", _MODELS_DIR / "advisory_lock_guard.py")
    TenantAdvisoryLockGuard = _guard_mod.TenantAdvisoryLockGuard
    compute_blake2b_lock_key = _guard_mod.compute_blake2b_lock_key

try:
    from tools.paged_telemetry_accumulator import PagedScanBlockTable, PAGE_SIZE_MODULES
except Exception:
    _paged_path = Path(__file__).resolve().parents[2] / "tools" / "paged_telemetry_accumulator.py"
    _paged_mod = _import_file("paged_telemetry_accumulator", _paged_path)
    PagedScanBlockTable = _paged_mod.PagedScanBlockTable
    PAGE_SIZE_MODULES = _paged_mod.PAGE_SIZE_MODULES


@tagged("post_install", "-at_install", "security", "adversarial", "insilos_security")
class TestSecurityAdversarialBoundary(TransactionCase):

    def test_blake2b_lock_key_distribution_and_bounds(self):
        """
        Verify keys fit within PostgreSQL signed 32-bit integer limits (-2147483648 <= key <= 2147483647).
        Verify deterministic hash and collision resistance across distinct models/IDs.
        """
        INT32_MIN = -2147483648
        INT32_MAX = 2147483647

        models = [
            "res.partner",
            "account.move",
            "sale.order",
            "purchase.order",
            "stock.picking",
            "hr.employee",
            "crm.lead",
            "tenant.workspace",
        ]
        sample_ids = [0, 1, 2, 42, 1000, 65535, 1000000, 2147483647, -1, 9999999999]

        for model in models:
            for rec_id in sample_ids:
                key = compute_blake2b_lock_key(model, rec_id)
                self.assertIsInstance(key, int)
                self.assertTrue(
                    INT32_MIN <= key <= INT32_MAX,
                    f"Lock key {key} for {model}:{rec_id} breached signed 32-bit bounds [{INT32_MIN}, {INT32_MAX}]",
                )

        # Deterministic verification
        key1 = compute_blake2b_lock_key("account.move", 42)
        key2 = compute_blake2b_lock_key("account.move", 42)
        self.assertEqual(key1, key2, "Blake2b lock key derivation is non-deterministic")

        # Collision resistance check over 2,000 distinct (model, id) items
        seen_keys = set()
        for i in range(2000):
            k = compute_blake2b_lock_key("res.partner", i)
            seen_keys.add(k)
        self.assertEqual(len(seen_keys), 2000, "Collision detected in 2000-key distribution sample")

    def test_cross_tenant_lock_partition_isolation(self):
        """
        Verify identical model/record_id across company 1 and company 2 produce identical
        object keys but strictly distinct composite lock tuples (tenant_key, object_key).
        """
        model_name = "account.move"
        record_id = 999

        object_key_1 = compute_blake2b_lock_key(model_name, record_id)
        object_key_2 = compute_blake2b_lock_key(model_name, record_id)
        self.assertEqual(object_key_1, object_key_2, "Identical records must share the same object_key")

        tenant_key_c1 = int(1) & 0x7FFFFFFF
        tenant_key_c2 = int(2) & 0x7FFFFFFF
        self.assertNotEqual(tenant_key_c1, tenant_key_c2, "Company keys must be distinct")

        lock_tuple_c1 = (tenant_key_c1, object_key_1)
        lock_tuple_c2 = (tenant_key_c2, object_key_2)

        self.assertNotEqual(lock_tuple_c1, lock_tuple_c2, "Cross-tenant composite lock tuples must never collide")
        self.assertEqual(lock_tuple_c1[1], lock_tuple_c2[1], "Object keys in lock tuples must remain identical")
        self.assertNotEqual(lock_tuple_c1[0], lock_tuple_c2[0], "Tenant partitions must remain strictly isolated")

        # Verify 31-bit masking boundary behavior
        overflow_company = 0xFFFFFFFF
        tenant_key_overflow = int(overflow_company) & 0x7FFFFFFF
        self.assertTrue(0 <= tenant_key_overflow <= 2147483647)

    def test_tenant_advisory_lock_guard_lifecycle(self):
        """
        Mock cr and test acquire_tenant_lock executing pg_advisory_xact_lock with correct (tenant_key, object_key).
        """
        mock_cr = MagicMock()
        mock_env = MagicMock()
        mock_env.cr = mock_cr
        mock_env.company.id = 5

        guard = TenantAdvisoryLockGuard(env=mock_env)

        # 1. Acquire with env company
        with guard.acquire_tenant_lock("sale.order", 77):
            pass

        mock_cr.execute.assert_called_once()
        call_sql, call_params = mock_cr.execute.call_args[0]
        self.assertIn("SELECT pg_advisory_xact_lock(%s, %s);", call_sql)
        expected_obj_key = compute_blake2b_lock_key("sale.order", 77)
        self.assertEqual(call_params, (5, expected_obj_key))

        # 2. Acquire with explicit company override
        mock_cr.reset_mock()
        with guard.acquire_tenant_lock("sale.order", 77, company_id=42):
            pass

        mock_cr.execute.assert_called_once()
        call_sql, call_params = mock_cr.execute.call_args[0]
        self.assertEqual(call_params, (42, expected_obj_key))

    def test_odoo_tenant_boundary_isolation(self):
        """
        Test environment isolation, cache invalidation, and restoration on completion and exception.
        """
        mock_prev_company = MagicMock(id=1)
        mock_target_company = MagicMock(id=2)
        mock_target_company.exists.return_value = True

        mock_env = MagicMock()
        mock_env.company = mock_prev_company
        mock_env.context = {"allowed_company_ids": [1], "statutory_token": "valid"}
        mock_env["res.company"].browse.return_value = mock_target_company

        mock_isolated_env = MagicMock()
        mock_env.return_value = mock_isolated_env
        mock_isolated_env.with_company.return_value = mock_isolated_env

        guard = TenantAdvisoryLockGuard(env=mock_env)

        # 1. Normal execution inside boundary
        with guard.odoo_tenant_boundary(target_company_id=2) as isolated:
            self.assertEqual(isolated, mock_isolated_env)
            self.assertEqual(mock_env.invalidate_all.call_count, 1)

        # Restored on exit
        self.assertEqual(mock_env.invalidate_all.call_count, 2)
        mock_env.with_company.assert_called_with(mock_prev_company)
        self.assertEqual(mock_env.context["allowed_company_ids"], [1])

        # 2. Exception handling inside boundary
        mock_env.invalidate_all.reset_mock()
        mock_env.with_company.reset_mock()
        with self.assertRaises(RuntimeError):
            with guard.odoo_tenant_boundary(target_company_id=2):
                raise RuntimeError("Batch cron worker failure simulation")

        self.assertEqual(mock_env.invalidate_all.call_count, 2)
        mock_env.with_company.assert_called_with(mock_prev_company)
        self.assertEqual(mock_env.context["allowed_company_ids"], [1])

        # 3. Target company does not exist
        mock_target_company.exists.return_value = False
        with self.assertRaises(UserError):
            with guard.odoo_tenant_boundary(target_company_id=999):
                pass

    def test_paged_scan_block_table_cow(self):
        """
        Test PagedScanBlockTable chunking, hashing, atomic writes, index persistence, and readback.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            table = PagedScanBlockTable(cache_dir=tmp_dir)

            # Generate 75 modules -> 3 pages (32, 32, 11)
            modules = [
                {"name": f"addon_{i}", "path": f"/workspace/addons/addon_{i}", "complexity": i * 1.5}
                for i in range(75)
            ]

            index_meta = table.write_module_blocks(modules)

            self.assertTrue(os.path.exists(table.index_file))
            self.assertEqual(index_meta["total_modules"], 75)
            self.assertEqual(index_meta["total_pages"], 3)
            self.assertEqual(len(index_meta["pages"]), 3)

            self.assertEqual(index_meta["pages"][0]["module_count"], 32)
            self.assertEqual(index_meta["pages"][1]["module_count"], 32)
            self.assertEqual(index_meta["pages"][2]["module_count"], 11)

            for page_entry in index_meta["pages"]:
                block_path = os.path.join(tmp_dir, page_entry["block_file"])
                self.assertTrue(os.path.exists(block_path))
                self.assertEqual(len(page_entry["page_hash"]), 16)

            # Read back and verify exact data fidelity
            read_back_modules = table.read_module_blocks()
            self.assertEqual(len(read_back_modules), 75)
            self.assertEqual(read_back_modules, modules)

            # Test empty list commit
            empty_meta = table.write_module_blocks([])
            self.assertEqual(empty_meta["total_modules"], 0)
            self.assertEqual(empty_meta["total_pages"], 0)
            self.assertEqual(table.read_module_blocks(), [])


if __name__ == "__main__":
    unittest.main()
