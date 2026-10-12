#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Repository Continuous Scanner & Documentation Drift Telemetry Engine (R2 / AL2C-AST-001)

Sovereign Repositories Inspected:
  1. /home/zen/O20 (O20 Core Platform & nested enterprise)
  2. /home/zen/VerticalRisk (GRC Monorepo & 67 extensions)
  3. /home/zen/insilos_mobile (Flutter Cross-Platform Client & 27 apps)
  4. /home/zen/zencode-ent (Sovereign Swarm & Fleet Router composite repo)

Audits:
  - Commit Velocity (30-day trailing)
  - Dirty File / Uncommitted WIP Index
  - Documentation Drift Delta: Δ(M) = (T_code - T_doc) / 86400 [days]
  - Dependency Risk Manifests (unpinned ': any', unpinned upper bounds)
  - Automated Backlog v2 Task Generation for Drift > 30 Days
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPOS = {
    'O20': {
        'name': 'Insilos O20 Core Platform',
        'path': '/home/zen/O20',
        'stack': 'Python 3.12 / Odoo 20 / OWL 2 / SCSS',
        'doc_paths': ['README.md', 'AGENTS.md', 'addons/insilos_al2c/README.md'],
        'code_glob': ['addons/**/*.py', 'addons/**/*.js', 'addons/**/*.xml'],
    },
    'O20_ENTERPRISE': {
        'name': 'Insilos O20 Enterprise Addons',
        'path': '/home/zen/O20/enterprise',
        'stack': 'Odoo 20 Enterprise / QWeb / SCSS',
        'doc_paths': ['README.md'],
        'code_glob': ['**/*.py', '**/*.js', '**/*.xml'],
    },
    'VERTICAL_RISK': {
        'name': 'Insilos Vertical Risk & Compliance GRC',
        'path': '/home/zen/VerticalRisk',
        'stack': 'TypeScript / Node.js / Eramba / Directus',
        'doc_paths': ['README.md', 'docs/extensions-catalog.md', 'docs/architecture.md'],
        'code_glob': ['extensions/**/*.ts', 'extensions/**/*.js', 'src/**/*.ts'],
    },
    'INSILOS_MOBILE': {
        'name': 'Insilos Mobile Cross-Platform Client',
        'path': '/home/zen/insilos_mobile',
        'stack': 'Flutter 3.x / Dart / Mobo Vert Shell',
        'doc_paths': ['README.md', 'mobo_vert_shell/README.md', 'docs/adr/'],
        'code_glob': ['packages/**/*.dart', 'mobo_vert_shell/**/*.dart'],
    },
    'ZENCODE_ENT': {
        'name': 'Zencode Enterprise AI Swarm & Router',
        'path': '/home/zen/zencode-ent',
        'stack': 'Python FastAPI / TypeScript Hub / Rust Core',
        'doc_paths': ['README.md', 'router/README.md', 'vertical/README.md'],
        'code_glob': ['router/**/*.py', 'hub/**/*.ts', 'vertical/**/*.ts'],
    },
}

DRIFT_THRESHOLD_DAYS = 30.0


