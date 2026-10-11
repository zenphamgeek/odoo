# -*- coding: utf-8 -*-
from unittest.mock import patch
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from .test_al2c import _isolate_dev_db


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cMailGate(TransactionCase):
    """
    Tests for AL2C-CRM-202: Dual-Mode Mail Gate (GOV-202).
    Enforces 'draft_only' trapping of autonomous outbound messages
    and reviewer approval workflow.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.agent_group = cls.env.ref('insilos_al2c.group_al2c_agent')
        cls.manager_group = cls.env.ref('sales_team.group_sale_manager')

        cls.user_agent = cls.env['res.users'].create({
            'name': 'Autonomous Outbound SDR',
            'login': 'al2c_agent_sdr',
            'email': 'sdr.agent@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id, cls.agent_group.id])],
        })
        cls.user_human_salesman = cls.env['res.users'].create({
            'name': 'Human Sales Representative',
            'login': 'human_rep',
            'email': 'human.rep@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Deal Desk Manager',
            'login': 'deal_desk_mgr',
            'email': 'mgr@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id, cls.manager_group.id])],
        })

    def test_agent_outbound_trapped_in_draft_only_mode(self):
        self.env['ir.config_parameter'].sudo().set_param('al2c.mail_mode', 'draft_only')

        mail = self.env['mail.mail'].with_user(self.user_agent).sudo().create({
            'subject': 'Cold Outbound Proposal: AI ERP Transformation',
            'email_to': 'prospect.ceo@targetcompany.vn',
            'body_html': '<p>Autonomous prospecting message</p>',
        })
        self.assertFalse(mail.al2c_trapped)

        # Trigger send
        mail.send()

        # Autonomous email must be trapped
        self.assertTrue(mail.al2c_trapped)
        self.assertIn('GOV-202', mail.al2c_trap_reason)

    def test_human_outbound_not_trapped(self):
        self.env['ir.config_parameter'].sudo().set_param('al2c.mail_mode', 'draft_only')

        mail = self.env['mail.mail'].with_user(self.user_human_salesman).sudo().create({
            'subject': 'Manual follow-up by human AE',
            'email_to': 'client@example.com',
            'body_html': '<p>Human written follow up</p>',
        })
        mail.send()
        self.assertFalse(mail.al2c_trapped)

    def test_manager_can_approve_and_send_trapped_email(self):
        self.env['ir.config_parameter'].sudo().set_param('al2c.mail_mode', 'draft_only')

        mail = self.env['mail.mail'].with_user(self.user_agent).sudo().create({
            'subject': 'Outbound pitch needing review',
            'email_to': 'prospect@example.com',
            'body_html': '<p>Reviewed pitch</p>',
        })
        mail.send()
        self.assertTrue(mail.al2c_trapped)

        # Non-manager cannot approve
        with self.assertRaises(AccessError):
            mail.with_user(self.user_human_salesman).action_approve_and_send()

        # Manager approves and sends
        mail.with_user(self.user_manager).action_approve_and_send()
        self.assertTrue(mail.al2c_approved)
        self.assertFalse(mail.al2c_trapped)

    def test_engage_mode_allows_agent_outbound(self):
        self.env['ir.config_parameter'].sudo().set_param('al2c.mail_mode', 'engage')

        mail = self.env['mail.mail'].with_user(self.user_agent).sudo().create({
            'subject': 'Verified consent inbound response',
            'email_to': 'inbound.lead@example.com',
            'body_html': '<p>Inbound response under engage mode</p>',
        })
        mail.send()
        self.assertFalse(mail.al2c_trapped)
