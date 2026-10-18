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


from decimal import Decimal

ConstraintViolationError = _lock_mod.ConstraintViolationError
DiscountConstraintSolver = _lock_mod.DiscountConstraintSolver
EnterpriseSalesProcessEngine = _lock_mod.EnterpriseSalesProcessEngine
FlowStateStepRecord = _lock_mod.FlowStateStepRecord
InvalidStateTransitionError = _lock_mod.InvalidStateTransitionError
SalesOrder = _lock_mod.SalesOrder
SalesOrderLine = _lock_mod.SalesOrderLine
SalesOrderStatus = _lock_mod.SalesOrderStatus
TenantContext = _lock_mod.TenantContext
TenantSecurityError = _lock_mod.TenantSecurityError


def test_2506_01423_invariant_full_lifecycle() -> None:
    """Verifies end-to-end sales lifecycle, cryptographic hash chaining, and margin integrity."""
    tenant = TenantContext(
        company_id="COMP_US_01",
        allowed_company_ids=("COMP_US_01", "COMP_EU_02"),
        user_id="USR_SALES_LEAD",
        is_system_admin=False,
    )
    engine = EnterpriseSalesProcessEngine(tenant_context=tenant)

    order = SalesOrder(
        order_id="SO-2026-0091",
        company_id="COMP_US_01",
        customer_id="CUST-GLOBAL-CORP",
    )
    line1 = SalesOrderLine(
        line_id="LINE-1",
        product_sku="SKU-ENTERPRISE-AGENT-CORE",
        quantity=Decimal("5.00"),
        unit_price=Decimal("12000.00"),
        unit_cost=Decimal("4000.00"),
        discount_pct=Decimal("10.00"),
    )
    line2 = SalesOrderLine(
        line_id="LINE-2",
        product_sku="SKU-KNOWLEDGE-BASE-WAL",
        quantity=Decimal("2.00"),
        unit_price=Decimal("8500.00"),
        unit_cost=Decimal("3000.00"),
        discount_pct=Decimal("5.00"),
    )
    order.lines.extend([line1, line2])

    assert order.total_net_amount == Decimal("70150.00")
    assert order.total_cost_amount == Decimal("26000.00")
    assert order.overall_margin_pct == Decimal("62.94")

    engine.execute_ai_qualification_pipeline(order=order, step_id="STEP-QUAL-01")
    assert order.status == SalesOrderStatus.AI_SCORED
    assert order.ai_risk_score == Decimal("0.08")
    assert order.ai_conversion_probability == Decimal("0.92")
    assert len(order.state_history) == 1
    assert engine.verify_invariant(order) is True

    engine.transition_order_state(
        order=order,
        target_status=SalesOrderStatus.APPROVED,
        step_id="STEP-APPR-02",
        reason="Margin exceeds compliance gate; AI risk score optimal",
    )
    assert order.status == SalesOrderStatus.APPROVED
    assert len(order.state_history) == 2
    assert engine.verify_invariant(order) is True

    engine.transition_order_state(
        order=order,
        target_status=SalesOrderStatus.CONFIRMED,
        step_id="STEP-CONF-03",
        reason="Client signed Master Service Agreement",
    )
    assert order.status == SalesOrderStatus.CONFIRMED
    assert len(order.state_history) == 3
    assert engine.verify_invariant(order) is True

    final_step = engine.transition_order_state(
        order=order,
        target_status=SalesOrderStatus.INVOICED,
        step_id="STEP-INV-04",
        reason="ERP Billing synchronized and posted to GL",
    )
    assert order.status == SalesOrderStatus.INVOICED
    assert len(order.state_history) == 4
    assert order.current_state_hash == final_step.cumulative_hash
    assert engine.verify_invariant(order) is True


def test_2506_01423_invariant_tenant_boundary_fail_closed() -> None:
    """Verifies that cross-company data access triggers fail-closed security errors."""
    unauthorized_tenant = TenantContext(
        company_id="COMP_ASIA_03",
        allowed_company_ids=("COMP_ASIA_03",),
        user_id="USR_REGIONAL_REP",
        is_system_admin=False,
    )
    engine = EnterpriseSalesProcessEngine(tenant_context=unauthorized_tenant)
    foreign_order = SalesOrder(
        order_id="SO-EU-9999",
        company_id="COMP_EU_02",
        customer_id="CUST-EUROPE-AG",
    )

    with pytest.raises(TenantSecurityError) as exc_info:
        engine.execute_ai_qualification_pipeline(order=foreign_order, step_id="STEP-BREACH-01")

    assert "Unauthorized tenant operation" in str(exc_info.value)
    assert foreign_order.status == SalesOrderStatus.DRAFT
    assert len(foreign_order.state_history) == 0


def test_2506_01423_invariant_illegal_state_skip_and_discount_solver() -> None:
    """Verifies state skip rejection, PubGrub discount bounds, and cryptographic tamper detection."""
    tenant = TenantContext(
        company_id="COMP_US_01",
        allowed_company_ids=("COMP_US_01",),
        user_id="USR_AGENT_AUTO",
        is_system_admin=False,
    )
    engine = EnterpriseSalesProcessEngine(tenant_context=tenant)
    order = SalesOrder(order_id="SO-JUMP-01", company_id="COMP_US_01", customer_id="CUST-01")

    with pytest.raises(InvalidStateTransitionError) as exc_info:
        engine.transition_order_state(
            order=order,
            target_status=SalesOrderStatus.INVOICED,
            step_id="STEP-JUMP-ATTEMPT",
        )
    assert "Illegal state transition from DRAFT to INVOICED" in str(exc_info.value)

    order.lines.append(
        SalesOrderLine(
            line_id="L-01",
            product_sku="HARDWARE-SERVER",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            unit_cost=Decimal("90.00"),
            discount_pct=Decimal("0.00"),
        )
    )
    valid, msg = DiscountConstraintSolver.evaluate_discount_constraints(
        order=order, target_discount_pct=Decimal("20.00"), is_executive_override=False
    )
    assert valid is False
    assert "requires executive approval override" in msg

    valid_exec, msg_exec = DiscountConstraintSolver.evaluate_discount_constraints(
        order=order, target_discount_pct=Decimal("45.00"), is_executive_override=True
    )
    assert valid_exec is False
    assert "exceeds maximum absolute ceiling" in msg_exec

    # Tamper detection on approved order
    order_tamper = SalesOrder(order_id="SO-TAMPER-01", company_id="COMP_US_01", customer_id="CUST-AUDIT")
    order_tamper.lines.append(
        SalesOrderLine(
            line_id="L1",
            product_sku="SKU-CORE",
            quantity=Decimal("1.00"),
            unit_price=Decimal("1000.00"),
            unit_cost=Decimal("500.00"),
        )
    )
    engine.execute_ai_qualification_pipeline(order=order_tamper, step_id="STEP-T1")
    engine.transition_order_state(
        order=order_tamper, target_status=SalesOrderStatus.APPROVED, step_id="STEP-T2"
    )
    assert engine.verify_invariant(order_tamper) is True

    corrupted_step = FlowStateStepRecord(
        step_id=order_tamper.state_history[0].step_id,
        source_status=order_tamper.state_history[0].source_status,
        target_status=order_tamper.state_history[0].target_status,
        timestamp_utc=order_tamper.state_history[0].timestamp_utc,
        initiator_user_id=order_tamper.state_history[0].initiator_user_id,
        state_payload_hash="0" * 64,
        previous_hash=order_tamper.state_history[0].previous_hash,
        cumulative_hash="F" * 64,
    )
    order_tamper.state_history[0] = corrupted_step
    assert engine.verify_invariant(order_tamper) is False


AccountingLeg = _lock_mod.AccountingLeg
DealSnapshot = _lock_mod.DealSnapshot
DealState = _lock_mod.DealState
DomainInvariantViolationError = _lock_mod.DomainInvariantViolationError
EnterpriseStateInvariantEngine = _lock_mod.EnterpriseStateInvariantEngine
LedgerEvent = _lock_mod.LedgerEvent
LedgerIntegrityError = _lock_mod.LedgerIntegrityError
TenantIsolationViolationError = _lock_mod.TenantIsolationViolationError


