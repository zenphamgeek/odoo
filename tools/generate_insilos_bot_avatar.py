#!/usr/bin/env python3
"""
tools/generate_insilos_bot_avatar.py
Generates canonical Insilos Bot Avatar assets and related AI dialog icons:
- addons/mail/static/src/img/odoobot.png (512x512)
- addons/mail/static/src/img/odoobot_transparent.png (512x512)
- addons/mail/static/src/img/odoo_o.png (100x100)
- enterprise/ai_documents_source/static/img/icon.png (100x100)
- enterprise/ai_knowledge/static/img/icon.png (100x100)
"""

import os
import sys
import io
import cairosvg
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Canonical Insilos Bot Avatar SVG (With Insilos Gradient Background)
SVG_ODOOBOT_BG = '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="insilos_grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#004455"/>
      <stop offset="50%" stop-color="#06395c"/>
      <stop offset="100%" stop-color="#0B2E64"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#0096B3" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#004455" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <!-- Background with subtle corner radius or full bleed for circular crop -->
  <rect width="512" height="512" fill="url(#insilos_grad)"/>
  <circle cx="256" cy="256" r="240" fill="url(#glow)"/>
  <!-- Bot Group centered & scaled for circle crop safety -->
  <g transform="translate(77, 86) scale(1.4)">
    <!-- Solid white head backing so face is bright, friendly, high contrast -->
    <rect x="32" y="80" width="192" height="112" rx="16" fill="#FFFFFF"/>
    <!-- Ears backing -->
    <rect x="24" y="104" width="8" height="64" rx="4" fill="#FFFFFF"/>
    <rect x="224" y="104" width="8" height="64" rx="4" fill="#FFFFFF"/>
    <!-- Inner face screen duotone tint -->
    <path d="M200,56H56A24,24,0,0,0,32,80V192a24,24,0,0,0,24,24H200a24,24,0,0,0,24-24V80A24,24,0,0,0,200,56ZM164,184H92a20,20,0,0,1,0-40h72a20,20,0,0,1,0,40Z" fill="#00BCD4" opacity="0.25"/>
    <!-- Antenna stem -->
    <rect x="120" y="16" width="16" height="32" rx="8" fill="#FFFFFF"/>
    <!-- Robot head, outline, eyes sockets, mouth grille -->
    <path d="M200,48H136V16a8,8,0,0,0-16,0V48H56A32,32,0,0,0,24,80V192a32,32,0,0,0,32,32H200a32,32,0,0,0,32-32V80A32,32,0,0,0,200,48Zm16,144a16,16,0,0,1-16,16H56a16,16,0,0,1-16-16V80A16,16,0,0,1,56,64H200a16,16,0,0,1,16,16ZM72,108a12,12,0,1,1,12,12A12,12,0,0,1,72,108Zm88,0a12,12,0,1,1,12,12A12,12,0,0,1,160,108Zm4,28H92a28,28,0,0,0,0,56h72a28,28,0,0,0,0-56Zm-24,16v24H116V152ZM80,164a12,12,0,0,1,12-12h8v24H92A12,12,0,0,1,80,164Zm84,12h-8V152h8a12,12,0,0,1,0,24Z" fill="#0B2E64"/>
    <!-- Glowing Insilos Amber eyes -->
    <circle cx="84" cy="120" r="7" fill="#FF8000"/>
    <circle cx="172" cy="120" r="7" fill="#FF8000"/>
    <!-- Antenna beacon -->
    <circle cx="128" cy="16" r="6" fill="#FF8000"/>
  </g>
