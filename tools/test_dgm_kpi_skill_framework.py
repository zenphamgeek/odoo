#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP-DGM-10 End-to-End Verification Suite:
Employee KPI Evaluation, Work Performance Appraisal & Mandatory Software Engineer Skill Upgrade Gate
====================================================================================================
Verifies across both `insilos20_dev` and `innoria_prod`:
1. Canonical Master Data Verification:
   - All 8 canonical `dgm.hr.skill.track` records exist and are active (`SKL-ERP-OWL3`, `SKL-ERP-SCSS-DARK`,
     `SKL-AI-MOJO`, `SKL-AI-RAG`, `SKL-K8S-PG`, `SKL-SEC-ISO27001`, `SKL-B2B-ACTIVATE`, `SKL-QA-PLAYWRIGHT`).
   - All 9 Digimate employees (`DGM-001`..`DGM-009`) have:
     * >= 1 active `dgm.hr.kpi.evaluation` record for `2026-Q4` with valid `weighted_kpi_score` (`0 < score <= 100`).
     * >= 1 active `dgm.hr.work.review` record linked to their evaluation.
     * >= 3 mandatory `dgm.hr.employee.skill.gate` records (`is_mandatory_for_next_level = True`).
   - `SOP-DGM-10_KPI_Danh_Gia_Nhan_Su_Va_Khung_Nang_Luc_Ky_Su_Phan_Mem_2026.html` and
     `TPL-HR-06_Phieu_Danh_Gia_KPI_Va_Lo_Trinh_Nang_Cap_Ky_Nang_SOP_DGM_10.html` exist in `documents.document`
     (`owner_id=False`, `access_internal='edit'`, `active=True`) and contain the canonical footer
     `data-dgm-footer="drive-logo-v1"` and `data-logo-source="google-drive-logo-folder"`.
   - `knowledge.article` contains an active `SOP-DGM-10` article with `data-dgm-footer="drive-logo-v1"`.
   - `0` empty active folders in `documents.document` across both databases.
2. Mandatory Software Engineer Skill Upgrade Gate Behavioral Test (Savepoint):
   - Inside a savepoint (`with cr.savepoint():`), locate an engineer (`DGM-007` Lê Cao Bảo Phúc or `DGM-008` Đỗ Minh Quân)
     whose `delivery_score >= 92`, `quality_score >= 90`, `collaboration_score >= 90`, `sop_compliance_score >= 95`,
     and who has 1 mandatory `dgm.hr.employee.skill.gate` in `state = 'in_progress'`.
   - Assert that while the mandatory skill gate is `'in_progress'`:
     * `kpi_eval.all_mandatory_skills_completed` is `False`
     * `kpi_eval.skill_gate_capped` is `True`
     * `kpi_eval.rank_grade == 'tier_b'` (blocked from Tier S / Tier A!)
     * `kpi_eval.promotion_eligible` is `False`
     * `kpi_eval.bonus_multiplier_pct == 100.0`
   - Call `uncertified_gate.action_certify_skill_upgrade(score=94.0, evidence_ref='PR-O20-2026-88')`
     (which sets `state = 'certified'`, `assessment_score = 94.0`, and triggers KPI recomputation).
   - Assert that immediately after certifying the mandatory skill upgrade:
     * `kpi_eval.all_mandatory_skills_completed` is `True`
     * `kpi_eval.skill_gate_capped` is `False`
     * `kpi_eval.rank_grade in ('tier_s', 'tier_a')`
     * `kpi_eval.promotion_eligible` is `True`
     * `kpi_eval.bonus_multiplier_pct in (150.0, 120.0)`
