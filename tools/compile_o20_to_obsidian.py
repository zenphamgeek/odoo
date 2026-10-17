#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Knowledge Compiler for O20 (Insilos Enterprise Odoo 20) -> SQLite WAL + FTS5 & Local Obsidian Vault
========================================================================================================
Executes the unified 5-skill Core Knowledge Compiler pipeline (`core-knowledge-compiler`):
  1. `understand-ast` + `graphify-sql`: Incremental AST & Call-Graph compilation of `/home/zen/O20`
     into `~/.hermes/knowledge_compiler.db` (`repo="O20"`).
  2. `decision-ledger`: Records 11 canonical Bi-Temporal Architecture Decision Records
     (`ADR-20261016-001` .. `ADR-20261017-011`) covering Sovereign Odoo 20 Architecture & `SOP-DGM-01..11`.
  3. `obsidian-session-compiler`: Emits 5 bidirectional wikilinked Obsidian notes into
     `/home/zen/Obsidian/SecondBrain/20-Projects/Active/O20-Insilos-ERP/`, updates
     `/home/zen/Obsidian/SecondBrain/Maps/Decisions.md` and `/home/zen/Obsidian/SecondBrain/Home.md`,
     links session `790b1743-1724-4f27-a6fd-6d949bee50cf` via `link_session_to_vault()`, and runs
     `obsidian-second-brain-sync` + `obsidian-hermes-research-export`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

HOME = Path.home().resolve()
O20_ROOT = Path("/home/zen/O20").resolve()
HERMES_ROOT = Path("/home/zen/hermes-agent").resolve()
DB_PATH = HOME / ".hermes" / "knowledge_compiler.db"
VAULT_ROOT = HOME / "Obsidian" / "SecondBrain"
O20_VAULT_DIR = VAULT_ROOT / "20-Projects" / "Active" / "O20-Insilos-ERP"
SESSION_ID = "790b1743-1724-4f27-a6fd-6d949bee50cf"

if str(HERMES_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT / "tools"))
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from jev_clef_knowledge_compiler import (  # type: ignore  # noqa: E402
    KnowledgeCompilerDB,
    LocalJEVEvaluator,
)

# Regex used by /home/zen/.local/bin/obsidian-hermes-research-export to reject secret-like strings
_OBSIDIAN_EXPORT_SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+")

COMPONENT_SKILLS = [
    "obsidian-session-compiler",
    "graphify-sql",
    "understand-ast",
    "decision-ledger",
    "git-memory-compiler",
]

O20_COMPILE_SUBDIRS = [
    "addons/insilos_al2c",
    "enterprise/web_enterprise",
    "enterprise/documents",
    "enterprise/insilos_theme_genesis",
    "enterprise/insilos_website",
    "odoo/orm",
    "tools",
]

CANONICAL_O20_ADRS: List[Dict[str, str]] = [
    {
        "adr_id": "ADR-20261016-001",
        "title": "Sovereign Dark Mode Dual-Bundle Token Architecture & Anti-Slop SCSS Governance",
        "valid_from": "2026-10-16T00:00:00+00:00",
        "rationale": (
            "Enforces strict separation between web.assets_backend (light semantic variables at root) and "
            "web.assets_web_dark (.dark.scss bundles with html[data-theme='light'] safety guards). "
            "Bans hardcoded bare white/dark hex fallbacks with !important and wildcard globs where .dark.scss coexists."
        ),
    },
    {
        "adr_id": "ADR-20261016-002",
        "title": "OWL 2 / OWL 3 (@insilos/owl) Reactive Props Boundary & Zero-Leak ErrorDialog Telemetry",
        "valid_from": "2026-10-16T02:00:00+00:00",
        "rationale": (
            "Unions base useProps schema keys with Enterprise static props in addons/web/static/lib/owl/owl.js, "
            "guards Object.defineProperty against frozen props in view hooks, and enforces native Zero-Leak PII/Secret "
            "sanitization (masking middle 5 digits of 10-digit VN phone numbers and scrubbing multi-provider credentials) "
            "in ErrorDialog and SanitizedCopyButton."
        ),
    },
    {
        "adr_id": "ADR-20261016-003",
        "title": "Sovereign Multi-Tenant Navigation Idempotency & Physical Table Compatibility View Auto-Healing",
        "valid_from": "2026-10-16T04:00:00+00:00",
        "rationale": (
            "Mandates canonical (website_id, parent_id, url) deduplication on website.menu and auto-heals updatable "
            "PostgreSQL compatibility views (res_partner -> party_master, account_move -> finance_journal_entry, "
            "sale_order_line -> order_line, product_template -> catalog_item) via Registry._ensure_sovereign_bridges()."
        ),
    },
    {
        "adr_id": "ADR-20261016-004",
        "title": "SOP-DGM-01..04: Corporate Governance, 5-Step Employee Onboarding & 5-Gate Offboarding Hub",
        "valid_from": "2026-10-16T06:00:00+00:00",
        "rationale": (
            "Embeds the OWL Employee Self-Service Hub (.o_insilos_emp_dashboard) directly into HomeMenu, providing "
            "5-Step Onboarding (SOP-DGM-04) and 5-Gate Leaving/Offboarding (SOP-DGM-03/04: Asset Handover, IAM Revocation, "
            "SHUI TZ0857G Closure, Pro-Rata Final Settlement, and Tax/BHXH Handover)."
        ),
    },
    {
        "adr_id": "ADR-20261016-005",
        "title": "SOP-DGM-05: Statutory VN 2026 Payroll (Unit TZ0857G, 5-Bracket PIT) & 11-Column VCB DigiBiz Export",
        "valid_from": "2026-10-16T08:00:00+00:00",
        "rationale": (
            "Implements statutory Vietnam 2026 social insurance (BHXH 8%, BHYT 1.5%, BHTN 1% under unit code TZ0857G), "
            "progressive 5-bracket PIT calculation, and 11-column VCB DigiBiz .xlsx batch payroll export with text-formatted "
            "leading-zero account protection and CWE-1236 formula injection neutralization."
        ),
    },
    {
        "adr_id": "ADR-20261016-006",
        "title": "ISO/IEC 27701 & Decree 13/2023/ND-CP Need-to-Know Partial PII Masking & Maker-Checker Profile Updates",
        "valid_from": "2026-10-16T10:00:00+00:00",
        "rationale": (
            "Default-masks sensitive employee PII (CCCD 089******917, phone 090*****01, bank account 13****8161) in UI payloads, "
            "restricts 30-second reveal (/insilos/employee_dashboard/reveal_pii) to SELF and HR_EXEC with immutable audit logging "
            "(dgm.hr.privacy_audit_log), and enforces 2-step Maker-Checker approval for post-contract profile changes."
        ),
    },
    {
        "adr_id": "ADR-20261016-007",
        "title": "Canonical Google Drive Shared-with-me 9-Level Data Room Tree & 11-Profile RBAC Matrix (978 Folders, 7,886 Files)",
        "valid_from": "2026-10-16T12:00:00+00:00",
        "rationale": (
            "Synchronizes the complete 9-level Google Drive 'Shared with me' hierarchy (info@inno.ai.vn <- tham.mai@inno.ai.vn) "
            "under root '3. INNO+ DGM' (978 folders, 7,886 files), enforces Zero Empty Folders, and classifies 100% of records "
            "into 11 deterministic RBAC profiles (dgm.document.rbac.rule) with 0 unmapped records."
        ),
    },
    {
        "adr_id": "ADR-20261016-008",
        "title": "SOP-DGM-06..08: Partner Onboarding Tiering, Staff Augmentation & Cryptographic 1C26TAA E-Invoice Pipeline",
        "valid_from": "2026-10-16T16:00:00+00:00",
        "rationale": (
            "Establishes 5-Gate Partner Onboarding (PTN-DGM-2026-0001..0009, Tier 1/2/3), B2B Staff Augmentation SLA contracts "
            "(SOP-DGM-07: MTI Technology & AIfin 360-Sales), and MTI-style 2-stage Draft-to-Official 1C26TAA VAT E-Invoicing "
            "(SOP-DGM-08) protected by two-key PostgreSQL advisory locks and SHA-256 customer acceptance seals."
        ),
    },
    {
        "adr_id": "ADR-20261016-009",
        "title": "SOP-DGM-09: Best-Practice Software Tax Incentive Contracts (MTI Onsite & KTT Turnkey ERP) & Drive Brand Footer",
        "valid_from": "2026-10-16T20:00:00+00:00",
        "rationale": (
            "Codifies 8 bilingual software contract templates (TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04) compliant with "
            "Decree 174/2025/ND-CP (8% VAT), Circular 219/2013/TT-BTC (0% Export VAT), and CIT software production incentives "
            "(4 years exemption + 9 years 50% reduction), paired with the standardized Google Drive Digimate Logo Brand Footer."
        ),
    },
    {
        "adr_id": "ADR-20261017-010",
        "title": "SOP-DGM-10: Employee 4-Pillar KPI Evaluation, Quarterly Work Reviews & Mandatory SWE Skill Upgrade Gate",
        "valid_from": "2026-10-17T00:00:00+00:00",
        "rationale": (
            "Implements dgm.hr.skill.track (8 canonical tracks: OWL 3, Dark Mode SCSS, Mojo SIMD, Grounded RAG, ISO 27001, "
            "Playwright E2E, K8s/PG16, SAP Activate), dgm.hr.employee.skill.gate (29 assignments), dgm.hr.kpi.evaluation "
            "(4 weighted pillars: Delivery 40%, Quality 25%, Skill Gate 20%, Compliance 15%), and dgm.hr.work.review. "
            "Enforces a hard promotion/grade cap (max B_good / 84.90) until 100% of mandatory skill tracks are certified."
        ),
    },
    {
        "adr_id": "ADR-20261017-011",
        "title": "SOP-DGM-11: PDCA Project Templates (SAP Activate 5-Phase), 360-Degree 9-Box HR Appraisals & Software OKR Cascade",
        "valid_from": "2026-10-17T01:30:00+00:00",
        "rationale": (
            "Implements dgm.project.pdca.template (PRJ-TPL-PDCA-01..04 with 5-stage [TPL-PDCA] projects), dgm.okr.objective "
            "(12 3-tier OKRs: 3 Company + 9 Squad/Individual), dgm.okr.key.result (24 KRs with live check-in cascade), and "
            "dgm.hr.appraisal.sheet (9 360-degree appraisals with 9-Box Talent Calibration where incomplete skill gates lock "
            "engineers at box_6_emerging / 84.90 until certified)."
        ),
    },
]


