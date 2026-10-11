# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cProjectRiskSentinel(TransactionCase):
    """
    Test suite for AL2C-PRJ-003: Autonomous Project Risk Sentinel on project.project.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Hanoi Precision Tech',
            'email': 'pm@hanoiprecision.vn',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Customer Implementation Project',
            'partner_id': cls.customer.id,
        })
        cls.milestone1 = cls.env['project.milestone'].create({
            'name': 'Milestone 1: Architecture Blueprint',
            'project_id': cls.project.id,
            'deadline': date.today() + timedelta(days=15),
        })

    def test_nominal_project_stays_green(self):
        """Nominal project with future milestones and no timesheet overrun evaluates to Green."""
        self.project.action_evaluate_project_risk()
        self.assertEqual(self.project.al2c_rag_status, 'green')
        self.assertEqual(self.project.al2c_risk_score, 0.0)

    def test_overdue_milestone_triggers_red_and_activity(self):
        """Milestone overdue by >7 days triggers Critical Red status and urgent PM alert activity."""
        self.milestone1.write({
            'deadline': date.today() - timedelta(days=10),
            'is_reached': False,
        })
        self.project.action_evaluate_project_risk()
        self.assertEqual(self.project.al2c_rag_status, 'red')
        self.assertGreaterEqual(self.project.al2c_risk_score, 45.0)

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'project.project'),
            ('res_id', '=', self.project.id),
        ])
        self.assertTrue(activities, "Critical Red status must create warning activity for PM.")
        self.assertIn("Sentinel RED", activities[0].summary)
