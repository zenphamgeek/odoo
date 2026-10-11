#!/usr/bin/env python3
"""
tools/apply_final_polish_and_unslop.py
Applies remaining de-slop updates and layout balance wrappers.

Hardened against CWE-200, CWE-321/345, CWE-732 with exact post-state anchors
and atomic POSIX file writing.
"""

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.atomic_io import atomic_write_text

pages_file = REPO_ROOT / "enterprise/insilos_website/views/innoria_pages.xml"

with open(pages_file, "r", encoding="utf-8") as f:
    content = f.read()

orig_content = content
changes = 0

# 1. Swarm status & text
replacements = [
    (
        '<span class="font-monospace text-uppercase small text-secondary" style="font-size: 0.72rem;">// 5 Tác Tử Swarm Trực Chiến:</span>',
        '<span class="font-monospace text-uppercase small text-secondary" style="font-size: 0.72rem;">5 Tác Nhân AI Phối Hợp Trực Chiến:</span>'
    ),
    (
        '<div class="fw-bold text-white font-monospace fs-5" style="color: #FFFFFF !important;">BẢNG ĐIỀU KHIỂN TELEMETRY TÁC TỬ MOJO // CỤM ĐANG HOẠT ĐỘNG</div>\n                                    <div class="small font-monospace" style="font-size: 0.75rem; color: #94A3B8 !important;">NỐT CỤM MÁY CHỦ: VN-SGP-PROD-08 // TUÂN THỦ CÔ LẬP MẠNG AIR-GAPPED</div>',
        '<div class="fw-bold text-white font-monospace fs-5" style="color: #FFFFFF !important;">BẢNG ĐIỀU PHỐI TÁC NHÂN AI MOJO · CỤM ĐANG HOẠT ĐỘNG</div>\n                                    <div class="small font-monospace" style="font-size: 0.75rem; color: #94A3B8 !important;">NÚT TÍNH TOÁN CỤM MÁY CHỦ: SIM-CLUSTER-NODE-01 · TUÂN THỦ CÔ LẬP MẠNG AIR-GAPPED</div>'
    ),
    (
        'Khởi đầu hành trình tự động hóa tác tử thông minh với buổi làm việc chuyên sâu 3 giờ cùng đội ngũ kiến trúc sư trưởng MOJO AI &amp; INNORIA.',
        'Khởi đầu lộ trình tự động hóa tác nhân AI thông minh với phiên làm việc 180 phút chuyên sâu cùng Hội đồng Kiến trúc sư Trưởng MOJO AI &amp; INNORIA.'
    ),
    (
        '<h2 class="df-title mb-4 text-white" style="color: #FFFFFF !important;">Động Cơ Hợp Nhất Đa Công Nghệ</h2>',
        '<h2 class="df-title mb-4 text-white" style="color: #FFFFFF !important;">Kiến Trúc Hợp Nhất Đa Phân Hệ</h2>'
    ),
    (
        'Hoàn toàn chính xác, 100% miễn phí và không đi kèm bất kỳ ràng buộc thương mại hay hợp đồng nào. Tại INNORIA, chúng tôi tin rằng sự tin cậy của doanh nghiệp được xây dựng dựa trên chiều sâu kiến trúc thực chất trước khi tiến hành bất kỳ thỏa thuận thương mại nào. Nếu quý doanh nghiệp nhận thấy nền tảng hoặc dịch vụ chưa phù hợp ở thời điểm hiện tại, toàn bộ bản vẽ thiết kế kiến trúc và lộ trình triển khai được kiến tạo trong phiên làm việc vẫn hoàn toàn thuộc quyền sở hữu của quý vị.',
        'Hoàn toàn miễn phí và không đi kèm bất kỳ ràng buộc thương mại hay hợp đồng ràng buộc nào. Tại INNORIA, niềm tin của các nhà lãnh đạo doanh nghiệp bắt nguồn từ chất lượng phân tích kiến trúc thực chứng, thay vì những cam kết tiếp thị chung chung. Toàn bộ sơ đồ kiến trúc và lộ trình chuyển đổi số được xây dựng trong phiên làm việc sẽ hoàn toàn thuộc quyền sở hữu của quý doanh nghiệp.'
    ),
    (
        '<strong>Bản Vẽ Sơ Đồ Kiến Trúc Mục Tiêu:</strong> Sơ đồ cấu trúc vi dịch vụ khuyến nghị, luồng quy trình tác tử AI và cấu trúc hợp nhất dữ liệu (Data Fabric).',
        '<strong>Bản Vẽ Kiến Trúc Mục Tiêu:</strong> Sơ đồ phân rã microservices đề xuất, luồng dữ liệu tác nhân AI và hạ tầng hợp nhất dữ liệu (Data Fabric).'
    )
]

