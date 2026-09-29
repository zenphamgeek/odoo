#!/usr/bin/env python3
"""
Insilos Enterprise — E2E Visual & Interactive Verification for PPE Videos
Validates:
 1. Homepage (/) CCTV section, HSE Spotlight Banner, and Cinema Modal trigger
 2. Resources (/resources) SOP Vault Featured HSE Video Player
 3. Video Showcase (/showcase-3d) EP 13 HSE Gold Master card and filter
 4. Navigation bar links
"""
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    print("=== Starting Insilos PPE Video E2E Verification ===")
    artifacts_dir = "/home/zen/.gemini/antigravity/brain/f6817d98-09d6-42ae-abf0-8349eb3b17c1"
    base_url = "http://localhost:28069"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        # Listen to console messages and errors
        page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}") if msg.type in ['error', 'warn'] else None)
        page.on("pageerror", lambda err: print(f"[Browser PageError] {err}"))

        # -------------------------------------------------------------
        # TEST 1: Homepage (/)
        # -------------------------------------------------------------
        print("\n--- Test 1: Testing Homepage (/) ---")
        page.goto(f"{base_url}/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1)

        # Check navigation item
        nav_item = page.locator("a[href='/showcase-3d']").first
        assert nav_item.is_visible(), "Link to /showcase-3d not visible in navigation!"
        print("✓ Verified: 'Video & 3D' link is present and visible in top navigation.")

        # Verify Spotlight Banner
        spotlight = page.locator(".ins-btn-open-hse-movie").first
        spotlight.scroll_into_view_if_needed()
        time.sleep(1)
        assert spotlight.is_visible(), "Spotlight banner button for HSE video not visible!"
        print("✓ Verified: HSE Video Spotlight Banner is prominently displayed.")

        # Take screenshot of CCTV section with Spotlight Banner
        page.screenshot(path=f"{artifacts_dir}/ppe_home_cctv_spotlight.png")
        print(f"✓ Saved screenshot: {artifacts_dir}/ppe_home_cctv_spotlight.png")

        # Click to open Cinema Modal
        spotlight.click()
        time.sleep(1.5)

        modal = page.locator("#insilosHseVideoModal")
        assert modal.is_visible(), "HSE Video Cinema Modal did not open!"
        print("✓ Verified: HSE Video Cinema Modal opened successfully.")

        # Check video player inside modal
        cinema_player = page.locator("#insilosHseCinemaPlayer")
        src = cinema_player.locator("source").get_attribute("src")
        print(f"✓ Cinema player source: {src}")
        assert "INSILOS_HSE_AI_VISION_75S_GOLD_MASTER.mp4" in src

        # Take screenshot of open Cinema Modal
        page.screenshot(path=f"{artifacts_dir}/ppe_cinema_modal_playing.png")
        print(f"✓ Saved screenshot: {artifacts_dir}/ppe_cinema_modal_playing.png")

        # Close modal
        close_btn = modal.locator(".btn-close").first
        close_btn.click()
        time.sleep(1)

        # Verify 4 CCTV Angles including Angle 4 (Factory Engineer PPE)
        angle4_btn = page.locator("button[data-camera-angle='factory_engineer']").first
        angle4_btn.scroll_into_view_if_needed()
        assert angle4_btn.is_visible(), "Angle 4 (Factory Engineer PPE) button not visible!"
        angle4_btn.click()
        time.sleep(1)

        # Check video player switches to cctv_cam01_factory_engineer.mp4
        cctv_player = page.locator(".s_insilos_cctv_ai_camera .ins-cctv-video").first
        cctv_src = cctv_player.locator("source").get_attribute("src")
        assert "cctv_cam01_factory_engineer.mp4" in cctv_src, f"Expected factory engineer video in CCTV player, got: {cctv_src}"
        print(f"✓ Verified: Angle 4 (Factory Engineer PPE) switches to {cctv_src}")

        # Check CAM-04 title and boxes rendered
        cam_title = page.locator(".ins-cctv-cam-title").first.inner_text()
        assert "CAM-04" in cam_title, f"Expected CAM-04 in title, got: {cam_title}"
        print(f"✓ Verified: CCTV Title updated to '{cam_title}'")

        # Take screenshot of Angle 4 CCTV playback
        page.screenshot(path=f"{artifacts_dir}/ppe_cctv_angle4_factory_engineer.png")
        print(f"✓ Saved screenshot: {artifacts_dir}/ppe_cctv_angle4_factory_engineer.png")

        # -------------------------------------------------------------
        # TEST 2: Resources Page (/resources)
        # -------------------------------------------------------------
        print("\n--- Test 2: Testing Resources Page (/resources) ---")
        page.goto(f"{base_url}/resources", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1)

        res_video = page.locator("#insilosResourcesHseVideo")
        res_video.scroll_into_view_if_needed()
        time.sleep(1)
        assert res_video.is_visible(), "Resources HSE Video player not visible!"
        res_src = res_video.locator("source").get_attribute("src")
        print(f"✓ Resources HSE video source: {res_src}")
        assert "INSILOS_HSE_AI_VISION_75S_GOLD_MASTER.mp4" in res_src

        page.screenshot(path=f"{artifacts_dir}/ppe_resources_featured_video.png")
        print(f"✓ Saved screenshot: {artifacts_dir}/ppe_resources_featured_video.png")

        # -------------------------------------------------------------
        # TEST 3: Showcase 3D & Video (/showcase-3d)
        # -------------------------------------------------------------
        print("\n--- Test 3: Testing Showcase 3D & Video (/showcase-3d) ---")
        page.goto(f"{base_url}/showcase-3d", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1)

        # Scroll to Gold Master Suite
        gold_suite = page.locator("#insilos-gold-suite")
        gold_suite.scroll_into_view_if_needed()
        time.sleep(1)

        # Check filter button for HSE
        hse_filter = page.locator("button[data-filter='hse']").first
        assert hse_filter.is_visible(), "HSE filter button not visible!"
        hse_filter.click()
        time.sleep(1)

        # Check EP 13 card
        ep13_card = page.locator(".ins-gold-card[data-category='hse']").first
        ep13_card.scroll_into_view_if_needed()
        time.sleep(1)
        assert ep13_card.is_visible(), "EP 13 HSE card not visible after filter!"
        print("✓ Verified: EP 13 HSE & PPE AI Vision Gold Master card is visible.")

        page.screenshot(path=f"{artifacts_dir}/ppe_showcase_ep13_card.png")
        print(f"✓ Saved screenshot: {artifacts_dir}/ppe_showcase_ep13_card.png")

        browser.close()
        print("\n=== ALL PPE VIDEO E2E TESTS PASSED WITH 100% SUCCESS ===")

if __name__ == "__main__":
    main()
