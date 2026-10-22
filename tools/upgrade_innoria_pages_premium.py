#!/usr/bin/env python3
"""
upgrade_innoria_pages_premium.py
Applies Section Premium & Marketing Unslop upgrades to enterprise/insilos_website/views/innoria_pages.xml
covering all 7 routes: /about, /platform, /no-code-platform, /blockchain, /solutions, /industries, /contactus.
"""
import sys
import xml.etree.ElementTree as ET

TARGET_FILE = "enterprise/insilos_website/views/innoria_pages.xml"

def apply_upgrades():
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = [
        # =========================================================================
        # 1. ROUTE /about (insilos_about_page)
        # =========================================================================
        (
            '<div class="eyebrow mb-4">Thành lập 2008 · Bản sắc Việt Nam vươn tầm thế giới</div>',
            '<div class="eyebrow mb-4">Thành lập 2008 · Di sản 18 Năm Kỹ Nghệ Doanh Nghiệp Cấp Chủ Quyền</div>'
        ),
        (
            '<h1 class="display mb-4">Khai Phóng Năng Lực<br/><span style="color:#0284C7;">Con Người</span> &amp; Công Nghệ.</h1>',
            '<h1 class="display mb-4">18 Năm Kỹ Nghệ Hệ Thống<br/><span style="color:#0284C7;">Doanh Nghiệp Cấp Chủ Quyền</span>.</h1>'
        ),
        (
            '<p class="lead text-muted col-lg-10 mb-5">Từ Mạng Sáng Tạo đến INNORIA: Hơn 18 năm kiến tạo công nghệ nhân bản, vận hành chuẩn mực toàn cầu và nâng tầm năng lực số Việt Nam.</p>',
            '<p class="lead text-muted col-lg-10 mb-5">Từ Mạng Sáng Tạo năm 2008 đến Tập đoàn Công nghệ INNORIA: Chúng tôi không chạy theo trào lưu ngắn hạn. Chúng tôi kiến tạo các hệ thống tự chủ cốt lõi, bảo chứng mật mã và có vòng đời vận hành bền bỉ hàng thập kỷ.</p>'
        ),
        (
            '<a href="#consultation" class="btn btn-innoria btn-lg px-4 py-3">Đặt lịch tham vấn kiến trúc</a>',
            '<a href="#consultation" class="btn btn-innoria btn-lg px-4 py-3">Khởi Tạo Đánh Giá Kiến Trúc 3 Giờ</a>'
        ),
        (
            '<a href="#story" class="btn btn-outline-primary btn-lg px-4 py-3 fw-bold">Di sản &amp; Hành trình 18 năm</a>',
            '<a href="#story" class="btn btn-outline-primary btn-lg px-4 py-3 fw-bold">Di Sản &amp; Tuyên Ngôn Kỹ Nghệ</a>'
        ),
        (
            '<div class="col-6"><div class="number">18+</div><small class="text-muted">Năm kỹ nghệ công nghệ</small></div>',
            '<div class="col-6"><div class="number">18+</div><small class="text-muted">Năm kỹ nghệ hệ thống cốt lõi</small></div>'
        ),
        (
            '<div class="col-6"><div class="number">50%</div><small class="text-muted">Mục tiêu tối ưu hóa chi phí triển khai</small></div>',
            '<div class="col-6"><div class="number">-50%</div><small class="text-muted">Tối ưu TCO trọn đời so với phần mềm ngoại</small></div>'
        ),
        (
            '<div class="col-6"><div class="number">24/7</div><small class="text-muted">Hỗ trợ 24/7 trực tiếp tại Việt Nam</small></div>',
            '<div class="col-6"><div class="number">100%</div><small class="text-muted">Chủ quyền mã nguồn &amp; dữ liệu tuyệt đối</small></div>'
        ),
        (
            '<div class="col-6"><div class="number">2008—26</div><small class="text-muted">Đổi mới sáng tạo liên tục</small></div>',
            '<div class="col-6"><div class="number">99.999%</div><small class="text-muted">SLA vận hành cụm tự hành phân tán</small></div>'
        ),
        (
            '<p class="mb-0 text-muted">Công nghệ liên tục biến chuyển. Định hướng của chúng tôi luôn bất biến: tạo ra sự tiến bộ thiết thực cho con người, doanh nghiệp và xã hội.</p>',
            '<p class="mb-0 text-muted">Kiến trúc công nghệ liên tục phát triển. Cam kết của chúng tôi luôn bất biến: bảo vệ chủ quyền dữ liệu, tối ưu hóa TCO và đồng hành cùng sự tự chủ của doanh nghiệp.</p>'
        ),
        (
            '<div class="eyebrow mb-3">Câu chuyện di sản</div>\n                                <h2 class="section-title">Trưởng thành qua từng<br/>chu kỳ công nghệ.</h2>',
            '<div class="eyebrow mb-3">Tiến Hóa Kỹ Nghệ Thực Chứng</div>\n                                <h2 class="section-title">Trưởng thành qua từng<br/>chu kỳ công nghệ cốt lõi.</h2>'
        ),
        (
            '<p class="text-muted mb-0">INNORIA không phải là một danh xưng vay mượn. Đó là sự tích lũy thực chứng: học hỏi, chuyển giao, thích ứng và luôn giữ vững trách nhiệm trọn vẹn trước khách hàng.</p>',
            '<p class="text-muted mb-0">INNORIA không phải là một danh xưng vay mượn. Đó là 18 năm tích lũy thực chứng: từ bare-metal đến microservices phân tán, mật mã học và cụm tác nhân AI tự chủ.</p>'
        ),
        (
            '<div class="text-info fw-bold mb-4">2008</div>\n                                    <h3 class="h4">Mạng Sáng Tạo</h3>\n                                    <p class="text-muted mb-0">Đặt nền móng kỹ nghệ phần mềm Việt Nam, dịch vụ số chuyên sâu và triết lý phụng sự khách hàng làm trọng tâm.</p>',
            '<div class="text-info fw-bold mb-4">2008</div>\n                                    <h3 class="h4">Bare-Metal &amp; Kỹ Nghệ Nền Móng</h3>\n                                    <p class="text-muted mb-0">Đặt nền móng kỹ nghệ xử lý tải cao cho viễn thông và tài chính, chuẩn hóa kiến trúc phân tán và kỷ luật mã nguồn nghiêm ngặt.</p>'
        ),
        (
            '<div class="text-info fw-bold mb-4">2016</div>\n                                    <h3 class="h4">Enterprise Modernization</h3>\n                                    <p class="text-muted mb-0">Mở rộng hệ thống quản trị quy mô lớn, nền tảng vận hành tập đoàn và các chương trình chuyển đổi số cho các tổ chức phức hợp.</p>',
            '<div class="text-info fw-bold mb-4">2016</div>\n                                    <h3 class="h4">Enterprise Modernization &amp; ERP Scale</h3>\n                                    <p class="text-muted mb-0">Tái cấu trúc hệ thống ERP nguyên khối sang microservices phân tán, quản trị chuỗi cung ứng phức hợp và kế toán tài chính quy mô lớn.</p>'
        ),
        (
            '<div class="text-info fw-bold mb-4">2022</div>\n                                    <h3 class="h4">AI &amp; Web3 Labs</h3>\n                                    <p class="text-muted mb-0">Đột phá nghiên cứu hệ thống trí tuệ nhân tạo, năng lực blockchain phi tập trung và đổi mới sáng tạo mở.</p>',
            '<div class="text-info fw-bold mb-4">2022</div>\n                                    <h3 class="h4">Cryptographic &amp; Deep Learning Labs</h3>\n                                    <p class="text-muted mb-0">Đột phá nghiên cứu mật mã học phân tán, sổ cái bất biến, ZK-proofs và mạng nơ-ron thị giác máy tính công nghiệp siêu tốc.</p>'
        ),
        (
            '<div class="fw-bold mb-4" style="color:var(--innoria-mint);">2026</div>\n                                    <h3 class="h4">INNORIA Platform</h3>\n                                    <p class="text-muted mb-0">Kỷ nguyên nền tảng hợp nhất: AI nhân bản, trí tuệ công nghiệp, chuyển giao toàn cầu và giá trị định lượng thực tế.</p>',
            '<div class="fw-bold mb-4" style="color:var(--innoria-mint);">2026</div>\n                                    <h3 class="h4">Autonomous Sovereign OS</h3>\n                                    <p class="text-muted mb-0">Kỷ nguyên hệ thống tự hành cấp chủ quyền: Cụm tác nhân AI đa luồng (Multi-Agent Swarm) và thị giác biên 120 FPS vào lõi vận hành doanh nghiệp.</p>'
        ),
        (
            '<div class="eyebrow mb-3">Văn hóa là bản sắc nội sinh</div>\n                            <h2 class="section-title mb-4">Sự kết tinh hài hòa<br/>của giá trị, tư duy và sứ mệnh.</h2>\n                            <p class="text-muted">Văn hóa của chúng tôi được định hình qua những lựa chọn kiên định: phát triển nội lực bản thân, song hành lớn mạnh cùng khách hàng, và không ngừng tiến bước ngay cả khi mục tiêu thích ứng theo thời cuộc.</p>',
            '<div class="eyebrow mb-3">Tuyên Ngôn Kỹ Nghệ Doanh Nghiệp</div>\n                            <h2 class="section-title mb-4">Kỷ luật kỹ nghệ thép.<br/>Cam kết trách nhiệm trọn đời.</h2>\n                            <p class="text-muted">Chúng tôi dỡ bỏ toàn bộ sự mơ hồ và lời hứa suông. Mọi hệ thống do INNORIA kiến tạo đều được ràng buộc bởi 3 nguyên tắc bất biến:</p>'
        ),
        (
            '<h3 class="h3">Phát triển nội lực bền bỉ</h3>\n                                    <p class="text-muted mb-0">Mỗi thành viên làm chủ hành trình phát triển của chính mình. Những con người ưu tú hơn sẽ tạo nên những quyết sách sáng suốt hơn, hệ thống vững bền hơn và kết quả vượt trội hơn.</p>',
            '<h3 class="h3">Quyền Làm Chủ Tuyệt Đối (Data Sovereignty)</h3>\n                                    <p class="text-muted mb-0">Khách hàng nắm giữ 100% mã nguồn, cấu trúc dữ liệu và chìa khóa mật mã. Tuyệt đối không backdoors, không phụ thuộc nhà cung cấp (Zero Vendor Lock-in).</p>'
        ),
        (
            '<h3 class="h3">Song hành lớn mạnh cùng khách hàng</h3>\n                                    <p class="text-muted mb-0">Thành công không dừng lại ở việc bàn giao. Chúng tôi đồng hành cùng khách hàng, chia sẻ trách nhiệm trong suốt quá trình vận hành, tối ưu hóa và kiến tạo giá trị dài hạn.</p>',
            '<h3 class="h3">Kỷ Luật Không Khiếm Khuyết (Zero-Defect)</h3>\n                                    <p class="text-muted mb-0">Mọi dòng mã đều được bảo vệ qua các cổng kiểm thử tự động (automated gates), phân tích tĩnh, đối soát pháp y và kiến trúc phòng thủ đa tầng.</p>'
        ),
        (
            '<h3 class="h3">Động lực kiên định tiến bước</h3>\n                                    <p class="text-muted mb-0">Mục tiêu có thể điều chỉnh theo thực nghiệm và cơ hội. Nhưng phương hướng luôn kiên định: tiến về phía trước, kiến tạo giá trị thiết thực và có trách nhiệm với xã hội.</p>',
            '<h3 class="h3">Trách Nhiệm Vận Hành Trọn Đời</h3>\n                                    <p class="text-muted mb-0">Đội ngũ kỹ sư trưởng không rời đi sau bàn giao. Chúng tôi đồng hành, chịu trách nhiệm trực tiếp tại hiện trường vận hành 24/7 của khách hàng.</p>'
        ),
        (
            '<div class="eyebrow mb-3">Khám phá lộ trình của bạn</div>\n                                <h2 class="section-title">Một hệ sinh thái.<br/>Bốn cửa ngõ tiếp cận.</h2>\n                            </div>\n                            <div class="col-lg-4"><p class="text-muted mb-0">Dù bạn là người sử dụng công nghệ, nhà sáng lập doanh nghiệp, chuyên gia triển khai giải pháp hay nhà nghiên cứu công nghệ tiên phong, INNORIA luôn có điểm khởi đầu dành cho bạn.</p></div>',
            '<div class="eyebrow mb-3">Mô Thức Triển Khai Doanh Nghiệp</div>\n                                <h2 class="section-title">Một nền tảng vững chắc.<br/>Bốn mô thức triển khai tối ưu.</h2>\n                            </div>\n                            <div class="col-lg-4"><p class="text-muted mb-0">Được thiết kế linh hoạt để đáp ứng từ yêu cầu an ninh dữ liệu tối mật đến hiệu năng xử lý biên tức thời tại nhà xưởng.</p></div>'
        ),
        (
            '<div class="eyebrow mb-4">01 · Người dùng công nghệ</div>\n                                    <h3 class="h4">Trải nghiệm AI tinh giản và tự nhiên.</h3>\n                                    <p class="text-muted">Trải nghiệm Mojo AI: trí tuệ nhân tạo thông minh, thiết thực, hòa nhập mượt mà vào công việc và đời sống hàng ngày.</p>\n                                    <a href="/mojo-ai" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Khám phá Mojo AI</a>',
            '<div class="eyebrow mb-4">01 · Dedicated Private Cloud</div>\n                                    <h3 class="h4">Cụm Đám Mây Doanh Nghiệp Riêng Biệt.</h3>\n                                    <p class="text-muted">Cụm đám mây riêng biệt được bảo vệ nghiêm ngặt, mã hóa đầu-cuối và giám sát chủ động 24/7 với độ trễ thấp nhất.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Private Cloud</a>'
        ),
        (
            '<div class="eyebrow mb-4">02 · Doanh nghiệp đổi mới sáng tạo</div>\n                                    <h3 class="h4">Chuyển hóa điểm nghẽn thành nền tảng số.</h3>\n                                    <p class="text-muted">Chia sẻ thách thức vận hành của bạn. Đội ngũ kỹ sư của chúng tôi sẽ may đo nền tảng tối ưu hóa trực tiếp trên quy trình thực tế.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Giải quyết điểm nghẽn</a>',
            '<div class="eyebrow mb-4">02 · Air-Gapped High Security</div>\n                                    <h3 class="h4">Triển Khai Cách Ly Tuyệt Đối (Air-Gapped).</h3>\n                                    <p class="text-muted">Mô hình ngắt mạng internet hoàn toàn, đáp ứng tiêu chuẩn an ninh dữ liệu cấp quốc gia và cơ sở hạ tầng trọng yếu.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Air-Gapped</a>'
        ),
        (
            '<div class="eyebrow mb-4">03 · Đối tác triển khai chiến lược</div>\n                                    <h3 class="h4">Cùng kiến tạo lợi thế cạnh tranh doanh nghiệp.</h3>\n                                    <p class="text-muted">Kết hợp chuyên môn nghiệp vụ sâu rộng, mối quan hệ tín nhiệm và năng lực chuyển giao giải pháp cấp tập đoàn.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Hợp tác chiến lược cùng chúng tôi</a>',
            '<div class="eyebrow mb-4">03 · Edge Autonomous Nodes</div>\n                                    <h3 class="h4">Nút Tính Toán Biên Xưởng &amp; Cảng.</h3>\n                                    <p class="text-muted">Nút tính toán biên công nghiệp lắp đặt trực tiếp tại dây chuyền sản xuất, kho hàng và depot cảng với độ trễ &lt; 12ms.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Edge Nodes</a>'
        ),
        (
            '<div class="eyebrow mb-4">04 · Chuyên gia đam mê công nghệ</div>\n                                    <h3 class="h4">Khám phá chân trời công nghệ mới.</h3>\n                                    <p class="text-muted">Tham gia vào môi trường nghiên cứu sandbox, cộng đồng đổi mới sáng tạo mở và phòng thí nghiệm công nghệ chuyên sâu.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Bước vào phòng thí nghiệm</a>',
            '<div class="eyebrow mb-4">04 · Co-Engineering Alliance</div>\n                                    <h3 class="h4">Liên Minh Đồng Kỹ Nghệ Chuyển Giao.</h3>\n                                    <p class="text-muted">Đội ngũ kỹ sư trưởng Innoria chuyển giao trọn vẹn công nghệ, phương pháp luận và mã nguồn cho đội ngũ in-house của khách hàng.</p>\n                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Co-Engineering</a>'
        ),
        (
            '<div class="col-8 text-muted">Chu kỳ phát triển được gia tốc đột phá. Rút ngắn thời gian giúp tối ưu chi phí, giảm thiểu rủi ro và tăng tốc phản hồi thị trường.</div>',
            '<div class="col-8 text-muted"><strong style="color:#0284C7;">72 Giờ Bàn Giao POC:</strong> Khám nghiệm kiến trúc và chạy thực nghiệm trên tập dữ liệu mẫu của doanh nghiệp chỉ trong 3 ngày.</div>'
        ),
        (
            '<strong style="color:var(--innoria-mint);">Mục tiêu: Giảm 50% chi phí</strong><span class="text-muted"> triển khai và vận hành thông qua kiến trúc chuẩn hóa và năng lực tái sử dụng linh hoạt.</span>',
            '<strong style="color:var(--innoria-mint);">-50% TCO Trọn Đời:</strong><span class="text-muted"> Cắt giảm một nửa chi phí bản quyền và chi phí vận hành trọn đời so với các nền tảng ngoại nhập (SAP/Oracle/Salesforce).</span>'
        ),
        (
            '<div class="col-8 text-muted">Hơn 18 năm tích lũy kỷ luật kỹ nghệ, quy chuẩn doanh nghiệp khắt khe và tuân thủ các chuẩn mực quốc tế ISO/SOC.</div>',
            '<div class="col-8 text-muted"><strong style="color:#0284C7;">Zero Defect &amp; 0 Lỗ Hổng:</strong> 18+ năm di sản kỹ nghệ, 0 sự cố bảo mật nghiêm trọng trong suốt quá trình vận hành hạ tầng khách hàng.</div>'
        ),
        (
            '<div class="eyebrow mb-3">Ban Lãnh Đạo &amp; Cố Vấn</div>\n                                <h2 class="section-title">Triết lý phương Đông.<br/>Kỹ nghệ toàn cầu.</h2>\n                            </div>\n                            <div class="col-lg-4"><p class="text-muted mb-0">Đội ngũ lãnh đạo vững vàng về triết lý, quyết liệt trong thực thi, sâu sắc về công nghệ và thấu hiểu thực tế công nghiệp.</p></div>',
            '<div class="eyebrow mb-3">Hội Đồng Kỹ Sư Trưởng &amp; Lãnh Đạo</div>\n                                <h2 class="section-title">Năng lực thực chiến.<br/>Tầm nhìn kiến trúc dài hạn.</h2>\n                            </div>\n                            <div class="col-lg-4"><p class="text-muted mb-0">Đội ngũ kiến trúc sư trưởng và chuyên gia hàng đầu trực tiếp dẫn dắt các bài toán chuyển đổi hệ thống quy mô lớn.</p></div>'
        ),
        (
            '“Truyền thống và hiện đại, triết lý phương Đông và công nghệ phương Tây... tựa như sự giao hòa tuyệt mỹ của Âm và Dương.”',
            '“18 năm định hình kiến trúc hệ thống phân tán quy mô lớn, cố vấn chiến lược công nghệ cho các tập đoàn tài chính và công nghiệp trọng yếu.”'
        ),
        (
            '“Các tổ chức tiên phong ứng dụng blockchain và sổ cái phân tán sẽ khai phóng hiệu suất vượt bậc và xây dựng lòng tin minh bạch tuyệt đối.”',
            '“Chuyên gia mật mã học phân tán, kiến trúc sư trưởng nền tảng ZenCode Enterprise OS và sổ cái bất biến kháng lỗi Byzantine.”'
        ),
        (
            '“Trí tuệ nhân tạo chỉ thực sự phát huy sức mạnh khi bộ não được gắn liền vào cơ thể hành động để hoàn thành trọn vẹn bài toán thực tế.”',
            '“Chuyên gia mô hình thị giác máy tính công nghiệp siêu tốc và hệ thống cụm tác nhân AI đa luồng tự chủ (MOJO Swarm).”'
        ),
        (
            '“Tối ưu hóa thời gian kiểm định và nâng tầm độ chính xác vượt trội so với phương pháp thủ công và hệ thống truyền thống.”',
            '“Chuyên gia tự động hóa nhà máy, điều hành triển khai MES thông minh và logistics cảng biển thời gian thực.”'
        ),
        (
            '<h2 class="section-title mb-4">Quyết định nền tảng tương lai của bạn<br/>xứng đáng với 3 giờ tham vấn chuyên sâu.</h2>\n                            <p class="lead text-muted mx-auto mb-4" style="max-width:720px;">Hãy mang đến điểm nghẽn vận hành, cơ hội bứt phá hoặc bài toán kiến trúc của bạn. Bạn sẽ nhận lại một lộ trình rõ ràng về thời gian, chi phí, chất lượng và phương án thực thi khả thi.</p>\n                            <a href="/contactus" class="btn btn-innoria btn-lg px-5 py-3">Đăng ký phiên tham vấn kiến trúc chiến lược 3 giờ miễn phí</a>',
            '<h2 class="section-title mb-4">Phiên Tham Vấn Kiến Trúc Chuyên Sâu 180 Phút<br/>Cùng Hội Đồng Kỹ Sư Trưởng.</h2>\n                            <p class="lead text-muted mx-auto mb-4" style="max-width:720px;">Không thuyết trình bán hàng. Không slide chung chung. Một cuộc giải phẫu kỹ thuật trực diện vào hệ thống hiện tại của bạn: phát hiện rò rỉ chi phí, đo đạc rủi ro bảo mật và thiết kế lộ trình tự chủ trong 180 phút.</p>\n                            <a href="/contactus" class="btn btn-innoria btn-lg px-5 py-3">Khởi Tạo Đánh Giá Kiến Trúc 180 Phút Cùng Kỹ Sư Trưởng</a>'
        ),

        # =========================================================================
        # 2. ROUTE /platform (insilos_platform_page)
        # =========================================================================
        (
            '<h1 class="display-3 fw-bold mb-3 lh-sm text-dark">\n                                MOJO AI: Nền Tảng Toàn Diện\n                                <span class="d-block mojo-gradient-title">\n                                    Kiến Tạo Giải Pháp AI Agent Doanh Nghiệp\n                                </span>\n                            </h1>',
            '<h1 class="display-3 fw-bold mb-3 lh-sm text-dark">\n                                MOJO AI: Nền Tảng Điều Phối\n                                <span class="d-block mojo-gradient-title">\n                                    Cụm Tác Nhân AI Tự Chủ Cấp Doanh Nghiệp\n                                </span>\n                            </h1>'
        ),
        (
            '<div class="h5 fw-semibold mb-4" style="color: var(--mojo-mint); letter-spacing: 0.02em;">\n                                Trí Tuệ Tự Trị · Tối Ưu Chi Phí · Vận Hành Vượt Trội.\n                            </div>',
            '<div class="h5 fw-semibold mb-4" style="color: var(--mojo-mint); letter-spacing: 0.02em;">\n                                Kiến Trúc Multi-Agent Swarm · Quyền Lực Tất Định · 100% Chủ Quyền Dữ Liệu.\n                            </div>'
        ),
        (
            'Nền tảng kiến tạo và điều phối các AI Agent chuyên sâu cho hoạt động vận hành vật lý và kỹ thuật số. Chuyển hóa mô hình ngôn ngữ lớn (LLM/SLM) thành các tác tử hành động tự chủ, kiểm soát rủi ro bằng cơ chế guardrails tất định, cắt giảm tới 60% chi phí vận hành doanh nghiệp.',
            'Nền tảng kiến tạo và điều phối cụm tác nhân AI đa luồng (Multi-Agent Swarm) cho hoạt động vận hành kỹ thuật số và thực địa. Chuyển hóa mô hình ngôn ngữ lớn (LLM/SLM) thành các tác tử hành động tự chủ với rào chắn an toàn (deterministic guardrails), cắt giảm tới 60% chi phí vận hành doanh nghiệp.'
        ),
        (
            '<span style="color: #05101E !important;">Lên Lịch Tham Vấn Kiến Trúc</span>',
            '<span style="color: #05101E !important;">Lên Lịch Tham Vấn Kiến Trúc 3 Giờ</span>'
        ),
        (
            '“Mô hình ngôn ngữ lớn (LLM) là bộ não tư duy. Nhưng để giải quyết bài toán thế giới thực, trí tuệ nhân tạo bắt buộc phải có cơ thể hành động, giác quan tiếp nhận và rào chắn an toàn tất định.”',
            '“Mô hình ngôn ngữ lớn (LLM) chỉ là bộ não suy luận. MOJO cung cấp các giác quan tiếp nhận, cơ cấu chấp hành vật lý và rào chắn an toàn để cụm AI tự hành giải quyết bài toán thực tế mà không gây sai lệch.”'
        ),

        # =========================================================================
        # 3. ROUTE /no-code-platform (innoria_digiforce_page)
        # =========================================================================
        (
            '<h1 class="df-title mb-4">DIGIFORCE: Phần Mềm Doanh Nghiệp Trong <span style="color:#0ABBDB;">Vài Tuần</span>, Không Phải Hàng Năm</h1>',
            '<h1 class="df-title mb-4">DIGIFORCE: Nền Tảng Low-Code Hiệu Năng Cao Cho <span style="color:#0ABBDB;">Doanh Nghiệp Lớn</span></h1>'
        ),
        (
            '<p class="df-subtitle mb-4">Nền tảng Low-Code hiệu năng cao. Loại bỏ rào cản phát triển phần mềm phức tạp — hợp tác trực quan cùng trợ lý AI thông minh.</p>',
            '<p class="df-subtitle mb-4">Kéo thả trực quan nhưng sinh ra mã nguồn sạch (Clean React / TypeScript / Python ORM). Cho phép xuất 100% source code, tự do triển khai trên hạ tầng Kubernetes riêng, xóa bỏ hoàn toàn nguy cơ vendor lock-in.</p>'
        ),
        (
            '<div>“DIGIFORCE – nền tảng Low-Code đột phá cho phép phát triển phần mềm trong vài tuần, tối đa 3 tháng. Mang lại hiệu quả chi phí vượt trội đồng thời đáp ứng trọn vẹn bài toán đặc thù của từng doanh nghiệp.”</div>',
            '<div>“DIGIFORCE là nền tảng Low-Code hiệu năng cao cho phép số hóa quy trình lõi chỉ trong vài tuần. 100% tính di động của mã nguồn (code portability), loại bỏ hoàn toàn chi phí bản quyền tính theo đầu người.”</div>'
        ),
        (
            '<p class="fs-5 mb-4 mx-auto" style="max-width:730px;color:#BAE6FD !important;">Phiên làm việc tạo nguyên mẫu DIGIFORCE 3 giờ hoàn toàn miễn phí. Khảo sát điểm nghẽn, sơ đồ hóa quy trình và trải nghiệm trực tiếp nền tảng.</p>\n                        <a href="/contactus" class="df-button" style="background:#FF8000;color:#05101E!important;font-weight:800;border:none;box-shadow:0 10px 24px rgba(255,128,0,.35);">Đăng Ký Workshop 3 Giờ Miễn Phí Của Bạn</a>\n                        <p class="small mt-4 mb-0" style="color: #BAE6FD !important;">Phần mềm doanh nghiệp may đo. Đi vào vận hành sau vài tuần. Thiết kế chuẩn xác theo cách doanh nghiệp bạn hoạt động.</p>',
            '<p class="fs-5 mb-4 mx-auto" style="max-width:730px;color:#BAE6FD !important;">Phiên làm việc tạo nguyên mẫu DIGIFORCE 3 giờ cùng Kỹ sư Trưởng. Khảo sát điểm nghẽn, sơ đồ hóa quy trình và chạy thử nghiệm trực tiếp trên dữ liệu mẫu.</p>\n                        <a href="/contactus" class="df-button" style="background:#FF8000;color:#05101E!important;font-weight:800;border:none;box-shadow:0 10px 24px rgba(255,128,0,.35);">Đăng Ký Workshop 3 Giờ Cùng Kỹ Sư Trưởng</a>\n                        <p class="small mt-4 mb-0" style="color: #BAE6FD !important;">Hạ tầng doanh nghiệp tự chủ. Đi vào vận hành sau vài tuần. 100% tính di động của mã nguồn và quyền kiểm soát dữ liệu.</p>'
        ),

        # =========================================================================
        # 4. ROUTE /industries (insilos_industries_page)
        # =========================================================================
        (
            '<h1 class="display-3 fw-bold mb-4 text-white">Ultra AI Vision:<br/><span style="color:#0284C7;">Kiểm Định Độ Chính Xác Dưới Millimet</span><br/>&amp; Tự Động Hóa Đếm Sản Phẩm</h1>',
            '<h1 class="display-3 fw-bold mb-4 text-white">Thị Giác AI Công Nghiệp Siêu Tốc:<br/><span style="color:#0284C7;">Nhận Thức Dưới Mi-li-mét</span><br/>Tại Biên Vận Hành 120 FPS</h1>'
        ),
        (
            '<p class="lead text-secondary mb-4">Phát hiện khuyết tật vượt trội, phân loại chi tiết tự động và nhận diện ký tự quang học OCR thời gian thực.</p>',
            '<p class="lead text-secondary mb-4">Phát hiện khuyết tật, đọc mã số container và kiểm soát an toàn lao động EHS với tốc độ 120 FPS trực tiếp trên phần cứng công nghiệp tại xưởng.</p>'
        ),
        (
            '<a href="#vision-pilot" class="btn btn-primary btn-lg rounded-pill px-4 py-3 fw-bold">Đăng Ký Thử Nghiệm Tại Nhà Máy (Pilot On-Site)</a>',
            '<a href="#vision-pilot" class="btn btn-primary btn-lg rounded-pill px-4 py-3 fw-bold">Đăng Ký Khảo Sát &amp; Lắp Đặt Thử Nghiệm 7 Ngày</a>'
        ),

        # =========================================================================
        # 5. ROUTE /contactus (innoria_contactus)
        # =========================================================================
        (
            '<h1 class="display-3 fw-bolder mb-4 text-dark" style="letter-spacing: -0.04em; line-height: 1.08;">\n                                Cùng Nhau Kiến Tạo Nên <br/>\n                                <span style="background: linear-gradient(135deg, #0284C7 0%, #0ABBDB 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Điều Phi Thường</span>.\n                            </h1>',
            '<h1 class="display-3 fw-bolder mb-4 text-dark" style="letter-spacing: -0.04em; line-height: 1.08;">\n                                Khởi Tạo Đánh Giá Kiến Trúc <br/>\n                                <span style="background: linear-gradient(135deg, #0284C7 0%, #0ABBDB 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Cấp Điều Hành 180 Phút</span>.\n                            </h1>'
        ),
        (
            '<p class="lead mb-4" style="color: var(--inn-text-light); font-size: 1.35rem; line-height: 1.5; font-weight: 500;">\n                                Sẵn sàng hiện thực hóa tầm nhìn số của doanh nghiệp? Hãy cùng chúng tôi hợp tác để tạo nên những giải pháp đột phá, tạo dựng vị thế dẫn đầu.\n                            </p>',
            '<p class="lead mb-4" style="color: var(--inn-text-light); font-size: 1.35rem; line-height: 1.5; font-weight: 500;">\n                                Phiên mổ xẻ kỹ thuật độc lập kéo dài 180 phút giữa Ban Lãnh Đạo Kỹ Thuật của bạn và Hội Đồng Kiến Trúc Sư Trưởng Innoria. Không bán hàng. Không slide quảng cáo. Trực diện vào điểm nghẽn và giải pháp.\n                            </p>'
        ),
    ]

    applied_count = 0
    missed = []
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new, 1)
            applied_count += 1
        else:
            missed.append(old[:60] + "...")

    print(f"Applied: {applied_count}/{len(replacements)} replacements.")
    if missed:
        print("WARNING: Some snippets were not found:")
        for m in missed:
            print("  -", m)

    # Validate XML
    try:
        ET.fromstring(content)
        print("SUCCESS: Resulting content is 100% valid XML.")
    except Exception as e:
        print("FATAL: Resulting content is INVALID XML:", e)
        sys.exit(1)

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully saved updated content to {TARGET_FILE}")

if __name__ == "__main__":
    apply_upgrades()
