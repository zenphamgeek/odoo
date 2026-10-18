#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Repository Governance & Continuous Scanner Engine.
Inspects sovereign enterprise repositories:
  - O20 (/home/zen/O20): Core ERP Platform & nested enterprise repository
  - VerticalRisk (/home/zen/VerticalRisk): GRC Suite & Extensions
  - insilos_mobile (/home/zen/insilos_mobile): Flutter Cross-Platform Operations
  - zencode-ent (/home/zen/zencode-ent): Autonomous Swarm Router & Submodules

Evaluates:
  1. Topology-aware repository resolution (nested repos & submodules)
  2. Git telemetry & 30-day commit velocity (resilient to git graph defects)
  3. Documentation staleness & drift (delta = (T_code - T_doc) / 86400 > 30d)
  4. Dependency risk analysis (pubspec.yaml, requirements.txt, pyproject.toml, package.json)
  5. Dual backlog sizing: Replacement value (LOC / 180 * complexity) vs Sprint churn workload
  6. Automated candidate backlog generation in Backlog v2 format with DoD and metadata
"""

import os
import sys
import json
import html
import hashlib
import re
import argparse
import logging
import subprocess
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("multi_repo_scanner")

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
MAX_METRIC_VALUE = Decimal('1000000.0')


def sanitize_string_field(val: Optional[str], max_len: int = 1024) -> str:
    """Strips terminal ANSI control characters and null bytes and enforces length bounds."""
    if val is None:
        return ""
    cleaned = ANSI_ESCAPE_RE.sub('', str(val))
    cleaned = cleaned.replace('\r', '').replace('\x00', '')
    return cleaned[:max_len].strip()


def validate_and_accumulate_metric(current: Decimal, delta: Any, metric_name: str) -> Decimal:
    """Accumulates floating/decimal values fail-closed against NaN, Inf, and negative values."""
    try:
        parsed = Decimal(str(delta))
    except (InvalidOperation, TypeError, ValueError) as err:
        raise ValueError(f"CRITICAL: Corrupted metric '{metric_name}' value '{delta}': {err}")

    if parsed.is_nan() or parsed.is_infinite():
        raise ValueError(f"CRITICAL: Unbounded IEEE 754 value detected in '{metric_name}': {parsed}")

    if parsed < Decimal('0.0') or parsed > MAX_METRIC_VALUE:
        raise ValueError(f"CRITICAL: Metric '{metric_name}' value {parsed} violates bounds [0.0, {MAX_METRIC_VALUE}]")

    result = current + parsed
    if result > MAX_METRIC_VALUE:
        raise OverflowError(f"CRITICAL: Metric accumulation overflow in '{metric_name}': {result}")
    return result


class ModuleRecordValidator:
    """Production Invariant Validator with Leaf-Level Quarantine."""

    def __init__(self, max_workload: Decimal = Decimal("50000.0")):
        self.max_workload = max_workload

    def validate_and_sanitize_record(self, record: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        required_keys = {"module_name", "category", "loc_code", "workload_days"}
        if not required_keys.issubset(record.keys()):
            return False, {}, "ERR_MISSING_SCHEMA_KEYS"

        name = str(record.get("module_name", ""))
        if not name or len(name) > 128 or any(c in name for c in ["\x00", "\x1b", "<", ">"]):
            return False, {}, "ERR_MALFORMED_IDENTIFIER"

        try:
            loc = int(record["loc_code"])
            workload = Decimal(str(record["workload_days"]))
        except (ValueError, TypeError, InvalidOperation):
            return False, {}, "ERR_INVALID_NUMERIC_TYPE"

        if loc < 0 or loc > 10_000_000:
            return False, {}, "ERR_LOC_OUT_OF_BOUNDS"

        if workload.is_nan() or workload.is_infinite():
            return False, {}, "ERR_WORKLOAD_IEEE754_POISON"

        if workload < Decimal("0.0") or workload > self.max_workload:
            return False, {}, "ERR_WORKLOAD_OUT_OF_BOUNDS"

        sanitized = {
            "module_name": name.strip(),
            "category": str(record.get("category", "generic")),
            "loc_code": loc,
            "workload_days": str(workload),
            "quarantined": False,
        }
        return True, sanitized, "VALID"


class MerkleSumQuarantineEngine:
    """Computes deterministic Merkle-Sum while isolating corrupted records into quarantine."""

    def __init__(self, validator: Optional[ModuleRecordValidator] = None):
        self.validator = validator or ModuleRecordValidator()

    def process_batch(self, raw_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        valid_records: List[Dict[str, Any]] = []
        quarantine_log: List[Dict[str, Any]] = []
        total_workload = Decimal("0.0")
        total_loc = 0

        for idx, rec in enumerate(raw_records):
            is_valid, sanitized, reason = self.validator.validate_and_sanitize_record(rec)
            if is_valid:
                valid_records.append(sanitized)
                total_workload += Decimal(sanitized["workload_days"])
                total_loc += sanitized["loc_code"]
            else:
                quarantine_log.append({
                    "record_index": idx,
                    "raw_payload_snippet": str(rec)[:100],
                    "rejection_reason": reason,
                    "quarantine_token": hashlib.sha256(f"{idx}:{reason}".encode()).hexdigest()[:16],
                })

        leaf_hashes = [
            hashlib.sha256(f"{r['module_name']}:{r['workload_days']}".encode()).hexdigest()
            for r in valid_records
        ]
        composite_root = hashlib.sha256("".join(leaf_hashes).encode()).hexdigest() if leaf_hashes else "EMPTY_ROOT"

        return {
            "valid_records_count": len(valid_records),
            "quarantined_records_count": len(quarantine_log),
            "total_loc": total_loc,
            "total_workload_days": str(total_workload),
            "merkle_sum_root": composite_root,
            "quarantine_log": quarantine_log,
            "quarantine_rate": len(quarantine_log) / len(raw_records) if raw_records else 0.0,
        }


DEFAULT_REPOSITORIES = [
    "/home/zen/O20",
    "/home/zen/VerticalRisk",
    "/home/zen/insilos_mobile",
    "/home/zen/zencode-ent",
]

DEFAULT_DRIFT_THRESHOLD_DAYS = 30.0

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".dart_tool",
    ".idea",
    ".vscode",
    ".gradle",
    ".cache",
    ".turbo",
}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".dart", ".xml", ".rs", ".go",
    ".html", ".vue", ".scss", ".css", ".sql", ".sh", ".c", ".cpp", ".h",
    ".java", ".kt", ".json"
}

TEST_PATTERNS = ["test", "tests", "spec", "_test.dart", "test_", "_spec.ts"]
TEXT_DOC_EXTS = {".md", ".rst", ".txt", ".adoc"}


class GitTelemetryInspector:
    """Robust Git telemetry extractor that handles detached HEAD, missing objects, and traversal errors."""

    @staticmethod
    def run_git(repo_path: str, args: List[str], timeout: int = 20) -> Tuple[int, str, str]:
        cmd = ["git", "-C", repo_path] + args
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s: {' '.join(cmd)}"
        except Exception as e:
            return -1, "", str(e)

    @classmethod
    def get_git_info(cls, repo_path: str) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "is_git": False,
            "branch": "unknown",
            "head": "none",
            "head_full": "",
            "author": "unknown",
            "commit_date": None,
            "commit_timestamp": 0,
            "commit_subject": "",
            "dirty_files_count": 0,
            "is_dirty": False,
            "velocity_30d": 0,
            "churn_30d": 0,
            "git_health_warning": None,
        }

        # Check if git repository
        rc, out, _ = cls.run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
        if rc != 0 or out != "true":
            return info
        info["is_git"] = True

        # Branch
        rc, out, _ = cls.run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        if rc == 0 and out:
            info["branch"] = html.escape(sanitize_string_field(out, 256), quote=True)

        # HEAD commit
        rc, out, _ = cls.run_git(repo_path, ["log", "-1", "--format=%H%x1f%an%x1f%ct%x1f%cI%x1f%s"])
        if rc == 0 and out:
            parts = out.split("\x1f")
            if len(parts) >= 5:
                info["head_full"] = parts[0]
                info["head"] = parts[0][:9]
                info["author"] = html.escape(sanitize_string_field(parts[1], 256), quote=True)
                try:
                    info["commit_timestamp"] = int(parts[2])
                except ValueError:
                    info["commit_timestamp"] = 0
                info["commit_date"] = parts[3]
                info["commit_subject"] = html.escape(sanitize_string_field(parts[4], 1024), quote=True)

        # Dirty status
        rc, out, _ = cls.run_git(repo_path, ["status", "--porcelain"])
        if rc == 0:
            lines = [l for l in out.splitlines() if l.strip()]
            info["dirty_files_count"] = len(lines)
            info["is_dirty"] = len(lines) > 0

        # Velocity: 30-day commit count (handling commit graph traversal defects)
        rc, out, err = cls.run_git(repo_path, ["rev-list", "--count", "--since=30 days ago", "HEAD"])
        if rc == 0 and out:
            try:
                info["velocity_30d"] = int(out)
            except ValueError:
                info["velocity_30d"] = 0
        else:
            # Traversal defect detected (e.g. zencode-ent/router missing object)
            warning_msg = sanitize_string_field(f"GIT_OBJECT_TRAVERSAL_ERROR: {err or 'Failed to count 30d commits'}", 1024)
            info["git_health_warning"] = warning_msg
            logger.warning("Git traversal error in %s: %s", repo_path, warning_msg)

            # Resilient fallback: sample available commits via git log -n 50
            rc_log, out_log, _ = cls.run_git(repo_path, ["log", "-n", "50", "--format=%ct"])
            if out_log:
                now_ts = int(datetime.now(timezone.utc).timestamp())
                cutoff_ts = now_ts - (30 * 86400)
                sampled_count = 0
                for line in out_log.splitlines():
                    try:
                        ts = int(line.strip())
                        if ts >= cutoff_ts:
                            sampled_count += 1
                    except ValueError:
                        pass
                info["velocity_30d"] = max(sampled_count, 1 if out_log else 0)

        # High-performance 30-day churn calculation via git diff --shortstat
        info["churn_30d"] = cls.get_fast_30d_churn(repo_path)

        return info

    @classmethod
    def get_fast_30d_churn(cls, repo_path: str) -> int:
        """Fast calculation of 30-day churn (insertions + deletions) using git diff --shortstat."""
        # 1. Find commit ~30 days ago
        rc, out, _ = cls.run_git(repo_path, ["rev-list", "-n", "1", "--before=30 days ago", "HEAD"])
        base_commit = out.strip() if rc == 0 and out else None

        if not base_commit:
            # If all commits are newer than 30 days, find oldest root commit
            rc_r, out_r, _ = cls.run_git(repo_path, ["rev-list", "--max-parents=0", "HEAD"])
            if rc_r == 0 and out_r:
                roots = out_r.splitlines()
                base_commit = roots[0] if roots else None

        if base_commit:
            rc_diff, out_diff, _ = cls.run_git(repo_path, ["diff", "--shortstat", base_commit, "HEAD"])
            if rc_diff == 0 and out_diff:
                ins_match = re.search(r'(\d+)\s+insertion', out_diff)
                del_match = re.search(r'(\d+)\s+deletion', out_diff)
                insertions = int(ins_match.group(1)) if ins_match else 0
                deletions = int(del_match.group(1)) if del_match else 0
                return insertions + deletions

        return 0

    @classmethod
    def get_latest_commit_ts(cls, repo_path: str, target_path: str) -> Optional[int]:
        """Returns the unix epoch seconds of the latest commit touching target_path."""
        rc, out, _ = cls.run_git(repo_path, ["log", "-1", "--format=%ct", "--", target_path])
        if rc == 0 and out:
            try:
                return int(out.strip())
            except ValueError:
                return None
        return None

    @classmethod
    def get_scoped_churn(cls, repo_path: str, target_paths: List[str]) -> int:
        """Returns the 30-day churn lines scoped to target paths."""
        if not target_paths:
            return 0
        args = ["log", "--since=30 days ago", "--numstat", "--format=", "--"] + target_paths
        rc, out, _ = cls.run_git(repo_path, args)
        if rc == 0 and out:
            churn_total = 0
            for line in out.splitlines():
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    try:
                        added = int(parts[0]) if parts[0].isdigit() else 0
                        deleted = int(parts[1]) if parts[1].isdigit() else 0
                        churn_total += (added + deleted)
                    except ValueError as exc:
                        logger.debug("Skipping non-numeric numstat line in %s: %s", repo_path, exc)
            return churn_total
        return 0


class RepoTopologyResolver:
    """Topology-aware resolver for sovereign repositories, nested repos, and submodules."""

    @staticmethod
    def resolve_topology(repo_path: str) -> Dict[str, Any]:
        p = Path(repo_path).resolve()
        repo_name = p.name

        topology = {
            "name": repo_name,
            "path": str(p),
            "nested_repositories": [],
            "submodules": [],
            "modules": [],
            "submodule_warnings": [],
        }

        # Check for nested repositories (e.g. O20/enterprise)
        if (p / "enterprise").is_dir() and (p / "enterprise" / ".git").exists():
            ent_path = p / "enterprise"
            ent_git = GitTelemetryInspector.get_git_info(str(ent_path))
            topology["nested_repositories"].append({
                "name": "enterprise",
                "rel_path": "enterprise",
                "abs_path": str(ent_path),
                "git": ent_git,
            })

        # Check for git submodules (e.g. zencode-ent)
        gitmodules_file = p / ".gitmodules"
        if gitmodules_file.exists():
            try:
                with open(gitmodules_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                submodule_paths = re.findall(r'path\s*=\s*([^\s]+)', content)
                for sm_rel in submodule_paths:
                    sm_abs = p / sm_rel
                    if sm_abs.exists():
                        is_active_git = (sm_abs / ".git").exists()
                        sm_git = GitTelemetryInspector.get_git_info(str(sm_abs)) if is_active_git else {}
                        submodule_entry = {
                            "name": sm_rel,
                            "rel_path": sm_rel,
                            "abs_path": str(sm_abs),
                            "is_active": is_active_git or (sm_abs / "README.md").exists(),
                            "git": sm_git,
                        }
                        if sm_git.get("git_health_warning"):
                            topology["submodule_warnings"].append({
                                "submodule": sm_rel,
                                "warning": sm_git["git_health_warning"]
                            })
                        topology["submodules"].append(submodule_entry)
            except Exception as e:
                logger.warning("Failed to parse .gitmodules in %s: %s", repo_path, e)

        return topology

    @staticmethod
    def discover_modules(repo_path: str, scope: str = "sovereign") -> List[Dict[str, Any]]:
        p = Path(repo_path).resolve()
        modules: List[Dict[str, Any]] = []

        # 1. O20 Core & Enterprise
        addons_dir = p / "addons"
        if addons_dir.is_dir():
            for item in sorted(os.listdir(addons_dir)):
                item_path = addons_dir / item
                manifest = item_path / "__manifest__.py"
                if manifest.is_file():
                    if scope == "sovereign" and not item.startswith("insilos_"):
                        continue
                    modules.append({
                        "name": item,
                        "category": "odoo_addon",
                        "rel_path": f"addons/{item}",
                        "abs_path": str(item_path),
                        "git_context_repo": str(p),
                        "git_rel_path": f"addons/{item}",
                    })

        enterprise_dir = p / "enterprise"
        if enterprise_dir.is_dir():
            for item in sorted(os.listdir(enterprise_dir)):
                item_path = enterprise_dir / item
                manifest = item_path / "__manifest__.py"
                if manifest.is_file():
                    if scope == "sovereign" and not (item.startswith("insilos_") or item.startswith("innokafe_")):
                        continue
                    modules.append({
                        "name": item,
                        "category": "odoo_enterprise",
                        "rel_path": f"enterprise/{item}",
                        "abs_path": str(item_path),
                        "git_context_repo": str(enterprise_dir) if (enterprise_dir / ".git").exists() else str(p),
                        "git_rel_path": item if (enterprise_dir / ".git").exists() else f"enterprise/{item}",
                    })

        # 2. VerticalRisk Extensions
        extensions_dir = p / "extensions"
        if extensions_dir.is_dir():
            for item in sorted(os.listdir(extensions_dir)):
                item_path = extensions_dir / item
                pkg_json = item_path / "package.json"
                if pkg_json.is_file():
                    modules.append({
                        "name": item,
                        "category": "grc_extension",
                        "rel_path": f"extensions/{item}",
                        "abs_path": str(item_path),
                        "git_context_repo": str(p),
                        "git_rel_path": f"extensions/{item}",
                    })

        # 3. insilos_mobile Packages
        if (p / "packages").is_dir() or any(p.name.startswith("mobo_") for p in p.iterdir() if p.is_dir()):
            for item in sorted(os.listdir(p)):
                item_path = p / item
                if item_path.is_dir() and item not in IGNORED_DIRS:
                    if (item_path / "pubspec.yaml").is_file():
                        modules.append({
                            "name": item,
                            "category": "flutter_package",
                            "rel_path": item,
                            "abs_path": str(item_path),
                            "git_context_repo": str(p),
                            "git_rel_path": item,
                        })
            packages_dir = p / "packages"
            if packages_dir.is_dir():
                for sub in sorted(os.listdir(packages_dir)):
                    sub_path = packages_dir / sub
                    if sub_path.is_dir() and (sub_path / "pubspec.yaml").is_file():
                        modules.append({
                            "name": sub,
                            "category": "flutter_core",
                            "rel_path": f"packages/{sub}",
                            "abs_path": str(sub_path),
                            "git_context_repo": str(p),
                            "git_rel_path": f"packages/{sub}",
                        })

        # 4. zencode-ent Submodules
        if (p / ".gitmodules").is_file():
            known_submodules = ["router", "hub", "vertical", "zencode", "zencode-core", "AI"]
            for sm in known_submodules:
                sm_path = p / sm
                if sm_path.is_dir():
                    is_git = (sm_path / ".git").exists()
                    modules.append({
                        "name": sm,
                        "category": "swarm_submodule",
                        "rel_path": sm,
                        "abs_path": str(sm_path),
                        "git_context_repo": str(sm_path) if is_git else str(p),
                        "git_rel_path": "." if is_git else sm,
                    })

        return modules


class DocDriftAuditor:
    """Calculates documentation drift: delta = (T_code - T_doc) / 86400."""

    @classmethod
    def audit_module(cls, module_meta: Dict[str, Any], threshold_days: float = DEFAULT_DRIFT_THRESHOLD_DAYS) -> Dict[str, Any]:
        git_repo = module_meta["git_context_repo"]
        git_rel = module_meta["git_rel_path"]
        abs_path = Path(module_meta["abs_path"])

        # Check for localized documentation
        doc_candidates = ["README.md", "README.rst", "README.txt", "doc/index.rst", "docs/index.md"]
        found_doc_rel = None
        for cand in doc_candidates:
            if (abs_path / cand).exists():
                found_doc_rel = cand
                break

        # Git code timestamp
        code_ts = GitTelemetryInspector.get_latest_commit_ts(git_repo, git_rel)

        doc_ts = None
        doc_git_path = None
        if found_doc_rel:
            if git_rel == ".":
                doc_git_path = found_doc_rel
            else:
                doc_git_path = f"{git_rel}/{found_doc_rel}"
            doc_ts = GitTelemetryInspector.get_latest_commit_ts(git_repo, doc_git_path)

        # Status determination & drift calculation
        drift_days = None
        status = "IN_SYNC"

        if not found_doc_rel:
            status = "MISSING_DOC"
        elif code_ts and doc_ts:
            delta_seconds = code_ts - doc_ts
            drift_days = round(delta_seconds / 86400.0, 2)
            if drift_days > threshold_days:
                status = "DRIFT_STALE"
            elif drift_days < -threshold_days:
                status = "DOC_AHEAD"
            else:
                status = "IN_SYNC"
        elif code_ts and not doc_ts:
            status = "MISSING_DOC"

        return {
            "name": module_meta["name"],
            "rel_path": module_meta["rel_path"],
            "category": module_meta["category"],
            "has_localized_doc": found_doc_rel is not None,
            "doc_rel_path": found_doc_rel,
            "last_code_commit_ts": code_ts,
            "last_code_commit_date": datetime.fromtimestamp(code_ts, tz=timezone.utc).isoformat() if code_ts else None,
            "last_doc_commit_ts": doc_ts,
            "last_doc_commit_date": datetime.fromtimestamp(doc_ts, tz=timezone.utc).isoformat() if doc_ts else None,
            "drift_days": drift_days,
            "status": status,
            "is_drift_stale": (status == "DRIFT_STALE"),
            "is_missing_doc": (status == "MISSING_DOC"),
        }


class DependencyRiskAnalyzer:
    """Parses dependency manifests and identifies unpinned/risky dependency patterns."""

    @classmethod
    def scan_repository(cls, repo_path: str) -> List[Dict[str, Any]]:
        p = Path(repo_path).resolve()
        risks: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            rel_root = os.path.relpath(root, p)

            # 1. Flutter pubspec.yaml
            if "pubspec.yaml" in files:
                pubspec_path = Path(root) / "pubspec.yaml"
                cls._parse_pubspec(pubspec_path, rel_root, risks)

            # 2. Python requirements.txt
            if "requirements.txt" in files:
                req_path = Path(root) / "requirements.txt"
                cls._parse_requirements(req_path, rel_root, risks)

            # 3. Python pyproject.toml
            if "pyproject.toml" in files:
                pyproj_path = Path(root) / "pyproject.toml"
                cls._parse_pyproject(pyproj_path, rel_root, risks)

            # 4. Node.js package.json (root or direct package files)
            if "package.json" in files:
                pkg_path = Path(root) / "package.json"
                cls._parse_package_json(pkg_path, rel_root, risks)

        return risks

    @classmethod
    def _parse_pubspec(cls, file_path: Path, rel_root: str, risks: List[Dict[str, Any]]):
        rel_file = str(Path(rel_root) / file_path.name)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            in_deps = False
            for line_no, raw_line in enumerate(lines, 1):
                line = raw_line.strip()
                if line.startswith("dependencies:") or line.startswith("dev_dependencies:"):
                    in_deps = True
                    continue
                if in_deps and line and not line.startswith("#"):
                    if not raw_line.startswith(" ") and not raw_line.startswith("\t"):
                        in_deps = False
                        continue
                    # Match ': any'
                    if ": any" in line:
                        dep_name = line.split(":")[0].strip()
                        risks.append({
                            "file": rel_file,
                            "line": line_no,
                            "dependency": dep_name,
                            "version_spec": "any",
                            "risk_type": "UNPINNED_FLUTTER_ANY",
                            "severity": "HIGH",
                            "rule_code": "DEP01",
                            "recommendation": f"Replace ': any' with bounded SemVer caret range for {dep_name}",
                        })
        except Exception as e:
            logger.warning("Failed to parse pubspec %s: %s", file_path, e)

    @classmethod
    def _parse_requirements(cls, file_path: Path, rel_root: str, risks: List[Dict[str, Any]]):
        rel_file = str(Path(rel_root) / file_path.name)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_no, raw_line in enumerate(lines, 1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                clean_line = line.split(";")[0].split("#")[0].strip()
                if not clean_line:
                    continue

                if re.search(r'>=[0-9.]+$', clean_line):
                    dep_name = re.split(r'>=', clean_line)[0].strip()
                    spec = ">=" + re.split(r'>=', clean_line)[1].strip()
                    risks.append({
                        "file": rel_file,
                        "line": line_no,
                        "dependency": dep_name,
                        "version_spec": spec,
                        "risk_type": "UNPINNED_UPPER_BOUND",
                        "severity": "MEDIUM",
                        "rule_code": "DEP02",
                        "recommendation": f"Add upper bound pin (e.g. {dep_name}{spec},<{int(spec[2:].split('.')[0])+1}.0.0)",
                    })
                elif re.match(r'^[a-zA-Z0-9_\-]+$', clean_line):
                    risks.append({
                        "file": rel_file,
                        "line": line_no,
                        "dependency": clean_line,
                        "version_spec": "unpinned",
                        "risk_type": "UNPINNED_PYTHON_PKG",
                        "severity": "MEDIUM",
                        "rule_code": "DEP02",
                        "recommendation": f"Specify explicit version pin for {clean_line}",
                    })
        except Exception as e:
            logger.warning("Failed to parse requirements %s: %s", file_path, e)

    @classmethod
    def _parse_pyproject(cls, file_path: Path, rel_root: str, risks: List[Dict[str, Any]]):
        rel_file = str(Path(rel_root) / file_path.name)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            matches = re.findall(r'["\']([a-zA-Z0-9_\-]+)>=([0-9.]+)["\']', content)
            for dep_name, ver in matches:
                if f"<{dep_name}" not in content:
                    risks.append({
                        "file": rel_file,
                        "line": 1,
                        "dependency": dep_name,
                        "version_spec": f">={ver}",
                        "risk_type": "UNPINNED_UPPER_BOUND",
                        "severity": "MEDIUM",
                        "rule_code": "DEP02",
                        "recommendation": f"Constrain upper bound for {dep_name}",
                    })
        except Exception as e:
            logger.warning("Failed to parse pyproject %s: %s", file_path, e)

    @classmethod
    def _parse_package_json(cls, file_path: Path, rel_root: str, risks: List[Dict[str, Any]]):
        rel_file = str(Path(rel_root) / file_path.name)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}

            critical_pkgs = {"knex", "pg", "vitest", "playwright", "puppeteer", "directus"}
            for pkg, spec in all_deps.items():
                if isinstance(spec, str):
                    if spec.startswith("^") and pkg in critical_pkgs:
                        risks.append({
                            "file": rel_file,
                            "line": 1,
                            "dependency": pkg,
                            "version_spec": spec,
                            "risk_type": "LOOSE_NPM_RANGE",
                            "severity": "LOW",
                            "rule_code": "DEP03",
                            "recommendation": f"Pin critical runtime package {pkg} to exact version or tilde range",
                        })
                    elif spec == "*" or spec == "latest":
                        risks.append({
                            "file": rel_file,
                            "line": 1,
                            "dependency": pkg,
                            "version_spec": spec,
                            "risk_type": "WILDCARD_NPM_VERSION",
                            "severity": "HIGH",
                            "rule_code": "DEP03",
                            "recommendation": f"Replace wildcard pin with explicit version for {pkg}",
                        })
        except Exception as e:
            logger.warning("Failed to parse package.json %s: %s", file_path, e)


class DualSizingEstimator:
    """Calculates Dual Backlog Sizing: Replacement Sizing vs Active Sprint Workload."""

    COMPLEXITY_MAP = {
        "O20": 1.5,
        "VerticalRisk": 1.25,
        "insilos_mobile": 1.25,
        "zencode-ent": 1.5,
    }

    @classmethod
    def compute_sizing(
        cls,
        repo_path: str,
        repo_name: str,
        churn_30d: int,
        dirty_count: int,
        drift_mods_count: int,
        topology: Dict[str, Any],
        modules: List[Dict[str, Any]],
        scope: str = "sovereign"
    ) -> Dict[str, Any]:
        p = Path(repo_path).resolve()

        files: List[str] = []

        # 1. Main repo tracked files
        if (p / ".gitmodules").exists():
            rc, out, _ = GitTelemetryInspector.run_git(str(p), ["ls-files", "--recurse-submodules"])
            if rc == 0 and out:
                files.extend(out.splitlines())
        else:
            rc, out, _ = GitTelemetryInspector.run_git(str(p), ["ls-files"])
            if rc == 0 and out:
                files.extend(out.splitlines())

        # 2. Check nested repositories (e.g. O20/enterprise)
        for nested in topology.get("nested_repositories", []):
            nested_abs = nested["abs_path"]
            nested_rel = nested["rel_path"]
            rc_n, out_n, _ = GitTelemetryInspector.run_git(nested_abs, ["ls-files"])
            if rc_n == 0 and out_n:
                for f_n in out_n.splitlines():
                    files.append(f"{nested_rel}/{f_n}")

        if not files:
            for root, dirs, f_list in os.walk(p):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
                for f in f_list:
                    files.append(os.path.relpath(os.path.join(root, f), p))

        total_files = len(files)
        code_lines = 0
        test_lines = 0
        doc_lines = 0

        # Sample up to 10,000 files to maintain sub-second performance
        for f in files[:10000]:
            fp = p / f
            if not fp.is_file():
                continue
            ext = fp.suffix.lower()
            is_test = any(tp in f.lower() for tp in TEST_PATTERNS)

            try:
                with open(fp, "rb") as f_obj:
                    line_count = sum(1 for _ in f_obj)
            except OSError as exc:
                logger.debug("Skipping unreadable file %s: %s", fp, exc)
                line_count = 0

            if ext in TEXT_DOC_EXTS or (ext in {".md", ".rst", ".txt"} and ("readme" in f.lower() or "adr" in f.lower())):
                doc_lines += line_count
            elif is_test:
                test_lines += line_count
            elif ext in CODE_EXTENSIONS and ext not in {".po", ".pot"}:
                code_lines += line_count

        test_ratio = round(test_lines / max(1, code_lines), 3)
        complexity_factor = cls.COMPLEXITY_MAP.get(repo_name, 1.25)

        # 1. Asset Replacement Sizing (LOC / 180 * Complexity)
        replacement_man_days = round((code_lines / 180.0) * complexity_factor, 1)

        # 2. Calculate effective sprint churn
        effective_churn = churn_30d
        if scope == "sovereign" and repo_name == "O20":
            sovereign_paths = [m["rel_path"] for m in modules if m["rel_path"].startswith("addons/")]
            scoped_churn = GitTelemetryInspector.get_scoped_churn(str(p), sovereign_paths)
            if scoped_churn > 0:
                effective_churn = scoped_churn
            else:
                effective_churn = min(churn_30d, code_lines)
        else:
            effective_churn = min(churn_30d, max(code_lines, 20000))

        # 3. Active Sprint Workload (Churn / 120 + Dirty * 0.2 + Drift_mods * 1.0)
        sprint_workload_days = round(
            (effective_churn / 120.0) + (dirty_count * 0.2) + (drift_mods_count * 1.0),
            1
        )

        return {
            "total_files": total_files,
            "loc_code": code_lines,
            "loc_test": test_lines,
            "loc_docs": doc_lines,
            "test_coverage_ratio": test_ratio,
            "complexity_rating": complexity_factor,
            "replacement_man_days": replacement_man_days,
            "active_sprint_workload_days": sprint_workload_days,
            "effective_churn_30d": effective_churn,
        }


class BacklogSynthesizer:
    """Synthesizes candidate backlog items in Backlog v2 format with DoD and metadata."""

    @classmethod
    def generate_backlog_items(
        cls,
        repo_name: str,
        git_info: Dict[str, Any],
        topology: Dict[str, Any],
        doc_drift_results: List[Dict[str, Any]],
        dependency_risks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        # 1. P0 Architecture: Git Traversal Health Warning in repository or submodules
        if git_info.get("git_health_warning"):
            item_code = f"GIT01-{repo_name.upper()}"
            title = f"Repair broken Git commit graph traversal in {repo_name}"
            dod = f"Fetch missing commit objects or reconcile git history so 'git rev-list' traverses parent tree without error"
            meta = f"repo={repo_name} path=. verify=\"git -C {repo_name} rev-list --count HEAD\" risk=R3"
            items.append({
                "item_code": item_code,
                "priority": "P0",
                "track": "architecture",
                "title": title,
                "dod": dod,
                "repo": repo_name,
                "path": ".",
                "verify": f"git -C {repo_name} rev-list --count HEAD",
                "risk": "R3",
                "formatted_line": f"- [ ] [{item_code}][P0][architecture] {title} — DoD: {dod} <!-- meta: {meta} -->"
            })

        for warn in topology.get("submodule_warnings", []):
            sm_name = warn["submodule"]
            sm_upper = sm_name.upper().replace("-", "_").replace(".", "_")
            item_code = f"GIT01-{sm_upper}"
            title = f"Repair broken Git commit graph traversal in {sm_name} submodule"
            dod = f"Fetch missing commit objects or reconcile submodule history so 'git rev-list' traverses parent tree cleanly"
            meta = f"repo={repo_name} path={sm_name} verify=\"git -C {sm_name} rev-list --count HEAD\" risk=R3"
            items.append({
                "item_code": item_code,
                "priority": "P0",
                "track": "architecture",
                "title": title,
                "dod": dod,
                "repo": repo_name,
                "path": sm_name,
                "verify": f"git -C {sm_name} rev-list --count HEAD",
                "risk": "R3",
                "formatted_line": f"- [ ] [{item_code}][P0][architecture] {title} — DoD: {dod} <!-- meta: {meta} -->"
            })

        # 2. P1 Docs: Documentation Drift > 30 Days
        for mod in doc_drift_results:
            if mod["status"] == "DRIFT_STALE":
                drift_str = f"{mod['drift_days']:.1f}d" if mod["drift_days"] is not None else ">30d"
                mod_name_upper = mod["name"].upper().replace("-", "_").replace(".", "_")
                item_code = f"DOC01-{mod_name_upper}"
                title = f"Reconcile documentation drift in {mod['name']} (drift: {drift_str})"
                dod = f"Update {mod['rel_path']}/README.md to align with latest HEAD code commits and verify living architecture assertions"
                meta = f"repo={repo_name} path={mod['rel_path']} verify=\"test -f {mod['rel_path']}/README.md\" risk=R1"
                items.append({
                    "item_code": item_code,
                    "priority": "P1",
                    "track": "docs",
                    "title": title,
                    "dod": dod,
                    "repo": repo_name,
                    "path": mod["rel_path"],
                    "verify": f"test -f {mod['rel_path']}/README.md",
                    "risk": "R1",
                    "formatted_line": f"- [ ] [{item_code}][P1][docs] {title} — DoD: {dod} <!-- meta: {meta} -->"
                })

        # 3. P1 Docs: Missing Localized Documentation
        for mod in doc_drift_results:
            if mod["status"] == "MISSING_DOC":
                mod_name_upper = mod["name"].upper().replace("-", "_").replace(".", "_")
                item_code = f"DOC02-{mod_name_upper}"
                title = f"Author sovereign localized README for {mod['name']}"
                dod = f"Create {mod['rel_path']}/README.md documenting architecture, dependencies, and contract tests"
                meta = f"repo={repo_name} path={mod['rel_path']}/README.md verify=\"test -f {mod['rel_path']}/README.md\" risk=R0"
                items.append({
                    "item_code": item_code,
                    "priority": "P1",
                    "track": "docs",
                    "title": title,
                    "dod": dod,
                    "repo": repo_name,
                    "path": f"{mod['rel_path']}/README.md",
                    "verify": f"test -f {mod['rel_path']}/README.md",
                    "risk": "R0",
                    "formatted_line": f"- [ ] [{item_code}][P1][docs] {title} — DoD: {dod} <!-- meta: {meta} -->"
                })

        # 4. P1 Security: Unpinned Flutter ': any'
        seen_deps = set()
        for risk in dependency_risks:
            if risk["risk_type"] == "UNPINNED_FLUTTER_ANY":
                dep_upper = risk["dependency"].upper().replace("-", "_").replace(".", "_")
                pkg_tag = risk["file"].split("/")[0].upper().replace("-", "_")
                item_code = f"DEP01-{pkg_tag}-{dep_upper}"
                if item_code in seen_deps:
                    continue
                seen_deps.add(item_code)

                title = f"Pin loose ': any' dependency for {risk['dependency']} in {risk['file']}"
                dod = f"Replace ': any' with explicit bounded SemVer caret range in {risk['file']}"
                meta = f"repo={repo_name} path={risk['file']} verify=\"flutter pub get\" risk=R2"
                items.append({
                    "item_code": item_code,
                    "priority": "P1",
                    "track": "security",
                    "title": title,
                    "dod": dod,
                    "repo": repo_name,
                    "path": risk["file"],
                    "verify": "flutter pub get",
                    "risk": "R2",
                    "formatted_line": f"- [ ] [{item_code}][P1][security] {title} — DoD: {dod} <!-- meta: {meta} -->"
                })

        # 5. P2 Security: Unpinned Python Upper Bounds
        for risk in dependency_risks:
            if risk["risk_type"] in ["UNPINNED_UPPER_BOUND", "UNPINNED_PYTHON_PKG"]:
                dep_upper = risk["dependency"].upper().replace("-", "_").replace(".", "_")
                file_tag = Path(risk["file"]).stem.upper()
                item_code = f"DEP02-{file_tag}-{dep_upper}"
                if item_code in seen_deps:
                    continue
                seen_deps.add(item_code)

                title = f"Pin upper bound on Python dependency {risk['dependency']} in {risk['file']}"
                dod = f"Add explicit upper bound constraint to {risk['dependency']} in {risk['file']}"
                meta = f"repo={repo_name} path={risk['file']} verify=\"pip check\" risk=R1"
                items.append({
                    "item_code": item_code,
                    "priority": "P2",
                    "track": "security",
                    "title": title,
                    "dod": dod,
                    "repo": repo_name,
                    "path": risk["file"],
                    "verify": "pip check",
                    "risk": "R1",
                    "formatted_line": f"- [ ] [{item_code}][P2][security] {title} — DoD: {dod} <!-- meta: {meta} -->"
                })

        # 6. P1 Plan: Dirty Files Quarantining (>20 files)
        if git_info.get("dirty_files_count", 0) > 20:
            item_code = f"WIP01-{repo_name.upper()}"
            title = f"Triage {git_info['dirty_files_count']} uncommitted dirty files in {repo_name}"
            dod = f"Review and quarantine uncommitted working tree modifications into feature branches to restore clean tree"
            meta = f"repo={repo_name} path=. verify=\"git -C {repo_name} status --porcelain\" risk=R1"
            items.append({
                "item_code": item_code,
                "priority": "P1",
                "track": "plan",
                "title": title,
                "dod": dod,
                "repo": repo_name,
                "path": ".",
                "verify": f"git -C {repo_name} status --porcelain",
                "risk": "R1",
                "formatted_line": f"- [ ] [{item_code}][P1][plan] {title} — DoD: {dod} <!-- meta: {meta} -->"
            })

        # 7. P3 Maintenance: Loose npm ranges
        for risk in dependency_risks:
            if risk["risk_type"] == "LOOSE_NPM_RANGE":
                dep_upper = risk["dependency"].upper().replace("-", "_").replace(".", "_")
                file_tag = Path(risk["file"]).parent.name.upper() or "ROOT"
                item_code = f"DEP03-{file_tag}-{dep_upper}"
                if item_code in seen_deps:
                    continue
                seen_deps.add(item_code)

                title = f"Pin explicit version for {risk['dependency']} in {risk['file']}"
                dod = f"Replace loose caret with exact SemVer pin in {risk['file']}"
                meta = f"repo={repo_name} path={risk['file']} verify=\"pnpm test\" risk=R0"
                items.append({
                    "item_code": item_code,
                    "priority": "P3",
                    "track": "plan",
                    "title": title,
                    "dod": dod,
                    "repo": repo_name,
                    "path": risk["file"],
                    "verify": "pnpm test",
                    "risk": "R0",
                    "formatted_line": f"- [ ] [{item_code}][P3][plan] {title} — DoD: {dod} <!-- meta: {meta} -->"
                })

        return items


class MultiRepoScanner:
    """Master orchestrator executing scans across all target repositories."""

    def __init__(self, repos: Optional[List[str]] = None, drift_threshold_days: float = DEFAULT_DRIFT_THRESHOLD_DAYS, scope: str = "sovereign"):
        self.repos = repos or DEFAULT_REPOSITORIES
        self.drift_threshold_days = drift_threshold_days
        self.scope = scope

    def scan_all(self) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        results: Dict[str, Any] = {
            "audit_metadata": {
                "timestamp": timestamp,
                "scanner_version": "2.0.0",
                "drift_threshold_days": self.drift_threshold_days,
                "scanned_repositories_count": len(self.repos),
                "scope": self.scope,
            },
            "summary": {
                "total_repositories": len(self.repos),
                "total_modules": 0,
                "total_loc_code": 0,
                "total_loc_test": 0,
                "total_velocity_30d": 0,
                "total_dirty_files": 0,
                "drift_stale_modules_count": 0,
                "missing_doc_modules_count": 0,
                "dependency_risks_count": 0,
                "total_replacement_man_days": 0.0,
                "total_active_sprint_workload_days": 0.0,
                "candidate_backlog_items_count": 0,
            },
            "repositories": {},
            "candidate_backlog": [],
        }

        all_backlog_items: List[Dict[str, Any]] = []

        for repo_path in self.repos:
            p = Path(repo_path).resolve()
            repo_name = p.name
            logger.info("Scanning repository [%s] at %s...", repo_name, repo_path)

            if not p.exists():
                logger.warning("Repository path does not exist: %s", repo_path)
                continue

            # 1. Topology resolution
            topology = RepoTopologyResolver.resolve_topology(str(p))
            modules = RepoTopologyResolver.discover_modules(str(p), scope=self.scope)

            # 2. Git Telemetry
            git_info = GitTelemetryInspector.get_git_info(str(p))

            # 3. Documentation Drift Audit
            doc_audits = []
            drift_stale_count = 0
            missing_doc_count = 0
            for mod in modules:
                audit = DocDriftAuditor.audit_module(mod, threshold_days=self.drift_threshold_days)
                doc_audits.append(audit)
                if audit["is_drift_stale"]:
                    drift_stale_count += 1
                if audit["is_missing_doc"]:
                    missing_doc_count += 1

            # 4. Dependency Risk Analysis
            dep_risks = DependencyRiskAnalyzer.scan_repository(str(p))

            # 5. Dual Sizing
            sizing = DualSizingEstimator.compute_sizing(
                repo_path=str(p),
                repo_name=repo_name,
                churn_30d=git_info["churn_30d"],
                dirty_count=git_info["dirty_files_count"],
                drift_mods_count=drift_stale_count + missing_doc_count,
                topology=topology,
                modules=modules,
                scope=self.scope
            )

            # 6. Candidate Backlog Generation
            backlog_items = BacklogSynthesizer.generate_backlog_items(
                repo_name=repo_name,
                git_info=git_info,
                topology=topology,
                doc_drift_results=doc_audits,
                dependency_risks=dep_risks
            )
            all_backlog_items.extend(backlog_items)

            repo_report = {
                "name": repo_name,
                "path": str(p),
                "git": git_info,
                "topology": topology,
                "modules_count": len(modules),
                "documentation_drift": {
                    "total_modules": len(modules),
                    "drift_stale_count": drift_stale_count,
                    "missing_doc_count": missing_doc_count,
                    "in_sync_count": len(modules) - (drift_stale_count + missing_doc_count),
                    "modules": doc_audits,
                },
                "dependency_risks": dep_risks,
                "sizing": sizing,
                "candidate_backlog_items": backlog_items,
            }

            results["repositories"][repo_name] = repo_report

            # Aggregate Summary
            s = results["summary"]
            s["total_modules"] += len(modules)
            s["total_loc_code"] += sizing["loc_code"]
            s["total_loc_test"] += sizing["loc_test"]
            s["total_velocity_30d"] += git_info["velocity_30d"]
            s["total_dirty_files"] += git_info["dirty_files_count"]
            s["drift_stale_modules_count"] += drift_stale_count
            s["missing_doc_modules_count"] += missing_doc_count
            s["dependency_risks_count"] += len(dep_risks)
            s["total_replacement_man_days"] += sizing["replacement_man_days"]
            s["total_active_sprint_workload_days"] += sizing["active_sprint_workload_days"]

        # Sort candidate backlog by priority (P0 -> P1 -> P2 -> P3)
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        all_backlog_items.sort(key=lambda x: (priority_order.get(x["priority"], 9), x["item_code"]))

        results["candidate_backlog"] = [item["formatted_line"] for item in all_backlog_items]
        results["summary"]["candidate_backlog_items_count"] = len(all_backlog_items)
        results["summary"]["total_replacement_man_days"] = round(results["summary"]["total_replacement_man_days"], 1)
        results["summary"]["total_active_sprint_workload_days"] = round(results["summary"]["total_active_sprint_workload_days"], 1)

        return results

    def generate_markdown_report(self, scan_results: Dict[str, Any]) -> str:
        lines: List[str] = []
        meta = scan_results["audit_metadata"]
        summary = scan_results["summary"]

        lines.append("# Insilos Multi-Repository Continuous Governance Report")
        lines.append(f"> **Audit Timestamp:** `{meta['timestamp']}` | **Scanner Version:** `v{meta['scanner_version']}` | **Drift Threshold:** `{meta['drift_threshold_days']} days`\n")

        # Executive Summary Table
        lines.append("## 1. Executive Telemetry Overview\n")
        lines.append("| Repository | Active Branch | HEAD Commit | 30d Velocity | Dirty Files | Code LOC | Sizing ($S_{replace}$) | Sprint Churn ($S_{sprint}$) | Doc Drift >30d | Dependency Risks |")
        lines.append("|:---|:---|:---:|---:|---:|---:|---:|---:|:---:|:---:|")

        for repo_name, repo_data in scan_results["repositories"].items():
            git = repo_data["git"]
            sz = repo_data["sizing"]
            doc = repo_data["documentation_drift"]
            dep_count = len(repo_data["dependency_risks"])

            dirty_icon = "⚠️" if git["dirty_files_count"] > 0 else "✅"
            drift_icon = "🔴" if doc["drift_stale_count"] > 0 else "🟢"
            dep_icon = "⚠️" if dep_count > 0 else "✅"

            lines.append(
                f"| **`{repo_name}`** | `{git['branch']}` | `{git['head']}` | "
                f"{git['velocity_30d']} | {dirty_icon} {git['dirty_files_count']} | "
                f"{sz['loc_code']:,} | {sz['replacement_man_days']:,} d | "
                f"{sz['active_sprint_workload_days']:,} d | "
                f"{drift_icon} {doc['drift_stale_count']} stale ({doc['missing_doc_count']} missing) | "
                f"{dep_icon} {dep_count} risks |"
            )

        lines.append("\n---\n")

        # Detailed Documentation Drift Table
        lines.append("## 2. Documentation Drift & Staleness Findings (>30 Days Threshold)\n")
        lines.append("| Repository | Module / Package | Category | Drift (Days) | Status | Last Code Commit | Last Doc Commit |")
        lines.append("|:---|:---|:---|---:|:---:|:---|:---|")

        has_drift_findings = False
        for repo_name, repo_data in scan_results["repositories"].items():
            for mod in repo_data["documentation_drift"]["modules"]:
                if mod["status"] in ["DRIFT_STALE", "MISSING_DOC"]:
                    has_drift_findings = True
                    drift_str = f"{mod['drift_days']:.1f} d" if mod["drift_days"] is not None else "N/A"
                    status_badge = "🔴 STALE" if mod["status"] == "DRIFT_STALE" else "⚠️ MISSING"
                    lines.append(
                        f"| `{repo_name}` | `{mod['rel_path']}` | `{mod['category']}` | "
                        f"**{drift_str}** | {status_badge} | "
                        f"{mod['last_code_commit_date'] or 'N/A'} | {mod['last_doc_commit_date'] or 'N/A'} |"
                    )

        if not has_drift_findings:
            lines.append("| - | All scanned modules in sync | - | 0.0 d | 🟢 IN_SYNC | - | - |")

        lines.append("\n---\n")

        # Dependency Risk Matrix
        lines.append("## 3. Dependency Risk Analysis Matrix\n")
        lines.append("| Severity | Rule | Manifest Path | Dependency | Offending Spec | Recommended Remediation |")
        lines.append("|:---:|:---:|:---|:---|:---|:---|")

        has_dep_risks = False
        for repo_name, repo_data in scan_results["repositories"].items():
            for r in repo_data["dependency_risks"]:
                has_dep_risks = True
                sev_icon = {"HIGH": "🔴 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🔵 LOW"}.get(r["severity"], r["severity"])
                lines.append(
                    f"| {sev_icon} | `{r['rule_code']}` | `{repo_name}/{r['file']}` | "
                    f"`{r['dependency']}` | `{r['version_spec']}` | {r['recommendation']} |"
                )

        if not has_dep_risks:
            lines.append("| 🟢 | - | Clean manifests | All dependencies pinned | - | - |")

        lines.append("\n---\n")

        # Prioritized Candidate Backlog (v2)
        lines.append("## 4. Prioritized Candidate Backlog (Backlog v2 Format)\n")
        lines.append("```markdown")
        for bl_line in scan_results["candidate_backlog"]:
            lines.append(bl_line)
        lines.append("```\n")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Multi-Repository Governance & Continuous Scanner")
    parser.add_argument("--repos", nargs="+", default=DEFAULT_REPOSITORIES, help="Target repository paths")
    parser.add_argument("--threshold", type=float, default=DEFAULT_DRIFT_THRESHOLD_DAYS, help="Drift threshold in days")
    parser.add_argument("--scope", choices=["sovereign", "all"], default="sovereign", help="Module discovery scope")
    parser.add_argument("--json", type=str, help="Path to write JSON scan report")
    parser.add_argument("--markdown", type=str, help="Path to write Markdown report")
    parser.add_argument("--check", action="store_true", help="Fail with exit code 1 if P0 defects exist")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")

    scanner = MultiRepoScanner(repos=args.repos, drift_threshold_days=args.threshold, scope=args.scope)
    results = scanner.scan_all()

    if args.json:
        out_json = Path(args.json).resolve()
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"✅ JSON scan report written to: {out_json}")

    if args.markdown:
        md_content = scanner.generate_markdown_report(results)
        out_md = Path(args.markdown).resolve()
        out_md.parent.mkdir(parents=True, exist_ok=True)
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ Markdown audit report written to: {out_md}")

    # Summary console output
    s = results["summary"]
    print("\n" + "=" * 60)
    print("MULTI-REPOSITORY GOVERNANCE SCAN SUMMARY")
    print("=" * 60)
    print(f"Repositories Scanned:       {s['total_repositories']}")
    print(f"Total Modules / Packages:   {s['total_modules']}")
    print(f"Total Tracked Code LOC:     {s['total_loc_code']:,}")
    print(f"30-Day Commit Velocity:     {s['total_velocity_30d']} commits")
    print(f"Dirty Files in Trees:       {s['total_dirty_files']} files")
    print(f"Doc Drift Stale (>30d):     {s['drift_stale_modules_count']} modules")
    print(f"Missing Localized Docs:     {s['missing_doc_modules_count']} modules")
    print(f"Dependency Risk Findings:   {s['dependency_risks_count']}")
    print(f"Total Replacement Sizing:   {s['total_replacement_man_days']:,} man-days")
    print(f"Active Sprint Workload:     {s['total_active_sprint_workload_days']:,} man-days")
    print(f"Generated Backlog Items:    {s['candidate_backlog_items_count']}")
    print("=" * 60 + "\n")

    if args.check:
        p0_items = [b for b in results.get("candidate_backlog", []) if "[P0]" in b]
        if p0_items:
            print(f"❌ CHECK FAILED: Found {len(p0_items)} P0 critical governance blocker(s):")
            for p0 in p0_items:
                print(f"   {p0}")
            sys.exit(1)
        else:
            print("✅ CHECK PASSED: Zero P0 critical governance blockers detected.")

    sys.exit(0)


if __name__ == "__main__":
    main()
