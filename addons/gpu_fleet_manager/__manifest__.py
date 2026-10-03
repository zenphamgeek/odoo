# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

{
    'name': 'GPU Fleet Manager',
    'version': '20.0.1.0.0',
    'category': 'Operations/Compute',
    'summary': 'GPU Worker Lifecycle, Multi-Provider Routing, Service Combos, Usage Analytics & Telemetry Bridge',
    'description': """
GPU Fleet Manager for High-Performance AI Compute Workloads
===========================================================
- GPU Provider Management: Multi-cloud hierarchy (Modal, ThinkPad Local P15, Thapsang AI, OpenAI-compatible).
- GPU Workspace Tracking: 20 Modal workspace profiles, budget ceilings, real-time usage, headroom scores, billing status, priority rotation.
- GPU Service Combos: Dynamic failover routing chains (P1 -> P2 -> P3) with sequential fallback.
- GPU Worker Management: Hardware tiers (A100, H100, A10G, L40S, L4, T4, RTX-5000), VRAM, states, hourly cost rates.
- GPU Task Logs: In-flight and completed request telemetry, duration, micro-costs.
- GPU Usage Analytics: Daily/monthly compute hours, dollar costs, and daily usage matrix dashboards.
- Live Bridge: Direct HTTP sync with Sovereign Fleet Gateway on port 8099.
    """,
    'author': 'Insilos Core Team',
    'website': 'https://insilos.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/gpu_workspace_data.xml',
        'data/gpu_cron_data.xml',
        'views/gpu_provider_views.xml',
        'views/gpu_worker_views.xml',
        'views/gpu_task_log_views.xml',
        'views/gpu_usage_meter_views.xml',
        'views/gpu_usage_daily_views.xml',
        'views/gpu_workspace_views.xml',
        'views/gpu_service_combo_views.xml',
        'views/gpu_fleet_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
