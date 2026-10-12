# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.

import base64
import csv
import io
import re
import math
import uuid
import hashlib
import logging
from datetime import datetime, date, timedelta

import psycopg2
from psycopg2 import errors as pg_errors, IntegrityError

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class _IdempotentDuplicateDescriptor:
    """Descriptor that defaults to False on class level, reflects context on records,
    and supports test mock attribute assignment without unbounded memory leaks."""
    def __get__(self, instance, owner=None):
        if instance is None:
            return False
        if hasattr(instance, '__dict__') and '_is_idempotent_duplicate_val' in instance.__dict__:
            return bool(instance.__dict__['_is_idempotent_duplicate_val'])
        env = getattr(instance, 'env', None)
        if env and hasattr(env, 'context') and isinstance(env.context, dict):
            return bool(env.context.get('al2c_idempotent_duplicate', False))
        return False

    def __set__(self, instance, value):
        if instance is not None and hasattr(instance, '__dict__'):
            instance.__dict__['_is_idempotent_duplicate_val'] = bool(value)


class Al2cTimesheetStaging(models.Model):
    _name = 'al2c.timesheet.staging'
    _description = 'AL2C Timesheet Staging & Ingestion Buffer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # Requires Odoo >= 18.0 declarative models.Constraint API.
    # Authoritative database-level race backstops for idempotent timesheet ingestion.
    _external_nonce_unique = models.Constraint(
        'UNIQUE (external_nonce)',
        'External nonce must be unique.',
    )

    _is_idempotent_duplicate = _IdempotentDuplicateDescriptor()

    def _auto_init(self):
        super()._auto_init()
        # Buffering duplicates in staging is allowed, but a given fingerprint
        # may be COMMITTED/APPROVED to the analytic ledger at most once. Enforce that at the
        # DB level so the race-rescue in commit has a real IntegrityError to catch under concurrent ingestion.
        self.env.cr.execute("""
            ALTER TABLE al2c_timesheet_staging 
            DROP CONSTRAINT IF EXISTS al2c_timesheet_staging_dedup_fingerprint_unique;

            -- Pre-flight: demote any legacy approved duplicate rows so index builds cleanly
            UPDATE al2c_timesheet_staging s
            SET state = 'duplicate'
            WHERE state = 'approved'
              AND dedup_fingerprint IS NOT NULL
              AND id > (
                SELECT MIN(s2.id) FROM al2c_timesheet_staging s2
                WHERE s2.dedup_fingerprint = s.dedup_fingerprint
                  AND s2.state = 'approved'
              )
              AND NOT EXISTS (
                SELECT 1 FROM al2c_timesheet_staging_line l
                WHERE l.staging_id = s.id AND l.analytic_line_id IS NOT NULL
              );

            CREATE UNIQUE INDEX IF NOT EXISTS
                al2c_timesheet_staging_dedup_approved_uniq
            ON al2c_timesheet_staging (dedup_fingerprint)
            WHERE state = 'approved' AND dedup_fingerprint IS NOT NULL;
        """)




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
    external_nonce = fields.Char(string='External Nonce / Idempotency Key', index=True, readonly=True,
                                 default=lambda self: uuid.uuid4().hex)
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
        Tier 3: res.partner -> hr.employee (email -> work_contact_id)
        Fallback: hr.employee search by name
        """
        if not email_or_identifier:
            return self.env['hr.employee']

        clean_str = str(email_or_identifier).strip()
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', clean_str)
        clean_email = email_match.group(0).lower() if email_match else clean_str.lower()

        # Tier 1: hr.employee directly
        emps = self.env['hr.employee'].search([
            '|', ('work_email', '=ilike', clean_email),
                 ('private_email', '=ilike', clean_email)
        ], order='id asc', limit=2)
        if len(emps) > 1:
            emp_ids = getattr(emps, 'ids', [e.id for e in emps if hasattr(e, 'id')])
            _logger.warning("Ambiguous consultant email '%s' matches %d employees (IDs: %s); refusing silent attribution.", clean_email, len(emps), emp_ids)
            return self.env['hr.employee']
        elif len(emps) == 1:
            return emps[0]

        # Tier 2: res.users -> hr.employee
        users = self.env['res.users'].search([
            '|', ('login', '=ilike', clean_email),
                 ('email', '=ilike', clean_email)
        ], order='id asc', limit=2)
        if len(users) > 1:
            user_ids = getattr(users, 'ids', [u.id for u in users if hasattr(u, 'id')])
            _logger.warning("Ambiguous user email '%s' matches %d users (IDs: %s); refusing silent attribution.", clean_email, len(users), user_ids)
            return self.env['hr.employee']
        elif len(users) == 1:
            user = users[0]
            if hasattr(user, 'employee_id') and user.employee_id:
                return user.employee_id
            emp = self.env['hr.employee'].search([('user_id', '=', user.id)], order='id asc', limit=2)
            if len(emp) > 1:
                e_ids = getattr(emp, 'ids', [e.id for e in emp if hasattr(e, 'id')])
                _logger.warning("Ambiguous user ID %d links to %d employees (IDs: %s); refusing silent attribution.", user.id, len(emp), e_ids)
                return self.env['hr.employee']
            elif len(emp) == 1:
                return emp[0]

        # Tier 3: hr.employee via linked partner/contact email (work_contact_id)
        # Directly searches hr.employee across linked contact emails to avoid shadow unlinked partners
        domain_t3 = [('work_contact_id.email', '=ilike', clean_email)]
        emps_t3 = self.env['hr.employee'].search(domain_t3, order='id asc', limit=2)
        if len(emps_t3) > 1:
            e_ids = getattr(emps_t3, 'ids', [e.id for e in emps_t3 if hasattr(e, 'id')])
            _logger.warning("Ambiguous linked partner email '%s' matches %d employees (IDs: %s); refusing silent attribution.", clean_email, len(emps_t3), e_ids)
            return self.env['hr.employee']
        elif len(emps_t3) == 1:
            return emps_t3[0]

        # Fallback by name if identifier is not an email
        if '@' not in clean_str:
            name_emps = self.env['hr.employee'].search([('name', '=ilike', clean_str)], order='id asc', limit=2)
            if len(name_emps) > 1:
                n_ids = getattr(name_emps, 'ids', [e.id for e in name_emps if hasattr(e, 'id')])
                _logger.warning("Ambiguous consultant name '%s' matches %d employees (IDs: %s); refusing silent attribution.", clean_str, len(name_emps), n_ids)
                return self.env['hr.employee']
            elif len(name_emps) == 1:
                return name_emps[0]

        return self.env['hr.employee']

    @api.model
    def _create_idempotent(self, vals):
        """Creates a staging record idempotently.
        If external_nonce or dedup_fingerprint violates unique constraint under concurrent race,
        rescues transaction using a database savepoint and retrieves the existing record.
        """
        # Normalize empty string inputs to False so Postgres stores SQL NULL (avoiding empty-string collision)
        if isinstance(vals, dict):
            if 'external_nonce' in vals and not vals['external_nonce']:
                vals['external_nonce'] = False
            if 'dedup_fingerprint' in vals and not vals['dedup_fingerprint']:
                vals['dedup_fingerprint'] = False
        elif isinstance(vals, list):
            for v in vals:
                if isinstance(v, dict):
                    if 'external_nonce' in v and not v['external_nonce']:
                        v['external_nonce'] = False
                    if 'dedup_fingerprint' in v and not v['dedup_fingerprint']:
                        v['dedup_fingerprint'] = False

        val_dict = vals[0] if isinstance(vals, (list, tuple)) and vals else (vals if isinstance(vals, dict) else {})
        nonce = val_dict.get('external_nonce') or False
        fingerprint = val_dict.get('dedup_fingerprint') or False

        def _lookup():
            if nonce:
                rec = self.search([('external_nonce', '=', nonce)], order='id asc', limit=1)
                if rec:
                    return rec
            if fingerprint:
                rec = self.search([('dedup_fingerprint', '=', fingerprint)], order='id asc', limit=1)
                if rec:
                    return rec
            return False

        def _mark_duplicate(rec):
            if not rec:
                return rec
            if hasattr(rec, 'with_context'):
                try:
                    rec = rec.with_context(al2c_idempotent_duplicate=True)
                except Exception:
                    pass
            try:
                rec._is_idempotent_duplicate = True
            except Exception:
                pass
            return rec

        existing = _lookup()
        if existing:
            return _mark_duplicate(existing)

        try:
            with self.env.cr.savepoint():
                return self.create(vals)
        except (pg_errors.UniqueViolation, IntegrityError, ValidationError) as exc:
            _logger.info("Concurrent duplicate insertion prevented by idempotency constraint: %s", exc)
            winner = _lookup()
            if winner:
                return _mark_duplicate(winner)
            raise

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
        if existing:
            return existing

        custom_values.update({
            'name': subject,
            'sender_email': sender_email,
            'submission_channel': 'email_pubsub',
            'raw_email_body': body,
            'dedup_fingerprint': fingerprint,
            'employee_id': consultant.id if consultant else False,
            'user_id': user.id if user else False,
            'state': 'received',
        })

        try:
            with self.env.cr.savepoint():
                staging = super().message_new(msg_dict, custom_values=custom_values)
        except (pg_errors.UniqueViolation, IntegrityError, ValidationError):
            existing = self.search([('dedup_fingerprint', '=', fingerprint)], limit=1)
            if existing:
                return existing
            raise

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
                        raw_bytes = base64.b64decode(att.datas, validate=True)
                    except Exception as exc:
                        logs.append(_("Failed to decode attachment '%s' base64 payload: %s") % (att.name or 'unknown', exc))
                        continue
                if isinstance(raw_bytes, str):
                    raw_bytes = raw_bytes.encode('utf-8')
                elif raw_bytes is not None and not isinstance(raw_bytes, (bytes, bytearray)):
                    try:
                        raw_bytes = bytes(raw_bytes)
                    except Exception as exc:
                        logs.append(_("Corrupt non-byte attachment payload on '%s': %s") % (att.name or 'unknown', exc))
                        continue
                if not raw_bytes:
                    logs.append(_("Attachment '%s' contains empty payload; skipped.") % (att.name or 'unknown'))
                    continue

                # 2.1 Excel .xlsx (openpyxl) - check extension or PK zip magic
                if fname.endswith(('.xlsx', '.xlsm', '.xltx')) or (raw_bytes[:4] == b'PK\x03\x04' and not fname.endswith(('.csv', '.txt'))):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(filename=io.BytesIO(raw_bytes), data_only=True)
                        sheet = wb.active
                        if sheet.max_row > 100_000 or sheet.max_column > 512:
                            raise UserError(_("Spreadsheet exceeds safe size limits (%s x %s). Maximum allowed is 100,000 rows x 512 columns.") % (sheet.max_row, sheet.max_column))
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
                    except UserError:
                        raise
                    except Exception as e:
                        logs.append(_("Error reading Excel .xlsx attachment %s: %s") % (att.name, str(e)))

                # 2.2 Excel .xls (xlrd) - check extension or OLE2 / BIFF2 magic
                elif fname.endswith('.xls') or raw_bytes[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' or (len(raw_bytes) > 4 and raw_bytes[:2] == b'\x09\x00'):
                    try:
                        import xlrd
                        book = xlrd.open_workbook(file_contents=raw_bytes)
                        sheet = book.sheet_by_index(0)
                        if sheet.nrows > 100_000 or sheet.ncols > 512:
                            raise UserError(_("Spreadsheet exceeds safe size limits (%s x %s). Maximum allowed is 100,000 rows x 512 columns.") % (sheet.nrows, sheet.ncols))
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
                                        try:
                                            if not math.isnan(val) and not math.isinf(val) and val == int(val):
                                                val = int(val)
                                        except Exception:
                                            pass
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
                    except UserError:
                        raise
                    except Exception as e:
                        logs.append(_("Error reading Excel .xls attachment %s: %s") % (att.name, str(e)))

                # 2.3 CSV attachment - strictly validate tabular text extension or text mimetype and verify absence of null bytes
                elif (
                    fname.endswith(('.csv', '.txt', '.tsv')) or
                    (bool(getattr(att, 'mimetype', False)) and att.mimetype.lower() in ('text/csv', 'text/plain', 'text/tab-separated-values', 'application/csv'))
                ) and not fname.endswith(('.bin', '.exe', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.7z', '.iso', '.doc', '.docx', '.mp4', '.mp3', '.pyc', '.so')) and b'\x00' not in raw_bytes[:512]:
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
                            csv_lines += 1
                            if csv_lines > 100_000:
                                raise UserError(_("Spreadsheet exceeds safe size limits (rows > 100,000)."))
                            line_val = rec._parse_row_dict(row, consultant)
                            if line_val:
                                parsed_lines.append(line_val)
                        has_parsed_attachment = True
                        logs.append(_("Parsed CSV attachment (%s): %d rows extracted.") % (att.name, csv_lines))
                        break
                    except UserError:
                        raise
                    except Exception as e:
                        logs.append(_("Error reading CSV attachment %s: %s") % (att.name, str(e)))
                else:
                    logs.append(_("Attachment '%s' is not a recognized spreadsheet or delimited text format; skipped.") % (att.name or 'unknown'))

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
                emp_id = line_val.get('employee_id')
                task_id = line_val.get('task_id')
                dt_key = str(line_val.get('date'))
                # If consultant is unresolved, use sender_email as dedup identifier
                dedup_consultant_key = emp_id or (rec.sender_email.strip().lower() if rec.sender_email else 'anon')
                batch_key = (dedup_consultant_key, task_id, dt_key)

                # Intra-batch check
                if batch_key in seen_tuples:
                    line_val['state'] = 'duplicate'
                    line_val['validation_message'] = _("Duplicate entry within the same submission batch.")
                else:
                    seen_tuples.add(batch_key)
                    # Cross-staging check
                    if task_id:
                        domain = [
                            ('staging_id', '!=', rec.id or 0),
                            ('task_id', '=', task_id),
                            ('date', '=', line_val.get('date')),
                            ('state', 'in', ['valid', 'committed', 'error', 'duplicate']),
                        ]
                        if emp_id:
                            domain.append(('employee_id', '=', emp_id))
                        elif rec.sender_email:
                            domain.append(('staging_id.sender_email', '=ilike', rec.sender_email.strip()))
                        other_staging = self.env['al2c.timesheet.staging.line'].search(domain, limit=1)
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

        date_raw = norm.get('date') or norm.get('ngay') or norm.get('ngày') or norm.get('work_date')
        prj_raw = norm.get('project') or norm.get('du_an') or norm.get('dự án') or norm.get('project_code') or ''
        tsk_raw = norm.get('task') or norm.get('nhiem_vu') or norm.get('nhiệm vụ') or norm.get('task_name') or ''
        hrs_raw = norm.get('hours') or norm.get('gio') or norm.get('giờ') or norm.get('unit_amount') or norm.get('so_gio')
        desc_raw = norm.get('description') or norm.get('mo_ta') or norm.get('mô tả') or norm.get('name') or _("Timesheet delivery")

        # Parse date
        parsed_date = None
        date_error = False
        if date_raw is None or str(date_raw).strip() == '':
            parsed_date = fields.Date.today()
        elif isinstance(date_raw, datetime):
            parsed_date = date_raw.date()
        elif isinstance(date_raw, date):
            parsed_date = date_raw
        elif isinstance(date_raw, (int, float)):
            try:
                if not math.isnan(date_raw) and not math.isinf(date_raw) and date_raw > 10000:
                    parsed_date = date(1899, 12, 30) + timedelta(days=int(date_raw))
                else:
                    date_error = True
            except Exception:
                date_error = True
        elif isinstance(date_raw, str):
            clean_date = date_raw.strip()
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d'):
                try:
                    parsed_date = datetime.strptime(clean_date, fmt).date()
                    break
                except ValueError:
                    pass
            if not parsed_date:
                date_error = True
        else:
            date_error = True

        if date_error or not parsed_date:
            parsed_date = fields.Date.today()

        # Parse hours safely against NaN / Inf / non-numeric injection
        hours = 0.0
        hrs_error = False
        if isinstance(hrs_raw, (int, float)):
            try:
                if math.isnan(hrs_raw) or math.isinf(hrs_raw):
                    hrs_error = True
                    hours = 0.0
                else:
                    hours = float(hrs_raw)
            except Exception:
                hrs_error = True
                hours = 0.0
        elif isinstance(hrs_raw, str):
            try:
                clean_hrs = hrs_raw.strip().replace(',', '.')
                if clean_hrs.lower() in ('nan', 'inf', '-inf', 'none', 'null', ''):
                    hrs_error = True
                    hours = 0.0
                else:
                    val = float(clean_hrs)
                    if math.isnan(val) or math.isinf(val):
                        hrs_error = True
                        hours = 0.0
                    else:
                        hours = val
            except (ValueError, TypeError):
                hrs_error = True
                hours = 0.0
        else:
            hrs_error = True
            hours = 0.0

        if hrs_error or math.isnan(hours) or math.isinf(hours):
            hours = 0.0
            hrs_error = True

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
        if hrs_error or hours <= 0:
            val_error = _("Invalid duration: %s hours") % hrs_raw
            state = 'error'
            hours = 0.0
        elif hours > 24:
            val_error = _("Exceeded daily threshold: %.2f hours (> 24h)") % hours
            state = 'error'
        elif date_error:
            val_error = _("Invalid date format: '%s'") % str(date_raw)
            state = 'error'
        elif not project:
            val_error = _("Target project not recognized: '%s'") % prj_raw
            state = 'error'
        elif not line_employee:
            consultant_email = str(row_emp_str).strip() if row_emp_str else ''
            sender_id = (self.sender_email or '').strip() if (self and hasattr(self, 'sender_email')) else ''
            val_error = _("Consultant identity unresolved from sender or row email: %s") % (consultant_email or sender_id or 'unknown')
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

        # Safeguard: ensure hours is never NaN or Inf under any circumstances
        if math.isnan(hours) or math.isinf(hours):
            hours = 0.0

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

        try:
            with self.env.cr.savepoint():
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
        except (pg_errors.UniqueViolation, IntegrityError):
            # Atomic savepoint rolled back all AnalyticLine records and staging line state mutations
            self.write({
                'state': 'duplicate',
                'rejection_reason': _("Duplicate commit collision: an identical timesheet payload has already been approved and committed to the analytic ledger.")
            })
            raise UserError(_("Duplicate commit collision: an identical timesheet payload has already been approved and committed."))

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
