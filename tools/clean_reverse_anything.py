#!/usr/bin/env python3
"""
clean_reverse_anything.py
=============================================================================
Reverse Engineer Anything (REA) & Sovereign Clean-Room Re-Engineering Engine
=============================================================================
Deconstructs, disassembles, and reverse-engineers binaries (.so, .elf, .wasm),
Python bytecode (.pyc), minified web bundles, and legacy enterprise modules.
Applies the Hegelian Dialectic (Thesis -> Antithesis -> Synthesis) to produce
pristine, schema-invariant, zero-genesis, OWL 2/Carbon-compliant sovereign code.
=============================================================================
"""

import os
import sys
import json
import dis
import marshal
import hashlib
import re
import argparse
import subprocess
import shutil
from typing import Dict, Any, List, Optional, Tuple


class TargetType:
    PYC = "python_bytecode"
    ELF_SO = "elf_shared_object"
    WASM = "webassembly"
    JS_BUNDLE = "javascript_bundle"
    QWEB_XML = "qweb_template"
    SCSS_CSS = "scss_stylesheet"
    UNKNOWN = "unknown_binary"


def detect_target_type(filepath: str) -> str:
    """Detect file format via magic bytes and extensions."""
    if not os.path.exists(filepath):
        return TargetType.UNKNOWN

    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == ".pyc":
        return TargetType.PYC
    elif ext in (".so", ".elf", ".bin"):
        return TargetType.ELF_SO
    elif ext == ".wasm":
        return TargetType.WASM
    elif ext in (".js", ".mjs"):
        return TargetType.JS_BUNDLE
    elif ext in (".xml", ".qweb"):
        return TargetType.QWEB_XML
    elif ext in (".scss", ".css"):
        return TargetType.SCSS_CSS

    # Check magic bytes
    try:
        with open(filepath, "rb") as f:
            magic = f.read(16)
            if magic.startswith(b"\x7fELF"):
                return TargetType.ELF_SO
            elif magic.startswith(b"\x00asm"):
                return TargetType.WASM
            elif len(magic) >= 4 and magic[2:4] == b"\r\n":
                return TargetType.PYC
    except Exception:
        pass

    return TargetType.UNKNOWN


# =============================================================================
# 1. THESIS: Deconstruction & Extraction Engine
# =============================================================================

def deconstruct_pyc(filepath: str) -> Dict[str, Any]:
    """Deconstruct Python .pyc bytecode file into code objects, opcodes and symbols."""
    with open(filepath, "rb") as f:
        # Python 3.7+ pyc header is 16 bytes: 4 bytes magic, 4 bytes flags, 8 bytes timestamp/size or hash
        header = f.read(16)
        code_obj = marshal.load(f)

    disassembled_lines = []
    constants = []
    varnames = list(code_obj.co_varnames)
    names = list(code_obj.co_names)

    for instr in dis.get_instructions(code_obj):
        disassembled_lines.append({
            "offset": instr.offset,
            "opname": instr.opname,
            "opcode": instr.opcode,
            "arg": instr.arg,
            "argval": str(instr.argval),
            "argrepr": instr.argrepr
        })

    for c in code_obj.co_consts:
        if isinstance(c, (str, int, float, bool, bytes)) or c is None:
            constants.append(str(c))
        elif hasattr(c, "co_name"):
            constants.append(f"<code_object: {c.co_name}>")

    return {
        "format": TargetType.PYC,
        "co_name": code_obj.co_name,
        "co_filename": code_obj.co_filename,
        "names": names,
        "varnames": varnames,
        "constants": constants,
        "instruction_count": len(disassembled_lines),
        "disassembly_preview": disassembled_lines[:50]
    }


