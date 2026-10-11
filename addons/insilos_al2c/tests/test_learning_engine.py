# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from datetime import date, timedelta


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cLearningEngine(TransactionCase):
    """
    Test suite for AL2C-HLP-002: Ticket & Win/Loss Pattern Mining.
    Synthesizes recurring customer friction points into actionable product enhancement tickets.
    DoD: Monthly mining report produces >= 5 actionable product tickets with target SKUs and remediations.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Da Nang Logistics Corp',
            'email': 'ops@dananglogistics.vn',
        })
        cls.team = cls.env['helpdesk.team'].create({
            'name': 'Enterprise Support',
        })

        # Sample helpdesk tickets
        cls.env['helpdesk.ticket'].create([
            {
                'name': 'Lỗi ký số XML Nghị định 70 khi xuất nhiều hóa đơn',
                'description': 'Xuất hàng loạt 300 hóa đơn bị timeout cổng CQT.',
                'partner_id': cls.customer.id,
                'team_id': cls.team.id,
            },
            {
                'name': 'Đồng bộ giờ công offline trên app mobile bị đè',
                'description': 'Kỹ sư ngoài hiện trường bị mất kết nối mạng khi chấm công.',
                'partner_id': cls.customer.id,
                'team_id': cls.team.id,
            },
        ])

        # Sample lost CRM leads
        cls.env['crm.lead'].create([
            {
                'name': 'Lost Deal - Pricing & Token Quota Lockout',
                'partner_id': cls.customer.id,
                'active': False,
                'al2c_qualification_state': 'disqualified',
                'al2c_sentiment': 'negative',
            },
            {
                'name': 'Lost Deal - Slow Quotation Turnaround',
                'partner_id': cls.customer.id,
                'active': False,
                'al2c_qualification_state': 'disqualified',
                'al2c_sentiment': 'negative',
            },
        ])

    def test_pattern_mining_synthesizes_at_least_5_tickets(self):
        """Pattern mining engine produces >= 5 actionable product tickets with valid remediation plans."""
        engine = self.env['al2c.learning.engine']
        today = date.today()
        start = today - timedelta(days=30)

        report = engine.mine_patterns(period_start=start, period_end=today)
        self.assertTrue(report, "Mining engine must return a created al2c.mining.report record.")
        self.assertEqual(report.state, 'published')
        self.assertGreaterEqual(
            report.product_ticket_count,
            5,
            "DoD check: Monthly mining report must produce >= 5 actionable product tickets.",
        )
        self.assertEqual(len(report.product_ticket_ids), report.product_ticket_count)

        # Verify ticket details and SKU linkage
        categories = set(report.product_ticket_ids.mapped('category'))
        self.assertTrue({'billing', 'performance', 'mobile_sync', 'pricing'}.issubset(categories))

        for ticket in report.product_ticket_ids:
            self.assertTrue(ticket.name, "Ticket must have a descriptive title.")
            self.assertTrue(ticket.proposed_remediation, "Ticket must specify an actionable engineering remediation.")
            self.assertTrue(ticket.root_cause_analysis, "Ticket must document root cause analysis.")
            self.assertIn(ticket.priority, ['0', '1', '2', '3'])
            self.assertEqual(ticket.state, 'backlog')

        # Verify Markdown summary contains table and recommended actions
        self.assertIn("# Pattern Mining Report", report.summary_markdown)
        self.assertIn("## Synthesized Product Enhancement Backlog", report.summary_markdown)
        self.assertIn("Decree 70", report.summary_markdown)
        self.assertIn("Mojo", report.summary_markdown)

    def test_product_ticket_lifecycle(self):
        """Product tickets can be transitioned from backlog to grooming and engineering."""
        engine = self.env['al2c.learning.engine']
        report = engine.mine_patterns()
        ticket = report.product_ticket_ids[0]

        ticket.write({'state': 'grooming'})
        self.assertEqual(ticket.state, 'grooming')

        ticket.write({'state': 'in_progress'})
        self.assertEqual(ticket.state, 'in_progress')
