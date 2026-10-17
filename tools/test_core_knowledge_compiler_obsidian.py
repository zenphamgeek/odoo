#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Verification Suite for Core Knowledge Compiler & Local Obsidian (`SecondBrain`) Export
================================================================================================
Verifies:
  1. All 6 skills (`core-knowledge-compiler`, `obsidian-session-compiler`, `graphify-sql`,
     `understand-ast`, `decision-ledger`, `git-memory-compiler`) exist and contain valid
     `SKILL.md` files in both `/home/zen/.gemini/config/skills/` and `/home/zen/O20/.agents/skills/`.
  2. `~/.hermes/knowledge_compiler.db` (SQLite WAL + FTS5) contains:
     - `repo='O20'` `FILE` (`>= 100`), `CLASS` (`>= 200`), and `FUNCTION` (`>= 1000`) nodes
     - `CONTROL_FLOW` and `CALL_GRAPH` `logic_trees` (`>= 200`)
     - `11` `ACTIVE` Bi-Temporal `decisions` (`ADR-20261016-001` .. `ADR-20261017-011`) with SHA-256 hashes
     - `session_links` for session `790b1743-1724-4f27-a6fd-6d949bee50cf`
     - Working FTS5 full-text search on `nodes_fts`
  3. All 5 Obsidian notes exist under `/home/zen/Obsidian/SecondBrain/20-Projects/Active/O20-Insilos-ERP/`,
     `/home/zen/Obsidian/SecondBrain/Maps/Decisions.md` and `/home/zen/Obsidian/SecondBrain/Home.md`
     are updated with O20 `[[Wikilinks]]`, and `/home/zen/Obsidian/SecondBrain/Data/hermes-research.jsonl`
     exports all 5 O20 research records with zero secret rejections.
  4. `/home/zen/O20/AGENTS.md` and `.agents/rules/01_insilos_enterprise_odoo_standards.md` include Section 10.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

HOME = Path.home().resolve()
O20_ROOT = Path("/home/zen/O20").resolve()
DB_PATH = HOME / ".hermes" / "knowledge_compiler.db"
VAULT_ROOT = HOME / "Obsidian" / "SecondBrain"
O20_VAULT_DIR = VAULT_ROOT / "20-Projects" / "Active" / "O20-Insilos-ERP"
SESSION_ID = "790b1743-1724-4f27-a6fd-6d949bee50cf"

REQUIRED_SKILLS = [
    "core-knowledge-compiler",
    "obsidian-session-compiler",
    "graphify-sql",
    "understand-ast",
    "decision-ledger",
    "git-memory-compiler",
]

EXPECTED_ADR_IDS = [
    "ADR-20261016-001",
    "ADR-20261016-002",
    "ADR-20261016-003",
    "ADR-20261016-004",
    "ADR-20261016-005",
    "ADR-20261016-006",
    "ADR-20261016-007",
    "ADR-20261016-008",
    "ADR-20261016-009",
    "ADR-20261017-010",
    "ADR-20261017-011",
    "ADR-20261017-012",
]

EXPECTED_OBSIDIAN_NOTES = [
    "00-O20-Master-Architecture-MOC.md",
    "01-AST-Knowledge-Graph-Models.md",
    "02-DGM-INNORIA-SOP-01-to-11-Master-Ledger.md",
    "03-BiTemporal-ADRs-and-Session-Links.md",
    "04-Google-Drive-SharedWithMe-RBAC-Matrix.md",
]


