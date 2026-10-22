const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const OUT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/artifacts';
if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
}

(async () => {
    console.log('=== STARTING PLAYWRIGHT VERIFICATION: ELEGANT BUTTONS & SMART TITLES ===');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2
    });

    const page = await context.newPage();

    // 1. VERIFY HOMEPAGE (NAVBAR, GRC BUTTONS, TITLES)
    console.log('[*] Navigating to https://innoria.com/ ...');
    await page.goto('https://innoria.com/', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Navbar Capture
    const navbar = await page.$('.ins-navbar-container, header.innoria-navbar, #innoria_navbar');
    if (navbar) {
        await navbar.screenshot({ path: path.join(OUT_DIR, 'navbar_luxury_buttons.png') });
        console.log('[✓] Saved navbar screenshot to navbar_luxury_buttons.png');
    }

    // Verify Navbar CTA & Lang Switcher CSS
    const navStyles = await page.evaluate(() => {
        const cta = document.querySelector('.btn-innoria-nav');
        const langGroup = document.querySelector('.ins-lang-group');
        const activeLang = document.querySelector('.ins-lang-pill.is-active, .ins-lang-pill.active');
        const indicator = document.querySelector('.ins-nav-indicator');

        return {
            cta: cta ? {
                background: window.getComputedStyle(cta).background,
                boxShadow: window.getComputedStyle(cta).boxShadow,
                borderRadius: window.getComputedStyle(cta).borderRadius,
                color: window.getComputedStyle(cta).color
            } : null,
            langGroup: langGroup ? {
                background: window.getComputedStyle(langGroup).background,
                backdropFilter: window.getComputedStyle(langGroup).backdropFilter || window.getComputedStyle(langGroup).webkitBackdropFilter,
                borderRadius: window.getComputedStyle(langGroup).borderRadius
            } : null,
            activeLang: activeLang ? {
                background: window.getComputedStyle(activeLang).background,
                color: window.getComputedStyle(activeLang).color,
                borderRadius: window.getComputedStyle(activeLang).borderRadius
            } : null,
            indicator: indicator ? {
                backdropFilter: window.getComputedStyle(indicator).backdropFilter || window.getComputedStyle(indicator).webkitBackdropFilter,
                borderRadius: window.getComputedStyle(indicator).borderRadius
            } : null
        };
    });

    console.log('Navbar evaluated styles:', JSON.stringify(navStyles, null, 2));

    // Scroll to GRC Trade & Ops section
    const grcSection = await page.$('#innoria_trade_compliance_interactive, #innoria_ops_compliance_interactive');
    if (grcSection) {
        await grcSection.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);
        await grcSection.screenshot({ path: path.join(OUT_DIR, 'grc_luxury_buttons.png') });
        console.log('[✓] Saved GRC interactive section to grc_luxury_buttons.png');
    }

    // 2. VERIFY /industries (TITLES & BUTTONS)
    console.log('[*] Navigating to https://innoria.com/industries ...');
    await page.goto('https://innoria.com/industries', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    const industriesTitles = await page.evaluate(() => {
        const h1 = document.querySelector('h1');
        const h2List = Array.from(document.querySelectorAll('section h2')).map(h => ({
            text: h.innerText.replace(/\n/g, ' '),
            textWrap: window.getComputedStyle(h).textWrap,
            lineHeight: window.getComputedStyle(h).lineHeight,
            hasBr: h.querySelectorAll('br').length > 0
        }));

        const heroButtons = Array.from(document.querySelectorAll('.ins-hero-stage a.btn, .ins-industries-stage a.btn')).map(b => ({
            text: b.innerText.trim(),
            className: b.className,
            background: window.getComputedStyle(b).background,
            boxShadow: window.getComputedStyle(b).boxShadow,
            borderRadius: window.getComputedStyle(b).borderRadius
        }));

        return {
            h1: h1 ? {
                text: h1.innerText.replace(/\n/g, ' '),
                textWrap: window.getComputedStyle(h1).textWrap,
                hasBr: h1.querySelectorAll('br').length > 0
            } : null,
            h2List,
            heroButtons
        };
    });

    console.log('Industries evaluation:', JSON.stringify(industriesTitles, null, 2));

    // Capture Industries Hero & Command Stage
    const indHero = await page.$('.ins-industries-stage section');
    if (indHero) {
        await indHero.screenshot({ path: path.join(OUT_DIR, 'industries_hero_titles_and_buttons.png') });
        console.log('[✓] Saved industries hero screenshot.');
    }

    const pilotCta = await page.$('#vision-pilot');
    if (pilotCta) {
        await pilotCta.scrollIntoViewIfNeeded();
        await page.waitForTimeout(800);
        await pilotCta.screenshot({ path: path.join(OUT_DIR, 'industries_pilot_cta_luxury.png') });
        console.log('[✓] Saved industries pilot CTA screenshot.');
    }

    await browser.close();
    console.log('=== PLAYWRIGHT VERIFICATION FINISHED SUCCESSFULLY ===');
})();
