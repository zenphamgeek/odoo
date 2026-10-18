#!/usr/bin/env python3
"""
tools/fleet_ibm_carbon_poppins_overhaul.py
=============================================================================
Patch 41 — IBM Carbon Design System v11 & Poppins Sans-Serif Typography Overhaul:
1. Purges mechanical/robotic monospace fonts (`font-monospace`, `JetBrains Mono`,
   `Fira Code`, `Roboto Mono`, `monospace`, `Inter`) across all 22 Website,
   Portal, and AI Concierge XML views and 11 SCSS stylesheets, replacing them
   with `'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`.
2. Enforces IBM Carbon v11 tokens (`#0f62fe` Blue 60, `#0043ce` Blue 70,
   `#161616` Gray 100, `#262626` Gray 90, `#f4f4f4` Gray 10, `#ffffff` White,
   `#e0e0e0` Gray 20, `#393939` Gray 80) and purges AI-slop neon borders,
   glowing box-shadows, rainbow text gradients, and bubbly pill/rounded-4/5 radii.
=============================================================================
"""

import glob
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.safe_xml import parse_xml_safe

POPPINS_FONT_STACK = (
    "'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
)

CARBON_MASTER_SCSS_MARKER = "/* === PATCH 41: IBM CARBON V11 & POPPINS SANS-SERIF MASTER ARCHITECTURE === */"

