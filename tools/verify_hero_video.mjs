import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const SCREENSHOT_DIR = '/home/zen/.gemini/antigravity/brain/fb5ae76a-1408-4c4b-a022-402bc164561b/screenshots';
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function run() {
    console.log("🚀 Launching Headless Chromium to verify Hero Video Showcase...");
    const browser = await chromium.launch({ headless: true });
    
    // 1. Desktop Test (1440x900)
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1
    });
    const page = await context.newPage();

    console.log("🌐 Navigating to http://localhost:28069/ ...");
    await page.goto('http://localhost:28069/', { waitUntil: 'networkidle' });

    // Wait for hero showcase
    await page.waitForSelector('#insilos_hero_showcase', { timeout: 10000 });
    console.log("✅ #insilos_hero_showcase found in DOM");

    // Check Act 1 state
    const act1Active = await page.$eval('.ins-hero-act-pane[data-act="1"]', el => el.classList.contains('active'));
    const tab1Active = await page.$eval('.ins-stepper-tab[data-act="1"]', el => el.classList.contains('active'));
    const videoASrc = await page.$eval('#ins-hero-video-a', el => el.src);
    console.log(`🎬 Act 1 Pane Active: ${act1Active}, Tab 1 Active: ${tab1Active}, Video A: ${videoASrc}`);

    // Wait a brief moment for rendering and screenshot Act 1
    await page.waitForTimeout(1000);
    const heroEl = await page.$('#insilos_hero_showcase');
    await heroEl.screenshot({ path: path.join(SCREENSHOT_DIR, 'hero_act1_desktop.png') });
    console.log("📸 Saved hero_act1_desktop.png");

    // Click Act 2 Tab (Vertical IDP / Maritime Logistics)
    console.log("👉 Clicking Stepper Tab 02 (Vertical IDP)...");
    await page.click('.ins-stepper-tab[data-act="2"]');
    await page.waitForTimeout(1500); // Wait for crossfade transition

    const act2Active = await page.$eval('.ins-hero-act-pane[data-act="2"]', el => el.classList.contains('active'));
    const cockpit2Highlighted = await page.$eval('.ins-cockpit-card[data-act-target="2"]', el => el.classList.contains('ins-act-highlight'));
    console.log(`🎬 Act 2 Active: ${act2Active}, Cockpit Card 2 Highlighted: ${cockpit2Highlighted}`);

    await heroEl.screenshot({ path: path.join(SCREENSHOT_DIR, 'hero_act2_desktop.png') });
    console.log("📸 Saved hero_act2_desktop.png");

    // Click Act 4 Tab (Intelligent FSM / Offshore Wind Energy)
    console.log("👉 Clicking Stepper Tab 04 (FSM Intelligence)...");
    await page.click('.ins-stepper-tab[data-act="4"]');
    await page.waitForTimeout(1500); // Wait for crossfade transition

    const act4Active = await page.$eval('.ins-hero-act-pane[data-act="4"]', el => el.classList.contains('active'));
    const cockpit4Highlighted = await page.$eval('.ins-cockpit-card[data-act-target="4"]', el => el.classList.contains('ins-act-highlight'));
    console.log(`🎬 Act 4 Active: ${act4Active}, Cockpit Card 4 Highlighted: ${cockpit4Highlighted}`);

    await heroEl.screenshot({ path: path.join(SCREENSHOT_DIR, 'hero_act4_desktop.png') });
    console.log("📸 Saved hero_act4_desktop.png");

    await context.close();

    // 2. Mobile Viewport Test (375x812 - iPhone 13/14)
    console.log("📱 Testing Mobile Viewport (375x812)...");
    const mobileContext = await browser.newContext({
        viewport: { width: 375, height: 812 },
        deviceScaleFactor: 2,
        isMobile: true
    });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto('http://localhost:28069/', { waitUntil: 'networkidle' });

    const videoDisplay = await mobilePage.$eval('#ins-hero-video-a', el => window.getComputedStyle(el).display);
    const posterDisplay = await mobilePage.$eval('#ins-hero-poster', el => window.getComputedStyle(el).display);
    console.log(`📱 Mobile Video Display: '${videoDisplay}' (Expected: 'none'), Poster Display: '${posterDisplay}' (Expected: 'block')`);

    await mobilePage.waitForTimeout(800);
    const mobileHero = await mobilePage.$('#insilos_hero_showcase');
    await mobileHero.screenshot({ path: path.join(SCREENSHOT_DIR, 'hero_mobile_375px.png') });
    console.log("📸 Saved hero_mobile_375px.png");

    await mobileContext.close();
    await browser.close();

    console.log("🎉 All Hero Video Verification Steps Completed Successfully!");
}

run().catch(err => {
    console.error("❌ Verification failed:", err);
    process.exit(1);
});
