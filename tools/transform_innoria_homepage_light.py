#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

path = 'enterprise/insilos_website/views/innoria_homepage.xml'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Navbar dropdown
content = content.replace(
    'class="dropdown-menu dropdown-menu-dark border-0 shadow-lg" aria-labelledby="innoriaPlatformDropdown" style="background-color: #1F2937; border: 1px solid rgba(255,255,255,0.08) !important;"',
    'class="dropdown-menu border-0 shadow-lg" aria-labelledby="innoriaPlatformDropdown" style="background-color: #FFFFFF; border: 1px solid #E2E8F0 !important; box-shadow: 0 10px 25px rgba(2, 132, 199, 0.08) !important;"'
)
content = re.sub(r'class="dropdown-item py-2 text-white"', 'class="dropdown-item py-2 text-dark"', content)

# 2. Main wrap
content = content.replace(
    '<main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">',
    '<main id="wrap" class="oe_structure o_colored_level" style="background-color: #FFFFFF; color: #0F172A;">'
)

# 3. Hero section
content = content.replace(
    '<section class="s_cover position-relative o_colored_level o_cc o_cc5 pt80 pb60 overflow-hidden innoria-hero-section"\n                         data-snippet="s_cover"\n                         data-name="Innoria 3D Sovereign Hero"\n                         data-bs-theme="dark"\n                         id="innoria_hero_cover"\n                         style="background-image: radial-gradient(circle at 50% 10%, rgba(10, 187, 219, 0.18) 0%, transparent 65%);">',
    '<section class="s_cover position-relative o_colored_level pt80 pb60 overflow-hidden innoria-hero-section"\n                         data-snippet="s_cover"\n                         data-name="Innoria 3D Sovereign Hero"\n                         id="innoria_hero_cover"\n                         style="background: linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 50%, #F8FAFC 100%);">'
)

# Hero texts
content = content.replace(
    '<h1 class="display-3 fw-bold text-white mb-3 lh-sm">',
    '<h1 class="display-3 fw-bold text-dark mb-3 lh-sm">'
)
content = content.replace(
    '<p class="lead text-secondary fs-5 col-lg-10 mx-auto mb-4">\n                                    Innoria mang nghệ thuật vào công nghệ (<em class="text-white">Brings art into technology</em>) — The Innovation of Real-life Intelligent Application. Hợp nhất Low-Code <strong class="text-white">DIGIFORCE</strong>, hệ sinh thái trí tuệ nhân tạo đa tác nhân <strong class="text-white">MOJO AI</strong>, blockchain <strong class="text-white">MOJOVERSE</strong> và lõi ERP thông minh.\n                                </p>',
    '<p class="lead text-secondary fs-5 col-lg-10 mx-auto mb-4">\n                                    Innoria mang nghệ thuật vào công nghệ (<em class="text-dark">Brings art into technology</em>) — The Innovation of Real-life Intelligent Application. Hợp nhất Low-Code <strong class="text-dark">DIGIFORCE</strong>, hệ sinh thái trí tuệ nhân tạo đa tác nhân <strong class="text-dark">MOJO AI</strong>, blockchain <strong class="text-dark">MOJOVERSE</strong> và lõi ERP thông minh.\n                                </p>'
)
content = content.replace(
    '<a href="#innoria_contact_section" class="btn btn-outline-light rounded-pill px-4 py-3 fw-bold d-inline-flex align-items-center gap-2">',
    '<a href="#innoria_contact_section" class="btn btn-outline-primary rounded-pill px-4 py-3 fw-bold d-inline-flex align-items-center gap-2" style="border-color: #0284C7; color: #0284C7; background: #FFFFFF;">'
)

