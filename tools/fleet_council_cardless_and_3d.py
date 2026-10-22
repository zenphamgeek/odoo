#!/usr/bin/env python3
"""
tools/fleet_council_cardless_and_3d.py
=============================================================================
AGY Fleet Parallel Council for:
1. 3D Interactive Sections Layout & Zero-Collision Assurance
2. Mega-Menu Layout, Balanced Labels & SCSS Unification
3. Platform-wide Cardless / Liquid Spatial UI Enforcement (Không dùng bừa bãi)
=============================================================================
"""

import os
import sys
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

FLEET_URL = "http://localhost:7777"

PROMPT_3D_SECTIONS = """You are the Senior 3D Interactive Graphics & Layout Architect on the AGY Fleet Council.
Review and optimize the 3D interactive sections of the Innoria platform:
- s_innoria_3d_architecture_deck
- s_innoria_3d_topology
- s_innoria_3d_solutions_erp
- s_innoria_3d_erp_shift

USER INSTRUCTION:
"luôn bỏ các style để thông tin điều khiển này trong các section 3D interactive. fleet_run lập hội đồng Audit và chỉnh sửa các khối 3d Interactive, không cần thẻ Card lớn bao toàn khối có các text tên của card, hãy layout đủ rộng để các animation không bị chạm đến khối text ,content kế bên"

REQUIREMENTS TO FULFILL:
1. STRICTLY CARDLESS (100% Frameless Stage):
   - The 3D stage and container must have ZERO card borders, ZERO box backgrounds, ZERO outer box-shadows.
   - Stage card must be completely frameless (background: transparent !important, border: none !important).
   - No giant outer card wrapping the entire 3D block with title labels on top of the card.
2. REMOVE ALL CONTROL CLUTTER & INSTRUCTION TEXT:
   - Eliminate any residual instructional text ("Kéo chuột để xoay...", "Hover vào khối...", "Hardware 3D // 60 FPS", etc.).
   - Only sleek floating action controls in the header are allowed (Phân Rã Deck, Đặt Lại Góc, Auto Demo).
3. AMPLE LAYOUT SPACING & ZERO COLLISION:
   - Provide concrete SCSS values for `.deck-grid` and `.stage-card`:
     * Expand `.deck-grid` gap (e.g. from 36px to 56px or 64px) and increase stage column width (540px) so when 3D slabs are pulled out (--pull-x: 75px) or rotated in 3D orbit, they NEVER collide with or touch the right-hand description cards.
     * Ensure `.stage-card` has `overflow: visible !important;` so slabs are not clipped, with ample negative space.
4. Provide the exact SCSS rules and XML adjustments in clear code blocks.
"""

PROMPT_MENU_AND_SCSS = """You are the Lead Design System & Typography Specialist on the AGY Fleet Council.
Review and optimize the Mega-Menus and Snippet SCSS Unification:
- Files: enterprise/insilos_website/views/innoria_homepage.xml, enterprise/insilos_website/static/src/scss/insilos_megamenu.scss, enterprise/insilos_website/static/src/scss/insilos_liquid_spatial.scss

USER INSTRUCTION:
"tiếp tục rà soát các Menu layout, các label chưa đồng nhất, text còn dài gây nhảy dòng , cần thiết kế text đồng đều, các Label cũng cần làm cho premium hơng, thống nhất scss cho các custome snippets này dùng chung với Website main scss"

REQUIREMENTS TO FULFILL:
1. BALANCED TITLES & ZERO AWKWARD LINE WRAPPING:
   - Audit all menu item titles in Products, Platform, Solutions:
     * Simplify overly long titles: e.g. "Quản Trị Vỏ Container Depot" (27 chars) -> "Quản Trị Vỏ Container" (21 chars); "Trung Tâm Vận Tải Cảng Biển" (27 chars) -> "Vận Tải Cảng Biển" (17 chars); "Tài Chính Kế Toán (FI)" -> "Tài Chính Kế Toán"; "Mua Hàng & Đấu Thầu (MM)" -> "Mua Hàng & Đấu Thầu".
     * Ensure title and badge never wrap onto a second line awkwardly.
2. PREMIUM & UNIFIED LABELS (.ins-label-lux):
   - Standardize all badges to `.ins-label-lux` with consistent semantic categories:
     * .ins-label-lux-cyan (Tech, Intelligence, No-Code, AI)
     * .ins-label-lux-mint (Security, Verification, Pass)
     * .ins-label-lux-blue (Standards, Protocols, Rules, ISO)
     * .ins-label-lux-amber (Logistics, Cost, Operations)
     * .ins-label-lux-rose (Critical, Safety, LOTO)
3. SCSS FLEXBOX SAFETY:
   - In `insilos_megamenu.scss`:
     * `.ins-menu-link-item .flex-grow-1` must have `min-width: 0 !important;`
     * `.ins-menu-item-title` must have `flex: 1 1 auto; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;`
     * `.ins-label-lux` must have `flex-shrink: 0; margin-left: 0.5rem;`
4. SCSS UNIFICATION FOR CUSTOM SNIPPETS:
   - Ensure all custom snippets reuse variables from `insilos_liquid_spatial.scss` (--ins-obsidian-deep, --ins-spatial-border-glow, .ins-cardless-*, .ins-label-lux).
   - Provide concrete SCSS and XML updates in clear code blocks.
"""

