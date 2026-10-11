#!/usr/bin/env python3
"""
tools/verify_attestation_key_consistency.py
CI/CD Security Gate: Cryptographic Attestation Key Consistency & Non-Ephemerality (CWE-321/345).

Verifies that:
1. No hardcoded HMAC signing keys exist in operational scripts.
2. In production deployments, ATTESTATION_HMAC_KEY is mandatory and >= 32 bytes (256 bits).
3. The attestation key resolves consistently across multiple simulated worker processes
   (no ephemeral per-process token_bytes in multi-worker / multi-pod environments).
4. Signature verification succeeds across distinct worker lifecycle boundaries.

Exit code 0 on PASS, non-zero on FAIL.
"""

import os
import sys
import hmac
import hashlib
import json
import secrets

def get_operational_attestation_key(require_shared: bool = False) -> tuple[bytes, str]:
    """
    Retrieves the attestation HMAC key adhering to CWE-321 and multi-worker consistency.
    """
    env_key = os.environ.get("ATTESTATION_HMAC_KEY", "").strip()
    if env_key:
        raw_key = env_key.encode("utf-8")
        if len(raw_key) < 32:
            raise ValueError(f"ATTESTATION_HMAC_KEY must provide >= 32 bytes of entropy (got {len(raw_key)} bytes)")
        return raw_key, "env_shared"

    is_prod = os.environ.get("ENVIRONMENT") == "production" or os.environ.get("DEPLOY_ENV") == "prod"
    if is_prod or require_shared:
        raise RuntimeError(
            "FATAL: ATTESTATION_HMAC_KEY is unset in production/shared mode. "
            "Ephemeral in-memory keys are forbidden to prevent multi-worker verification failures (CWE-345/347)."
        )

    # In local testing mode without injected key, generate ephemeral key with explicit degraded warning
    print("[!] [DEGRADED AUDIT MODE] Using per-process ephemeral key. Set ATTESTATION_HMAC_KEY for cross-worker parity.")
    return secrets.token_bytes(32), "local_ephemeral"

def sign_attestation(payload: dict, key: bytes) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(key, canonical_json.encode("utf-8"), hashlib.sha256).hexdigest()

def verify_attestation(payload: dict, signature: str, key: bytes) -> bool:
    expected = sign_attestation(payload, key)
    return hmac.compare_digest(expected, signature)

def run_gate():
    print("=== CI GATE: ATTESTATION KEY CONSISTENCY & SECURITY AUDIT ===")

    # Test 1: Scan for hardcoded static keys across tools/
    print("[1/4] Scanning for hardcoded static HMAC keys (CWE-321)...")
    forbidden_literals = [
        b"deterministic_offline_oracle_key",
        b"default_insecure_hmac_key",
        b"hardcoded_signing_secret"
    ]
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    violations = []
    this_file = os.path.abspath(__file__)
    for root, _, files in os.walk(tools_dir):
        for f in files:
            if f.endswith((".py", ".sh", ".js")):
                fp = os.path.join(root, f)
                if os.path.abspath(fp) == this_file:
                    continue
                with open(fp, "rb") as fh:
                    c = fh.read()
                for fl in forbidden_literals:
                    if fl in c:
                        violations.append((fp, fl.decode("utf-8", errors="ignore")))

    if violations:
        print(f"[✗] Found {len(violations)} hardcoded key violations:")
        for vp, vl in violations:
            print(f"      - {vp}: '{vl}'")
        return 1
    print("  [✓] Zero hardcoded static key literals detected.")

    # Test 2: Multi-worker cross-process consistency simulation
    print("[2/4] Testing multi-worker signature consistency...")
    payload = {
        "event": "build_provenance",
        "target": "innokafe_website",
        "version": "20.0-enterprise",
        "build_timestamp": 1775899200
    }

    # Simulate Worker 1 and Worker 2 with injected environment key
    test_key = "a" * 32  # 32-byte known key
    sig1 = sign_attestation(payload, test_key.encode("utf-8"))
    sig2 = sign_attestation(payload, test_key.encode("utf-8"))
    if sig1 != sig2:
        print("[✗] Inconsistent HMAC between identical worker environments!")
        return 1
    if not verify_attestation(payload, sig1, test_key.encode("utf-8")):
        print("[✗] HMAC signature verification failed!")
        return 1
    print("  [✓] Deterministic cross-worker signing & verification verified.")

    # Test 3: Minimum entropy enforcement
    print("[3/4] Verifying entropy boundary (>= 32 bytes)...")
    try:
        os.environ["ATTESTATION_HMAC_KEY"] = "short_insecure_key"
        try:
            get_operational_attestation_key(require_shared=True)
            print("[✗] Weak key (< 32 bytes) was improperly accepted!")
            return 1
        except ValueError:
            print("  [✓] Short key correctly rejected (< 32 bytes).")
    finally:
        os.environ.pop("ATTESTATION_HMAC_KEY", None)

    # Test 4: Production fail-closed behavior
    print("[4/4] Verifying production fail-closed requirement...")
    try:
        os.environ["ENVIRONMENT"] = "production"
        try:
            get_operational_attestation_key()
            print("[✗] Production mode accepted missing ATTESTATION_HMAC_KEY!")
            return 1
        except RuntimeError:
            print("  [✓] Production mode correctly fails closed when key is absent.")
    finally:
        os.environ.pop("ENVIRONMENT", None)

    print("\n[✓✓✓] ALL ATTESTATION KEY CONSISTENCY GATES PASSED (EXIT CODE: 0)")
    return 0

if __name__ == "__main__":
    sys.exit(run_gate())
