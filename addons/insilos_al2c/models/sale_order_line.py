# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    milestone_ids = fields.One2many(
        'project.milestone',
        'sale_line_id',
        string='Milestones',
    )

    @api.depends('milestone_ids.al2c_billing_eligible')
    def _compute_qty_delivered(self):
        super()._compute_qty_delivered()

    def _prepare_qty_delivered(self):
        delivered_qties = super()._prepare_qty_delivered()
        lines_by_milestones = self.filtered(lambda sol: sol.qty_delivered_method == 'milestones')
        if not lines_by_milestones:
            return delivered_qties

        # Decree 70/2025 & SAP Activate stage gate enforcement:
        # A milestone line only contributes to delivered quantity if it is reached AND has verified customer sign-off (al2c_billing_eligible == True).
        project_milestone_read_group = self.env['project.milestone']._read_group(
            [('sale_line_id', 'in', lines_by_milestones.ids), ('al2c_billing_eligible', '=', True)],
            ['sale_line_id'],
            ['quantity_percentage:sum'],
        )
        eligible_milestones_per_sol = {sale_line.id: percentage_sum for sale_line, percentage_sum in project_milestone_read_group}
        for line in lines_by_milestones:
            sol_id = line.id or line._origin.id
            delivered_qties[line] = eligible_milestones_per_sol.get(sol_id, 0.0) * line.product_uom_qty
        return delivered_qties

    def _get_to_invoice_qty(self):
        self.ensure_one()
        if self.qty_delivered_method == 'milestones':
            # Block milestone invoicing if no deliverables have reached certified billing eligibility
            eligible_ms = self.milestone_ids.filtered(lambda m: m.al2c_billing_eligible)
            if not eligible_ms:
                return 0.0
        return super()._get_to_invoice_qty()
