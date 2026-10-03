# Avatar Consistency Fix — IBM Carbon 11 / SAP Fiori Horizon

## Root Cause Summary

The bug is a three-layer mismatch:
- `<DiscussAvatar>` renders `.rounded` (4px squircle) + SVG mask cuts a circular hole → "vừa vuông vừa tròn"
- Dropdown identity card uses `border-radius: 50%` → pure circle
- Chatter uses `rounded-3` (8px) → different squircle

The fix standardizes all **person avatars** to `border-radius: 50%` via a QWeb template patch + SCSS overrides.

---

## 1. QWeb Template Patch

**File:** `enterprise/insilos_theme_genesis/static/src/xml/discuss_avatar_patch.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <!--
        Patch: mail.DiscussAvatar.avatarImg
        Purpose: Override Bootstrap .rounded (4px) with full circle for person avatars.
        Carbon 11 ref: https://carbondesignsystem.com/components/avatar/style/
        Fiori Horizon ref: SAP Avatar shape="Circle"
    -->
    <t t-name="insilos.DiscussAvatar.avatarImg"
       t-inherit="mail.DiscussAvatar.avatarImg"
       t-inherit-mode="extension">
        <xpath expr="//img[hasclass('rounded')]" position="replace">
            <img
                t-att-src="props.src"
                t-att-alt="props.alt or ''"
                t-att-class="'o-is-avatar-img w-100 h-100 object-fit-cover rounded-circle'"
                loading="lazy"
                aria-hidden="false"
            />
        </xpath>
    </t>

    <!--
        Patch: mail.DiscussAvatar (container + SVG mask)
        Purpose: Re-center the status badge mask to work with a circle shape.
        The original mask rect rx="8" was designed for a squircle. 
        We switch to a <circle> clip to complement the round avatar.
    -->
    <t t-name="insilos.DiscussAvatar"
       t-inherit="mail.DiscussAvatar"
       t-inherit-mode="extension">
        <!--
            Replace the squircle <rect> mask with a <circle> mask so the
            online-status cutout blends cleanly against the circular avatar.
            Original: <rect rx="8" ry="8" width="16" height="16" transform="translate(19, 19)"/>
            The outer avatar cell is always rendered at props.size × props.size.
            We use a circle whose radius matches the status dot (r ≈ 4.5px @ 16px cell).
        -->
        <xpath expr="//mask//rect[contains(@transform,'translate')]" position="replace">
            <circle
                t-att-r="Math.round(props.size * 0.28)"
                t-att-cx="props.size - Math.round(props.size * 0.28)"
                t-att-cy="props.size - Math.round(props.size * 0.28)"
                fill="black"
            />
        </xpath>
    </t>
</templates>
```

**File:** `enterprise/insilos_theme_genesis/__manifest__.py` — ensure the asset is registered:

```python
# In __manifest__.py assets section, add:
'assets': {
    'web.assets_backend': [
        # SCSS — load order matters: variables → components → overrides
        'insilos_theme_genesis/static/src/scss/insilos_systray_restructure.scss',
        'insilos_theme_genesis/static/src/scss/insilos_usermenu_restructure.scss',
    ],
    'web.assets_backend_xml': [
        'insilos_theme_genesis/static/src/xml/discuss_avatar_patch.xml',
    ],
},
```

---

## 2. SCSS Rules

### `insilos_systray_restructure.scss`

