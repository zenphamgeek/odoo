# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from . import account_analytic_line


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
                    pm = task.project_id.user_id if task.project_id else False
                    partner_ids = [pm.partner_id.id] if pm and pm.partner_id else []

                    # 1. Post to task chatter
                    task.message_post(body=msg, subtype_xmlid='mail.mt_note', partner_ids=partner_ids)

                    # 2. Post to project chatter
                    if task.project_id:
                        task.project_id.message_post(body=msg, subtype_xmlid='mail.mt_note', partner_ids=partner_ids)

                    # 3. Schedule To-Do activity for Project Manager
                    if pm:
                        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                        if todo_type:
                            existing_act = task.activity_ids.filtered(
                                lambda a: a.activity_type_id == todo_type and a.summary == "AL2C Budget Burn Warning (>= 85%)"
                            )
                            if not existing_act:
                                task.activity_schedule(
                                    activity_type_id=todo_type.id,
                                    summary=_("AL2C Budget Burn Warning (>= 85%)"),
                                    note=msg,
                                    user_id=pm.id,
                                )
                elif burn_ratio < 0.85 and task.al2c_burn_warning_sent:
                    task.al2c_burn_warning_sent = False

    def write(self, vals):
        res = super().write(vals)
        if 'allocated_hours' in vals:
            self.filtered(lambda t: t.allocated_hours > 0)._check_budget_burn_threshold()
        return res
