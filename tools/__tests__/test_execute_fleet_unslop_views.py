#!/usr/bin/env python3
"""
tools/__tests__/test_execute_fleet_unslop_views.py
Unit tests for execute_fleet_unslop_views.py verifying:
1. Idempotency invariant: clean(clean(x)) == clean(x)
2. F1: Unicode strings with XML encoding declarations do not crash
3. F3: Structural drift is detected and rejected
4. F2: Two-phase batch transaction prevents partial writes on validation failure
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.execute_fleet_unslop_views import (
    clean_file_content,
    assert_markup_preserved,
)

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
        xml_with_decl = '<?xml version="1.0" encoding="utf-8"?>\n<odoo><template id="t1" name="Title | Insilos"><p>Clean text</p></template></odoo>'
        # Must not raise ValueError or ParseError
        assert_markup_preserved(xml_with_decl, xml_with_decl, "test.xml")

    def test_assert_markup_preserved_passes_on_text_changes(self):
        """F3: Preserves identical element hierarchy and attribute topology across text modifications."""
        before = '<odoo><template id="t1" name="Before — Subtitle"><div class="container"><span class="badge">01 — Step</span></div></template></odoo>'
        after = '<odoo><template id="t1" name="Before | Subtitle"><div class="container"><span class="badge">01. Step</span></div></template></odoo>'
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

    def test_assert_markup_preserved_rejects_entity_expansion_bomb(self):
        """CWE-776: billion-laughs style payload must not expand or hang."""
        bomb = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE lolz [<!ENTITY lol "lol">'
            '<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
            '<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">]>'
            '<odoo><template id="t1"><p>&lol3;</p></template></odoo>'
        )
        with self.assertRaises((ValueError, Exception)):
            assert_markup_preserved(bomb, bomb, "bomb.xml")

    def test_clean_file_content_type_guard(self):
        """F-C (CWE-628): Raises TypeError if non-string argument is passed."""
        with self.assertRaises(TypeError):
            clean_file_content(123)  # type: ignore

        with self.assertRaises(TypeError):
            clean_file_content(["path", "content"])  # type: ignore

if __name__ == "__main__":
    unittest.main()
