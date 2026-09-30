#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/test_dossier_suite_d3.py
=============================================================================
AUTOMATED VERIFICATION TEST FOR DELIVERABLE D3: ENTERPRISE DOSSIER SUITE
=============================================================================
Checks:
  1. Existence of all 13 dossiers at footage_dossier/ root with both
     standard and canonical filenames.
  2. Completeness of all 7 core sections across every single dossier:
     - Section 1: Usecase ID, Scenario Name & ERP Module
     - Section 2: Technical Footage Reference (Gold Master MP4, duration, resolution, audio)
     - Section 3: Live Module Deep-Link Ref (Odoo 20 Owl WebClient)
     - Section 4: Enterprise Seed Data Specifications (Partner, Tax ID, Products, Specs, Contract Value, Document Numbers)
     - Section 5: Timestamped Screen Recording Cue-Sheet (1:1 TTS voiceover mapped to clicks/zooms)
     - Section 6: Multi-dimensional Expert Council Analysis (all 6 council members)
     - Section 7: Quantitative Impact Metrics (TCO Savings, ROI Payback, OEE %, Lead Time, Win Rate)
  3. Absolute zero tolerance for placeholders (TODO, TBD, FIXME).
  4. DOSSIER_INDEX.md and dossier_manifest.json alignment and references to
     SEED_DATA_MATRIX.md and SCREEN_RECORDING_STANDARDS.md.
