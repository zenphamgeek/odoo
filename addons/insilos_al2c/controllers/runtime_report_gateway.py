# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Crash Reporting Ingress Gatekeeper.

try:
    from odoo.addons.insilos_adapter.controllers.runtime_report_gateway import (
        RuntimeReportGateway,
        ALLOWED_ASSETS,
        sanitize_telemetry_string,
        MAX_PAYLOAD_BYTES,
        MAX_INSTANCE_BURST_PER_MIN,
        MAX_IP_BURST_PER_MIN,
        TIMESTAMP_TOLERANCE_SECONDS,
        DEFAULT_HMAC_SECRET,
        ALLOWED_SUPPORT_DATABASES,
        MAX_STRING_LEN,
        MAX_TRACEBACK_LEN,
    )
except ImportError:
    RuntimeReportGateway = None
