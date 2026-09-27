const { chromium } = require('playwright-core');

(async () => {
    const browser = await chromium.launch({
        executablePath: '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    
    console.log("Navigating to http://localhost:28069 ...");
    await page.goto('http://localhost:28069/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Hide sticky header so it never occludes section titles
    await page.evaluate(() => {
        const header = document.querySelector('header');
        if (header) header.style.display = 'none';
        const topNav = document.querySelector('.o_header_standard');
        if (topNav) topNav.style.display = 'none';
    });

    const sections = [
        { id: 'insilos_hero_showcase', name: 'sec1_hero' },
        { id: 'contrast-hook', name: 'sec2_contrast' },
        { id: 'proof-anchors', name: 'sec3_proof' },
        { selector: '.s_banner[data-name="Compliance &amp; Standards Banner"], .s_banner', name: 'sec4_banner' },
        { id: 'pillars', name: 'sec5_pillars' },
        { selector: '.s_tabs[data-name="Interactive Solution Matrix"]', name: 'sec6_matrix' },
        { selector: '.s_features[data-name="Compliance Dossier Spec Matrix"]', name: 'sec7_dossier' },
        { selector: '.s_process_steps[data-name="Multi-Agent Pipeline"]', name: 'sec8_pipeline' },
        { id: 'insilos_code_studio', name: 'sec9_code_studio' },
        { selector: '.s_text_image[data-name="C3.ai Terminal Command Console"]', name: 'sec10_terminal' },
        { selector: '.s_numbers[data-name="C3.ai ROI Calculator"]', name: 'sec11_roi' },
        { selector: '.s_three_columns[data-name="Three-Tier Runtime Architecture"]', name: 'sec12_tiers' },
        { selector: '.s_timeline[data-name="Rapid Pilot Playbook"]', name: 'sec13_playbook' },
        { id: 'industries', name: 'sec14_industries' },
        { selector: '.s_card[data-name="Enterprise Sovereign Security"]', name: 'sec15_security' },
        { selector: '.s_quotes_carousel', name: 'sec16_carousel' },
        { selector: '.s_faq_collapse', name: 'sec17_faq' },
    ];

    for (const sec of sections) {
        try {
            let el;
            if (sec.id) {
                el = await page.$('#' + sec.id);
            } else if (sec.selector) {
                el = await page.$(sec.selector);
            }
            if (el) {
                const path = `/tmp/verified_${sec.name}.png`;
                await el.screenshot({ path });
                console.log(`Saved screenshot: ${path}`);
            } else {
                console.warn(`Could not find element for ${sec.name}`);
            }
        } catch (e) {
            console.error(`Error capturing ${sec.name}:`, e.message);
        }
    }

    await browser.close();
    console.log("Visual verification capture complete!");
})();
