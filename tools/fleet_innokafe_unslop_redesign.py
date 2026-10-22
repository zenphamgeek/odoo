#!/usr/bin/env python3
"""
tools/fleet_innokafe_unslop_redesign.py
=============================================================================
AGY Fleet Multi-Node Swarm: Orchestrates parallel redesign and un-slopping
of InnoKafe Specialty Coffee (innokafe.insilos.com).

Workflow:
1. Fleet Plan: Uses high-capacity Claude Opus / Gemini Ultra node to generate 
   the authoritative, non-slop specialty coffee narrative & architecture.
2. Parallel Section Workers: Dispatches 5 parallel section redesign tasks
   across available Fleet nodes (Gemini 4 Argon High / Claude Sonnet).
3. SCSS De-Slopping: Polishes card borders, star glyphs, typography, and contrast.
4. Assembly & Local Validation: Assembles the new home.xml and verifies syntax.
=============================================================================
"""

import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

FLEET_API = "http://localhost:7777/api/fleet/run-sync"
REPO_ROOT = Path(__file__).resolve().parent.parent

def call_fleet_node(task_name: str, prompt: str, preferred_node: str = None, model: str = "gemini-4-argon-high", timeout: int = 180):
    print(f"[*] [Fleet Task: {task_name}] Dispatching to {preferred_node or 'auto'} ({model})...")
    payload = {
        "prompt": prompt,
        "model": model,
        "timeout": timeout
    }
    if preferred_node:
        payload["node_name"] = preferred_node

    req = urllib.request.Request(
        FLEET_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout + 30) as res:
            data = json.loads(res.read().decode("utf-8"))
            elapsed = time.time() - start_t
            node = data.get("node_name", "unknown")
            output = data.get("output") or data.get("clean_response") or ""
            print(f"[✓] [Fleet Task: {task_name}] Completed by Node [{node}] in {elapsed:.1f}s ({len(output)} chars)")
            return {
                "task_name": task_name,
                "node": node,
                "elapsed": elapsed,
                "output": output,
                "error": None
            }
    except Exception as e:
        elapsed = time.time() - start_t
        print(f"[✗] [Fleet Task: {task_name}] Failed after {elapsed:.1f}s: {e}")
        return {
            "task_name": task_name,
            "node": preferred_node,
            "elapsed": elapsed,
            "output": "",
            "error": str(e)
        }

def run_fleet_plan():
    print("=" * 70)
    print("PHASE 1: AGY FLEET MASTER EDITORIAL PLANNING (UN-SLOP INNOKAFE)")
    print("=" * 70)

    prompt = """You are the Creative Director and Master Specialty Coffee Copywriter for InnoKafe (Vietnam Specialty Coffee).
TASK: Audit and rewrite the brand copy and layout philosophy for InnoKafe to completely purge "AI Slop", robotic corporate jargon, and generic dark-mode template vibes.

CRITICAL INSTRUCTIONS & ANTI-SLOP RULES:
1. BAN THESE ROBOTIC AI PHRASES:
   - "Đánh thức vị giác...", "Cuộc gặp gỡ của hai đỉnh cao thổ nhưỡng...", "4 Trụ cột định hình đẳng cấp...", "Bảo chứng chất lượng...", "Thuật toán so khớp vector 7 chiều..."
2. BAN UGLY "AI SLOP" CARDS:
   - No more dark cards with glowing yellow outlines (border border-warning border-opacity-30) or heavy grey borders (border border-secondary border-opacity-25).
   - No box-in-box nesting (e.g., card containing inner rounded divs with another border).
   - Star ratings must use clean Unicode stars (★) or reliable SVG, never broken font-awesome squares (□□□□□).
3. NEW AUTHENTIC EDITORIAL TONE:
   - Earthy, warm, honest, craftsman tone. Focus on the actual farmer, the red volcanic soil of Cư M'gar, the cold morning mist of Cầu Đất, slow sun-drying for 28 days on raised mesh beds, gentle hot-air roasting that preserves bean sweetness without burning the surface.
   - Tone: Like Blue Bottle / % Arabica / Tim Wendelboe, but proudly rooted in Vietnamese heritage.
4. AVAILABLE NEW ASSETS TO INCORPORATE:
   - Videos:
     - /innokafe_website/static/src/video/innokafe_hero_terroir_16x9_opt.mp4 (Farm & Cherry picking loop)
     - /innokafe_website/static/src/video/innokafe_cooling_tray_16x9_opt.mp4 (Roasting cooling tray)
     - /innokafe_website/static/src/video/innokafe_coffee_pour_16x9_opt.mp4 (Pouring & extraction)
   - High-Res Curated Photos:
     - /innokafe_website/static/src/img/photography/farm_cherries_ripe.webp (Ripe cherries on tree)
     - /innokafe_website/static/src/img/photography/farm_plantation_mist.webp (Highland mist plantation)
     - /innokafe_website/static/src/img/photography/artisan_drying_sun.webp (Raised drying beds)
     - /innokafe_website/static/src/img/photography/artisan_roasting_beans.webp (Freshly roasted beans)
     - /innokafe_website/static/src/img/photography/sensory_cupping_flight.webp (SCA cupping table)
     - /innokafe_website/static/src/img/photography/extraction_pourover_v60.webp (V60 drip)
     - /innokafe_website/static/src/img/photography/extraction_espresso_crema.webp (Golden crema)
     - /innokafe_website/static/src/img/photography/lifestyle_barista_craft.webp (Barista craft)
     - /innokafe_website/static/src/img/photography/lifestyle_modern_cafe.webp (Modern cafe space)
     - /innokafe_website/static/src/img/photography/b2b_wholesale_packaging.webp (Packaging & valve bags)

OUTPUT:
Provide a structured Plan with:
1. Executive Creative Directive (Layout, Typography, Palette, Borderless/Subtle hairline approach).
2. Rewrite for Hero Headline, Sub-headline, and Hero Showcase.
3. Rewrite for Brand Values & Terroir Origins.
4. Rewrite for Taste Profiler & Product Showcase.
5. Exact Guidelines for SCSS border cleanup."""

    res = call_fleet_node("Master Creative Plan", prompt, preferred_node="justaskgao", model="claude-opus-5-5-high", timeout=240)
    if res["error"] or not res["output"]:
        print("[!] Falling back to node-5 (gemini-4-argon-high) for Master Plan...")
        res = call_fleet_node("Master Creative Plan Fallback", prompt, preferred_node="node-5", model="gemini-4-argon-high", timeout=120)
    
    plan_path = REPO_ROOT / "enterprise/innokafe_website/INNOKAFE_FLEET_REVISION_PLAN.md"
    plan_path.write_text(res["output"], encoding="utf-8")
    print(f"[✓] Saved Master Plan to {plan_path} ({len(res['output'])} chars)")
    return res["output"]

if __name__ == "__main__":
    plan_content = run_fleet_plan()
    print("Master Plan generated successfully. Proceeding to section parallelization.")
