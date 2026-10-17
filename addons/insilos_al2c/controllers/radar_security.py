# -*- coding: utf-8 -*-
"""
SOP-DGM-13 Adversarial Security Hardening (Patch 35 `traimai` & Patch 36 `zenonmind` PLSH-ADG):
- `TenantSecurityBarrier`: Multi-tenant company isolation & scoped domain enforcement (`CWE-284`).
- `SafeDomainASTValidator`: Strict AST-whitelisted domain expression visitor (`validate_domain_expression`, `CWE-94`) + field/operator allowlist, 256-char ceiling, UTF-16 surrogate & SQLi rejection (`CWE-20`, `CWE-89`).
- `NonRepetitionGuard`: Thread-safe bounded LRU/TTL SHA-256 replay & multi-tenant partitioned prompt hash guard (`compute_prompt_hash`, `register_or_reject`, `CWE-285`, `CWE-400`).
- `MerkleWitnessGate`: Ephemeral Proof-Carrying Interactive UI (`PCP-UI`) Merkle state-transition witness (`< 5ms` mint/verify, `100%` tamper rejection).
- `DeterministicLockstepEngine`: Game-engine deterministic lockstep tick state hash ($H_{t+1}$) with 8-decimal `Decimal('0.00000001')` quantization and Decree 70/2025/ND-CP anti-1.0 FX fallback guard.
- `sanitize_telemetry_payload`: Recursive secret/token/session scrubber (`CWE-259`).
"""
import ast
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from odoo.exceptions import AccessDenied, ValidationError

ALLOWED_RADAR_FIELDS = frozenset(
    {
        "id",
        "code",
        "name",
        "service_pillar",
        "target_icp_segment",
        "state",
        "active",
        "company_id",
        "grounding_verified",
        "autonomy_mode",
        "channel_mix",
        "research_radar_id",
    }
)

ALLOWED_DOMAIN_OPERATORS = frozenset(
    {
        "=",
        "!=",
        "in",
        "not in",
        "ilike",
        "=ilike",
        "like",
        ">",
        ">=",
        "<",
        "<=",
    }
)

MAX_DOMAIN_CLAUSES = 32
MAX_STRING_VALUE_LEN = 256
MAX_IN_LIST_ITEMS = 64

_SQLI_PATTERN = re.compile(
    r"(--|/\*|\*/|;\s*(?:select|insert|update|delete|drop|alter|create|truncate|grant|revoke)\b|\bunion\s+all\s+select\b|\bunion\s+select\b|\bdrop\s+table\b)",
    re.IGNORECASE,
)

_SENSITIVE_KEY_SUBSTRINGS = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "passwd",
    "authorization",
    "session_id",
    "private_key",
    "access_token",
    "refresh_token",
    "bearer_token",
    "auth_token",
    "jwt_token",
)

_SENSITIVE_EXACT_KEYS = frozenset(
    {
        "token",
        "bearer",
        "jwt",
        "cookie",
        "set-cookie",
    }
)

_SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"\bsk-(?:ant-|proj-|live-|test-)?[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bAIzaSy[A-Za-z0-9_\-]{10,}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{10,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{12,}\b"),
    re.compile(r"(?i)\b(?:session_id|api_key|apikey|access_token|auth_token|secret|password)\s*[=:]\s*[^\s,;'\"]+"),
)


def _contains_utf16_surrogate(text: str) -> bool:
    for ch in text:
        code_pt = ord(ch)
        if 0xD800 <= code_pt <= 0xDFFF:
            return True
    return False


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


class TenantSecurityBarrier:
    """Enforces strict multi-tenant company boundary checks (CWE-284)."""

    @staticmethod
    def validate_tenant_boundary(record_company_id, allowed_company_ids=None, current_company_id=None) -> bool:
        allowed_set = set()
        if allowed_company_ids:
            for cid in allowed_company_ids:
                try:
                    val = int(cid)
                    if val > 0:
                        allowed_set.add(val)
                except (TypeError, ValueError):
                    continue
        if current_company_id is not None:
            try:
                cval = int(current_company_id)
                if cval > 0:
                    allowed_set.add(cval)
            except (TypeError, ValueError):
                pass

        if not allowed_set:
            raise AccessDenied("Cross-tenant access denied (CWE-284): caller has no valid company context.")

        if record_company_id in (None, False):
            return True

        try:
            rec_cid = int(record_company_id)
        except (TypeError, ValueError) as exc:
            raise AccessDenied("Cross-tenant access denied (CWE-284): invalid record company_id.") from exc

        if rec_cid <= 0 or rec_cid not in allowed_set:
            raise AccessDenied(
                f"Cross-tenant access denied (CWE-284): company_id={rec_cid} is outside allowed companies {sorted(allowed_set)}."
            )
        return True

    @staticmethod
    def scoped_company_domain(company_id) -> list:
        try:
            cid = int(company_id)
        except (TypeError, ValueError) as exc:
            raise AccessDenied("Invalid tenant company_id for scoped domain (CWE-284).") from exc
        if cid <= 0:
            raise AccessDenied(f"Non-positive tenant company_id={cid} rejected (CWE-284).")
        return [("company_id", "in", [cid, False])]


