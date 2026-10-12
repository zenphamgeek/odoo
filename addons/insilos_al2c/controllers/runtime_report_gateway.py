# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Crash Reporting Ingress Gatekeeper.

try:
    from odoo.addons.insilos_adapter.controllers.runtime_report_gateway import (
        RuntimeReportGateway,
        MAX_PAYLOAD_BYTES,
        MAX_INSTANCE_BURST_PER_MIN,
        MAX_IP_BURST_PER_MIN,
        TIMESTAMP_TOLERANCE_SECONDS,
        DEFAULT_HMAC_SECRET,
    )
except ImportError:
    RuntimeReportGateway = None
