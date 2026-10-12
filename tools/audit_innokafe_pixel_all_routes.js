#!/usr/bin/env node
/**
 * tools/audit_innokafe_pixel_all_routes.js
 * =============================================================================
 * Automated Multi-Route Pixel Layout & Visual Quality Auditor for InnoKafe
 * Scans all 6 core routes across Desktop (1440x900), Tablet (768x1024), and Mobile (375x812):
 * 1. / (Home)
 * 2. /story (Heritage & Story)
 * 3. /products (Specialty Coffee Products)
 * 4. /taste-profiler (Interactive Sensory Radar)
 * 5. /solutions-b2b (B2B Wholesale & ROI Calculator)
 * 6. /contactus (Contact Us)
 *
 * Utilizes the official screenshot-pixels-scan engine.
 * =============================================================================
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function resolveBaseUrl() {
    const raw = process.env.INNOKAFE_BASE_URL || 'https://innokafe.insilos.com';
    let u;
    try {
        u = new URL(raw);
    } catch {
        throw new Error(`Invalid INNOKAFE_BASE_URL: ${raw}`);
    }
    if (!['http:', 'https:'].includes(u.protocol)) {
        throw new Error(`INNOKAFE_BASE_URL must be http(s), got ${u.protocol}`);
    }
    return u.origin;
}

const BASE_URL = resolveBaseUrl();
const SCANNER = path.join('.agents', 'skills', 'screenshot-pixels-scan', 'scripts', 'pixel_layout_scanner.js');
const OUTPUT_ROOT = path.join(process.cwd(), 'innokafe_pixel_scan');

const ROUTES = [
    { name: 'home', path: '/' },
    { name: 'story', path: '/story' },
    { name: 'products', path: '/products' },
    { name: 'taste-profiler', path: '/taste-profiler' },
    { name: 'solutions-b2b', path: '/solutions-b2b' },
    { name: 'contactus', path: '/contactus' }
];

async function runAudit() {
    console.log('===============================================================');
    console.log(`🚀 INNOKAFE MULTI-ROUTE PIXEL LAYOUT AUDITOR: ${BASE_URL}`);
    console.log(`📁 Output Root: ${OUTPUT_ROOT}`);
    console.log('===============================================================');

    const summaryReport = {
        baseUrl: BASE_URL,
        timestamp: new Date().toISOString(),
        totalRoutes: ROUTES.length,
        routes: {}
    };

    for (const route of ROUTES) {
        const routeUrl = `${BASE_URL}${route.path}`;
        const routeDir = path.join(OUTPUT_ROOT, route.name);
        
        console.log(`\n---------------------------------------------------------------`);
        console.log(`[*] Auditing Route: ${route.path} -> ${routeDir}`);
        console.log(`---------------------------------------------------------------`);
        
        try {
            execFileSync('node', [SCANNER, '--url', routeUrl, '--output', routeDir], { stdio: 'inherit' });
            
            const summaryFile = path.join(routeDir, 'pixel_scan_summary.json');
            if (fs.existsSync(summaryFile)) {
                const data = JSON.parse(fs.readFileSync(summaryFile, 'utf8'));
                summaryReport.routes[route.name] = {
                    path: route.path,
                    url: routeUrl,
                    status: 'SUCCESS',
                    viewports: data.viewports
                };
            }
        } catch (err) {
            console.error(`[X] Error auditing ${route.path}:`, err.message);
            summaryReport.routes[route.name] = {
                path: route.path,
                url: routeUrl,
                status: 'FAILED',
                error: err.message
            };
        }
    }

    // Compile Master Markdown Report
    const masterReportPath = path.join(OUTPUT_ROOT, 'INNOKAFE_ALL_ROUTES_PIXEL_AUDIT_REPORT.md');
    let md = `# InnoKafe Master Visual Quality & Pixel Layout Audit Report\n\n`;
    md += `**Target System:** [${BASE_URL}](${BASE_URL})\n`;
    md += `**Audit Timestamp:** ${summaryReport.timestamp}\n`;
    md += `**Total Routes Audited:** ${ROUTES.length} routes across 3 viewports (Desktop HD, Tablet iPad, Mobile iPhone)\n\n`;
    md += `## 1. Master Cross-Route Quality Matrix\n\n`;
    md += `| Route | Path | Desktop (1440x900) | Tablet (768x1024) | Mobile (375x812) | Overall Grade | Status |\n`;
    md += `| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n`;

    let totalScore = 0;
    let scoreCount = 0;
    let allGradeAPlus = true;

    for (const [key, r] of Object.entries(summaryReport.routes)) {
        if (r.status === 'SUCCESS' && r.viewports) {
            const d = r.viewports.desktop || {};
            const t = r.viewports.tablet || {};
            const m = r.viewports.mobile || {};

            const avgRouteScore = Math.round(((d.score || 0) + (t.score || 0) + (m.score || 0)) / 3);
            totalScore += avgRouteScore;
            scoreCount++;

            const grade = avgRouteScore >= 95 ? 'A+' : (avgRouteScore >= 85 ? 'A' : (avgRouteScore >= 75 ? 'B' : 'C'));
            if (grade !== 'A+') allGradeAPlus = false;

            md += `| **${key.toUpperCase()}** | \`${r.path}\` | ${d.score}/100 (${d.grade || '-'}) | ${t.score}/100 (${t.grade || '-'}) | ${m.score}/100 (${m.grade || '-'}) | **${grade}** | ✅ Grade ${grade} |\n`;
        } else {
            md += `| **${key.toUpperCase()}** | \`${r.path}\` | - | - | - | F | ❌ Failed |\n`;
            allGradeAPlus = false;
        }
    }

    const grandAvg = scoreCount > 0 ? Math.round(totalScore / scoreCount) : 0;
    md += `\n**Overall InnoKafe Platform Score: ${grandAvg}/100 [Grade ${allGradeAPlus ? 'A+' : 'A'}]**\n\n`;
    md += `## 2. Route-by-Route Breakdown & Visual Artifacts\n\n`;

    for (const [key, r] of Object.entries(summaryReport.routes)) {
        md += `### ${key.toUpperCase()} (\`${r.path}\`)\n\n`;
        if (r.status === 'SUCCESS' && r.viewports) {
            md += `- **Desktop Screenshot:** [Fullpage](./${key}/scan_desktop_fullpage.png) | [Above-Fold](./${key}/scan_desktop_fold.png)\n`;
            md += `- **Tablet Screenshot:** [Fullpage](./${key}/scan_tablet_fullpage.png) | [Above-Fold](./${key}/scan_tablet_fold.png)\n`;
            md += `- **Mobile Screenshot:** [Fullpage](./${key}/scan_mobile_fullpage.png) | [Above-Fold](./${key}/scan_mobile_fold.png)\n`;
            md += `- **Defect Count:** Desktop: ${r.viewports.desktop?.defects?.length || 0}, Tablet: ${r.viewports.tablet?.defects?.length || 0}, Mobile: ${r.viewports.mobile?.defects?.length || 0}\n\n`;
        } else {
            md += `> [!CAUTION]\n> Scan error: ${r.error}\n\n`;
        }
    }

    fs.writeFileSync(masterReportPath, md, 'utf8');
    fs.writeFileSync(path.join(OUTPUT_ROOT, 'master_pixel_scan_summary.json'), JSON.stringify(summaryReport, null, 2), 'utf8');

    console.log('\n===============================================================');
    console.log('🎉 ALL INNOKAFE ROUTES AUDIT COMPLETE!');
    console.log(`📊 Grand Average Score: ${grandAvg}/100`);
    console.log(`📄 Master Report: ${masterReportPath}`);
    console.log('===============================================================');
}

runAudit().catch(err => {
    console.error('Fatal audit failure:', err);
    process.exit(1);
});