def deconstruct_elf_so(filepath: str) -> Dict[str, Any]:
    """Deconstruct ELF shared library (.so) using readelf, nm, and strings."""
    result: Dict[str, Any] = {
        "format": TargetType.ELF_SO,
        "symbols": [],
        "dependencies": [],
        "strings_sample": []
    }

    # Extract dynamic symbols via nm or readelf
    if shutil.which("nm"):
        proc = subprocess.run(["nm", "-D", filepath], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            lines = proc.stdout.splitlines()
            result["symbols"] = [l.strip() for l in lines[:100]]

    # Extract dynamic dependencies via readelf
    if shutil.which("readelf"):
        proc = subprocess.run(["readelf", "-d", filepath], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if "NEEDED" in line:
                    result["dependencies"].append(line.strip())

    # Extract strings
    if shutil.which("strings"):
        proc = subprocess.run(["strings", "-n", "6", filepath], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            lines = [l.strip() for l in proc.stdout.splitlines() if len(l.strip()) >= 6]
            result["strings_sample"] = lines[:80]

    return result


def deconstruct_js_bundle(filepath: str) -> Dict[str, Any]:
    """Analyze JavaScript bundle, extract string literals, exports, and potential APIs."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Detect strings
    string_pat = re.compile(r'["\']([^"\'\\]{4,100})["\']')
    strings = list(set(string_pat.findall(content)))

    # Detect exports / classes / functions
    fn_pat = re.compile(r'(?:function\s+([a-zA-Z0-9_$]+)|class\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:function|\()|\b([a-zA-Z0-9_$]+)\s*:\s*function)')
    identifiers = set()
    for m in fn_pat.finditer(content):
        for g in m.groups():
            if g:
                identifiers.add(g)

    # Detect legacy jQuery or Widget usage
    has_jquery = bool(re.search(r'\$\([\'"].*?[\'"]\)', content) or 'jQuery' in content)
    has_legacy_widget = bool('Widget.extend' in content or 'owl.Component' not in content and 'Component' in content)

    return {
        "format": TargetType.JS_BUNDLE,
        "size_bytes": len(content),
        "string_count": len(strings),
        "sample_strings": strings[:60],
        "extracted_identifiers": list(identifiers)[:60],
        "indicators": {
            "has_jquery": has_jquery,
            "has_legacy_widget": has_legacy_widget,
            "has_owl2": bool("@web/core" in content or "useState" in content or "useSubEnv" in content)
        }
    }


def deconstruct_qweb_or_scss(filepath: str, ftype: str) -> Dict[str, Any]:
    """Deconstruct QWeb XML template or SCSS stylesheet."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if ftype == TargetType.QWEB_XML:
        templates = re.findall(r'<t\s+t-name=["\']([^"\']+)["\']', content)
        xpaths = re.findall(r'<xpath\s+expr=["\']([^"\']+)["\']', content)
        field_names = re.findall(r'<field\s+name=["\']([^"\']+)["\']', content)
        return {
            "format": TargetType.QWEB_XML,
            "template_names": templates,
            "xpath_expressions": xpaths,
            "fields_referenced": list(set(field_names))
        }
    else:
        # SCSS
        classes = re.findall(r'\.([a-zA-Z0-9_-]{3,})', content)
        css_vars = re.findall(r'var\((--[a-zA-Z0-9_-]+)', content)
        hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b', content)
        return {
            "format": TargetType.SCSS_CSS,
            "class_count": len(classes),
            "css_variables_used": list(set(css_vars)),
            "hardcoded_hex_colors": list(set(hex_colors))
        }


# =============================================================================
# 2. ANTITHESIS: Adversarial Audit & Invariant Checker
# =============================================================================

def audit_antithesis(target_data: Dict[str, Any], filepath: str) -> Dict[str, Any]:
    """
    Evaluates the deconstructed target against Sovereign Invariants:
    1. Schema Invariance (0 DDL)
    2. Counter Code Security (Zero Genesis)
    3. Anti-Slop & Design Tokens (Zero Bare Surfaces, Carbon/Fiori)
    4. Modern OWL 2 Lifecycle
    """
    violations = []
    warnings = []

    # Read raw content if text
    raw_text = ""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
    except Exception:
        pass

    # 1. Counter-Code Invariant: Brand Leaks
    genesis_pat = re.compile(r'\b(odoo|odoobot|odoo-community|odoo_enterprise)\b', re.IGNORECASE)
    brand_matches = genesis_pat.findall(raw_text)
    if brand_matches:
        violations.append({
            "rule": "Counter Code Security Invariance",
            "severity": "CRITICAL",
            "message": f"Detected {len(brand_matches)} legacy brand references ({set(brand_matches)}). Must be sanitized to 'insilos'."
        })

    # 2. Schema Invariance: DDL Mutations in Python / SQL
    ddl_pat = re.compile(r'\b(CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE|ADD\s+COLUMN|DROP\s+COLUMN)\b', re.IGNORECASE)
    ddl_matches = ddl_pat.findall(raw_text)
    if ddl_matches:
        violations.append({
            "rule": "Strict Database Schema Invariance",
            "severity": "CRITICAL",
            "message": f"Forbidden DDL statements detected: {set(ddl_matches)}. Must use read-only queries or existing ORM fields."
        })

    # 3. Anti-Slop SCSS: Bare White Surfaces & Hex Fallbacks
    if target_data.get("format") == TargetType.SCSS_CSS or filepath.endswith((".scss", ".css")):
        bare_white_pat = re.compile(r'(?:background(?:-color)?)\s*:\s*(?:#ffffff|#fff|#f8fafc|#f4f6f8)\b', re.IGNORECASE)
        if bare_white_pat.search(raw_text):
            violations.append({
                "rule": "Zero Bare White Surfaces",
                "severity": "HIGH",
                "message": "Hardcoded bare white surface found. Must use semantic tokens (var(--insilos-bg-canvas), var(--insilos-bg-card))."
            })

        fallback_important_pat = re.compile(r'var\([^)]+,\s*#[0-9a-fA-F]+\)\s*!important')
        if fallback_important_pat.search(raw_text):
            violations.append({
                "rule": "Banned Hex Fallbacks with !important",
                "severity": "HIGH",
                "message": "Banned hex fallback coupled with !important detected. Semantic tokens must be guaranteed at root."
            })

    # 4. OWL 2 Lifecycle: Legacy Widget / jQuery Mutation
    if target_data.get("format") == TargetType.JS_BUNDLE or filepath.endswith(".js"):
        if target_data.get("indicators", {}).get("has_jquery"):
            warnings.append({
                "rule": "OWL 2 Reactive Lifecycle",
                "severity": "MEDIUM",
                "message": "Direct jQuery DOM manipulation detected. Refactor to reactive OWL 2 hooks (useState, useRef)."
            })
        if target_data.get("indicators", {}).get("has_legacy_widget"):
            violations.append({
                "rule": "Zero Legacy Widgets",
                "severity": "HIGH",
                "message": "Legacy Widget architecture detected. Must convert to OWL 2 Component."
            })

    # 5. Sensitive credentials / private keys
    key_pat = re.compile(r'-----BEGIN\s+(?:RSA|OPENSSH|EC)?\s*PRIVATE\s+KEY-----')
    if key_pat.search(raw_text):
        violations.append({
            "rule": "Zero Private Key Exposure",
            "severity": "CRITICAL",
            "message": "Hardcoded private key detected in target asset!"
        })

    return {
        "status": "FAIL" if any(v["severity"] == "CRITICAL" for v in violations) else ("WARN" if violations else "PASS"),
        "violations_count": len(violations),
        "violations": violations,
        "warnings_count": len(warnings),
        "warnings": warnings
    }


# =============================================================================
# 3. SYNTHESIS: Clean-Room Refactor Generator
# =============================================================================

def generate_synthesis_spec(target_data: Dict[str, Any], audit_result: Dict[str, Any], target_file: str) -> Dict[str, Any]:
    """Generates the clean-room re-architecture plan and template specifications."""
    fmt = target_data.get("format", TargetType.UNKNOWN)
    base_name = os.path.basename(target_file)

    refactor_plan: Dict[str, Any] = {
        "target_file": target_file,
        "target_type": fmt,
        "remediation_actions": [],
        "architecture_blueprint": {}
    }

    if fmt == TargetType.PYC:
        refactor_plan["remediation_actions"] = [
            "Decompile bytecode to pure Python 3.12 syntax with type annotations",
            "Ensure 0 DDL migrations on PostgreSQL (schema invariance)",
            "Scrub all legacy namespace references to insilos.*",
            "Implement unit test suite with mock DB fixtures"
        ]
        refactor_plan["architecture_blueprint"] = {
            "module_type": "Odoo 20 Model Extension",
            "model_pattern": "class ModelExtension(models.Model): _inherit = 'target.model'",
            "schema_contract": "Strict Invariance (0 column renames, 0 table mutations)"
        }

    elif fmt == TargetType.JS_BUNDLE or target_file.endswith(".js"):
        refactor_plan["remediation_actions"] = [
            "Convert DOM/Widget routines to OWL 2 reactive Component",
            "Bind state reactively with useState and useSubEnv",
            "Register component in registry.category('actions') or 'views'",
            "Author modern HOOT unit tests in static/tests/"
        ]
        refactor_plan["architecture_blueprint"] = {
            "component_standard": "OWL 2 Reactive Component (Component, useState, xml)",
            "ui_token_binding": "IBM Carbon 11 & SAP Fiori Horizon variables",
            "test_framework": "OWL 2 HOOT Runner (run_hoot.js)"
        }

    elif fmt in (TargetType.SCSS_CSS, TargetType.QWEB_XML):
        refactor_plan["remediation_actions"] = [
            "Eliminate bare white backgrounds and replace with var(--insilos-bg-*)",
            "Register dual dark mode bundle under web.assets_web_dark in __manifest__.py",
            "Enforce WCAG AAA contrast ratio (>= 7:1) across all text elements",
            "Wrap XML view additions in <odoo noupdate='1'> where applicable"
        ]
        refactor_plan["architecture_blueprint"] = {
            "design_system": "IBM Carbon 11 / SAP Fiori Horizon",
            "dark_mode_tokens": [
                "var(--insilos-bg-canvas)",
                "var(--insilos-bg-surface)",
                "var(--insilos-bg-card)",
                "var(--insilos-cyan-primary)"
            ]
        }

    return refactor_plan


# =============================================================================
# CLI & Full Pipeline Runner
# =============================================================================

def run_pipeline(target_path: str, output_json: Optional[str] = None) -> Dict[str, Any]:
    """Execute the full 3-phase Hegelian Dialectic pipeline."""
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Target path does not exist: {target_path}")

    # Compute File Checksum
    with open(target_path, "rb") as f:
        file_bytes = f.read()
        sha256 = hashlib.sha256(file_bytes).hexdigest()

    ttype = detect_target_type(target_path)

    # 1. THESIS
    if ttype == TargetType.PYC:
        thesis = deconstruct_pyc(target_path)
    elif ttype == TargetType.ELF_SO:
        thesis = deconstruct_elf_so(target_path)
    elif ttype == TargetType.JS_BUNDLE or target_path.endswith((".js", ".mjs")):
        thesis = deconstruct_js_bundle(target_path)
    elif ttype in (TargetType.QWEB_XML, TargetType.SCSS_CSS):
        thesis = deconstruct_qweb_or_scss(target_path, ttype)
    else:
        thesis = {
            "format": TargetType.UNKNOWN,
            "size_bytes": len(file_bytes),
            "sample_bytes": file_bytes[:32].hex()
        }

    thesis["sha256"] = sha256
    thesis["size_bytes"] = len(file_bytes)

    # 2. ANTITHESIS
    antithesis = audit_antithesis(thesis, target_path)

    # 3. SYNTHESIS
    synthesis = generate_synthesis_spec(thesis, antithesis, target_path)

    report = {
        "target": target_path,
        "type": ttype,
        "thesis": thesis,
        "antithesis": antithesis,
        "synthesis": synthesis,
        "sovereign_status": "COMPLIANT" if antithesis["status"] == "PASS" else "REMEDIATION_REQUIRED"
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def main():
    parser = argparse.ArgumentParser(description="Reverse Engineer Anything (REA) & Sovereign Clean-Room Engine")
    parser.add_argument("target", help="Path to binary, .pyc, js bundle, or stylesheet to deconstruct")
    parser.add_argument("--json", help="Path to write JSON forensic analysis report", default=None)
    parser.add_argument("--audit-only", action="store_true", help="Run Antithesis audit only and return exit code 0/1")

    args = parser.parse_args()

    report = run_pipeline(args.target, output_json=args.json)

    print("=" * 80)
    print(" SOVEREIGN CLEAN REVERSE ENGINEERING REPORT")
    print("=" * 80)
    print(f"Target:       {report['target']}")
    print(f"Format:       {report['type']}")
    print(f"SHA-256:      {report['thesis']['sha256']}")
    print(f"Audit Status: {report['antithesis']['status']}")
    print(f"Violations:   {report['antithesis']['violations_count']}")
    print(f"Warnings:     {report['antithesis']['warnings_count']}")
    print("-" * 80)

    if report['antithesis']['violations']:
        print("VIOLATIONS DETECTED (ANTITHESIS):")
        for v in report['antithesis']['violations']:
            print(f"  • [{v['severity']}] {v['rule']}: {v['message']}")
        print("-" * 80)

    print("SYNTHESIS REMEDIATION PLAN:")
    for action in report['synthesis']['remediation_actions']:
        print(f"  ✓ {action}")
    print("=" * 80)

    if args.audit_only and report['antithesis']['violations_count'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