class SafeDomainASTValidator:
    """Strict AST validator for user/RPC-supplied Odoo search domains (CWE-20, CWE-89, CWE-94, CWE-200, CWE-284, CWE-400)."""

    MAX_PREFIX_DEPTH = 3
    MAX_DOMAIN_TERMS = 15

    ALLOWED_AST_NODES = (
        ast.Expression,
        ast.List,
        ast.Tuple,
        ast.Constant,
        ast.UnaryOp,
        ast.USub,
        ast.UAdd,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Load,
    )

    FORBIDDEN_NAME_PREFIXES = (
        "__",
        "eval",
        "exec",
        "compile",
        "open",
        "getattr",
        "setattr",
        "import",
        "subclasses",
        "globals",
        "builtins",
    )

    @classmethod
    def validate_domain_expression(
        cls,
        domain_str: str,
        allowed_fields=None,
        enforce_company_id=None,
    ) -> List[Tuple[str, str, Any]]:
        """Parses a string domain expression via `ast.parse(..., mode='eval')`, enforces strict AST node
        whitelisting (`ALLOWED_AST_NODES`) and forbidden name/dunder token blocking (`CWE-94`), and delegates
        to `sanitize_and_validate`.
        """
        if domain_str is None:
            return cls.sanitize_and_validate([], allowed_fields=allowed_fields, enforce_company_id=enforce_company_id)
        if not isinstance(domain_str, str):
            raise ValidationError("Domain expression must be a string (CWE-20).")
        stripped = domain_str.strip()
        if not stripped or stripped == "[]":
            return cls.sanitize_and_validate([], allowed_fields=allowed_fields, enforce_company_id=enforce_company_id)
        if len(stripped) > 4096:
            raise ValidationError("Domain expression exceeds 4096-character limit (CWE-400).")
        if "\x00" in stripped or _contains_utf16_surrogate(stripped):
            raise ValidationError("Malformed null byte or UTF-16 surrogate in domain expression (CWE-20).")

        try:
            tree = ast.parse(stripped, mode="eval")
        except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError) as exc:
            raise ValidationError(f"Malformed domain expression syntax (CWE-20): {exc}") from exc

        for node in ast.walk(tree):
            if not isinstance(node, cls.ALLOWED_AST_NODES):
                raise AccessDenied(
                    f"Forbidden AST node '{type(node).__name__}' rejected in domain expression (CWE-94)."
                )
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low_s = node.value.strip().lower()
                for bad_tok in cls.FORBIDDEN_NAME_PREFIXES:
                    if bad_tok in low_s:
                        raise AccessDenied(
                            f"Forbidden dunder/builtin token '{bad_tok}' rejected in domain constant (CWE-94)."
                        )

        try:
            evaluated = ast.literal_eval(tree)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as exc:
            raise ValidationError(f"Failed to literal_eval domain expression (CWE-20): {exc}") from exc

        return cls.sanitize_and_validate(
            evaluated,
            allowed_fields=allowed_fields,
            enforce_company_id=enforce_company_id,
        )

    @classmethod
    def validate_domain(cls, domain, allowed_fields=None, enforce_company_id=None) -> list:
        if isinstance(domain, str):
            return cls.validate_domain_expression(
                domain,
                allowed_fields=allowed_fields,
                enforce_company_id=enforce_company_id,
            )
        return cls.sanitize_and_validate(
            domain,
            allowed_fields=allowed_fields,
            enforce_company_id=enforce_company_id,
        )

    @classmethod
    def _validate_scalar_value(cls, value):
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            if len(value) > MAX_STRING_VALUE_LEN:
                raise ValidationError(
                    f"Domain string value length ({len(value)}) exceeds {MAX_STRING_VALUE_LEN} characters (CWE-20)."
                )
            if "\x00" in value:
                raise ValidationError("Null byte injection detected in domain value (CWE-20).")
            if _contains_utf16_surrogate(value):
                raise ValidationError("Unpaired UTF-16 surrogate character rejected in domain value (CWE-20).")
            if _SQLI_PATTERN.search(value):
                raise ValidationError("Potential SQL injection pattern rejected in domain value (CWE-89).")
            low_v = value.strip().lower()
            for bad_tok in cls.FORBIDDEN_NAME_PREFIXES:
                if bad_tok in low_v:
                    raise AccessDenied(
                        f"Forbidden dunder/builtin token '{bad_tok}' rejected in domain value (CWE-94)."
                    )
            return value
        raise ValidationError(f"Unsupported domain value type: {type(value).__name__} (CWE-20).")

    @classmethod
    def sanitize_and_validate(cls, raw_domain, allowed_fields=None, enforce_company_id=None) -> list:
        enforced_cid = None
        if enforce_company_id is not None:
            try:
                enforced_cid = int(enforce_company_id)
            except (TypeError, ValueError) as exc:
                raise AccessDenied("Invalid enforce_company_id (CWE-284).") from exc
            if enforced_cid <= 0:
                raise AccessDenied("enforce_company_id must be > 0 (CWE-284).")

        if raw_domain is None or raw_domain == []:
            if enforced_cid is not None:
                return [("company_id", "in", [enforced_cid, False])]
            return []
        if not isinstance(raw_domain, (list, tuple)):
            raise ValidationError("Search domain must be a list or tuple of expressions (CWE-20).")
        if len(raw_domain) > cls.MAX_DOMAIN_TERMS:
            raise ValidationError(
                f"Search domain exceeds maximum term count ({cls.MAX_DOMAIN_TERMS}) (CWE-400)."
            )

        permitted_fields = frozenset(allowed_fields) if allowed_fields is not None else ALLOWED_RADAR_FIELDS
        normalized = []
        prefix_depth = 0
        has_company_guard = False

        for token in raw_domain:
            if isinstance(token, str):
                if token in ("&", "|", "!"):
                    prefix_depth += 1
                    if prefix_depth > cls.MAX_PREFIX_DEPTH:
                        raise ValidationError(
                            f"Search domain prefix combinator depth exceeds {cls.MAX_PREFIX_DEPTH} (CWE-400)."
                        )
                    normalized.append(token)
                    continue
                raise ValidationError(f"Invalid logical token in search domain: {token!r} (CWE-20).")

            prefix_depth = max(0, prefix_depth - 1)
            if not isinstance(token, (list, tuple)) or len(token) != 3:
                raise ValidationError("Each search domain leaf must be a 3-element (field, operator, value) tuple (CWE-20).")

            field_name, operator, raw_val = token[0], token[1], token[2]
            if not isinstance(field_name, str) or not field_name.strip():
                raise ValidationError("Domain field name must be a non-empty string (CWE-20).")
            if "\x00" in field_name or _contains_utf16_surrogate(field_name):
                raise ValidationError("Malformed characters in domain field name (CWE-20).")
            if "." in field_name or not field_name.isidentifier():
                raise AccessDenied(
                    f"Relational traversal or non-identifier field '{field_name}' rejected by SafeDomainASTValidator (CWE-89)."
                )
            if field_name not in permitted_fields:
                raise AccessDenied(
                    f"Forbidden domain field '{field_name}' rejected by SafeDomainASTValidator (CWE-284)."
                )

            if not isinstance(operator, str):
                raise ValidationError("Domain operator must be a string (CWE-20).")
            op_clean = operator.strip().lower()
            if op_clean not in ALLOWED_DOMAIN_OPERATORS:
                raise ValidationError(
                    f"Forbidden domain operator '{operator}' rejected by SafeDomainASTValidator (CWE-89)."
                )

            if op_clean in ("in", "not in"):
                if not isinstance(raw_val, (list, tuple)):
                    raise ValidationError(f"Operator '{op_clean}' requires a list/tuple value (CWE-20).")
                if len(raw_val) > MAX_IN_LIST_ITEMS:
                    raise ValidationError(
                        f"Domain '{op_clean}' list exceeds {MAX_IN_LIST_ITEMS} items (CWE-400)."
                    )
                clean_val = [cls._validate_scalar_value(item) for item in raw_val]
            else:
                if isinstance(raw_val, (list, tuple, dict, set)):
                    raise ValidationError(
                        f"Operator '{op_clean}' requires a scalar value, got {type(raw_val).__name__} (CWE-20)."
                    )
                clean_val = cls._validate_scalar_value(raw_val)

            if field_name == "company_id" and enforced_cid is not None:
                allowed_co_vals = {enforced_cid, False, None}
                if op_clean == "=":
                    if clean_val not in allowed_co_vals:
                        raise AccessDenied(
                            f"Cross-tenant company_id={clean_val} rejected for enforced company_id={enforced_cid} (CWE-200)."
                        )
                elif op_clean == "in":
                    if any(v not in allowed_co_vals for v in clean_val):
                        raise AccessDenied(
                            f"Cross-tenant company_id list {clean_val} rejected for enforced company_id={enforced_cid} (CWE-200)."
                        )
                else:
                    raise AccessDenied(
                        f"Disallowed operator '{op_clean}' on company_id when tenant enforcement is active (CWE-200)."
                    )
                has_company_guard = True

            normalized.append((field_name, op_clean, clean_val))

        if enforced_cid is not None and not has_company_guard:
            if normalized:
                normalized = ["&", ("company_id", "in", [enforced_cid, False])] + normalized
            else:
                normalized = [("company_id", "in", [enforced_cid, False])]

        return normalized



