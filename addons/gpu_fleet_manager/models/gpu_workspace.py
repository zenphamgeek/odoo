# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import json
import logging
import requests
from datetime import datetime
from insilos import models, fields, api, _
from insilos.exceptions import UserError

_logger = logging.getLogger("insilos.gpu_fleet.workspace")

FLEET_SERVER_BASE_URL = "http://localhost:8099"
FLEET_SERVER_AUTH_TOKEN = "sk-modal-sovereign-local"

TIER_HOURLY_RATES = {
    "A100-80GB": 2.10,
    "H100": 3.95,
    "A10G": 1.10,
    "L40S": 1.35,
    "L4": 0.80,
    "T4": 0.59,
    "RTX-5000": 0.00,
}


class GpuWorkspace(models.Model):
    _name = "gpu.workspace"
    _description = "GPU Workspace Profile"
    _order = "priority asc, headroom_score desc, name asc"

    name = fields.Char(string="Workspace Name", required=True, index=True)
    active = fields.Boolean(default=True)
    email_account = fields.Char(string="Email Account", required=True, default="just.ask.mr.zen@gmail.com")
    tier = fields.Selection([
        ("A100-80GB", "NVIDIA A100-80GB"),
        ("H100", "NVIDIA H100"),
        ("A10G", "NVIDIA A10G"),
        ("L40S", "NVIDIA L40S"),
        ("L4", "NVIDIA L4"),
        ("T4", "NVIDIA T4"),
        ("RTX-5000", "NVIDIA RTX-5000 (Local)"),
    ], string="Default GPU Tier", default="T4", required=True)

    priority = fields.Integer(
        string="Rotation Priority",
        default=10,
        index=True,
        help="Workspace rotation priority (1 = primary/preferred, 20 = standby/fallback). Lower values are allocated first."
    )
    provider_id = fields.Many2one(
        "gpu.provider",
        string="Cloud Provider",
        ondelete="restrict",
        index=True,
        help="Parent cloud provider managing this workspace."
    )

    budget_ceiling = fields.Float(string="Budget Ceiling ($)", digits=(16, 2), default=30.0)
    current_usage = fields.Float(string="Current Usage ($)", digits=(16, 4), default=0.0)
    remaining_headroom = fields.Float(
        string="Remaining Headroom ($)",
        digits=(16, 4),
        compute="_compute_headroom",
        store=True,
    )
    headroom_score = fields.Float(string="Headroom Score", digits=(16, 2), default=30.0)
    hard_ceiling = fields.Float(string="Hard Ceiling ($)", digits=(16, 2), default=29.50)
    hard_ceiling_breached = fields.Boolean(
        string="Hard Ceiling Breached",
        compute="_compute_headroom",
        store=True,
    )
    preemptive_cutoff = fields.Float(string="Pre-Emptive Cutoff ($)", digits=(16, 2), default=29.20)

    has_overdue_invoice = fields.Boolean(string="Overdue Invoice Flag", default=False)
    billing_status = fields.Selection([
        ("healthy", "Healthy ($0 - $25)"),
        ("warning", "Warning ($25 - $29.20)"),
        ("critical", "Critical ($29.20 - $29.50)"),
        ("breached", "Breached ($29.50+)"),
        ("overdue", "Overdue Invoice PENDING"),
    ], string="Billing Status", default="healthy", compute="_compute_billing_status", store=True)

    is_configured = fields.Boolean(string="Spend Limit Configured", default=True)
    is_compliant = fields.Boolean(string="Audit Compliant (< $29.80)", default=True)
    configured_limit_usd = fields.Float(string="Configured Spend Limit ($)", digits=(16, 2), default=29.50)
    active_workers_count = fields.Integer(string="Active Workers", default=0)
    probes_today = fields.Integer(string="Probes Today", default=0)
    last_sync = fields.Datetime(string="Last Synced")

    worker_ids = fields.One2many("gpu.worker", "workspace_id", string="Assigned Workers")
    task_log_ids = fields.One2many("gpu.task.log", "workspace_id", string="Task Logs")
    meter_ids = fields.One2many("gpu.usage.meter", "workspace_id", string="Usage Meters")

    task_count = fields.Integer(string="Total Tasks", compute="_compute_counts")
    worker_count = fields.Integer(string="Total Workers", compute="_compute_counts")

    _name_uniq = models.Constraint(
        "unique (name)",
        "Workspace name must be unique!",
    )

    @api.depends("budget_ceiling", "current_usage", "hard_ceiling")
    def _compute_headroom(self):
        for rec in self:
            budget = rec.budget_ceiling or 30.0
            usage = rec.current_usage or 0.0
            rec.remaining_headroom = round(max(0.0, budget - usage), 4)
            rec.hard_ceiling_breached = usage >= (rec.hard_ceiling or 29.50)

    @api.depends("current_usage", "hard_ceiling", "preemptive_cutoff", "has_overdue_invoice")
    def _compute_billing_status(self):
        for rec in self:
            if rec.has_overdue_invoice:
                rec.billing_status = "overdue"
                continue
            usage = rec.current_usage or 0.0
            if usage >= (rec.hard_ceiling or 29.50):
                rec.billing_status = "breached"
            elif usage >= (rec.preemptive_cutoff or 29.20):
                rec.billing_status = "critical"
            elif usage >= 25.0:
                rec.billing_status = "warning"
            else:
                rec.billing_status = "healthy"

    def _compute_counts(self):
        for rec in self:
            rec.task_count = len(rec.task_log_ids)
            rec.worker_count = len(rec.worker_ids)

    @api.model
    def get_optimal_workspace(self, service_type=None):
        """Select the optimal workspace based on:
        1. active = True
        2. hard_ceiling_breached = False
        3. has_overdue_invoice = False
        4. billing_status in ['healthy', 'warning']
        5. ordered by priority asc, headroom_score desc, remaining_headroom desc
        """
        domain = [
            ("active", "=", True),
            ("hard_ceiling_breached", "=", False),
            ("has_overdue_invoice", "=", False),
            ("billing_status", "in", ["healthy", "warning"]),
        ]
        workspaces = self.search(domain, order="priority asc, headroom_score desc, remaining_headroom desc")
        return workspaces[0] if workspaces else self.env["gpu.workspace"]

    def action_sync_from_fleet_server(self):
        """Live Data Bridge querying Modal Fleet Server endpoints:
        - GET /api/proactive_cost
        - GET /api/sentinel/usage_limits
        - GET /api/fleet/requests/in_flight
        """
        headers = {"Authorization": f"Bearer {FLEET_SERVER_AUTH_TOKEN}"}
        now_dt = fields.Datetime.now()
        synced_workspaces = 0

        # 0. Ensure Default Providers Exist
        Provider = self.env["gpu.provider"]
        modal_provider = Provider.search([("code", "=", "modal")], limit=1)
        if not modal_provider:
            modal_provider = Provider.create({
                "name": "Modal Sovereign Fleet",
                "code": "modal",
                "provider_type": "modal",
                "base_url": FLEET_SERVER_BASE_URL,
                "api_prefix": "modal",
                "priority": 1,
                "status": "active",
                "description": "20 Sovereign Workspaces with $30/month budget ceiling per workspace",
            })
        local_provider = Provider.search([("code", "=", "local")], limit=1)
        if not local_provider:
            local_provider = Provider.create({
                "name": "Local Workstation (ThinkPad P15)",
                "code": "local",
                "provider_type": "local",
                "base_url": "http://localhost:20128",
                "api_prefix": "local",
                "priority": 0,
                "status": "active",
                "description": "Local ThinkPad P15 Quadro RTX 5000 16GB VRAM",
            })
        thapsang_provider = Provider.search([("code", "=", "thapsang")], limit=1)
        if not thapsang_provider:
            thapsang_provider = Provider.create({
                "name": "Thapsang Sovereign AI Engine",
                "code": "thapsang",
                "provider_type": "custom",
                "base_url": f"{FLEET_SERVER_BASE_URL}/v1",
                "api_prefix": "thapsang",
                "priority": 10,
                "status": "active",
                "description": "Thapsang Sovereign AI Platform & Fallback Hub",
            })

        data_cost = {}

        # 1. Fetch Proactive Cost & Workspaces
        try:
            resp_cost = requests.get(f"{FLEET_SERVER_BASE_URL}/api/proactive_cost", headers=headers, timeout=10)
            if resp_cost.status_code == 200:
                data_cost = resp_cost.json()
                ws_list = data_cost.get("workspaces", [])
                for ws_data in ws_list:
                    ws_name = ws_data.get("workspace")
                    if not ws_name:
                        continue
                    ws = self.search([("name", "=", ws_name)], limit=1)
                    vals = {
                        "email_account": ws_data.get("account", "just.ask.mr.zen@gmail.com"),
                        "tier": ws_data.get("tier", "T4"),
                        "budget_ceiling": float(ws_data.get("budget", 30.0)),
                        "current_usage": float(ws_data.get("estimated_spent", 0.0)),
                        "headroom_score": float(ws_data.get("headroom_score", 30.0)),
                        "hard_ceiling": float(ws_data.get("hard_ceiling", 29.50)),
                        "active_workers_count": int(ws_data.get("active_workers", 0)),
                        "probes_today": int(ws_data.get("probes_today", 0)),
                        "provider_id": modal_provider.id,
                        "last_sync": now_dt,
                    }
                    if ws:
                        ws.write(vals)
                    else:
                        vals["name"] = ws_name
                        ws = self.create(vals)
                    synced_workspaces += 1

                    # Ensure worker exists for this workspace
                    worker_name = f"{ws_name}-worker-01"
                    worker = self.env["gpu.worker"].search([("name", "=", worker_name)], limit=1)
                    hourly_rate = TIER_HOURLY_RATES.get(ws.tier, 0.59)
                    if not worker:
                        self.env["gpu.worker"].create({
                            "name": worker_name,
                            "gpu_type": ws.tier.lower().replace("-", "_"),
                            "workspace_id": ws.id,
                            "hourly_cost_rate": hourly_rate,
                            "state": "running" if ws.active_workers_count > 0 else "idle",
                        })
                    else:
                        worker.write({
                            "workspace_id": ws.id,
                            "hourly_cost_rate": hourly_rate,
                            "state": "running" if ws.active_workers_count > 0 else "idle",
                        })

                # Ingest recent records into gpu.task.log
                recent_recs = data_cost.get("recent_records", [])
                for r in recent_recs:
                    req_id = r.get("request_id")
                    if not req_id:
                        continue
                    existing_log = self.env["gpu.task.log"].search([("request_id", "=", str(req_id))], limit=1)
                    if not existing_log:
                        ws_target = self.search([("name", "=", r.get("workspace"))], limit=1)
                        ts = r.get("timestamp")
                        exec_dt = datetime.fromtimestamp(ts) if ts else now_dt
                        self.env["gpu.task.log"].create({
                            "request_id": str(req_id),
                            "endpoint": f"/api/{r.get('service', 'generate')}",
                            "model_template": r.get("service") or r.get("hardware_tier", "unknown"),
                            "workspace_id": ws_target.id if ws_target else False,
                            "duration_seconds": float(r.get("duration_sec", 0.0)),
                            "micro_cost": float(r.get("calibrated_cost", r.get("nominal_cost", 0.0))),
                            "status": "completed",
                            "execution_timestamp": exec_dt,
                        })
        except requests.exceptions.RequestException as exc:
            _logger.error("Fleet Server proactive_cost sync failed: %s", exc)
            raise UserError(_("Could not reach Modal Fleet Server at %s: %s") % (FLEET_SERVER_BASE_URL, exc))

        # 2. Fetch Sentinel Usage Limits
        try:
            resp_sentinel = requests.get(f"{FLEET_SERVER_BASE_URL}/api/sentinel/usage_limits", headers=headers, timeout=10)
            if resp_sentinel.status_code == 200:
                sentinel_data = resp_sentinel.json()
                for s_ws in sentinel_data.get("workspaces", []):
                    ws_name = s_ws.get("workspace")
                    ws = self.search([("name", "=", ws_name)], limit=1)
                    if ws:
                        s_vals = {
                            "is_configured": bool(s_ws.get("is_configured", True)),
                            "is_compliant": bool(s_ws.get("is_compliant", True)),
                            "configured_limit_usd": float(s_ws.get("configured_limit_usd") or 29.50),
                        }
                        if s_ws.get("alarm") == "OVERDUE_INVOICE" or s_ws.get("overdue_alert"):
                            s_vals["has_overdue_invoice"] = True
                            s_vals["billing_status"] = "overdue"
                        else:
                            s_vals["has_overdue_invoice"] = False
                        ws.write(s_vals)
        except Exception as exc:
            _logger.warning("Sentinel sync warning: %s", exc)

        # 3. Fetch In-Flight and Completed Requests
        try:
            resp_inflight = requests.get(f"{FLEET_SERVER_BASE_URL}/api/fleet/requests/in_flight", headers=headers, timeout=10)
            if resp_inflight.status_code == 200:
                inflight_data = resp_inflight.json()
                for comp in inflight_data.get("completed_requests", []):
                    req_id = comp.get("id") or comp.get("request_id")
                    if not req_id:
                        continue
                    existing_log = self.env["gpu.task.log"].search([("request_id", "=", str(req_id))], limit=1)
                    ws_name_comp = comp.get("assigned_workspace") or comp.get("workspace")
                    ws_assigned = self.search([("name", "=", ws_name_comp)], limit=1) if ws_name_comp else False
                    if not existing_log:
                        status_val = "completed" if comp.get("status", 200) == 200 else "failed"
                        exec_iso = comp.get("completed_at_iso")
                        exec_dt = now_dt
                        if exec_iso:
                            try:
                                clean_iso = exec_iso.replace("Z", "").split("+")[0]
                                exec_dt = datetime.fromisoformat(clean_iso)
                            except Exception:
                                exec_dt = now_dt
                        self.env["gpu.task.log"].create({
                            "request_id": str(req_id),
                            "endpoint": comp.get("endpoint", "/api/generate"),
                            "model_template": comp.get("template", "unknown"),
                            "workspace_id": ws_assigned.id if ws_assigned else False,
                            "duration_seconds": float(comp.get("duration_sec", 0.0)),
                            "micro_cost": float(comp.get("cost_usd", comp.get("cost", 0.0))),
                            "status": status_val,
                            "execution_timestamp": exec_dt,
                        })
        except Exception as exc:
            _logger.warning("In-flight requests sync warning: %s", exc)

        # 4. Aggregate Daily Usage Meter and Daily Usage Rollups for Today
        today = fields.Date.context_today(self)
        service_telemetry = data_cost.get("service_telemetry") if isinstance(data_cost, dict) else {}
        telemetry_json = json.dumps(service_telemetry) if service_telemetry else "{}"

        for ws in self.search([]):
            tasks_today = self.env["gpu.task.log"].search([
                ("workspace_id", "=", ws.id),
                ("execution_timestamp", ">=", datetime.combine(today, datetime.min.time())),
                ("execution_timestamp", "<=", datetime.combine(today, datetime.max.time())),
            ])
            total_dur = sum(tasks_today.mapped("duration_seconds"))
            total_cost = sum(tasks_today.mapped("micro_cost"))
            tot_req = len(tasks_today)
            succ_req = len(tasks_today.filtered(lambda t: t.status == "completed"))
            fail_req = len(tasks_today.filtered(lambda t: t.status == "failed"))
            avg_lat = (total_dur / tot_req * 1000.0) if tot_req > 0 else 0.0

            # 4a. Update gpu.usage.meter
            meter = self.env["gpu.usage.meter"].search([
                ("workspace_id", "=", ws.id),
                ("date", "=", today),
                ("period", "=", "daily"),
            ], limit=1)
            meter_vals = {
                "compute_hours": round(total_dur / 3600.0, 4),
                "cost_dollars": round(total_cost if total_cost > 0 else ws.current_usage, 4),
                "total_requests": tot_req,
                "successful_requests": succ_req,
                "failed_requests": fail_req,
                "avg_latency_ms": round(avg_lat, 2),
            }
            if meter:
                meter.write(meter_vals)
            elif tot_req > 0 or ws.current_usage > 0:
                meter_vals.update({
                    "workspace_id": ws.id,
                    "date": today,
                    "period": "daily",
                })
                self.env["gpu.usage.meter"].create(meter_vals)

            # 4b. Update gpu.usage.daily (9Router Aggregation)
            prov_id = ws.provider_id.id if ws.provider_id else modal_provider.id
            daily_rec = self.env["gpu.usage.daily"].search([
                ("workspace_id", "=", ws.id),
                ("provider_id", "=", prov_id),
                ("date", "=", today),
            ], limit=1)
            daily_vals = {
                "compute_hours": round(total_dur / 3600.0, 4),
                "cost": round(total_cost if total_cost > 0 else ws.current_usage, 4),
                "total_requests": tot_req,
                "successful_requests": succ_req,
                "failed_requests": fail_req,
                "avg_latency_ms": round(avg_lat, 2),
                "service_breakdown": telemetry_json,
            }
            if daily_rec:
                daily_rec.write(daily_vals)
            elif tot_req > 0 or ws.current_usage > 0:
                daily_vals.update({
                    "workspace_id": ws.id,
                    "provider_id": prov_id,
                    "date": today,
                })
                self.env["gpu.usage.daily"].create(daily_vals)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Fleet Synchronized"),
                "message": _("Successfully synchronized %d workspaces and telemetry from Modal Fleet Server.") % synced_workspaces,
                "sticky": False,
                "type": "success",
            }
        }
