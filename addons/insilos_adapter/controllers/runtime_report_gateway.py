# -*- coding: utf-8 -*-
# Part of Insilos Ports & Adapters Gateway.
# Sovereign Anti-DoS Ingress Gatekeeper & Runtime Incident Reporting Engine.

import json
import time
import hmac
import hashlib
import logging
import os
import tempfile
import urllib.request
from collections import defaultdict
from odoo import http, fields, api, SUPERUSER_ID, _
from odoo.http import request, Response
from odoo.modules.registry import Registry

_logger = logging.getLogger("insilos.runtime.gateway")

# In-memory Anti-DoS sliding window rate limiters (ephemeral process memory)
_INSTANCE_RATE_LIMIT = defaultdict(list)
_IP_RATE_LIMIT = defaultdict(list)
_DEDUP_CACHE = {}  # fingerprint -> (incident_code, timestamp, hit_count)

MAX_PAYLOAD_BYTES = 256 * 1024  # 256 KB hard limit to prevent memory exhaustion
MAX_INSTANCE_BURST_PER_MIN = 20
MAX_IP_BURST_PER_MIN = 6
TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutes replay window
DEFAULT_HMAC_SECRET = "insilos-enterprise-runtime-sovereign-2026"
AUDIT_LOG_PATH = "/var/lib/insilos/filestore/runtime_incidents.jsonl"


def _check_rate_limit(store, key, limit_per_min):
    now = time.time()
    cutoff = now - 60.0
    store[key] = [t for t in store[key] if t > cutoff]
    if len(store[key]) >= limit_per_min:
        return False
    store[key].append(now)
    return True


def _append_audit_ledger(incident_dict):
    """Resilient append to persistent JSONL ledger."""
    paths_to_try = [
        AUDIT_LOG_PATH,
        os.path.join(tempfile.gettempdir(), "runtime_incidents.jsonl"),
    ]
    for path in paths_to_try:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(incident_dict, ensure_ascii=False) + "\n")
            return
        except Exception:
            continue