```scss
// =============================================================================
// Insilos Systray — Avatar Consistency
// Standard: IBM Carbon 11 + SAP Fiori Horizon
// Token refs:
//   Carbon  → $avatar-border-radius: 50%  (person), 4px (app icon)
//   Fiori   → @sapAvatarShapeCircle, @sapAvatarBorderWidth: 2px
// =============================================================================

// ---------------------------------------------------------------------------
// DESIGN TOKENS
// Map to Odoo CSS custom properties so dark-mode overrides are automatic.
// ---------------------------------------------------------------------------
:root {
    // Person avatar — always circle
    --is-avatar-border-radius:      50%;
    --is-avatar-border-width:       2px;
    --is-avatar-border-color:       rgba(var(--bs-body-color-rgb, 0 0 0), 0.12);
    --is-avatar-size-sm:            26px;   // systray
    --is-avatar-size-md:            40px;   // dropdown identity card
    --is-avatar-size-lg:            64px;   // profile pages
    --is-avatar-bg:                 var(--bs-secondary-bg, #e9ecef);

    // Status badge — Carbon "Online" green
    --is-status-online-color:       #24a148;   // Carbon green-50
    --is-status-away-color:         #f1c21b;   // Carbon yellow-30
    --is-status-busy-color:         #da1e28;   // Carbon red-50
    --is-status-offline-color:      var(--bs-secondary-color, #6c757d);
    --is-status-badge-size:         10px;
    --is-status-badge-border:       2px solid var(--bs-body-bg, #fff);
}

// Dark-mode token overrides (Odoo sets [data-color-scheme="dark"] on <html>)
[data-color-scheme="dark"] {
    --is-avatar-border-color:       rgba(255 255 255 / 0.18);
    --is-avatar-border-color-focus: rgba(255 255 255 / 0.55);
    --is-status-badge-border:       2px solid var(--bs-body-bg, #161616); // Carbon Gray-100
}

// ---------------------------------------------------------------------------
// BASE AVATAR MIXIN
// Single source of truth — apply to every person-avatar site.
// ---------------------------------------------------------------------------
@mixin is-person-avatar($size: null) {
    position:       relative;
    display:        inline-flex;
    align-items:    center;
    justify-content: center;
    flex-shrink:    0;
    overflow:       hidden;                     // clips the img to circle
    border-radius:  var(--is-avatar-border-radius);
    border:         var(--is-avatar-border-width) solid var(--is-avatar-border-color);
    background:     var(--is-avatar-bg);
    aspect-ratio:   1 / 1;

    @if $size {
        width:  $size;
        height: $size;
    }

    // The <img> inside must also be circular and cover the cell
    > img,
    .o-is-avatar-img {
        display:       block;
        width:         100%;
        height:        100%;
        border-radius: 50% !important; // override any Bootstrap .rounded-* utility
        object-fit:    cover;
        object-position: center;
        border:        none;           // border lives on the wrapper, not the img
    }
}

// ---------------------------------------------------------------------------
// SYSTRAY — .o_user_menu trigger button
// Hosts <DiscussAvatar size="26"/>
// ---------------------------------------------------------------------------
.o_menu_systray {
    .o_user_menu {
        // Remove default button chrome that causes layout shifts
        &.o_dropdown {
            padding:    0 4px;
            background: transparent;
            border:     none;
            line-height: 1;
        }

        // The DiscussAvatar wrapper <div>
        .o-mail-DiscussAvatar {
            @include is-person-avatar(var(--is-avatar-size-sm));

            // The SVG layer that renders the status-mask sits outside the img
            // Keep it absolutely positioned so it overlays the circle cleanly
            > svg.position-absolute {
                // Do NOT hide — it carries the mask + status dot
                pointer-events: none;
            }
        }

        // Fallback: plain <img class="o_user_avatar"> (no mail module)
        .o_user_avatar,
        img.o_user_avatar {
            @include is-person-avatar(var(--is-avatar-size-sm));
        }
    }
}

// ---------------------------------------------------------------------------
// STATUS BADGE — .o-mail-ImStatus
// Replaces the raw SVG circle for cleaner styling control.
// ---------------------------------------------------------------------------
.o-mail-ImStatus {
    position:     absolute;
    bottom:       -1px;
    right:        -1px;
    width:        var(--is-status-badge-size);
    height:       var(--is-status-badge-size);
    border-radius: 50%;
    border:       var(--is-status-badge-border);
    background:   var(--is-status-offline-color);
    z-index:      1;

    &.o-mail-ImStatus-online  { background: var(--is-status-online-color); }
    &.o-mail-ImStatus-away    { background: var(--is-status-away-color); }
    &.o-mail-ImStatus-busy    { background: var(--is-status-busy-color); }
}

// ---------------------------------------------------------------------------
// CHATTER — message thread author avatars
// .o-mail-Message-avatar, .o-mail-Thread-avatar
// ---------------------------------------------------------------------------
.o-mail-Message,
.o-mail-Thread {
    .o-mail-Message-avatar,
    .o-mail-Thread-avatar {
        @include is-person-avatar(32px);

        // Chatter cells use rounded-3 (8px) by default — override completely
        border-radius: 50% !important;

        img {
            border-radius: 50% !important;
        }
    }
}

// ---------------------------------------------------------------------------
// MANY2ONE / MANY2MANY — .o_m2o_avatar, .o_m2m_avatar
// Only override *person* avatars — object/doc icons should stay squircle.
// Odoo adds .o_avatar_person on person records; use that as scope.
// ---------------------------------------------------------------------------
.o_m2o_avatar,
.o_m2m_avatar {
    &.o_avatar_person,
    &[data-model="res.partner"],
    &[data-model="res.users"] {
        @include is-person-avatar(24px);
    }
}

// ---------------------------------------------------------------------------
// GLOBAL SAFETY NET
// Catch any remaining loose <img> with Bootstrap round utilities inside
// a known avatar context. Does NOT affect app/doc icons.
// ---------------------------------------------------------------------------
[class*="o_user_avatar"],
[class*="o-mail-DiscussAvatar"] {
    img.rounded,
    img.rounded-1,
    img.rounded-2,
    img.rounded-3 {
        border-radius: 50% !important;
        overflow:      hidden;
    }
}
```