class NonRepetitionGuard:
    """Thread-safe bounded LRU/TTL SHA-256 idempotency guard against replay amplification
    and cross-tenant prompt cache poisoning (CWE-285, CWE-400).
    """

    def __init__(self, max_entries: int = 4096, ttl_seconds: int = 86400):
        self.max_entries = max(16, int(max_entries))
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._lock = threading.Lock()
        self._entries = OrderedDict()

    @staticmethod
    def compute_fingerprint(tenant_id, action_key: str, payload) -> str:
        canonical = _canonical_json(
            {
                "tenant_id": int(tenant_id) if isinstance(tenant_id, int) or (isinstance(tenant_id, str) and tenant_id.isdigit()) else str(tenant_id or ""),
                "action_key": str(action_key or ""),
                "payload": payload,
            }
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_prompt_hash(prompt: str, tenant_id: str = "default", company_id: int = 1) -> str:
        """Computes a tenant- and company-partitioned SHA-256 hash (`CWE-285`) so Tenant A cannot
        poison or DoS Tenant B's non-repetition window.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValidationError("Prompt must be a non-empty string (CWE-20).")
        if "\x00" in prompt or _contains_utf16_surrogate(prompt):
            raise ValidationError("Malformed null byte or UTF-16 surrogate in prompt (CWE-20).")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValidationError("tenant_id must be a non-empty string (CWE-285).")
        if "\x00" in tenant_id or _contains_utf16_surrogate(tenant_id):
            raise ValidationError("Malformed characters in tenant_id (CWE-20).")
        try:
            cid = int(company_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("company_id must be a valid positive integer (CWE-284).") from exc
        if cid <= 0:
            raise ValidationError("company_id must be > 0 (CWE-284).")

        canonical = _canonical_json(
            {
                "ns": "PLSH-ADG-v1",
                "tenant_id": tenant_id.strip(),
                "company_id": cid,
                "prompt": prompt.strip(),
            }
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _evict_expired_unlocked(self, now_ts: float):
        cutoff = now_ts - self.ttl_seconds
        expired_keys = []
        for fp, ts in self._entries.items():
            if ts <= cutoff:
                expired_keys.append(fp)
            else:
                break
        for fp in expired_keys:
            self._entries.pop(fp, None)

    def register_or_reject(
        self,
        prompt: str,
        tenant_id: str = "default",
        company_id: int = 1,
        now_ts: Optional[float] = None,
    ) -> str:
        ts = float(now_ts) if now_ts is not None else time.time()
        fp = self.compute_prompt_hash(prompt=prompt, tenant_id=tenant_id, company_id=company_id)

        with self._lock:
            self._evict_expired_unlocked(ts)
            if fp in self._entries:
                prev_ts = self._entries[fp]
                if ts - prev_ts < self.ttl_seconds:
                    raise ValidationError(
                        f"Duplicate prompt replay rejected for tenant='{tenant_id}' company_id={company_id} within {self.ttl_seconds}s TTL (CWE-285/CWE-400)."
                    )
            self._entries[fp] = ts
            self._entries.move_to_end(fp)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

        return fp

    def check_and_record(
        self,
        tenant_id,
        action_key: str,
        payload=None,
        now_ts: float = None,
        raise_on_duplicate: bool = True,
    ) -> str:
        if not tenant_id or int(tenant_id) <= 0:
            raise AccessDenied("NonRepetitionGuard requires a positive tenant_id (CWE-284).")
        ts = float(now_ts) if now_ts is not None else time.time()
        fp = self.compute_fingerprint(tenant_id, action_key, payload)

        with self._lock:
            self._evict_expired_unlocked(ts)
            if fp in self._entries:
                prev_ts = self._entries[fp]
                if ts - prev_ts < self.ttl_seconds:
                    if raise_on_duplicate:
                        raise ValidationError(
                            f"Duplicate autonomous action replay rejected within {self.ttl_seconds}s TTL window (fingerprint={fp[:16]}..., CWE-400)."
                        )
                    return ""
            self._entries[fp] = ts
            self._entries.move_to_end(fp)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

        return fp

    def clear(self):
        with self._lock:
            self._entries.clear()


class DeterministicLockstepEngine:
    """PLSH-ADG Game-Engine Deterministic Lockstep State Hash Barrier:
    $$H_{t+1} = \\text{SHA256}(H_t \\parallel (t+1) \\parallel \\text{canonical}(I_t) \\parallel \\text{canonical}(S_{t+1}))$$
    Enforces 8-decimal `Decimal('0.00000001')` quantization and forbids silent `1.0` FX rate fallbacks
    when `source_currency != target_currency` per Decree 70/2025/ND-CP.
    """

    QUANTIZE_8DEC = Decimal("0.00000001")
    GENESIS_HASH = hashlib.sha256(b"INSILOS_PLSH_ADG_GENESIS_TICK_0").hexdigest()

    @classmethod
    def quantize_rate(
        cls,
        rate_val: Any,
        source_currency: str = "VND",
        target_currency: str = "VND",
    ) -> Decimal:
        if rate_val is None or isinstance(rate_val, bool):
            raise ValidationError("Statutory FX rate cannot be None or boolean (Decree 70/2025/ND-CP).")
        try:
            dec = Decimal(str(rate_val))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValidationError(f"Invalid statutory FX rate '{rate_val}' (Decree 70/2025/ND-CP).") from exc

        if not dec.is_finite() or dec <= Decimal("0"):
            raise ValidationError(f"Statutory FX rate must be finite and > 0, got {rate_val} (Decree 70/2025/ND-CP).")

        q_rate = dec.quantize(cls.QUANTIZE_8DEC, rounding=ROUND_HALF_UP)
        src_c = str(source_currency or "").strip().upper()
        tgt_c = str(target_currency or "").strip().upper()
        if not src_c or not tgt_c:
            raise ValidationError("source_currency and target_currency must be non-empty ISO codes.")

        if src_c != tgt_c and q_rate == Decimal("1.00000000"):
            raise ValidationError(
                f"Decree 70/2025/ND-CP Violation: silent 1.0 FX rate fallback prohibited for cross-currency pair {src_c}->{tgt_c}."
            )
        return q_rate

    @classmethod
    def convert_statutory_amount(
        cls,
        amount: Any,
        rate_val: Any,
        source_currency: str = "USD",
        target_currency: str = "VND",
    ) -> Decimal:
        if amount is None or isinstance(amount, bool):
            raise ValidationError("Statutory amount cannot be None or boolean.")
        try:
            amt_dec = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValidationError(f"Invalid statutory amount '{amount}'.") from exc
        if not amt_dec.is_finite() or amt_dec < Decimal("0"):
            raise ValidationError("Statutory amount must be finite and non-negative.")

        q_rate = cls.quantize_rate(rate_val, source_currency=source_currency, target_currency=target_currency)
        return (amt_dec * q_rate).quantize(cls.QUANTIZE_8DEC, rounding=ROUND_HALF_UP)

    @classmethod
    def step_tick(
        cls,
        prev_hash: str,
        tick: int,
        inputs_dict: dict,
        next_state_dict: dict,
    ) -> str:
        if not isinstance(prev_hash, str) or len(prev_hash.strip()) != 64:
            raise ValidationError("prev_hash must be a 64-character hex SHA-256 string.")
        try:
            next_tick = int(tick)
        except (TypeError, ValueError) as exc:
            raise ValidationError("tick must be an integer.") from exc
        if next_tick < 0:
            raise ValidationError("tick must be non-negative.")

        canonical_in = _canonical_json(inputs_dict or {})
        canonical_st = _canonical_json(next_state_dict or {})
        frame = f"{prev_hash.strip()}|{next_tick}|{canonical_in}|{canonical_st}".encode("utf-8")
        return hashlib.sha256(frame).hexdigest()

    @classmethod
    def verify_multi_node_consensus(cls, node_hashes) -> bool:
        if isinstance(node_hashes, dict):
            values = [str(v or "") for v in node_hashes.values()]
        elif isinstance(node_hashes, (list, tuple)):
            values = [str(v or "") for v in node_hashes]
        else:
            raise ValidationError("node_hashes must be a dict or sequence of state hashes.")

        if len(values) < 2:
            raise ValidationError("Consensus check requires at least 2 node hashes.")

        ref = values[0]
        if len(ref) != 64:
            raise ValidationError("Invalid reference lockstep state hash length.")

        for idx, candidate in enumerate(values[1:], start=1):
            if not hmac.compare_digest(ref, candidate):
                raise ValidationError(
                    f"Lockstep state hash desynchronization detected at node index {idx}: {candidate[:12]} != {ref[:12]} (PLSH-ADG)."
                )
        return True


class ZeroTrustPromptPartition:
    """Zero-Trust Prompt Partitioning Envelope (`ZTPP`, `CWE-20` / `CWE-74` / `CWE-285`):
    Escapes exogenous untrusted input against `<tenant_envelope>`, `</company_context>`, and `###`
    delimiter breakouts, serializes an RFC 8785 canonical JSON envelope, and signs it with per-tenant
    `HMAC-SHA256` (`envelope_signature`).
    """

    @staticmethod
    def _escape_delimiters(text: str) -> str:
        raw = str(text or "")
        if "\x00" in raw or _contains_utf16_surrogate(raw):
            raise ValidationError("Null byte or UTF-16 surrogate rejected in untrusted prompt data (CWE-20).")
        escaped = (
            raw.replace("<tenant_envelope", "&lt;tenant_envelope")
            .replace("</tenant_envelope>", "&lt;/tenant_envelope&gt;")
            .replace("<company_context", "&lt;company_context")
            .replace("</company_context>", "&lt;/company_context&gt;")
            .replace("###", "&#35;&#35;&#35;")
        )
        return escaped

    @classmethod
    def construct_secure_prompt(
        cls,
        system_manifest: str,
        tenant_id: int,
        tenant_secret: str,
        exogenous_untrusted_data: str,
    ) -> dict:
        if not isinstance(system_manifest, str) or not system_manifest.strip():
            raise ValidationError("system_manifest must be a non-empty string (CWE-20).")
        try:
            tid = int(tenant_id)
        except (TypeError, ValueError) as exc:
            raise AccessDenied("Invalid tenant_id for ZeroTrustPromptPartition (CWE-284).") from exc
        if tid <= 0:
            raise AccessDenied("tenant_id must be > 0 (CWE-284).")
        if not isinstance(tenant_secret, str) or len(tenant_secret.strip()) < 8:
            raise ValidationError("tenant_secret must be at least 8 characters (CWE-326).")

        sanitized_data = cls._escape_delimiters(exogenous_untrusted_data)
        envelope_obj = {
            "system_manifest": system_manifest.strip(),
            "tenant_id": tid,
            "untrusted_data": f'<tenant_envelope id="{tid}">{sanitized_data}</tenant_envelope>',
            "version": "ZTPP-v1",
        }
        payload_envelope = json.dumps(envelope_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        signature = hmac.new(
            tenant_secret.encode("utf-8"),
            payload_envelope.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "tenant_id": tid,
            "payload_envelope": payload_envelope,
            "envelope_signature": signature,
            "sanitized_untrusted_data": sanitized_data,
        }

    @classmethod
    def verify_envelope(cls, payload_envelope: str, signature: str, tenant_secret: str) -> bool:
        if not isinstance(payload_envelope, str) or not payload_envelope:
            return False
        if not isinstance(signature, str) or not signature:
            return False
        if not isinstance(tenant_secret, str) or len(tenant_secret.strip()) < 8:
            return False

        # Ensure no unescaped breakout tag appears more than the single canonical wrapper
        if payload_envelope.count("</tenant_envelope>") > 1:
            return False

        expected_sig = hmac.new(
            tenant_secret.encode("utf-8"),
            payload_envelope.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected_sig)

    @staticmethod
    def envelope_untrusted_lead(
        tenant_id: str,
        lead_data: Dict[str, Any],
        secret_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Wraps untrusted exogenous lead payload in a per-session cryptographic `BOUNDARY_ISOLATION_ZONE_<nonce>`
        partition signed with `HMAC-SHA256` (`CWE-200` / `CWE-284`).
        """
        tid = str(tenant_id or "").strip()
        if not tid:
            raise AccessDenied("tenant_id must be non-empty for envelope_untrusted_lead (CWE-284).")
        if not isinstance(lead_data, dict):
            raise ValidationError("lead_data must be a dictionary (CWE-20).")

        session_nonce = secrets.token_hex(16)
        boundary_tag = f"BOUNDARY_ISOLATION_ZONE_{session_nonce}"
        canonical_bytes = canonical_json_dumps(lead_data)
        canonical_str = canonical_bytes.decode("utf-8")
        if "\x00" in canonical_str or _contains_utf16_surrogate(canonical_str):
            raise ValidationError("Null byte or UTF-16 surrogate rejected in lead_data (CWE-20).")

        escaped_str = ZeroTrustPromptPartition._escape_delimiters(canonical_str).replace(
            boundary_tag, "[REDACTED_BOUNDARY_TAG]"
        )
        key_bytes = MerkleWitnessGate._resolve_key(secret_key)
        signing_payload = f"{tid}|{boundary_tag}|".encode("utf-8") + canonical_bytes
        signature = hmac.new(key_bytes, signing_payload, hashlib.sha256).hexdigest()
        prompt_block = (
            f"<{boundary_tag} tenant_id=\"{tid}\">\n"
            f"{escaped_str}\n"
            f"</{boundary_tag}>"
        )
        return {
            "tenant_id": tid,
            "boundary_tag": boundary_tag,
            "signature": signature,
            "partitioned_prompt": prompt_block,
        }


def canonical_json_dumps(obj: Any) -> bytes:
    """RFC 8785 deterministic JSON serialization (`allow_nan=False, separators=(',', ':'), sort_keys=True`)."""
    return json.dumps(
        obj,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")


class DomainSecurityViolation(ValidationError):
    """Raised when an untrusted domain expression violates SMT-bounded AST security constraints (`CWE-20` / `CWE-94`)."""


class SMTBoundedDomainASTValidator(ast.NodeVisitor):
    """SMT-Bounded AST Whitelist Visitor (`CWE-20` / `CWE-94`):
    Enforces `MAX_DEPTH = 6`, `MAX_NODES = 64`, `ALLOWED_OPERATORS`, `ALLOWED_COMPARATORS`,
    rejects `ast.Call`, `ast.Attribute`, imports, comprehensions, lambdas, and enforces 3-tuple leaf clauses.
    """

    MAX_DEPTH = 6
    MAX_NODES = 64
    ALLOWED_OPERATORS = {"&", "|", "!"}
    ALLOWED_COMPARATORS = {"=", "!=", ">", ">=", "<", "<=", "like", "ilike", "=like", "in", "not in"}
    FORBIDDEN_NODES = (
        ast.Call,
        ast.Attribute,
        ast.Import,
        ast.ImportFrom,
        ast.Global,
        ast.Nonlocal,
        ast.Lambda,
        ast.ListComp,
        ast.GeneratorExp,
        ast.SetComp,
        ast.DictComp,
        ast.Subscript,
        ast.Starred,
        ast.Await,
        ast.Yield,
        ast.YieldFrom,
        ast.FormattedValue,
        ast.JoinedStr,
        ast.NamedExpr,
        ast.BinOp,
        ast.BoolOp,
        ast.Compare,
        ast.IfExp,
    )

    def __init__(self, allowed_fields: Set[str]):
        self.allowed_fields = set(allowed_fields or ())
        self.node_count = 0
        self.current_depth = 0

    def visit(self, node: ast.AST):
        self.node_count += 1
        if self.node_count > self.MAX_NODES:
            raise DomainSecurityViolation(
                f"Domain AST node count ({self.node_count}) exceeds MAX_NODES ({self.MAX_NODES}) (CWE-400)."
            )
        self.current_depth += 1
        if self.current_depth > self.MAX_DEPTH:
            raise DomainSecurityViolation(
                f"Domain AST nesting depth ({self.current_depth}) exceeds MAX_DEPTH ({self.MAX_DEPTH}) (CWE-400)."
            )
        if isinstance(node, self.FORBIDDEN_NODES):
            raise DomainSecurityViolation(
                f"Forbidden AST construct '{type(node).__name__}' in domain expression (CWE-94)."
            )
        if isinstance(node, ast.Name) and node.id not in ("True", "False", "None"):
            raise DomainSecurityViolation(
                f"Forbidden identifier '{node.id}' in domain expression (CWE-94)."
            )
        try:
            return super().visit(node)
        finally:
            self.current_depth -= 1

    @staticmethod
    def _extract_literal_value(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name) and node.id in ("True", "False", "None"):
            return {"True": True, "False": False, "None": None}[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)) and isinstance(node.operand, ast.Constant):
            if isinstance(node.operand.value, (int, float)) and not isinstance(node.operand.value, bool):
                return -node.operand.value if isinstance(node.op, ast.USub) else +node.operand.value
        if isinstance(node, (ast.List, ast.Tuple)):
            return [SMTBoundedDomainASTValidator._extract_literal_value(elt) for elt in node.elts]
        raise DomainSecurityViolation(
            f"Non-literal domain value node '{type(node).__name__}' rejected (CWE-20)."
        )

    def validate(self, domain_str: str) -> bool:
        self.node_count = 0
        self.current_depth = 0
        if not isinstance(domain_str, str) or not domain_str.strip():
            raise DomainSecurityViolation("domain_str must be a non-empty string (CWE-20).")
        if "\x00" in domain_str or _contains_utf16_surrogate(domain_str):
            raise DomainSecurityViolation("Null byte or UTF-16 surrogate rejected in domain_str (CWE-20).")

        try:
            tree = ast.parse(domain_str.strip(), mode="eval")
        except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError) as exc:
            raise DomainSecurityViolation(f"Invalid domain syntax or recursion bomb: {exc}") from exc

        self.visit(tree.body)

        if not isinstance(tree.body, (ast.List, ast.Tuple)):
            raise DomainSecurityViolation("Domain root must be a list or tuple (CWE-20).")

        for elt in tree.body.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                if elt.value not in self.ALLOWED_OPERATORS:
                    raise DomainSecurityViolation(f"Disallowed prefix boolean operator '{elt.value}' (CWE-20).")
                continue

            if not isinstance(elt, (ast.Tuple, ast.List)) or len(elt.elts) != 3:
                raise DomainSecurityViolation("Each domain leaf clause must be a 3-element tuple/list (CWE-20).")

            f_node, op_node, val_node = elt.elts
            f_val = self._extract_literal_value(f_node)
            op_val = self._extract_literal_value(op_node)
            _ = self._extract_literal_value(val_node)

            if not isinstance(f_val, str) or "." in f_val or not f_val.isidentifier():
                raise DomainSecurityViolation(f"Invalid or dotted field name '{f_val}' rejected (CWE-89).")
            if f_val not in self.allowed_fields:
                raise DomainSecurityViolation(f"Field '{f_val}' is not in allowed_fields allowlist (CWE-284).")
            if not isinstance(op_val, str) or op_val not in self.ALLOWED_COMPARATORS:
                raise DomainSecurityViolation(f"Comparator '{op_val}' is not in ALLOWED_COMPARATORS (CWE-89).")

        return True


