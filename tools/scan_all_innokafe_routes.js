#!/usr/bin/env node
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

let rawBaseUrl = process.argv[2] || 'http://127.0.0.1:28071';
let baseUrl;
try {
  const parsed = new URL(rawBaseUrl);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error(`unsupported protocol: ${parsed.protocol}`);
  }
  baseUrl = `${parsed.origin}${parsed.pathname.replace(/\/+$/, '')}`;
} catch (e) {
  console.error(`[✗] Invalid base URL argument: ${e.message}`);
  process.exit(2);
}

const routes = [
  '/',
  '/story',
  '/products',
  '/taste-profiler',
  '/solutions-b2b',
  '/contactus'
];

console.log('='.repeat(70));
console.log(`PIXEL LAYOUT AUDIT SWEEP ACROSS ALL 6 INNOKAFE ROUTES`);
console.log(`Target: ${baseUrl}`);
console.log('='.repeat(70));

const results = [];
const scannerScript = path.resolve(__dirname, '..', '.agents', 'skills', 'screenshot-pixels-scan', 'scripts', 'pixel_layout_scanner.js');

for (const route of routes) {
  const slug = route === '/' ? 'home' : route.replace('/', '');
  const outDir = path.join(__dirname, '..', 'artifacts', `scan_local_${slug}`);
  fs.mkdirSync(outDir, { recursive: true });

  const url = `${baseUrl}${route}`;
  console.log(`\n▶ Scanning ${route} (${url})...`);
  try {
    const args = [
      scannerScript,
      '--url', url,
      '--viewports', 'desktop,mobile',
      '--output', outDir
    ];
    const out = execFileSync('node', args, { encoding: 'utf-8', timeout: 120000 });
    
    // Check summary json
    const summaryFile = path.join(outDir, 'pixel_scan_summary.json');
    if (fs.existsSync(summaryFile)) {
      const summary = JSON.parse(fs.readFileSync(summaryFile, 'utf-8'));
      const dData = (summary.viewports && summary.viewports.desktop) || summary.desktop;
      const mData = (summary.viewports && summary.viewports.mobile) || summary.mobile;
      const dScore = dData ? dData.score : 'N/A';
      const mScore = mData ? mData.score : 'N/A';
      const dGrade = dData ? dData.grade : 'N/A';
      const mGrade = mData ? mData.grade : 'N/A';
      console.log(`  [✓] ${route.padEnd(18)} | Desktop: ${dScore}/100 (${dGrade}) | Mobile: ${mScore}/100 (${mGrade})`);
      results.push({ route, desktop: { score: dScore, grade: dGrade }, mobile: { score: mScore, grade: mGrade } });
    }
  } catch (err) {
    console.error(`  [✗] Error scanning ${route}: ${err.message}`);
    results.push({ route, error: err.message });
  }
}

console.log('\n' + '='.repeat(70));
console.log('SUMMARY OF PIXEL LAYOUT AUDIT:');
console.log('='.repeat(70));
let allA = true;
for (const r of results) {
  if (r.error) {
    console.log(`  ❌ ${r.route.padEnd(18)} FAILED: ${r.error}`);
    allA = false;
  } else {
    console.log(`  ✅ ${r.route.padEnd(18)} Desktop: ${r.desktop.score} (${r.desktop.grade}) | Mobile: ${r.mobile.score} (${r.mobile.grade})`);
    if (r.desktop.grade !== 'A+' || r.mobile.grade !== 'A+') {
      allA = false;
    }
  }
}
console.log('='.repeat(70));
if (allA) {
  console.log('🎉 100% PERFECT GRADE A+ ACROSS ALL 6 ROUTES AND ALL VIEWPORTS!');
} else {
  console.log('⚠️ Some routes require further adjustment.');
}
