#!/usr/bin/env python3
"""
tools/audit_and_unslop_website_content.py
==========================================
Council for Sovereign Enterprise Content & Linguistic Quality.
Purges AI-slop, robotic literal word-translations, and awkward phrasing across all website templates.
Elevates Vietnamese website copy to executive B2B standard: natural, authoritative, crisp, and domain-precise.
"""

import re
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def apply_unslop_to_file(filepath: Path, replacements: list):
    if not filepath.exists():
        print(f"[!] File not found: {filepath}")
        return False
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes_count = 0

    for old_str, new_str in replacements:
        if old_str in content:
            content = content.replace(old_str, new_str)
            changes_count += 1
        else:
            print(f"  [-] Target string not found in {filepath.name}: {old_str[:60]}...")

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[✓] {filepath.name}: Successfully applied {changes_count} content updates.")
        return True
    else:
        print(f"[i] {filepath.name}: No changes needed or already clean.")
        return False

def main():
    print("=== COUNCIL OF LINGUISTIC & CONTENT QUALITY: UNSLOP ENGINE ===")

    # 1. enterprise/insilos_website/views/snippets_3d.xml
    snippets_3d_file = REPO_ROOT / "enterprise/insilos_website/views/snippets_3d.xml"
    snippets_3d_replacements = [
        (
            "bầy đàn đặc vụ tự hành (Agent Swarms)",
            "cụm tác nhân AI tự chủ (Multi-Agent Swarms)"
        ),
        (
            "16 Nốt Tính Toán Độc Lập · Suy Luận VLM · Phá Vỡ Silo",
            "16 Nút Tính Toán Độc Lập · Suy Luận VLM · Phá Vỡ Ốc Đảo Dữ Liệu"
        )
    ]
    apply_unslop_to_file(snippets_3d_file, snippets_3d_replacements)

    # 2. enterprise/insilos_website/views/platform_solutions.xml
    platform_sol_file = REPO_ROOT / "enterprise/insilos_website/views/platform_solutions.xml"
    platform_sol_replacements = [
        ("Tác Tử AI Tự Trị Đạt", "Tác Nhân AI Tự Chủ Đạt"),
        ("Khám Phá Các Tác Tử AI", "Khám Phá Cụm Tác Nhân AI"),
        ("và tác tử AI tự trị — kiểm", "và cụm tác nhân AI tự chủ — kiểm")
    ]
    apply_unslop_to_file(platform_sol_file, platform_sol_replacements)

    # 3. enterprise/insilos_website/views/resources_about_demo.xml
    resources_file = REPO_ROOT / "enterprise/insilos_website/views/resources_about_demo.xml"
    resources_replacements = [
        ("module tác tử AI độc lập", "module tác nhân AI độc lập"),
        ("mô hình tác tử AI tự trị không phụ thuộc", "mô hình tác nhân AI tự chủ không phụ thuộc")
    ]
    apply_unslop_to_file(resources_file, resources_replacements)

    # 4. enterprise/insilos_website/views/innoria_pages.xml
    pages_file = REPO_ROOT / "enterprise/insilos_website/views/innoria_pages.xml"
    pages_replacements = [
        # /about
        (
            "Kỷ luật kỹ nghệ thép.<br/>Cam kết trách nhiệm trọn đời.",
            "Kỷ luật kỹ nghệ chuẩn mực.<br/>Cam kết trách nhiệm trọn đời."
        ),
        (
            "Tận tâm phụng sự trong nước.<br/>Sẵn sàng chuẩn mực toàn cầu.",
            "Thấu hiểu thị trường nội địa.<br/>Chuẩn mực kỹ nghệ toàn cầu."
        ),
        (
            "Một cuộc giải phẫu kỹ thuật trực diện vào hệ thống hiện tại của bạn: phát hiện rò rỉ chi phí, đo đạc rủi ro bảo mật và thiết kế lộ trình tự chủ trong 180 phút.",
            "Một phiên kiểm định chuyên sâu trực tiếp vào hiện trạng hệ thống của doanh nghiệp: bóc tách chính xác các điểm nghẽn chi phí, đo lường rủi ro an ninh và thiết lập lộ trình tự chủ vận hành trong 180 phút."
        ),
        (
            '<a href="#consultation" class="btn btn-innoria btn-lg px-4 py-3">Khởi Tạo Đánh Giá Kiến Trúc 3 Giờ</a>',
            '<a href="#consultation" class="btn ins-btn-lux ins-btn-lux-primary px-4 py-3 fw-bold">Khởi Tạo Đánh Giá Kiến Trúc 3 Giờ</a>'
        ),
        (
            '<a href="#story" class="btn btn-outline-primary btn-lg px-4 py-3 fw-bold">Di Sản &amp; Tuyên Ngôn Kỹ Nghệ</a>',
            '<a href="#story" class="btn ins-btn-lux ins-btn-lux-outline px-4 py-3 fw-bold">Di Sản &amp; Tuyên Ngôn Kỹ Nghệ</a>'
        ),
        (
            '<a href="/contactus" class="btn btn-innoria btn-lg px-5 py-3">Khởi Tạo Đánh Giá Kiến Trúc 180 Phút Cùng Kỹ Sư Trưởng</a>',
            '<a href="/contactus" class="btn ins-btn-lux ins-btn-lux-primary btn-lg px-5 py-3">Khởi Tạo Đánh Giá Kiến Trúc 180 Phút Cùng Kỹ Sư Trưởng</a>'
        ),

        # /platform
        (
            "Kiến Trúc Multi-Agent Swarm · Quyền Lực Tất Định · 100% Chủ Quyền Dữ Liệu.",
            "Kiến Trúc Multi-Agent Đa Luồng · Cơ Chế Kiểm Soát Tất Định · 100% Chủ Quyền Dữ Liệu."
        ),
        (
            "thành các tác tử hành động tự chủ với rào chắn an toàn (deterministic guardrails), cắt giảm tới 60% chi phí vận hành doanh nghiệp.",
            "thành các tác nhân AI tự chủ với rào chắn an toàn tất định (deterministic guardrails), giúp doanh nghiệp cắt giảm tới 60% chi phí vận hành."
        ),
        (
            "KÍCH HOẠT QUẦN THỂ TÁC TỬ",
            "KÍCH HOẠT ĐIỀU PHỐI MULTI-AGENT"
        ),
        (
            "// 5 Tác Tử Phối Hợp",
            "// 5 Tác Nhân AI Phối Hợp"
        ),
        (
            "LUỒNG PHẢN HỒI CỦA QUẦN THỂ TÁC TỬ:",
            "NHẬT KÝ PHỐI HỢP CỤM TÁC NHÂN AI:"
        ),
        (
            'Hệ thống sẵn sàng. Đang chờ tín hiệu vận hành... Nhấp "KÍCH HOẠT QUẦN THỂ TÁC TỬ" hoặc chọn kịch bản mẫu phía trên để chạy kiểm thử luồng phối hợp 5 tác tử.',
            'Hệ thống sẵn sàng. Đang chờ tín hiệu vận hành... Nhấp "KÍCH HOẠT ĐIỀU PHỐI MULTI-AGENT" hoặc chọn kịch bản mẫu phía trên để kiểm thử luồng phối hợp giữa 5 tác nhân chuyên trách.'
        ),
        (
            "Chiến Lược Doanh Nghiệp &amp; Quần Thể Tác Tử",
            "Chiến Lược Chuyển Đổi Số &amp; Cụm Tác Nhân AI"
        ),
        (
            "Tác tử tự hành giám sát chất lượng phủ sóng trạm BTS, dự báo nghẽn mạng trong các sự kiện đông người",
            "Tác nhân AI tự chủ giám sát chất lượng phủ sóng trạm BTS, dự báo nghẽn mạng trong các sự kiện đông người"
        ),
        (
            "Điều phối đồng bộ các mô hình diffusion, tác tử LLM và thị giác máy tính thời gian thực dưới một bộ SDK duy nhất.",
            "Điều phối đồng bộ các mô hình diffusion, tác nhân AI nền tảng LLM và thị giác máy tính thời gian thực trên một bộ SDK duy nhất."
        ),
        (
            "Tác tử soạn thảo văn bản quy chuẩn, tổng hợp hồ sơ thầu, bóc tách hợp đồng pháp lý và tóm tắt biên bản họp tự động.",
            "Tự động soạn thảo văn bản quy chuẩn, tổng hợp hồ sơ dự thầu, bóc tách điều khoản hợp đồng pháp lý và lập biên bản cuộc họp tự động."
        ),
        (
            "BẢNG ĐIỀU KHIỂN TÁC TỬ THỰC THI (HUD)",
            "BẢNG ĐIỀU PHỐI TÁC NHÂN AI THỜI GIAN THỰC (HUD)"
        ),
        (
            "NỐT CỤM MÁY CHỦ: VN-SOUTH-01",
            "NÚT TÍNH TOÁN CỤM MÁY CHỦ: VN-SOUTH-01"
        ),
        (
            '<span class="text-warning">Động cơ vLLM</span>',
            '<span class="text-warning">Bộ máy suy luận vLLM</span>'
        ),
        (
            "Khởi đầu hành trình tự động hóa tác tử thông minh với buổi làm việc chuyên sâu 3 giờ cùng đội ngũ kiến trúc sư trưởng INNORIA.",
            "Khởi đầu lộ trình tự động hóa tác nhân AI thông minh với phiên làm việc chuyên sâu 180 phút cùng đội ngũ kiến trúc sư trưởng INNORIA."
        ),
        (
            "consoleOutput.textContent = 'Hệ thống sẵn sàng. Nhấp \"KÍCH HOẠT QUẦN THỂ TÁC TỬ\" để bắt đầu luồng phối hợp 5 tác tử...';",
            "consoleOutput.textContent = 'Hệ thống sẵn sàng. Nhấp \"KÍCH HOẠT ĐIỀU PHỐI MULTI-AGENT\" để bắt đầu luồng phối hợp 5 tác nhân chuyên trách...';"
        ),
        (
            'consoleOutput.textContent = "KHỞI CHẠY QUẦN THỂ TÁC TỬ INNORIA SWARM // PHÂN TẦNG VẬN HÀNH CHỦ QUYỀN...\\n";',
            'consoleOutput.textContent = "KHỞI CHẠY HỆ THỐNG MULTI-AGENT INNORIA SWARM // ĐIỀU PHỐI VẬN HÀNH CHỦ QUYỀN...\\n";'
        ),

        # /no-code-platform
        (
            '<div class="df-eyebrow mb-2" style="color: #00F0FF;">MỘT HỆ LÕI DUY NHẤT. ĐA NĂNG LỰC CÔNG NGHỆ.</div>',
            '<div class="df-eyebrow mb-2" style="color: #00F0FF;">MỘT NỀN TẢNG DUY NHẤT. TOÀN DIỆN NĂNG LỰC VẬN HÀNH.</div>'
        ),
        (
            '<h3 class="display-6 fw-bold text-white mb-3">Động Cơ Hợp Nhất Đa Công Nghệ</h3>',
            '<h3 class="display-6 fw-bold text-white mb-3">Kiến Trúc Hợp Nhất Đa Phân Hệ</h3>'
        ),
        (
            'Thay vì tích hợp chắp vá hàng chục phần mềm riêng lẻ, DIGIFORCE đóng vai trò như một động cơ vận hành lõi kết nối liền mạch các ứng dụng giao diện, quy trình nghiệp vụ và cơ sở dữ liệu doanh nghiệp.',
            'Thay vì chắp vá hàng chục phần mềm rời rạc, DIGIFORCE thiết lập một hạ tầng vận hành tập trung, kết nối thông suốt giữa giao diện người dùng, quy trình nghiệp vụ và cơ sở dữ liệu doanh nghiệp.'
        ),
        (
            '<div class="df-flow-node">Thẩm Định Dữ Liệu<small>Động cơ quy tắc (Rules Engine)</small></div>',
            '<div class="df-flow-node">Thẩm Định Dữ Liệu<small>Bộ quy tắc nghiệp vụ (Rules Engine)</small></div>'
        ),

        # /blockchain
        (
            'poster="/insilos_website/static/src/video/hero_act3_datacenter_poster.webp" class="ins-ambient-video-backdrop" style="opacity: 0.14;"',
            'poster="/insilos_website/static/src/video/hero_blockchain_opt_poster.webp" class="ins-ambient-video-backdrop" style="opacity: 0.16;"'
        ),
        (
            '<source src="/insilos_website/static/src/video/hero_act3_datacenter.mp4" type="video/mp4"/>',
            '<source src="/insilos_website/static/src/video/hero_blockchain_opt.mp4" type="video/mp4"/>'
        ),
        (
            'Động cơ Bảo mật Chủ quyền Zero-Telemetry',
            'Kiến trúc Bảo mật Chủ quyền Zero-Telemetry'
        ),
        (
            '<a href="#assessment" class="btn btn-primary btn-lg rounded-pill px-4 py-3 fw-bold">',
            '<a href="#assessment" class="btn ins-btn-lux ins-btn-lux-primary btn-lg px-4 py-3 fw-bold">'
        ),
        (
            '<a href="#topology" class="btn btn-outline-primary btn-lg rounded-pill px-4 py-3 fw-bold">',
            '<a href="#topology" class="btn ins-btn-lux ins-btn-lux-outline btn-lg px-4 py-3 fw-bold">'
        ),
        (
            '<a href="/contactus" class="btn btn-primary btn-lg rounded-pill px-5 py-3 fw-bold">',
            '<a href="/contactus" class="btn ins-btn-lux ins-btn-lux-primary btn-lg px-5 py-3 fw-bold">'
        ),
        (
            '<a href="/insilos" class="btn btn-outline-primary btn-lg rounded-pill px-4 py-3 fw-bold">',
            '<a href="/solutions" class="btn ins-btn-lux ins-btn-lux-outline btn-lg px-4 py-3 fw-bold">'
        ),
        (
            "Trực quan hóa cấu trúc liên kết thời gian thực giữa ZenCode Sovereign Swarm, Clef DAG Scheduler và các nốt thực thi cô lập.",
            "Trực quan hóa cấu trúc liên kết thời gian thực giữa ZenCode Sovereign Swarm, Clef DAG Scheduler và các nút thực thi độc lập."
        ),
        (
            "QUẢN TRỊ ĐA TÁC TỬ TỰ TRỊ",
            "MÔ HÌNH ĐIỀU PHỐI MULTI-AGENT TỰ CHỦ"
        ),
        (
            "Mỗi chu trình phát triển và refactor được phân rã thành quy trình kiểm soát khắt khe giữa 5 đặc vụ độc lập.",
            "Mỗi chu trình phát triển và kiểm định được phân định trách nhiệm rõ ràng giữa 5 tác nhân chuyên trách độc lập:"
        ),
        (
            "ĐỘNG CƠ BẢO MẬT CHỦ QUYỀN STEALTH",
            "KIẾN TRÚC BẢO MẬT CHỦ QUYỀN STEALTH"
        ),
        (
            "Mỗi nốt tính toán sở hữu một IP ra tĩnh 1:1 độc lập, ngăn chặn hoàn toàn việc tương quan mạng và suy đoán dấu vết hành vi.",
            "Mỗi nút tính toán sở hữu một IP tĩnh 1:1 độc lập, ngăn chặn hoàn toàn nguy cơ tương quan lưu lượng mạng và truy vết hành vi."
        ),

        # /solutions
        (
            "<span>ĐỘNG CƠ VẬN HÀNH TỰ TRỊ · CÔNG NGHIỆP 4.0 &amp; CHUỖI CUNG ỨNG THÔNG MINH</span>",
            "<span>HỆ ĐIỀU HÀNH DOANH NGHIỆP TỰ HÀNH · CÔNG NGHIỆP 4.0 &amp; LOGISTICS THÔNG MINH</span>"
        ),
        (
            '<a href="#poc" class="btn btn-primary btn-lg rounded-pill px-4 py-3 fw-bold shadow-sm d-inline-flex align-items-center">',
            '<a href="#poc" class="btn ins-btn-lux ins-btn-lux-primary btn-lg px-4 py-3 fw-bold shadow-sm d-inline-flex align-items-center">'
        ),
        (
            '<a href="#erp-core-3d" class="btn btn-outline-light btn-lg rounded-pill px-4 py-3 fw-bold d-inline-flex align-items-center" style="color: #0ABBDB !important; border: 1px solid rgba(10, 187, 219, 0.45) !important; background: rgba(10, 187, 219, 0.08) !important; background-color: rgba(10, 187, 219, 0.08) !important;">',
            '<a href="#erp-core-3d" class="btn ins-btn-lux ins-btn-lux-outline btn-lg px-4 py-3 fw-bold d-inline-flex align-items-center" style="color: #0ABBDB !important; border: 1px solid rgba(10, 187, 219, 0.45) !important; background: rgba(10, 187, 219, 0.08) !important; background-color: rgba(10, 187, 219, 0.08) !important;">'
        ),
        (
            '<a href="/contactus" class="btn btn-primary btn-lg rounded-pill px-5 py-3 fw-bold">\n                                <span>Đăng Ký Buổi Proof of Concept 3 Giờ</span>',
            '<a href="/contactus" class="btn ins-btn-lux ins-btn-lux-primary btn-lg px-5 py-3 fw-bold">\n                                <span>Đăng Ký Buổi Proof of Concept 3 Giờ</span>'
        ),
        (
            '<a href="/contactus" class="btn btn-outline-primary btn-lg rounded-pill px-5 py-3 fw-bold">\n                                <span>Tải Tài Liệu Kỹ Thuật Dossier</span>',
            '<a href="/contactus" class="btn ins-btn-lux ins-btn-lux-outline btn-lg px-5 py-3 fw-bold">\n                                <span>Tải Tài Liệu Kỹ Thuật Dossier</span>'
        ),
        (
            "Đăng ký buổi làm việc 3 giờ Proof of Concept (POC) cùng đội ngũ chuyên gia kiến trúc INSILOS. Mang theo dữ liệu thực tế (BOM sản xuất, danh mục chuyến xe hoặc bảng cân đối kế toán) để trực tiếp chứng kiến hệ thống tự vận hành và nhận lộ trình tối ưu hóa miễn phí.",
            "Đăng ký phiên kiểm chứng thực nghiệm 180 phút Proof of Concept (POC) cùng Hội đồng Kiến trúc sư Trưởng INSILOS. Đưa dữ liệu mẫu thực tế của doanh nghiệp (định mức BOM sản xuất, nhật trình điều xe hoặc bảng cân đối kế toán) để trực tiếp trải nghiệm năng lực vận hành tự động và nhận bản đề xuất tối ưu hóa chi phí chi tiết."
        ),

        # /contactus
        (
            "Tổng hợp cấu trúc mục tiêu theo mô-đun: Điều phối DIGIFORCE, tác tử MOJO AI, mỏ neo sổ cái MOJOVERSE",
            "Tổng hợp kiến trúc mục tiêu theo phân hệ: Điều phối DIGIFORCE, cụm tác nhân MOJO AI, sổ cái bất biến MOJOVERSE"
        ),
        (
            '<option value="DIGIFORCE">DIGIFORCE (Động cơ Low-Code Doanh nghiệp)</option>',
            '<option value="DIGIFORCE">DIGIFORCE (Nền tảng Low-Code Doanh nghiệp)</option>'
        ),
        (
            '<option value="MOJO AI">MOJO AI (LLM Công nghiệp &amp; Tác tử Tự trị)</option>',
            '<option value="MOJO AI">MOJO AI (LLM Công nghiệp &amp; Tác nhân AI Tự chủ)</option>'
        ),
        (
            "Được xây dựng trên các tiêu chuẩn kiểm soát thể chế khắt khe, đáp ứng đầy đủ yêu cầu kiểm toán của khối ngân hàng hàng đầu, các tập đoàn công nghiệp và chuỗi cung ứng đa quốc gia.",
            "Tuân thủ nghiêm ngặt chuẩn mực kiểm soát thể chế, đáp ứng toàn diện tiêu chuẩn kiểm toán quốc tế cho các ngân hàng thương mại, tập đoàn công nghiệp và chuỗi cung ứng đa quốc gia."
        ),
        (
            "Hoàn toàn chính xác, 100% miễn phí và không đi kèm bất kỳ ràng buộc thương mại hay hợp đồng nào. Tại INNORIA, chúng tôi tin rằng các quyết định kiến trúc cấp điều hành cần được xây dựng dựa trên dữ liệu đo lường thực tế từ chính hệ thống của doanh nghiệp.",
            "Hoàn toàn miễn phí và không đi kèm bất kỳ ràng buộc thương mại nào. Tại INNORIA, mọi quyết định kiến trúc chiến lược đều phải dựa trên số liệu đo đạc thực tế từ hiện trường vận hành của chính doanh nghiệp."
        ),
        (
            "Sơ đồ cấu trúc vi dịch vụ khuyến nghị, luồng quy trình nghiệp vụ và các điểm tích hợp tác tử AI tự động.",
            "Sơ đồ phân rã microservices đề xuất, luồng dữ liệu nghiệp vụ và các điểm tích hợp tác nhân AI tự động."
        )
    ]
    apply_unslop_to_file(pages_file, pages_replacements)

    print("[🎉] Content Unslop & Enterprise Copywriting Polish Completed.")

if __name__ == "__main__":
    main()
