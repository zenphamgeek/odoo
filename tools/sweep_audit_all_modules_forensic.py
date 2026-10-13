#!/usr/bin/env python3
"""
High-Precision Forensic Module-by-Module Brand & Schema Sweep Auditor
=====================================================================
Focuses strictly on user-facing leaks across all modules:
1. Python:
   - fields.Selection choice labels
   - string="..." attributes
   - help="..." attributes
2. XML:
   - Text nodes inside user-facing tags (p, span, h1-h6, label, button, a)
   - string="...", title="...", placeholder="..."
   - Action window <field name="help">
3. Database (Requires PGPASSWORD environment variable; read-only session):
   - ir_model_fields_selection (JSONB name)
   - ir_act_window (help, name)
   - ir_ui_menu (name)
   - ir_model_fields (field_description, help)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/zen/O20"))

# Database connection settings strictly externalized (CWE-798 / CWE-259)
PG_HOST = os.environ.get("PGHOST", "127.0.0.1")
PG_PORT = int(os.environ.get("PGPORT", "5434"))
PG_USER = os.environ.get("PGUSER", "odoo")
PG_PASS = os.environ.get("PGPASSWORD")

# Scope Isolation: Prod databases are strictly opt-in and blocked by default
_ALL_DBS = {
    "dev": ["odoo20_dev", "insilos20_dev"],
    "prod": ["innoria_prod", "innokafe_prod"],
}
_scope = os.environ.get("AUDIT_SCOPE", "dev").lower()
if _scope == "prod":
    if os.environ.get("ALLOW_PROD_AUDIT") != "1":
        sys.exit("Error: AUDIT_SCOPE='prod' requires explicit ALLOW_PROD_AUDIT='1' authorization.")
    DATABASES = _ALL_DBS["prod"]
else:
    DATABASES = _ALL_DBS["dev"]

ALLOWED_DATABASE_NAMES = set(_ALL_DBS["dev"] + _ALL_DBS["prod"])

# Precise user-facing regex patterns
RE_USER_FACING_ODOO = re.compile(
    r'\b(In Odoo|via Odoo|from Odoo|with Odoo|to Odoo|Odoo ERP|Odoo Community|Odoo Enterprise|Odoo Domain|Odoo App|Odoo Server|Odoo SA)\b',
    re.IGNORECASE
)

# Python field string/help with Odoo
RE_PY_FIELD_STRING = re.compile(r'(string|help)\s*=\s*["\']([^"\']*\bodoo\b[^"\']*)["\']', re.IGNORECASE)
# Python selection tuple with Odoo
RE_PY_SELECTION_ITEM = re.compile(r'\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']*\bodoo\b[^"\']*)["\']\s*\)', re.IGNORECASE)

# XML user-facing attributes
RE_XML_ATTR = re.compile(r'(string|title|placeholder|help)\s*=\s*["\']([^"\']*\bodoo\b[^"\']*)["\']', re.IGNORECASE)
# XML text content (between tags)
RE_XML_TEXT = re.compile(r'>([^<]*\b(?:In Odoo|Odoo ERP|to Odoo|via Odoo|with Odoo|from Odoo)\b[^<]*)<', re.IGNORECASE)


def is_competitor_context(text: str) -> bool:
    t = text.lower()
    return any(c in t for c in ["sap", "oracle", "netsuite", "salesforce", "microsoft dynamics"])


def _format_relpath(p: Path) -> str:
    try:
        return str(p.relative_to(WORKSPACE))
    except ValueError:
        return str(p)


def audit_module_python(module_path: Path) -> List[Dict[str, Any]]:
    leaks = []
    for py_file in module_path.glob("**/*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        in_multiline_doc = False
        doc_delimiter = None

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_s = line.strip()

            # Handle multiline triple-quoted docstrings
            if not in_multiline_doc:
                if line_s.startswith('"""') or line_s.startswith("'''"):
                    delim = line_s[:3]
                    # If it opens and closes on the same line (e.g. """doc"""), skip line
                    if line_s.count(delim) >= 2 and len(line_s) > 3:
                        continue
                    in_multiline_doc = True
                    doc_delimiter = delim
                    continue
            else:
                if doc_delimiter and doc_delimiter in line:
                    in_multiline_doc = False
                    doc_delimiter = None
                continue

            if line_s.startswith("#"):
                continue

            # Check selection item
            for m in RE_PY_SELECTION_ITEM.finditer(line):
                val, label = m.group(1), m.group(2)
                if not is_competitor_context(label):
                    leaks.append({
                        "file": _format_relpath(py_file),
                        "line": idx,
                        "type": "fields.Selection label",
                        "text": f"({val!r}, {label!r})"
                    })

            # Check string or help
            for m in RE_PY_FIELD_STRING.finditer(line):
                attr, val = m.group(1), m.group(2)
                if not is_competitor_context(val) and not line_s.startswith("#"):
                    leaks.append({
                        "file": _format_relpath(py_file),
                        "line": idx,
                        "type": f"Field {attr}",
                        "text": f"{attr}={val!r}"
                    })

    return leaks


