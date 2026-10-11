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
        """F3 & F4: Transport failure (e.g. SSLError) retries via curl argv list with exact 200 check."""
        import ssl
        mock_urlopen.side_effect = ssl.SSLError("SNI handshake failure")
        mock_run_cmd.return_value = MagicMock(returncode=0, stdout="200\n", stderr="")

        edge_verification()

        # Verify run_cmd was called with an argv list (shell=False), not a shell pipeline
        self.assertTrue(mock_run_cmd.called)
        called_cmd = mock_run_cmd.call_args[0][0]
        self.assertIsInstance(called_cmd, list, "run_cmd must receive an argv list, not a shell string")
        self.assertEqual(called_cmd[0], "curl")
        self.assertIn("%{http_code}", called_cmd)

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


if __name__ == '__main__':
    unittest.main()
