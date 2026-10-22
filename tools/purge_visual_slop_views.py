#!/usr/bin/env python3
"""
tools/purge_visual_slop_views.py
Rigorously purges AI Slop visual elements and buzzword slash-badges from all QWeb XML views.
Validates each file with xml.etree.ElementTree to ensure 100% valid XML.
"""

import os
import re
import xml.etree.ElementTree as ET

VIEWS_DIR = "enterprise/insilos_website/views"

# Exact slop element patterns to remove cleanly
SLOP_ELEMENT_PATTERNS = [
    # Neon corners (all orientations TL/TR/BL/BR)
    r'\s*<div\s+class=\"[^\"]*ins-neon-corner[^\"]*\"[^>]*/>',
    # CRT Scanline overlays
    r'\s*<div\s+class=\"[^\"]*ins-hero-scanlines[^\"]*\"[^>]*/>',
    r'\s*<div\s+class=\"[^\"]*ins-scanline-overlay[^\"]*\"[^>]*/>',
    r'\s*<div\s+class=\"[^\"]*ins-cctv-scanlines[^\"]*\"[^>]*/>',
    r'\s*<div\s+class=\"[^\"]*ins-yolo-scanlines[^\"]*\"[^>]*/>',
    # Reticles and crosshairs
    r'\s*<div\s+class=\"[^\"]*ins-cctv-reticle[^\"]*\"[^>]*/>',
    r'\s*<div\s+class=\"[^\"]*ins-yolo-reticle[^\"]*\"[^>]*/>',
    r'\s*<div\s+class=\"ins-3d-crosshair\">\s*<div\s+class=\"ins-crosshair-ring\"/>\s*</div>',
    # Floating glowing orbs & ambient glow
    r'\s*<div\s+class=\"[^\"]*mojo-glow-orb[^\"]*\"[^>]*/>',
    r'\s*<div\s+class=\"[^\"]*hero-ambient-glow[^\"]*\"[^>]*/>',
    # Cybernetic grid backgrounds
    r'\s*<div\s+class=\"[^\"]*ins-3d-grid-bg[^\"]*\"[^>]*/>',
]

