# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cSecuritySoDMatrix(TransactionCase):
    """
    Test suite for AL2C-SEC-001: Segregation of Duties (SoD) Matrix & Role ACL Hardening.
    Verifies that autonomous agent identities operate under strict least-privilege boundaries
    without cross-domain privilege escalation.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent_group = cls.env.ref('insilos_al2c.group_al2c_agent')

        # Create specialized agent users
        cls.sales_agent = cls.env['res.users'].create({
            'name': 'Agent Autonomous Sales',
            'login': 'agent_sales_al2c',
            'email': 'agent_sales@example.com',
            'group_ids': [(6, 0, [cls.agent_group.id, cls.env.ref('sales_team.group_sale_salesman').id])],
        })

        cls.support_agent = cls.env['res.users'].create({
            'name': 'Agent Autonomous Support',
            'login': 'agent_support_al2c',
            'email': 'agent_support@example.com',
            'group_ids': [(6, 0, [cls.agent_group.id, cls.env.ref('helpdesk.group_helpdesk_user').id])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Vinaseed Corporation',
            'email': 'procurement@vinaseed.vn',
        })
        cls.sku = cls.env['product.product'].search([('default_code', '=', 'ERP-ENT')], limit=1)

    def test_sales_agent_cannot_manipulate_commission_ledger(self):
        """Sales agent cannot create or manipulate commission ledger entries (finance separation)."""
        with self.assertRaises((AccessError, UserError)):
            self.env['al2c.commission.ledger'].with_user(self.sales_agent).create({
                'name': 'Unauthorized Commission Grant',
                'amount': 50000000.0,
            })

    def test_support_agent_cannot_create_or_confirm_sales_orders(self):
        """Support/helpdesk agent cannot confirm sales orders (cross-domain SoD block)."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.sku.id,
                'product_uom_qty': 1,
                'price_unit': self.sku.list_price,
            })],
        })
        with self.assertRaises((AccessError, UserError)):
            so.with_user(self.support_agent).action_confirm()

    def test_sales_agent_cannot_self_approve_deal_desk(self):
        """Sales agent cannot self-approve discounted quotations exceeding GOV-002 thresholds."""
        so = self.env['sale.order'].with_user(self.sales_agent).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.sku.id,
                'product_uom_qty': 1,
                'price_unit': self.sku.list_price * 0.70,  # 30% discount
            })],
        })
        # Attempt to confirm directly raises approval block
        with self.assertRaises(UserError) as cm:
            so.action_confirm()
        self.assertIn("Deal Desk Approved", str(cm.exception))

