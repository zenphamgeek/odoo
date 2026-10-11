#!/usr/bin/env python3
"""
tools/execute_full_codebase_unslop.py
Surgical unslop refactoring for InnoKafe views and static assets.
Eliminates:
- Em-dashes (—)
- AI vocabulary (showcase, vibrant, seamlessly, lan tỏa, khúc giao hòa)
- Tautological comments
"""

import re
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.atomic_io import atomic_write_text

def clean_file(path, replacements):
    if not os.path.exists(path):
        print(f"[!] File not found: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    orig = content
    for pattern, repl in replacements:
        if isinstance(pattern, str):
            content = content.replace(pattern, repl)
        else:
            content = pattern.sub(repl, content)

    if content != orig:
        atomic_write_text(path, content)
        print(f"[✓] Atomically refactored: {path}")
    else:
        print(f"[-] No changes needed: {path}")

def main():
    print("=== EXECUTING SURGICAL CODEBASE UNSLOP ===")

    # 1. products.xml
    clean_file("enterprise/innokafe_website/views/products.xml", [
        ("Độ lan tỏa và độ phức hợp của khí thơm.", "Cường độ và độ phong phú của hợp chất hương tự nhiên."),
        (" — ", ", "),
        ("—", ", "),
    ])

    # 2. snippets.xml
    clean_file("enterprise/innokafe_website/views/snippets.xml", [
        ("<!-- Snippet 5: Bean Showcase Grid -->", "<!-- Snippet 5: Bean Collection Grid -->"),
        ("<keywords>beans, showcase, products, specialty, cà phê hạt</keywords>", "<keywords>beans, collection, products, specialty, cà phê hạt</keywords>"),
        (" — ", ", "),
        ("—", ", "),
    ])

    # 3. story.xml
    clean_file("enterprise/innokafe_website/views/story.xml", [
        (" — ", ", "),
        ("—", ", "),
    ])

    # 4. taste_profiler.xml
    clean_file("enterprise/innokafe_website/views/taste_profiler.xml", [
        (" — ", ", "),
        ("—", ", "),
    ])

    # 5. solutions_b2b.xml
    clean_file("enterprise/innokafe_website/views/solutions_b2b.xml", [
        (" — ", ", "),
        ("—", ", "),
    ])

    # 6. contactus.xml
    clean_file("enterprise/innokafe_website/views/contactus.xml", [
        (" — ", ", "),
        ("—", ", "),
    ])

    # 7. website_templates.xml
    clean_file("enterprise/innokafe_website/views/website_templates.xml", [
        (" — ", ", "),
        ("—", ", "),
    ])

    # 8. SCSS: innokafe_liquid_spatial.scss
    clean_file("enterprise/innokafe_website/static/src/scss/innokafe_liquid_spatial.scss", [
        ("Vibrant Honey Gold", "Bright Honey Gold"),
        ("vibrant", "bright"),
    ])

    # 9. JS: innokafe_cart_drawer.js
    clean_file("enterprise/innokafe_website/static/src/js/innokafe_cart_drawer.js", [
        ("split('—')", "split(/[-—,]/)"),
        ("Client localStorage maintains state seamlessly", "Client localStorage maintains state locally"),
        (" — ", ", "),
    ])

    # 10. JS: innokafe_interactions.js
    clean_file("enterprise/innokafe_website/static/src/js/innokafe_interactions.js", [
        ("INNOKAFE SPECIALTY COFFEE BREW LAB — INTERACTIVE ENGINE", "INNOKAFE SPECIALTY COFFEE BREW LAB: INTERACTIVE ENGINE"),
        ("Nghi Thức Bản Địa — Tinh Hoa Đậm Sánh", "Nghi Thức Bản Địa, Tinh Hoa Đậm Sánh"),
        ("Áp Suất Hoàng Kim — Lớp Crema Dày Đậm", "Áp Suất Hoàng Kim, Lớp Crema Dày Đậm"),
        ("Vũ Điệu Dòng Nước — Thanh Tao Tinh Khiết", "Chiết Xuất Trọng Lực, Thanh Tao Tinh Khiết"),
        ("Ủ Lạnh Chậm Rãi — Ngọt Dịu Thanh Mát", "Ủ Lạnh Chậm Rãi, Ngọt Dịu Thanh Mát"),
        ("Áp Lực Khí Nén — Thể Chất Đa Tầng", "Áp Lực Khí Nén, Thể Chất Đa Tầng"),
        (" — ", ", "),
    ])

    # 11. JS: subscription_club.js
    clean_file("enterprise/innokafe_website/static/src/js/subscription_club.js", [
        ("INNOKAFE SPECIALTY COFFEE ARTISAN CLUB — 3-STEP SUBSCRIPTION WIZARD", "INNOKAFE SPECIALTY COFFEE ARTISAN CLUB: 3-STEP SUBSCRIPTION WIZARD"),
        ("// Set Loading State on Submit Button", "// Update submit button loading indicator"),
        (" — ", ", "),
    ])

    # 12. JS: taste_profiler.js
    clean_file("enterprise/innokafe_website/static/src/js/taste_profiler.js", [
        ("Bản sắc đại ngàn — Vị đậm đà ngút ngàn, ngọt sâu hậu vị", "Bản sắc đại ngàn, vị đậm đà sâu lắng, ngọt sâu hậu vị"),
        ("Tinh hoa sương mù — Chua thanh hoa nhài, trong trẻo tao nhã", "Hạt Arabica Cầu Đất, chua thanh hoa nhài, trong trẻo tao nhã"),
        ("Khúc giao hòa đỉnh cao — Ngọt ngào mật ong rừng, kem bơ sánh quyện", "Dòng hạt Heritage Red Honey, mật ong rừng, kem bơ sánh quyện"),
        ("Tiện lợi mọi lúc mọi nơi — Đẳng cấp cà phê phin giấy lọc Nhật Bản", "Phin giấy lọc tiện lợi, cà phê mộc nguyên bản chuẩn Nhật Bản"),
        ("Sảng khoái mùa hè — Chua ngọt bùng nổ, ủ lạnh 24h ngọt ngào", "Hương cam chanh tươi mát, vị ngọt dịu êm sau 24h ủ lạnh"),
        ("Chuẩn mực quầy bar chuyên nghiệp — Crema dày mịn, ổn định chiết xuất", "Phối trộn chuyên biệt cho quầy bar, crema dày mịn, chiết xuất ổn định"),
        (" — ", ", "),
    ])

    print("[✓] Finished all codebase unslop replacements.")

if __name__ == "__main__":
    main()
