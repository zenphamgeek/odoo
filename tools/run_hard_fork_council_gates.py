#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/run_hard_fork_council_gates.py
====================================
Hard Fork Experts Council - 10-Gate Release Verification Runner
Insilos Enterprise Platform (insilos-genesis-fork)

Automated execution engine for the full 10-Gate Release Verification Matrix:
  Gate 1:  Python AST Syntax & Compilation Audit (py_compile)
  Gate 2:  XML & QWeb Well-Formedness Audit (lxml.etree)
  Gate 3:  Server Boot & Preload Integrity (--stop-after-init)
  Gate 4:  PEP 451 Import Hook Interoperability (insilos_adapter)
  Gate 5:  Perimeter Security Gateway API Contract (/insilos/api/v1)
  Gate 6:  App Icons & Branding Asset Integrity (Phosphor Duotone)
  Gate 7:  Counter Code Security Invariance (Genesis Fingerprint Scanner)
  Gate 8:  Ported Enterprise Modules E2E Lifecycle (Playwright)
  Gate 9:  72-App Parallel Playwright Suite (Playwright Concurrency)
  Gate 10: UI Brand & Lexicon Leak Sweep Across Core Apps (Playwright)
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_VENV = REPO_ROOT / ".venv" / "bin" / "python"
if not PYTHON_VENV.exists():
    PYTHON_VENV = Path(sys.executable)

# ANSI Colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def colorize(text, color, enabled=True):
    if not enabled:
        return text
    return f"{color}{text}{Colors.RESET}"

# Gate Definitions
GATE_DEFINITIONS = [
    {
        "id": 1,
        "name": "Python AST Syntax & Compilation Audit",
        "description": "Verifies that all Python files across all enterprise modules compile without syntax errors",
        "command": [str(PYTHON_VENV), "tools/verify_gates_1_2.py", "--gate", "1"],
        "target": "tools/verify_gates_1_2.py",
        "timeout": 60,
        "requires_server": False,
        "milestone": "M1",
    },
    {
        "id": 2,
        "name": "XML & QWeb Well-formedness Audit",
        "description": "Parses and verifies all XML views and templates across enterprise modules with lxml",
        "command": [str(PYTHON_VENV), "tools/verify_gates_1_2.py", "--gate", "2"],
        "target": "tools/verify_gates_1_2.py",
        "timeout": 60,
        "requires_server": False,
        "milestone": "M1",
    },
    {
        "id": 3,
        "name": "Server Boot & Preload Integrity",
        "description": "Initializes database registry and preloads 697+ active modules under stop-after-init mode",
        "command": [str(PYTHON_VENV), "insilos-bin", "-c", "insilos.conf", "--no-http", "-d", "odoo20_dev", "--stop-after-init"],
        "target": "insilos-bin",
        "timeout": 120,
        "requires_server": False,
        "milestone": "M1",
    },
    {
        "id": 4,
        "name": "PEP 451 Import Hook Interoperability",
        "description": "Validates dynamic insilos to odoo namespace aliasing, deep imports, and class identity",
        "command": [str(PYTHON_VENV), "tools/test_insilos_import_hook.py"],
        "target": "tools/test_insilos_import_hook.py",
        "timeout": 45,
        "requires_server": False,
        "milestone": "M1",
    },
    {
        "id": 5,
        "name": "Perimeter Security Gateway API Contract",
        "description": "Tests masked JSON API endpoints (/insilos/api/v1), Server headers, and error sanitization",
        "command": [str(PYTHON_VENV), "tools/test_insilos_perimeter_gateway.py"],
        "target": "tools/test_insilos_perimeter_gateway.py",
        "timeout": 60,
        "requires_server": True,
        "milestone": "M1",
    },
    {
        "id": 6,
        "name": "App Icons & Branding Asset Integrity",
        "description": "Verifies 62+ launcher application icons comply with Phosphor Duotone vector standard",
        "command": [str(PYTHON_VENV), "tools/check_app_icons_integrity.py"],
        "target": "tools/check_app_icons_integrity.py",
        "timeout": 45,
        "requires_server": False,
        "milestone": "M4",
    },
    {
        "id": 7,
        "name": "Counter Code Security Invariance",
        "description": "Scans core scopes for legacy genesis markers, URLs, and brand colors with zero detection threshold",
        "command": [
            "python3",
            "scripts/counter_code_scanner.py",
            "--path", ".",
            "--scope", "addons/web", "addons/base", "branding", "enterprise/web_enterprise",
            "--max-allowed-detections", "0",
        ],
        "target": "scripts/counter_code_scanner.py",
        "timeout": 60,
        "requires_server": False,
        "milestone": "M5",
    },
    {
        "id": 8,
        "name": "Ported Enterprise Modules E2E Lifecycle",
        "description": "Headless Playwright audit of 26 custom ported enterprise modules (installed state, routing, zero UI brand leaks)",
        "command": ["node", "tools/test_enterprise_ported_modules_e2e.js"],
        "target": "tools/test_enterprise_ported_modules_e2e.js",
        "timeout": 120,
        "requires_server": True,
        "milestone": "M6",
    },
    {
        "id": 9,
        "name": "Full 72-App Parallel Playwright Verification",
        "description": "Parallel browser automation across all 72 launcher applications verifying navigation and zero console errors",
        "command": ["node", "test_all_home_apps_parallel.js"],
        "target": "test_all_home_apps_parallel.js",
        "timeout": 300,
        "requires_server": True,
        "milestone": "M6",
    },
    {
        "id": 10,
        "name": "UI Brand & Lexicon Leak Sweep Across Core Apps",
        "description": "Comprehensive DOM text scraper sweeping 5 public routes and 28 core authenticated apps for legacy text leaks",
        "command": ["node", "tools/sweep_ui_all_apps.js"],
        "target": "tools/sweep_ui_all_apps.js",
        "timeout": 150,
        "requires_server": True,
        "milestone": "M6",
    },
]


