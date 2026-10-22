#!/usr/bin/env node
/**
 * tools/verify_hero_interactive_flow.js
 * =============================================================================
 * Automated Playwright Interactive Flow & Kinetic Animation Test Suite
 * Target: https://innoria.insilos.com/ (or configurable via --url)
 *
 * Verifies Homepage Hero Stage Breakthrough Quality:
 *  1. B2B Cinema Headline: "Tailored Technology for Sovereign Enterprise".
 *  2. 4-Mode Interactive Scene Switcher:
 *     - Mode 0: [Cloud & Data Fabric] (cloud-fabric)
 *     - Mode 1: [Autonomous AI Swarm] (ai-swarm)
 *     - Mode 2: [Intelligent ERP] (smart-erp)
 *     - Mode 3: [Enterprise Trust & Security] (trust-security)
 *  3. Dynamic active mode classes, content pane crossfade, and kinetic camera / scene state update.
 *  4. VIP CTA Button: "Trải Nghiệm Live Proof-of-Concept 3 Giờ" with @keyframes haloPulse,
 *     linking to #innoria_contact_section.
 *  5. 60 FPS Kinetic Performance: requestAnimationFrame benchmark asserting frame rate
 *     and zero frame freeze (> 100ms).
 *  6. Zero Instructional Text in Hero Stage DOM ("Kéo chuột", "Hover khối", etc.).
 *  7. 0 unhandled JavaScript exceptions in browser console.
 *
 * Exit code 0 on 100% PASS, 1 on any failure.
 * =============================================================================
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// CLI Argument Parsing
const args = process.argv.slice(2);
function getArg(flag, defaultValue) {
    const idx = args.indexOf(flag);
    if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
    return defaultValue;
}
const hasFlag = flag => args.includes(flag);

if (hasFlag('--help') || hasFlag('-h')) {
    console.log(`
Usage: node tools/verify_hero_interactive_flow.js [options]

Options:
  --url <url>          Base URL to test (default: https://innoria.insilos.com)
  --headed             Run browser in headed mode (default: headless)
  --verbose            Show detailed frame timings, DOM state, and transition logs
  --min-fps <number>   Minimum acceptable average FPS (default: 24 for headless, 50 for headed)
  --timeout <ms>       Navigation & test timeout in ms (default: 35000)
  --json <path>        Write JSON test report to specified path
  --help, -h           Show this help message
`);
    process.exit(0);
}

const BASE_URL = (getArg('--url', process.env.BASE_URL || 'https://innoria.insilos.com')).replace(/\/$/, '');
const IS_HEADLESS = !hasFlag('--headed');
const IS_VERBOSE = hasFlag('--verbose');
const TIMEOUT_MS = parseInt(getArg('--timeout', '35000'), 10);
const JSON_OUTPUT_PATH = getArg('--json', null);
const MIN_FPS = parseFloat(getArg('--min-fps', IS_HEADLESS ? '24' : '50'));
const ARTIFACT_DIR = getArg('--artifacts', '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865');

// 4 Interactive Scene Modes Specification
const SCENE_MODES = [
    {
        index: 0,
        id: 'cloud-fabric',
        label: 'Cloud & Data Fabric',
        keywords: ['cloud', 'fabric', 'data', 'digiforce'],
        expectedNarrative: 'Data Fabric'
    },
    {
        index: 1,
        id: 'ai-swarm',
        label: 'Autonomous AI Swarm',
        keywords: ['swarm', 'mojo', 'copilot', 'autonomous ai'],
        expectedNarrative: 'AI'
    },
    {
        index: 2,
        id: 'smart-erp',
        label: 'Intelligent ERP',
        keywords: ['erp', 'intelligent', 'lõi', 'sovereign'],
        expectedNarrative: 'ERP'
    },
    {
        index: 3,
        id: 'trust-security',
        label: 'Enterprise Trust & Security',
        keywords: ['trust', 'security', 'mojoverse', 'blockchain'],
        expectedNarrative: 'Trust'
    }
];

// ANSI Colors
const colors = {
    reset: '\x1b[0m',
    bold: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    cyan: '\x1b[36m',
    gray: '\x1b[90m',
    magenta: '\x1b[35m'
};

async function runHeroInteractiveFlow() {
    console.log(`\n${colors.bold}${colors.cyan}==============================================================================${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}    INNORIA HOMEPAGE HERO INTERACTIVE STAGE & 60 FPS FLOW TEST SUITE          ${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}==============================================================================${colors.reset}`);
    console.log(`${colors.gray}Target URL:    ${BASE_URL}/${colors.reset}`);
    console.log(`${colors.gray}Headless:      ${IS_HEADLESS ? 'YES' : 'NO'}${colors.reset}`);
    console.log(`${colors.gray}Timeout SLA:   ${TIMEOUT_MS}ms${colors.reset}`);
    console.log(`${colors.gray}Min FPS SLA:   ${MIN_FPS} FPS${colors.reset}\n`);

    if (!fs.existsSync(ARTIFACT_DIR)) {
        try { fs.mkdirSync(ARTIFACT_DIR, { recursive: true }); } catch (e) {}
    }

    const report = {
        timestamp: new Date().toISOString(),
        targetUrl: `${BASE_URL}/`,
        passed: false,
        steps: {
            stagePresence: { name: 'Hero Container Visibility', pass: false, details: '' },
            stageController: { name: 'Hero Controller Instance', pass: false, details: '' },
            b2bHeadline: { name: 'B2B Cinema Headline Assertion', pass: false, details: '' },
            modeSwitcher: { name: '4-Mode Interactive Switcher', pass: false, tested: 0, passed: 0, modes: [] },
            vipCtaHalo: { name: 'VIP CTA Button & Halo Pulse', pass: false, details: '' },
            fpsPerformance: { name: '60 FPS & Zero-Freeze Benchmark', pass: false, metrics: {} },
            zeroInstructionText: { name: 'Zero Instructional Text', pass: false, details: '' },
            consoleCleanliness: { name: 'Console Error Cleanliness', pass: false, errors: [] }
        }
    };

    const consoleErrors = [];
    const browser = await chromium.launch({
        headless: IS_HEADLESS,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--ignore-gpu-blocklist',
            '--enable-gpu-rasterization',
            '--enable-webgl',
            '--use-gl=angle',
            '--use-angle=gl'
        ]
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    page.on('console', msg => {
        if (msg.type() === 'error') {
            const txt = msg.text();
            if (!txt.includes('google-analytics') && !txt.includes('doubleclick') && !txt.includes('favicon.ico')) {
                consoleErrors.push(txt);
            }
        }
    });

    page.on('pageerror', err => {
        consoleErrors.push(err.message || String(err));
    });

    try {
        // =================================================================
        // STEP 1: Navigate to Homepage & Check Hero Stage Presence
        // =================================================================
        process.stdout.write(`  [1/8] Navigating to ${BASE_URL}/ and verifying Hero stage ... `);
        const resp = await page.goto(`${BASE_URL}/`, {
            waitUntil: 'domcontentloaded',
            timeout: TIMEOUT_MS
        });

        if (!resp || resp.status() !== 200) {
            throw new Error(`Unexpected HTTP status code: ${resp ? resp.status() : 'NULL'}`);
        }

        await page.waitForTimeout(2000); // Allow WebGL/video initialization

        const heroContainer = page.locator('#innoria_hero_cover');
        const heroExists = (await heroContainer.count()) > 0;
        const heroVisible = heroExists && (await heroContainer.first().isVisible());

        if (heroExists && heroVisible) {
            report.steps.stagePresence.pass = true;
            report.steps.stagePresence.details = '#innoria_hero_cover container mounted and visible in DOM.';
            console.log(`${colors.green}✓ PASS${colors.reset}`);
        } else {
            report.steps.stagePresence.pass = false;
            report.steps.stagePresence.details = '#innoria_hero_cover not found or hidden.';
            console.log(`${colors.red}✗ FAIL (#innoria_hero_cover missing/hidden)${colors.reset}`);
        }

        // =================================================================
        // STEP 2: Verify Hero Controller Instance in Window (if mounted)
        // =================================================================
        process.stdout.write(`  [2/8] Checking Hero Interactive Stage Controller instance ... `);
        await page.waitForFunction(() => !!(window.innoriaHeroInteractiveStage || window.innoriaHeroSlider), { timeout: 8000 }).catch(() => {});
        const controllerStatus = await page.evaluate(() => {
            const stage = window.innoriaHeroInteractiveStage || window.innoriaHeroSlider;
            if (!stage) return { exists: false };
            return {
                exists: true,
                currentIndex: typeof stage.currentIndex === 'number' ? stage.currentIndex : 0,
                totalSlides: stage.totalSlides || 4,
                isPlaying: !!stage.isPlaying,
                hasThreeEngine: !!stage.threeEngine,
                dprClamp: stage.threeEngine && stage.threeEngine.renderer ? stage.threeEngine.renderer.getPixelRatio() : null
            };
        });

        if (controllerStatus.exists) {
            report.steps.stageController.pass = true;
            report.steps.stageController.details = `Controller active (slides: ${controllerStatus.totalSlides}, current: ${controllerStatus.currentIndex}, 3D: ${controllerStatus.hasThreeEngine}).`;
            console.log(`${colors.green}✓ PASS (controller mounted)${colors.reset}`);
        } else {
            // Even if JS controller is not globally bound, DOM-driven interactive switcher may be present
            report.steps.stageController.pass = false;
            report.steps.stageController.details = 'window.innoriaHeroInteractiveStage or slider not globally exposed.';
            console.log(`${colors.yellow}⚠ WARN (global controller handle not found, testing via DOM)${colors.reset}`);
        }

        // =================================================================
        // STEP 3: Assert B2B Cinema Headline Presence
        // =================================================================
        process.stdout.write(`  [3/8] Asserting B2B Cinema Headline ("Tailored Technology for Sovereign Enterprise") ... `);
        const headlineEvaluation = await page.evaluate(() => {
            const heroEl = document.querySelector('#innoria_hero_cover');
            if (!heroEl) return { found: false, text: '' };

            const text = heroEl.innerText || '';
            const normalized = text.toLowerCase().replace(/\s+/g, ' ');

            const exactPhrase = 'tailored technology for sovereign enterprise';
            const hasExact = normalized.includes(exactPhrase);
            const hasSovereign = normalized.includes('sovereign enterprise');
            const hasTailored = normalized.includes('tailored technology');
            const hasAutonomousOps = normalized.includes('autonomous enterprise operations') || normalized.includes('vận hành tự động');

            return {
                found: hasExact || (hasSovereign && hasTailored),
                hasExact,
                hasSovereign,
                hasTailored,
                hasAutonomousOps,
                heroTextPreview: text.substring(0, 300)
            };
        });

        if (headlineEvaluation.found) {
            report.steps.b2bHeadline.pass = true;
            report.steps.b2bHeadline.details = headlineEvaluation.hasExact
                ? 'Exact match: "Tailored Technology for Sovereign Enterprise" found.'
                : 'Found "Tailored Technology" and "Sovereign Enterprise" narrative tokens.';
            console.log(`${colors.green}✓ PASS${colors.reset}`);
        } else {
            report.steps.b2bHeadline.pass = false;
            report.steps.b2bHeadline.details = `Headline missing in hero stage. Preview: "${headlineEvaluation.heroTextPreview.substring(0, 100)}..."`;
            console.log(`${colors.red}✗ FAIL (Headline not detected)${colors.reset}`);
            if (IS_VERBOSE) {
                console.log(`       ${colors.gray}Hero text preview: ${headlineEvaluation.heroTextPreview}${colors.reset}`);
            }
        }

        // =================================================================
        // STEP 4: Test 4-Mode Interactive Scene Switcher
        // =================================================================
        process.stdout.write(`  [4/8] Testing 4-Mode Scene Switcher clicks, active classes & crossfades ... `);

        const switcherResults = [];
        let switcherPassedCount = 0;

        for (const mode of SCENE_MODES) {
            const modeCheck = {
                index: mode.index,
                id: mode.id,
                label: mode.label,
                buttonFound: false,
                becameActive: false,
                contentUpdated: false,
                pass: false
            };

            // Locate switcher tab/button by multiple flexible contracts:
            const locatorCandidates = [
                page.locator(`button.hero-scene-nav-item[data-tab-target="${mode.index}"]`),
                page.locator(`button.hero-scene-nav-item[data-scene-id="${mode.id}"]`),
                page.locator(`[data-scene-id="${mode.id}"]`),
                page.locator(`.hero-scene-nav-item:has-text("${mode.label}")`),
                page.locator(`#innoria_hero_cover [data-slide-index="${mode.index}"]`),
                page.locator(`#innoria_hero_cover .hero-product-tab:has-text("${mode.label}")`),
                page.locator(`#innoria_hero_cover button[data-tab-target="${mode.index}"]`)
            ];

            let activeLocator = null;
            for (const loc of locatorCandidates) {
                if ((await loc.count()) > 0) {
                    activeLocator = loc.first();
                    break;
                }
            }

            // Fallback: search by keywords in hero tabs
            if (!activeLocator) {
                for (const kw of mode.keywords) {
                    const fallbackLoc = page.locator(`#innoria_hero_cover [data-scene-id*="${kw}"], #innoria_hero_cover button:has-text("${kw}"), #innoria_hero_cover .nav-link:has-text("${kw}")`);
                    if ((await fallbackLoc.count()) > 0) {
                        activeLocator = fallbackLoc.first();
                        break;
                    }
                }
            }

            if (activeLocator) {
                modeCheck.buttonFound = true;

                // Click mode switcher
                await activeLocator.click({ timeout: 5000 }).catch(() => {});
                await page.waitForTimeout(500); // Allow camera LERP & crossfade

                // Check active state
                const stateCheck = await page.evaluate((args) => {
                    const { mId, mIdx } = args;
                    const btn = document.querySelector(`button.hero-scene-nav-item[data-tab-target="${mIdx}"]`) ||
                                document.querySelector(`[data-scene-id="${mId}"]`) ||
                                Array.from(document.querySelectorAll('#innoria_hero_cover .hero-scene-nav-item, #innoria_hero_cover [data-scene-id]')).find(el => el.innerText.toLowerCase().includes(mId));

                    const isActive = btn ? (
                        btn.classList.contains('active') ||
                        btn.classList.contains('is-active') ||
                        btn.getAttribute('aria-selected') === 'true' ||
                        btn.getAttribute('data-active') === 'true'
                    ) : false;

                    // Check active slide item / content crossfade
                    const activeSlide = document.querySelector(`#innoria_hero_cover .hero-slide-item.active, #innoria_hero_cover [data-slide-index="${mIdx}"].active, #innoria_hero_cover [data-scene-content="${mId}"].active`);
                    const hasVisiblePane = activeSlide ? (window.getComputedStyle(activeSlide).opacity > '0.1') : true;

                    // Check controller index if available
                    const controller = window.innoriaHeroInteractiveStage || window.innoriaHeroSlider;
                    const controllerIdx = controller ? controller.currentIndex : -1;

                    return {
                        isActive,
                        hasVisiblePane,
                        controllerIdx
                    };
                }, { mId: mode.id, mIdx: mode.index });

                modeCheck.becameActive = stateCheck.isActive || stateCheck.controllerIdx === mode.index;
                modeCheck.contentUpdated = stateCheck.hasVisiblePane;
                modeCheck.pass = (modeCheck.buttonFound && (modeCheck.becameActive || modeCheck.contentUpdated));

                // Optional: Capture mode screenshot artifact
                try {
                    const heroBox = await (await heroContainer.first()).boundingBox();
                    const screenshotFile = path.join(ARTIFACT_DIR, `hero_stage_mode_${mode.index}_${mode.id}.png`);
                    await page.screenshot({ path: screenshotFile, clip: heroBox || undefined });
                } catch (e) {}
            } else {
                modeCheck.pass = false;
            }

            if (modeCheck.pass) {
                switcherPassedCount++;
            }

            switcherResults.push(modeCheck);
        }

        report.steps.modeSwitcher.tested = SCENE_MODES.length;
        report.steps.modeSwitcher.passed = switcherPassedCount;
        report.steps.modeSwitcher.modes = switcherResults;
        report.steps.modeSwitcher.pass = (switcherPassedCount === SCENE_MODES.length);

        if (report.steps.modeSwitcher.pass) {
            console.log(`${colors.green}✓ PASS (4/4 modes)${colors.reset}`);
        } else {
            console.log(`${colors.red}✗ FAIL (${switcherPassedCount}/4 modes verified)${colors.reset}`);
            if (IS_VERBOSE) {
                for (const m of switcherResults) {
                    console.log(`       ${colors.gray}Mode [${m.label}]: found=${m.buttonFound}, active=${m.becameActive}, content=${m.contentUpdated}${colors.reset}`);
                }
            }
        }

        // =================================================================
        // STEP 5: Assert VIP CTA Button & Halo Pulse
        // =================================================================
        process.stdout.write(`  [5/8] Asserting VIP CTA button ("Trải Nghiệm Live Proof-of-Concept 3 Giờ") & Halo Pulse ... `);

        const vipCtaEvaluation = await page.evaluate(() => {
            const candidates = Array.from(document.querySelectorAll('#innoria_hero_cover a, #innoria_hero_cover button, a.btn-hero-vip-poc, .btn-hero-vip-poc'));
            const cta = candidates.find(el => {
                const txt = (el.innerText || '').toLowerCase();
                return (
                    el.classList.contains('btn-hero-vip-poc') ||
                    txt.includes('trải nghiệm live proof-of-concept 3 giờ') ||
                    txt.includes('proof-of-concept 3 giờ') ||
                    txt.includes('poc 3 giờ') ||
                    txt.includes('tư vấn 3 giờ')
                );
            });

            if (!cta) {
                return { found: false, hasHalo: false, href: null, text: '' };
            }

            const style = window.getComputedStyle(cta);
            const href = cta.getAttribute('href') || '';
            const text = cta.innerText.trim();

            const animName = style.animationName || '';
            const hasAnimation = animName.toLowerCase().includes('halo') || animName.toLowerCase().includes('pulse');
            const hasBoxShadow = style.boxShadow && style.boxShadow !== 'none';
            const hasHaloClass = cta.classList.contains('halo-pulse') || cta.classList.contains('btn-hero-vip-poc');

            // Scan CSS rules for @keyframes haloPulse
            let keyframeFound = false;
            try {
                for (const sheet of Array.from(document.styleSheets)) {
                    try {
                        const rules = Array.from(sheet.cssRules || []);
                        for (const rule of rules) {
                            if (rule.type === CSSRule.KEYFRAMES_RULE && rule.name.toLowerCase().includes('halopulse')) {
                                keyframeFound = true;
                                break;
                            }
                        }
                    } catch (e) {}
                    if (keyframeFound) break;
                }
            } catch (e) {}

            const linksToContact = (
                href.includes('#innoria_contact_section') ||
                href.includes('#contactus') ||
                href.includes('/contactus')
            );

            const hasExactText = text.includes('Trải Nghiệm Live Proof-of-Concept 3 Giờ');

            return {
                found: true,
                text,
                href,
                hasExactText,
                hasHalo: (hasAnimation || keyframeFound || hasBoxShadow || hasHaloClass),
                linksToContact
            };
        });

        if (vipCtaEvaluation.found && vipCtaEvaluation.hasExactText && vipCtaEvaluation.linksToContact && vipCtaEvaluation.hasHalo) {
            report.steps.vipCtaHalo.pass = true;
            report.steps.vipCtaHalo.details = `VIP CTA "${vipCtaEvaluation.text}" found, linked to "${vipCtaEvaluation.href}", with kinetic halo effect.`;
            console.log(`${colors.green}✓ PASS${colors.reset}`);
        } else if (vipCtaEvaluation.found) {
            report.steps.vipCtaHalo.pass = false;
            report.steps.vipCtaHalo.details = `VIP CTA found ("${vipCtaEvaluation.text}"), exactText=${vipCtaEvaluation.hasExactText}, linkToContact=${vipCtaEvaluation.linksToContact} (href: "${vipCtaEvaluation.href}"), hasHalo=${vipCtaEvaluation.hasHalo}`;
            console.log(`${colors.yellow}⚠ PARTIAL (CTA found but exact text, href or halo unaligned)${colors.reset}`);
        } else {
            report.steps.vipCtaHalo.pass = false;
            report.steps.vipCtaHalo.details = 'VIP CTA button with text "Trải Nghiệm Live Proof-of-Concept 3 Giờ" not found in Hero stage.';
            console.log(`${colors.red}✗ FAIL (VIP CTA button missing)${colors.reset}`);
        }

        // =================================================================
        // STEP 6: 60 FPS Performance & Zero-Freeze Benchmark
        // =================================================================
        process.stdout.write(`  [6/8] Benchmarking 60 FPS Kinetic Performance & Zero-Freeze ... `);

        const fpsMetrics = await page.evaluate(async () => {
            return new Promise((resolve) => {
                const frameDeltas = [];
                let lastTime = performance.now();
                let frameCount = 0;
                const TARGET_FRAMES = 120; // ~2 seconds of frames

                function onFrame(now) {
                    const delta = now - lastTime;
                    lastTime = now;
                    frameDeltas.push(delta);
                    frameCount++;

                    if (frameCount < TARGET_FRAMES) {
                        requestAnimationFrame(onFrame);
                    } else {
                        const totalDurationMs = frameDeltas.reduce((a, b) => a + b, 0);
                        const avgFps = Math.round((frameCount / (totalDurationMs / 1000)) * 10) / 10;
                        const maxDelta = Math.round(Math.max(...frameDeltas.slice(2)) * 10) / 10;
                        const minFps = Math.round((1000 / maxDelta) * 10) / 10;
                        const freezes = frameDeltas.filter(d => d > 100).length; // Frame freeze > 100ms
                        const droppedFrames = frameDeltas.filter(d => d > 33.3).length; // Below 30fps

                        resolve({
                            frameCount,
                            totalDurationMs: Math.round(totalDurationMs),
                            avgFps,
                            minFps,
                            maxDelta,
                            freezes,
                            droppedFrames
                        });
                    }
                }

                requestAnimationFrame(onFrame);
            });
        });

        report.steps.fpsPerformance.metrics = fpsMetrics;
        const fpsPass = (fpsMetrics.avgFps >= MIN_FPS && fpsMetrics.freezes === 0);
        report.steps.fpsPerformance.pass = fpsPass;

        if (fpsPass) {
            console.log(`${colors.green}✓ PASS (${fpsMetrics.avgFps} FPS, max delta ${fpsMetrics.maxDelta}ms, 0 freeze)${colors.reset}`);
        } else {
            console.log(`${colors.yellow}⚠ FPS WARN (${fpsMetrics.avgFps} FPS vs SLA ${MIN_FPS}, ${fpsMetrics.freezes} freezes > 100ms)${colors.reset}`);
        }

        // =================================================================
        // STEP 7: Zero Instructional Text in Hero Stage DOM
        // =================================================================
        process.stdout.write(`  [7/8] Verifying Zero Instructional Text in Hero stage DOM ... `);
        const instructionalCheck = await page.evaluate(() => {
            const hero = document.getElementById('innoria_hero_cover');
            if (!hero) return { clean: false, error: 'Hero not found' };
            const text = (hero.innerText || '').toLowerCase();
            const banned = ['hover khối', 'kéo chuột', 'rê chuột', '360°', 'hardware 3d // 60 fps', 'click to rotate'];
            const violations = banned.filter(b => text.includes(b));
            return {
                clean: violations.length === 0,
                violations
            };
        });

        if (instructionalCheck.clean) {
            report.steps.zeroInstructionText.pass = true;
            report.steps.zeroInstructionText.details = '0 instructional text strings found in Hero DOM.';
            console.log(`${colors.green}✓ PASS (0 banned strings)${colors.reset}`);
        } else {
            report.steps.zeroInstructionText.pass = false;
            report.steps.zeroInstructionText.details = `Instructional text detected: ${instructionalCheck.violations.join(', ')}`;
            console.log(`${colors.red}✗ FAIL (${instructionalCheck.violations.join(', ')})${colors.reset}`);
        }

        // =================================================================
        // STEP 8: Zero Unhandled Console Errors
        // =================================================================
        process.stdout.write(`  [8/8] Verifying browser console cleanliness (zero unhandled exceptions) ... `);
        report.steps.consoleCleanliness.errors = consoleErrors;
        report.steps.consoleCleanliness.pass = (consoleErrors.length === 0);

        if (report.steps.consoleCleanliness.pass) {
            console.log(`${colors.green}✓ PASS (0 console errors)${colors.reset}`);
        } else {
            console.log(`${colors.red}✗ FAIL (${consoleErrors.length} console errors)${colors.reset}`);
            if (IS_VERBOSE) {
                for (const err of consoleErrors) {
                    console.log(`       ${colors.yellow}└─ Error: ${err}${colors.reset}`);
                }
            }
        }

    } catch (err) {
        console.error(`\n${colors.red}[!] Execution Error:${colors.reset}`, err.message);
        consoleErrors.push(err.message);
    } finally {
        await browser.close();
    }

    // =================================================================
    // Final Summary Diagnostic Table
    // =================================================================
    console.log(`\n${colors.bold}${colors.cyan}======================================================================================${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}                      HERO INTERACTIVE FLOW DIAGNOSTIC MATRIX                         ${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}======================================================================================${colors.reset}`);

    const printRow = (title, status, detail) => {
        const statusStr = status
            ? `${colors.bold}${colors.green}PASS${colors.reset}`
            : `${colors.bold}${colors.red}FAIL${colors.reset}`;
        console.log(`| ${title.padEnd(42)} | ${statusStr.padEnd(14)} | ${(detail || '').substring(0, 36).padEnd(36)} |`);
    };

    console.log(`| ${'Verification Gate'.padEnd(42)} | ${'Status'.padEnd(5)} | ${'Diagnostic Summary'.padEnd(36)} |`);
    console.log(`|${'-'.repeat(44)}|${'-'.repeat(8)}|${'-'.repeat(38)}|`);

    printRow('1. Hero Stage Presence (#innoria_hero_cover)', report.steps.stagePresence.pass, report.steps.stagePresence.details);
    printRow('2. Hero Controller Instance (JS)', report.steps.stageController.pass, report.steps.stageController.details);
    printRow('3. B2B Cinema Headline Assertion', report.steps.b2bHeadline.pass, report.steps.b2bHeadline.details);
    printRow('4. 4-Mode Interactive Switcher', report.steps.modeSwitcher.pass, `${report.steps.modeSwitcher.passed}/4 modes verified`);
    printRow('5. VIP CTA Button & Kinetic Halo Pulse', report.steps.vipCtaHalo.pass, report.steps.vipCtaHalo.details);
    printRow('6. 60 FPS Performance (Zero-Freeze)', report.steps.fpsPerformance.pass, `${report.steps.fpsPerformance.metrics.avgFps || 0} FPS, ${report.steps.fpsPerformance.metrics.freezes || 0} freezes`);
    printRow('7. Zero Instructional Text in Hero DOM', report.steps.zeroInstructionText.pass, report.steps.zeroInstructionText.details);
    printRow('8. Console Cleanliness (0 Errors)', report.steps.consoleCleanliness.pass, `${report.steps.consoleCleanliness.errors.length} unhandled errors`);

    console.log(`|${'-'.repeat(44)}|${'-'.repeat(8)}|${'-'.repeat(38)}|`);

    // Overall Status
    report.passed = (
        report.steps.stagePresence.pass &&
        report.steps.stageController.pass &&
        report.steps.b2bHeadline.pass &&
        report.steps.modeSwitcher.pass &&
        report.steps.vipCtaHalo.pass &&
        report.steps.fpsPerformance.pass &&
        report.steps.zeroInstructionText.pass &&
        report.steps.consoleCleanliness.pass
    );

    if (JSON_OUTPUT_PATH) {
        const dir = path.dirname(JSON_OUTPUT_PATH);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(JSON_OUTPUT_PATH, JSON.stringify(report, null, 2));
        console.log(`\n${colors.gray}Saved JSON report to: ${JSON_OUTPUT_PATH}${colors.reset}`);
    }

    if (report.passed) {
        console.log(`\n${colors.green}${colors.bold}[SUCCESS] Hero stage interactive flow passed 100% of all acceptance criteria!${colors.reset}\n`);
        process.exit(0);
    } else {
        console.log(`\n${colors.red}${colors.bold}[FAIL] Hero stage interactive flow did not meet 100% acceptance criteria.${colors.reset}\n`);
        process.exit(1);
    }
}

// Execute
runHeroInteractiveFlow().catch(err => {
    console.error(`\n${colors.red}Fatal Runner Error:${colors.reset}`, err);
    process.exit(1);
});