drift_count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f"[✓] Replaced slop phrase: {old[:50]}...")
    elif new in content:
        print(f"[=] Already applied: {new[:50]}...")
    else:
        drift_count += 1
        print(f"[!] DRIFT WARNING: phrase not found: {old[:50]}...")

# 2. Card Balance: /about 4 Deployment Modes (lines 135-166)
old_modes_block = """                        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-4 g-4">
                            <div class="col">
                                <article class="glass hover-card h-100 p-4">
                                    <div class="eyebrow mb-4">01 · Dedicated Private Cloud</div>
                                    <h3 class="h4">Cụm Đám Mây Doanh Nghiệp Riêng Biệt.</h3>
                                    <p class="text-muted">Cụm đám mây riêng biệt được bảo vệ nghiêm ngặt, mã hóa đầu-cuối và giám sát chủ động 24/7 với độ trễ thấp nhất.</p>
                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Private Cloud</a>
                                </article>
                            </div>
                            <div class="col">
                                <article class="glass hover-card h-100 p-4">
                                    <div class="eyebrow mb-4">02 · Air-Gapped High Security</div>
                                    <h3 class="h4">Triển Khai Cách Ly Tuyệt Đối (Air-Gapped).</h3>
                                    <p class="text-muted">Mô hình ngắt mạng internet hoàn toàn, đáp ứng tiêu chuẩn an ninh dữ liệu cấp quốc gia và cơ sở hạ tầng trọng yếu.</p>
                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Air-Gapped</a>
                                </article>
                            </div>
                            <div class="col">
                                <article class="glass hover-card h-100 p-4">
                                    <div class="eyebrow mb-4">03 · Edge Autonomous Nodes</div>
                                    <h3 class="h4">Nút Tính Toán Biên Xưởng &amp; Cảng.</h3>
                                    <p class="text-muted">Nút tính toán biên công nghiệp lắp đặt trực tiếp tại dây chuyền sản xuất, kho hàng và depot cảng với độ trễ &lt; 12ms.</p>
                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Edge Nodes</a>
                                </article>
                            </div>
                            <div class="col">
                                <article class="glass hover-card h-100 p-4">
                                    <div class="eyebrow mb-4">04 · Co-Engineering Alliance</div>
                                    <h3 class="h4">Liên Minh Đồng Kỹ Nghệ Chuyển Giao.</h3>
                                    <p class="text-muted">Đội ngũ kỹ sư trưởng Innoria chuyển giao trọn vẹn công nghệ, phương pháp luận và mã nguồn cho đội ngũ in-house của khách hàng.</p>
                                    <a href="#consultation" class="text-decoration-none fw-bold" style="color:#0369A1 !important; font-weight:700;">Tìm hiểu Co-Engineering</a>
                                </article>
                            </div>
                        </div>"""