def parse_gate_selection(spec):
    """Parse comma-separated and ranged gate IDs (e.g. '1,2,4' or '1-5' or 'all')."""
    if not spec or spec.strip().lower() in ("all", "1-10", "1..10"):
        return list(range(1, 11))

    selected = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            selected.update(range(int(start), int(end) + 1))
        elif ".." in part:
            start, end = part.split("..", 1)
            selected.update(range(int(start), int(end) + 1))
        else:
            selected.add(int(part))
    return sorted([g for g in selected if 1 <= g <= 10])


def check_server_available():
    """Quick check if server is responsive on port 28069."""
    import urllib.request
    try:
        req = urllib.request.Request("http://localhost:28069/insilos/api/v1/ping", headers={"User-Agent": "CouncilRunner/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def run_single_gate(gate_def, verbose=False, color=True):
    """Execute a single gate subprocess and capture output, exit code, and execution time."""
    gate_id = gate_def["id"]
    name = gate_def["name"]
    cmd = gate_def["command"]
    timeout = gate_def.get("timeout", 120)

    print(f"\n{colorize(f'▶ GATE {gate_id}: {name}', Colors.BOLD + Colors.CYAN, color)}")
    print(colorize(f"  Description: {gate_def['description']}", Colors.DIM, color))
    print(colorize(f"  Command:     {' '.join(cmd)}", Colors.DIM, color))

    start_time = time.perf_counter()
    status = "UNKNOWN"
    output = ""
    error_summary = ""
    exit_code = -1

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        duration = time.perf_counter() - start_time
        exit_code = proc.returncode
        output = proc.stdout or ""

        if verbose:
            print(output)

        if exit_code == 0:
            status = "PASS"
            badge = colorize("✓ PASS", Colors.BOLD + Colors.GREEN, color)
            print(f"  Result:      {badge} ({duration:.2f}s)")
        else:
            status = "FAIL"
            badge = colorize(f"✗ FAIL (exit code {exit_code})", Colors.BOLD + Colors.RED, color)
            print(f"  Result:      {badge} ({duration:.2f}s)")
            # Extract last few meaningful lines for immediate diagnostic
            lines = [l for l in output.strip().splitlines() if l.strip()]
            err_snippet = "\n".join(lines[-6:]) if lines else "No output produced"
            error_summary = err_snippet
            if not verbose:
                print(colorize("  Failure Output Excerpt:", Colors.RED, color))
                for eline in err_snippet.splitlines():
                    print(f"    {colorize(eline, Colors.RED, color)}")

    except subprocess.TimeoutExpired as te:
        duration = time.perf_counter() - start_time
        exit_code = 124
        status = "TIMEOUT"
        badge = colorize(f"⏱ TIMEOUT (>{timeout}s)", Colors.BOLD + Colors.RED, color)
        print(f"  Result:      {badge} ({duration:.2f}s)")
        output = te.stdout or "" if hasattr(te, "stdout") else ""
        error_summary = f"Gate timed out after {timeout} seconds"

    except Exception as e:
        duration = time.perf_counter() - start_time
        exit_code = 1
        status = "ERROR"
        badge = colorize(f"⚠ ERROR ({str(e)})", Colors.BOLD + Colors.RED, color)
        print(f"  Result:      {badge} ({duration:.2f}s)")
        error_summary = str(e)

    return {
        "gate_id": gate_id,
        "name": name,
        "command": cmd,
        "duration_seconds": round(duration, 3),
        "exit_code": exit_code,
        "status": status,
        "error_summary": error_summary,
        "output": output,
    }


def print_banner(color=True):
    banner = r"""
  ___           _ _             ____       _       __  __       _        _      
 |_ _|_ __  ___(_) | ___  ___  / ___| __ _| |_ ___ |  \/  | __ _| |_ _ __(_)_  __
  | || '_ \/ __| | |/ _ \/ __|| |  _ / _` | __/ _ \| |\/| |/ _` | __| '__| \ \/ /
  | || | | \__ \ | | (_) \__ \| |_| | (_| | ||  __/| |  | | (_| | |_| |  | |>  < 
 |___|_| |_|___/_|_|\___/|___/ \____|\__,_|\__\___||_|  |_|\__,_|\__|_|  |_/_/\_\
               HARD FORK EXPERTS COUNCIL — 10-GATE VERIFICATION RUNNER
    """
    print(colorize(banner, Colors.BOLD + Colors.BLUE, color))


def print_summary_table(results, color=True):
    print("\n" + "=" * 80)
    print(colorize("               10-GATE RELEASE VERIFICATION SUMMARY MATRIX", Colors.BOLD, color))
    print("=" * 80)
    header = f"{'Gate':<6} | {'Verification Domain':<44} | {'Time (s)':<9} | {'Exit':<5} | {'Status':<8}"
    print(header)
    print("-" * 80)

    passed_count = 0
    failed_count = 0
    total_time = 0.0

    for r in results:
        gid = f"Gate {r['gate_id']}"
        name = r["name"][:44]
        dur = f"{r['duration_seconds']:.2f}s"
        code = str(r["exit_code"])
        total_time += r["duration_seconds"]

        if r["status"] == "PASS":
            status_str = colorize("PASS", Colors.BOLD + Colors.GREEN, color)
            passed_count += 1
        elif r["status"] == "WARN":
            status_str = colorize("WARN", Colors.BOLD + Colors.YELLOW, color)
            passed_count += 1
        else:
            status_str = colorize(r["status"], Colors.BOLD + Colors.RED, color)
            failed_count += 1

        print(f"{gid:<6} | {name:<44} | {dur:<9} | {code:<5} | {status_str}")

    print("-" * 80)
    summary_line = (
        f"Total Gates Executed: {len(results)} | "
        f"Passed: {colorize(str(passed_count), Colors.GREEN, color)} | "
        f"Failed: {colorize(str(failed_count), Colors.RED if failed_count else Colors.GREEN, color)} | "
        f"Total Wall Time: {total_time:.2f}s"
    )
    print(summary_line)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Hard Fork Experts Council - 10-Gate Release Verification Matrix Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--gates",
        default="1-10",
        help="Comma-separated or ranged gate numbers to run (e.g. '1,2,4', '1-6', 'all'). Default: '1-10'",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Halt gate execution immediately on first gate failure",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print verbose real-time stdout and stderr from gate subprocesses",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON report to stdout at the end",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write structured JSON report to the specified file path",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI terminal colors in output",
    )
    parser.add_argument(
        "--allow-pending-m5",
        action="store_true",
        help="Mark Gate 7 failure as pending milestone M5 requirement (warning only)",
    )

    args = parser.parse_args()
    use_color = (not args.no_color) and sys.stdout.isatty()

    if not args.json:
        print_banner(use_color)

    selected_ids = parse_gate_selection(args.gates)
    selected_gates = [g for g in GATE_DEFINITIONS if g["id"] in selected_ids]

    if not selected_gates:
        print(colorize("Error: No valid gates selected in range 1-10.", Colors.RED, use_color))
        sys.exit(1)

    # Pre-flight check for server-dependent gates
    needs_server = any(g.get("requires_server", False) for g in selected_gates)
    server_ready = True
    if needs_server:
        server_ready = check_server_available()
        if not server_ready and not args.json:
            print(colorize("⚠️  Warning: Live Odoo server at http://localhost:28069 is NOT responsive!", Colors.YELLOW, use_color))
            print(colorize("   Gates requiring live server (5, 8, 9, 10) may fail.", Colors.YELLOW, use_color))

    results = []
    overall_success = True

    for gate_def in selected_gates:
        res = run_single_gate(gate_def, verbose=args.verbose, color=use_color)

        # Handle pending M5 annotation for Gate 7 if requested
        if gate_def["id"] == 7 and res["status"] == "FAIL" and args.allow_pending_m5:
            res["status"] = "WARN"
            res["note"] = "Remediation scheduled in Milestone M5 (Feature 20)"

        results.append(res)

        if res["status"] not in ("PASS", "WARN"):
            overall_success = False
            if args.stop_on_fail:
                print(colorize("\n[HALT] --stop-on-fail triggered. Aborting remaining gates.", Colors.YELLOW, use_color))
                break

    # Build report dict
    report = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "runner": "tools/run_hard_fork_council_gates.py",
        "repository": str(REPO_ROOT),
        "gates_selected": selected_ids,
        "total_executed": len(results),
        "passed_count": sum(1 for r in results if r["status"] in ("PASS", "WARN")),
        "failed_count": sum(1 for r in results if r["status"] not in ("PASS", "WARN")),
        "overall_success": overall_success,
        "gates": [
            {
                "id": r["gate_id"],
                "name": r["name"],
                "status": r["status"],
                "exit_code": r["exit_code"],
                "duration_seconds": r["duration_seconds"],
                "error_summary": r["error_summary"],
            }
            for r in results
        ],
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        if not args.json:
            print(f"\n[INFO] Wrote structured JSON audit report to {out_path}")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_summary_table(results, color=use_color)

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