def test_a2a_clearing_e2e_deal_lifecycle_and_double_entry() -> None:
    """Verifies end-to-end A2A deal lifecycle (DRAFT -> PROPOSED -> COMMITTED -> SETTLED) and double-entry balance."""
    engine = EnterpriseStateInvariantEngine(
        allowed_companies=["comp-alpha", "comp-beta", "comp-gamma"]
    )
    valid_legs = [
        AccountingLeg(account_id="1010-CASH", debit_cents=500000, credit_cents=0),
        AccountingLeg(account_id="4000-REVENUE", debit_cents=0, credit_cents=500000),
    ]

    deal = engine.create_genesis_deal(
        deal_id="DEAL-2026-001",
        initiator_id="comp-alpha",
        counterparty_id="comp-beta",
        sku_manifest=["SKU-AI-ROUTER-ENTERPRISE", "SKU-SUPPORT-TIER-1"],
        total_value_cents=500000,
        initial_legs=valid_legs,
    )
    assert deal.state == DealState.DRAFT
    assert deal.sequence_number == 0
    assert len(deal.current_hash) == 64

    snap1 = engine.transition_state(
        deal_id=deal.deal_id,
        target_state=DealState.PROPOSED,
        event=LedgerEvent(
            event_id="evt-prop-1",
            event_type="AGENT_PRICE_QUOTE",
            company_id="comp-alpha",
            payload={"term_days": 30},
        ),
    )
    assert snap1.state == DealState.PROPOSED
    assert snap1.sequence_number == 1

    snap2 = engine.transition_state(
        deal_id=deal.deal_id,
        target_state=DealState.COMMITTED,
        event=LedgerEvent(
            event_id="evt-comm-2",
            event_type="COUNTERPARTY_ACCEPT",
            company_id="comp-beta",
            payload={"accepted": True},
        ),
    )
    assert snap2.state == DealState.COMMITTED
    assert snap2.sequence_number == 2

    snap3 = engine.transition_state(
        deal_id=deal.deal_id,
        target_state=DealState.SETTLED,
        event=LedgerEvent(
            event_id="evt-settle-3",
            event_type="CLEARINGHOUSE_SETTLEMENT",
            company_id="comp-alpha",
            payload={"settled_cents": 500000},
        ),
    )
    assert snap3.state == DealState.SETTLED
    assert snap3.sequence_number == 3
    assert engine.verify_ledger_chain(deal.deal_id) is True

    # Double-entry imbalance must fail closed
    unbalanced_legs = [
        AccountingLeg(account_id="1010-CASH", debit_cents=500000, credit_cents=0),
        AccountingLeg(account_id="4000-REVENUE", debit_cents=0, credit_cents=450000),
    ]
    with pytest.raises(LedgerIntegrityError):
        engine.create_genesis_deal(
            deal_id="DEAL-UNBALANCED",
            initiator_id="comp-alpha",
            counterparty_id="comp-beta",
            sku_manifest=["SKU-ORCHESTRATOR"],
            total_value_cents=500000,
            initial_legs=unbalanced_legs,
        )

    # Unauthorized third-party company must fail closed
    with pytest.raises(TenantIsolationViolationError):
        engine.transition_state(
            deal_id=deal.deal_id,
            target_state=DealState.TERMINATED,
            event=LedgerEvent(
                event_id="evt-tamper-01",
                event_type="UNAUTHORIZED_MUTATION",
                company_id="comp-gamma",
                payload={},
            ),
        )


import asyncio

PipelineStage = _lock_mod.PipelineStage
KanbanCapacityExceededError = _lock_mod.KanbanCapacityExceededError
TokenLeaseTimeoutError = _lock_mod.TokenLeaseTimeoutError
PipelineEvent = _lock_mod.PipelineEvent
SalesLeadState = _lock_mod.SalesLeadState
KanbanPullController = _lock_mod.KanbanPullController
EnterpriseSalesPipeline = _lock_mod.EnterpriseSalesPipeline


def test_kanban_sales_pipeline_e2e_lifecycle_and_wip_bounds() -> None:
    """Verifies end-to-end CRM Lead-to-Deal Kanban Pull lifecycle, WIP limits, and SHA-256 chain integrity."""
    async def _run_scenario() -> None:
        limits = {
            PipelineStage.LEAD_TRIAGE: 3,
            PipelineStage.DEAL_QUALIFICATION: 2,
            PipelineStage.PROPOSAL_SYNTHESIS: 1,
            PipelineStage.EXECUTIVE_CLOSING: 2,
        }
        controller = KanbanPullController(limits)
        pipeline = EnterpriseSalesPipeline(controller)

        lead = EnterpriseSalesPipeline.initialize_lead(
            lead_id="LEAD-ENT-900",
            tenant_id="TENANT-ACME",
            initial_metrics={"arr_estimate": 120000, "source": "inbound_enterprise"},
        )
        assert lead.current_stage == PipelineStage.LEAD_TRIAGE
        assert len(lead.event_log) == 1
        assert lead.verify_audit_chain() is True

        async def qualify_agent(state: SalesLeadState) -> Dict[str, Any]:
            assert controller.get_active_wip(PipelineStage.DEAL_QUALIFICATION) == 1
            return {"meddic_score": 92, "qualified": True}

        lead = await pipeline.execute_stage_pull(
            lead, PipelineStage.DEAL_QUALIFICATION, qualify_agent
        )
        assert lead.current_stage == PipelineStage.DEAL_QUALIFICATION
        assert lead.deal_metrics["meddic_score"] == 92
        assert controller.get_active_wip(PipelineStage.DEAL_QUALIFICATION) == 0

        async def proposal_agent(state: SalesLeadState) -> Dict[str, Any]:
            assert controller.get_active_wip(PipelineStage.PROPOSAL_SYNTHESIS) == 1
            return {"discount_pct": 8.5, "proposal_doc": "SOW-900-V1"}

        lead = await pipeline.execute_stage_pull(
            lead, PipelineStage.PROPOSAL_SYNTHESIS, proposal_agent
        )
        assert lead.current_stage == PipelineStage.PROPOSAL_SYNTHESIS

        async def closing_agent(state: SalesLeadState) -> Dict[str, Any]:
            return {"countersigned": True, "po_number": "PO-ACME-2026"}

        lead = await pipeline.execute_stage_pull(
            lead, PipelineStage.EXECUTIVE_CLOSING, closing_agent
        )
        assert lead.current_stage == PipelineStage.EXECUTIVE_CLOSING

        async def finalize_agent(state: SalesLeadState) -> Dict[str, Any]:
            return {"closed_won": True}

        lead = await pipeline.execute_stage_pull(
            lead, PipelineStage.COMPLETED, finalize_agent
        )
        assert lead.current_stage == PipelineStage.COMPLETED
        assert len(lead.event_log) == 5
        assert lead.verify_audit_chain() is True

        # Verify strict non-blocking WIP capacity enforcement on PROPOSAL_SYNTHESIS (limit=1)
        lead_a = EnterpriseSalesPipeline.initialize_lead("L-A", "T-1", {})
        lead_b = EnterpriseSalesPipeline.initialize_lead("L-B", "T-1", {})

        async def noop(s: SalesLeadState) -> Dict[str, Any]:
            return {"ok": True}

        lead_a = await pipeline.execute_stage_pull(lead_a, PipelineStage.DEAL_QUALIFICATION, noop)
        lead_b = await pipeline.execute_stage_pull(lead_b, PipelineStage.DEAL_QUALIFICATION, noop)

        stage_entered = asyncio.Event()
        release_stage = asyncio.Event()

        async def slow_synthesis(s: SalesLeadState) -> Dict[str, Any]:
            stage_entered.set()
            await release_stage.wait()
            return {"synthesized": True}

        task_a = asyncio.create_task(
            pipeline.execute_stage_pull(lead_a, PipelineStage.PROPOSAL_SYNTHESIS, slow_synthesis)
        )
        await stage_entered.wait()
        assert controller.get_active_wip(PipelineStage.PROPOSAL_SYNTHESIS) == 1

        with pytest.raises(KanbanCapacityExceededError, match="CONWIP capacity exhausted"):
            await pipeline.execute_stage_pull(
                lead_b,
                PipelineStage.PROPOSAL_SYNTHESIS,
                noop,
                block=False,
            )

        release_stage.set()
        await task_a
        assert controller.get_active_wip(PipelineStage.PROPOSAL_SYNTHESIS) == 0

    asyncio.run(_run_scenario())


CircuitState = _lock_mod.CircuitState
SalesStage = _lock_mod.SalesStage
BulkheadCapacityExceededError = _lock_mod.BulkheadCapacityExceededError
SalesEvent = _lock_mod.SalesEvent
CircuitBreaker = _lock_mod.CircuitBreaker
BulkheadPool = _lock_mod.BulkheadPool
ResilientSalesEngine = _lock_mod.ResilientSalesEngine


def test_resilient_sales_engine_e2e_circuit_breaker_and_bulkhead() -> None:
    """Verifies end-to-end ResilientSalesEngine bulkhead isolation, circuit breaker transitions, and deterministic CPQ fallback."""
    async def _run_resilience_e2e() -> None:
        engine = ResilientSalesEngine()

        async def healthy_agent(event: SalesEvent) -> Dict[str, Any]:
            return {"amount": 1500.0, "status": "APPROVED"}

        def cpq_fallback(event: SalesEvent) -> Dict[str, Any]:
            return {"amount": 500.0, "status": "FALLBACK_CPQ"}

        for i in range(4):
            evt = SalesEvent(
                event_id=f"EVT-{i}",
                tenant_id=f"TENANT-{i % 2}",
                stage=SalesStage.P1_QUOTATION,
                action="GENERATE_QUOTE",
                payload={"line_items": 3},
            )
            res = await engine.execute_sales_step(evt, healthy_agent, cpq_fallback)
            assert res["amount"] == 1500.0

        assert len(engine.state_ledger) == 4
        assert engine.verify_invariant() is True
        assert engine.apply_odoo_odoo_pattern() is True
        assert engine.apply_astral_sh_uv_pattern() is True
        assert engine._current_state["pipeline_revenue"] == 6000.0
        assert engine._current_state["total_deals"] == 4
        assert engine._current_state["tenant_deals"]["TENANT-0"] == 2
        assert engine._current_state["tenant_deals"]["TENANT-1"] == 2

        # Verify CircuitBreaker state machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
        cb = CircuitBreaker(failure_threshold=2, recovery_time_seconds=0.1, success_threshold=2)
        assert cb.state == CircuitState.CLOSED
        await cb.record_result(success=False)
        await cb.record_result(success=False)
        assert cb.state == CircuitState.OPEN
        assert await cb.can_execute() is False

        await asyncio.sleep(0.12)
        assert await cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN
        await cb.record_result(success=True)
        await cb.record_result(success=True)
        assert cb.state == CircuitState.CLOSED

        # Verify Bulkhead concurrency isolation between P2_ENRICHMENT and P0_CLOSING
        pool = BulkheadPool({SalesStage.P2_ENRICHMENT: 1, SalesStage.P0_CLOSING: 5})
        entered = asyncio.Event()
        release = asyncio.Event()

        async def hold_enrichment() -> str:
            entered.set()
            await release.wait()
            return "ENRICHED"

        async def fast_close() -> str:
            return "CLOSED_DEAL"

        t1 = asyncio.create_task(pool.execute_in_bulkhead(SalesStage.P2_ENRICHMENT, hold_enrichment))
        await entered.wait()

        with pytest.raises(BulkheadCapacityExceededError):
            await pool.execute_in_bulkhead(SalesStage.P2_ENRICHMENT, fast_close)

        res_p0 = await pool.execute_in_bulkhead(SalesStage.P0_CLOSING, fast_close)
        assert res_p0 == "CLOSED_DEAL"

        release.set()
        assert await t1 == "ENRICHED"

    asyncio.run(_run_resilience_e2e())