def _sanitize_for_obsidian_export(markdown_text: str) -> str:
    """Ensures no substring in generated Markdown triggers obsidian-hermes-research-export's SECRET regex."""
    return _OBSIDIAN_EXPORT_SECRET_RE.sub(lambda m: f"{m.group(1)} [REDACTED_PARAM]", markdown_text)


def ensure_skill_symlinks() -> List[str]:
    """Ensures core-knowledge-compiler and its 5 component skills are linked in global and workspace skill dirs."""
    global_skills_dir = HOME / ".gemini" / "config" / "skills"
    workspace_skills_dir = O20_ROOT / ".agents" / "skills"
    hermes_skills_dir = HERMES_ROOT / ".agents" / "skills"

    global_skills_dir.mkdir(parents=True, exist_ok=True)
    workspace_skills_dir.mkdir(parents=True, exist_ok=True)

    linked: List[str] = []

    # 1. Symlink core-knowledge-compiler into workspace .agents/skills/
    core_global = global_skills_dir / "core-knowledge-compiler"
    core_ws = workspace_skills_dir / "core-knowledge-compiler"
    if core_global.exists():
        if core_ws.is_symlink() or core_ws.exists():
            if core_ws.is_symlink() and core_ws.resolve() != core_global.resolve():
                core_ws.unlink()
                core_ws.symlink_to(core_global, target_is_directory=True)
        else:
            core_ws.symlink_to(core_global, target_is_directory=True)
        linked.append("core-knowledge-compiler")

    # 2. Symlink 5 component skills into both ~/.gemini/config/skills/ and /home/zen/O20/.agents/skills/
    for skill_name in COMPONENT_SKILLS:
        src = hermes_skills_dir / skill_name
        if not src.exists():
            continue
        for dst_root in (global_skills_dir, workspace_skills_dir):
            dst = dst_root / skill_name
            if dst.is_symlink():
                if dst.resolve() != src.resolve():
                    dst.unlink()
                    dst.symlink_to(src, target_is_directory=True)
            elif not dst.exists():
                dst.symlink_to(src, target_is_directory=True)
        linked.append(skill_name)

    return linked


def query_o20_graph_stats(compiler_db: KnowledgeCompilerDB) -> Dict[str, Any]:
    """Queries live AST node, edge, logic_tree, decision, and top module statistics for repo='O20'."""
    cur = compiler_db.conn.cursor()

    cur.execute(
        "SELECT node_type, COUNT(*) FROM nodes WHERE repo='O20' GROUP BY node_type"
    )
    node_counts = dict(cur.fetchall())

    cur.execute(
        """
        SELECT e.edge_type, COUNT(*)
          FROM edges e
          JOIN nodes n ON n.id = e.src_id
         WHERE n.repo = 'O20'
         GROUP BY e.edge_type
        """
    )
    edge_counts = dict(cur.fetchall())

    cur.execute(
        """
        SELECT lt.tree_type, COUNT(*)
          FROM logic_trees lt
          JOIN nodes n ON n.id = lt.root_id
         WHERE n.repo = 'O20'
         GROUP BY lt.tree_type
        """
    )
    tree_counts = dict(cur.fetchall())

    cur.execute(
        """
        SELECT name, file_path, end_lineno, sha256
          FROM nodes
         WHERE repo='O20' AND node_type='FILE'
         ORDER BY COALESCE(end_lineno, 0) DESC, name ASC
        """
    )
    all_files = cur.fetchall()

    cur.execute(
        """
        SELECT name, file_path, lineno, end_lineno
          FROM nodes
         WHERE repo='O20' AND node_type='CLASS'
         ORDER BY file_path ASC, lineno ASC
        """
    )
    all_classes = cur.fetchall()

    cur.execute(
        """
        SELECT adr_id, title, status, rationale, valid_from, valid_to, sha256
          FROM decisions
         WHERE repo='O20' AND status='ACTIVE'
         ORDER BY adr_id ASC
        """
    )
    active_adrs = cur.fetchall()

    return {
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "tree_counts": tree_counts,
        "files": all_files,
        "classes": all_classes,
        "active_adrs": active_adrs,
    }