new_modes_block = """                        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-4 g-4">
                            <div class="col">
                                <article class="glass hover-card h-100 p-4 d-flex flex-column justify-content-between">
                                    <div>
                                        <div class="eyebrow mb-4">01 · Dedicated Private Cloud</div>
                                        <h3 class="h4">Cụm Đám Mây Doanh Nghiệp Riêng Biệt.</h3>
                                        <p class="text-muted mb-0">Cụm đám mây riêng biệt được bảo vệ nghiêm ngặt, mã hóa đầu-cuối và giám sát chủ động 24/7 với độ trễ thấp nhất.</p>
                                    </div>
                                    <div class="pt-3">
                                        <a href="#consultation" class="text-decoration-none fw-bold d-inline-flex align-items-center gap-1" style="color:#0369A1 !important; font-weight:700;">
                                            <span>Tìm hiểu Private Cloud</span>
                                            <span>→</span>
                                        </a>
                                    </div>
                                </article>
                            </div>
                            <div class="col">
                                <article class="glass hover-card h-100 p-4 d-flex flex-column justify-content-between">
                                    <div>
                                        <div class="eyebrow mb-4">02 · Air-Gapped High Security</div>
                                        <h3 class="h4">Triển Khai Cách Ly Tuyệt Đối (Air-Gapped).</h3>
                                        <p class="text-muted mb-0">Mô hình ngắt mạng internet hoàn toàn, đáp ứng tiêu chuẩn an ninh dữ liệu cấp quốc gia và cơ sở hạ tầng trọng yếu.</p>
                                    </div>
                                    <div class="pt-3">
                                        <a href="#consultation" class="text-decoration-none fw-bold d-inline-flex align-items-center gap-1" style="color:#0369A1 !important; font-weight:700;">
                                            <span>Tìm hiểu Air-Gapped</span>
                                            <span>→</span>
                                        </a>
                                    </div>
                                </article>
                            </div>
                            <div class="col">
                                <article class="glass hover-card h-100 p-4 d-flex flex-column justify-content-between">
                                    <div>
                                        <div class="eyebrow mb-4">03 · Edge Autonomous Nodes</div>
                                        <h3 class="h4">Nút Tính Toán Biên Xưởng &amp; Cảng.</h3>
                                        <p class="text-muted mb-0">Nút tính toán biên công nghiệp lắp đặt trực tiếp tại dây chuyền sản xuất, kho hàng và depot cảng với độ trễ &lt; 12ms.</p>
                                    </div>
                                    <div class="pt-3">
                                        <a href="#consultation" class="text-decoration-none fw-bold d-inline-flex align-items-center gap-1" style="color:#0369A1 !important; font-weight:700;">
                                            <span>Tìm hiểu Edge Nodes</span>
                                            <span>→</span>
                                        </a>
                                    </div>
                                </article>
                            </div>
                            <div class="col">
                                <article class="glass hover-card h-100 p-4 d-flex flex-column justify-content-between">
                                    <div>
                                        <div class="eyebrow mb-4">04 · Co-Engineering Alliance</div>
                                        <h3 class="h4">Liên Minh Đồng Kỹ Nghệ Chuyển Giao.</h3>
                                        <p class="text-muted mb-0">Đội ngũ kỹ sư trưởng Innoria chuyển giao trọn vẹn công nghệ, phương pháp luận và mã nguồn cho đội ngũ in-house của khách hàng.</p>
                                    </div>
                                    <div class="pt-3">
                                        <a href="#consultation" class="text-decoration-none fw-bold d-inline-flex align-items-center gap-1" style="color:#0369A1 !important; font-weight:700;">
                                            <span>Tìm hiểu Co-Engineering</span>
                                            <span>→</span>
                                        </a>
                                    </div>
                                </article>
                            </div>
                        </div>"""

if old_modes_block in content:
    content = content.replace(old_modes_block, new_modes_block)
    changes += 1
    print("[✓] Upgraded /about 4 Deployment Mode cards with symmetrical bottom alignment.")
elif new_modes_block in content:
    print("[=] Already applied: /about 4 Deployment Mode cards.")
else:
    drift_count += 1
    print("[!] DRIFT WARNING: old_modes_block not matched in /about.")

# 3. Card Balance: /solutions 4 ROI cards (lines 2973-3008)
old_roi_block = """                                    <div class="col-md-6">
                                        <div class="ins-spatial-layer h-100 p-4 rounded-4">
                                            <div class="small fw-bold mb-2" style="color: #00F0FF;">CHI PHÍ BẢN QUYỀN &amp; TỰ ĐỘNG HÓA</div>
                                            <div class="display-6 fw-bold text-white mb-2">-65%</div>
                                            <p class="small mb-0" style="color: #94A3B8;">Loại bỏ chi phí mua nhiều phần mềm rời rạc (CRM riêng, Kế toán riêng, Quản lý kho riêng, TMS riêng).</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="ins-spatial-layer h-100 p-4 rounded-4">
                                            <div class="small fw-bold mb-2" style="color: #10B981;">TỐC ĐỘ ĐÓNG SỔ KẾ TOÁN CUỐI THÁNG</div>
                                            <div class="display-6 fw-bold text-white mb-2">2 NGÀY</div>
                                            <p class="small mb-0" style="color: #94A3B8;">Rút ngắn thời gian lập báo cáo tài chính và chốt sổ giá thành từ 12-15 ngày xuống còn 48 giờ làm việc.</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="ins-spatial-layer h-100 p-4 rounded-4">
                                            <div class="small fw-bold mb-2" style="color: #F59E0B;">THỜI GIAN HOÀN VỐN ĐẦU TƯ ROI</div>
                                            <div class="display-6 fw-bold text-white mb-2">6 - 9 THÁNG</div>
                                            <p class="small mb-0" style="color: #94A3B8;">Thu hồi toàn bộ chi phí triển khai và đào tạo nhờ cắt giảm phí phạt bãi cảng và hao hụt nguyên vật liệu.</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="ins-spatial-layer h-100 p-4 rounded-4">
                                            <div class="small fw-bold mb-2" style="color: #8B5CF6;">TỶ LỆ GIAO HÀNG ĐÚNG HẸN OTIF</div>
                                            <div class="display-6 fw-bold text-white mb-2">98.8%</div>
                                            <p class="small mb-0" style="color: #94A3B8;">Hạn chế tối đa chậm trễ đơn hàng, nâng cao mức độ hài lòng và uy tín thương hiệu đối tác.</p>
                                        </div>
                                    </div>"""

