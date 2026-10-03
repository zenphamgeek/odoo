const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

async function main() {
    console.log('--- Launching Playwright Auth Screens Verification Engine ---');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
    });
    const page = await context.newPage();

    const targets = [
        {
            url: 'http://localhost:28069/web/login',
            name: 'Login (Light)',
            file: 'evidence_login_light.png',
            darkMode: false
        },
        {
            url: 'http://localhost:28069/web/login',
            name: 'Login (Dark)',
            file: 'evidence_login_dark.png',
            darkMode: true
        },
        {
            url: 'http://localhost:28069/web/reset_password',
            name: 'Reset Password',
            file: 'evidence_reset_password.png',
            darkMode: false
        },
        {
            url: 'http://localhost:28069/web/signup',
            name: 'Sign Up',
            file: 'evidence_signup.png',
            darkMode: false
        },
        {
            url: 'http://localhost:28069/web/database/manager',
            name: 'Database Manager',
            file: 'evidence_db_manager.png',
            darkMode: true
        },
        {
            url: 'http://localhost:28069/web/database/selector',
            name: 'Database Selector',
            file: 'evidence_db_selector.png',
            darkMode: true
        }
    ];

    for (const t of targets) {
        console.log(`\nNavigating to ${t.name}: ${t.url}`);
        const resp = await page.goto(t.url, { waitUntil: 'networkidle', timeout: 30000 });
        console.log(`Status: ${resp.status()}`);

        if (t.darkMode) {
            await page.evaluate(() => {
                document.body.classList.add('o_dark_mode');
                document.documentElement.setAttribute('data-bs-theme', 'dark');
            });
            await page.waitForTimeout(300);
        } else {
            await page.evaluate(() => {
                document.body.classList.remove('o_dark_mode');
                document.documentElement.removeAttribute('data-bs-theme');
            });
            await page.waitForTimeout(200);
        }

        // Diagnostic verification
        const audit = await page.evaluate(() => {
            const logoImg = document.querySelector('img[src*="insilos_logo"]');
            const fabricatedSvg = document.querySelector('svg.header-brand-logo, svg path[d*="M20 4L4"]');
            const authTitle = document.querySelector('.auth_title')?.textContent?.trim();
            const authSubtitle = document.querySelector('.auth_subtitle')?.textContent?.trim();
            const heroTitle = document.querySelector('.insilos_auth_hero_showcase h2')?.textContent?.trim();
            const emailLabel = document.querySelector('.field-login label')?.textContent?.trim();
            const pwdLabel = document.querySelector('.field-password label, label[for="password"]')?.textContent?.trim();
            const loginBtn = document.querySelector('.oe_login_buttons button[type="submit"]')?.textContent?.trim();
            const resetLink = document.querySelector('a[href*="reset_password"]')?.textContent?.trim();
            const signupLink = document.querySelector('a[href*="signup"]')?.textContent?.trim();
            const passkeyBtn = document.querySelector('.passkey_login_link')?.textContent?.trim();

            return {
                canonicalLogoFound: !!logoImg,
                canonicalLogoSrc: logoImg ? logoImg.getAttribute('src') : null,
                fabricatedSvgFound: !!fabricatedSvg,
                authTitle,
                authSubtitle,
                heroTitle,
                emailLabel,
                pwdLabel,
                loginBtn,
                resetLink,
                signupLink,
                passkeyBtn
            };
        });

        console.log(`Audit metrics for ${t.name}:`, JSON.stringify(audit, null, 2));

        const destPath = path.join(ARTIFACT_DIR, t.file);
        await page.screenshot({ path: destPath, fullPage: true });
        console.log(`Saved screenshot: ${destPath}`);
    }

    await browser.close();
    console.log('\n--- All Auth Screens Verified & Captured Successfully ---');
}

main().catch(err => {
    console.error('Fatal error during capture:', err);
    process.exit(1);
});
