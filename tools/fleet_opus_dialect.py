#!/usr/bin/env python3
"""
tools/fleet_opus_dialect.py
=============================================================================
AGY Fleet Dialectic Engine (Hegelian Triad: Thesis -> Antithesis -> Synthesis)
Executes deep architectural dialectic for Clean Reverse Engineering & Hard Refactor.
Supports Claude Opus 5.5 High / Gemini 3.1 Pro High across the AGY Fleet Swarm.
=============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

FLEET_API_BASE = os.environ.get("FLEET_API_BASE", "http://localhost:7777")

DIALECTIC_SYSTEM_PROMPT = """You are the Senior Sovereign Systems Architect & Principal Reverse Engineering Dialectician on the AGY Fleet Council.
You specialize in Clean-Room Reverse Engineering, Binary/Bytecode Decompilation, AST De-obfuscation, and Modern Enterprise Hard-Refactoring.

You strictly follow the Hegelian Dialectic Method:
1. THESIS (Decompilation & Raw Logic Extraction):
   - Faithfully deconstruct the raw binary, bytecode (.pyc), minified bundle, or legacy module.
   - Extract exact symbols, data structures, control flow graphs, algorithms, and protocols.

2. ANTITHESIS (Adversarial Critique & Sovereign Invariants):
   - Ruthlessly audit the raw logic against Sovereign Invariants:
     * Strict Database Schema Invariance: ZERO DDL/schema migrations on PostgreSQL.
     * Counter Code Security: ZERO vendor/genesis markers, URLs, or telemetry.
     * Anti-Slop & Design Tokens: Zero bare white surfaces, zero synthetic inline styles; strict IBM Carbon 11 / SAP Fiori Horizon tokens.
     * Reactive OWL 2 Lifecycle: Pure reactive components (useState, useSubEnv), zero legacy widget/DOM mutation.
     * Air-Gapped Security: Zero arbitrary execution or unauthenticated network egress.

3. SYNTHESIS (Clean-Room Sovereign Re-Architecture):
   - Synthesize the final, pristine, sovereign implementation.
   - Provide production-grade, un-slopped, 100% testable code and specifications.
"""


def call_fleet_api(endpoint: str, payload: Dict[str, Any], timeout: int = 180) -> Dict[str, Any]:
    url = f"{FLEET_API_BASE.rstrip('/')}/{endpoint.lstrip('/')}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            elapsed = time.time() - t0
            res = json.loads(body)
            res["_elapsed"] = elapsed
            return res
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"status": "error", "code": e.code, "error": err_body}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_dialectic_cycle(topic: str, context: str, model: str = "claude-opus-5-5-high") -> Dict[str, Any]:
    """
    Executes a structured dialectic cycle across the Fleet Swarm.
    """
    print(f"[*] Initiating Dialectic Cycle: {topic}")
    print(f"    Target Model: {model} on {FLEET_API_BASE}")

    dialectic_prompt = f"""{DIALECTIC_SYSTEM_PROMPT}

TOPIC FOR DIALECTIC RESOLUTION:
{topic}

INPUT CONTEXT / SPECIFICATION / RAW ASSET:
{context}

Execute the complete 3-stage Dialectic now:
# 1. THESIS: Deconstruction & Raw Logic Analysis
# 2. ANTITHESIS: Adversarial Flaw & Invariant Critique
# 3. SYNTHESIS: Clean-Room Sovereign Architecture & Hard Refactor Specification
"""

    # 1. Try smart/sync endpoint
    payload = {
        "prompt": dialectic_prompt,
        "model": model,
        "workload_type": "architectural_dialectic",
        "timeout": 180
    }

    # First attempt: run-smart or run-sync
    resp = call_fleet_api("/api/fleet/run-smart", payload, timeout=190)
    if resp.get("status") == "ok" and (resp.get("clean_response") or resp.get("output")):
        return {
            "status": "success",
            "content": resp.get("clean_response") or resp.get("output"),
            "node": resp.get("node_name"),
            "model": resp.get("model"),
            "elapsed": resp.get("_elapsed")
        }

    # Fallback to run-sync
    resp = call_fleet_api("/api/fleet/run-sync", payload, timeout=190)
    if resp.get("status") == "ok" and (resp.get("clean_response") or resp.get("output")):
        return {
            "status": "success",
            "content": resp.get("clean_response") or resp.get("output"),
            "node": resp.get("node_name"),
            "model": resp.get("model"),
            "elapsed": resp.get("_elapsed")
        }

    # Fallback to plan endpoint
    plan_payload = {
        "prompt": dialectic_prompt,
        "model": model,
        "workload_type": "planning"
    }
    plan_resp = call_fleet_api("/api/fleet/plan", plan_payload, timeout=60)

    return {
        "status": "partial",
        "plan_meta": plan_resp,
        "raw_resp": resp
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/fleet_opus_dialect.py <topic_or_file> [context_file]")
        sys.exit(1)

    target_topic = sys.argv[1]
    context_data = ""
    if len(sys.argv) >= 3 and os.path.exists(sys.argv[2]):
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            context_data = f.read()
    elif os.path.exists(target_topic):
        with open(target_topic, "r", encoding="utf-8") as f:
            context_data = f.read()
            target_topic = f"Dialectic Analysis of {os.path.basename(target_topic)}"

    res = run_dialectic_cycle(target_topic, context_data)
    print("\n" + "=" * 80)
    print("DIALECTIC RESULT:")
    print("=" * 80)
    print(json.dumps(res, indent=2, ensure_ascii=False)[:2000])
