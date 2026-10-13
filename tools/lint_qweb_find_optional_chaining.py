#!/usr/bin/env python3
"""
tools/lint_qweb_find_optional_chaining.py
================================================================================
QWeb / Owl Template Null-Safety Linter: Array.prototype.find() Guard
================================================================================
Enforces that expressions deriving from .find(...) in QWeb/Owl XML templates
must employ optional chaining (?.) or defensive ternary/existence guards
before dereferencing properties, preventing runtime TypeError crashes when
no matching entry exists.
================================================================================
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict, Any


def find_balanced_call(s: str, open_paren_idx: int) -> int:
    """Find the index of the matching closing parenthesis for an opening '('."""
    depth = 0
    in_str = None
    for i in range(open_paren_idx, len(s)):
        ch = s[i]
        if in_str:
            if ch == in_str and s[i - 1] != '\\':
                in_str = None
        elif ch in ('"', "'", "`"):
            in_str = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i
    return -1


# Regex to detect t-set defining a variable using .find(...)
T_SET_FIND_RE = re.compile(
    r'<t\s+[^>]*t-set="([a-zA-Z_$][a-zA-Z0-9_$]*)"\s+[^>]*t-value="([^"]*\.find\s*\([^"]*\)[^"]*)"'
)


def scan_qweb_content(content: str, filename: str) -> List[Dict[str, Any]]:
    violations = []
    lines = content.splitlines()

    # 1. Check for inline unsafe dereferencing across all lines using balanced call detection
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue

        if "null-safety-ignore" in line:
            continue

        start_idx = 0
        while True:
            find_idx = line.find(".find(", start_idx)
            if find_idx == -1:
                break

            open_paren = find_idx + 5  # Index of '('
            close_paren = find_balanced_call(line, open_paren)
            if close_paren == -1:
                start_idx = find_idx + 6
                continue

            # Inspect what follows close_paren
            remainder = line[close_paren + 1:].lstrip()
            if remainder.startswith("?."):
                # Safe: uses optional chaining
                start_idx = close_paren + 1
                continue
            elif remainder.startswith(".") and len(remainder) > 1 and (remainder[1].isalpha() or remainder[1] in "_$"):
                # Unsafe: direct property access e.g. .name
                deref_match = re.match(r"^\.([a-zA-Z_$][a-zA-Z0-9_$]*)", remainder)
                prop_name = deref_match.group(1) if deref_match else "prop"
                violations.append({
                    "file": filename,
                    "line": line_no,
                    "type": "INLINE_UNSAFE_FIND_DEREF",
                    "detail": f"Unsafe direct property dereference on .find(...) without '?.' at '.find(...).{prop_name}'",
                    "snippet": stripped[:120],
                })

            start_idx = close_paren + 1


    # 2. Check for scoped variable assignments: <t t-set="var" t-value="...find(...)"/>
    # followed by unsafe dereference `var.prop` without `var?.prop` or `var ?` or `<t t-if="var">`
    for match in T_SET_FIND_RE.finditer(content):
        var_name = match.group(1)
        start_pos = match.end()
        # Look ahead within reasonable scope (next 800 characters)
        scope_text = content[start_pos:start_pos + 800]
        
        # Regex to find direct dereference: e.g. activeView.icon
        # Should not match activeView?.icon or activeView ? ... or activeView == ... or activeView.find
        unsafe_deref_re = re.compile(
            rf"(?<![\w?.])\b{re.escape(var_name)}\.([a-zA-Z_$][a-zA-Z0-9_$]*)"
        )

        for deref in unsafe_deref_re.finditer(scope_text):
            # Check if this dereference is guarded by a preceding t-if="var_name" or ternary
            prefix = scope_text[:deref.start()]
            if f't-if="{var_name}"' in prefix or f"t-if='{var_name}'" in prefix or f"{var_name} ?" in prefix:
                continue
            
            # Find approximate line number
            char_offset = start_pos + deref.start()
            line_no = content[:char_offset].count("\n") + 1
            line_str = lines[line_no - 1].strip() if line_no <= len(lines) else ""
            
            if "null-safety-ignore" in line_str:
                continue

            violations.append({
                "file": filename,
                "line": line_no,
                "type": "SCOPED_UNSAFE_FIND_DEREF",
                "detail": f"Unsafe dereference of variable '{var_name}.{deref.group(1)}' derived from .find(...) without '?.'",
                "snippet": line_str[:120],
            })

    return violations


def lint_file(file_path: Path) -> List[Dict[str, Any]]:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [{
            "file": str(file_path),
            "line": 0,
            "type": "READ_ERROR",
            "detail": str(e),
            "snippet": "",
        }]
    return scan_qweb_content(content, str(file_path))


def run_self_tests() -> bool:
    print("Running lint_qweb_find_optional_chaining internal self-tests...")

    # Case 1: Unsafe inline find dereference -> violation
    bad_inline = '<span t-out="items.find(x => x.id === id).name"/>'
    v1 = scan_qweb_content(bad_inline, "test1.xml")
    assert len(v1) == 1 and v1[0]["type"] == "INLINE_UNSAFE_FIND_DEREF"

    # Case 2: Safe inline find with optional chaining -> clean
    good_inline = '<span t-out="items.find(x => x.id === id)?.name"/>'
    v2 = scan_qweb_content(good_inline, "test2.xml")
    assert len(v2) == 0

    # Case 3: Unsafe scoped variable dereference -> violation
    bad_scoped = """
    <t t-set="activeItem" t-value="items.find(x => x.active)"/>
    <i t-attf-class="icon-{{ activeItem.icon }}"/>
    """
    v3 = scan_qweb_content(bad_scoped, "test3.xml")
    assert len(v3) >= 1 and any(x["type"] == "SCOPED_UNSAFE_FIND_DEREF" for x in v3)

    # Case 4: Safe scoped variable with optional chaining -> clean
    good_scoped = """
    <t t-set="activeItem" t-value="items.find(x => x.active)"/>
    <i t-attf-class="icon-{{ activeItem?.icon || 'default' }}" t-att-data-icon="activeItem ? activeItem.icon : undefined"/>
    """
    v4 = scan_qweb_content(good_scoped, "test4.xml")
    assert len(v4) == 0

    # Case 5: Safe scoped variable guarded by t-if -> clean
    good_guarded = """
    <t t-set="activeItem" t-value="items.find(x => x.active)"/>
    <t t-if="activeItem">
        <i t-attf-class="icon-{{ activeItem.icon }}"/>
    </t>
    """
    v5 = scan_qweb_content(good_guarded, "test5.xml")
    assert len(v5) == 0

    # Case 6: Explicit audited suppression comment -> clean
    suppressed = """
    <t t-set="activeItem" t-value="items.find(x => x.active)"/>
    <i t-attf-class="icon-{{ activeItem.icon }}"/> <!-- null-safety-ignore: guaranteed non-empty -->
    """
    v6 = scan_qweb_content(suppressed, "test6.xml")
    assert len(v6) == 0

    print("  [✓] All 6 self-tests passed cleanly.")
    return True


def main(argv: List[str] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if "--self-test" in argv:
        run_self_tests()
        return 0

    run_self_tests()

    targets = [a for a in argv if not a.startswith("--")]
    if not targets:
        targets = ["addons/web", "enterprise"]

    print("=" * 80)
    print(" QWEB / OWL TEMPLATE NULL-SAFETY FIND LINTER")
    print(f" Targets: {targets}")
    print("=" * 80)

    total_files = 0
    all_violations = []

    for target in targets:
        p = Path(target)
        if p.is_file() and p.suffix == ".xml":
            files = [p]
        elif p.is_dir():
            files = list(p.rglob("*.xml"))
        else:
            continue

        for f in files:
            total_files += 1
            v = lint_file(f)
            all_violations.extend(v)

    if all_violations:
        print(f"\n[FAIL] Found {len(all_violations)} null-safety violation(s) across {total_files} files:\n")
        for v in all_violations:
            print(f"  ❌ {v['file']}:{v['line']} [{v['type']}]: {v['detail']}")
            if v["snippet"]:
                print(f"     Snippet: {v['snippet']}")
        print("\nFix: Use optional chaining (?.) or an explicit ternary/t-if guard before dereferencing.\n")
        return 1

    print(f"\n[PASS] All {total_files} XML template files clean. Zero unsafe find dereferences detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