CARBON_PUBLIC_SCSS_BLOCK = """
/* === PATCH 41: IBM CARBON V11 & POPPINS SANS-SERIF MASTER ARCHITECTURE === */
:root {
    --cds-font-sans: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --cds-font-mono: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --bs-body-font-family: var(--cds-font-sans);
    --bs-font-sans-serif: var(--cds-font-sans);
    --bs-font-monospace: var(--cds-font-sans);
    --ins-font-sans: var(--cds-font-sans);
    --ins-font-display: var(--cds-font-sans);
    --ins-font-mono: var(--cds-font-sans);

    /* IBM Carbon v11 Interactive & Brand Tokens */
    --cds-interactive: #0f62fe;
    --cds-button-primary: #0f62fe;
    --cds-button-primary-hover: #0043ce;
    --cds-button-primary-active: #002d9c;
    --cds-focus: #0f62fe;
    --cds-link-primary: #0f62fe;
    --cds-link-primary-hover: #0043ce;
    --cds-link-dark: #78a9ff;

    /* IBM Carbon v11 White / Gray 10 Light Layering */
    --cds-background: #ffffff;
    --cds-layer-01: #f4f4f4;
    --cds-layer-02: #ffffff;
    --cds-layer-hover-01: #e8e8e8;
    --cds-border-subtle-01: #e0e0e0;
    --cds-border-strong-01: #8d8d8d;
    --cds-text-primary: #161616;
    --cds-text-secondary: #525252;
    --cds-text-helper: #6f6f6f;

    /* IBM Carbon v11 Gray 100 / Gray 90 Dark Layering */
    --cds-bg-dark: #161616;
    --cds-layer-dark-01: #262626;
    --cds-layer-dark-02: #393939;
    --cds-border-dark-subtle: #393939;
    --cds-border-dark-strong: #6f6f6f;
    --cds-text-dark-primary: #f4f4f4;
    --cds-text-dark-secondary: #c6c6c6;

    /* Remap Legacy Neon & AI-Slop Tokens to IBM Carbon v11 */
    --ins-primary: #0f62fe;
    --ins-orange: #0f62fe;
    --ins-orange-hover: #0043ce;
    --ins-orange-dark: #002d9c;
    --ins-orange-glow: transparent;
    --ins-cyan: #0f62fe;
    --ins-cyan-glow: transparent;
    --ins-mint: #007d79;
    --ins-emerald: #198038;
    --ins-violet: #0f62fe;
    --innoria-cyan: #0f62fe;
    --innoria-cyan-glow: transparent;
    --innoria-blue-primary: #0f62fe;
    --innoria-blue-dark: #0043ce;
    --innoria-blue-deep: #002d9c;
    --innoria-orange: #0f62fe;
    --innoria-orange-glow: transparent;
    --innoria-border-subtle: #e0e0e0;
    --innoria-text-primary: #161616;
    --innoria-text-secondary: #525252;
    --innoria-text-muted: #6f6f6f;
}

/* 1. Universal Poppins Sans-Serif Typography (Zero Mechanical Monospace) */
html, body, #wrapwrap,
.innoria-navbar, .innoria-footer,
.o_portal_wrap, .ai-concierge-drawer {
    font-family: var(--cds-font-sans) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;

    h1, h2, h3, h4, h5, h6,
    .h1, .h2, .h3, .h4, .h5, .h6,
    .display-1, .display-2, .display-3, .display-4, .display-5, .display-6,
    p, span, a, button, input, select, textarea, label, li, th, td,
    .font-monospace, .cds-font-sans, [class*="mono"], code, kbd, samp, pre {
        font-family: var(--cds-font-sans) !important;
        font-variant-numeric: tabular-nums;
    }
}

/* 2. IBM Carbon v11 Tile Architecture — Purge AI-Slop Borders, Pill Radii & Neon Glows */
#wrapwrap {
    .card,
    .bento-card,
    .ins-card,
    .inn-card,
    .feature-card,
    .solution-card,
    .c3-card,
    .ins-glass-card,
    .ins-spatial-layer,
    .ins-floating-pod,
    .inno-spatial-layer,
    .inno-floating-pod,
    .mojo-card,
    .df-card {
        border-radius: 2px !important;
        box-shadow: none !important;
        border: 1px solid var(--cds-border-subtle-01) !important;
        transition: border-color 150ms cubic-bezier(0.2, 0, 0.38, 0.9),
                    background-color 150ms cubic-bezier(0.2, 0, 0.38, 0.9) !important;

        &:hover, &:focus-within {
            border-color: var(--cds-interactive) !important;
            box-shadow: none !important;
            transform: none !important;
        }
    }

    [data-bs-theme="dark"], .bg-dark, .o_cc5, #innoria_hero_cover, .mojo-hero-section {
        .card,
        .bento-card,
        .ins-card,
        .inn-card,
        .feature-card,
        .solution-card,
        .c3-card,
        .ins-glass-card,
        .ins-spatial-layer,
        .ins-floating-pod {
            border-color: var(--cds-border-dark-subtle) !important;
            box-shadow: none !important;

            &:hover, &:focus-within {
                border-color: var(--cds-link-dark) !important;
                box-shadow: none !important;
            }
        }
    }

    /* 3. IBM Carbon v11 Rectangular Buttons — Zero Pill Radii, Zero Gradients */
    .btn,
    .btn-primary,
    .btn-secondary,
    .btn-outline-light,
    .btn-outline-secondary,
    .btn-outline-primary,
    .ins-btn-lux,
    .btn-innoria-nav {
        border-radius: 0px !important;
        box-shadow: none !important;
        font-family: var(--cds-font-sans) !important;
        font-weight: 500 !important;
        letter-spacing: 0.16px !important;
        background-image: none !important;
        transition: background-color 110ms cubic-bezier(0.2, 0, 0.38, 0.9),
                    border-color 110ms cubic-bezier(0.2, 0, 0.38, 0.9),
                    color 110ms cubic-bezier(0.2, 0, 0.38, 0.9) !important;

        &:focus-visible {
            outline: 2px solid var(--cds-focus) !important;
            outline-offset: -2px !important;
            box-shadow: inset 0 0 0 1px #ffffff !important;
        }
    }

    .btn-primary,
    .ins-btn-lux,
    .btn-innoria-nav {
        background: var(--cds-button-primary) !important;
        background-color: var(--cds-button-primary) !important;
        border: 1px solid var(--cds-button-primary) !important;
        color: #ffffff !important;

        &:hover {
            background: var(--cds-button-primary-hover) !important;
            background-color: var(--cds-button-primary-hover) !important;
            border-color: var(--cds-button-primary-hover) !important;
            color: #ffffff !important;
            transform: none !important;
        }

        &:active {
            background: var(--cds-button-primary-active) !important;
            background-color: var(--cds-button-primary-active) !important;
            border-color: var(--cds-button-primary-active) !important;
        }
    }

    /* 4. IBM Carbon v11 Tags / Badges — Clean 4px Radius & Solid Semantic Fills */
    .badge,
    .chip,
    .ins-tag,
    .ins-pill-badge,
    .ins-status-chip,
    .badge-innoria-cyan,
    .badge-innoria-blue,
    .badge-innoria-orange {
        border-radius: 4px !important;
        box-shadow: none !important;
        font-family: var(--cds-font-sans) !important;
        font-weight: 500 !important;
        letter-spacing: 0.32px !important;
    }

    /* 5. Purge AI-Slop Rainbow Gradient Headlines */
    .ins-gradient-headline,
    .text-gradient,
    .text-innoria-gradient,
    .text-innoria-gradient-orange {
        background: none !important;
        background-image: none !important;
        -webkit-background-clip: unset !important;
        background-clip: unset !important;
        -webkit-text-fill-color: currentColor !important;
        color: var(--cds-interactive) !important;
    }

    [data-bs-theme="dark"], .bg-dark, .o_cc5, #innoria_hero_cover {
        .ins-gradient-headline,
        .text-gradient,
        .text-innoria-gradient,
        .text-innoria-gradient-orange {
            color: var(--cds-link-dark) !important;
        }
    }
}
"""


