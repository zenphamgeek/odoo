#!/usr/bin/env python3
"""
tools/fleet_master_marketing_audit.py
Dispatches comprehensive DOM and visual audit data of innoria.com across all 8 routes
to AGY Fleet (Claude Opus: claude-opus-4-6-thinking) for an uncompromising, unslop
Master Marketing Audit and Section Premium Upgrade Blueprint.
"""
import json
import os
import sys
import urllib.request
import urllib.error

FLEET_API_URL = "http://localhost:7777/api/fleet/run"
MANIFEST_PATH = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/audit_innoria_com_routes/innoria_routes_audit_manifest.json"
OUTPUT_REPORT_PATH = "/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/INNORIA_MASTER_MARKETING_AUDIT_OPUS.md"

def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_opus_audit_prompt(manifest):
    routes_summary = []
    for r in manifest.get("routes", []):
        route_info = {
            "name": r.get("name"),
            "route": r.get("route"),
            "section_count": r.get("section_count"),
            "sections": [
                {
                    "index": s.get("index"),
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "snippet": s.get("snippet"),
                    "headings": s.get("headings"),
                    "eyebrow": s.get("eyebrow"),
                    "textExcerpt": s.get("textExcerpt")
                }
                for s in r.get("sections", [])
            ]
        }
        routes_summary.append(route_info)

    prompt = f"""You are the Lead B2B Enterprise Creative Director, Product Marketing Architect, and Adversarial Conversion Auditor.
You adhere strictly to the "Unslop" Engineering Standard: ZERO sycophancy, ZERO AI fluff, ZERO generic buzzwords ('revolutionize', 'seamlessly', 'tapestry', 'crucial', 'vibrant', 'chuyển đổi số toàn diện').
Every evaluation must be sharp, technical, and candid.

CONTEXT:
innoria.com is the sovereign enterprise technology flagship platform comprising 8 primary routes:
1. `/` (Homepage — Sovereign Enterprise Technology)
2. `/about` (Company Heritage, 18-Year Engineering Depth, Leadership & Culture)
3. `/platform` (MOJO AI Autonomous Multi-Agent Swarm Platform)
4. `/no-code-platform` (DIGIFORCE Sovereign Low-Code Engine)
5. `/blockchain` (ZenCode Enterprise OS & Cryptographic Ledger)
6. `/solutions` (INSILOS Autonomous Operations Platform & ERP)
7. `/industries` (Industrial Ultra AI Vision & YOLO Edge Inference)
8. `/contactus` (Executive 3-Hour Architecture Consultation Booking)
Plus Global Components: INNORIA Navbar & INNORIA Footer.

AUDIT MANIFEST EXTRACTED FROM LIVE PRODUCTION INNORIA.COM:
{json.dumps(routes_summary, ensure_ascii=False, indent=2)}

TASK:
Perform a deep, candid, section-by-section Master Marketing Audit and formulate the definitive "Section Premium Master Plan" for 100% of sections across all routes without lazy omissions.

REQUIRED REPORT STRUCTURE:

# 1. EXECUTIVE DIAGNOSTIC & STRATEGIC POSITIONING AUDIT
- Honest critique of the current positioning across innoria.com: Is it genuinely perceived as an elite sovereign enterprise powerhouse (Palantir/Stripe/Snowflake tier) or does it still suffer from agency clichés, uneven typography, or mixed messaging?
- Cognitive friction & trust deficits: Where do Enterprise CIOs/CTOs hesitate?
- Authority & proof-point gaps: Missing verifiable telemetry, overused abstractions, and unproven claims.

# 2. GLOBAL COMPONENTS SECTION PREMIUM AUDIT
- `innoria_navbar`: Evaluation of layout, hierarchy, mobile responsiveness, mega-menu density, language switcher, and primary CTA efficacy. Concrete premium upgrades.
- `innoria_footer`: Evaluation of authority, trust badges, enterprise coordinates, sitemap taxonomy. Concrete premium upgrades.

# 3. ROUTE-BY-ROUTE, SECTION-BY-SECTION DEEP AUDIT & PREMIUM BLUEPRINT
Cover EVERY SINGLE ROUTE and EVERY SINGLE SECTION documented in the manifest:
For each section:
- **Section ID & Baseline Purpose**: Current snippet, title, and function.
- **Candid Adversarial Critique (The "Unslop" Verdict)**: What is weak, generic, redundant, or confusing? Where is the visual or copy friction?
- **Section Premium Architecture**:
  * Upgraded Positioning & Headline (Vietnamese & English where applicable)
  * High-Converting Technical Copy & Micro-Proof Points (replacing fluff with hard metrics)
  * Visual, 3D, Interactive or Kinetic Mechanics (e.g. volumetric 3D slabs, telemetry feeds, interactive toggles, micro-charts)
  * SCSS & Component Tokens (contrast, border-radius, elevation, dark/light coherence)

# 4. SECTION PREMIUM IMPLEMENTATION MATRIX & PARALLEL EXECUTION SCHEDULE
- Comprehensive summary matrix: Route | Section Name | Current Score (1-10) | Primary Friction | Premium Upgrade Priority (P0/P1) | Target Model for Parallel Vibe Coding.

Tone: Searing, candid, professional, high-agency engineering and marketing masterclass. Return in rich Markdown.
"""
    return prompt

def run_fleet_audit():
    manifest = load_manifest()
    prompt = build_opus_audit_prompt(manifest)
    print(f"[Master Marketing Audit] Prepared prompt with {len(prompt)} characters.")
    print(f"[Master Marketing Audit] Dispatching to Fleet API at {FLEET_API_URL} using model claude-opus-4-6-thinking ...")

    payload = {
        "node_name": "zenonmind",
        "model": "gemini-3.1-pro-high",
        "prompt": prompt,
        "timeout": 600
    }

    req = urllib.request.Request(
        FLEET_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    import time
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            job_id = data.get("job_id")
            node_name = data.get("node_name")
            print(f"[Master Marketing Audit] Dispatched job {job_id} to node {node_name}. Polling status...")

            start_time = time.time()
            while time.time() - start_time < 600:
                time.sleep(5)
                poll_url = f"http://localhost:7777/api/fleet/jobs/{job_id}"
                with urllib.request.urlopen(poll_url, timeout=30) as p_resp:
                    job_data = json.loads(p_resp.read().decode("utf-8"))
                    status = job_data.get("status")
                    print(f"[Master Marketing Audit] Job {job_id} status: {status} (elapsed: {int(time.time() - start_time)}s)")
                    if status == "completed":
                        output_text = job_data.get("output", "") or job_data.get("clean_response", "") or job_data.get("stdout", "")
                        with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
                            f.write(output_text)
                        print(f"[Master Marketing Audit] Successfully saved full report ({len(output_text)} chars) to {OUTPUT_REPORT_PATH}")
                        return output_text
                    elif status == "failed":
                        err = job_data.get("stderr") or job_data.get("output")
                        raise RuntimeError(f"Job failed: {err}")
            raise TimeoutError("Job timed out after 600s")
    except Exception as e:
        print(f"[Master Marketing Audit] Execution error: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    run_fleet_audit()
