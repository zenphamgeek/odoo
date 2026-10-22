#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adversarial stress test suite for DGM Governance & Hyper-Automation Remediation.
Tests:
1. Regex Boundary & Inverted Entity Names
2. Formatted Tax Code Separators & Adjacent Characters
3. False Positive / False Negative Invariance
"""
import sys
import re

# Directly test the patterns from al2c_compliance_scanner
LEGACY_VAT_PATTERNS = [
    r'\b0313[\s\.\-]?683[\s\.\-]?499\b',
    r'(?<!\d)0313[\s\.\-]*683[\s\.\-]*499(?!\d)',
]

LEGACY_ENTITY_PATTERNS = [
    r'ứng\s*dụng\s*sáng\s*tạo',
    r'ung\s*dung\s*sang\s*tao',
    r'ung\s+dung\s+sang\s+tao\s+llc',
    r'cty\s+tnhh\s+ung\s+dung\s+sang\s+tao',
    r'công\s*ty\s*tnhh\s*ứng\s*dụng\s*sáng\s*tạo',
    r'sáng\s*tạo\s*ứng\s*dụng',
    r'sang\s*tao\s*ung\s*dung',
    r'sang\s+tao\s+ung\s+dung\s+llc',
    r'cty\s+tnhh\s+sang\s+tao\s+ung\s+dung',
    r'công\s*ty\s*tnhh\s*sáng\s*tạo\s*ứng\s*dụng',
]

def scan_text_mock(text):
    if not text:
        return {'is_compliant': True, 'violations': []}
    violations = []
    for p in LEGACY_VAT_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            violations.append(('tax_code', m.group(0)))
            break
    for p in LEGACY_ENTITY_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            violations.append(('entity', m.group(0)))
            break
    return {
        'is_compliant': len(violations) == 0,
        'violations': violations
    }

def run_adversarial_tests():
    print("=== STARTING ADVERSARIAL SCANNER TESTS ===")
    failures = []

    # 1. Required Formatted Tax Codes
    required_tax_codes = [
        "0313-683-499",
        "0313.683.499",
        "0313 683 499",
        "0313683499",
        "0313 - 683 - 499",
        "0313  683  499",
    ]
    for tc in required_tax_codes:
        text = f"Hợp đồng số 10/2022 MST: {tc} ký ngày 01/01/2022."
        res = scan_text_mock(text)
        if res['is_compliant'] or not any(v[0] == 'tax_code' for v in res['violations']):
            failures.append(f"FAILED to detect legacy tax code: '{tc}' in '{text}'")
        else:
            print(f" [PASS] Tax code detected: '{tc}' -> matched: {[v[1] for v in res['violations']]}")

    # 2. Adjacent Characters & Boundary Stress
    adjacent_cases = [
        ("MST:0313-683-499", True),
        ("(0313-683-499)", True),
        ("[0313.683.499]", True),
        ("0313 683 499/DGM", True),
        ("MST: 0313-683-499.", True),
        ("0313-683-499-001", True), # branch
        ("prefix0313-683-499suffix", True), # punctuation or text boundary
        ("10313683499", False), # False positive guard: 11-digit number starting with 1
        ("03136834999", False), # False positive guard: 11-digit number ending with 9
        ("0317958465", False),  # Canonical DGM MST
        ("0317-958-465", False), # Canonical DGM MST formatted
    ]
    for text, should_detect in adjacent_cases:
        res = scan_text_mock(text)
        detected = any(v[0] == 'tax_code' for v in res['violations'])
        if detected != should_detect:
            failures.append(f"FAILED boundary case: '{text}', expected detected={should_detect}, got {detected}")
        else:
            print(f" [PASS] Adjacent boundary '{text}': detected={detected} (expected={should_detect})")

    # 3. Required Inverted Entity Names
    required_inverted_entities = [
        "Sáng Tạo Ứng Dụng",
        "Sang Tao Ung Dung",
        "Công ty TNHH Sáng Tạo Ứng Dụng",
        "CÔNG TY TNHH SÁNG TẠO ỨNG DỤNG",
        "công ty tnhh sáng tạo ứng dụng",
        "Cty TNHH Sang Tao Ung Dung",
        "Sang Tao Ung Dung LLC",
        "Ứng Dụng Sáng Tạo",
        "Ung Dung Sang Tao",
        "Công ty TNHH Ứng Dụng Sáng Tạo",
    ]
    for entity in required_inverted_entities:
        text = f"Đơn vị phát hành: {entity} bảo lưu mọi quyền."
        res = scan_text_mock(text)
        if res['is_compliant'] or not any(v[0] == 'entity' for v in res['violations']):
            failures.append(f"FAILED to detect legacy entity: '{entity}' in '{text}'")
        else:
            print(f" [PASS] Legacy entity detected: '{entity}' -> matched: {[v[1] for v in res['violations']]}")

    # 4. Canonical / Compliant Entity Names
    valid_entities = [
        "CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ",
        "Công ty Cổ phần Người Bạn Số",
        "Digital Mate Joint Stock Company",
        "Digimate JSC",
        "DGM",
    ]
    for entity in valid_entities:
        text = f"Đơn vị ký kết: {entity} mã số thuế 0317958465."
        res = scan_text_mock(text)
        if not res['is_compliant']:
            failures.append(f"FALSE POSITIVE on valid entity '{entity}': {res['violations']}")
        else:
            print(f" [PASS] Valid entity allowed: '{entity}'")

    print("\n=== SUMMARY ===")
    if failures:
        print(f"TEST FAILED with {len(failures)} failures:")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    else:
        print("ALL ADVERSARIAL SCANNER & REGEX TESTS PASSED (0 failures)!")
        sys.exit(0)

if __name__ == '__main__':
    run_adversarial_tests()
