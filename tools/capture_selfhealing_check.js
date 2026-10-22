const { chromium } = require('/home/zen/O20/node_modules/playwright');

(async () => {
    const browser = await chromium.launch({
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader']
    });
    const page = await browser.newPage({ viewport: { width: 1440, height: 2400 } });
    await page.goto('http://localhost:7788', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);

    // Find heading containing 'Self-Healing & Capacity'
    const heading = await page.getByText('Self-Healing & Capacity', { exact: false }).first();
    if (heading) {
        console.log('Found heading "Self-Healing & Capacity"!');
        // Get the parent card/section
        const section = await heading.evaluateHandle(el => el.closest('.card, .panel, section, div.topology-card, div') || el.parentElement);
        const text = await section.asElement().innerText();
        console.log('Section content:\n' + text);
        await section.asElement().screenshot({ path: '/tmp/selfhealing_section.png' });
        console.log('Saved section screenshot to /tmp/selfhealing_section.png');
    } else {
        console.log('Heading not found');
    }
    await browser.close();
})();
