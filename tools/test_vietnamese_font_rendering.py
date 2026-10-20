#!/usr/bin/env python3
"""
tools/test_vietnamese_font_rendering.py
=======================================
Automated Pre-Application & Regression Gate for Vietnamese Font Rendering
and Hero Cinematic Overlay Brightness across Local & Production (innoria.com).

Checks:
1. WOFF2 Font Binary Integrity:
   - poppins-latin.woff2: size >= 40,000 bytes, MD5 == 260c81a4759baf163c025001c4f27872
     (rejects broken 7,884-byte static 400 Latin font).
   - poppins-vietnamese.woff2: size >= 9,000 bytes, MD5 == 9df17551da76cba6ee2d5d35fc762ed9
     (rejects broken 5,644-byte static Latin-Ext font missing U+1EA0-1EF9).
2. @font-face Cascade Priority & Non-Overlapping Unicode Range:
   - In website_templates.xml, poppins-vietnamese.woff2 MUST be declared AFTER
     poppins-latin.woff2 for both 'Poppins' and 'Inter'.
   - poppins-latin.woff2 unicode-range MUST NOT include U+0100-02BA (which shadows
     Vietnamese characters Ă, ă, Đ, đ, Ĩ, ĩ, Ũ, ũ, Ơ, ơ, Ư, ư).
   - poppins-vietnamese.woff2 unicode-range MUST cover U+0102-0103, U+0110-0111,
     U+01A0-01A1, U+01AF-01B0, and U+1EA0-1EF9.
3. Hero Dark Overlay Opacity & Poster Backdrop Guard:
   - In innoria_theme.scss, .hero-cinematic-mask center alpha <= 0.20 and edge alpha <= 0.60.
   - In innoria_hero_3d_manager.js, clearAlpha == 0.0 so WebGL canvas never occludes video/poster.
4. Live Headless Browser (Playwright) Glyph & Weight Rendering Gate:
   - Loads http://127.0.0.1:28069/ in headless Chromium, waits for document.fonts.ready,
     verifies all 134 Vietnamese diacritic characters render using 'Poppins' (zero fallback
     to system serif/monospace) across weights 400, 600, 700, 800.
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT_DIR / "enterprise/insilos_website/static/src/fonts"
TEMPLATES_XML = ROOT_DIR / "enterprise/insilos_website/views/website_templates.xml"
HERO_SCSS = ROOT_DIR / "enterprise/insilos_website/static/src/scss/innoria_theme.scss"
HERO_3D_JS = ROOT_DIR / "enterprise/insilos_website/static/src/js/innoria_hero_3d_manager.js"

EXPECTED_LATIN_MD5 = "260c81a4759baf163c025001c4f27872"
EXPECTED_VN_MD5 = "9df17551da76cba6ee2d5d35fc762ed9"

VN_DIACRITICS = (
    "ăâđêôơưĂÂĐÊÔƠƯ"
    "áàảãạấầẩẫậắằẳẵặ"
    "éèẻẽẹếềểễệ"
    "íìỉĩị"
    "óòỏõọốồổỗộớờởỡợ"
    "úùủũụứừửữự"
    "ýỳỷỹỵ"
    "ÁÀẢÃẠẤẦẨẪẬẮẰẲẴẶ"
    "ÉÈẺẼẸẾỀỂỄỆ"
    "ÍÌỈĨỊ"
    "ÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢ"
    "ÚÙỦŨỤỨỪỬỮỰ"
    "ÝỲỶỸỴ"
)


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def test_font_binaries():
    for prefix in ("poppins", "inter"):
        latin_path = FONTS_DIR / f"{prefix}-latin.woff2"
        vn_path = FONTS_DIR / f"{prefix}-vietnamese.woff2"

        assert latin_path.exists(), f"Missing {latin_path}"
        assert vn_path.exists(), f"Missing {vn_path}"

        latin_size = latin_path.stat().st_size
        vn_size = vn_path.stat().st_size
        latin_md5 = md5_file(latin_path)
        vn_md5 = md5_file(vn_path)

        assert latin_size >= 40000, f"{prefix}-latin.woff2 too small ({latin_size} B) - static/truncated font!"
        assert vn_size >= 9000, f"{prefix}-vietnamese.woff2 too small ({vn_size} B) - missing Vietnamese glyphs!"
        assert latin_md5 == EXPECTED_LATIN_MD5, f"{prefix}-latin.woff2 MD5 mismatch: {latin_md5}"
        assert vn_md5 == EXPECTED_VN_MD5, f"{prefix}-vietnamese.woff2 MD5 mismatch: {vn_md5}"
        print(f"[PASS] {prefix} binaries verified: latin={latin_size}B ({latin_md5[:8]}), vn={vn_size}B ({vn_md5[:8]})")


def test_font_face_cascade():
    xml_text = TEMPLATES_XML.read_text(encoding="utf-8")
    blocks = re.findall(r"@font-face\s*\{[^}]+\}", xml_text, re.DOTALL)
    assert len(blocks) >= 4, f"Expected >= 4 @font-face blocks in website_templates.xml, found {len(blocks)}"

    for family, prefix in (("'Poppins'", "poppins"), ("'Inter'", "inter")):
        fam_blocks = [b for b in blocks if f"font-family: {family}" in b]
        assert len(fam_blocks) == 2, f"Expected 2 @font-face blocks for {family}, found {len(fam_blocks)}"
        first_block, second_block = fam_blocks[0], fam_blocks[1]
        assert f"{prefix}-latin.woff2" in first_block, f"{family} first @font-face must be {prefix}-latin.woff2"
        assert f"{prefix}-vietnamese.woff2" in second_block, f"{family} second @font-face must be {prefix}-vietnamese.woff2"
        assert "U+0100-02BA" not in first_block, f"{family} latin unicode-range must not shadow U+0100-02BA!"
        for req_range in ("U+0102-0103", "U+0110-0111", "U+01A0-01A1", "U+01AF-01B0", "U+1EA0-1EF9"):
            assert req_range in second_block, f"{family} vietnamese @font-face missing {req_range}"

    print("[PASS] @font-face cascade priority & non-overlapping Vietnamese unicode-range verified.")


def test_hero_overlay_brightness():
    scss_text = HERO_SCSS.read_text(encoding="utf-8")
    m = re.search(r"\.hero-cinematic-mask\s*\{([^}]+)\}", scss_text, re.DOTALL)
    assert m, "Missing .hero-cinematic-mask in innoria_theme.scss"
    mask_body = m.group(1)
    alphas = [float(a) for a in re.findall(r"rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*([0-9.]+)\s*\)", mask_body)]
    assert alphas, "No rgba() stops found in .hero-cinematic-mask"
    min_alpha = min(alphas)
    max_alpha = max(alphas)
    assert min_alpha <= 0.20, f"Hero mask center alpha too dark ({min_alpha} > 0.20)"
    assert max_alpha <= 0.60, f"Hero mask edge alpha too dark ({max_alpha} > 0.60)"

    js_text = HERO_3D_JS.read_text(encoding="utf-8")
    assert "var clearAlpha = 0.0;" in js_text, "InnoriaHero3DManager must keep clearAlpha = 0.0 for transparent WebGL stage"
    print(f"[PASS] Hero dark overlay opacity verified (min_alpha={min_alpha}, max_alpha={max_alpha}, WebGL clearAlpha=0.0).")


def test_live_playwright_vietnamese_glyphs():
    node_script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1440, height: 900 }} }});
  await page.goto('http://127.0.0.1:28069/', {{ waitUntil: 'load', timeout: 30000 }});
  await page.evaluate(() => document.fonts.ready);

  const result = await page.evaluate((vnChars) => {{
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const weights = [400, 600, 700, 800];
    const fallbackFailures = [];
    const weightProgression = {{}};

    for (const w of weights) {{
      for (const ch of vnChars) {{
        ctx.font = `${{w}} 48px 'Poppins', monospace`;
        const wPoppins = ctx.measureText(ch).width;
        ctx.font = `${{w}} 48px monospace`;
        const wMono = ctx.measureText(ch).width;
        if (Math.abs(wPoppins - wMono) < 0.05) {{
          fallbackFailures.push({{ weight: w, char: ch, wPoppins, wMono }});
        }}
      }}
      ctx.font = `${{w}} 48px 'Poppins', sans-serif`;
      weightProgression[w] = ctx.measureText('Công Nghệ Cho Vận Hành Được Kiểm Soát & Tuân Thủ. Cụm Tác Nhân AI Đa Luồng').width;
    }}

    const h1 = document.querySelector('.hero-main-title');
    const mask = document.querySelector('.hero-cinematic-mask');
    const h1Font = h1 ? window.getComputedStyle(h1).fontFamily : '';
    const maskBg = mask ? window.getComputedStyle(mask).backgroundImage : '';

    return {{
      fallbackCount: fallbackFailures.length,
      fallbackSample: fallbackFailures.slice(0, 5),
      weightProgression,
      h1Font,
      maskBg
    }};
  }}, {repr(VN_DIACRITICS)});

  await browser.close();
  if (result.fallbackCount > 0) {{
    console.error('FAIL: Vietnamese glyph fallback detected:', JSON.stringify(result));
    process.exit(1);
  }}
  if (!(result.weightProgression[800] > result.weightProgression[400])) {{
    console.error('FAIL: Variable weight progression failed:', JSON.stringify(result.weightProgression));
    process.exit(1);
  }}
  console.log('[PASS] Live Playwright Vietnamese Glyph & Weight Check (134 chars x 4 weights):', JSON.stringify(result));
}})();
"""
    proc = subprocess.run(["node", "-e", node_script], cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise AssertionError("Playwright Vietnamese font rendering check failed")
    print(proc.stdout.strip())


if __name__ == "__main__":
    test_font_binaries()
    test_font_face_cascade()
    test_hero_overlay_brightness()
    test_live_playwright_vietnamese_glyphs()
    print("=== ALL VIETNAMESE FONT & HERO OVERLAY CHECKS PASSED (EXIT 0) ===")