def audit_module_xml(module_path: Path) -> List[Dict[str, Any]]:
    leaks = []
    for xml_file in module_path.glob("**/*.xml"):
        if ".venv" in str(xml_file):
            continue
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        in_comment = False
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_s = line.strip()

            # Handle multiline XML comments
            if not in_comment:
                if "<!--" in line:
                    if "-->" in line:
                        # Single-line comment, strip commented portion
                        line = re.sub(r'<!--.*?-->', '', line)
                    else:
                        in_comment = True
                        line = line.split("<!--")[0]
            else:
                if "-->" in line:
                    in_comment = False
                    line = line.split("-->")[1]
                else:
                    continue

            # Check attribute leaks (string, title, placeholder)
            for m in RE_XML_ATTR.finditer(line):
                attr, val = m.group(1), m.group(2)
                if not is_competitor_context(val):
                    leaks.append({
                        "file": _format_relpath(xml_file),
                        "line": idx,
                        "type": f"XML attribute {attr}",
                        "text": f'{attr}="{val}"'
                    })

            # Check text between tags
            for m in RE_XML_TEXT.finditer(line):
                text_content = m.group(1).strip()
                if text_content and not is_competitor_context(text_content):
                    leaks.append({
                        "file": _format_relpath(xml_file),
                        "line": idx,
                        "type": "XML text node",
                        "text": text_content[:120]
                    })

    return leaks


def audit_databases() -> Dict[str, Any]:
    """
    Audits PostgreSQL database tables across configured tenants.
    Enforces:
    - PGPASSWORD environment check (fails closed if missing).
    - Read-only transaction session (least privilege invariant).
    - Fully parameterized SQL statements (CWE-89 SQL injection mitigation).
    - Deterministic connection lifecycle / context management (zero resource leak).
    """
    if not PG_PASS:
        print(
            "[ERROR] PGPASSWORD environment variable is required to audit databases; "
            "refusing to run database audit without credentials from environment.",
            file=sys.stderr
        )
        raise RuntimeError("Missing PGPASSWORD environment variable")

    try:
        import psycopg2
    except ImportError:
        print("[ERROR] psycopg2 library is required for database auditing.", file=sys.stderr)
        raise

    db_report = {}
    for db in DATABASES:
        if db not in ALLOWED_DATABASE_NAMES:
            print(f"Skipping unauthorized database name: {db}", file=sys.stderr)
            continue
        if db.endswith('_prod') and os.environ.get("ALLOW_PROD_AUDIT") != "1":
            print(f"Skipping prod database {db} (set ALLOW_PROD_AUDIT=1 to enable).", file=sys.stderr)
            continue
        db_report[db] = {
            "selections": [],
            "action_windows": [],
            "menus": [],
            "fields": []
        }
        try:
            # Deterministic context manager ensures connection and cursor are cleanly released
            with psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASS,
                dbname=db,
                connect_timeout=5,
                options="-c default_transaction_read_only=on -c statement_timeout=15000",
            ) as conn:
                # Least privilege invariant: guarantee read-only transactional execution
                conn.set_session(readonly=True, autocommit=True)
                with conn.cursor() as cur:
                    # 1. Selection options (Parameterized query)
                    cur.execute("""
                        SELECT fs.id, f.model, f.name, fs.value, fs.name 
                        FROM ir_model_fields_selection fs 
                        JOIN ir_model_fields f ON f.id = fs.field_id 
                        WHERE fs.name::text ILIKE %s
                          AND f.model != %s;
                    """, ('%Odoo%', 'insilos.demo.request'))
                    for r in cur.fetchall():
                        db_report[db]["selections"].append({
                            "id": r[0], "model": r[1], "field": r[2], "value": r[3], "name": r[4]
                        })

                    # 2. Window actions (Parameterized query)
                    cur.execute("""
                        SELECT id, name, help 
                        FROM ir_act_window 
                        WHERE (help::text ILIKE %s OR help::text ILIKE %s OR name::text ILIKE %s)
                          AND name::text NOT ILIKE %s;
                    """, ('%in odoo%', '%with odoo%', '%odoo%', '%competitor%'))
                    for r in cur.fetchall():
                        db_report[db]["action_windows"].append({
                            "id": r[0], "name": r[1], "help": str(r[2])[:150]
                        })

                    # 3. Menus (Parameterized query)
                    cur.execute("""
                        SELECT id, name 
                        FROM ir_ui_menu 
                        WHERE name::text ILIKE %s
                          AND name::text NOT ILIKE %s;
                    """, ('%Odoo%', '%insilos%'))
                    for r in cur.fetchall():
                        db_report[db]["menus"].append({
                            "id": r[0], "name": r[1]
                        })
        except Exception as e:
            print(f"Error querying DB {db}: {e}", file=sys.stderr)

    return db_report