SalesProcessStage = _lock_mod.SalesProcessStage
EnterpriseEvent = _lock_mod.EnterpriseEvent
PubGrubDealConstraintSolver = _lock_mod.PubGrubDealConstraintSolver
EnterpriseSalesState = _lock_mod.EnterpriseSalesState


def test_s_curve_pubgrub_deal_constraint_solver_and_merkle_state_e2e() -> None:
    """Verifies S-Curve PubGrub deal term constraint solver, mandatory rider enforcement, and Merkle state transitions."""
    state = EnterpriseSalesState(
        tenant_id="tenant-alpha",
        opportunity_id="opp-1001",
        current_stage=SalesProcessStage.LEAD_INCEPTION,
        active_terms={"pricing_tier": "enterprise_base"},
        max_memory_slots=2,
    )
    assert state.verify_invariant() is True

    policy = {
        "max_authorized_discount": 0.25,
        "mandatory_riders": ["data_residency_vn", "iso_27001_audit"],
    }

    evt1 = EnterpriseEvent(
        event_id="evt-001",
        tenant_id="tenant-alpha",
        timestamp=1776510000.0,
        action="QUALIFY_AND_NEGOTIATE",
        payload={
            "terms": {
                "discount_rate": 0.20,
                "attached_riders": ["data_residency_vn", "iso_27001_audit", "sla_99_9"],
            }
        },
        actor_agent_id="agent-scout-01",
    )
    h1 = state.transition_state(
        event=evt1,
        next_stage=SalesProcessStage.COMMERCIAL_NEGOTIATION,
        tenant_policy=policy,
    )
    assert len(h1) == 64
    assert state.last_block_hash == h1
    assert state.current_stage == SalesProcessStage.COMMERCIAL_NEGOTIATION
    assert len(state.state_history_hashes) == 1
    assert state.active_memory_slots == 0

    # Cross-tenant isolation check
    with pytest.raises(PermissionError, match="MultiTenantIsolationViolation"):
        state.apply_odoo_odoo_pattern("tenant-malicious")

    # Excessive discount must fail closed
    is_valid, reason = PubGrubDealConstraintSolver.resolve_deal_terms(
        {"discount_rate": 0.35, "attached_riders": ["data_residency_vn", "iso_27001_audit"]},
        policy,
    )
    assert is_valid is False
    assert "ConstraintViolation: requested discount 0.35 exceeds limit 0.25" in str(reason)

    # Missing mandatory rider must fail closed
    is_valid2, reason2 = PubGrubDealConstraintSolver.resolve_deal_terms(
        {"discount_rate": 0.15, "attached_riders": ["sla_99_9"]},
        policy,
    )
    assert is_valid2 is False
    assert "missing mandatory riders" in str(reason2)

    # Memory slot saturation check
    state.active_memory_slots = 2
    with pytest.raises(BufferError, match="MemoryInvariantBreached"):
        state.transition_state(
            event=evt1,
            next_stage=SalesProcessStage.COMPLIANCE_SIGN_OFF,
            tenant_policy=policy,
        )


OrchestratorSalesStage = _lock_mod.OrchestratorSalesStage
OrchestratorTenantContext = _lock_mod.OrchestratorTenantContext
OrchestratorSalesEvent = _lock_mod.OrchestratorSalesEvent
BoundedResourcePool = _lock_mod.BoundedResourcePool
EnterpriseSalesOrchestrator = _lock_mod.EnterpriseSalesOrchestrator
InvariantViolationError = _lock_mod.InvariantViolationError
TenantSecurityViolationError = _lock_mod.TenantSecurityViolationError
ConcurrencyResourceExhaustedError = _lock_mod.ConcurrencyResourceExhaustedError


def test_enterprise_sales_orchestrator_double_entry_and_bounded_pool_e2e() -> None:
    """Verifies EnterpriseSalesOrchestrator weighted pipeline delta ledger, multi-company RLS, and bounded slot pool."""
    orchestrator = EnterpriseSalesOrchestrator(max_concurrent_slots=4)
    primary_tenant = OrchestratorTenantContext(company_id=1, allowed_company_ids=(1, 2), user_id=101, is_system_admin=False)
    foreign_tenant = OrchestratorTenantContext(company_id=99, allowed_company_ids=(99,), user_id=999, is_system_admin=False)

    orchestrator.register_opportunity(
        tenant_context=primary_tenant,
        opportunity_id="OPP-001",
        company_id=1,
        initial_value=10000.0,
    )

    ev1 = OrchestratorSalesEvent(
        event_id="EVT-01",
        opportunity_id="OPP-001",
        company_id=1,
        source_stage=OrchestratorSalesStage.LEAD,
        target_stage=OrchestratorSalesStage.QUALIFICATION,
        deal_value=12000.0,
        probability=0.25,
        payload={"qualified_by": "agent_alpha", "bant_score": 85},
    )
    entry1 = orchestrator.execute_transition_flow(primary_tenant, ev1)

    assert entry1.index == 0
    assert entry1.prev_hash == "0" * 64
    assert len(entry1.current_hash) == 64
    assert entry1.delta_weighted_value == (12000.0 * 0.25) - (10000.0 * 0.10)
    assert orchestrator.verify_invariant() is True

    # Illegal stage skip must fail closed
    orchestrator.register_opportunity(primary_tenant, "OPP-002", 1, 50000.0)
    illegal_ev = OrchestratorSalesEvent(
        event_id="EVT-ILLEGAL",
        opportunity_id="OPP-002",
        company_id=1,
        source_stage=OrchestratorSalesStage.LEAD,
        target_stage=OrchestratorSalesStage.CLOSED_WON,
        deal_value=50000.0,
        probability=1.0,
        payload={"exploit": "skip_stages"},
    )
    with pytest.raises(InvariantViolationError, match="Illegal stage transition from LEAD to CLOSED_WON"):
        orchestrator.execute_transition_flow(primary_tenant, illegal_ev)

    # Cross-company tamper attempt must fail closed
    tamper_ev = OrchestratorSalesEvent(
        event_id="EVT-INTRUDER",
        opportunity_id="OPP-001",
        company_id=1,
        source_stage=OrchestratorSalesStage.QUALIFICATION,
        target_stage=OrchestratorSalesStage.PROPOSAL,
        deal_value=12000.0,
        probability=0.50,
        payload={"actor": "unauthorized"},
    )
    with pytest.raises(TenantSecurityViolationError, match="Tenant Security Violation"):
        orchestrator.execute_transition_flow(foreign_tenant, tamper_ev)

    # Bounded slot pool exhaustion & release
    for idx in range(1, 5):
        orchestrator.resource_pool.acquire(f"hold_slot_{idx}")

    with pytest.raises(ConcurrencyResourceExhaustedError, match="Resource quota exhausted"):
        orchestrator.execute_transition_flow(
            primary_tenant,
            OrchestratorSalesEvent(
                event_id="EVT-BURST",
                opportunity_id="OPP-001",
                company_id=1,
                source_stage=OrchestratorSalesStage.QUALIFICATION,
                target_stage=OrchestratorSalesStage.PROPOSAL,
                deal_value=12000.0,
                probability=0.50,
                payload={},
            ),
        )

    orchestrator.resource_pool.release("hold_slot_1")
    assert orchestrator.resource_pool.current_utilization == 3
    assert orchestrator.apply_astral_sh_uv_pattern() is True


import hashlib

SalesOrderState = _lock_mod.SalesOrderState
DomainSecurityError = _lock_mod.DomainSecurityError
TenantSecurityContext = _lock_mod.TenantSecurityContext
QuotationLineItem = _lock_mod.QuotationLineItem
SalesTransitionEvent = _lock_mod.SalesTransitionEvent
EnterpriseSalesStateMachine = _lock_mod.EnterpriseSalesStateMachine


