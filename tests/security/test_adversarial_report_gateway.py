"""
tests/security/test_adversarial_report_gateway.py
================================================================================
Adversarial Security Test Suite for Runtime Report Gateway (SEC-01..04)
================================================================================
"""
import pytest
import zlib
import time
import hmac
import hashlib
import json

from tools.report_gateway.db_router import resolve_and_verify_database
from tools.report_gateway.outbox_processor import compute_advisory_lock_id, acquire_report_lock, fetch_pending_outbox_tasks
from tools.report_gateway.security_gate import (
    verify_report_bearer_token,
    GATEWAY_SIGNING_SECRET,
    is_safe_origin_or_referer,
)


class TestAdversarialSecurityAudit:

    @pytest.mark.parametrize("malicious_input", [
        "postgres",
        "template1",
        "insilos_core_prod; DROP TABLE ir_attachment;--",
        "../../../etc/passwd",
        "insilos_core_prod\x00_test",
        "   ",
        "' OR '1'='1",
    ])
    def test_cwe_20_89_database_whitelist_injection(self, malicious_input):
        """Exercises boundary conditions on database resolution against SQL injection."""
        with pytest.raises((ValueError, PermissionError)):
            resolve_and_verify_database(malicious_input)

    def test_cwe_662_advisory_lock_id_range_invariants(self):
        """Verifies advisory lock IDs always map into signed 64-bit integer space [-2^63, 2^63 - 1]."""
        test_cases = [
            ("insilos_core_prod", "report_ledger_2026_q3"),
            ("zzzzzzzzzzzzzzzz", "ffffffffffffffff"),
            ("a", "b"),
            ("", ""),
        ]
        for db, task in test_cases:
            lock_id = compute_advisory_lock_id(db, task)
            assert -(2**63) <= lock_id <= (2**63 - 1), f"Lock ID {lock_id} out of bounds"

    def test_cwe_285_token_tampering_and_replay(self, monkeypatch):
        """Verifies HMAC validation rejects forged signatures, expired tokens, and tampered claims."""
        test_secret = "0123456789abcdef0123456789abcdef0123456789abcdef"
        monkeypatch.setattr("tools.report_gateway.security_gate.GATEWAY_SIGNING_SECRET", test_secret)

        header = "eyJhbGciOiJIUzI1NiJ9"
        valid_claims = {"db": "insilos_core_prod", "user_id": 2, "exp": int(time.time()) + 300}
        payload = json.dumps(valid_claims)
        
        valid_sig = hmac.new(
            test_secret.encode(),
            f"{header}.{payload}".encode(),
            hashlib.sha256
        ).hexdigest()
        valid_token = f"{header}.{payload}.{valid_sig}"

        # 1. Valid token passes
        claims = verify_report_bearer_token(valid_token)
        assert claims["db"] == "insilos_core_prod"

        # 2. Tampered payload fails
        tampered_token = f"{header}.{json.dumps({'db': 'template1'})}.{valid_sig}"
        with pytest.raises(PermissionError, match="signature"):
            verify_report_bearer_token(tampered_token)

        # 3. Expired token fails
        expired_payload = json.dumps({"db": "insilos_core_prod", "exp": int(time.time()) - 10})
        expired_sig = hmac.new(
            test_secret.encode(),
            f"{header}.{expired_payload}".encode(),
            hashlib.sha256
        ).hexdigest()
        with pytest.raises(PermissionError, match="expired"):
            verify_report_bearer_token(f"{header}.{expired_payload}.{expired_sig}")

    def test_cwe_662_advisory_lock_manager_concurrency(self):
        """Verifies lock manager executes localized statements and raises on conflict."""
        class MockCursor:
            def __init__(self, acquired=True):
                self.statements = []
                self.acquired = acquired

            def execute(self, stmt, params=None):
                self.statements.append((stmt, params))

            def fetchone(self):
                return (self.acquired,)

        # Successful acquisition
        cr_ok = MockCursor(acquired=True)
        with acquire_report_lock(cr_ok, 123456789):
            pass
        assert any("SET LOCAL lock_timeout" in s[0] for s in cr_ok.statements)
        assert any("pg_try_advisory_xact_lock" in s[0] for s in cr_ok.statements)

        # Conflict raises BlockingIOError
        cr_conflict = MockCursor(acquired=False)
        with pytest.raises(BlockingIOError):
            with acquire_report_lock(cr_conflict, 987654321):
                pass

    def test_cwe_362_fetch_pending_outbox_skip_locked(self):
        """Verifies fetch query enforces FOR UPDATE SKIP LOCKED concurrency."""
        class MockCursor:
            def __init__(self):
                self.query = None
                self.params = None

            def execute(self, q, p):
                self.query = q
                self.params = p

            def fetchall(self):
                return [(1, "account.report_general_ledger", "{}")]

        cr = MockCursor()
        rows = fetch_pending_outbox_tasks(cr, limit=10)
        assert len(rows) == 1
        assert "FOR UPDATE SKIP LOCKED" in cr.query
        assert "WHERE status = 'PENDING'" in cr.query

    @pytest.mark.parametrize("valid_origin", [
        "https://innoria.com",
        "https://sub.innoria.com",
        "https://app.insilos.com:8069",
        "https://innokafe.com",
        "https://order.innokafe.com",
        "http://localhost:8069",
        "http://127.0.0.1:8069",
    ])
    def test_cwe_346_origin_legitimate_domains_pass(self, valid_origin):
        """SEC-02: Legitimate sovereign tenant origins and local fixtures are admitted."""
        assert is_safe_origin_or_referer(valid_origin) is True

    @pytest.mark.parametrize("spoofed_origin", [
        "https://evil-innoria.com",
        "https://innoria.com.evil.com",
        "https://innoria.com:password@attacker.com",
        "https://attacker.com/sub.innoria.com",
        "https://evil-insilos.com",
        "javascript:alert(1)",
        "data:text/html,evil",
        "   ",
        "",
        None,
    ])
    def test_cwe_346_origin_spoofing_and_subdomain_attacks_rejected(self, spoofed_origin):
        """CWE-346 / SEC-02: Subdomain collisions, authority trickery, and attacker prefixes rejected."""
        assert is_safe_origin_or_referer(spoofed_origin) is False
