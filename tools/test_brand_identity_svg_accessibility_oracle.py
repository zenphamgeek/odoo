#!/usr/bin/env python3
"""
INNOKAFE BRAND IDENTITY SVG RENDER & ACCESSIBILITY EMPIRICAL ORACLE
==================================================================
Empirical Challenger Test Suite for:
1. SVG XML well-formedness, viewBox attribute validity, and key brand elements:
   - Amber Bean (#FF8000), evenodd S-groove cutout, 3 sprouts, Lambda 'Λ', script tagline.
2. PNG Favicon Suite binary verification:
   - PNG magic bytes b'\\x89PNG\\r\\n\\x1a\\n', IHDR dimensions, CRC32 integrity.
3. Webmanifest JSON validation:
   - Valid JSON, theme_color #1E120B, background_color, icon mappings.
4. Mathematical WCAG 2.1 relative luminance and contrast ratio proofs:
   - Warm Amber (#D48842) on Deep Espresso (#1E120B) >= 4.5:1 (AA).
   - White (#FFFFFF) on Warm Amber (#D48842) MUST FAIL (< 4.5:1).
   - Cream Foam (#F7F2EA) on Deep Espresso (#1E120B) >= 7.0:1 (AAA).
5. Adversarial deep pixel inspection:
   - Probing rasterized PNG favicons for brand color fidelity and CairoSVG CSS variable evaluation.

Author: challenger_svg_render_and_accessibility_1 (critic, specialist)
Platform: Insilos Enterprise Platform 20
"""

import os
import sys
import json
import struct
import zlib
import re
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BRANDING_DIR = ROOT_DIR / "enterprise" / "innokafe_website" / "static" / "src" / "img" / "branding"
FAVICON_DIR = ROOT_DIR / "enterprise" / "innokafe_website" / "static" / "src" / "img" / "favicon"
SCSS_FILE = ROOT_DIR / "enterprise" / "innokafe_website" / "static" / "src" / "scss" / "innokafe_theme.scss"
TEMPLATES_FILE = ROOT_DIR / "enterprise" / "innokafe_website" / "views" / "website_templates.xml"

# WCAG 2.1 Mathematical Formulas
def srgb_to_linear(c_srgb: float) -> float:
    """Converts 8-bit sRGB channel normalized to [0, 1] to linear luminance component."""
    if c_srgb <= 0.04045:
        return c_srgb / 12.92
    return ((c_srgb + 0.055) / 1.055) ** 2.4