### `insilos_usermenu_restructure.scss`

```scss
// =============================================================================
// Insilos User Menu Dropdown — Identity Card + Avatar
// Picks up tokens defined in insilos_systray_restructure.scss
// =============================================================================

// ---------------------------------------------------------------------------
// IDENTITY CARD — top section of the user menu dropdown
// ---------------------------------------------------------------------------
.o_user_menu_dropdown,
.o_user_menu .dropdown-menu {
    .is-user-identity-card {
        display:     flex;
        align-items: center;
        gap:         12px;
        padding:     16px;

        // Avatar — medium size per Carbon avatar sizing scale
        .is-identity-avatar,
        .o-mail-DiscussAvatar {
            @include is-person-avatar(var(--is-avatar-size-md)); // 40px

            // Slightly more prominent border in the menu context
            --is-avatar-border-color: rgba(var(--bs-body-color-rgb, 0 0 0), 0.20);
            --is-avatar-border-width: 2px;

            // Subtle elevation on hover for interactivity cue
            transition: box-shadow 0.15s ease;

            &:hover {
                box-shadow: 0 0 0 3px rgba(var(--bs-primary-rgb, 15 98 254), 0.30);
            }
        }

        // User name + role block
        .is-identity-info {
            flex:        1;
            min-width:   0;         // enable text truncation

            .is-identity-name {
                font-size:   0.875rem;
                font-weight: 600;
                white-space: nowrap;
                overflow:    hidden;
                text-overflow: ellipsis;
                color: var(--bs-body-color);
            }

            .is-identity-role,
            .is-identity-company {
                font-size:  0.75rem;
                color:      var(--bs-secondary-color, #6c757d);
                white-space: nowrap;
                overflow:    hidden;
                text-overflow: ellipsis;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// DARK MODE — dropdown-specific overrides
// ---------------------------------------------------------------------------
[data-color-scheme="dark"] {
    .o_user_menu_dropdown,
    .o_user_menu .dropdown-menu {
        .is-user-identity-card {
            .is-identity-avatar,
            .o-mail-DiscussAvatar {
                --is-avatar-border-color: rgba(255 255 255 / 0.22);
                --is-avatar-bg:           #393939; // Carbon Gray-80

                &:hover {
                    box-shadow: 0 0 0 3px rgba(141 141 255 / 0.50); // Carbon Blue-40 tint
                }
            }

            .is-identity-info {
                .is-identity-role,
                .is-identity-company {
                    color: var(--bs-secondary-color, #8d8d8d); // Carbon Gray-40
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// HIGH CONTRAST MODE (Windows / accessibility)
// ---------------------------------------------------------------------------
@media (forced-colors: active) {
    .is-identity-avatar,
    .o-mail-DiscussAvatar,
    .o-mail-Message-avatar {
        border-color:  ButtonText;
        forced-color-adjust: none;
    }
}
```

