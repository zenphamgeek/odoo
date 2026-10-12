# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'insilos_al2c', 'tech_asset')
class TestTechAssetRegistry(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env['al2c.tech.asset']
        cls.improvement_model = cls.env['al2c.tech.asset.improvement']

        # Create test asset pointing to O20 workspace
        cls.asset_o20 = cls.asset_model.create({
            'name': 'Test O20 Core Platform',
            'code': 'TEST_O20',
            'repo_path': '/home/zen/O20',
            'category': 'platform_core',
            'tech_stack': 'Python 3.12 / Odoo 20 LTS',
            'primary_doc_path': '/home/zen/O20/AGENTS.md',
            'complexity_rating': 'very_high',
        })

    def test_01_asset_creation_and_defaults(self):
        """Verify technology asset is created with correct defaults."""
        self.assertTrue(self.asset_o20.active)
        self.assertEqual(self.asset_o20.state, 'active')
        self.assertEqual(self.asset_o20.risk_level, 'low')
        self.assertEqual(self.asset_o20.doc_freshness, 'fresh')

    def test_02_git_telemetry_scan(self):
        """Verify git telemetry scan populates branch, commit, dirty status, and LOC metrics."""
        self.asset_o20.action_scan_and_sync_git()
        self.assertTrue(self.asset_o20.git_branch)
        self.assertNotEqual(self.asset_o20.git_branch, 'unknown')
        self.assertTrue(self.asset_o20.git_commit)
        self.assertGreater(self.asset_o20.total_files_count, 0)
        self.assertGreater(self.asset_o20.loc_code, 0)
        self.assertIsNotNone(self.asset_o20.test_coverage_ratio)

    def test_03_estimation_and_risk_evaluation(self):
        """Verify estimation (man-days) and risk scoring logic."""
        self.asset_o20.write({
            'loc_code': 18000,
            'loc_test': 9000,
            'test_coverage_ratio': 0.5,
            'uncommitted_files_count': 5,
            'recent_commits_30d': 50,
            'complexity_rating': 'high',  # factor 1.25
        })
        self.asset_o20.action_evaluate_estimation_and_risk()

        # 18000 / 180 * 1.25 = 125.0 man-days
        self.assertEqual(self.asset_o20.estimated_effort_man_days, 125.0)
        self.assertGreater(self.asset_o20.estimated_delivery_weeks, 0)
        self.assertIn(self.asset_o20.risk_level, ['low', 'medium', 'high', 'critical'])

    def test_04_improvement_backlog_generation_and_metadata_v2(self):
        """Verify autonomous generation of Backlog v2 improvements."""
        self.asset_o20.write({
            'uncommitted_files_count': 45,
            'test_coverage_ratio': 0.15,  # deficit
            'doc_freshness': 'stale',
        })
        self.asset_o20.action_generate_improvement_backlog()

        improvements = self.asset_o20.improvement_ids
        self.assertGreaterEqual(len(improvements), 3)

        # Check Backlog v2 formatting
        for imp in improvements:
            self.assertTrue(imp.backlog_v2_line.startswith('- [ ] ['))
            self.assertIn('<!-- meta:', imp.backlog_v2_line)
            self.assertIn(imp.item_code, imp.backlog_v2_line)
            self.assertIn(imp.priority, imp.backlog_v2_line)

        # Check transition states
        p0_item = improvements.filtered(lambda i: i.priority == 'P0')[:1]
        if p0_item:
            p0_item.action_queue_for_swarm()
            self.assertEqual(p0_item.state, 'queued')
            p0_item.action_mark_verified()
            self.assertEqual(p0_item.state, 'verified')

    def test_05_living_doc_and_knowledge_sync(self):
        """Verify automated synchronization with Odoo knowledge.article and documents.document."""
        self.asset_o20.action_full_telemetry_cycle()

        self.assertTrue(self.asset_o20.knowledge_article_id)
        self.assertIn('TEST_O20', self.asset_o20.knowledge_article_id.name)
        self.assertIn('Living Architecture', self.asset_o20.knowledge_article_id.name)
        self.assertIn('Estimation &amp; Code Sizing', self.asset_o20.knowledge_article_id.body)

        self.assertTrue(self.asset_o20.document_folder_id)
        self.assertEqual(self.asset_o20.document_folder_id.name, self.asset_o20.name)
        self.assertEqual(self.asset_o20.document_folder_id.type, 'folder')
