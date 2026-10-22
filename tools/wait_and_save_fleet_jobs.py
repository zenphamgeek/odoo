#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request

FLEET_URL = "http://localhost:7777"

JOB_MAP = {
    "HERO_AND_RIBBON": "d0b4b265-55dd-4b60-b596-1794b1e820f7",
    "CRAFT_AND_TERROIR": "23381f69-b474-4231-b8d1-e46c769b65a5",
    "TASTE_PROFILER_AND_PRODUCTS": "c3f470da-a015-4663-befb-0c40ac91dbf3",
    "TASTING_BAR_AND_B2B": "56f7ca17-cb6b-4789-b710-d11a86ff581a",
    "REVIEWS_AND_CTA": "92b891b4-eb07-465b-9b9a-99f1221e270a"
}

out_dir = "/home/zen/O20/artifacts/fleet_swarm_results"
os.makedirs(out_dir, exist_ok=True)

remaining = dict(JOB_MAP)
start_t = time.time()

print("Waiting for running jobs to finish...")
while remaining and (time.time() - start_t < 360):
    for task_id, jid in list(remaining.items()):
        try:
            r = urllib.request.urlopen(f"{FLEET_URL}/api/fleet/jobs/{jid}", timeout=10)
            data = json.loads(r.read().decode())
            status = data.get("status")
            if status == "completed":
                out = data.get("clean_response") or data.get("output") or ""
                path = os.path.join(out_dir, f"{task_id}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(out)
                print(f"[✓] {task_id} COMPLETED ({len(out)} chars) -> saved to {path}")
                del remaining[task_id]
            elif status == "failed":
                err = data.get("stderr") or "unknown"
                print(f"[✗] {task_id} FAILED: {err}")
                del remaining[task_id]
            else:
                pass
        except Exception as e:
            print(f"[!] Error polling {task_id}: {e}")
    if remaining:
        time.sleep(5)

if remaining:
    print(f"[!] Timed out waiting for: {list(remaining.keys())}")
else:
    print("🎉 ALL FLEET JOBS COMPLETED SUCCESSFULLY!")
