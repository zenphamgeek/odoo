# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError


@tagged('post_install', '-at_install', 'insilos_al2c', 'council')
class TestCouncilAdditions(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id

        cls.partner = cls.env['res.partner'].create({
            'name': 'VinTech Global Corp',
            'is_company': True,
            'email': 'procurement@vintech-example.com',
        })

        cls.agent_group = cls.env.ref('insilos_al2c.group_al2c_agent')
        cls.manager_group = cls.env.ref('sales_team.group_sale_manager')

        cls.agent_user = cls.env['res.users'].create({
            'name': 'Autonomous Deal Agent',
            'login': 'agent_deal_desk_test',
            'email': 'agent_deal@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.agent_group.id])],
        })

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Enterprise Sales Director',
            'login': 'sales_dir_test',
            'email': 'sales_dir@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.manager_group.id])],
        })

        cls.product_erp = cls.env.ref('insilos_al2c.product_erp_growth', raise_if_not_found=False)
        if not cls.product_erp:
            cls.product_erp = cls.env['product.template'].search([('default_code', '=', 'ERP-GROWTH')], limit=1)

    def test_value_case_lifecycle_and_propagation(self):
        """AL2C-VAL-101: Value Case quantification and propagation across Lead -> SO -> Project."""
        ValueCase = self.env['al2c.value.case']
        ValueDriver = self.env['al2c.value.driver']

        case = ValueCase.create({
            'name': 'VinTech ERP Modernization Value Case',
            'partner_id': self.partner.id,
            'tco_current_vnd': 1_200_000_000.0,
            'tco_future_vnd': 450_000_000.0,
        })

        # Add 2 quantitative drivers
        ValueDriver.create({
            'case_id': case.id,
            'name': 'Invoice Processing Automation',
            'category': 'efficiency',
            'annual_benefit_vnd': 300_000_000.0,
            'confidence_level': 'high',
        })
        ValueDriver.create({
            'case_id': case.id,
            'name': 'Decree 70 Compliance Penalty Risk Elimination',
            'category': 'compliance',
            'annual_benefit_vnd': 250_000_000.0,
            'confidence_level': 'high',
        })

        case._compute_metrics()
        # net_annual_benefit = (1200M - 450M) + 300M + 250M = 1,300,000,000 VND
        self.assertEqual(case.net_annual_benefit_vnd, 1_300_000_000.0)
        self.assertGreater(case.roi_percentage, 200.0)
        self.assertLess(case.payback_months, 12.0)

        case.action_quantify()
        self.assertEqual(case.state, 'quantified')

        # Link to Lead and create Sale Order
        lead = self.env['crm.lead'].create({
            'name': 'VinTech Modernization Lead',
            'partner_id': self.partner.id,
            'value_case_id': case.id,
        })
        self.assertEqual(lead.value_case_id.id, case.id)

        # Create SO linked to value case
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.manager_user.id,
            'value_case_id': case.id,
            'order_line': [(0, 0, {
                'product_id': self.product_erp.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': 450_000_000.0,
            })],
        })
        self.assertEqual(order.value_case_id.id, case.id)

        # Confirm SO and verify project inherits value_case_id
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        if order.project_ids:
            self.assertEqual(order.project_ids[:1].value_case_id.id, case.id)

        # Mark value realized post-go-live
        case.action_mark_realized()
        self.assertEqual(case.state, 'realized')

    def test_fit_to_standard_clean_core_governance(self):
        """AL2C-CRM-101: Fit-to-Standard Clean Core Scope check on quote confirmation."""
        FtsItem = self.env['al2c.fts.item']

        order = self.env['sale.order'].with_user(self.agent_user).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_erp.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': 450_000_000.0,
            })],
        })

        # Standard Class A item
        FtsItem.create({
            'sale_order_id': order.id,
            'name': 'Standard Chart of Accounts Setup',
            'clean_core_class': 'class_a',
        })

        # Agent with Deal Desk approval for TCV/commercials
        order.with_user(self.manager_user).write({'al2c_approved': True})
        # Should confirm fine with only Class A
        order.with_user(self.agent_user).action_confirm()
        self.assertEqual(order.state, 'sale')

        # Now test Class D: create another order with Class D modification
        order_d = self.env['sale.order'].with_user(self.agent_user).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_erp.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': 100_000_000.0,
            })],
        })
        fts_d = FtsItem.create({
            'sale_order_id': order_d.id,
            'name': 'Custom Patch inside core odoo/orm/models.py',
            'clean_core_class': 'class_d',
            'justification': 'Legacy procedural override attempt',
        })

        # Attempting to confirm without Architecture Board sign-off raises UserError
        with self.assertRaises(UserError) as cm:
            order_d.with_user(self.agent_user).action_confirm()
        self.assertIn("Clean-Core Prohibited", str(cm.exception))

        # Architecture board approves exception
        fts_d.with_user(self.manager_user).action_approve_class_d()
        self.assertTrue(fts_d.approved_by_architect)

        # Now confirmation succeeds
        order_d.with_user(self.manager_user).write({'al2c_approved': True})
        order_d.with_user(self.agent_user).action_confirm()
        self.assertEqual(order_d.state, 'sale')

    def test_commercial_dispute_dunning_freeze(self):
        """AL2C-INV-103: Open commercial dispute freezes automated dunning progression."""
        Move = self.env['account.move']
        Dispute = self.env['al2c.dispute']

        past_due = date.today() - timedelta(days=35)
        invoice = Move.create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': past_due,
            'invoice_date_due': past_due,
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting Services',
                'quantity': 1,
                'price_unit': 50_000_000.0,
            })],
        })
        invoice.action_post()

        # Without dispute: 35 days overdue transitions to d30_suspension
        invoice._al2c_update_dunning_stage()
        self.assertEqual(invoice.al2c_dunning_stage, 'd30_suspension')

        # Reset stage to current and open dispute
        invoice.write({'al2c_dunning_stage': 'current'})
        dispute = Dispute.create({
            'invoice_id': invoice.id,
            'reason': 'milestone_deliverable',
            'disputed_amount': 50_000_000.0,
        })
        self.assertEqual(dispute.state, 'open')
        self.assertTrue(invoice.al2c_has_open_dispute)

        # Dunning ladder run while dispute is open: stays at 'current' (frozen)
        invoice._al2c_update_dunning_stage()
        self.assertEqual(invoice.al2c_dunning_stage, 'current')

        # Resolve dispute
        dispute.action_resolve_dispute("Client approved deliverable revisions")
        self.assertEqual(dispute.state, 'resolved')
        self.assertFalse(invoice.al2c_has_open_dispute)

        # Dunning ladder resumes normal progression
        invoice._al2c_update_dunning_stage()
        self.assertEqual(invoice.al2c_dunning_stage, 'd30_suspension')

    def test_method_level_deny_list_gov_204(self):
        """AL2C-GOV-204: Method-level deny-list raises AccessError when agent calls restricted actions."""
        # 1. Agent attempting to cancel issued e-invoice
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'name': 'License Subscription',
                'quantity': 1,
                'price_unit': 25_000_000.0,
            })],
        })
        invoice.action_post()
        invoice.write({'al2c_einvoice_state': 'issued'})

        with self.assertRaises(AccessError):
            invoice.with_user(self.agent_user).action_cancel_einvoice("Unauthorized agent cancellation")

        # 2. Agent attempting to call button_draft on posted invoice
        with self.assertRaises(AccessError):
            invoice.with_user(self.agent_user).button_draft()
