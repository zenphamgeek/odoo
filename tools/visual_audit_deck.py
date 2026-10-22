import asyncio
from playwright.async_api import async_playwright

async def run_visual_audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            viewport={'width': 1440, 'height': 900}
        )
        page = await context.new_page()

        await page.goto('https://innoria.insilos.com/', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)

        deck_section = await page.query_selector('#architecture_deck')
        if deck_section:
            await deck_section.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)

        # Shot 1: Resting state
        await page.screenshot(path='/home/zen/O20/deck_step_1_resting.png')
        print('[✓] Shot 1: Resting state saved')

        # Hover over slab-1
        s1 = await page.query_selector('#slab-1')
        if s1:
            box = await s1.bounding_box()
            print(f'Hovering slab-1 at {box}...')
            await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await page.wait_for_timeout(1000)
            await page.screenshot(path='/home/zen/O20/deck_step_2_hover_slab1.png')
            print('[✓] Shot 2: Hover slab-1 saved')

        # Hover over slab-0
        s0 = await page.query_selector('#slab-0')
        if s0:
            box = await s0.bounding_box()
            print(f'Hovering slab-0 at {box}...')
            await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await page.wait_for_timeout(1000)
            await page.screenshot(path='/home/zen/O20/deck_step_3_hover_slab0.png')
            print('[✓] Shot 3: Hover slab-0 saved')

        # Click Explode button
        btn_exp = await page.query_selector('#btnExplode')
        if btn_exp:
            print('Clicking Explode...')
            await btn_exp.click()
            await page.wait_for_timeout(1000)
            await page.screenshot(path='/home/zen/O20/deck_step_4_exploded.png')
            print('[✓] Shot 4: Exploded saved')

        # Drag orbit
        stage = await page.query_selector('#stageCard')
        if stage:
            box = await stage.bounding_box()
            cx = box['x'] + box['width']/2
            cy = box['y'] + box['height']/2
            print('Dragging stageCard...')
            await page.mouse.move(cx, cy)
            await page.mouse.down()
            await page.mouse.move(cx - 100, cy - 50, steps=15)
            await page.mouse.up()
            await page.wait_for_timeout(1000)
            await page.screenshot(path='/home/zen/O20/deck_step_5_dragged.png')
            print('[✓] Shot 5: Dragged saved')

        await browser.close()

asyncio.run(run_visual_audit())
