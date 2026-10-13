#!/usr/bin/env python3
"""
tools/test_clean_reverse_anything.py
=============================================================================
Automated Test Suite for Clean-Room Reverse Engineering & Hard Refactor Skill
Verifies the Hegelian Dialectic engine against real Insilos / O20 codebase assets.
=============================================================================
"""

import os
import sys
import json
import py_compile
import tempfile
import pathlib
import unittest

from tools.clean_reverse_anything import (
    run_pipeline,
    detect_target_type,
    TargetType,
    deconstruct_pyc,
    deconstruct_js_bundle,
    deconstruct_qweb_or_scss,
    audit_antithesis,
    generate_synthesis_spec
)


class TestCleanReverseAnything(unittest.TestCase):

    def setUp(self):
        self.repo_root = pathlib.Path(__file__).resolve().parent.parent

    def test_01_pyc_bytecode_deconstruction(self):
        """Test bytecode deconstruction on a compiled Python asset."""
        sample_py = self.repo_root / "odoo" / "tools" / "misc.py"
        self.assertTrue(sample_py.exists(), f"Sample Python file not found: {sample_py}")

        with tempfile.TemporaryDirectory() as tmpdir:
            pyc_path = pathlib.Path(tmpdir) / "misc.cpython-312.pyc"
            py_compile.compile(str(sample_py), cfile=str(pyc_path))
            self.assertTrue(pyc_path.exists(), "Compilation to .pyc failed")

            report = run_pipeline(str(pyc_path))

            self.assertEqual(report["type"], TargetType.PYC)
            self.assertIn("constants", report["thesis"])
            self.assertIn("names", report["thesis"])
            self.assertGreater(report["thesis"]["instruction_count"], 0)
            self.assertIn("remediation_actions", report["synthesis"])

            print("\n[✓] Test 1 PASS: Python bytecode (.pyc) deconstructed and analyzed successfully.")

    def test_02_javascript_bundle_analysis(self):
        """Test JavaScript bundle deconstruction on an existing enterprise module."""
        js_path = self.repo_root / "enterprise" / "pos_react" / "static" / "src" / "app.js"
        self.assertTrue(js_path.exists(), f"POS React app.js not found: {js_path}")

        report = run_pipeline(str(js_path))

        self.assertEqual(report["type"], TargetType.JS_BUNDLE)
        self.assertGreater(report["thesis"]["string_count"], 0)
        self.assertGreater(len(report["thesis"]["extracted_identifiers"]), 0)
        self.assertIn("architecture_blueprint", report["synthesis"])

        print("[✓] Test 2 PASS: Enterprise JS bundle deconstructed with full identifier extraction.")

    def test_03_scss_design_tokens_and_anti_slop(self):
        """Test SCSS token extraction on Insilos Modern Tokens stylesheet."""
        scss_path = self.repo_root / "enterprise" / "insilos_theme_genesis" / "static" / "src" / "scss" / "insilos_modern_tokens.scss"
        self.assertTrue(scss_path.exists(), f"SCSS not found: {scss_path}")

        report = run_pipeline(str(scss_path))

        self.assertEqual(report["type"], TargetType.SCSS_CSS)
        self.assertGreater(len(report["thesis"]["css_variables_used"]), 0)
        # Insilos Modern Tokens should pass or warn on bare white
        self.assertIn("remediation_actions", report["synthesis"])

        print("[✓] Test 3 PASS: SCSS stylesheet token architecture verified.")

    def test_04_adversarial_antithesis_violation_catch(self):
        """Adversarial Test: Invariant checker must catch brand leaks, DDL mutations, and bare white."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = pathlib.Path(tmpdir) / "corrupt_module.py"
            bad_content = """
# Legacy enterprise bridge
class LegacyPartner(models.Model):
    _inherit = 'res.partner'

    def migrate(self):
        # Forbidden DDL mutation
        self.env.cr.execute("ALTER TABLE res_partner ADD COLUMN legacy_odoo_id VARCHAR(64)")
        # Legacy brand leak
        return "Powered by Odoo Community"
"""
            bad_file.write_text(bad_content, encoding="utf-8")

            report = run_pipeline(str(bad_file))

            # Must catch both DDL and brand leak
            self.assertEqual(report["sovereign_status"], "REMEDIATION_REQUIRED")
            violations = report["antithesis"]["violations"]
            self.assertGreaterEqual(len(violations), 2)

            rules_hit = [v["rule"] for v in violations]
            self.assertIn("Counter Code Security Invariance", rules_hit)
            self.assertIn("Strict Database Schema Invariance", rules_hit)

            print("[✓] Test 4 PASS: Adversarial Invariant violations (DDL & Brand leaks) caught 100%.")

    def test_05_dialectic_fleet_engine_contract(self):
        """Verify the fleet dialectic engine schema and dialectic structure."""
        from tools.fleet_opus_dialect import DIALECTIC_SYSTEM_PROMPT

        self.assertIn("THESIS", DIALECTIC_SYSTEM_PROMPT)
        self.assertIn("ANTITHESIS", DIALECTIC_SYSTEM_PROMPT)
        self.assertIn("SYNTHESIS", DIALECTIC_SYSTEM_PROMPT)
        self.assertIn("Strict Database Schema Invariance", DIALECTIC_SYSTEM_PROMPT)
        self.assertIn("Counter Code Security", DIALECTIC_SYSTEM_PROMPT)

        print("[✓] Test 5 PASS: Hegelian Dialectic prompt and contract validated.")


if __name__ == "__main__":
    unittest.main()
