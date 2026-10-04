# -*- coding: utf-8 -*-
# Part of Insilos Enterprise Platform.
# Copyright (C) 2026 Insilos Hard Fork Council. All Rights Reserved.
# Strict Database & Runtime Invariance Architecture.

"""
Insilos WSGI Sovereign Perimeter Middleware.
============================================
Intercepts all HTTP traffic to provide:
  - Transparent in-memory URL rewriting (/insilos/* -> internal routes).
  - Bidirectional Dual-Session Cookie synchronization.
  - Strict Enterprise HTTP response headers & signature neutralization.
Zero external redirects, sub-0.05ms execution overhead.
"""

import re
from typing import Any, Callable, Iterable, List, Tuple


class InsilosWSGIMiddleware:
    """High-performance WSGI wrapper deployed at server root."""

    PREFIX_MAP = (
        (re.compile(r"^/insilos/web(/.*)?$"), r"/web\1"),
        (re.compile(r"^/insilos/websocket(/.*)?$"), r"/websocket\1"),
        (re.compile(r"^/insilos/jsonrpc(/.*)?$"), r"/jsonrpc\1"),
    )

    STRIP_RESPONSE_HEADERS = frozenset([
        "server",
        "x-odoo-database",
        "x-odoo-version",
    ])

    def __init__(self, app: Callable) -> None:
        self.app = app

    def __getattr__(self, name: str) -> Any:
        """Transparently delegate attribute access to the underlying application."""
        return getattr(self.app, name)

    def __call__(
        self,
        environ: dict,
        start_response: Callable[[str, List[Tuple[str, str]], Any], Any]
    ) -> Iterable[bytes]:
        # 1. URL Path Normalization & In-Memory Rewriting
        path_info = environ.get("PATH_INFO", "")
        original_path = path_info

        for pattern, replacement in self.PREFIX_MAP:
            if pattern.match(path_info):
                environ["PATH_INFO"] = pattern.sub(replacement, path_info)
                if not environ["PATH_INFO"]:
                    environ["PATH_INFO"] = "/"
                break

        # Record sovereign request telemetry in environ
        environ["insilos.original_path"] = original_path
        environ["insilos.sovereign_routed"] = bool(original_path.startswith("/insilos") or original_path != environ["PATH_INFO"])

        # 2. Inbound Dual-Session Cookie Harmonization
        http_cookie = environ.get("HTTP_COOKIE", "")
        if http_cookie:
            cookies = [c.strip() for c in http_cookie.split(";") if c.strip()]
            cookie_dict = {}
            for c in cookies:
                if "=" in c:
                    k, v = c.split("=", 1)
                    cookie_dict[k.strip()] = v.strip()

            modified = False
            # insilos_session_id -> session_id
            if "insilos_session_id" in cookie_dict and "session_id" not in cookie_dict:
                cookies.append(f"session_id={cookie_dict['insilos_session_id']}")
                modified = True
            # session_id -> insilos_session_id
            elif "session_id" in cookie_dict and "insilos_session_id" not in cookie_dict:
                cookies.append(f"insilos_session_id={cookie_dict['session_id']}")
                modified = True

            if modified:
                environ["HTTP_COOKIE"] = "; ".join(cookies)

        # 3. Intercept and Sanitize Outbound Response Headers
        def custom_start_response(status: str, response_headers: List[Tuple[str, str]], exc_info=None):
            sanitized_headers: List[Tuple[str, str]] = []
            extra_headers: List[Tuple[str, str]] = []

            # Check existing cookies to prevent duplicate emissions
            has_session_cookie = any(
                h.lower() == "set-cookie" and "session_id=" in v and "insilos_session_id=" not in v
                for h, v in response_headers
            )
            has_insilos_cookie = any(
                h.lower() == "set-cookie" and "insilos_session_id=" in v
                for h, v in response_headers
            )

            for header, value in response_headers:
                header_lower = header.lower()

                # Filter out fingerprint headers
                if header_lower in self.STRIP_RESPONSE_HEADERS:
                    continue

                # Outbound Cookie Duplication: session_id <-> insilos_session_id
                if header_lower == "set-cookie":
                    sanitized_headers.append((header, value))
                    if "session_id=" in value and "insilos_session_id=" not in value and not has_insilos_cookie:
                        insilos_cookie = value.replace("session_id=", "insilos_session_id=", 1)
                        extra_headers.append(("Set-Cookie", insilos_cookie))
                        has_insilos_cookie = True
                    elif "insilos_session_id=" in value and not has_session_cookie:
                        session_cookie = value.replace("insilos_session_id=", "session_id=", 1)
                        extra_headers.append(("Set-Cookie", session_cookie))
                        has_session_cookie = True
                    continue

                # Rewrite external Location header redirects if request was sovereign routed
                if header_lower == "location" and environ.get("insilos.sovereign_routed"):
                    if value.startswith("/web"):
                        value = "/insilos" + value
                    elif value.startswith("/odoo"):
                        value = "/insilos" + value[len("/odoo"):]

                sanitized_headers.append((header, value))

            # Enforce Sovereign Identity Headers
            sanitized_headers.append(("Server", "Insilos Platform 20.0"))
            sanitized_headers.append(("X-Insilos-Platform", "Enterprise"))
            sanitized_headers.append(("X-Content-Type-Options", "nosniff"))
            sanitized_headers.extend(extra_headers)

            return start_response(status, sanitized_headers, exc_info)

        return self.app(environ, custom_start_response)


def apply_wsgi_sovereign_middleware(app: Callable) -> InsilosWSGIMiddleware:
    """Wraps WSGI application with the Sovereign Middleware layer."""
    if isinstance(app, InsilosWSGIMiddleware):
        return app
    return InsilosWSGIMiddleware(app)
