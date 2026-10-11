# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cDiscoveryBriefing(TransactionCase):
    """
    Test suite for AL2C-CRM-006: Automated Discovery Meeting Briefing Generator on calendar.event.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Viet Thang Industrial Garments',
            'email': 'procurement@vietthang.vn',
        })
        cls.lead = cls.env['crm.lead'].create({
            'name': 'ERP Enterprise & Supply Chain Modernization',
            'partner_id': cls.customer.id,
            'al2c_bant_need': 'Legacy ERP is crashing during month-end close; need real-time WIP tracking.',
            'al2c_bant_authority_name': 'Tran Van Thang (General Director)',
            'al2c_meddicc_metrics': 'Eliminate 4-day closing delay and reduce inventory discrepancies by 40%.',
        })
        cls.event = cls.env['calendar.event'].create({
            'name': 'Executive Discovery Call - Viet Thang Garments',
            'start': datetime.now() + timedelta(days=1),
            'stop': datetime.now() + timedelta(days=1, hours=1),
            'opportunity_id': cls.lead.id,
            'partner_ids': [(6, 0, [cls.customer.id])],
        })

    def test_discovery_briefing_generation(self):
        """Briefing generator compiles customer pain points, ROI metrics, and reference cases."""
        self.assertFalse(self.event.al2c_briefing_generated)
        self.assertFalse(self.event.al2c_briefing_note)

        self.event.action_generate_discovery_briefing()

        self.assertTrue(self.event.al2c_briefing_generated)
        self.assertIn("Executive Discovery Briefing Pack", self.event.al2c_briefing_note)
        self.assertIn("Legacy ERP is crashing", self.event.al2c_briefing_note)
        self.assertIn("Tran Van Thang", self.event.al2c_briefing_note)
        self.assertIn("Eliminate 4-day closing delay", self.event.al2c_briefing_note)

        # Confirm briefing was posted to calendar event and crm lead chatter
        event_messages = self.event.message_ids.mapped('body')
        self.assertTrue(any("Executive Discovery Briefing Pack" in m for m in event_messages))
        lead_messages = self.lead.message_ids.mapped('body')
        self.assertTrue(any("Executive Discovery Briefing Pack" in m for m in lead_messages))
