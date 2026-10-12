#!/usr/bin/env python3
"""
Residual Polish Script for exact HTML-embedded strings.
"""

import re

updates = [
    (
        'enterprise/insilos_website/views/innoria_pages.xml',
        r'Khám nghiệm kiến trúc và chạy thực nghiệm trên tập dữ liệu mẫu của doanh nghiệp chỉ trong 3 ngày\.',
        'Thẩm định kiến trúc và triển khai thực nghiệm trên tập dữ liệu mẫu của doanh nghiệp chỉ trong 3 ngày.'
    ),
    (
        'enterprise/insilos_website/views/innoria_pages.xml',
        r'Đánh giá có hệ thống về khả năng tích hợp hệ thống di sản, các điểm nghẽn cơ sở dữ liệu và mức độ sẵn sàng của dữ liệu\.',
        'Đánh giá có hệ thống về khả năng tích hợp hệ thống hiện hữu (Legacy Systems), các điểm nghẽn cơ sở dữ liệu và mức độ sẵn sàng của dữ liệu.'
    ),
    (
        'enterprise/insilos_website/views/innoria_pages.xml',
        r'Kế hoạch sprint linh hoạt chìa khóa trao tay từ 6 đến 8 tuần với phân bổ nguồn lực cụ thể, tiến độ thực hiện và các mốc đánh giá hoàn vốn ROI rõ ràng\.',
        'Kế hoạch triển khai Sprint linh hoạt trọn gói từ 6 đến 8 tuần với phân bổ nguồn lực chi tiết, tiến độ thực hiện và các mốc đánh giá hoàn vốn ROI rõ ràng.'
    ),
    (
        'enterprise/insilos_website/views/platform_solutions.xml',
        r'Khóa Chặt Sai Lệch <span class="ins-gradient-aurora-text">0 Variance Budget</span>',
        'Triệt Tiêu Sai Lệch <span class="ins-gradient-aurora-text">0 Variance Budget</span>'
    ),
    (
        'enterprise/insilos_website/views/resources_about_demo.xml',
        r'nơi từng quyết định của tác tử được kiểm chứng bằng mật mã học',
        'nơi từng quyết định của tác nhân AI được kiểm chứng bằng mật mã học'
    ),
    (
        'enterprise/insilos_website/views/industries.xml',
        r'Phương pháp luận triển khai chìa khóa trao tay \(Turnkey Deployment\)',
        'Phương pháp luận triển khai trọn gói (Turnkey Deployment)'
    ),
    (
        'enterprise/insilos_website/views/industries.xml',
        r'Khóa Chặt Sai Lệch <span class="text-warning">-70% Sự Cố OOS/OOT</span>',
        'Kiểm Soát Nghiêm Ngặt: <span class="text-warning">-70% Sự Cố OOS/OOT</span>'
    ),
    (
        'enterprise/insilos_website/views/brochure.xml',
        r'mô hình tính toán TCO/ROI cá nhân hóa cho cơ sở sản xuất của bạn\.',
        'mô hình phân tích TCO/ROI tối ưu hóa riêng cho cơ sở sản xuất của doanh nghiệp.'
    ),
    (
        'enterprise/insilos_website/views/home.xml',
        r'và tiêu chuẩn ISO 27001 của bạn\.',
        'và tiêu chuẩn quốc tế ISO 27001.'
    ),
    (
        'enterprise/insilos_website/views/home.xml',
        r'bất kỳ thông tin nào của bạn\.',
        'bất kỳ thông tin nào của doanh nghiệp.'
    )
]

import os
import sys
from pathlib import Path
import lxml.etree

REPO_ROOT = Path('/home/zen/O20').resolve()

for fpath, pattern, replacement in updates:
    # 1. Path Traversal & Boundary Guard
    if '..' in fpath or fpath.startswith('/'):
        sys.stderr.write(f"Security error: Invalid file path '{fpath}' (traversal forbidden)\n")
        sys.exit(1)

    target_file = (REPO_ROOT / fpath).resolve()
    if not str(target_file).startswith(str(REPO_ROOT)):
        sys.stderr.write(f"Security error: File path '{target_file}' escapes workspace root\n")
        sys.exit(1)

    if not target_file.exists():
        print(f"[!] {fpath}: File not found, skipping.")
        continue

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        # 2. AST Safety Verification: verify XML well-formedness before persisting
        try:
            lxml.etree.fromstring(new_content.encode('utf-8'))
        except lxml.etree.XMLSyntaxError as err:
            sys.stderr.write(f"AST Safety violation: Regex replacement in {fpath} corrupted XML AST: {err}\n")
            sys.exit(1)

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[✓] {fpath}: {count} replacement(s) applied (AST verified).")
    else:
        print(f"[-] {fpath}: pattern not found: {pattern[:40]}")
