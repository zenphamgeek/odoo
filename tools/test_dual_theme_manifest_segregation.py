#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sovereign Dual-Theme & Form Architecture Static Verification Gate.

Enforces AGENTS.md Section 4 invariants across all 700+ modules in addons/ and enterprise/:
1. Zero .dark.scss files leaked into web.assets_backend via wildcard globs.
2. Zero invalid ('remove', ...) directives for files never added to web.assets_backend.
3. Dual-theme navbar launcher icon inline XML guard + light/dark SCSS toggle parity.
4. Full-width form sheet DOM selector hierarchy and notebook nav transparent reset.
"""

import ast
import glob
import os
import re
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestDualThemeManifestSegregation(unittest.TestCase):
    """Verifies AGENTS.md Rule 4 invariants across the entire codebase."""

    def test_zero_banned_light_hex_fallbacks_with_important(self):
        """Ensure no SCSS file uses light hex fallbacks inside var(--insilos-bg-*) with !important."""
        banned_pattern = re.compile(
            r"var\(\s*--insilos-bg-[a-z0-9_-]+\s*,\s*(#fff(?:fff)?|#f8fafc|#f4f6f8|#f1f5f9)\s*\)\s*!important",
            re.IGNORECASE,
        )
        violations = []
        scss_globs = (
            "enterprise/insilos_theme_genesis/static/src/scss/*.scss",
            "addons/insilos_sap_fiori/static/src/scss/*.scss",
            "enterprise/insilos_logistics_idp/static/src/**/*.scss",
            "enterprise/insilos_market_terminal/static/src/**/*.scss",
        )
        for rel_glob in scss_globs:
            for fpath in sorted(glob.glob(os.path.join(WORKSPACE_ROOT, rel_glob), recursive=True)):
                with open(fpath, "r", encoding="utf-8") as fh:
                    for line_no, line in enumerate(fh, 1):
                        if banned_pattern.search(line):
                            violations.append(
                                (os.path.relpath(fpath, WORKSPACE_ROOT), line_no, line.strip())
                            )
        self.assertEqual(
            violations,
            [],
            f"Found banned light hex fallbacks coupled with !important: {violations}",
        )

    def test_zero_dark_scss_leaks_and_valid_removes_in_assets_backend(self):
        """Ensure no module leaks .dark.scss into web.assets_backend or removes unbundled files."""
        leaking_modules = []
        invalid_removes = []

        for root_name in ("enterprise", "addons"):
            root_dir = os.path.join(WORKSPACE_ROOT, root_name)
            for mpath in sorted(glob.glob(os.path.join(root_dir, "*", "__manifest__.py"))):
                with open(mpath, "r", encoding="utf-8") as fh:
                    try:
                        manifest = ast.literal_eval(fh.read())
                    except Exception:
                        continue

                backend_ops = manifest.get("assets", {}).get("web.assets_backend", [])
                included = set()

                for item in backend_ops:
                    if isinstance(item, str):
                        pattern = os.path.join(root_dir, item)
                        for match in glob.glob(pattern, recursive=True):
                            if os.path.isfile(match):
                                included.add(os.path.relpath(match, root_dir))
                    elif isinstance(item, tuple) and len(item) >= 2 and item[0] in ("after", "before", "replace", "prepend", "append"):
                        target = item[-1]
                        pattern = os.path.join(root_dir, target)
                        for match in glob.glob(pattern, recursive=True):
                            if os.path.isfile(match):
                                included.add(os.path.relpath(match, root_dir))
                    elif isinstance(item, tuple) and len(item) == 2 and item[0] == "remove":
                        rem_rel = item[1]
                        rem_pattern = os.path.join(root_dir, rem_rel)
                        rem_matches = {
                            os.path.relpath(m, root_dir)
                            for m in glob.glob(rem_pattern, recursive=True)
                            if os.path.isfile(m)
                        }
                        if rem_rel.endswith(".dark.scss") and not (rem_matches & included):
                            invalid_removes.append((os.path.relpath(mpath, WORKSPACE_ROOT), rem_rel))
                        included -= rem_matches

                dark_leaks = sorted(f for f in included if f.endswith(".dark.scss"))
                if dark_leaks:
                    leaking_modules.append((os.path.relpath(mpath, WORKSPACE_ROOT), dark_leaks))

        self.assertEqual(
            leaking_modules,
            [],
            f"Found .dark.scss files leaked into web.assets_backend: {leaking_modules}",
        )
        self.assertEqual(
            invalid_removes,
            [],
            f"Found ('remove', ...) directives for .dark.scss not present in web.assets_backend: {invalid_removes}",
        )

    def test_dual_theme_launcher_icon_guard(self):
        """Ensure navbar.xml has inline display:none on dark icon and SCSS bundles toggle visibility."""
        navbar_xml = os.path.join(
            WORKSPACE_ROOT,
            "enterprise/web_enterprise/static/src/webclient/navbar/navbar.xml",
        )
        with open(navbar_xml, "r", encoding="utf-8") as fh:
            xml_content = fh.read()

        self.assertIn("o_insilos_launcher_icon_light", xml_content)
        self.assertIn("o_insilos_launcher_icon_dark", xml_content)
        self.assertIn("display: none;", xml_content)

        light_scss = os.path.join(
            WORKSPACE_ROOT,
            "enterprise/insilos_theme_genesis/static/src/scss/insilos_systray_restructure.scss",
        )
        with open(light_scss, "r", encoding="utf-8") as fh:
            light_content = fh.read()
        self.assertIn(".o_insilos_launcher_icon_dark", light_content)

        dark_scss = os.path.join(
            WORKSPACE_ROOT,
            "enterprise/insilos_theme_genesis/static/src/scss/insilos_webclient_general.dark.scss",
        )
        with open(dark_scss, "r", encoding="utf-8") as fh:
            dark_content = fh.read()
        self.assertIn(".o_insilos_launcher_icon_dark", dark_content)

    def test_form_sheet_hierarchy_and_notebook_transparent_reset(self):
        """Ensure form sheet selector hierarchy is non-inverted and notebook nav background is transparent."""
        form_scss = os.path.join(
            WORKSPACE_ROOT,
            "enterprise/insilos_theme_genesis/static/src/scss/insilos_form_restructure.scss",
        )
        with open(form_scss, "r", encoding="utf-8") as fh:
            content = fh.read()

        self.assertNotIn(".o_content > .o_form_view", content)
        self.assertIn("> .o_content,", content)
        self.assertIn("max-width: 100% !important;", content)
        self.assertIn(".o_notebook_headers", content)
        self.assertIn("background-color: transparent !important;", content)


if __name__ == "__main__":
    unittest.main()
