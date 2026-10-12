# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.

import base64
import csv
import io
import re
import hashlib
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Al2cTimesheetStaging(models.Model):
    _name = 'al2c.timesheet.staging'
    _description = 'AL2C Timesheet Staging & Ingestion Buffer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Submission Subject', required=True, tracking=True)
    sender_email = fields.Char(string='Sender Email', required=True, index=True, tracking=True)
    submission_channel = fields.Selection([
        ('email_pubsub', 'Email Pub/Sub (info@inno.ai.vn)'),
        ('api_webhook', 'Inbound API Webhook'),
        ('manual_upload', 'Manual CSV/Excel Upload'),
        ('mobile_sync', 'Mobile Edge Sync'),
    ], string='Ingestion Channel', default='email_pubsub', required=True, tracking=True)
    submission_date = fields.Datetime(string='Submission Timestamp', default=fields.Datetime.now, required=True)
    
    employee_id = fields.Many2one('hr.employee', string='Identified Consultant', index=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Submitter User', tracking=True)
    project_id = fields.Many2one('project.project', string='Default Target Project', tracking=True)

    state = fields.Selection([
        ('received', 'Received / Pending Parse'),
        ('parsed', 'Parsed / Pending Review'),
        ('approved', 'Approved & Committed'),
        ('rejected', 'Rejected by PM'),
        ('duplicate', 'Duplicate Submission'),
    ], string='Ingestion Status', default='received', required=True, tracking=True, index=True)

    raw_email_body = fields.Text(string='Raw Email / Payload Body')
    raw_payload_json = fields.Text(string='Raw Ingestion Payload (JSON)')
    attachment_ids = fields.Many2many('ir.attachment', 'al2c_timesheet_staging_attachment_rel',
                                      'staging_id', 'attachment_id', string='Timesheet Attachments')

    line_ids = fields.One2many('al2c.timesheet.staging.line', 'staging_id', string='Staging Entries')
    total_hours = fields.Float(string='Total Hours', compute='_compute_totals', store=True)
    line_count = fields.Integer(string='Line Count', compute='_compute_totals', store=True)

    dedup_fingerprint = fields.Char(string='Deduplication Fingerprint', index=True, readonly=True)
    external_nonce = fields.Char(string='External Nonce / Idempotency Key', index=True, readonly=True)
    parse_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Successfully Parsed'),
        ('partial_error', 'Partially Parsed (Warnings)'),
        ('error', 'Parse Failure'),
    ], string='Parse Diagnostics', default='pending', tracking=True)
    parse_log = fields.Text(string='Parser Diagnostics Log')

    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approval Timestamp', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')

    @api.depends('line_ids.unit_amount', 'line_ids.state')
    def _compute_totals(self):
        for rec in self:
            valid_lines = rec.line_ids.filtered(lambda l: l.state not in ['error', 'duplicate'])
            rec.total_hours = sum(valid_lines.mapped('unit_amount'))
            rec.line_count = len(rec.line_ids)

    @api.model
    def compute_dedup_hash(self, sender, subject, body_or_lines):
        """Computes deterministic SHA-256 fingerprint for idempotency."""
        normalized = f"{sender.strip().lower()}|{subject.strip().lower()}|{str(body_or_lines).strip()}"
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Standard Odoo email gateway entrypoint: automatically creates a timesheet staging
        record when an email is routed to info@inno.ai.vn or timesheet aliases."""
        if custom_values is None:
            custom_values = {}

        sender = msg_dict.get('from', '')
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        sender_email = email_match.group(0) if email_match else sender

        subject = msg_dict.get('subject', _("Timesheet Submission"))
        body = msg_dict.get('body', '')

        custom_values.update({
            'name': subject,
            'sender_email': sender_email,
            'submission_channel': 'email_pubsub',
            'raw_email_body': body,
            'dedup_fingerprint': self.compute_dedup_hash(sender_email, subject, body),
        })

        staging = super().message_new(msg_dict, custom_values=custom_values)

        if msg_dict.get('attachments'):
            att_ids = []
            for fname, content in msg_dict['attachments']:
                att = self.env['ir.attachment'].create({
                    'name': fname,
                    'raw': content if isinstance(content, bytes) else str(content).encode('utf-8'),
                    'res_model': staging._name,
                    'res_id': staging.id,
                })
                att_ids.append(att.id)
            if att_ids:
                staging.write({'attachment_ids': [(6, 0, att_ids)]})

        staging.action_parse_content()
        return staging

    def action_parse_content(self):
        """Parses timesheet data from attached CSV/Excel or structured body."""
        for rec in self:
            logs = []
            parsed_lines = []
            rec.line_ids.unlink()

            # 1. Match default consultant
            consultant = rec.employee_id
            if not consultant and rec.sender_email:
                consultant = self.env['hr.employee'].search([
                    '|', ('work_email', '=ilike', rec.sender_email.strip()),
                    ('private_email', '=ilike', rec.sender_email.strip())
                ], limit=1)
                if not consultant:
                    user = self.env['res.users'].search([('email', '=ilike', rec.sender_email.strip())], limit=1)
                    if user and user.employee_id:
                        consultant = user.employee_id
                if consultant:
                    rec.employee_id = consultant.id
                    logs.append(_("Matched consultant: %s (%s)") % (consultant.name, rec.sender_email))

            # 2. Try parsing attachments first (CSV / Excel)
            has_parsed_attachment = False
            for att in rec.attachment_ids:
                fname = (att.name or '').lower()
                raw_bytes = getattr(att, 'raw', None)
                if not raw_bytes and att.datas:
                    try:
                        raw_bytes = base64.b64decode(att.datas)
                    except Exception:
                        raw_bytes = att.datas if isinstance(att.datas, bytes) else str(att.datas).encode('utf-8')

                if fname.endswith('.csv'):
                    try:
                        content = raw_bytes.decode('utf-8', errors='replace') if raw_bytes else ""
                        csv_reader = csv.DictReader(io.StringIO(content))
                        for row in csv_reader:
                            line_val = rec._parse_row_dict(row, consultant)
                            if line_val:
                                parsed_lines.append(line_val)
                        has_parsed_attachment = True
                        logs.append(_("Parsed CSV attachment: %s with %d rows.") % (att.name, len(parsed_lines)))
                        break
                    except Exception as e:
                        logs.append(_("Error reading CSV attachment %s: %s") % (att.name, str(e)))

                elif fname.endswith(('.xlsx', '.xls')):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(filename=io.BytesIO(raw_bytes), data_only=True)
                        sheet = wb.active
                        rows = list(sheet.iter_rows(values_only=True))
                        if rows:
                            header = [str(c or '').strip().lower() for c in rows[0]]
                            for r in rows[1:]:
                                if not any(r):
                                    continue
                                row_dict = {header[i]: r[i] for i in range(min(len(header), len(r)))}
                                line_val = rec._parse_row_dict(row_dict, consultant)
                                if line_val:
                                    parsed_lines.append(line_val)
                            has_parsed_attachment = True
                            logs.append(_("Parsed Excel attachment: %s with %d rows.") % (att.name, len(parsed_lines)))
                            break
                    except Exception as e:
                        logs.append(_("Error reading Excel attachment %s: %s") % (att.name, str(e)))

            # 3. Fallback: Parse structured text in email body if no attachment parsed
            if not has_parsed_attachment and rec.raw_email_body:
                text_lines = rec.raw_email_body.splitlines()
                line_regex = re.compile(
                    r'^(?P<date>\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\s*[,|;\t]\s*'
                    r'(?P<project>[^,|;\t]+)\s*[,|;\t]\s*'
                    r'(?P<task>[^,|;\t]+)\s*[,|;\t]\s*'
                    r'(?P<hours>\d+(?:\.\d+)?)\s*[,|;\t]\s*'
                    r'(?P<desc>.*)$'
                )
                for line in text_lines:
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith('#'):
                        continue
                    m = line_regex.match(line_clean)
                    if m:
                        dt_str = m.group('date')
                        prj_str = m.group('project').strip()
                        tsk_str = m.group('task').strip()
                        hrs = float(m.group('hours'))
                        desc = m.group('desc').strip() or _("Consulting delivery")
                        row_dict = {
                            'date': dt_str,
                            'project': prj_str,
                            'task': tsk_str,
                            'hours': hrs,
                            'description': desc
                        }
                        val = rec._parse_row_dict(row_dict, consultant)
                        if val:
                            parsed_lines.append(val)

            # 4. Intra-batch duplicate check
            seen_tuples = set()
            for line_val in parsed_lines:
                if line_val['state'] == 'valid':
                    key = (line_val.get('employee_id'), line_val.get('task_id'), str(line_val.get('date')))
                    if key in seen_tuples:
                        line_val['state'] = 'duplicate'
                        line_val['validation_message'] = _("Duplicate entry within the same submission batch.")
                    else:
                        seen_tuples.add(key)

            # 5. Populate lines
            if parsed_lines:
                created_lines = self.env['al2c.timesheet.staging.line'].create(parsed_lines)
                error_count = len(created_lines.filtered(lambda l: l.state in ['error', 'duplicate']))
                rec.state = 'parsed'
                rec.parse_status = 'partial_error' if error_count > 0 else 'success'
                logs.append(_("Extraction completed: %d total lines (%d valid, %d warnings/duplicates).") %
                            (len(created_lines), len(created_lines) - error_count, error_count))
            else:
                rec.parse_status = 'error'
                logs.append(_("No timesheet entries could be parsed from email body or attachments."))

            rec.parse_log = "\n".join(logs)

    def _parse_row_dict(self, row, default_employee):
        """Converts raw row dict into al2c.timesheet.staging.line values."""
        norm = {str(k).lower().strip(): v for k, v in row.items() if k}
        date_raw = norm.get('date') or norm.get('ngay') or fields.Date.today()
        prj_raw = norm.get('project') or norm.get('du_an') or norm.get('project_code') or ''
        tsk_raw = norm.get('task') or norm.get('nhiem_vu') or norm.get('task_name') or ''
        hrs_raw = norm.get('hours') or norm.get('gio') or norm.get('unit_amount') or 0.0
        desc_raw = norm.get('description') or norm.get('mo_ta') or norm.get('name') or _("Timesheet delivery")

        # Parse date
        parsed_date = fields.Date.today()
        if isinstance(date_raw, str):
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                try:
                    parsed_date = datetime.strptime(date_raw.strip(), fmt).date()
                    break
                except ValueError:
                    pass

        # Parse hours
        try:
            hours = float(hrs_raw)
        except (ValueError, TypeError):
            hours = 0.0

        # Resolve Project
        project = None
        if prj_raw:
            project = self.env['project.project'].search([
                '|', ('name', '=ilike', str(prj_raw).strip()),
                '|', ('name', 'ilike', str(prj_raw).strip()),
                ('id', '=', int(prj_raw) if str(prj_raw).isdigit() else 0)
            ], limit=1)
        if not project and self.project_id:
            project = self.project_id

        # Resolve Task
        task = None
        if project and tsk_raw:
            task = self.env['project.task'].search([
                ('project_id', '=', project.id),
                '|', ('name', '=ilike', str(tsk_raw).strip()),
                ('name', 'ilike', str(tsk_raw).strip())
            ], limit=1)

        val_error = False
        state = 'valid'
        if not project:
            val_error = _("Target project not recognized: '%s'") % prj_raw
            state = 'error'
        elif hours <= 0:
            val_error = _("Invalid duration: %.2f hours") % hours
            state = 'error'
        elif hours > 24:
            val_error = _("Exceeded daily threshold: %.2f hours (> 24h)") % hours
            state = 'error'

        # Row-level deduplication against account.analytic.line
        if state == 'valid' and default_employee and task and parsed_date:
            existing = self.env['account.analytic.line'].search([
                ('employee_id', '=', default_employee.id),
                ('task_id', '=', task.id),
                ('date', '=', parsed_date),
            ], limit=1)
            if existing:
                state = 'duplicate'
                val_error = _("Duplicate: Consultant %s already has timesheet logged for task '%s' on %s (Analytic Line #%d)") % (
                    default_employee.name, task.name, parsed_date, existing.id
                )

        return {
            'staging_id': self.id,
            'date': parsed_date,
            'employee_id': default_employee.id if default_employee else False,
            'project_id': project.id if project else False,
            'task_id': task.id if task else False,
            'unit_amount': hours,
            'name': str(desc_raw).strip(),
            'state': state,
            'validation_message': val_error or '',
        }

    def action_approve_and_commit(self):
        """Validates SoD and commits valid lines into account.analytic.line."""
        self.ensure_one()
        is_manager = self.env.user.has_group('project.group_project_manager') or \
                     self.env.user.has_group('sales_team.group_sale_manager')
        if not is_manager:
            raise UserError(_("Segregation of Duties: Only a Project Manager or Sales Manager can commit timesheets."))

        valid_lines = self.line_ids.filtered(lambda l: l.state in ['valid', 'draft'])
        if not valid_lines:
            raise UserError(_("No valid lines to commit. Please review errors or duplicate lines first."))

        AnalyticLine = self.env['account.analytic.line']
        committed_count = 0
        for line in valid_lines:
            if line.analytic_line_id:
                continue

            user = line.employee_id.user_id if line.employee_id else self.env.user
            aal_vals = {
                'name': line.name or _("Consulting Delivery"),
                'project_id': line.project_id.id,
                'task_id': line.task_id.id if line.task_id else False,
                'employee_id': line.employee_id.id if line.employee_id else False,
                'user_id': user.id if user else self.env.uid,
                'date': line.date,
                'unit_amount': line.unit_amount,
            }
            new_aal = AnalyticLine.create(aal_vals)
            line.write({
                'analytic_line_id': new_aal.id,
                'state': 'committed',
            })
            committed_count += 1

        self.write({
            'state': 'approved',
            'approved_by_id': self.env.uid,
            'approved_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Timesheet approved & committed: %d lines (%.2f hours) written to analytic ledger.") %
                                (committed_count, self.total_hours))
        return True

    def action_reject(self):
        """Rejects the staging submission."""
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.message_post(body=_("Timesheet submission rejected by %s.") % self.env.user.name)


class Al2cTimesheetStagingLine(models.Model):
    _name = 'al2c.timesheet.staging.line'
    _description = 'AL2C Timesheet Staging Detail Line'
    _order = 'date desc, id desc'

    staging_id = fields.Many2one('al2c.timesheet.staging', string='Staging Parent', ondelete='cascade', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    employee_id = fields.Many2one('hr.employee', string='Consultant')
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Task')
    unit_amount = fields.Float(string='Hours Worked', digits=(5, 2), required=True)
    name = fields.Char(string='Activity Description', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ('duplicate', 'Duplicate Line'),
        ('error', 'Validation Warning'),
        ('committed', 'Committed to Timesheet'),
    ], string='Line Status', default='draft', required=True)
    
    validation_message = fields.Char(string='Validation Diagnostics')
    analytic_line_id = fields.Many2one('account.analytic.line', string='Committed Timesheet Line', readonly=True)
