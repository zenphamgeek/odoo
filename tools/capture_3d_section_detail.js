const { chromium } = require('playwright');
const path = require('path');

async function main() {
    const artifactDir = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage({
        viewport: { width: 1440, height: 1200 },
        deviceScaleFactor: 2
    });

    await page.goto('https://innoria.insilos.com/solutions', { waitUntil: 'networkidle', timeout: 35000 });

    const comp = await page.$('#erp_shift_3d_component');
    if (comp) {
        const sec = await page.evaluateHandle(() => document.querySelector('#erp_shift_3d_component').closest('section'));
        await sec.asElement().scrollIntoViewIfNeeded();
        await page.waitForTimeout(2000);

        // Capture table specifically
        const table = await page.$('#erp_shift_3d_component ~ .row, section:has(#erp_shift_3d_component) .table-responsive');
        if (table) {
            await table.screenshot({ path: path.join(artifactDir, '3d_erp_shift_table_fullwidth.png') });
            console.log('[✓] Captured fullwidth table screenshot');
        }

        // Capture whole section viewport
        await page.screenshot({
            path: path.join(artifactDir, '3d_erp_shift_section_viewport.png'),
            fullPage: false
        });
        console.log('[✓] Captured section in viewport');
    }

    await browser.close();
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
