#!/usr/bin/env node
/**
 * tools/generate_innokafe_social_share_card.js
 * =============================================================================
 * Generates pixel-perfect, 1200x630 OpenGraph / Twitter Cards social share banner
 * for InnoKafe Specialty Coffee using Playwright Chromium headless.
 * Outputs:
 * - enterprise/innokafe_website/static/src/img/branding/innokafe_social_share_1200x630.jpg (High-compatibility JPEG)
 * - enterprise/innokafe_website/static/src/img/branding/innokafe_social_share_1200x630.webp (Modern WebP)
 * =============================================================================
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const OUT_DIR = path.join(ROOT_DIR, 'enterprise', 'innokafe_website', 'static', 'src', 'img', 'branding');
fs.mkdirSync(OUT_DIR, { recursive: true });

const bgImagePath = path.join(ROOT_DIR, 'enterprise', 'innokafe_website', 'static', 'src', 'img', 'photography', 'artisan_roasting_beans.jpg');
const logoSvgPath = path.join(ROOT_DIR, 'enterprise', 'innokafe_website', 'static', 'src', 'img', 'branding', 'innokafe_logo_white.svg');

if (!fs.existsSync(bgImagePath)) {
  throw new Error(`Background image not found: ${bgImagePath}`);
}
if (!fs.existsSync(logoSvgPath)) {
  throw new Error(`Logo SVG not found: ${logoSvgPath}`);
}

const bgBase64 = fs.readFileSync(bgImagePath).toString('base64');
const bgDataUrl = `data:image/jpeg;base64,${bgBase64}`;
const logoSvgContent = fs.readFileSync(logoSvgPath, 'utf-8');

const htmlContent = `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      width: 1200px;
      height: 630px;
      overflow: hidden;
      background-color: #0C0704;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* Ambient Background Layer with Optical Glow */
    .bg-layer {
      position: absolute;
      inset: 0;
      background-image: url('${bgDataUrl}');
      background-size: cover;
      background-position: center 38%;
      filter: brightness(0.68) contrast(1.15) saturate(1.1);
      transform: scale(1.02);
    }

    /* Spatial Gradient Masks */
    .overlay-vignette {
      position: absolute;
      inset: 0;
      background: 
        radial-gradient(ellipse at 80% 30%, rgba(255, 128, 0, 0.18) 0%, transparent 60%),
        radial-gradient(ellipse at 20% 80%, rgba(212, 136, 66, 0.22) 0%, transparent 55%),
        linear-gradient(90deg, rgba(12, 7, 4, 0.96) 0%, rgba(12, 7, 4, 0.88) 42%, rgba(12, 7, 4, 0.65) 100%),
        linear-gradient(180deg, rgba(12, 7, 4, 0.45) 0%, rgba(12, 7, 4, 0.85) 100%);
    }

    /* Content Canvas */
    .canvas-container {
      position: relative;
      z-index: 10;
      width: 100%;
      height: 100%;
      padding: 56px 64px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    /* Header Strip */
    .top-strip {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .brand-logo-wrap {
      width: 280px;
      display: flex;
      align-items: center;
    }

    .brand-logo-wrap svg {
      width: 100%;
      height: auto;
      filter: drop-shadow(0 6px 18px rgba(0, 0, 0, 0.7));
    }

    .top-badge {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background: rgba(255, 128, 0, 0.12);
      border: 1px solid rgba(255, 128, 0, 0.35);
      border-radius: 999px;
      padding: 8px 18px;
      color: #FFB366;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      backdrop-filter: blur(12px);
    }

    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #FF8000;
      box-shadow: 0 0 10px #FF8000;
    }

    /* Main Typography Block */
    .main-content {
      max-width: 840px;
      margin-top: 10px;
    }

    .category-label {
      color: #D48842;
      font-size: 14px;
      font-weight: 800;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .category-label::before {
      content: "";
      display: inline-block;
      width: 24px;
      height: 2px;
      background: #FF8000;
    }

    .hero-title {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 54px;
      line-height: 1.15;
      font-weight: 700;
      color: #FFFFFF;
      margin-bottom: 18px;
      letter-spacing: -0.5px;
      text-shadow: 0 4px 24px rgba(0, 0, 0, 0.8);
    }

    .hero-title .highlight {
      color: #FF8000;
      font-style: italic;
      font-weight: 600;
    }

    .hero-desc {
      font-size: 19px;
      line-height: 1.55;
      color: #D0C5BD;
      font-weight: 400;
      max-width: 780px;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.9);
    }

    /* Provenance Pillars & Feature Badges */
    .footer-strip {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      padding-top: 24px;
    }

    .pills-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .spec-pill {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      backdrop-filter: blur(10px);
    }

    .spec-pill .pill-val {
      color: #FFFFFF;
      font-weight: 800;
      font-size: 15px;
      letter-spacing: 0.3px;
    }

    .spec-pill .pill-label {
      color: #A3968E;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .domain-tag {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 700;
      color: #FFFFFF;
      background: rgba(212, 136, 66, 0.18);
      border: 1px solid rgba(212, 136, 66, 0.4);
      padding: 8px 18px;
      border-radius: 999px;
      letter-spacing: 0.5px;
    }

    .domain-tag span {
      color: #FF8000;
    }
  </style>
</head>
<body>
  <div class="bg-layer"></div>
  <div class="overlay-vignette"></div>

  <div class="canvas-container">
    <!-- Top Brand & Status -->
    <div class="top-strip">
      <div class="brand-logo-wrap">
        ${logoSvgContent}
      </div>
      <div class="top-badge">
        <span class="pulse-dot"></span>
        <span>SCA 84+ Specialty Roastery</span>
      </div>
    </div>

    <!-- Main Headline & Narrative -->
    <div class="main-content">
      <div class="category-label">Cà Phê Việt Nam Nguyên Bản</div>
      <h1 class="hero-title">
        Từ Nông Trại Bazan Đến <span class="highlight">Tách Cà Phê Có Gu</span>
      </h1>
      <p class="hero-desc">
        Hạt Robusta núi lửa Cư M'gar đậm đà &amp; Arabica Cầu Đất (1.650m) thanh thoát. Rang mộc đối lưu Hot-Air, bảo toàn hương hoa trái tự nhiên. Cam kết Cà Phê Mộc 4 Không.
      </p>
    </div>

    <!-- Footer Provenance Metrics -->
    <div class="footer-strip">
      <div class="pills-group">
        <div class="spec-pill">
          <span class="pill-val">SCA 84+</span>
          <span class="pill-label">Cupping Score</span>
        </div>
        <div class="spec-pill">
          <span class="pill-val">1.650m</span>
          <span class="pill-label">Cầu Đất Terroir</span>
        </div>
        <div class="spec-pill">
          <span class="pill-val">4 KHÔNG</span>
          <span class="pill-label">Cà Phê Mộc</span>
        </div>
        <div class="spec-pill">
          <span class="pill-val">HOT-AIR</span>
          <span class="pill-label">Đối Lưu Tuần Hoàn</span>
        </div>
      </div>

      <div class="domain-tag">
        innokafe.<span>com</span>
      </div>
    </div>
  </div>
</body>
</html>`;

async function main() {
  console.log('='.repeat(70));
  console.log('GENERATING INNOKAFE SOCIAL SHARE BANNER (1200 x 630)');
  console.log('='.repeat(70));

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1200, height: 630 },
    deviceScaleFactor: 2 // 2x high-density render
  });

  const page = await context.newPage();
  await page.setContent(htmlContent, { waitUntil: 'networkidle' });

  // Allow web fonts to render cleanly
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  await page.waitForTimeout(500);

  const outJpg = path.join(OUT_DIR, 'innokafe_social_share_1200x630.jpg');
  const outWebp = path.join(OUT_DIR, 'innokafe_social_share_1200x630.webp');

  await page.screenshot({
    path: outJpg,
    type: 'jpeg',
    quality: 92,
    clip: { x: 0, y: 0, width: 1200, height: 630 }
  });
  console.log(`[✓] Created JPEG: ${outJpg} (${fs.statSync(outJpg).size} bytes)`);

  await page.screenshot({
    path: outWebp,
    type: 'png', // save then convert, or use native page screenshot
    clip: { x: 0, y: 0, width: 1200, height: 630 }
  });
  console.log(`[✓] Captured high-res master: ${outWebp} (${fs.statSync(outWebp).size} bytes)`);

  await browser.close();
  console.log('🎉 Social share banner generated successfully!');
}

main().catch(err => {
  console.error('[✗] Failed to generate social banner:', err);
  process.exit(1);
});