"""

import site
import sys
import types

site.addsitedir("/home/zen/O20/.venv/lib/python3.12/site-packages")
sys.path.insert(0, "/home/zen/O20")

# Mock xmlsec in case native libxmlsec bindings have symbol mismatch in CLI context
mock_xmlsec = types.ModuleType("xmlsec")
mock_xmlsec.enable_debug_trace = lambda *a, **kw: None
mock_xmlsec.constants = types.SimpleNamespace()
mock_xmlsec.template = types.SimpleNamespace()
mock_xmlsec.tree = types.SimpleNamespace()
sys.modules["xmlsec"] = mock_xmlsec

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

DATABASES = ["insilos20_dev", "innoria_prod"]

EXPECTED_SKILL_TRACK_CODES = [
    "SKL-ERP-OWL3",
    "SKL-ERP-SCSS-DARK",
    "SKL-AI-MOJO",
    "SKL-AI-RAG",
    "SKL-K8S-PG",
    "SKL-SEC-ISO27001",
    "SKL-B2B-ACTIVATE",
    "SKL-QA-PLAYWRIGHT",
]

EXPECTED_EMPLOYEE_CODES = [f"DGM-00{i}" for i in range(1, 10)]

SOP_DOC_NAME = "SOP-DGM-10_KPI_Danh_Gia_Nhan_Su_Va_Khung_Nang_Luc_Ky_Su_Phan_Mem_2026.html"
TPL_DOC_NAME = "TPL-HR-06_Phieu_Danh_Gia_KPI_Va_Lo_Trinh_Nang_Cap_Ky_Nang_SOP_DGM_10.html"


def verify_database(dbname: str):
    print(f"\n======================================================================")
    print(f"🔍 [SOP-DGM-10 Verification] Auditing database: {dbname}")
    print(f"======================================================================")

    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # ------------------------------------------------------------------
        # 1. Verify all 8 canonical dgm.hr.skill.track records
        # ------------------------------------------------------------------
        SkillTrack = env["dgm.hr.skill.track"].sudo()
        tracks = SkillTrack.search([("code", "in", EXPECTED_SKILL_TRACK_CODES), ("active", "=", True)])
        found_track_codes = set(tracks.mapped("code"))
        missing_tracks = set(EXPECTED_SKILL_TRACK_CODES) - found_track_codes
        assert not missing_tracks, f"[{dbname}] Missing canonical skill tracks: {missing_tracks}"
        print(f"  [PASS] All 8 canonical dgm.hr.skill.track records exist and are active: {sorted(found_track_codes)}")

        # ------------------------------------------------------------------
        # 2. Verify all 9 Digimate employees (DGM-001..DGM-009)
        # ------------------------------------------------------------------
        Employee = env["hr.employee"].sudo()
        KpiEval = env["dgm.hr.kpi.evaluation"].sudo()
        WorkReview = env["dgm.hr.work.review"].sudo()
        SkillGate = env["dgm.hr.employee.skill.gate"].sudo()

        for emp_code in EXPECTED_EMPLOYEE_CODES:
            emp = Employee.search([("registration_number", "=", emp_code), ("active", "=", True)], limit=1)
            assert emp, f"[{dbname}] Employee {emp_code} not found!"

            evals = KpiEval.search([
                ("employee_id", "=", emp.id),
                ("period_code", "=", "2026-Q4"),
            ])
            assert len(evals) >= 1, f"[{dbname}] Employee {emp_code} missing 2026-Q4 dgm.hr.kpi.evaluation!"
            kpi_rec = evals[0]
            assert 0 < kpi_rec.final_kpi_score <= 100.0, (
                f"[{dbname}] Employee {emp_code} invalid final_kpi_score: {kpi_rec.final_kpi_score}"
            )
            assert 0 < kpi_rec.raw_weighted_score <= 100.0, (
                f"[{dbname}] Employee {emp_code} invalid raw_weighted_score: {kpi_rec.raw_weighted_score}"
            )

            reviews = WorkReview.search([
                ("evaluation_id", "=", kpi_rec.id),
            ])
            assert len(reviews) >= 1, (
                f"[{dbname}] Employee {emp_code} missing dgm.hr.work.review linked to evaluation {kpi_rec.name}!"
            )

            mandatory_gates = SkillGate.search([
                ("employee_id", "=", emp.id),
                ("is_mandatory_for_next_level", "=", True),
                ("active", "=", True),
            ])
            assert len(mandatory_gates) >= 3, (
                f"[{dbname}] Employee {emp_code} has only {len(mandatory_gates)} mandatory skill gates (expected >= 3)!"
            )

        print(f"  [PASS] All 9 Digimate employees (DGM-001..DGM-009) verified with 2026-Q4 KPI, Work Review, and >= 3 Mandatory Skill Gates")

        # ------------------------------------------------------------------
        # 3. Verify SOP-DGM-10 and TPL-HR-06 in documents.document
        # ------------------------------------------------------------------
        Doc = env["documents.document"].sudo()
        for doc_name in (SOP_DOC_NAME, TPL_DOC_NAME):
            docs = Doc.search([
                ("name", "=", doc_name),
                ("type", "!=", "folder"),
                ("active", "=", True),
            ])
            assert len(docs) >= 1, f"[{dbname}] Missing active document '{doc_name}' in documents.document!"
            for d in docs:
                assert not d.owner_id, f"[{dbname}] Document '{doc_name}' (id={d.id}) must have owner_id=False!"
                assert d.access_internal == "edit", (
                    f"[{dbname}] Document '{doc_name}' (id={d.id}) must have access_internal='edit' (got {d.access_internal})!"
                )
                assert d.attachment_id and d.attachment_id.raw, (
                    f"[{dbname}] Document '{doc_name}' (id={d.id}) has no attachment payload!"
                )
                raw_html = d.attachment_id.raw.decode("utf-8", errors="ignore")
                assert 'data-dgm-footer="drive-logo-v1"' in raw_html, (
                    f"[{dbname}] Document '{doc_name}' (id={d.id}) missing canonical data-dgm-footer='drive-logo-v1'!"
                )
                assert 'data-logo-source="google-drive-logo-folder"' in raw_html, (
                    f"[{dbname}] Document '{doc_name}' (id={d.id}) missing data-logo-source='google-drive-logo-folder'!"
                )
            print(f"  [PASS] Verified '{doc_name}' ({len(docs)} active record(s)) with canonical Drive logo & brand footer")

        # ------------------------------------------------------------------
        # 4. Verify SOP-DGM-10 Knowledge Article
        # ------------------------------------------------------------------
        if "knowledge.article" in env:
            Article = env["knowledge.article"].sudo()
            articles = Article.search([
                ("name", "ilike", "SOP-DGM-10"),
                ("active", "=", True),
            ])
            assert len(articles) >= 1, f"[{dbname}] Missing active SOP-DGM-10 knowledge.article!"
            art_body = articles[0].body or ""
            assert 'data-dgm-footer="drive-logo-v1"' in art_body, (
                f"[{dbname}] SOP-DGM-10 knowledge.article missing data-dgm-footer='drive-logo-v1'!"
            )
            print(f"  [PASS] Verified SOP-DGM-10 knowledge.article (id={articles[0].id}) with canonical footer")

        # ------------------------------------------------------------------
        # 5. Verify 0 Empty Active Folders in documents.document
        # ------------------------------------------------------------------
        cr.execute("""
            SELECT COUNT(*)
            FROM documents_document f
            WHERE f.type = 'folder'
              AND f.active = TRUE
              AND NOT EXISTS (
                  SELECT 1 FROM documents_document c
                  WHERE c.folder_id = f.id AND c.active = TRUE
              )
        """)
        empty_count = cr.fetchone()[0]
        assert empty_count == 0, f"[{dbname}] Found {empty_count} empty active folders in documents_document!"
        print(f"  [PASS] Zero empty active folders invariant verified (0 empty active folders)")

        # ------------------------------------------------------------------
        # 6. Mandatory Software Engineer Skill Upgrade Gate Behavioral Test
        # ------------------------------------------------------------------
        try:
            with cr.savepoint():
                target_emp = Employee.search([("registration_number", "=", "DGM-007"), ("active", "=", True)], limit=1)
                if not target_emp:
                    target_emp = Employee.search([("registration_number", "=", "DGM-008"), ("active", "=", True)], limit=1)
                assert target_emp, f"[{dbname}] Could not find DGM-007 or DGM-008 for Skill Gate behavioral test!"

                kpi_eval = KpiEval.search([
                    ("employee_id", "=", target_emp.id),
                    ("period_code", "=", "2026-Q4"),
                ], limit=1)
                assert kpi_eval, f"[{dbname}] Missing 2026-Q4 KPI evaluation for {target_emp.registration_number}!"

                assert kpi_eval.score_delivery >= 92.0, f"Expected score_delivery >= 92.0, got {kpi_eval.score_delivery}"
                assert kpi_eval.score_quality >= 90.0, f"Expected score_quality >= 90.0, got {kpi_eval.score_quality}"
                assert kpi_eval.score_work_eval >= 90.0, f"Expected score_work_eval >= 90.0, got {kpi_eval.score_work_eval}"
                assert kpi_eval.kpi_sop_compliance_score >= 95.0, f"Expected kpi_sop_compliance_score >= 95.0, got {kpi_eval.kpi_sop_compliance_score}"

                uncertified_gate = SkillGate.search([
                    ("employee_id", "=", target_emp.id),
                    ("is_mandatory_for_next_level", "=", True),
                    ("state", "=", "in_progress"),
                    ("active", "=", True),
                ], limit=1)
                if not uncertified_gate:
                    # In case a prior run certified the gate, reset one mandatory gate to in_progress within this savepoint
                    test_gate = SkillGate.search([
                        ("employee_id", "=", target_emp.id),
                        ("is_mandatory_for_next_level", "=", True),
                        ("active", "=", True),
                    ], order="id desc", limit=1)
                    if test_gate:
                        test_gate.write({
                            "state": "in_progress",
                            "assessment_score": 80.0,
                            "completed_hours": 18.0,
                            "certified_date": False,
                        })
                        uncertified_gate = test_gate

                assert uncertified_gate, (
                    f"[{dbname}] Expected {target_emp.registration_number} to have 1 mandatory skill gate in state='in_progress'!"
                )

                # Force recompute check before certification
                kpi_eval._compute_kpi_scores()
                assert kpi_eval.all_mandatory_skills_completed is False, (
                    f"[{dbname}] Expected all_mandatory_skills_completed == False while gate is in_progress!"
                )
                assert kpi_eval.skill_gate_capped is True, (
                    f"[{dbname}] Expected skill_gate_capped == True while mandatory skill gate is in_progress!"
                )
                assert kpi_eval.rank_grade == "tier_b", (
                    f"[{dbname}] Expected rank_grade == 'tier_b' (capped), got '{kpi_eval.rank_grade}'!"
                )
                assert kpi_eval.promotion_eligible is False, (
                    f"[{dbname}] Expected promotion_eligible == False while mandatory skill gate is in_progress!"
                )
                assert kpi_eval.bonus_multiplier_pct == 100.0, (
                    f"[{dbname}] Expected bonus_multiplier_pct == 100.0 while capped, got {kpi_eval.bonus_multiplier_pct}!"
                )
                print(
                    f"  [PASS] Pre-certification Skill Gate cap verified for {target_emp.registration_number}: "
                    f"raw={kpi_eval.raw_weighted_score:.2f}, final={kpi_eval.final_kpi_score:.2f}, "
                    f"skill_gate_capped={kpi_eval.skill_gate_capped}, rank_grade={kpi_eval.rank_grade}, "
                    f"promotion_eligible={kpi_eval.promotion_eligible}"
                )

                # Now certify the mandatory skill upgrade!
                uncertified_gate.action_certify_skill_upgrade(score=94.0, evidence_ref="PR-O20-2026-88")
                assert uncertified_gate.state == "certified", (
                    f"[{dbname}] Expected gate state == 'certified' after action_certify_skill_upgrade, got {uncertified_gate.state}!"
                )
                assert uncertified_gate.assessment_score == 94.0, (
                    f"[{dbname}] Expected gate assessment_score == 94.0, got {uncertified_gate.assessment_score}!"
                )

                kpi_eval.invalidate_recordset()
                kpi_eval._compute_kpi_scores()

                assert kpi_eval.all_mandatory_skills_completed is True, (
                    f"[{dbname}] Expected all_mandatory_skills_completed == True after certifying gate!"
                )
                assert kpi_eval.skill_gate_capped is False, (
                    f"[{dbname}] Expected skill_gate_capped == False after certifying gate!"
                )
                assert kpi_eval.rank_grade in ("tier_s", "tier_a"), (
                    f"[{dbname}] Expected rank_grade in ('tier_s', 'tier_a') after certifying gate, got '{kpi_eval.rank_grade}'!"
                )
                assert kpi_eval.promotion_eligible is True, (
                    f"[{dbname}] Expected promotion_eligible == True after certifying gate!"
                )
                assert kpi_eval.bonus_multiplier_pct in (150.0, 120.0), (
                    f"[{dbname}] Expected bonus_multiplier_pct in (150.0, 120.0), got {kpi_eval.bonus_multiplier_pct}!"
                )
                print(
                    f"  [PASS] Post-certification Skill Gate unlock verified for {target_emp.registration_number}: "
                    f"raw={kpi_eval.raw_weighted_score:.2f}, final={kpi_eval.final_kpi_score:.2f}, "
                    f"skill_gate_capped={kpi_eval.skill_gate_capped}, rank_grade={kpi_eval.rank_grade}, "
                    f"promotion_eligible={kpi_eval.promotion_eligible}, bonus_multiplier_pct={kpi_eval.bonus_multiplier_pct}%"
                )
                # Roll back savepoint cleanly to preserve pristine database state for idempotent repeat tests
                raise RuntimeError("_ROLLBACK_TEST_SAVEPOINT_")
        except RuntimeError as exc:
            if str(exc) != "_ROLLBACK_TEST_SAVEPOINT_":
                raise


def main():
    odoo.tools.config.parse_config(["-c", "/home/zen/O20/odoo.conf"])
    for db in DATABASES:
        verify_database(db)
    print("\n✅ ALL SOP-DGM-10 KPI & SOFTWARE ENGINEER SKILL UPGRADE GATE CHECKS PASSED ACROSS ALL DATABASES!")


if __name__ == "__main__":
    main()
