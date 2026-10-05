const { chromium } = require('playwright');

(async () => {
    console.log('[*] Launching Chromium to capture all sections...');
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    const artifactDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

    // 1. Hero Cover with 3D Topology
    await page.screenshot({ path: `${artifactDir}/innoria_sec_hero.png` });
    console.log('[✓] Captured hero section');

    // 2. Client Trust Strip
    const elClients = await page.$('.innoria-client-strip');
    if (elClients) {
        await elClients.screenshot({ path: `${artifactDir}/innoria_sec_clients.png` });
        console.log('[✓] Captured clients strip');
    }

    // 3. Platform & Architecture Diagram
    const elPlatform = await page.$('#platform');
    if (elPlatform) {
        await elPlatform.scrollIntoViewIfNeeded();
        await page.waitForTimeout(600);
        await page.screenshot({ path: `${artifactDir}/innoria_sec_platform.png` });
        console.log('[✓] Captured platform section');
    }

    // 4. Cadence & Ecosystem
    const elEcosystem = await page.$('.innoria-card-ecosystem');
    if (elEcosystem) {
        await elEcosystem.scrollIntoViewIfNeeded();
        await page.waitForTimeout(600);
        await page.screenshot({ path: `${artifactDir}/innoria_sec_ecosystem.png` });
        console.log('[✓] Captured ecosystem section');
    }

    // 5. Key Services (AIaaS, Digital Transformation, Dev, Blockchain)
    const elServices = await page.$('#services');
    if (elServices) {
        await elServices.scrollIntoViewIfNeeded();
        await page.waitForTimeout(600);
        await page.screenshot({ path: `${artifactDir}/innoria_sec_services.png` });
        console.log('[✓] Captured services section');
    }

    // 6. Industry Solutions
    const elSolutions = await page.$('#solutions');
    if (elSolutions) {
        await elSolutions.scrollIntoViewIfNeeded();
        await page.waitForTimeout(600);
        await page.screenshot({ path: `${artifactDir}/innoria_sec_solutions.png` });
        console.log('[✓] Captured solutions section');
    }

    // 7. Footer (Element Screenshot)
    const elFooter = await page.$('.innoria-footer');
    if (elFooter) {
        await elFooter.scrollIntoViewIfNeeded();
        await page.waitForTimeout(600);
        await elFooter.screenshot({ path: `${artifactDir}/innoria_sec_footer.png` });
        console.log('[✓] Captured element footer section');
    }

    // 8. Full page screenshot
    await page.screenshot({ path: `${artifactDir}/innoria_3d_elevated_fullpage.png`, fullPage: true });
    console.log('[✓] Captured complete fullpage screenshot');

    await browser.close();
    console.log('[*] All section captures completed successfully!');
})();