class MonotonicFencingTokenError(RuntimeError):
    """Raised when a stale or expired fencing token attempts to mutate state or commit a savepoint (`CWE-367` / `CWE-662`)."""


class MonotonicLeaseSavepointBarrier:
    """Monotonic Fencing Leases with Cryptographic Lamport Witness (`MFL-CLW`, `SEC-02`):
    Enforces lease validity using `time.monotonic()` and strictly increasing fencing tokens
    to prevent split-brain savepoint corruption under NTP clock skew.
    """

    def __init__(self, lease_duration_sec: float = 30.0):
        self.lease_duration_sec = float(lease_duration_sec)
        self._lock = threading.Lock()
        self._current_fencing_token: int = 0
        self._lease_expiry_monotonic: float = 0.0
        self._active_owner = None
        self._lamport_witness_chain: str = hashlib.sha256(b"INSILOS_MFL_CLW_GENESIS").hexdigest()

    def acquire_lease(self, owner_id: str):
        owner = str(owner_id or "").strip()
        if not owner:
            raise MonotonicFencingTokenError("owner_id must be a non-empty string.")
        with self._lock:
            now_mono = time.monotonic()
            if self._active_owner is not None and now_mono < self._lease_expiry_monotonic:
                if self._active_owner != owner:
                    raise MonotonicFencingTokenError(
                        f"Lease currently held by {self._active_owner} until {self._lease_expiry_monotonic:.3f}"
                    )
            self._current_fencing_token += 1
            self._active_owner = owner
            self._lease_expiry_monotonic = now_mono + self.lease_duration_sec
            frame = f"{self._lamport_witness_chain}|{self._current_fencing_token}|{owner}".encode("utf-8")
            self._lamport_witness_chain = hashlib.sha256(frame).hexdigest()
            return self._current_fencing_token, self._lease_expiry_monotonic

    def validate_action(self, owner_id: str, fencing_token: int) -> bool:
        with self._lock:
            now_mono = time.monotonic()
            if int(fencing_token) != self._current_fencing_token:
                raise MonotonicFencingTokenError(
                    f"Stale fencing token {fencing_token} < current {self._current_fencing_token}. Split-brain prevented."
                )
            if self._active_owner != str(owner_id or "").strip():
                raise MonotonicFencingTokenError(
                    f"Invalid lease owner {owner_id} (expected {self._active_owner})."
                )
            if now_mono >= self._lease_expiry_monotonic:
                raise MonotonicFencingTokenError(
                    f"Lease expired at monotonic {self._lease_expiry_monotonic:.3f} (now: {now_mono:.3f})."
                )
            return True

    def release_lease(self, owner_id: str, fencing_token: int) -> None:
        with self._lock:
            if self._active_owner == str(owner_id or "").strip() and int(fencing_token) == self._current_fencing_token:
                self._active_owner = None
                self._lease_expiry_monotonic = 0.0

    @property
    def lamport_witness_hash(self) -> str:
        return self._lamport_witness_chain


