#!/usr/bin/env python3
"""
CI Schema-Level Invariant: InnoKafe arch_db & QWeb Branding Gate
================================================================
Guarantees that database views and on-disk QWeb templates maintain 100% official vector branding
and strictly forbid any legacy/fabricated text logo placeholders (CWE-703, Zero-Fake-Pass).
"""

import os
import re
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
VIEWS_DIR = WORKSPACE_ROOT / "enterprise" / "innokafe_website" / "views"

BANNED_PATTERNS = [
    re.compile(r"class=[\"'][^\"']*\b(text-logo|logo-text|font-logo)\b[^\"']*[\"']", re.IGNORECASE),
    re.compile(r"<span[^>]*class=[\"'][^\"']*\b(inno-logo-text|brand-text)\b[^\"']*[\"']", re.IGNORECASE),
]

REQUIRED_VECTOR_SVGS = [
    "innokafe_logo_master.svg",
    "innokafe_logo_white.svg",
    "favicon.svg",
]


class TestArchDbBrandingInvariance(unittest.TestCase):
    """Enforces zero-fake-text-logo invariant across both disk views and database arch_db."""

    def test_01_static_qweb_views_invariance(self):
        """Assert zero banned text logo classes across all InnoKafe QWeb template files."""
        self.assertTrue(VIEWS_DIR.exists(), f"Views directory missing: {VIEWS_DIR}")
        xml_files = list(VIEWS_DIR.glob("*.xml"))
        self.assertGreater(len(xml_files), 0, "No XML view templates found")

        for xml_file in xml_files:
            content = xml_file.read_text(encoding="utf-8")
            for pattern in BANNED_PATTERNS:
                matches = pattern.findall(content)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Forbidden fake text logo pattern detected in {xml_file.name}: {matches}"
                )

    def test_02_navbar_and_footer_vector_mandates(self):
        """Assert that navbar and footer templates strictly link to official vector SVGs."""
        website_templates = VIEWS_DIR / "website_templates.xml"
        self.assertTrue(website_templates.exists(), "website_templates.xml not found")
        content = website_templates.read_text(encoding="utf-8")

        for svg_asset in REQUIRED_VECTOR_SVGS:
            self.assertIn(
                svg_asset,
                content,
                f"Required vector asset {svg_asset} not referenced in website_templates.xml"
            )

    def test_03_database_arch_db_live_invariance(self):
        """Audit PostgreSQL innokafe_prod ir_ui_view arch_db for zero regression."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.environ.get("PGHOST", "127.0.0.1"),
                port=int(os.environ.get("PGPORT", "5434")),
                user=os.environ.get("PGUSER", "odoo"),
                password=os.environ.get("PGPASSWORD", "1NN0R1@2026"),
                dbname=os.environ.get("PGDATABASE", "innokafe_prod"),
                connect_timeout=3
            )
        except Exception as e:
            self.skipTest(f"Database connection skipped: {e}")
            return

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, key, name, arch_db::text
                FROM ir_ui_view
                WHERE key ILIKE '%innokafe%'
                   OR arch_db::text ILIKE '%innokafe_logo%'
                   OR key IN ('website.option_header_brand_logo', 'website.footer_custom')
            """)
            views = cur.fetchall()
            self.assertGreater(len(views), 0, "No InnoKafe views found in database")

            for vid, key, name, arch in views:
                for pattern in BANNED_PATTERNS:
                    matches = pattern.findall(arch)
                    self.assertEqual(
                        len(matches),
                        0,
                        f"Regression detected in DB view ID={vid} ({key}): found {matches}"
                    )
            conn.close()
        except Exception as e:
            conn.close()
            raise e


if __name__ == "__main__":
    unittest.main()