def generate_obsidian_notes(
    compiler_db: KnowledgeCompilerDB,
    stats: Dict[str, Any],
    delta_res: Dict[str, Any],
    jev_eval_info: Dict[str, Any],
) -> List[Tuple[str, str]]:
    """Generates the 5 interlinked Obsidian Markdown notes under O20-Insilos-ERP/."""
    O20_VAULT_DIR.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    nc = stats["node_counts"]
    ec = stats["edge_counts"]
    tc = stats["tree_counts"]
    files = stats["files"]
    classes = stats["classes"]
    adrs = stats["active_adrs"]

    file_count = nc.get("FILE", 0)
    class_count = nc.get("CLASS", 0)
    func_count = nc.get("FUNCTION", 0)
    mod_count = nc.get("MODULE", 0)
    total_nodes = sum(nc.values())
    total_edges = sum(ec.values())
    total_trees = sum(tc.values())

    # -------------------------------------------------------------------------
    # Note 1: 00-O20-Master-Architecture-MOC.md
    # -------------------------------------------------------------------------
    moc_path = O20_VAULT_DIR / "00-O20-Master-Architecture-MOC.md"
    moc_content = f"""---
hermes_research: true
type: architecture
project: O20
status: active
compiled_at: "{now_iso}"
session_id: "{SESSION_ID}"
---

# O20 Insilos Enterprise Odoo 20 — Master Architecture MOC

> **Canonical Knowledge Graph Hub** compiled by `core-knowledge-compiler` (`jev_clef_knowledge_compiler.py`) into `~/.hermes/knowledge_compiler.db` (SQLite WAL + FTS5) and synchronized to local Obsidian (`SecondBrain`).

## Navigation & Knowledge Graph Index

- **Parent Maps**: [[Maps/Projects|Projects Map]] • [[Maps/Decisions|Decisions Map]] • [[Home|SecondBrain Home]]
- **Active Compilation Session**: [[Session-{SESSION_ID}]]
- **O20 Knowledge Graph Notes**:
  1. [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|00 — O20 Master Architecture MOC]]
  2. [[20-Projects/Active/O20-Insilos-ERP/01-AST-Knowledge-Graph-Models|01 — AST Knowledge Graph & ORM Models ({file_count} Files, {class_count} Classes, {func_count} Functions)]]
  3. [[20-Projects/Active/O20-Insilos-ERP/02-DGM-INNORIA-SOP-01-to-11-Master-Ledger|02 — Digimate & Innoria Master SOP Ledger (SOP-DGM-01 to SOP-DGM-11)]]
  4. [[20-Projects/Active/O20-Insilos-ERP/03-BiTemporal-ADRs-and-Session-Links|03 — Bi-Temporal Architecture Decision Records ({len(adrs)} Active ADRs)]]
  5. [[20-Projects/Active/O20-Insilos-ERP/04-Google-Drive-SharedWithMe-RBAC-Matrix|04 — Google Drive Shared-with-me 9-Level Tree & 11-Profile RBAC Matrix]]
- **Direct Documentation Link**: [O20 Organization & Process SOP Docs](../../../Data/Projects/O20__docs/organization_and_processes/)

---

## Live SQLite WAL + FTS5 Compilation Metrics (`repo="O20"`)

| Metric Category | Subtype / Relation | Compiled Count | Storage / Verification |
| :--- | :--- | ---: | :--- |
| **AST Nodes (`nodes`)** | `FILE` (Python Modules & Scripts) | **{file_count}** | SHA-256 Attested (`nodes_fts` Indexed) |
| **AST Nodes (`nodes`)** | `CLASS` (Odoo ORM Models & Controllers) | **{class_count}** | Line-Range Mapped (`lineno`..`end_lineno`) |
| **AST Nodes (`nodes`)** | `FUNCTION` (Methods, Compute & Routes) | **{func_count}** | Call-Graph Linked |
| **AST Nodes (`nodes`)** | `MODULE` (Imported Packages) | **{mod_count}** | Dependency Graph |
| **Total Graph Nodes** | All `O20` Nodes | **{total_nodes}** | `~/.hermes/knowledge_compiler.db` |
| **Graph Edges (`edges`)** | `CONTAINS` (`EXTRACTED`, conf `1.0`) | **{ec.get("CONTAINS", 0)}** | File -> Class / Function |
| **Graph Edges (`edges`)** | `IMPORTS` (`EXTRACTED`, conf `1.0`) | **{ec.get("IMPORTS", 0)}** | File -> Module |
| **Graph Edges (`edges`)** | `CALLS` (`EXTRACTED`, conf `1.0`) | **{ec.get("CALLS", 0)}** | AST Call Graph |
| **Total Graph Edges** | All `O20` Edges | **{total_edges}** | Foreign-Key Enforced |
| **Logic Trees (`logic_trees`)** | `CONTROL_FLOW` + `CALL_GRAPH` | **{total_trees}** | `{tc.get("CONTROL_FLOW", 0)}` CF / `{tc.get("CALL_GRAPH", 0)}` CG |
| **Bi-Temporal ADRs (`decisions`)** | `ACTIVE` Architectural Decisions | **{len(adrs)}** | `ADR-20261016-001` .. `ADR-20261017-011` |
| **Delta Run Summary** | Scanned / Recompiled / Unchanged | **{delta_res.get("scanned", 0)}** / **{delta_res.get("recompiled", 0)}** / **{delta_res.get("skipped_unchanged", 0)}** | JEV Engine: `{jev_eval_info.get("engine")}` (`C={jev_eval_info.get("complexity")}`) |

---

## Architectural Pillars of Insilos Enterprise Odoo 20 (`/home/zen/O20`)

```mermaid
flowchart TD
    subgraph UI["1. OWL 2/3 WebClient & Sovereign Dual-Theme UI"]
        HM["HomeMenu Employee Self-Service Hub (.o_insilos_emp_dashboard)"]
        DM["Dual-Bundle Dark Mode (web.assets_backend + web.assets_web_dark)"]
        ED["Zero-Leak ErrorDialog & SanitizedCopyButton"]
    end
    subgraph ORM["2. Sovereign ORM & Compatibility Bridge Layer (odoo/orm)"]
        BR["Registry._ensure_sovereign_bridges()"]
        PM["party_master <-> res_partner"]
        FJ["finance_journal_entry <-> account_move"]
        OL["order_line <-> sale_order_line"]
        CI["catalog_item <-> product_template"]
    end
    subgraph SOP["3. Digimate & Innoria Enterprise Governance (SOP-DGM-01..11)"]
        HR["SOP-DGM-04/05: 5-Step Onboarding, 5-Gate Offboarding, TZ0857G Payroll & VCB DigiBiz"]
        B2B["SOP-DGM-06..09: Partner Tiering, MTI/AIfin Timesheets, 1C26TAA E-Invoice & Tax Incentives"]
        KPI["SOP-DGM-10: 4-Pillar KPI & Mandatory 8-Track SWE Skill Upgrade Gate"]
        OKR["SOP-DGM-11: 4 PDCA Project Templates, 12 OKRs (24 KRs) & 360° 9-Box Appraisals"]
    end
    subgraph DR["4. Google Drive Shared-with-me Data Room & Knowledge Compiler"]
        GD["3. INNO+ DGM (978 Folders, 7,886 Files, 11 RBAC Profiles)"]
        KC["SQLite WAL + FTS5 (~/.hermes/knowledge_compiler.db) <-> Local Obsidian SecondBrain"]
    end
    UI --> ORM
    ORM --> SOP
    SOP --> DR
```

## Active Bi-Temporal Decisions Summary

| ADR ID | Title | Status |
| :--- | :--- | :--- |
"""
    for adr_id, title, status, _rat, valid_from, _vt, _sha in adrs:
        moc_content += f"| [[ADR-{adr_id}\\|{adr_id}]] | {title} | `{status}` ({valid_from[:10]}) |\n"

    moc_content = _sanitize_for_obsidian_export(moc_content)
    moc_path.write_text(moc_content, encoding="utf-8")

    # -------------------------------------------------------------------------
    # Note 2: 01-AST-Knowledge-Graph-Models.md
    # -------------------------------------------------------------------------
    ast_path = O20_VAULT_DIR / "01-AST-Knowledge-Graph-Models.md"
    ast_content = f"""---
hermes_research: true
type: architecture
project: O20
status: active
compiled_at: "{now_iso}"
session_id: "{SESSION_ID}"
---

# O20 AST Knowledge Graph — Compiled Modules, ORM Models & Controllers

> Linked to [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|00 — O20 Master Architecture MOC]] • [[Session-{SESSION_ID}]]

## 1. Core `addons/insilos_al2c` & `odoo/orm` Classes (`CLASS` Nodes in SQLite)

| Class Name | Source File (Relative to `/home/zen/O20`) | Line Range | Architectural Role |
| :--- | :--- | :--- | :--- |
"""
    for cname, fpath, lineno, end_lineno in classes:
        rel_fp = str(fpath or "").replace("/home/zen/O20/", "")
        if any(
            rel_fp.startswith(prefix)
            for prefix in ("addons/insilos_al2c/", "odoo/orm/", "enterprise/web_enterprise/", "enterprise/documents/")
        ):
            role = "ORM Model / Controller"
            if "controllers/" in rel_fp:
                role = "HTTP / JSON-RPC Controller (`readonly=False`)"
            elif "odoo/orm/" in rel_fp:
                role = "Sovereign Core ORM Engine"
            elif "dgm_okr_appraisal_project_pdca" in rel_fp:
                role = "SOP-DGM-11 OKR, 360° 9-Box Appraisal & PDCA Template"
            elif "dgm_hr_kpi_skill" in rel_fp:
                role = "SOP-DGM-10 4-Pillar KPI & Mandatory SWE Skill Gate"
            elif "dgm_software_tax_contract" in rel_fp:
                role = "SOP-DGM-09 Software Tax Incentive Contract Blueprint"
            elif "dgm_project_timesheet_billing" in rel_fp:
                role = "SOP-DGM-08 Project Timesheet & 1C26TAA E-Invoice Pipeline"
            elif "dgm_partner_onboarding" in rel_fp:
                role = "SOP-DGM-06/07 Partner Onboarding & B2B Staff Augmentation"
            elif "dgm_document_rbac" in rel_fp:
                role = "11-Profile Document RBAC Matrix Engine"
            elif "dgm_hr_governance" in rel_fp:
                role = "SOP-DGM-03/04/05 HR Onboarding, Offboarding, Payroll & ISO 27701"
            ast_content += f"| `{cname}` | `{rel_fp}` | `L{lineno}–L{end_lineno or lineno}` | {role} |\n"

    ast_content += """
---

## 2. Top Compiled Python Files by Line Count (`FILE` Nodes with SHA-256 Attestation)

| File Name | Relative Path | Lines | SHA-256 Prefix |
| :--- | :--- | ---: | :--- |
"""
    for fname, fpath, end_lineno, sha256 in files[:80]:
        rel_fp = str(fpath or "").replace("/home/zen/O20/", "")
        sha_short = (sha256 or "")[:16]
        ast_content += f"| `{fname}` | `{rel_fp}` | {end_lineno or 0} | `{sha_short}` |\n"

    ast_content = _sanitize_for_obsidian_export(ast_content)
    ast_path.write_text(ast_content, encoding="utf-8")

    # -------------------------------------------------------------------------
    # Note 3: 02-DGM-INNORIA-SOP-01-to-11-Master-Ledger.md
    # -------------------------------------------------------------------------
    sop_path = O20_VAULT_DIR / "02-DGM-INNORIA-SOP-01-to-11-Master-Ledger.md"
    sop_content = f"""---
hermes_research: true
type: playbook
project: O20
status: active
compiled_at: "{now_iso}"
session_id: "{SESSION_ID}"
---

# Digimate & Innoria Master SOP Ledger (`SOP-DGM-01` to `SOP-DGM-11`)

> Linked to [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|00 — O20 Master Architecture MOC]] • [[20-Projects/Active/O20-Insilos-ERP/03-BiTemporal-ADRs-and-Session-Links|03 — Bi-Temporal ADRs]] • [[Session-{SESSION_ID}]]

## 1. Complete 11-SOP Governance Architecture (`CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ — MST: 0317958465 • Mã ĐV BHXH: TZ0857G`)

| SOP Code | Title & Operational Scope | Core ORM Models (`insilos_al2c`) | Verification Gate Script |
| :--- | :--- | :--- | :--- |
| **`SOP-DGM-01`** | Cơ cấu Tổ chức, Phân quyền RBAC 5 Tầng & Quản trị Doanh nghiệp | `res.company`, `hr.department`, `dgm.document.rbac.rule` | `tools/test_dgm_inno_rbac_access.py` |
| **`SOP-DGM-02`** | Quy trình Mua hàng, Tạm ứng, Hoàn ứng & Phê duyệt Chi phí (`DOA`) | `account.move`, `purchase.order` | `tools/test_dgm_hr_payroll_dashboard.py` |
| **`SOP-DGM-03`** | Quy trình Nghỉ việc 5 Cổng (`5-Gate Offboarding`) & Thu hồi Tài sản / IAM | `dgm.hr.offboarding.checklist`, `hr.employee` | `tools/test_dgm_hr_payroll_dashboard.py` |
| **`SOP-DGM-04`** | Quy trình Hội nhập Nhân sự Mới 5 Bước (`5-Step Onboarding`) & Hợp đồng `hr.version` | `dgm.hr.onboarding.checklist`, `hr.version` | `tools/test_dgm_hr_payroll_dashboard.py` |
| **`SOP-DGM-05`** | Quy trình Tính lương BHXH `TZ0857G`, Thuế TNCN 5 Bậc & Xuất VCB DigiBiz 11 Cột | `hr.employee`, `dgm.hr.profile.change.request`, `dgm.hr.privacy_audit_log` | `tools/test_dgm_hr_payroll_dashboard.py` |
| **`SOP-DGM-06`** | Quy trình Thẩm định, Phân hạng (`Tier 1/2/3`) & Onboarding Đối tác B2B | `res.partner`, `dgm.partner.onboarding.checklist` | `tools/test_dgm_partner_onboarding.py` |
| **`SOP-DGM-07`** | Quy trình Phái cử Nhân sự Kỹ thuật B2B (`Staff Augmentation`: MTI & AIfin) | `sale.order`, `project.project`, `hr.employee` | `tools/test_dgm_partner_onboarding.py` |
| **`SOP-DGM-08`** | Quy trình Chấm công Dự án, Nghiệm thu SHA-256 & Xuất Hóa đơn Nháp / Chính thức `1C26TAA` | `dgm.project.notification`, `dgm.project.timesheet.sheet`, `dgm.project.timesheet.line` | `tools/test_dgm_timesheet_to_invoice_pipeline.py` |
| **`SOP-DGM-09`** | Bộ Hợp đồng Mẫu Dịch vụ Phần mềm Tối ưu Ưu đãi Thuế TNDN & GTGT (MTI & KTT) | `dgm.software.contract.template` | `tools/test_dgm_software_tax_contracts.py` |
| **`SOP-DGM-10`** | Quy trình Đánh giá KPI 4 Trụ cột & Cổng Nâng cấp Kỹ năng Kỹ sư Phần mềm Bắt buộc | `dgm.hr.skill.track`, `dgm.hr.employee.skill.gate`, `dgm.hr.kpi.evaluation`, `dgm.hr.work.review` | `tools/test_dgm_kpi_skill_framework.py` |
| **`SOP-DGM-11`** | Quy trình PDCA Quản trị Dự án Phần mềm, Đánh giá 360° (`9-Box`) & OKRs Doanh nghiệp | `dgm.project.pdca.template`, `dgm.okr.objective`, `dgm.okr.key.result`, `dgm.hr.appraisal.sheet` | `tools/test_dgm_okr_appraisal_project_pdca.py` |

---

## 2. Canonical 28 Standardized HTML Templates in `Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance`

All 28 templates carry the authentic Google Drive Digimate Logo Header & Footer (`data-dgm-footer="drive-logo-v1"`, `data-logo-source="google-drive-logo-folder"`):

1. **HR, Payroll, KPI, 360° Appraisals & OKRs (`TPL-HR-01..08`, `TPL-OKR-01`)**:
   - `TPL-HR-01_Hop_Dong_Lao_Dong_Chuan_Digimate_2026.html`
   - `TPL-HR-02_Thoa_Thuan_Bao_Mat_NDA_Va_SHTT_Nhan_Su.html`
   - `TPL-HR-03_Bien_Ban_Ban_Giao_Cong_Viec_Tai_San_Offboarding.html`
   - `TPL-HR-04_Phieu_Danh_Gia_Thu_Viec_2_Thang_85pct.html`
   - `TPL-HR-05_De_Nghi_Tam_Ung_Hoan_Ung_Chi_Phi_DOA.html`
   - `TPL-HR-06_Phieu_Danh_Gia_KPI_Va_Lo_Trinh_Nang_Cap_Ky_Nang_SOP_DGM_10.html`
   - `TPL-HR-07_Phieu_Danh_Gia_Nhan_Su_360_HR_Appraisal_9Box_PDCA.html`
   - `TPL-HR-08_Bien_Ban_Hieu_Chuan_Nang_Luc_Career_Calibration_SWE.html`
   - `TPL-OKR-01_Khung_OKRs_Doanh_Nghiep_Phan_Mem_Digimate_Innoria_2026.html`
2. **Partner Onboarding & Staff Augmentation (`TPL-ONB-01..05`)**:
   - `TPL-ONB-01_Phieu_Dang_Ky_Va_Tham_Dinh_Doi_Tac_KYC_KYB.html`
   - `TPL-ONB-02_Hop_Dong_Nguyen_Tac_Dich_Vu_CNTT_MSA.html`
   - `TPL-ONB-03_Thoa_Thuan_Bao_Mat_NDA_Va_Bao_Ve_DLCN_DPA_ND13.html`
   - `TPL-ONB-04_Phu_Luc_SLA_Quy_Trinh_Doi_Soat_Timesheet_Hoa_Don_1C26TAA.html`
   - `TPL-ONB-05_Lenh_Phai_Cu_Nhan_Su_Ky_Thuat_Onsite_SOW.html`
3. **Project Delivery & PDCA SAP Activate (`TPL-PRJ-01..06`)**:
   - `TPL-PRJ-01_Dieu_Le_Khoi_Dong_Du_An_Project_Charter.html`
   - `TPL-PRJ-02_Ho_So_Thiet_Ke_Kien_Truc_Ky_Thuat_SDD.html`
   - `TPL-PRJ-03_Bien_Ban_Kiem_Thu_Va_Nghiem_Thu_UAT.html`
   - `TPL-PRJ-04_Bien_Ban_Ban_Giao_He_Thong_Go_Live_Acceptance.html`
   - `TPL-PRJ-05_Mau_Ke_Hoach_Du_An_Phan_Mem_PDCA_SAP_Activate.html`
   - `TPL-PRJ-06_Bien_Ban_Nghiem_Thu_Sprint_UAT_Va_Go_Live_PDCA.html`
4. **Software Tax Incentive Contracts (`TPL-SW-MTI-01..04`, `TPL-SW-KTT-01..04`)**:
   - `TPL-SW-MTI-01_Hop_Dong_Nguyen_Tac_Phat_Trien_Phan_Mem_B2B_MTI_Tax_Optimal.html`
   - `TPL-SW-MTI-02_Phu_Luc_SOW_Phai_Cu_Ky_Su_Phan_Mem_Onsite_SLA_MTI.html`
   - `TPL-SW-MTI-03_Bien_Ban_Nghiem_Thu_Timesheet_Va_Xac_Nhan_Cong_Doan_San_Xuat_Phan_Mem.html`
   - `TPL-SW-MTI-04_Ho_So_Tu_Xac_Dinh_Quy_Trinh_7_Cong_Doan_San_Xuat_Phan_Mem_Uu_Dai_Thue_TNDN.html`
   - `TPL-SW-KTT-01_Hop_Dong_Tron_Goi_Thiet_Ke_Phat_Trien_Trien_Khai_Phan_Mem_ERP_AI_KTT.html`
   - `TPL-SW-KTT-02_Phu_Luc_Phan_Tach_Gia_Tri_Ban_Quyen_Phan_Mem_Trien_Khai_Va_Cloud_SLA_KTT.html`
   - `TPL-SW-KTT-03_Bien_Ban_Nghiem_Thu_UAT_Ban_Giao_Ma_Nguon_SHTT_Va_Go_Live_KTT.html`
   - `TPL-SW-KTT-04_Hop_Dong_Xuat_Khau_Phan_Mem_Quoc_Te_Thue_Suat_GTGT_0_Phan_Tram_KTT_Global.html`

---

## 3. Canonical 9-Employee Roster, KPI Grades & 360° 9-Box Calibration (`2026-Q4`)

| Emp Code | Full Name | Role / Level | Primary OKR (`2026-Q4`) | SWE Skill Gate | 360° Calibrated Score | 9-Box Calibration |
| :--- | :--- | :--- | :--- | :--- | ---: | :--- |
| `DGM-001` | Lê Xuân Hoàng | CEO (`L5 Principal`) | `OKR-2026-Q4-C01` / `EXEC01` | `4/4` Certified (100%) | **98.28** | `box_9_star` (`[9] Top Talent`) |
| `DGM-002` | Nguyễn Hoài Ân | CTO (`L5 Principal`) | `OKR-2026-Q4-C02` / `AI01` | `4/4` Certified (100%) | **98.11** | `box_9_star` (`[9] Top Talent`) |
| `DGM-003` | Mai Thị Hồng Thắm | Chief Accountant & HR (`L4 Lead`) | `OKR-2026-Q4-C03` / `FIN01` | `2/2` Certified (100%) | **98.28** | `box_9_star` (`[9] Top Talent`) |
| `DGM-004` | Bùi Hữu Tài | Senior SWE — MTI (`L3 Senior`) | `OKR-2026-Q4-B2B01` | `4/4` Certified (100%) | **97.25** | `box_9_star` (`[9] Top Talent`) |
| `DGM-005` | Huỳnh Trần Quang Khánh | Tech Lead — MTI (`L4 Lead`) | `OKR-2026-Q4-ENG01` | `4/4` Certified (100%) | **98.28** | `box_9_star` (`[9] Top Talent`) |
| `DGM-006` | Ngô Thanh Lộc | Senior SWE — MTI (`L3 Senior`) | `OKR-2026-Q4-B2B02` | `3/3` Certified (100%) | **93.35** | `box_9_star` (`[9] Top Talent`) |
| `DGM-007` | Lê Cao Bảo Phúc | Mid SWE — MTI (`L2 Mid`) | `OKR-2026-Q4-B2B03` | `2/3` (`SKL-ERP-OWL3` WIP) | **84.90** *(Cap)* | `box_6_emerging` (`[6] Emerging — Gate Cap`) |
| `DGM-008` | Thái Nguyễn Đăng Khoa | Junior SWE & QA (`L1 Junior`) | `OKR-2026-Q4-QA01` | `2/3` (`SKL-QA-PLAYWRIGHT` WIP) | **84.90** *(Cap)* | `box_6_emerging` (`[6] Emerging — Gate Cap`) |
| `DGM-009` | Trần Văn Huỳnh Phố | Senior SWE — AIfin (`L3 Senior`) | `OKR-2026-Q4-B2B04` | `4/4` Certified (100%) | **98.15** | `box_9_star` (`[9] Top Talent`) |
"""
    sop_content = _sanitize_for_obsidian_export(sop_content)
    sop_path.write_text(sop_content, encoding="utf-8")

    # -------------------------------------------------------------------------
    # Note 4: 03-BiTemporal-ADRs-and-Session-Links.md
    # -------------------------------------------------------------------------
    adr_path = O20_VAULT_DIR / "03-BiTemporal-ADRs-and-Session-Links.md"
    adr_content = f"""---
hermes_research: true
type: decision
project: O20
status: active
compiled_at: "{now_iso}"
session_id: "{SESSION_ID}"
---

# Bi-Temporal Architecture Decision Ledger (`decisions` & `session_links`)

> Linked to [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|00 — O20 Master Architecture MOC]] • [[Maps/Decisions|Decisions Map]] • [[Session-{SESSION_ID}]]

All Architecture Decision Records below are persisted in `~/.hermes/knowledge_compiler.db` (`decisions` table) with bi-temporal bounds (`valid_from`, `valid_to IS NULL` for `ACTIVE` records) and SHA-256 cryptographic attestation.

"""
    for adr_id, title, status, rationale, valid_from, valid_to, sha256 in adrs:
        adr_content += f"""## [[ADR-{adr_id}]] — {title}

- **Status**: `{status}`
- **Repository**: `O20`
- **Valid From**: `{valid_from}` | **Valid To**: `{valid_to or "CURRENT (ACTIVE)"}`
- **SHA-256 Attestation**: `{sha256}`
- **Session Link**: [[Session-{SESSION_ID}]] [[ADR-{adr_id}]]
- **Rationale**:
  {rationale}

---

"""
    adr_content = _sanitize_for_obsidian_export(adr_content)
    adr_path.write_text(adr_content, encoding="utf-8")

    # -------------------------------------------------------------------------
    # Note 5: 04-Google-Drive-SharedWithMe-RBAC-Matrix.md
    # -------------------------------------------------------------------------
    rbac_path = O20_VAULT_DIR / "04-Google-Drive-SharedWithMe-RBAC-Matrix.md"
    rbac_content = f"""---
hermes_research: true
type: architecture
project: O20
status: active
compiled_at: "{now_iso}"
session_id: "{SESSION_ID}"
---

# Canonical Google Drive `Shared with me` 9-Level Tree & 11-Profile RBAC Matrix

> Linked to [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|00 — O20 Master Architecture MOC]] • [[ADR-ADR-20261016-007|ADR-20261016-007]] • [[Session-{SESSION_ID}]]

## 1. Canonical Data Room Topology (`3. INNO+ DGM`)

- **Google Drive Source**: `Shared with me` (`sharedWithMe = true`) of `info@inno.ai.vn` shared by `tham.mai@inno.ai.vn`.
- **Unified Root Folder**: `3. INNO+ DGM` (`ID 3223` in `insilos20_dev`, `ID 207` in `innoria_prod`).
- **Scale & Depth**: **978 active folders** and **7,886 active files** across **9 hierarchical levels** (`0` empty active folders, `0` unmapped RBAC records).

## 2. The 11 Deterministic RBAC Profiles (`dgm.document.rbac.rule`)

| Seq | Profile Code | Vietnamese Governance Scope | Internal Access | Link Access | Authorized Roles (`DGM-001..009`) |
| ---: | :--- | :--- | :--- | :--- | :--- |
| 1 | `public_brand` | Nhận diện Thương hiệu, Logo Drive & Brochure Công khai | `view` | `view` | Toàn bộ Nhân sự (`DGM-001..009`) & Đối tác |
| 2 | `company_common` | Quy trình Chuẩn (`SOP-DGM-01..11`) & Bộ Mẫu Biểu Chuẩn Digimate | `view` | `none` | Toàn bộ Nhân sự Nội bộ (`DGM-001..009`) |
| 3 | `executive_board` | Chiến lược Ban Điều hành, Cổ đông & Đầu tư (`CEO/CTO`) | `view` | `none` | `DGM-001` (CEO), `DGM-002` (CTO) (`edit`) |
| 4 | `hr_recruitment` | Tuyển dụng, JD, Ngân hàng CV & Đánh giá Ứng viên | `view` | `none` | `DGM-001`, `DGM-002`, `DGM-003` (HR), `DGM-005` (Tech Lead) |
| 5 | `hr_confidential` | Hồ sơ Nhân sự, Hợp đồng, Lương BHXH `TZ0857G`, KPI & Appraisal 360° | `view` | `none` | `DGM-001`, `DGM-003` (`edit`); Nhân sự xem theo phân quyền ISO 27701 |
| 6 | `finance_tax_legal` | Kế toán – Thuế, Sao kê VCB DigiBiz, Hóa đơn `1C26TAA` & Pháp lý | `view` | `none` | `DGM-001` (CEO), `DGM-003` (Kế toán trưởng), `DGM-002` (CTO) |
| 7 | `commercial_contracts` | Hợp đồng Thương mại B2B (`INNO - HỢP ĐỒNG`, MSA, SOW, Ưu đãi Thuế) | `view` | `none` | `DGM-001`, `DGM-002`, `DGM-003`, `DGM-005` |
| 8 | `mti_timesheet_Delivery` | Bảng Chấm công `MTI - TIMESHEET`, Nghiệm thu & Phái cử Onsite | `edit` | `none` | `DGM-001..007` (MTI Squad), `DGM-009` (AIfin Squad) |
| 9 | `project_delivery` | Hồ sơ Dự án (`DỰ ÁN`, `KH`, KTT, Swarovski, Canva, AIfin, Innoria) | `edit` | `none` | Toàn bộ Kỹ sư Dự án & QA (`DGM-001..009`) |
| 10 | `marketing_growth` | Chiến dịch Marketing, Website & Truyền thông Số | `edit` | `none` | Ban Điều hành & Đội ngũ Sản phẩm / Giao diện |
| 11 | `personal_workspace` | Không gian Lưu trữ Cá nhân theo Chủ sở hữu (`owner_id`) | `view` | `none` | Chính chủ (`SELF`) & Quản trị Hệ thống |
"""
    rbac_content = _sanitize_for_obsidian_export(rbac_content)
    rbac_path.write_text(rbac_content, encoding="utf-8")

    return [
        (str(moc_path.relative_to(VAULT_ROOT)), "ADR-20261016-001"),
        (str(ast_path.relative_to(VAULT_ROOT)), "ADR-20261016-002"),
        (str(sop_path.relative_to(VAULT_ROOT)), "ADR-20261017-010"),
        (str(adr_path.relative_to(VAULT_ROOT)), "ADR-20261017-011"),
        (str(rbac_path.relative_to(VAULT_ROOT)), "ADR-20261016-007"),
    ]


