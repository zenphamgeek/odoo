#!/usr/bin/env python3
"""
Innoria Enterprise Bilingual (VN - EN) Engine & Database Synchronizer
Translates all 14 Innoria website templates into Executive Enterprise English,
constructs dual JSONB arch_db {"vi_VN": arch_vn, "en_US": arch_en},
and synchronizes with Odoo database.
"""

import os
import re
import json
import psycopg2

def extract_template_arch(xml_path, template_id, full_key):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = rf'(<template\s+[^>]*id=["\']{template_id}["\'][^>]*>)(.*?)(</template>)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Template '{template_id}' not found in {xml_path}")
    
    open_tag = match.group(1)
    body = match.group(2)
    name_match = re.search(r'name=["\']([^"\']+)["\']', open_tag)
    name_attr = f' name="{name_match.group(1)}"' if name_match else ''
    return f'<t t-name="{full_key}"{name_attr}>{body}</t>'

# Executive Domain Translation Dictionary (Strict Industrial & Enterprise Lexicon)
VN_EN_TERMS = [
    # Navigation & General
    ("Tham Vấn 3 Giờ", "3-Hour Consultation"),
    ("Nền Tảng", "Platform"),
    ("Giải Pháp", "Solutions"),
    ("Ngành Nghề", "Industries"),
    ("Về Innoria", "About Innoria"),
    ("Về Chúng Tôi", "About Us"),
    ("Liên Hệ", "Contact Us"),
    ("Khám Phá Giải Pháp", "Explore Solutions"),
    ("Khám Phá Nền Tảng", "Explore Platform"),
    ("Tìm Hiểu Thêm", "Learn More"),
    ("Xem Thêm", "Read More"),
    ("Bắt Đầu Ngay", "Get Started"),
    ("Tư Vấn Chuyên Sâu", "Executive Consultation"),
    ("Đặt lịch tham vấn kiến trúc", "Schedule Architecture Consultation"),
    ("Di sản &amp; Hành trình 18 năm", "Heritage &amp; 18-Year Journey"),
    ("Di sản & Hành trình 18 năm", "Heritage & 18-Year Journey"),
    ("Gửi Yêu Cầu Tham Vấn", "Submit Consultation Request"),

    # Hero & Core Messaging
    ("Khai Phóng Năng Lực Con Người &amp; Công Nghệ", "Empowering Human Potential &amp; Technology"),
    ("Khai Phóng Năng Lực Con Người & Công Nghệ", "Empowering Human Potential & Technology"),
    ("Khai Phóng Năng Lực<br/><span style=\"color:#0284C7;\">Con Người</span> &amp; Công Nghệ.", "Empowering Human<br/><span style=\"color:#0284C7;\">Potential</span> &amp; Technology."),
    ("Khai Phóng Năng Lực<br/>Con Người &amp; Công Nghệ.", "Empowering Human<br/>Potential &amp; Technology."),
    ("Kiến Trúc Đám Mây Chuyên Biệt", "Tailored Cloud Architecture"),
    ("Hệ Thống Trí Tuệ Nhân Tạo MOJO AI", "MOJO AI Multi-Agent Intelligence"),
    ("Nền Tảng Tự Chủ Vận Hành Doanh Nghiệp INSILOS", "INSILOS Autonomous Enterprise Operations Platform"),
    ("Chuẩn Mực An Toàn &amp; Pháp Lý Toàn Diện", "Comprehensive Security &amp; Compliance Standards"),
    ("Chuẩn Mực An Toàn & Pháp Lý Toàn Diện", "Comprehensive Security & Compliance Standards"),
    ("Nền Tảng Cốt Lõi", "Core Platform"),
    ("4 Trụ Cột Nền Tảng Lõi", "4 Core Platform Pillars"),

    # 4 Pillars & Products
    ("Nền tảng No-Code / Low-Code siêu tốc: Xây dựng ứng dụng doanh nghiệp tùy biến sâu theo chuẩn 3h -> 3d -> 3w -> 3m.",
     "Ultra-rapid No-Code / Low-Code platform: Build deeply customized enterprise applications with 3h -> 3d -> 3w -> 3m agile standard."),
    ("Mạng lưới AI đa tác nhân phối hợp nhận thức VLM See-Detect-Analyze-Adapt và lập kế hoạch tự chủ Reason-Solve-Plan-Execute.",
     "Multi-agent AI network combining VLM perception (See-Detect-Analyze-Adapt) with autonomous reasoning and planning (Reason-Solve-Plan-Execute)."),
    ("Hệ thống tự động hóa lập trình và thực thi hợp đồng thông minh: Chuyển hóa đặc tả nghiệp vụ thành mã nguồn có kiểm chứng hình thức.",
     "Automated coding & smart contract execution: Transform business specifications into formally verified production code."),
    ("Hệ điều hành vận hành số doanh nghiệp: Hợp nhất ERP, MES, WMS, TMS, HRM và Kế toán Việt Nam thành một khối thống nhất.",
     "Unified enterprise operating system: Orchestrating ERP, MES, WMS, TMS, HRM, and Vietnam Statutory Accounting into a single fabric."),
    ("Kiến tạo ứng dụng tùy biến sâu, rút ngắn 80% thời gian phát triển", "Create deeply customized apps, cutting 80% development lead time"),
    ("Trí tuệ nhân tạo đa tác nhân tự chủ giải quyết bài toán phức hợp", "Multi-agent AI autonomously solving complex mission-critical challenges"),
    ("Kỹ nghệ phần mềm tự động hóa & giải pháp blockchain tin cậy cao", "Automated software engineering & high-assurance blockchain solutions"),
    ("Hệ điều hành tích hợp vận hành doanh nghiệp toàn diện chuẩn ERP", "Unified enterprise operations OS with next-generation autonomous ERP"),

    # Stats & Numbers
    ("Năm kỹ nghệ công nghệ", "Years of Tech Engineering"),
    ("Mục tiêu tối ưu hóa chi phí triển khai", "Target Deployment Cost Optimization"),
    ("Hỗ trợ 24/7 trực tiếp tại Việt Nam", "24/7 Direct Engineering Support in Vietnam"),
    ("Đổi mới sáng tạo liên tục", "Continuous Mission Innovation"),
    ("Độ Trễ Suy Luận", "Inference Latency"),
    ("Độ Chính Xác VLM", "VLM Accuracy"),
    ("Nút Tác Nhân Hoạt Động", "Active Agent Nodes"),
    ("Nguyên Mẫu", "Prototype"),
    ("Thực Nghiệm POC", "POC Trial"),
    ("Hệ Lõi Tự Chủ", "Sovereign Core"),
    ("Tuân Thủ Pháp Lý", "Statutory Compliance"),
    ("Rút Ngắn Khấu Hao", "Amortization Reduction"),
    ("Chu Kỳ Đóng Sổ", "Fast Closing Cycle"),
    ("BOM Đa Tầng", "Multi-Level BOM"),
    ("Thời Gian Lên Khung", "Scaffolding Time"),
    ("Bảo Mật Bất Biến", "Immutable Security"),
    ("Kiểm Chứng Hình Thức", "Formal Verification"),

    # About Story & Culture
    ("Thành lập 2008 · Bản sắc Việt Nam vươn tầm thế giới", "Founded 2008 · Vietnamese Engineering Heritage, Global Reach"),
    ("Từ Mạng Sáng Tạo đến INNORIA: Hơn 18 năm kiến tạo công nghệ nhân bản, vận hành chuẩn mực toàn cầu và nâng tầm năng lực số Việt Nam.",
     "From Creative Network to INNORIA: Over 18 years engineering human-centric technology, operating at global standards, and advancing Vietnam's digital sovereignty."),
    ("Công nghệ liên tục biến chuyển. Định hướng của chúng tôi luôn bất biến: tạo ra sự tiến bộ thiết thực cho con người, doanh nghiệp và xã hội.",
     "Technology constantly evolves. Our mission remains steadfast: delivering tangible progress for people, enterprises, and society."),
    ("Câu chuyện di sản", "Heritage Story"),
    ("Trưởng thành qua từng<br/>chu kỳ công nghệ.", "Matured through every<br/>technology cycle."),
    ("INNORIA không phải là một danh xưng vay mượn. Đó là sự tích lũy thực chứng: học hỏi, chuyển giao, thích ứng và luôn giữ vững trách nhiệm trọn vẹn trước khách hàng.",
     "INNORIA is not a borrowed identity. It represents empirical mastery: continuous learning, agile transfer, adaptation, and total accountability to our clients."),
    ("Văn hóa là bản sắc nội sinh", "Culture as Core Identity"),
    ("Sự kết tinh hài hòa<br/>của giá trị, tư duy và sứ mệnh.", "Harmonious synthesis<br/>of values, mindset, and mission."),
    ("Văn hóa của chúng tôi được định hình qua những lựa chọn kiên định: phát triển nội lực bản thân, song hành lớn mạnh cùng khách hàng, và không ngừng tiến bước ngay cả khi mục tiêu thích ứng theo thời cuộc.",
     "Our culture is forged through steadfast principles: cultivating inner technical mastery, growing symbiotically with clients, and advancing relentlessly as operational landscapes shift."),
    ("Phát triển nội lực bền bỉ", "Relentless Internal Mastery"),
    ("Song hành lớn mạnh cùng khách hàng", "Symbiotic Growth with Clients"),
    ("Thích ứng chủ động trước thách thức", "Proactive Adaptation to Challenges"),
    ("Mỗi thành viên làm chủ hành trình phát triển của chính mình. Những con người ưu tú hơn sẽ tạo nên những quyết sách sáng suốt hơn, hệ thống vững bền hơn và kết quả vượt trội hơn.",
     "Every engineer owns their mastery journey. Empowered people build sounder architectures, resilient platforms, and deliver superior operational outcomes."),
    ("Thành công không dừng lại ở việc bàn giao. Chúng tôi đồng hành cùng khách hàng, chia sẻ trách nhiệm trong suốt quá trình vận hành, tối ưu hóa và kiến tạo giá trị dài hạn.",
     "Success goes beyond delivery. We stand alongside our partners, sharing accountability throughout operations, optimization, and long-term value compounding."),
    ("Mục tiêu có thể biến động theo bối cảnh, nhưng năng lực kiên trì hành động và tư duy giải quyết vấn đề tới cùng là cam kết danh dự của đội ngũ INNORIA.",
     "Contexts may shift, but our resolve to execute and solve root problems with relentless rigor is INNORIA's solemn engineering commitment."),

    # Footer & Bottom
    ("Bản quyền", "Copyright"),
    ("Bảo lưu mọi quyền", "All Rights Reserved"),
    ("Chính Sách Bảo Mật", "Privacy Policy"),
    ("Điều Khoản Dịch Vụ", "Terms of Service"),
    ("Bản quyền © 2026 INNORIA Solutions JSC. Tất cả quyền được bảo lưu.", "Copyright © 2026 INNORIA Solutions JSC. All Rights Reserved."),
]