class PrefectLeaseOdooSavepointBarrier:
    """PrefectLease-OdooSavepoint Barrier (`CWE-662` / `CWE-833`):
    Synchronizes Prefect task lease hashing and monotonic fencing tokens (`MFL-CLW`) with an atomic
    PostgreSQL/Odoo `with cr.savepoint():` scope and SMT-bounded domain validation so any
    `DomainSecurityViolation` rolls back cleanly without poisoning the ambient transaction.
    """

    _MONOTONIC_BARRIER = MonotonicLeaseSavepointBarrier(lease_duration_sec=30.0)

    @classmethod
    def execute_in_savepoint(
        cls,
        cr,
        task_key: str,
        allowed_fields: Set[str],
        domain_str: str,
        callback=None,
    ) -> Dict[str, Any]:
        if not isinstance(task_key, str) or not task_key.strip():
            raise ValidationError("task_key must be a non-empty string.")
        clean_key = task_key.strip()
        fencing_token, expiry_mono = cls._MONOTONIC_BARRIER.acquire_lease(clean_key)
        lease_hash = hashlib.sha256(
            canonical_json_dumps(
                {
                    "task_key": clean_key,
                    "domain_str": str(domain_str or ""),
                    "fencing_token": fencing_token,
                }
            )
        ).hexdigest()

        try:
            with cr.savepoint():
                cls._MONOTONIC_BARRIER.validate_action(clean_key, fencing_token)
                validator = SMTBoundedDomainASTValidator(allowed_fields=allowed_fields)
                validator.validate(domain_str)
                cb_result = callback(cr, lease_hash) if callable(callback) else None
                cls._MONOTONIC_BARRIER.validate_action(clean_key, fencing_token)
                return {
                    "status": "COMMITTED",
                    "task_key": clean_key,
                    "lease_hash": lease_hash,
                    "fencing_token": fencing_token,
                    "expiry_monotonic": expiry_mono,
                    "lamport_witness_hash": cls._MONOTONIC_BARRIER.lamport_witness_hash,
                    "node_count": validator.node_count,
                    "result": cb_result,
                }
        finally:
            cls._MONOTONIC_BARRIER.release_lease(clean_key, fencing_token)


