"""
tools/report_gateway/security_gate.py
================================================================================
Headless NoDB Gateway Cryptographic Token Verification (SEC-04-REV)
================================================================================
Prevents CWE-259 (Hardcoded Secrets) and CWE-285 (Improper Authorization).
Validates HMAC-SHA256 signatures, timestamps, and claims for report tokens.
================================================================================
"""
import os
import hmac
import hashlib
import json
import time
from typing import Dict, Any

GATEWAY_SIGNING_SECRET = os.environ.get("INSILOS_REPORT_HMAC_SECRET", "").strip()


def get_signing_secret() -> str:
    """Returns the effective signing secret from module attribute or environment."""
    return globals().get("GATEWAY_SIGNING_SECRET") or os.environ.get("INSILOS_REPORT_HMAC_SECRET", "").strip()


def verify_report_bearer_token(token: str) -> Dict[str, Any]:
    """
    Verifies HMAC-SHA256 signature and freshness on incoming NoDB report tokens.
    Prevents CWE-259 (Hardcoded Secrets) and CWE-285 (Improper Authorization).
    """
    secret = get_signing_secret()
    if not secret or len(secret) < 32:
        raise RuntimeError("Security Invariant Violated: INSILOS_REPORT_HMAC_SECRET is unconfigured or weak (< 32 chars).")
        
    try:
        encoded_header, encoded_payload, signature = token.split(".")
    except ValueError:
        raise PermissionError("Malformed token structure.")

    expected_sig = hmac.new(
        secret.encode("utf-8"),
        f"{encoded_header}.{encoded_payload}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise PermissionError("Invalid token cryptographic signature.")

    try:
        claims = json.loads(encoded_payload)
    except Exception as e:
        raise PermissionError(f"Invalid token payload JSON: {e}")

    now = int(time.time())
    if claims.get("exp", 0) < now:
        raise PermissionError("Report token expired.")
    if claims.get("nbf", now) > now:
        raise PermissionError("Report token not yet active.")
        
    return claims


def is_safe_origin_or_referer(url_str: str) -> bool:
    """Validate that origin/referer belongs to an authorized sovereign domain (SEC-02).
    Uses strict hostname matching and suffix checks (.domain.com) to prevent subdomain/path spoofing.
    """
    if not url_str or not isinstance(url_str, str):
        return False
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url_str)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        if host in ("localhost", "127.0.0.1", "::1"):
            return True
        valid_suffixes = ("insilos.com", "innoria.com", "innokafe.com", "inno.ai.vn", "mate.ai.vn")
        return any(host == s or host.endswith(f".{s}") for s in valid_suffixes)
    except Exception:
        return False
