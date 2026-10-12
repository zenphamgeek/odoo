# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Crash Reporting & Incident Gatekeeper.

import hashlib
import re
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Al2cRuntimeIncident(models.Model):
    _name = 'al2c.runtime.incident'
    _description = 'Insilos Runtime Error Incident & Telemetry Tracker'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'last_seen_date desc, occurrence_count desc, id desc'

    name = fields.Char(string='Incident Title', required=True, tracking=True)
    incident_code = fields.Char(string='Incident Code', required=True, index=True, tracking=True)
    fingerprint = fields.Char(string='Error Fingerprint (SHA256)', required=True, index=True)

    asset_id = fields.Many2one('al2c.tech.asset', string='Affected Tech Asset', index=True, tracking=True)
    error_name = fields.Char(string='Exception / Error Class', required=True, tracking=True)
    error_message = fields.Text(string='Primary Error Message')
    traceback = fields.Text(string='Sanitized Stack Trace')
    component_stack = fields.Text(string='Client Component Stack')

    # Originating Telemetry
    instance_id = fields.Char(string='Originating Instance ID', index=True, tracking=True)
    instance_url = fields.Char(string='Originating URL')
    user_identifier = fields.Char(string='User Hash (PDPL Redacted)')
    client_info = fields.Char(string='Client Platform & Browser')
    server_version = fields.Char(string='Server Version / Commit')

    # Occurrence & Timeline
    occurrence_count = fields.Integer(string='Occurrences Count', default=1, tracking=True)
    first_seen_date = fields.Datetime(string='First Detected', default=fields.Datetime.now, readonly=True)
    last_seen_date = fields.Datetime(string='Last Detected', default=fields.Datetime.now, tracking=True)

    severity = fields.Selection([
        ('critical', 'Critical (Crash / Blocker)'),
        ('high', 'High (RPC / Data Flow Failure)'),
        ('medium', 'Medium (UI Glitch / Transient)'),
        ('low', 'Low (Warning / Non-fatal)'),
    ], string='Severity', default='high', required=True, tracking=True)

    state = fields.Selection([
        ('new', 'New Incident'),
        ('triaged', 'Triaged'),
        ('in_backlog', 'In Autonomous Backlog'),
        ('resolved', 'Resolved & Deployed'),
        ('ignored', 'Ignored / Known Flake'),
    ], string='Status', default='new', required=True, tracking=True)

    improvement_id = fields.Many2one('al2c.tech.asset.improvement', string='Linked Backlog v2 Item', tracking=True)

    @api.model
    def compute_fingerprint(self, error_name, traceback_str, asset_code=None):
        """Generates a stable normalized SHA256 fingerprint from the root cause in the stack trace."""
        clean_name = (error_name or 'Error').strip()
        lines = [l.strip() for l in (traceback_str or '').splitlines() if l.strip()]

        # Filter out line numbers or timestamps to ensure deterministic hashing across environments
        normalized_frames = []
        for line in lines:
            normalized = re.sub(r'line \d+', 'line X', line)
            normalized = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', normalized)
            normalized = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', 'TIMESTAMP', normalized)
            normalized_frames.append(normalized)

        root_sample = "\n".join(normalized_frames[-6:]) if normalized_frames else clean_name
        hash_input = f"{clean_name}:{root_sample}:{asset_code or ''}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    def action_create_backlog_improvement(self):
        """Converts runtime incident into a Backlog v2 improvement item for the associated tech asset."""
        improvement_model = self.env['al2c.tech.asset.improvement']
        for incident in self:
            if incident.improvement_id:
                raise UserError(_("This incident is already linked to backlog item %s") % incident.improvement_id.item_code)

            asset = incident.asset_id or self.env['al2c.tech.asset'].search([('code', '=', 'O20')], limit=1)
            if not asset:
                raise UserError(_("No technology asset associated with this incident."))

            code = f"AL2C-{asset.code}-BUG{self.env['ir.sequence'].next_by_code('al2c.runtime.incident') or incident.id:03d}"
            priority = 'P0' if incident.severity == 'critical' else 'P1'

            dod = f"Replicate and verify fix for '{incident.name[:60]}' — Automated test passes with 0 tracebacks."
            new_item = improvement_model.create({
                'asset_id': asset.id,
                'name': f"Fix Runtime Crash: {incident.name[:80]}",
                'item_code': code,
                'priority': priority,
                'category': 'testing',
                'risk_level': 'R2' if priority == 'P0' else 'R1',
                'description': f"Runtime Error reported from instance {incident.instance_id or 'unknown'} ({incident.occurrence_count} occurrences).\n\n"
                               f"Message: {incident.error_message}\n\nTraceback:\n{incident.traceback}\n\nClient Info: {incident.client_info}",
                'definition_of_done': dod,
                'target_file_path': asset.repo_path,
                'verification_command': f"pytest tests",
                'estimated_hours': 4.0 if priority == 'P0' else 2.0,
                'state': 'queued',
            })

            incident.write({
                'improvement_id': new_item.id,
                'state': 'in_backlog',
            })

        return True

    def action_mark_resolved(self):
        self.write({'state': 'resolved'})
