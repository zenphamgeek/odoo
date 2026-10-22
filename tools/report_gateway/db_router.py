"""
tools/report_gateway/db_router.py
================================================================================
Database Router & Strict Whitelisting Engine (SEC-01-REV)
================================================================================
Prevents CWE-89 (SQL Injection) and CWE-20 (Improper Input Validation).
Strictly validates and canonicalizes target database name against an immutable allowlist.
================================================================================
"""
import re
import logging
from typing import Optional

_logger = logging.getLogger(__name__)

# Strict canonical database name format: lowercase alphanumeric + underscore, 3-32 chars
VALID_DB_REGEX = re.compile(r"^[a-z0-9][a-z0-9_]{2,31}$")

# Immutable set of authorized multi-tenant enterprise databases
STATIC_TENANT_ALLOWLIST: frozenset[str] = frozenset({
    "insilos_core_prod",
    "insilos_resilience_prod",
    "innoria_services_prod",
    "insilos20_dev",
    "innokafe_prod",
})


def resolve_and_verify_database(raw_db_name: Optional[str]) -> str:
    """
    Strictly validates and canonicalizes target database name.
    Prevents CWE-89 (SQL Injection) and CWE-20 (Improper Input Validation).
    """
    if not raw_db_name:
        raise ValueError("Missing mandatory target database parameter.")
    
    clean_name = raw_db_name.strip().lower()
    if not VALID_DB_REGEX.match(clean_name):
        _logger.warning("SEC-01-ATTACK: Invalid database format rejected: %r", raw_db_name)
        raise ValueError("Malformed database identifier.")
        
    if clean_name not in STATIC_TENANT_ALLOWLIST:
        _logger.warning("SEC-01-UNAUTHORIZED: Tenant database not in allowlist: %s", clean_name)
        raise PermissionError(f"Unauthorized database target: {clean_name}")
        
    return clean_name
