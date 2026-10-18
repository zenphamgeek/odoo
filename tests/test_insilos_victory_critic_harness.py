"""Unit tests for Insilos Victory Critic & Anti-Fake-Pass Harness (Odoo 20 / O20)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from insilos_victory_critic_harness import (
    GEMINI_STRICT_DOD_MARKER,
    build_gemini_strict_dod_reminder,
    critique_victory_claim,
    ensure_gemini_dod_reminder,
    evaluate_fake_pass_risk,
)


def test_clean_odoo20_qweb_and_owl_code_passes() -> None:
    qweb = """
<templates xml:space="preserve">
    <t t-name="insilos.FleetCockpit">
        <div class="insilos-obsidian-canvas border-bottom border-secondary">
            <t t-foreach="state.nodes" t-as="node" t-key="node">
                <span t-out="node"/>
            </t>
        </div>
    </t>
</templates>
"""
    test_code = """
def test_fleet_cockpit_model_selection():
    model = "gemini-4-argon-high"
    assert model.startswith("gemini-4-argon-")
    assert len(model) > 10
"""
    logs = """
=== 12 passed in 0.42s ===
0 collisions, 0 loose ends
audit passed
"""
    result = evaluate_fake_pass_risk(
        code_or_xml=qweb,
        test_code=test_code,
        command_output=logs,
    )
    assert result["is_fake_pass"] is False
    assert result["risk_score"] == 0.0
    assert result["violation_codes"] == []

    critique = critique_victory_claim(
        claim_type="task_victory",
        summary="All tests pass and zero defects verified via pytest and isometric audit.",
        requirements=["Odoo 20 t-out", "0 collisions"],
        code_or_xml=qweb,
        test_code=test_code,
        command_output=logs,
        edge_cases_tested=["empty_nodes", "collision_check"],
    )
    assert critique["verdict"] == "PASS"
    assert critique["overall_score"] >= 0.85
    assert all(axis["passed"] for axis in critique["rubric"].values())


def test_detects_trivial_assert_true_and_zero_assertion_test() -> None:
    bad_test_code = """
def test_fake_feature():
    x = 42
    assert True

def test_empty_check():
    y = 100
    print(y)
"""
    result = evaluate_fake_pass_risk(
        test_code=bad_test_code,
        command_output="2 passed in 0.01s",
    )
    assert result["is_fake_pass"] is True
    assert "TRIVIAL_ASSERT_TRUE" in result["violation_codes"]
    assert "ZERO_ASSERTION_TEST" in result["violation_codes"]


def test_detects_legacy_gemini_flash_and_deprecated_qweb_and_card_body() -> None:
    legacy_model = "-".join(("gemini", "3.8", "flash", "high"))
    bad_code = f"""
MODEL = "{legacy_model}"
<div class="card-body">
    <t t-foreach="items" t-as="item">
        <span t-esc="item.name"/>
    </t>
</div>
"""
    result = evaluate_fake_pass_risk(
        code_or_xml=bad_code,
        command_output="1 passed in 0.10s",
    )
    assert result["is_fake_pass"] is True
    assert "LEGACY_GEMINI_3_8_FLASH" in result["violation_codes"]
    assert "ODOO20_DEPRECATED_QWEB_DIRECTIVE" in result["violation_codes"]
    assert "OWL_MISSING_T_KEY" in result["violation_codes"]
    assert "RULE29_OPAQUE_CARD_BODY" in result["violation_codes"]


def test_rejects_unexecuted_verification_claim_and_isometric_claim() -> None:
    code = """
// s_innoria_anatomy_sovereign_rig via iso-kit.mjs
"""
    test_code = """
def test_isometric_rig():
    rig_status = "ready"
    assert rig_status == "ready"
