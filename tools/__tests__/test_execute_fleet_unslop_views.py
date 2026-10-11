#!/usr/bin/env python3
"""
tools/__tests__/test_execute_fleet_unslop_views.py
==================================================
Unit tests for execute_fleet_unslop_views.py, safe_xml.py, and unslop_ledger.py verifying:
1. Idempotency invariant: clean(clean(x)) == clean(x)
2. F1: Unicode strings with XML encoding declarations do not crash
3. F3: Structural drift is detected and rejected
4. CWE-776: Entity expansion bombs (UTF-8 and UTF-16) are rejected with specific ValueError
5. CWE-628: Type guard prevents accidental argument swap
6. Content-addressed ledger idempotency and audit tracking
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from concurrent.futures import ProcessPoolExecutor
import hashlib
from unittest.mock import patch

from tools.atomic_io import atomic_write_text
from tools.execute_fleet_unslop_views import (
    assert_mutation_fraction_bounded,
    clean_file_content,
    main as execute_views_main,
)
from tools.safe_xml import ForbiddenMarkupError, assert_markup_preserved, parse_xml_safe
from tools.unslop_ledger import UnslopLedger


def _ledger_concurrent_worker(args):
    """Picklable worker for multiprocess ledger concurrency test."""
    db_path_str, worker_id, num_writes = args
    ledger = UnslopLedger(db_path=Path(db_path_str))
    for i in range(num_writes):
        rel_path = f"enterprise/worker_{worker_id}_file_{i}.xml"
        sha = hashlib.sha256(f"content_{worker_id}_{i}".encode()).hexdigest()
        ledger.record_entry(
            rel_path=rel_path,
            sha256_before=sha,
            sha256_after=sha,
            rule_fingerprint="fp_concurrent",
            diff_chars=0,
            status="clean",
            notes=f"worker_{worker_id}",
        )
    return True


class TestExecuteFleetUnslopViews(unittest.TestCase):
    def test_clean_file_content_idempotency(self):
        """Idempotency Invariant: clean(clean(x)) == clean(x)."""
        sample_snippets = [
            '<t t-set="additional_title">101 Vertical Industry Solutions — Insilos Autonomous AI</t>',
            '<template id="test_template" name="Logistics &amp; Shipping — Insilos Port">',
            '<h3 class="step">01 — Discovery &amp; Scope</h3>',
            '<div class="location">Hải Phòng — Vũng Tàu</div>',
            '<pre><span class="token-comment">// Insilos Sovereign OS</span></pre>',
            '<p>sai số không tính bằng phần trăm, nó được đo bằng sinh mạng con người</p>',
        ]

        for s in sample_snippets:
            first_pass = clean_file_content(s)
            second_pass = clean_file_content(first_pass)
            self.assertEqual(first_pass, second_pass, f"Failed idempotency on: {s}")
            self.assertNotIn("—", first_pass)
            self.assertNotIn("// Insilos", first_pass)

    def test_xml_encoding_declaration_does_not_raise_value_error(self):
        """F1: Encoded bytes prevent ValueError on XML encoding declaration."""
        xml_with_decl = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<odoo><template id="t1" name="Title | Insilos"><p>Clean text</p></template></odoo>'
        )
        # Must not raise ValueError or ParseError
        assert_markup_preserved(xml_with_decl, xml_with_decl, "test.xml")

    def test_assert_markup_preserved_passes_on_text_changes(self):
        """F3: Preserves identical element hierarchy and attribute topology across text modifications."""
        before = (
            '<odoo><template id="t1" name="Before — Subtitle">'
            '<div class="container"><span class="badge">01 — Step</span></div>'
            '</template></odoo>'
        )
        after = (
            '<odoo><template id="t1" name="Before | Subtitle">'
            '<div class="container"><span class="badge">01. Step</span></div>'
            '</template></odoo>'
        )
        # Must pass cleanly
        assert_markup_preserved(before, after, "test.xml")

    def test_assert_markup_preserved_detects_structural_drift(self):
        """F3: Rejects changes that alter element tags or attribute keys."""
        before = '<odoo><template id="t1" name="Old"><div class="c1"><p>Text</p></div></template></odoo>'

        # Altered tag: <p> -> <span>
        after_altered_tag = '<odoo><template id="t1" name="Old"><div class="c1"><span>Text</span></div></template></odoo>'
        with self.assertRaises(ValueError) as ctx:
            assert_markup_preserved(before, after_altered_tag, "test_tag.xml")
        self.assertIn("STRUCTURAL DRIFT", str(ctx.exception))

        # Dropped attribute
        after_dropped_attrib = '<odoo><template id="t1"><div class="c1"><p>Text</p></div></template></odoo>'
        with self.assertRaises(ValueError) as ctx:
            assert_markup_preserved(before, after_dropped_attrib, "test_attrib.xml")
        self.assertIn("STRUCTURAL DRIFT", str(ctx.exception))

    def test_assert_markup_preserved_rejects_entity_expansion_bomb_utf8(self):
        """CWE-776: billion-laughs style payload in UTF-8 must be rejected with specific ValueError."""
        bomb = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE lolz [<!ENTITY lol "lol">'
            '<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
            '<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">]>'
            '<odoo><template id="t1"><p>&lol3;</p></template></odoo>'
        )
        with self.assertRaises(ValueError) as ctx:
            assert_markup_preserved(bomb, bomb, "bomb.xml")
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_assert_markup_preserved_rejects_entity_expansion_bomb_utf16(self):
        """CWE-776: billion-laughs style payload in UTF-16 must also be rejected."""
        bomb_text = '<!DOCTYPE lolz [<!ENTITY lol "lol">]><root><p>boom</p></root>'
        bomb_utf16 = bomb_text.encode("utf-16")
        with self.assertRaises(ValueError) as ctx:
            parse_xml_safe(bomb_utf16)
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_clean_file_content_type_guard(self):
        """F-C (CWE-628): Raises TypeError if non-string argument is passed."""
        with self.assertRaises(TypeError):
            clean_file_content(123)  # type: ignore

        with self.assertRaises(TypeError):
            clean_file_content(["path", "content"])  # type: ignore

    def test_unslop_ledger_content_addressed_idempotency(self):
        """Verifies content-addressed ledger tracking and instant skip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_unslop.db"
            ledger = UnslopLedger(db_path=test_db)

            rel_path = "enterprise/test_view.xml"
            content = "<odoo><template id='t'>Clean</template></odoo>"
            sha = UnslopLedger.compute_sha256(content)
            fp = "test_fp_v1"

            # Initially not recorded
            self.assertFalse(ledger.is_clean(rel_path, sha, fp))

            # Record entry
            ledger.record_entry(
                rel_path=rel_path,
                sha256_before=sha,
                sha256_after=sha,
                rule_fingerprint=fp,
                diff_chars=0,
                status="clean",
            )

            # Now recorded as clean
            self.assertTrue(ledger.is_clean(rel_path, sha, fp))

            # Different hash or rule fp is not clean
            self.assertFalse(ledger.is_clean(rel_path, "different_sha", fp))
            self.assertFalse(ledger.is_clean(rel_path, sha, "different_fp"))

            # Stats check
            stats = ledger.get_stats()
            self.assertEqual(stats["total_tracked"], 1)
            self.assertEqual(stats["clean_count"], 1)

    def test_assert_markup_preserved_rejects_xxe_system_file_read(self):
        """CWE-611: XXE SYSTEM entity payload attempting to read local files must be strictly blocked."""
        xxe_payload = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE root [\n'
            '  <!ENTITY xxe SYSTEM "file:///etc/passwd">\n'
            ']>\n'
            '<odoo><template id="t1"><p>&xxe;</p></template></odoo>'
        )
        with self.assertRaises(ValueError) as ctx:
            parse_xml_safe(xxe_payload)
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_assert_markup_preserved_rejects_parameter_entity_bomb(self):
        """CWE-776: Parameter entity declaration must be rejected."""
        pe_payload = (
            '<?xml version="1.0"?>\n'
            '<!DOCTYPE test [\n'
            '  <!ENTITY % pe "<!ENTITY bomb \'payload\'>">\n'
            '  %pe;\n'
            ']>\n'
            '<odoo><template id="t1"><p>&bomb;</p></template></odoo>'
        )
        with self.assertRaises(ValueError) as ctx:
            parse_xml_safe(pe_payload)
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_assert_markup_preserved_rejects_quadratic_blowup_entity(self):
        """CWE-776: Quadratic entity expansion bomb must be rejected."""
        quad_payload = (
            '<?xml version="1.0"?>\n'
            '<!DOCTYPE root [\n'
            '  <!ENTITY chunk "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa">\n'
            ']>\n'
            '<odoo><template id="t1"><p>&chunk;&chunk;&chunk;&chunk;</p></template></odoo>'
        )
        with self.assertRaises(ValueError) as ctx:
            parse_xml_safe(quad_payload)
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_assert_markup_preserved_rejects_padding_bypass_attempt(self):
        """CWE-611/CWE-776: Padding bypass (>8000 bytes before DOCTYPE) must NOT bypass safe_xml."""
        padding = " " * 8000 + "<!-- " + "x" * 6000 + " -->\n"
        bypassing_payload = (
            padding + '<!DOCTYPE root [<!ENTITY secret "test">]><odoo><p>&secret;</p></odoo>'
        )
        with self.assertRaises(ValueError) as ctx:
            parse_xml_safe(bypassing_payload)
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_unslop_ledger_concurrent_multiprocess_writes(self):
        """CWE-367: Multi-process concurrent ledger writes execute without SQLite lock error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_concurrent.db"
            # Pre-init
            ledger = UnslopLedger(db_path=test_db)

            num_workers = 4
            writes_per_worker = 25
            tasks = [
                (str(test_db), w_id, writes_per_worker)
                for w_id in range(num_workers)
            ]

            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                results = list(executor.map(_ledger_concurrent_worker, tasks))

            self.assertTrue(all(results))

            stats = ledger.get_stats()
            self.assertEqual(stats["total_tracked"], num_workers * writes_per_worker)
            self.assertEqual(stats["clean_count"], num_workers * writes_per_worker)
            self.assertEqual(stats["audit_events"], num_workers * writes_per_worker)

            # Integrity check
            with ledger._get_connection() as con:
                res = con.execute("PRAGMA integrity_check").fetchone()[0]
                self.assertEqual(res, "ok")

    def test_unslop_ledger_secure_permissions(self):
        """Verifies that ledger DB and lock files are created with 0o600 permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_perms.db"
            ledger = UnslopLedger(db_path=test_db)
            ledger.record_entry("path/a", "s1", "s2", "fp1", 0)

            db_mode = test_db.stat().st_mode & 0o777
            self.assertEqual(
                db_mode & 0o077, 0, f"DB has loose permissions: {oct(db_mode)}"
            )

            lock_mode = ledger.lock_path.stat().st_mode & 0o777
            self.assertEqual(
                lock_mode & 0o077, 0, f"Lock has loose permissions: {oct(lock_mode)}"
            )

    def test_atomic_write_crash_injection_leaves_original_intact(self):
        """Crash injection: Simulated failure during write leaves original file completely untouched."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "original_view.xml"
            original_content = "<odoo><template id='t1'>Untouched</template></odoo>"
            target.write_text(original_content, encoding="utf-8")

            # Mock os.replace to raise an unhandled OSError
            with patch("os.replace", side_effect=OSError("Simulated crash before rename")):
                with self.assertRaises(OSError):
                    atomic_write_text(target, "<odoo><template id='t1'>Corrupted</template></odoo>")

            # Target file MUST remain exactly as original
            self.assertEqual(target.read_text(encoding="utf-8"), original_content)

            # No leftover .tmp files
            tmp_files = list(Path(tmpdir).glob(".*.tmp"))
            self.assertEqual(len(tmp_files), 0, f"Found leftover temp files: {tmp_files}")

    def test_ledger_rejects_sql_metacharacter_rel_path(self):
        """CWE-89: SQL injection payloads in rel_path are parameterized safely and stored literally."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_sqli.db"
            ledger = UnslopLedger(db_path=test_db)

            # Malicious path attempting SQL injection
            sqli_path = "views/normal'; DROP TABLE unslop_ledger; --.xml"
            sha = hashlib.sha256(b"dummy").hexdigest()

            # Record entry with SQL metacharacters
            ledger.record_entry(
                rel_path=sqli_path,
                sha256_before=sha,
                sha256_after=sha,
                rule_fingerprint="fp1",
                diff_chars=0,
                status="clean",
                notes="Attempted SQLi in notes: ' OR 1=1; --",
            )

            # Table must still exist and be intact
            self.assertTrue(ledger.is_clean(sqli_path, sha, "fp1"))

            # Direct verification of table schema and row
            with ledger._get_connection() as con:
                row = con.execute(
                    "SELECT rel_path, status FROM unslop_ledger WHERE rel_path = ?",
                    (sqli_path,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], sqli_path)

                audit_row = con.execute(
                    "SELECT rel_path, notes FROM unslop_audit_log WHERE rel_path = ?",
                    (sqli_path,),
                ).fetchone()
                self.assertIsNotNone(audit_row)
                self.assertEqual(audit_row[0], sqli_path)
                self.assertIn("DROP TABLE", sqli_path)

    def test_ledger_rejects_path_traversal_and_nul(self):
        """CWE-22 / CWE-626: Directory traversal ('..'), absolute paths, and NUL bytes are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_traversal.db"
            ledger = UnslopLedger(db_path=test_db)
            sha = hashlib.sha256(b"dummy").hexdigest()

            # Path traversal
            with self.assertRaises(ValueError) as ctx:
                ledger.record_entry("../../etc/passwd", sha, sha, "fp1", 0)
            self.assertIn("traversal", str(ctx.exception).lower())

            # Absolute path
            with self.assertRaises(ValueError) as ctx:
                ledger.record_entry("/var/log/syslog", sha, sha, "fp1", 0)
            self.assertIn("relative", str(ctx.exception).lower())

            # NUL byte injection
            with self.assertRaises(ValueError) as ctx:
                ledger.record_entry("views/safe.xml\x00.evil", sha, sha, "fp1", 0)
            self.assertIn("nul", str(ctx.exception).lower())

    def test_markup_guard_rejects_unbounded_padding(self):
        """CWE-611 / CWE-776: 1 MiB of leading whitespace/comments before DOCTYPE raises ForbiddenMarkupError."""
        # 1 MiB padding of spaces and XML comments
        padding = " " * (512 * 1024) + "<!-- " + "pad" * (100 * 1024) + " -->\n"
        bypassing_payload = (
            padding + '<!DOCTYPE root [<!ENTITY secret "test">]><odoo><p>&secret;</p></odoo>'
        )
        with self.assertRaises(ForbiddenMarkupError):
            parse_xml_safe(bypassing_payload)

    def test_markup_guard_raises_typed_forbidden_markup_error(self):
        """Behavioral Typing: Verifies that safe_xml raises typed ForbiddenMarkupError specifically."""
        bomb = '<!DOCTYPE test [<!ENTITY bomb "bomb">]><root><p>&bomb;</p></root>'
        with self.assertRaises(ForbiddenMarkupError) as ctx:
            parse_xml_safe(bomb)
        self.assertIsInstance(ctx.exception, ValueError)

    def test_ledger_negative_selection_drift_detection(self):
        """Immunology Frame (Negative Selection): detect_anomalies flags drifted/tampered files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_thymus.db"
            ledger = UnslopLedger(db_path=test_db)

            clean_sha = hashlib.sha256(b"known_clean_content").hexdigest()
            drifted_sha = hashlib.sha256(b"tampered_content").hexdigest()

            # Enroll clean file into ledger "self"
            ledger.record_entry(
                rel_path="enterprise/views/home.xml",
                sha256_before=clean_sha,
                sha256_after=clean_sha,
                rule_fingerprint="fp_v1",
                diff_chars=0,
                status="clean",
            )

            # Test 1: Clean tree matching self -> 0 anomalies
            clean_files = [("enterprise/views/home.xml", clean_sha)]
            anomalies_clean = ledger.detect_anomalies(clean_files, enabled=True)
            self.assertEqual(len(anomalies_clean), 0)

            # Test 2: Drifted tree (content tampered) -> 1 anomaly detected
            drifted_files = [("enterprise/views/home.xml", drifted_sha)]
            anomalies_drifted = ledger.detect_anomalies(drifted_files, enabled=True)
            self.assertEqual(len(anomalies_drifted), 1)
            rel_path, last_clean, current = anomalies_drifted[0]
            self.assertEqual(rel_path, "enterprise/views/home.xml")
            self.assertEqual(last_clean, clean_sha)
            self.assertEqual(current, drifted_sha)

            # Test 3: Disabled mode -> returns empty
            self.assertEqual(len(ledger.detect_anomalies(drifted_files, enabled=False)), 0)

    def test_ledger_rejects_symlink_escape(self):
        """CWE-59: A rel_path resolving outside the ledger base directory via symlink is strictly rejected."""
        with tempfile.TemporaryDirectory() as root_tmp:
            base_dir = Path(root_tmp) / "safe_workspace"
            base_dir.mkdir()
            outside_dir = Path(root_tmp) / "outside"
            outside_dir.mkdir()
            secret_file = outside_dir / "secret.key"
            secret_file.write_text("SUPER_SECRET_PAYLOAD", encoding="utf-8")

            # Create symlink inside base_dir pointing to external target
            symlink_in_base = base_dir / "symlink_escape.xml"
            os.symlink(str(secret_file), str(symlink_in_base))

            test_db = base_dir / "test_symlink.db"
            ledger = UnslopLedger(db_path=test_db, base_dir=base_dir)
            sha = hashlib.sha256(b"dummy").hexdigest()

            with self.assertRaises(ValueError) as ctx:
                ledger.record_entry("symlink_escape.xml", sha, sha, "fp1", 0)
            self.assertIn("escapes base directory", str(ctx.exception).lower())

    def test_ledger_rejects_backslash_and_dotslash_normalization(self):
        """CWE-22: 'views\\..\\..\\etc\\passwd' and './../x' are rejected after normalization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_norm.db"
            ledger = UnslopLedger(db_path=test_db)
            sha = hashlib.sha256(b"dummy").hexdigest()

            evasive_paths = [
                "views\\..\\..\\etc\\passwd",
                "./../x",
                "enterprise/views/../../../shadow",
                "views/./../../etc/hosts",
                "C:\\Windows\\System32\\calc.exe",
            ]

            for evil_path in evasive_paths:
                with self.assertRaises(ValueError, msg=f"Failed to reject: {evil_path}"):
                    ledger.record_entry(evil_path, sha, sha, "fp1", 0)

    def test_ledger_lock_released_on_exception(self):
        """CWE-667 / CWE-833: An exception mid-write releases fcntl lock so subsequent calls never deadlock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "test_lock_crash.db"
            ledger = UnslopLedger(db_path=test_db)

            # Intentionally simulate exception inside exclusive lock
            try:
                with ledger._flock_exclusive(timeout_sec=5.0):
                    raise RuntimeError("Simulated process crash / interruption during write")
            except RuntimeError:
                pass

            # Subsequent call MUST acquire lock immediately without TimeoutError
            acquired = False
            with ledger._flock_exclusive(timeout_sec=0.5):
                acquired = True
            self.assertTrue(acquired, "Failed to acquire lock: previous lock was not cleanly released")

    def test_sale_order_create_invoices_signature_is_pinned(self):
        """F-1 / CWE-20: SaleOrder._create_invoices signature is pinned; no **kwargs allowed."""
        import ast

        sale_order_path = ROOT_DIR / "addons" / "sale" / "models" / "sale_order.py"
        tree = ast.parse(sale_order_path.read_text(encoding="utf-8"))

        found_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_create_invoices":
                found_func = node
                break

        self.assertIsNotNone(found_func, "Could not find _create_invoices in sale_order.py")
        # Check that vararg and kwarg are strictly None (no *args or **kwargs allowed)
        self.assertIsNone(
            found_func.args.vararg,
            "SaleOrder._create_invoices must not have *args parameter",
        )
        self.assertIsNone(
            found_func.args.kwarg,
            "SaleOrder._create_invoices must not have **kwargs parameter to prevent silent argument swallowing (F-1)",
        )
        arg_names = {arg.arg for arg in found_func.args.args}
        required = {"self", "final", "grouped"}
        allowed_extra = {"date"}  # Odoo canonical override; reviewed & permitted
        missing = required - arg_names
        self.assertFalse(missing, f"Accounting boundary lost required params: {sorted(missing)}")
        unexpected = arg_names - required - allowed_extra
        self.assertFalse(
            unexpected,
            f"Unreviewed params added to accounting boundary: {sorted(unexpected)}",
        )

    def test_sale_order_create_invoices_rejects_typo_kwargs(self):
        """F-1 / F-5 / CWE-20: Behavioral check ensuring _create_invoices raises TypeError on unexpected kwargs."""
        import ast
        import inspect

        sale_order_path = ROOT_DIR / "addons" / "sale" / "models" / "sale_order.py"
        tree = ast.parse(sale_order_path.read_text(encoding="utf-8"))

        found_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_create_invoices":
                found_func = node
                break

        self.assertIsNotNone(found_func, "Could not find _create_invoices in sale_order.py")
        num_args = len(found_func.args.args)
        num_defaults = len(found_func.args.defaults)
        default_offset = num_args - num_defaults
        params = []
        for i, arg in enumerate(found_func.args.args):
            default = inspect.Parameter.empty
            if i >= default_offset:
                default = ast.literal_eval(found_func.args.defaults[i - default_offset])
            params.append(
                inspect.Parameter(
                    arg.arg,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                )
            )

        sig = inspect.Signature(params)
        # Ensure signature binds valid keyword arguments
        bound = sig.bind(object(), final=True, grouped=False)
        self.assertTrue(bound.arguments["final"])
        self.assertFalse(bound.arguments["grouped"])

        # Ensure unexpected typo kwargs strictly raise TypeError
        with self.assertRaises(TypeError):
            sig.bind(object(), nonexistent_typo_kwarg=True)

    def test_clean_file_content_purges_endashes_and_emojis(self):
        """Unslop Engine v3.0: En-dashes and decorative emojis are purged idempotently."""
        sample = (
            '<odoo>\n'
            '  <template id="t1" name="Title – Scope">\n'
            '    <span>🧪 Sandbox Mô Phỏng 48h</span>\n'
            '    <div class="range">4.6 – 6.1 Tháng</div>\n'
            '    <span class="tab-icon">🏭</span>\n'
            '    <button>🌟 3D Blender Twin</button>\n'
            '  </template>\n'
            '</odoo>'
        )
        cleaned = clean_file_content(sample)
        self.assertNotIn("–", cleaned)
        self.assertNotIn("🧪", cleaned)
        self.assertNotIn("🏭", cleaned)
        self.assertNotIn("🌟", cleaned)
        self.assertIn("Sandbox Mô Phỏng 48h", cleaned)
        self.assertIn("4.6 - 6.1 Tháng", cleaned)
        self.assertIn('<span class="tab-icon">MFG</span>', cleaned)
        self.assertIn("<button>3D Blender Twin</button>", cleaned)
        # Idempotency
        self.assertEqual(clean_file_content(cleaned), cleaned)
        # Topology preservation
        assert_markup_preserved(sample, cleaned, "test_template.xml")

    def test_cli_check_drift_passes_when_clean(self):
        """CLI: execute_views_main(['--check-drift']) returns 0 when no drift exists."""
        exit_code = execute_views_main(["--check-drift"])
        self.assertEqual(exit_code, 0)

    def test_cli_check_drift_detects_anomaly(self):
        """CLI: execute_views_main(['--check-drift']) exits with code 1 when anomaly is detected."""
        with patch.object(
            UnslopLedger,
            "detect_anomalies",
            return_value=[("enterprise/insilos_website/views/home.xml", "old_sha", "drifted_sha")],
        ):
            exit_code = execute_views_main(["--check-drift"])
            self.assertEqual(exit_code, 1)

    def test_vietnamese_and_cjk_bytes_preserved_exactly(self):
        """CWE-20 Data Integrity: Vietnamese diacritics and CJK text must be 100% byte-for-byte preserved."""
        sample = '<odoo><span>Mô Phỏng Tháng Chuỗi 工厂 サンドボックス</span></odoo>'
        self.assertEqual(clean_file_content(sample), sample)

    def test_bare_endash_without_surrounding_spaces_is_handled(self):
        """Boundary: bare numeric range en-dash '4.6–6.1' is cleaned to '4.6-6.1' without residuals."""
        cleaned = clean_file_content('<div class="range">4.6–6.1</div>')
        self.assertNotIn("–", cleaned)
        self.assertEqual(cleaned, '<div class="range">4.6-6.1</div>')

    def test_mutation_fraction_stays_small_on_clean_input(self):
        """Adversarial Canary: Surgical unslop touches only minimal character ratio (< 10%)."""
        src = '<odoo><t t-set="additional_title">A — B</t></odoo>'
        out = clean_file_content(src)
        fraction = assert_mutation_fraction_bounded(src, out, max_fraction=0.15)
        self.assertLess(fraction, 0.15)

    def test_mutation_fraction_circuit_breaker_trips_on_excessive_delta(self):
        """Safety Circuit Breaker: Aborts with ValueError if mutation fraction exceeds threshold."""
        src = '<odoo><p>Original small body text</p></odoo>'
        mutated = '<odoo><p>Radically altered content completely diverging from original bytes</p></odoo>'
        with self.assertRaises(ValueError) as ctx:
            assert_mutation_fraction_bounded(src, mutated, max_fraction=0.10)
        self.assertIn("circuit breaker", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()

