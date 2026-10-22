#!/usr/bin/env python3
"""
tools/fleet_innokafe_artisan_elevation.py
Dispatches parallel prompts to AGY Fleet to generate high-end artisan coffee graphics,
interactive animations, and non-slop editorial layouts for InnoKafe.
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

FLEET_URL = "http://localhost:7777"

TASKS = [
    {
        "id": "ARTISAN_SVG_AND_GRAPHICS",
        "node": "zenonmind",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite graphic designer and SVG artist for luxury specialty coffee brands (like Onyx Coffee Lab, Blue Bottle, Kurasu Kyoto).
Design 3 pure SVG vector components for InnoKafe Specialty Coffee Vietnam:

1. Circular Artisan Roaster Stamp / Seal:
   - A circular vintage hot-foil stamp with circular text wrapping around the perimeter via <textPath>:
     "★ INNOKAFE SPECIALTY ROASTERY ★ CƯ M'GAR & CẦU ĐẤT TERROIR ★ DIRECT TRADE ★"
   - Inner core with coffee branch / cherry / roaster flame monogram.
   - Clean, scalable, viewbox="0 0 160 160", warm amber (#D48842) and gold accents, with a CSS class "inno-artisan-stamp" suitable for rotating animation.

2. Highland Topographic Contour Lines SVG Pattern:
   - Elevation contour curves representing the Langbiang / Cầu Đất 1.650m mountain peaks and Cư M'gar basalt plateau.
   - Clean vector lines with subtle stroke-width, suitable as an atmospheric background overlay with opacity.
   - ViewBox="0 0 800 300", stroke="rgba(212, 136, 66, 0.25)", fill="none".

3. 5 Vector Line-Art Icons for Brewing Methods:
   - Phin Nhôm Việt Nam (Vietnamese traditional gravity drip phin)
   - Espresso 9-Bar Portafilter
   - Conical Pour-Over V60 dripper
   - Cold Brew extraction flask / tower
   - Aeropress cylinder
   - Clean 48x48 viewBox, stroke="currentColor", stroke-width="2", fill="none".

OUTPUT FORMAT:
Return pure, valid XML / SVG blocks with clean CSS classes. Do not use external images."""
    },
    {
        "id": "ARTISAN_SCSS_ANIMATIONS",
        "node": "pro-1",
        "model": "gemini-4-argon-high",
        "prompt": """You are a master CSS/SCSS animation engineer for award-winning editorial websites (Awwwards, Standart Mag).
Write high-performance SCSS animations and visual effects for InnoKafe:

1. `@keyframes inno-stamp-spin`: Smooth, 30-second continuous linear rotation for the roaster stamp.
2. `@keyframes inno-telemetry-marquee`: Infinite horizontal ticker scroll for the live roastery batch ticker.
3. `@keyframes inno-liquid-glow`: Subtle breathing ambient glow for cardless spatial containers using var(--inno-spatial-glow).
4. `.inno-roaster-passport`: Styling for the artisan cupping ledger / roaster passport card (vintage paper texture feel, tactile monospace typography, Agtron color indicator chips, clean hairline borders).
5. `.inno-topographic-bg`: Background styling for the highland elevation contour overlay with soft radial fade.
6. `.inno-sensor-tag`: Pill tags with tactile micro-color dot for flavor notes (Chocolate, Jasmine, Hazelnut, Honey, Bergamot).

CRITICAL ANTI-SLOP RULES:
- ZERO synthetic inline styles.
- ZERO hardcoded bare white surfaces or forbidden hex fallbacks with !important.
- Use native Odoo / InnoKafe semantic variables: var(--inno-spatial-bg), var(--inno-spatial-hairline), var(--inno-amber), var(--inno-espresso-dark).

OUTPUT FORMAT:
Return clean SCSS code ready to be appended to innokafe_liquid_spatial.scss."""
    },
    {
        "id": "ARTISAN_HOMEPAGE_SECTIONS",
        "node": "ultra-2",
        "model": "gemini-4-argon-high",
        "prompt": """You are the Lead Creative Director & Odoo QWeb Architect for InnoKafe (Vietnam Specialty Coffee).
Architect a revised, non-slop layout for two crucial sections of enterprise/innokafe_website/views/home.xml:

1. Live Roastery Telemetry & Roasting Curve Lab Section:
   - A live roaster ticker ribbon at top of section:
     "● BATCH #0849 IN DRUM: 204.2°C (RoR +8.4°C/min) · 1.650m CẦU ĐẤT ARABICA · SCA SCORE: 86.75 · RANG MỚI MỖI THỨ TƯ"
   - An artisan Roast Science interactive teaser integrating the Bean Temp (BT) & Rate of Rise (RoR) curve preview, allowing visitors to inspect roasting profiles directly on the homepage.
   - Roaster's tasting notes and Agtron classification.

2. Micro-Lot Terroir Flight & Roaster's Passport (Replacing generic 3-card grid):
   - Asymmetric layout featuring a flagship single-origin micro-lot:
     "Fine Robusta Cư M'gar Anaerobic Natural (SCA 84.50)" with its full roaster passport (Elevation 750m, Soil Basaltic Loam, Fermentation 72h, Agtron 48, Tasting Notes chips: Dark Cacao, Hazelnut, Molasses).
   - Paired with Arabica Bourbon Cầu Đất (1.650m, SCA 86.75) and Heritage Blend Red Honey.
   - Interactive flavor chips and cupping score medals.

OUTPUT FORMAT:
Return valid QWeb XML template code conforming to Odoo 20 standards (t-out, data-snippet, o_colored_level o_cc o_cc5)."""
    }
]

def dispatch_task(task):
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
        return tid, None

    for _ in range(40):
        time.sleep(2)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                jd = json.loads(r.read().decode())
                st = jd.get("status")
                if st == "completed":
                    out = jd.get("clean_response") or jd.get("output") or ""
                    print(f"[✓] [FLEET] {tid} COMPLETED on node '{node}' ({len(out)} chars)")
                    return tid, out
                elif st == "failed":
                    print(f"[✗] [FLEET] {tid} FAILED on node '{node}'")
                    return tid, None
        except Exception:
            pass
    print(f"[!] [FLEET] {tid} timed out")
    return tid, None

def main():
    print("=== AGY FLEET PARALLEL ARTISAN ELEVATION SWARM ===")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(dispatch_task, t): t for t in TASKS}
        for f in futures:
            tid, out = f.result()
            results[tid] = out

    out_file = "/home/zen/O20/artifacts/innokafe_e2e/fleet_artisan_outputs.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[✓] Results written to {out_file}")

if __name__ == "__main__":
    main()
