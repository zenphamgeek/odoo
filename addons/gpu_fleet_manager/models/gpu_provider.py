# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
import requests
from insilos import models, fields, api, _

_logger = logging.getLogger("insilos.gpu_fleet.provider")


class GpuProvider(models.Model):
    _name = "gpu.provider"
    _description = "GPU Compute Provider"
    _order = "priority asc, name asc"

    name = fields.Char(string="Provider Name", required=True, index=True)
    code = fields.Char(string="Provider Code", required=True, index=True,
                       help="Unique identifier (e.g. 'modal', 'thapsang', 'local', 'bai')")
    provider_type = fields.Selection([
        ("modal", "Modal.com Sovereign Fleet"),
        ("local", "Local Workstation (ThinkPad P15)"),
        ("openai_compatible", "OpenAI-Compatible Endpoint"),
        ("runpod", "RunPod GPU Cloud"),
        ("lambda", "Lambda Labs"),
        ("custom", "Custom Sovereign Node"),
    ], string="Provider Type", default="modal", required=True)

    base_url = fields.Char(string="Base URL", default="http://localhost:8099", required=True)
    api_prefix = fields.Char(string="Route Prefix", default="modal",
                             help="Route prefix used in 9Router combos (e.g. 'modal' for modal/wan2.2-s2v)")
    api_key = fields.Char(string="API Key / Auth Token", default="sk-modal-sovereign-local")
    active = fields.Boolean(default=True)
    priority = fields.Integer(string="Provider Priority", default=10,
                              help="Lower value indicates higher failover preference (1 = primary)")
    status = fields.Selection([
        ("active", "Active / Available"),
        ("degraded", "Degraded / Throttled"),
        ("offline", "Offline / Unavailable"),
    ], string="Status", default="active")

    workspace_ids = fields.One2many("gpu.workspace", "provider_id", string="Managed Workspaces")
    workspace_count = fields.Integer(string="Workspaces", compute="_compute_provider_stats")
    worker_count = fields.Integer(string="Workers", compute="_compute_provider_stats")
    total_budget = fields.Float(string="Total Budget ($)", compute="_compute_provider_stats", digits=(16, 2))
    total_usage = fields.Float(string="Total Usage ($)", compute="_compute_provider_stats", digits=(16, 4))
    remaining_budget = fields.Float(string="Remaining Budget ($)", compute="_compute_provider_stats", digits=(16, 2))
    description = fields.Text(string="Provider Architecture & Notes")

    _code_uniq = models.Constraint(
        "unique (code)",
        "Provider code must be unique!",
    )

    @api.depends("workspace_ids", "workspace_ids.budget_ceiling", "workspace_ids.current_usage", "workspace_ids.worker_ids")
    def _compute_provider_stats(self):
        for rec in self:
            workspaces = rec.workspace_ids
            rec.workspace_count = len(workspaces)
            rec.worker_count = sum(len(ws.worker_ids) for ws in workspaces)
            rec.total_budget = sum(workspaces.mapped("budget_ceiling"))
            rec.total_usage = sum(workspaces.mapped("current_usage"))
            rec.remaining_budget = max(0.0, rec.total_budget - rec.total_usage)

    def action_test_connection(self):
        self.ensure_one()
        try:
            target_url = f"{self.base_url.rstrip('/')}/api/proactive_cost"
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            resp = requests.get(target_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                self.status = "active"
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Connection Succeeded"),
                        "message": _("Successfully connected to provider '%s' at %s") % (self.name, self.base_url),
                        "type": "success",
                        "sticky": False,
                    }
                }
            else:
                target_models = f"{self.base_url.rstrip('/')}/v1/models"
                resp_m = requests.get(target_models, headers=headers, timeout=5)
                if resp_m.status_code == 200:
                    self.status = "active"
                    return {
                        "type": "ir.actions.client",
                        "tag": "display_notification",
                        "params": {
                            "title": _("Connection Succeeded"),
                            "message": _("Successfully connected to provider '%s' models endpoint at %s") % (self.name, self.base_url),
                            "type": "success",
                            "sticky": False,
                        }
                    }
                self.status = "degraded"
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Connection Degraded"),
                        "message": _("Provider '%s' returned HTTP %d") % (self.name, resp.status_code),
                        "type": "warning",
                        "sticky": False,
                    }
                }
        except Exception as exc:
            self.status = "offline"
            _logger.warning("Provider connection test failed for %s: %s", self.name, exc)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Connection Failed"),
                    "message": _("Could not connect to %s: %s") % (self.base_url, exc),
                    "type": "warning",
                    "sticky": False,
                }
            }
