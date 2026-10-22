#!/usr/bin/env python3
"""
Empirical Challenger 2 Audit & Stress Harness
Milestone M1: Elegance Palette Tokens & Liquid Spatial Theme
Role: Empirical Challenger 2 (critic, specialist)
Platform: Insilos Enterprise Odoo 20
"""

import sys
import os
import ast
import re
import math
import subprocess

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

def hex_to_rgb(hex_str):
    h = hex_str.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join([c*2 for c in h])
    elif len(h) == 8:
        h = h[:6]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def rel_luminance(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def contrast_ratio(hex1, hex2):
    l1 = rel_luminance(hex1)
    l2 = rel_luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

def main():
    print("=" * 80)
    print("EMPIRICAL CHALLENGER 2: MILESTONE M1 AUDIT & ADVERSARIAL SUITE")
    print("=" * 80)
    
    passed = 0
    failed = 0
    errors = []

    def check(name, cond, details=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[PASS] {name}")
            if details:
                print(f"       └─ {details}")
        else:
            failed += 1
            errors.append((name, details))
            print(f"[FAIL] {name}")
            if details:
                print(f"       └─ ERROR: {details}")

    # 1. Manifest AST & Asset Loading Order
    print("\n--- 1. MANIFEST & ASSET LOADING ORDER ---")
    manifest_path = "enterprise/insilos_website/__manifest__.py"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_text = f.read()

    try:
        manifest_data = ast.literal_eval(manifest_text)
        check("Manifest is valid Python AST literal", True, "Successfully parsed with ast.literal_eval")
    except Exception as e:
        check("Manifest is valid Python AST literal", False, str(e))
        return 1

    assets = manifest_data.get("assets", {}).get("web.assets_frontend", [])
    target_asset = "insilos_website/static/src/scss/insilos_liquid_spatial.scss"
    check("Target asset exists in web.assets_frontend", target_asset in assets, f"Found at index {assets.index(target_asset) if target_asset in assets else -1}")

    if target_asset in assets:
        idx = assets.index(target_asset)
        base_idx = assets.index("insilos_website/static/src/scss/insilos.scss") if "insilos_website/static/src/scss/insilos.scss" in assets else -1
        theme_idx = assets.index("insilos_website/static/src/scss/innoria_theme.scss") if "insilos_website/static/src/scss/innoria_theme.scss" in assets else -1
        
        check("Asset loaded immediately after base insilos.scss", idx == base_idx + 1, f"insilos.scss at {base_idx}, liquid_spatial at {idx}")
        check("Asset loaded prior to theme overrides (innoria_theme.scss)", idx < theme_idx, f"liquid_spatial at {idx}, innoria_theme at {theme_idx}")

    # 2. Inspect Worker's Test Suite for Mocking/Bypasses
    print("\n--- 2. WORKER TEST SUITE INTEGRITY INSPECTION ---")
    test_suite_path = "tools/test_design_tokens_wcag_empirical.py"
    with open(test_suite_path, "r", encoding="utf-8") as f:
        test_suite_text = f.read()

    check("Zero 'mock' references in test suite", "mock" not in test_suite_text.lower(), "Verified no unittest.mock or magic mocks")
    check("Zero 'monkeypatch' or 'patch' in test suite", "patch" not in test_suite_text.lower(), "Verified no test monkey-patching")
    check("Test suite terminates with real sys.exit(run_tests())", "sys.exit(run_tests())" in test_suite_text, "Real exit code returned")

    # 3. Independent Libsass SCSS Compilation
    print("\n--- 3. DIRECT LIBSASS SCSS COMPILATION ---")
    import sass
    spatial_path = "enterprise/insilos_website/static/src/scss/insilos_liquid_spatial.scss"
    with open(spatial_path, "r", encoding="utf-8") as f:
        scss_content = f.read()

    try:
        compiled = sass.compile(string=scss_content)
        check("Direct libsass compilation succeeds", len(compiled) > 1000, f"Generated {len(compiled)} bytes of clean CSS")
        check("No uncompiled SCSS variables ($) in output", "$" not in compiled, "Zero variable leakage")
    except Exception as e:
        check("Direct libsass compilation succeeds", False, str(e))

    # 4. Rigorous WCAG Contrast Audit
    print("\n--- 4. RIGOROUS WCAG MATHEMATICAL CONTRAST AUDIT ---")
    contrast_specs = [
        ("White (#FFFFFF) on Deep Obsidian (#050811)", "#FFFFFF", "#050811", 7.0, "AAA"),
        ("Slate 200 (#E2E8F0) on Deep Obsidian (#050811)", "#E2E8F0", "#050811", 7.0, "AAA"),
        ("White (#FFFFFF) on Deep Obsidian Surface (#0A101D)", "#FFFFFF", "#0A101D", 7.0, "AAA"),
        ("Slate 200 (#E2E8F0) on Deep Obsidian Surface (#0A101D)", "#E2E8F0", "#0A101D", 7.0, "AAA"),
        ("White (#FFFFFF) on Titanium Slate (#1E293B)", "#FFFFFF", "#1E293B", 7.0, "AAA"),
        ("Slate 200 (#E2E8F0) on Titanium Slate (#1E293B)", "#E2E8F0", "#1E293B", 7.0, "AAA"),
        ("Slate 400 (#94A3B8) on Titanium Slate (#1E293B)", "#94A3B8", "#1E293B", 4.5, "AA"),
        ("Liquid Aurora Mint (#42E6C3) on Deep Obsidian (#050811)", "#42E6C3", "#050811", 7.0, "AAA"),
        ("Liquid Aurora Cyan (#00F2FE) on Deep Obsidian (#050811)", "#00F2FE", "#050811", 7.0, "AAA"),
        ("Dark text (#05101E) on Aurora Mint badge (#42E6C3)", "#05101E", "#42E6C3", 7.0, "AAA"),
        ("Dark text (#05101E) on Aurora Cyan badge (#00F2FE)", "#05101E", "#00F2FE", 7.0, "AAA"),
        ("White (#FFFFFF) on Royal Electric Indigo badge (#6366F1)", "#FFFFFF", "#6366F1", 3.0, "UI Component/Badge"),
        ("White (#FFFFFF) on Warm Rose Glow badge (#F43F5E)", "#FFFFFF", "#F43F5E", 3.0, "UI Component/Badge"),
        ("Rose Tint (#FB7185) on Deep Obsidian (#050811)", "#FB7185", "#050811", 7.0, "AAA"),
        ("Indigo Tint (#818CF8) on Deep Obsidian (#050811)", "#818CF8", "#050811", 4.5, "AA"),
    ]

    for label, fg, bg, min_c, standard in contrast_specs:
        cr = contrast_ratio(fg, bg)
        check(f"{label} (Req >={min_c}:1 [{standard}])", cr >= min_c, f"Computed ratio: {cr:.2f}:1")

    # 5. Live DB QWeb Compiled Bundle Verification
    print("\n--- 5. LIVE DB QWEB COMPILED BUNDLE VERIFICATION ---")
    try:
        import insilos
        from insilos.tools import config
        from insilos.modules.registry import Registry

        config.parse_config(['-c', 'insilos.conf', '-d', 'odoo20_dev'])
        registry = Registry('odoo20_dev')
        with registry.cursor() as cr:
            env = insilos.api.Environment(cr, insilos.SUPERUSER_ID, {})
            att = env['ir.attachment'].search([('name', '=', 'web.assets_frontend.min.css')], order='id desc', limit=1)
            check("Asset bundle attachment found", bool(att), f"Attachment ID {att.id if att else 'None'}")
            if att:
                data = att.raw.content
                text = data.decode('utf-8', errors='ignore')
                check("Compiled bundle size > 1.5MB", len(data) > 1500000, f"Actual size: {len(data)} bytes")
                check("Compiled bundle contains --ins-obsidian-deep", "--ins-obsidian-deep" in text, "Found in minified bundle")
                check("Compiled bundle contains --ins-aurora-mint", "--ins-aurora-mint" in text, "Found in minified bundle")
                check("Compiled bundle contains .ins-spatial-layer", ".ins-spatial-layer" in text, "Found in minified bundle")
                check("Compiled bundle contains .ins-floating-pod", ".ins-floating-pod" in text, "Found in minified bundle")
                check("Compiled bundle contains .ins-cardless", ".ins-cardless" in text, "Found in minified bundle")
    except Exception as e:
        check("Live DB bundle verification", False, str(e))

    print("\n" + "=" * 80)
    print(f"CHALLENGER AUDIT SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 80)

    if failed == 0:
        print("VERDICT: CONFIRM_CORRECT — All empirical tests passed without reservation.")
        return 0
    else:
        print("VERDICT: CHALLENGE_FAILED — Regressions or discrepancies detected.")
        for err, detail in errors:
            print(f" - {err}: {detail}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