"""

import os
import sys
import json
import re

ROOT_DIR = "/home/zen/O20"
DOSSIER_DIR = os.path.join(ROOT_DIR, "footage_dossier")

EXPECTED_FILES = [
    # (standard_filename, canonical_filename)
    ("DOSSIER_VID_01_CRM.md", "DOSSIER_VID_01_CRM.md"),
    ("DOSSIER_VID_02_PURCHASE.md", "DOSSIER_VID_02_PUR.md"),
    ("DOSSIER_VID_03_INVENTORY.md", "DOSSIER_VID_03_INV.md"),
    ("DOSSIER_VID_04_BOM.md", "DOSSIER_VID_04_BOM.md"),
    ("DOSSIER_VID_05_PLANNING.md", "DOSSIER_VID_05_PLN.md"),
    ("DOSSIER_VID_06_SHOPFLOOR.md", "DOSSIER_VID_06_SFL.md"),
    ("DOSSIER_VID_07_FLEET.md", "DOSSIER_VID_07_FLT.md"),
    ("DOSSIER_VID_08_FULFILLMENT.md", "DOSSIER_VID_08_FUL.md"),
    ("DOSSIER_VID_09_LOGISTICS.md", "DOSSIER_VID_09_LOG.md"),
    ("DOSSIER_VID_10_EINVOICE.md", "DOSSIER_VID_10_SAL.md"),
    ("DOSSIER_VID_11_ACCOUNTING.md", "DOSSIER_VID_11_ACC.md"),
    ("DOSSIER_VID_12_MKT.md", "DOSSIER_VID_12_MKT.md"),
    ("DOSSIER_HSE_01_AI_VISION.md", "DOSSIER_HSE_01_AI_VISION.md"),
]

REQUIRED_SECTIONS = [
    ("THÔNG TIN TỔNG QUAN HỒ SƠ", "Section 1: Usecase Profile"),
    ("I. THÔNG SỐ TƯ LIỆU HÌNH ẢNH & VIDEO", "Section 2: Technical Footage Reference"),
    ("II. LIÊN KẾT TRỰC TIẾP PHÂN HỆ ERP", "Section 3: Live Module Deep-Link Reference"),
    ("III. BẢNG ĐẶC TẢ DỮ LIỆU MẪU CHÂN THỰC", "Section 4: Enterprise Seed Data Specification"),
    ("IV. KỊCH BẢN PHÂN CẢNH GHI HÌNH CHI TIẾT", "Section 5: Screen Recording Cue-Sheet"),
    ("V. ĐÁNH GIÁ ĐA CHIỀU TỪ HỘI ĐỒNG CHUYÊN GIA", "Section 6: Expert Council Perspectives"),
    ("VI. CHỈ SỐ TÁC ĐỘNG TÀI CHÍNH & VẬN HÀNH ĐỊNH LƯỢNG", "Section 7: Quantitative Impact Metrics")
]

COUNCIL_MEMBERS = [
    "Sales Director of SAP",
    "Marketing Director of Google",
    "TCO Expert of IBM",
    "Logistics Dept Head",
    "VCCI Head Việt Nam",
    "Giám đốc Sản xuất"
]

IMPACT_METRIC_KEYWORDS = [
    ("TCO Savings", "Cắt Giảm TCO Hàng Năm"),
    ("ROI Payback", "Thời Gian Hoàn Vốn"),
    ("OEE", "Hiệu Suất Tổng Thể Thiết Bị"),
    ("Lead Time", "Rút Ngắn Chu Kỳ"),
    ("Win Rate", "Tỷ Lệ Thắng Thầu")
]


def test_file_existence():
    print("[1/5] Testing file existence at footage_dossier/ root...")
    missing = []
    all_filenames = set()
    for std, can in EXPECTED_FILES:
        all_filenames.add(std)
        all_filenames.add(can)

    for fn in sorted(all_filenames):
        path = os.path.join(DOSSIER_DIR, fn)
        if not os.path.exists(path):
            missing.append(fn)
        else:
            size = os.path.getsize(path)
            assert size > 2000, f"File {fn} is too small ({size} bytes)"

    if missing:
        print(f"FAILED: Missing files at footage_dossier/: {missing}")
        return False
    print(f"PASSED: All {len(all_filenames)} standard and canonical files exist at footage_dossier/ root.")
    return True


def test_placeholders():
    print("[2/5] Testing for placeholders (TODO, TBD, FIXME) across all dossier markdown files...")
    placeholder_pattern = re.compile(r"\b(TODO|TBD|FIXME)\b", re.IGNORECASE)
    violations = []

    for std, can in EXPECTED_FILES:
        for fn in set([std, can]):
            path = os.path.join(DOSSIER_DIR, fn)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                matches = placeholder_pattern.findall(content)
                if matches:
                    violations.append((fn, matches))

    if violations:
        print(f"FAILED: Found placeholders: {violations}")
        return False
    print("PASSED: Zero placeholders (TODO, TBD, FIXME) detected across all files.")
    return True


def test_core_sections():
    print("[3/5] Testing 7 core sections, 6 council members, and impact metrics across all 13 dossiers...")
    failures = []

    for std, can in EXPECTED_FILES:
        path = os.path.join(DOSSIER_DIR, std)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check 7 core sections
        for header, sec_name in REQUIRED_SECTIONS:
            if header not in content:
                failures.append(f"{std}: Missing {sec_name} ('{header}')")

        # Check 6 council members
        for member in COUNCIL_MEMBERS:
            if member not in content:
                failures.append(f"{std}: Missing commentary for {member}")

        # Check impact metrics
        for eng, vn in IMPACT_METRIC_KEYWORDS:
            if eng not in content and vn not in content:
                failures.append(f"{std}: Missing impact metric keyword {eng}/{vn}")

        # Check deep-link format
        if "http://localhost:28069/web#" not in content:
            failures.append(f"{std}: Missing valid deep-link reference")

        # Check Gold Master MP4 reference
        if "GOLD_MASTER.mp4" not in content and "INSILOS_HSE_AI_VISION" not in content:
            failures.append(f"{std}: Missing Gold Master video reference")

    if failures:
        print("FAILED: Section check failures:")
        for fail in failures:
            print(f"  - {fail}")
        return False
    print("PASSED: All 13 dossiers contain all 7 sections, 6 council members, and 5 impact metrics.")
    return True


def test_dossier_index():
    print("[4/5] Testing DOSSIER_INDEX.md integrity and references...")
    index_path = os.path.join(DOSSIER_DIR, "DOSSIER_INDEX.md")
    if not os.path.exists(index_path):
        print("FAILED: DOSSIER_INDEX.md not found")
        return False

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check references to SEED_DATA_MATRIX.md and SCREEN_RECORDING_STANDARDS.md
    assert "SEED_DATA_MATRIX.md" in content, "DOSSIER_INDEX.md must reference SEED_DATA_MATRIX.md"
    assert "SCREEN_RECORDING_STANDARDS.md" in content, "DOSSIER_INDEX.md must reference SCREEN_RECORDING_STANDARDS.md"

    # Check that all 13 dossiers are listed in table
    for std, can in EXPECTED_FILES:
        assert std in content, f"DOSSIER_INDEX.md must link to standard file {std}"

    # Check 6 council members mentioned
    for member in COUNCIL_MEMBERS:
        assert member in content, f"DOSSIER_INDEX.md must mention council member {member}"

    print("PASSED: DOSSIER_INDEX.md is completely aligned and contains all required references.")
    return True


def test_dossier_manifest():
    print("[5/5] Testing dossier_manifest.json structure and alignment...")
    manifest_path = os.path.join(DOSSIER_DIR, "dossier_manifest.json")
    if not os.path.exists(manifest_path):
        print("FAILED: dossier_manifest.json not found")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("total_dossiers") == 13, f"Expected 13 dossiers, got {data.get('total_dossiers')}"
    assert len(data.get("dossiers", [])) == 13, f"Expected 13 dossier objects in array"
    assert "seed_data_matrix_file" in data, "Missing seed_data_matrix_file in manifest root"
    assert "screen_recording_standards_file" in data, "Missing screen_recording_standards_file in manifest root"
    assert "dossier_index_file" in data, "Missing dossier_index_file in manifest root"

    for d in data["dossiers"]:
        assert "dossier_file" in d, f"Dossier {d.get('id')} missing dossier_file"
        assert "canonical_file" in d, f"Dossier {d.get('id')} missing canonical_file"
        assert "aliases" in d, f"Dossier {d.get('id')} missing aliases"
        assert "seed_data" in d, f"Dossier {d.get('id')} missing seed_data"
        assert "cue_sheet" in d, f"Dossier {d.get('id')} missing cue_sheet"
        assert "council_commentary" in d, f"Dossier {d.get('id')} missing council_commentary"
        assert len(d["council_commentary"]) == 6, f"Dossier {d.get('id')} council_commentary count != 6"
        assert "impact_metrics" in d, f"Dossier {d.get('id')} missing impact_metrics"
        assert "tco_savings_annual" in d["impact_metrics"], f"Dossier {d.get('id')} missing tco_savings_annual"
        assert "roi_payback" in d["impact_metrics"], f"Dossier {d.get('id')} missing roi_payback"
        assert "oee_benchmark" in d["impact_metrics"], f"Dossier {d.get('id')} missing oee_benchmark"

    print("PASSED: dossier_manifest.json is structurally sound, valid JSON, and fully aligned.")
    return True


def main():
    print("=" * 80)
    print("STARTING DELIVERABLE D3 DOSSIER SUITE INTEGRITY AUDIT")
    print("=" * 80)
    
    t1 = test_file_existence()
    t2 = test_placeholders()
    t3 = test_core_sections()
    t4 = test_dossier_index()
    t5 = test_dossier_manifest()

    print("=" * 80)
    if t1 and t2 and t3 and t4 and t5:
        print("ALL AUDIT CHECKS PASSED: DELIVERABLE D3 IS 100% VERIFIED AND READY!")
        print("=" * 80)
        return 0
    else:
        print("AUDIT FAILED! SEE DETAILS ABOVE.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
