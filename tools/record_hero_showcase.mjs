import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const RECORDINGS_DIR = '/home/zen/.gemini/antigravity/brain/fb5ae76a-1408-4c4b-a022-402bc164561b/recordings';
if (!fs.existsSync(RECORDINGS_DIR)) {
    fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
}

async function recordShowcase() {
    console.log("🚀 Starting Playwright Video Recording of C3.ai Pexels Showcase...");
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--autoplay-policy=no-user-gesture-required']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        recordVideo: {
            dir: RECORDINGS_DIR,
            size: { width: 1440, height: 900 }
        }
    });

    const page = await context.newPage();
    console.log("🌐 Navigating to http://localhost:28069/ ...");
    await page.goto('http://localhost:28069/', { waitUntil: 'networkidle' });
    await page.waitForSelector('#insilos_hero_showcase', { timeout: 10000 });

    console.log("🎬 Recording Act 1: Industrial Robotics & Autonomous SCADA (4s)...");
    await page.waitForTimeout(4000);

    console.log("👉 Switching to Act 2: Cái Mép - Thị Vải Maritime Port (4s)...");
    await page.click('.ins-stepper-tab[data-act="2"]');
    await page.waitForTimeout(4000);

    console.log("👉 Switching to Act 3: Mission Control NOC & Knowledge Graph (4s)...");
    await page.click('.ins-stepper-tab[data-act="3"]');
    await page.waitForTimeout(4000);

    console.log("👉 Switching to Act 4: Offshore Wind Turbines & Clean Energy (4s)...");
    await page.click('.ins-stepper-tab[data-act="4"]');
    await page.waitForTimeout(4000);

    console.log("👉 Returning to Act 1 to demonstrate loop (3s)...");
    await page.click('.ins-stepper-tab[data-act="1"]');
    await page.waitForTimeout(3000);

    const videoPath = await page.video().path();
    await context.close();
    await browser.close();

    console.log(`🎥 Raw recording saved at: ${videoPath}`);
    const finalMp4 = path.join(RECORDINGS_DIR, 'pexels_c3_hero_showcase.mp4');
    
    // Convert to web-friendly MP4 with ffmpeg
    const { execSync } = await import('child_process');
    execSync(`ffmpeg -y -i "${videoPath}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "${finalMp4}"`);
    console.log(`✅ Final MP4 saved at: ${finalMp4}`);
}

recordShowcase().catch(err => {
    console.error("❌ Recording error:", err);
    process.exit(1);
});
