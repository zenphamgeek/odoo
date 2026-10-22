#!/usr/bin/env python3
"""
tools/fleet_enterprise_research_runner.py
Autonomous Fleet Swarm Dispatcher for Enterprise Operating Models & Deep Research:
- Track 1: Enterprise Software Services Organization & CoE Operating Model across 4 Products (Insilos ERP, Vertical Resilience, Mojo AI, Zencode Ent)
- Track 2: Enterprise DMS, Corporate KMS, and SOP-RAG Grounding Architecture for innoria.com
- Track 3: Event-Driven Timesheet Intake, Multi-Modal Parsing, Deduplication & Decree 70/2025 E-Invoicing Pipeline

Dispatches to high-capacity AGY Fleet Pro / Ultra nodes and stores verified markdown artifacts.
"""

import concurrent.futures
import json
import os
import sys
import time
import urllib.request

FLEET_URL = "http://localhost:7777"
OUTPUT_DIR = "/home/zen/O20/artifacts/fleet_swarm_results"
DOCS_DIR = "/home/zen/O20/docs/organization_and_processes"

TASKS = [
    {
        "id": "TRACK1_ORGANIZATION_AND_COE_RESEARCH",
        "node": "innoria.team",
        "model": "gemini-4-argon-high",
        "fallback_node": "coderedgen",
        "fallback_model": "gemini-3.1-pro-high",
        "prompt": """You are an Enterprise Software Services Principal Architect and Corporate Operating Model Researcher.
Conduct an exhaustive, high-rigor research study on the Organizational Structure and Centers of Excellence (CoE) for an Enterprise Software Services Corporation operating four core products:
1. Insilos ERP (/home/zen/O20, /home/zen/insilos_mobile): Next-Gen Odoo 20 fork, VAS/IFRS accounting, WMS, MRP, Napas247 VietQR, mobile field operations.
2. Vertical Resilience (/home/zen/VerticalRisk): GRC, ISO 27001, SOC 2, BCM, ERM, ESG CSRD, HS Tariff integration.
3. Mojo AI (/home/zen/O20/addons/insilos_al2c): Autonomous Agent Swarms, SOP-RAG Grounding, Multimodal Document Parsing, Edge Inference.
4. Zencode Ent (/home/zen/zencode-ent): Enterprise Developer Platform, Swarm orchestration, Hegelian Dialectic legacy code refactoring, 13 Council Gates.

Requirements:
- Structure the report in pristine Markdown (Vietnamese with standard English technical terms).
- Section 1: Matrix Operating Model (Practice CoEs vs Client Delivery Pods). Detailed roles: Practice Principal, Solution Architect, Delivery Lead, Technical Architect, AI Engineer, GRC Consultant, ERP Consultant.
- Section 2: Financial & Delivery Invariants: Billable Utilization Target (>= 78%), Resource Shadowing, Blended Daily Rates (VND), Margin Protection, and Deal-Desk Guardrails.
- Section 3: Cross-Product Synergy & Bundling Playbooks (e.g. ERP Implementation + GRC Compliance Gate + Mojo Multimodal Automation + Zencode Modernization). Bilateral SLAs and cross-charging models.
- Section 4: Multi-Repository Synchronization & Governance: Code & documentation contracts between /home/zen/O20, /home/zen/VerticalRisk, /home/zen/insilos_mobile, and /home/zen/zencode-ent.
- Section 5: Concrete RACI Matrix and Operational Checklists for Enterprise Project Delivery.
Make the report deep, comprehensive (> 2,500 words), mathematically sound, and directly actionable for executive leadership.
"""
    },
    {
        "id": "TRACK2_DMS_KMS_RAG_AI_RESEARCH",
        "node": "coderedgen",
        "model": "gemini-3.1-pro-high",
        "fallback_node": "sunward",
        "fallback_model": "claude-opus-5-5-high",
        "prompt": """You are an Enterprise AI Systems & Knowledge Engineering Principal Architect.
Conduct an exhaustive, high-rigor research study on Enterprise Document Management (DMS), Corporate Knowledge Management (KMS), and SOP-RAG Grounding for Innoria (innoria.com) and the Insilos Platform.

Requirements:
- Structure the report in pristine Markdown (Vietnamese with standard English technical terms).
- Section 1: Enterprise DMS Architecture:
  * Document lifecycle (Draft -> Review -> Approved -> Immutable/Locked).
  * Cryptographic SHA-256 fingerprinting & audit trails on documents.document.
  * Decree 13/2023/NĐ-CP (PDPD) compliance, PII redaction, and access revocation.
- Section 2: Corporate KMS & Knowledge Taxonomy:
  * 7 Core Knowledge Spaces (Products, Industries, Delivery Playbooks, Sales Battlecards, RFP Library, Post-Mortems, Compliance).
  * 90-day review cycles, markdown AST extraction, and bidirectional Git-Sync.
- Section 3: SOP-RAG Grounding Architecture:
  * Chunking strategy: semantic table preservation, markdown header hierarchies.
  * Hybrid retrieval: Dense vector embeddings + BM25 sparse lexical search with Reciprocal Rank Fusion (RRF).
  * Strict Entailment Gate (confidence >= 0.75) via NLI cross-encoders to eliminate hallucinations.
  * Universal Citation Contract format: `[Document_Name | Section_Heading | Chunk_ID | SHA256_Prefix]`.
  * Safe abstention protocols and human escalation fallback.
- Section 4: Public Executive AI Concierge on innoria.com:
  * B2B Lead qualification & fit scoring algorithm (0-100) based on firmographics, budget, and implementation timeline.
  * Autonomous dossier creation in crm.lead with privacy protection.
  * Real-time visitor query answering with verified citation chips.
  * OWL 2 Component & QWeb Drawer frontend architecture.
Make the report deep, comprehensive (> 2,500 words), technically rigorous, and directly implementable in code.
"""
    },
    {
        "id": "TRACK3_TIMESHEET_PIPELINE_AND_EINVOICE",
        "node": "justaskgao",
        "model": "claude-opus-5-5-high",
        "fallback_node": "zenonmind",
        "fallback_model": "gemini-4-argon-high",
        "prompt": """You are an Enterprise Billing, ERP Architecture, and Revenue Operations Principal Specialist.
Conduct an exhaustive, high-rigor technical analysis and operational specification for the Event-Driven Timesheet Email Ingestion, Deduplication, Billing, and Decree 70/2025/NĐ-CP E-Invoicing Pipeline for Innoria / Insilos.

Requirements:
- Structure the report in pristine Markdown (Vietnamese with standard English technical terms).
- Section 1: Event-Driven Intake Architecture via info@inno.ai.vn:
  * Inbound webhook / Google Workspace Pub-Sub / Mailgun architecture.
  * HMAC-SHA256 signature verification, DMARC/SPF validation, and secure buffer staging (al2c.timesheet.staging).
- Section 2: Intelligent Multi-Modal Parsing & Deduplication:
  * Parsing engines for Excel (.xlsx), CSV, and structured email body text.
  * Entity matching algorithm: 3-tier consultant matching (email -> employee_code -> name fallback), project matching, and analytic account matching.
  * Cryptographic SHA-256 deduplication invariant: hashing (consultant_id, date, duration, task_id, external_ref) + attachment hash to prevent replay attacks and duplicate billing.
- Section 3: Billable Timesheet Calculation & PM Approval Workflow:
  * Rate card resolution: project contract rates vs consultant seniority rates.
  * Billable vs Non-Billable rules, overtime multiplier, cap hours per day (max 12h/day invariant).
  * 1-Click Project Manager review and atomic transition to account.analytic.line.
- Section 4: Customer Verification Portal & Decree 70/2025/NĐ-CP E-Invoicing:
  * Automated delivery of Timesheet Statement with unique secure portal link (/innoria/portal/timesheet_statement/<id>).
  * Interactive Customer Portal verification: client PM reviews timesheet breakdown, logs any dispute, or clicks 'Xác nhận đối soát' (1-click confirmation).
  * Automatic post of draft invoice upon confirmation.
  * Decree 70/2025/NĐ-CP & Decree 123/2020/NĐ-CP compliance: XML digital signing, e-invoice lookup portal, and tax authority transmission.
- Section 5: End-to-End State Machine, Sequence Diagram, and Failure Recovery Protocols.
Make the report deep, comprehensive (> 2,500 words), with code patterns and data schemas.
"""
    }
]

