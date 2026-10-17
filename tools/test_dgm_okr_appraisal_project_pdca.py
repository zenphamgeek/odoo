#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Verification Suite for SOP-DGM-11:
PDCA Project Templates, 360-Degree HR Appraisals & Software Enterprise OKR Cascade
(`dgm.okr.objective`, `dgm.okr.key.result`, `dgm.hr.appraisal.sheet`, `dgm.project.pdca.template`)
across `insilos20_dev` and `innoria_prod`.
"""
import base64
import os
import site
import sys
import types

PYENV_PYTHON = "/home/zen/.pyenv/versions/3.12.13/bin/python3"
if os.path.exists(PYENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(PYENV_PYTHON):
    os.execv(PYENV_PYTHON, [PYENV_PYTHON] + sys.argv)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_SITE = os.path.join(ROOT_DIR, ".venv/lib/python3.12/site-packages")
if os.path.isdir(VENV_SITE):
    site.addsitedir(VENV_SITE)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    import xmlsec  # noqa: F401
except Exception:
    sys.modules["xmlsec"] = types.ModuleType("xmlsec")

try:
    from insilos_adapter.hook import install as install_insilos_hook
    install_insilos_hook()
except Exception:
    pass

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

_local_conf = os.path.join(ROOT_DIR, "odoo.conf")
if os.path.isdir("/var/lib/insilos/filestore"):
    _extra = [p for p in ("/var/lib/insilos/filestore/custom_addons", f"{ROOT_DIR}/odoo/addons", f"{ROOT_DIR}/addons", f"{ROOT_DIR}/enterprise", f"{ROOT_DIR}/apps") if os.path.isdir(p)]
    odoo.tools.config.parse_config([
        f"--addons-path={','.join(_extra)}",
        "--data-dir=/var/lib/insilos/filestore",
    ])
elif os.path.isfile("/etc/insilos/insilos.conf"):
    odoo.tools.config.parse_config(["-c", "/etc/insilos/insilos.conf"])
elif os.path.isfile(_local_conf):
    odoo.tools.config.parse_config(["-c", _local_conf])
else:
    odoo.tools.config.parse_config([])
if os.environ.get("DB_HOST"):
    odoo.tools.config["db_host"] = os.environ["DB_HOST"]
if os.environ.get("DB_PORT"):
    odoo.tools.config["db_port"] = int(os.environ["DB_PORT"])
if os.environ.get("DB_USER"):
    odoo.tools.config["db_user"] = os.environ["DB_USER"]
if os.environ.get("PGPASSWORD"):
    odoo.tools.config["db_password"] = os.environ["PGPASSWORD"]

EXPECTED_TEMPLATE_CODES = [
    "PRJ-TPL-PDCA-01",
    "PRJ-TPL-PDCA-02",
    "PRJ-TPL-PDCA-03",
    "PRJ-TPL-PDCA-04",
]

EXPECTED_DOC_FILENAMES = [
    "TPL-PRJ-05_Mau_Ke_Hoach_Du_An_Phan_Mem_PDCA_SAP_Activate.html",
    "TPL-PRJ-06_Bien_Ban_Nghiem_Thu_Sprint_UAT_Va_Go_Live_PDCA.html",
    "TPL-HR-07_Phieu_Danh_Gia_Nhan_Su_360_HR_Appraisal_9Box_PDCA.html",
    "TPL-HR-08_Bien_Ban_Hieu_Chuan_Nang_Luc_Career_Calibration_SWE.html",
    "TPL-OKR-01_Khung_OKRs_Doanh_Nghiep_Phan_Mem_Digimate_Innoria_2026.html",
    "SOP-DGM-11_Quy_Trinh_PDCA_Quan_Tri_Du_An_HR_Appraisals_Va_OKRs_Phan_Mem.html",
]


def verify_database(dbname):
    print(f"\n=== Verifying SOP-DGM-11 PDCA Project Templates, 360° Appraisals & OKRs in `{dbname}` ===")
    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        PdcaTpl = env["dgm.project.pdca.template"].sudo()
        OkrObj = env["dgm.okr.objective"].sudo()
        OkrKr = env["dgm.okr.key.result"].sudo()
        Appraisal = env["dgm.hr.appraisal.sheet"].sudo()
        SkillGate = env["dgm.hr.employee.skill.gate"].sudo()
        Document = env["documents.document"].sudo()

        # 1. Verify 4 Project PDCA Templates
        for code in EXPECTED_TEMPLATE_CODES:
            tpl = PdcaTpl.search([("code", "=", code), ("active", "=", True)], limit=1)
            assert tpl, f"[{dbname}] Missing Project PDCA Template `{code}`"
            assert tpl.linked_project_id, f"[{dbname}] Template `{code}` missing linked_project_id"
            assert len(tpl.linked_project_id.type_ids) >= 5, (
                f"[{dbname}] Linked project for `{code}` must have >= 5 PDCA/Activate stages"
            )
            assert tpl.plan_phase_gate and tpl.do_phase_gate and tpl.check_phase_gate and tpl.act_phase_gate
        print(f"  [PASS] 4/4 Project PDCA Templates (`PRJ-TPL-PDCA-01..04`) & 5-Stage Projects verified.")

        # 2. Verify 12 OKR Objectives & 24 Key Results
        objs = OkrObj.search([("period_code", "=", "2026-Q4"), ("active", "=", True)])
        assert len(objs) >= 12, f"[{dbname}] Expected >= 12 OKR Objectives, found {len(objs)}"
        company_objs = [o for o in objs if o.okr_tier == "company"]
        assert len(company_objs) >= 3, f"[{dbname}] Expected >= 3 Company OKRs, found {len(company_objs)}"
        for o in objs:
            assert 0.0 <= o.okr_score <= 1.0, f"[{dbname}] Invalid okr_score on `{o.code}`: {o.okr_score}"
            assert o.confidence_level in ("on_track", "at_risk", "off_track")

        krs = OkrKr.search([("objective_id.period_code", "=", "2026-Q4")])
        assert len(krs) >= 24, f"[{dbname}] Expected >= 24 Key Results, found {len(krs)}"
        for kr in krs:
            assert 0.0 <= kr.progress_pct <= 100.0
            assert 0.0 <= kr.kr_score <= 1.0
        print(f"  [PASS] {len(objs)} OKR Objectives & {len(krs)} Key Results verified.")

        # 3. Verify 9 360-Degree HR Appraisal Sheets (APR-2026-Q4-DGM001..009)
        appraisals = Appraisal.search([("period_code", "=", "2026-Q4"), ("active", "=", True)])
        assert len(appraisals) >= 9, f"[{dbname}] Expected >= 9 Appraisal Sheets, found {len(appraisals)}"
        ap_by_code = {a.code: a for a in appraisals}
        for idx in range(1, 10):
            ap_code = f"APR-2026-Q4-DGM00{idx}"
            assert ap_code in ap_by_code, f"[{dbname}] Missing Appraisal Sheet `{ap_code}`"
            ap = ap_by_code[ap_code]
            assert ap.okr_objective_ids, f"[{dbname}] `{ap_code}` has no linked OKRs"
            if idx in (7, 8):
                assert not ap.skill_gate_passed, f"[{dbname}] `{ap_code}` should have skill_gate_passed=False initially"
                assert ap.calibration_box == "box_6_emerging", (
                    f"[{dbname}] `{ap_code}` expected box_6_emerging while skill gate incomplete, got {ap.calibration_box}"
                )
                assert ap.calibrated_total_score <= 84.90, (
                    f"[{dbname}] `{ap_code}` expected calibrated_total_score <= 84.90, got {ap.calibrated_total_score}"
                )
            else:
                assert ap.skill_gate_passed, f"[{dbname}] `{ap_code}` should have skill_gate_passed=True"
                assert ap.calibration_box in ("box_9_star", "box_8_high_perf"), (
                    f"[{dbname}] `{ap_code}` expected box_9_star/box_8_high_perf, got {ap.calibration_box}"
                )
        print("  [PASS] 9/9 360° HR Appraisal Sheets & 9-Box Skill Gate Cap verified.")

        # 4. Verify 6 Branded HTML Document Templates, SOP-DGM-11 Knowledge Article, Zero Empty Folders & RBAC
        for fname in EXPECTED_DOC_FILENAMES:
            docs = Document.search([("name", "=", fname), ("active", "=", True)])
            assert docs, f"[{dbname}] Missing document `{fname}` in documents.document"
            for doc in docs:
                assert not doc.owner_id, f"[{dbname}] `{fname}` must have owner_id=False"
                assert doc.access_internal in ("edit", "view"), f"[{dbname}] `{fname}` invalid access_internal"
                assert doc.dgm_rbac_profile, f"[{dbname}] `{fname}` missing dgm_rbac_profile"
                assert doc.attachment_id and doc.attachment_id.raw, f"[{dbname}] `{fname}` missing attachment raw payload"
                raw_html = doc.attachment_id.raw.decode("utf-8", errors="replace")
                assert 'data-dgm-footer="drive-logo-v1"' in raw_html, (
                    f"[{dbname}] `{fname}` missing Drive Logo Brand Footer"
                )
                assert 'data-logo-source="google-drive-logo-folder"' in raw_html, (
                    f"[{dbname}] `{fname}` missing google-drive-logo-folder marker"
                )

        if "knowledge.article" in env:
            kb_11 = env["knowledge.article"].sudo().search([("name", "ilike", "SOP-DGM-11%"), ("active", "=", True)], limit=1)
            assert kb_11, f"[{dbname}] Missing SOP-DGM-11 Knowledge Article"
            assert 'data-dgm-footer="drive-logo-v1"' in (kb_11.body or ""), (
                f"[{dbname}] SOP-DGM-11 Knowledge Article missing Drive Logo Brand Footer"
            )

        cr.execute(
            """
            SELECT COUNT(*)
              FROM documents_document f
             WHERE f.type = 'folder' AND f.active = TRUE
               AND NOT EXISTS (
                   SELECT 1 FROM documents_document c
                    WHERE c.folder_id = f.id AND c.active = TRUE
               );
            """
        )
        empty_folder_count = cr.fetchone()[0]
        assert empty_folder_count == 0, f"[{dbname}] Found {empty_folder_count} empty active folders!"

        cr.execute(
            """
            SELECT COUNT(*)
              FROM documents_document
             WHERE active = TRUE
               AND (dgm_rbac_profile IS NULL OR dgm_rbac_profile = '' OR dgm_rbac_generation_id IS NULL);
            """
        )
        unmapped_rbac = cr.fetchone()[0]
        assert unmapped_rbac == 0, f"[{dbname}] Found {unmapped_rbac} unmapped RBAC records!"
        print("  [PASS] 6/6 Branded HTML Templates, SOP-DGM-11 Knowledge Article, 0 Empty Folders & 0 Unmapped RBAC verified.")

        # 5. Behavioral Test inside Savepoint: KR Check-in & Mandatory Skill Gate 9-Box Promotion
        with cr.savepoint() as sp:
            ap_007 = ap_by_code["APR-2026-Q4-DGM007"]
            kr_20 = OkrKr.search([("code", "=", "KR-2026-Q4-20")], limit=1)
            assert kr_20, f"[{dbname}] Missing KR-2026-Q4-20"

            # Check-in KR-2026-Q4-20 to 24.0 / 24.0 hours (100%)
            kr_20.action_update_kr_checkin(new_value=24.0, evidence_ref="LAB-OWL3-DONE-007", pdca_stage="act")
            assert kr_20.progress_pct == 100.0
            assert kr_20.kr_score == 1.0
            assert kr_20.objective_id.okr_score == 1.0
            assert kr_20.objective_id.pdca_stage == "act"

            # Even with 100% OKR score, while SKL-ERP-OWL3 skill gate is not yet 'certified',
            # DGM-007 must still be capped at box_6_emerging and <= 84.90!
            ap_007._compute_appraisal_calibration()
            assert not ap_007.skill_gate_passed
            assert ap_007.calibration_box == "box_6_emerging"
            assert ap_007.calibrated_total_score == 84.90

            # Now certify DGM-007's remaining mandatory skill gate (SKL-ERP-OWL3)
            wip_gates = SkillGate.search([
                ("employee_id", "=", ap_007.employee_id.id),
                ("state", "!=", "certified"),
            ])
            assert wip_gates, f"[{dbname}] Expected in-progress skill gate for DGM-007"
            wip_gates.action_certify_skill_upgrade(score=96.0, evidence_ref="CERT-OWL3-2026-007")

            ap_007.invalidate_recordset()
            ap_007._compute_appraisal_calibration()
            assert ap_007.skill_gate_passed, f"[{dbname}] Expected skill_gate_passed=True after certification"
            assert ap_007.calibrated_total_score > 92.0, (
                f"[{dbname}] Expected calibrated_total_score > 92.0 after gate pass, got {ap_007.calibrated_total_score}"
            )
            assert ap_007.calibration_box == "box_9_star", (
                f"[{dbname}] Expected promotion to box_9_star after gate pass, got {ap_007.calibration_box}"
            )
            sp.close(rollback=True)
        cr.rollback()
        print("  [PASS] Savepoint Behavioral Test (KR Check-in Cascade & 9-Box Skill Gate Promotion) verified.")


def main():
    md_path = os.path.join(
        ROOT_DIR,
        "docs/organization_and_processes/11_PDCA_PROJECT_TEMPLATES_HR_APPRAISALS_AND_SOFTWARE_OKR_SOP.md",
    )
    assert os.path.isfile(md_path) and os.path.getsize(md_path) > 1000, f"Missing or empty {md_path}"

    db_list = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev", "innoria_prod"]
    for dbname in db_list:
        verify_database(dbname)
    print("\n=== ALL SOP-DGM-11 PDCA PROJECT, 360° APPRAISAL & OKR TESTS PASSED (EXIT 0) ===")


if __name__ == "__main__":
    main()
