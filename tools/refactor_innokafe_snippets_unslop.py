#!/usr/bin/env python3
"""
Refactor and Un-Slop enterprise/innokafe_website/views/snippets.xml.
Purges harsh border-warning, boxed-in-box nesting, AI jargon, and broken glyphs.
Replaces with .inno-craft-card, .inno-hero-vignette, authentic photography,
inline SVG stars, and grounded Vietnamese specialty coffee storytelling.
Validates XML integrity with xml.etree.ElementTree before writing.
"""

import re
import xml.etree.ElementTree as ET

SNIPPETS_PATH = "enterprise/innokafe_website/views/snippets.xml"

def perform_unslop():
    with open(SNIPPETS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Clean up generic card borders in snippets
    content = content.replace(
        'class="card bg-black bg-opacity-60 border border-warning border-opacity-30 rounded-4 p-4 text-white"',
        'class="inno-craft-card rounded-4 p-4 text-white"'
    )
    content = content.replace(
        'class="card h-100 bg-black bg-opacity-50 border border-warning border-opacity-30 rounded-4 p-4 text-white"',
        'class="inno-craft-card h-100 rounded-4 p-4 text-white"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-60 border border-warning border-opacity-25 rounded-4 p-4 p-md-5 text-white h-100 shadow-lg"',
        'class="inno-craft-card rounded-4 p-4 p-md-5 text-white h-100 shadow-lg"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-60 border border-warning border-opacity-30 rounded-4 p-4 p-md-5 text-white h-100 position-relative overflow-hidden inno-terroir-card"',
        'class="inno-craft-card rounded-4 p-4 p-md-5 text-white h-100 position-relative overflow-hidden inno-terroir-card"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-60 border border-warning border-opacity-30 rounded-4 p-4 text-white shadow-lg inno-roast-transparency-card"',
        'class="inno-craft-card rounded-4 p-4 text-white shadow-lg inno-roast-transparency-card"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-70 border border-warning border-opacity-30 rounded-4 p-4 p-md-5 text-white shadow-lg inno-roast-telemetry-container"',
        'class="inno-craft-card rounded-4 p-4 p-md-5 text-white shadow-lg inno-roast-telemetry-container"'
    )
    content = content.replace(
        'class="position-relative rounded-4 overflow-hidden shadow-lg border border-warning border-opacity-30 mb-4 bg-black"',
        'class="inno-hero-vignette position-relative rounded-4 overflow-hidden shadow-lg mb-4"'
    )

    # 2. Purge border-warning from subscription cards and indicators
    content = content.replace('border border-warning border-opacity-25 bg-black bg-opacity-40', 'border border-secondary border-opacity-25 bg-black bg-opacity-30')
    content = content.replace('border-start border-4 border-warning', 'border-start border-3 border-warning')
    content = content.replace('inno-step-indicator active p-3 rounded-3 border border-warning bg-dark', 'inno-step-indicator active p-3 rounded-3 border border-secondary border-opacity-40 bg-dark')
    content = content.replace('badge bg-dark border border-warning text-warning', 'badge bg-dark text-warning border border-secondary border-opacity-40')
    content = content.replace('inno-choice-card d-block p-4 rounded-4 border border-warning bg-black bg-opacity-50', 'inno-choice-card d-block p-4 rounded-4 inno-craft-card')
    content = content.replace('inno-tier-box d-block p-3 rounded-3 border border-warning bg-black', 'inno-tier-box d-block p-3 rounded-3 inno-craft-card')
    content = content.replace('p-4 rounded-4 bg-black border border-warning border-opacity-40', 'p-4 rounded-4 inno-craft-card')
    content = content.replace('p-4 rounded-4 bg-black border-2 border-warning', 'p-4 rounded-4 inno-craft-card')
    content = content.replace('bg-black border border-warning cursor-pointer', 'inno-craft-card cursor-pointer')
    content = content.replace('badge bg-warning bg-opacity-20 text-warning border border-warning border-opacity-50', 'badge bg-warning bg-opacity-20 text-warning border border-warning border-opacity-30')

    # 3. Clean up generic buzzwords
    content = content.replace('Chúng tôi đánh thức vị giác bằng hạt cà phê đặc sản tuyển chọn từ', 'Từng hạt cà phê đặc sản được thu hái thủ công từ vùng đất đỏ')
    content = content.replace('Khám phá 5 phương thức chiết xuất đỉnh cao được hiệu chuẩn', 'Khám phá 5 phương thức chiết xuất thủ công được hiệu chuẩn')
    content = content.replace('Thợ rang bậc thầy (Master Roaster)', 'Kỹ sư rang mộc (Roaster)')

    # 4. Refactor Hero Story Right Column Vignette in s_innokafe_hero_story
    old_hero_right_col = re.search(r'(<!-- Snippet 1: Innokafe Hero Story -->.*?<div class="col-lg-4">)(.*?)(</div>\s+</div>\s+</div>\s+</section>)', content, re.DOTALL)
    if old_hero_right_col:
        new_vignette = """
                        <div class="inno-hero-vignette p-2">
                            <div class="position-relative rounded-4 overflow-hidden" style="aspect-ratio: 4 / 3;">
                                <img src="/innokafe_website/static/src/img/photography/sensory_cupping_flight.webp" alt="Thử nếm hạt cà phê đặc sản InnoKafe" class="w-100 h-100 object-fit-cover"/>
                                <div class="position-absolute top-0 start-0 w-100 h-100" style="background: linear-gradient(180deg, rgba(20, 12, 7, 0.15) 30%, rgba(20, 12, 7, 0.95) 100%);"/>
                                <div class="position-absolute bottom-0 start-0 p-4 text-white w-100">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="badge bg-warning text-dark font-monospace fw-bold">FINE ROBUSTA NATURAL</span>
                                        <span class="text-secondary small font-monospace">CƯ M'GAR · 750M</span>
                                    </div>
                                    <h3 class="h5 fw-bold text-white mb-2">Đắk Lắk Highland Natural</h3>
                                    <div class="inno-stars mb-2">
                                        <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                        <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                        <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                        <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                        <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                        <span class="star-score">84.50 SCA</span>
                                    </div>
                                    <p class="text-secondary small mb-3">
                                        Sô-cô-la đen 85%, hạt dẻ nướng và hậu vị mật mía ngọt sâu.
                                    </p>
                                    <div class="d-flex justify-content-between align-items-center pt-2 border-top border-secondary border-opacity-25">
                                        <span class="text-white fw-bold">125.000 đ / 250g</span>
                                        <a href="/products" class="btn btn-sm btn-primary rounded-pill px-3 py-1">Khám Phá</a>
                                    </div>
                                </div>
                            </div>
                        </div>"""
        prefix = old_hero_right_col.group(1)
        suffix = old_hero_right_col.group(3)
        content = content[:old_hero_right_col.start()] + prefix + new_vignette + "\n                    " + suffix + content[old_hero_right_col.end():]

    # 5. Fix star ratings in testimonials
    star_svg_block = """<div class="inno-stars mb-2">
                                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                            </div>"""

    # Replace FontAwesome star groups if any
    content = re.sub(r'<div class="[^"]*star[^"]*">.*?<i class="fa fa-star"[^>]*>.*?</div>', star_svg_block, content, flags=re.DOTALL)

    # 6. Validate XML before writing
    try:
        ET.fromstring(content)
        print("[✓] XML parsed cleanly with ElementTree!")
    except ET.ParseError as err:
        print(f"[!] XML Validation Error: {err}")
        return False

    with open(SNIPPETS_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Successfully wrote un-slopped snippets to {SNIPPETS_PATH}")
    return True

if __name__ == "__main__":
    success = perform_unslop()
    if not success:
        exit(1)