def dispatch_task(task):
    tid = task["id"]
    model = "gemini-4-argon-high"
    payload = {
        "prompt": task["prompt"],
        "model": model,
        "timeout": 240
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    print(f"[*] [FLEET] Dispatching {tid} (model: {model})...")
    job_id = None
    node_name = "auto"
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read().decode())
            job_id = res.get("job_id")
            node_name = res.get("node_name", "auto")
            print(f"[*] [FLEET] {tid} queued on node '{node_name}' as Job {job_id}")
    except Exception as e:
        print(f"[!] [FLEET] {tid} dispatch error: {e}")
        return tid, f"Error: {e}"

    if not job_id:
        return tid, "No job_id returned"

    # Poll for completion up to 240s
    for attempt in range(48):
        time.sleep(5)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=15) as r:
                jd = json.loads(r.read().decode())
                st = jd.get("status")
                node = jd.get("node_name", node_name)
                if st == "completed":
                    out = jd.get("clean_response") or jd.get("output") or ""
                    print(f"[✓] [FLEET] {tid} COMPLETED on node '{node}' ({len(out)} chars)")
                    return tid, out
                elif st == "failed":
                    err = jd.get("stderr") or "unknown"
                    print(f"[✗] [FLEET] {tid} FAILED on node '{node}': {err}")
                    return tid, f"Failed: {err}"
        except Exception as pe:
            print(f"[~] [FLEET] {tid} polling attempt {attempt+1}: {pe}")
            continue

    return tid, "Timeout waiting for job completion"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    print("================================================================================")
    print("AGY FLEET SWARM: PARALLEL ENTERPRISE OPERATING MODEL & DEEP RESEARCH RUNNER")
    print(f"Target Nodes: {[t['node'] for t in TASKS]}")
    print("================================================================================")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TASKS)) as executor:
        futures = {executor.submit(dispatch_task, t): t for t in TASKS}
        for future in concurrent.futures.as_completed(futures):
            t = futures[future]
            tid, content = future.result()
            results[tid] = content
            # Save raw artifact
            art_path = os.path.join(OUTPUT_DIR, f"{tid}.md")
            with open(art_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[+] Saved artifact to {art_path}")

    print("\n[✓] All Fleet Research Tasks Completed!")

if __name__ == "__main__":
    main()
