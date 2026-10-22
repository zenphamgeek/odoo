const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        ignoreHTTPSErrors: true
    });

    // Add session cookie
    const session_id = 'WToAegmmLn8VoB6oHlTVKHy9ujIK6M_v8uKyqdj2RR6DmMsdjRky9AyAKz8QvTJ_NGn-_tD6-OyAzrwXZ77oWA';
    await context.addCookies([
        {
            name: 'session_id',
            value: session_id,
            domain: '.innoria.com',
            path: '/',
            httpOnly: true,
            secure: true,
            sameSite: 'Lax'
        },
        {
            name: 'insilos_session_id',
            value: session_id,
            domain: '.innoria.com',
            path: '/',
            httpOnly: true,
            secure: true,
            sameSite: 'Lax'
        }
    ]);

    const page = await context.newPage();
    const errors = [];
    const logs = [];

    page.on('console', msg => {
        logs.push(`[${msg.type()}] ${msg.text()}`);
    });

    page.on('pageerror', err => {
        errors.push(`PAGE ERROR: ${err.message}`);
        console.error('PAGE ERROR:', err.message);
    });

    console.log('Navigating to https://innoria.com/insilos...');
    try {
        const response = await page.goto('https://innoria.com/insilos', {
            waitUntil: 'domcontentloaded',
            timeout: 15000
        });
        console.log('Response status:', response ? response.status() : 'null');
    } catch (e) {
        console.log('Navigation event:', e.message);
    }

    // Wait 5 seconds for OWL to mount
    await page.waitForTimeout(5000);

    const bodyClass = await page.evaluate(() => document.body ? document.body.className : 'no body');
    const rootHtml = await page.evaluate(() => document.documentElement.outerHTML.slice(0, 500));
    const owlRoot = await page.evaluate(() => {
        const client = document.querySelector('.o_web_client');
        const homeMenu = document.querySelector('.o_home_menu');
        const navbar = document.querySelector('.o_navbar, .o_main_navbar');
        const actionManager = document.querySelector('.o_action_manager');
        const apps = document.querySelectorAll('.o_app');
        return {
            hasWebClient: !!client,
            hasHomeMenu: !!homeMenu,
            hasNavbar: !!navbar,
            hasActionManager: !!actionManager,
            appCount: apps.length,
            bodyText: document.body.innerText.slice(0, 200)
        };
    });

    console.log('Body Class:', bodyClass);
    console.log('OWL Root Status:', JSON.stringify(owlRoot, null, 2));
    console.log('Total Console Logs:', logs.length);
    console.log('Total Errors:', errors.length);
    if (errors.length > 0) {
        console.log('Errors:', errors);
    }

    const artifactPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/authenticated_insilos_verified.png';
    await page.screenshot({ path: artifactPath, fullPage: true });
    console.log('Screenshot saved to:', artifactPath);

    await browser.close();
    process.exit(errors.length > 0 ? 1 : 0);
})();