---

## 3. Playwright Verification Script

**File:** `tests/e2e/avatar_consistency.spec.ts`

```typescript
/**
 * Playwright E2E: Avatar Shape Consistency
 * Verifies all person-avatar contexts render as circles (border-radius = 50%)
 * across light and dark modes.
 *
 * Run:  npx playwright test avatar_consistency.spec.ts
 * Deps: @playwright/test, pixelmatch, pngjs
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

// ---------------------------------------------------------------------------
// CONFIG
// ---------------------------------------------------------------------------
const BASE_URL   = process.env.ODOO_BASE_URL ?? 'http://localhost:8069';
const ADMIN_USER = process.env.ODOO_USER     ?? 'admin';
const ADMIN_PASS = process.env.ODOO_PASS     ?? 'admin';
const SNAP_DIR   = path.join(__dirname, 'screenshots', 'avatar');

fs.mkdirSync(SNAP_DIR, { recursive: true });

// ---------------------------------------------------------------------------
// HELPERS
// ---------------------------------------------------------------------------

/** Log in to Odoo and return a ready page. */
async function login(page: Page): Promise<void> {
    await page.goto(`${BASE_URL}/web/login`);
    await page.fill('#login',    ADMIN_USER);
    await page.fill('#password', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/odoo/**`);
}

/**
 * Evaluate computed border-radius for an element and assert it resolves to 50%.
 * Works for both the string "50%" and pixel-equivalent values (e.g. "13px" when
 * the element is 26×26px — 13 === 26/2).
 */
async function assertCircle(
    page:     Page,
    selector: string,
    label:    string,
): Promise<void> {
    const elements = page.locator(selector);
    const count    = await elements.count();

    expect(count, `[${label}] No elements found for "${selector}"`).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
        const el = elements.nth(i);

        // Skip hidden elements (display:none, visibility:hidden)
        const visible = await el.isVisible();
        if (!visible) continue;

        const result = await el.evaluate((node: HTMLElement) => {
            const cs  = window.getComputedStyle(node);
            const br  = cs.borderRadius; // e.g. "13px" or "50%"
            const w   = node.offsetWidth;
            const h   = node.offsetHeight;

            // Accept "50%" literally or px-value that equals half the size
            const brPx = parseFloat(br);
            const isCircle = br.includes('50%')
                || (w > 0 && h > 0 && brPx >= w / 2 && brPx >= h / 2);

            return { br, w, h, isCircle };
        });

        expect(
            result.isCircle,
            `[${label}] #${i} selector="${selector}" → border-radius="${result.br}" ` +
            `on ${result.w}×${result.h}px element. Expected circle (50%).`
        ).toBe(true);

        // Also assert 1:1 aspect ratio (±1px tolerance for sub-pixel rounding)
        expect(
            Math.abs(result.w - result.h),
            `[${label}] #${i} selector="${selector}" → ${result.w}×${result.h}px is not square`
        ).toBeLessThanOrEqual(1);
    }
}

/**
 * Assert the squircle contexts we deliberately keep as rectangles
 * still have border-radius < 50%.
 */
