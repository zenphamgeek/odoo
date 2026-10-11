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
