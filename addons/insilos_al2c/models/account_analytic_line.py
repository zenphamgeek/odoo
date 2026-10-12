# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        tasks = lines.mapped('task_id').filtered(lambda t: t.allocated_hours > 0)
        if tasks:
            tasks._check_budget_burn_threshold()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'unit_amount' in vals or 'task_id' in vals:
            tasks = self.mapped('task_id').filtered(lambda t: t.allocated_hours > 0)
            if tasks:
                tasks._check_budget_burn_threshold()
        return res