def update_vault_maps(adrs: List[Tuple[Any, ...]]) -> None:
    """Updates SecondBrain/Maps/Decisions.md and SecondBrain/Home.md with O20 links while preserving other repos."""
    decisions_map = VAULT_ROOT / "Maps" / "Decisions.md"
    section_header = "## O20 — Insilos Enterprise Odoo 20 (`SOP-DGM-01..11` & Bi-Temporal ADRs)"
    o20_lines = [
        section_header,
        "",
        "- **Master Architecture MOC**: [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|00 — O20 Master Architecture MOC]]",
        "- **Full Bi-Temporal ADR Ledger**: [[20-Projects/Active/O20-Insilos-ERP/03-BiTemporal-ADRs-and-Session-Links|03 — O20 Bi-Temporal ADRs & Session Links]]",
        "",
    ]
    for adr_id, title, status, _rat, valid_from, _vt, sha256 in adrs:
        o20_lines.append(
            f"- **[[20-Projects/Active/O20-Insilos-ERP/03-BiTemporal-ADRs-and-Session-Links#{adr_id}|{adr_id}]]** "
            f"(`{status}` • `{valid_from[:10]}` • `{sha256[:12]}`): {title}"
        )
    o20_block = "\n".join(o20_lines) + "\n"

    existing = decisions_map.read_text(encoding="utf-8") if decisions_map.exists() else "# Decisions\n\nCác quyết định kiến trúc có chi phí đảo ngược.\n"
    if "## O20" in existing:
        import re as _re
        updated = _re.sub(r"## O20[^\n]*\n(?:(?!## ).*\n)*", o20_block + "\n", existing)
    else:
        updated = existing.rstrip() + "\n\n" + o20_block
    decisions_map.write_text(updated, encoding="utf-8")

    home_md = VAULT_ROOT / "Home.md"
    if home_md.exists():
        home_text = home_md.read_text(encoding="utf-8")
        o20_link = "- [[20-Projects/Active/O20-Insilos-ERP/00-O20-Master-Architecture-MOC|O20-Insilos-ERP (Odoo 20 & SOP-DGM-01..11)]]"
        if "O20-Insilos-ERP" not in home_text:
            if "## Active Projects\n\n" in home_text:
                home_text = home_text.replace(
                    "## Active Projects\n\n",
                    f"## Active Projects\n\n{o20_link}\n",
                    1,
                )
            else:
                home_text = home_text.rstrip() + f"\n{o20_link}\n"
            home_md.write_text(home_text, encoding="utf-8")