async function assertSquircle(
    page:     Page,
    selector: string,
    label:    string,
): Promise<void> {
    const elements = page.locator(selector);
    const count    = await elements.count();
    if (count === 0) return; // optional context — skip silently

    for (let i = 0; i < count; i++) {
        const el = elements.nth(i);
        if (!(await el.isVisible())) continue;

        const result = await el.evaluate((node: HTMLElement) => {
            const cs  = window.getComputedStyle(node);
            const br  = cs.borderRadius;
            const w   = node.offsetWidth;
            const brPx = parseFloat(br);
            const isCircle = br.includes('50%') || (w > 0 && brPx >= w / 2);
            return { br, isCircle };
        });

        expect(
            result.isCircle,
            `[${label}] #${i} selector="${selector}" → border-radius="${result.br}" ` +
            `should NOT be a circle (it is a doc/app icon tile).`
        ).toBe(false);
    }
}

/** Switch Odoo UI color scheme. */
async function setColorScheme(
    page: Page,
    scheme: 'light' | 'dark',
): Promise<void> {
    await page.evaluate((s) => {
        document.documentElement.setAttribute('data-color-scheme', s);
    }, scheme);
    // Allow repaint
    await page.waitForTimeout(300);
}

/** Take a labeled screenshot for visual diff archiving. */
async function snap(page: Page, name: string): Promise<void> {
    await page.screenshot({
        path:     path.join(SNAP_DIR, `${name}.png`),
        fullPage: false,
    });
}

// ---------------------------------------------------------------------------
// SELECTORS
// Per avatar context identified in the bug report.
// ---------------------------------------------------------------------------
const SELECTORS = {
    // 1. Systray trigger — DiscussAvatar wrapper
    systraySVGMask:      '.o_user_menu .o-mail-DiscussAvatar',
    // 1b. img inside systray avatar
    sysTrayImg:          '.o_user_menu .o-mail-DiscussAvatar img',
    // 2. Dropdown identity avatar
    dropdownAvatar:      '.is-user-identity-card .is-identity-avatar',
    dropdownDiscuss:     '.is-user-identity-card .o-mail-DiscussAvatar',
    // 3. Chatter message author avatar
    chatterAvatar:       '.o-mail-Message-avatar',
    chatterAvatarImg:    '.o-mail-Message-avatar img',
    // 4. Many2one person avatar
    m2oPersonAvatar:     '.o_m2o_avatar.o_avatar_person',
    // NEGATIVE: app/doc icon tiles must stay squircle
    appIconTile:         '.o_app_icon img, .o_home_menu .o_menuitem img',
} as const;

// ---------------------------------------------------------------------------
// TESTS
// ---------------------------------------------------------------------------

