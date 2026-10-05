#!/usr/bin/env python3
"""
tools/assemble_innoria_pages.py
=============================================================================
Assembles all 7 Fleet-generated Innoria page templates into a single,
clean, production-ready QWeb XML file:
enterprise/insilos_website/views/innoria_pages.xml
=============================================================================
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

FLEET_DIR = "/tmp/innoria_fleet_results"
OUTPUT_FILE = "/home/zen/O20/enterprise/insilos_website/views/innoria_pages.xml"

PAGES = [
    ("about.xml", "insilos_about_page", "About Us | INNORIA"),
    ("ai_platform.xml", "insilos_platform_page", "MOJO AI Platform | INNORIA"),
    ("no_code.xml", "innoria_digiforce_page", "DIGIFORCE No-Code Platform | INNORIA"),
    ("blockchain.xml", "innoria_blockchain_page", "MOJOVERSE Blockchain Platform | INNORIA"),
    ("erp_ai.xml", "insilos_solutions_page", "AI-Enhanced ERP | INNORIA"),
    ("ultra_ai_vision.xml", "insilos_industries_page", "Ultra AI Vision &amp; Industries | INNORIA"),
    ("contactus.xml", "innoria_contactus", "Contact Us | INNORIA"),
]

NAVBAR_XML = """    <template id="innoria_navbar" name="INNORIA Navbar">
        <nav class="navbar navbar-expand-lg innoria-navbar" id="innoria_main_nav">
            <div class="container d-flex align-items-center justify-content-between">
                <!-- Brand Logo -->
                <a class="navbar-brand py-0 d-flex align-items-center" href="/">
                    <img src="/insilos_website/static/src/img/innoria/logo_innoria_header.svg" alt="INNORIA" class="navbar-brand-logo" width="130" height="38"/>
                </a>

                <!-- Navbar Toggler for Mobile -->
                <button class="navbar-toggler border-0 text-white" type="button" data-bs-toggle="collapse" data-bs-target="#innoriaNavContent" aria-controls="innoriaNavContent" aria-expanded="false" aria-label="Toggle navigation">
                    <svg class="ph-duotone ph-list" style="width: 1.75rem; height: 1.75rem;"><use href="/insilos_website/static/src/icons/phosphor-duotone.svg#ph-list"/></svg>
                </button>

                <!-- Nav Links & Action -->
                <div class="collapse navbar-collapse justify-content-end" id="innoriaNavContent">
                    <ul class="navbar-nav align-items-lg-center gap-lg-2 me-lg-3 my-2 my-lg-0">
                        <li class="nav-item">
                            <a class="nav-link" href="/about">Company</a>
                        </li>
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="innoriaPlatformDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                Platform
                            </a>
                            <ul class="dropdown-menu dropdown-menu-dark border-0 shadow-lg" aria-labelledby="innoriaPlatformDropdown" style="background-color: #1F2937; border: 1px solid rgba(255,255,255,0.08) !important;">
                                <li><a class="dropdown-item py-2 text-white" href="/platform"><strong style="color: #0ABBDB;">MOJO AI</strong> — AI Agent Platform</a></li>
                                <li><a class="dropdown-item py-2 text-white" href="/no-code-platform"><strong style="color: #FF8000;">DIGIFORCE</strong> — No-Code Engine</a></li>
                                <li><a class="dropdown-item py-2 text-white" href="/blockchain"><strong style="color: #8B5CF6;">MOJOVERSE</strong> — Enterprise Web3</a></li>
                            </ul>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/solutions">Solutions (ERP)</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/industries">Industries (Vision)</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/#innoria_topology_section">3D Topology</a>
                        </li>
                    </ul>
                    <div class="d-flex align-items-center gap-2">
                        <a href="/contactus" class="btn btn-innoria-nav d-inline-flex align-items-center gap-2">
                            <span>Tư Vấn 3 Giờ</span>
                            <svg class="ph-duotone ph-arrow-right" style="width: 1rem; height: 1rem;"><use href="/insilos_website/static/src/icons/phosphor-duotone.svg#ph-arrow-right"/></svg>
                        </a>
                    </div>
                </div>
            </div>
        </nav>
    </template>"""

FOOTER_XML = """    <template id="innoria_footer" name="INNORIA Footer">
        <footer class="innoria-footer mt-auto py-5" style="background-color: #0B111A; border-top: 1px solid rgba(255,255,255,0.08);">
            <style>
                .innoria-footer h6 { color: #FFFFFF !important; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; margin-bottom: 1rem !important; }
                .innoria-footer-link { color: #94A3B8 !important; text-decoration: none !important; transition: color 0.2s ease !important; }
                .innoria-footer-link:hover { color: #0ABBDB !important; text-decoration: underline !important; }
            </style>
            <div class="container">
                <div class="row g-4 mb-4">
                    <!-- Company Identity -->
                    <div class="col-lg-4">
                        <a href="/">
                            <img src="/insilos_website/static/src/img/innoria/innoria_logo_grayscale.svg" alt="INNORIA Logo" class="footer-logo mb-3" width="160" height="48"/>
                        </a>
                        <p class="small text-secondary mb-3">
                            The future technology needs a new vision, new motivation and new people. Set core values for each product using uniformed data, automated and intelligence business processes. Along with governance, risk and compliance.
                        </p>
                        <div class="small text-secondary font-monospace">
                            © 2026 INNORIA Solutions JSC · UNG DUNG SANG TAO LLC. All rights reserved.
                        </div>
                    </div>

                    <!-- Core Navigation -->
                    <div class="col-6 col-lg-2">
                        <h6 class="text-white fw-bold mb-3">PLATFORM</h6>
                        <ul class="list-unstyled small d-flex flex-column gap-2 mb-0">
                            <li><a href="/platform" class="innoria-footer-link">MOJO AI Platform</a></li>
                            <li><a href="/no-code-platform" class="innoria-footer-link">DIGIFORCE No-Code</a></li>
                            <li><a href="/blockchain" class="innoria-footer-link">MOJOVERSE Web3</a></li>
                            <li><a href="/solutions" class="innoria-footer-link">Intelligent ERP</a></li>
                            <li><a href="/#innoria_topology_section" class="innoria-footer-link">3D Topology Engine</a></li>
                        </ul>
                    </div>

                    <!-- Solutions -->
                    <div class="col-6 col-lg-3">
                        <h6 class="text-white fw-bold mb-3">SOLUTIONS</h6>
                        <ul class="list-unstyled small d-flex flex-column gap-2 mb-0">
                            <li><a href="/industries" class="innoria-footer-link">Ultra AI Vision Công Nghiệp</a></li>
                            <li><a href="/solutions" class="innoria-footer-link">Quản Trị ERP &amp; Hóa Đơn Tự Động</a></li>
                            <li><a href="/no-code-platform" class="innoria-footer-link">Permit to Work &amp; EHS Số</a></li>
                            <li><a href="/blockchain" class="innoria-footer-link">Chứng Nhận Xuất Xứ Số (e-CO)</a></li>
                            <li><a href="/about" class="innoria-footer-link">Văn Hóa &amp; Di Sản 18 Năm</a></li>
                        </ul>
                    </div>

                    <!-- Contact & Legal -->
                    <div class="col-lg-3">
                        <h6 class="text-white fw-bold mb-3">CONNECT</h6>
                        <div class="small text-secondary mb-2">
                            <strong class="text-white">UNG DUNG SANG TAO LLC</strong><br/>
                            Mã số DN (Tax ID): 0313683499
                        </div>
                        <div class="small text-secondary mb-2">
                            <svg class="ph-duotone ph-map-pin text-innoria-cyan me-1" style="width: 1rem; height: 1rem;"><use href="/insilos_website/static/src/icons/phosphor-duotone.svg#ph-map-pin"/></svg>
                            45 đường số 3, KDC Trung Sơn, Xã Bình Hưng, Huyện Bình Chánh, TP. Hồ Chí Minh
                        </div>
                        <div class="small text-secondary">
                            <svg class="ph-duotone ph-envelope text-innoria-cyan me-1" style="width: 1rem; height: 1rem;"><use href="/insilos_website/static/src/icons/phosphor-duotone.svg#ph-envelope"/></svg>
                            <a href="mailto:contact@innoria.com" class="text-innoria-cyan text-decoration-none">contact@innoria.com</a>
                        </div>
                    </div>
                </div>

                <!-- Bottom Bar -->
                <div class="border-top border-secondary border-opacity-20 pt-3 d-flex flex-column flex-md-row align-items-center justify-content-between small text-secondary">
                    <div>Bản quyền thuộc về INNORIA | Tailored Technology Solutions</div>
                    <div class="d-flex align-items-center gap-3 mt-2 mt-md-0">
                        <span class="badge bg-secondary bg-opacity-25 text-white">ISO 27001 // SOC-2</span>
                        <span class="badge bg-secondary bg-opacity-25 text-white">100% Air-Gapped Ready</span>
                    </div>
                </div>
            </div>
        </footer>
    </template>"""

def sanitize_template(xml_content, target_id, target_name):
    # Remove any markdown code fences
    xml_content = re.sub(r"^```(?:xml)?\s*", "", xml_content.strip())
    xml_content = re.sub(r"\s*```$", "", xml_content.strip())
    
    # Ensure starting <template> tag has correct id and name
    template_match = re.search(r"<template\b[^>]*>", xml_content)
    if template_match:
        old_tag = template_match.group(0)
        new_tag = f'<template id="{target_id}" name="{target_name}">'
        xml_content = xml_content.replace(old_tag, new_tag, 1)
    else:
        xml_content = f'<template id="{target_id}" name="{target_name}">\n{xml_content}\n</template>'
        
    # Replace stray unescaped ampersands
    xml_content = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', xml_content)
    return xml_content

def main():
    print("=== ASSEMBLING INNORIA ENTERPRISE PAGES ===")
    assembled_templates = []
    
    for filename, template_id, template_name in PAGES:
        filepath = os.path.join(FLEET_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[!] Error: File missing: {filepath}")
            return 1
        with open(filepath, "r", encoding="utf-8") as f:
            raw_xml = f.read()
        sanitized = sanitize_template(raw_xml, template_id, template_name)
        
        # Indent each line
        indented = "\n".join("    " + line if line.strip() else "" for line in sanitized.splitlines())
        assembled_templates.append(indented)
        print(f"[✓] Added {template_id} ({len(sanitized)} chars)")
        
    final_xml = '<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n'
    final_xml += "\n\n".join(assembled_templates)
    final_xml += "\n</odoo>\n"
    
    # Final global ampersand cleanup to be 100% sure
    final_xml = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', final_xml)
    
    # Validate well-formed XML
    try:
        ET.fromstring(final_xml)
        print("[✓] XML Structure validated successfully with ElementTree!")
    except ET.ParseError as e:
        print(f"[!] XML Validation Error: {e}")
        with open("/tmp/innoria_pages_debug.xml", "w", encoding="utf-8") as f:
            f.write(final_xml)
        print("Written debug XML to /tmp/innoria_pages_debug.xml")
        return 1
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_xml)
    print(f"[✓] Assembled all 7 pages + navbar + footer -> {OUTPUT_FILE} ({len(final_xml)} chars)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
