# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Al2cFtsItem(models.Model):
    """
    Fit-to-Standard Clean Core Scope Item (AL2C-CRM-101):
    Categorizes every customer business requirement into clean-core extensibility tiers:
    - Class A: Standard Out-of-the-Box Configuration (Clean Core)
    - Class B: Low-Code Studio / QWeb Layout Customization
    - Class C: Decoupled API Integration / Mojo AI App
    - Class D: Prohibited Core Modification (Forbidden unless signed off by Architecture Board)
    """
    _name = 'al2c.fts.item'
    _description = 'Fit-to-Standard Clean Core Requirement'
    _order = 'clean_core_class desc, id'

    name = fields.Char(string='Requirement Summary', required=True)
    lead_id = fields.Many2one('crm.lead', string='Source Opportunity', ondelete='cascade', index=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', string='Implementation Project', ondelete='cascade', index=True)
    module = fields.Char(string='Target Business Module', default='General')

    clean_core_class = fields.Selection([
        ('class_a', 'Class A: Standard Out-of-the-Box Config'),
        ('class_b', 'Class B: Low-Code Studio / QWeb View'),
        ('class_c', 'Class C: Decoupled API / Mojo AI App'),
        ('class_d', 'Class D: Prohibited Core Modification'),
    ], string='Clean Core Classification', default='class_a', required=True)

    description = fields.Text(string='Requirement Specification')
    justification = fields.Text(string='Architectural Justification')

    approved_by_architect = fields.Boolean(
        string='Architecture Board Approved',
        default=False,
        help='Class D scope items strictly require Solution Architect sign-off before quotation confirmation.',
    )
    architect_user_id = fields.Many2one('res.users', string='Approving Architect')
    approval_date = fields.Datetime(string='Approval Date')

    def action_approve_class_d(self):
        """Approve a Class D requirement exception."""
        for item in self:
            if not self.env.user.has_group('sales_team.group_sale_manager') and not self.env.is_admin():
                raise UserError(_("Only a Solution Architect or Sales Manager can approve Class D core modifications."))
            item.write({
                'approved_by_architect': True,
                'architect_user_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
        return True
