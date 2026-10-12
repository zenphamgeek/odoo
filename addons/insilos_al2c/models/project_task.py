# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    tz = fields.Selection(
        lambda self: self.env['res.partner']._fields['tz'].selection,
        string="Timezone",
        default=lambda self: self.env.user.tz or 'UTC',
        compute='_compute_tz',
        store=False,
    )

    def _compute_tz(self):
        for cal in self:
            cal.tz = cal.company_id.partner_id.tz or self.env.user.tz or 'UTC'


class ProjectTask(models.Model):
    _inherit = 'project.task'

    al2c_burn_warning_sent = fields.Boolean(
        string='Budget Burn Warning Sent',
        default=False,
        copy=False,
        help='Indicates whether a budget burn warning (>= 85% allocated hours) has been posted to chatter.',
    )

    def _scheduling(self, vals, max_date_start, first_possible_date_per_task=None):
        # Compatibility shim: "create project from template" always calls
        # _scheduling, even when no copied task carries planned dates. With an empty
        # recordset there is nothing to schedule.
        if not self:
            return [{}, {}]
        return super()._scheduling(vals, max_date_start, first_possible_date_per_task=first_possible_date_per_task)

    def _check_budget_burn_threshold(self):
        """Enforce R4 Project Governance: Trigger notification when recorded hours cross 85% of allocated task budget."""
        for task in self:
            if task.allocated_hours > 0:
                burn_ratio = task.effective_hours / task.allocated_hours
                if burn_ratio >= 0.85 and not task.al2c_burn_warning_sent:
                    task.al2c_burn_warning_sent = True
                    msg = _(
                        "⚠️ <strong>AL2C Budget Burn Warning (R4 Governance)</strong>: "
                        "Task '%(task)s' has reached %(pct).1f%% of allocated budget "
                        "(%(effective).1f / %(allocated).1f hours). Project Manager review required.",
                        task=task.name,
                        pct=burn_ratio * 100.0,
                        effective=task.effective_hours,
                        allocated=task.allocated_hours,
                    )
                    task.message_post(body=msg, subtype_xmlid='mail.mt_note')
                    if task.project_id:
                        task.project_id.message_post(body=msg, subtype_xmlid='mail.mt_note')
                elif burn_ratio < 0.85 and task.al2c_burn_warning_sent:
                    task.al2c_burn_warning_sent = False


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
