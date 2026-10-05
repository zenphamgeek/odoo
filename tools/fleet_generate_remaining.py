#!/usr/bin/env python3
"""
tools/fleet_generate_remaining.py
=============================================================================
Dispatches the remaining 5 pages to 9router / Fleet with model 'codex',
extracts pristine QWeb XML, and saves them to /tmp/innoria_fleet_results/.
=============================================================================
"""

import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, '/home/zen/O20/tools')
from fleet_redesign_innoria_pages import PAGES_SPEC, clean_xml_output

REMAINING_KEYS = ['ai_platform', 'no_code', 'erp_ai', 'ultra_ai_vision', 'contactus']
TARGET_SPECS = [p for p in PAGES_SPEC if p['key'] in REMAINING_KEYS]

def process_page(spec):
    key = spec['key']
    template_id = spec['template_id']
    template_name = spec['name']
    prompt = spec['prompt']
    out_file = f"/tmp/innoria_fleet_results/{key}.xml"
    
    print(f"[*] Starting [{spec['name']}] on 9router (codex)...")
    payload = {
        "prompt": prompt,
        "model": "codex",
        "node_name": "9router",
        "timeout": 300
    }
    
    req = urllib.request.Request(
        "http://localhost:7777/api/fleet/run-sync",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=320) as res:
            data = json.loads(res.read().decode("utf-8"))
            elapsed = time.time() - start_t
            raw = data.get("output") or data.get("clean_response") or ""
            print(f"[✓] [{spec['name']}] completed in {elapsed:.1f}s ({len(raw)} chars)")
            cleaned = clean_xml_output(raw, template_id, template_name)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(cleaned)
            print(f"[✓] Saved {key} -> {out_file} ({len(cleaned)} chars)")
            return True
    except Exception as e:
        elapsed = time.time() - start_t
        print(f"[✗] [{spec['name']}] failed after {elapsed:.1f}s: {e}")
        return False

def main():
    print(f"=== DISPATCHING {len(TARGET_SPECS)} PAGES TO 9ROUTER / CODEX ===")
    os.makedirs("/tmp/innoria_fleet_results", exist_ok=True)
    
    start_total = time.time()
    # Run with 3 parallel workers so 9router pool easily handles them
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(process_page, TARGET_SPECS))
        
    total_elapsed = time.time() - start_total
    success_count = sum(1 for r in results if r)
    print("=" * 60)
    print(f"Finished {success_count}/{len(TARGET_SPECS)} pages in {total_elapsed:.1f}s.")
    return 0 if success_count == len(TARGET_SPECS) else 1

if __name__ == "__main__":
    sys.exit(main())
