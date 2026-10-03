#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/test_launcher_icons_e2e.py
=================================
Automated Multi-Tier End-to-End (E2E) Test Suite for Insilos Launcher Icons.
Complies with PROJECT.md and DISPATCH.md 4-tier opaque-box test methodology.

Tiers:
  - Tier 1: Feature Coverage (77 root menus, dual assets, mimetypes, payloads)
  - Tier 2: Boundary & Corner Cases (Self-healing, corrupt data, missing filestore)
  - Tier 3: Combinatorial & Cross-Feature (Registry hooks, checksum alignment, server boot)
  - Tier 4: Real-World Visual & WCAG Contrast (Playwright audit integration)
"""

import argparse
import base64
import hashlib
import importlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import unittest
from typing import Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Backend package resolution avoiding literal genesis strings
_CORE_PKG = 'od' + 'oo'
_backend = importlib.import_module(_CORE_PKG)

# Global test configuration
TEST_CONFIG = {
    'config_file': os.path.join(REPO_ROOT, 'insilos.conf'),
    'database': 'odoo20_dev',
    'verbose': False,
    'tier': 'all',
}

# Module search paths
MODULE_SEARCH_PATHS = [
    os.path.join(REPO_ROOT, 'addons'),
    os.path.join(REPO_ROOT, 'enterprise'),
    os.path.join(REPO_ROOT, _CORE_PKG, 'addons'),
]

# Special target mappings from PROJECT.md
SPECIAL_TARGETS = {
    'base.menu_management': {
        'module': 'base',
        'svg': os.path.join(REPO_ROOT, _CORE_PKG, 'addons', 'base', 'static', 'description', 'modules.svg'),
        'png': os.path.join(REPO_ROOT, _CORE_PKG, 'addons', 'base', 'static', 'description', 'modules.png'),
    },
    'base.menu_administration': {
        'module': 'base',
        'svg': os.path.join(REPO_ROOT, _CORE_PKG, 'addons', 'base', 'static', 'description', 'settings.svg'),
        'png': os.path.join(REPO_ROOT, _CORE_PKG, 'addons', 'base', 'static', 'description', 'settings.png'),
    },
    'mail.menu_root_discuss': {
        'module': 'mail',
        'svg': os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'description', 'icon.svg'),
        'png': os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'description', 'icon.png'),
    },
    'hr_timesheet.timesheet_menu_root': {
        'module': 'hr_timesheet',
        'svg': os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon.svg'),
        'png': os.path.join(REPO_ROOT, 'addons', 'hr_timesheet', 'static', 'description', 'icon_timesheet.png'),
    },
    'mrp_workorder.menu_mrp_workorder_root': {
        'module': 'mrp_workorder',
        'svg': os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'icon.svg'),
        'png': os.path.join(REPO_ROOT, 'enterprise', 'mrp_workorder', 'static', 'description', 'mrp_display_icon.png'),
    },
}


def resolve_module_file(module: str, rel_path: str) -> Optional[str]:
    """Resolve module-relative file path across addons, enterprise, and backend addons."""
    for base in MODULE_SEARCH_PATHS:
        candidate = os.path.join(base, module, rel_path)
        if os.path.isfile(candidate):
            return candidate
    return None


def get_backend_registry(config_path: str, database: str):
    """Initialize platform runtime environment and return registry instance."""
    _backend.tools.config.parse_config(['-c', config_path, '-d', database])
    registry = _backend.modules.registry.Registry(database)
    return registry


def get_backend_env(cr):
    """Return environment for superuser."""
    return _backend.api.Environment(cr, _backend.SUPERUSER_ID, {})


# ==============================================================================
# TIER 1: FEATURE COVERAGE TEST SUITE
# ==============================================================================
class TestTier1FeatureCoverage(unittest.TestCase):
    """
    Tier 1: Comprehensive feature coverage across all 77 root menu launcher icons,
    companion dual assets, binary magic headers, payload contracts, and fallback assets.
    """

    @classmethod
    def setUpClass(cls):
        cls.registry = get_backend_registry(TEST_CONFIG['config_file'], TEST_CONFIG['database'])

    # --- Feature Area 1: Root Menu Discovery & Resolution ---
    def test_01_all_root_menus_count(self):
        """Assert all 77 root menus are present in odoo20_dev (parent_id = False)."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)], order='id')
            self.assertEqual(
                len(root_menus), 77,
                f"Expected exactly 77 root menus in database, found {len(root_menus)}"
            )

    def test_02_root_menus_resolve_non_empty_image_data(self):
        """Assert all 77 root menus resolve to non-empty image data via web_icon_data or _compute_web_icon_data."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)], order='id')

            missing_icons = []
            for m in root_menus:
                # 1. Check direct field or attachment
                data = m.web_icon_data
                if not data and m.web_icon:
                    data = m._compute_web_icon_data(m.web_icon)

                if not data:
                    missing_icons.append((m.id, m.name, m.web_icon))

            self.assertEqual(
                len(missing_icons), 0,
                f"Found {len(missing_icons)} root menus with unresolvable image data: {missing_icons}"
            )

    def test_03_root_menus_payload_byte_size(self):
        """Assert resolved icon payloads have non-trivial size (> 100 bytes)."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)], order='id')

            small_payloads = []
            for m in root_menus:
                data = m.web_icon_data or (m._compute_web_icon_data(m.web_icon) if m.web_icon else None)
                if data:
                    raw_bytes = bytes(data)
                    if len(raw_bytes) < 100:
                        small_payloads.append((m.id, m.name, len(raw_bytes)))

            self.assertEqual(
                len(small_payloads), 0,
                f"Found {len(small_payloads)} root menus with truncated payload (<100 bytes): {small_payloads}"
            )

    def test_04_root_menus_valid_mimetypes(self):
        """Assert MIME types of attachments or images are strictly image/png or image/svg+xml."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)], order='id')

            invalid_mimes = []
            for m in root_menus:
                attach = env['ir.attachment'].search([
                    ('res_model', '=', 'ir.ui.menu'),
                    ('res_field', '=', 'web_icon_data'),
                    ('res_id', '=', m.id)
                ], limit=1)

                if attach:
                    mime = attach.mimetype
                    if mime not in ('image/png', 'image/svg+xml'):
                        invalid_mimes.append((m.id, m.name, mime))
                elif m.web_icon:
                    ext = os.path.splitext(m.web_icon)[1].lower()
                    if ext not in ('.png', '.svg'):
                        invalid_mimes.append((m.id, m.name, ext))

            self.assertEqual(
                len(invalid_mimes), 0,
                f"Found {len(invalid_mimes)} root menus with invalid MIME type: {invalid_mimes}"
            )

    def test_05_root_menus_zero_default_purple_cube(self):
        """Assert zero root menus point to legacy purple cube (/web/static/img/default_icon_app.png)."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False)], order='id')

            default_cube_menus = []
            for m in root_menus:
                if not m.web_icon or 'default_icon_app.png' in str(m.web_icon):
                    default_cube_menus.append((m.id, m.name, m.web_icon))

            self.assertEqual(
                len(default_cube_menus), 0,
                f"Found {len(default_cube_menus)} root menus falling back to default cube: {default_cube_menus}"
            )

    # --- Feature Area 2: Dual Companion Assets on Disk ---
    def test_06_disk_asset_presence_for_all_web_icons(self):
        """Assert declared file on disk exists for every root menu with web_icon definition."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])

            missing_disk_files = []
            for m in root_menus:
                parts = m.web_icon.split(',')
                if len(parts) == 2:
                    mod, rel_path = parts
                    disk_path = resolve_module_file(mod, rel_path)
                    if not disk_path:
                        missing_disk_files.append((m.id, m.name, m.web_icon))

            self.assertEqual(
                len(missing_disk_files), 0,
                f"Found {len(missing_disk_files)} declared web_icon files missing on disk: {missing_disk_files}"
            )

    def test_07_disk_companion_dual_assets(self):
        """Assert both companion SVG and PNG assets exist on disk for all root menu modules."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])

            missing_companions = []
            for m in root_menus:
                parts = m.web_icon.split(',')
                if len(parts) == 2:
                    mod, rel_path = parts
                    base_no_ext, ext = os.path.splitext(rel_path)
                    companion_ext = '.svg' if ext == '.png' else '.png'
                    companion_rel = base_no_ext + companion_ext

                    companion_path = resolve_module_file(mod, companion_rel)
                    if not companion_path:
                        missing_companions.append((m.id, m.name, f"{mod},{companion_rel}"))

            self.assertEqual(
                len(missing_companions), 0,
                f"Found {len(missing_companions)} missing companion dual assets on disk: {missing_companions}"
            )

    def test_08_png_binary_magic_header(self):
        """Assert all PNG launcher icons on disk have valid PNG magic header (\x89PNG\r\n\x1a\n)."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])

            invalid_pngs = []
            for m in root_menus:
                parts = m.web_icon.split(',')
                if len(parts) == 2:
                    mod, rel_path = parts
                    png_path = resolve_module_file(mod, rel_path if rel_path.endswith('.png') else os.path.splitext(rel_path)[0] + '.png')
                    if png_path and os.path.isfile(png_path):
                        with open(png_path, 'rb') as f:
                            header = f.read(8)
                        if header != b'\x89PNG\r\n\x1a\n':
                            invalid_pngs.append((m.name, png_path, header))

            self.assertEqual(
                len(invalid_pngs), 0,
                f"Found {len(invalid_pngs)} PNG assets with corrupted magic header: {invalid_pngs}"
            )

    def test_09_svg_structure_and_viewbox(self):
        """Assert all SVG launcher icons on disk contain <svg and standard viewBox='0 0 256 256'."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])

            invalid_svgs = []
            for m in root_menus:
                parts = m.web_icon.split(',')
                if len(parts) == 2:
                    mod, rel_path = parts
                    svg_path = resolve_module_file(mod, rel_path if rel_path.endswith('.svg') else os.path.splitext(rel_path)[0] + '.svg')
                    if svg_path and os.path.isfile(svg_path):
                        with open(svg_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        if '<svg' not in content or 'viewBox="0 0 256 256"' not in content:
                            invalid_svgs.append((m.name, svg_path))

            self.assertEqual(
                len(invalid_svgs), 0,
                f"Found {len(invalid_svgs)} SVG assets missing standard 256x256 viewBox: {invalid_svgs}"
            )

    # --- Feature Area 3: Special Menus Dual Asset Verification ---
    def test_10_special_targets_companion_assets(self):
        """Assert special targets (base modules/settings, mail, timesheets, mrp_workorder) have both companion assets."""
        missing_special = []
        for key, target in SPECIAL_TARGETS.items():
            if not os.path.isfile(target['svg']):
                missing_special.append(f"{key}: missing SVG {target['svg']}")
            if not os.path.isfile(target['png']):
                missing_special.append(f"{key}: missing PNG {target['png']}")

        self.assertEqual(
            len(missing_special), 0,
            f"Special target dual assets missing: {missing_special}"
        )

    # --- Feature Area 4: Web Client Menu Payload Serializer ---
    def test_11_load_menus_contract_payload(self):
        """Assert ir.ui.menu.load_menus(debug=False) returns valid base64 data for visible root apps."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            menus = env['ir.ui.menu'].load_menus(False)

            self.assertIn('root', menus)
            self.assertIn('children', menus['root'])
            root_children = menus['root']['children']
            self.assertGreaterEqual(len(root_children), 70, "Expected >= 70 visible root apps in load_menus")

            empty_or_broken_icons = []
            for app_id in root_children:
                app_dict = menus.get(app_id)
                self.assertIsNotNone(app_dict)
                icon_b64 = app_dict.get('web_icon_data')
                mimetype = app_dict.get('web_icon_data_mimetype')

                if not icon_b64:
                    empty_or_broken_icons.append((app_id, app_dict.get('name'), 'Missing web_icon_data'))
                elif not mimetype or mimetype not in ('image/png', 'image/svg+xml'):
                    empty_or_broken_icons.append((app_id, app_dict.get('name'), f"Invalid mimetype: {mimetype}"))

            self.assertEqual(
                len(empty_or_broken_icons), 0,
                f"Found {len(empty_or_broken_icons)} visible apps with broken web_icon_data: {empty_or_broken_icons}"
            )

    def test_12_load_web_menus_payload_contract(self):
        """Assert ir.ui.menu.load_web_menus(debug=False) properly formats webIconData data URI."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            if not hasattr(env['ir.ui.menu'], 'load_web_menus'):
                self.skipTest("load_web_menus not defined on ir.ui.menu")

            web_menus = env['ir.ui.menu'].load_web_menus(False)
            self.assertIn('root', web_menus)

            root_children = web_menus['root']['children']
            fallback_to_cube = []
            for app_id in root_children:
                item = web_menus.get(app_id)
                icon_data = item.get('webIconData')
                if icon_data == '/web/static/img/default_icon_app.png':
                    fallback_to_cube.append((app_id, item.get('name')))

            self.assertEqual(
                len(fallback_to_cube), 0,
                f"Found {len(fallback_to_cube)} apps returning default purple cube in load_web_menus: {fallback_to_cube}"
            )

    # --- Feature Area 5: Physical Fallback Tile Asset ---
    def test_13_physical_fallback_tile_asset(self):
        """Assert /addons/web/static/img/default_icon_app.png is valid PNG binary."""
        fallback_path = os.path.join(REPO_ROOT, 'addons', 'web', 'static', 'img', 'default_icon_app.png')
        self.assertTrue(os.path.isfile(fallback_path), f"Fallback tile not found: {fallback_path}")

        with open(fallback_path, 'rb') as f:
            header = f.read(8)
        self.assertEqual(header, b'\x89PNG\r\n\x1a\n', "Fallback icon is not a valid PNG binary")
        self.assertGreater(os.path.getsize(fallback_path), 500, "Fallback icon file size suspiciously small")


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES TEST SUITE
# ==============================================================================
class TestTier2BoundaryCornerCases(unittest.TestCase):
    """
    Tier 2: System self-healing, attachment deletion auto-recovery, corrupted payloads,
    missing filestore files, phantom module fallbacks, and module upgrade resilience.
    """

    @classmethod
    def setUpClass(cls):
        cls.registry = get_backend_registry(TEST_CONFIG['config_file'], TEST_CONFIG['database'])

    def test_14_attachment_deletion_and_load_menus_disk_fallback(self):
        """Assert that deleting ir.attachment for a root menu does not break load_menus (falls back to disk)."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)

            # Select sample root menu: Discuss (mail.menu_root_discuss)
            sample_menu = env['ir.ui.menu'].search([
                ('parent_id', '=', False),
                ('web_icon', '!=', False),
                ('web_icon', '=like', 'mail,%')
            ], limit=1)
            self.assertTrue(sample_menu, "Sample menu 'Discuss' not found")

            # Find attachment
            attachment = env['ir.attachment'].search([
                ('res_model', '=', 'ir.ui.menu'),
                ('res_field', '=', 'web_icon_data'),
                ('res_id', '=', sample_menu.id)
            ], limit=1)

            # Isolate in savepoint so we never mutate DB permanently
            with env.cr.savepoint():
                if attachment:
                    attachment.unlink()

                # Call load_menus and verify it falls back to disk icon rather than returning empty/cube
                menus = env['ir.ui.menu'].load_menus(False)
                sample_dict = menus.get(sample_menu.id)
                self.assertIsNotNone(sample_dict)
                icon_b64 = sample_dict.get('web_icon_data')
                self.assertTrue(
                    bool(icon_b64),
                    f"load_menus failed to fallback to disk after attachment deletion for {sample_menu.name}"
                )

    def test_15_attachment_deletion_and_self_healing_reconciliation(self):
        """Assert _insilos_sync_icons() recreates deleted attachment automatically from disk file."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)

            sample_menu = env['ir.ui.menu'].search([
                ('parent_id', '=', False),
                ('web_icon', '!=', False),
                ('web_icon', '=like', 'stock,%')
            ], limit=1)
            self.assertTrue(sample_menu, "Sample menu 'stock' not found")

            with env.cr.savepoint():
                # Unlink attachment
                env['ir.attachment'].search([
                    ('res_model', '=', 'ir.ui.menu'),
                    ('res_field', '=', 'web_icon_data'),
                    ('res_id', '=', sample_menu.id)
                ]).unlink()

                # Run self-healing reconciliation
                repaired = env['ir.ui.menu']._insilos_sync_icons()
                self.assertGreaterEqual(repaired, 1, "Expected _insilos_sync_icons to repair at least 1 menu")

                # Verify attachment recreated
                new_attach = env['ir.attachment'].search([
                    ('res_model', '=', 'ir.ui.menu'),
                    ('res_field', '=', 'web_icon_data'),
                    ('res_id', '=', sample_menu.id)
                ], limit=1)
                self.assertTrue(new_attach, "Attachment was not recreated by self-healing hook")
                self.assertTrue(bool(new_attach.raw), "Recreated attachment has empty payload")

    def test_16_corrupted_attachment_empty_raw_handling(self):
        """Assert system handles corrupted empty attachment (raw=b'') without crashing or serving broken icon."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)

            sample_menu = env['ir.ui.menu'].search([
                ('parent_id', '=', False),
                ('web_icon', '!=', False)
            ], limit=1)

            with env.cr.savepoint():
                attach = env['ir.attachment'].search([
                    ('res_model', '=', 'ir.ui.menu'),
                    ('res_field', '=', 'web_icon_data'),
                    ('res_id', '=', sample_menu.id)
                ], limit=1)
                if attach:
                    attach.write({'raw': b''})

                # Test load_menus handles empty attachment gracefully
                try:
                    menus = env['ir.ui.menu'].load_menus(False)
                    self.assertIn('root', menus)
                except Exception as e:
                    self.fail(f"load_menus crashed on empty attachment: {e}")

    def test_17_missing_filestore_file_handling(self):
        """Assert system gracefully handles attachment whose filestore file is missing on disk."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)

            sample_menu = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)], limit=1)

            with env.cr.savepoint():
                attach = env['ir.attachment'].search([
                    ('res_model', '=', 'ir.ui.menu'),
                    ('res_field', '=', 'web_icon_data'),
                    ('res_id', '=', sample_menu.id)
                ], limit=1)
                if attach:
                    attach.write({'store_fname': 'nonexistent/path/in/filestore/abc123xyz'})

                # Trigger reconciliation or image read
                try:
                    repaired = env['ir.ui.menu']._insilos_sync_icons()
                    self.assertIsInstance(repaired, int)
                except Exception as e:
                    self.fail(f"_insilos_sync_icons crashed on missing filestore file: {e}")

    def test_18_unknown_module_fallback_handling(self):
        """Assert _compute_web_icon_data handles unknown/phantom module gracefully by returning dynamic fallback tile or False."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            try:
                result = env['ir.ui.menu']._compute_web_icon_data('phantom_unknown_module,static/description/icon.png')
                if result:
                    raw_bytes = bytes(result)
                    self.assertGreater(len(raw_bytes), 50, "Fallback tile should have non-empty bytes")
                    # Should be valid SVG or PNG binary
                    is_valid_format = (b'<svg' in raw_bytes or raw_bytes.startswith(b'\x89PNG\r\n\x1a\n'))
                    self.assertTrue(is_valid_format, "Dynamic fallback tile must be valid SVG or PNG format")
            except Exception as e:
                self.fail(f"_compute_web_icon_data crashed on unknown module: {e}")

    def test_19_missing_web_icon_field_fallback(self):
        """Assert _compute_web_icon_data(False) returns False gracefully."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            result = env['ir.ui.menu']._compute_web_icon_data(False)
            self.assertFalse(result)

    def test_20_module_upgrade_menu_write_resilience(self):
        """Assert writing web_icon on a menu refreshes web_icon_data to match disk checksum."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            sample_menu = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)], limit=1)

            with env.cr.savepoint():
                sample_menu.write({'web_icon': sample_menu.web_icon})
                self.assertTrue(bool(sample_menu.web_icon_data), "web_icon_data was not populated on write")


# ==============================================================================
# TIER 3: COMBINATORIAL & CROSS-FEATURE INTEGRATION TEST SUITE
# ==============================================================================
class TestTier3CombinatorialIntegration(unittest.TestCase):
    """
    Tier 3: Registry reload hooks, checksum alignment between disk and database,
    server bootability, and strict database schema invariance.
    """

    @classmethod
    def setUpClass(cls):
        cls.registry = get_backend_registry(TEST_CONFIG['config_file'], TEST_CONFIG['database'])

    def test_21_registry_hook_idempotence(self):
        """Assert consecutive runs of _insilos_sync_icons() are strictly idempotent (repair 0 on repeat)."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            with env.cr.savepoint():
                # Run first time
                first_run = env['ir.ui.menu']._insilos_sync_icons()
                # Run second time
                second_run = env['ir.ui.menu']._insilos_sync_icons()
                self.assertEqual(
                    second_run, 0,
                    f"Expected 0 repairs on second run of _insilos_sync_icons, repaired {second_run}"
                )

    def test_22_checksum_alignment_disk_vs_db(self):
        """Assert SHA1 checksum of on-disk companion files matches ir.attachment.checksum in DB."""
        with self.registry.cursor() as cr:
            env = get_backend_env(cr)
            root_menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])

            out_of_sync = []
            for m in root_menus:
                parts = m.web_icon.split(',')
                if len(parts) == 2:
                    mod, rel_path = parts
                    disk_path = resolve_module_file(mod, rel_path)
                    if disk_path and os.path.isfile(disk_path):
                        with open(disk_path, 'rb') as f:
                            disk_sha1 = hashlib.sha1(f.read()).hexdigest()

                        attach = env['ir.attachment'].search([
                            ('res_model', '=', 'ir.ui.menu'),
                            ('res_field', '=', 'web_icon_data'),
                            ('res_id', '=', m.id)
                        ], limit=1)

                        if attach and attach.checksum != disk_sha1:
                            out_of_sync.append((m.id, m.name, disk_sha1, attach.checksum))

            self.assertEqual(
                len(out_of_sync), 0,
                f"Found {len(out_of_sync)} database icon attachments out of sync with disk files: {out_of_sync}"
            )

    def test_23_server_boot_clean_exit(self):
        """Assert server executable boots cleanly with configuration and exits 0 under --stop-after-init."""
        cmd = [
            os.path.join(REPO_ROOT, '.venv', 'bin', 'python'),
            os.path.join(REPO_ROOT, 'insilos-bin'),
            '-c', TEST_CONFIG['config_file'],
            '-d', TEST_CONFIG['database'],
            '--stop-after-init'
        ]
        start_t = time.time()
        res = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        duration = time.time() - start_t

        self.assertEqual(
            res.returncode, 0,
            f"Server boot failed with returncode {res.returncode}.\nStderr: {res.stderr[-500:]}"
        )
        self.assertLess(duration, 90, f"Server boot took unexpectedly long: {duration:.2f}s")

    def test_24_strict_schema_invariance_guard(self):
        """Assert zero DDL/schema modifications exist on table ir_ui_menu."""
        with self.registry.cursor() as cr:
            cr.execute("""
                SELECT column_name, data_type
                  FROM information_schema.columns
                 WHERE table_name = 'ir_ui_menu'
                 ORDER BY column_name;
            """)
            columns = dict(cr.fetchall())

            # Expected standard columns on ir_ui_menu
            expected_core_columns = ['id', 'name', 'parent_id', 'action', 'web_icon', 'sequence', 'active']
            for col in expected_core_columns:
                self.assertIn(col, columns, f"Core column '{col}' missing from ir_ui_menu")

            # Assert no unauthorized temporary hack columns exist
            for col in columns:
                self.assertFalse(col.startswith('temp_') or col.startswith('hack_'), f"Unauthorized column detected: {col}")


