"""
tools/__tests__/test_sync_edge_verification.py
=============================================================================
Regression test suite for hardened edge_verification() in tools/sync_innokafe_to_pods.py.
Verifies:
1. F2: Hardened DB credential requirements in sync_innokafe_views_db.py.
2. F3 & F4: Curl fallback uses list-based run_cmd and exact status code checking.
3. F5: HTTPError (4xx/5xx) raises immediately without fallback paper-over.
4. F6: EDGE_BUILD_MARKER validation asserts content integrity (CWE-345).
=============================================================================
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

# Add tools to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sync_innokafe_to_pods import edge_verification, run_cmd


class TestEdgeVerificationHardening(TestCase := unittest.TestCase):

    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_http_error_fails_hard_without_curl_fallback(self, mock_urlopen):
        """F5: HTTPError must fail hard immediately without papering over via curl."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://innokafe.com/",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None
        )

        with self.assertRaises(RuntimeError) as ctx:
            edge_verification()

        self.assertIn("HTTP status: 500", str(ctx.exception))

    @patch('sync_innokafe_to_pods.run_cmd')
    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_transport_error_falls_back_to_curl_argv(self, mock_urlopen, mock_run_cmd):
        """F3 & F4 & FAIL-1: Transport failure retries via curl argv list with --fail, --max-redirs 0 and exact 200 check."""
        import ssl
        mock_urlopen.side_effect = ssl.SSLError("SNI handshake failure")
        mock_run_cmd.return_value = MagicMock(returncode=0, stdout="<html>InnoKafe InnoRia</html>\n200", stderr="")

        edge_verification()

        # Verify run_cmd was called with an argv list (shell=False), not a shell pipeline
        self.assertTrue(mock_run_cmd.called)
        called_cmd = mock_run_cmd.call_args[0][0]
        self.assertIsInstance(called_cmd, list, "run_cmd must receive an argv list, not a shell string")
        self.assertEqual(called_cmd[0], "curl")
        self.assertIn("--fail", called_cmd)
        self.assertIn("--max-redirs", called_cmd)
        self.assertIn("0", called_cmd)
        self.assertIn("--proto", called_cmd)
        self.assertIn("=https", called_cmd)
        self.assertIn("\n%{http_code}", called_cmd)

    @patch('sync_innokafe_to_pods.run_cmd')
    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_curl_fallback_non_200_fails_hard(self, mock_urlopen, mock_run_cmd):
        """FAIL-1: Curl fallback returning non-200 or error must fail hard (CWE-345 / CWE-601)."""
        import ssl
        mock_urlopen.side_effect = ssl.SSLError("SNI failure")
        mock_run_cmd.return_value = MagicMock(returncode=22, stdout="<html>InnoKafe Server Error</html>\n500", stderr="error 500")

        with self.assertRaises(RuntimeError) as ctx:
            edge_verification()
        self.assertIn("curl exit=22", str(ctx.exception))

    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_build_marker_mismatch_fails_integrity_check(self, mock_urlopen):
        """F6: When EDGE_BUILD_MARKER is set, 200 without marker must fail (CWE-345)."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"<html>Defaced or Stale Cache Page</html>"
        mock_resp.headers = {}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict(os.environ, {"EDGE_BUILD_MARKER": "sha256-correct-marker"}):
            with self.assertRaises(RuntimeError) as ctx:
                edge_verification()

            self.assertIn("build marker not found", str(ctx.exception))

    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_build_marker_match_passes_integrity_check(self, mock_urlopen):
        """F6: When EDGE_BUILD_MARKER matches response body, verification succeeds."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"<html><meta name='build-marker' content='sha256-correct-marker'/></html>"
        mock_resp.headers = {}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict(os.environ, {"EDGE_BUILD_MARKER": "sha256-correct-marker"}):
            # Should not raise
            edge_verification()

    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_build_marker_hmac_header_match(self, mock_urlopen):
        """#5: When X-Edge-Build header matches EDGE_BUILD_MARKER via HMAC, verification succeeds."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"<html>Opaque SPA HTML without inline marker</html>"
        mock_resp.headers = {"X-Edge-Build": "sig-release-2026-xyz"}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict(os.environ, {"EDGE_BUILD_MARKER": "sig-release-2026-xyz"}):
            edge_verification()

    def test_empty_pods_guard_raises_cwe20(self):
        """#6: Empty pods list raises RuntimeError instead of IndexError."""
        from sync_innokafe_to_pods import prewarm_assets
        with self.assertRaises(RuntimeError) as ctx:
            prewarm_assets([])
        self.assertIn("Zero active pods resolved", str(ctx.exception))

    def test_require_secret_raises_on_missing_env(self):
        """CWE-259: _require_secret must raise SystemExit if secrets are missing."""
        from sync_innokafe_views_db import _require_secret
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                _require_secret(["TEST_NON_EXISTENT_KEY"])
            self.assertIn("Missing required secret environment variable", str(ctx.exception))

    def test_require_secret_returns_valid_value(self):
        """CWE-259: _require_secret returns secret from environment without leaking."""
        from sync_innokafe_views_db import _require_secret
        with patch.dict(os.environ, {"SECRET_KEY_A": "my-secret-token"}):
            val = _require_secret(["NON_EXISTENT", "SECRET_KEY_A"])
            self.assertEqual(val, "my-secret-token")

    @patch('sync_innokafe_to_pods.urllib.request.urlopen')
    def test_default_probe_rejects_page_missing_brand_provenance(self, mock_urlopen):
        """CWE-345: When no EDGE_BUILD_MARKER is set, edge probe must reject responses without InnoKafe brand provenance."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"<html>Welcome to Nginx generic 200 page</html>"
        mock_resp.headers = {}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                edge_verification()
            self.assertIn("missing application provenance marker", str(ctx.exception))

    def test_append_deploy_audit_record_hash_chain(self):
        """Audit Ledger: append_deploy_audit_record enforces rolling SHA-256 hash-chain integrity."""
        import tempfile
        import json
        import hashlib
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger):
                # First append
                h1 = append_deploy_audit_record(["pod-a", "pod-b"], "success", 12.34)
                self.assertEqual(len(h1), 64)
                self.assertTrue(all(c in "0123456789abcdef" for c in h1))

                # Verify first record contents
                with open(temp_ledger, "r", encoding="utf-8") as f:
                    lines = [json.loads(line) for line in f if line.strip()]
                self.assertEqual(len(lines), 1)
                rec1 = lines[0]
                self.assertEqual(rec1["prev_hash"], "0" * 64)
                self.assertEqual(rec1["record_hash"], h1)
                self.assertEqual(rec1["pods"], ["pod-a", "pod-b"])
                self.assertEqual(rec1["status"], "success")

                # Verify cryptographic hash of rec1
                rec1_copy = {k: v for k, v in rec1.items() if k != "record_hash"}
                ser1 = json.dumps(rec1_copy, sort_keys=True)
                expected_h1 = hashlib.sha256(("0" * 64 + ser1).encode("utf-8")).hexdigest()
                self.assertEqual(h1, expected_h1)

                # Second append
                h2 = append_deploy_audit_record(["pod-a", "pod-b", "pod-c"], "success", 18.5)
                self.assertEqual(len(h2), 64)
                self.assertNotEqual(h1, h2)

                # Verify second record contents and prev_hash chaining
                with open(temp_ledger, "r", encoding="utf-8") as f:
                    lines = [json.loads(line) for line in f if line.strip()]
                self.assertEqual(len(lines), 2)
                rec2 = lines[1]
                self.assertEqual(rec2["prev_hash"], h1)
                self.assertEqual(rec2["record_hash"], h2)

                # Verify cryptographic hash of rec2
                rec2_copy = {k: v for k, v in rec2.items() if k != "record_hash"}
                ser2 = json.dumps(rec2_copy, sort_keys=True)
                expected_h2 = hashlib.sha256((h1 + ser2).encode("utf-8")).hexdigest()
                self.assertEqual(h2, expected_h2)


if __name__ == '__main__':
    unittest.main()

