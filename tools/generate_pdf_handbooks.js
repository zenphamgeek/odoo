/**
 * High-Quality PDF Converter for Insilos Enterprise Handbooks & Brochures
 * Uses Playwright Chromium headless with printBackground: true and A4 styling.
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function renderPdf(htmlPath, pdfPath, options = {}) {
  console.log(`📄 Converting [${path.basename(htmlPath)}] -> [${path.basename(pdfPath)}]...`);
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const fileUrl = 'file://' + path.resolve(htmlPath);
  await page.goto(fileUrl, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1500);

  await page.pdf({
    path: pdfPath,
    format: options.format || 'A4',
    landscape: options.landscape || false,
    printBackground: true,
    margin: options.margin || {
      top: '15mm',
      bottom: '15mm',
      left: '15mm',
      right: '15mm'
    },
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `
      <div style="font-family: 'Inter', sans-serif; font-size: 8pt; width: 100%; padding: 0 15mm; display: flex; justify-content: space-between; color: #64748b;">
        <span>Insilos Enterprise Platform — Confidential &amp; Proprietary</span>
        <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
      </div>
    `
  });

  await browser.close();
  const stats = fs.statSync(pdfPath);
  console.log(`  ✓ Generated ${path.basename(pdfPath)} (${(stats.size / 1024).toFixed(1)} KB)`);
}

async function main() {
  const docDir = path.resolve(__dirname, '../doc');

  const filesToConvert = [
    {
      html: path.join(docDir, 'INSILOS_ENTERPRISE_DEPLOYMENT_HANDBOOK.html'),
      pdf: path.join(docDir, 'INSILOS_ENTERPRISE_DEPLOYMENT_HANDBOOK.pdf'),
      landscape: false
    },
    {
      html: path.join(docDir, 'INSILOS_MARKETING_PRODUCT_OVERVIEW.html'),
      pdf: path.join(docDir, 'INSILOS_MARKETING_PRODUCT_OVERVIEW.pdf'),
      landscape: false
    },
    {
      html: path.join(docDir, 'INSILOS_EXECUTIVE_PITCH_DECK.html'),
      pdf: path.join(docDir, 'INSILOS_EXECUTIVE_PITCH_DECK.pdf'),
      landscape: true
    }
  ];

  for (const item of filesToConvert) {
    if (fs.existsSync(item.html)) {
      await renderPdf(item.html, item.pdf, { landscape: item.landscape });
    } else {
      console.warn(`⚠️ HTML file not found: ${item.html}`);
    }
  }
}

if (require.main === module) {
  main().catch(err => {
    console.error('❌ Error generating PDFs:', err);
    process.exit(1);
  });
}

module.exports = { renderPdf };