new_roi_block = """                                    <div class="col-md-6">
                                        <div class="ins-cardless-kpi h-100 border-top border-white-10 pt-3 d-flex flex-column justify-content-between">
                                            <div>
                                                <div class="small fw-bold mb-2" style="color: #00F0FF;">CHI PHÍ BẢN QUYỀN &amp; TỰ ĐỘNG HÓA</div>
                                                <div class="display-6 fw-bold text-white mb-2">-65%</div>
                                            </div>
                                            <p class="small mb-0 mt-3" style="color: #94A3B8;">Loại bỏ chi phí mua nhiều phần mềm rời rạc (CRM riêng, Kế toán riêng, Quản lý kho riêng, TMS riêng).</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="ins-cardless-kpi h-100 border-top border-white-10 pt-3 d-flex flex-column justify-content-between">
                                            <div>
                                                <div class="small fw-bold mb-2" style="color: #10B981;">TỐC ĐỘ ĐÓNG SỔ KẾ TOÁN CUỐI THÁNG</div>
                                                <div class="display-6 fw-bold text-white mb-2">2 NGÀY</div>
                                            </div>
                                            <p class="small mb-0 mt-3" style="color: #94A3B8;">Rút ngắn thời gian lập báo cáo tài chính và chốt sổ giá thành từ 12-15 ngày xuống còn 48 giờ làm việc.</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="ins-cardless-kpi h-100 border-top border-white-10 pt-3 d-flex flex-column justify-content-between">
                                            <div>
                                                <div class="small fw-bold mb-2" style="color: #F59E0B;">THỜI GIAN HOÀN VỐN ĐẦU TƯ ROI</div>
                                                <div class="display-6 fw-bold text-white mb-2">6 - 9 THÁNG</div>
                                            </div>
                                            <p class="small mb-0 mt-3" style="color: #94A3B8;">Thu hồi toàn bộ chi phí triển khai và đào tạo nhờ cắt giảm phí phạt bãi cảng và hao hụt nguyên vật liệu.</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="ins-cardless-kpi h-100 border-top border-white-10 pt-3 d-flex flex-column justify-content-between">
                                            <div>
                                                <div class="small fw-bold mb-2" style="color: #8B5CF6;">TỶ LỆ GIAO HÀNG ĐÚNG HẸN OTIF</div>
                                                <div class="display-6 fw-bold text-white mb-2">98.8%</div>
                                            </div>
                                            <p class="small mb-0 mt-3" style="color: #94A3B8;">Hạn chế tối đa chậm trễ đơn hàng, nâng cao mức độ hài lòng và uy tín thương hiệu đối tác.</p>
                                        </div>
                                    </div>"""

if old_roi_block in content:
    content = content.replace(old_roi_block, new_roi_block)
    changes += 1
    print("[✓] Upgraded /solutions 4 ROI cards with symmetrical bottom alignment.")
elif new_roi_block in content:
    print("[=] Already applied: /solutions 4 ROI cards.")
else:
    drift_count += 1
    print("[!] DRIFT WARNING: old_roi_block not matched in /solutions.")

