#!/usr/bin/env python3
"""
Comprehensive Website Content Unslop & B2B Vietnamese Localization Script
Convenes the Council of Linguistic & Content Quality:
- Enterprise Copywriting Director
- Chief Systems & Domain Terminologist
- B2B Localization Specialist
- QA Unslop Automation Engine

Audits and transforms all literal/machine translations ("word-for-word translation"),
robotic phrasing, and AI slop into authoritative, natural, and executive B2B Vietnamese copy.
"""

import os
import re

# Precise replacement dictionary: (pattern, replacement, description)
REPLACEMENTS = {
    # -------------------------------------------------------------
    # 1. innoria_homepage.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/innoria_homepage.xml': [
        (
            r'QUẦN THỂ AI ĐA TÁC NHÂN',
            'CỤM TÁC NHÂN AI ĐA LUỒNG',
            'Replace "quần thể" with "cụm tác nhân AI đa luồng"'
        ),
        (
            r'Cho phép đội ngũ nghiệp vụ và chuyên gia CNTT cùng hợp tác xây dựng phần mềm doanh nghiệp thông qua giao diện trực quan kéo thả\.',
            'Giúp đội ngũ nghiệp vụ và chuyên gia CNTT hợp tác kiến tạo phần mềm doanh nghiệp trên giao diện kéo thả trực quan.',
            'Unslop DIGIFORCE description'
        ),
        (
            r'Bộ công cụ xây dựng tác nhân AI tự hành\. Tích hợp thị giác máy tính VLM \(See-Detect-Analyze-Adapt\) và mạng lưới suy luận độc lập \(Reason-Solve-Plan-Execute\)\.',
            'Nền tảng phát triển tác nhân AI tự trị: Tích hợp thị giác máy tính VLM công nghiệp (See-Detect-Analyze-Adapt) và mạng lưới suy luận logic đa tầng (Reason-Solve-Plan-Execute).',
            'Unslop MOJO AI description'
        ),
        (
            r'Không chỉ cung cấp phần mềm, Innoria cử các chuyên gia kiến trúc giải pháp tham gia trực tiếp vào toàn bộ hành trình số hóa của bạn\.',
            'Không dừng lại ở việc chuyển giao phần mềm, Innoria đồng hành cùng doanh nghiệp bằng đội ngũ chuyên gia kiến trúc giải pháp giàu kinh nghiệm trong toàn bộ tiến trình số hóa.',
            'Remove consumer "của bạn" and unslop engineering services description'
        ),
        (
            r'Tự động hoá văn phòng, RPA, phát hiện lỗi sản phẩm qua camera công nghiệp, giúp doanh nghiệp trở nên tinh gọn, linh hoạt và lấy khách hàng làm trung tâm\.',
            'Tự động hóa tác vụ văn phòng, RPA thông minh, kiểm định chất lượng sản phẩm qua thị giác máy tính công nghiệp, giúp chuẩn hóa quy trình và nâng cao năng lực cạnh tranh của doanh nghiệp.',
            'Remove generic buzzword "lấy khách hàng làm trung tâm"'
        ),
        (
            r'Được tôi luyện qua hàng trăm dự án sản xuất, kho vận và bán lẻ với yêu cầu tuân thủ khắt khe nhất\.',
            'Được bảo chứng qua hàng trăm dự án sản xuất, kho vận và chuỗi cung ứng với các yêu cầu tuân thủ khắt khe nhất.',
            'Elevate industry solutions intro copy'
        ),
        (
            r'phát hiện hàng hết date hoặc thiếu hàng trên quầy kệ siêu thị thông qua ảnh chụp của nhân viên tiếp thị\.',
            'tự động phát hiện hàng cận date, hết hạn sử dụng hoặc đứt gãy nguồn cung trên quầy kệ thông qua ảnh chụp thực tế.',
            'Replace slang "hết date" with standard enterprise Vietnamese'
        ),
        (
            r'Phiên mổ xẻ kỹ thuật độc lập trực tiếp cùng Giám Đốc Công Nghệ &amp; Kiến Trúc Sư Trưởng Innoria\. Bóc tách điểm nghẽn, kiểm toán nợ công nghệ và xác lập bản thiết kế kiến trúc mục tiêu khả thi trong 72 giờ\.',
            'Phiên thẩm định kỹ thuật chuyên sâu trực tiếp cùng Giám Đốc Công Nghệ &amp; Kiến Trúc Sư Trưởng Innoria: Phân tích kiến trúc hiện hữu, đánh giá nợ công nghệ và xác lập bản thiết kế kiến trúc mục tiêu khả thi trong 72 giờ.',
            'Replace medical term "mổ xẻ kỹ thuật" with "thẩm định kỹ thuật chuyên sâu"'
        ),
        (
            r'Khám nghiệm 1:1 trực tiếp cùng CTO &amp; Solution Architect',
            'Tham vấn kiến trúc 1:1 trực tiếp cùng CTO &amp; Solution Architect',
            'Replace forensic term "khám nghiệm" with "tham vấn kiến trúc"'
        ),
        (
            r'Văn Hóa &amp; Di Sản 18 Năm',
            'Lịch Sử Phát Triển &amp; Năng Lực 18 Năm',
            'Replace awkward "di sản" with "Lịch Sử Phát Triển & Năng Lực"'
        ),
        (
            r'Hàng rào bảo vệ: Tất định \(Deterministic\)',
            'Hàng rào bảo vệ: Chuẩn xác tuyệt đối (Deterministic)',
            'Elevate deterministic terminology'
        )
    ],

    # -------------------------------------------------------------
    # 2. innoria_pages.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/innoria_pages.xml': [
        (
            r'72 Giờ Bàn Giao POC: Khám nghiệm kiến trúc và chạy thực nghiệm trên tập dữ liệu mẫu của doanh nghiệp chỉ trong 3 ngày\.',
            '72 Giờ Bàn Giao POC: Thẩm định kiến trúc và triển khai thực nghiệm trên tập dữ liệu mẫu của doanh nghiệp chỉ trong 3 ngày.',
            'Replace "khám nghiệm kiến trúc" in /about'
        ),
        (
            r'Kiến Trúc Multi-Agent Đa Luồng · Cơ Chế Kiểm Soát Tất Định · 100% Chủ Quyền Dữ Liệu\.',
            'Kiến Trúc Multi-Agent Đa Luồng · Cơ Chế Kiểm Soát Chuẩn Xác · 100% Chủ Quyền Dữ Liệu.',
            'Refine deterministic phrasing'
        ),
        (
            r'Kiểm Soát Tất Định · Triệt Tiêu Ảo Giác Thuật Toán',
            'Kiểm Soát Chuẩn Xác Tuyệt Đối · Loại Bỏ Ảo Giác Thuật Toán',
            'Elevate deterministic control heading'
        ),
        (
            r'bắt đầu luồng phối hợp 5 tác tử',
            'bắt đầu luồng phối hợp 5 tác nhân AI chuyên trách',
            'Replace "5 tác tử" in simulation script'
        ),
        (
            r'ĐƯỢC TÔI LUYỆN TỪ THỰC TẾ VẬN HÀNH',
            'CHỨNG MINH TỪ THỰC TIỄN VẬN HÀNH',
            'Elevate badge text'
        ),
        (
            r'Khóa chặt biên lợi nhuận',
            'Bảo toàn biên lợi nhuận',
            'Replace "khóa chặt biên lợi nhuận"'
        ),
        (
            r'Hãy chọn một điểm nghẽn vật lý lớn nhất trong dây chuyền của bạn\.',
            'Hãy chọn điểm nghẽn vận hành trọng yếu nhất trong dây chuyền sản xuất.',
            'Remove consumer "của bạn" in /industries CTA'
        ),
        (
            r'Phiên mổ xẻ kỹ thuật độc lập kéo dài 180 phút giữa Ban Lãnh Đạo Kỹ Thuật của bạn và Hội Đồng Kiến Trúc Sư Trưởng Innoria\.',
            'Phiên thẩm định kỹ thuật chuyên sâu độc lập kéo dài 180 phút giữa Ban Lãnh Đạo Kỹ Thuật của quý doanh nghiệp và Hội Đồng Kiến Trúc Sư Trưởng Innoria.',
            'Replace "mổ xẻ kỹ thuật" and "của bạn" in /contactus'
        ),
        (
            r'Tuyệt Đối Không Khóa Chặt Nhà Cung Cấp',
            'Cam Kết Không Ràng Buộc Nhà Cung Cấp (Zero Vendor Lock-In)',
            'Standardize zero vendor lock-in heading'
        ),
        (
            r'Không mất phí · Không khóa chặt công nghệ · 100% Chủ quyền dữ liệu',
            'Không chi phí phát sinh · Không ràng buộc công nghệ độc quyền · 100% Chủ quyền dữ liệu',
            'Unslop zero lock-in badge'
        ),
        (
            r'Bắt rễ từ hệ sinh thái công nghệ tốc độ cao tại Việt Nam cùng các trung tâm hợp tác chuyên sâu khắp khu vực Châu Á - Thái Bình Dương\.',
            'Phát triển vững chắc từ hệ sinh thái công nghệ tốc độ cao tại Việt Nam cùng mạng lưới hợp tác chuyên sâu khắp khu vực Châu Á - Thái Bình Dương.',
            'Replace literal translation "Bắt rễ từ..."'
        ),
        (
            r'Tuyệt Đối Không Khóa Chặt Công Nghệ\. Chủ Quyền Dữ Liệu Tối Cao\.',
            'Cam Kết Không Ràng Buộc Công Nghệ Độc Quyền. Chủ Quyền Dữ Liệu Tối Cao.',
            'Elevate heading copy'
        ),
        (
            r'Nhật ký kiểm toán liên tục, phân tách người thuê theo vai trò, tự động quét lỗ hổng bảo mật và quy trình vận hành khắc phục sự cố sau thảm họa\.',
            'Nhật ký kiểm toán liên tục (Audit Trail), cơ chế cô lập môi trường thuê (Tenant Isolation) và phân quyền vai trò chuyên sâu, tự động quét lỗ hổng bảo mật cùng quy trình khắc phục sự cố sau thảm họa (Disaster Recovery).',
            'Fix machine translation of "tenant separation" ("phân tách người thuê")'
        ),
        (
            r'3\. INNORIA bảo đảm việc không bị khóa chặt nhà cung cấp \(Zero Lock-In\) ra sao\?',
            '3. INNORIA bảo đảm nguyên tắc không bị phụ thuộc nhà cung cấp (Zero Vendor Lock-In) như thế nào?',
            'Elevate FAQ question 3'
        ),
        (
            r'Không phụ thuộc nhà cung cấp là nguyên tắc kiến trúc bất biến cốt lõi của chúng tôi\.',
            'Loại bỏ hoàn toàn rủi ro phụ thuộc nhà cung cấp (Zero Lock-In) là nguyên tắc kiến trúc bất biến cốt lõi của INNORIA.',
            'Elevate FAQ answer 3'
        ),
        (
            r'Bảng Đánh Giá Khả Thi Kỹ Thuật &amp; Khoảng Trống Hệ Thống: Đánh giá có hệ thống về khả năng tích hợp hệ thống di sản, các điểm nghẽn cơ sở dữ liệu và mức độ sẵn sàng của dữ liệu\.',
            'Bảng Đánh Giá Khả Thi Kỹ Thuật &amp; Khoảng Trống Hệ Thống: Đánh giá có hệ thống về khả năng tích hợp hệ thống hiện hữu (Legacy Systems), các điểm nghẽn cơ sở dữ liệu và mức độ sẵn sàng của dữ liệu.',
            'Replace literal translation "hệ thống di sản" with "hệ thống hiện hữu (Legacy Systems)"'
        ),
        (
            r'Bản Đặc Tả Phạm Vi Thử Nghiệm MVP: Kế hoạch sprint linh hoạt chìa khóa trao tay từ 6 đến 8 tuần với phân bổ nguồn lực cụ thể, tiến độ thực hiện và các mốc đánh giá hoàn vốn ROI rõ ràng\.',
            'Bản Đặc Tả Phạm Vi Thử Nghiệm MVP: Kế hoạch triển khai Sprint linh hoạt trọn gói từ 6 đến 8 tuần với phân bổ nguồn lực chi tiết, tiến độ thực hiện và các mốc đánh giá hoàn vốn ROI rõ ràng.',
            'Replace "chìa khóa trao tay" with "triển khai Sprint linh hoạt trọn gói"'
        ),
        (
            r'Khám phá cách thức kiến trúc Innoria bẻ khóa các rào cản vật lý và tối ưu hóa chuỗi giá trị theo từng đặc thù nghiệp vụ chuyên sâu\.',
            'Khám phá cách thức kiến trúc Innoria tháo gỡ các điểm nghẽn vật lý và tối ưu hóa chuỗi giá trị theo từng đặc thù nghiệp vụ chuyên sâu.',
            'Replace awkward translation "bẻ khóa rào cản vật lý"'
        ),
        (
            r'Kéo thả trực quan nhưng sinh ra mã nguồn sạch \(Clean React / TypeScript / Python ORM\)\. Cho phép xuất 100% source code, tự do triển khai trên hạ tầng Kubernetes riêng, xóa bỏ hoàn toàn nguy cơ vendor lock-in\.',
            'Kéo thả trực quan nhưng sinh ra mã nguồn sạch (Clean React / TypeScript / Python ORM). Hỗ trợ xuất trọn vẹn 100% mã nguồn, tự do triển khai trên hạ tầng Kubernetes riêng, loại bỏ hoàn toàn nguy cơ phụ thuộc nhà cung cấp (Vendor Lock-In).',
            'Elevate /no-code-platform lead paragraph'
        ),
        (
            r'đưa quyền kiểm soát vận hành tối cao về tay ban lãnh đạo',
            'giúp ban lãnh đạo chủ động kiểm soát toàn diện và chuẩn xác mọi hoạt động vận hành',
            'Unslop grandiose translation in /solutions quote'
        )
    ],

    # -------------------------------------------------------------
    # 3. snippets_cctv.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/snippets_cctv.xml': [
        (
            r'Trình duyệt của bạn không hỗ trợ định dạng video MP4\.',
            'Trình duyệt không hỗ trợ phát trực tiếp định dạng video MP4.',
            'Unslop video fallback message'
        )
    ],

    # -------------------------------------------------------------
    # 4. snippets_cinematic.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/snippets_cinematic.xml': [
        (
            r'Lập tiến độ sản xuất trực quan, phân bổ máy chấn dập CNC Trumpf và triệt tiêu nút thắt cổ chai\.',
            'Lập tiến độ sản xuất trực quan, cân bằng phụ tải máy chấn dập CNC Trumpf và giải tỏa triệt để các điểm nghẽn vận hành (Bottlenecks).',
            'Replace literal translation "triệt tiêu nút thắt cổ chai"'
        )
    ],

    # -------------------------------------------------------------
    # 5. platform_solutions.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/platform_solutions.xml': [
        (
            r'Đối Soát 3 Bên Cross-Validation Khóa Chặt Sai Lệch 0 Variance Budget',
            'Đối Soát 3 Chiều (Cross-Validation) Triệt Tiêu Sai Lệch Ngân Sách (Zero Variance Budget)',
            'Unslop cross-validation title'
        ),
        (
            r'Tối Ưu Thuế FTA Của Bạn',
            'Tối Ưu Hóa Ưu Đãi Thuế Quan FTA Cho Doanh Nghiệp',
            'Remove consumer "Của Bạn"'
        ),
        (
            r'Tận dụng tối đa ưu đãi thuế quan EVFTA, CPTPP, RCEP',
            'Khai thác tối đa các ưu đãi thuế quan theo hiệp định EVFTA, CPTPP, RCEP',
            'Elevate FTA compliance description'
        )
    ],

    # -------------------------------------------------------------
    # 6. resources_about_demo.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/resources_about_demo.xml': [
        (
            r'từng quyết định tự trị của tác tử',
            'từng quyết định tự trị của tác nhân AI',
            'Replace "tác tử" with "tác nhân AI"'
        ),
        (
            r'Trình duyệt của bạn không hỗ trợ định dạng video HTML5\.',
            'Trình duyệt không hỗ trợ phát trực tiếp định dạng video HTML5.',
            'Unslop video fallback'
        ),
        (
            r'nơi từng quyết định của tác tử được kiểm chứng',
            'nơi từng quyết định của tác nhân AI được kiểm chứng',
            'Replace "tác tử"'
        ),
        (
            r'Insilos được tôi luyện trên những bài toán hóc búa nhất của hạ tầng quốc gia',
            'Insilos được chứng minh qua những bài toán vận hành phức tạp nhất của hạ tầng công nghiệp',
            'Elevate historical narrative copy'
        ),
        (
            r'sát thực tế ngành của bạn\.',
            'sát thực tế vận hành của doanh nghiệp.',
            'Remove consumer "của bạn"'
        )
    ],

    # -------------------------------------------------------------
    # 7. industries.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/industries.xml': [
        (
            r'Phương pháp luận triển khai chìa khóa trao tay \(Turnkey Deployment\) đã được kiểm chứng tại hơn 50\+ tập đoàn\.',
            'Phương pháp luận triển khai trọn gói (Turnkey Deployment) đã được kiểm chứng tại hơn 50+ tập đoàn công nghiệp.',
            'Replace "chìa khóa trao tay" in industries'
        ),
        (
            r'Khởi Tạo Môi Trường Demo May Đo Theo Ngành Của Bạn',
            'Khởi Tạo Môi Trường Demo May Đo Theo Đặc Thù Ngành',
            'Remove consumer "Của Bạn"'
        ),
        (
            r'Khóa Chặt Sai Lệch -70% Sự Cố OOS/OOT Bảo Vệ Mẻ Thuốc Zero Discarded Batches',
            'Kiểm Soát Nghiêm Ngặt: Giảm 70% Sự Cố OOS/OOT, Bảo Toàn 100% Lô Mẻ Dược Phẩm (Zero Discarded Batches)',
            'Elevate pharma headline'
        ),
        (
            r'Nâng Tầm Nhà Máy Sản Xuất Dược Phẩm Của Bạn',
            'Nâng Tầm Vận Hành Nhà Máy Sản Xuất Dược Phẩm Chuẩn GMP',
            'Remove consumer "Của Bạn"'
        ),
        (
            r'Tối Ưu Hóa Nhà Máy Năng Lượng Tái Tạo Của Bạn',
            'Tối Ưu Hóa Hiệu Suất Nhà Máy Năng Lượng Tái Tạo',
            'Remove consumer "Của Bạn"'
        ),
        (
            r'Tối Ưu Hóa Đội Ngũ Kỹ Thuật Hiện Trường Của Bạn',
            'Tối Ưu Hóa Hiệu Quả Đội Ngũ Kỹ Thuật Hiện Trường',
            'Remove consumer "Của Bạn"'
        )
    ],

    # -------------------------------------------------------------
    # 8. dossiers.xml, home.xml, brochure.xml
    # -------------------------------------------------------------
    'enterprise/insilos_website/views/dossiers.xml': [
        (
            r'Cần Khảo Sát &amp; Xây Dựng Hồ Sơ Rủi Ro Cho Nhà Máy Của Bạn\?',
            'Cần Khảo Sát &amp; Xây Dựng Hồ Sơ Quản Trị Rủi Ro Cho Nhà Máy Doanh Nghiệp?',
            'Remove consumer "Của Bạn"'
        )
    ],
    'enterprise/insilos_website/views/home.xml': [
        (
            r'Khóa cứng rủi ro rò rỉ bí mật công nghiệp, tuân thủ nghiêm ngặt Nghị định 13/2023/NĐ-CP về Bảo vệ Dữ liệu Cá nhân và tiêu chuẩn ISO 27001 của bạn\.',
            'Triệt tiêu rủi ro rò rỉ bí mật công nghiệp, tuân thủ nghiêm ngặt Nghị định 13/2023/NĐ-CP về Bảo vệ Dữ liệu Cá nhân và tiêu chuẩn quốc tế ISO 27001.',
            'Remove awkward "của bạn" at the end of sentence'
        ),
        (
            r'Đội ngũ Enterprise Solution Architect sẵn sàng ký kết thỏa thuận NDA song phương trước khi tiếp nhận bất kỳ thông tin nào của bạn\.',
            'Đội ngũ Enterprise Solution Architect sẵn sàng ký kết thỏa thuận NDA song phương trước khi tiếp nhận bất kỳ thông tin nào của doanh nghiệp.',
            'Remove consumer "của bạn"'
        )
    ],
    'enterprise/insilos_website/views/brochure.xml': [
        (
            r'Bảo Vệ Nhà Máy Triệu Đô Của Bạn Ngay Hôm Nay',
            'Bảo Toàn Chuỗi Giá Trị &amp; Nâng Cao Năng Lực Cạnh Tranh Nhà Máy Doanh Nghiệp',
            'Elevate consumer tone in brochure'
        ),
        (
            r'mô hình tính toán TCO/ROI cá nhân hóa cho doanh nghiệp của bạn\.',
            'mô hình phân tích TCO/ROI tối ưu hóa riêng cho doanh nghiệp.',
            'Unslop brochure CTA copy'
        )
    ]
}

def execute_unslop():
    print("=" * 70)
    print("COUNCIL OF LINGUISTIC & CONTENT QUALITY — WEBSITE UNSLOP ENGINE")
    print("=" * 70)
    total_files_modified = 0
    total_replacements = 0

    for fpath, rules in REPLACEMENTS.items():
        if not os.path.exists(fpath):
            print(f"[-] File not found: {fpath}, skipping...")
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        file_mods = 0
        original_content = content
        for pattern, replacement, desc in rules:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                file_mods += count
                print(f"  [✓] {os.path.basename(fpath)}: {desc} ({count} applied)")
            else:
                print(f"  [-] {os.path.basename(fpath)}: Pattern not matched: {pattern[:40]}...")

        if content != original_content:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            total_files_modified += 1
            total_replacements += file_mods
            print(f"[SUCCESS] {fpath}: {file_mods} updates written.\n")
        else:
            print(f"[SKIP] No changes needed in {fpath}.\n")

    print("=" * 70)
    print(f"SUMMARY: {total_replacements} replacements across {total_files_modified} files.")
    print("=" * 70)

if __name__ == '__main__':
    execute_unslop()
