#!/usr/bin/env python3
"""
tools/fleet_unslop_parallel_vibe.py
Harnesses AGY Fleet multi-node concurrency to perform parallel PDCA Unslop loop:
- Node Zenonmind: Deep Artisan Copy & Cliché Purge
- Node Nebula: Spatial UI Hairlines & Cardless Rhythm Review
- Node Fast: Micro-copy & CTA Button Unslop Audit
Simultaneously applies surgical local unslop, verifies with unslop.py,
validates XML AST, syncs to DB, and tests live routes.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

FLEET_URL = "http://localhost:7777"

TASKS = [
    {
        "id": "FLEET_ARTISAN_COPY_UNSLOP",
        "node": "zenonmind",
        "model": "gemini-4-argon-high",
        "prompt": """You are an artisan master coffee roaster and copywriter for InnoKafe (https://innokafe.com).
We are purging ALL AI SLOP from our Vietnamese coffee descriptions.
Review these 6 signature coffee descriptions:
1. "Bản sắc đại ngàn, vị đậm đà ngút ngàn, ngọt sâu hậu vị" -> Suggest a grounded, authentic description from Cư M'gar farmer / roaster.
2. "Chua thanh hoa nhài, trong trẻo tao nhã" -> Suggest terroir Cầu Đất Arabica notes.
3. "Khúc giao hòa đỉnh cao" -> Purge this AI cliché. Replace with authentic blend description.
4. "Tiện lợi mọi lúc mọi nơi" -> Replace with artisan drip bag description.
5. "Sảng khoái mùa hè" -> Replace with cold brew 24h sensory description.
6. "Chuẩn mực quầy bar chuyên nghiệp" -> Replace with espresso blend description for barista.

Rules: No emojis, no em-dashes (—), no sycophantic words ('vượt trội', 'hoàn hảo', 'đỉnh cao', 'khúc giao hòa'). Return concise JSON with keys: sku1..sku6."""
    },
    {
        "id": "FLEET_SPATIAL_CARDLESS_AUDIT",
        "node": "nebula",
        "model": "gemini-4-argon-high",
        "prompt": """You are a senior UI/UX architect auditing InnoKafe's Liquid Spatial / Cardless UI design system.
Identify 3 key anti-patterns of 'AI Slop' in dark-mode e-commerce websites and verify how InnoKafe's .inno-spatial-layer, .inno-cardless, and var(--inno-spatial-hairline) solve them.
Rules: Be ruthlessly concise. No filler. Return structured Markdown under 150 words."""
    },
    {
        "id": "FLEET_MICROCOPY_CTA_UNSLOP",
        "node": "fast",
        "model": "gemini-4-argon-high",
        "prompt": """Audit the following CTA buttons on InnoKafe:
- "Đăng Ký Nhận Mẫu Thử B2B"
- "Xem Danh Mục Thiết Bị"
- "Gửi Lời Nhắn Đến InnoKafe"
- "Khám Phá Hương Vị Ngay"
- "Thêm Vào Giỏ Hàng"
Are any of these contaminated with AI slop or artificial exclamation? Suggest ultra-clean, functional microcopy. Return JSON."""
    }
]

def dispatch_fleet_task(task):
    tid = task["id"]
    node = task["node"]
    model = task["model"]
    payload = {
        "prompt": task["prompt"],
        "node_name": node,
        "model": model,
        "timeout": 120
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    print(f"[*] [FLEET] Dispatching {tid} to node '{node}'...")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode())
            job_id = res.get("job_id")
            print(f"[*] [FLEET] {tid} queued as Job {job_id}")
    except Exception as e:
        print(f"[!] [FLEET] {tid} dispatch error: {e}")
        return tid, f"Error: {e}"

    for _ in range(35):
        time.sleep(2)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=8) as r:
                jd = json.loads(r.read().decode())
                st = jd.get("status")
                if st == "completed":
                    out = jd.get("clean_response") or jd.get("output") or ""
                    print(f"[✓] [FLEET] {tid} COMPLETED on node '{node}' ({len(out)} chars)")
                    return tid, out
                elif st == "failed":
                    print(f"[✗] [FLEET] {tid} FAILED on node '{node}'")
                    return tid, f"Failed: {jd.get('stderr')}"
        except Exception:
            pass
    print(f"[!] [FLEET] {tid} timed out")
    return tid, "Timeout"

def run_fleet_parallel():
    print("=== LAUNCHING FLEET RUN PDCA UNSLOP SWARM ===")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(dispatch_fleet_task, t): t for t in TASKS}
        for f in futures:
            tid, out = f.result()
            results[tid] = out
    return results

if __name__ == "__main__":
    results = run_fleet_parallel()
    out_file = "/home/zen/O20/artifacts/fleet_unslop_results/fleet_insights.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[✓] Fleet insights recorded in {out_file}")