# 4 metric badges in Hero
content = content.replace(
    '<div class="p-3 rounded-3 bg-dark bg-opacity-50 border border-secondary border-opacity-25">\n                                    <div class="text-secondary small text-uppercase fw-semibold">Thời Gian Triển Khai</div>\n                                    <div class="fs-4 fw-bold text-white mt-1">30 Ngày Go-Live</div>\n                                </div>',
    '<div class="p-3 rounded-3 bg-white border border-slate-200 shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">\n                                    <div class="text-muted small text-uppercase fw-semibold" style="color: #64748B;">Thời Gian Triển Khai</div>\n                                    <div class="fs-4 fw-bold text-dark mt-1">30 Ngày Go-Live</div>\n                                </div>'
)
content = content.replace(
    '<div class="p-3 rounded-3 bg-dark bg-opacity-50 border border-secondary border-opacity-25">\n                                    <div class="text-secondary small text-uppercase fw-semibold">Chi Phí Sở Hữu TCO</div>\n                                    <div class="fs-4 fw-bold text-innoria-mint mt-1">-50% So Với Truyền Thống</div>\n                                </div>',
    '<div class="p-3 rounded-3 bg-white border border-slate-200 shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">\n                                    <div class="text-muted small text-uppercase fw-semibold" style="color: #64748B;">Chi Phí Sở Hữu TCO</div>\n                                    <div class="fs-4 fw-bold mt-1" style="color: #0284C7;">-50% So Với Truyền Thống</div>\n                                </div>'
)
content = content.replace(
    '<div class="p-3 rounded-3 bg-dark bg-opacity-50 border border-secondary border-opacity-25">\n                                    <div class="text-secondary small text-uppercase fw-semibold">Độ Chuẩn Xác VLM AI</div>\n                                    <div class="fs-4 fw-bold text-innoria-cyan mt-1">99.8% Nhận Diện</div>\n                                </div>',
    '<div class="p-3 rounded-3 bg-white border border-slate-200 shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">\n                                    <div class="text-muted small text-uppercase fw-semibold" style="color: #64748B;">Độ Chuẩn Xác VLM AI</div>\n                                    <div class="fs-4 fw-bold mt-1" style="color: #0ABBDB;">99.8% Nhận Diện</div>\n                                </div>'
)
content = content.replace(
    '<div class="p-3 rounded-3 bg-dark bg-opacity-50 border border-secondary border-opacity-25">\n                                    <div class="text-secondary small text-uppercase fw-semibold">Môi Trường Vận Hành</div>\n                                    <div class="fs-4 fw-bold text-innoria-amber mt-1">Air-Gapped &amp; Sovereign</div>\n                                </div>',
    '<div class="p-3 rounded-3 bg-white border border-slate-200 shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">\n                                    <div class="text-muted small text-uppercase fw-semibold" style="color: #64748B;">Môi Trường Vận Hành</div>\n                                    <div class="fs-4 fw-bold mt-1" style="color: #EA580C;">Air-Gapped &amp; Sovereign</div>\n                                </div>'
)

# 4. References Client strip
content = content.replace(
    '<section class="s_references o_colored_level o_cc o_cc5 innoria-client-strip"\n                         data-snippet="s_references"\n                         data-name="Innoria Internationally Trusts"\n                         data-bs-theme="dark">',
    '<section class="s_references o_colored_level innoria-client-strip"\n                         data-snippet="s_references"\n                         data-name="Innoria Internationally Trusts"\n                         style="background: #F8FAFC; border-top: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">'
)

