import asyncio
import pprint
from playwright.async_api import async_playwright

async def check_hero():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            viewport={'width': 1440, 'height': 900}
        )
        page = await context.new_page()

        console_logs = []
        page.on('console', lambda m: console_logs.append(f'[{m.type}] {m.text}'))
        page.on('pageerror', lambda e: console_logs.append(f'[PAGE_ERROR] {e}'))

        await page.goto('https://innoria.insilos.com/', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)

        # Inspect Hero 3D Stage & 3D elements
        hero_info = await page.evaluate('''() => {
            const canvasList = Array.from(document.querySelectorAll('canvas')).map(c => ({
                id: c.id,
                className: c.className,
                w: c.width,
                h: c.height,
                styleW: c.style.width,
                styleH: c.style.height,
                pointerEvents: window.getComputedStyle(c).pointerEvents,
                zIndex: window.getComputedStyle(c).zIndex
            }));

            const modeBtns = Array.from(document.querySelectorAll('.hero-mode-btn, [data-hero-mode], .stage-mode-btn, .pill-mode-btn')).map(b => ({
                text: b.textContent.trim(),
                mode: b.getAttribute('data-hero-mode') || b.getAttribute('data-mode'),
                active: b.classList.contains('active')
            }));

            return {
                canvases: canvasList,
                modeBtns: modeBtns,
                heroStageObj: window._heroStage ? 'present' : 'none',
                hero3DManager: typeof window.initInnoriaHero3DManager,
                heroStageFunc: typeof window.initInnoriaHeroInteractiveStage
            };
        }''')

        print('=== ALL CANVASES ON PAGE ===')
        pprint.pprint(hero_info)

        print('\n=== CONSOLE LOGS ===')
        for l in console_logs:
            if any(k in l.lower() for k in ['hero', 'stage', '3d', 'three', 'canvas', 'error', 'warn']):
                print(l)

        # Check if any canvas is draggable
        canvases = await page.query_selector_all('canvas')
        for i, c in enumerate(canvases):
            box = await c.bounding_box()
            print(f'Canvas {i} ({box}):')
            if box and box['width'] > 50 and box['height'] > 50:
                cx = box['x'] + box['width'] / 2
                cy = box['y'] + box['height'] / 2
                await page.mouse.move(cx, cy)
                await page.mouse.down()
                await page.mouse.move(cx + 80, cy + 40, steps=10)
                await page.mouse.up()
                await page.wait_for_timeout(500)

        await page.screenshot(path='/home/zen/O20/all_canvases_check.png')
        print('\nSaved screenshot to /home/zen/O20/all_canvases_check.png')
        await browser.close()

asyncio.run(check_hero())