PROMPT_CARDLESS_PLATFORM = """You are the Principal UX Architect on the AGY Fleet Council.
Review and validate the Cardless / Liquid Spatial UI enforcement across the entire Innoria platform.

USER INSTRUCTION:
"fleet_run toàn bộ UI/UX sử dụng Cardless / Liquid Spatial UI , không dùng bừa bãi"

REQUIREMENTS TO FULFILL:
1. DISCIPLINED RESTRAINT ("Không dùng bừa bãi"):
   - What elements MUST be cardless:
     * 3D stages, canvases, video players (floating on continuous obsidian canvas).
     * Cadence timeline steps (.innoria-cadence-step with top hairline accent, 0 card background).
     * Solution blocks (.ins-cardless-solution with open negative space, hairlines).
     * Metric & KPI displays (.ins-cardless-kpi with bold numbers, hairlines).
     * Quotes & citations (.ins-cardless-quote with left accent line).
     * Ecosystem partner pills (.ins-cardless-partner).
   - Where floating surfaces ARE permitted:
     * Only when grouping is semantically necessary: live preview card in mega-menu (.ins-preview-card), ERP shift comparison matrix table, and VIP contact form.
     * Never nested inside another card (zero double-containment).
2. Produce a concise audit checklist and verify that the platform achieves pure Cardless / Liquid Spatial elegance.
"""

TASKS = [
    {
        "id": "TASK-1-3D-SECTIONS",
        "prompt": PROMPT_3D_SECTIONS,
        "node": "pro-1",
        "model": "gemini-4-argon-high"
    },
    {
        "id": "TASK-2-MENU-AND-SCSS",
        "prompt": PROMPT_MENU_AND_SCSS,
        "node": "codegeekvn",
        "model": "gemini-4-argon-high"
    },
    {
        "id": "TASK-3-CARDLESS-PLATFORM",
        "prompt": PROMPT_CARDLESS_PLATFORM,
        "node": "zenonmind",
        "model": "gemini-4-argon-high"
    }
]

def run_fleet_job(task):
    task_id = task["id"]
    print(f"[*] Dispathing {task_id} to node {task['node']} ({task['model']})...")
    payload = {
        "prompt": task["prompt"],
        "node_name": task["node"],
        "model": task["model"],
        "timeout": 180
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            job_id = res.get("job_id")
            actual_node = res.get("node_name", task["node"])
            print(f"[✓] {task_id} queued as job {job_id} on {actual_node}")
    except Exception as e:
        print(f"[!] {task_id} dispatch failed: {e}")
        return task_id, None

    for _ in range(40):
        time.sleep(3)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                job_data = json.loads(r.read().decode())
                status = job_data.get("status")
                if status == "completed":
                    out = job_data.get("output", "") or job_data.get("clean_response", "")
                    print(f"[✓] {task_id} finished ({len(out)} chars)")
                    return task_id, out
                elif status == "failed":
                    print(f"[!] {task_id} reported failure")
                    return task_id, None
        except Exception:
            pass

    print(f"[!] {task_id} timed out")
    return task_id, None

def main():
    print("=== AGY FLEET PARALLEL COUNCIL DISPATCH ===")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_fleet_job, t): t["id"] for t in TASKS}
        for future in as_completed(futures):
            task_id, out = future.result()
            results[task_id] = out

    os.makedirs("/tmp/fleet_council_results", exist_ok=True)
    for task_id, out in results.items():
        if out:
            path = f"/tmp/fleet_council_results/{task_id}.txt"
            with open(path, "w") as f:
                f.write(out)
            print(f"[✓] Saved {task_id} result to {path}")
        else:
            print(f"[!] No result for {task_id}")

if __name__ == "__main__":
    main()
