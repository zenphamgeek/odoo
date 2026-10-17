#!/usr/bin/env python3
"""
Fleet Parallel Vibe-Coding Script: InnoKafe Un-Slop & Modernization Engine.
Dispatches prompt tasks across AGY Fleet nodes in parallel to refactor
snippets and views into pure craftsmanship, borderless canvas, and authentic
Vietnamese specialty coffee storytelling.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

FLEET_URL = "http://localhost:7777"

# Reliable nodes from fleet status
FLEET_NODES = ["pro-1", "team-3", "node-5", "binhthuong", "zenonmind"]


def validate_qweb_xml_safety(xml_string: str) -> None:
    """Parses generated QWeb XML and blocks unescaped t-raw XSS sinks."""
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as exc:
        raise ValueError(f"Generated output is not well-formed XML: {exc}") from exc

    for elem in root.iter():
        for attr in elem.attrib:
            if attr == "t-raw" or attr.endswith("}t-raw"):
                raise ValueError(
                    f"Security Policy Violation: Disallowed QWeb attribute '{attr}' in <{elem.tag}>. Use 't-out' instead."
                )
            val = elem.attrib[attr]
            if attr.startswith(("href", "src", "t-att-href", "t-att-src")) and "javascript:" in val.lower():
                raise ValueError(f"Security Policy Violation: javascript: URI detected in {attr}.")
            if attr.startswith("t-") and ("__" in val or "eval(" in val or "exec(" in val or "importlib" in val):
                raise ValueError(f"Security Policy Violation: unsafe expression in QWeb attribute {attr}.")

SYSTEM_PROMPT = """You are an elite Lead UI/UX Designer and Specialty Coffee Storyteller for InnoKafe (innokafe.insilos.com).
Your task is to un-slop QWeb XML views, replacing generic AI template clichés with authentic Vietnamese coffee craftsmanship.

MANDATORY RULES:
1. ZERO AI SLOP / BORDER PURGE:
   - Completely eliminate harsh border cards: replace `border-warning border-opacity-30`, `bg-black bg-opacity-60`, `border-secondary border-opacity-30` with `.inno-craft-card`, `.card-innokafe`, or borderless translucent glass `.inno-hero-vignette`.
   - No box-in-box nesting (e.g. inner dark boxes inside outer dark cards).
   - Use soft translucent backgrounds: rgba(28, 16, 10, 0.60) with backdrop-filter blur and subtle hairlines rgba(255,255,255,0.08).
2. STAR GLYPH FIX:
   - Never use FontAwesome stars `fa fa-star` (which render as broken boxes □).
   - Always use inline SVG golden stars:
     <div class="inno-stars">
         <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
         ...
         <span class="star-score">84.50 SCA</span>
     </div>
3. AUTHENTIC VIETNAMESE SPECIALTY COFFEE STORYTELLING:
   - Grounded facts: Cư M'gar (Đắk Lắk 750m, đất đỏ bazan), Cầu Đất (1.650m sương mù, Arabica Bourbon).
   - Processing: Phơi chậm trên giàn lưới 28 ngày (Natural), Lên men 32h nước ngầm (Washed), Giữ lớp nhầy đường (Honey).
   - Roasting: Khí nóng Hot-Air đối lưu mỗi tuần, Agtron 48-65, Mộc 4 Không (Không hương liệu, không bảo quản, không phẩm màu, không độn bắp đậu).
   - Ban words: 'đánh thức vị giác', 'định hình đẳng cấp', 'khúc giao hòa', 'vector 7 chiều', 'bậc thầy'.
4. PHOTOGRAPHY ASSETS:
   - Farm & Cherries: /innokafe_website/static/src/img/photography/farm_cherries_ripe.webp, farm_plantation_mist.webp
   - Artisan Craft: artisan_drying_sun.webp, artisan_roasting_beans.webp
   - Sensory & Lifestyle: sensory_cupping_flight.webp, extraction_pourover_v60.webp, extraction_espresso_crema.webp, lifestyle_barista_craft.webp, b2b_wholesale_packaging.webp
5. FORMAT:
   Return valid, well-formatted XML templates starting with <template id="..." and ending with </template>.
"""

def dispatch_fleet_job(task_name, prompt, node_name="pro-1", model="gemini-4-argon-high", timeout=180):
    payload = {
        "prompt": f"{SYSTEM_PROMPT}\n\nTASK [{task_name}]:\n{prompt}",
        "node_name": node_name,
        "model": model,
        "timeout": timeout
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode("utf-8"))
            job_id = res.get("job_id")
            assigned_node = res.get("node_name", node_name)
            print(f"[*] [{task_name}] Dispatched to Fleet -> Job {job_id} on {assigned_node}")
    except Exception as e:
        print(f"[!] [{task_name}] Dispatch failed: {e}")
        return task_name, None

    # Poll for completion
    for attempt in range(60):
        time.sleep(3)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                job_data = json.loads(r.read().decode("utf-8"))
                status = job_data.get("status")
                if status == "completed":
                    output = job_data.get("output", "") or job_data.get("clean_response", "")
                    duration = time.time() - t0
                    print(f"[✓] [{task_name}] Completed in {duration:.1f}s by {assigned_node} ({len(output)} chars)")
                    return task_name, output
                elif status == "failed":
                    print(f"[!] [{task_name}] Job {job_id} reported failed.")
                    return task_name, None
        except Exception as poll_err:
            time.sleep(1)

    print(f"[!] [{task_name}] Timed out waiting for job {job_id}")
    return task_name, None

if __name__ == '__main__':
    print("[*] Testing Fleet connection...")
    try:
        with urllib.request.urlopen(f"{FLEET_URL}/api/fleet/status", timeout=5) as r:
            st = json.loads(r.read().decode())
            print(f"[✓] Fleet status OK. Active model: {st.get('active_model')}")
    except Exception as e:
        print(f"[!] Cannot connect to fleet: {e}")
        sys.exit(1)
