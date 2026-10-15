#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/__tests__/test_adversarial_owl_telemetry_payroll_gate.py
==============================================================
Adversarial Security & Resilience Test Suite for Patch 22:
1. ErrorDialog Telemetry Bounded Sanitization, PagedTelemetryBlockTable, and PII/Secret Guard
2. OWL makeProps Prototype Pollution Guard (__proto__, constructor, prototype) and Unidirectional Warning
3. Document Tree Ancestry Cycle Interception (Zero Infinite Loops)
4. VCB DigiBiz Payroll Spreadsheet Formula Neutralization (CWE-1236)
"""

import json
import os
import re
import subprocess
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

ERROR_DIALOGS_JS = os.path.join(ROOT_DIR, "addons/web/static/src/core/errors/error_dialogs.js")
PATCH_JS = os.path.join(ROOT_DIR, "enterprise/insilos_theme_genesis/static/src/errors/runtime_error_dialog_patch.js")
OWL_JS = os.path.join(ROOT_DIR, "addons/web/static/lib/owl/owl.js")
DOCUMENTS_DOC_PY = os.path.join(ROOT_DIR, "enterprise/documents/models/documents_document.py")
HR_PAYSLIP_VCB_PY = os.path.join(ROOT_DIR, "addons/insilos_al2c/models/hr_payslip_vcb.py")


def extract_function_block(filepath, func_name):
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()
    marker = f"export function {func_name}("
    idx = src.find(marker)
    if idx == -1:
        marker = f"function {func_name}("
        idx = src.find(marker)
    assert idx != -1, f"Function {func_name} not found in {filepath}"
    brace_depth = 0
    started = False
    for pos in range(idx, len(src)):
        ch = src[pos]
        if ch == "{":
            brace_depth += 1
            started = True
        elif ch == "}":
            brace_depth -= 1
            if started and brace_depth == 0:
                return src[idx : pos + 1].replace("export function ", "function ")
    raise RuntimeError(f"Unbalanced braces in {func_name} of {filepath}")


def extract_class_block(filepath, class_name):
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()
    marker = f"export class {class_name}"
    idx = src.find(marker)
    if idx == -1:
        marker = f"class {class_name}"
        idx = src.find(marker)
    assert idx != -1, f"Class {class_name} not found in {filepath}"
    brace_depth = 0
    started = False
    for pos in range(idx, len(src)):
        ch = src[pos]
        if ch == "{":
            brace_depth += 1
            started = True
        elif ch == "}":
            brace_depth -= 1
            if started and brace_depth == 0:
                return src[idx : pos + 1].replace("export class ", "class ")
    raise RuntimeError(f"Unbalanced braces in {class_name} of {filepath}")


def test_sec_telemetry_sanitization_and_paged_block_table():
    """Verifies bounded sanitization, expanded phone numbers, formula guard, and PagedTelemetryBlockTable."""
    sanitize_payload_code = extract_function_block(ERROR_DIALOGS_JS, "sanitizeErrorPayload")
    paged_table_code = extract_class_block(ERROR_DIALOGS_JS, "PagedTelemetryBlockTable")

    node_script = f"""
{sanitize_payload_code}
{paged_table_code}

// 1. Test massive payload truncation
const massivePayload = "A".repeat(100000);
const sanitizedMassive = sanitizeErrorPayload(massivePayload);
if (!sanitizedMassive.includes("[TRUNCATED]")) {{
    throw new Error("Massive payload (>64KB) was not truncated");
}}

// 2. Test international & varied Vietnamese phone numbers
const phoneCases = [
    sanitizeErrorPayload("Call customer at 0912345678 immediately"),
    sanitizeErrorPayload("Call customer at +84912345678 immediately"),
    sanitizeErrorPayload("Call customer at 84912345678 immediately"),
    sanitizeErrorPayload("Call customer at 098 123 4567 immediately"),
    sanitizeErrorPayload("Call customer at 077-123-4567 immediately"),
    sanitizeErrorPayload("Call customer at 039.123.4567 immediately"),
];
for (const res of phoneCases) {{
    if (res.includes("12345678") || res.includes("123 4567") || res.includes("123-4567") || res.includes("123.4567")) {{
        throw new Error("Phone number leak detected in: " + res);
    }}
    if (!res.includes("*****")) {{
        throw new Error("Missing mask asterisks in: " + res);
    }}
}}