def _clean_class_value(prefix: str, val: str, quote: str) -> str:
    tokens = val.split()
    new_tokens = []
    for t in tokens:
        if t == "font-monospace":
            continue
        if t in ("rounded-4", "rounded-5", "rounded-pill"):
            new_tokens.append("rounded-1")
        elif t in ("border-info", "border-warning", "border-cyan"):
            new_tokens.append("border-secondary")
        else:
            new_tokens.append(t)
    if not new_tokens and "font-monospace" in tokens:
        new_tokens = ["cds-font-sans"]
    return f"{prefix}{' '.join(new_tokens)}{quote}"


def transform_xml_file(filepath: Path) -> int:
    orig = filepath.read_text(encoding="utf-8")
    text = orig
    mono_hits = len(
        re.findall(r"font-monospace|JetBrains Mono|Fira Code|Roboto Mono|monospace", text, re.IGNORECASE)
    )

    text = re.sub(
        r'(\b(?:t-attf-)?class=(["\']))([^"\']*)\2',
        lambda m: _clean_class_value(m.group(1), m.group(3), m.group(2)),
        text,
    )
    text = re.sub(r"\bfont-monospace\b", "cds-font-sans", text)
    text = re.sub(r"'?JetBrains Mono'?(?:,\s*monospace)?", POPPINS_FONT_STACK, text, flags=re.IGNORECASE)
    text = re.sub(r"'?Fira Code'?(?:,\s*monospace)?", POPPINS_FONT_STACK, text, flags=re.IGNORECASE)
    text = re.sub(r"'?Roboto Mono'?(?:,\s*monospace)?", POPPINS_FONT_STACK, text, flags=re.IGNORECASE)
    text = re.sub(r"'Inter'(?=\s*,)", "'Poppins'", text)
    text = re.sub(
        r"font-family:\s*[^;\"']*\bmonospace\b",
        f"font-family: {POPPINS_FONT_STACK}",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"--bs-font-monospace", "--cds-font-sans", text)
    text = re.sub(r"\bmonospace\b", "sans-serif", text)

    # Purge inline AI-slop box-shadows, bubbly border-radius, rainbow text-fill, and neon borders
    text = re.sub(r"box-shadow:\s*[^;\"']+", "box-shadow: none", text)
    text = re.sub(
        r"border-radius:\s*(?:1[0-9]|2[0-9]|3[0-9]|4[0-9]|50|9999)px",
        "border-radius: 2px",
        text,
    )
    text = re.sub(r"border-radius:\s*[1-9](?:\.\d+)?rem", "border-radius: 2px", text)
    text = re.sub(r"-webkit-text-fill-color:\s*transparent", "-webkit-text-fill-color: currentColor", text)
    text = re.sub(r"-webkit-background-clip:\s*text", "-webkit-background-clip: unset", text)
    text = re.sub(r"background:\s*radial-gradient\([^;\"']+\)", "background: transparent", text)
    text = re.sub(
        r"background(?:-image)?:\s*linear-gradient\(135deg,\s*#(?:0284C7|0369A1|0ABBDB|FF8000|EA580C)[^;\"']+\)",
        "background: #0f62fe",
        text,
        flags=re.IGNORECASE,
    )

    if text != orig:
        parse_xml_safe(text.encode("utf-8"))
        filepath.write_text(text, encoding="utf-8")
    return mono_hits