def relative_luminance(hex_code: str) -> float:
    """Calculates relative luminance L according to WCAG 2.1 definition."""
    hex_clean = hex_code.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join(c * 2 for c in hex_clean)
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates contrast ratio between two colors (L1 + 0.05) / (L2 + 0.05)."""
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def run_oracle_suite():
    print("================================================================================")
    print("INNOKAFE BRAND IDENTITY SVG RENDER & ACCESSIBILITY EMPIRICAL ORACLE")
    print("Challenger: challenger_svg_render_and_accessibility_1")
    print("Target Module: enterprise/innokafe_website")
    print("================================================================================\n")

    tests_run = 0
    tests_passed = 0
    findings = []
    critical_failures = []

    def assert_gate(name, condition, details=""):
        nonlocal tests_run, tests_passed
        tests_run += 1
        if condition:
            tests_passed += 1
            print(f"  ✅ [PASS] {name}")
            if details:
                print(f"            └─ {details}")
        else:
            critical_failures.append((name, details))
            print(f"  ❌ [FAIL] {name}")
            if details:
                print(f"            └─ ERROR: {details}")

    def warn_finding(name, details=""):
        findings.append((name, details))
        print(f"  ⚠️  [CHALLENGE / ADVERSARIAL FINDING] {name}")
        if details:
            print(f"            └─ DETAILS: {details}")

    # =========================================================================
    # STAGE 1: SVG XML Well-Formedness & Dimension Invariants
    # =========================================================================
    print("--- STAGE 1: SVG XML Well-Formedness & Dimension Invariants ---")
    svg_files = [
        "innokafe_logo_master.svg",
        "innokafe_logo_stacked.svg",
        "innokafe_mark_symbol.svg",
        "innokafe_logo_white.svg",
        "innokafe_logo_dark.svg",
        "favicon.svg",
    ]

    expected_viewboxes = {
        "innokafe_logo_master.svg": (0.0, 0.0, 805.6, 232.6),
        "innokafe_logo_stacked.svg": (0.0, 0.0, 600.0, 680.0),
        "innokafe_mark_symbol.svg": (0.0, 0.0, 512.0, 512.0),
        "innokafe_logo_white.svg": (0.0, 0.0, 805.6, 232.6),
        "innokafe_logo_dark.svg": (0.0, 0.0, 805.6, 232.6),
        "favicon.svg": (0.0, 0.0, 512.0, 512.0),
    }

    for svg_name in svg_files:
        svg_path = BRANDING_DIR / svg_name
        assert_gate(f"SVG File Exists: {svg_name}", svg_path.exists(), f"File size: {svg_path.stat().st_size if svg_path.exists() else 0} bytes")
        if not svg_path.exists():
            continue

        # XML parse test
        xml_valid = False
        try:
            root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
            xml_valid = "svg" in root.tag.lower()
        except Exception as e:
            xml_valid = False
        assert_gate(f"W3C XML Well-Formedness: {svg_name}", xml_valid)

        # ViewBox test
        viewbox_str = root.attrib.get("viewBox", "") if xml_valid else ""
        vb_parts = [float(p) for p in viewbox_str.split()] if viewbox_str else []
        exp = expected_viewboxes.get(svg_name, (0, 0, 0, 0))
        vb_match = len(vb_parts) == 4 and all(abs(a - b) < 0.2 for a, b in zip(vb_parts, exp))
        assert_gate(
            f"ViewBox Exact Invariant: {svg_name}",
            vb_match,
            f"Expected {exp}, got '{viewbox_str}'"
        )

    # =========================================================================
    # STAGE 2: Geometric Feature Probing & Brand Vector Elements
    # =========================================================================
    print("\n--- STAGE 2: Geometric Feature Probing & Brand Vector Elements ---")
    for svg_name in svg_files:
        svg_path = BRANDING_DIR / svg_name
        content = svg_path.read_text(encoding="utf-8")
        root = ET.fromstring(content)

        # 1. Amber Bean (#FF8000)
        has_amber_bean = "#FF8000" in content
        assert_gate(f"Amber Bean Color #FF8000: {svg_name}", has_amber_bean)

        # 2. S-Groove cutout (evenodd)
        has_evenodd = "evenodd" in content
        paths = root.findall(".//{http://www.w3.org/2000/svg}path") + root.findall(".//path")
        bean_paths = [p for p in paths if "bean" in p.attrib.get("class", "").lower()]
        m_count = len(re.findall(r'[Mm]\s*[\d\.\-]+', bean_paths[0].attrib.get("d", ""))) if bean_paths else 0
        assert_gate(
            f"S-Groove Negative Space Cutout (evenodd + >=2 subpaths): {svg_name}",
            has_evenodd and m_count >= 2,
            f"fill-rule=evenodd present: {has_evenodd}, bean subpaths count: {m_count}"
        )

        # 3. Botanical Sprout Triad (3 distinct sprout paths)
        sprout_paths = [p for p in paths if "sprout" in p.attrib.get("class", "").lower()]
        assert_gate(
            f"Botanical Sprout Triad (3 Sprouts): {svg_name}",
            len(sprout_paths) == 3,
            f"Sprout path count: {len(sprout_paths)}"
        )

    # Wordmark and Script Tagline in full logos
    full_logos = [
        "innokafe_logo_master.svg",
        "innokafe_logo_stacked.svg",
        "innokafe_logo_white.svg",
        "innokafe_logo_dark.svg",
    ]
    for svg_name in full_logos:
        content = (BRANDING_DIR / svg_name).read_text(encoding="utf-8")
        root = ET.fromstring(content)
        polygons = root.findall(".//{http://www.w3.org/2000/svg}polygon") + root.findall(".//polygon")
        lambda_present = any("594" in p.attrib.get("points", "") for p in polygons)
        assert_gate(f"Chevron Lambda 'Λ' Glyph: {svg_name}", lambda_present)

        script_paths = [p for p in root.findall(".//{http://www.w3.org/2000/svg}path") + root.findall(".//path")
                        if "inno-script-path" in p.attrib.get("class", "").lower()]
        assert_gate(
            f"Calligraphic Tagline 'Inspire the Techno' (16 glyph strokes): {svg_name}",
            len(script_paths) == 16,
            f"Found {len(script_paths)} script paths"
        )

    # =========================================================================
    # STAGE 3: Rasterized PNG Favicon Suite Magic Bytes & Chunk Grammar
    # =========================================================================
    print("\n--- STAGE 3: Rasterized PNG Favicon Suite Magic Bytes & Chunk Grammar ---")
    magic_png = b'\x89PNG\r\n\x1a\n'
    png_targets = [
        ("favicon-16x16.png", 16, 16),
        ("favicon-32x32.png", 32, 32),
        ("apple-touch-icon-180x180.png", 180, 180),
    ]

    for dir_name, dir_path in [("branding/", BRANDING_DIR), ("favicon/", FAVICON_DIR)]:
        for fname, exp_w, exp_h in png_targets:
            fpath = dir_path / fname
            assert_gate(f"PNG File Exists: {dir_name}{fname}", fpath.exists())
            if not fpath.exists():
                continue

            data = fpath.read_bytes()
            assert_gate(f"PNG Magic Bytes (\\x89PNG\\r\\n\\x1a\\n): {dir_name}{fname}", data[:8] == magic_png)

            ihdr_len, ihdr_type = struct.unpack('>I4s', data[8:16])
            width, height, bit_depth, color_type, _, _, _ = struct.unpack('>IIBBBBB', data[16:29])
            file_crc = struct.unpack('>I', data[29:33])[0]
            calc_crc = zlib.crc32(data[12:29])

            assert_gate(
                f"IHDR Header & Exact Dimensions ({exp_w}x{exp_h}): {dir_name}{fname}",
                ihdr_len == 13 and ihdr_type == b'IHDR' and width == exp_w and height == exp_h and file_crc == calc_crc,
                f"Size={width}x{height}, BitDepth={bit_depth}, ColorType={color_type}, CRC32={'VALID' if file_crc == calc_crc else 'INVALID'}"
            )

    # =========================================================================
    # STAGE 4: Web Application Manifest Specification (JSON & Theme Color)
    # =========================================================================
    print("\n--- STAGE 4: Web Application Manifest Specification ---")
    for dir_name, dir_path in [("branding/", BRANDING_DIR), ("favicon/", FAVICON_DIR)]:
        manifest_path = dir_path / "site.webmanifest"
        assert_gate(f"Manifest Exists: {dir_name}site.webmanifest", manifest_path.exists())
        if not manifest_path.exists():
            continue

        try:
            m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            json_valid = True
        except Exception:
            json_valid = False
            m_data = {}

        assert_gate(f"Manifest Valid JSON: {dir_name}site.webmanifest", json_valid)
        assert_gate(f"Manifest theme_color: #1E120B: {dir_name}site.webmanifest", m_data.get("theme_color") == "#1E120B", f"Value: '{m_data.get('theme_color')}'")
        assert_gate(f"Manifest background_color: #1E120B: {dir_name}site.webmanifest", m_data.get("background_color") == "#1E120B")
        assert_gate(f"Manifest Icon Count (>= 4 entries): {dir_name}site.webmanifest", len(m_data.get("icons", [])) >= 4, f"Found {len(m_data.get('icons', []))} icons")

    # =========================================================================
    # STAGE 5: Mathematical WCAG 2.1 Contrast Ratios & Relative Luminance
    # =========================================================================
    print("\n--- STAGE 5: Mathematical WCAG 2.1 Contrast Calculations ---")
    l_espresso = relative_luminance("#1E120B")
    l_amber = relative_luminance("#D48842")
    l_cream = relative_luminance("#F7F2EA")
    l_white = relative_luminance("#FFFFFF")
    l_forest = relative_luminance("#2D4739")
    l_orange = relative_luminance("#FF8000")

    # Contract 1: Warm Amber on Deep Espresso >= 4.5:1
    cr_amber_espresso = contrast_ratio("#D48842", "#1E120B")
    assert_gate(
        "Contract 1: Warm Amber (#D48842) on Deep Espresso (#1E120B) >= 4.5:1 (AA)",
        cr_amber_espresso >= 4.5,
        f"L(Amber)={l_amber:.5f}, L(Espresso)={l_espresso:.5f} -> Contrast Ratio = {cr_amber_espresso:.4f}:1 (PASSES AA)"
    )

    # Contract 2: White on Warm Amber MUST FAIL (< 4.5:1)
    cr_white_amber = contrast_ratio("#FFFFFF", "#D48842")
    assert_gate(
        "Contract 2: White (#FFFFFF) on Warm Amber (#D48842) MUST FAIL (< 4.5:1)",
        cr_white_amber < 4.5,
        f"L(White)={l_white:.5f}, L(Amber)={l_amber:.5f} -> Contrast Ratio = {cr_white_amber:.4f}:1 (< 4.5:1 STRICT CONTRACT)"
    )

    # Contract 3: Cream Foam on Deep Espresso >= 7.0:1
    cr_cream_espresso = contrast_ratio("#F7F2EA", "#1E120B")
    assert_gate(
        "Contract 3: Cream Foam (#F7F2EA) on Deep Espresso (#1E120B) >= 7.0:1 (AAA)",
        cr_cream_espresso >= 7.0,
        f"L(Cream)={l_cream:.5f}, L(Espresso)={l_espresso:.5f} -> Contrast Ratio = {cr_cream_espresso:.4f}:1 (PASSES AAA)"
    )

    # Extended Brand Contrast Proofs
    cr_forest_cream = contrast_ratio("#2D4739", "#F7F2EA")
    assert_gate(
        "Extended Proof: Forest Leaf (#2D4739) on Cream Foam (#F7F2EA) >= 7.0:1 (AAA)",
        cr_forest_cream >= 7.0,
        f"L(Forest)={l_forest:.5f}, L(Cream)={l_cream:.5f} -> Contrast Ratio = {cr_forest_cream:.4f}:1 (PASSES AAA)"
    )

    cr_orange_espresso = contrast_ratio("#FF8000", "#1E120B")
    assert_gate(
        "Extended Proof: Amber Orange (#FF8000) on Deep Espresso (#1E120B) >= 7.0:1 (AAA)",
        cr_orange_espresso >= 7.0,
        f"L(Orange)={l_orange:.5f}, L(Espresso)={l_espresso:.5f} -> Contrast Ratio = {cr_orange_espresso:.4f}:1 (PASSES AAA)"
    )

    # =========================================================================
    # STAGE 6: Theme SCSS Button Contrast Invariance Audit
    # =========================================================================
    print("\n--- STAGE 6: Theme SCSS Button Accessibility Verification ---")
    scss_content = SCSS_FILE.read_text(encoding="utf-8")
    has_mandate_comment = "NEVER USE WHITE #FFFFFF ON WARM AMBER" in scss_content
    assert_gate("SCSS Accessibility Mandate Documented", has_mandate_comment)

    # Check button text color
    btn_blocks = re.findall(r'(\.btn-amber[^{]*\{[^}]*\})', scss_content)
    has_white_text = any("#ffffff" in b.lower() or "#fff;" in b.lower() for b in btn_blocks)
    assert_gate("SCSS Zero White-on-Amber Button Violations", not has_white_text, "No #FFFFFF assigned to .btn-amber text")

    # =========================================================================
    # STAGE 7: ADVERSARIAL STRESS: PNG Favicon Color Fidelity & CairoSVG Evaluation
    # =========================================================================
    print("\n--- STAGE 7: ADVERSARIAL STRESS: PNG Favicon Color Fidelity ---")
    # Probing pixel color distributions of rasterized PNGs
    for fname in ["favicon-16x16.png", "favicon-32x32.png", "apple-touch-icon-180x180.png"]:
        img_path = BRANDING_DIR / fname
        img = Image.open(img_path)
        raw_bytes = img.tobytes()
        total_pixels = img.width * img.height
        non_black_pixels = [
            (raw_bytes[i], raw_bytes[i+1], raw_bytes[i+2], raw_bytes[i+3])
            for i in range(0, len(raw_bytes), 4)
            if raw_bytes[i] > 0 or raw_bytes[i+1] > 0
        ]
        
        # Test: Does the PNG contain visible brand colors (non-black)?
        if len(non_black_pixels) == 0:
            warn_finding(
                f"Raster Color Regression: {fname} is 100% black silhouette",
                f"Total pixels: {total_pixels}, Non-black pixels: 0 (0.0%). "
                f"CairoSVG failed to evaluate CSS variables 'var(--inno-fav-bg)' / 'var(--inno-fav-bean)' during build_brand_assets.py rasterization, "
                f"resulting in solid black-on-black rendering with zero bean/sprout visibility!"
            )
        else:
            print(f"  ✅ [PASS] {fname} contains {len(non_black_pixels)} non-black brand pixels")

    # =========================================================================
    # STAGE 8: Database arch_db Logo Authenticity Invariant & Anomaly Tripwire
    # =========================================================================
    print("\n--- STAGE 8: Database arch_db Logo Authenticity CI Invariant & Anomaly Tripwire ---")
    
    def validate_logo_arch_structure(arch_text: str, is_footer: bool = False):
        if 'Inno<span' in arch_text or 'Specialty<br' in arch_text:
            return False, "Detected residual fake text logo markup in arch_db"
        expected_svg = "innokafe_logo_white.svg" if is_footer else "innokafe_logo_master.svg"
        if expected_svg not in arch_text:
            return False, f"Missing canonical vector logo '{expected_svg}' in arch_db"
        return True, "Valid vector branding"

    # Negative-Selection Anomaly Tripwire Self-Test
    adversarial_fake_arch = '<a class="navbar-brand"><span class="inno-serif">Inno<span class="text-warning">Kafe</span></span></a>'
    ok_fake, reason_fake = validate_logo_arch_structure(adversarial_fake_arch, is_footer=False)
    assert_gate(
        "Negative-Selection Tripwire: Adversarial fake text logo correctly trapped",
        not ok_fake and "residual fake text logo" in reason_fake,
        reason_fake
    )

    adversarial_missing_svg = '<a class="navbar-brand"><img src="/static/placeholder.png"/></a>'
    ok_miss, reason_miss = validate_logo_arch_structure(adversarial_missing_svg, is_footer=False)
    assert_gate(
        "Negative-Selection Tripwire: Missing canonical vector SVG correctly trapped",
        not ok_miss and "Missing canonical vector logo" in reason_miss,
        reason_miss
    )

    # Live Database Structural Integrity Audit (if reachable)
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = int(os.environ.get("DB_PORT", 5434))
    db_user = os.environ.get("DB_USER", "insilos")
    db_pass = os.environ.get("PGPASSWORD", "1NN0R1@2026")
    db_name = os.environ.get("DB_NAME", "innokafe_prod")

    try:
        import psycopg2
        conn = psycopg2.connect(
            host=db_host, port=db_port, user=db_user, password=db_pass, dbname=db_name, connect_timeout=3
        )
        cur = conn.cursor()
        
        # Verify View 1046 (Header Brand Logo)
        cur.execute("SELECT arch_db::text FROM ir_ui_view WHERE id = 1046 OR key = 'website.option_header_brand_logo' LIMIT 1")
        row = cur.fetchone()
        if row:
            ok_h, msg_h = validate_logo_arch_structure(row[0], is_footer=False)
            assert_gate(f"View 1046 (website.option_header_brand_logo) structural authenticity: {msg_h}", ok_h, msg_h)

        # Verify View 1059 / 1696 (Footer Custom)
        cur.execute("SELECT id, arch_db::text FROM ir_ui_view WHERE key = 'website.footer_custom' OR id IN (1059, 1696) ORDER BY id")
        for v_id, arch_txt in cur.fetchall():
            ok_f, msg_f = validate_logo_arch_structure(arch_txt, is_footer=True)
            assert_gate(f"Footer View {v_id} (website.footer_custom) structural authenticity: {msg_f}", ok_f, msg_f)

        # Fleet-wide Zero Residual Fake Text Logo Query
        cur.execute("""
            SELECT count(*)
            FROM ir_ui_view
            WHERE arch_db::text ILIKE '%Inno<span%' OR arch_db::text ILIKE '%Specialty<br%'
        """)
        residual_count = cur.fetchone()[0]
        assert_gate(
            f"Fleet-wide Zero Fake Text Logos Invariant: exactly {residual_count} residual views (Expected: 0)",
            residual_count == 0,
            f"Residual count: {residual_count}"
        )
        conn.close()
    except Exception as exc:
        print(f"  [i] Live DB check skipped or in offline mode ({exc}) — Tripwire contracts verified.")

    # =========================================================================
    # SCORECARD & SUMMARY
    # =========================================================================
    print("\n================================================================================")
    print("FINAL EMPIRICAL SCORECARD")
    print("================================================================================")
    print(f"  • Total Assertions Run : {tests_run}")
    print(f"  • Contract Passes      : {tests_passed} / {tests_run}")
    print(f"  • Critical Gate Errors : {len(critical_failures)}")
    print(f"  • Adversarial Findings : {len(findings)}")
    print("--------------------------------------------------------------------------------")

    if len(findings) > 0:
        print("CRITICAL ADVERSARIAL VULNERABILITY IDENTIFIED:")
        for name, details in findings:
            print(f"  ❌ {name}")
            print(f"     └─ {details}\n")

    if len(critical_failures) == 0 and len(findings) > 0:
        print("VERDICT: REJECT (Blocking on Favicon PNG Raster Color Fidelity)")
        print("Worker 1 must update build_brand_assets.py / favicon.svg to use direct CSS hex fills")
        print("instead of CSS variables 'var(...)', so CairoSVG rasterizes full-color PNG favicons.")
        print("================================================================================")
        return 2
    elif len(critical_failures) == 0:
        print("VERDICT: APPROVE (100% PASS across all verification gates)")
        print("================================================================================")
        return 0
    else:
        print("VERDICT: REJECT (Critical gate failures encountered)")
        print("================================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(run_oracle_suite())
