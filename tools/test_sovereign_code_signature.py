#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insilos Enterprise Platform v20.0
Sovereign Code Signature & Architecture Verification Test Suite.
================================================================
Performs rigorous unit and integration checks across sovereign architectural layers:
  - Layer 1: Python Import Hook & PEP 451 Module Identity Invariance
  - Layer 3: WSGI Sovereign Perimeter Middleware (URL rewrite, dual-cookie, headers)
  - Layer 4: ORM Model Registry Nomenclature Facade & Exception Sanitization
"""

import os
import sys
import unittest

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Ensure PEP 451 Import Hook is installed
try:
    from addons.insilos_adapter.hook import install as _install_hook
    _install_hook()
except ImportError:
    try:
        from insilos_adapter.hook import install as _install_hook
        _install_hook()
    except ImportError:
        pass


class TestLayer1ModuleIdentity(unittest.TestCase):
    """Layer 1: Python Import Hook & Module Identity Invariance."""

    def test_import_insilos_succeeds_and_identity(self):
        """Asserts import insilos succeeds and shares exact module identity with odoo."""
        import odoo
        import insilos

        self.assertIs(
            insilos,
            odoo,
            "Object Identity Failure: insilos is not identical to odoo",
        )
        self.assertIn("insilos", sys.modules, "sys.modules missing 'insilos'")
        self.assertIn("odoo", sys.modules, "sys.modules missing 'odoo'")
        self.assertIs(
            sys.modules["insilos"],
            sys.modules["odoo"],
            "sys.modules['insilos'] must be identical to sys.modules['odoo']",
        )

    def test_submodules_and_class_identity(self):
        """Asserts from insilos import models, fields, api works and classes match."""
        import odoo.models
        import odoo.fields
        import insilos
        from insilos import models, fields, api

        self.assertIs(
            insilos.models.Model,
            odoo.models.Model,
            "insilos.models.Model must be odoo.models.Model",
        )
        self.assertIs(
            models.Model,
            odoo.models.Model,
            "Imported models.Model must be identical to odoo.models.Model",
        )
        self.assertIs(
            fields.Char,
            odoo.fields.Char,
            "insilos fields.Char must be identical to odoo.fields.Char",
        )
        self.assertIs(
            api.model,
            odoo.api.model,
            "insilos api.model must be identical to odoo.api.model",
        )


class TestLayer3WSGISovereignPerimeterMiddleware(unittest.TestCase):
    """Layer 3: WSGI Sovereign Perimeter Middleware Verification."""

    def test_path_translation(self):
        """
        Tests path translation:
          - /insilos/web/login -> /web/login, insilos.sovereign_routed is True.
          - /insilos/jsonrpc -> /jsonrpc.
        """
        from odoo.http_sovereign import InsilosWSGIMiddleware

        recorded_env = {}

        def mock_app(environ, start_response):
            recorded_env.update(environ)
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"OK"]

        middleware = InsilosWSGIMiddleware(mock_app)

        # 1. Test /insilos/web/login -> /web/login
        recorded_env.clear()
        env_login = {"PATH_INFO": "/insilos/web/login"}
        middleware(env_login, lambda status, headers, exc_info=None: None)
        self.assertEqual(
            env_login.get("PATH_INFO"),
            "/web/login",
            "PATH_INFO was not rewritten to /web/login",
        )
        self.assertTrue(
            env_login.get("insilos.sovereign_routed"),
            "insilos.sovereign_routed flag must be True for /insilos/web/login",
        )

        # 2. Test /insilos/jsonrpc -> /jsonrpc
        recorded_env.clear()
        env_jsonrpc = {"PATH_INFO": "/insilos/jsonrpc"}
        middleware(env_jsonrpc, lambda status, headers, exc_info=None: None)
        self.assertEqual(
            env_jsonrpc.get("PATH_INFO"),
            "/jsonrpc",
            "PATH_INFO was not rewritten to /jsonrpc",
        )
        self.assertTrue(
            env_jsonrpc.get("insilos.sovereign_routed"),
            "insilos.sovereign_routed flag must be True for /insilos/jsonrpc",
        )

    def test_inbound_dual_cookie_harmonization(self):
        """
        Tests inbound dual-cookie harmonization:
          - Header Cookie: insilos_session_id=abc123 -> injected session_id=abc123.
        """
        from odoo.http_sovereign import InsilosWSGIMiddleware

        recorded_env = {}

        def mock_app(environ, start_response):
            recorded_env.update(environ)
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"OK"]

        middleware = InsilosWSGIMiddleware(mock_app)
        env = {
            "PATH_INFO": "/web/login",
            "HTTP_COOKIE": "insilos_session_id=abc123",
        }
        middleware(env, lambda status, headers, exc_info=None: None)

        http_cookie = env.get("HTTP_COOKIE", "")
        self.assertIn(
            "session_id=abc123",
            http_cookie,
            "Inbound harmonization failed to inject session_id=abc123",
        )
        self.assertIn(
            "insilos_session_id=abc123",
            http_cookie,
            "Inbound harmonization must preserve insilos_session_id=abc123",
        )

    def test_outbound_response_header_sanitization(self):
        """
        Tests outbound response header sanitization:
          - Mock app returns Server: Werkzeug/Python and Set-Cookie: session_id=abc123; Path=/; HttpOnly.
          - Middleware asserts Server is Insilos Platform 20.0.
          - Middleware asserts Set-Cookie includes both session_id=abc123... and insilos_session_id=abc123...
          - Asserts X-Insilos-Platform: Enterprise.
        """
        from odoo.http_sovereign import InsilosWSGIMiddleware

        captured_headers = []

        def mock_app(environ, start_response):
            headers = [
                ("Server", "Werkzeug/Python"),
                ("Set-Cookie", "session_id=abc123; Path=/; HttpOnly"),
            ]
            start_response("200 OK", headers)
            return [b"OK"]

        middleware = InsilosWSGIMiddleware(mock_app)
        env = {"PATH_INFO": "/insilos/web/login"}

        def start_response(status, response_headers, exc_info=None):
            captured_headers.extend(response_headers)

        middleware(env, start_response)

        header_dict = {}
        cookies = []
        for name, value in captured_headers:
            if name.lower() == "set-cookie":
                cookies.append(value)
            else:
                header_dict[name] = value

        # Middleware asserts Server is Insilos Platform 20.0
        self.assertEqual(
            header_dict.get("Server"),
            "Insilos Platform 20.0",
            "Server header was not sanitized to Insilos Platform 20.0",
        )

        # Asserts X-Insilos-Platform: Enterprise
        self.assertEqual(
            header_dict.get("X-Insilos-Platform"),
            "Enterprise",
            "Missing or invalid X-Insilos-Platform header",
        )

        # Middleware asserts Set-Cookie includes both session_id=abc123... and insilos_session_id=abc123...
        has_session_id = any(c.startswith("session_id=abc123") for c in cookies)
        has_insilos_session_id = any(c.startswith("insilos_session_id=abc123") for c in cookies)
        self.assertTrue(
            has_session_id,
            f"Set-Cookie missing session_id=abc123, captured: {cookies}",
        )
        self.assertTrue(
            has_insilos_session_id,
            f"Set-Cookie missing duplicated insilos_session_id=abc123, captured: {cookies}",
        )


class TestLayer4ORMModelRegistryFacade(unittest.TestCase):
    """Layer 4: ORM Model Registry Facade & Exception Sanitization."""

    def test_orm_sovereign_patch_and_aliases(self):
        """
        Invokes patch_orm_sovereign() from odoo.orm_sovereign.
        Verifies SOVEREIGN_MODEL_ALIASES translations.
        """
        from odoo.orm_sovereign import SOVEREIGN_MODEL_ALIASES, patch_orm_sovereign

        # Invokes patch_orm_sovereign()
        patch_orm_sovereign()

        # Verifies SOVEREIGN_MODEL_ALIASES translations
        self.assertIn("enterprise.business_partner", SOVEREIGN_MODEL_ALIASES)
        self.assertEqual(SOVEREIGN_MODEL_ALIASES["enterprise.business_partner"], "res.partner")

        self.assertIn("insilos.business_partner", SOVEREIGN_MODEL_ALIASES)
        self.assertEqual(SOVEREIGN_MODEL_ALIASES["insilos.business_partner"], "res.partner")

        self.assertIn("enterprise.user", SOVEREIGN_MODEL_ALIASES)
        self.assertEqual(SOVEREIGN_MODEL_ALIASES["enterprise.user"], "res.users")

        self.assertIn("enterprise.model", SOVEREIGN_MODEL_ALIASES)
        self.assertEqual(SOVEREIGN_MODEL_ALIASES["enterprise.model"], "ir.model")

    def test_sanitize_rpc_exception(self):
        """
        Tests sanitize_rpc_exception to confirm internal paths and res_partner
        table references are neutralized.
        """
        from odoo.orm_sovereign import sanitize_rpc_exception

        raw_exc = Exception(
            'Error in File "/home/zen/O20/odoo/models.py", line 123, in _check_integrity: '
            'Unique constraint violation on physical table res_partner_email_uniq'
        )

        sanitized = sanitize_rpc_exception(raw_exc)

        self.assertEqual(sanitized.get("code"), 500)
        self.assertIn("name", sanitized)
        message = sanitized.get("message", "")

        # Confirm internal paths are neutralized
        self.assertNotIn("/home/zen/O20/odoo", message, "Disk path leaked in RPC error message")
        self.assertIn("insilos://core/", message, "Virtual path insilos://core/ missing")

        # Confirm res_partner table references are neutralized to enterprise alias
        self.assertNotIn("res_partner", message, "Physical table res_partner leaked in RPC error message")
        self.assertIn(
            "enterprise.business_partner",
            message,
            "Physical table res_partner should be translated to enterprise.business_partner",
        )


if __name__ == "__main__":
    unittest.main()