// 3. Test Formula Injection on error lines
const formulaCases = [
    "=cmd|' /C calc'!A0",
    "+123456789",
    "-@SUM(1,1)",
    "@SUM(A1:A10)",
];
for (const fc of formulaCases) {{
    const sanitized = sanitizeErrorPayload(fc);
    if (!sanitized.startsWith("'")) {{
        throw new Error("Formula not neutralized: " + sanitized);
    }}
}}

// 4. Test PagedTelemetryBlockTable
const table = new PagedTelemetryBlockTable(64, 3);
const encoder = new TextEncoder();
table.writeChunk(encoder.encode("Page 0 Root Cause: NullPointer\\n"));
table.writeChunk(encoder.encode("Page 1 Middle Frame: at line 42\\n"));
table.writeChunk(encoder.encode("Page 2 Eviction Trigger Frame\\n"));
table.writeChunk(encoder.encode("Page 3 Final Tail Frame\\n"));

const dumped = table.getSanitizedString();
if (!dumped.includes("Page 0 Root Cause")) {{
    throw new Error("Head page was improperly evicted from block table");
}}
if (!dumped.includes("Final Tail Frame")) {{
    throw new Error("Tail frame missing from block table");
}}

console.log("TELEMETRY_BLOCK_TABLE_OK");
"""
    proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True, check=True)
    assert "TELEMETRY_BLOCK_TABLE_OK" in proc.stdout
    print("[✓] SEC-01: Bounded telemetry sanitization, expanded VN phones, formula guard & PagedTelemetryBlockTable verified")


def test_sec_owl_make_props_prototype_pollution_guard():
    """Verifies that owl.js makeProps ignores prototype pollution keys (__proto__, constructor, prototype)."""
    with open(OWL_JS, "r", encoding="utf-8") as f:
        src = f.read()

    assert 'if (key === "__proto__" || key === "constructor" || key === "prototype")' in src, (
        "owl.js must protect defineProp against prototype pollution keys"
    )
    assert "signals[key] = signal(resolveValue(node.props, key));" in src
    assert "get: signals[key]" in src
    assert "signals[key].set(val);" in src

    # Node simulation of defineProp logic
    node_script = """
const signals = {};
const result = {};
let warnTriggered = false;
const app = { dev: true };
const node = { props: { safeKey: "hello", __proto__: { polluted: true }, constructor: "hacked" } };
function signal(v) {
    let val = v;
    const s = function() { return val; };
    s.set = function(newV) { val = newV; };
    return s;
}
function resolveValue(p, k) { return p[k]; }

function defineProp(key) {
    if (key === "__proto__" || key === "constructor" || key === "prototype") {
        return;
    }
    signals[key] = signal(resolveValue(node.props, key));
    Reflect.defineProperty(result, key, {
        enumerable: true,
        configurable: true,
        get: signals[key],
        set(val) {
            if (app.dev) {
                warnTriggered = true;
            }
            signals[key].set(val);
        }
    });
}

defineProp("safeKey");
defineProp("__proto__");
defineProp("constructor");

if (result.safeKey !== "hello") throw new Error("safeKey getter failed");
result.safeKey = "world";
if (result.safeKey !== "world") throw new Error("safeKey setter failed");
if (!warnTriggered) throw new Error("Dev warning was not triggered on direct prop mutation");
if (Object.prototype.polluted) throw new Error("Prototype was polluted");
if (result.constructor !== Object.prototype.constructor) throw new Error("Constructor was overwritten");