# 4. Card Balance: /blockchain Swarm PDCA 5 Roles (lines 2160-2252)
old_roles_block = """                            <!-- Role 1: Explorer -->
                            <div class="col-lg-4 col-md-6">
                                <div class="p-4 rounded-4 h-100 position-relative" style="background: #070B14; border: 1px solid rgba(66, 230, 195, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div class="d-flex align-items-center justify-content-between mb-3">
                                        <span class="font-mono text-muted small">01 // PLAN</span>
                                        <span class="badge rounded-pill" style="background: rgba(66, 230, 195, 0.15); color: #42E6C3; border: 1px solid #42E6C3;">EXPLORER AGENT</span>
                                    </div>
                                    <h3 class="h4 fw-bold text-white mb-3">Điều Tra &amp; Thăm Dò Cấu Trúc</h3>
                                    <p class="text-secondary small mb-3">Quét toàn bộ AST của Monorepo, lập bản đồ quan hệ giữa các microservices, định vị chính xác phạm vi ảnh hưởng và xây dựng kế hoạch phân rã.</p>
                                    <ul class="text-muted small ps-3 mb-0">
                                        <li>AST Call-Graph Dependency Analysis</li>
                                        <li>Zero-Hallucination Scope Mapping</li>
                                        <li>Schema Invariance Audit Pre-flight</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 2: Worker -->
                            <div class="col-lg-4 col-md-6">
                                <div class="p-4 rounded-4 h-100 position-relative" style="background: #070B14; border: 1px solid rgba(0, 240, 255, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div class="d-flex align-items-center justify-content-between mb-3">
                                        <span class="font-mono text-muted small">02 // DO</span>
                                        <span class="badge rounded-pill" style="background: rgba(0, 240, 255, 0.15); color: #00F0FF; border: 1px solid #00F0FF;">WORKER AGENT</span>
                                    </div>
                                    <h3 class="h4 fw-bold text-white mb-3">Hiện Thực Hóa Mã Nguồn</h3>
                                    <p class="text-secondary small mb-3">Viết mã theo chuẩn kiến trúc, đảm bảo tuân thủ nghiêm ngặt các Invariants, tạo Pull Request cục bộ trong không gian làm việc cô lập.</p>
                                    <ul class="text-muted small ps-3 mb-0">
                                        <li>Deterministic Code Generation</li>
                                        <li>Isolated Sandbox Git Worktree</li>
                                        <li>Strict Schema Invariance Preservation</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 3: Reviewer -->
                            <div class="col-lg-4 col-md-6">
                                <div class="p-4 rounded-4 h-100 position-relative" style="background: #070B14; border: 1px solid rgba(139, 92, 246, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div class="d-flex align-items-center justify-content-between mb-3">
                                        <span class="font-mono text-muted small">03 // CHECK</span>
                                        <span class="badge rounded-pill" style="background: rgba(139, 92, 246, 0.15); color: #A78BFA; border: 1px solid #8B5CF6;">REVIEWER AGENT</span>
                                    </div>
                                    <h3 class="h4 fw-bold text-white mb-3">Thẩm Tra Quy Chuẩn &amp; Test</h3>
                                    <p class="text-secondary small mb-3">Kiểm tra tính sạch sẽ của mã, đối chiếu quy chuẩn kỹ thuật ngân hàng, chạy bộ kiểm thử đơn vị và xác thực độ phủ kiểm thử (Test Coverage).</p>
                                    <ul class="text-muted small ps-3 mb-0">
                                        <li>Automated Linting &amp; Static Analysis</li>
                                        <li>Regression Guard Verification</li>
                                        <li>HOOT &amp; E2E Automated Suites</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 4: Challenger -->
                            <div class="col-lg-6 col-md-6">
                                <div class="p-4 rounded-4 h-100 position-relative" style="background: #070B14; border: 1px solid rgba(245, 158, 11, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div class="d-flex align-items-center justify-content-between mb-3">
                                        <span class="font-mono text-muted small">04 // ADVERSARIAL</span>
                                        <span class="badge rounded-pill" style="background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid #F59E0B;">CHALLENGER AGENT</span>
                                    </div>
                                    <h3 class="h4 fw-bold text-white mb-3">Tấn Công Đối Kháng &amp; Stress Test</h3>
                                    <p class="text-secondary small mb-3">Đóng vai hacker và tình huống lỗi hệ thống: thực hiện Fuzzing dữ liệu ngẫu nhiên, mô phỏng nghẽn mạng, race conditions, replay attacks và xung đột khóa phân tán.</p>
                                    <ul class="text-muted small ps-3 mb-0">
                                        <li>Chaos Engineering &amp; Fault Injection</li>
                                        <li>High-Concurrency Idempotency Attack</li>
                                        <li>Double-Spending &amp; Balance Race Validation</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 5: Forensic Auditor -->
                            <div class="col-lg-6 col-md-12">
                                <div class="p-4 rounded-4 h-100 position-relative" style="background: #070B14; border: 1px solid rgba(239, 68, 68, 0.35); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div class="d-flex align-items-center justify-content-between mb-3">
                                        <span class="font-mono text-muted small">05 // BINARY VETO</span>
                                        <span class="badge rounded-pill" style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid #EF4444;">FORENSIC AUDITOR AGENT</span>
                                    </div>
                                    <h3 class="h4 fw-bold text-white mb-3">Kiểm Toán Pháp Y &amp; Quyền Phủ Quyết Tuyệt Đối</h3>
                                    <p class="text-secondary small mb-3">Có quyền phủ quyết nhị phân tuyệt đối (`Binary Veto = 0`). Nếu phát hiện dù chỉ một rò rỉ telemetry, một vi phạm invariant kế toán hoặc lỗ hổng bảo mật, toàn bộ tác vụ lập tức bị từ chối.</p>
                                    <ul class="text-muted small ps-3 mb-0">
                                        <li>Zero-Leak Outbound Telemetry Scan</li>
                                        <li>Cryptographic Audit Trail Anchoring</li>
                                        <li>Absolute Binary Pass/Fail Gate</li>
                                    </ul>
                                </div>
                            </div>"""

