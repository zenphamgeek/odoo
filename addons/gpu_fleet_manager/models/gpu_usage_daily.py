# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import subprocess
from insilos import models, fields, api, _
from insilos.exceptions import UserError


class GpuUsageDaily(models.Model):
    _name = "gpu.usage.daily"
    _description = "GPU Daily Usage Aggregation"
    _order = "date desc, workspace_id asc"

    name = fields.Char(string="Reference", compute="_compute_name", store=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today, index=True)
    workspace_id = fields.Many2one("gpu.workspace", string="Workspace", ondelete="cascade", index=True)
    provider_id = fields.Many2one("gpu.provider", string="Provider", ondelete="set null", index=True)

    compute_hours = fields.Float(string="Compute Hours (h)", digits=(16, 4), default=0.0)
    total_requests = fields.Integer(string="Total Requests", default=0)
    successful_requests = fields.Integer(string="Successful Requests", default=0)
    failed_requests = fields.Integer(string="Failed Requests", default=0)
    cost = fields.Float(string="Total Cost ($)", digits=(16, 4), default=0.0)
    avg_latency_ms = fields.Float(string="Avg Latency (ms)", digits=(16, 2), default=0.0)
    cache_hit_rate = fields.Float(string="Cache Hit Rate (%)", digits=(5, 2), default=0.0)
    service_breakdown = fields.Text(string="Service Telemetry JSON")

    _ws_prov_date_uniq = models.Constraint(
        "unique (date, workspace_id, provider_id)",
        "Daily usage record already exists for this date, workspace, and provider!",
    )

    @api.depends("workspace_id.name", "provider_id.name", "date")
    def _compute_name(self):
        for rec in self:
            ws_part = rec.workspace_id.name if rec.workspace_id else "All Workspaces"
            prov_part = f" [{rec.provider_id.name}]" if rec.provider_id else ""
            rec.name = f"{ws_part}{prov_part} - {rec.date}"

    @api.model
    def action_sync_from_9router(self, limit=1000):
        """Execute 9Router SQLite to Insilos Fleet bridge sync."""
        script_path = "/home/zen/hermes-agent/scripts/bridge_9router_to_odoo.py"
        python_bin = "/home/zen/O20/.venv/bin/python"
        try:
            res = subprocess.run(
                [python_bin, script_path, "--limit-history", str(limit)],
                capture_output=True,
                text=True,
                timeout=45
            )
            if res.returncode == 0:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("9Router Sync Complete"),
                        "message": _("Successfully synchronized daily usage metrics and task logs from 9Router SQLite database."),
                        "sticky": False,
                        "type": "success",
                    }
                }
            else:
                raise UserError(_("9Router sync failed: %s") % (res.stderr or res.stdout))
        except Exception as e:
            raise UserError(_("Could not execute 9Router sync bridge: %s") % str(e))
