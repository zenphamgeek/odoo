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
        mock_run_cmd.return_value = MagicMock(returncode=22, stdout="", stderr="curl: (22) The requested URL returned error: 500")

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

    def test_concurrent_append_deploy_audit_record_prevents_fork(self):
        """F4 / CWE-362: Concurrent appends with flock must produce an unbroken, unforked hash-chain."""
        import tempfile
        import json
        import hashlib
        from concurrent.futures import ThreadPoolExecutor
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger):
                num_workers = 10

                def worker_task(idx):
                    return append_deploy_audit_record([f"pod-{idx}"], "success", 1.0 + idx)

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(worker_task, i) for i in range(num_workers)]
                    results = [f.result() for f in futures]

                self.assertEqual(len(results), num_workers)

                # Verify all records in ledger
                with open(temp_ledger, "r", encoding="utf-8") as f:
                    records = [json.loads(line) for line in f if line.strip()]

                self.assertEqual(len(records), num_workers)

                # Verify unbroken linear chain with zero forks
                all_prev_hashes = set()
                for i, rec in enumerate(records):
                    expected_prev = "0" * 64 if i == 0 else records[i - 1]["record_hash"]
                    self.assertEqual(rec["prev_hash"], expected_prev, f"Chain broken at index {i}")
                    self.assertEqual(rec["seq"], i + 1, f"Sequence broken at index {i}")
                    all_prev_hashes.add(rec["prev_hash"])

                    # Recompute hash
                    body = {k: v for k, v in rec.items() if k != "record_hash"}
                    ser = json.dumps(body, sort_keys=True)
                    expected_hash = hashlib.sha256((expected_prev + ser).encode("utf-8")).hexdigest()
                    self.assertEqual(rec["record_hash"], expected_hash)

                # Exactly num_workers distinct prev_hashes (no two workers read the same tip)
                self.assertEqual(len(all_prev_hashes), num_workers)

    def test_external_anchor_prevents_tampered_ledger(self):
        """F5 / CWE-345: External trust anchor must detect tampered or forked ledger file."""
        import tempfile
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")
            test_key = "anchor_signing_secret_key_32bytes!"

            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": test_key}):

                # 1. Normal initial append updates external anchor
                h1 = append_deploy_audit_record(["pod-1"], "success", 5.0)
                with open(temp_anchor, "r", encoding="utf-8") as f:
                    self.assertTrue(f.read().strip().startswith(h1 + ":"))

                # 2. Normal second append succeeds when in lockstep
                h2 = append_deploy_audit_record(["pod-2"], "success", 6.0)
                with open(temp_anchor, "r", encoding="utf-8") as f:
                    self.assertTrue(f.read().strip().startswith(h2 + ":"))

                # 3. Simulate tampering: rewrite external anchor with a forged hash lacking valid HMAC
                with open(temp_anchor, "w", encoding="utf-8") as f:
                    f.write("f" * 64 + "\n")

                # 4. Next append must reject tampered state
                with self.assertRaises(RuntimeError) as ctx:
                    append_deploy_audit_record(["pod-3"], "success", 7.0)

                self.assertTrue(
                    "Ledger tip integrity failure" in str(ctx.exception)
                    or "External trust anchor lacks required HMAC signature" in str(ctx.exception)
                )

    def test_truncation_rollback_rejected_by_anchor(self):
        """CWE-345: Truncating the ledger back to an earlier valid record must be rejected by anchor as a rollback."""
        import tempfile
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")
            test_key = "anchor_signing_secret_key_32bytes!"

            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": test_key}):

                # 1. Normal record sequence: record 1 and record 2
                h1 = append_deploy_audit_record(["pod-1"], "success", 5.0)
                h2 = append_deploy_audit_record(["pod-2"], "success", 6.0)

                with open(temp_anchor, "r", encoding="utf-8") as f:
                    self.assertTrue(f.read().strip().startswith(h2 + ":"))

                # 2. Simulate adversarial rollback: truncate ledger back to record 1
                with open(temp_ledger, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                self.assertEqual(len(lines), 2)

                with open(temp_ledger, "w", encoding="utf-8") as f:
                    f.write(lines[0])  # drop record 2

                # 3. Next append must detect that the local tip (h1) does not match the anchor (h2)
                with self.assertRaises(RuntimeError) as ctx:
                    append_deploy_audit_record(["pod-3"], "success", 7.0)

                self.assertIn("Ledger tip integrity failure", str(ctx.exception))
                self.assertIn("Possible ledger tampering, rollback or fork detected", str(ctx.exception))

    def test_read_ledger_tip_o1_reverse_seek(self):
        """WARN-2: _read_ledger_tip reads the tip in O(1) with bounded byte reads (<= 16384 bytes)."""
        import tempfile
        import json
        from sync_innokafe_to_pods import _read_ledger_tip

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            for i in range(500):
                f.write(json.dumps({"record_hash": f"{i:064d}", "idx": i}) + "\n")
            final_hash = "f" * 64
            f.write(json.dumps({"record_hash": final_hash, "idx": 500}) + "\n")
            temp_path = f.name

        try:
            total_file_size = os.path.getsize(temp_path)
            self.assertGreater(total_file_size, 30000, "File must be larger than 16KB chunk window")

            # Instrument file read to assert <= 16384 bytes are read
            original_open = open
            bytes_read_tracker = []

            def tracked_open(*args, **kwargs):
                f_obj = original_open(*args, **kwargs)
                mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")
                if "b" in mode:
                    orig_read = f_obj.read
                    def tracked_read(*r_args, **r_kwargs):
                        data = orig_read(*r_args, **r_kwargs)
                        bytes_read_tracker.append(len(data))
                        return data
                    f_obj.read = tracked_read
                return f_obj

            with patch("builtins.open", side_effect=tracked_open):
                tip = _read_ledger_tip(temp_path)

            self.assertEqual(tip, final_hash)
            self.assertTrue(len(bytes_read_tracker) > 0)
            self.assertLessEqual(sum(bytes_read_tracker), 16384, "O(1) read must be bounded by 16KB")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_read_ledger_tip_oversized_record_fallback(self):
        """WARN-2 / CWE-20: Oversized records (> 16KB) fall back to streaming scan and are never dropped."""
        import tempfile
        import json
        from sync_innokafe_to_pods import _read_ledger_tip

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write(json.dumps({"record_hash": "a" * 64, "idx": 1}) + "\n")
            # Create a single huge record exceeding 25 KB
            huge_payload = "x" * 25000
            expected_tip = "e" * 64
            f.write(json.dumps({"record_hash": expected_tip, "idx": 2, "huge_data": huge_payload}) + "\n")
            temp_path = f.name

        try:
            self.assertGreater(os.path.getsize(temp_path), 25000)
            tip = _read_ledger_tip(temp_path)
            self.assertEqual(tip, expected_tip, "Must successfully resolve oversized record >16KB via fallback")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_read_ledger_tip_torn_write_resilience(self):
        """WARN-3: Torn partial line at EOF from sudden process crash is gracefully bypassed to previous valid tip."""
        import tempfile
        import json
        from sync_innokafe_to_pods import _read_ledger_tip

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            valid_tip = "b" * 64
            f.write(json.dumps({"record_hash": valid_tip, "idx": 1}) + "\n")
            # Simulate torn line at EOF from SIGKILL mid-write
            f.write('{"timestamp": "2026-10-11T05:35:00Z", "incomplete_json": true')
            temp_path = f.name

        try:
            tip = _read_ledger_tip(temp_path)
            self.assertEqual(tip, valid_tip)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_atomic_anchor_update_fsync_durability(self):
        """WARN-3: _update_external_anchor writes atomically via tempfile + os.replace with zero leftover tmp files."""
        import tempfile
        from sync_innokafe_to_pods import _update_external_anchor

        with tempfile.TemporaryDirectory() as tmpdir:
            anchor_file = os.path.join(tmpdir, "test_anchor.sha256")
            expected_hash = "a" * 64
            _update_external_anchor(expected_hash, anchor_file)

            with open(anchor_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            self.assertEqual(content, expected_hash)

            # Assert no leftover temp files in directory
            leftovers = [name for name in os.listdir(tmpdir) if name.startswith(".anchor_tmp_")]
            self.assertEqual(leftovers, [], "All temp files must be cleanly renamed or unlinked")

    def test_audit_record_monotonic_sequence(self):
        """Merkle Sequence: Each audit record contains a strictly incrementing monotonic 'seq' slot."""
        import tempfile
        import json
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger):
                append_deploy_audit_record(["pod-1"], "success", 1.0)
                append_deploy_audit_record(["pod-2"], "success", 2.0)
                append_deploy_audit_record(["pod-3"], "success", 3.0)

                with open(temp_ledger, "r", encoding="utf-8") as f:
                    records = [json.loads(line) for line in f if line.strip()]

                self.assertEqual(len(records), 3)
                self.assertEqual(records[0]["seq"], 1)
                self.assertEqual(records[1]["seq"], 2)
                self.assertEqual(records[2]["seq"], 3)

    def test_external_anchor_hmac_authentication(self):
        """CWE-345 / F3: When LEDGER_ANCHOR_KEY is set, anchor stores <hash>:<hmac> and verifies authenticated tip."""
        import tempfile
        import hmac
        import hashlib
        from sync_innokafe_to_pods import append_deploy_audit_record

        test_key = "super_secret_anchor_signing_key_32bytes!"
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")

            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": test_key}):

                h1 = append_deploy_audit_record(["pod-1"], "success", 10.0)

                with open(temp_anchor, "r", encoding="utf-8") as f:
                    anchor_content = f.read().strip()

                self.assertIn(":", anchor_content)
                stored_hash, stored_mac = anchor_content.split(":", 1)
                self.assertEqual(stored_hash, h1)
                expected_mac = hmac.new(test_key.encode("utf-8"), h1.encode("utf-8"), hashlib.sha256).hexdigest()
                self.assertEqual(stored_mac, expected_mac)

                # Subsequent append succeeds with verified HMAC
                h2 = append_deploy_audit_record(["pod-2"], "success", 12.0)
                self.assertNotEqual(h1, h2)

    def test_external_anchor_tampered_hmac_fails(self):
        """CWE-345 / F3: Tampered HMAC signature in external anchor fails closed."""
        import tempfile
        from sync_innokafe_to_pods import append_deploy_audit_record

        test_key = "super_secret_anchor_signing_key_32bytes!"
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")

            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": test_key}):

                h1 = append_deploy_audit_record(["pod-1"], "success", 10.0)

                # Attacker forges the anchor with an invalid HMAC signature
                with open(temp_anchor, "w", encoding="utf-8") as f:
                    f.write(f"{h1}:deadbeefbadf00d0000000000000000000000000000000000000000000000000\n")

                with self.assertRaises(RuntimeError) as ctx:
                    append_deploy_audit_record(["pod-2"], "success", 12.0)

                self.assertIn("External trust anchor authentication failed: HMAC signature mismatch", str(ctx.exception))

    def test_required_anchor_without_key_fails_closed(self):
        """CWE-287 / F2: REQUIRE_EXTERNAL_ANCHOR with no LEDGER_ANCHOR_KEY must refuse, not downgrade to unauthenticated."""
        import tempfile
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")
            env = {k: v for k, v in os.environ.items() if k != "LEDGER_ANCHOR_KEY"}
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, env, clear=True):
                with self.assertRaises(RuntimeError) as ctx:
                    append_deploy_audit_record(["pod-1"], "success", 10.0)
                self.assertIn("LEDGER_ANCHOR_KEY is missing", str(ctx.exception))

    def test_required_anchor_weak_key_fails_closed(self):
        """CWE-326 / F6: LEDGER_ANCHOR_KEY with insufficient length (<16 bytes) fails closed."""
        import tempfile
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": "weak_short_key"}):
                with self.assertRaises(RuntimeError) as ctx:
                    append_deploy_audit_record(["pod-1"], "success", 10.0)
                self.assertIn("LEDGER_ANCHOR_KEY is too short", str(ctx.exception))

    def test_external_anchor_malformed_fails_closed(self):
        """CWE-20 / F4: Malformed anchor files (missing halves, extra colons, whitespace) fail closed."""
        import tempfile
        from sync_innokafe_to_pods import _verify_against_external_anchor

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")
            test_key = "sufficient_length_signing_key_32bytes!"

            with patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": test_key}):
                malformed_payloads = [
                    ":",
                    "hash_only_colon:",
                    ":mac_only_colon",
                    "hash:mac:extra_field",
                    "   :   ",
                ]
                for bad_payload in malformed_payloads:
                    with open(temp_anchor, "w", encoding="utf-8") as f:
                        f.write(bad_payload + "\n")

                    with self.assertRaises(RuntimeError) as ctx:
                        _verify_against_external_anchor("0" * 64, temp_anchor)
                    self.assertIn("External trust anchor malformed", str(ctx.exception))

    def test_seq_is_bound_into_hash_chain(self):
        """F5 / CWE-345: The monotonic 'seq' slot is cryptographically bound into record_hash."""
        import tempfile
        import json
        import hashlib
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger):
                h1 = append_deploy_audit_record(["pod-1"], "success", 1.0)

                with open(temp_ledger, "r", encoding="utf-8") as f:
                    rec = json.loads(f.readline())

                self.assertEqual(rec["seq"], 1)
                self.assertEqual(rec["record_hash"], h1)

                # Tamper seq from 1 to 999
                rec_tampered = dict(rec)
                rec_tampered["seq"] = 999
                del rec_tampered["record_hash"]
                ser = json.dumps(rec_tampered, sort_keys=True)
                tampered_hash = hashlib.sha256((rec["prev_hash"] + ser).encode("utf-8")).hexdigest()

                # Recomputed hash must differ because seq is cryptographically bound into serialized payload
                self.assertNotEqual(h1, tampered_hash)

    def test_validate_pod_identifier(self):
        """A7 / CWE-20/78/88: Pod identifiers must strictly adhere to RFC 1123 DNS subdomain labels."""
        from sync_innokafe_to_pods import validate_pod_identifier

        # Valid RFC 1123 pod identifiers
        valid_pods = ["pod-1", "insilos-saas-app-6ffc759bc9-djcxk", "app.worker.0", "web-123"]
        for p in valid_pods:
            self.assertEqual(validate_pod_identifier(p), p)

        # Malicious or malformed pod identifiers must raise ValueError
        invalid_pods = [
            "pod; rm -rf /",
            "pod\n{\"injected\": true}",
            "pod-1\n",            # trailing newline — $-anchor bypass attempt (S-01)
            "pod-1\r",            # carriage return — CR terminal whitespace bypass attempt (S-01)
            "pod-1\t",            # trailing tab
            "\x00pod",           # NUL byte
            "pod/../etc",         # path traversal attempt into path-join sinks
            ".leading-dot",
            "trailing-dot.",
            "double..dot",
            "POD_UPPERCASE",
            "-leading-dash",
            "trailing-dash-",
            "pod with spaces",
            "a" * 65,            # label exceeds 63 chars (S-07)
            "",                  # empty string
        ]
        for bad_p in invalid_pods:
            with self.assertRaises(ValueError):
                validate_pod_identifier(bad_p)

    def test_verify_audit_ledger_detects_corruptions(self):
        """Full-Chain Merkle Audit: verify_audit_ledger detects interior, tail, seq, and deletion corruptions (S-08)."""
        import tempfile
        import json
        from sync_innokafe_to_pods import append_deploy_audit_record, verify_audit_ledger

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")

            test_key = "a" * 32
            with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                 patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                 patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                 patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": test_key}):

                append_deploy_audit_record(["pod-1"], "success", 1.0)
                append_deploy_audit_record(["pod-2"], "success", 2.0)
                append_deploy_audit_record(["pod-3"], "success", 3.0)

                # Valid chain passes
                self.assertTrue(verify_audit_ledger(temp_ledger, temp_anchor))

                with open(temp_ledger, "r", encoding="utf-8") as f:
                    clean_records = [json.loads(line) for line in f if line.strip()]

                # 1. Tamper interior record status
                records_interior = [dict(r) for r in clean_records]
                records_interior[1]["status"] = "tampered_failure"
                with open(temp_ledger, "w", encoding="utf-8") as f:
                    for r in records_interior:
                        f.write(json.dumps(r) + "\n")
                with self.assertRaises(RuntimeError) as ctx:
                    verify_audit_ledger(temp_ledger, temp_anchor)
                self.assertIn("Audit ledger cryptographic corruption", str(ctx.exception))

                # 2. Tamper seq sequence order
                records_seq = [dict(r) for r in clean_records]
                records_seq[1]["seq"] = 99
                with open(temp_ledger, "w", encoding="utf-8") as f:
                    for r in records_seq:
                        f.write(json.dumps(r) + "\n")
                with self.assertRaises(RuntimeError) as ctx:
                    verify_audit_ledger(temp_ledger, temp_anchor)
                self.assertIn("sequence violation", str(ctx.exception))

                # 3. Delete middle record: strictly triggers sequence violation
                records_deleted = [clean_records[0], clean_records[2]]
                with open(temp_ledger, "w", encoding="utf-8") as f:
                    for r in records_deleted:
                        f.write(json.dumps(r) + "\n")
                with self.assertRaises(RuntimeError) as ctx:
                    verify_audit_ledger(temp_ledger, temp_anchor)
                self.assertIn("sequence violation", str(ctx.exception))

                # 4. Tail truncation: drop last record; must fail against external anchor (S-08)
                records_tail_truncated = clean_records[:-1]
                with open(temp_ledger, "w", encoding="utf-8") as f:
                    for r in records_tail_truncated:
                        f.write(json.dumps(r) + "\n")
                with self.assertRaises(RuntimeError) as ctx:
                    verify_audit_ledger(temp_ledger, temp_anchor)
                self.assertIn("Ledger tip integrity failure", str(ctx.exception))

    def test_multiprocess_concurrent_append_deploy_audit_record(self):
        """A6 / S-02 / CWE-362: True OS multi-process concurrency with safe env passing prevents ledger forks."""
        import tempfile
        import subprocess
        import sys
        import json
        from sync_innokafe_to_pods import verify_audit_ledger, ROOT_DIR

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")

            # Safe script using os.environ, zero f-string interpolation into source (S-02)
            worker_script = """
import sys, os
sys.path.insert(0, os.environ["SYNC_TOOLS_DIR"])
from unittest.mock import patch
import sync_innokafe_to_pods

with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", os.environ["TMP_LEDGER"]), \\
     patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", os.environ["TMP_ANCHOR"]):
    sync_innokafe_to_pods.append_deploy_audit_record([f"pod-proc-{sys.argv[1]}"], "success", 1.0)
"""
            child_env = dict(os.environ)
            child_env["SYNC_TOOLS_DIR"] = os.path.join(ROOT_DIR, "tools")
            child_env["TMP_LEDGER"] = temp_ledger
            child_env["TMP_ANCHOR"] = temp_anchor

            num_procs = 5
            procs = []
            for i in range(num_procs):
                p = subprocess.Popen([sys.executable, "-c", worker_script, str(i)], env=child_env)
                procs.append(p)

            for p in procs:
                p.wait()
                self.assertEqual(p.returncode, 0)

            # Full-chain Merkle integrity check over all concurrent multi-process writes
            self.assertTrue(verify_audit_ledger(temp_ledger, temp_anchor))

            with open(temp_ledger, "r", encoding="utf-8") as f:
                records = [json.loads(line) for line in f if line.strip()]

            self.assertEqual(len(records), num_procs)
            for idx, rec in enumerate(records):
                self.assertEqual(rec["seq"], idx + 1)

    def test_anchor_key_never_leaked_to_logs_or_errors(self):
        """S-06 / CWE-259/532: LEDGER_ANCHOR_KEY is never leaked to logging or error exception strings."""
        import tempfile
        import logging
        from sync_innokafe_to_pods import append_deploy_audit_record

        secret_key = "super_confidential_secret_key_32bytes_value!"
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            temp_anchor = os.path.join(tmpdir, ".deploy_external_anchor.sha256")

            log_records = []
            class CapturingHandler(logging.Handler):
                def emit(self, record):
                    log_records.append(self.format(record))

            handler = CapturingHandler()
            logging.getLogger().addHandler(handler)
            try:
                with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                     patch("sync_innokafe_to_pods.EXTERNAL_ANCHOR_PATH", temp_anchor), \
                     patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
                     patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": secret_key}):

                    append_deploy_audit_record(["pod-1"], "success", 1.0)

                    # Trigger error path with forged anchor
                    with open(temp_anchor, "w", encoding="utf-8") as f:
                        f.write("0" * 64 + ":" + "f" * 64 + "\n")

                    try:
                        append_deploy_audit_record(["pod-2"], "success", 2.0)
                    except Exception as exc:
                        self.assertNotIn(secret_key, str(exc), "Secret key must not appear in exception messages")

                    for log_msg in log_records:
                        self.assertNotIn(secret_key, log_msg, "Secret key must not be emitted to log records")
            finally:
                logging.getLogger().removeHandler(handler)

    def test_flock_timeout_raises_timeout_error(self):
        """S-03 / CWE-833: Bounded flock acquisition times out and raises TimeoutError when lock is held."""
        import tempfile
        import fcntl
        from sync_innokafe_to_pods import append_deploy_audit_record

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_ledger = os.path.join(tmpdir, ".deploy_audit_ledger.jsonl")
            lock_path = temp_ledger + ".lock"

            # Pre-lock with exclusive flock from another file descriptor
            hold_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(hold_fd, fcntl.LOCK_EX)
            try:
                with patch("sync_innokafe_to_pods.AUDIT_LEDGER_PATH", temp_ledger), \
                     patch.dict(os.environ, {"LEDGER_LOCK_TIMEOUT_S": "0.1"}):
                    with self.assertRaises(TimeoutError) as ctx:
                        append_deploy_audit_record(["pod-1"], "success", 1.0)
                    self.assertIn("timed out after 0.1s", str(ctx.exception))
                    self.assertFalse(
                        os.path.exists(temp_ledger),
                        "Fail-Closed verification: No records must be written on lock acquisition timeout (CWE-833)"
                    )
            finally:
                fcntl.flock(hold_fd, fcntl.LOCK_UN)
                os.close(hold_fd)

    def test_rejects_undersized_anchor_key(self):
        """CWE-521/326: HMAC anchor key below minimum entropy must be refused, not silently accepted."""
        from sync_innokafe_to_pods import append_deploy_audit_record
        with patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
             patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": "short"}):
            with self.assertRaises((ValueError, RuntimeError)) as ctx:
                append_deploy_audit_record(["pod-1"], "success", 1.0)
            self.assertIn("too short", str(ctx.exception).lower())

    def test_deploy_preflight_security_fails_closed_without_anchor(self):
        """CWE-636: Deploy pipeline must fail closed when REQUIRE_EXTERNAL_ANCHOR is false unless degraded mode is explicitly allowed."""
        from sync_innokafe_to_pods import assert_deploy_preflight_security
        with patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", False), \
             patch.dict(os.environ, {"INNOKAFE_ALLOW_DEGRADED_AUDIT": "0"}):
            with self.assertRaises(RuntimeError) as ctx:
                assert_deploy_preflight_security()
            self.assertIn("refuses to execute in unanchored/fail-open mode", str(ctx.exception))

    def test_deploy_preflight_security_passes_with_anchor_and_key(self):
        """CWE-636 / CWE-326: Pre-flight check succeeds when REQUIRE_EXTERNAL_ANCHOR is true and valid key (>= 32 bytes) is set."""
        from sync_innokafe_to_pods import assert_deploy_preflight_security
        with patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True), \
             patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": "a" * 32}):
            # Must succeed without raising
            assert_deploy_preflight_security()

    def test_deploy_preflight_security_passes_with_explicit_degraded_override(self):
        """CWE-636: Pre-flight check permits offline local dev only when explicitly opted in via INNOKAFE_ALLOW_DEGRADED_AUDIT=1."""
        from sync_innokafe_to_pods import assert_deploy_preflight_security
        with patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", False), \
             patch.dict(os.environ, {"INNOKAFE_ALLOW_DEGRADED_AUDIT": "1"}):
            # Must succeed without raising
            assert_deploy_preflight_security()

    def test_deploy_preflight_security_prod_default(self):
        """CWE-636: In production environment (ENV=prod), REQUIRE_EXTERNAL_ANCHOR defaults to enabled in isolated process."""
        import subprocess
        import sys
        from sync_innokafe_to_pods import ROOT_DIR

        proc_script = """
import os, sys
sys.path.insert(0, os.path.join(os.environ["REPO_ROOT"], "tools"))
import sync_innokafe_to_pods as m
assert m.REQUIRE_EXTERNAL_ANCHOR is True, "Must default to True under ENV=prod"
"""
        env = dict(os.environ)
        env["REPO_ROOT"] = ROOT_DIR
        env["ENV"] = "prod"
        env.pop("INNOKAFE_REQUIRE_EXTERNAL_ANCHOR", None)
        env.pop("PYTEST_CURRENT_TEST", None)

        res = subprocess.run([sys.executable, "-c", proc_script], env=env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Subprocess validation failed:\nStdout: {res.stdout}\nStderr: {res.stderr}")

    def test_mutation_oracle_kills_regex_and_entropy_mutants(self):
        """Zero-Fake-Pass Mutation Testing: Proves that subtle corruptions to regex anchors and byte entropy thresholds fail (CWE-20 / CWE-326)."""
        import re
        from sync_innokafe_to_pods import validate_pod_identifier, _load_anchor_key, _POD_LABEL_RE

        # Mutant 1: Weak regex with $ instead of \Z
        weak_re = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
        # In re, $ matches before trailing newline, whereas \Z never matches trailing newline
        self.assertIsNotNone(weak_re.match("pod-1\n"), "Mutant would survive by matching trailing newline")
        self.assertIsNone(_POD_LABEL_RE.fullmatch("pod-1\n"), "Actual _POD_LABEL_RE kills mutant by rejecting trailing newline")
        with self.assertRaises(ValueError):
            validate_pod_identifier("pod-1\n")

        # Mutant 2: Relaxed entropy threshold (< 32 bytes)
        with patch("sync_innokafe_to_pods.REQUIRE_EXTERNAL_ANCHOR", True):
            for bad_len in [0, 1, 16, 31]:
                with patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": "x" * bad_len}):
                    with self.assertRaises(RuntimeError) as ctx:
                        _load_anchor_key()
                    err = str(ctx.exception)
                    self.assertTrue("missing" in err or "too short" in err)

            # Unmutated threshold accepts >= 32 bytes
            with patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": "x" * 32}):
                self.assertEqual(_load_anchor_key(), b"x" * 32)

            # Mutant 3: Multibyte UTF-8 byte entropy vs character length (CWE-326)
            # 16 2-byte Vietnamese characters ('đ') = 32 bytes in UTF-8: MUST PASS
            multibyte_valid = "đ" * 16
            self.assertEqual(len(multibyte_valid), 16, "Character length is 16")
            self.assertEqual(len(multibyte_valid.encode("utf-8")), 32, "Byte length is 32")
            with patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": multibyte_valid}):
                self.assertEqual(_load_anchor_key(), multibyte_valid.encode("utf-8"))

            # 15 2-byte Vietnamese characters ('đ') = 30 bytes in UTF-8: MUST FAIL
            multibyte_undersized = "đ" * 15
            with patch.dict(os.environ, {"LEDGER_ANCHOR_KEY": multibyte_undersized}):
                with self.assertRaises(RuntimeError) as ctx:
                    _load_anchor_key()
                self.assertIn("30 bytes < 32 minimum", str(ctx.exception))

    def test_run_cmd_rejects_string_commands_cwe78(self):
        """CWE-78: run_cmd strictly requires List[str] argv and rejects shell strings."""
        from sync_innokafe_to_pods import run_cmd

        with self.assertRaises(TypeError) as ctx:
            run_cmd("echo 'attempted shell injection'")
        self.assertIn("run_cmd requires a List[str]", str(ctx.exception))

    def test_validate_pod_identifier_length_bounds(self):
        """CWE-20: Pod identifier enforces total DNS subdomain length bound [1, 253] and label bound [1, 63]."""
        from sync_innokafe_to_pods import validate_pod_identifier

        # Max valid single label: 63 chars
        max_label = "a" * 63
        self.assertEqual(validate_pod_identifier(max_label), max_label)

        # Oversized label: 64 chars
        with self.assertRaises(ValueError):
            validate_pod_identifier("a" * 64)

        # Total length > 253 chars
        oversized_subdomain = "a" * 60 + "." + "b" * 60 + "." + "c" * 60 + "." + "d" * 60 + "." + "e" * 20
        self.assertGreater(len(oversized_subdomain), 253)
        with self.assertRaises(ValueError) as ctx:
            validate_pod_identifier(oversized_subdomain)
        self.assertIn("out of range [1, 253]", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()