</svg>'''

# Canonical Insilos Bot Avatar SVG (Transparent Background for Desktop Notifications)
SVG_ODOOBOT_TRANSPARENT = '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <!-- Bot Group centered & scaled -->
  <g transform="translate(77, 86) scale(1.4)">
    <!-- Inner face screen duotone layer -->
    <path d="M200,56H56A24,24,0,0,0,32,80V192a24,24,0,0,0,24,24H200a24,24,0,0,0,24-24V80A24,24,0,0,0,200,56ZM164,184H92a20,20,0,0,1,0-40h72a20,20,0,0,1,0,40Z" fill="#004455" opacity="0.2"/>
    <!-- Robot head, outline, eyes sockets, mouth grille -->
    <path d="M200,48H136V16a8,8,0,0,0-16,0V48H56A32,32,0,0,0,24,80V192a32,32,0,0,0,32,32H200a32,32,0,0,0,32-32V80A32,32,0,0,0,200,48Zm16,144a16,16,0,0,1-16,16H56a16,16,0,0,1-16-16V80A16,16,0,0,1,56,64H200a16,16,0,0,1,16,16ZM72,108a12,12,0,1,1,12,12A12,12,0,0,1,72,108Zm88,0a12,12,0,1,1,12,12A12,12,0,0,1,160,108Zm4,28H92a28,28,0,0,0,0,56h72a28,28,0,0,0,0-56Zm-24,16v24H116V152ZM80,164a12,12,0,0,1,12-12h8v24H92A12,12,0,0,1,80,164Zm84,12h-8V152h8a12,12,0,0,1,0,24Z" fill="#004455"/>
    <!-- Glowing Insilos Amber eyes -->
    <circle cx="84" cy="120" r="7" fill="#FF8000"/>
    <circle cx="172" cy="120" r="7" fill="#FF8000"/>
    <!-- Antenna beacon -->
    <circle cx="128" cy="16" r="6" fill="#FF8000"/>
  </g>
</svg>'''


def render_svg_to_png(svg_str, out_path, width, height):
    """Render an SVG string to PNG at exact dimensions."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    png_bytes = cairosvg.svg2png(bytestring=svg_str.encode('utf-8'), output_width=width, output_height=height)
    with open(out_path, 'wb') as f:
        f.write(png_bytes)
    print(f"  [OK] Generated {out_path} ({width}x{height}, {len(png_bytes)} bytes)")


def generate_source_dialog_icon(glyph_name, out_path, size=100):
    """Generate a clean Phosphor duotone icon for AI source dialogs."""
    src_svg = os.path.join(REPO_ROOT, 'tools', 'phosphor_duotone', f"{glyph_name}-duotone.svg")
    if not os.path.exists(src_svg):
        src_svg = os.path.join(REPO_ROOT, 'branding', 'phosphor', 'assets', 'duotone', f"{glyph_name}-duotone.svg")
    
    with open(src_svg, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Compile with #0B2E64
    if 'fill="currentColor"' in svg_content:
        svg_content = svg_content.replace('fill="currentColor"', 'fill="#0B2E64"')
    elif 'fill=' not in svg_content[:svg_content.find('>')]:
        svg_content = svg_content.replace('<svg ', '<svg fill="#0B2E64" ')

    if 'opacity="0.2"' not in svg_content:
        svg_content = svg_content.replace('<path ', '<path opacity="0.2" ', 1)

    render_svg_to_png(svg_content, out_path, size, size)


def main():
    print("=== Generating Canonical Insilos Bot Avatars & Dialog Assets ===")

    # 1. odoobot.png (512x512)
    odoobot_png = os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'src', 'img', 'odoobot.png')
    render_svg_to_png(SVG_ODOOBOT_BG, odoobot_png, 512, 512)

    # 2. odoobot_transparent.png (512x512)
    odoobot_trans = os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'src', 'img', 'odoobot_transparent.png')
    render_svg_to_png(SVG_ODOOBOT_TRANSPARENT, odoobot_trans, 512, 512)

    # 3. odoo_o.png (100x100) from branding/icon-dark.svg
    icon_dark_svg = os.path.join(REPO_ROOT, 'branding', 'icon-dark.svg')
    if os.path.exists(icon_dark_svg):
        with open(icon_dark_svg, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        odoo_o_png = os.path.join(REPO_ROOT, 'addons', 'mail', 'static', 'src', 'img', 'odoo_o.png')
        render_svg_to_png(svg_content, odoo_o_png, 100, 100)

    # 4. enterprise/ai_documents_source/static/img/icon.png (100x100 folder-open)
    doc_source_png = os.path.join(REPO_ROOT, 'enterprise', 'ai_documents_source', 'static', 'img', 'icon.png')
    if os.path.exists(os.path.dirname(doc_source_png)):
        generate_source_dialog_icon('folder-open', doc_source_png, 100)

    # 5. enterprise/ai_knowledge/static/img/icon.png (100x100 book-bookmark)
    know_source_png = os.path.join(REPO_ROOT, 'enterprise', 'ai_knowledge', 'static', 'img', 'icon.png')
    if os.path.exists(os.path.dirname(know_source_png)):
        generate_source_dialog_icon('book-bookmark', know_source_png, 100)

    print("=== All Bot & AI Dialog Assets Generated Successfully ===")


if __name__ == '__main__':
    main()