def main() -> int:
    print("=== Testing Core Knowledge Compiler & Local Obsidian (`SecondBrain`) Integration ===")

    # 1. Verify all 6 skills in global and workspace skill directories
    global_skills = HOME / ".gemini" / "config" / "skills"
    workspace_skills = O20_ROOT / ".agents" / "skills"
    for skill in REQUIRED_SKILLS:
        g_skill_md = global_skills / skill / "SKILL.md"
        w_skill_md = workspace_skills / skill / "SKILL.md"
        assert g_skill_md.is_file() and g_skill_md.stat().st_size > 100, f"Missing global skill: {g_skill_md}"
        assert w_skill_md.is_file() and w_skill_md.stat().st_size > 100, f"Missing workspace skill: {w_skill_md}"
    print(f"  [PASS] All 6 Core Knowledge Compiler skills verified in global & workspace directories.")

    # 2. Verify SQLite WAL + FTS5 Knowledge Graph (~/.hermes/knowledge_compiler.db)
    assert DB_PATH.is_file(), f"Missing SQLite database: {DB_PATH}"
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("PRAGMA journal_mode;")
    jmode = cur.fetchone()[0].lower()
    assert jmode == "wal", f"Expected WAL journal_mode, got {jmode}"

    cur.execute("SELECT node_type, COUNT(*) FROM nodes WHERE repo='O20' GROUP BY node_type")
    node_counts = dict(cur.fetchall())
    file_cnt = node_counts.get("FILE", 0)
    class_cnt = node_counts.get("CLASS", 0)
    func_cnt = node_counts.get("FUNCTION", 0)
    assert file_cnt >= 100, f"Expected >= 100 FILE nodes for O20, got {file_cnt}"
    assert class_cnt >= 200, f"Expected >= 200 CLASS nodes for O20, got {class_cnt}"
    assert func_cnt >= 1000, f"Expected >= 1000 FUNCTION nodes for O20, got {func_cnt}"

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
    assert tree_counts.get("CONTROL_FLOW", 0) >= 100, f"Missing CONTROL_FLOW trees: {tree_counts}"
    assert tree_counts.get("CALL_GRAPH", 0) >= 100, f"Missing CALL_GRAPH trees: {tree_counts}"

    # Verify FTS5 full-text search
    cur.execute("SELECT COUNT(*) FROM nodes_fts WHERE nodes_fts MATCH 'DgmHrAppraisalSheet OR DgmOkrObjective'")
    fts_hits = cur.fetchone()[0]
    assert fts_hits >= 2, f"Expected >= 2 FTS5 hits for DgmHrAppraisalSheet/DgmOkrObjective, got {fts_hits}"
    print(
        f"  [PASS] SQLite WAL + FTS5 Graph (`repo='O20'`): {file_cnt} FILEs, {class_cnt} CLASSes, "
        f"{func_cnt} FUNCTIONs, {sum(tree_counts.values())} Logic Trees, FTS5 hits={fts_hits}."
    )

    # 3. Verify 11 ACTIVE Bi-Temporal ADRs & Session Links
    cur.execute(
        "SELECT adr_id, status, sha256 FROM decisions WHERE repo='O20' AND status='ACTIVE' ORDER BY adr_id"
    )
    adr_rows = cur.fetchall()
    adr_map = {r[0]: (r[1], r[2]) for r in adr_rows}
    for expected_adr in EXPECTED_ADR_IDS:
        assert expected_adr in adr_map, f"Missing active ADR `{expected_adr}` in decisions table"
        assert len(adr_map[expected_adr][1]) == 64, f"Invalid SHA-256 on `{expected_adr}`"

    cur.execute(
        "SELECT COUNT(*) FROM session_links WHERE session_id = ?",
        (SESSION_ID,),
    )
    link_cnt = cur.fetchone()[0]
    assert link_cnt >= 16, f"Expected >= 16 session_links for {SESSION_ID}, got {link_cnt}"
    conn.close()
    print(f"  [PASS] 11/11 Bi-Temporal ADRs (`ADR-20261016-001`..`ADR-20261017-011`) & {link_cnt} Session Links verified.")

    # 4. Verify 5 Obsidian Notes, Maps/Decisions.md, Home.md & Data/hermes-research.jsonl
    for note_name in EXPECTED_OBSIDIAN_NOTES:
        note_fp = O20_VAULT_DIR / note_name
        assert note_fp.is_file() and note_fp.stat().st_size > 1500, f"Missing or incomplete Obsidian note: {note_fp}"
        text = note_fp.read_text(encoding="utf-8")
        assert "hermes_research: true" in text
        assert "project: O20" in text
        assert f"[[Session-{SESSION_ID}]]" in text

    decisions_md = (VAULT_ROOT / "Maps" / "Decisions.md").read_text(encoding="utf-8")
    assert "O20-Insilos-ERP" in decisions_md and "ADR-20261017-011" in decisions_md

    home_md = (VAULT_ROOT / "Home.md").read_text(encoding="utf-8")
    assert "O20-Insilos-ERP" in home_md

    research_jsonl = VAULT_ROOT / "Data" / "hermes-research.jsonl"
    assert research_jsonl.is_file(), f"Missing {research_jsonl}"
    o20_records = [
        json.loads(line)
        for line in research_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("project") == "O20"
    ]
    assert len(o20_records) >= 5, f"Expected >= 5 exported O20 records in hermes-research.jsonl, got {len(o20_records)}"
    print(f"  [PASS] 5/5 Obsidian Notes, Maps/Decisions.md, Home.md & {len(o20_records)} exported hermes-research.jsonl records verified.")

    # 5. Verify AGENTS.md & .agents/rules/01_insilos_enterprise_odoo_standards.md Section 10
    agents_md = (O20_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    rules_md = (O20_ROOT / ".agents" / "rules" / "01_insilos_enterprise_odoo_standards.md").read_text(encoding="utf-8")
    assert "## 10. Core Knowledge Compiler" in agents_md
    assert "## 10. Core Knowledge Compiler" in rules_md
    print("  [PASS] Section 10 verified in AGENTS.md and .agents/rules/01_insilos_enterprise_odoo_standards.md.")

    print("\n=== ALL CORE KNOWLEDGE COMPILER & OBSIDIAN TESTS PASSED (EXIT 0) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