def test_cdk_cssm_margin_floor_and_counter_signature_e2e() -> None:
    """Verifies CDK-CSSM full sales order counter-signature lifecycle and gross margin floor enforcement."""
    tenant = TenantSecurityContext(
        tenant_id="TENANT_APAC_HQ",
        company_id=101,
        minimum_margin_floor=Decimal("0.2500"),
        allowed_agent_roles=("LEAD_SCORER", "QUOTATION_AGENT", "COMPLIANCE_OFFICER"),
    )
    sm = EnterpriseSalesStateMachine(order_id="SO-2026-9041", tenant_context=tenant)
    assert sm.current_state == SalesOrderState.DRAFT_LEAD
    assert sm.verify_chain_integrity() is True

    evt1 = SalesTransitionEvent(
        event_id="EVT-001",
        order_id=sm.order_id,
        from_state=SalesOrderState.DRAFT_LEAD,
        to_state=SalesOrderState.QUALIFIED,
        agent_id="AGENT-SCORE-01",
        agent_role="LEAD_SCORER",
        agent_signature_digest=hashlib.sha256(b"sig1").hexdigest(),
        line_items=(),
        timestamp_utc="2026-10-18T15:00:00Z",
    )
    e1 = sm.transition(evt1, requesting_company_id=101)
    assert sm.current_state == SalesOrderState.QUALIFIED
    assert e1.sequence == 1

    # Sub-floor margin (10% < 25%) must be rejected fail-closed
    sub_floor_items = (
        QuotationLineItem(
            product_sku="SKU-ENTERPRISE-CORE",
            quantity=5,
            unit_cost=Decimal("90.00"),
            offered_price=Decimal("100.00"),
        ),
    )
    evt_breach = SalesTransitionEvent(
        event_id="EVT-BREACH",
        order_id=sm.order_id,
        from_state=SalesOrderState.QUALIFIED,
        to_state=SalesOrderState.QUOTATION_PROPOSED,
        agent_id="AGENT-QUOTE-02",
        agent_role="QUOTATION_AGENT",
        agent_signature_digest="sig_breach",
        line_items=sub_floor_items,
        timestamp_utc="2026-10-18T15:05:00Z",
    )
    with pytest.raises(DomainSecurityError, match="Financial Invariant Breach"):
        sm.transition(evt_breach, requesting_company_id=101)
    assert sm.current_state == SalesOrderState.QUALIFIED

    # Valid margin (40% >= 25%) advances through QUOTATION_PROPOSED -> COUNTER_SIGNED_AUDITED -> CONFIRMED_SALES_ORDER
    valid_items = (
        QuotationLineItem(
            product_sku="SKU-ENTERPRISE-CORE",
            quantity=10,
            unit_cost=Decimal("60.00"),
            offered_price=Decimal("100.00"),
        ),
    )
    evt2 = SalesTransitionEvent(
        event_id="EVT-002",
        order_id=sm.order_id,
        from_state=SalesOrderState.QUALIFIED,
        to_state=SalesOrderState.QUOTATION_PROPOSED,
        agent_id="AGENT-QUOTE-02",
        agent_role="QUOTATION_AGENT",
        agent_signature_digest=hashlib.sha256(b"sig2").hexdigest(),
        line_items=valid_items,
        timestamp_utc="2026-10-18T15:10:00Z",
    )
    sm.transition(evt2, requesting_company_id=101)

    evt3 = SalesTransitionEvent(
        event_id="EVT-003",
        order_id=sm.order_id,
        from_state=SalesOrderState.QUOTATION_PROPOSED,
        to_state=SalesOrderState.COUNTER_SIGNED_AUDITED,
        agent_id="AGENT-AUDIT-03",
        agent_role="COMPLIANCE_OFFICER",
        agent_signature_digest=hashlib.sha256(b"sig3").hexdigest(),
        line_items=valid_items,
        timestamp_utc="2026-10-18T15:20:00Z",
    )
    sm.transition(evt3, requesting_company_id=101)

    evt4 = SalesTransitionEvent(
        event_id="EVT-004",
        order_id=sm.order_id,
        from_state=SalesOrderState.COUNTER_SIGNED_AUDITED,
        to_state=SalesOrderState.CONFIRMED_SALES_ORDER,
        agent_id="AGENT-AUDIT-03",
        agent_role="COMPLIANCE_OFFICER",
        agent_signature_digest=hashlib.sha256(b"sig4").hexdigest(),
        line_items=valid_items,
        timestamp_utc="2026-10-18T15:30:00Z",
    )
    sm.transition(evt4, requesting_company_id=101)
    assert sm.current_state == SalesOrderState.CONFIRMED_SALES_ORDER
    assert len(sm.ledger) == 5
    assert sm.verify_chain_integrity() is True


PolicySalesStage = _lock_mod.PolicySalesStage
PolicyConstraintUnsatError = _lock_mod.PolicyConstraintUnsatError
ResourceExhaustionError = _lock_mod.ResourceExhaustionError
DealPolicyRequirement = _lock_mod.DealPolicyRequirement
PubGrubPolicyStateMachine = _lock_mod.PubGrubPolicyStateMachine


def test_pubgrub_policy_state_machine_e2e_sat_and_lease_bounds() -> None:
    """Verifies PG-CASPR sales stage policy SAT solver, executive signoff rules, and bounded lease pool."""
    policy = DealPolicyRequirement(
        max_discount_pct=20.0,
        min_contract_value=50000.0,
        requires_executive_signoff=True,
        requires_security_review=True,
    )
    engine = PubGrubPolicyStateMachine(tenant_id="tenant_insilos_corp", max_concurrent_leases=2)
    assert engine.verify_invariant() is True

    evt1 = engine.transition_stage(
        request_tenant_id="tenant_insilos_corp",
        deal_id="DEAL-001",
        target_stage=PolicySalesStage.QUALIFIED,
        payload={"contract_value": 75000.0, "discount_pct": 10.0},
        policy=policy,
    )
    assert evt1.from_stage == PolicySalesStage.LEAD
    assert evt1.to_stage == PolicySalesStage.QUALIFIED
    assert evt1.prev_hash == "0" * 64
    assert len(evt1.current_hash) == 64

    evt2 = engine.transition_stage(
        request_tenant_id="tenant_insilos_corp",
        deal_id="DEAL-001",
        target_stage=PolicySalesStage.PROPOSAL,
        payload={"contract_value": 75000.0, "discount_pct": 15.0},
        policy=policy,
    )
    assert evt2.prev_hash == evt1.current_hash
    assert engine.verify_invariant() is True

    # Illegal stage skip must fail closed
    with pytest.raises(InvalidStateTransitionError, match="Illegal transition from LEAD to CLOSED_WON"):
        engine.transition_stage(
            request_tenant_id="tenant_insilos_corp",
            deal_id="DEAL-SKIP",
            target_stage=PolicySalesStage.CLOSED_WON,
            payload={
                "contract_value": 100000.0,
                "discount_pct": 0.0,
                "executive_signoff": True,
                "security_review_completed": True,
            },
            policy=policy,
        )

    # Cross-tenant access must fail closed
    with pytest.raises(TenantSecurityViolationError, match="Cross-tenant access rejected"):
        engine.apply_odoo_odoo_pattern("tenant_competitor_corp")

    # Excessive discount without executive signoff must fail closed
    with pytest.raises(PolicyConstraintUnsatError, match="exceeds limit 20.0% without executive signoff"):
        engine.transition_stage(
            request_tenant_id="tenant_insilos_corp",
            deal_id="DEAL-DISCOUNT",
            target_stage=PolicySalesStage.QUALIFIED,
            payload={"contract_value": 100000.0, "discount_pct": 35.0, "executive_signoff": False},
            policy=policy,
        )

    # Lease pool capacity bounds
    assert engine.acquire_lease() == 1
    assert engine.acquire_lease() == 2
    with pytest.raises(ResourceExhaustionError):
        engine.acquire_lease()
    assert engine.release_lease() == 1
    assert engine.release_lease() == 0
    assert engine.apply_astral_sh_uv_pattern() is True


SalesQuoteCRDT = _lock_mod.SalesQuoteCRDT


def test_sales_quote_crdt_e2e_concurrent_merge_and_tombstones() -> None:
    """Verifies OR-Set SalesQuoteCRDT offline-first concurrent proposal convergence and tombstone propagation."""
    rep_replica = SalesQuoteCRDT(quote_id="Q-1001", client_id="rep_mobile_client")
    ai_replica = SalesQuoteCRDT(quote_id="Q-1001", client_id="ai_margin_agent")

    rep_replica.add_line_item(
        product_sku="SKU-ENTERPRISE-CORE",
        quantity=50,
        unit_price_cents=12000,
        discount_pct=10.0,
    )
    ai_replica.add_line_item(
        product_sku="SKU-24-7-PREMIUM-SUPPORT",
        quantity=1,
        unit_price_cents=50000,
        discount_pct=5.0,
    )

    rep_replica.merge(ai_replica)
    ai_replica.merge(rep_replica)

    rep_skus = {item.product_sku for item in rep_replica.active_items()}
    ai_skus = {item.product_sku for item in ai_replica.active_items()}

    assert rep_skus == {"SKU-ENTERPRISE-CORE", "SKU-24-7-PREMIUM-SUPPORT"}
    assert rep_skus == ai_skus
    assert rep_replica.calculate_total_cents() == ai_replica.calculate_total_cents()
    assert rep_replica.verify_invariant() is True
    assert ai_replica.verify_invariant() is True

    # Tombstone propagation across replicas
    node_a = SalesQuoteCRDT(quote_id="Q-2002", client_id="node_a")
    node_b = SalesQuoteCRDT(quote_id="Q-2002", client_id="node_b")
    tag = node_a.add_line_item("SKU-HARDWARE-TOKEN", 10, 2500, 0.0)
    node_b.merge(node_a)
    assert len(node_b.active_items()) == 1

    node_a.remove_line_item(tag)
    assert len(node_a.active_items()) == 0
    node_b.merge(node_a)
    assert len(node_b.active_items()) == 0
    assert node_b.calculate_total_cents() == 0
    assert node_b.verify_invariant() is True


GateSalesStage = _lock_mod.GateSalesStage
GateSalesEvent = _lock_mod.GateSalesEvent
StateAuditBlock = _lock_mod.StateAuditBlock
BantGateSalesStateMachine = _lock_mod.BantGateSalesStateMachine