def translate_to_executive_english(xml_text):
    res = xml_text
    for vn, en in VN_EN_TERMS:
        res = res.replace(vn, en)
    
    # Specific navbar link text
    res = res.replace('>Nền Tảng<', '>Platform<')
    res = res.replace('>Giải Pháp<', '>Solutions<')
    res = res.replace('>Ngành Nghề<', '>Industries<')
    res = res.replace('>Về Innoria<', '>About Us<')
    res = res.replace('>Tham Vấn 3 Giờ<', '>3-Hour Consultation<')
    return res

def main():
    print("[*] Generating bilingual views and updating database...")
    
    # Target files
    module_dir = os.path.abspath("enterprise/insilos_website")
    xml_homepage = os.path.join(module_dir, "views/innoria_homepage.xml")
    xml_snippets = os.path.join(module_dir, "views/snippets_3d.xml")
    xml_pages = os.path.join(module_dir, "views/innoria_pages.xml")

    targets = [
        ("innoria_navbar", "insilos_website.innoria_navbar", xml_homepage),
        ("innoria_homepage_template", "insilos_website.innoria_homepage_template", xml_homepage),
        ("innoria_footer", "insilos_website.innoria_footer", xml_homepage),
        ("s_innoria_3d_topology", "insilos_website.s_innoria_3d_topology", xml_snippets),
        ("s_innoria_3d_architecture_deck", "insilos_website.s_innoria_3d_architecture_deck", xml_snippets),
        ("s_innoria_3d_solutions_erp", "insilos_website.s_innoria_3d_solutions_erp", xml_snippets),
        ("s_innoria_3d_erp_shift", "insilos_website.s_innoria_3d_erp_shift", xml_snippets),
        ("insilos_about_page", "insilos_website.insilos_about_page", xml_pages),
        ("insilos_platform_page", "insilos_website.insilos_platform_page", xml_pages),
        ("innoria_digiforce_page", "insilos_website.innoria_digiforce_page", xml_pages),
        ("innoria_blockchain_page", "insilos_website.innoria_blockchain_page", xml_pages),
        ("insilos_solutions_page", "insilos_website.insilos_solutions_page", xml_pages),
        ("insilos_industries_page", "insilos_website.insilos_industries_page", xml_pages),
        ("innoria_contactus", "insilos_website.innoria_contactus", xml_pages),
    ]

    # Connect to database innoria.insilos.com (and optionally innoria_prod)
    for dbname in ["innoria.insilos.com", "innoria_prod"]:
        try:
            conn = psycopg2.connect(
                host="127.0.0.1",
                port=5434,
                user="odoo",
                password="1NN0R1@2026",
                dbname=dbname
            )
            conn.autocommit = True
            cur = conn.cursor()
            print(f"\n[*] Connected to database: {dbname}")

            # 1. Ensure res_lang has both vi_VN and en_US active
            cur.execute("UPDATE res_lang SET active = true, url_code = 'vi' WHERE code = 'vi_VN';")
            cur.execute("UPDATE res_lang SET active = true, url_code = 'en' WHERE code = 'en_US';")
            
            # 2. Ensure website_lang_rel has both languages
            cur.execute("""
                INSERT INTO website_lang_rel (website_id, lang_id)
                SELECT 1, 91
                WHERE NOT EXISTS (SELECT 1 FROM website_lang_rel WHERE website_id = 1 AND lang_id = 91);
            """)
            cur.execute("""
                INSERT INTO website_lang_rel (website_id, lang_id)
                SELECT 1, 1
                WHERE NOT EXISTS (SELECT 1 FROM website_lang_rel WHERE website_id = 1 AND lang_id = 1);
            """)

            # 3. Update all 14 views with dual arch_db
            for tmpl_id, key, xml_path in targets:
                arch_vn = extract_template_arch(xml_path, tmpl_id, key)
                arch_en = translate_to_executive_english(arch_vn)
                
                arch_dict = {
                    "vi_VN": arch_vn,
                    "en_US": arch_en
                }

                cur.execute("SELECT id FROM ir_ui_view WHERE key = %s;", (key,))
                row = cur.fetchone()
                if row:
                    view_id = row[0]
                    cur.execute("""
                        UPDATE ir_ui_view
                        SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
                        WHERE id = %s;
                    """, (json.dumps(arch_dict), view_id))
                    print(f"  [✓] Updated view {key} with dual arch_db (VN: {len(arch_vn)} B, EN: {len(arch_en)} B)")
                else:
                    cur.execute("""
                        INSERT INTO ir_ui_view (name, key, type, mode, priority, active, arch_updated, arch_db, arch_fs, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, %s, 'qweb', 'primary', 16, true, true, %s::jsonb, NULL, 1, 1, NOW(), NOW());
                    """, (tmpl_id, key, json.dumps(arch_dict)))
                    print(f"  [✓] Created view {key} with dual arch_db")

            conn.close()
        except Exception as e:
            print(f"[!] Warning on db {dbname}: {e}")

    print("\n[✓] All views synchronized with dual VN-EN support!")

if __name__ == "__main__":
    main()