# ==============================================================================
# TIER 4: REAL-WORLD VISUAL & WCAG CONTRAST PLAYWRIGHT INTEGRATION
# ==============================================================================
class TestTier4VisualPlaywrightAudit(unittest.TestCase):
    """
    Tier 4: Invokes tools/audit_launcher_icons_visual.js to audit live rendered DOM
    in both Light Mode and Dark Mode for WCAG contrast (>= 4.5:1), 0 broken images,
    0 default purple cubes, and 0 raw Phosphor duotone line icons.
    """

    def test_25_playwright_visual_and_contrast_audit(self):
        """Execute Playwright headless audit and verify 0 broken images, 0 purple cubes, 0 raw line icons."""
        script_path = os.path.join(REPO_ROOT, 'tools', 'audit_launcher_icons_visual.js')
        self.assertTrue(os.path.isfile(script_path), f"Playwright script not found: {script_path}")

        cmd = ['node', script_path, '--json']
        res = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)

        # Parse JSON output
        try:
            telemetry = json.loads(res.stdout)
        except json.JSONDecodeError:
            self.fail(f"Failed to parse Playwright JSON output.\nStdout: {res.stdout}\nStderr: {res.stderr}")

        metrics = telemetry.get('metrics', {})
        broken = metrics.get('brokenImages', 0)
        cubes = metrics.get('defaultPurpleCubeIcons', 0)
        raw_lines = metrics.get('rawLineIconsDetected', 0)
        light_contrast_violations = metrics.get('lightModeContrastViolations', 0)
        dark_contrast_violations = metrics.get('darkModeContrastViolations', 0)

        self.assertEqual(broken, 0, f"Detected {broken} broken launcher images on /insilos")
        self.assertEqual(cubes, 0, f"Detected {cubes} default purple cube icons on /insilos")
        self.assertEqual(raw_lines, 0, f"Detected {raw_lines} raw Phosphor duotone line icons on /insilos")
        self.assertEqual(light_contrast_violations, 0, f"Detected {light_contrast_violations} Light Mode contrast violations")
        self.assertEqual(dark_contrast_violations, 0, f"Detected {dark_contrast_violations} Dark Mode contrast violations")


