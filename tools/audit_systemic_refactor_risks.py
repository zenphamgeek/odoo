#!/usr/bin/env python3
"""
Systemic Theme, Asset Bundle (`ir_asset`), & SCSS/ORM Refactoring Auditor
=========================================================================
Scans `/home/zen/O20/addons` and `/home/zen/O20/enterprise` plus PostgreSQL
(`insilos20_dev` and `innoria_prod`) across 5 systemic risk categories:

- Category A (Light-Bundle Dark Leak):
  Base `.variables.scss` / `.scss` files in `web.assets_backend` containing
  hardcoded dark hex backgrounds (`#070b14`, `#090d16`, `#0a0e17`, `#0b0f19`,
  `#0d1322`, `#141e33`, `#1B1D26`, `#262A36`) on UI surfaces outside
  `body.o_dark_mode` / `[data-theme="dark"]` (excluding token definitions in
  `insilos_modern_tokens.scss` or code/terminal syntax highlighters).

- Category B (Dark-Mode Bare White Surface Leak):
  Backend `.scss` or backend QWeb `.xml` files (excluding print/PDF report
  templates and website frontend templates) containing hardcoded bare light
  background hex colors (`#fff`, `#ffffff`, `#f8fafc`, `#f1f5f9`, `#f4f6f8`)
  outside `:root` token definitions, `body:not(.o_dark_mode)`, or
  `[data-theme="light"]`.

- Category C (`__manifest__.py` <-> `ir_asset` Drift):
  Any installed custom/enterprise module (`insilos_*`, `web_enterprise`,
  `documents`) whose explicit `web.assets_backend` or `web.assets_web_dark`
  file entries in `__manifest__.py` are missing or `active = FALSE` in
  `ir_asset` in `insilos20_dev` or `innoria_prod`.

- Category D (`.dark.scss` Bundle Segregation & Light Safety Guard):
  1. Any wildcard glob (`static/src/**/*`) in `web.assets_backend` where
     `.dark.scss` files coexist in that tree (unless explicitly excluded via
     `('remove', '**/*.dark.scss')` or segregated).
  2. Any `.dark.scss` file in `web.assets_web_dark` that binds
     `:root, html, body` dark variables without a corresponding
     `html[data-theme="light"] body:not(.o_dark_mode)` safety guard.

- Category E (OWL 2 / OWL 3 & ORM View/Table Refactoring Traps):
  1. OWL templates using `t-ref="root"` on components inheriting OWL 3
     `signal.ref()` (`rootRef`) without `this.rootRef` or compatibility proxy
     fallback (`makeRefProxy` / `useRef("root")`).
  2. Direct `CREATE INDEX` on `res_partner` without checking if `res_partner`
     is an updatable view over `party_master` (`relkind = 'v'`).
  3. Unqualified `SQL('id')` / `SQL('move_id')` / `SQL('order_id')` in
     `_get_count_id`.
"""

import argparse
import ast
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import psycopg2

ROOT_DIR = Path("/home/zen/O20")
ADDONS_DIRS = [ROOT_DIR / "addons", ROOT_DIR / "enterprise"]

PG_HOST = os.environ.get("PGHOST", "127.0.0.1")
PG_PORT = int(os.environ.get("PGPORT", "5434"))
PG_USER = os.environ.get("PGUSER", "odoo")
PG_PASS = os.environ.get("PGPASSWORD", "1NN0R1@2026")
TARGET_DBS = ["insilos20_dev", "innoria_prod"]

DARK_HEX_RE = re.compile(
    r"(?i)#(?:070b14|090d16|0a0e17|0b0f19|0d1322|141e33|1b1d26|262a36)\b"
)
LIGHT_BG_HEX_RE = re.compile(
    r"(?i)(?:background(?:-color)?)\s*:\s*[^;{}]*?#(?:fff|ffffff|f8fafc|f1f5f9|f4f6f8)\b"
)

CUSTOM_ENTERPRISE_MODULES = {
    "web_enterprise",
    "documents",
    "gpu_fleet_manager",
}


def is_target_module(mod_name: str) -> bool:
    return mod_name.startswith("insilos_") or mod_name in CUSTOM_ENTERPRISE_MODULES