def test_bant_gate_sales_state_machine_e2e_lifecycle_and_gate_validation() -> None:
    """Verifies BANT-to-Closed-Won semantic gates, RLS tenant guard, and StateAuditBlock chain."""
    fsm = BantGateSalesStateMachine(tenant_id="tenant_acme_01", opportunity_id="opp_99412")
    assert fsm.current_stage == GateSalesStage.LEAD_DISCOVERY
    assert len(fsm.audit_chain) == 1
    assert fsm.verify_invariant() is True

    # Cross-tenant isolation check
    with pytest.raises(PermissionError, match="Access Denied: Tenant mismatch"):
        fsm.transition(
            GateSalesEvent(
                event_id="evt_leak",
                tenant_id="tenant_competitor_99",
                target_stage=GateSalesStage.QUALIFICATION_BANT,
                payload={"budget": 50000, "authority": "VP", "need": "CRM", "timeline": "Q1"},
                timestamp_utc="2026-04-19T12:05:00Z",
                actor_id="malicious_agent",
            )
        )

    # Illegal stage jump and incomplete BANT payload check
    with pytest.raises(ValueError, match="Invalid transition"):
        fsm.transition(
            GateSalesEvent(
                event_id="evt_skip",
                tenant_id="tenant_acme_01",
                target_stage=GateSalesStage.CLOSED_WON,
                payload={"contract_signature_ref": "sig_fake"},
                timestamp_utc="2026-04-19T12:10:00Z",
                actor_id="agent_sales_02",
            )
        )
    with pytest.raises(ValueError, match="BANT qualification failed"):
        fsm.transition(
            GateSalesEvent(
                event_id="evt_bad_bant",
                tenant_id="tenant_acme_01",
                target_stage=GateSalesStage.QUALIFICATION_BANT,
                payload={"budget": -100, "authority": "CTO"},
                timestamp_utc="2026-04-19T12:11:00Z",
                actor_id="agent_sales_02",
            )
        )

    # Full 5-stage progression to CLOSED_WON
    steps = [
        (
            "evt_01",
            GateSalesStage.QUALIFICATION_BANT,
            {"budget": 150000, "authority": "CTO", "need": "ERP Consolidation", "timeline": "Q3"},
        ),
        ("evt_02", GateSalesStage.TECHNICAL_VALIDATION, {"architecture_approved": True}),
        ("evt_03", GateSalesStage.COMMERCIAL_PROPOSAL, {"pricing_schedule_id": "PRC-2026-88B"}),
        ("evt_04", GateSalesStage.LEGAL_SECURITY_REVIEW, {"dpa_signed": True}),
        ("evt_05", GateSalesStage.CLOSED_WON, {"contract_signature_ref": "DOCUSIGN-ENV-7741"}),
    ]
    for idx, (evt_id, target, payload) in enumerate(steps, start=1):
        block = fsm.transition(
            GateSalesEvent(
                event_id=evt_id,
                tenant_id="tenant_acme_01",
                target_stage=target,
                payload=payload,
                timestamp_utc=f"2026-04-19T12:0{idx}:00Z",
                actor_id="agent_sales_01",
            )
        )
        assert block.index == idx
        assert fsm.current_stage == target
        assert fsm.verify_invariant() is True

    assert len(fsm.audit_chain) == 6
    assert fsm.metadata["contract_signature_ref"] == "DOCUSIGN-ENV-7741"

    # Tamper detection on StateAuditBlock chain
    original = fsm.audit_chain[1]
    fsm.audit_chain[1] = StateAuditBlock(
        index=original.index,
        prev_hash=original.prev_hash,
        state_digest="f" * 64,
        event_id=original.event_id,
        timestamp_utc=original.timestamp_utc,
        block_hash=original.block_hash,
    )
    assert fsm.verify_invariant() is False


IntegrityViolationError = _lock_mod.IntegrityViolationError
ConstraintResolutionError = _lock_mod.ConstraintResolutionError
SalesQuotationCRDT = _lock_mod.SalesQuotationCRDT
MerkleTransparencyLog = _lock_mod.MerkleTransparencyLog
PubGrubQuotationSolver = _lock_mod.PubGrubQuotationSolver


def test_json_crdt_merkle_transparency_and_pubgrub_quotation_solver_e2e() -> None:
    """Verifies SalesQuotationCRDT convergence, MerkleTransparencyLog inclusion proofs, and PubGrubQuotationSolver CPQ bundle resolution."""
    quote_agent_a = SalesQuotationCRDT(document_id="QUOTE-2026-001", actor_id="agent_alpha")
    quote_agent_b = SalesQuotationCRDT(document_id="QUOTE-2026-001", actor_id="agent_beta")

    quote_agent_a.set_header_field("customer", "Acme Corporation")
    quote_agent_b.merge(quote_agent_a)

    quote_agent_a.set_header_field("global_discount_percent", 10.0)
    quote_agent_a.set_line_item("LINE-001", "sku", "CLOUD-ERP-ENTERPRISE")
    quote_agent_a.set_line_item("LINE-001", "unit_price", 15000.0)

    quote_agent_b.set_header_field("payment_terms", "NET-45")
    quote_agent_b.set_line_item("LINE-002", "sku", "AI-AUTOMATION-ADDON")
    quote_agent_b.set_line_item("LINE-002", "unit_price", 4500.0)

    quote_agent_a.merge(quote_agent_b)
    quote_agent_b.merge(quote_agent_a)

    state_a = quote_agent_a.to_canonical_dict()
    state_b = quote_agent_b.to_canonical_dict()
    assert state_a["header"]["customer"] == "Acme Corporation"
    assert state_a["header"]["global_discount_percent"] == 10.0
    assert state_a["header"]["payment_terms"] == "NET-45"
    assert state_a["line_items"] == state_b["line_items"]
    assert state_a["tombstones"] == state_b["tombstones"]

    # Tombstone fail-closed check
    quote_agent_a.remove_line_item("LINE-002")
    with pytest.raises(IntegrityViolationError, match="Cannot mutate tombstoned line item"):
        quote_agent_a.set_line_item("LINE-002", "sku", "RESURRECTED-SKU")

    # Merkle Transparency Log inclusion and tamper proofs
    tree = MerkleTransparencyLog()
    events = [
        {"quote_id": "Q-01", "action": "CREATE", "amount": 10000.0, "approver": "system"},
        {"quote_id": "Q-01", "action": "APPLY_DISCOUNT", "amount": 9000.0, "approver": "sales_rep_1"},
        {"quote_id": "Q-01", "action": "ESCALATE_MARGIN", "amount": 9000.0, "approver": "sales_manager_4"},
        {"quote_id": "Q-01", "action": "FINAL_SIGNATURE", "amount": 9000.0, "approver": "vp_sales"},
    ]
    leaf_records = [tree.record_approval_event(ev) for ev in events]
    root_hash = tree.get_root_hash()
    assert len(root_hash) == 64

    for idx, leaf_h in leaf_records:
        proof = tree.generate_inclusion_proof(idx)
        assert MerkleTransparencyLog.verify_inclusion_proof(leaf_h, proof, root_hash) is True

    assert (
        MerkleTransparencyLog.verify_inclusion_proof(
            "0" * 64, tree.generate_inclusion_proof(0), root_hash
        )
        is False
    )

    # PubGrub CPQ Bundle Solver
    solver = PubGrubQuotationSolver()
    solver.register_dependency("SKU-ENTERPRISE-BUNDLE", "SKU-CLOUD-STORAGE")
    solver.register_dependency("SKU-ENTERPRISE-BUNDLE", "SKU-DB-CONNECTOR")
    solver.register_incompatibility("SKU-LEGACY-ONPREM", "SKU-CLOUD-STORAGE")

    resolved = solver.solve_bundle(["SKU-ENTERPRISE-BUNDLE"])
    assert resolved == ["SKU-CLOUD-STORAGE", "SKU-DB-CONNECTOR", "SKU-ENTERPRISE-BUNDLE"]

    with pytest.raises(ConstraintResolutionError, match="SKU conflict detected"):
        solver.solve_bundle(["SKU-ENTERPRISE-BUNDLE", "SKU-LEGACY-ONPREM"])


EnvelopeBreachError = _lock_mod.EnvelopeBreachError
TwoChallengeLockoutError = _lock_mod.TwoChallengeLockoutError
MerkleTreeIntegrity = _lock_mod.MerkleTreeIntegrity
CrdtJsonRegister = _lock_mod.CrdtJsonRegister
AviationPreFlightChecklistGate = _lock_mod.AviationPreFlightChecklistGate


def test_aviation_preflight_checklist_gate_and_two_challenge_circuit_breaker_e2e() -> None:
    """Verifies AviationPreFlightChecklistGate margin envelope protection, Two-Challenge lockout, CrdtJsonRegister, and MerkleTreeIntegrity."""
    reg = CrdtJsonRegister(key="discount_rate", initial_value=0.10, timestamp=100, author="agent_a")
    assert reg.update(new_value=0.25, timestamp=95, author="agent_b") is False
    assert reg.value == 0.10
    assert reg.update(new_value=0.15, timestamp=105, author="agent_b") is True
    assert reg.value == 0.15
    assert reg.author == "agent_b"

    leaves = [
        MerkleTreeIntegrity.hash_leaf({"quote_id": "Q-001", "discount": 0.05}),
        MerkleTreeIntegrity.hash_leaf({"quote_id": "Q-002", "discount": 0.12}),
        MerkleTreeIntegrity.hash_leaf({"quote_id": "Q-003", "discount": 0.08}),
    ]
    root_1 = MerkleTreeIntegrity.compute_root(leaves)
    assert len(root_1) == 64
    assert root_1 == MerkleTreeIntegrity.compute_root(leaves)
    tampered_leaves = list(leaves)
    tampered_leaves[1] = MerkleTreeIntegrity.hash_leaf({"quote_id": "Q-002", "discount": 0.20})
    assert root_1 != MerkleTreeIntegrity.compute_root(tampered_leaves)

    gate = AviationPreFlightChecklistGate(tenant_id="enterprise_sg", flag_enabled=True)
    res = gate.evaluate_preflight_envelope(
        quote_id="Q-1001",
        total_revenue=100000.0,
        cost_basis=75000.0,
        line_items=[{"sku": "ERP-CORE", "qty": 1, "price": 100000.0}],
        company_id="enterprise_sg",
    )
    assert res["status"] == "CLEARED"
    assert res["margin_ratio"] == 0.25

    with pytest.raises(InvariantViolationError, match="Tenant Isolation Breach"):
        gate.evaluate_preflight_envelope(
            quote_id="Q-1002",
            total_revenue=50000.0,
            cost_basis=30000.0,
            line_items=[{"sku": "ERP-ADDON", "qty": 1, "price": 50000.0}],
            company_id="malicious_tenant",
        )
    assert gate.consecutive_challenge_failures == 1

    with pytest.raises(EnvelopeBreachError, match="Margin breach: Computed 0.1000"):
        gate.evaluate_preflight_envelope(
            quote_id="Q-1003",
            total_revenue=10000.0,
            cost_basis=9000.0,
            line_items=[{"sku": "CONSULTING", "price": 10000.0}],
            company_id="enterprise_sg",
        )
    assert gate.consecutive_challenge_failures == 2

    with pytest.raises(
        TwoChallengeLockoutError, match="locked out: 2 consecutive flight-envelope challenges tripped"
    ):
        gate.evaluate_preflight_envelope(
            quote_id="Q-1004",
            total_revenue=10000.0,
            cost_basis=5000.0,
            line_items=[{"sku": "CONSULTING", "price": 10000.0}],
            company_id="enterprise_sg",
        )


