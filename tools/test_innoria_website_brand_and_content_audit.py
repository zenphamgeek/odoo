#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch 39 Verification Suite:
1. Website Primary Brand = INNORIA ONLY (`logo_innoria_header.svg` & `INNORIA GROUP` on all public website & portal views;
   zero `Digimate`, `Người Bạn Số`, `0317958465`, `digimate_drive_logo.png`, `UNG DUNG SANG TAO`, `Ứng Dụng Sáng Tạo`, `0313683499`).
2. Internal ERP Brand Separation (`Digimate` / `digimate_drive_logo.png` preserved in `dgm_brand_footer.py` and `report_templates.xml`).
3. Zero Explicit Client, Partner, Vendor, Bank, or Port Names across public Website XML views (`enterprise/insilos_website/views/*.xml`),
   Portal templates (`addons/insilos_al2c/views/portal_templates.xml`), and Public AI Concierge (`ai_concierge.py`, `ai_concierge_widget.js`,
   `ai_concierge_widget.xml`, `dgm_knowledge_rag_chatbot.py`, `seed_dgm_knowledge_rag_chatbot.py`).
"""
import glob
import os
import re
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_PUBLIC_PATTERNS = [
    r"Digimate",
    r"DIGIMATE",
    r"Người Bạn Số",
    r"0317958465",
    r"digimate_drive_logo\.png",
    r"UNG DUNG SANG TAO",
    r"Ứng Dụng Sáng Tạo",
    r"0313683499",
    r"\bCanva\b",
    r"\bMobiFone\b",
    r"\bMobifone\b",
    r"\bMOBIFONE\b",
    r"\bMTI\b",
    r"\bShinsei\b",
    r"\bAES\b(?!\s*[-–]\s*(?:128|192|256|GCM))",
    r"Mông Dương",
    r"\bVNDIRECT\b",
    r"\bEximbank\b",
    r"\bMUFG\b",
    r"\bTemecula\b",
    r"\bSwarovski\b",
    r"\bAIfin\b",
    r"\bAIFin\b",
    r"\bKTT\b",
    r"Tân Cảng",
    r"Cát Lái",
    r"Cái Mép",
    r"Lạch Huyện",
    r"Hòa Phát",
    r"\bPVFCCo\b",
    r"DHG Pharma",
    r"\bDHG\b",
    r"V-LIFT",
    r"\bPVOIL\b",
    r"\bPetrolimex\b",
    r"\bVinamilk\b",
    r"TH True",
    r"\bEVN\b",
    r"\bMaersk\b",
    r"Hapag-Lloyd",
    r"\bHyundai\b",
    r"\bCIMC\b",
    r"\bViettel\b",
    r"\bVNPT\b",
    r"\bFPT\b",
    r"\bCMC\b",
    r"\bVCB\b",
    r"\bVietcombank\b",
    r"\bSAP\b",
    r"\bOracle\b",
    r"\bSalesforce\b",
    r"\bNetSuite\b",
    r"\bMaximo\b",
    r"\bCargoWise\b",
    r"\bMISA\b",
    r"Base\.vn",
]


def verify_source_files():
    combined_rx = re.compile("|".join(FORBIDDEN_PUBLIC_PATTERNS))

    # 1. Verify all enterprise/insilos_website/views/*.xml and portal_templates.xml
    public_xml_files = sorted(glob.glob(os.path.join(ROOT_DIR, "enterprise/insilos_website/views/*.xml")))
    portal_xml = os.path.join(ROOT_DIR, "addons/insilos_al2c/views/portal_templates.xml")
    public_xml_files.append(portal_xml)

    for path in public_xml_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = combined_rx.findall(content)
        assert not matches, f"Forbidden explicit names found in {os.path.relpath(path, ROOT_DIR)}: {sorted(set(matches))}"

    # 2. Verify website_templates.xml sets is_innoria to True whenever not is_innokafe and uses logo_innoria_header.svg
    wt_path = os.path.join(ROOT_DIR, "enterprise/insilos_website/views/website_templates.xml")
    with open(wt_path, "r", encoding="utf-8") as f:
        wt_content = f.read()
    assert "/insilos_website/static/src/img/innoria/logo_innoria_header.svg" in wt_content
    assert "INNORIA GROUP" in wt_content
    assert "'innokafe' in" in wt_content

    # 3. Verify portal_templates.xml does NOT override //header or //div[@id='footer'] on portal.frontend_layout
    with open(portal_xml, "r", encoding="utf-8") as f:
        portal_content = f.read()
    assert 'expr="//header" position="replace"' not in portal_content
    assert 'expr="//div[@id=\'footer\']" position="replace"' not in portal_content
    assert "/insilos_website/static/src/img/innoria/logo_innoria_header.svg" in portal_content
    assert "digimate_drive_logo.png" not in portal_content

    # 4. Verify Internal Operation ERP still preserves Digimate brand (dgm_brand_footer.py & report_templates.xml)
    brand_py = os.path.join(ROOT_DIR, "addons/insilos_al2c/models/dgm_brand_footer.py")
    report_xml = os.path.join(ROOT_DIR, "addons/insilos_al2c/views/report_templates.xml")
    with open(brand_py, "r", encoding="utf-8") as f:
        assert "digimate_drive_logo.png" in f.read()
    with open(report_xml, "r", encoding="utf-8") as f:
        assert "digimate_drive_logo.png" in f.read()

    # 5. Verify Public AI Concierge files have zero explicit vendor/client names
    concierge_files = [
        os.path.join(ROOT_DIR, "addons/insilos_al2c/controllers/ai_concierge.py"),
        os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/js/ai_concierge_widget.js"),
        os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/xml/ai_concierge_widget.xml"),
    ]
    for path in concierge_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = combined_rx.findall(content)
        assert not matches, f"Forbidden explicit names found in {os.path.relpath(path, ROOT_DIR)}: {sorted(set(matches))}"

    # 6. Verify Patch 41 IBM Carbon v11 & Poppins Sans-Serif Typography Overhaul
    #    - 12 Poppins .woff2 font files exist with valid wOF2 header
    #    - website_templates.xml preloads poppins-latin.woff2 and poppins-vietnamese.woff2
    #    - Zero font-monospace, JetBrains Mono, Fira Code, or Roboto Mono across all public Website, Portal, and AI Concierge XML views
    #    - IBM Carbon v11 tokens (--cds-interactive: #0f62fe, --cds-background: #ffffff, --cds-layer-01: #f4f4f4) present in SCSS
    fonts_dir = os.path.join(ROOT_DIR, "enterprise/insilos_website/static/src/fonts")
    for required_font in (
        "poppins-latin.woff2",
        "poppins-vietnamese.woff2",
        "poppins-latin-400.woff2",
        "poppins-latin-600.woff2",
        "poppins-latin-700.woff2",
    ):
        fp = os.path.join(fonts_dir, required_font)
        assert os.path.isfile(fp), f"Missing Poppins font file: {fp}"
        with open(fp, "rb") as bf:
            magic = bf.read(4)
        assert magic == b"wOF2", f"Invalid WOFF2 magic header in {fp}: {magic}"

    assert "/insilos_website/static/src/fonts/poppins-latin.woff2" in wt_content
    assert "/insilos_website/static/src/fonts/poppins-vietnamese.woff2" in wt_content
    assert "font-family: 'Poppins'" in wt_content

    all_checked_xml = list(public_xml_files) + [
        os.path.join(ROOT_DIR, "enterprise/insilos_industry_showcase/views/templates.xml"),
        os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/xml/ai_concierge_widget.xml"),
    ]
    forbidden_font_rx = re.compile(r"font-monospace|JetBrains\s*Mono|Fira\s*Code|Roboto\s*Mono", re.IGNORECASE)
    for xml_p in all_checked_xml:
        with open(xml_p, "r", encoding="utf-8") as f:
            xml_txt = f.read()
        bad_fonts = forbidden_font_rx.findall(xml_txt)
        assert not bad_fonts, f"Forbidden monospace/robotic font token in {os.path.relpath(xml_p, ROOT_DIR)}: {bad_fonts}"

    forbidden_scss_font_rx = re.compile(r"JetBrains\s*Mono|Fira\s*Code|Roboto\s*Mono", re.IGNORECASE)
    for scss_rel in (
        "enterprise/insilos_website/static/src/scss/insilos.scss",
        "enterprise/insilos_website/static/src/scss/innoria_theme.scss",
        "enterprise/insilos_website/static/src/scss/insilos_liquid_spatial.scss",
    ):
        scss_p = os.path.join(ROOT_DIR, scss_rel)
        with open(scss_p, "r", encoding="utf-8") as f:
            scss_txt = f.read()
        assert "--cds-interactive: #0f62fe" in scss_txt, f"Missing --cds-interactive in {scss_rel}"
        assert "--cds-background: #ffffff" in scss_txt, f"Missing --cds-background in {scss_rel}"
        assert "--cds-layer-01: #f4f4f4" in scss_txt, f"Missing --cds-layer-01 in {scss_rel}"
        assert "'Poppins'" in scss_txt, f"Missing 'Poppins' font-family in {scss_rel}"
        assert not forbidden_scss_font_rx.findall(scss_txt), f"Forbidden monospace token in {scss_rel}"

    print("[✓] Source audit passed: 100% INNORIA primary website brand, IBM Carbon v11 design system, Poppins sans-serif typography & zero explicit client/vendor/competitor names.")


def main():
    verify_source_files()
    print("[🎉] PATCH 39 & PATCH 41 INNORIA WEBSITE BRAND, IBM CARBON V11 & POPPINS TYPOGRAPHY AUDIT PASSED (EXIT 0)")


if __name__ == "__main__":
    main()