def main() -> int:
    print("=== [1/5] Verifying & Linking Core Knowledge Compiler Skills ===")
    linked_skills = ensure_skill_symlinks()
    print(f"  [✓] Linked {len(linked_skills)} skills in ~/.gemini/config/skills & /home/zen/O20/.agents/skills: {', '.join(linked_skills)}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    compiler_db = KnowledgeCompilerDB(db_path=DB_PATH)
    compiler_db.conn.execute("PRAGMA busy_timeout=60000;")
    compiler_db.conn.execute("PRAGMA synchronous=NORMAL;")

    # Install O(1) in-memory lookup cache on compiler_db._upsert_node for repo='O20'
    node_cache = {
        (nt, nm, rp, fp or ""): nid
        for nid, nt, nm, rp, fp in compiler_db.conn.execute(
            "SELECT id, node_type, name, repo, COALESCE(file_path,'') FROM nodes WHERE repo='O20'"
        ).fetchall()
    }
    _orig_insert_node = compiler_db._insert_node

    def _fast_upsert_node(node_type, name, repo, file_path, lineno=None, end_lineno=None, sha256=None):
        key = (node_type, name, repo, file_path or "")
        cached_id = node_cache.get(key)
        if cached_id is not None:
            if sha256 and node_type == "FILE":
                compiler_db.conn.execute(
                    "UPDATE nodes SET sha256=?, end_lineno=? WHERE id=?",
                    (sha256, end_lineno, cached_id),
                )
            return cached_id
        nid = _orig_insert_node(node_type, name, repo, file_path, lineno, end_lineno, sha256)
        node_cache[key] = nid
        return nid

    compiler_db._upsert_node = _fast_upsert_node  # type: ignore[method-assign]

    print("\n=== [2/5] Running AST & Call-Graph Delta Compilation (`understand-ast` + `graphify-sql`) ===")
    import ast as _ast

    existing_shas = {
        row[0]: row[1]
        for row in compiler_db.conn.execute(
            "SELECT file_path, sha256 FROM nodes WHERE node_type='FILE' AND repo='O20'"
        ).fetchall()
    }
    total_scanned = 0
    recompiled = 0
    skipped_unchanged = 0
    recompiled_files = []

    with compiler_db.conn:
        for subdir in O20_COMPILE_SUBDIRS:
            target_dir = O20_ROOT / subdir
            if not target_dir.is_dir():
                continue
            for pf in sorted(target_dir.rglob("*.py")):
                if not pf.is_file():
                    continue
                total_scanned += 1
                resolved_path = str(pf.resolve())
                current_sha = compiler_db._sha256_file(pf)
                if resolved_path in existing_shas and existing_shas[resolved_path] == current_sha:
                    skipped_unchanged += 1
                    continue
                try:
                    source = pf.read_text(errors="replace")
                    tree = _ast.parse(source, filename=resolved_path)
                except SyntaxError:
                    continue
                file_id = compiler_db._upsert_node(
                    "FILE",
                    pf.name,
                    "O20",
                    resolved_path,
                    lineno=1,
                    end_lineno=source.count("\n") + 1,
                    sha256=current_sha,
                )
                func_names = []
                import_names = set()
                call_edges = []
                seen_calls = set()
                for node in _ast.walk(tree):
                    if isinstance(node, _ast.Import):
                        for alias in node.names:
                            import_names.add(alias.name)
                    elif isinstance(node, _ast.ImportFrom):
                        import_names.add(node.module or "")
                    elif isinstance(node, _ast.ClassDef):
                        cid = compiler_db._upsert_node(
                            "CLASS",
                            node.name,
                            "O20",
                            resolved_path,
                            lineno=node.lineno,
                            end_lineno=getattr(node, "end_lineno", None),
                        )
                        compiler_db._insert_edge(file_id, cid, "CONTAINS", "EXTRACTED")
                    elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                        fid = compiler_db._upsert_node(
                            "FUNCTION",
                            node.name,
                            "O20",
                            resolved_path,
                            lineno=node.lineno,
                            end_lineno=getattr(node, "end_lineno", None),
                        )
                        func_names.append(node.name)
                        compiler_db._insert_edge(file_id, fid, "CONTAINS", "EXTRACTED")
                    elif isinstance(node, _ast.Call):
                        callee = (
                            node.func.id
                            if isinstance(node.func, _ast.Name)
                            else (node.func.attr if isinstance(node.func, _ast.Attribute) else "")
                        )
                        if callee and callee not in seen_calls:
                            seen_calls.add(callee)
                            call_edges.append(("__file__", callee))
                for imp in import_names:
                    imp_id = compiler_db._upsert_node("MODULE", imp, "O20", None)
                    compiler_db._insert_edge(file_id, imp_id, "IMPORTS", "EXTRACTED", 1.0)
                for _, callee in call_edges:
                    callee_id = compiler_db._upsert_node("FUNCTION", callee, "O20", None)
                    compiler_db._insert_edge(file_id, callee_id, "CALLS", "EXTRACTED", 1.0)
                now_ts = compiler_db._now()
                compiler_db.conn.execute(
                    "INSERT INTO logic_trees(tree_type, root_id, payload_json, created_at) VALUES (?,?,?,?)",
                    ("CONTROL_FLOW", file_id, json.dumps({"type": "CONTROL_FLOW", "file": resolved_path, "functions": func_names}), now_ts),
                )
                compiler_db.conn.execute(
                    "INSERT INTO logic_trees(tree_type, root_id, payload_json, created_at) VALUES (?,?,?,?)",
                    ("CALL_GRAPH", file_id, json.dumps({"type": "CALL_GRAPH", "file": resolved_path, "calls": call_edges[:100]}), now_ts),
                )
                recompiled += 1
                recompiled_files.append(resolved_path)

    delta_res = {
        "scanned": total_scanned,
        "recompiled": recompiled,
        "skipped_unchanged": skipped_unchanged,
        "recompiled_files": recompiled_files,
    }
    evaluator = LocalJEVEvaluator(
        dedup_cache_path=HOME / ".hermes" / ".jev_dedup_cache.json",
        ledger_path=HOME / ".hermes" / "action_ledger.jsonl",
    )
    jev_res = evaluator.evaluate(
        prompt="Compile O20 sovereign architecture, ORM models, controllers, and SOP-DGM-01..11 into SQLite WAL + FTS5 and Obsidian.",
        files=[str(O20_ROOT / "addons/insilos_al2c/models/dgm_okr_appraisal_project_pdca.py")],
    )
    jev_eval_info = {
        "engine": jev_res.engine,
        "verdict": jev_res.verdict,
        "complexity": jev_res.complexity,
    }
    print(
        f"  [✓] Delta Compilation (`repo='O20'`): Scanned={delta_res['scanned']} | "
        f"Recompiled={delta_res['recompiled']} | Skipped={delta_res['skipped_unchanged']} | "
        f"JEV={jev_res.engine} (C={jev_res.complexity})"
    )

    print("\n=== [3/5] Recording 11 Canonical Bi-Temporal ADRs (`decision-ledger`) ===")
    for adr in CANONICAL_O20_ADRS:
        compiler_db.record_decision(
            adr_id=adr["adr_id"],
            title=adr["title"],
            rationale=adr["rationale"],
            valid_from=adr["valid_from"],
            valid_to=None,
            repo="O20",
        )
    print(f"  [✓] Recorded {len(CANONICAL_O20_ADRS)} ACTIVE Bi-Temporal ADRs (`ADR-20261016-001` .. `ADR-20261017-011`)")

    print("\n=== [4/5] Emitting Bidirectional Local Obsidian Notes (`obsidian-session-compiler`) ===")
    stats = query_o20_graph_stats(compiler_db)
    note_links = generate_obsidian_notes(compiler_db, stats, delta_res, jev_eval_info)
    update_vault_maps(stats["active_adrs"])

    # Clean previous session links for this session_id to remain idempotent
    with compiler_db.conn:
        compiler_db.conn.execute(
            "DELETE FROM session_links WHERE session_id = ?",
            (SESSION_ID,),
        )
    for rel_note_path, primary_adr in note_links:
        compiler_db.link_session_to_vault(
            session_id=SESSION_ID,
            vault_note_path=rel_note_path,
            adr_id=primary_adr,
        )
    for adr in CANONICAL_O20_ADRS:
        compiler_db.link_session_to_vault(
            session_id=SESSION_ID,
            vault_note_path="20-Projects/Active/O20-Insilos-ERP/03-BiTemporal-ADRs-and-Session-Links.md",
            adr_id=adr["adr_id"],
        )
    print(f"  [✓] Generated 5 Obsidian notes in {O20_VAULT_DIR} and linked Session `{SESSION_ID}`")

    print("\n=== [5/5] Synchronizing Local Obsidian Vault (`obsidian-second-brain-sync` + `obsidian-hermes-research-export`) ===")
    for bin_name in ("/home/zen/.local/bin/obsidian-second-brain-sync", "/home/zen/.local/bin/obsidian-hermes-research-export"):
        if os.path.isfile(bin_name):
            proc = subprocess.run([bin_name], capture_output=True, text=True, check=True)
            print(f"  [✓] {os.path.basename(bin_name)}: {proc.stdout.strip()}")

    compiler_db.close()
    print("\n=== CORE KNOWLEDGE COMPILER -> LOCAL OBSIDIAN COMPLETED SUCCESSFULLY (EXIT 0) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