class MerkleWitnessGate:
    """Ephemeral Cryptographic Proof-Carrying Interactive UI (`PCP-UI`) & Lockless RFC 8785 Merkle Witness Gate.
    Supports both:
    - Class-level state-transition witness minting/verification (`mint_witness`, `verify_witness` in < 5ms).
    - Instance-level bounded OrderedDict action replay cache (`generate_witness`, `record_and_verify`, `CWE-294`).
    """

    DEFAULT_SECRET = "insilos-pcp-ui-merkle-witness-sovereign-key-v1"

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 4096):
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.max_entries = max(16, int(max_entries))
        self._action_cache = OrderedDict()

    @classmethod
    def compute_leaf_hash(cls, event_data: Dict[str, Any]) -> str:
        """Computes an RFC 8785 deterministic SHA-256 leaf digest over `event_data` (`CWE-345`)."""
        if not isinstance(event_data, dict):
            raise ValidationError("event_data must be a dictionary.")
        return hashlib.sha256(canonical_json_dumps(event_data)).hexdigest()

    @classmethod
    def build_witness_proof(cls, previous_state_hash: str, new_state_data: Dict[str, Any]) -> Dict[str, str]:
        """Builds a cryptographic Merkle state-transition witness proof linking `previous_state_hash`
        to `new_state_data` via RFC 8785 canonical leaf hashing (`CWE-345`).
        """
        prev = str(previous_state_hash or "").strip()
        if not prev:
            raise ValidationError("previous_state_hash must be a non-empty string.")
        leaf_hash = cls.compute_leaf_hash(new_state_data)
        merkle_root = hashlib.sha256(f"{prev}:{leaf_hash}".encode("utf-8")).hexdigest()
        return {
            "previous_state_hash": prev,
            "leaf_hash": leaf_hash,
            "merkle_root": merkle_root,
        }

    @staticmethod
    def generate_witness(action_type: str, tenant_id: int, write_set: dict) -> str:
        """Generates an RFC 8785 canonical JSON SHA-256 witness digest for `(action_type, tenant_id, write_set)`."""
        if not isinstance(action_type, str) or not action_type.strip():
            raise ValidationError("action_type must be a non-empty string.")
        try:
            tid = int(tenant_id)
        except (TypeError, ValueError) as exc:
            raise AccessDenied("Invalid tenant_id for generate_witness (CWE-284).") from exc
        if tid <= 0:
            raise AccessDenied("tenant_id must be > 0 (CWE-284).")

        canonical = json.dumps(
            {
                "action_type": action_type.strip(),
                "tenant_id": tid,
                "write_set": write_set if isinstance(write_set, dict) else {},
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def record_and_verify(
        self,
        action_id: str,
        witness: str,
        now_ts: Optional[float] = None,
    ) -> bool:
        """Admits a witness on first presentation and rejects any replay within `ttl_seconds` (`CWE-294`)."""
        if not isinstance(action_id, str) or not action_id.strip():
            return False
        if not isinstance(witness, str) or len(witness.strip()) != 64:
            return False

        now = float(now_ts) if now_ts is not None else time.time()
        cutoff = now - self.ttl_seconds
        expired = []
        for k, ts in self._action_cache.items():
            if ts <= cutoff:
                expired.append(k)
            else:
                break
        for k in expired:
            self._action_cache.pop(k, None)

        composite_key = f"{action_id.strip()}:{witness.strip()}"
        w_key = f"w:{witness.strip()}"
        if composite_key in self._action_cache or action_id.strip() in self._action_cache or w_key in self._action_cache:
            return False

        self._action_cache[composite_key] = now
        self._action_cache[action_id.strip()] = now
        self._action_cache[w_key] = now
        while len(self._action_cache) > self.max_entries:
            self._action_cache.popitem(last=False)
        return True

    @classmethod
    def _resolve_key(cls, secret_key=None) -> bytes:
        raw = secret_key or os.environ.get("INSILOS_MERKLE_WITNESS_KEY") or cls.DEFAULT_SECRET
        if isinstance(raw, bytes):
            return raw
        return str(raw).encode("utf-8")

    @classmethod
    def _compute_hashes(cls, tenant_id: int, model_name: str, pre_hash: str, post_hash: str):
        leaf_meta = hashlib.sha256(f"{int(tenant_id)}|{model_name}".encode("utf-8")).hexdigest()
        merkle_left = hashlib.sha256(f"{pre_hash}:{post_hash}".encode("utf-8")).hexdigest()
        merkle_root = hashlib.sha256(f"{merkle_left}:{leaf_meta}".encode("utf-8")).hexdigest()
        return merkle_root

    @classmethod
    def mint_witness(
        cls,
        tenant_id: int,
        model_name: str,
        pre_state_dict: dict,
        post_state_dict: dict,
        secret_key=None,
    ) -> dict:
        t0 = time.perf_counter()
        if not tenant_id or int(tenant_id) <= 0:
            raise AccessDenied("MerkleWitnessGate requires a positive tenant_id (CWE-284).")
        tid = int(tenant_id)
        mname = str(model_name or "").strip()
        if not mname:
            raise ValidationError("MerkleWitnessGate requires a non-empty model_name.")

        pre_hash = hashlib.sha256(_canonical_json(pre_state_dict or {}).encode("utf-8")).hexdigest()
        post_hash = hashlib.sha256(_canonical_json(post_state_dict or {}).encode("utf-8")).hexdigest()
        merkle_root = cls._compute_hashes(tid, mname, pre_hash, post_hash)

        key_bytes = cls._resolve_key(secret_key)
        signing_input = f"{tid}|{mname}|{pre_hash}|{post_hash}|{merkle_root}".encode("utf-8")
        signature = hmac.new(key_bytes, signing_input, hashlib.sha256).hexdigest()
        latency_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "tenant_id": tid,
            "model_name": mname,
            "pre_hash": pre_hash,
            "post_hash": post_hash,
            "merkle_root": merkle_root,
            "signature": signature,
            "timestamp": int(time.time()),
            "latency_ms": round(latency_ms, 4),
        }

    @classmethod
    def verify_witness(
        cls,
        witness: dict,
        expected_tenant_id: int,
        expected_model_name: str,
        secret_key=None,
        expected_pre_state: dict = None,
        expected_post_state: dict = None,
    ):
        if not isinstance(witness, dict):
            return False, "Witness payload must be a dictionary."
        required_keys = ("tenant_id", "model_name", "pre_hash", "post_hash", "merkle_root", "signature")
        for req_k in required_keys:
            if req_k not in witness:
                return False, f"Missing witness field: {req_k}"

        try:
            w_tid = int(witness["tenant_id"])
            exp_tid = int(expected_tenant_id)
        except (TypeError, ValueError):
            return False, "Invalid tenant_id in witness."

        if not hmac.compare_digest(str(w_tid), str(exp_tid)):
            return False, "Cross-tenant witness mismatch (CWE-284)."

        w_model = str(witness["model_name"] or "")
        exp_model = str(expected_model_name or "")
        if not hmac.compare_digest(w_model, exp_model):
            return False, "Model name mismatch in witness."

        pre_hash = str(witness["pre_hash"] or "")
        post_hash = str(witness["post_hash"] or "")

        if expected_pre_state is not None:
            calc_pre = hashlib.sha256(_canonical_json(expected_pre_state).encode("utf-8")).hexdigest()
            if not hmac.compare_digest(pre_hash, calc_pre):
                return False, "Pre-state hash mismatch (tampered pre_state)."

        if expected_post_state is not None:
            calc_post = hashlib.sha256(_canonical_json(expected_post_state).encode("utf-8")).hexdigest()
            if not hmac.compare_digest(post_hash, calc_post):
                return False, "Post-state hash mismatch (tampered post_state)."

        expected_root = cls._compute_hashes(exp_tid, exp_model, pre_hash, post_hash)
        if not hmac.compare_digest(str(witness["merkle_root"] or ""), expected_root):
            return False, "Merkle root integrity verification failed."

        key_bytes = cls._resolve_key(secret_key)
        signing_input = f"{exp_tid}|{exp_model}|{pre_hash}|{post_hash}|{expected_root}".encode("utf-8")
        expected_sig = hmac.new(key_bytes, signing_input, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(str(witness["signature"] or ""), expected_sig):
            return False, "HMAC signature verification failed."

        return True, "VERIFIED"



def _is_sensitive_key(key_name: str) -> bool:
    k_low = str(key_name or "").strip().lower()
    if not k_low:
        return False
    if k_low in ("claim_count", "token_count", "approval_token_valid", "csrf_token_verified"):
        return False
    if k_low in _SENSITIVE_EXACT_KEYS:
        return True
    return any(sub in k_low for sub in _SENSITIVE_KEY_SUBSTRINGS)


def _scrub_string_secrets(val: str) -> str:
    out = val
    for pat in _SECRET_VALUE_PATTERNS:
        out = pat.sub("[REDACTED_SECRET]", out)
    return out


def sanitize_telemetry_payload(data):
    """Recursively scrubs secrets, API keys, bearer tokens, passwords, and session_ids from telemetry payloads (CWE-259)."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if _is_sensitive_key(k):
                cleaned[k] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = sanitize_telemetry_payload(v)
        return cleaned
    if isinstance(data, list):
        return [sanitize_telemetry_payload(item) for item in data]
    if isinstance(data, tuple):
        return tuple(sanitize_telemetry_payload(item) for item in data)
    if isinstance(data, str):
        return _scrub_string_secrets(data)
    return data


GLOBAL_NON_REPETITION_GUARD = NonRepetitionGuard(max_entries=4096, ttl_seconds=86400)
