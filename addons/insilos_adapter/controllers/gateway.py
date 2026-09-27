# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

"""
Insilos API Perimeter Gateway Controller
========================================
Exposes clean, perimeter-secured API endpoints under /insilos/api/v1/...
Ensures:
- 'Server: insilos/20.0' response header on all gateway responses.
- Clean, consistent JSON envelope ({ "success": true/false, "data": ..., "error": ... }).
- Complete masking of internal Odoo stack traces and file paths on unexpected errors.
"""

from contextlib import ExitStack
import json
import logging
import time

import odoo
import odoo.modules.registry
from odoo import http
from odoo.http import Response, request
from odoo.http.session import authenticate, save_session
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

_logger = logging.getLogger("insilos.perimeter.gateway")


def _sanitize_error_message(exc: Exception) -> str:
    """Sanitize error messages to eliminate internal paths, SQL details, and trace details."""
    import re
    msg = str(exc)
    sensitive_patterns = [
        r"/home/",
        r"/usr/",
        r"/var/",
        r"/opt/",
        r"/etc/",
        r"\.py\b",
        r"Traceback",
        r"File \".*\"",
        r"line \d+",
        r"SELECT .* FROM",
        r"relation \".*\" does not exist",
        r"psycopg2\.",
    ]
    for pat in sensitive_patterns:
        if re.search(pat, msg, re.IGNORECASE):
            return "An internal system error occurred. Details have been logged."
    return msg


def _gateway_json_default(obj):
    """Serialize custom Odoo types (datetime, date, bytes, recordsets) into JSON."""
    if hasattr(obj, "_name") and hasattr(obj, "ids"):
        return obj.ids
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            import base64
            return base64.b64encode(obj).decode("ascii")
    try:
        import odoo.tools.json
        return odoo.tools.json.json_default(obj)
    except Exception:
        return str(obj)


def make_gateway_response(data=None, error=None, status=200) -> Response:
    """Construct a standardized Insilos Perimeter Gateway HTTP Response."""
    payload = {}
    if error is not None:
        payload["success"] = False
        payload["error"] = error
    else:
        payload["success"] = True
        payload["data"] = data

    body = json.dumps(payload, indent=2, ensure_ascii=False, default=_gateway_json_default)
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Server", "insilos/20.0"),
        ("X-Content-Type-Options", "nosniff"),
    ]
    return Response(
        response=body,
        status=status,
        headers=headers,
        mimetype="application/json",
    )


