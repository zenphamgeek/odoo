const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    fs.mkdirSync('tools/artifacts', { recursive: true });
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    
    // Login
    await page.goto('http://localhost:28069/web/login', { waitUntil: 'domcontentloaded' });
    await page.fill('input[name="login"]', 'admin');
    await page.fill('input[name="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    
    // Inspect user menu button avatar
    const userMenu = await page.$('.o_user_menu');
    if (userMenu) {
        const userMenuHtml = await userMenu.evaluate(el => el.outerHTML);
        console.log('UserMenu HTML:\n', userMenuHtml);
        
        const avatarEl = await page.$('.o_user_menu .o-mail-DiscussAvatar, .o_user_menu img');
        if (avatarEl) {
            const styles = await avatarEl.evaluate(el => {
                const cs = window.getComputedStyle(el);
                const img = el.tagName === 'IMG' ? el : el.querySelector('img');
                const imgCs = img ? window.getComputedStyle(img) : null;
                return {
                    tag: el.tagName,
                    class: typeof el.className === 'string' ? el.className : el.className.baseVal,
                    width: cs.width,
                    height: cs.height,
                    borderRadius: cs.borderRadius,
                    border: cs.border,
                    imgTag: img ? img.tagName : null,
                    imgClass: img ? img.className : null,
                    imgBorderRadius: imgCs ? imgCs.borderRadius : null,
                };
            });
            console.log('Avatar element styles:\n', JSON.stringify(styles, null, 2));
        }
        
        // Take screenshot of navbar user menu area
        await userMenu.screenshot({ path: 'tools/artifacts/user_menu_avatar_button.png' });
        console.log('Saved tools/artifacts/user_menu_avatar_button.png');
        
        // Click to open user menu dropdown
        await userMenu.click();
        await page.waitForTimeout(600);
        
        const identityCard = await page.$('.is-user-identity-card');
        if (identityCard) {
            const idStyles = await identityCard.evaluate(el => {
                const img = el.querySelector('.is-identity-avatar');
                const cs = img ? window.getComputedStyle(img) : null;
                return {
                    imgClass: img ? img.className : null,
                    borderRadius: cs ? cs.borderRadius : null,
                    width: cs ? cs.width : null,
                    height: cs ? cs.height : null,
                };
            });
            console.log('Identity card avatar styles:\n', JSON.stringify(idStyles, null, 2));
            await identityCard.screenshot({ path: 'tools/artifacts/user_identity_card.png' });
            console.log('Saved tools/artifacts/user_identity_card.png');
        }
        
        // Capture entire top-right navbar corner
        const systray = await page.$('.o_menu_systray');
        if (systray) {
            await systray.screenshot({ path: 'tools/artifacts/systray_overview.png' });
            console.log('Saved tools/artifacts/systray_overview.png');
        }
    } else {
        console.log('User menu button not found!');
    }
    
    await browser.close();
})();
