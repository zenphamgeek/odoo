# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.

import base64
import csv
import io
import re
import hashlib
import logging
from datetime import datetime, date, timedelta

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
    def _resolve_consultant(self, email_or_identifier):
        """Resolves consultant employee across 3 tiers:
        Tier 1: hr.employee directly (work_email, private_email)
        Tier 2: res.users -> hr.employee (login, email, employee_id)
        Tier 3: res.partner -> hr.employee (email -> work_contact_id / address_home_id)
        Fallback: hr.employee search by name
        """
        if not email_or_identifier:
            return self.env['hr.employee']

        clean_str = str(email_or_identifier).strip()
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', clean_str)
        clean_email = email_match.group(0).lower() if email_match else clean_str.lower()

        # Tier 1: hr.employee directly
        emp = self.env['hr.employee'].search([
            '|', ('work_email', '=ilike', clean_email),
                 ('private_email', '=ilike', clean_email)
        ], limit=1)
        if emp:
            return emp

        # Tier 2: res.users -> hr.employee
        user = self.env['res.users'].search([
            '|', ('login', '=ilike', clean_email),
                 ('email', '=ilike', clean_email)
        ], limit=1)
        if user:
            if hasattr(user, 'employee_id') and user.employee_id:
                return user.employee_id
            emp = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if emp:
                return emp

        # Tier 3: res.partner -> hr.employee
        partner = self.env['res.partner'].search([('email', '=ilike', clean_email)], limit=1)
        if partner:
            emp = self.env['hr.employee'].search([
                '|', ('work_contact_id', '=', partner.id),
                     ('address_home_id', '=', partner.id)
            ], limit=1)
            if emp:
                return emp

        # Fallback by name if identifier is not an email
        if '@' not in clean_str:
            emp = self.env['hr.employee'].search([('name', '=ilike', clean_str)], limit=1)
            if emp:
                return emp

        return self.env['hr.employee']

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Standard Odoo email gateway entrypoint: automatically creates a timesheet staging
        record when an email is routed to info@inno.ai.vn or timesheet aliases."""
        if custom_values is None:
            custom_values = {}

        sender = msg_dict.get('email_from') or msg_dict.get('from', '')
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        sender_email = email_match.group(0) if email_match else sender

        subject = msg_dict.get('subject', _("Timesheet Submission"))
        body = msg_dict.get('body', '')

        # Multi-tier consultant resolution
        consultant = self._resolve_consultant(sender_email)
        user = consultant.user_id if consultant and consultant.user_id else (
            self.env['res.users'].search([('email', '=ilike', sender_email)], limit=1)
        )

        fingerprint = self.compute_dedup_hash(sender_email, subject, body)

        # Check for existing duplicate staging by fingerprint
        existing = self.search([('dedup_fingerprint', '=', fingerprint)], limit=1)
        initial_state = 'duplicate' if existing else 'received'

        custom_values.update({
            'name': subject,
            'sender_email': sender_email,
            'submission_channel': 'email_pubsub',
            'raw_email_body': body,
            'dedup_fingerprint': fingerprint,
            'employee_id': consultant.id if consultant else False,
            'user_id': user.id if user else False,
            'state': initial_state,
        })

        staging = super().message_new(msg_dict, custom_values=custom_values)

        if msg_dict.get('attachments'):
            att_ids = []
            Attachment = self.env['ir.attachment']
            for fname, content in msg_dict['attachments']:
                raw_bytes = content if isinstance(content, bytes) else str(content).encode('utf-8')
                att = Attachment.create({
                    'name': fname,
                    'raw': raw_bytes,
                    'res_model': staging._name,
                    'res_id': staging.id,
                })
                att_ids.append(att.id)
            if att_ids:
                staging.write({'attachment_ids': [(6, 0, att_ids)]})

        if staging.state != 'duplicate':
            staging.action_parse_content()

        return staging

    def action_parse_content(self):
        """Parses timesheet data from attached CSV/Excel (.xlsx via openpyxl, .xls via xlrd)
        or structured body with multi-tier consultant resolution and duplicate detection."""
        for rec in self:
            logs = []
            parsed_lines = []
            rec.line_ids.unlink()

            # 1. Match default consultant via multi-tier lookup
            consultant = rec.employee_id
            if not consultant and rec.sender_email:
                consultant = rec._resolve_consultant(rec.sender_email)
                if consultant:
                    rec.employee_id = consultant.id
                    if not rec.user_id and consultant.user_id:
                        rec.user_id = consultant.user_id.id
                    logs.append(_("Matched consultant via multi-tier lookup: %s (%s)") % (consultant.name, rec.sender_email))

            # 2. Try parsing attachments first (CSV / Excel .xlsx / .xls)
            has_parsed_attachment = False
            for att in rec.attachment_ids:
                fname = (att.name or '').lower()
                raw_bytes = getattr(att, 'raw', None)
                if hasattr(raw_bytes, 'content'):
                    raw_bytes = raw_bytes.content
                elif hasattr(raw_bytes, '__bytes__') and not isinstance(raw_bytes, (bytes, bytearray)):
                    raw_bytes = bytes(raw_bytes)
                if not raw_bytes and att.datas:
                    try:
                        raw_bytes = base64.b64decode(att.datas)
                    except Exception:
                        raw_bytes = att.datas if isinstance(att.datas, bytes) else str(att.datas).encode('utf-8')
                if isinstance(raw_bytes, str):
                    raw_bytes = raw_bytes.encode('utf-8')
                elif raw_bytes is not None and not isinstance(raw_bytes, (bytes, bytearray)):
                    try:
                        raw_bytes = bytes(raw_bytes)
                    except Exception:
                        raw_bytes = b''
                if not raw_bytes:
                    continue

                # 2.1 Excel .xlsx (openpyxl) - check extension or PK zip magic
                if fname.endswith(('.xlsx', '.xlsm', '.xltx')) or (raw_bytes[:4] == b'PK\x03\x04' and not fname.endswith(('.csv', '.txt'))):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(filename=io.BytesIO(raw_bytes), data_only=True)
                        sheet = wb.active
                        rows = list(sheet.iter_rows(values_only=True))
                        if rows:
                            header = [str(c or '').strip().lower() for c in rows[0]]
                            sheet_lines = 0
                            for r in rows[1:]:
                                if not any(r):
                                    continue
                                row_dict = {header[i]: r[i] for i in range(min(len(header), len(r)))}
                                line_val = rec._parse_row_dict(row_dict, consultant)
                                if line_val:
                                    parsed_lines.append(line_val)
                                    sheet_lines += 1
                            has_parsed_attachment = True
                            logs.append(_("Parsed Excel .xlsx attachment (%s): %d rows extracted.") % (att.name, sheet_lines))
                            break
                    except Exception as e:
                        logs.append(_("Error reading Excel .xlsx attachment %s: %s") % (att.name, str(e)))

                # 2.2 Excel .xls (xlrd) - check extension or OLE2 / BIFF2 magic
                elif fname.endswith('.xls') or raw_bytes[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' or (len(raw_bytes) > 4 and raw_bytes[:2] == b'\x09\x00'):
                    try:
                        import xlrd
                        book = xlrd.open_workbook(file_contents=raw_bytes)
                        sheet = book.sheet_by_index(0)
                        if sheet.nrows > 0:
                            header = [str(sheet.cell_value(0, c) or '').strip().lower() for c in range(sheet.ncols)]
                            sheet_lines = 0
                            for row_idx in range(1, sheet.nrows):
                                row_values = []
                                is_empty = True
                                for col_idx in range(sheet.ncols):
                                    c_type = sheet.cell_type(row_idx, col_idx)
                                    val = sheet.cell_value(row_idx, col_idx)
                                    if c_type == xlrd.XL_CELL_DATE:
                                        try:
                                            val = xlrd.xldate_as_datetime(val, book.datemode).date()
                                        except Exception:
                                            pass
                                    elif c_type == xlrd.XL_CELL_NUMBER:
                                        if val == int(val):
                                            val = int(val)
                                    if val is not None and str(val).strip() != '':
                                        is_empty = False
                                    row_values.append(val)
                                if is_empty:
                                    continue
                                row_dict = {header[i]: row_values[i] for i in range(min(len(header), len(row_values)))}
                                line_val = rec._parse_row_dict(row_dict, consultant)
                                if line_val:
                                    parsed_lines.append(line_val)
                                    sheet_lines += 1
                            has_parsed_attachment = True
                            logs.append(_("Parsed Excel .xls attachment (%s): %d rows extracted.") % (att.name, sheet_lines))
                            break
                    except Exception as e:
                        logs.append(_("Error reading Excel .xls attachment %s: %s") % (att.name, str(e)))

                # 2.3 CSV attachment
                elif fname.endswith(('.csv', '.txt')) or b',' in raw_bytes[:200] or b';' in raw_bytes[:200] or b'|' in raw_bytes[:200]:
                    try:
                        content = raw_bytes.decode('utf-8-sig', errors='replace')
                        first_line = content.splitlines()[0] if content.splitlines() else ''
                        delimiter = ','
                        for delim in (',', ';', '\t', '|'):
                            if delim in first_line:
                                delimiter = delim
                                break
                        csv_reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                        csv_lines = 0
                        for row in csv_reader:
                            line_val = rec._parse_row_dict(row, consultant)
                            if line_val:
                                parsed_lines.append(line_val)
                                csv_lines += 1
                        has_parsed_attachment = True
                        logs.append(_("Parsed CSV attachment (%s): %d rows extracted.") % (att.name, csv_lines))
                        break
                    except Exception as e:
                        logs.append(_("Error reading CSV attachment %s: %s") % (att.name, str(e)))

            # 3. Fallback: Parse structured text in email body if no attachment parsed
            if not has_parsed_attachment and rec.raw_email_body:
                text_lines = rec.raw_email_body.splitlines()
                line_regex = re.compile(
                    r'^(?P<date>\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\s*[,|;\t]\s*'
                    r'(?P<project>[^,|;\t]+)\s*[,|;\t]\s*'
                    r'(?P<task>[^,|;\t]+)\s*[,|;\t]\s*'
                    r'(?P<hours>\d+(?:\.\d+)?)\s*[,|;\t]?\s*'
                    r'(?P<desc>.*)$'
                )
                body_lines = 0
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
                            body_lines += 1
                if body_lines:
                    logs.append(_("Parsed %d timesheet rows from structured email body.") % body_lines)

            # 4. Intra-batch and Cross-staging Duplicate Checks
            seen_tuples = set()
            for line_val in parsed_lines:
                if line_val['state'] == 'valid':
                    emp_id = line_val.get('employee_id')
                    task_id = line_val.get('task_id')
                    dt_key = str(line_val.get('date'))
                    batch_key = (emp_id, task_id, dt_key)

                    # Intra-batch check
                    if batch_key in seen_tuples:
                        line_val['state'] = 'duplicate'
                        line_val['validation_message'] = _("Duplicate entry within the same submission batch.")
                    else:
                        seen_tuples.add(batch_key)
                        # Cross-staging check
                        if emp_id and task_id:
                            other_staging = self.env['al2c.timesheet.staging.line'].search([
                                ('staging_id', '!=', rec.id or 0),
                                ('employee_id', '=', emp_id),
                                ('task_id', '=', task_id),
                                ('date', '=', line_val.get('date')),
                                ('state', 'in', ['valid', 'committed']),
                            ], limit=1)
                            if other_staging:
                                line_val['state'] = 'duplicate'
                                line_val['validation_message'] = _(
                                    "Duplicate: Identical entry recorded in staging #%d (Line #%d)."
                                ) % (other_staging.staging_id.id, other_staging.id)

            # 5. Populate lines
            if parsed_lines:
                created_lines = self.env['al2c.timesheet.staging.line'].create(parsed_lines)
                error_count = len(created_lines.filtered(lambda l: l.state in ['error', 'duplicate']))
                valid_count = len(created_lines) - error_count
                rec.state = 'parsed'
                rec.parse_status = 'partial_error' if error_count > 0 else 'success'
                logs.append(_("Extraction completed: %d total lines (%d valid, %d warnings/duplicates).") %
                            (len(created_lines), valid_count, error_count))
            else:
                rec.parse_status = 'error'
                logs.append(_("No timesheet entries could be parsed from email body or attachments."))

            rec.parse_log = "\n".join(logs)

    def _parse_row_dict(self, row, default_employee):
        """Converts raw row dict into al2c.timesheet.staging.line values with
        robust column mapping, multi-tier consultant resolution, and row-level
        duplicate detection against account.analytic.line."""
        norm = {str(k).lower().strip(): v for k, v in row.items() if k is not None}

        # Resolve row-specific consultant if column present
        row_emp_str = (
            norm.get('consultant') or norm.get('employee') or norm.get('nhan_vien') or
            norm.get('email') or norm.get('consultant_email') or ''
        )
        line_employee = self._resolve_consultant(row_emp_str) if row_emp_str else default_employee

        date_raw = norm.get('date') or norm.get('ngay') or norm.get('ngày') or norm.get('work_date') or fields.Date.today()
        prj_raw = norm.get('project') or norm.get('du_an') or norm.get('dự án') or norm.get('project_code') or ''
        tsk_raw = norm.get('task') or norm.get('nhiem_vu') or norm.get('nhiệm vụ') or norm.get('task_name') or ''
        hrs_raw = norm.get('hours') or norm.get('gio') or norm.get('giờ') or norm.get('unit_amount') or norm.get('so_gio') or 0.0
        desc_raw = norm.get('description') or norm.get('mo_ta') or norm.get('mô tả') or norm.get('name') or _("Timesheet delivery")

        # Parse date
        parsed_date = fields.Date.today()
        if isinstance(date_raw, datetime):
            parsed_date = date_raw.date()
        elif isinstance(date_raw, date):
            parsed_date = date_raw
        elif isinstance(date_raw, (int, float)) and date_raw > 10000:
            parsed_date = date(1899, 12, 30) + timedelta(days=int(date_raw))
        elif isinstance(date_raw, str):
            clean_date = date_raw.strip()
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d'):
                try:
                    parsed_date = datetime.strptime(clean_date, fmt).date()
                    break
                except ValueError:
                    pass

        # Parse hours
        hours = 0.0
        if isinstance(hrs_raw, (int, float)):
            hours = float(hrs_raw)
        elif isinstance(hrs_raw, str):
            try:
                hours = float(hrs_raw.strip().replace(',', '.'))
            except (ValueError, TypeError):
                hours = 0.0

        # Resolve Project
        project = None
        if prj_raw:
            clean_prj = str(prj_raw).strip()
            project = self.env['project.project'].search([
                '|', ('name', '=ilike', clean_prj),
                '|', ('name', 'ilike', clean_prj),
                ('id', '=', int(clean_prj) if clean_prj.isdigit() else 0)
            ], limit=1)
        if not project and self.project_id:
            project = self.project_id

        # Resolve Task
        task = None
        if project and tsk_raw:
            clean_tsk = str(tsk_raw).strip()
            task = self.env['project.task'].search([
                ('project_id', '=', project.id),
                '|', ('name', '=ilike', clean_tsk),
                ('name', 'ilike', clean_tsk)
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
        if state == 'valid' and line_employee and task and parsed_date:
            existing_aal = self.env['account.analytic.line'].search([
                ('employee_id', '=', line_employee.id),
                ('task_id', '=', task.id),
                ('date', '=', parsed_date),
            ], limit=1)
            if existing_aal:
                state = 'duplicate'
                val_error = _("Duplicate: Consultant %s already has timesheet logged for task '%s' on %s (Analytic Line #%d)") % (
                    line_employee.name, task.name, parsed_date, existing_aal.id
                )

        return {
            'staging_id': self.id,
            'date': parsed_date,
            'employee_id': line_employee.id if line_employee else False,
            'project_id': project.id if project else False,
            'task_id': task.id if task else False,
            'unit_amount': hours,
            'name': str(desc_raw).strip(),
            'state': state,
            'validation_message': val_error or '',
        }

    def action_approve_and_commit(self):
        """Validates Segregation of Duties (SoD) and commits valid staging lines
        into account.analytic.line with robust telemetry and duplicate prevention."""
        self.ensure_one()
        is_manager = (
            self.env.user.has_group('project.group_project_manager') or
            self.env.user.has_group('sales_team.group_sale_manager') or
            self.env.is_superuser()
        )
        if not is_manager:
            raise UserError(_("Segregation of Duties: Only a Project Manager or Sales Manager can commit timesheets."))

        valid_lines = self.line_ids.filtered(lambda l: l.state in ['valid', 'draft'])
        if not valid_lines:
            raise UserError(_("No valid lines to commit. Please review errors or duplicate lines first."))

        AnalyticLine = self.env['account.analytic.line']
        committed_count = 0
        total_committed_hours = 0.0
        duplicates_skipped = len(self.line_ids.filtered(lambda l: l.state == 'duplicate'))
        errors_skipped = len(self.line_ids.filtered(lambda l: l.state == 'error'))

        for line in valid_lines:
            if line.analytic_line_id:
                continue

            # Real-time duplicate check against account.analytic.line before creation
            if line.employee_id and line.task_id and line.date:
                recent_dup = AnalyticLine.search([
                    ('employee_id', '=', line.employee_id.id),
                    ('task_id', '=', line.task_id.id),
                    ('date', '=', line.date),
                ], limit=1)
                if recent_dup:
                    line.write({
                        'state': 'duplicate',
                        'validation_message': _("Duplicate detected during approval: Analytic Line #%d exists.") % recent_dup.id
                    })
                    duplicates_skipped += 1
                    continue

            user = line.employee_id.user_id if line.employee_id and line.employee_id.user_id else self.env.user
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
            total_committed_hours += line.unit_amount

        if committed_count == 0:
            raise UserError(_("All eligible lines were skipped as duplicates during commit."))

        self.write({
            'state': 'approved',
            'approved_by_id': self.env.uid,
            'approved_date': fields.Datetime.now(),
        })

        telemetry_msg = _(
            "Timesheet approved & committed by %s: %d lines (%.2f hours) written to analytic ledger. "
            "(Skipped %d duplicate rows, %d invalid rows)."
        ) % (self.env.user.name, committed_count, total_committed_hours, duplicates_skipped, errors_skipped)

        self.message_post(body=telemetry_msg)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Timesheet Approved"),
                'message': telemetry_msg,
                'type': 'success',
                'sticky': False,
            }
        }

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
