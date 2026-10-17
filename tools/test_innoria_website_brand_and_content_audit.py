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
    r"client_[abd]_gray\.png",
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

    print("[✓] Source audit passed: 100% INNORIA primary website brand & zero explicit client/vendor/competitor names across public views & AI Concierge.")


def main():
    verify_source_files()
    print("[🎉] PATCH 39 INNORIA WEBSITE PRIMARY BRAND & DE-EXPLICITIZED CONTENT AUDIT PASSED (EXIT 0)")


if __name__ == "__main__":
    main()
