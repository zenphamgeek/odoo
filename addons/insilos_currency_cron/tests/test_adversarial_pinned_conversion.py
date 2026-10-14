# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import ast
import hashlib
import importlib.util
import struct
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    from ..models.account_pinned_conversion import AccountPinnedConversion
    from ..models.pinned_conversion_engine import PinnedConversionEngine, generate_dual_key_lock_id, LOCK_NAMESPACE
except Exception:
    _acc_mod = _import_file("account_pinned_conversion", _MODELS_DIR / "account_pinned_conversion.py")
    AccountPinnedConversion = _acc_mod.AccountPinnedConversion

    _engine_mod = _import_file("pinned_conversion_engine", _MODELS_DIR / "pinned_conversion_engine.py")
    PinnedConversionEngine = _engine_mod.PinnedConversionEngine
    generate_dual_key_lock_id = _engine_mod.generate_dual_key_lock_id
    LOCK_NAMESPACE = _engine_mod.LOCK_NAMESPACE


@tagged('post_install', '-at_install', 'security', 'adversarial', 'pinned_conversion')
class TestAdversarialPinnedConversion(TransactionCase):
    """
    Sovereign Adversarial Verification Suite:
    DPAS-TSM (Dual-Key Prefect-Airflow Slot-Sensing Transactional State Machine) Protocol
    for Pinned Conversions.
    """

    def test_adv_01_ast_static_scan_prohibit_session_advisory_lock(self):
        """
        1. AST static scan: Prohibit session-scoped pg_advisory_lock.
           Only transaction-scoped pg_try_advisory_xact_lock is permitted.
           Validate all classes, fields, and method signatures.
        """
        model_files = [
            _MODELS_DIR / "account_pinned_conversion.py",
            _MODELS_DIR / "pinned_conversion_engine.py",
        ]
        for fpath in model_files:
            self.assertTrue(fpath.exists(), f"Missing model file: {fpath}")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertNotIn(
                "pg_advisory_lock",
                content.replace("pg_try_advisory_xact_lock", ""),
                f"Session-scoped pg_advisory_lock prohibited in {fpath.name}",
            )
            self.assertNotIn(
                "pg_advisory_unlock",
                content,
                f"pg_advisory_unlock prohibited in {fpath.name}",
            )

        # Inspect account_pinned_conversion.py
        acc_path = _MODELS_DIR / "account_pinned_conversion.py"
        with open(acc_path, "r", encoding="utf-8") as f:
            acc_src = f.read()
        self.assertIn("_name = 'account.pinned.conversion'", acc_src)
        self.assertIn("statutory_locked", acc_src)
        self.assertIn("idempotency_key", acc_src)
        self.assertIn("last_error", acc_src)

        tree_acc = ast.parse(acc_src)
        classes_acc = {n.name: n for n in ast.walk(tree_acc) if isinstance(n, ast.ClassDef)}
        self.assertIn("AccountPinnedConversion", classes_acc)
        acc_methods = {n.name for n in ast.walk(classes_acc["AccountPinnedConversion"]) if isinstance(n, ast.FunctionDef)}
        self.assertIn("_compute_and_lock_statutory_rate", acc_methods)

        # Inspect pinned_conversion_engine.py
        eng_path = _MODELS_DIR / "pinned_conversion_engine.py"
        with open(eng_path, "r", encoding="utf-8") as f:
            eng_src = f.read()
        self.assertIn("_name = 'insilos.pinned.conversion.engine'", eng_src)
        self.assertIn("pg_try_advisory_xact_lock", eng_src)
        self.assertIn("allowed_company_ids=[company.id]", eng_src)
        self.assertIn("statutory_locked = True", eng_src)
        self.assertIn("hashlib.blake2b(token_payload.encode(), digest_size=8).hexdigest()", eng_src)
        self.assertIn("with self.env.cr.savepoint(): record._compute_and_lock_statutory_rate(idempotency_token)", eng_src)

        tree_eng = ast.parse(eng_src)
        classes_eng = {n.name: n for n in ast.walk(tree_eng) if isinstance(n, ast.ClassDef)}
        self.assertIn("PinnedConversionEngine", classes_eng)
        eng_methods = {n.name for n in ast.walk(classes_eng["PinnedConversionEngine"]) if isinstance(n, ast.FunctionDef)}
        self.assertIn("_generate_dual_key_lock_id", eng_methods)
        self.assertIn("process_pinned_conversions_cron", eng_methods)
        self.assertIn("_process_company_conversions_isolated", eng_methods)

    def test_adv_02_dual_key_lock_generation_and_concurrency_race(self):
        """
        2. Dual-key generation and 16-thread concurrency race stress.
           Verifies mathematical confinement of the 64-bit dual-key lock ID.
           16 threads compete for advisory lock: exactly 1 wins, 15 yield cleanly.
        """
        engine = PinnedConversionEngine()

        # Check dual-key derivation
        ns_hash = int(hashlib.blake2b(LOCK_NAMESPACE.encode()).hexdigest()[:8], 16) & 0xFFFFFFFF
        for cid in [1, 7, 42, 9999]:
            expected_key = (ns_hash << 32) | (cid & 0xFFFFFFFF)
            gen_key = engine._generate_dual_key_lock_id(cid)
            self.assertEqual(gen_key, expected_key)
            self.assertEqual(gen_key & 0xFFFFFFFF, cid)
            self.assertEqual((gen_key >> 32) & 0xFFFFFFFF, ns_hash)

        # 16-thread concurrency simulation
        company_id = 42
        target_company = MagicMock()
        target_company.id = company_id

        pg_advisory_lock_table = set()
        table_lock = threading.Lock()

        def mock_try_advisory_xact_lock(key):
            with table_lock:
                if key in pg_advisory_lock_table:
                    return False
                pg_advisory_lock_table.add(key)
                return True

        def mock_release_lock(key):
            with table_lock:
                pg_advisory_lock_table.discard(key)

        num_threads = 16
        barrier = threading.Barrier(num_threads)
        results = []
        errors = []

        def worker_task(thread_idx):
            import time
            mock_cr = MagicMock()
            current_held_key = [None]

            def cr_execute(sql, params=None):
                if "pg_try_advisory_xact_lock" in sql and params:
                    key = params[0]
                    acquired = mock_try_advisory_xact_lock(key)
                    if acquired:
                        current_held_key[0] = key
                    mock_cr.fetchone.return_value = (acquired,)
                else:
                    mock_cr.fetchone.return_value = (True,)

            mock_cr.execute.side_effect = cr_execute

            mock_env = MagicMock()
            mock_env.cr = mock_cr
            mock_env.company = target_company
            mock_env.context = {'allowed_company_ids': [company_id]}
            mock_env.__getitem__.side_effect = lambda k: MagicMock(search=MagicMock(return_value=[target_company])) if k == 'res.company' else MagicMock()

            cron_inst = MagicMock()
            cron_inst.env = mock_env
            cron_inst._generate_dual_key_lock_id = PinnedConversionEngine._generate_dual_key_lock_id.__get__(cron_inst)
            cron_inst.process_pinned_conversions_cron = PinnedConversionEngine.process_pinned_conversions_cron.__get__(cron_inst)
            
            isolated_inst = MagicMock()
            def simulate_isolated_work(comp):
                time.sleep(0.05)
                return ['simulated_done']
            isolated_inst._process_company_conversions_isolated = MagicMock(side_effect=simulate_isolated_work)
            cron_inst.with_context = MagicMock(return_value=isolated_inst)

            try:
                barrier.wait()
                res = cron_inst.process_pinned_conversions_cron()
                results.append((thread_idx, res.get(company_id, {})))
            except Exception as e:
                errors.append((thread_idx, e))
            finally:
                if current_held_key[0] is not None:
                    time.sleep(0.02)
                    mock_release_lock(current_held_key[0])

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors encountered: {errors}")
        self.assertEqual(len(results), 16)

        winners = [r for r in results if r[1].get('acquired') is True]
        yielders = [r for r in results if r[1].get('acquired') is False]

        self.assertEqual(len(winners), 1, f"Expected exactly 1 winner, got {len(winners)}")
        self.assertEqual(len(yielders), 15, f"Expected exactly 15 yielders, got {len(yielders)}")

    def test_adv_03_tenant_boundary_isolation(self):
        """
        3. Tenant boundary isolation assertions.
           - Records from foreign company raise AccessError.
           - Context allowed_company_ids mismatch raises AccessError.
        """
        comp_a = MagicMock()
        comp_a.id = 1
        comp_b = MagicMock()
        comp_b.id = 2

        engine = PinnedConversionEngine()
        engine_inst = MagicMock()
        engine_inst.env = MagicMock()
        engine_inst.env.context = {'allowed_company_ids': [1]}
        engine_inst._process_company_conversions_isolated = PinnedConversionEngine._process_company_conversions_isolated.__get__(engine_inst)

        # Record belonging to foreign company (Company 2)
        foreign_rec = MagicMock()
        foreign_rec.id = 501
        foreign_rec.company_id = comp_b
        foreign_rec.statutory_locked = False
        foreign_rec.invoice_id = False

        engine_inst.env.__getitem__.side_effect = lambda k: MagicMock(search=MagicMock(return_value=[foreign_rec]))

        with self.assertRaises(AccessError):
            engine_inst._process_company_conversions_isolated(comp_a)

        # Target company not in context allowed_company_ids
        engine_inst.env.context = {'allowed_company_ids': [99]}
        with self.assertRaises(AccessError):
            engine_inst._process_company_conversions_isolated(comp_a)

    def test_adv_04_decree_70_statutory_barrier_and_idempotency(self):
        """
        4. Decree 70 statutory immutability barrier, Prefect idempotency, and Airflow savepoint.
           - Invoices with state in ['posted', 'cancel'] set statutory_locked = True.
           - Calling _compute_and_lock_statutory_rate on statutory_locked record raises ValidationError.
           - Valid draft conversion successfully computes rate, sets state = 'computed' and idempotency_key.
           - Exception inside Airflow savepoint transitions record to 'failed_retry' with last_error.
        """
        comp = MagicMock()
        comp.id = 1

        mock_cr = MagicMock()
        savepoint_ctx = MagicMock()
        mock_cr.savepoint.return_value = savepoint_ctx
        savepoint_ctx.__enter__.return_value = None
        savepoint_ctx.__exit__.return_value = None

        mock_env = MagicMock()
        mock_env.cr = mock_cr
        mock_env.context = {'allowed_company_ids': [1]}

        engine_inst = MagicMock()
        engine_inst.env = mock_env
        engine_inst._process_company_conversions_isolated = PinnedConversionEngine._process_company_conversions_isolated.__get__(engine_inst)

        # 1. Invoice posted triggers statutory lock
        rec_posted_inv = MagicMock()
        rec_posted_inv.id = 701
        rec_posted_inv.company_id = comp
        rec_posted_inv.statutory_locked = False
        posted_inv = MagicMock()
        posted_inv.state = 'posted'
        rec_posted_inv.invoice_id = posted_inv

        # 2. Invoice cancelled triggers statutory lock
        rec_cancel_inv = MagicMock()
        rec_cancel_inv.id = 702
        rec_cancel_inv.company_id = comp
        rec_cancel_inv.statutory_locked = False
        cancel_inv = MagicMock()
        cancel_inv.state = 'cancel'
        rec_cancel_inv.invoice_id = cancel_inv

        # 3. Valid draft record
        rec_valid = MagicMock()
        rec_valid.id = 703
        rec_valid.company_id = comp
        rec_valid.statutory_locked = False
        rec_valid.rate = 1.085
        rec_valid.date_conversion = '2026-10-15'
        draft_inv = MagicMock()
        draft_inv.state = 'draft'
        rec_valid.invoice_id = draft_inv
        rec_valid._compute_and_lock_statutory_rate = AccountPinnedConversion._compute_and_lock_statutory_rate.__get__(rec_valid)

        # 4. Faulty record failing in savepoint
        rec_failing = MagicMock()
        rec_failing.id = 704
        rec_failing.company_id = comp
        rec_failing.statutory_locked = False
        rec_failing.date_conversion = '2026-10-15'
        rec_failing.invoice_id = False
        rec_failing._compute_and_lock_statutory_rate = MagicMock(side_effect=RuntimeError("Simulated FX gateway timeout"))

        all_recs = [rec_posted_inv, rec_cancel_inv, rec_valid, rec_failing]
        mock_env.__getitem__.side_effect = lambda k: MagicMock(search=MagicMock(return_value=all_recs))

        processed = engine_inst._process_company_conversions_isolated(comp)

        # Verify posted & cancel invoices set statutory_locked = True
        self.assertTrue(rec_posted_inv.statutory_locked)
        self.assertTrue(rec_cancel_inv.statutory_locked)

        # Verify valid record computed successfully
        self.assertIn(703, processed)
        self.assertEqual(rec_valid.state, 'computed')
        self.assertEqual(rec_valid.rate, 1.085)
        self.assertTrue(isinstance(rec_valid.idempotency_key, str))
        self.assertEqual(len(rec_valid.idempotency_key), 16)  # 8 bytes blake2b = 16 hex chars

        # Verify statutory locked record rejects mutation
        with self.assertRaises(ValidationError):
            AccountPinnedConversion._compute_and_lock_statutory_rate(rec_posted_inv, "test_token")

        # Verify failing record was isolated and transitioned to failed_retry
        self.assertNotIn(704, processed)
        self.assertEqual(rec_failing.state, 'failed_retry')
        self.assertIn("Simulated FX gateway timeout", rec_failing.last_error)