# 5. Architecture section
content = content.replace(
    '<section class="s_image_text o_colored_level o_cc o_cc5 py-5 position-relative"\n                         data-snippet="s_image_text"\n                         data-name="Innoria Platform Architecture"\n                         data-bs-theme="dark"\n                         id="platform">',
    '<section class="s_image_text o_colored_level py-5 position-relative"\n                         data-snippet="s_image_text"\n                         data-name="Innoria Platform Architecture"\n                         id="platform"\n                         style="background: #FFFFFF;">'
)
content = content.replace(
    '<h2 class="display-5 fw-bold text-white mb-3">\n                                    Từ Bài Toán Đến Giải Pháp <span class="text-innoria-gradient">Trong 30 Ngày</span>\n                                </h2>',
    '<h2 class="display-5 fw-bold text-dark mb-3">\n                                    Từ Bài Toán Đến Giải Pháp <span class="text-innoria-gradient">Trong 30 Ngày</span>\n                                </h2>'
)
content = content.replace(
    '<div class="p-3 rounded-4 bg-dark bg-opacity-60 border border-secondary border-opacity-30 shadow-lg">',
    '<div class="p-3 rounded-4 bg-white border shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 10px 30px rgba(10, 187, 219, 0.08);">'
)
# 3 cards in Architecture section
content = re.sub(
    r'<div class="p-3 rounded-3 bg-dark bg-opacity-40 border border-secondary border-opacity-20">\s*<div class="d-flex align-items-center gap-3 mb-2">\s*<div class="([^"]*)">\s*<svg class="([^"]*)" style="([^"]*)"><use href="([^"]*)"/></svg>\s*</div>\s*<h4 class="text-white mb-0 fs-5">([^<]+)</h4>\s*</div>\s*<p class="text-secondary small mb-0">([^<]+)</p>\s*</div>',
    r'<div class="p-3 rounded-3 bg-white border shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);">\n                                        <div class="d-flex align-items-center gap-3 mb-2">\n                                            <div class="\1">\n                                                <svg class="\2" style="\3"><use href="\4"/></svg>\n                                            </div>\n                                            <h4 class="text-dark mb-0 fs-5">\5</h4>\n                                        </div>\n                                        <p class="text-secondary small mb-0">\6</p>\n                                    </div>',
    content
)

# 6. Process steps (Cadence)
content = content.replace(
    '<section class="s_process_steps o_colored_level o_cc o_cc5 py-5 position-relative"\n                         data-snippet="s_process_steps"\n                         data-name="Innoria 4-Stage Cadence"\n                         data-bs-theme="dark">',
    '<section class="s_process_steps o_colored_level py-5 position-relative"\n                         data-snippet="s_process_steps"\n                         data-name="Innoria 4-Stage Cadence"\n                         style="background: #F8FAFC;">'
)
content = content.replace(
    '<h2 class="display-5 fw-bold text-white mb-3">\n                                    Lộ Trình Triển Khai Thực Chiến <span class="text-innoria-gradient-orange">4 Giai Đoạn</span>\n                                </h2>',
    '<h2 class="display-5 fw-bold text-dark mb-3">\n                                    Lộ Trình Triển Khai Thực Chiến <span class="text-innoria-gradient-orange">4 Giai Đoạn</span>\n                                </h2>'
)
content = content.replace(
    '<span class="badge bg-secondary bg-opacity-25 text-white small">Giai Đoạn',
    '<span class="badge bg-light text-secondary border small">Giai Đoạn'
)
content = re.sub(
    r'<h4 class="text-white fs-5 fw-bold mb-2">',
    r'<h4 class="text-dark fs-5 fw-bold mb-2">',
    content
)

# 7. Core Platforms section
content = content.replace(
    '<section class="s_three_columns o_colored_level o_cc o_cc5 py-5 position-relative"\n                         data-snippet="s_three_columns"\n                         data-name="Innoria Core Platforms"\n                         data-bs-theme="dark">',
    '<section class="s_three_columns o_colored_level py-5 position-relative"\n                         data-snippet="s_three_columns"\n                         data-name="Innoria Core Platforms"\n                         style="background: #FFFFFF;">'
)
content = content.replace(
    '<h2 class="display-5 fw-bold text-white mb-3">\n                                    4 Trụ Cột Công Nghệ Độc Lập\n                                </h2>',
    '<h2 class="display-5 fw-bold text-dark mb-3">\n                                    4 Trụ Cột Công Nghệ Độc Lập\n                                </h2>'
)
content = content.replace(
    '<span class="badge bg-secondary bg-opacity-25 text-white small mb-2 font-monospace">',
    '<span class="badge bg-light text-primary border small mb-2 font-monospace">'
)
content = re.sub(
    r'<h3 class="text-white fs-4 fw-bold mb-2">',
    r'<h3 class="text-dark fs-4 fw-bold mb-2">',
    content
)
content = content.replace(
    '<div class="small text-white fw-semibold mb-1">Điểm nổi bật:</div>',
    '<div class="small text-dark fw-semibold mb-1">Điểm nổi bật:</div>'
)