new_roles_block = """                            <!-- Role 1: Explorer -->
                            <div class="col-lg-4 col-md-6">
                                <div class="p-4 rounded-2 h-100 position-relative d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(66, 230, 195, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div>
                                        <div class="d-flex align-items-center justify-content-between mb-3">
                                            <span class="font-mono text-muted small">01 · PLAN</span>
                                            <span class="badge rounded-1" style="background: rgba(66, 230, 195, 0.15); color: #42E6C3; border: 1px solid #42E6C3;">TÁC NHÂN KHẢO SÁT</span>
                                        </div>
                                        <h3 class="h4 fw-bold text-white mb-3">Điều Tra &amp; Thăm Dò Cấu Trúc</h3>
                                        <p class="text-secondary small mb-3">Quét toàn bộ AST của Monorepo, lập bản đồ quan hệ giữa các microservices, định vị chính xác phạm vi ảnh hưởng và xây dựng kế hoạch phân rã.</p>
                                    </div>
                                    <ul class="text-muted small ps-3 mb-0 pt-2 border-top border-white-10">
                                        <li>AST Call-Graph Dependency Analysis</li>
                                        <li>Zero-Hallucination Scope Mapping</li>
                                        <li>Schema Invariance Audit Pre-flight</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 2: Worker -->
                            <div class="col-lg-4 col-md-6">
                                <div class="p-4 rounded-2 h-100 position-relative d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(0, 240, 255, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div>
                                        <div class="d-flex align-items-center justify-content-between mb-3">
                                            <span class="font-mono text-muted small">02 · DO</span>
                                            <span class="badge rounded-1" style="background: rgba(0, 240, 255, 0.15); color: #00F0FF; border: 1px solid #00F0FF;">TÁC NHÂN THỰC THI</span>
                                        </div>
                                        <h3 class="h4 fw-bold text-white mb-3">Hiện Thực Hóa Mã Nguồn</h3>
                                        <p class="text-secondary small mb-3">Viết mã theo chuẩn kiến trúc, đảm bảo tuân thủ nghiêm ngặt các Invariants, tạo Pull Request cục bộ trong không gian làm việc cô lập.</p>
                                    </div>
                                    <ul class="text-muted small ps-3 mb-0 pt-2 border-top border-white-10">
                                        <li>Deterministic Code Generation</li>
                                        <li>Isolated Sandbox Git Worktree</li>
                                        <li>Strict Schema Invariance Preservation</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 3: Reviewer -->
                            <div class="col-lg-4 col-md-6">
                                <div class="p-4 rounded-2 h-100 position-relative d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(139, 92, 246, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div>
                                        <div class="d-flex align-items-center justify-content-between mb-3">
                                            <span class="font-mono text-muted small">03 · CHECK</span>
                                            <span class="badge rounded-1" style="background: rgba(139, 92, 246, 0.15); color: #A78BFA; border: 1px solid #8B5CF6;">TÁC NHÂN THẨM ĐỊNH</span>
                                        </div>
                                        <h3 class="h4 fw-bold text-white mb-3">Thẩm Tra Quy Chuẩn &amp; Test</h3>
                                        <p class="text-secondary small mb-3">Kiểm tra tính sạch sẽ của mã, đối chiếu quy chuẩn kỹ thuật ngân hàng, chạy bộ kiểm thử đơn vị và xác thực độ phủ kiểm thử (Test Coverage).</p>
                                    </div>
                                    <ul class="text-muted small ps-3 mb-0 pt-2 border-top border-white-10">
                                        <li>Automated Linting &amp; Static Analysis</li>
                                        <li>Regression Guard Verification</li>
                                        <li>HOOT &amp; E2E Automated Suites</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 4: Challenger -->
                            <div class="col-lg-6 col-md-6">
                                <div class="p-4 rounded-2 h-100 position-relative d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(245, 158, 11, 0.25); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div>
                                        <div class="d-flex align-items-center justify-content-between mb-3">
                                            <span class="font-mono text-muted small">04 · ADVERSARIAL</span>
                                            <span class="badge rounded-1" style="background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid #F59E0B;">TÁC NHÂN ĐỐI KHÁNG</span>
                                        </div>
                                        <h3 class="h4 fw-bold text-white mb-3">Tấn Công Đối Kháng &amp; Stress Test</h3>
                                        <p class="text-secondary small mb-3">Đóng vai hacker và tình huống lỗi hệ thống: thực hiện Fuzzing dữ liệu ngẫu nhiên, mô phỏng nghẽn mạng, race conditions, replay attacks và xung đột khóa phân tán.</p>
                                    </div>
                                    <ul class="text-muted small ps-3 mb-0 pt-2 border-top border-white-10">
                                        <li>Chaos Engineering &amp; Fault Injection</li>
                                        <li>High-Concurrency Idempotency Attack</li>
                                        <li>Double-Spending &amp; Balance Race Validation</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Role 5: Forensic Auditor -->
                            <div class="col-lg-6 col-md-12">
                                <div class="p-4 rounded-2 h-100 position-relative d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(239, 68, 68, 0.35); box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
                                    <div>
                                        <div class="d-flex align-items-center justify-content-between mb-3">
                                            <span class="font-mono text-muted small">05 · BINARY VETO</span>
                                            <span class="badge rounded-1" style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid #EF4444;">TÁC NHÂN KIỂM TOÁN (BINARY VETO)</span>
                                        </div>
                                        <h3 class="h4 fw-bold text-white mb-3">Kiểm Toán Pháp Y &amp; Quyền Phủ Quyết Tuyệt Đối</h3>
                                        <p class="text-secondary small mb-3">Có quyền phủ quyết nhị phân tuyệt đối (`Binary Veto = 0`). Nếu phát hiện dù chỉ một rò rỉ telemetry, một vi phạm invariant kế toán hoặc lỗ hổng bảo mật, toàn bộ tác vụ lập tức bị từ chối.</p>
                                    </div>
                                    <ul class="text-muted small ps-3 mb-0 pt-2 border-top border-white-10">
                                        <li>Zero-Leak Outbound Telemetry Scan</li>
                                        <li>Cryptographic Audit Trail Anchoring</li>
                                        <li>Absolute Binary Pass/Fail Gate</li>
                                    </ul>
                                </div>
                            </div>"""

