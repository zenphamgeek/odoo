# -*- coding: utf-8 -*-
# Part of Insilos AL2C (Autonomous Lead-to-Cash) Enterprise Engine.

import base64
import hashlib
import hmac
import json
import logging
import time
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

_MAX_BODY = 256 * 1024  # Reject oversized payloads (> 256 KB) (Anti-DoS / CWE-400)
_TS_WINDOW = 300        # 5 minute replay window (Replay Mitigation)


class Al2cTimesheetWebhookController(http.Controller):

    @http.route(['/api/v1/timesheet/ingest', '/api/v1/timesheet/ingest/'],
                type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False, cors=False, website=False, multilang=False)
    def timesheet_ingest(self, **kwargs):
        """Inbound webhook receiving timesheet submissions with strict HMAC authentication."""
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Allow': 'POST, OPTIONS',
            }
            return Response(status=204, headers=headers)

        headers = {'Content-Type': 'application/json'}

        # 1. Payload size guard (Anti-DoS / CWE-400)
        raw_data = request.httprequest.get_data(cache=False, as_text=False)
        if len(raw_data) > _MAX_BODY:
            _logger.warning("Timesheet webhook rejected: payload exceeds %d bytes (got %d)", _MAX_BODY, len(raw_data))
            return Response(json.dumps({'error': 'Payload Too Large', 'max_bytes': _MAX_BODY}), status=413, headers=headers)

        if not raw_data:
            return Response(json.dumps({'error': 'Empty payload'}), status=400, headers=headers)

        # 2. HMAC & Timestamp signature verification (CWE-306, CWE-327)
        sig = request.httprequest.headers.get('X-Signature', '').strip()
        ts = request.httprequest.headers.get('X-Timestamp', '').strip()

        env = request.env(su=True)
        secret = env['ir.config_parameter'].get_param('insilos_al2c.timesheet_webhook_secret') or \
                 env['ir.config_parameter'].get_param('al2c.timesheet_webhook_secret') or \
                 request.httprequest.environ.get('AL2C_TIMESHEET_WEBHOOK_SECRET', '')

        if not secret or not sig or not ts:
            _logger.warning("Timesheet webhook rejected: missing secret, signature, or timestamp header")
            return Response(json.dumps({'error': 'Unauthorized', 'detail': 'Missing signature headers or unconfigured secret'}), status=401, headers=headers)

        # Timestamp freshness guard (5 min window)
        try:
            req_time = float(ts)
            if abs(time.time() - req_time) > _TS_WINDOW:
                _logger.warning("Timesheet webhook rejected: timestamp skew exceeds window (skew: %.2fs)", abs(time.time() - req_time))
                return Response(json.dumps({'error': 'Unauthorized', 'detail': 'Timestamp expired or clock skew exceeds threshold'}), status=401, headers=headers)
        except (ValueError, TypeError):
            return Response(json.dumps({'error': 'Invalid X-Timestamp header'}), status=400, headers=headers)

        # Constant-time HMAC-SHA256 comparison (CWE-208, CWE-327)
        expected_sig = hmac.new(secret.encode('utf-8'), ts.encode('utf-8') + b'.' + raw_data, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig.lower(), sig.lower()):
            _logger.warning("Timesheet webhook rejected: invalid HMAC signature")
            return Response(json.dumps({'error': 'Unauthorized', 'detail': 'Invalid signature'}), status=401, headers=headers)

        # 3. Parse JSON payload
        try:
            payload = json.loads(raw_data.decode('utf-8'))
            if not isinstance(payload, dict):
                return Response(json.dumps({'error': 'Invalid payload format: root must be JSON object'}), status=400, headers=headers)
        except Exception as e:
            _logger.warning("Failed to decode timesheet webhook JSON: %s", str(e))
            return Response(json.dumps({'error': 'Invalid JSON', 'detail': str(e)}), status=400, headers=headers)

        sender = payload.get('sender') or payload.get('from') or 'unknown@inno.ai.vn'
        subject = payload.get('subject') or 'Timesheet Submission'
        body = payload.get('body') or payload.get('text_content') or payload.get('text') or ''
        channel = payload.get('channel') or 'email_pubsub'
        attachments = payload.get('attachments') or []
        nonce = payload.get('nonce')

        StagingModel = env['al2c.timesheet.staging']

        # 4. Idempotency & Replay Protection: Nonce & Fingerprint Deduplication
        if nonce:
            existing_nonce = StagingModel.search([('external_nonce', '=', str(nonce).strip())], limit=1)
            if existing_nonce:
                _logger.info("Duplicate timesheet submission detected by nonce: %s (ID %d)", nonce, existing_nonce.id)
                return Response(json.dumps({
                    'status': 'duplicate',
                    'staging_id': existing_nonce.id,
                    'message': 'Duplicate submission identified by nonce; ignored.',
                }), status=200, headers=headers)

        fingerprint = StagingModel.compute_dedup_hash(sender, subject, body)
        existing_fp = StagingModel.search([('dedup_fingerprint', '=', fingerprint)], limit=1)
        if existing_fp:
            _logger.info("Duplicate timesheet submission detected by fingerprint: %s (ID %d)", fingerprint, existing_fp.id)
            return Response(json.dumps({
                'status': 'duplicate',
                'staging_id': existing_fp.id,
                'message': 'Duplicate submission identified; ignored.',
            }), status=200, headers=headers)

        # 5. Create staging record (scoped values only, never raw external dict)
        valid_channels = dict(StagingModel._fields['submission_channel'].selection)
        consultant = StagingModel._resolve_consultant(sender)
        user = consultant.user_id if consultant and consultant.user_id else False
        staging_vals = {
            'name': str(subject)[:200],
            'sender_email': str(sender)[:200],
            'submission_channel': channel if channel in valid_channels else 'api_webhook',
            'employee_id': consultant.id if consultant else False,
            'user_id': user.id if user else False,
            'raw_email_body': str(body),
            'raw_payload_json': json.dumps(payload),
            'dedup_fingerprint': fingerprint,
            'external_nonce': str(nonce).strip() if nonce else False,
            'state': 'received',
        }
        staging = StagingModel._create_idempotent(staging_vals)
        if getattr(staging, '_is_idempotent_duplicate', None) is True:
            return Response(json.dumps({
                'status': 'duplicate',
                'staging_id': staging.id,
                'message': 'Duplicate submission identified; ignored.',
            }), status=200, headers=headers)

        # 6. Create and attach any binary attachments
        Attachment = env['ir.attachment']
        for att in attachments:
            if not isinstance(att, dict):
                continue
            fname = att.get('filename') or 'timesheet.csv'
            b64_content = att.get('content_base64') or att.get('content')
            if b64_content:
                try:
                    att_vals = {
                        'name': str(fname)[:100],
                        'res_model': 'al2c.timesheet.staging',
                        'res_id': staging.id,
                        'type': 'binary',
                    }
                    if isinstance(b64_content, str):
                        try:
                            # Verify if string is valid base64
                            base64.b64decode(b64_content, validate=True)
                            att_vals['datas'] = b64_content
                        except Exception:
                            att_vals['raw'] = b64_content.encode('utf-8')
                    elif isinstance(b64_content, bytes):
                        att_vals['raw'] = b64_content
                    else:
                        att_vals['raw'] = str(b64_content).encode('utf-8')

                    att_rec = Attachment.create(att_vals)
                    staging.attachment_ids = [(4, att_rec.id)]
                except Exception as ex:
                    _logger.warning("Could not attach timesheet file %s: %s", fname, str(ex))

        # 7. Trigger auto-parse
        try:
            staging.action_parse_content()
        except Exception as e:
            _logger.exception("Error while auto-parsing timesheet staging %d: %s", staging.id, str(e))

        return Response(json.dumps({
            'status': 'received',
            'staging_id': staging.id,
            'parse_status': staging.parse_status,
            'line_count': staging.line_count,
            'total_hours': staging.total_hours,
            'message': 'Timesheet staged successfully.',
        }), status=201, headers=headers)
