# -*- coding: utf-8 -*-
"""
Automated Test Suite for Insilos Continuous Multi-Repository Governance Scanner.
Verifies:
  1. Topology-aware repository resolution (nested repos and submodules)
  2. Git telemetry & resilient traversal error handling (zencode-ent/router)
  3. Documentation drift calculation exceeding 30-day threshold (mobo_vert_shell, vertical)
  4. Dependency risk parser for pubspec.yaml, requirements.txt, and package.json
  5. Dual backlog sizing (Replacement Sizing vs Active Sprint Workload)
  6. Backlog v2 candidate generation with DoD and machine-readable metadata comments
  7. Full scanner execution and JSON/Markdown output schema validation
  8. CLI runner execution and --check gate behavior
"""

import os
import sys
import json
import re
import tempfile
import subprocess
import unittest
from pathlib import Path

# Add O20 root to sys.path
O20_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(O20_DIR))

from tools.multi_repo_scanner import (
    MultiRepoScanner,
    RepoTopologyResolver,
    GitTelemetryInspector,
    DocDriftAuditor,
    DependencyRiskAnalyzer,
    DualSizingEstimator,
    BacklogSynthesizer,
    DEFAULT_REPOSITORIES,
)


class TestMultiRepoScanner(unittest.TestCase):
    """Unit and integration test cases for MultiRepoScanner engine."""

    @classmethod
    def setUpClass(cls):
        cls.repos = DEFAULT_REPOSITORIES
        cls.o20_path = "/home/zen/O20"
        cls.vr_path = "/home/zen/VerticalRisk"
        cls.mobile_path = "/home/zen/insilos_mobile"
        cls.zen_path = "/home/zen/zencode-ent"

    def test_01_topology_resolver_and_nested_repos(self):
        """Verify topology resolver detects nested O20/enterprise repo and zencode-ent submodules."""
        # 1. O20 Nested Enterprise Repo
        top_o20 = RepoTopologyResolver.resolve_topology(self.o20_path)
        self.assertEqual(top_o20["name"], "O20")
        nested_names = [n["name"] for n in top_o20["nested_repositories"]]
        self.assertIn("enterprise", nested_names)

        # 2. Zencode-ent Submodules
        top_zen = RepoTopologyResolver.resolve_topology(self.zen_path)
        self.assertEqual(top_zen["name"], "zencode-ent")
        submodule_names = [s["name"] for s in top_zen["submodules"]]
        for expected_sm in ["router", "hub", "vertical", "zencode", "zencode-core", "AI"]:
            self.assertIn(expected_sm, submodule_names)

        # 3. Sovereign Module Discovery
        mods_o20 = RepoTopologyResolver.discover_modules(self.o20_path, scope="sovereign")
        mods_vr = RepoTopologyResolver.discover_modules(self.vr_path, scope="sovereign")
        mods_mob = RepoTopologyResolver.discover_modules(self.mobile_path, scope="sovereign")
        mods_zen = RepoTopologyResolver.discover_modules(self.zen_path, scope="sovereign")

        total_sovereign = len(mods_o20) + len(mods_vr) + len(mods_mob) + len(mods_zen)
        self.assertEqual(len(mods_o20), 21, "Expected 21 sovereign modules in O20 (3 addons + 18 enterprise)")
        self.assertEqual(len(mods_vr), 67, "Expected 67 extensions in VerticalRisk")
        self.assertEqual(len(mods_mob), 27, "Expected 27 packages in insilos_mobile")
        self.assertEqual(len(mods_zen), 6, "Expected 6 submodules in zencode-ent")
        self.assertEqual(total_sovereign, 121, "Expected exactly 121 sovereign modules across 4 repositories")

    def test_02_git_telemetry_resilience_and_traversal_errors(self):
        """Verify git telemetry extraction and graceful handling of broken git commit traversal."""
        # Clean repository telemetry
        git_o20 = GitTelemetryInspector.get_git_info(self.o20_path)
        self.assertTrue(git_o20["is_git"])
        self.assertEqual(git_o20["branch"], "insilos-genesis-fork")
        self.assertTrue(git_o20["head"])
        self.assertGreater(git_o20["velocity_30d"], 0)
        self.assertIsNone(git_o20["git_health_warning"])

        # Defective submodule traversal: zencode-ent/router
        router_path = os.path.join(self.zen_path, "router")
        git_router = GitTelemetryInspector.get_git_info(router_path)
        self.assertTrue(git_router["is_git"])
        self.assertIsNotNone(git_router["git_health_warning"])
        self.assertIn("GIT_OBJECT_TRAVERSAL_ERROR", git_router["git_health_warning"])
        # Even with defective parent traversal, fallback sampling must succeed
        self.assertGreater(git_router["velocity_30d"], 0)

    def test_03_doc_drift_calculation_exceeding_30d_threshold(self):
        """Verify documentation drift calculation: delta = (T_code - T_doc) / 86400 > 30 days."""
        # 1. mobo_vert_shell in insilos_mobile (exceeds 30d threshold)
        mob_meta = {
            "name": "mobo_vert_shell",
            "rel_path": "mobo_vert_shell",
            "category": "flutter_package",
            "abs_path": os.path.join(self.mobile_path, "mobo_vert_shell"),
            "git_context_repo": self.mobile_path,
            "git_rel_path": "mobo_vert_shell",
        }
        audit_shell = DocDriftAuditor.audit_module(mob_meta, threshold_days=30.0)
        self.assertTrue(audit_shell["has_localized_doc"])
        self.assertEqual(audit_shell["status"], "DRIFT_STALE")
        self.assertTrue(audit_shell["is_drift_stale"])
        self.assertIsNotNone(audit_shell["drift_days"])
        self.assertGreater(audit_shell["drift_days"], 30.0, "mobo_vert_shell drift must exceed 30 days")

        # 2. vertical submodule in zencode-ent (exceeds 30d threshold)
        zen_vert_meta = {
            "name": "vertical",
            "rel_path": "vertical",
            "category": "swarm_submodule",
            "abs_path": os.path.join(self.zen_path, "vertical"),
            "git_context_repo": os.path.join(self.zen_path, "vertical"),
            "git_rel_path": ".",
        }
        audit_vert = DocDriftAuditor.audit_module(zen_vert_meta, threshold_days=30.0)
        self.assertTrue(audit_vert["has_localized_doc"])
        self.assertEqual(audit_vert["status"], "DRIFT_STALE")
        self.assertTrue(audit_vert["is_drift_stale"])
        self.assertIsNotNone(audit_vert["drift_days"])
        self.assertGreater(audit_vert["drift_days"], 30.0, "vertical submodule drift must exceed 30 days")

        # 3. Missing localized documentation: addons/insilos_al2c in O20
        al2c_meta = {
            "name": "insilos_al2c",
            "rel_path": "addons/insilos_al2c",
            "category": "odoo_addon",
            "abs_path": os.path.join(self.o20_path, "addons/insilos_al2c"),
            "git_context_repo": self.o20_path,
            "git_rel_path": "addons/insilos_al2c",
        }
        audit_al2c = DocDriftAuditor.audit_module(al2c_meta, threshold_days=30.0)
        self.assertFalse(audit_al2c["has_localized_doc"])
        self.assertEqual(audit_al2c["status"], "MISSING_DOC")
        self.assertTrue(audit_al2c["is_missing_doc"])

    def test_04_dependency_risk_analyzer(self):
        """Verify dependency risk parsing for Flutter : any, Python upper bounds, and npm ranges."""
        # 1. insilos_mobile: Unpinned Flutter ': any'
        mobile_risks = DependencyRiskAnalyzer.scan_repository(self.mobile_path)
        flutter_any_risks = [r for r in mobile_risks if r["risk_type"] == "UNPINNED_FLUTTER_ANY"]
        self.assertGreaterEqual(len(flutter_any_risks), 16, "Expected at least 16 ': any' dependencies in Flutter")
        offending_deps = [r["dependency"] for r in flutter_any_risks]
        self.assertIn("flutter_svg", offending_deps)
        self.assertIn("http", offending_deps)
        self.assertIn("intl", offending_deps)

        # 2. zencode-ent: Unpinned Python Upper Bounds
        zen_risks = DependencyRiskAnalyzer.scan_repository(self.zen_path)
        upper_bound_risks = [r for r in zen_risks if r["risk_type"] == "UNPINNED_UPPER_BOUND"]
        self.assertGreaterEqual(len(upper_bound_risks), 5, "Expected unpinned upper bounds in zencode-ent")
        zen_deps = [r["dependency"] for r in upper_bound_risks]
        self.assertIn("modal", zen_deps)
        self.assertIn("numpy", zen_deps)

        # 3. O20: Unpinned Noble patch in requirements.txt
        o20_risks = DependencyRiskAnalyzer.scan_repository(self.o20_path)
        lxml_risk = [r for r in o20_risks if r["dependency"] == "lxml-html-clean"]
        self.assertTrue(len(lxml_risk) >= 1, "Expected lxml-html-clean unpinned risk in O20 requirements.txt")

    def test_05_dual_backlog_sizing_model(self):
        """Verify dual sizing calculations: Replacement Sizing vs Active Sprint Workload."""
        top_o20 = RepoTopologyResolver.resolve_topology(self.o20_path)
        mods_o20 = RepoTopologyResolver.discover_modules(self.o20_path, scope="sovereign")
        git_o20 = GitTelemetryInspector.get_git_info(self.o20_path)

        sizing = DualSizingEstimator.compute_sizing(
            repo_path=self.o20_path,
            repo_name="O20",
            churn_30d=git_o20["churn_30d"],
            dirty_count=git_o20["dirty_files_count"],
            drift_mods_count=20,
            topology=top_o20,
            modules=mods_o20,
            scope="sovereign"
        )

        self.assertGreater(sizing["loc_code"], 0)
        self.assertEqual(sizing["complexity_rating"], 1.5)
        # S_replace = round((LOC / 180) * 1.5, 1)
        expected_replace = round((sizing["loc_code"] / 180.0) * 1.5, 1)
        self.assertEqual(sizing["replacement_man_days"], expected_replace)
        self.assertGreater(sizing["active_sprint_workload_days"], 0)

    def test_06_backlog_v2_generation_and_metadata_contract(self):
        """Verify Backlog v2 item generation, DoD completeness, and machine-readable metadata format."""
        top_zen = RepoTopologyResolver.resolve_topology(self.zen_path)
        git_zen = GitTelemetryInspector.get_git_info(self.zen_path)
        mods_zen = RepoTopologyResolver.discover_modules(self.zen_path, scope="sovereign")
        doc_zen = [DocDriftAuditor.audit_module(m) for m in mods_zen]
        dep_zen = DependencyRiskAnalyzer.scan_repository(self.zen_path)

        items = BacklogSynthesizer.generate_backlog_items(
            repo_name="zencode-ent",
            git_info=git_zen,
            topology=top_zen,
            doc_drift_results=doc_zen,
            dependency_risks=dep_zen
        )

        item_codes = [i["item_code"] for i in items]
        # P0 Traversal blocker
        self.assertIn("GIT01-ROUTER", item_codes, "Expected P0 GIT01-ROUTER blocker item")
        # P1 Documentation drift
        self.assertIn("DOC01-VERTICAL", item_codes, "Expected P1 DOC01-VERTICAL drift item")

        # Verify Backlog v2 Regex Format on all items
        pattern = re.compile(
            r'^- \[ \] \[([A-Z0-9_\-]+)\]\[(P[0-3])\]\[([a-z]+)\] .+ — DoD: .+ <!-- meta: repo=[^ ]+ path=[^ ]+ verify="[^"]+" risk=[A-Z0-9]+ -->$'
        )
        for item in items:
            line = item["formatted_line"]
            match = pattern.match(line)
            self.assertIsNotNone(match, f"Item did not match Backlog v2 syntax: {line}")
            self.assertEqual(match.group(1), item["item_code"])
            self.assertEqual(match.group(2), item["priority"])
            self.assertEqual(match.group(3), item["track"])

    def test_07_full_scanner_execution_and_json_schema(self):
        """Verify full multi-repository scan execution, JSON schema validity, and Markdown report structure."""
        scanner = MultiRepoScanner(repos=self.repos, drift_threshold_days=30.0, scope="sovereign")
        results = scanner.scan_all()

        # Schema checks
        self.assertIn("audit_metadata", results)
        self.assertIn("summary", results)
        self.assertIn("repositories", results)
        self.assertIn("candidate_backlog", results)

        summary = results["summary"]
        self.assertEqual(summary["total_repositories"], 4)
        self.assertEqual(summary["total_modules"], 121)
        self.assertGreater(summary["total_loc_code"], 1000000)
        self.assertGreater(summary["total_velocity_30d"], 100)
        self.assertEqual(summary["drift_stale_modules_count"], 2)  # mobo_vert_shell & vertical
        self.assertGreaterEqual(summary["missing_doc_modules_count"], 90)
        self.assertGreaterEqual(summary["dependency_risks_count"], 20)
        self.assertGreater(summary["candidate_backlog_items_count"], 50)

        # Markdown report validation
        md_report = scanner.generate_markdown_report(results)
        self.assertIn("# Insilos Multi-Repository Continuous Governance Report", md_report)
        self.assertIn("Executive Telemetry Overview", md_report)
        self.assertIn("Documentation Drift & Staleness Findings (>30 Days Threshold)", md_report)
        self.assertIn("Dependency Risk Analysis Matrix", md_report)
        self.assertIn("Prioritized Candidate Backlog (Backlog v2 Format)", md_report)
        self.assertIn("mobo_vert_shell", md_report)
        self.assertIn("vertical", md_report)

    def test_08_cli_runner_and_check_gate_behavior(self):
        """Verify CLI runner outputs JSON/Markdown artifacts and fails on --check when P0 blockers exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = os.path.join(tmpdir, "test_out.json")
            md_out = os.path.join(tmpdir, "test_out.md")

            # 1. Normal run with artifact export
            res_normal = subprocess.run(
                ["python3", "tools/run_multi_repo_scan.py", "--json", json_out, "--markdown", md_out],
                cwd=str(O20_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45
            )
            self.assertEqual(res_normal.returncode, 0, f"Scanner CLI failed: {res_normal.stderr}")
            self.assertTrue(os.path.exists(json_out))
            self.assertTrue(os.path.exists(md_out))

            # Verify exported JSON is valid
            with open(json_out, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["summary"]["total_repositories"], 4)

            # 2. Check gate run: must exit with code 1 due to P0 GIT01-ROUTER blocker
            res_check = subprocess.run(
                ["python3", "tools/run_multi_repo_scan.py", "--check", "--json", json_out, "--markdown", md_out],
                cwd=str(O20_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45
            )
            self.assertEqual(res_check.returncode, 1, "Expected --check to exit with code 1 on P0 blocker")
            self.assertIn("CHECK FAILED", res_check.stdout)
            self.assertIn("GIT01-ROUTER", res_check.stdout)


if __name__ == "__main__":
    unittest.main()