JSONCRDTSalesDoc = _lock_mod.JSONCRDTSalesDoc
MerkleTransparencyTree = _lock_mod.MerkleTransparencyTree
OdooContext = _lock_mod.OdooContext
OdooModelRegistry = _lock_mod.OdooModelRegistry
TaskState = _lock_mod.TaskState
PrefectSalesFlowRunner = _lock_mod.PrefectSalesFlowRunner


def test_scpoe_json_crdt_merkle_tree_odoo_registry_and_prefect_flow_e2e() -> None:
    """Verifies SCPOE JSONCRDTSalesDoc convergence, MerkleTransparencyTree audit proofs, OdooModelRegistry RLS, and PrefectSalesFlowRunner retries/memoization."""
    doc_a = JSONCRDTSalesDoc(doc_id="SO-2026-001")
    doc_b = JSONCRDTSalesDoc(doc_id="SO-2026-001")

    doc_a.set_item("L1", "SERVER-RACK", 5000.0, 2, 0.0, actor_id="rep_a", timestamp=100.0)
    doc_a.set_item("L2", "INSTALL-SERVICE", 1500.0, 1, 0.0, actor_id="rep_a", timestamp=101.0)
    doc_b.set_item("L1", "SERVER-RACK", 5000.0, 2, 15.0, actor_id="mgr_b", timestamp=105.0)
    doc_b.remove_item("L2", actor_id="mgr_b", timestamp=106.0)

    merged_a = doc_a.merge(doc_b)
    merged_b = doc_b.merge(doc_a)
    assert merged_a.compute_total() == 8500.0
    assert merged_b.compute_total() == 8500.0
    assert len(merged_a._items) == 1
    assert "L2" not in merged_a._items

    tree = MerkleTransparencyTree()
    leaf1 = tree.append_entry({"event": "CREATE_QUOTE", "so_id": "SO-101", "amount": 10000})
    leaf2 = tree.append_entry({"event": "APPLY_DISCOUNT", "so_id": "SO-101", "pct": 20})
    tree.append_entry({"event": "APPROVE_MARGIN", "so_id": "SO-101", "mgr": "alice"})
    root = tree.get_root()
    proof_leaf2 = tree.get_audit_proof(1)
    assert MerkleTransparencyTree.verify_proof(leaf2, proof_leaf2, root) is True
    assert MerkleTransparencyTree.verify_proof(leaf2[:-4] + "ffff", proof_leaf2, root) is False
    assert MerkleTransparencyTree.verify_proof(leaf1, proof_leaf2, root) is False

    registry = OdooModelRegistry()
    registry.register_record(
        "crm.lead",
        {"id": 1, "name": "Cloud Migration", "company_id": 1, "expected_revenue": 50000},
    )
    registry.register_record(
        "crm.lead",
        {"id": 2, "name": "AI ERP Suite", "company_id": 2, "expected_revenue": 120000},
    )
    registry.register_record(
        "crm.lead",
        {"id": 3, "name": "Global Support", "company_id": 1, "expected_revenue": 30000},
    )
    ctx1 = OdooContext(active_company_id=1, allowed_company_ids=[1], user_id=10)
    results1 = registry.search_records("crm.lead", [("expected_revenue", ">", 20000)], ctx1)
    assert {r["id"] for r in results1} == {1, 3}
    ctx2 = OdooContext(active_company_id=1, allowed_company_ids=[1, 2], user_id=1)
    results2 = registry.search_records("crm.lead", [("expected_revenue", ">", 40000)], ctx2)
    assert {r["id"] for r in results2} == {1, 2}

    runner = PrefectSalesFlowRunner()
    call_count = 0

    def unreliable_ai_scoring(deal_size: float) -> float:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("Transient timeout reaching AI model inference gateway")
        return deal_size * 0.85

    res1 = runner.execute_task("ai_win_scoring", unreliable_ai_scoring, (100000.0,), max_retries=2)
    assert res1.state == TaskState.COMPLETED
    assert res1.return_value == 85000.0
    assert res1.retry_count == 1
    assert call_count == 2

    res2 = runner.execute_task("ai_win_scoring", unreliable_ai_scoring, (100000.0,), max_retries=2)
    assert res2.state == TaskState.COMPLETED
    assert res2.return_value == 85000.0
    assert res2.retry_count == 0
    assert call_count == 2


AxiomaticDiscretionEnclave = _lock_mod.AxiomaticDiscretionEnclave


def test_axiomatic_discretion_enclave_delta_merge_and_merkle_proof_e2e() -> None:
    """Verifies AxiomaticDiscretionEnclave commutative JSON delta merge, Merkle proof enclave, and multi-company approval rules."""
    initial_state = {
        "order_id": "SO-2026-0042",
        "lines": {"item_1": {"qty": 5, "price": 100.0}},
        "discount_pct": 0.0,
        "version": 1,
        "actor": "system",
    }
    delta_rep = {"lines": {"item_1": {"qty": 10}}, "version": 2, "actor": "human"}
    delta_ai = {"discount_pct": 5.0, "version": 2, "actor": "ai_agent"}

    state_ab = AxiomaticDiscretionEnclave.apply_commutative_delta(
        AxiomaticDiscretionEnclave.apply_commutative_delta(initial_state, delta_rep),
        delta_ai,
    )
    state_ba = AxiomaticDiscretionEnclave.apply_commutative_delta(
        AxiomaticDiscretionEnclave.apply_commutative_delta(initial_state, delta_ai),
        delta_rep,
    )
    assert state_ab["lines"]["item_1"]["qty"] == 10
    assert state_ab["discount_pct"] == 5.0
    assert state_ab == state_ba

    enclave = AxiomaticDiscretionEnclave(company_id=1)
    leaf_1 = enclave.record_discretionary_concession("AGENT_ACTION:LEAD_QUALIFIED:SCORE_88")
    leaf_2 = enclave.record_discretionary_concession("AGENT_ACTION:DISCOUNT_PROPOSED:3.5_PCT")
    assert leaf_1 != leaf_2
    merkle_root = enclave.compute_merkle_root()
    assert len(merkle_root) == 64
    assert merkle_root == AxiomaticDiscretionEnclave.hash_node(leaf_1, leaf_2)

    approved_rec = enclave.evaluate_quote_approval(
        {"id": 101, "company_id": 1, "quote_amount": 54000.0, "approved": False}
    )
    assert approved_rec["approved"] is True

    with pytest.raises(PermissionError, match="Multi-company isolation breach"):
        enclave.evaluate_quote_approval(
            {"id": 102, "company_id": 2, "quote_amount": 25000.0, "approved": False}
        )


CRDTOperation = _lock_mod.CRDTOperation
MerkleAuditNode = _lock_mod.MerkleAuditNode
ReplicatedSalesLeadCRDT = _lock_mod.ReplicatedSalesLeadCRDT
TenantSecurityError = _lock_mod.TenantSecurityError


def test_replicated_sales_lead_crdt_convergence_and_merkle_tamper_e2e() -> None:
    """Verifies ReplicatedSalesLeadCRDT out-of-order convergence, MerkleAuditNode tamper detection, and TenantSecurityError isolation."""
    lead_id = "crm_lead_10492"
    tenant_id = "company_group_alpha"

    replica_a = ReplicatedSalesLeadCRDT(lead_id=lead_id, tenant_id=tenant_id)
    replica_b = ReplicatedSalesLeadCRDT(lead_id=lead_id, tenant_id=tenant_id)

    op1 = CRDTOperation(
        op_id="op_agent1_001",
        tenant_id=tenant_id,
        lead_id=lead_id,
        field_name="discount_rate",
        value=0.15,
        lamport_timestamp=2,
        actor_id="agent_pricing_tier1",
    )
    op2 = CRDTOperation(
        op_id="op_vp_002",
        tenant_id=tenant_id,
        lead_id=lead_id,
        field_name="discount_rate",
        value=0.10,
        lamport_timestamp=3,
        actor_id="human_sales_vp",
    )

    replica_a.apply_operation(op1)
    replica_a.apply_operation(op2)

    replica_b.apply_operation(op2)
    replica_b.apply_operation(op1)

    state_a = replica_a.get_state()
    state_b = replica_b.get_state()
    assert state_a["discount_rate"] == 0.10
    assert state_a == state_b
    assert replica_a.verify_transparency_chain() is True
    assert replica_b.verify_transparency_chain() is True

    # Tamper detection on MerkleAuditNode
    tampered_node = replica_a._audit_trail[0]
    replica_a._audit_trail[0] = MerkleAuditNode(
        op_hash="fake_hash_injected_after_fact",
        prev_root=tampered_node.prev_root,
    )
    assert replica_a.verify_transparency_chain() is False

    # Cross-tenant isolation check
    with pytest.raises(TenantSecurityError, match="Tenant mismatch"):
        replica_b.apply_operation(
            CRDTOperation(
                op_id="malicious_op_403",
                tenant_id="tenant_external_competitor",
                lead_id=lead_id,
                field_name="expected_revenue",
                value=0.0,
                lamport_timestamp=10,
                actor_id="compromised_agent",
            )
        )


