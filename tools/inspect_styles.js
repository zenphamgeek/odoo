const { chromium } = require('playwright');

async function inspect() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    
    await page.goto('https://innokafe.insilos.com/', { waitUntil: 'load' });
    await page.waitForTimeout(2000);

    const info = await page.evaluate(() => {
        const sheets = Array.from(document.styleSheets).map(s => {
            return {
                href: s.href,
                rulesCount: (() => { try { return s.cssRules.length; } catch (e) { return e.message; } })()
            };
        });

        const h1 = document.querySelector('h1');
        const h1Style = h1 ? {
            fontFamily: window.getComputedStyle(h1).fontFamily,
            fontSize: window.getComputedStyle(h1).fontSize,
            color: window.getComputedStyle(h1).color
        } : null;

        const container = document.querySelector('.container');
        const containerStyle = container ? {
            display: window.getComputedStyle(container).display,
            maxWidth: window.getComputedStyle(container).maxWidth,
            paddingLeft: window.getComputedStyle(container).paddingLeft,
            marginLeft: window.getComputedStyle(container).marginLeft,
            marginRight: window.getComputedStyle(container).marginRight
        } : null;

        const skipLink = document.querySelector('.o_skip_to_content');
        const skipStyle = skipLink ? {
            display: window.getComputedStyle(skipLink).display,
            position: window.getComputedStyle(skipLink).position,
            transform: window.getComputedStyle(skipLink).transform,
            opacity: window.getComputedStyle(skipLink).opacity
        } : null;

        const btnPrimary = document.querySelector('.btn-primary');
        const btnStyle = btnPrimary ? {
            background: window.getComputedStyle(btnPrimary).background,
            borderRadius: window.getComputedStyle(btnPrimary).borderRadius,
            padding: window.getComputedStyle(btnPrimary).padding
        } : null;

        return { sheets, h1Style, containerStyle, skipStyle, btnStyle };
    });

    console.log(JSON.stringify(info, null, 2));
    await browser.close();
}

inspect().catch(console.error);