def load_manifests() -> Dict[str, Tuple[Path, dict]]:
    manifests: Dict[str, Tuple[Path, dict]] = {}
    for base in ADDONS_DIRS:
        if not base.exists():
            continue
        for mf_path in sorted(base.glob("*/__manifest__.py")):
            mod_dir = mf_path.parent
            try:
                data = ast.literal_eval(mf_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    manifests[mod_dir.name] = (mod_dir, data)
            except Exception:
                pass
    return manifests


def strip_comments(text: str) -> str:
    text = re.sub(
        r"/\*.*?\*/",
        lambda m: "\n" * m.group(0).count("\n"),
        text,
        flags=re.DOTALL,
    )
    lines = []
    for line in text.splitlines():
        idx = line.find("//")
        if idx != -1 and "://" not in line:
            line = line[:idx]
        lines.append(line)
    return "\n".join(lines)


def audit_category_a(manifests: Dict[str, Tuple[Path, dict]]) -> List[dict]:
    """Category A: Light-Bundle Dark Leak in web.assets_backend SCSS files."""
    violations = []
    checked_files = set()

    for mod_name, (mod_dir, data) in manifests.items():
        if not (is_target_module(mod_name) or mod_name == "web"):
            continue
        assets = data.get("assets", {})
        backend_entries = assets.get("web.assets_backend", [])
        raw_globs = []
        for entry in backend_entries:
            if isinstance(entry, (tuple, list)) and len(entry) >= 2:
                if entry[0] != "remove":
                    raw_globs.append(entry[-1])
            elif isinstance(entry, str):
                raw_globs.append(entry)

        for pattern in raw_globs:
            if not pattern.startswith(mod_name + "/"):
                continue
            rel = pattern[len(mod_name) + 1 :]
            for fpath in sorted(mod_dir.glob(rel)):
                if not fpath.is_file() or fpath.suffix != ".scss":
                    continue
                if fpath.name.endswith(".dark.scss"):
                    continue
                if fpath.name == "insilos_modern_tokens.scss":
                    continue
                if fpath in checked_files:
                    continue
                checked_files.add(fpath)

                content = strip_comments(fpath.read_text(encoding="utf-8", errors="ignore"))
                if not DARK_HEX_RE.search(content):
                    continue

                stack: List[str] = []
                for lineno, raw_line in enumerate(content.splitlines(), start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    if DARK_HEX_RE.search(line):
                        ctx = " ".join(stack + [line]).lower()
                        allowed_ctx = any(
                            tok in ctx
                            for tok in (
                                "o_dark_mode",
                                'data-theme="dark"',
                                "data-theme='dark'",
                                'data-bs-theme="dark"',
                                "insilos-code",
                                "o_code",
                                "pre",
                                "code",
                                "terminal-log",
                                "monaco",
                                "ace_editor",
                                "tooltip",
                                "toast-dark",
                                "preview-dark",
                                "badge-dark",
                                "hero",
                                "linear-gradient",
                            )
                        )
                        is_bg_or_var = any(
                            k in line.lower()
                            for k in ("background", "--", "$", "surface", "canvas", "card")
                        )
                        if is_bg_or_var and not allowed_ctx:
                            violations.append(
                                {
                                    "category": "A",
                                    "file": str(fpath.relative_to(ROOT_DIR)),
                                    "line": lineno,
                                    "detail": f"Hardcoded dark hex in light bundle outside dark selector: `{line}`",
                                }
                            )
                    if "{" in line:
                        selector_part = line.split("{")[0].strip()
                        for _ in range(line.count("{")):
                            stack.append(selector_part)
                    if "}" in line:
                        for _ in range(line.count("}")):
                            if stack:
                                stack.pop()
    return violations


def audit_category_b(manifests: Dict[str, Tuple[Path, dict]]) -> List[dict]:
    """Category B: Dark-Mode Bare White Surface Leak in custom/enterprise backend SCSS & XML."""
    violations = []
    for mod_name, (mod_dir, _data) in manifests.items():
        if not mod_name.startswith("insilos_"):
            continue
        static_src = mod_dir / "static" / "src"
        if not static_src.exists():
            continue
        for fpath in sorted(static_src.rglob("*")):
            if not fpath.is_file() or fpath.suffix not in (".scss", ".xml"):
                continue
            if fpath.name == "insilos_modern_tokens.scss":
                continue
            rel_str = str(fpath.relative_to(ROOT_DIR))
            if any(
                skip in rel_str.lower()
                for skip in (
                    "report",
                    "print",
                    "website",
                    "portal",
                    "frontend",
                    "public_auth",
                    "email",
                )
            ):
                continue

            raw_text = fpath.read_text(encoding="utf-8", errors="ignore")
            if fpath.suffix == ".scss":
                text = strip_comments(raw_text)
                stack: List[str] = []
                for lineno, raw_line in enumerate(text.splitlines(), start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    if LIGHT_BG_HEX_RE.search(line):
                        ctx = " ".join(stack + [line]).lower()
                        has_var_token = "var(--" in line.lower() and "!important" not in line.lower()
                        allowed_ctx = has_var_token or any(
                            tok in ctx
                            for tok in (
                                ":root",
                                "not(.o_dark_mode)",
                                'data-theme="light"',
                                "data-theme='light'",
                                "@media print",
                                "print",
                                "paper",
                                "slider::before",
                                "switch",
                                "thumb",
                                "knob",
                                "qr",
                                "barcode",
                                "::after",
                                "::before",
                            )
                        )
                        if not allowed_ctx:
                            violations.append(
                                {
                                    "category": "B",
                                    "file": rel_str,
                                    "line": lineno,
                                    "detail": f"Bare light background hex in backend SCSS: `{line}`",
                                }
                            )
                    if "{" in line:
                        selector_part = line.split("{")[0].strip()
                        for _ in range(line.count("{")):
                            stack.append(selector_part)
                    if "}" in line:
                        for _ in range(line.count("}")):
                            if stack:
                                stack.pop()
            elif fpath.suffix == ".xml":
                for lineno, raw_line in enumerate(raw_text.splitlines(), start=1):
                    line = raw_line.strip()
                    if "style=" in line.lower() and LIGHT_BG_HEX_RE.search(line):
                        if "var(--" not in line.lower():
                            violations.append(
                                {
                                    "category": "B",
                                    "file": rel_str,
                                    "line": lineno,
                                    "detail": f"Inline bare light background hex in backend QWeb XML: `{line}`",
                                }
                            )
    return violations


def audit_category_c(manifests: Dict[str, Tuple[Path, dict]]) -> List[dict]:
    """Category C: `__manifest__.py` <-> `ir_asset` Drift across target DBs."""
    violations = []
    for db_name in TARGET_DBS:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASS,
                dbname=db_name,
            )
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM ir_module_module WHERE state = 'installed'"
            )
            installed = {r[0] for r in cur.fetchall()}

            cur.execute(
                "SELECT bundle, path, directive, active FROM ir_asset"
            )
            asset_map: Dict[Tuple[str, str, str], bool] = {}
            for bundle, path, directive, active in cur.fetchall():
                key = (bundle, path, directive or "append")
                asset_map[key] = bool(asset_map.get(key, False) or active)

            for mod_name in sorted(installed):
                if not is_target_module(mod_name) or mod_name not in manifests:
                    continue
                mod_dir, data = manifests[mod_name]
                assets = data.get("assets", {})
                for bundle in ("web.assets_backend", "web.assets_web_dark"):
                    entries = assets.get(bundle, [])
                    for entry in entries:
                        if not isinstance(entry, str):
                            # Tuple directives ('remove', 'include', 'before', 'after') are
                            # structural Step-2 manifest operations in _fill_asset_paths.
                            continue
                        directive = "append"
                        path = entry

                        if "*" in path and mod_name in ("web_enterprise", "documents"):
                            continue

                        key = (bundle, path, directive)
                        if key not in asset_map:
                            violations.append(
                                {
                                    "category": "C",
                                    "file": f"{mod_name}/__manifest__.py",
                                    "line": 1,
                                    "detail": f"[{db_name}] Missing ir_asset record for ({bundle}, {directive}, {path})",
                                }
                            )
                        elif not asset_map[key]:
                            violations.append(
                                {
                                    "category": "C",
                                    "file": f"{mod_name}/__manifest__.py",
                                    "line": 1,
                                    "detail": f"[{db_name}] Inactive (active=FALSE) ir_asset record for ({bundle}, {directive}, {path})",
                                }
                            )

            explicit_core_assets = [
                ("web.assets_backend", "web_enterprise/static/src/webclient/home_menu/home_menu.scss"),
                ("web.assets_backend", "web_enterprise/static/src/webclient/home_menu/home_menu_background.scss"),
                ("web.assets_backend", "web_enterprise/static/src/webclient/home_menu/home_menu.js"),
                ("web.assets_backend", "web_enterprise/static/src/webclient/home_menu/home_menu.xml"),
                ("web.assets_web_dark", "web_enterprise/static/src/webclient/home_menu/home_menu.dark.scss"),
                ("web.assets_web_dark", "web_enterprise/static/src/webclient/home_menu/home_menu.variables.dark.scss"),
                ("web.assets_web_dark", "web_enterprise/static/src/webclient/home_menu/home_menu_background.dark.scss"),
                ("web.assets_backend", "documents/static/src/views/hooks.js"),
                ("web.assets_backend", "documents/static/src/views/search/documents_search_model.js"),
                ("web.assets_backend", "documents/static/src/views/search/documents_search_panel.js"),
            ]
            for bundle, path in explicit_core_assets:
                key = (bundle, path, "append")
                if not asset_map.get(key, False):
                    violations.append(
                        {
                            "category": "C",
                            "file": path,
                            "line": 1,
                            "detail": f"[{db_name}] Missing or inactive explicit ir_asset record for ({bundle}, append, {path})",
                        }
                    )
            conn.close()
        except Exception as exc:
            violations.append(
                {
                    "category": "C",
                    "file": f"db:{db_name}",
                    "line": 0,
                    "detail": f"Database check error on {db_name}: {exc}",
                }
            )
    return violations


def audit_category_d(manifests: Dict[str, Tuple[Path, dict]]) -> List[dict]:
    """Category D: `.dark.scss` Bundle Segregation & Light Safety Guard."""
    violations = []
    for mod_name, (mod_dir, data) in manifests.items():
        if not is_target_module(mod_name):
            continue
        assets = data.get("assets", {})
        backend_entries = assets.get("web.assets_backend", [])
        dark_entries = assets.get("web.assets_web_dark", [])

        removed_patterns = set()
        backend_globs = []
        for entry in backend_entries:
            if isinstance(entry, (tuple, list)) and len(entry) >= 2:
                if entry[0] == "remove":
                    removed_patterns.add(entry[1])
                else:
                    backend_globs.append(entry[-1])
            elif isinstance(entry, str):
                backend_globs.append(entry)

        # D1: Wildcard glob in web.assets_backend where .dark.scss coexists without removal
        for pattern in backend_globs:
            if "*" not in pattern or not pattern.startswith(mod_name + "/"):
                continue
            rel = pattern[len(mod_name) + 1 :]
            matched_dark = [
                p
                for p in mod_dir.glob(rel)
                if p.is_file() and p.name.endswith(".dark.scss")
            ]
            if matched_dark:
                # Check if removed_patterns covers .dark.scss
                has_remove = any(".dark.scss" in rm for rm in removed_patterns)
                if not has_remove:
                    violations.append(
                        {
                            "category": "D",
                            "file": str((mod_dir / "__manifest__.py").relative_to(ROOT_DIR)),
                            "line": 1,
                            "detail": f"Wildcard `{pattern}` in web.assets_backend matches {[p.name for p in matched_dark]} without explicit exclusion",
                        }
                    )

        # D2: .dark.scss in web.assets_web_dark binding :root, html, body dark tokens without light safety guard
        dark_patterns = []
        for entry in dark_entries:
            if isinstance(entry, (tuple, list)) and len(entry) >= 2 and entry[0] != "remove":
                dark_patterns.append(entry[-1])
            elif isinstance(entry, str):
                dark_patterns.append(entry)

        for pattern in dark_patterns:
            if not pattern.startswith(mod_name + "/"):
                continue
            rel = pattern[len(mod_name) + 1 :]
            for fpath in sorted(mod_dir.glob(rel)):
                if not fpath.is_file() or not fpath.name.endswith(".dark.scss"):
                    continue
                content = strip_comments(fpath.read_text(encoding="utf-8", errors="ignore"))
                binds_root = bool(
                    re.search(r"(:root|\bhtml\b|\bbody\b)[^{]*\{[^}]*--insilos-", content, re.DOTALL)
                )
                if binds_root:
                    has_light_guard = (
                        'data-theme="light"' in content
                        or "data-theme='light'" in content
                        or "not(.o_dark_mode)" in content
                    )
                    if not has_light_guard:
                        violations.append(
                            {
                                "category": "D",
                                "file": str(fpath.relative_to(ROOT_DIR)),
                                "line": 1,
                                "detail": "`.dark.scss` binds `:root/html/body` `--insilos-*` variables without a `html[data-theme=\"light\"] body:not(.o_dark_mode)` safety guard",
                            }
                        )
    return violations


def audit_category_e(manifests: Dict[str, Tuple[Path, dict]]) -> List[dict]:
    """Category E: OWL 2 / OWL 3 & ORM View/Table Refactoring Traps."""
    violations = []

    # E1: Check that @insilos/owl App.mount / makeRefProxy or component rootRef bridges t-ref="root"
    owl_patch_path = ROOT_DIR / "addons/web/static/src/owl2_compatibility/app.js"
    if owl_patch_path.exists():
        owl_patch_text = owl_patch_path.read_text(encoding="utf-8", errors="ignore")
        if "makeRefProxy" not in owl_patch_text:
            violations.append(
                {
                    "category": "E",
                    "file": str(owl_patch_path.relative_to(ROOT_DIR)),
                    "line": 1,
                    "detail": "Missing `makeRefProxy` OWL 2/3 compatibility bridge in `owl2_compatibility/app.js`",
                }
            )

    # Scan Python files in addons/ and enterprise/ for E2 and E3
    for base in ADDONS_DIRS:
        if not base.exists():
            continue
        for py_file in sorted(base.rglob("*.py")):
            rel_str = str(py_file.relative_to(ROOT_DIR))
            text = py_file.read_text(encoding="utf-8", errors="ignore")

            # E2: Direct CREATE INDEX on res_partner without checking relkind = 'v' or party_master
            if "CREATE INDEX" in text.upper() and "res_partner" in text:
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if re.search(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b.*?\bON\s+res_partner\b", line, re.IGNORECASE):
                        if "relkind" not in text and "party_master" not in text and "to_regclass" not in text:
                            violations.append(
                                {
                                    "category": "E",
                                    "file": rel_str,
                                    "line": lineno,
                                    "detail": f"Direct `CREATE INDEX ON res_partner` without view (`relkind = 'v'`) guard: `{line.strip()}`",
                                }
                            )

            # E3: Unqualified SQL('id') / SQL('move_id') / SQL('order_id') inside def _get_count_id
            if "def _get_count_id" in text:
                match = re.search(
                    r"def\s+_get_count_id\s*\([^)]*\)\s*:(.+?)(?=\n    def\s+|\Z)",
                    text,
                     flags=re.DOTALL,
                )
                if match:
                    body = match.group(1)
                    unqualified = re.search(
                        r"""SQL\(\s*['"](?:id|move_id|order_id)['"]\s*\)""", body
                    )
                    if unqualified:
                        lineno = text[: match.start() + unqualified.start()].count("\n") + 1
                        violations.append(
                            {
                                "category": "E",
                                "file": rel_str,
                                "line": lineno,
                                "detail": f"Unqualified `{unqualified.group(0)}` in `_get_count_id` (must use `self._table_sql` qualification)",
                            }
                        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit systemic theme, ir_asset, SCSS, and OWL/ORM refactoring risks."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status code if any Category A-E violations are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output audit report in JSON format.",
    )
    args = parser.parse_args()

    manifests = load_manifests()
    cat_a = audit_category_a(manifests)
    cat_b = audit_category_b(manifests)
    cat_c = audit_category_c(manifests)
    cat_d = audit_category_d(manifests)
    cat_e = audit_category_e(manifests)

    all_violations = cat_a + cat_b + cat_c + cat_d + cat_e

    summary = {
        "Category A (Light-Bundle Dark Leak)": len(cat_a),
        "Category B (Dark-Mode Bare White Surface Leak)": len(cat_b),
        "Category C (__manifest__.py <-> ir_asset Drift)": len(cat_c),
        "Category D (.dark.scss Segregation & Light Guard)": len(cat_d),
        "Category E (OWL 2/3 & ORM View/Table Traps)": len(cat_e),
        "total_violations": len(all_violations),
    }

    if args.json:
        print(json.dumps({"summary": summary, "violations": all_violations}, indent=2))
    else:
        print("=" * 76)
        print("INSILOS ODOO 20 SYSTEMIC REFACTOR & ASSET BUNDLE RISK AUDIT")
        print("=" * 76)
        for k, v in summary.items():
            if k == "total_violations":
                continue
            status = "PASS (0 violations)" if v == 0 else f"FAIL ({v} violations)"
            print(f"  - {k:<50} : {status}")
        print("-" * 76)
        if all_violations:
            for item in all_violations:
                print(
                    f"  [Cat {item['category']}] {item['file']}:{item['line']} -> {item['detail']}"
                )
            print("-" * 76)
        print(f"TOTAL VIOLATIONS: {len(all_violations)}")
        print("=" * 76)

    if args.strict and all_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
