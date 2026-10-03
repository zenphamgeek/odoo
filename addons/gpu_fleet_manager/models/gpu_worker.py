# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
import random
import requests
from datetime import timedelta
from insilos import models, fields, api, _

_logger = logging.getLogger("insilos.gpu_fleet.worker")

FLEET_SERVER_BASE_URL = "http://localhost:8099"
FLEET_SERVER_AUTH_TOKEN = "sk-modal-sovereign-local"


class GpuWorker(models.Model):
    _name = "gpu.worker"
    _description = "GPU Compute Worker"
    _order = "state desc, name asc"

    name = fields.Char(string="Worker Identifier", required=True, index=True)
    active = fields.Boolean(default=True)
    gpu_type = fields.Selection([
        ("a100_80gb", "NVIDIA A100-80GB"),
        ("h100", "NVIDIA H100"),
        ("a10g", "NVIDIA A10G"),
        ("l40s", "NVIDIA L40S"),
        ("l4", "NVIDIA L4"),
        ("t4", "NVIDIA T4"),
        ("rtx5000", "NVIDIA RTX-5000 (Local)"),
    ], string="GPU Tier", default="t4", required=True)

    vram_gb = fields.Integer(string="VRAM (GB)", default=16)
    cloud_provider = fields.Selection([
        ("modal", "Modal.com"),
        ("local", "Local Workstation (ThinkPad P15)"),
        ("runpod", "RunPod"),
        ("lambda", "Lambda Labs"),
    ], string="Cloud Provider", default="modal", required=True)

    workspace_id = fields.Many2one("gpu.workspace", string="Assigned Workspace", ondelete="set null", index=True)
    state = fields.Selection([
        ("idle", "Idle"),
        ("running", "Running"),
        ("quarantined", "Quarantined"),
        ("offline", "Offline"),
    ], string="Worker State", default="idle", required=True)

    hourly_cost_rate = fields.Float(string="Hourly Rate ($/hr)", digits=(16, 4), default=0.59)
    active_requests = fields.Integer(string="Active Requests", default=0)
    consecutive_failures = fields.Integer(string="Consecutive Failures", default=0)
    quarantine_until = fields.Datetime(string="Quarantined Until")
    last_heartbeat = fields.Datetime(string="Last Heartbeat", default=fields.Datetime.now)

    # Stealth Mode & Distributed Random Jitter Scheduling
    stealth_sync_enabled = fields.Boolean(
        string="Stealth Mode",
        default=True,
        help="Enable distributed randomized probe scheduling to stay within daily quota."
    )
    stealth_status = fields.Selection([
        ("scheduled", "Stealth Scheduled"),
        ("probing", "Probing Live"),
        ("cooldown", "In Cooldown"),
        ("passive", "Passive Only"),
    ], string="Stealth Status", default="scheduled", compute="_compute_stealth_status", store=True)

    next_probe_at = fields.Datetime(
        string="Next Stealth Probe",
        index=True,
        default=fields.Datetime.now,
        help="Timestamp of next scheduled stealth probe"
    )
    last_probe_at = fields.Datetime(string="Last Probe Executed")
    probe_jitter_minutes = fields.Integer(
        string="Random Jitter (min)",
        default=15,
        help="Randomized jitter range applied to next probe schedule"
    )

    stealth_countdown_display = fields.Char(
        string="Next Probe ETA",
        compute="_compute_stealth_display",
        help="Real-time human readable countdown with jitter indication"
    )
    stealth_quota_display = fields.Char(
        string="Daily Quota Status",
        compute="_compute_stealth_display",
        help="Stealth daily probe quota status"
    )

    task_log_ids = fields.One2many("gpu.task.log", "worker_id", string="Execution Logs")
    total_completed_tasks = fields.Integer(string="Completed Tasks", compute="_compute_task_stats", store=True)
    total_compute_seconds = fields.Float(string="Total Compute Time (s)", compute="_compute_task_stats", store=True)

    _name_uniq = models.Constraint(
        "unique (name)",
        "Worker name must be unique!",
    )

    @api.depends("task_log_ids.duration_seconds", "task_log_ids.status")
    def _compute_task_stats(self):
        for rec in self:
            completed = rec.task_log_ids.filtered(lambda t: t.status == "completed")
            rec.total_completed_tasks = len(completed)
            rec.total_compute_seconds = sum(completed.mapped("duration_seconds"))

    @api.depends("stealth_sync_enabled", "next_probe_at", "last_probe_at")
    def _compute_stealth_status(self):
        for rec in self:
            if not rec.stealth_sync_enabled:
                rec.stealth_status = "passive"
            else:
                rec.stealth_status = "scheduled"

    def _compute_stealth_display(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.stealth_sync_enabled:
                rec.stealth_countdown_display = "Stealth Disabled"
                rec.stealth_quota_display = "Passive Only"
                continue

            jitter_str = f"±{rec.probe_jitter_minutes or 15}m"
            if not rec.next_probe_at:
                rec.stealth_countdown_display = f"Scheduled ({jitter_str})"
            else:
                delta = rec.next_probe_at - now
                total_seconds = delta.total_seconds()
                if total_seconds > 0:
                    mins = int(total_seconds // 60)
                    hours = mins // 60
                    rem_mins = mins % 60
                    if hours > 0:
                        time_str = f"In {hours}h {rem_mins}m"
                    else:
                        time_str = f"In {mins}m"
                    rec.stealth_countdown_display = f"{time_str} ({jitter_str})"
                else:
                    rec.stealth_countdown_display = f"Due Now ({jitter_str})"

            rec.stealth_quota_display = "Quota ≤ 5/day"

    def action_quarantine(self):
        self.write({
            "state": "quarantined",
            "quarantine_until": fields.Datetime.now() + timedelta(minutes=5),
        })

    def action_unquarantine(self):
        self.write({
            "state": "idle",
            "consecutive_failures": 0,
            "quarantine_until": False,
        })

    def action_trigger_stealth_probe(self):
        """Manually trigger a stealth probe for this worker's workspace with random jitter rescheduling."""
        self.ensure_one()
        now = fields.Datetime.now()
        if self.workspace_id:
            self.workspace_id.action_sync_from_fleet_server()

        base_delay = random.randint(45, 90)
        jitter = random.randint(-15, 20)
        next_time = now + timedelta(minutes=max(20, base_delay + jitter))
        self.write({
            "last_probe_at": now,
            "next_probe_at": next_time,
            "probe_jitter_minutes": abs(jitter),
            "stealth_status": "scheduled",
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Stealth Probe Executed"),
                "message": _("Stealth probe completed for %s. Next randomized probe scheduled in %d minutes (jitter ±%dm).") % (
                    self.name, max(20, base_delay + jitter), abs(jitter)
                ),
                "sticky": False,
                "type": "success",
            }
        }

    @api.model
    def _cron_stealth_distributed_worker_sync(self):
        """
        Stealth Mode Cron:
        - Checks daily probe quota to prevent exceeding 5 probes/day.
        - Staggers uninitialized workers across randomized future windows.
        - Picks at most 1 due worker per cycle to eliminate burst traffic.
        - Reschedules with dynamic random delay + jitter.
        """
        now = fields.Datetime.now()
        _logger.info("Starting GPU Fleet Stealth Distributed Worker Sync Cron pass...")

        # 1. Verify Probe Quota from Fleet Server
        quota_remaining = 5
        try:
            resp = requests.get(
                f"{FLEET_SERVER_BASE_URL}/api/probe_quota",
                headers={"Authorization": f"Bearer {FLEET_SERVER_AUTH_TOKEN}"},
                timeout=5
            )
            if resp.status_code == 200:
                quota_data = resp.json()
                quota_remaining = quota_data.get("remaining", 5)
                _logger.info("Stealth Probe Quota check: %d remaining today", quota_remaining)
        except Exception as e:
            _logger.warning("Could not fetch probe quota from fleet server: %s", e)

        if quota_remaining <= 0:
            _logger.warning("Daily stealth probe quota exhausted (0 remaining). Putting workers in cooldown.")
            cooldown_workers = self.search([("stealth_sync_enabled", "=", True)])
            tomorrow = now.replace(hour=0, minute=15, second=0) + timedelta(days=1)
            cooldown_workers.write({
                "stealth_status": "cooldown",
                "next_probe_at": tomorrow,
            })
            return

        # 2. Stagger uninitialized workers with random spread (10 to 120 minutes)
        uninit_workers = self.search([
            ("stealth_sync_enabled", "=", True),
            ("next_probe_at", "=", False),
        ])
        for w in uninit_workers:
            stagger = random.randint(10, 120)
            jitter = random.randint(5, 20)
            w.write({
                "next_probe_at": now + timedelta(minutes=stagger),
                "probe_jitter_minutes": jitter,
            })

        # 3. Find candidate workers due for probe
        due_workers = self.search([
            ("stealth_sync_enabled", "=", True),
            ("state", "in", ("idle", "running")),
            ("next_probe_at", "<=", now),
        ], order="next_probe_at asc")

        if not due_workers:
            _logger.info("No workers due for stealth probe at this cycle.")
            return

        # 4. Stealth Constraint: Probe strictly 1 worker per cron run (distributed over time)
        target_worker = due_workers[0]
        _logger.info(
            "Executing stealth probe for worker '%s' (Workspace: %s)",
            target_worker.name,
            target_worker.workspace_id.name if target_worker.workspace_id else "None"
        )

        if target_worker.workspace_id:
            target_worker.workspace_id.action_sync_from_fleet_server()

        # 5. Reschedule target worker with randomized base interval + jitter
        base_delay = random.randint(60, 120)
        jitter = random.randint(-20, 25)
        next_time = now + timedelta(minutes=max(30, base_delay + jitter))

        target_worker.write({
            "last_probe_at": now,
            "next_probe_at": next_time,
            "probe_jitter_minutes": abs(jitter),
            "stealth_status": "scheduled",
        })
        _logger.info(
            "Worker '%s' stealth probe finished. Next scheduled at %s (delay %dm, jitter ±%dm)",
            target_worker.name, next_time, max(30, base_delay + jitter), abs(jitter)
        )
