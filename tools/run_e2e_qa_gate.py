#!/usr/bin/env python3
"""
Master E2E QA Gate Orchestrator for Insilos Enterprise Odoo 20 & Innoria Group.
Shifts QA focus from security micro-gates to comprehensive End-to-End (E2E)
functional & UI QA gates across insilos20_dev (http://localhost:28069) and
innoria_prod (http://localhost:28070).
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent

E2E_QA_GATES: List[Dict[str, Any]] = [
    {
        "id": "E2E-QA-01",
        "title": "Public Website Brand, IBM Carbon v11, Poppins Typography & Header Menu Uniqueness",
        "category": "website",
        "fast": True,
        "commands": [
            ["python3", "tools/audit_header_menu_collision.py", "--check"],
            ["python3", "tools/test_innoria_website_brand_and_content_audit.py"],
        ],
    },
    {
        "id": "E2E-QA-02",
        "title": "Public AI Concierge, Service Configurator & Grounded RAG Lead-to-CRM Flow",
        "category": "website",
        "fast": False,
        "commands": [
            ["python3", "tools/test_website_concierge_and_marketing.py"],
        ],
    },
    {
        "id": "E2E-QA-03",
        "title": "Sales-First Partner Onboarding, Tiering, Companion Docs (TPL-ONB-01..04) & Payment Gate",
        "category": "domain",
        "fast": True,
        "commands": [
            ["python3", "tools/test_dgm_partner_onboarding.py"],
        ],
    },
    {
        "id": "E2E-QA-04",
        "title": "Project Delivery, SAP Activate Stage Gates & Timesheet-to-1C26TAA E-Invoice Pipeline",
        "category": "domain",
        "fast": True,
        "commands": [
            ["python3", "tools/test_dgm_timesheet_to_invoice_pipeline.py"],
        ],
    },
    {
        "id": "E2E-QA-05",
        "title": "Knowledge Management & Grounded SOP-RAG Chatbot (SOP-DGM-12)",
        "category": "domain",
        "fast": False,
        "commands": [
            ["python3", "tools/test_dgm_knowledge_rag_chatbot.py"],
        ],
    },
    {
        "id": "E2E-QA-06",
        "title": "Employee Self-Service Hub (HomeMenu), Statutory VN 2026 Payroll, VCB DigiBiz 11-Col Export & ISO 27701 Masking",
        "category": "domain",
        "fast": False,
        "commands": [
            ["python3", "tools/test_dgm_hr_payroll_dashboard.py"],
        ],
    },
    {
        "id": "E2E-QA-07",
        "title": "KPI & SWE Skill Framework + OKR, 360° Appraisal & Project PDCA (SOP-DGM-10/11)",
        "category": "domain",
        "fast": False,
        "commands": [
            ["python3", "tools/test_dgm_kpi_skill_framework.py"],
            ["python3", "tools/test_dgm_okr_appraisal_project_pdca.py"],
        ],
    },
    {
        "id": "E2E-QA-08",
        "title": "Documents Multi-Level Tree & Google Drive Shared-With-Me RBAC Matrix",
        "category": "domain",
        "fast": False,
        "commands": [
            ["/usr/bin/python3", "tools/test_documents_rbac_matrix.py"],
        ],
    },
    {
        "id": "E2E-QA-09",
        "title": "Playwright Dual-Theme (Light <-> Dark) & CRM/Documents Luminance E2E",
        "category": "ui",
        "fast": True,
        "commands": [
            ["node", "tools/audit_crm_dual_theme.js"],
            ["node", "tools/test_theme_switch_dark_to_light.js"],
        ],
    },
    {
        "id": "E2E-QA-10",
        "title": "Playwright Master User Journeys E2E (Public Nav, AI Concierge, HomeMenu Hub, Documents Tree Switcher, CRM Form)",
        "category": "ui",
        "fast": True,
        "commands": [
            ["node", "tools/test_e2e_qa_master_flows.js"],
        ],
    },
    {
        "id": "E2E-QA-11",
        "title": "Order-to-Cash (O2C) Sales Lifecycle DAG, PubGrub Discount Solver & Double-Entry Clearing E2E",
        "category": "domain",
        "fast": True,
        "commands": [
            ["pytest", "tests/test_insilos_victory_critic_harness.py", "-q"],
        ],
    },
    {
        "id": "E2E-QA-12",
        "title": "RAG-SOP Sales & Marketing Framework (SOP-DGM-15), <5 Min Rapid CPQ Quoting, 5-Archetype ROI Matrix & Executive PDF Report",
        "category": "domain",
        "fast": True,
        "commands": [
            ["python3", "tools/test_dgm_rapid_quote_roi_pdf.py"],
        ],
    },
    {
        "id": "E2E-QA-13",
        "title": "CRM 7-Stage Dual-Motion AL2C Pipeline, Hunter/Farmer/SDR Teams, 1-Click Lead-to-CPQ-ROI Bridge, 6 ICP Email Lists, 8 Carbon Mailings & 24 ABM Activities",
        "category": "domain",
        "fast": True,
        "commands": [
            ["python3", "tools/test_dgm_crm_email_marketing_e2e.py"],
        ],
    },
]


def extract_evidence_lines(output: str) -> List[str]:
    """Extract assertion/pass lines containing [✓], ✓, or PASS markers."""
    evidence: List[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "[✓]" in line or "✓" in line or line.startswith("PASS") or "PASSED" in line:
            evidence.append(line)
    return evidence


def print_gates_list() -> None:
    print("=" * 100)
    print("CANONICAL E2E QA GATES (insilos20_dev :28069 & innoria_prod :28070)")
    print("=" * 100)
    for gate in E2E_QA_GATES:
        fast_badge = "FAST" if gate["fast"] else "FULL"
        print(
            f"  {gate['id']}  [{gate['category'].upper():7s}] [{fast_badge:4s}]  {gate['title']}"
        )
        for cmd in gate["commands"]:
            print(f"      $ {' '.join(cmd)}")
    print("=" * 100)


def filter_gates(args: argparse.Namespace) -> List[Dict[str, Any]]:
    selected = list(E2E_QA_GATES)

    if args.gate:
        requested_ids = set()
        for item in args.gate:
            for part in item.split(","):
                cleaned = part.strip().upper()
                if cleaned:
                    requested_ids.add(cleaned)
        unknown = requested_ids - {g["id"] for g in E2E_QA_GATES}
        if unknown:
            print(
                f"[ERROR] Unknown gate ID(s): {', '.join(sorted(unknown))}",
                file=sys.stderr,
            )
            sys.exit(2)
        selected = [g for g in selected if g["id"] in requested_ids]

    if args.category:
        cat = args.category.strip().lower()
        selected = [g for g in selected if g["category"] == cat]

    if args.fast and not args.gate:
        selected = [g for g in selected if g["fast"]]

    return selected


def run_command(cmd: List[str], timeout_sec: int = 600) -> Dict[str, Any]:
    start_ts = time.monotonic()
    cmd_str = " ".join(cmd)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        duration = round(time.monotonic() - start_ts, 3)
        combined_out = (proc.stdout or "") + (
            ("\n" + proc.stderr) if proc.stderr else ""
        )
        evidence = extract_evidence_lines(combined_out)
        return {
            "command": cmd,
            "command_str": cmd_str,
            "returncode": proc.returncode,
            "passed": proc.returncode == 0,
            "duration_sec": duration,
            "evidence_count": len(evidence),
            "evidence": evidence,
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.monotonic() - start_ts, 3)
        return {
            "command": cmd,
            "command_str": cmd_str,
            "returncode": 124,
            "passed": False,
            "duration_sec": duration,
            "evidence_count": 0,
            "evidence": [],
            "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": f"TimeoutExpired after {timeout_sec}s",
        }


def write_markdown_report(report: Dict[str, Any], md_path: Path) -> None:
    lines: List[str] = [
        "# Insilos O20 & Innoria Master E2E QA Gate Report",
        "",
        f"- **Generated At (UTC)**: `{report['generated_at_utc']}`",
        f"- **Mode**: `{report['mode']}`",
        f"- **Total Gates Executed**: `{report['summary']['total_gates']}`",
        f"- **Passed Gates**: `{report['summary']['passed_gates']}`",
        f"- **Failed Gates**: `{report['summary']['failed_gates']}`",
        f"- **Total Assertions (`[✓]`)**: `{report['summary']['total_evidence_assertions']}`",
        f"- **Wall-Clock Duration**: `{report['summary']['total_duration_sec']}s`",
        f"- **Overall Verdict**: **{'PASS' if report['summary']['overall_passed'] else 'FAIL'}**",
        "",
        "## Gate Summary Matrix",
        "",
        "| Gate ID | Category | Fast | Title | Commands | Assertions | Duration (s) | Status |",
        "| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |",
    ]

    for g in report["gates"]:
        status_str = "PASS" if g["passed"] else "FAIL"
        fast_str = "Yes" if g["fast"] else "No"
        lines.append(
            f"| `{g['id']}` | `{g['category']}` | {fast_str} | {g['title']} | {len(g['commands'])} | {g['evidence_count']} | {g['duration_sec']:.2f}s | **{status_str}** |"
        )

    lines.extend(["", "## Detailed Gate Evidence", ""])

    for g in report["gates"]:
        status_badge = "PASS" if g["passed"] else "FAIL"
        lines.append(f"### {g['id']}: {g['title']} [{status_badge}]")
        lines.append(
            f"- **Category**: `{g['category']}` | **Fast Gate**: `{g['fast']}` | **Duration**: `{g['duration_sec']:.2f}s`"
        )
        for cmd_res in g["commands"]:
            cmd_status = "PASS" if cmd_res["passed"] else f"FAIL (rc={cmd_res['returncode']})"
            lines.append(
                f"- **Command**: `{cmd_res['command_str']}` — **{cmd_status}** (`{cmd_res['duration_sec']:.2f}s`, `{cmd_res['evidence_count']}` assertions)"
            )
            if cmd_res["evidence"]:
                lines.append("  ```text")
                for ev in cmd_res["evidence"][:40]:
                    lines.append(f"  {ev}")
                if len(cmd_res["evidence"]) > 40:
                    lines.append(f"  ... (+{len(cmd_res['evidence']) - 40} more assertions)")
                lines.append("  ```")
            if not cmd_res["passed"]:
                lines.append("  **Failure Output Tail**:")
                lines.append("  ```text")
                tail = (cmd_res["stdout_tail"] + "\n" + cmd_res["stderr_tail"]).strip()
                for tline in tail.splitlines()[-30:]:
                    lines.append(f"  {tline}")
                lines.append("  ```")
        lines.append("")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Master E2E QA Gate Orchestrator for Insilos Enterprise Odoo 20 & Innoria Group."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print all 10 E2E QA Gates with ID, category, fast-mode flag, and commands, then exit 0.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run the fast E2E smoke gate subset (fast=True).",
    )
    parser.add_argument(
        "--gate",
        action="append",
        help="Run only specified gates (repeatable or comma-separated, e.g. --gate E2E-QA-01,E2E-QA-09).",
    )
    parser.add_argument(
        "--category",
        choices=["website", "domain", "ui"],
        help="Filter gates by category (website, domain, ui).",
    )
    parser.add_argument(
        "--json-report",
        default="tools/e2e_qa_gate_report.json",
        help="Path to write JSON report (default: tools/e2e_qa_gate_report.json).",
    )
    parser.add_argument(
        "--md-report",
        default="tools/e2e_qa_gate_report.md",
        help="Path to write Markdown report (default: tools/e2e_qa_gate_report.md).",
    )
    args = parser.parse_args()

    if args.list:
        print_gates_list()
        return 0

    selected_gates = filter_gates(args)
    if not selected_gates:
        print("[ERROR] No E2E QA gates matched the given filters.", file=sys.stderr)
        return 2

    mode_parts = []
    if args.gate:
        mode_parts.append(f"gates={','.join(g['id'] for g in selected_gates)}")
    elif args.fast:
        mode_parts.append("fast")
    else:
        mode_parts.append("full")
    if args.category:
        mode_parts.append(f"category={args.category}")
    mode_str = "+".join(mode_parts)

    print("=" * 100)
    print(f"STARTING E2E QA GATE ORCHESTRATOR | Mode: {mode_str} | Gates: {len(selected_gates)}")
    print("=" * 100)

    suite_start = time.monotonic()
    gate_results: List[Dict[str, Any]] = []
    total_assertions = 0

    for idx, gate in enumerate(selected_gates, start=1):
        print(
            f"\n[{idx}/{len(selected_gates)}] >>> Running {gate['id']} ({gate['category'].upper()}): {gate['title']}"
        )
        gate_start = time.monotonic()
        cmd_results: List[Dict[str, Any]] = []
        gate_passed = True
        gate_evidence_count = 0

        for cmd in gate["commands"]:
            cmd_str = " ".join(cmd)
            print(f"    $ {cmd_str} ...", flush=True)
            res = run_command(cmd)
            cmd_results.append(res)
            gate_evidence_count += res["evidence_count"]
            total_assertions += res["evidence_count"]

            for ev in res["evidence"]:
                print(f"      {ev}")

            if res["passed"]:
                print(
                    f"    [PASS] {cmd_str} ({res['duration_sec']:.2f}s, {res['evidence_count']} assertions)"
                )
            else:
                gate_passed = False
                print(
                    f"    [FAIL] {cmd_str} (rc={res['returncode']}, {res['duration_sec']:.2f}s)"
                )
                if res["stdout_tail"]:
                    print("    --- STDOUT TAIL ---")
                    for line in res["stdout_tail"].splitlines()[-20:]:
                        print(f"      {line}")
                if res["stderr_tail"]:
                    print("    --- STDERR TAIL ---")
                    for line in res["stderr_tail"].splitlines()[-20:]:
                        print(f"      {line}")

        gate_duration = round(time.monotonic() - gate_start, 3)
        status_label = "PASS" if gate_passed else "FAIL"
        print(
            f"<<< {gate['id']} [{status_label}] in {gate_duration:.2f}s ({gate_evidence_count} assertions)"
        )

        gate_results.append(
            {
                "id": gate["id"],
                "title": gate["title"],
                "category": gate["category"],
                "fast": gate["fast"],
                "passed": gate_passed,
                "duration_sec": gate_duration,
                "evidence_count": gate_evidence_count,
                "commands": cmd_results,
            }
        )

    total_duration = round(time.monotonic() - suite_start, 3)
    passed_gates = sum(1 for g in gate_results if g["passed"])
    failed_gates = len(gate_results) - passed_gates
    overall_passed = failed_gates == 0

    report: Dict[str, Any] = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": mode_str,
        "summary": {
            "total_gates": len(gate_results),
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "total_evidence_assertions": total_assertions,
            "total_duration_sec": total_duration,
            "overall_passed": overall_passed,
        },
        "gates": gate_results,
    }

    json_path = Path(args.json_report)
    if not json_path.is_absolute():
        json_path = ROOT_DIR / json_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md_path = Path(args.md_report)
    if not md_path.is_absolute():
        md_path = ROOT_DIR / md_path
    write_markdown_report(report, md_path)

    print("\n" + "=" * 100)
    print(
        f"E2E QA GATE SUMMARY: {passed_gates}/{len(gate_results)} Gates Passed | "
        f"{total_assertions} Assertions | {total_duration:.2f}s Total"
    )
    print(f"JSON Report: {json_path}")
    print(f"MD Report  : {md_path}")
    print("=" * 100)

    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
