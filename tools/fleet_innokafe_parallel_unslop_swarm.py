#!/usr/bin/env python3
"""
tools/fleet_innokafe_parallel_unslop_swarm.py
=============================================================================
AGY Fleet Multi-Node Swarm:
Executes parallel Cardless / Liquid Spatial UI refactoring & authentic
copywriting rewrite across InnoKafe routes.
=============================================================================
"""

import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

FLEET_URL = "http://localhost:7777"

# ---------------------------------------------------------------------------
# Task Prompts
# ---------------------------------------------------------------------------

PROMPT_SCSS = """You are the Senior CSS Architect specializing in luxury Cardless / Liquid Spatial UI.
Refactor and upgrade the SCSS rules for InnoKafe:
Target: enterprise/innokafe_website/static/src/scss/innokafe_liquid_spatial.scss

REQUIREMENTS:
1. STRICT CARDLESS DISCIPLINE ("Không dùng bừa bãi"):
   - Eliminate all boxy, rigid cards with harsh outlines (border-warning, border-secondary, border-opacity-*).
   - Cardless stages float on continuous obsidian espresso background (#0C0704, #120A06).
   - Use subtle optical hairlines: rgba(255, 255, 255, 0.06).
   - Use diffused warm honey ambient glow: 0 20px 45px -15px rgba(0, 0, 0, 0.85), 0 0 35px -8px rgba(212, 136, 66, 0.16).
2. FLOATING POD & LAYER PRIMITIVES:
   - .inno-spatial-layer: backdrop-filter: blur(24px) saturate(160%); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 1.5rem.
   - .inno-floating-pod: multi-tier depth, subtle hover elevation (-3px), zero harsh glowing yellow borders.
   - .inno-cardless: border: none !important; background: transparent !important; box-shadow: none !important.
   - .inno-badge-liquid: Honey gold gradient, high contrast text (#0C0704), no borders.
   - .inno-badge-pill-dark: Frosted dark pill with 1px hairline border.
3. GLOBAL OVERRIDES:
   - Override all .card, .inno-craft-card, .border-warning, .border-secondary to eliminate ugly AI slop borders.
   - Ensure WCAG AAA compliance (text contrast >= 7:1 against dark backgrounds).

Return the COMPLETE SCSS file content inside a single ```scss code block.
"""

PROMPT_HOME = """You are the Creative Director and Master Specialty Coffee Copywriter for InnoKafe.
Rewrite the InnoKafe Homepage template:
Target: enterprise/innokafe_website/views/home.xml

REQUIREMENTS:
1. PURGE AI SLOP COPY & VISUALS:
   - Ban: "đẳng cấp thế giới", "đánh thức vị giác", "cuộc gặp gỡ đỉnh cao", "bảo chứng chất lượng", "4 trụ cột định hình đẳng cấp".
   - Replace with authentic Vietnamese specialty coffee craft: Cư M'gar đất đỏ bazan cổ, Cầu Đất 1.650m mây sương, thu hái 100% quả chín, phơi chậm 28 ngày trên giàn lưới, rang mộc Hot-Air đối lưu, cupping SCA 84+, cam kết Cà Phê Mộc 4 Không.
2. CARDLESS / LIQUID SPATIAL UI ("Không dùng bừa bãi"):
   - Strip all ugly border-warning or border-secondary outlines from cards.
   - Replace rigid craft card grids with .inno-spatial-layer or .inno-floating-pod with subtle hairline borders (rgba(255,255,255,0.06)) and ample spacing.
   - Curated product section: cardless pods with clean typography, clear SCA score stars (SVG), single-line balance, no awkward wrapping.
   - Sensory Brew Lab: interactive calculator with refined dark controls.
3. PRESERVE TECHNICAL INTEGRITY:
   - Valid Odoo 20 QWeb XML.
   - Keep all existing IDs and data attributes: data-sku, data-product-id, inno-weight-select, inno-grind-select, brew lab sliders, cart triggers.

Return the complete home.xml or key section replacements in clean code blocks.
"""

PROMPT_STORY = """You are the Lead Heritage Storyteller for InnoKafe.
Rewrite the Farm-to-Cup Heritage Story template:
Target: enterprise/innokafe_website/views/story.xml

REQUIREMENTS:
1. AUTHENTIC VIETNAMESE COFFEE CULTURE:
   - Deep dive into the real farmers of Cư M'gar (Đắk Lắk) and Cầu Đất (Lâm Đồng).
   - Natural, honest, unpretentious narrative: how farmers wake at 5 AM in the mist, select only cherry-red fruits with brix sugar > 20%, slow-dry them under natural mountain breezes.
   - The roasting philosophy: why Hot-Air convection roasting beats traditional contact roasting (zero charred spots, preserves natural sweetness and floral aromatics).
2. CARDLESS SPATIAL UI:
   - Replace boxed timeline containers with cardless timeline nodes (.inno-cardless-step) with hairline markers.
   - Hero video and photo showcases floating directly on continuous obsidian canvas.
   - Zero glowing yellow border cards or rigid bounding boxes.

Return the complete story.xml or key section replacements in clean code blocks.
"""

