#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insilos Enterprise AL2C Tech Asset & Living Documentation Sync Engine.
Synchronizes Git Telemetry, Code Sizing, Estimation, Risk Assessment,
and Living Knowledge Articles across all registered Technology Assets:
- O20 (Core ERP & Platform)
- Vertical (Vertical Risk & GRC Suite)
- Insilos Mobile (Flutter Cross-Platform Client)
- Zencode Ent (Autonomous AI Fleet Router)
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add O20 root to sys.path
O20_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(O20_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("al2c_tech_asset_sync")


def sync_all_assets(dbname="insilos20_dev", config_file="insilos.conf"):
    import odoo
    from odoo import api, SUPERUSER_ID
    from odoo.modules.registry import Registry

    logger.info("Initializing Odoo environment with config %s, database %s...", config_file, dbname)
    odoo.tools.config.parse_config(["-c", str(O20_DIR / config_file), "-d", dbname])
    registry = Registry(dbname)

    report_lines = []
    report_lines.append("# Insilos Enterprise Technology Asset Registry & Living Telemetry Report")
    report_lines.append(f"> **Audit Timestamp:** {odoo.fields.Datetime.now()} | **Environment:** {dbname}\n")

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        asset_model = env['al2c.tech.asset']

        assets = asset_model.search([])
        if not assets:
            logger.warning("No tech assets found in database. Initializing default assets...")
            # Trigger reload or create
            return False

        logger.info("Found %d registered tech assets. Running full telemetry cycle...", len(assets))

        table_rows = []
        for asset in assets:
            logger.info("Scanning asset [%s] %s at %s...", asset.code, asset.name, asset.repo_path)
            try:
                asset.action_full_telemetry_cycle()
                cr.commit()

                status_emoji = "⚠️" if asset.is_dirty else "✅"
                risk_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠',
                    'critical': '🔴',
                }.get(asset.risk_level, '⚪')

                table_rows.append(
                    f"| **{asset.code}** | {asset.name} | `{asset.git_branch}` | `{asset.git_commit}` | "
                    f"{status_emoji} {asset.uncommitted_files_count} | {asset.loc_code:,} | "
                    f"{(asset.test_coverage_ratio or 0)*100:.1f}% | {asset.estimated_effort_man_days:,.1f} d | "
                    f"{risk_emoji} {asset.risk_score} ({asset.risk_level}) | {asset.doc_freshness} | {asset.improvement_count} |"
                )
                logger.info(
                    "Asset [%s] successfully synced: LOC=%d, TestRatio=%.1f%%, Effort=%.1fd, Risk=%s (%.1f)",
                    asset.code, asset.loc_code, (asset.test_coverage_ratio or 0)*100,
                    asset.estimated_effort_man_days, asset.risk_level, asset.risk_score
                )
            except Exception as e:
                logger.error("Failed to sync asset [%s]: %s", asset.code, e, exc_info=True)
                cr.rollback()

        # Build Markdown summary
        report_lines.append("## 1. Executive Telemetry Overview\n")
        report_lines.append("| Code | Asset Name | Branch | HEAD Commit | Dirty Files | Code LOC | Test % | Sizing (Man-Days) | Risk Level | Doc Freshness | Backlog Items |")
        report_lines.append("|:---|:---|:---|:---|:---:|---:|---:|---:|:---|:---:|---:|")
        report_lines.extend(table_rows)

        report_lines.append("\n---\n")
        report_lines.append("## 2. Deep Health & Risk Diagnostics\n")
        for asset in assets:
            report_lines.append(f"### {asset.name} (`{asset.code}`)")
            report_lines.append(f"- **Repository Path:** `{asset.repo_path}`")
            report_lines.append(f"- **Primary Specification:** `{asset.primary_doc_path or 'N/A'}` ({asset.doc_freshness})")
            report_lines.append(f"- **Tech Stack:** {asset.tech_stack or 'Not specified'}")
            report_lines.append(f"- **Architectural Complexity:** {asset.complexity_rating}")
            report_lines.append(f"- **Composite Risk Score:** **{asset.risk_score} / 100** ({asset.risk_level.upper()})")
            report_lines.append(f"- **Technical Debt Score:** {asset.tech_debt_score} / 100")
            report_lines.append("- **Identified Risk Factors:**")
            if asset.risk_factors:
                for line in asset.risk_factors.splitlines():
                    if line.strip():
                        report_lines.append(f"  {line.strip()}")
            else:
                report_lines.append("  * None detected.")

            report_lines.append("\n**Active Autonomous Improvement Backlog (Backlog v2):**")
            if asset.improvement_ids:
                for imp in asset.improvement_ids:
                    report_lines.append(f"{imp.backlog_v2_line}")
            else:
                report_lines.append("*No items queued.*")
            report_lines.append("")

        report_content = "\n".join(report_lines)
        report_file = O20_DIR / "tech_asset_registry_report.md"
        report_file.write_text(report_content, encoding="utf-8")
        logger.info("Saved telemetry report to %s", report_file)
        print(report_content)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AL2C Tech Asset & Living Documentation Sync Engine")
    parser.add_argument("-d", "--database", default="insilos20_dev", help="Target database (default: insilos20_dev)")
    parser.add_argument("-c", "--config", default="insilos.conf", help="Odoo configuration file (default: insilos.conf)")
    args = parser.parse_args()

    success = sync_all_assets(dbname=args.database, config_file=args.config)
    sys.exit(0 if success else 1)