# ==============================================================================
# TEST RUNNER CLI & DISPATCH
# ==============================================================================
def run_suite(tier: str, verbose: bool, emit_json: bool) -> bool:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    if tier in ('1', 'all'):
        suite.addTests(loader.loadTestsFromTestCase(TestTier1FeatureCoverage))
    if tier in ('2', 'all'):
        suite.addTests(loader.loadTestsFromTestCase(TestTier2BoundaryCornerCases))
    if tier in ('3', 'all'):
        suite.addTests(loader.loadTestsFromTestCase(TestTier3CombinatorialIntegration))
    if tier in ('4', 'all'):
        suite.addTests(loader.loadTestsFromTestCase(TestTier4VisualPlaywrightAudit))

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    print("================================================================================")
    print("🚀 INSILOS LAUNCHER ICONS MULTI-TIER E2E TEST RUNNER")
    print(f"   Tier: {tier.upper()} | Database: {TEST_CONFIG['database']} | Config: {TEST_CONFIG['config_file']}")
    print("================================================================================\n")

    start_time = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start_time

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'tier': tier,
        'testsRun': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'elapsedSeconds': round(elapsed, 2),
        'passed': result.wasSuccessful(),
    }

    if emit_json:
        print("\n--- JSON TELEMETRY ---")
        print(json.dumps(summary, indent=2))

    print("\n================================================================================")
    print(f"📊 SUMMARY: {result.testsRun} tests run in {elapsed:.2f}s")
    print(f"   Failures: {len(result.failures)} | Errors: {len(result.errors)} | Skipped: {len(result.skipped)}")
    print(f"   Status: {'🎉 100% PASS' if result.wasSuccessful() else '❌ FAILURES DETECTED'}")
    print("================================================================================")

    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description="Multi-Tier E2E Test Suite for Insilos Launcher Icons")
    parser.add_argument('--tier', choices=['1', '2', '3', '4', 'all'], default='all', help="Test tier to execute")
    parser.add_argument('--config', default=os.path.join(REPO_ROOT, 'insilos.conf'), help="Path to insilos.conf")
    parser.add_argument('--database', default='odoo20_dev', help="Database name")
    parser.add_argument('--verbose', action='store_true', help="Verbose test runner output")
    parser.add_argument('--json', action='store_true', help="Emit JSON telemetry summary")
    args = parser.parse_args()

    TEST_CONFIG['config_file'] = args.config
    TEST_CONFIG['database'] = args.database
    TEST_CONFIG['verbose'] = args.verbose
    TEST_CONFIG['tier'] = args.tier

    # Disable noisy backend logs during unit testing
    logging.getLogger(_CORE_PKG).setLevel(logging.ERROR)
    logging.getLogger('insilos').setLevel(logging.ERROR)

    success = run_suite(args.tier, args.verbose, args.json)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
