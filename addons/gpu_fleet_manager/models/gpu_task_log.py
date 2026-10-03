# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos import models, fields, api, _


class GpuTaskLog(models.Model):
    _name = "gpu.task.log"
    _description = "GPU Execution Task Log"
    _order = "execution_timestamp desc, id desc"

    name = fields.Char(string="Task Reference", compute="_compute_name", store=True)
    request_id = fields.Char(string="Request ID", required=True, index=True)
    endpoint = fields.Char(string="API Endpoint", required=True)
    model_template = fields.Char(string="Model / Template", required=True)

    workspace_id = fields.Many2one("gpu.workspace", string="Workspace Used", ondelete="set null", index=True)
    worker_id = fields.Many2one("gpu.worker", string="Worker Used", ondelete="set null", index=True)

    duration_seconds = fields.Float(string="Duration (s)", digits=(16, 3), default=0.0)
    micro_cost = fields.Float(string="Micro-Cost ($)", digits=(16, 6), default=0.0)
    status = fields.Selection([
        ("running", "In-Flight"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("quarantined", "Quarantined"),
    ], string="Execution Status", default="completed", index=True)

    execution_timestamp = fields.Datetime(string="Execution Timestamp", default=fields.Datetime.now, index=True)
    error_message = fields.Text(string="Error Message")

    _request_id_uniq = models.Constraint(
        "unique (request_id)",
        "Request ID must be unique!",
    )

    @api.depends("request_id", "model_template")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.request_id} ({rec.model_template or 'task'})"