DeltaCRDTJsonObject = _lock_mod.DeltaCRDTJsonObject
TransparencyMerkleLog = _lock_mod.TransparencyMerkleLog
OdooTenantSecurityContext = _lock_mod.OdooTenantSecurityContext
PubGrubQuoteConstraintEngine = _lock_mod.PubGrubQuoteConstraintEngine


def test_delta_crdt_merkle_fabric_and_pubgrub_quote_engine_e2e() -> None:
    """Verifies DeltaCRDTJsonObject convergence, TransparencyMerkleLog RFC-6962 style inclusion proofs, OdooTenantSecurityContext, and PubGrubQuoteConstraintEngine."""
    doc_sales_rep = DeltaCRDTJsonObject(replica_id="rep_human_01")
    doc_ai_agent = DeltaCRDTJsonObject(replica_id="agent_pricing_02")

    delta_init = doc_sales_rep.set_field("quote_status", "draft")
    doc_ai_agent.apply_delta(delta_init)

    delta_human = doc_sales_rep.set_field("discount_tier", "10_percent")
    delta_ai = doc_ai_agent.set_field("discount_tier", "12_percent")

    doc_sales_rep.apply_delta(delta_ai)
    doc_ai_agent.apply_delta(delta_human)

    state_rep = doc_sales_rep.read_document()
    state_ai = doc_ai_agent.read_document()
    assert state_rep == state_ai
    assert state_rep["discount_tier"] == "12_percent"
    assert doc_sales_rep.compute_state_hash() == doc_ai_agent.compute_state_hash()

    log = TransparencyMerkleLog()
    _, root_0 = log.append_decision("agent_pricing", "override_discount", {"from": 10.0, "to": 15.0})
    _, root_1 = log.append_decision("compliance_bot", "flag_compliance", {"risk_score": 0.12})
    _, root_2 = log.append_decision("human_director", "approve_quote", {"approved": True})
    assert root_0 != root_1
    assert root_1 != root_2

    target_entry = log.entries[1]
    proof_1 = log.generate_inclusion_proof(1)
    assert TransparencyMerkleLog.verify_inclusion_proof(target_entry, proof_1, root_2) is True
    tampered_entry = {**target_entry, "details": {"risk_score": 0.99}}
    assert TransparencyMerkleLog.verify_inclusion_proof(tampered_entry, proof_1, root_2) is False

    ctx_eu_rep = OdooTenantSecurityContext(
        user_id="user_eu_1", company_id=2, allowed_company_ids={2}
    )
    ctx_global_director = OdooTenantSecurityContext(
        user_id="user_dir_hq", company_id=1, allowed_company_ids={1, 2, 3}
    )
    quote_eu = {"quote_id": "SO-2026-EU-001", "company_id": 2, "total_eur": 125000.0}
    quote_apac = {"quote_id": "SO-2026-APAC-002", "company_id": 3, "total_eur": 85000.0}
    assert ctx_eu_rep.evaluate_record_rule(quote_eu) is True
    assert ctx_eu_rep.evaluate_record_rule(quote_apac) is False
    assert ctx_global_director.evaluate_record_rule(quote_eu) is True
    assert ctx_global_director.evaluate_record_rule(quote_apac) is True
    assert ctx_global_director.evaluate_record_rule({"quote_id": "ORPHAN"}) is False

    solver = PubGrubQuoteConstraintEngine()
    solver.register_incompatibility(
        sku_a="ENTERPRISE_AI_SUITE",
        sku_b="LEGACY_ONPREM_CONNECTOR",
        reason="Cloud AI Suite requires modern gRPC cloud gateway; legacy connector unsupported.",
    )
    valid, err = solver.validate_quote(
        skus=["ENTERPRISE_AI_SUITE", "CLOUD_STORAGE_10TB"],
        discount_percent=15.0,
        is_executive=False,
    )
    assert valid is True and err is None

    valid, err = solver.validate_quote(
        skus=["ENTERPRISE_AI_SUITE", "LEGACY_ONPREM_CONNECTOR"],
        discount_percent=10.0,
        is_executive=False,
    )
    assert valid is False and "Conflict between ENTERPRISE_AI_SUITE" in str(err)

    valid, err = solver.validate_quote(
        skus=["ENTERPRISE_AI_SUITE"],
        discount_percent=25.0,
        is_executive=False,
    )
    assert valid is False and "Discounts exceeding 20.0% require Executive approval" in str(err)

    valid, err = solver.validate_quote(
        skus=["ENTERPRISE_AI_SUITE"],
        discount_percent=25.0,
        is_executive=True,
    )
    assert valid is True and err is None


def test_zcese_sales_order_crdt_merkle_tree_and_uv_pubgrub_cache_e2e():
    """Verify Zero-Copy Ephemeral Shadow Environments (ZCESE) SalesOrderCRDTDocument, SalesAuditMerkleTree & UvPubGrubCacheManager."""
    import tempfile

    CRDTConvergenceError = _lock_mod.CRDTConvergenceError
    DependencyResolutionError = _lock_mod.DependencyResolutionError
    SalesAuditMerkleTree = _lock_mod.SalesAuditMerkleTree
    SalesOrderCRDTDocument = _lock_mod.SalesOrderCRDTDocument
    TenantIsolationError = _lock_mod.TenantIsolationError
    UvPubGrubCacheManager = _lock_mod.UvPubGrubCacheManager

    doc_a = SalesOrderCRDTDocument(order_id="SO-2026-001", actor_id="agent_alpha", company_id=10)
    doc_b = SalesOrderCRDTDocument(order_id="SO-2026-001", actor_id="rep_beta", company_id=10)

    doc_a.set_line_item("line_1", "Enterprise CRM Seat", quantity=10, unit_price=100.0)
    doc_a.set_discount(10.0)

    doc_b.set_line_item("line_2", "AI Analytics Addon", quantity=1, unit_price=500.0)
    doc_b.set_line_item("line_1", "Enterprise CRM Seat", quantity=12, unit_price=100.0)
    doc_b.set_discount(15.0)

    doc_a.merge(doc_b)
    doc_b.merge(doc_a)

    state_a = doc_a.export_canonical_state()
    state_b = doc_b.export_canonical_state()
    assert state_a == state_b
    assert state_a["total"] == 1445.0

    doc_foreign = SalesOrderCRDTDocument(order_id="SO-2026-001", actor_id="attacker", company_id=99)
    with pytest.raises(TenantIsolationError):
        doc_a.merge(doc_foreign)

    doc_other = SalesOrderCRDTDocument(order_id="SO-2026-999", actor_id="rep_beta", company_id=10)
    with pytest.raises(CRDTConvergenceError):
        doc_a.merge(doc_other)

    tree = SalesAuditMerkleTree()
    events = [
        {"seq": 1, "action": "lead_created", "lead_id": "L-900", "actor": "system"},
        {"seq": 2, "action": "quote_drafted", "order_id": "SO-2026-001", "total": 1000.0},
        {"seq": 3, "action": "discount_applied", "order_id": "SO-2026-001", "discount": 15.0},
        {"seq": 4, "action": "order_confirmed", "order_id": "SO-2026-001", "total": 1445.0},
        {"seq": 5, "action": "invoice_posted", "invoice_id": "INV-2026-001", "paid": True},
    ]
    for ev in events:
        tree.append_event(ev)

    root_hash = tree.get_root_hash()
    for idx, ev in enumerate(events):
        proof = tree.generate_inclusion_proof(idx)
        assert SalesAuditMerkleTree.verify_inclusion_proof(ev, proof, root_hash) is True

    tampered_event = dict(events[2])
    tampered_event["discount"] = 50.0
    proof_2 = tree.generate_inclusion_proof(2)
    assert SalesAuditMerkleTree.verify_inclusion_proof(tampered_event, proof_2, root_hash) is False

    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_mgr = UvPubGrubCacheManager(Path(tmp_dir))
        cache_mgr.register_package("sales-harness-core", 1, {"crdt-sync": {1, 2}, "merkle-audit": {1}})
        cache_mgr.register_package("sales-harness-core", 2, {"crdt-sync": {2}, "merkle-audit": {2}})
        cache_mgr.register_package("crdt-sync", 1, {"crypto-primitives": {1}})
        cache_mgr.register_package("crdt-sync", 2, {"crypto-primitives": {2}})
        cache_mgr.register_package("merkle-audit", 1, {"crypto-primitives": {1, 2}})
        cache_mgr.register_package("merkle-audit", 2, {"crypto-primitives": {1}})
        cache_mgr.register_package("crypto-primitives", 1, {})
        cache_mgr.register_package("crypto-primitives", 2, {})

        resolved = cache_mgr.resolve_dependencies({"sales-harness-core": {1, 2}})
        assert resolved["sales-harness-core"] == 1

        env_path = cache_mgr.materialize_ephemeral_env("e2e-worker-01", resolved)
        for pkg, ver in resolved.items():
            whl_file = env_path / f"{pkg}-{ver}.whl"
            assert whl_file.exists() and whl_file.stat().st_nlink >= 2

        with pytest.raises(DependencyResolutionError):
            cache_mgr.resolve_dependencies({"sales-harness-core": {2}})


