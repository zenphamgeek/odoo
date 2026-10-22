#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Runner for Insilos Multi-Repository Governance & Continuous Scanner.
Inspects the 4 sovereign repositories (/home/zen/O20, /home/zen/VerticalRisk, /home/zen/insilos_mobile, /home/zen/zencode-ent)
and generates verified JSON and Markdown governance reports.

Usage:
  python3 tools/run_multi_repo_scan.py [--json <path>] [--markdown <path>] [--check]
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add repo root to sys.path
O20_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(O20_DIR))

from tools.multi_repo_scanner import (
    MultiRepoScanner,
    DEFAULT_REPOSITORIES,
    DEFAULT_DRIFT_THRESHOLD_DAYS,
)

logger = logging.getLogger("run_multi_repo_scan")


def run_scan(
    repos=None,
    json_path=None,
    markdown_path=None,
    check=False,
    threshold=DEFAULT_DRIFT_THRESHOLD_DAYS,
    scope="sovereign",
    sync_db=False,
    dbname="insilos20_dev",
    config_file="insilos.conf"
):
    repos = repos or DEFAULT_REPOSITORIES
    default_json = O20_DIR / "tools" / "multi_repo_scan_report.json"
    default_md = O20_DIR / "tools" / "multi_repo_scan_report.md"

    out_json = Path(json_path) if json_path else default_json
    out_md = Path(markdown_path) if markdown_path else default_md

    scanner = MultiRepoScanner(repos=repos, drift_threshold_days=threshold, scope=scope)
    results = scanner.scan_all()

    # Write JSON report
    out_json.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("JSON report written to: %s", out_json)

    # Write Markdown report
    md_content = scanner.generate_markdown_report(results)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info("Markdown report written to: %s", out_md)

    # Optional DB sync to al2c.tech.asset on insilos20_dev
    if sync_db:
        try:
            logger.info("Attempting DB synchronization to %s...", dbname)
            from tools.sync_tech_assets import sync_all_assets
            sync_all_assets(dbname=dbname, config_file=config_file)
            logger.info("DB sync completed successfully.")
        except Exception as e:
            logger.warning("DB sync skipped or failed (non-blocking): %s", e)

    # Print executive summary
    s = results["summary"]
    print("\n" + "=" * 65)
    print(" CONTINUOUS MULTI-REPOSITORY GOVERNANCE SCAN REPORT")
    print("=" * 65)
    print(f" Target Repositories:       {s['total_repositories']}")
    print(f" Scanned Modules/Packages:  {s['total_modules']}")
    print(f" Total Tracked Code LOC:    {s['total_loc_code']:,}")
    print(f" 30-Day Commit Velocity:    {s['total_velocity_30d']} commits")
    print(f" Dirty Files in Trees:      {s['total_dirty_files']} files")
    print(f" Documentation Drift >30d:  {s['drift_stale_modules_count']} modules (STALE)")
    print(f" Missing Localized Docs:    {s['missing_doc_modules_count']} modules")
    print(f" Dependency Risk Findings:  {s['dependency_risks_count']}")
    print(f" Replacement Sizing (LOC):  {s['total_replacement_man_days']:,} man-days")
    print(f" Active Sprint Workload:    {s['total_active_sprint_workload_days']:,} man-days")
    print(f" Candidate Backlog Items:   {s['candidate_backlog_items_count']}")
    print("=" * 65)
    print(f" Report Artifacts:")
    print(f"   JSON:     {out_json}")
    print(f"   Markdown: {out_md}")
    print("=" * 65 + "\n")

    if check:
        p0_items = [b for b in results.get("candidate_backlog", []) if "[P0]" in b]
        if p0_items:
            print(f"❌ CHECK FAILED: {len(p0_items)} P0 critical governance blocker(s) detected:")
            for item in p0_items:
                print(f"   {item}")
            return 1
        else:
            print("✅ CHECK PASSED: Zero P0 critical governance blockers.")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Run Multi-Repository Governance Scan")
    parser.add_argument("--repos", nargs="+", default=DEFAULT_REPOSITORIES, help="Target repositories")
    parser.add_argument("--json", type=str, help="Output JSON path")
    parser.add_argument("--markdown", type=str, help="Output Markdown path")
    parser.add_argument("--check", action="store_true", help="Fail if P0 issues exist")
    parser.add_argument("--threshold", type=float, default=DEFAULT_DRIFT_THRESHOLD_DAYS, help="Drift threshold in days")
    parser.add_argument("--scope", choices=["sovereign", "all"], default="sovereign", help="Module discovery scope")
    parser.add_argument("--sync-db", action="store_true", help="Sync results into al2c.tech.asset on insilos20_dev")
    parser.add_argument("-d", "--database", default="insilos20_dev", help="Database name for sync")
    parser.add_argument("-c", "--config", default="insilos.conf", help="Config file for sync")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")

    exit_code = run_scan(
        repos=args.repos,
        json_path=args.json,
        markdown_path=args.markdown,
        check=args.check,
        threshold=args.threshold,
        scope=args.scope,
        sync_db=args.sync_db,
        dbname=args.database,
        config_file=args.config
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
