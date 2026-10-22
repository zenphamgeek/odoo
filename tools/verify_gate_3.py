#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/verify_gate_3.py
======================
Hard Fork Experts Council - Gate 3 Verification Runner
Combines:
  1. Server Boot & Preload Integrity (--stop-after-init)
  2. View Graph & Schema Integrity Matrix Scanner (audit_views_integrity.py)

Guarantees:
  - 100% Registry module loading without crash.
  - Zero ghost views in database.
  - Zero get_views() compilation failures across core models.
  - 100% physical existence of all Many2many relation columns in PostgreSQL.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_VENV = REPO_ROOT / ".venv" / "bin" / "python"
if not PYTHON_VENV.exists():
    PYTHON_VENV = Path(sys.executable)

def run_step(step_name, cmd, timeout=120):
    print(f"\n[*] RUNNING STEP: {step_name}")
    print(f"    Command: {' '.join(cmd)}")
    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=timeout)
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"[✗] FAILED ({elapsed:.2f}s, exit code {res.returncode}):")
        if res.stdout:
            print(res.stdout[-1500:])
        if res.stderr:
            print(res.stderr[-1500:])
        return False
    print(f"[✓] PASSED in {elapsed:.2f}s")
    return True

def main():
    db_name = os.environ.get("DB_NAME", "odoo20_dev")
    print("=" * 78)
    print(f"GATE 3: SERVER BOOT & VIEW/SCHEMA INTEGRITY VERIFICATION (DB: {db_name})")
    print("=" * 78)

    # Step 1: Server Boot & Preload
    step1_cmd = [
        str(PYTHON_VENV), "insilos-bin",
        "-c", "insilos.conf",
        "--no-http",
        "-d", db_name,
        "--stop-after-init"
    ]
    if not run_step("Server Boot & Registry Preload (--stop-after-init)", step1_cmd, timeout=120):
        sys.exit(1)

    # Step 2: View Graph & Schema Integrity Scanner
    step2_cmd = [
        str(PYTHON_VENV), "tools/audit_views_integrity.py",
        "-d", db_name
    ]
    if not run_step("View Graph & Relational Schema Invariance Matrix", step2_cmd, timeout=120):
        sys.exit(1)

    print("\n" + "=" * 78)
    print("[🎉] GATE 3 100% PASS: Server boot and view/schema integrity verified!")
    print("=" * 78)
    sys.exit(0)

if __name__ == "__main__":
    main()