def test_zk_macdf_crdt_map_merkle_deal_rule_solver_and_tenant_rules_e2e():
    """Verify Zero-Knowledge Merkle-Audit CRDT Deal Fabric (ZK-MACDF) CRDTMap, PubGrubDealRuleSolver & MultiTenantRecordRuleEngine."""
    import hashlib

    CRDTMap = _lock_mod.CRDTMap
    MerkleTransparencyLog = _lock_mod.MerkleTransparencyLog
    MultiTenantRecordRuleEngine = _lock_mod.MultiTenantRecordRuleEngine
    PubGrubDealRuleSolver = _lock_mod.PubGrubDealRuleSolver
    MemoryLimitExceededError = _lock_mod.MemoryLimitExceededError

    quote_replica_a = CRDTMap("quote_001")
    quote_replica_b = CRDTMap("quote_001")

    quote_replica_a.set_field("total_amount", 100000.0, timestamp=100, replica_id="node_us_east")
    quote_replica_a.set_field("discount_pct", 10.0, timestamp=102, replica_id="node_us_east")

    quote_replica_b.set_field("total_amount", 98000.0, timestamp=105, replica_id="node_eu_west")
    quote_replica_b.set_field("discount_pct", 15.0, timestamp=101, replica_id="node_eu_west")

    merged_ab = quote_replica_a.merge(quote_replica_b)
    merged_ba = quote_replica_b.merge(quote_replica_a)

    assert merged_ab.get_field("total_amount") == 98000.0
    assert merged_ba.get_field("total_amount") == 98000.0
    assert merged_ab.get_field("discount_pct") == 10.0
    assert merged_ba.get_field("discount_pct") == 10.0

    hash_ab = merged_ab.compute_state_hash()
    hash_ba = merged_ba.compute_state_hash()
    assert hash_ab == hash_ba and len(hash_ab) == 64

    log = MerkleTransparencyLog()
    state_hashes = [
        hashlib.sha256(f"state_event_{i}".encode("utf-8")).hexdigest() for i in range(5)
    ]
    for sh in state_hashes:
        log.append_event(sh)

    root = log.get_root()
    assert len(root) == 64

    target_idx = 2
    target_leaf_hash = hashlib.sha256(state_hashes[target_idx].encode("utf-8")).hexdigest()
    proof = log.get_inclusion_proof(target_idx)
    assert MerkleTransparencyLog.verify_inclusion(target_leaf_hash, proof, root) is True

    tampered_leaf_hash = hashlib.sha256(b"tampered_state").hexdigest()
    assert MerkleTransparencyLog.verify_inclusion(tampered_leaf_hash, proof, root) is False

    engine = MultiTenantRecordRuleEngine()
    engine.register_company(2, parent_id=1)
    engine.register_company(3, parent_id=1)
    engine.register_company(4, parent_id=None)

    engine.add_record("deal_101", company_id=2, data={"amount": 50000})
    engine.add_record("deal_102", company_id=3, data={"amount": 75000})
    engine.add_record("deal_103", company_id=4, data={"amount": 120000})

    holding_view = engine.filter_records(allowed_company_ids=[1])
    assert {r["id"] for r in holding_view} == {"deal_101", "deal_102"}

    sub_b_view = engine.filter_records(allowed_company_ids=[3])
    assert {r["id"] for r in sub_b_view} == {"deal_102"}

    solver = PubGrubDealRuleSolver(max_memory_slots=4)
    solver.register_incompatibility(
        "promo_startup_90_off",
        "tier_enterprise_custom_sla",
        "Startup promo cannot be combined with Enterprise SLA",
    )

    valid, reason = solver.solve_feasibility(["item_base_crm", "promo_startup_90_off"])
    assert valid is True and reason is None

    invalid, conflict_reason = solver.solve_feasibility(
        ["item_base_crm", "promo_startup_90_off", "tier_enterprise_custom_sla"]
    )
    assert invalid is False and conflict_reason is not None and "Conflict between" in conflict_reason

    solver.allocate_slot("slot_1", {"data": "A"})
    solver.allocate_slot("slot_2", {"data": "B"})
    solver.allocate_slot("slot_3", {"data": "C"})
    solver.allocate_slot("slot_4", {"data": "D"})

    with pytest.raises(MemoryLimitExceededError):
        solver.allocate_slot("slot_5_overflow", {"data": "E"})

    solver.release_slot("slot_1")
    solver.allocate_slot("slot_5_recovered", {"data": "E"})
    assert "slot_5_recovered" in solver.active_slots


def test_sales_quote_crdt_transparency_tree_and_pubgrub_cpq_validator_e2e():
    """Verify Deal-Desk CRDT Mesh (DealDeskSalesQuoteCRDT, TransparencyTreeVerifier & PubGrubCPQValidator)."""
    SalesQuoteCRDT = _lock_mod.DealDeskSalesQuoteCRDT
    TransparencyTreeVerifier = _lock_mod.TransparencyTreeVerifier
    PubGrubCPQValidator = _lock_mod.PubGrubCPQValidator

    replica_a = SalesQuoteCRDT(quote_id="Q-2026-001")
    replica_b = SalesQuoteCRDT(quote_id="Q-2026-001")

    replica_a.update_field("discount_pct", 15.0, timestamp=101, actor_id="sales_rep_1")
    replica_b.update_field("discount_pct", 18.0, timestamp=102, actor_id="deal_desk_lead")

    replica_a.update_item("SKU-AI-SEAT", "quantity", 50, timestamp=200, actor_id="sales_rep_1")
    replica_a.update_item("SKU-AI-SEAT", "unit_price", 120.0, timestamp=200, actor_id="sales_rep_1")

    replica_b.update_item("SKU-AI-SEAT", "unit_price", 110.0, timestamp=205, actor_id="deal_desk_lead")
    replica_b.update_item("SKU-ANALYTICS-ADDON", "quantity", 1, timestamp=202, actor_id="deal_desk_lead")

    merged_a = replica_a.merge_remote(replica_b)
    merged_b = replica_b.merge_remote(replica_a)

    state_a = merged_a.to_canonical_dict()
    state_b = merged_b.to_canonical_dict()

    assert state_a == state_b
    assert state_a["fields"]["discount_pct"] == 18.0
    assert state_a["items"]["SKU-AI-SEAT"]["quantity"] == 50
    assert state_a["items"]["SKU-AI-SEAT"]["unit_price"] == 110.0
    assert state_a["items"]["SKU-ANALYTICS-ADDON"]["quantity"] == 1

    verifier = TransparencyTreeVerifier()
    events = [
        {"deal_id": "DEAL-091", "action": "quote_created", "val": 100000},
        {"deal_id": "DEAL-091", "action": "discount_requested", "val": 15},
        {"deal_id": "DEAL-091", "action": "vp_approval", "actor": "vp_sales_01"},
    ]
    root_original = verifier.build_audit_root(events)
    assert len(root_original) == 64

    tampered_events = [
        {"deal_id": "DEAL-091", "action": "quote_created", "val": 100000},
        {"deal_id": "DEAL-091", "action": "discount_requested", "val": 35},
        {"deal_id": "DEAL-091", "action": "vp_approval", "actor": "vp_sales_01"},
    ]
    root_tampered = verifier.build_audit_root(tampered_events)
    assert root_original != root_tampered

    solver = PubGrubCPQValidator()
    solver.add_dependency("SKU-ENTERPRISE-CLOUD", "SKU-CORE-DB")
    solver.add_incompatibility("SKU-ENTERPRISE-CLOUD", "SKU-LEGACY-ONPREM")

    valid, errors = solver.validate_cart({"SKU-ENTERPRISE-CLOUD"})
    assert not valid and any("requires missing dependency" in err for err in errors)

    valid, errors = solver.validate_cart(
        {"SKU-ENTERPRISE-CLOUD", "SKU-CORE-DB", "SKU-LEGACY-ONPREM"}
    )
    assert not valid and any("is incompatible with present items" in err for err in errors)

    valid, errors = solver.validate_cart({"SKU-ENTERPRISE-CLOUD", "SKU-CORE-DB"})
    assert valid and len(errors) == 0


def test_sales_quote_crdt_harness_state_trellis_e2e():
    """Verify ProVerif-Verified State-Trellis SalesQuoteCRDTHarness & JSONCRDTOperation."""
    JSONCRDTOperation = _lock_mod.JSONCRDTOperation
    SalesQuoteCRDTHarness = _lock_mod.SalesQuoteCRDTHarness

    harness = SalesQuoteCRDTHarness(quote_id="SO-2026-T13", tenant_id="TENANT-INNORIA-VN")
    assert harness.verify_invariant() is True
    assert harness.apply_odoo_odoo_pattern() is True

    op1 = JSONCRDTOperation(
        op_id="op-001",
        actor="rep_vn",
        path=["lines", "line_1"],
        op_type="set",
        value={"sku": "ERP-GROWTH", "qty": 1, "discount": 5.0},
    )
    op2 = JSONCRDTOperation(
        op_id="op-002",
        actor="deal_desk",
        path=["lines", "line_2"],
        op_type="set",
        value={"sku": "AI-PILOT", "qty": 1, "discount": 10.0},
    )
    op3 = JSONCRDTOperation(
        op_id="op-003",
        actor="deal_desk",
        path=["status"],
        op_type="set",
        value="approved",
    )

    h1 = harness.apply_operation(op1)
    h2 = harness.apply_operation(op2)
    h3 = harness.apply_operation(op3)

    assert len(h1) == 64 and h1 != h2 and h2 != h3
    assert harness.verify_invariant() is True
    assert harness.apply_odoo_odoo_pattern() is True
    assert harness.apply_astral_sh_uv_pattern() is True

    # Duplicate SKU violates astral_sh_uv uniqueness pattern
    op_dup = JSONCRDTOperation(
        op_id="op-004",
        actor="rep_vn",
        path=["lines", "line_3"],
        op_type="set",
        value={"sku": "ERP-GROWTH", "qty": 2},
    )
    harness.apply_operation(op_dup)
    assert harness.apply_astral_sh_uv_pattern() is False

    # Delete duplicate line restores validity
    op_del = JSONCRDTOperation(
        op_id="op-005",
        actor="rep_vn",
        path=["lines", "line_3"],
        op_type="delete",
        value=None,
    )
    harness.apply_operation(op_del)
    assert harness.apply_astral_sh_uv_pattern() is True
    assert harness.verify_invariant() is True

    # Tamper Merkle history -> fails invariant
    harness.merkle_history[2] = "0" * 64
    assert harness.verify_invariant() is False