def transform_scss_file(filepath: Path, is_backend_addon: bool = False) -> int:
    orig = filepath.read_text(encoding="utf-8")
    text = orig
    hits = len(
        re.findall(r"JetBrains Mono|Fira Code|Roboto Mono|SFMono-Regular|monospace|'Inter'", text, re.IGNORECASE)
    )

    text = re.sub(
        r"font-family:\s*[^;{}]*(?:JetBrains Mono|Fira Code|Roboto Mono|SFMono-Regular|Consolas|Liberation Mono|Courier New|monospace|'Inter'|\"Inter\")[^;{}]*;",
        f"font-family: {POPPINS_FONT_STACK};",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(--(?:bs-body-font-family|bs-font-sans-serif|bs-font-monospace|ins-font-sans|ins-font-display|ins-font-mono|concierge-font-sans|concierge-font-mono)\s*:\s*)[^;]+;",
        rf"\1{POPPINS_FONT_STACK};",
        text,
    )
    text = re.sub(r"'JetBrains Mono'|\"JetBrains Mono\"", "'Poppins'", text, flags=re.IGNORECASE)
    text = re.sub(r"'Inter'|\"Inter\"", "'Poppins'", text)

    if not is_backend_addon and filepath.name in ("insilos.scss", "innoria_theme.scss", "insilos_liquid_spatial.scss"):
        if CARBON_MASTER_SCSS_MARKER not in text:
            text = text.rstrip() + "\n\n" + CARBON_PUBLIC_SCSS_BLOCK.strip() + "\n"

    if text != orig:
        filepath.write_text(text, encoding="utf-8")
    return hits


def main() -> int:
    xml_files = sorted(glob.glob(str(ROOT_DIR / "enterprise/insilos_website/views/*.xml")))
    xml_files += [
        str(ROOT_DIR / "enterprise/insilos_industry_showcase/views/templates.xml"),
        str(ROOT_DIR / "addons/insilos_al2c/views/portal_templates.xml"),
        str(ROOT_DIR / "addons/insilos_al2c/static/src/xml/ai_concierge_widget.xml"),
    ]

    total_xml_hits = 0
    for xf in xml_files:
        p = Path(xf)
        if p.exists():
            h = transform_xml_file(p)
            total_xml_hits += h
            print(f"[✓] XML Carbon/Poppins overhaul: {p.relative_to(ROOT_DIR)} (purged {h} robotic font refs)")

    pub_scss = sorted(glob.glob(str(ROOT_DIR / "enterprise/insilos_website/static/src/scss/*.scss")))
    for sf in pub_scss:
        p = Path(sf)
        if p.name == "odoo_ui_icons_patch.scss":
            continue
        h = transform_scss_file(p, is_backend_addon=False)
        print(f"[✓] Public SCSS Carbon/Poppins overhaul: {p.relative_to(ROOT_DIR)} (purged {h} font refs)")

    al2c_scss = sorted(glob.glob(str(ROOT_DIR / "addons/insilos_al2c/static/src/scss/*.scss")))
    for sf in al2c_scss:
        p = Path(sf)
        h = transform_scss_file(p, is_backend_addon=True)
        print(f"[✓] Addon SCSS Carbon/Poppins overhaul: {p.relative_to(ROOT_DIR)} (purged {h} font refs)")

    print(f"\n[🎉] Completed IBM Carbon v11 & Poppins Overhaul (Total XML robotic font refs purged: {total_xml_hits})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
