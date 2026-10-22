"""
tools/report_gateway/__init__.py
================================================================================
Runtime Report Gateway Package: NoDB Headless Engine & Outbox Processor
================================================================================
"""
from .db_router import resolve_and_verify_database, STATIC_TENANT_ALLOWLIST
from .outbox_processor import compute_advisory_lock_id, acquire_report_lock, fetch_pending_outbox_tasks
from .security_gate import verify_report_bearer_token

__all__ = [
    "resolve_and_verify_database",
    "STATIC_TENANT_ALLOWLIST",
    "compute_advisory_lock_id",
    "acquire_report_lock",
    "fetch_pending_outbox_tasks",
    "verify_report_bearer_token",
]