PROMPT_B2B_AND_PRODUCTS = """You are the Specialty Coffee Commerce Specialist for InnoKafe.
Audit and refine:
- enterprise/innokafe_website/views/products.xml
- enterprise/innokafe_website/views/solutions_b2b.xml

REQUIREMENTS:
1. PRODUCTS (/products):
   - Refined specialty coffee lineup: Đắk Lắk Highland Fine Robusta Natural (84.5 SCA), Cầu Đất Mountain Bourbon Washed (86.0 SCA), InnoKafe Heritage Red Honey (85.2 SCA).
   - Cardless product cards: floating pods with smooth image transitions, clear tasting notes badges (.inno-badge-pill-dark), clear SCA score indicators.
   - Ensure all touch targets >= 44px.
2. B2B SOLUTIONS (/solutions-b2b):
   - Professional, grounded B2B offerings: Commercial Equipment (Synesso, La Marzocco, Mahlkönig), Roastery Fresh Wholesale (weekly roast batches, batch consistency logs), Barista Calibration & Sensorium Training.
   - Replace any lingering card borders with .inno-spatial-layer.
   - Inquire form: sleek dark spatial form with floating inputs, zero harsh borders.

Return the concrete code blocks for products.xml and solutions_b2b.xml.
"""

TASKS = [
    {
        "id": "TASK_SCSS",
        "node": "fast",
        "model": "gemini-3.8-flash-high",
        "prompt": PROMPT_SCSS
    },
    {
        "id": "TASK_HOME",
        "node": "node-4",
        "model": "gemini-3.8-flash-high",
        "prompt": PROMPT_HOME
    },
    {
        "id": "TASK_STORY",
        "node": "gaopham",
        "model": "gemini-3.8-flash-high",
        "prompt": PROMPT_STORY
    },
    {
        "id": "TASK_B2B_PRODUCTS",
        "node": "ai-digimate",
        "model": "gemini-3.8-flash-high",
        "prompt": PROMPT_B2B_AND_PRODUCTS
    }
]

def run_fleet_job(task):
    task_id = task["id"]
    node = task["node"]
    model = task["model"]
    print(f"[*] Dispatching {task_id} to node {node} ({model})...")
    
    payload = {
        "prompt": task["prompt"],
        "node_name": node,
        "model": model,
        "timeout": 240
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read().decode())
            job_id = res.get("job_id")
            actual_node = res.get("node_name", node)
            print(f"[✓] {task_id} queued as job {job_id} on {actual_node}")
    except Exception as e:
        print(f"[✗] {task_id} dispatch failed: {e}")
        return task_id, None

    for attempt in range(60):
        time.sleep(3)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                job_data = json.loads(r.read().decode())
                status = job_data.get("status")
                if status == "completed":
                    out = job_data.get("clean_response") or job_data.get("output") or ""
                    dur = time.time() - t0
                    print(f"[✓] {task_id} COMPLETED by {actual_node} in {dur:.1f}s ({len(out)} chars)")
                    return task_id, out
                elif status == "failed":
                    err = job_data.get("stderr") or "Job failed"
                    print(f"[✗] {task_id} FAILED: {err}")
                    return task_id, None
        except Exception:
            pass

    print(f"[!] {task_id} timed out after 180s")
    return task_id, None

def main():
    print("=" * 75)
    print("🚀 LAUNCHING INNOKAFE AGY FLEET PARALLEL SWARM (4 CONCURRENT NODES)")
    print("=" * 75)
    t_start = time.time()
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_fleet_job, t): t["id"] for t in TASKS}
        for future in as_completed(futures):
            task_id, out = future.result()
            results[task_id] = out

    out_dir = "/home/zen/O20/artifacts/fleet_swarm_results"
    os.makedirs(out_dir, exist_ok=True)
    for task_id, content in results.items():
        if content:
            path = os.path.join(out_dir, f"{task_id}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[✓] Saved {task_id} output to {path}")
        else:
            print(f"[!] No content for {task_id}")

    total_dur = time.time() - t_start
    print("=" * 75)
    print(f"🎉 FLEET PARALLEL SWARM COMPLETED IN {total_dur:.1f}s!")
    print("=" * 75)

if __name__ == "__main__":
    main()