if old_roles_block in content:
    content = content.replace(old_roles_block, new_roles_block)
    changes += 1
    print("[✓] Upgraded /blockchain Swarm PDCA 5 Roles cards with symmetrical bottom alignment.")
elif new_roles_block in content:
    print("[=] Already applied: /blockchain Swarm PDCA 5 Roles cards.")
else:
    drift_count += 1
    print("[!] DRIFT WARNING: old_roles_block not matched in /blockchain.")

# 5. Card Balance: /blockchain 3 Use Case cards (lines 2326-2368)
old_use_cases = """                            <!-- Case 1 -->
                            <div class="col-lg-4">
                                <div class="p-4 rounded-4 h-100" style="background: #070B14; border: 1px solid rgba(66, 230, 195, 0.25);">
                                    <div class="font-mono text-muted small mb-2">USE CASE 01</div>
                                    <h3 class="h5 fw-bold text-white mb-3">Hiện Đại Hóa Core Banking (Strangler-Fig Pattern)</h3>
                                    <p class="text-secondary small mb-3">Tách nhỏ lõi ngân hàng di sản hàng triệu dòng mã sang microservices hiện đại theo kiến trúc Strangler-Fig, hoạt động song song không gián đoạn dịch vụ.</p>
                                    <div class="p-3 rounded-3" style="background: #0B1220;">
                                        <div class="small fw-bold" style="color: #42E6C3;">KẾT QUẢ ĐẠT ĐƯỢC:</div>
                                        <div class="small text-muted">0 giây downtime, giảm -70% thời gian triển khai tính năng thanh toán mới.</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Case 2 -->
                            <div class="col-lg-4">
                                <div class="p-4 rounded-4 h-100" style="background: #070B14; border: 1px solid rgba(0, 240, 255, 0.25);">
                                    <div class="font-mono text-muted small mb-2">USE CASE 02</div>
                                    <h3 class="h5 fw-bold text-white mb-3">Cổng Chuyển Mạch Thanh Toán (85,000+ TPS)</h3>
                                    <p class="text-secondary small mb-3">Tối ưu hóa bộ xử lý giao dịch với cơ chế kiểm thực khóa Idempotency Key phân tán, chống hoàn toàn sự cố trùng lặp giao dịch khi nghẽn mạng viễn thông.</p>
                                    <div class="p-3 rounded-3" style="background: #0B1220;">
                                        <div class="small fw-bold" style="color: #00F0FF;">KẾT QUẢ ĐẠT ĐƯỢC:</div>
                                        <div class="small text-muted">Độ trễ p99 &lt; 15ms, chống 100% tấn công lặp lệnh (Double-spending).</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Case 3 -->
                            <div class="col-lg-4">
                                <div class="p-4 rounded-4 h-100" style="background: #070B14; border: 1px solid rgba(245, 158, 11, 0.25);">
                                    <div class="font-mono text-muted small mb-2">USE CASE 03</div>
                                    <h3 class="h5 fw-bold text-white mb-3">Đối Soát Giao Dịch &amp; Sổ Cái Liên Ngân Hàng</h3>
                                    <p class="text-secondary small mb-3">Tự động hóa đối soát 3 chiều giữa Ngân hàng - Cổng thanh toán - Đơn vị chấp nhận thẻ, tự động bồi hoàn giao dịch treo và phát hiện bất thường gian lận.</p>
                                    <div class="p-3 rounded-3" style="background: #0B1220;">
                                        <div class="small fw-bold" style="color: #FBBF24;">KẾT QUẢ ĐẠT ĐƯỢC:</div>
                                        <div class="small text-muted">Đối soát hoàn tất trong 3.2 phút thay vì 24 giờ thủ công; 0 sai lệch số dư.</div>
                                    </div>
                                </div>
                            </div>"""

