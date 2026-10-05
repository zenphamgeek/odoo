const { chromium } = require('playwright');

(async () => {
    console.log('--- Verifying Clean Navbar Icons, App Title, and AI Button ---');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.error('[PAGE ERROR]', msg.text());
        }
    });

    // 1. Login
    console.log('Navigating to http://localhost:18069/insilos...');
    await page.goto('http://localhost:18069/insilos', { waitUntil: 'networkidle', timeout: 45000 });

    const loginInput = await page.$('input[name="login"]');
    const passwordInput = await page.$('input[name="password"]');
    const submitBtn = await page.$('button[type="submit"]');

    if (loginInput && passwordInput && submitBtn) {
        await loginInput.fill('admin');
        await passwordInput.fill('admin');
        console.log('Logging in...');
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle', timeout: 60000 }),
            submitBtn.click()
        ]);
    }

    await page.waitForTimeout(3000);
    console.log('Logged in successfully! Current URL:', page.url());

    // 2. Capture Navbar on Home Menu
    const navbar = await page.$('.o_navbar');
    if (navbar) {
        const homeNavPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/navbar_home_clean.png';
        await navbar.screenshot({ path: homeNavPath });
        console.log('Home navbar screenshot captured:', homeNavPath);
    }

    // Capture the AI button specifically
    const aiBtn = await page.$('.o_ai_systray_btn');
    if (aiBtn) {
        const aiBtnPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/ai_btn_clean.png';
        await aiBtn.screenshot({ path: aiBtnPath });
        console.log('AI button screenshot captured:', aiBtnPath);

        // Check if .insilos-brain-glow-dot exists
        const glowDot = await page.$('.insilos-brain-glow-dot');
        console.log('Glow dot present (should be false):', !!glowDot);
    }

    // 3. Click "Meeting Rooms" app
    console.log('\nClicking on Meeting Rooms app...');
    // Look for app with text "Meeting Rooms"
    const apps = await page.$$('.o_app');
    let clicked = false;
    for (const app of apps) {
        const text = await app.innerText();
        if (text.includes('Meeting Rooms')) {
            console.log('Found Meeting Rooms app card! Clicking...');
            await app.click();
            clicked = true;
            break;
        }
    }

    if (!clicked && apps.length > 0) {
        console.log('Meeting Rooms not found by text, clicking first app...');
        await apps[0].click();
    }

    await page.waitForTimeout(4000);
    console.log('In App! Current URL:', page.url());

    // 4. Verify inside module view
    // Check if .o_menu_brand_icon exists in DOM
    const brandIcon = await page.$('.o_menu_brand_icon');
    console.log('.o_menu_brand_icon present in DOM (should be false):', !!brandIcon);

    const brandTitle = await page.$('.o_menu_brand');
    if (brandTitle) {
        const titleText = await brandTitle.innerText();
        console.log('.o_menu_brand text:', titleText);
    }

    // Capture navbar in module view
    if (navbar) {
        const moduleNavPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/navbar_module_clean.png';
        await navbar.screenshot({ path: moduleNavPath });
        console.log('Module navbar screenshot captured:', moduleNavPath);
    }

    // Capture launcher button specifically
    const launcherBtn = await page.$('.o_navbar_apps_menu');
    if (launcherBtn) {
        const launcherPath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/launcher_icon_clean.png';
        await launcherBtn.screenshot({ path: launcherPath });
        console.log('Launcher icon screenshot captured:', launcherPath);
    }

    // Full page screenshot of module view
    const fullModulePath = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/module_view_verified.png';
    await page.screenshot({ path: fullModulePath, fullPage: true });
    console.log('Full module view screenshot captured:', fullModulePath);

    await browser.close();
    console.log('--- Verification Completed Successfully ---');
})();
