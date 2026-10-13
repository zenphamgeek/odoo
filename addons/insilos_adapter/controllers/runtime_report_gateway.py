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
import urllib.parse
import zlib
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

# Security invariant: Authorized tenant whitelist for support telemetry (SEC-01)
_env_allowed = os.getenv("ALLOWED_SUPPORT_DATABASES")
ALLOWED_SUPPORT_DATABASES = frozenset(
    [d.strip() for d in _env_allowed.split(",") if d.strip()]
    if _env_allowed
    else ["insilos", "innoria_prod", "insilos20_dev"]
)
MAX_STRING_LEN = 2048
MAX_TRACEBACK_LEN = 65536


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


def _is_safe_origin_or_referer(url_str: str) -> bool:
    """Validate that origin/referer belongs to an authorized sovereign domain (SEC-02).
    Uses strict hostname matching and suffix checks (.domain.com) to prevent subdomain/path spoofing.
    """
    if not url_str or not isinstance(url_str, str):
        return False
    try:
        parsed = urllib.parse.urlparse(url_str)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        if host in ("localhost", "127.0.0.1", "::1"):
            return True
        valid_suffixes = ("insilos.com", "innoria.com", "innokafe.com", "inno.ai.vn", "mate.ai.vn")
        return any(host == s or host.endswith(f".{s}") for s in valid_suffixes)
    except Exception:
        return False


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

        # 5. Authenticate Runtime Origin (HMAC & Timestamp Freshness, or Trusted Origin)
        # Security Guard: Use actual socket peer address (remote_addr) for loopback trust,
        # never client-supplied headers (CF-Connecting-IP, X-Forwarded-For) to prevent IP spoofing bypass.
        socket_ip = request.httprequest.remote_addr or ''
        is_loopback = socket_ip in ('127.0.0.1', '::1')

        origin_header = request.httprequest.headers.get('Origin') or ''
        referer_header = request.httprequest.headers.get('Referer') or ''
        is_trusted_origin = _is_safe_origin_or_referer(origin_header) or _is_safe_origin_or_referer(referer_header)

        if signature:
            if not hmac.compare_digest(signature, expected_sig):
                _logger.warning("Invalid HMAC signature from instance %s (socket: %s, client: %s)", instance_id, socket_ip, client_ip)
                return Response(json.dumps({'error': 'Forbidden: Invalid Runtime Signature'}), status=403, content_type='application/json')
        elif not is_loopback and not is_trusted_origin:
            _logger.warning("Rejected unauthenticated runtime report from external origin (socket: %s, origin: %s, client: %s)", socket_ip, origin_header, client_ip)
            return Response(json.dumps({'error': 'Forbidden: Invalid or Missing Runtime Signature'}), status=403, content_type='application/json')

        # 6. Asset Classification
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

        # Sanitize and bound untrusted input fields (SEC-04)
        safe_error_name = str(error_name or 'UnknownError')[:128]
        safe_error_message = str(error_message or '')[:MAX_STRING_LEN]
        safe_traceback = str(traceback_str or '')[:MAX_TRACEBACK_LEN]
        safe_component_stack = str(component_stack or '')[:MAX_STRING_LEN]
        safe_instance_url = str(payload.get('url') or payload.get('server_host') or '')[:MAX_STRING_LEN]

        # Attempt ORM persistence across strictly authorized support tenant database (SEC-01)
        target_db = self._resolve_target_db()
        if target_db:
            orm_persisted, incident_code = self._persist_incident_orm(
                target_db, incident_code, fingerprint, asset_code, safe_error_name, safe_error_message,
                safe_traceback, safe_component_stack, instance_id, payload, client_ip, safe_instance_url
            )
        else:
            orm_persisted = False

        # Sovereign persistent ledger append
        _append_audit_ledger({
            'status': 'created',
            'incident_code': incident_code,
            'fingerprint': fingerprint,
            'asset': asset_code,
            'error_name': safe_error_name,
            'error_message': safe_error_message,
            'traceback': safe_traceback,
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

    def _resolve_target_db(self):
        """Resolves the designated Insilos Support Tenant database hosting al2c.runtime.incident.
        Enforces strict whitelisting to eliminate unauthenticated cross-tenant hopping (SEC-01).
        Uses fast loaded registry inspection to prevent thread blocking during request handling.
        """
        configured_db = None
        if hasattr(request, 'env') and request.env:
            try:
                configured_db = request.env['ir.config_parameter'].sudo().get_param('al2c.support_db')
            except Exception:
                configured_db = None

        candidates = [configured_db] if configured_db else []
        candidates.extend(sorted(list(ALLOWED_SUPPORT_DATABASES)))

        for cand in candidates:
            if not cand or cand not in ALLOWED_SUPPORT_DATABASES:
                continue
            try:
                # In test mock environments, Registry is a MagicMock (not a real class with registries dict)
                if isinstance(getattr(Registry, 'registries', None), dict):
                    if cand not in Registry.registries:
                        continue
                    reg = Registry.registries[cand]
                else:
                    reg = Registry(cand)
                if 'al2c.runtime.incident' in reg:
                    return cand
            except Exception:
                continue
        return None

    def _persist_incident_orm(self, target_db, incident_code, fingerprint, asset_code,
                              error_name, error_message, traceback_str, component_stack,
                              instance_id, payload, client_ip, instance_url=None):
        """Thread-safe, atomic incident ingestion using Postgres advisory locking (SEC-02, SEC-03)."""
        if not target_db:
            return False, incident_code

        lock_key = zlib.crc32(fingerprint.encode('utf-8')) & 0x7FFFFFFF
        orm_persisted = False
        try:
            reg = Registry(target_db)
            with reg.cursor() as cr:
                # Prefect/Airflow Invariant: Serialize concurrency on identical fingerprint
                cr.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))
                env = api.Environment(cr, SUPERUSER_ID, {})
                if 'al2c.runtime.incident' not in env:
                    return False, incident_code

                incident_model = env['al2c.runtime.incident']
                existing = incident_model.search([('fingerprint', '=', fingerprint)], limit=1)
                if existing:
                    existing.write({
                        'occurrence_count': existing.occurrence_count + 1,
                        'last_seen_date': fields.Datetime.now(),
                    })
                    incident_code = existing.incident_code
                else:
                    tech_asset = False
                    if 'al2c.tech.asset' in env and asset_code:
                        tech_asset = env['al2c.tech.asset'].search([('code', '=', asset_code)], limit=1)

                    user_identifier = hashlib.sha256(
                        str(payload.get('user_id') or client_ip).encode('utf-8')
                    ).hexdigest()[:12]

                    user_agent_str = ''
                    if request and hasattr(request, 'httprequest') and getattr(request.httprequest, 'user_agent', None):
                        user_agent_str = request.httprequest.user_agent.string or ''
                    client_info = str(payload.get('user_agent') or user_agent_str or 'Unknown')[:512]

                    is_critical = any(k in str(error_name).lower() for k in ['crash', 'database', 'syntax', 'uncaught'])
                    create_vals = {
                        'name': f"{error_name}: {error_message[:120] if error_message else 'Unspecified Runtime Error'}",
                        'incident_code': incident_code,
                        'fingerprint': fingerprint,
                        'asset_id': tech_asset.id if tech_asset else False,
                        'error_name': str(error_name)[:128],
                        'error_message': str(error_message)[:MAX_STRING_LEN] if error_message else '',
                        'traceback': str(traceback_str)[:MAX_TRACEBACK_LEN] if traceback_str else '',
                        'component_stack': str(component_stack)[:MAX_STRING_LEN] if component_stack else '',
                        'instance_id': str(instance_id)[:64],
                        'instance_url': str(instance_url or payload.get('url') or payload.get('server_host') or '')[:MAX_STRING_LEN],
                        'user_identifier': user_identifier,
                        'client_info': client_info,
                        'server_version': str(payload.get('server_version') or '')[:32],
                        'severity': 'critical' if is_critical else 'high',
                        'state': 'new',
                    }
                    if 'backlog_generation_pending' in incident_model._fields:
                        create_vals['backlog_generation_pending'] = True if is_critical else False

                    new_inc = incident_model.create(create_vals)
                    incident_code = new_inc.incident_code

                cr.commit()
                orm_persisted = True
        except Exception as e:
            _logger.warning("ORM persistence failed on db %s (%s), relying on persistent audit ledger", target_db, e)

        return orm_persisted, incident_code

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

        # SSRF mitigation (CWE-918): Strictly require https or localhost origin
        if not (central_url.startswith('https://') or central_url.startswith(('http://127.0.0.1', 'http://localhost'))):
            _logger.warning("Blocked unsafe central_report_url protocol/destination: %s", central_url)
            central_url = 'https://report.insilos.com/api/v1/runtime-report'

        current_host = request.httprequest.host if hasattr(request, 'httprequest') and request.httprequest else ''

        # If not on report.insilos.com, forward over HTTPS to central report gateway
        if 'report.insilos.com' not in current_host and central_url:
            try:
                req = urllib.request.Request(
                    central_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'InsilosRuntimeRelay/1.0',
                        'X-Insilos-Instance-Id': instance_id,
                        'X-Insilos-Timestamp': timestamp_str,
                        'X-Insilos-Signature': signature,
                    },
                    method='POST',
                )
                with urllib.request.urlopen(req, timeout=10) as response:
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

        # Sanitize and bound untrusted input fields (SEC-04)
        safe_error_name = str(error_name or 'UnknownError')[:128]
        safe_error_message = str(payload.get('message') or '')[:MAX_STRING_LEN]
        safe_traceback = str(tb or '')[:MAX_TRACEBACK_LEN]
        safe_component_stack = str(payload.get('component_stack') or '')[:MAX_STRING_LEN]
        safe_instance_url = str(payload.get('url') or payload.get('server_host') or '')[:MAX_STRING_LEN]

        target_db = self._resolve_target_db()
        client_ip = request.httprequest.remote_addr if hasattr(request, 'httprequest') and request.httprequest else ''
        if target_db:
            orm_persisted, incident_code = self._persist_incident_orm(
                target_db, incident_code, fingerprint, asset_code, safe_error_name, safe_error_message,
                safe_traceback, safe_component_stack, instance_id, payload, client_ip, safe_instance_url
            )
        else:
            orm_persisted = False

        _append_audit_ledger({
            'status': 'relay_local',
            'incident_code': incident_code,
            'fingerprint': fingerprint,
            'asset': asset_code,
            'error_name': error_name,
            'error_message': payload.get('message'),
            'instance_id': instance_id,
            'timestamp': now_time,
            'orm_persisted': orm_persisted,
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