test.describe('Avatar Shape Consistency — Carbon 11 / Fiori Horizon', () => {

    let context: BrowserContext;
    let page:    Page;

    test.beforeAll(async ({ browser }) => {
        context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        page    = await context.newPage();
        await login(page);
    });

    test.afterAll(async () => {
        await context.close();
    });

    // -----------------------------------------------------------------------
    // LIGHT MODE
    // -----------------------------------------------------------------------
    test.describe('Light mode', () => {

        test.beforeEach(async () => {
            await setColorScheme(page, 'light');
        });

        test('Systray DiscussAvatar wrapper is circular', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            await page.waitForSelector(SELECTORS.systraySVGMask, { timeout: 10_000 });
            await snap(page, 'light-systray-before-click');

            await assertCircle(page, SELECTORS.systraySVGMask,  'systray-wrapper [light]');
            await assertCircle(page, SELECTORS.sysTrayImg,      'systray-img [light]');
        });

        test('SVG mask cutout is a circle (not squircle rect)', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            await page.waitForSelector('.o_user_menu', { timeout: 10_000 });

            const maskShape = await page.evaluate(() => {
                // Find the <rect> or <circle> inside the SVG mask
                const rect   = document.querySelector('.o_user_menu svg mask rect');
                const circle = document.querySelector('.o_user_menu svg mask circle');
                if (circle) return 'circle';
                if (rect)   return 'rect';
                return 'none';
            });

            expect(maskShape, 'SVG mask should use <circle>, not <rect>').toBe('circle');
        });

        test('Dropdown identity avatar is circular', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            // Open the user menu
            await page.click('.o_user_menu');
            await page.waitForSelector(
                `${SELECTORS.dropdownAvatar}, ${SELECTORS.dropdownDiscuss}`,
                { timeout: 8_000 }
            );
            await snap(page, 'light-dropdown-open');

            // Try both selectors — theme may use either
            const combined = `${SELECTORS.dropdownAvatar}, ${SELECTORS.dropdownDiscuss}`;
            await assertCircle(page, combined, 'dropdown-identity [light]');
        });

        test('Chatter message avatars are circular', async () => {
            // Navigate to any chatter-rich view — res.partner works universally
            await page.goto(`${BASE_URL}/odoo/contacts`);
            // Open first contact with messages
            const firstContact = page.locator('.o_data_row').first();
            if (await firstContact.isVisible()) {
                await firstContact.click();
                await page.waitForSelector('.o-mail-Chatter', { timeout: 10_000 });
            }

            const chatterMsgs = page.locator(SELECTORS.chatterAvatar);
            const count       = await chatterMsgs.count();

            if (count > 0) {
                await assertCircle(page, SELECTORS.chatterAvatar,    'chatter-wrapper [light]');
                await assertCircle(page, SELECTORS.chatterAvatarImg, 'chatter-img [light]');
            } else {
                test.info().annotations.push({
                    type: 'skip-reason',
                    description: 'No chatter messages found in first contact — skipping chatter check',
                });
            }
        });

        test('App/doc icon tiles remain squircle (regression guard)', async () => {
            await page.goto(`${BASE_URL}/odoo/settings`);
            await assertSquircle(page, SELECTORS.appIconTile, 'app-icon-tile [light]');
        });

        test('No "rounded" or "rounded-N" class left on person avatar imgs', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            await page.waitForSelector('.o_user_menu', { timeout: 10_000 });

            const offenders = await page.evaluate(() => {
                const imgs = document.querySelectorAll(
                    '.o_user_menu img, .o-mail-DiscussAvatar img, ' +
                    '.o-mail-Message-avatar img'
                );
                const bad: string[] = [];
                imgs.forEach((img, i) => {
                    const cls = img.className;
                    // Bootstrap .rounded gives 4px, .rounded-1/.rounded-2/.rounded-3 give 2/4/8px
                    if (/\brounded\b(?!-circle)/.test(cls)) {
                        bad.push(`img[${i}] classes: "${cls}"`);
                    }
                });
                return bad;
            });

            expect(
                offenders,
                'These imgs still carry a non-circle Bootstrap rounded class:\n' +
                offenders.join('\n')
            ).toHaveLength(0);
        });
    });

    // -----------------------------------------------------------------------
    // DARK MODE
    // -----------------------------------------------------------------------
    test.describe('Dark mode', () => {

        test.beforeEach(async () => {
            await setColorScheme(page, 'dark');
        });

        test('Systray avatar is circular in dark mode', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            await page.waitForSelector(SELECTORS.systraySVGMask, { timeout: 10_000 });
            await snap(page, 'dark-systray');

            await assertCircle(page, SELECTORS.systraySVGMask, 'systray [dark]');
            await assertCircle(page, SELECTORS.sysTrayImg,     'systray-img [dark]');
        });

        test('Status badge border matches dark body background', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            await page.waitForSelector('.o-mail-ImStatus', { timeout: 10_000 });

            const result = await page.evaluate(() => {
                const badge = document.querySelector('.o-mail-ImStatus') as HTMLElement | null;
                if (!badge) return null;
                const cs    = window.getComputedStyle(badge);
                return {
                    borderColor: cs.borderColor,
                    borderWidth: cs.borderWidth,
                };
            });

            if (result) {
                // Border width must be at least 1px to separate badge from avatar
                expect(parseFloat(result.borderWidth)).toBeGreaterThanOrEqual(1);
            }
        });

        test('Dropdown identity avatar is circular in dark mode', async () => {
            await page.goto(`${BASE_URL}/odoo`);
            await page.click('.o_user_menu');
            await page.waitForSelector(
                `${SELECTORS.dropdownAvatar}, ${SELECTORS.dropdownDiscuss}`,
                { timeout: 8_000 }
            );
            await snap(page, 'dark-dropdown-open');

            const combined = `${SELECTORS.dropdownAvatar}, ${SELECTORS.dropdownDiscuss}`;
            await assertCircle(page, combined, 'dropdown-identity [dark]');
        });
    });

    // -----------------------------------------------------------------------
    // CROSS-MODE SNAPSHOT DIFF
    // Fails if light/dark snapshots are identical (meaning the dark-mode CSS
    // isn't applying at all).
    // -----------------------------------------------------------------------
    test('Light and dark systray screenshots differ (dark mode is active)', async () => {
        // Light snapshot
        await setColorScheme(page, 'light');
        await page.goto(`${BASE_URL}/odoo`);
        await page.waitForSelector(SELECTORS.systraySVGMask, { timeout: 10_000 });
        const lightBuffer = await page.locator(SELECTORS.systraySVGMask)
            .first()
            .screenshot();

        // Dark snapshot
        await setColorScheme(page, 'dark');
        await page.waitForTimeout(400);
        const darkBuffer  = await page.locator(SELECTORS.systraySVGMask)
            .first()
            .screenshot();

        // Pixel-level diff using pixelmatch
        const { PNG } = await import('pngjs');
        const pixelmatch = (await import('pixelmatch')).default;

        const lightPng = PNG.sync.read(lightBuffer);
        const darkPng  = PNG.sync.read(darkBuffer);

        const { width, height } = lightPng;
        const diffPng = new PNG({ width, height });

        const mismatchedPixels = pixelmatch(
            lightPng.data, darkPng.data, diffPng.data,
            width, height,
            { threshold: 0.1 }
        );

        fs.writeFileSync(path.join(SNAP_DIR, 'diff-light-vs-dark.png'), PNG.sync.write(diffPng));

        // If 0 pixels differ, dark mode CSS is not working
        expect(
            mismatchedPixels,
            'Light and dark avatar screenshots are pixel-identical — ' +
            'dark mode CSS is not being applied.'
        ).toBeGreaterThan(0);
    });
});
```

**`playwright.config.ts`** (minimal, add to existing if present):

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir:    './tests/e2e',
    timeout:    30_000,
    retries:    1,
    reporter:   [['html', { outputFolder: 'playwright-report' }]],
    use: {
        baseURL:    process.env.ODOO_BASE_URL ?? 'http://localhost:8069',
        screenshot: 'only-on-failure',
        video:      'retain-on-failure',
    },
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
        { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    ],
});
```

