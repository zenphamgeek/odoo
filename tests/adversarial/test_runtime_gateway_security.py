# -*- coding: utf-8 -*-
"""Adversarial Security Test Suite for RuntimeReportGateway.
Verifies remediations for SEC-01, SEC-02, SEC-03, and SEC-04.
"""

import unittest
import threading
import zlib
from unittest.mock import MagicMock, patch

from addons.insilos_adapter.controllers.runtime_report_gateway import (
    RuntimeReportGateway,
    ALLOWED_SUPPORT_DATABASES,
    MAX_STRING_LEN,
    MAX_TRACEBACK_LEN,
)


class TestRuntimeGatewaySecurityAdversarial(unittest.TestCase):

    def setUp(self):
        self.gateway = RuntimeReportGateway()

    def test_sec01_rejects_unauthorized_session_db_spoofing(self):
        """SEC-01: Verify that an untrusted session DB parameter cannot hijack target routing."""
        mock_request = MagicMock()
        mock_request.session.db = 'malicious_tenant_db'
        mock_request.env.get_param.return_value = None
        mock_reg = MagicMock()
        mock_reg.__contains__.side_effect = lambda m: m == 'al2c.runtime.incident'

        with patch('addons.insilos_adapter.controllers.runtime_report_gateway.request', mock_request), \
             patch('addons.insilos_adapter.controllers.runtime_report_gateway.Registry', return_value=mock_reg):
            resolved = self.gateway._resolve_target_db()
            self.assertNotEqual(resolved, 'malicious_tenant_db')
            if resolved is not None:
                self.assertIn(resolved, ALLOWED_SUPPORT_DATABASES)

    def test_sec01_configured_param_must_be_whitelisted(self):
        """SEC-01: An al2c.support_db setting outside the whitelist is strictly ignored."""
        mock_request = MagicMock()
        mock_request.env.get_param.return_value = 'forbidden_tenant_db'
        mock_reg = MagicMock()
        mock_reg.__contains__.side_effect = lambda m: m == 'al2c.runtime.incident'

        with patch('addons.insilos_adapter.controllers.runtime_report_gateway.request', mock_request), \
             patch('addons.insilos_adapter.controllers.runtime_report_gateway.Registry', return_value=mock_reg):
            resolved = self.gateway._resolve_target_db()
            self.assertNotEqual(resolved, 'forbidden_tenant_db')
            if resolved is not None:
                self.assertIn(resolved, ALLOWED_SUPPORT_DATABASES)

    def test_sec02_outbox_decoupling_prevents_synchronous_cascade(self):
        """SEC-02: Verify that incoming critical incidents stage an outbox flag instead of calling heavy methods."""
        mock_model = MagicMock()
        mock_model.search.return_value = False
        mock_model._fields = {'backlog_generation_pending': True}

        mock_env = {
            'al2c.runtime.incident': mock_model,
            'al2c.tech.asset': MagicMock(),
        }
        mock_cr = MagicMock()
        mock_reg = MagicMock()
        mock_reg.cursor.return_value.__enter__.return_value = mock_cr

        with patch('addons.insilos_adapter.controllers.runtime_report_gateway.Registry', return_value=mock_reg), \
             patch('addons.insilos_adapter.controllers.runtime_report_gateway.api.Environment', return_value=mock_env):

            payload = {'url': 'https://victim.com'}

            persisted, code = self.gateway._persist_incident_orm(
                'insilos', 'INC-2026-00001', 'fingerprint_abc', 'ASSET_01',
                'Uncaught Crash Error', 'Memory Dump', 'traceback...', 'stack...',
                'inst_01', payload, '127.0.0.1', 'https://victim.com'
            )

            self.assertTrue(persisted)
            self.assertTrue(mock_model.create.called)
            created_kwargs = mock_model.create.call_args[0][0]
            self.assertTrue(created_kwargs.get('backlog_generation_pending'))
            self.assertEqual(created_kwargs.get('severity'), 'critical')

            # Invariant: action_create_backlog_improvement must NOT be invoked synchronously
            new_record = mock_model.create.return_value
            self.assertFalse(hasattr(new_record, 'action_create_backlog_improvement') and new_record.action_create_backlog_improvement.called)

    def test_sec03_advisory_locking_executed_in_transaction(self):
        """SEC-03: Verify that pg_advisory_xact_lock is executed with deterministic positive integer key."""
        mock_model = MagicMock()
        mock_model.search.return_value = False
        mock_model._fields = {}
        mock_env = {'al2c.runtime.incident': mock_model}
        mock_cr = MagicMock()
        mock_reg = MagicMock()
        mock_reg.cursor.return_value.__enter__.return_value = mock_cr

        fingerprint = "test_fingerprint_for_crc32"
        expected_lock_key = zlib.crc32(fingerprint.encode('utf-8')) & 0x7FFFFFFF

        with patch('addons.insilos_adapter.controllers.runtime_report_gateway.Registry', return_value=mock_reg), \
             patch('addons.insilos_adapter.controllers.runtime_report_gateway.api.Environment', return_value=mock_env):

            self.gateway._persist_incident_orm(
                'insilos', 'INC-2026-00002', fingerprint, 'O20',
                'SampleError', 'Message', 'Trace', 'Stack',
                'inst_02', {}, '127.0.0.1', 'http://localhost'
            )

            # Ensure pg_advisory_xact_lock was called with expected lock key
            mock_cr.execute.assert_any_call("SELECT pg_advisory_xact_lock(%s)", (expected_lock_key,))
            mock_cr.commit.assert_called_once()

    def test_sec03_concurrency_race_condition_under_parallel_burst(self):
        """SEC-03: Simulate 20 concurrent threads submitting the exact same fingerprint."""
        lock = threading.Lock()
        db_store = {}

        def mock_search(domain, limit=None):
            fp = domain[0][2]
            with lock:
                if fp in db_store:
                    return db_store[fp]
                return False

        def mock_create(vals):
            rec = MagicMock()
            rec.incident_code = vals['incident_code']
            rec.occurrence_count = 1
            def _write(wvals):
                if 'occurrence_count' in wvals:
                    rec.occurrence_count = wvals['occurrence_count']
            rec.write.side_effect = _write
            with lock:
                db_store[vals['fingerprint']] = rec
            return rec

        mock_model = MagicMock()
        mock_model.search.side_effect = mock_search
        mock_model.create.side_effect = mock_create
        mock_model._fields = {}

        mock_env = {'al2c.runtime.incident': mock_model}
        mock_reg = MagicMock()
        mock_cr = MagicMock()
        mock_reg.cursor.return_value.__enter__.return_value = mock_cr

        fingerprint = "burst_shared_fp_hash"
        results = []

        def worker(idx):
            with patch('addons.insilos_adapter.controllers.runtime_report_gateway.Registry', return_value=mock_reg), \
                 patch('addons.insilos_adapter.controllers.runtime_report_gateway.api.Environment', return_value=mock_env):
                persisted, code = self.gateway._persist_incident_orm(
                    'insilos', f'INC-2026-{idx:05d}', fingerprint, 'O20',
                    'ConcurrencyCrash', 'Details', 'Trace', 'Stack',
                    f'inst_{idx}', {}, '127.0.0.1', 'http://localhost'
                )
                results.append((persisted, code))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 20)
        self.assertTrue(all(r[0] for r in results))
        self.assertEqual(mock_model.create.call_count, 1)
        self.assertEqual(db_store[fingerprint].occurrence_count, 20)

    def test_sec04_unbounded_payload_fields_truncated(self):
        """SEC-04: Verify fields exceeding limits are truncated cleanly in create_vals."""
        mock_model = MagicMock()
        mock_model.search.return_value = False
        mock_model._fields = {}
        mock_env = {'al2c.runtime.incident': mock_model}
        mock_cr = MagicMock()
        mock_reg = MagicMock()
        mock_reg.cursor.return_value.__enter__.return_value = mock_cr

        huge_error_name = "E" * 500
        huge_msg = "M" * (MAX_STRING_LEN + 1000)
        huge_tb = "T" * (MAX_TRACEBACK_LEN + 5000)
        huge_stack = "S" * (MAX_STRING_LEN + 1000)
        huge_url = "U" * (MAX_STRING_LEN + 1000)

        with patch('addons.insilos_adapter.controllers.runtime_report_gateway.Registry', return_value=mock_reg), \
             patch('addons.insilos_adapter.controllers.runtime_report_gateway.api.Environment', return_value=mock_env):

            self.gateway._persist_incident_orm(
                'insilos', 'INC-2026-00003', 'fp_huge', 'O20',
                huge_error_name, huge_msg, huge_tb, huge_stack,
                'inst_03', {'url': huge_url}, '127.0.0.1', huge_url
            )

            self.assertTrue(mock_model.create.called)
            created_kwargs = mock_model.create.call_args[0][0]
            self.assertLessEqual(len(created_kwargs['error_name']), 128)
            self.assertLessEqual(len(created_kwargs['error_message']), MAX_STRING_LEN)
            self.assertLessEqual(len(created_kwargs['traceback']), MAX_TRACEBACK_LEN)
            self.assertLessEqual(len(created_kwargs['component_stack']), MAX_STRING_LEN)
            self.assertLessEqual(len(created_kwargs['instance_url']), MAX_STRING_LEN)


if __name__ == '__main__':
    unittest.main()
