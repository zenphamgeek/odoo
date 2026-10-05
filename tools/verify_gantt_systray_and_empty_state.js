const { chromium } = require('playwright');
const path = require('path');

const ARTIFACT_DIR = '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();

  console.log('1. Logging in to http://localhost:28069 ...');
  await page.goto('http://localhost:28069/web/login');
  await page.fill('input[name="login"]', 'admin');
  await page.fill('input[name="password"]', 'admin');
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  await page.waitForTimeout(2000);

  // 1. Navigate to Meeting Rooms
  console.log('2. Navigating to Meeting Rooms (http://localhost:28069/insilos/rooms) ...');
  await page.goto('http://localhost:28069/insilos/rooms');
  await page.waitForTimeout(3000);

  // Capture Systray in Light Mode
  const systray = await page.$('.o_main_navbar .o_menu_systray');
  if (systray) {
    await systray.screenshot({ path: path.join(ARTIFACT_DIR, 'systray_light_verified.png') });
    console.log('Captured systray_light_verified.png');
  }

  // Capture View Switcher (Gantt & Calendar)
  const viewSwitcher = await page.$('.o_cp_switch_buttons');
  if (viewSwitcher) {
    await viewSwitcher.screenshot({ path: path.join(ARTIFACT_DIR, 'view_switcher_gantt_verified.png') });
    console.log('Captured view_switcher_gantt_verified.png');
  }

  // Inspect Gantt button icon
  const ganttIconInfo = await page.evaluate(() => {
    const btn = document.querySelector('.o_switch_view.o_gantt');
    if (!btn) return { found: false };
    const i = btn.querySelector('i, .oi');
    const computed = window.getComputedStyle(btn);
    const iComputed = i ? window.getComputedStyle(i, ':before') : null;
    return {
      found: true,
      btnClass: btn.className,
      iconClass: i ? i.className : null,
      beforeContent: iComputed ? iComputed.content : null,
      beforeFontFamily: iComputed ? iComputed.fontFamily : null,
      btnText: btn.textContent.trim()
    };
  });
  console.log('Gantt Icon Info:', JSON.stringify(ganttIconInfo, null, 2));

  // Inspect Systray Line Thickness & Icons
  const systrayInfo = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.o_main_navbar .o_menu_systray > *')).filter(el => el.offsetWidth > 0);
    return items.map(el => {
      const icon = el.querySelector('i, .oi, svg');
      const iconStyle = icon ? window.getComputedStyle(icon) : null;
      const beforeStyle = icon ? window.getComputedStyle(icon, ':before') : null;
      return {
        tag: el.tagName,
        className: el.className,
        iconTag: icon ? icon.tagName : null,
        iconClass: icon ? icon.className : null,
        beforeContent: beforeStyle ? beforeStyle.content : null,
        beforeFont: beforeStyle ? beforeStyle.fontFamily : null,
        iconColor: iconStyle ? iconStyle.color : null,
        iconStroke: icon?.getAttribute('stroke') || null
      };
    });
  });
  console.log('Systray Items Info:', JSON.stringify(systrayInfo, null, 2));

  // Capture Empty State
  const nocontent = await page.$('.o_view_nocontent');
  if (nocontent) {
    await nocontent.screenshot({ path: path.join(ARTIFACT_DIR, 'nocontent_particles_verified.png') });
    console.log('Captured nocontent_particles_verified.png');
  }

  // Check if redundant button is hidden
  const redundantBtnVisible = await page.evaluate(() => {
    const btn = document.querySelector('.o_nocontent_help a.btn-outline-primary');
    if (!btn) return false;
    const style = window.getComputedStyle(btn);
    return style.display !== 'none';
  });
  console.log('Is redundant Create a Room button visible?', redundantBtnVisible);

  // Test interactive click on smiling face (+)
  console.log('3. Testing interactive click on (+) smiling face ...');
  const smilingFace = await page.$('.o_view_nocontent_smiling_face');
  if (smilingFace) {
    await smilingFace.click();
    await page.waitForTimeout(2000);
    console.log('Current URL after click:', page.url());
  }

  // Now test Dark Mode
  console.log('4. Testing Dark Mode Systray ...');
  await page.evaluate(() => {
    document.body.classList.add('o_dark_mode');
    document.documentElement.dataset.colorScheme = 'dark';
  });
  await page.waitForTimeout(1000);
  const systrayDark = await page.$('.o_main_navbar .o_menu_systray');
  if (systrayDark) {
    await systrayDark.screenshot({ path: path.join(ARTIFACT_DIR, 'systray_dark_verified.png') });
    console.log('Captured systray_dark_verified.png');
  }

  const fullNavbarDark = await page.$('header.o_navbar');
  if (fullNavbarDark) {
    await fullNavbarDark.screenshot({ path: path.join(ARTIFACT_DIR, 'navbar_full_dark_verified.png') });
    console.log('Captured navbar_full_dark_verified.png');
  }

  await browser.close();
  console.log('All verifications complete!');
})();