def run_git(cmd, cwd):
    """Run a local git command safely returning stdout or empty string under strict stealth invariant."""
    cwd_path = Path(cwd).resolve()
    if not cwd_path.exists():
        return "", f"Directory {cwd} does not exist", 1

    # Strict Stealth & Local Integrity Guard: forbid outbound network subcommands
    FORBIDDEN_GIT_COMMANDS = {'fetch', 'pull', 'push', 'clone', 'submodule', 'ls-remote'}
    if any(c in FORBIDDEN_GIT_COMMANDS for c in cmd):
        raise ValueError(f"Strict stealth violation: git network subcommand '{cmd}' forbidden")

    try:
        res = subprocess.run(
            ['git'] + cmd,
            cwd=str(cwd_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False
        )
        return res.stdout.strip(), res.stderr.strip(), res.returncode
    except Exception as e:
        return "", str(e), 1


def scan_repo(repo_key, config):
    repo_path = config['path']
    if not os.path.exists(repo_path):
        return {
            'repo_key': repo_key,
            'name': config['name'],
            'path': repo_path,
            'status': 'MISSING_PATH',
            'error': f"Directory {repo_path} does not exist",
        }

    # 1. Active branch & HEAD commit
    branch, _, _ = run_git(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path)
    head_commit, _, _ = run_git(['rev-parse', '--short', 'HEAD'], repo_path)
    commit_date_str, _, _ = run_git(['log', '-1', '--format=%cI'], repo_path)
    commit_author, _, _ = run_git(['log', '-1', '--format=%an'], repo_path)
    commit_msg, _, _ = run_git(['log', '-1', '--format=%s'], repo_path)

    # 2. 30-day velocity
    rev_count_str, _, code = run_git(['rev-list', '--count', '--since=30.days', 'HEAD'], repo_path)
    try:
        velocity_30d = int(rev_count_str) if code == 0 else 0
    except ValueError:
        velocity_30d = 0

    # 3. Dirty files
    status_out, _, _ = run_git(['status', '--porcelain'], repo_path)
    dirty_lines = [l for l in status_out.splitlines() if l.strip()]
    dirty_count = len(dirty_lines)

    # 4. Documentation Drift Analysis
    # Get latest code commit timestamp
    # Look for last commit modifying code
    code_exts = ('py', 'js', 'ts', 'dart', 'xml', 'rs')
    latest_code_epoch = 0
    latest_code_file = ""
    latest_doc_epoch = 0
    latest_doc_file = ""

    # Check git log for code files
    code_log, _, _ = run_git(['log', '-n', '1', '--format=%at %ct', '--', '*.py', '*.js', '*.ts', '*.dart', '*.xml'], repo_path)
    if code_log:
        try:
            latest_code_epoch = int(code_log.split()[0])
        except (ValueError, IndexError):
            pass

    # Fallback to general HEAD epoch if no specific code commit matched
    if latest_code_epoch == 0:
        head_epoch_str, _, _ = run_git(['log', '-1', '--format=%at'], repo_path)
        try:
            latest_code_epoch = int(head_epoch_str)
        except ValueError:
            latest_code_epoch = int(datetime.now(timezone.utc).timestamp())

    # Check git log for doc files
    doc_candidates = config.get('doc_paths', ['README.md'])
    for dp in doc_candidates:
        full_dp = os.path.join(repo_path, dp)
        if os.path.exists(full_dp):
            doc_log, _, _ = run_git(['log', '-n', '1', '--format=%at', '--', dp], repo_path)
            if doc_log:
                try:
                    epoch = int(doc_log.split()[0])
                    if epoch > latest_doc_epoch:
                        latest_doc_epoch = epoch
                        latest_doc_file = dp
                except (ValueError, IndexError):
                    pass

    # If no doc commit found, check filesystem mtime
    if latest_doc_epoch == 0:
        for dp in doc_candidates:
            full_dp = os.path.join(repo_path, dp)
            if os.path.exists(full_dp):
                mtime = int(os.path.getmtime(full_dp))
                if mtime > latest_doc_epoch:
                    latest_doc_epoch = mtime
                    latest_doc_file = dp

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    drift_days = 0.0
    drift_status = 'IN_SYNC'
    if latest_doc_epoch > 0:
        drift_seconds = max(0, latest_code_epoch - latest_doc_epoch)
        drift_days = round(drift_seconds / 86400.0, 1)
        if drift_days > DRIFT_THRESHOLD_DAYS:
            drift_status = 'DRIFT_STALE'
        else:
            drift_status = 'IN_SYNC'
    else:
        drift_status = 'MISSING_DOC'
        drift_days = round(max(0, now_epoch - latest_code_epoch) / 86400.0, 1)

    # 5. Dependency Risk Scan
    dep_risks = []
    # Dart / Flutter pubspec.yaml check for ': any'
    if 'insilos_mobile' in repo_path:
        for root, _, files in os.walk(repo_path):
            if 'pubspec.yaml' in files:
                p_path = os.path.join(root, 'pubspec.yaml')
                rel_p = os.path.relpath(p_path, repo_path)
                try:
                    with open(p_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for idx, line in enumerate(f, 1):
                            if re.search(r'^\s*[\w_]+:\s*any\b', line):
                                dep_name = line.split(':')[0].strip()
                                dep_risks.append({
                                    'file': rel_p,
                                    'line': idx,
                                    'package': dep_name,
                                    'severity': 'HIGH',
                                    'reason': f"Unpinned dependency '{dep_name}: any' introduces non-deterministic build breaks",
                                })
                except Exception:
                    pass

    # Python requirements.txt check for unpinned upper bounds
    for root, _, files in os.walk(repo_path):
        # Exclude .venv
        if '.venv' in root or 'node_modules' in root or '.git' in root:
            continue
        if 'requirements.txt' in files:
            r_path = os.path.join(root, 'requirements.txt')
            rel_r = os.path.relpath(r_path, repo_path)
            try:
                with open(r_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for idx, line in enumerate(f, 1):
                        line_clean = line.strip()
                        if line_clean and not line_clean.startswith('#'):
                            # check if >= without <
                            if '>=' in line_clean and '<' not in line_clean and '==' not in line_clean:
                                pkg = line_clean.split('>=')[0].strip()
                                dep_risks.append({
                                    'file': rel_r,
                                    'line': idx,
                                    'package': pkg,
                                    'severity': 'MEDIUM',
                                    'reason': f"Unpinned upper bound on '{line_clean}' risks breaking changes on library major upgrades",
                                })
            except Exception:
                pass

    return {
        'repo_key': repo_key,
        'name': config['name'],
        'path': repo_path,
        'stack': config['stack'],
        'branch': branch,
        'head_commit': head_commit,
        'commit_date': commit_date_str,
        'commit_author': commit_author,
        'commit_msg': commit_msg,
        'velocity_30d': velocity_30d,
        'dirty_count': dirty_count,
        'drift_status': drift_status,
        'drift_days': drift_days,
        'latest_code_time': datetime.fromtimestamp(latest_code_epoch, timezone.utc).isoformat() if latest_code_epoch else None,
        'latest_doc_file': latest_doc_file or 'None',
        'latest_doc_time': datetime.fromtimestamp(latest_doc_epoch, timezone.utc).isoformat() if latest_doc_epoch else None,
        'dependency_risks': dep_risks,
    }


def generate_backlog_items(results):
    """Generates candidate Backlog v2 tasks for items with drift > 30 days or high dependency risk."""
    tasks = []
    for r in results:
        if r.get('drift_status') == 'DRIFT_STALE':
            key_hash = hashlib.sha256(f"{r['repo_key']}:doc_drift:{r['drift_days']}".encode()).hexdigest()[:8].upper()
            tasks.append({
                'task_id': f"AL2C-DOC-{key_hash}",
                'priority': 'P1',
                'track': 'docs',
                'repo': r['repo_key'],
                'path': r['path'],
                'drift_days': r['drift_days'],
                'markdown': (
                    f"- [ ] [AL2C-DOC-{key_hash}][P1][docs] Refresh stale architectural documentation for {r['name']} "
                    f"(detected drift: {r['drift_days']} days vs active code commits) — "
                    f"DoD: Localized documentation updated, verified by multi-repo scanner <!-- meta: repo={r['repo_key']} "
                    f"path={r['path']} verify=\"python3 tools/al2c_multirepo_scanner.py --check\" risk=R1 -->"
                )
            })
        elif r.get('drift_status') == 'MISSING_DOC':
            key_hash = hashlib.sha256(f"{r['repo_key']}:missing_doc".encode()).hexdigest()[:8].upper()
            tasks.append({
                'task_id': f"AL2C-DOC-{key_hash}",
                'priority': 'P1',
                'track': 'docs',
                'repo': r['repo_key'],
                'path': r['path'],
                'drift_days': r['drift_days'],
                'markdown': (
                    f"- [ ] [AL2C-DOC-{key_hash}][P1][docs] Establish localized architectural specification for {r['name']} "
                    f"— DoD: Component README.md and interface specification established <!-- meta: repo={r['repo_key']} "
                    f"path={r['path']} verify=\"python3 tools/al2c_multirepo_scanner.py --check\" risk=R1 -->"
                )
            })

        # High severity dependency risks
        for risk in r.get('dependency_risks', []):
            if risk.get('severity') == 'HIGH':
                key_hash = hashlib.sha256(f"{r['repo_key']}:{risk['package']}:dep_risk".encode()).hexdigest()[:8].upper()
                tasks.append({
                    'task_id': f"AL2C-DEP-{key_hash}",
                    'priority': 'P0',
                    'track': 'security',
                    'repo': r['repo_key'],
                    'path': f"{r['path']}/{risk['file']}",
                    'drift_days': 0,
                    'markdown': (
                        f"- [ ] [AL2C-DEP-{key_hash}][P0][security] Pin loose dependency '{risk['package']}' in {r['name']} "
                        f"({risk['file']}:{risk['line']}) to exact reproducible release — "
                        f"DoD: Manifest pinned, clean compile without ': any' <!-- meta: repo={r['repo_key']} "
                        f"path={risk['file']} verify=\"python3 tools/al2c_multirepo_scanner.py --check\" risk=R0 -->"
                    )
                })
    return tasks


def format_markdown_report(results, backlog_tasks):
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [
        "# Continuous Multi-Repository Governance & Risk Telemetry Report",
        "",
        f"> **Generated at**: {now_str}  ",
        f"> **Target Fleet**: 4 Sovereign Repositories (5 Git contexts)  ",
        f"> **Governance Threshold**: Documentation Drift > 30.0 Days triggers mandatory Backlog item",
        "",
        "---",
        "",
        "## 1. Multi-Repository Fleet Health Matrix",
        "",
        "| Repository | Tech Stack | Branch | HEAD Commit | 30d Velocity | Dirty WIP | Doc Drift | Status |",
        "|:---|:---|:---:|:---:|---:|---:|---:|:---:|",
    ]
    for r in results:
        status_icon = "🟢 IN_SYNC" if r['drift_status'] == 'IN_SYNC' else ("🔴 STALE" if r['drift_status'] == 'DRIFT_STALE' else "⚠️ MISSING")
        lines.append(
            f"| **{r['repo_key']}**<br><small>{r['name']}</small> | {r['stack']} | `{r.get('branch', '-')}` | "
            f"`{r.get('head_commit', '-')}` | {r.get('velocity_30d', 0)} commits | {r.get('dirty_count', 0)} files | "
            f"**{r.get('drift_days', 0.0)}d** | {status_icon} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Dependency Risk Assessment",
        "",
    ])

    total_risks = sum(len(r.get('dependency_risks', [])) for r in results)
    if total_risks == 0:
        lines.append("✅ **Zero high/medium dependency risks identified across manifests.**\n")
    else:
        lines.append(f"Identified **{total_risks} dependency risk items** across repositories:\n")
        lines.append("| Repo | Severity | Package / Manifest | Location | Risk Diagnostic |")
        lines.append("|:---|:---:|:---|:---|:---|")
        for r in results:
            for d in r.get('dependency_risks', []):
                sev_icon = "🔴 HIGH" if d['severity'] == 'HIGH' else "🟡 MEDIUM"
                lines.append(f"| `{r['repo_key']}` | {sev_icon} | `{d['package']}` | `{d['file']}:{d['line']}` | {d['reason']} |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Prioritized Continuous-Improvement Backlog (Backlog v2 Candidates)",
        "",
        "The following improvement tasks were automatically synthesized based on empirical drift > 30 days and dependency risk:",
        "",
    ])

    if not backlog_tasks:
        lines.append("🎉 *All sovereign repositories are within 30-day documentation sync and have zero unpinned high-risk dependencies.*")
    else:
        for t in backlog_tasks:
            lines.append(t['markdown'])

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Multi-Repository Continuous Scanner (R2 / AL2C-AST-001)")
    parser.add_argument('--check', action='store_true', help="Fail-closed check: returns exit code 1 if drift > 30d or high risk exists")
    parser.add_argument('--json', action='store_true', help="Output structured JSON telemetry")
    parser.add_argument('--output', type=str, default=None, help="Save markdown report to path")
    args = parser.parse_args()

    if args.output:
        if '..' in args.output or args.output.startswith('/etc') or args.output.startswith('/var'):
            sys.stderr.write(f"Security error: Invalid output path '{args.output}' (traversal forbidden)\n")
            sys.exit(1)

    results = []
    for r_key, r_cfg in REPOS.items():
        results.append(scan_repo(r_key, r_cfg))

    backlog_tasks = generate_backlog_items(results)

    if args.json:
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'repositories': results,
            'backlog_candidates': backlog_tasks,
        }
        print(json.dumps(payload, indent=2))
    else:
        md_report = format_markdown_report(results, backlog_tasks)
        print(md_report)
        if args.output:
            out_path = Path(args.output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md_report)

    if args.check:
        has_stale = any(r.get('drift_status') in ['DRIFT_STALE', 'MISSING_DOC'] for r in results)
        has_high_risk = any(
            any(d.get('severity') == 'HIGH' for d in r.get('dependency_risks', []))
            for r in results
        )
        if has_stale or has_high_risk:
            sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