# 8. Key Services
content = content.replace(
    '<section class="s_features o_colored_level o_cc o_cc5 py-5 position-relative"\n                         data-snippet="s_features"\n                         data-name="Innoria Key Services"\n                         data-bs-theme="dark"\n                         id="services">',
    '<section class="s_features o_colored_level py-5 position-relative"\n                         data-snippet="s_features"\n                         data-name="Innoria Key Services"\n                         id="services"\n                         style="background: #F8FAFC;">'
)
content = content.replace(
    '<h2 class="display-5 fw-bold text-white mb-3">\n                                    Đội Ngũ Kỹ Sư Cấp Cao Đồng Hành Cùng Doanh Nghiệp\n                                </h2>',
    '<h2 class="display-5 fw-bold text-dark mb-3">\n                                    Đội Ngũ Kỹ Sư Cấp Cao Đồng Hành Cùng Doanh Nghiệp\n                                </h2>'
)

# 9. Solutions section
content = content.replace(
    '<section class="s_text_image o_colored_level o_cc o_cc5 py-5 position-relative"\n                         data-snippet="s_text_image"\n                         data-name="Innoria Vertical Solutions"\n                         data-bs-theme="dark"\n                         id="solutions">',
    '<section class="s_text_image o_colored_level py-5 position-relative"\n                         data-snippet="s_text_image"\n                         data-name="Innoria Vertical Solutions"\n                         id="solutions"\n                         style="background: #FFFFFF;">'
)
content = content.replace(
    '<h2 class="display-5 fw-bold text-white mb-3">\n                                    Ứng Dụng Thực Chiến Cho Từng Ngành Công Nghiệp\n                                </h2>',
    '<h2 class="display-5 fw-bold text-dark mb-3">\n                                    Ứng Dụng Thực Chiến Cho Từng Ngành Công Nghiệp\n                                </h2>'
)
content = content.replace(
    '<div class="p-4 rounded-3 bg-dark bg-opacity-40 border border-secondary border-opacity-25 h-100">',
    '<div class="p-4 rounded-3 bg-white border h-100 shadow-sm" style="border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);">'
)

# 10. Proof numbers section
content = content.replace(
    '<section class="s_numbers o_colored_level o_cc o_cc5 py-5 position-relative border-top border-bottom border-secondary border-opacity-20"\n                         data-snippet="s_numbers"\n                         data-name="Innoria Proof Numbers"\n                         data-bs-theme="dark">',
    '<section class="s_numbers o_colored_level py-5 position-relative border-top border-bottom"\n                         data-snippet="s_numbers"\n                         data-name="Innoria Proof Numbers"\n                         style="background: #F0F9FF; border-color: #BAE6FD !important;">'
)
content = content.replace(
    '<div class="display-4 fw-bold text-white mb-1">140+</div>',
    '<div class="display-4 fw-bold text-dark mb-1">140+</div>'
)
content = content.replace(
    '<div class="display-4 fw-bold text-innoria-mint mb-1">30 Ngày</div>',
    '<div class="display-4 fw-bold mb-1" style="color: #0284C7;">30 Ngày</div>'
)
content = content.replace(
    '<div class="display-4 fw-bold text-innoria-amber mb-1">-50%</div>',
    '<div class="display-4 fw-bold mb-1" style="color: #EA580C;">-50%</div>'
)

