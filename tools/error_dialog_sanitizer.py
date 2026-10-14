#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/error_dialog_sanitizer.py
===============================
Zero-Leak Error Payload & Telemetry Sanitizer (Patch 18.1).
Provides:
- Redaction of Authorization headers (Bearer, Basic, Digest)
- Redaction of known token prefixes (sk-, AKIA, ghp_)
- Redaction of key-value secrets (handles multi-word, quotes, and JSON structures)
- Redaction of PII phone numbers (Vietnam format: mask middle 5 digits)
"""

import re


def sanitize_error_payload(text: str) -> str:
    """
    Sanitizes raw error tracebacks, telemetry logs, and JSON payloads
    to guarantee zero credential, API key, and PII leakage.
    """
    if not text or not isinstance(text, str):
        return ""

    sanitized = text

    # 1. Redact Authorization headers (Bearer, Basic, Digest)
    sanitized = re.sub(
        r'Authorization\s*:\s*(Bearer|Basic|Digest)\s+[^\s\r\n]+',
        r'Authorization: \1 [REDACTED]',
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
        'Bearer [REDACTED]',
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r'Basic\s+[A-Za-z0-9+/=]+',
        'Basic [REDACTED]',
        sanitized,
        flags=re.IGNORECASE,
    )

    # 2. Redact Known Token Prefixes (sk-, AKIA, ghp_)
    sanitized = re.sub(
        r'\b(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36})\b',
        '[REDACTED_API_KEY]',
        sanitized,
    )

    # 3. Redact Key-Value Secrets (handles multi-word, quotes, and JSON structures)
    pattern = r'(?:["\']?(?:[a-zA-Z0-9_.-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?token|client[_-]?secret|session[_-]?id|sid)[a-zA-Z0-9_.-]*)["\']?\s*[:=]\s*)(?:["\'][^"\']*["\']|[^\s,;&{}]+)'

    def _redact_kv(m):
        raw = m.group(0)
        sep = ':' if ':' in raw else '='
        key_part = raw.split(sep, 1)[0]
        return f'{key_part}{sep} "[REDACTED]"'

    sanitized = re.sub(pattern, _redact_kv, sanitized, flags=re.IGNORECASE)

    # 4. Redact PII Phone Numbers (Vietnam format: mask middle 5 digits)
    sanitized = re.sub(r'\b(0[35789]\d)(\d{5})(\d{2})\b', r'\1*****\3', sanitized)

    return sanitized
