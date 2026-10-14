#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/telemetry_accumulator.py
==============================
Tenant-Boundary Paged Telemetry Accumulator (Patch 16.2 / 17).
Provides:
- Strict cross-tenant boundary verification on initialization.
- Cursor-based streaming pagination over insilos_telemetry_event.
- Parameterized SQL execution preventing cross-tenant leakage.
"""

try:
    from odoo.exceptions import AccessDenied
except Exception:
    class AccessDenied(Exception):
        pass


class PagedTelemetryAccumulator:
    """
    Accumulator for tenant-isolated telemetry events.
    Enforces tenant boundaries and cursor-based streaming.
    """

    def __init__(self, env, tenant_company_id: int, batch_size: int = 100):
        self.env = env
        self.tenant_company_id = tenant_company_id
        self.batch_size = max(1, min(batch_size, 500))
        if getattr(env, "company", None) and env.company.id != self.tenant_company_id:
            raise AccessDenied("Cross-tenant telemetry accumulation breach detected!")

    def fetch_page(self, last_cursor_ts: int = 0):
        if not isinstance(last_cursor_ts, int) or isinstance(last_cursor_ts, bool):
            raise ValueError("Invalid cursor format")
        query = """
            SELECT id, module_name, payload, commit_ts
            FROM insilos_telemetry_event
            WHERE company_id = %s
              AND commit_ts > %s
            ORDER BY commit_ts ASC, id ASC
            LIMIT %s;
        """
        self.env.cr.execute(query, (self.tenant_company_id, last_cursor_ts, self.batch_size))
        if hasattr(self.env.cr, 'dictfetchall'):
            return self.env.cr.dictfetchall()
        return self.env.cr.fetchall()
