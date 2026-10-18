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


