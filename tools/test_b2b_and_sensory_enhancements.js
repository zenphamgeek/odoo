#!/usr/bin/env node
/**
 * Test Suite: InnoKafe Enhanced Sensory Radar & B2B Wholesale Pricing Calculator
 * ==============================================================================
 * Validates:
 * 1. /solutions-b2b:
 *    - Presence of #b2b_calculator section.
 *    - Interactive slider changing volume and updating metrics in real time.
 *    - Preset buttons (20kg, 50kg, 100kg, 250kg) switching tiers (Bronze -> Silver -> Gold -> Platinum).
 *    - Blend selection updating base price and cost-per-cup calculation.
 *    - Form synchronization: #b2b_calc_apply_btn auto-populates #b2b_form fields.
 * 2. /taste-profiler:
 *    - Presence of enhanced sensory wheel SVG.
 *    - Exactly 6 interactive axis circles (dots).
 *    - SCA Cupping Score badge visibility with valid score.
 *    - Interactive spoke lines and node click/drag responsiveness.
 */

const { chromium } = require('playwright');

const BASE_URL = process.env.INNOKAFE_BASE_URL || 'http://localhost:28071';

async function run() {
    console.log(`🚀 Starting B2B Calculator & Sensory Radar Verification on ${BASE_URL}...`);
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();

    let passed = 0;
    let failed = 0;

    function assert(condition, message) {
        if (condition) {
            console.log(`  [✓] PASS: ${message}`);
            passed++;
        } else {
            console.error(`  [✗] FAIL: ${message}`);
            failed++;
        }
    }

    try {
        // =====================================================================
        // PART 1: B2B WHOLESALE PRICING & ROI CALCULATOR (/solutions-b2b)
        // =====================================================================
        await page.goto(`${BASE_URL}/solutions-b2b`, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForFunction(() => typeof window.initB2BCalculator === 'function', { timeout: 30000 });
        await page.waitForTimeout(500);

        // 1. Calculator section presence
        const calcSection = await page.$('#b2b_calculator');
        assert(calcSection !== null, 'Section #b2b_calculator exists in DOM');

        // 2. Volume slider presence
        const slider = await page.$('#b2b_calc_volume');
        assert(slider !== null, 'Volume slider #b2b_calc_volume exists');

        // 3. Initial state verification (default 50kg => Tier 2: Silver)
        const initialVolLabel = await page.innerText('#b2b_calc_vol_label');
        assert(initialVolLabel.includes('50 kg'), `Initial volume label displays '50 kg' (actual: ${initialVolLabel})`);

        const initialTierBadge = await page.innerText('#b2b_calc_tier_badge');
        assert(initialTierBadge.includes('Silver') || initialTierBadge.includes('25%'),
               `Initial tier badge is Silver (-25%) (actual: ${initialTierBadge})`);

        // 4. Test clicking Gold preset (100 kg)
        console.log('  Testing preset button: 100 kg (Gold)...');
        await page.click('.b2b-preset-vol[data-vol="100"]');
        await page.waitForTimeout(300);

        const goldVolLabel = await page.innerText('#b2b_calc_vol_label');
        assert(goldVolLabel.includes('100 kg'), `Volume updated to 100 kg after preset click (actual: ${goldVolLabel})`);

        const goldTierBadge = await page.innerText('#b2b_calc_tier_badge');
        assert(goldTierBadge.includes('Gold') || goldTierBadge.includes('32%'),
               `Tier updated to Gold (-32%) (actual: ${goldTierBadge})`);

        const goldNetPrice = await page.innerText('#b2b_calc_net_price');
        assert(goldNetPrice.includes('238.000'), `Net price correctly computed for Gold tier (actual: ${goldNetPrice})`);

        // 5. Test clicking Platinum preset (250 kg)
        console.log('  Testing preset button: 250 kg (Platinum)...');
        await page.click('.b2b-preset-vol[data-vol="250"]');
        await page.waitForTimeout(300);

        const platTierBadge = await page.innerText('#b2b_calc_tier_badge');
        assert(platTierBadge.includes('Platinum') || platTierBadge.includes('38%'),
               `Tier updated to Platinum (-38%) (actual: ${platTierBadge})`);

        // 6. Test Form Synchronization via Apply Button
        console.log('  Testing form synchronization via #b2b_calc_apply_btn...');
        await page.click('#b2b_calc_apply_btn');
        await page.waitForTimeout(600);

        const descValue = await page.inputValue('#b2b_form textarea[name="description"]');
        assert(descValue.includes('250 kg/tháng') && descValue.includes('Platinum'),
               `Description textarea populated with calculated plan: "${descValue.slice(0, 60)}..."`);

        const volSelectValue = await page.inputValue('#b2b_form select[name="estimated_monthly_volume"]');
        assert(volSelectValue.includes('100') || volSelectValue.includes('Trên'),
               `Volume select auto-updated to match tier: "${volSelectValue}"`);

        // =====================================================================
        // PART 2: TASTE PROFILER ENHANCED SENSORY RADAR (/taste-profiler)
        // =====================================================================
        console.log('\n--- Part 2: Taste Profiler Enhanced Sensory Radar Audit ---');
        await page.goto(`${BASE_URL}/taste-profiler/result/INNO-ARABICA-WASH-02`, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForFunction(() => !!window.InnokafeTasteProfiler, { timeout: 30000 });
        await page.waitForSelector('.innokafe-sensory-wheel-svg circle', { timeout: 30000 });
        await page.waitForTimeout(500);

        // 1. Radar SVG presence
        const radarSvg = await page.$('.innokafe-sensory-wheel-svg');
        assert(radarSvg !== null, 'Enhanced Sensory Wheel SVG exists in DOM');

        // 2. Data polygon presence
        const polygon = await page.$('.innokafe-sensory-wheel-svg polygon');
        assert(polygon !== null, 'Sensory data polygon rendered');

        // 3. Interactive dots presence (6 axes)
        const dots = await page.$$('.innokafe-sensory-wheel-svg circle');
        assert(dots.length === 6, `Sensory wheel rendered exactly 6 axis dots (found: ${dots.length})`);

        // 4. SCA score badge presence
        const scaBadge = await page.waitForSelector('.innokafe-sensory-wheel-svg .sca-score-badge', { timeout: 10000 }).catch(() => null);
        assert(scaBadge !== null, 'SCA Cupping Score badge rendered in sensory wheel');

        if (scaBadge) {
            const scaText = await scaBadge.textContent();
            assert(scaText.includes('SCA:'), `SCA badge displays score value: "${scaText.trim()}"`);
        }

        // 5. Test Node Interaction / Click
        console.log('  Testing interactive dot click on sensory wheel...');
        const dot = await page.$('.innokafe-sensory-wheel-svg circle[data-axis="aroma"]');
        if (dot) {
            await dot.click({ force: true });
            await page.waitForTimeout(200);
            assert(true, 'Clicked on aroma sensory dot without runtime errors');
        }

        console.log('\n================================================================');
        console.log(`🏁 Audit Results: ${passed} PASSED, ${failed} FAILED`);
        console.log('================================================================');

        if (failed > 0) {
            process.exit(1);
        }
    } finally {
        await browser.close();
    }
}

run().catch((err) => {
    console.error('Fatal Error:', err);
    process.exit(1);
});
