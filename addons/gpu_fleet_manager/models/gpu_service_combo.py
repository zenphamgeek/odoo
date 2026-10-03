# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos import models, fields, api, _


class GpuServiceCombo(models.Model):
    _name = "gpu.service.combo"
    _description = "GPU Service Combo & Failover Chain"
    _order = "name asc"

    name = fields.Char(string="Combo Name", required=True, index=True)
    code = fields.Char(string="Combo Identifier", required=True, index=True,
                       help="Virtual model requested by clients, e.g. 'thapsang-s2v', 'modal-fleet'")
    active = fields.Boolean(default=True)
    service_type = fields.Selection([
        ("video_wan22", "Speech-to-Video (Wan 2.2 / S2V)"),
        ("video_ltx", "Cinema Video (LTX Video 2.5)"),
        ("image_dit", "Text-to-Image (Qwen DiT)"),
        ("tts_vieneu", "Text-to-Speech (VieNeu-TTS CUDA)"),
        ("video_swapface", "Face Swap (Video SwapFace)"),
        ("llm_chat", "LLM Reasoning / Chat"),
        ("composite", "Composite / Multi-Service Pipeline"),
    ], string="Service Category", default="composite", required=True)

    routing_strategy = fields.Selection([
        ("failover", "Sequential Failover (P1 → P2 → P3)"),
        ("lowest_cost", "Lowest Micro-Cost First"),
        ("least_busy", "Least Concurrency / Headroom"),
        ("round_robin", "Round-Robin Balancing"),
    ], string="Routing Strategy", default="failover", required=True)

    timeout_seconds = fields.Float(string="Step Timeout (s)", default=30.0)
    max_retries = fields.Integer(string="Max Failover Retries", default=3)
    line_ids = fields.One2many("gpu.service.combo.line", "combo_id", string="Target Chain Order")
    targets_summary = fields.Char(string="Execution Chain", compute="_compute_targets_summary", store=True)
    line_count = fields.Integer(string="Targets Count", compute="_compute_line_count")
    description = fields.Text(string="Description & SLA")

    _code_uniq = models.Constraint(
        "unique (code)",
        "Combo identifier must be unique!",
    )

    @api.depends("line_ids", "line_ids.sequence", "line_ids.target_model", "line_ids.active")
    def _compute_targets_summary(self):
        for rec in self:
            active_lines = rec.line_ids.filtered(lambda l: l.active).sorted("sequence")
            rec.targets_summary = " → ".join(l.target_model for l in active_lines) if active_lines else "No targets configured"

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)


class GpuServiceComboLine(models.Model):
    _name = "gpu.service.combo.line"
    _description = "GPU Service Combo Chain Target"
    _order = "sequence asc, id asc"

    combo_id = fields.Many2one("gpu.service.combo", string="Combo", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(string="Sequence / Priority Order", default=10)
    target_model = fields.Char(string="Target Model / Route", required=True,
                               help="e.g. 'thapsang/wan2.2-s2v' or 'modal/wan2.2-s2v'")
    provider_id = fields.Many2one("gpu.provider", string="Provider Target", ondelete="set null")
    endpoint = fields.Char(string="Endpoint", default="/v1/videos/generations")
    weight = fields.Integer(string="Routing Weight", default=1)
    active = fields.Boolean(default=True)
    notes = fields.Char(string="Target Description")
