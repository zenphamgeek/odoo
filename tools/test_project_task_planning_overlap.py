#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/test_project_task_planning_overlap.py
===========================================
Regression test for project.task planning_overlap computation
and web_read_group query construction with TableSQL in Odoo 20 / Insilos.
"""
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import odoo
from odoo.tools import config
from odoo.modules.registry import Registry


class TestProjectTaskPlanningOverlap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        conf_file = REPO_ROOT / 'insilos.conf'
        if not conf_file.exists():
            conf_file = REPO_ROOT / 'odoo.conf'
        config.parse_config(['-c', str(conf_file), '-d', 'insilos20_dev'])

    def test_planning_overlap_computation_insilos20_dev(self):
        self._verify_planning_overlap('insilos20_dev')

    def test_planning_overlap_computation_odoo20_dev(self):
        self._verify_planning_overlap('odoo20_dev')

    def _verify_planning_overlap(self, dbname):
        registry = Registry(dbname)
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
            Task = env['project.task']
            tasks = Task.search([], limit=10)
            if not tasks:
                # Create sample task if none exists
                project = env['project.project'].search([], limit=1)
                if not project:
                    project = env['project.project'].create({'name': 'Test Project Overlap'})
                tasks = Task.create({
                    'name': 'Test Overlap Task',
                    'project_id': project.id,
                    'planned_date_begin': odoo.fields.Datetime.now(),
                    'date_deadline': odoo.fields.Datetime.add(odoo.fields.Datetime.now(), days=2),
                    'allocated_hours': 8.0,
                })

            # 1. Directly invoke the compute method that triggers _fetch_planning_overlap
            tasks._compute_planning_overlap()

            # 2. Invoke web_read specifying planning_overlap
            read_res = tasks.web_read({'name': {}, 'planning_overlap': {}, 'planned_date_begin': {}, 'date_deadline': {}})
            self.assertIsInstance(read_res, list)
            self.assertGreater(len(read_res), 0)

            # 3. Invoke web_read_group with unfold_read_specification (exact web client pattern)
            group_res = Task.web_read_group(
                domain=[],
                groupby=['stage_id'],
                auto_unfold=True,
                unfold_read_specification={
                    'name': {},
                    'stage_id': {},
                    'planning_overlap': {},
                    'planned_date_begin': {},
                    'date_deadline': {},
                }
            )
            self.assertIn('groups', group_res)
            print(f"✓ [{dbname}] Verified planning_overlap & web_read_group: {len(tasks)} tasks processed successfully.")


if __name__ == '__main__':
    unittest.main()