"""
    critique = critique_victory_claim(
        claim_type="goal",
        summary="All tests pass, 100% verified, and isometric rig has 0 collisions.",
        code_or_xml=code,
        test_code=test_code,
        command_output="",
    )
    assert critique["verdict"] == "REJECT_FAKE_PASS"
    assert "UNEXECUTED_VERIFICATION_CLAIM" in critique["violation_codes"]
    assert "UNAUDITED_ISOMETRIC_COLLISION" in critique["violation_codes"]


def test_conditional_retry_when_edge_cases_missing() -> None:
    critique = critique_victory_claim(
        claim_type="job",
        summary="Updated Owl template with t-out",
        code_or_xml='<t t-name="insilos.Simple"><span t-out="state.label"/></t>',
        test_code="def test_one():\n    x = 1\n    assert x == 1\n",
        command_output="1 passed in 0.02s",
        edge_cases_tested=[],
    )
    assert critique["verdict"] == "CONDITIONAL_RETRY"
    assert critique["is_fake_pass"] is False


def test_ensure_gemini_dod_reminder_injection_and_idempotency() -> None:
    base_prompt = "Implement Odoo 20 Owl component for fleet telemetry."
    for tier_model in ("gemini-4-argon-high", "gemini-4-argon-medium", "gemini-4-argon-low"):
        enriched = ensure_gemini_dod_reminder(
            base_prompt,
            target_model=tier_model,
            task_level="L3_COMPLEX",
            task_type="code_gen",
        )
        assert GEMINI_STRICT_DOD_MARKER in enriched
        assert tier_model in enriched
        for idx in range(1, 6):
            assert f"[DoD-{idx}]" in enriched
        assert "<t t-out>" in enriched
        assert "0 collisions, 0 loose ends" in enriched
        # Idempotency check
        assert ensure_gemini_dod_reminder(enriched, target_model=tier_model) == enriched

    # Non-Gemini model remains unchanged
    assert ensure_gemini_dod_reminder(base_prompt, target_model="claude-opus-4-6-thinking") == base_prompt
    assert GEMINI_STRICT_DOD_MARKER in build_gemini_strict_dod_reminder()


import importlib.util
from typing import Any, Dict
import pytest

_LOCK_PATH = Path(__file__).resolve().parents[1] / "enterprise" / "insilos_industry_showcase" / "security" / "advisory_lock.py"
_LOCK_SPEC = importlib.util.spec_from_file_location("insilos_advisory_lock_harness", _LOCK_PATH)
assert _LOCK_SPEC is not None and _LOCK_SPEC.loader is not None
_lock_mod = importlib.util.module_from_spec(_LOCK_SPEC)
_LOCK_SPEC.loader.exec_module(_lock_mod)

SecurityException = _lock_mod.SecurityException
TenantBoundaryViolation = _lock_mod.TenantBoundaryViolation
CyclicStructureDetected = _lock_mod.CyclicStructureDetected
DeadlockHazardException = _lock_mod.DeadlockHazardException
FullwidthFormulaSanitizer = _lock_mod.FullwidthFormulaSanitizer
DeterministicHeterogeneousLockManager = _lock_mod.DeterministicHeterogeneousLockManager
AtomicMultiTenantGuard = _lock_mod.AtomicMultiTenantGuard


class TestFormulaSanitizationAdversarial:
    def test_fullwidth_and_control_char_neutralization(self) -> None:
        malicious_input = "\ufeff\uff1dSUM(A1:B10)"
        sanitized = FullwidthFormulaSanitizer.sanitize_string(malicious_input)
        assert sanitized.startswith("'"), "Sanitizer failed to prepend escape tick to normalized fullwidth formula"
        assert sanitized == "'=SUM(A1:B10)"

    def test_pipe_command_injection_neutralization(self) -> None:
        pipe_payload = "\t|cmd|' /C calc'!A0"
        sanitized = FullwidthFormulaSanitizer.sanitize_string(pipe_payload)
        assert sanitized.startswith("'"), "Sanitizer failed to escape tab-prefixed pipe command"
        assert sanitized == "'|cmd|' /C calc'!A0"

    def test_deep_nested_payload_sanitization(self) -> None:
        payload = {
            "order_ref": "SO-2026-001",
            "lines": [
                {"description": "\uff0b1000", "qty": 5},
                {"description": "Standard Product", "qty": 10},
            ],
            "metadata": {"approver": "@CEO_APPROVE"},
        }
        sanitized = FullwidthFormulaSanitizer.sanitize_payload(payload)
        assert sanitized["lines"][0]["description"] == "'+1000"
        assert sanitized["lines"][1]["description"] == "Standard Product"
        assert sanitized["metadata"]["approver"] == "'@CEO_APPROVE"

    def test_cyclic_dictionary_dos_detection(self) -> None:
        cyclic_dict: Dict[str, Any] = {"name": "Malicious Payload"}
        cyclic_dict["self_reference"] = cyclic_dict

        with pytest.raises(CyclicStructureDetected) as exc_info:
            FullwidthFormulaSanitizer.sanitize_payload(cyclic_dict)
        assert "Cyclic dictionary reference detected" in str(exc_info.value)

    def test_depth_bound_exhaustion_defense(self) -> None:
        nested: Dict[str, Any] = {"bottom": "=DANGEROUS"}
        for _ in range(20):
            nested = {"child": nested}

        with pytest.raises(CyclicStructureDetected) as exc_info:
            FullwidthFormulaSanitizer.sanitize_payload(nested, max_depth=16)
        assert "Traversal exceeded maximum allowable depth" in str(exc_info.value)


class TestHeterogeneousLockOrdering:
    def test_canonical_sort_order_eliminates_deadlock(self) -> None:
        tx1_requests = [("stock.quant", 101), ("sale.order", 45), ("res.partner", 9)]
        tx2_requests = [("res.partner", 9), ("stock.quant", 101), ("sale.order", 45)]

        ordered_tx1 = DeterministicHeterogeneousLockManager.order_lock_requests(tx1_requests)
        ordered_tx2 = DeterministicHeterogeneousLockManager.order_lock_requests(tx2_requests)

        expected_order = [("res.partner", 9), ("sale.order", 45), ("stock.quant", 101)]
        assert ordered_tx1 == expected_order, f"TX1 lock order mismatch: {ordered_tx1}"
        assert ordered_tx2 == expected_order, f"TX2 lock order mismatch: {ordered_tx2}"
        assert ordered_tx1 == ordered_tx2, "Non-deterministic lock ordering between transactions detected"

    def test_invalid_record_id_rejection(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            DeterministicHeterogeneousLockManager.order_lock_requests([("sale.order", 0)])
        assert "Must be positive integer" in str(exc_info.value)


class TestAtomicMultiTenantGuardAdversarial:
    def test_unauthorized_cross_tenant_access_rejection(self) -> None:
        allowed_companies = [1, 2]
        unauthorized_tenant = 3

        with pytest.raises(TenantBoundaryViolation) as exc_info:
            AtomicMultiTenantGuard.validate_tenant_access(unauthorized_tenant, allowed_companies)
        assert "is not within authorized scope" in str(exc_info.value)

    def test_falsy_and_zero_tenant_bypass_rejection(self) -> None:
        allowed_companies = [1, 2]

        for invalid_val in [0, -1, None, False, "1", [1]]:
            with pytest.raises(TenantBoundaryViolation):
                AtomicMultiTenantGuard.validate_tenant_access(invalid_val, allowed_companies)

    def test_valid_in_scope_tenant_acceptance(self) -> None:
        allowed_companies = [1, 5, 9]
        result = AtomicMultiTenantGuard.validate_tenant_access(5, allowed_companies)
        assert result == 5


