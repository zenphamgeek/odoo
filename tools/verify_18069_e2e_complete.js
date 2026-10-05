const { chromium } = require('playwright');

(async () => {
    console.log('--- Starting Comprehensive 18069 E2E Verification ---');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    const failedRequests = [];
    const consoleErrors = [];

    page.on('response', response => {
        const url = response.url();
        const status = response.status();
        const headers = response.headers();
        const contentLength = headers['content-length'];
        if (url.includes('/web/assets/')) {
            console.log(`[ASSET] ${status} ${url.split('/').slice(-2).join('/')} (${contentLength || 'chunked'} bytes)`);
        }
        if (status >= 400) {
            failedRequests.push({ url, status });
        }
    });

    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('[PAGE ERROR]', msg.text());
            consoleErrors.push(msg.text());
        }
    });

    // 1. Test unauthenticated /insilos
    console.log('\n[Phase 1] Navigating to http://localhost:18069/insilos (Unauthenticated)...');
    const response = await page.goto('http://localhost:18069/insilos', { waitUntil: 'networkidle', timeout: 45000 });
    console.log('Final URL after redirect:', page.url());
    console.log('HTTP Status:', response.status());

    await page.waitForTimeout(2000);

    const canvas = await page.$('#insilosLoginDigitalTwinCanvas');
    console.log('Canvas #insilosLoginDigitalTwinCanvas present:', !!canvas);

    const unauthPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/verify_18069_unauth_fixed.png';
    await page.screenshot({ path: unauthPath, fullPage: true });
    console.log('Saved unauthenticated screenshot:', unauthPath);

    // 2. Perform Login
    console.log('\n[Phase 2] Performing Login on http://localhost:18069...');
    const loginInput = await page.$('input[name="login"]');
    const passwordInput = await page.$('input[name="password"]');
    const submitBtn = await page.$('button[type="submit"]');

    if (loginInput && passwordInput && submitBtn) {
        await loginInput.fill('admin');
        await passwordInput.fill('admin');
        console.log('Submitting credentials (admin/admin)...');
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle', timeout: 60000 }),
            submitBtn.click()
        ]);
        console.log('Logged in! Current URL:', page.url());
    } else {
        console.error('Login form elements not found!');
    }

    // 3. Verify Authenticated WebClient
    console.log('\n[Phase 3] Verifying Authenticated WebClient State...');
    await page.waitForTimeout(3000);

    const navbar = await page.$('.o_navbar');
    const homeMenu = await page.$('.o_home_menu');
    const appIcons = await page.$$('.o_app');
    const webClient = await page.$('.o_web_client');

    console.log('.o_web_client mounted:', !!webClient);
    console.log('.o_navbar mounted:', !!navbar);
    console.log('.o_home_menu mounted:', !!homeMenu);
    console.log('App launcher count:', appIcons.length);

    // Verify background color is not black screen
    const bodyBg = await page.evaluate(() => {
        const body = document.body;
        return window.getComputedStyle(body).backgroundColor;
    });
    console.log('Body background color:', bodyBg);

    const authPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/verify_18069_auth_fixed.png';
    await page.screenshot({ path: authPath, fullPage: true });
    console.log('Saved authenticated screenshot:', authPath);

    // Summary
    console.log('\n--- VERIFICATION SUMMARY ---');
    console.log('Failed HTTP requests:', failedRequests.length);
    console.log('Console errors:', consoleErrors.length);
    if (consoleErrors.length > 0) {
        console.log('Error samples:', consoleErrors.slice(0, 3));
    }
    console.log('Apps visible:', appIcons.length);
    console.log('Black screen resolved:', !!homeMenu && appIcons.length > 50);

    await browser.close();
})();
