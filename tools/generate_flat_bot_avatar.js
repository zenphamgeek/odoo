/**
 * tools/generate_flat_bot_avatar.js
 * Renders a delightful, cute, and cheerful Flat SVG InsilosBot mascot avatar to 512x512 PNG using Playwright.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0E3A7E"/>
      <stop offset="60%" stop-color="#0B2E64"/>
      <stop offset="100%" stop-color="#05152F"/>
    </linearGradient>

    <!-- Cyan Glow -->
    <filter id="cyanGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>

    <filter id="softShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#020914" flood-opacity="0.45"/>
    </filter>

    <!-- Linear Accent for Visor -->
    <linearGradient id="visorGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#091426"/>
      <stop offset="100%" stop-color="#050C17"/>
    </linearGradient>

    <!-- White Ceramic Highlight -->
    <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#E2EEFC"/>
    </linearGradient>

    <linearGradient id="cyanAccent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F2FE"/>
      <stop offset="100%" stop-color="#0B78FF"/>
    </linearGradient>
  </defs>

  <!-- Circular Outer Background Canvas -->
  <circle cx="256" cy="256" r="256" fill="url(#bgGrad)"/>
  
  <!-- Subtle Decorative Outer Tech Ring -->
  <circle cx="256" cy="256" r="236" fill="none" stroke="#00F2FE" stroke-width="2" stroke-opacity="0.25" stroke-dasharray="16 8"/>

  <!-- Character Group Centered -->
  <g transform="translate(0, 16)" filter="url(#softShadow)">
    
    <!-- Cute Dual Antennas -->
    <!-- Left Antenna -->
    <g transform="rotate(-18 190 120)">
      <rect x="186" y="70" width="8" height="42" rx="4" fill="#CCDDF0"/>
      <circle cx="190" cy="65" r="14" fill="url(#cyanAccent)" filter="url(#cyanGlow)"/>
      <circle cx="187" cy="62" r="4" fill="#FFFFFF" opacity="0.8"/>
    </g>
    <!-- Right Antenna -->
    <g transform="rotate(18 322 120)">
      <rect x="318" y="70" width="8" height="42" rx="4" fill="#CCDDF0"/>
      <circle cx="322" cy="65" r="14" fill="url(#cyanAccent)" filter="url(#cyanGlow)"/>
      <circle cx="319" cy="62" r="4" fill="#FFFFFF" opacity="0.8"/>
    </g>

    <!-- Cute Torso & Floating Body -->
    <path d="M 180,310 C 180,310 170,390 256,390 C 342,390 332,310 332,310 Z" fill="url(#bodyGrad)"/>
    <!-- Cyan Torso Apron / Badge -->
    <path d="M 205,320 C 205,320 198,368 256,368 C 314,368 307,320 307,320 Z" fill="url(#cyanAccent)" opacity="0.9"/>
    <!-- Insilos "iB" emblem on torso -->
    <circle cx="256" cy="336" r="5" fill="#FFFFFF"/>
    <rect x="253" y="345" width="6" height="13" rx="3" fill="#FFFFFF"/>

    <!-- Cheerful Waving Arms -->
    <!-- Left Arm (Waving high) -->
    <path d="M 175,325 C 140,315 118,280 122,255 C 124,242 136,236 148,244 C 160,252 170,290 182,312 Z" fill="url(#bodyGrad)"/>
    <circle cx="123" cy="250" r="14" fill="url(#bodyGrad)"/>
    <!-- Left Arm Cyan Palm Light -->
    <circle cx="123" cy="250" r="6" fill="#00F2FE" filter="url(#cyanGlow)"/>

    <!-- Right Arm (Welcoming gesture) -->
    <path d="M 337,325 C 372,315 394,280 390,255 C 388,242 376,236 364,244 C 352,252 342,290 330,312 Z" fill="url(#bodyGrad)"/>
    <circle cx="389" cy="250" r="14" fill="url(#bodyGrad)"/>
    <!-- Right Arm Cyan Palm Light -->
    <circle cx="389" cy="250" r="6" fill="#00F2FE" filter="url(#cyanGlow)"/>

    <!-- Head Shell Outer (Chubby, lovable, smooth rounded shape) -->
    <!-- Head width: 260px, height: 200px, rx: 70px -->
    <rect x="126" y="115" width="260" height="200" rx="72" fill="url(#bodyGrad)"/>

    <!-- Ear Caps (Cute rounded side headphones) -->
    <rect x="110" y="175" width="24" height="75" rx="12" fill="#B8D3F2"/>
    <rect x="115" y="185" width="8" height="55" rx="4" fill="url(#cyanAccent)"/>

    <rect x="378" y="175" width="24" height="75" rx="12" fill="#B8D3F2"/>
    <rect x="389" y="185" width="8" height="55" rx="4" fill="url(#cyanAccent)"/>

    <!-- Dark Visor Display Screen -->
    <rect x="150" y="137" width="212" height="156" rx="52" fill="url(#visorGrad)"/>
    
    <!-- Subtle Glass Sheen on Top of Visor -->
    <path d="M 160,185 C 160,150 185,142 256,142 C 327,142 352,150 352,185 C 330,165 290,158 256,158 C 220,158 180,165 160,185 Z" fill="#FFFFFF" opacity="0.12"/>

    <!-- Happy Eyes & Smile: Pure Joy Expression -->
    <!-- Left Happy Eye: Cute Upward Crescent Moon Arc -->
    <path d="M 188,206 C 188,186 222,186 222,206" fill="none" stroke="#00F2FE" stroke-width="12" stroke-linecap="round" filter="url(#cyanGlow)"/>
    <!-- Inner bright core -->
    <path d="M 188,206 C 188,186 222,186 222,206" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>

    <!-- Right Happy Eye: Cute Upward Crescent Moon Arc -->
    <path d="M 290,206 C 290,186 324,186 324,206" fill="none" stroke="#00F2FE" stroke-width="12" stroke-linecap="round" filter="url(#cyanGlow)"/>
    <!-- Inner bright core -->
    <path d="M 290,206 C 290,186 324,186 324,206" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>

    <!-- Cute Rosy Cheeks (Soft Glowing Blush) -->
    <circle cx="180" cy="226" r="13" fill="#FF4F79" opacity="0.4" filter="url(#cyanGlow)"/>
    <circle cx="332" cy="226" r="13" fill="#FF4F79" opacity="0.4" filter="url(#cyanGlow)"/>

    <!-- Cheerful Big Smile -->
    <path d="M 230,230 Q 256,256 282,230" fill="none" stroke="#00F2FE" stroke-width="10" stroke-linecap="round" filter="url(#cyanGlow)"/>
    <!-- Inner Smile Bright Core -->
    <path d="M 230,230 Q 256,256 282,230" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>

    <!-- Playful Sparkle Star Top Right -->
    <path d="M 370,120 Q 370,135 385,135 Q 370,135 370,150 Q 370,135 355,135 Q 370,135 370,120 Z" fill="#00F2FE" filter="url(#cyanGlow)"/>
  </g>
</svg>`;

async function renderAvatar() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 512, height: 512 } });

  await page.setContent(`<!DOCTYPE html>
  <html>
    <head>
      <style>
        body, html { margin: 0; padding: 0; width: 512px; height: 512px; overflow: hidden; background: transparent; }
      </style>
    </head>
    <body>${svgContent}</body>
  </html>`);

  const pngBuffer = await page.screenshot({ omitBackground: true });
  await browser.close();

  // Save SVG
  const svgPath = path.resolve(__dirname, '../addons/mail/static/src/img/odoobot.svg');
  fs.writeFileSync(svgPath, svgContent);
  console.log('Saved SVG to:', svgPath);

  // Save PNG 512x512
  const pngPath = path.resolve(__dirname, '../addons/mail/static/src/img/odoobot.png');
  fs.writeFileSync(pngPath, pngBuffer);
  console.log('Saved PNG to:', pngPath);

  // Also transparent variant
  const transparentPngPath = path.resolve(__dirname, '../addons/mail/static/src/img/odoobot_transparent.png');
  fs.writeFileSync(transparentPngPath, pngBuffer);
  console.log('Saved transparent PNG to:', transparentPngPath);

  // Also copy to artifact dir so we can preview with view_file
  const artifactPng = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/insilosbot_flat_avatar_preview.png';
  fs.writeFileSync(artifactPng, pngBuffer);
  console.log('Saved preview to artifact dir:', artifactPng);
}

renderAvatar().catch(console.error);
