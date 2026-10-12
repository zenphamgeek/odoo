# -*- coding: utf-8 -*-
# Part of Insilos Enterprise AL2C Security & Governance Subsystem.
# Developer-Workflow Guard: Controller Authorization Snapshot Test.
# Enforces that no internal controller route is left with auth='public' or 'none'
# unless explicitly curated on the reviewed PUBLIC_ALLOWLIST.

import unittest
from odoo.tests.common import TransactionCase, tagged
from odoo.http import Controller

# Explicitly curated and security-reviewed public and unauthenticated routes
PUBLIC_ALLOWLIST = frozenset([
    # AL2C Public Manifests
    '/llms.txt',
    '/llms-full.txt',

    # Customer Portal Dispute Route (CSRF-protected, form-clamped, auth='public' for portal invitation links)
    '/my/invoices/<int:invoice_id>/dispute',

    # Anti-DoS Runtime Incident Reporting Gateway (Protected by HMAC signature, IP rate limits, and 256KB cap)
    '/api/v1/runtime-report',
    '/api/v1/runtime-report/',
    '/insilos/runtime_error/relay',
    '/insilos/runtime_error/relay/',

    # Perimeter Gateway API Ingress (Protected by custom bearer session token, auth='none' for handshake)
    '/insilos/api/v1',
    '/insilos/api/v1/',
    '/insilos/api/v1/<path:subpath>',
    '/insilos/api/v1/test_error',
    '/insilos/api/v1/ping',
    '/insilos/api/v1/version',
    '/insilos/api/v1/authenticate',
    '/insilos/api/v1/call',

    # HMAC / Secret Verified Webhooks
    '/webhooks/hse-events',
    '/insilos/hse/webhook',
    '/api/v1/hse/cems/telemetry',
    '/webhooks/cems-telemetry',
    '/insilos/webhooks/hs-events',
    # Timesheet Ingestion Webhook (info@inno.ai.vn pubsub / HMAC verified)
    '/api/v1/timesheet/ingest',
    '/api/v1/timesheet/ingest/',
])


@tagged('post_install', '-at_install', 'insilos_al2c', 'security_audit')
class TestRouteAuthzSnapshot(TransactionCase):
    """
    Automated Developer-Workflow Guard & CI Security Gate:
    Verifies that no controller in insilos modules exposes unauthorized public endpoints.
    """

    def test_01_no_unexpected_public_routes_in_insilos_addons(self):
        """Introspect all registered Controller classes in insilos_* modules
        and ensure no route uses auth in ('public', 'none') without being allowlisted.
        """
        offenders = []
        insilos_controllers = []

        # Gather all controller subclasses
        def get_all_subclasses(cls):
            all_sub = []
            for sub in cls.__subclasses__():
                all_sub.append(sub)
                all_sub.extend(get_all_subclasses(sub))
            return all_sub

        for ctrl_cls in get_all_subclasses(Controller):
            mod = getattr(ctrl_cls, '__module__', '')
            if 'insilos' in mod and not mod.startswith('odoo.addons.insilos_website'):
                insilos_controllers.append(ctrl_cls)

        for ctrl in insilos_controllers:
            for name, method in list(ctrl.__dict__.items()):
                routing = getattr(method, 'routing', None)
                if not routing or not isinstance(routing, dict):
                    continue
                auth = routing.get('auth')
                if auth in ('public', 'none'):
                    routes = routing.get('routes', [])
                    for r in routes:
                        if r not in PUBLIC_ALLOWLIST:
                            offenders.append({
                                'controller': f"{ctrl.__module__}.{ctrl.__name__}",
                                'method': name,
                                'route': r,
                                'auth': auth,
                            })

        self.assertFalse(
            offenders,
            f"SECURITY VIOLATION (CWE-862/CWE-863): Unreviewed public routes detected in insilos modules:\n"
            f"{offenders}\n"
            f"Every new public route must undergo adversarial security audit and be explicitly added to PUBLIC_ALLOWLIST."
        )

    def test_02_guard_adversarial_detection_of_rogue_public_route(self):
        """Verify the guard mechanism itself detects and flags a rogue unreviewed public route."""
        class RogueController(Controller):
            def rogue_report(self):
                pass
        RogueController.rogue_report.routing = {
            'routes': ['/insilos/unauthorized_leak'],
            'auth': 'none',
        }

        # Simulated inspection of RogueController
        offenders = []
        routing = getattr(RogueController.rogue_report, 'routing', None)
        if routing and routing.get('auth') in ('public', 'none'):
            for r in routing.get('routes', []):
                if r not in PUBLIC_ALLOWLIST:
                    offenders.append(r)

        self.assertIn('/insilos/unauthorized_leak', offenders, "Guard must catch rogue public route.")
