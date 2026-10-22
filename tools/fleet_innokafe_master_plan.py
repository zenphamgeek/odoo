#!/usr/bin/env python3
"""
tools/fleet_innokafe_master_plan.py
=============================================================================
Phase 1 AGY Fleet Master Plan for InnoKafe:
Dispatches deep editorial & spatial UI planning to Claude Opus 5.5 nodes
(justaskgao & sunward) concurrently.
=============================================================================
"""

import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

FLEET_API = "http://localhost:7777/api/fleet/run-sync"

PROMPT_EDITORIAL_PLAN = """You are the Creative Director and Master Specialty Coffee Copywriter for InnoKafe (Vietnam Specialty Coffee).
TASK: Create the authoritative Editorial & Copywriting Overhaul Plan for InnoKafe (innokafe.com / innokafe.insilos.com).

USER INSTRUCTION:
"Tiến hành tìm kiếm thêm hình ảnh Pexel, các video nền, kiểm tra Pixel Scan các layout mất cân đối trong section , bỏ phong cách các thẻ card có border kì , vì visual nhìn như AI Slop , content cần viết lại tự nhiên. fleet_run toàn bộ UI/UX sử dụng Cardless / Liquid Spatial UI , không dùng bừa bãi"

CORE ANTI-SLOP DIRECTIVES:
1. BAN ALL AI MARKETING BUZZWORDS & JARGON:
   - Purge: "đẳng cấp thế giới", "đánh thức vị giác", "cuộc gặp gỡ của hai đỉnh cao", "4 trụ cột định hình đẳng cấp", "bảo chứng chất lượng", "giải pháp đỉnh cao", "công nghệ tiên tiến", "vươn tầm quốc tế", "thuật toán so khớp vector".
2. REPLACE WITH AUTHENTIC VIETNAMESE SPECIALTY COFFEE CRAFT:
   - Terroir: Cư M'gar (Đắk Lắk) - đất đỏ bazan cổ 70cm, khí hậu nhiệt đới gió mùa cho Robusta hạt chắc, đầm vị, nốt socola đen và mật mía; Cầu Đất (Trạm Hành, Đà Lạt) - độ cao 1.650m, khí hậu lạnh quanh năm, sương mù dày, hạt Arabica Typica/Bourbon cho hương hoa nhài, chanh bergamot và vị chua thanh sáng.
   - Craft: Thu hái 100% quả chín đỏ bằng tay; Phơi chậm tự nhiên 28 ngày trên giàn lưới cách mặt đất 80cm đón nắng gió Tây Nguyên; Rang mộc đối lưu bằng khí nóng Hot-Air (giữ trọn vị ngọt tự nhiên, không cháy cạnh, không tẩm bơ/bắp/hương liệu); Thử nếm cupping chuẩn SCA quốc tế đạt 84+ điểm.
   - Tone: Khiêm nhường, chân thành, tôn trọng công sức người nông dân vùng cao, sâu sắc về kỹ thuật nhưng gần gũi với người yêu cà phê mộc.
3. CONCRETE PLAN FOR EACH ROUTE:
   - Provide concrete copy guidelines and section-by-section rewrite directives for:
     1. Homepage (/)
     2. Story (/story)
     3. Products (/products)
     4. Taste Profiler (/taste-profiler)
     5. Solutions B2B (/solutions-b2b)
     6. Contact Us (/contactus)
Return your comprehensive plan in structured Markdown.
"""

PROMPT_CARDLESS_SPATIAL_PLAN = """You are the Principal Design System Architect & Spatial UI Director for InnoKafe.
TASK: Create the definitive Cardless / Liquid Spatial UI Architecture Plan for InnoKafe.

USER INSTRUCTION:
"bỏ phong cách các thẻ card có border kì , vì visual nhìn như AI Slop , fleet_run toàn bộ UI/UX sử dụng Cardless / Liquid Spatial UI , không dùng bừa bãi"

CORE ARCHITECTURAL DIRECTIVES:
1. WHAT IS "CARDLESS / LIQUID SPATIAL UI"?
   - An organic, continuous espresso-obsidian canvas (#0C0704) where content breathes freely without rigid rectangular cages or glowing border outlines.
   - Atmospheric depth created through multi-tier mesh gradients, delicate hairlines (rgba(255,255,255,0.06)), and diffused warm honey optical glows (0 20px 45px -15px rgba(0,0,0,0.85), 0 0 35px -8px rgba(212,136,66,0.16)).
   - Floating spatial pods (.inno-spatial-layer, .inno-floating-pod) with frosted glass backdrop-filter (blur(24px) saturate(160%)), but ZERO harsh borders (border-warning, border-secondary outlines completely eliminated).
2. DISCIPLINED RESTRAINT ("KHÔNG DÙNG BỪA BÃI"):
   - Define exact rules:
     * Where to use pure Cardless (open text, hairline dividers, fluid metric strips, hero layouts, value steps, quotes).
     * Where floating pods ARE permitted (interactive selectors, product purchase units, taste profiler options, contact form) and how they must blend seamlessly without rigid box aesthetics.
     * Zero nested boxes (no box inside another box).
3. SCSS & XML REFACTORING SPECIFICATION:
   - Provide exact CSS variables, SCSS class rules, and template markup replacements to eradicate all remaining border-warning, border-secondary, and boxy cards across InnoKafe.
Return your architectural specification in structured Markdown.
"""

def dispatch_task(task_id: str, prompt: str, node: str, model: str = "gemini-4-argon-high", timeout: int = 120):
    print(f"[*] Dispatching {task_id} to node {node} ({model})...")
    payload = {
        "prompt": prompt,
        "node_name": node,
        "model": model,
        "timeout": timeout
    }
    req = urllib.request.Request(
        FLEET_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout + 30) as res:
            data = json.loads(res.read().decode())
            dur = time.time() - t0
            output = data.get("clean_response") or data.get("output") or ""
            print(f"[✓] {task_id} finished on {node} in {dur:.1f}s ({len(output)} chars)")
            return task_id, output
    except Exception as e:
        dur = time.time() - t0
        print(f"[✗] {task_id} failed on {node} after {dur:.1f}s: {e}")
        return task_id, None

def main():
    print("=" * 70)
    print("🚀 DISPATCHING AGY FLEET MASTER PLANNING TO GEMINI 3.8 FLASH HIGH NODES")
    print("=" * 70)
    tasks = [
        ("EDITORIAL_PLAN", PROMPT_EDITORIAL_PLAN, "node-4"),
        ("CARDLESS_SPATIAL_PLAN", PROMPT_CARDLESS_SPATIAL_PLAN, "gaopham")
    ]
    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(dispatch_task, tid, prompt, node) for tid, prompt, node in tasks]
        for f in futures:
            tid, out = f.result()
            results[tid] = out

    out_dir = "/home/zen/O20/artifacts/fleet_plans"
    os.makedirs(out_dir, exist_ok=True)
    for tid, content in results.items():
        if content:
            path = os.path.join(out_dir, f"{tid}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[✓] Saved plan to {path}")

if __name__ == "__main__":
    main()