new_use_cases = """                            <!-- Case 1 -->
                            <div class="col-lg-4">
                                <div class="p-4 rounded-2 h-100 d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(66, 230, 195, 0.25);">
                                    <div>
                                        <div class="font-mono text-muted small mb-2">USE CASE 01</div>
                                        <h3 class="h5 fw-bold text-white mb-3">Hiện Đại Hóa Core Banking (Strangler-Fig Pattern)</h3>
                                        <p class="text-secondary small mb-3">Tách nhỏ lõi ngân hàng di sản hàng triệu dòng mã sang microservices hiện đại theo kiến trúc Strangler-Fig, hoạt động song song không gián đoạn dịch vụ.</p>
                                    </div>
                                    <div class="p-3 rounded-3 mt-3" style="background: #0B1220;">
                                        <div class="small fw-bold" style="color: #42E6C3;">KẾT QUẢ ĐẠT ĐƯỢC:</div>
                                        <div class="small text-muted">0 giây downtime, giảm -70% thời gian triển khai tính năng thanh toán mới.</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Case 2 -->
                            <div class="col-lg-4">
                                <div class="p-4 rounded-2 h-100 d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(0, 240, 255, 0.25);">
                                    <div>
                                        <div class="font-mono text-muted small mb-2">USE CASE 02</div>
                                        <h3 class="h5 fw-bold text-white mb-3">Cổng Chuyển Mạch Thanh Toán (85,000+ TPS)</h3>
                                        <p class="text-secondary small mb-3">Tối ưu hóa bộ xử lý giao dịch với cơ chế kiểm thực khóa Idempotency Key phân tán, chống hoàn toàn sự cố trùng lặp giao dịch khi nghẽn mạng viễn thông.</p>
                                    </div>
                                    <div class="p-3 rounded-3 mt-3" style="background: #0B1220;">
                                        <div class="small fw-bold" style="color: #00F0FF;">KẾT QUẢ ĐẠT ĐƯỢC:</div>
                                        <div class="small text-muted">Độ trễ p99 &lt; 15ms, chống 100% tấn công lặp lệnh (Double-spending).</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Case 3 -->
                            <div class="col-lg-4">
                                <div class="p-4 rounded-2 h-100 d-flex flex-column justify-content-between" style="background: #070B14; border: 1px solid rgba(245, 158, 11, 0.25);">
                                    <div>
                                        <div class="font-mono text-muted small mb-2">USE CASE 03</div>
                                        <h3 class="h5 fw-bold text-white mb-3">Đối Soát Giao Dịch &amp; Sổ Cái Liên Ngân Hàng</h3>
                                        <p class="text-secondary small mb-3">Tự động hóa đối soát 3 chiều giữa Ngân hàng - Cổng thanh toán - Đơn vị chấp nhận thẻ, tự động bồi hoàn giao dịch treo và phát hiện bất thường gian lận.</p>
                                    </div>
                                    <div class="p-3 rounded-3 mt-3" style="background: #0B1220;">
                                        <div class="small fw-bold" style="color: #FBBF24;">KẾT QUẢ ĐẠT ĐƯỢC:</div>
                                        <div class="small text-muted">Đối soát hoàn tất trong 3.2 phút thay vì 24 giờ thủ công; 0 sai lệch số dư.</div>
                                    </div>
                                </div>
                            </div>"""

if old_use_cases in content:
    content = content.replace(old_use_cases, new_use_cases)
    changes += 1
    print("[✓] Upgraded /blockchain 3 Use Case cards with symmetrical bottom alignment.")
elif new_use_cases in content:
    print("[=] Already applied: /blockchain 3 Use Case cards.")
else:
    drift_count += 1
    print("[!] DRIFT WARNING: old_use_cases not matched in /blockchain.")

if content != orig_content:
    atomic_write_text(pages_file, content)
    print(f"\n[✓] Total {changes} updates atomically written to {pages_file}.")
else:
    print(f"\n[i] No changes needed; {pages_file} is untouched.")

if drift_count > 0:
    sys.exit(f"[!] Refusing success: {drift_count} phrase(s) drifted or missing.")