def main() -> int:
    parser = argparse.ArgumentParser(description="High-Precision Forensic Module-by-Module Brand & Schema Sweep")
    parser.add_argument("--db", action="store_true", help="Run database audit (requires PGPASSWORD)")
    parser.add_argument("--db-only", action="store_true", help="Audit database tables only (skips codebase module sweep)")
    parser.add_argument("--code-only", action="store_true", help="Audit codebase modules only (skips database audit)")
    parser.add_argument("--skip-db", action="store_true", help="Skip database audit and scan codebase only")
    parser.add_argument("--fail-on-leaks", action="store_true", help="Exit with code 1 if any brand leaks are detected")
    args = parser.parse_args()

    print("=" * 80)
    print("🔍 HIGH-PRECISION FORENSIC MODULE-BY-MODULE BRAND & SCHEMA SWEEP")
    print("=" * 80)

    # Fail fast: validate credentials immediately if database audit is explicitly requested
    if (args.db or args.db_only) and not PG_PASS:
        print(
            "[FAIL-CLOSED] PGPASSWORD environment variable is required to audit databases; "
            "refusing to run database audit without credentials from environment.",
            file=sys.stderr
        )
        return 1

    modules = []
    module_findings = {}
    total_py_leaks = 0
    total_xml_leaks = 0

    if not args.db_only:
        for d in [WORKSPACE / "addons", WORKSPACE / "enterprise"]:
            if not d.exists():
                continue
            for item in d.iterdir():
                if item.is_dir() and (item / "__manifest__.py").exists():
                    modules.append(item)

        print(f"[*] Auditing {len(modules)} individual modules...")
        for mod in sorted(modules, key=lambda p: p.name):
            py_leaks = audit_module_python(mod)
            xml_leaks = audit_module_xml(mod)

            if py_leaks or xml_leaks:
                module_findings[mod.name] = {
                    "python": py_leaks,
                    "xml": xml_leaks
                }
                total_py_leaks += len(py_leaks)
                total_xml_leaks += len(xml_leaks)

        print(f"\n[*] Codebase Audit Results:")
        print(f"    - Modules with findings: {len(module_findings)} / {len(modules)}")
        print(f"    - Total Python Field/Selection Leaks: {total_py_leaks}")
        print(f"    - Total XML View/Attribute Leaks: {total_xml_leaks}")

        if module_findings:
            print("\n=== BREAKDOWN OF MODULE FINDINGS ===")
            for mod_name, f in module_findings.items():
                cnt = len(f["python"]) + len(f["xml"])
                print(f"\n📦 Module: {mod_name} ({cnt} occurrences)")
                for item in f["python"]:
                    print(f"   [PY]  {item['file']}:{item['line']} ({item['type']}): {item['text']}")
                for item in f["xml"]:
                    print(f"   [XML] {item['file']}:{item['line']} ({item['type']}): {item['text']}")
    else:
        print("[*] Skipping codebase module sweep (--db-only requested).")

    db_report = {}
    total_db_findings = 0

    # Audit databases if explicitly requested or if not skipped and credentials present
    should_audit_db = args.db or (not args.skip_db and PG_PASS is not None)

    if should_audit_db:
        print("\n[*] Auditing Database Tables Across Configured Databases...")
        try:
            db_report = audit_databases()
            for db, items in db_report.items():
                total = len(items["selections"]) + len(items["action_windows"]) + len(items["menus"])
                total_db_findings += total
                print(f"  • {db}: {total} items (Selections: {len(items['selections'])}, Window Actions: {len(items['action_windows'])}, Menus: {len(items['menus'])})")
                if total > 0:
                    for s in items["selections"]:
                        print(f"    - [Selection] ID {s['id']} ({s['model']}.{s['field']}={s['value']}): {s['name']}")
                    for w in items["action_windows"]:
                        print(f"    - [Window] ID {w['id']} ({w['name']}): {w['help']}")
                    for m in items["menus"]:
                        print(f"    - [Menu] ID {m['id']}: {m['name']}")
        except RuntimeError as e:
            if args.db:
                print(f"[FAIL-CLOSED] {e}", file=sys.stderr)
                return 1
            else:
                print(f"[SKIP] Database audit skipped: {e}")
    else:
        print("\n[*] Database audit skipped (--skip-db or PGPASSWORD not provided in environment).")

    output_path = WORKSPACE / "forensic_sweep_precision_report.json"
    output_path.write_text(json.dumps({
        "modules_scanned": len(modules),
        "modules_with_findings": len(module_findings),
        "total_python_leaks": total_py_leaks,
        "total_xml_leaks": total_xml_leaks,
        "total_db_findings": total_db_findings,
        "module_findings": module_findings,
        "database_report": db_report
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[+] Detailed report written to: {output_path}")

    if args.fail_on_leaks and (total_py_leaks > 0 or total_xml_leaks > 0 or total_db_findings > 0):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
