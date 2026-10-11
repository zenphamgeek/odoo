# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cHelpdeskTriage(TransactionCase):
    """
    Test suite for AL2C-HLP-001: Helpdesk L1 Autonomous Triage & Knowledge Resolution on helpdesk.ticket.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Mekong AgriTech Ltd',
            'email': 'support@mekongagri.vn',
        })
        cls.team = cls.env['helpdesk.team'].create({
            'name': 'Insilos Enterprise Support Team',
        })

    def test_billing_inquiry_grounded_resolution(self):
        """Inbound Decree 70 e-invoice question is categorized as billing and resolved autonomously."""
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'Làm thế nào để tra cứu mã hóa đơn điện tử Nghị định 70?',
            'description': 'Chúng tôi cần kiểm tra tính hợp lệ của hóa đơn trên cổng Tổng cục Thuế.',
            'partner_id': self.customer.id,
            'team_id': self.team.id,
        })
        ticket.action_autonomous_triage()
        self.assertEqual(ticket.al2c_triage_category, 'billing')
        self.assertTrue(ticket.al2c_autonomous_resolved)
        self.assertGreaterEqual(ticket.al2c_confidence_score, 80.0)

    def test_software_bug_escalation_to_l2(self):
        """Critical bug ticket is categorized as software defect and routed to L2 with activity."""
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'Gặp lỗi traceback 500 khi xác nhận đơn hàng lớn',
            'description': 'Hệ thống báo exception crash khi bấm button_confirm.',
            'partner_id': self.customer.id,
            'team_id': self.team.id,
        })
        ticket.action_autonomous_triage()
        self.assertEqual(ticket.al2c_triage_category, 'bug')
        self.assertFalse(ticket.al2c_autonomous_resolved)

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'helpdesk.ticket'),
            ('res_id', '=', ticket.id),
        ])
        self.assertTrue(activities, "Software bug ticket must create L2 investigation activity.")
        self.assertIn("L2 Engineering Investigation", activities[0].summary)
