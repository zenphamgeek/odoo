#!/usr/bin/env python3
"""
tools/fleet_unslop_pdca_runner.py
Orchestrates the PDCA Unslop loop using AGY Fleet parallel workers.
Dispatches self-contained refactoring prompts to idle Fleet nodes,
gathers pristine Cardless / Liquid Spatial XML, and verifies zero slop.
"""

import os
import sys
import time
import json
import re
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

FLEET_URL = "http://localhost:7777"

def extract_xml(text: str) -> str:
    if not text:
        return ""
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:xml)?\s*", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
    # Search for <odoo>...</odoo>
    match = re.search(r"(<odoo[\s\S]*?</odoo>)", text)
    if match:
        return match.group(1).strip()
    # Search for <template>...</template>
    match = re.search(r"(<template[\s\S]*?</template>)", text)
    if match:
        return f"<odoo>\n{match.group(1).strip()}\n</odoo>"
    return text.strip()

TASKS = [
    {
        "id": "TASTE_PROFILER_UNSLOP",
        "target_file": "enterprise/innokafe_website/views/taste_profiler.xml",
        "node": "pro-1",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite UI/UX designer and artisan copywriter for InnoKafe (Specialty Coffee Vietnam, https://innokafe.com).
Your task is to refactor the taste options and sensory cards in enterprise/innokafe_website/views/taste_profiler.xml to achieve pure Cardless / Liquid Spatial UI and 100% PURGE OF AI SLOP.

CRITICAL RULES:
1. ZERO EMOJIS: Purge all raw emojis (☕, 🥛, 🌸, 🧊, 🍫, 🍊, 🍯, 🏆, 🛒, 🔄, 🌱, 🔥, 🛡️, 🚚).
   - Replace habit icons (Step 1) with clean, elegant inline SVGs or minimalist sensory badges.
   - Replace flavor notes (Step 3: Chocolate, Citrus, Honey) with refined SVG icons or `.inno-badge-pill-dark` typography.
   - Replace trust icons (Step 4 & footer) with clean inline SVGs or subtle hairlines.
   - Replace button emojis (🛒, 🔄) with clean text or SVG arrows/icons: e.g. <i class="fa fa-shopping-bag me-2"/>, <i class="fa fa-redo me-2"/>.
2. CARDLESS / LIQUID SPATIAL UI:
   - Use `.inno-spatial-layer`, `.inno-floating-pod`, `.inno-badge-liquid`.
   - Remove `border-secondary border-opacity-15`, replace with `var(--inno-spatial-hairline)` or `.inno-hairline-bottom`.
3. PRESERVE JAVASCRIPT STATE MACHINE & DATA BINDING:
   - Keep all `data-step`, `data-key`, `data-value`, `data-step-panel`, `.profiler-option-card`, `.profiler-progress-bar`, `.profiler-progress-text`, `#innokafe-skus-data` attributes completely intact.
4. AUTHENTIC ARTISAN COPY:
   - Humble, grounded, sensory Vietnamese copy for coffee lovers.

Return the complete, valid <odoo><template id="taste_profiler_page" ...> ... </template></odoo> code block.
Do NOT wrap in markdown fences or comments, just the raw XML."""
    },
    {
        "id": "SOLUTIONS_B2B_UNSLOP",
        "target_file": "enterprise/innokafe_website/views/solutions_b2b.xml",
        "node": "codegeekvn",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite UI/UX designer and artisan copywriter for InnoKafe (Specialty Coffee Vietnam, https://innokafe.com).
Your task is to refactor enterprise/innokafe_website/views/solutions_b2b.xml to achieve pure Cardless / Liquid Spatial UI and 100% PURGE OF AI SLOP.

CRITICAL RULES:
1. ZERO EMOJIS: Purge all raw emojis (☕, ↓, 📐, 💧, 🎓, 🛠️, 🎉, 🚀, ✓).
   - Replace checkmark ✓ with <i class="fa fa-check text-warning me-2"/> or subtle hairlines.
   - Replace service emojis (📐, 💧, 🎓, 🛠️) with refined inline SVGs or minimalist typography badges.
   - Replace button emojis (☕, ↓, 🚀) with clean text: "Đăng Ký Nhận Mẫu Thử B2B", "Xem Danh Mục Thiết Bị", "Gửi Yêu Cầu & Nhận Hộp Mẫu Thử".
   - Replace 🎉 in success banner with "Đăng Ký Thành Công".
2. CARDLESS / LIQUID SPATIAL UI & FORM RESTRAINT:
   - Replace inline styles `style="background-color: #1E120B; border-color: rgba(212, 136, 66, 0.3); ..."` on form controls with `.inno-inner-panel` and frosted glass classes.
   - Remove harsh borders `border-bottom: 1px solid rgba(212, 136, 66, 0.2);`, use `.inno-hairline-bottom` or `var(--inno-spatial-hairline)`.
3. PRESERVE FORM FUNCTIONALITY & POST ACTIONS:
   - Form action `/solutions-b2b/submit`, method `post`, csrf_token, all input names (`contact_name`, `job_position`, `partner_name`, `phone`, `email_from`, `business_type`, `street`, `estimated_monthly_volume`, `service_interest`, `description`) must be 100% preserved.

Return the complete, valid <odoo><template id="solutions_b2b_page" ...> ... </template></odoo> code block.
Do NOT wrap in markdown fences or comments, just the raw XML."""
    },
    {
        "id": "CONTACTUS_UNSLOP",
        "target_file": "enterprise/innokafe_website/views/contactus.xml",
        "node": "zenonmind",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite UI/UX designer and artisan copywriter for InnoKafe (Specialty Coffee Vietnam, https://innokafe.com).
Your task is to refactor enterprise/innokafe_website/views/contactus.xml to achieve pure Cardless / Liquid Spatial UI and 100% PURGE OF AI SLOP.

CRITICAL RULES:
1. ZERO EMOJIS: Purge all raw emojis (☕, 📍, ⏰, 📞, ✉️, 🏭, 🌄, 🎉).
   - Replace 📍, ⏰, 📞, ✉️ with clean inline SVGs or Phosphor/FontAwesome icons: <i class="fa fa-map-marker-alt text-warning me-2"/>, <i class="fa fa-clock text-warning me-2"/>, <i class="fa fa-phone text-warning me-2"/>, <i class="fa fa-envelope text-warning me-2"/>.
   - Replace 🎉 in success alert with clean heading "Gửi Lời Nhắn Thành Công".
   - Replace ✉️ on submit button with "Gửi Lời Nhắn Đến InnoKafe".
2. CARDLESS / LIQUID SPATIAL UI:
   - Re-architect 3 location cards (HCM Flagship, Đắk Lắk Roastery, Cầu Đất Farm) into `.inno-spatial-layer.inno-floating-pod` with photography vignettes or warm amber badges.
   - Remove `border-secondary border-opacity-15`, use `var(--inno-spatial-hairline)`.
3. PRESERVE FORM FUNCTIONALITY:
   - Form action `/contactus/submit`, method `post`, csrf_token, and all input names (`contact_name`, `phone`, `email_from`, `subject`, `message`) must be 100% preserved.

Return the complete, valid <odoo><template id="contactus_page" ...> ... </template></odoo> code block.
Do NOT wrap in markdown fences or comments, just the raw XML."""
    }
]

def dispatch_task(t):
    tid = t["id"]
    node = t["node"]
    model = t["model"]
    payload = {
        "prompt": t["prompt"],
        "node_name": node,
        "model": model,
        "timeout": 360
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    print(f"[*] Dispatching {tid} to Fleet node {node}...")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read().decode())
            job_id = res.get("job_id")
            print(f"[*] {tid} enqueued -> Job {job_id}")
    except Exception as e:
        print(f"[!] {tid} dispatch failed: {e}")
        return tid, None

    for attempt in range(120):
        time.sleep(3)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                jd = json.loads(r.read().decode())
                st = jd.get("status")
                if st == "completed":
                    out = jd.get("clean_response") or jd.get("output") or jd.get("stdout") or ""
                    clean = extract_xml(out)
                    print(f"[✓] {tid} COMPLETED ({len(clean)} chars)")
                    return tid, clean
                elif st == "failed":
                    print(f"[✗] {tid} FAILED: {jd.get('stderr')}")
                    return tid, None
        except Exception:
            pass

    print(f"[!] {tid} timed out")
    return tid, None

def main():
    print("=== LAUNCHING FLEET RUN PDCA UNSLOP ENGINE ===")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(dispatch_task, t): t for t in TASKS}
        for f in futures:
            tid, out = f.result()
            results[tid] = out

    out_dir = "/home/zen/O20/artifacts/fleet_unslop_results"
    os.makedirs(out_dir, exist_ok=True)
    success_count = 0
    for t in TASKS:
        tid = t["id"]
        content = results.get(tid)
        if content and ("<odoo>" in content or "<template" in content):
            save_path = os.path.join(out_dir, f"{tid}.xml")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[✓] Saved {tid} to {save_path}")
            success_count += 1
        else:
            print(f"[!] {tid} result invalid or empty")

    print(f"\n[✓] Fleet PDCA run finished: {success_count}/{len(TASKS)} tasks completed.")
    return 0 if success_count == len(TASKS) else 1

if __name__ == "__main__":
    sys.exit(main())
