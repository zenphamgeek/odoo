#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN SEQUENTIAL PDCA AST-GREP ORCHESTRATOR
"No-Forbidden-Zone" Refactoring Engine: OWL 3 -> QWeb -> ORM -> Table Names
================================================================================
"""
import sys
import os
import json
import subprocess
import argparse
from pathlib import Path

AST_GREP_BIN = "/home/zen/.local/bin/ast-grep"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "sgconfig.yml"

def run_ast_grep_scan(target_paths, rule_dir=None, json_output=True):
    """Executes ast-grep scan across target paths."""
    cmd = [AST_GREP_BIN, "scan", "--config", str(CONFIG_PATH)]
    if json_output:
        cmd.append("--json=compact")
    for p in target_paths:
        cmd.append(str(p))
    
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if json_output and proc.stdout.strip():
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return []
    return proc.stdout

def audit_cohort_footprints(cohort_name="master_data"):
    """Audits footprints for a specific domain cohort using AST-Grep."""
    print(f"[*] Starting AST-Grep Footprint Audit for Cohort: [{cohort_name}]...")
    
    # 1. ORM Models & Tables
    orm_target = REPO_ROOT / "addons" / "base" / "models"
    matches = run_ast_grep_scan([orm_target])
    
    print(f"[✓] Discovered {len(matches)} AST nodes matching structural patterns in {orm_target.name}")
    for m in matches[:10]:
        file_path = m.get("file", "")
        text = m.get("text", "").strip()
        lines = m.get("range", {}).get("start", {}).get("line", 0) + 1
        print(f"  • {file_path}:{lines} -> {text}")
    
    if len(matches) > 10:
        print(f"  ... and {len(matches) - 10} more AST matches.")

def verify_server_preflight():
    """Runs pre-flight server initialization to ensure zero registry breakage."""
    print("[*] Running pre-flight server verification...")
    cmd = [
        str(REPO_ROOT / ".venv" / "bin" / "python"),
        str(REPO_ROOT / "insilos-bin"),
        "-c", "insilos.conf",
        "-d", "odoo20_dev",
        "--stop-after-init"
    ]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if proc.returncode == 0:
        print("[✓] Server pre-flight PASSED with exit code 0 (Registry intact).")
        return True
    else:
        print(f"[!] Server pre-flight FAILED (code {proc.returncode}):\n{proc.stderr[-500:]}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Insilos Sovereign PDCA AST-Grep Orchestrator")
    parser.add_argument("--cohort", default="master_data", help="Domain cohort to inspect or refactor")
    parser.add_argument("--mode", choices=["audit", "check", "full"], default="audit", help="Execution mode")
    args = parser.parse_args()

    print("================================================================================")
    print("🚀 INSILOS SOVEREIGN AST-GREP SEQUENTIAL PDCA ENGINE")
    print("   No Forbidden Zones: OWL 3 ──▶ QWeb ──▶ ORM Models ──▶ PostgreSQL Tables")
    print("================================================================================")

    if args.mode in ("audit", "full"):
        audit_cohort_footprints(args.cohort)
    
    if args.mode in ("check", "full"):
        verify_server_preflight()

if __name__ == "__main__":
    main()
