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
3. Database:
   - ir_model_fields_selection (JSONB name)
   - ir_act_window (help, name)
   - ir_ui_menu (name)
   - ir_model_fields (field_description, help)
"""

import os
import sys
import re
import json
import psycopg2
from pathlib import Path

WORKSPACE = Path("/home/zen/O20")
DATABASES = ["odoo20_dev", "insilos20_dev", "innoria_prod", "innokafe_prod"]
PG_HOST = "127.0.0.1"
PG_PORT = 5434
PG_USER = "odoo"
PG_PASS = "1NN0R1@2026"

# Precise user-facing regex patterns
RE_USER_FACING_ODOO = re.compile(r'\b(In Odoo|via Odoo|from Odoo|with Odoo|to Odoo|Odoo ERP|Odoo Community|Odoo Enterprise|Odoo Domain|Odoo App|Odoo Server|Odoo SA)\b', re.IGNORECASE)

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

def audit_module_python(module_path: Path):
    leaks = []
    for py_file in module_path.glob("**/*.py"):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_s = line.strip()
            if line_s.startswith("#") or line_s.startswith('"""') or line_s.startswith("'''"):
                continue

            # Check selection item
            for m in RE_PY_SELECTION_ITEM.finditer(line):
                val, label = m.group(1), m.group(2)
                if not is_competitor_context(label):
                    leaks.append({
                        "file": str(py_file.relative_to(WORKSPACE)),
                        "line": idx,
                        "type": "fields.Selection label",
                        "text": f"({val!r}, {label!r})"
                    })

            # Check string or help
            for m in RE_PY_FIELD_STRING.finditer(line):
                attr, val = m.group(1), m.group(2)
                if not is_competitor_context(val) and not line_s.startswith("#"):
                    leaks.append({
                        "file": str(py_file.relative_to(WORKSPACE)),
                        "line": idx,
                        "type": f"Field {attr}",
                        "text": f"{attr}={val!r}"
                    })

    return leaks

def audit_module_xml(module_path: Path):
    leaks = []
    for xml_file in module_path.glob("**/*.xml"):
        if ".venv" in str(xml_file):
            continue
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_s = line.strip()
            if line_s.startswith("<!--"):
                continue

            # Check attribute leaks (string, title, placeholder)
            for m in RE_XML_ATTR.finditer(line):
                attr, val = m.group(1), m.group(2)
                if not is_competitor_context(val):
                    leaks.append({
                        "file": str(xml_file.relative_to(WORKSPACE)),
                        "line": idx,
                        "type": f"XML attribute {attr}",
                        "text": f'{attr}="{val}"'
                    })

            # Check text between tags
            for m in RE_XML_TEXT.finditer(line):
                text_content = m.group(1).strip()
                if text_content and not is_competitor_context(text_content):
                    leaks.append({
                        "file": str(xml_file.relative_to(WORKSPACE)),
                        "line": idx,
                        "type": "XML text node",
                        "text": text_content[:120]
                    })

    return leaks

def audit_databases():
    db_report = {}
    for db in DATABASES:
        db_report[db] = {
            "selections": [],
            "action_windows": [],
            "menus": [],
            "fields": []
        }
        try:
            conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, dbname=db)
            cur = conn.cursor()

            # 1. Selection options
            cur.execute("""
                SELECT fs.id, f.model, f.name, fs.value, fs.name 
                FROM ir_model_fields_selection fs 
                JOIN ir_model_fields f ON f.id = fs.field_id 
                WHERE fs.name::text ILIKE '%Odoo%'
                  AND f.model != 'insilos.demo.request';
            """)
            for r in cur.fetchall():
                db_report[db]["selections"].append({
                    "id": r[0], "model": r[1], "field": r[2], "value": r[3], "name": r[4]
                })

            # 2. Window actions
            cur.execute("""
                SELECT id, name, help 
                FROM ir_act_window 
                WHERE (help::text ILIKE '%in odoo%' OR help::text ILIKE '%with odoo%' OR name::text ILIKE '%odoo%')
                  AND name::text NOT ILIKE '%competitor%';
            """)
            for r in cur.fetchall():
                db_report[db]["action_windows"].append({
                    "id": r[0], "name": r[1], "help": str(r[2])[:150]
                })

            # 3. Menus
            cur.execute("""
                SELECT id, name 
                FROM ir_ui_menu 
                WHERE name::text ILIKE '%Odoo%'
                  AND name::text NOT ILIKE '%insilos%';
            """)
            for r in cur.fetchall():
                db_report[db]["menus"].append({
                    "id": r[0], "name": r[1]
                })

            conn.close()
        except Exception as e:
            print(f"Error querying DB {db}: {e}", file=sys.stderr)

    return db_report

def main():
    print("=" * 80)
    print("🔍 HIGH-PRECISION FORENSIC MODULE-BY-MODULE BRAND & SCHEMA SWEEP")
    print("=" * 80)

    modules = []
    for d in [WORKSPACE / "addons", WORKSPACE / "enterprise"]:
        if not d.exists():
            continue
        for item in d.iterdir():
            if item.is_dir() and (item / "__manifest__.py").exists():
                modules.append(item)

    print(f"[*] Auditing {len(modules)} individual modules...")
    module_findings = {}
    total_py_leaks = 0
    total_xml_leaks = 0

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

    print("\n[*] Auditing Database Tables Across 4 Databases...")
    db_report = audit_databases()

    total_db_findings = 0
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
    return 0

if __name__ == "__main__":
    sys.exit(main())