# 11. VIP Consultation Form
content = content.replace(
    '<section class="s_call_to_action o_colored_level o_cc o_cc5 py-5 position-relative overflow-hidden"\n                         data-snippet="s_call_to_action"\n                         data-name="Innoria VIP Consultation Form"\n                         data-bs-theme="dark"\n                         id="innoria_contact_section">',
    '<section class="s_call_to_action o_colored_level py-5 position-relative overflow-hidden"\n                         data-snippet="s_call_to_action"\n                         data-name="Innoria VIP Consultation Form"\n                         id="innoria_contact_section"\n                         style="background: linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 100%);">'
)
content = content.replace(
    '<h2 class="display-5 fw-bold text-white mb-3">\n                                    Sẵn Sàng Rút Ngắn Thời Gian Phát Triển Xuống 30 Ngày?\n                                </h2>',
    '<h2 class="display-5 fw-bold text-dark mb-3">\n                                    Sẵn Sàng Rút Ngắn Thời Gian Phát Triển Xuống 30 Ngày?\n                                </h2>'
)
content = content.replace(
    '<strong class="text-white">3 Hours Executive Briefing</strong>',
    '<strong class="text-dark">3 Hours Executive Briefing</strong>'
)
content = content.replace(
    '<div class="p-4 p-md-5 rounded-4 bg-dark bg-opacity-60 border border-secondary border-opacity-30 shadow-lg">\n                                    <h4 class="text-white fw-bold mb-4">Đăng Ký Tư Vấn Giải Pháp</h4>',
    '<div class="p-4 p-md-5 rounded-4 bg-white shadow-lg" style="border: 1px solid #E2E8F0; box-shadow: 0 20px 40px rgba(2, 132, 199, 0.08);">\n                                    <h4 class="text-dark fw-bold mb-4">Đăng Ký Tư Vấn Giải Pháp</h4>'
)
content = content.replace(
    'class="form-control bg-dark text-white border-secondary border-opacity-40 rounded-3"',
    'class="form-control bg-white text-dark rounded-3" style="border: 1px solid #CBD5E1; color: #0F172A;"'
)
content = re.sub(
    r'<label class="form-label text-secondary small mb-1">',
    r'<label class="form-label text-dark small fw-semibold mb-1">',
    content
)

# 12. Footer
content = content.replace(
    '<footer class="innoria-footer py-5" id="company" style="background-color: #0B0F17 !important; color: #94A3B8 !important; border-top: 1px solid rgba(10, 187, 219, 0.25) !important;">\n            <style>\n                .innoria-footer h6 { color: #FFFFFF !important; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; margin-bottom: 1rem !important; }\n                .innoria-footer-link { color: #94A3B8 !important; text-decoration: none !important; transition: color 0.2s ease !important; }\n                .innoria-footer-link:hover { color: #0ABBDB !important; text-decoration: underline !important; }\n            </style>',
    '<footer class="innoria-footer py-5" id="company" style="background-color: #F8FAFC !important; color: #475569 !important; border-top: 1px solid #E2E8F0 !important;">\n            <style>\n                .innoria-footer h6 { color: #0F172A !important; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; margin-bottom: 1rem !important; }\n                .innoria-footer-link { color: #475569 !important; text-decoration: none !important; transition: color 0.2s ease !important; }\n                .innoria-footer-link:hover { color: #0284C7 !important; text-decoration: underline !important; }\n            </style>'
)
content = content.replace(
    '<h6 class="text-white fw-bold mb-3">',
    '<h6 class="text-dark fw-bold mb-3">'
)
content = content.replace(
    '<strong class="text-white">UNG DUNG SANG TAO LLC</strong>',
    '<strong class="text-dark">UNG DUNG SANG TAO LLC</strong>'
)
content = content.replace(
    '<span class="badge bg-secondary bg-opacity-25 text-white">ISO 27001 // SOC-2</span>\n                        <span class="badge bg-secondary bg-opacity-25 text-white">100% Air-Gapped Ready</span>',
    '<span class="badge bg-light text-dark border">ISO 27001 // SOC-2</span>\n                        <span class="badge bg-light text-dark border">100% Air-Gapped Ready</span>'
)
# Use official logo in footer
content = content.replace(
    '<img src="/insilos_website/static/src/img/innoria/innoria_logo_grayscale.svg" alt="INNORIA Logo" class="footer-logo mb-3" width="160" height="48"/>',
    '<img src="/insilos_website/static/src/img/innoria/logo_innoria_header.svg" alt="INNORIA Logo" class="footer-logo mb-3" width="160" height="48"/>'
)

# Parse check
ET.fromstring(content)
print("XML validation passed successfully!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated enterprise/insilos_website/views/innoria_homepage.xml successfully!")
