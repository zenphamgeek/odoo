# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos import models, fields, api, _


class GpuUsageMeter(models.Model):
    _name = "gpu.usage.meter"
    _description = "GPU Usage Meter"
    _order = "date desc, workspace_id asc"

    name = fields.Char(string="Reference", compute="_compute_name", store=True)
    workspace_id = fields.Many2one("gpu.workspace", string="Workspace", required=True, ondelete="cascade", index=True)
    date = fields.Date(string="Meter Date", required=True, default=fields.Date.context_today, index=True)
    period = fields.Selection([
        ("daily", "Daily"),
        ("monthly", "Monthly"),
    ], string="Period", default="daily", required=True)

    compute_hours = fields.Float(string="Compute Hours (h)", digits=(16, 3), default=0.0)
    cost_dollars = fields.Float(string="Compute Cost ($)", digits=(16, 4), default=0.0)
    total_requests = fields.Integer(string="Total Requests", default=0)
    successful_requests = fields.Integer(string="Successful Requests", default=0)
    failed_requests = fields.Integer(string="Failed Requests", default=0)
    avg_latency_ms = fields.Float(string="Avg Latency (ms)", digits=(16, 2), default=0.0)

    _ws_date_period_uniq = models.Constraint(
        "unique (workspace_id, date, period)",
        "Usage meter entry already exists for this workspace, date, and period!",
    )

    @api.depends("workspace_id.name", "date", "period")
    def _compute_name(self):
        for rec in self:
            ws_name = rec.workspace_id.name if rec.workspace_id else "All"
            rec.name = f"{ws_name} - {rec.date} ({rec.period})"
