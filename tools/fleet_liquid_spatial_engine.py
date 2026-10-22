#!/usr/bin/env python3
"""
tools/fleet_liquid_spatial_engine.py
=============================================================================
Fleet-driven Cardless & Liquid Spatial UI Engine for InnoKafe.
Harnesses AGY Fleet nodes (pro-1, team-3, node-5, insilos) to architect,
synthesize, and validate the Liquid Spatial UI conversion across all views.
=============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

FLEET_URL = "http://localhost:7777"

FLEET_PROMPT = """You are the Lead Visual Architect for InnoKafe (innokafe.insilos.com).
We are implementing the "Cardless / Liquid Spatial UI" design system across the entire InnoKafe platform.

MANDATORY DESIGN SYSTEM SPECIFICATION:
1. CORE PHILOSOPHY:
   - CARDLESS: Eliminate rigid boxy card containers, thick border outlines, and nested box-in-box structures. Elements float directly on the continuous atmospheric Liquid Spatial canvas.
   - LIQUID SPATIAL: Translucent glass layers with backdrop-filter blur(24px) saturate(160%), subtle hairlines (rgba(255,255,255,0.06)), diffused ambient warm honey glows (rgba(212, 136, 66, 0.14)), and deep elevation shadows.
   - KHÔNG DÙNG BỪA BÃI (DISCIPLINED RESTRAINT): Clean negative space, open coordinates, uncluttered typography rhythm. No random glowing borders or decorative noise.

2. PALETTE TOKENS:
   - Deep Espresso Obsidian Canvas: #0C0704
   - Atmospheric Terroir Canvas: #130B07
   - Liquid Amber Honey: #D48842
   - Radiant Honey Gold: #F59E0B
   - Espresso Crema Gold: #E5A967
   - Foam Cream High-Contrast Body: #F7F2EA (17.5:1 WCAG AAA on obsidian)
   - Spatial Hairline: rgba(255, 255, 255, 0.06)

3. PRIMITIVE CLASSES:
   - .inno-cardless: Pure borderless element with no box background, flowing with editorial typography.
   - .inno-cardless--bordered-bottom: Borderless with subtle hairline bottom divider (rgba(255,255,255,0.06)).
   - .inno-spatial-layer: Soft frosted surface (rgba(22, 12, 7, 0.55)), backdrop-filter blur(24px), 1px hairline border rgba(255,255,255,0.06), 0 20px 50px rgba(0,0,0,0.40).
   - .inno-spatial-layer--elevated: Elevated with ambient amber honey aura.
   - .inno-floating-pod: Hover lift with transform translateY(-4px) and smooth cubic-bezier easing.
   - .inno-fluid-strip: Horizontal fluid metadata strip without boxed cards.
   - .inno-badge-liquid: High-contrast WCAG AAA badge.

Return the production-ready SCSS stylesheet code enclosed in ```scss ... ```.
"""

def generate_liquid_spatial_scss():
    print("[*] Requesting Liquid Spatial SCSS Architecture from AGY Fleet (pro-1)...")
    payload = {
        "prompt": FLEET_PROMPT,
        "node_name": "pro-1",
        "model": "gemini-4-argon-high",
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
            node = res.get("node_name", "pro-1")
            print(f"[✓] Dispatched job {job_id} to node {node}")
    except Exception as e:
        print(f"[!] Fleet dispatch failed: {e}")
        return None

    for _ in range(40):
        time.sleep(3)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                job_data = json.loads(r.read().decode())
                if job_data.get("status") == "completed":
                    out = job_data.get("output", "") or job_data.get("clean_response", "")
                    print(f"[✓] Fleet job {job_id} completed successfully ({len(out)} chars)")
                    return out
                elif job_data.get("status") == "failed":
                    print(f"[!] Job {job_id} reported failure.")
                    return None
        except Exception:
            pass

    print("[!] Fleet request timed out.")
    return None

if __name__ == '__main__':
    result = generate_liquid_spatial_scss()
    if result:
        with open("/tmp/fleet_liquid_spatial_response.txt", "w") as f:
            f.write(result)
        print("[✓] Saved fleet response to /tmp/fleet_liquid_spatial_response.txt")
    else:
        sys.exit(1)
