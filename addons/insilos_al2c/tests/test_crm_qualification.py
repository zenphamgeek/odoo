# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cCrmQualification(TransactionCase):
    """
    Test suite for AL2C-CRM-004: Conversational BANT/MEDDICC Qualification Loop on crm.lead.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Saigon Smart Logistics Corp',
            'email': 'procurement@saigonsmart.vn',
        })
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Inbound ERP & AI Logistics Inquiry',
            'partner_id': cls.customer.id,
            'contact_name': 'Nguyen Van Nam',
            'email_from': 'nam.nguyen@saigonsmart.vn',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Innoria ERP Implementation',
            'allow_timesheets': True,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Explore Phase Architecture Workshop',
            'project_id': cls.project.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Consultant A',
            'work_email': 'consultant.a@inno.ai.vn',
        })

    def test_bant_qualification_advances_to_sql(self):
        """Lead providing complete BANT criteria reaches SQL stage and qualified status."""
        self.assertEqual(self.lead.al2c_qualification_state, 'unqualified')
        self.assertEqual(self.lead.al2c_touch_count, 0)

        # Turn 1: Customer identifies Need and Authority
        self.lead.action_process_qualification_turn(
            extracted_data={
                'al2c_bant_need': 'Need to unify multi-warehouse WMS and automate customs reporting.',
                'al2c_bant_authority': True,
                'al2c_bant_authority_name': 'Nguyen Van Nam (CIO)',
                'al2c_meddicc_economic_buyer': 'Nguyen Van Nam (CIO)',
                'al2c_sentiment': 'positive',
            }
        )
        self.assertEqual(self.lead.al2c_touch_count, 1)
        self.assertEqual(self.lead.al2c_qualification_state, 'in_progress')
        self.assertFalse(self.lead.al2c_bant_budget)

        # Turn 2: Customer confirms Budget and Timeline
        self.lead.action_process_qualification_turn(
            extracted_data={
                'al2c_bant_budget': True,
                'al2c_bant_budget_amount': 850000000.0,
                'al2c_bant_timeline': '1_3_months',
                'al2c_meddicc_metrics': 'Reduce inventory turnover cycle by 35% and labor cost by 20%.',
                'al2c_meddicc_decision_criteria': 'Scalable API, Decree 70 e-invoice compliance, cloud hosting.',
            }
        )
        self.assertEqual(self.lead.al2c_touch_count, 2)
        self.assertEqual(self.lead.al2c_qualification_state, 'qualified')
        self.assertGreaterEqual(self.lead.al2c_qualification_score, 80.0)

        # Confirm activity created for sales executive
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'crm.lead'),
            ('res_id', '=', self.lead.id),
        ])
        self.assertTrue(activities, "Handoff activity must be scheduled for sales rep.")
        self.assertIn("Autonomous SQL Handoff", activities[0].summary)

    def test_touch_cap_relegates_to_nurture(self):
        """Reaching 3 touches without complete BANT moves lead to nurture stream."""
        lead = self.env['crm.lead'].create({
            'name': 'Casual Inquiry Without Budget',
            'partner_id': self.customer.id,
        })
        self.assertEqual(lead.al2c_touch_count, 0)

        # Touch 1
        lead.action_process_qualification_turn(message_text="Hello, we are exploring software solutions.")
        self.assertEqual(lead.al2c_touch_count, 1)
        self.assertEqual(lead.al2c_qualification_state, 'in_progress')

        # Touch 2
        lead.action_process_qualification_turn(message_text="Just browsing features right now.")
        self.assertEqual(lead.al2c_touch_count, 2)
        self.assertEqual(lead.al2c_qualification_state, 'in_progress')

        # Touch 3 (Cap reached)
        lead.action_process_qualification_turn(message_text="No budget approved yet for this year.")
        self.assertEqual(lead.al2c_touch_count, 3)
        self.assertEqual(lead.al2c_qualification_state, 'nurture')

    def test_negative_sentiment_disqualifies_immediately(self):
        """Negative sentiment marks lead disqualified immediately without wasting touches."""
        lead = self.env['crm.lead'].create({
            'name': 'Unsolicited Vendor Lead',
            'partner_id': self.customer.id,
        })
        lead.action_process_qualification_turn(message_text="Chúng tôi không có nhu cầu, xin vui lòng dừng gửi thư.")
        self.assertEqual(lead.al2c_sentiment, 'negative')
        self.assertEqual(lead.al2c_qualification_state, 'disqualified')

    def test_inbound_timesheet_reroutes_to_staging(self):
        """Inbound email with timesheet subject or attachment reroutes from crm.lead to al2c.timesheet.staging."""
        msg = {
            'subject': '[Timesheet] Weekly Log W42 - Consultant A',
            'email_from': 'consultant.a@inno.ai.vn',
            'body': '2026-10-12 | Innoria ERP Implementation | Explore Phase Architecture Workshop | 8.0 | Core development\n',
            'attachments': [('timesheet_w42.csv', b'Date,Project,Task,Hours,Description\n2026-10-12,Innoria ERP Implementation,Explore Phase Architecture Workshop,8.0,Core dev\n')],
        }
        res = self.env['crm.lead'].message_new(msg)
        self.assertEqual(res._name, 'al2c.timesheet.staging', "Timesheet email must reroute to al2c.timesheet.staging")
        self.assertEqual(res.sender_email, 'consultant.a@inno.ai.vn')
        self.assertEqual(res.state, 'parsed')
        self.assertGreaterEqual(res.total_hours, 8.0)

    def test_inbound_inquiry_creates_crm_lead(self):
        """Inbound sales inquiry email creates a crm.lead with BANT evaluation."""
        msg = {
            'subject': 'Yêu cầu tư vấn & báo giá ERP cho chuỗi bán lẻ 50 cửa hàng',
            'email_from': 'ceo@retailcorp.vn',
            'body': 'Chào Innoria, chúng tôi có ngân sách 500 triệu VND và cần triển khai trong Q1 năm tới.',
        }
        res = self.env['crm.lead'].message_new(msg)
        self.assertEqual(res._name, 'crm.lead', "General sales inquiry must create a crm.lead")
        self.assertEqual(res.name, 'Yêu cầu tư vấn & báo giá ERP cho chuỗi bán lẻ 50 cửa hàng')
        self.assertTrue(res.al2c_bant_budget, "Should auto-detect budget from message body")
        self.assertEqual(res.al2c_bant_timeline, '1_3_months')
