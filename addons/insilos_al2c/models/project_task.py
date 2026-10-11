# -*- coding: utf-8 -*-
from odoo import models, fields


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

    def _scheduling(self, vals, max_date_start, first_possible_date_per_task=None):
        # Compatibility shim: "create project from template" always calls
        # _scheduling, even when no copied task carries planned dates. With an empty
        # recordset there is nothing to schedule.
        if not self:
            return [{}, {}]
        return super()._scheduling(vals, max_date_start, first_possible_date_per_task=first_possible_date_per_task)