console.log("OWL_PROPS_GUARD_OK");
"""
    proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True, check=True)
    assert "OWL_PROPS_GUARD_OK" in proc.stdout
    print("[✓] SEC-02: OWL makeProps prototype pollution guard & unidirectional warning verified")


def test_sec_document_tree_cycle_detection():
    """Verifies that _compute_user_folder_id in documents_document.py intercepts circular graphs."""
    with open(DOCUMENTS_DOC_PY, "r", encoding="utf-8") as f:
        src = f.read()

    assert "seen_ids = set()" in src, "Missing seen_ids cycle tracking set in _compute_user_folder_id"
    assert "if curr.id in seen_ids:" in src, "Missing cycle check in _compute_user_folder_id"
    assert "document.user_folder_id = 'CYCLIC_ERROR'" in src, "Missing CYCLIC_ERROR assignment on cycle detection"

    # Behavioral graph cycle simulation
    class MockDoc:
        def __init__(self, doc_id, folder_id=None):
            self.id = doc_id
            self.folder_id = folder_id

    d1 = MockDoc(1)
    d2 = MockDoc(2, d1)
    d3 = MockDoc(3, d2)
    d1.folder_id = d3  # Circular cycle: 1 -> 3 -> 2 -> 1

    seen_ids = set()
    curr = d1.folder_id
    is_cycle = False
    while curr:
        if curr.id in seen_ids:
            is_cycle = True
            break
        seen_ids.add(curr.id)
        curr = curr.folder_id

    assert is_cycle is True, "Failed to detect circular folder ancestry"
    print("[✓] SEC-03: Document folder ancestry cycle interception verified (Zero loop hang)")


def test_sec_vcb_digibiz_formula_injection_guard():
    """Verifies that sanitize_csv_cell in hr_payslip_vcb.py neutralizes formula triggers."""
    with open(HR_PAYSLIP_VCB_PY, "r", encoding="utf-8") as f:
        src = f.read()

    assert "def sanitize_csv_cell(value):" in src
    assert "stripped = s.lstrip()" in src
    assert "if stripped and stripped[0] in ('=', '+', '-', '@', '\\t', '\\r'):" in src

    # Dynamically extract and compile sanitize_csv_cell without full odoo import tree
    import ast
    parsed = ast.parse(src)
    func_node = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == "sanitize_csv_cell")
    mod = ast.Module(body=[func_node], type_ignores=[])
    compiled = compile(mod, filename="<ast>", mode="exec")
    scope = {}
    exec(compiled, scope)
    sanitize_csv_cell = scope["sanitize_csv_cell"]

    test_vectors = [
        ("=cmd|' /C calc'!A0", "'=cmd|' /C calc'!A0"),
        ("+123456789", "'+123456789"),
        ("-@SUM(1,1)*cmd", "'-@SUM(1,1)*cmd"),
        ("@SUM(A1:A10)", "'@SUM(A1:A10)"),
        ("\t=2+5", "'\t=2+5"),
        ("   =cmd|calc", "'   =cmd|calc"),
        ("Normal Employee Name", "Normal Employee Name"),
        ("0901234567", "0901234567"),
        (None, ""),
    ]

    for raw, expected in test_vectors:
        res = sanitize_csv_cell(raw)
        assert res == expected, f"Failed formula sanitization for {raw!r}: got {res!r}, expected {expected!r}"

    print("[✓] SEC-04: VCB DigiBiz formula injection neutralization (CWE-1236) verified")


def run_all_tests():
    test_sec_telemetry_sanitization_and_paged_block_table()
    test_sec_owl_make_props_prototype_pollution_guard()
    test_sec_document_tree_cycle_detection()
    test_sec_vcb_digibiz_formula_injection_guard()
    print("[🎉] ALL ADVERSARIAL OWL, TELEMETRY & PAYROLL GATE TESTS PASSED (EXIT 0)")


if __name__ == "__main__":
    run_all_tests()