class RuntimeReportGateway(http.Controller):

    @http.route(['/api/v1/runtime-report', '/api/v1/runtime-report/'], type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*', website=False, multilang=False)
    def ingress_runtime_report(self, **kwargs):
        """Public-facing Ingress Gateway endpoint for Insilos Runtime Error Reporting.
        Protected by Multi-Layer Anti-DoS, HMAC Signature Verification, and Fingerprint Deduplication.
        """
        # Handle CORS pre-flight
        if request.httprequest.method == 'OPTIONS':
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, X-Insilos-Instance-Id, X-Insilos-Timestamp, X-Insilos-Signature, Authorization'),
            ]
            return Response(status=204, headers=headers)

        # 1. Anti-DoS: Payload Size Gating (< 256 KB)
        raw_data = request.httprequest.get_data()
        if not raw_data or len(raw_data) > MAX_PAYLOAD_BYTES:
            _logger.warning("Rejected runtime report: payload size %d exceeds %d bytes limit", len(raw_data or b''), MAX_PAYLOAD_BYTES)
            return Response(
                json.dumps({'error': 'Payload Too Large', 'max_bytes': MAX_PAYLOAD_BYTES}),
                status=413, content_type='application/json'
            )

        # 2. Anti-DoS: IP Rate Limiting (6 req/min)
        client_ip = (
            request.httprequest.headers.get('CF-Connecting-IP')
            or request.httprequest.headers.get('X-Forwarded-For')
            or request.httprequest.remote_addr
        )
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        if not _check_rate_limit(_IP_RATE_LIMIT, client_ip or 'unknown_ip', MAX_IP_BURST_PER_MIN):
            _logger.warning("Rate limit exceeded for IP: %s", client_ip)
            return Response(
                json.dumps({'error': 'Too Many Requests', 'retry_after': 60}),
                status=429, headers=[('Retry-After', '60')], content_type='application/json'
            )

        # 3. Parse JSON Body
        try:
            payload = json.loads(raw_data.decode('utf-8'))
        except Exception:
            return Response(json.dumps({'error': 'Malformed JSON'}), status=400, content_type='application/json')

        # 4. Authenticate Runtime Origin (HMAC & Timestamp Freshness)
        instance_id = request.httprequest.headers.get('X-Insilos-Instance-Id') or payload.get('instance_id') or 'insilos-default'
        timestamp_str = request.httprequest.headers.get('X-Insilos-Timestamp') or str(payload.get('timestamp') or '')
        signature = request.httprequest.headers.get('X-Insilos-Signature') or payload.get('signature')

        # Anti-DoS: Instance-level rate limit (20 req/min)
        if not _check_rate_limit(_INSTANCE_RATE_LIMIT, instance_id, MAX_INSTANCE_BURST_PER_MIN):
            _logger.warning("Rate limit exceeded for instance: %s", instance_id)
            return Response(
                json.dumps({'error': 'Instance Rate Limit Exceeded', 'retry_after': 60}),
                status=429, headers=[('Retry-After', '60')], content_type='application/json'
            )

        # Timestamp verification (5-min replay window)
        now_ts = time.time()
        try:
            req_ts = float(timestamp_str) if timestamp_str else now_ts
        except ValueError:
            req_ts = 0

        if timestamp_str and abs(now_ts - req_ts) > TIMESTAMP_TOLERANCE_SECONDS:
            return Response(json.dumps({'error': 'Timestamp expired or clock drift too large'}), status=403, content_type='application/json')

        error_name = payload.get('name') or payload.get('error_name') or 'RuntimeError'
        error_message = payload.get('message') or payload.get('error_message') or ''
        traceback_str = payload.get('traceback') or ''
        component_stack = payload.get('component_stack') or ''

        # Compute expected HMAC
        secret = DEFAULT_HMAC_SECRET
        try:
            if hasattr(request, 'env') and request.env:
                secret = request.env['ir.config_parameter'].sudo().get_param(
                    f'al2c.instance_secret_{instance_id}',
                    request.env['ir.config_parameter'].sudo().get_param('al2c.master_instance_secret', DEFAULT_HMAC_SECRET)
                )
        except Exception:
            pass

        hash_body = f"{instance_id}:{timestamp_str}:{error_name}".encode('utf-8')
        expected_sig = hmac.new(secret.encode('utf-8'), hash_body, hashlib.sha256).hexdigest()

        # If external request, enforce mandatory signature; if loopback provides signature, validate it
        is_loopback = client_ip in ('127.0.0.1', '::1', 'localhost')
        if not is_loopback:
            if not signature or not hmac.compare_digest(signature, expected_sig):
                _logger.warning("Invalid or missing HMAC signature from instance %s (IP: %s)", instance_id, client_ip)
                return Response(json.dumps({'error': 'Forbidden: Invalid or Missing Runtime Signature'}), status=403, content_type='application/json')
        elif signature and not hmac.compare_digest(signature, expected_sig):
            _logger.warning("Invalid HMAC signature on loopback from instance %s", instance_id)
            return Response(json.dumps({'error': 'Forbidden: Invalid Runtime Signature'}), status=403, content_type='application/json')

        # 5. Asset Classification
        asset_code = self._classify_tech_asset(traceback_str, payload)

        # 6. Fingerprint & In-Memory Deduplication (15-min window)
        raw_fp = f"{error_name}:{asset_code}:{traceback_str[:300]}"
        fingerprint = hashlib.sha256(raw_fp.encode('utf-8')).hexdigest()

        now_time = time.time()
        if fingerprint in _DEDUP_CACHE:
            cached_code, cached_time, hit_count = _DEDUP_CACHE[fingerprint]
            if now_time - cached_time < 900:  # 15 min TTL
                _DEDUP_CACHE[fingerprint] = (cached_code, now_time, hit_count + 1)
                _append_audit_ledger({
                    'status': 'deduplicated',
                    'incident_code': cached_code,
                    'fingerprint': fingerprint,
                    'hit_count': hit_count + 1,
                    'instance_id': instance_id,
                    'timestamp': now_time,
                })
                return Response(
                    json.dumps({
                        'status': 'deduplicated',
                        'incident_code': cached_code,
                        'occurrences': hit_count + 1,
                        'message': 'Duplicate incident aggregated successfully.',
                    }),
                    status=200, content_type='application/json'
                )

        # 7. Record Incident (ORM if available, JSONL ledger guaranteed)
        seq_num = f"{int(now_time) % 100000:05d}"
        incident_code = f"INC-2026-{seq_num}"

        # Attempt ORM persistence across active database
        orm_persisted = False
        target_db = getattr(getattr(request, 'session', None), 'db', None)
        if not target_db:
            # Check candidate databases
            for cand in ['innoria_prod', 'insilos', 'insilos20_dev']:
                try:
                    reg = Registry(cand)
                    if 'al2c.runtime.incident' in reg:
                        target_db = cand
                        break
                except Exception:
                    continue

        if target_db:
            try:
                reg = Registry(target_db)
                with reg.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    if 'al2c.runtime.incident' in env:
                        incident_model = env['al2c.runtime.incident']
                        existing = incident_model.search([('fingerprint', '=', fingerprint)], limit=1)
                        if existing:
                            existing.write({
                                'occurrence_count': existing.occurrence_count + 1,
                                'last_seen_date': fields.Datetime.now(),
                            })
                            incident_code = existing.incident_code
                        else:
                            tech_asset = env['al2c.tech.asset'].search([('code', '=', asset_code)], limit=1) if 'al2c.tech.asset' in env else False
                            new_inc = incident_model.create({
                                'name': f"{error_name}: {error_message[:120] if error_message else 'Unspecified Runtime Error'}",
                                'incident_code': incident_code,
                                'fingerprint': fingerprint,
                                'asset_id': tech_asset.id if tech_asset else False,
                                'error_name': error_name,
                                'error_message': error_message,
                                'traceback': traceback_str,
                                'component_stack': component_stack,
                                'instance_id': instance_id,
                                'instance_url': payload.get('url') or payload.get('server_host'),
                                'user_identifier': hashlib.sha256(str(payload.get('user_id') or client_ip).encode('utf-8')).hexdigest()[:12],
                                'client_info': payload.get('user_agent') or (request.httprequest.user_agent.string if request.httprequest.user_agent else 'Unknown'),
                                'server_version': payload.get('server_version'),
                                'severity': 'critical' if any(k in error_name.lower() for k in ['crash', 'database', 'syntax', 'uncaught']) else 'high',
                                'state': 'new',
                            })
                            if new_inc.severity == 'critical':
                                try:
                                    new_inc.action_create_backlog_improvement()
                                except Exception:
                                    pass
                        cr.commit()
                        orm_persisted = True
            except Exception as e:
                _logger.warning("ORM persistence failed (%s), relying on persistent audit ledger", e)

        # Sovereign persistent ledger append
        _append_audit_ledger({
            'status': 'created',
            'incident_code': incident_code,
            'fingerprint': fingerprint,
            'asset': asset_code,
            'error_name': error_name,
            'error_message': error_message,
            'traceback': traceback_str,
            'instance_id': instance_id,
            'client_ip': client_ip,
            'timestamp': now_time,
            'orm_persisted': orm_persisted,
        })

        _DEDUP_CACHE[fingerprint] = (incident_code, now_time, 1)
        _logger.info("Ingested Runtime Incident [%s] for Asset [%s] from instance %s (ORM: %s)", incident_code, asset_code, instance_id, orm_persisted)

        return Response(
            json.dumps({
                'status': 'created',
                'incident_code': incident_code,
                'asset': asset_code,
                'message': 'Incident ingested, verified and registered successfully.',
            }),
            status=201, content_type='application/json'
        )

    def _classify_tech_asset(self, traceback_str, payload):
        """Maps an error traceback to one of the 4 core repositories."""
        tb = (traceback_str or '') + ' ' + (payload.get('url') or '') + ' ' + (payload.get('name') or '')
        tb_lower = tb.lower()

        if any(k in tb_lower for k in ['flutter', 'dart', 'mobo_vert', 'peek_', 'polycondensation', 'insilos_mobile']):
            return 'INSILOS_MOBILE'
        elif any(k in tb_lower for k in ['verticalrisk', 'eramba', 'iso27001', 'grc', 'ncsp']):
            return 'VERTICAL_RISK'
        elif any(k in tb_lower for k in ['zencode', 'fleet_manager', 'stealth_engine', 'router', 'clef_']):
            return 'ZENCODE_ENT'
        else:
            return 'O20'

    @http.route(
        ['/insilos/runtime_error/relay', '/insilos/runtime_error/relay/'],
        type='http', auth='none', methods=['POST', 'OPTIONS'],
        csrf=False, cors='*', website=False, multilang=False
    )
    def local_runtime_error_relay(self, **post):
        """Local instance relay endpoint called by OWL ErrorDialog in the browser.
        Attaches server-side identity, signs the request with instance secret, and forwards to central report.
        """
        if request.httprequest.method == 'OPTIONS':
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With'),
            ]
            return Response(status=204, headers=headers)

        raw_payload = request.get_json_data() or {}
        if isinstance(raw_payload, dict) and 'params' in raw_payload and isinstance(raw_payload['params'], dict):
            payload = raw_payload['params']
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = {}

        # Enrich with local server telemetry
        instance_id = 'insilos-local-prod'
        secret = DEFAULT_HMAC_SECRET
        try:
            if hasattr(request, 'env') and request.env:
                instance_id = request.env['ir.config_parameter'].sudo().get_param('insilos.instance_id', 'insilos-local-prod')
                secret = request.env['ir.config_parameter'].sudo().get_param('al2c.instance_secret', DEFAULT_HMAC_SECRET)
        except Exception:
            pass

        timestamp_str = str(int(time.time()))
        error_name = payload.get('name') or 'ClientRuntimeError'

        hash_body = f"{instance_id}:{timestamp_str}:{error_name}".encode('utf-8')
        signature = hmac.new(secret.encode('utf-8'), hash_body, hashlib.sha256).hexdigest()

        payload['instance_id'] = instance_id
        payload['timestamp'] = timestamp_str
        payload['signature'] = signature
        payload['server_version'] = 'Insilos 20.0-LTS (Sovereign)'

        central_url = 'https://report.insilos.com/api/v1/runtime-report'
        try:
            if hasattr(request, 'env') and request.env:
                central_url = request.env['ir.config_parameter'].sudo().get_param('al2c.central_report_url', central_url)
        except Exception:
            pass

        current_host = request.httprequest.host if hasattr(request, 'httprequest') and request.httprequest else ''

        # If not on report.insilos.com, forward over HTTPS to central report gateway
        if 'report.insilos.com' not in current_host and central_url:
            try:
                req = urllib.request.Request(
                    central_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'X-Insilos-Instance-Id': instance_id,
                        'X-Insilos-Timestamp': timestamp_str,
                        'X-Insilos-Signature': signature,
                    },
                    method='POST',
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_body = json.loads(response.read().decode('utf-8'))
                    return Response(
                        json.dumps({'success': True, **res_body}),
                        status=200, content_type='application/json'
                    )
            except Exception as e:
                _logger.warning("Relay forward to %s failed (%s), falling back to in-process handling", central_url, e)

        # Fallback / In-Process handling
        tb = payload.get('traceback') or ''
        asset_code = self._classify_tech_asset(tb, payload)
        raw_fp = f"{error_name}:{asset_code}:{tb[:300]}"
        fingerprint = hashlib.sha256(raw_fp.encode('utf-8')).hexdigest()

        now_time = time.time()
        if fingerprint in _DEDUP_CACHE:
            cached_code, cached_time, hit_count = _DEDUP_CACHE[fingerprint]
            if now_time - cached_time < 900:
                _DEDUP_CACHE[fingerprint] = (cached_code, now_time, hit_count + 1)
                return Response(
                    json.dumps({
                        'success': True,
                        'status': 'deduplicated',
                        'incident_code': cached_code,
                        'occurrences': hit_count + 1,
                    }),
                    status=200, content_type='application/json'
                )

        seq_num = f"{int(now_time) % 100000:05d}"
        incident_code = f"INC-2026-{seq_num}"

        _append_audit_ledger({
            'status': 'relay_local',
            'incident_code': incident_code,
            'fingerprint': fingerprint,
            'asset': asset_code,
            'error_name': error_name,
            'error_message': payload.get('message'),
            'instance_id': instance_id,
            'timestamp': now_time,
        })

        _DEDUP_CACHE[fingerprint] = (incident_code, now_time, 1)

        return Response(
            json.dumps({
                'success': True,
                'status': 'created',
                'incident_code': incident_code,
                'asset': asset_code,
            }),
            status=200, content_type='application/json'
        )
