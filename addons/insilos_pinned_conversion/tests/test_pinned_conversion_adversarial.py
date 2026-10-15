# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import ast
import hashlib
import importlib.util
import math
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
    from ..models.pinned_conversion_cron import PinnedConversionCron, derive_company_lock_key
    from ..models.conversion_engine import ConversionEngine
    from ..models.conversion_journal_helper import ConversionJournalHelper
except Exception:
    _cron_mod = _import_file("pinned_conversion_cron", _MODELS_DIR / "pinned_conversion_cron.py")
    PinnedConversionCron = _cron_mod.PinnedConversionCron
    derive_company_lock_key = _cron_mod.derive_company_lock_key

    _engine_mod = _import_file("conversion_engine", _MODELS_DIR / "conversion_engine.py")
    ConversionEngine = _engine_mod.ConversionEngine

    _helper_mod = _import_file("conversion_journal_helper", _MODELS_DIR / "conversion_journal_helper.py")
    ConversionJournalHelper = _helper_mod.ConversionJournalHelper


@tagged('post_install', '-at_install', 'security', 'adversarial', 'pinned_conversion')
class TestPinnedConversionAdversarial(TransactionCase):
    """
    Sovereign Adversarial Verification Suite:
    DERS-ZLRR (Deterministic Ephemeral Rate-Window Snapshotting with Zero-Lock Read Reconciliation)
    and Decree 70 Statutory Barrier for Pinned Conversions.
    """

    def test_adv_01_ast_static_scan_prohibit_session_advisory_lock(self):
        """
        1. AST static scan: Prohibit session-scoped pg_advisory_lock.
           Only transaction-scoped pg_try_advisory_xact_lock is permitted.
        """
        model_files = [
            _MODELS_DIR / "pinned_conversion_cron.py",
            _MODELS_DIR / "conversion_engine.py",
            _MODELS_DIR / "conversion_journal_helper.py",
        ]
        for fpath in model_files:
            self.assertTrue(fpath.exists(), f"Missing expected model file: {fpath}")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            # Ensure session-scoped pg_advisory_lock is strictly prohibited
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

        # Confirm strictly pg_try_advisory_xact_lock in cron
        cron_path = _MODELS_DIR / "pinned_conversion_cron.py"
        with open(cron_path, "r", encoding="utf-8") as f:
            cron_src = f.read()
        self.assertIn("pg_try_advisory_xact_lock", cron_src)
        self.assertIn("hashlib.md5", cron_src)
        self.assertIn("struct.unpack", cron_src)

        # Parse AST to verify class and method definitions
        tree = ast.parse(cron_src)
        classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        self.assertIn("PinnedConversionCron", classes)
        cron_methods = {n.name for n in ast.walk(classes["PinnedConversionCron"]) if isinstance(n, ast.FunctionDef)}
        self.assertIn("process_247_conversions", cron_methods)
        self.assertIn("_process_company_conversion", cron_methods)
        self.assertIn("_execute_conversion_pipeline", cron_methods)

    def test_adv_02_concurrency_race_stress_16_threads(self):
        """
        2. Concurrency race stress: 16 threads compete for the company advisory lock.
           Exactly 1 acquires the lock, 15 yield cleanly without deadlock.
        """
        company_id = 7
        target_company = MagicMock()
        target_company.id = company_id

        # Simulating PostgreSQL transaction-scoped advisory lock state
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
        completion_barrier = threading.Barrier(num_threads)
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

            def execute_pipeline_simulation(comp):
                # Simulate transaction work while holding transaction-scoped lock
                time.sleep(0.01)
                return True

            cron_inst = MagicMock()
            cron_inst.env = mock_env
            cron_inst.with_company = MagicMock(return_value=cron_inst)
            cron_inst._process_company_conversion = PinnedConversionCron._process_company_conversion.__get__(cron_inst)
            cron_inst._execute_conversion_pipeline = MagicMock(side_effect=execute_pipeline_simulation)

            try:
                # Synchronize start across all 16 threads
                barrier.wait()
                res = cron_inst._process_company_conversion(target_company)
                results.append((thread_idx, res, cron_inst._execute_conversion_pipeline.called))
            except Exception as e:
                errors.append((thread_idx, e))
            finally:
                # Wait for all threads to complete their attempts before releasing transaction lock
                completion_barrier.wait()
                if current_held_key[0] is not None:
                    # Simulating transaction commit auto-release
                    mock_release_lock(current_held_key[0])

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors encountered: {errors}")
        self.assertEqual(len(results), 16)

        winners = [r for r in results if r[1] is True]
        yielders = [r for r in results if r[1] is False]

        self.assertEqual(len(winners), 1, f"Expected exactly 1 winner, got {len(winners)}")
        self.assertEqual(len(yielders), 15, f"Expected exactly 15 yielders, got {len(yielders)}")

    def test_adv_03_decree70_statutory_barrier_and_multicompany_boundary(self):
        """
        3. Decree 70 statutory barrier & multi-company boundary assertion.
           - Invoices belonging to company B raise AccessError under company A.
           - Invoices with state != 'draft' raise ValidationError.
           - Invoices with edi_state not in [False, 'to_send'] raise ValidationError.
           - Valid draft invoices succeed and trigger journal helper revaluation.
        """
        comp_a = MagicMock()
        comp_a.id = 1
        comp_b = MagicMock()
        comp_b.id = 2

        mock_helper = MagicMock()
        mock_helper.with_company.return_value = mock_helper
        mock_helper.create_exchange_adjustment_entry.return_value = {'entry_id': 999, 'status': 'applied'}

        mock_env = MagicMock()
        mock_env.company = comp_a
        mock_env.__getitem__.side_effect = lambda k: mock_helper if k == 'insilos.conversion.journal.helper' else MagicMock()

        engine = ConversionEngine()
        engine_inst = MagicMock()
        engine_inst.env = mock_env
        engine_inst.with_company = MagicMock(return_value=engine_inst)
        engine_inst._apply_revaluation_entry = ConversionEngine._apply_revaluation_entry.__get__(engine_inst)
        engine_inst._revalue_contract_invoices = ConversionEngine._revalue_contract_invoices.__get__(engine_inst)

        # 1. Multi-Company Boundary Test: Foreign company invoice
        foreign_inv = MagicMock()
        foreign_inv.id = 101
        foreign_inv.company_id = comp_b
        foreign_inv.state = 'draft'
        foreign_inv.edi_state = False

        with self.assertRaises(AccessError):
            engine_inst._apply_revaluation_entry(foreign_inv, pinned_rate=25000.0)

        # 2. Decree 70 Barrier: Posted invoice
        posted_inv = MagicMock()
        posted_inv.id = 102
        posted_inv.company_id = comp_a
        posted_inv.state = 'posted'
        posted_inv.edi_state = False

        with self.assertRaises(ValidationError):
            engine_inst._apply_revaluation_entry(posted_inv, pinned_rate=25000.0)

        # 3. Decree 70 Barrier: EDI-signed / sent invoice
        signed_inv = MagicMock()
        signed_inv.id = 103
        signed_inv.company_id = comp_a
        signed_inv.state = 'draft'
        signed_inv.edi_state = 'sent'

        with self.assertRaises(ValidationError):
            engine_inst._apply_revaluation_entry(signed_inv, pinned_rate=25000.0)

        # 4. Valid Draft Invoice: Passes Decree 70 barrier
        valid_inv = MagicMock()
        valid_inv.id = 104
        valid_inv.company_id = comp_a
        valid_inv.state = 'draft'
        valid_inv.edi_state = 'to_send'
        valid_inv.amount_total = 1000.0

        res = engine_inst._apply_revaluation_entry(valid_inv, pinned_rate=1.05)
        self.assertEqual(res, {'entry_id': 999, 'status': 'applied'})
        mock_helper.create_exchange_adjustment_entry.assert_called_with(valid_inv, 50.0)

    def test_adv_04_double_entry_balance_and_cache_invalidation(self):
        """
        4. Double-entry debit/credit balance assertion and cache invalidation.
           - Double-entry balance check: math.isclose(total_debit, total_credit, abs_tol=1e-4).
           - Raises ValidationError on unbalanced lines.
           - On exception: evicts cache via self.env.invalidate_all() and raises.
        """
        mock_cr = MagicMock()
        savepoint_ctx = MagicMock()
        mock_cr.savepoint.return_value = savepoint_ctx
        savepoint_ctx.__enter__.return_value = None
        savepoint_ctx.__exit__.return_value = None

        mock_env = MagicMock()
        mock_env.cr = mock_cr
        mock_env.invalidate_all = MagicMock()

        helper = ConversionJournalHelper()
        helper_inst = MagicMock()
        helper_inst.env = mock_env
        helper_inst.create_exchange_adjustment_entry = ConversionJournalHelper.create_exchange_adjustment_entry.__get__(helper_inst)

        inv = MagicMock()
        inv.id = 888
        inv.company_id.id = 1

        # 1. Balanced entry succeeds
        entry = helper_inst.create_exchange_adjustment_entry(inv, 300.0, total_debit=300.0, total_credit=300.0)
        self.assertEqual(entry['total_debit'], 300.0)
        self.assertEqual(entry['total_credit'], 300.0)
        self.assertTrue(math.isclose(entry['total_debit'], entry['total_credit'], abs_tol=1e-4))
        mock_cr.savepoint.assert_called_with("pinned_conv_sp_888")

        # 2. Unbalanced entry raises ValidationError and triggers cache invalidation
        mock_env.invalidate_all.reset_mock()
        with self.assertRaises(ValidationError):
            helper_inst.create_exchange_adjustment_entry(inv, 300.0, total_debit=300.0, total_credit=299.0)

        # Assert cache was evicted on exception
        mock_env.invalidate_all.assert_called_once()

        # 3. Simulated savepoint error also triggers cache invalidation
        mock_env.invalidate_all.reset_mock()
        mock_cr.savepoint.side_effect = RuntimeError("Database connection reset")
        with self.assertRaises(RuntimeError):
            helper_inst.create_exchange_adjustment_entry(inv, 300.0)

        mock_env.invalidate_all.assert_called_once()