# Clean B2B title mappings for slash-badges
BADGE_TRANSLATIONS = {
    # 3D snippets
    "SOVEREIGN DIGITAL TWIN // THREE.JS 360° WEBGL": "Mô Hình 3D Thiết Bị V-LIFT 2500E",
    "MULTIMODAL SUPPLY CHAIN RADAR // VSIP TO SEAPORT": "Hành Lang Vận Tải Đa Phương Thức",
    "CINEMA HUD TELEMETRY // REAL-TIME ERP SYNCHRONIZATION": "Đồng Bộ Dữ Liệu ERP Thời Gian Thực",
    "INTERACTIVE ROI &amp; FACTORY CONFIGURATOR": "Công Cụ Định Lượng ROI Nhà Máy",
    
    # CCTV & Vision
    "AI COMPUTER VISION // CCTV LIVE HSE PATROL": "Thị Giác Máy Tính Giám Sát An Toàn HSE",
    "AI PATROL // NOMINAL": "Trạng Thái: Chuẩn Vận Hành",
    "YOLOv11x // PHÂN LOẠI KHUYẾT TẬT THỜI GIAN THỰC": "Phát Hiện &amp; Phân Loại Khuyết Tật Cơ Khí",

    # Homepage & Pages
    "CỤM TÁC NHÂN AI // MẠNG LƯỚI TÁC NHÂN TỰ CHỦ CẤP DOANH NGHIỆP": "Mạng Lưới Tác Nhân AI Doanh Nghiệp",
    "HỆ LÕI DOANH NGHIỆP TỰ CHỦ // NỀN TẢNG INSILOS": "Lõi Vận Hành Doanh Nghiệp Tự Hành",
    "TÍN NHIỆM &amp; PHÒNG THỦ TỰ CHỦ // BẢO MẬT CẤP TẬP ĐOÀN": "An Toàn &amp; Phòng Thủ Chủ Quyền",
    "HỘI ĐỒNG KIẾN TRÚC SƯ TRƯỞNG // ARCHITECTURE BOARD": "Hội Đồng Kiến Trúc Sư Trưởng",
    
    # Platform & Solutions
    "PLATFORM ARCHITECTURE // 4 TIERS": "Kiến Trúc Nền Tảng 4 Tầng",
    "LIVE BUS // 50.02 Hz": "Tần Số Lưới: 50.02 Hz",
    "SWARM CONSENSUS // REAL-TIME DISPATCH": "Đồng Thuận Tác Nhân: Điều Phối Trực Tiếp",
    "ENTERPRISE SOLUTIONS MATRIX // 4 PILLARS": "Ma Trận Giải Pháp 4 Trụ Cột",
    "LIVING KNOWLEDGE MESH // FABRIC": "Đồ Thị Tri Thức Doanh Nghiệp",
    "GRAPH CLUSTER // 1,418,920 TRIPLES": "Cụm Tri Thức: 1.418.920 Bộ Ba",
    "STREAMING OCR // 1,420 DOCS/HR": "Tốc Độ Bóc Tách: 1.420 Chứng Từ/Giờ",
    "CUSTOMS REGULATORY ENGINE // CIRCULAR 78 &amp; VAS 200/133": "Tuân Thủ Thông Tư 78 &amp; VAS 200",
    "REGULATORY ENGINE // TT 78 &amp; VAS 200/133": "Tuân Thủ Thông Tư 78 &amp; VAS 200",
    "SUBSTATION BUS // BAY CONTROLLER BCU-T1": "Điều Khiển Ngăn Trạm BCU-T1",

    # Home & Verticals
    "Physical World Invariants // Heavy Process Verticals": "Quy Chuẩn Vận Hành Thực Địa",
    "PHÂN HỆ 01 // MULTIMODAL DOCUMENT EXTRACTION": "Phân Hệ 01: Bóc Tách Chứng Từ Đa Phương Thức",
    "PHÂN HỆ 02 // SEMANTIC TOPOLOGY &amp; DIGITAL TWIN": "Phân Hệ 02: Sơ Đồ Cấu Trúc &amp; Bản Sao Số",
    "PHÂN HỆ 03 // REGULATORY REASONING &amp; FTA": "Phân Hệ 03: Suy Luận Pháp Lý &amp; Quy Tắc Xuất Xứ",
    "PHÂN HỆ 04 // FIELD SERVICE &amp; ASSET OPERATIONS": "Phân Hệ 04: Vận Hành Thiết Bị &amp; Bảo Trì Hiện Trường",
    "PHÒNG THÍ NGHIỆM SỐ HÓA VẬN HÀNH 48H // IEC 61850 GOOSE": "Phòng Thí Nghiệm Số Hóa Vận Hành 48 Giờ",
    "CORRIDOR STRATEGY // NORTHERN MARITIME &amp; MULTIMODAL FLEET": "Chiến Lược Hành Lang Hàng Hải &amp; Đội Xe Đa Phương Thức",

    # Sandbox & Resources
    "EXECUTIVE STUDIO LAUNCHPAD // LIVE SANDBOX": "Không Gian Trải Nghiệm Điều Hành Trực Tiếp",
    "SANDBOX TELEMETRY // REAL-TIME BUS": "Dữ Liệu Thao Tác Thời Gian Thực",
    "INTERACTIVE INDUSTRIAL WORKBENCH // 4 CORE TOOLS": "Bàn Thao Tác Kỹ Thuật Công Nghiệp",
    "3D ASSET SIMULATION &amp; SENSOR GAUGES // ISO 10816": "Mô Phỏng Thiết Bị 3D Theo Chuẩn ISO 10816",
    "CẢNH BÁO SỰ CỐ NGHIÊM TRỌNG // ĐÃ TẠO PHIẾU FSM": "Cảnh Báo Vận Hành: Đã Khởi Tạo Phiếu FSM",
    "C-LEVEL EXECUTIVE VALUE ENGINEERING // 3-YEAR FINANCIAL MODEL": "Mô Hình Tài Chính &amp; Giá Trị Đầu Tư 3 Năm",
    "PILOT READY // 14-DAY FIELD PROOF OF CONCEPT": "Sẵn Sàng Triển Khai Thử Nghiệm Thực Địa 14 Ngày",

    # Trust & Compliance
    "SOVEREIGN OPERATIONAL TRUST // APAC INFRASTRUCTURE": "Hạ Tầng Tín Nhiệm Vận Hành Doanh Nghiệp",
    "SLA 99.995% // P99 &lt; 15MS": "Cam Kết SLA 99.995% (Độ Trễ P99 &lt; 15ms)",
    "PLANE 4: MODEL RISK GOVERNANCE // EU AI ACT 2024/1689": "Quản Trị Rủi Ro AI Theo Chuẩn EU AI Act 2024/1689",
    "QĐ 749/QĐ-TTg // CĐS QUỐC GIA": "Quy Chuẩn Chuyển Đổi Số Quốc Gia (QĐ 749/QĐ-TTg)",
    "NQ 175/NQ-CP // TTDL QUỐC GIA": "Đề Án Trung Tâm Dữ Liệu Quốc Gia (NQ 175/NQ-CP)",
    "VAS 200 // B01-DN &amp; B02-DN": "Báo Cáo Tài Chính Chuẩn Mực VAS 200 (B01-DN, B02-DN)",
    "TT 78 // VIETTEL &amp; VNPT E-INVOICE": "Hóa Đơn Điện Tử Chuẩn Thông Tư 78",
    "3D RISK COCKPIT // BARRIER DEFENSE SIMULATOR": "Mô Phỏng Phòng Thủ Rủi Ro Đa Tầng",
    "CROSS-SYSTEM E2E RUNTIME // ERP &lt;-&gt; GRC INTERLOCK": "Đồng Bộ Khép Kín Hệ Thống ERP và GRC",

    # Snippets
    "OPERATIONAL TELEMETRY // REAL-TIME": "Dữ Liệu Vận Hành Thời Gian Thực",
    "MICRO-LEDGER BILLING // REAL-TIME METERING": "Hệ Thống Đo Lường &amp; Định Giá Tiêu Thụ",
    "SHOP-FLOOR TELEMETRY // ISA-95": "Tiêu Chuẩn Tích Hợp Xưởng Sản Xuất ISA-95",
    "CYBER-PHYSICAL SYSTEM TOPOLOGY // INDUSTRY 4.0": "Sơ Đồ Hệ Thống Không Gian Số - Thực",
    "EXECUTIVE AUDIT VAULT // ISO 45001 &amp; INDUSTRIAL HSE SUITE": "Hồ Sơ Kiểm Toán Tuân Thủ ISO 45001 &amp; HSE",
    "ZERO-TRUST ARCHITECTURE // SOVEREIGN SECURITY": "Kiến Trúc An Toàn Thông Tin Zero-Trust",
    "SOVEREIGN 3D DIGITAL TWIN &amp; CINEMA HUD SUITE // INSILOS ERP LIVE": "Mô Hình Số Hóa 3D &amp; Trực Quan Hóa ERP Live",
    "INSILOS INDUSTRIAL ENGINE // 3D DIGITAL TWIN &amp; REAL-TIME ERP": "Lõi Công Nghệ Doanh Nghiệp &amp; ERP Live",
}