class InsilosPerimeterGateway(http.Controller):
    """Insilos API Perimeter Gateway Controller for v1 endpoints."""

    @http.route(
        ["/insilos/api/v1/ping"],
        type="http",
        auth="none",
        methods=["GET", "POST", "OPTIONS"],
        csrf=False,
        cors="*",
    )
    def api_ping(self, **kwargs):
        """Gateway liveness and connectivity probe."""
        if request.httprequest.method == "OPTIONS":
            return make_gateway_response(status=204)

        return make_gateway_response(
            data={
                "status": "pong",
                "server": "insilos",
                "version": "20.0",
                "timestamp": time.time(),
                "gateway": "insilos-perimeter-v1",
            },
            status=200,
        )

    @http.route(
        ["/insilos/api/v1/version"],
        type="http",
        auth="none",
        methods=["GET", "POST", "OPTIONS"],
        csrf=False,
        cors="*",
    )
    def api_version(self, **kwargs):
        """Return Insilos platform and gateway version metadata."""
        if request.httprequest.method == "OPTIONS":
            return make_gateway_response(status=204)

        return make_gateway_response(
            data={
                "server_name": "insilos",
                "server_version": "20.0",
                "server_series": "20.0",
                "protocol_version": 1,
                "flavor": "Insilos Enterprise Platform",
                "architecture": "Ports & Adapters (Hexagonal)",
            },
            status=200,
        )

    @http.route(
        ["/insilos/api/v1/authenticate"],
        type="http",
        auth="none",
        methods=["POST", "OPTIONS"],
        csrf=False,
        cors="*",
    )
    def api_authenticate(self, **kwargs):
        """Authenticate session and return session token with Insilos headers."""
        if request.httprequest.method == "OPTIONS":
            return make_gateway_response(status=204)

        try:
            raw_data = request.httprequest.get_data()
            payload = json.loads(raw_data.decode("utf-8")) if raw_data else {}
        except Exception:
            return make_gateway_response(
                error={"code": 400, "message": "Invalid JSON payload in request body."},
                status=400,
            )

        db = payload.get("db") or request.session.db or "odoo20_dev"
        login = payload.get("login")
        password = payload.get("password")

        if not login or not password:
            return make_gateway_response(
                error={"code": 400, "message": "Missing 'login' or 'password' parameter."},
                status=400,
            )

        try:
            with ExitStack() as stack:
                if not request.db or request.db != db:
                    cr = stack.enter_context(odoo.modules.registry.Registry(db).cursor())
                    env = odoo.api.Environment(cr, None, {})
                else:
                    env = request.env

                credential = {"login": login, "password": password, "type": "password"}
                auth_info = authenticate(request.session, env, credential)
                uid = auth_info.get("uid") if auth_info else None
                if not uid:
                    return make_gateway_response(
                        error={"code": 401, "message": "Invalid database credentials."},
                        status=401,
                    )

                request.session.uid = uid
                request.session.db = db
                save_session(request, env)

                return make_gateway_response(
                    data={
                        "uid": uid,
                        "session_id": request.session.sid,
                        "db": db,
                    },
                    status=200,
                )
        except Exception as exc:
            _logger.warning("Gateway authentication failure: %s", exc)
            return make_gateway_response(
                error={"code": 401, "message": "Authentication failed."},
                status=401,
            )

    @http.route(
        ["/insilos/api/v1/call"],
        type="http",
        auth="none",
        methods=["POST", "OPTIONS"],
        csrf=False,
        cors="*",
    )
    def api_call(self, **kwargs):
        """
        Execute model operations through the perimeter gateway.
        Never leaks internal stack traces or core exceptions.
        Supports session cookie or 'Authorization: Bearer <session_id>' / 'X-Session-Id'.
        """
        if request.httprequest.method == "OPTIONS":
            return make_gateway_response(status=204)

        try:
            raw_data = request.httprequest.get_data()
            payload = json.loads(raw_data.decode("utf-8")) if raw_data else {}
        except Exception:
            return make_gateway_response(
                error={"code": 400, "message": "Invalid JSON payload in request body."},
                status=400,
            )

        if not isinstance(payload, dict):
            return make_gateway_response(
                error={"code": 400, "message": "Request payload must be a JSON object."},
                status=400,
            )

        # Support JSON-RPC envelope wrapping
        if "params" in payload and isinstance(payload["params"], dict):
            params = payload["params"]
        else:
            params = payload

        model_name = params.get("model")
        method_name = params.get("method")
        args = params.get("args", [])
        method_kwargs = params.get("kwargs", {})

        if not isinstance(model_name, str) or not isinstance(method_name, str):
            return make_gateway_response(
                error={"code": 400, "message": "Missing or invalid 'model' or 'method' (must be strings)."},
                status=400,
            )

        if not isinstance(args, list):
            return make_gateway_response(
                error={"code": 400, "message": "Parameter 'args' must be a list."},
                status=400,
            )

        if not isinstance(method_kwargs, dict):
            return make_gateway_response(
                error={"code": 400, "message": "Parameter 'kwargs' must be an object."},
                status=400,
            )

        # Reject private or protected method invocations
        if method_name.startswith("_"):
            return make_gateway_response(
                error={"code": 403, "message": f"Access to private method '{method_name}' is forbidden."},
                status=403,
            )

        # Check authentication / session
        uid = request.session.uid
        db = request.session.db or params.get("db") or "odoo20_dev"

        # If not authenticated via cookie, check Authorization header, X-Session-Id, or payload session_id
        if not uid:
            auth_header = request.httprequest.headers.get("Authorization", "")
            sid = None
            if auth_header.startswith("Bearer "):
                sid = auth_header[7:].strip()
            elif "X-Session-Id" in request.httprequest.headers:
                sid = request.httprequest.headers["X-Session-Id"].strip()
            elif "session_id" in params and isinstance(params["session_id"], str):
                sid = params["session_id"].strip()

            if sid:
                try:
                    from odoo.http.session import session_store
                    sess = session_store().get(sid, keep_sid=True)
                    if sess and sess.uid:
                        uid = sess.uid
                        db = sess.db or db
                        request.session = sess
                except Exception as exc:
                    _logger.debug("Failed retrieving session from token %s: %s", sid, exc)

        _logger.info("api_call received: uid=%s, db=%s, sid=%s", uid, db, getattr(request.session, "sid", None))

        if not uid:
            return make_gateway_response(
                error={
                    "code": 401,
                    "message": "Authentication required. Please authenticate via /insilos/api/v1/authenticate first.",
                },
                status=401,
            )

        try:
            with ExitStack() as stack:
                if not request.db or request.db != db:
                    cr = stack.enter_context(odoo.modules.registry.Registry(db).cursor())
                    env = odoo.api.Environment(cr, uid, {})
                else:
                    env = request.env(user=uid)

                request.env = env
                request.db = db

                if model_name not in env:
                    return make_gateway_response(
                        error={"code": 404, "message": f"Model '{model_name}' not found in registry."},
                        status=404,
                    )

                model = env[model_name]
                method = getattr(model, method_name, None)
                if not method or not callable(method):
                    return make_gateway_response(
                        error={"code": 404, "message": f"Method '{method_name}' not found on model '{model_name}'."},
                        status=404,
                    )

                result = method(*args, **method_kwargs)
                return make_gateway_response(data=result, status=200)

        except (UserError, ValidationError) as exc:
            _logger.info("Gateway handled user error on %s.%s: %s", model_name, method_name, exc)
            return make_gateway_response(
                error={"code": 400, "message": _sanitize_error_message(exc)},
                status=400,
            )
        except (AccessError, AccessDenied) as exc:
            _logger.warning("Gateway access denied on %s.%s: %s", model_name, method_name, exc)
            return make_gateway_response(
                error={"code": 403, "message": "Access denied to requested resource."},
                status=403,
            )
        except Exception as exc:
            # Mask all internal stack traces
            _logger.error("Perimeter Gateway internal error executing %s.%s: %s", model_name, method_name, exc, exc_info=True)
            return make_gateway_response(
                error={"code": 500, "message": "Internal gateway processing error."},
                status=500,
            )

    @http.route(
        ["/insilos/api/v1/test_error"],
        type="http",
        auth="none",
        methods=["GET", "POST", "OPTIONS"],
        csrf=False,
        cors="*",
    )
    def api_test_error(self, **kwargs):
        """Diagnostic route to verify that internal errors mask stack traces completely."""
        if request.httprequest.method == "OPTIONS":
            return make_gateway_response(status=204)

        try:
            # Deliberate internal error
            raise RuntimeError("Secret internal database trace at /home/zen/O20/odoo/core.py:42: simulated crash")
        except Exception as exc:
            _logger.error("Intentional test error triggered: %s", exc, exc_info=True)
            return make_gateway_response(
                error={"code": 500, "message": _sanitize_error_message(exc)},
                status=500,
            )

    @http.route(
        [
            "/insilos/api/v1",
            "/insilos/api/v1/",
            "/insilos/api/v1/<path:subpath>",
        ],
        type="http",
        auth="none",
        methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        csrf=False,
        cors="*",
    )
    def api_catchall(self, subpath="", **kwargs):
        """Fallback for undefined perimeter gateway endpoints and base index route."""
        if request.httprequest.method == "OPTIONS":
            return make_gateway_response(status=204)

        if not subpath:
            return make_gateway_response(
                data={
                    "gateway": "insilos-perimeter-v1",
                    "server": "insilos",
                    "version": "20.0",
                    "endpoints": [
                        "/insilos/api/v1/ping",
                        "/insilos/api/v1/version",
                        "/insilos/api/v1/authenticate",
                        "/insilos/api/v1/call",
                    ],
                },
                status=200,
            )

        return make_gateway_response(
            error={
                "code": 404,
                "message": f"Endpoint '/insilos/api/v1/{subpath}' not found on Insilos Perimeter Gateway.",
            },
            status=404,
        )
