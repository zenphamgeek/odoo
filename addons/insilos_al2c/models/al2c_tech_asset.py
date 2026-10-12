# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.

import os
import subprocess
import datetime
import logging
from pathlib import Path
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Al2cTechAsset(models.Model):
    _name = 'al2c.tech.asset'
    _description = 'Technology Asset & Git Repository Registry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'risk_score desc, sequence asc, name asc'

    name = fields.Char(string='Asset Name', required=True, tracking=True)
    code = fields.Char(string='Asset Code', required=True, index=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    repo_path = fields.Char(string='Local Repository Path', required=True, tracking=True)
    category = fields.Selection([
        ('platform_core', 'Platform & ERP Core'),
        ('grc_vertical', 'Industry Vertical & GRC'),
        ('mobile_client', 'Mobile & Edge Client'),
        ('ai_swarm', 'AI Swarm & Fleet Infrastructure'),
        ('other', 'Other Technology Asset'),
    ], string='Category', required=True, default='platform_core', tracking=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('active', 'Active Production'),
        ('development', 'Active Development'),
        ('maintenance', 'Maintenance / AMS'),
        ('archived', 'Archived / Legacy'),
    ], string='Lifecycle Status', default='active', required=True, tracking=True)

    # Git Telemetry
    git_branch = fields.Char(string='Active Branch', readonly=True, tracking=True)
    git_commit = fields.Char(string='Latest Commit Hash', readonly=True)
    git_commit_full = fields.Char(string='Full Commit Hash', readonly=True)
    git_commit_message = fields.Char(string='Commit Message', readonly=True)
    git_commit_author = fields.Char(string='Commit Author', readonly=True)
    git_commit_date = fields.Datetime(string='Last Commit Timestamp', readonly=True)
    is_dirty = fields.Boolean(string='Has Uncommitted Changes', readonly=True)
    uncommitted_files_count = fields.Integer(string='Dirty Files Count', readonly=True)
    recent_commits_30d = fields.Integer(string='Commits (Last 30 Days)', readonly=True)

    # Estimation & Sizing Metrics
    total_files_count = fields.Integer(string='Tracked Files Count', readonly=True)
    loc_code = fields.Integer(string='Production Code LOC', readonly=True)
    loc_test = fields.Integer(string='Test Suite LOC', readonly=True)
    loc_docs = fields.Integer(string='Documentation LOC', readonly=True)
    test_coverage_ratio = fields.Float(string='Test / Code Ratio', digits=(5, 3), readonly=True)
    tech_stack = fields.Char(string='Primary Tech Stack')
    complexity_rating = fields.Selection([
        ('low', 'Low (Focused / Micro)'),
        ('medium', 'Moderate (Standard Enterprise)'),
        ('high', 'High (Multi-tier Suite)'),
        ('very_high', 'Very High (Sovereign Platform)'),
    ], string='Architectural Complexity', default='medium')
    estimated_effort_man_days = fields.Float(string='Estimated Effort (Man-Days)', readonly=True)
    estimated_delivery_weeks = fields.Float(string='Sprint Cycle Horizon (Weeks)', readonly=True)
    tech_debt_score = fields.Float(string='Technical Debt Score (0-100)', digits=(5, 1), readonly=True)

    # Risk Assessment
    risk_level = fields.Selection([
        ('low', 'Low / Stable (Green)'),
        ('medium', 'Moderate / Monitored (Amber)'),
        ('high', 'High Risk (Orange)'),
        ('critical', 'Critical Intervention (Red)'),
    ], string='Risk Grade', default='low', readonly=True, tracking=True)
    risk_score = fields.Float(string='Composite Risk Score (0-100)', digits=(5, 1), readonly=True, tracking=True)
    risk_factors = fields.Text(string='Identified Risk Factors', readonly=True)
    architectural_drift = fields.Selection([
        ('sovereign', 'Sovereign / In Sync'),
        ('minor_drift', 'Minor Drift Detected'),
        ('divergent', 'Architectural Divergence'),
    ], string='Architectural Drift', default='sovereign', tracking=True)

    # Documentation & Knowledge Synchronization
    primary_doc_path = fields.Char(string='Primary Specification / SRS Path')
    doc_freshness = fields.Selection([
        ('fresh', 'Fresh / Up-to-date (<7d)'),
        ('adequate', 'Adequate (<30d)'),
        ('stale', 'Stale (>30d)'),
        ('missing', 'Missing Specification'),
    ], string='Doc Freshness', default='fresh', readonly=True)
    doc_last_modified = fields.Datetime(string='Primary Doc Last Modified', readonly=True)
    last_sync_date = fields.Datetime(string='Last Automated Sync', readonly=True)
    knowledge_article_id = fields.Many2one('knowledge.article', string='Linked Knowledge Article')
    document_folder_id = fields.Many2one('documents.document', string='Linked Documents Folder')
    living_doc_summary = fields.Html(string='Living Architecture & Telemetry Card', readonly=True)

    # Improvements & Backlog
    improvement_ids = fields.One2many('al2c.tech.asset.improvement', 'asset_id', string='Improvement Backlog')
    improvement_count = fields.Integer(string='Total Improvements', compute='_compute_improvement_counts')
    p0_improvement_count = fields.Integer(string='P0 Blockers', compute='_compute_improvement_counts')
    p1_improvement_count = fields.Integer(string='P1 High Priority', compute='_compute_improvement_counts')

    @api.depends('improvement_ids', 'improvement_ids.priority', 'improvement_ids.state')
    def _compute_improvement_counts(self):
        for record in self:
            active_items = record.improvement_ids.filtered(lambda i: i.state not in ['cancelled', 'verified'])
            record.improvement_count = len(active_items)
            record.p0_improvement_count = len(active_items.filtered(lambda i: i.priority == 'P0'))
            record.p1_improvement_count = len(active_items.filtered(lambda i: i.priority == 'P1'))

    def action_scan_and_sync_git(self):
        """Scans local git repository, reads branches, commits, dirty files, and LOC."""
        for record in self:
            path = record.repo_path
            if not path or not os.path.exists(path):
                raise UserError(_("Repository path does not exist: %s") % path)

            vals = {}
            # Git Branch
            try:
                vals['git_branch'] = subprocess.check_output(
                    ['git', '-C', path, 'rev-parse', '--abbrev-ref', 'HEAD'],
                    text=True, stderr=subprocess.DEVNULL
                ).strip()
            except Exception:
                vals['git_branch'] = 'unknown'

            # Git Commit HEAD
            try:
                commit_info = subprocess.check_output(
                    ['git', '-C', path, 'log', '-1', '--format=%H%x1f%an%x1f%ci%x1f%s'],
                    text=True, stderr=subprocess.DEVNULL
                ).strip().split('\x1f')
                vals['git_commit_full'] = commit_info[0]
                vals['git_commit'] = commit_info[0][:9]
                vals['git_commit_author'] = commit_info[1]
                # parse timestamp
                dt_str = commit_info[2][:19]
                try:
                    vals['git_commit_date'] = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    vals['git_commit_date'] = fields.Datetime.now()
                vals['git_commit_message'] = commit_info[3]
            except Exception:
                vals['git_commit'] = 'none'
                vals['git_commit_full'] = False
                vals['git_commit_author'] = 'unknown'
                vals['git_commit_date'] = fields.Datetime.now()
                vals['git_commit_message'] = 'No commit found'

            # Git status (dirty / uncommitted files)
            try:
                status_lines = subprocess.check_output(
                    ['git', '-C', path, 'status', '--porcelain'],
                    text=True, stderr=subprocess.DEVNULL
                ).strip().splitlines()
                vals['uncommitted_files_count'] = len(status_lines)
                vals['is_dirty'] = len(status_lines) > 0
            except Exception:
                vals['uncommitted_files_count'] = 0
                vals['is_dirty'] = False

            # Velocity: 30-day commits
            try:
                vals['recent_commits_30d'] = int(subprocess.check_output(
                    ['git', '-C', path, 'rev-list', '--count', '--since=30.days', 'HEAD'],
                    text=True, stderr=subprocess.DEVNULL
                ).strip())
            except Exception:
                vals['recent_commits_30d'] = 0

            # LOC and code metrics
            loc_metrics = record._compute_loc_and_files(path)
            vals.update(loc_metrics)

            # Document freshness
            doc_freshness = record._evaluate_doc_freshness(record.primary_doc_path)
            vals.update(doc_freshness)

            vals['last_sync_date'] = fields.Datetime.now()
            record.write(vals)

            # Chain evaluation & doc card sync
            record.action_evaluate_estimation_and_risk()
            record.action_sync_documents_and_knowledge()

        return True

    def _compute_loc_and_files(self, path):
        """Scans tracked files and calculates code, test, and doc LOC."""
        p = Path(path)
        code_exts = {'.py', '.js', '.dart', '.ts', '.tsx', '.jsx', '.scss', '.css', '.xml', '.html', '.sh', '.sql', '.yaml', '.yml'}
        test_patterns = ['test', 'tests', 'spec']
        doc_exts = {'.md', '.rst', '.txt', '.adoc'}

        code_lines = 0
        test_lines = 0
        doc_lines = 0
        total_files = 0

        # Try git ls-files first
        try:
            files = subprocess.check_output(
                ['git', '-C', path, 'ls-files'],
                text=True, stderr=subprocess.DEVNULL
            ).splitlines()
        except Exception:
            files = []

        # If submodule or subfolder has files (like zencode-ent/router)
        router_path = p / 'router'
        if router_path.is_dir() and (router_path / '.git').exists():
            try:
                sub_files = subprocess.check_output(
                    ['git', '-C', str(router_path), 'ls-files'],
                    text=True, stderr=subprocess.DEVNULL
                ).splitlines()
                files.extend(['router/' + f for f in sub_files])
            except Exception:
                pass

        total_files = len(files)
        # Fast sampling / line counter (limit to max 5000 files to maintain <2s response)
        for f in files[:8000]:
            fp = p / f
            if not fp.is_file():
                continue
            ext = fp.suffix.lower()
            is_test = any(tp in f.lower() for tp in test_patterns)
            
            # Fast line count
            try:
                lines = sum(1 for _ in open(fp, 'rb'))
            except Exception:
                lines = 0

            if ext in doc_exts or 'readme' in f.lower() or 'srs' in f.lower() or 'adr' in f.lower():
                doc_lines += lines
            elif is_test:
                test_lines += lines
            elif ext in code_exts:
                code_lines += lines

        test_ratio = round(test_lines / max(1, code_lines), 3)

        return {
            'total_files_count': total_files,
            'loc_code': code_lines,
            'loc_test': test_lines,
            'loc_docs': doc_lines,
            'test_coverage_ratio': test_ratio,
        }

    def _evaluate_doc_freshness(self, doc_path):
        if not doc_path or not os.path.exists(doc_path):
            return {
                'doc_freshness': 'missing',
                'doc_last_modified': False,
            }
        try:
            mtime = os.path.getmtime(doc_path)
            doc_date = datetime.datetime.fromtimestamp(mtime)
            delta_days = (datetime.datetime.now() - doc_date).days
            if delta_days <= 7:
                freshness = 'fresh'
            elif delta_days <= 30:
                freshness = 'adequate'
            else:
                freshness = 'stale'
            return {
                'doc_freshness': freshness,
                'doc_last_modified': doc_date,
            }
        except Exception:
            return {
                'doc_freshness': 'missing',
                'doc_last_modified': False,
            }

    def action_evaluate_estimation_and_risk(self):
        """Calculates effort estimation (man-days) and composite risk score (0-100)."""
        for record in self:
            # 1. Estimation
            loc = record.loc_code or 0
            tests = record.loc_test or 0
            total_loc = loc + tests

            # Enterprise COCOMO heuristic: 180 LOC/day base productivity
            complexity_factors = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.25,
                'very_high': 1.5,
            }
            factor = complexity_factors.get(record.complexity_rating, 1.0)
            man_days = round((loc / 180.0) * factor, 1)

            # Sprint cycle horizon based on commits in 30d
            velocity = record.recent_commits_30d or 1
            # Weeks to deliver next major release increment
            delivery_weeks = round(max(2.0, (record.uncommitted_files_count / max(1.0, velocity * 0.2))), 1)

            # 2. Risk Calculation
            risk_score = 0.0
            factors = []

            # Factor A: Dirty files debt
            dirty = record.uncommitted_files_count or 0
            if dirty > 100:
                risk_score += 35.0
                factors.append(_("Critical uncommitted changes: %d dirty files in working tree.") % dirty)
            elif dirty > 20:
                risk_score += 20.0
                factors.append(_("High WIP debt: %d uncommitted files.") % dirty)
            elif dirty > 0:
                risk_score += 5.0
                factors.append(_("Minor active WIP: %d uncommitted files.") % dirty)

            # Factor B: Test coverage deficit
            ratio = record.test_coverage_ratio or 0.0
            if ratio < 0.2:
                risk_score += 30.0
                factors.append(_("Severe test deficit: Test/code ratio is %.1f%% (minimum recommended is 50%%).") % (ratio * 100))
            elif ratio < 0.5:
                risk_score += 15.0
                factors.append(_("Moderate test coverage: Test/code ratio is %.1f%%.") % (ratio * 100))
            else:
                factors.append(_("Robust test suite: Test/code ratio is %.1f%%.") % (ratio * 100))

            # Factor C: Specification Freshness
            if record.doc_freshness == 'missing':
                risk_score += 25.0
                factors.append(_("Missing primary specification or SRS documentation."))
            elif record.doc_freshness == 'stale':
                risk_score += 15.0
                factors.append(_("Stale primary specification (last modified >30 days ago)."))
            elif record.doc_freshness == 'adequate':
                risk_score += 5.0

            # Factor D: Architectural Drift
            if record.architectural_drift == 'divergent':
                risk_score += 30.0
                factors.append(_("Architectural divergence detected against clean core guidelines."))
            elif record.architectural_drift == 'minor_drift':
                risk_score += 12.0
                factors.append(_("Minor architectural drift detected."))

            # Factor E: Commit Stagnation
            if record.recent_commits_30d == 0:
                risk_score += 15.0
                factors.append(_("Repository inactivity: 0 commits in the last 30 days."))

            risk_score = min(100.0, round(risk_score, 1))

            if risk_score >= 75.0:
                risk_level = 'critical'
            elif risk_score >= 50.0:
                risk_level = 'high'
            elif risk_score >= 25.0:
                risk_level = 'medium'
            else:
                risk_level = 'low'

            record.write({
                'estimated_effort_man_days': man_days,
                'estimated_delivery_weeks': delivery_weeks,
                'tech_debt_score': round(min(100.0, (dirty * 0.4) + (max(0, 0.5 - ratio) * 60)), 1),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': "\n• ".join([""] + factors) if factors else _("No elevated risk factors detected."),
            })

        return True

    def action_generate_improvement_backlog(self):
        """Synthesizes structured candidate Backlog v2 improvements for this technology asset."""
        improvement_model = self.env['al2c.tech.asset.improvement']
        for record in self:
            existing_codes = set(record.improvement_ids.mapped('item_code'))
            items_to_create = []

            # Rule 1: High uncommitted dirty files
            if record.uncommitted_files_count > 10:
                code = f"AL2C-{record.code}-WIP01"
                if code not in existing_codes:
                    items_to_create.append({
                        'asset_id': record.id,
                        'name': f"Quarantine and Reconcile {record.uncommitted_files_count} Dirty Files",
                        'item_code': code,
                        'priority': 'P1',
                        'category': 'architecture',
                        'risk_level': 'R1',
                        'description': f"The working directory in {record.repo_path} has {record.uncommitted_files_count} uncommitted dirty files. Reconcile or branch them to prevent working-tree corruption.",
                        'definition_of_done': f"git status --porcelain reports 0 untracked/dirty files or segregated into clean topic branches.",
                        'target_file_path': record.repo_path,
                        'verification_command': f"git -C {record.repo_path} status --short",
                        'estimated_hours': 8.0,
                    })

            # Rule 2: Test coverage deficit
            if (record.test_coverage_ratio or 0.0) < 0.5:
                code = f"AL2C-{record.code}-TEST01"
                if code not in existing_codes:
                    items_to_create.append({
                        'asset_id': record.id,
                        'name': f"Expand Automated Regression Test Suite to reach >= 50% Coverage",
                        'item_code': code,
                        'priority': 'P0' if (record.test_coverage_ratio or 0.0) < 0.2 else 'P1',
                        'category': 'testing',
                        'risk_level': 'R1',
                        'description': f"Current test-to-code ratio is {(record.test_coverage_ratio or 0.0)*100:.1f}%. Add unit and integration tests to ensure automated verification gates pass consistently.",
                        'definition_of_done': f"Automated test suite executes with 100% green assertions and test LOC >= 50% of code LOC.",
                        'target_file_path': f"{record.repo_path}/tests",
                        'verification_command': f"pytest {record.repo_path}/tests",
                        'estimated_hours': 16.0,
                    })

            # Rule 3: Living specification freshness
            if record.doc_freshness in ['stale', 'missing']:
                code = f"AL2C-{record.code}-DOC01"
                if code not in existing_codes:
                    items_to_create.append({
                        'asset_id': record.id,
                        'name': f"Synchronize Living Architecture Specification (SRS/ADR) with Git HEAD",
                        'item_code': code,
                        'priority': 'P1',
                        'category': 'docs',
                        'risk_level': 'R0',
                        'description': f"Primary specification at {record.primary_doc_path or 'N/A'} is {record.doc_freshness}. Update architecture documents, system boundaries, and backlog items to match active git commits.",
                        'definition_of_done': f"SRS/ADR document updated with current system state and verified against codebase manifest.",
                        'target_file_path': record.primary_doc_path or f"{record.repo_path}/README.md",
                        'verification_command': f"test -f {record.primary_doc_path or f'{record.repo_path}/README.md'}",
                        'estimated_hours': 6.0,
                    })

            # Rule 4: Domain specific improvements
            if record.category == 'platform_core':
                code = f"AL2C-{record.code}-CORE01"
                if code not in existing_codes:
                    items_to_create.append({
                        'asset_id': record.id,
                        'name': "Sovereign Dual-Bundle SCSS Dark Mode & Zero Bare White Surfaces Audit",
                        'item_code': code,
                        'priority': 'P0',
                        'category': 'unslop',
                        'risk_level': 'R1',
                        'description': "Verify that all custom enterprise themes register dedicated web.assets_web_dark bundles with root CSS tokens and zero bare white hardcoded surfaces.",
                        'definition_of_done': "Playwright headless audit confirms canvas RGB(7,11,20) and control panel RGB(15,23,42) on dark mode.",
                        'target_file_path': f"{record.repo_path}/enterprise/insilos_theme_genesis",
                        'verification_command': "python3 tools/sync_all_pods_and_reload.py --verify",
                        'estimated_hours': 12.0,
                    })
            elif record.category == 'mobile_client':
                code = f"AL2C-{record.code}-HUD01"
                if code not in existing_codes:
                    items_to_create.append({
                        'asset_id': record.id,
                        'name': "Industrial Telemetry HUD 60fps Optimization & Cold Start Benchmark",
                        'item_code': code,
                        'priority': 'P1',
                        'category': 'performance',
                        'risk_level': 'R1',
                        'description': "Benchmark industrial polycondensation train HUD rendering performance and ensure cold start time is under 1200ms on edge devices.",
                        'definition_of_done': "flutter test mobo_vert_shell/test/e2e_peek_polycondensation_uat_test.dart passes 100% with 0 frame drops.",
                        'target_file_path': f"{record.repo_path}/mobo_vert_shell",
                        'verification_command': f"flutter test mobo_vert_shell/test",
                        'estimated_hours': 10.0,
                    })
            elif record.category == 'ai_swarm':
                code = f"AL2C-{record.code}-FLEET01"
                if code not in existing_codes:
                    items_to_create.append({
                        'asset_id': record.id,
                        'name': "Multi-Account Autonomous Quota Circuit Breaker & Fallback Resilience",
                        'item_code': code,
                        'priority': 'P0',
                        'category': 'security',
                        'risk_level': 'R2',
                        'description': "Ensure fleet router automatically cools down quota-exhausted Claude Opus nodes and transparently falls back to Gemini 3.8 Flash High without job loss.",
                        'definition_of_done': "pytest tests/test_fleet_routing.py passes 33/33 tests green with active service status.",
                        'target_file_path': f"{record.repo_path}/router/fleet_manager.py",
                        'verification_command': "curl -s http://localhost:7777/api/fleet/status",
                        'estimated_hours': 8.0,
                    })

            for item_vals in items_to_create:
                improvement_model.create(item_vals)

        return True

    def action_sync_documents_and_knowledge(self):
        """Generates or updates Odoo knowledge.article and documents.document folder for living documentation."""
        knowledge_model = self.env['knowledge.article'].sudo()
        documents_model = self.env['documents.document'].sudo()

        for record in self:
            # 1. Knowledge Article Root Workspace
            root_article = knowledge_model.search([('name', '=', 'Technology Assets & Repositories')], limit=1)
            if not root_article:
                root_article = knowledge_model.create({
                    'name': 'Technology Assets & Repositories',
                    'icon': '💻',
                    'internal_permission': 'write',
                    'sequence': 10,
                    'body': '<h1>Technology Assets & Repositories</h1><p>Living architectural registry, estimation telemetry, and continuous improvement backlogs synchronized directly from Git HEAD.</p>',
                })

            # 2. Child Article for this Asset
            article_name = f"{record.name} ({record.code}) — Living Architecture"
            article = record.knowledge_article_id
            if not article or not article.exists():
                article = knowledge_model.search([('name', '=', article_name)], limit=1)

            # Build living rich HTML body
            risk_badge_color = {
                'low': '#10b981',
                'medium': '#f59e0b',
                'high': '#f97316',
                'critical': '#ef4444',
            }.get(record.risk_level, '#6b7280')

            freshness_badge = {
                'fresh': '🟢 Fresh (<7d)',
                'adequate': '🟡 Adequate (<30d)',
                'stale': '🔴 Stale (>30d)',
                'missing': '⚪ Missing',
            }.get(record.doc_freshness, 'Unknown')

            improvements_html = "".join([
                f"<tr><td><code>{item.item_code}</code></td><td><b>{item.priority}</b></td><td>{item.name}</td><td>{item.state}</td></tr>"
                for item in record.improvement_ids[:8]
            ]) or "<tr><td colspan='4'><i>No active improvement items queued.</i></td></tr>"

            body_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 20px;">
                    <div>
                        <h1 style="margin: 0; font-size: 24px; color: #0f172a;">{record.name}</h1>
                        <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Code: <b>{record.code}</b> | Category: {dict(record._fields['category'].selection).get(record.category)}</p>
                    </div>
                    <div>
                        <span style="background-color: {risk_badge_color}; color: #ffffff; padding: 6px 14px; border-radius: 9999px; font-weight: 600; font-size: 12px; text-transform: uppercase;">
                            Risk: {record.risk_level} ({record.risk_score} / 100)
                        </span>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px;">
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Active Branch</div>
                        <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 4px;"><code>{record.git_branch or 'N/A'}</code></div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Latest Commit (HEAD)</div>
                        <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 4px;"><code>{record.git_commit or 'none'}</code></div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Working Tree Cleanliness</div>
                        <div style="font-size: 14px; font-weight: 700; color: {'#ef4444' if record.is_dirty else '#10b981'}; margin-top: 4px;">
                            {'⚠️ ' + str(record.uncommitted_files_count) + ' Dirty Files' if record.is_dirty else '✅ Clean Tree'}
                        </div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Spec Freshness</div>
                        <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 4px;">{freshness_badge}</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                        <h3 style="margin-top: 0; font-size: 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">📊 Estimation & Code Sizing</h3>
                        <table style="width: 100%; font-size: 13px; line-height: 1.8;">
                            <tr><td style="color: #64748b;">Production Code LOC:</td><td><b>{record.loc_code:,}</b> lines</td></tr>
                            <tr><td style="color: #64748b;">Test Suite LOC:</td><td><b>{record.loc_test:,}</b> lines</td></tr>
                            <tr><td style="color: #64748b;">Test / Code Ratio:</td><td><b>{(record.test_coverage_ratio or 0)*100:.1f}%</b></td></tr>
                            <tr><td style="color: #64748b;">Documentation LOC:</td><td><b>{record.loc_docs:,}</b> lines</td></tr>
                            <tr><td style="color: #64748b;">Estimated Size (Man-Days):</td><td><b style="color: #0284c7;">{record.estimated_effort_man_days:,.1f}</b> man-days</td></tr>
                            <tr><td style="color: #64748b;">Release Cycle Horizon:</td><td><b>{record.estimated_delivery_weeks:.1f}</b> weeks</td></tr>
                        </table>
                    </div>

                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                        <h3 style="margin-top: 0; font-size: 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">🛡️ Risk & Technical Debt Profile</h3>
                        <div style="font-size: 13px; margin-bottom: 12px;">
                            <span style="color: #64748b;">Composite Risk:</span> <b>{record.risk_score} / 100</b> | 
                            <span style="color: #64748b;">Tech Debt Score:</span> <b>{record.tech_debt_score} / 100</b>
                        </div>
                        <div style="font-size: 12px; color: #334155; line-height: 1.6; background: #fff1f2; border: 1px solid #fecdd3; padding: 10px; border-radius: 6px;">
                            <b>Identified Risk Factors:</b><br/>
                            {record.risk_factors or 'None'}
                        </div>
                    </div>
                </div>

                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                    <h3 style="margin-top: 0; font-size: 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">🚀 Autonomous Improvement Backlog</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px;">
                        <thead>
                            <tr style="text-align: left; background: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                                <th style="padding: 6px 8px;">Code</th>
                                <th style="padding: 6px 8px;">Priority</th>
                                <th style="padding: 6px 8px;">Title</th>
                                <th style="padding: 6px 8px;">State</th>
                            </tr>
                        </thead>
                        <tbody>
                            {improvements_html}
                        </tbody>
                    </table>
                </div>
            </div>
            """

            if not article:
                article = knowledge_model.create({
                    'name': article_name,
                    'parent_id': root_article.id,
                    'icon': '📘',
                    'internal_permission': 'write',
                    'body': body_html,
                })
            else:
                article.write({
                    'parent_id': root_article.id,
                    'body': body_html,
                })

            # 3. Documents Folder
            root_folder = documents_model.search([('name', '=', 'Tech Assets'), ('type', '=', 'folder')], limit=1)
            if not root_folder:
                root_folder = documents_model.create({
                    'name': 'Tech Assets',
                    'type': 'folder',
                    'access_internal': 'view',
                    'sequence': 70,
                })

            asset_folder = record.document_folder_id
            if not asset_folder or not asset_folder.exists():
                asset_folder = documents_model.search([('name', '=', record.name), ('folder_id', '=', root_folder.id), ('type', '=', 'folder')], limit=1)
                if not asset_folder:
                    asset_folder = documents_model.create({
                        'name': record.name,
                        'type': 'folder',
                        'folder_id': root_folder.id,
                        'access_internal': 'view',
                    })

            record.write({
                'knowledge_article_id': article.id,
                'document_folder_id': asset_folder.id,
                'living_doc_summary': body_html,
            })

        return True

    def action_full_telemetry_cycle(self):
        """Runs the entire telemetry cycle: Git scan, risk evaluation, backlog generation, doc sync."""
        self.action_scan_and_sync_git()
        self.action_generate_improvement_backlog()
        self.action_sync_documents_and_knowledge()
        return True


class Al2cTechAssetImprovement(models.Model):
    _name = 'al2c.tech.asset.improvement'
    _description = 'Technology Asset Improvement Request / Backlog Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority asc, risk_level desc, id desc'

    name = fields.Char(string='Title', required=True, tracking=True)
    item_code = fields.Char(string='Backlog Code', required=True, index=True, tracking=True)
    asset_id = fields.Many2one('al2c.tech.asset', string='Technology Asset', required=True, ondelete='cascade', tracking=True)
    priority = fields.Selection([
        ('P0', 'P0 - Blocker / Critical'),
        ('P1', 'P1 - High Priority'),
        ('P2', 'P2 - Medium Priority'),
    ], string='Priority', default='P1', required=True, tracking=True)
    category = fields.Selection([
        ('architecture', 'Architecture & Clean Core'),
        ('security', 'Security & Compliance'),
        ('performance', 'Performance & Harness Optimization'),
        ('testing', 'Test Coverage & Regression Gates'),
        ('docs', 'Living Documentation & SRS Sync'),
        ('unslop', 'Anti-Slop & SCSS Invariant'),
    ], string='Category', default='architecture', required=True)
    risk_level = fields.Selection([
        ('R0', 'R0 - Low Risk (Docs/Config)'),
        ('R1', 'R1 - Moderate Risk (Standard Feature)'),
        ('R2', 'R2 - High Risk (Core/Architecture)'),
        ('R3', 'R3 - Critical Risk (Auth/Billing)'),
    ], string='Risk Grade', default='R1', required=True)
    state = fields.Selection([
        ('draft', 'Draft / Discovered'),
        ('queued', 'Queued for Autonomous Swarm'),
        ('in_progress', 'In Progress'),
        ('verified', 'Verified / Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    description = fields.Text(string='Problem & Context')
    definition_of_done = fields.Text(string='Definition of Done (DoD Assertion)', required=True)
    target_file_path = fields.Char(string='Target File / Component')
    verification_command = fields.Char(string='Automated Verification Command')
    estimated_hours = fields.Float(string='Estimated Hours', default=4.0)

    backlog_v2_line = fields.Char(string='Backlog v2 Formatted Line', compute='_compute_backlog_v2_line', store=True)

    @api.depends('item_code', 'priority', 'category', 'name', 'definition_of_done', 'asset_id.code', 'target_file_path', 'verification_command', 'risk_level')
    def _compute_backlog_v2_line(self):
        for record in self:
            track = 'plan'
            if record.category in ['testing']:
                track = 'tests'
            elif record.category in ['security']:
                track = 'security'
            elif record.category in ['docs']:
                track = 'docs'
            elif record.category in ['performance', 'unslop']:
                track = 'plan'

            meta = f"repo={record.asset_id.code or 'O20'} path={record.target_file_path or '.'} verify=\"{record.verification_command or 'pytest'}\" risk={record.risk_level or 'R1'}"
            record.backlog_v2_line = f"- [ ] [{record.item_code}][{record.priority}][{track}] {record.name} — DoD: {record.definition_of_done} <!-- meta: {meta} -->"

    def action_queue_for_swarm(self):
        self.write({'state': 'queued'})

    def action_mark_verified(self):
        self.write({'state': 'verified'})