def unslop_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    orig_content = content
    slop_count = 0

    # 1. Remove physical slop elements
    for pat in SLOP_ELEMENT_PATTERNS:
        matches = len(re.findall(pat, content))
        if matches > 0:
            content = re.sub(pat, '', content)
            slop_count += matches

    # 2. Replace slash-badges with clean human-written titles
    badge_count = 0
    for raw_badge, clean_badge in BADGE_TRANSLATIONS.items():
        search_str = f"<span>{raw_badge}</span>"
        replace_str = f"<span>{clean_badge}</span>"
        if search_str in content:
            c = content.count(search_str)
            content = content.replace(search_str, replace_str)
            badge_count += c

    if content != orig_content:
        # Validate XML before writing
        try:
            ET.fromstring(content)
        except ET.ParseError as e:
            print(f"[!] XML Validation Error in {fpath}: {e}")
            return False

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[✓] {os.path.basename(fpath)}: Removed {slop_count} slop elements, un-slopped {badge_count} badges (XML VALID)")
        return True
    return False

def main():
    print("=== RIGOROUS PURGE OF AI SLOP FROM QWEB VIEWS ===")
    total_modified = 0
    for root, _, files in os.walk(VIEWS_DIR):
        for f in sorted(files):
            if f.endswith('.xml'):
                fpath = os.path.join(root, f)
                if unslop_file(fpath):
                    total_modified += 1

    print(f"\n[✓] Completed: {total_modified} view files successfully un-slopped and validated!")

if __name__ == '__main__':
    main()