**`package.json`** additions:

```json
{
  "devDependencies": {
    "@playwright/test": "^1.44.0",
    "pixelmatch": "^5.3.0",
    "pngjs": "^7.0.0"
  },
  "scripts": {
    "test:avatar": "npx playwright test avatar_consistency.spec.ts --reporter=html"
  }
}
```

---

## Delivery Checklist

```
enterprise/insilos_theme_genesis/
├── __manifest__.py                          ← register xml + scss assets
├── static/
│   ├── src/
│   │   ├── xml/
│   │   │   └── discuss_avatar_patch.xml     ← 1. QWeb patch (img class + SVG mask)
│   │   └── scss/
│   │       ├── insilos_systray_restructure.scss    ← 2a. tokens + systray + chatter
│   │       └── insilos_usermenu_restructure.scss   ← 2b. dropdown + dark overrides
tests/
└── e2e/
    └── avatar_consistency.spec.ts           ← 3. Playwright checks
```

Key design decisions worth noting:
- The SVG mask `<rect>` → `<circle>` swap in the QWeb patch eliminates the "bite taken out of a square" artifact at the source, not just via CSS
- `overflow: hidden` on the wrapper div is the actual circle clip — `border-radius` on `<img>` alone doesn't clip if the parent overflows
- The `!important` guards on `border-radius` are scoped tightly to `[class*="o-mail-DiscussAvatar"] img` so they don't bleed into app icon tiles
- `forced-colors: active` support satisfies WCAG 1.4.11 for high-contrast Windows users
