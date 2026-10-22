#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Verification Suite for DGM HR, Payroll, Contracts (`hr.version`),
Payslips (`hr.payslip`), Employee Self-Service Dashboard (`o_insilos_emp_dashboard`),
Onboarding (`SOP-DGM-04`), Leaving/Offboarding (`SOP-DGM-03/04`), and
VCB DigiBiz 11-Column Excel Export (`VCB_DigiBiz_Luong_DGM_Thang_10_2026.xlsx`).
"""
import configparser
import io
import json
import os
import subprocess
import sys
import zipfile
import psycopg2

ROOT_DIR = "/home/zen/O20"
sys.path.insert(0, os.path.join(ROOT_DIR, "enterprise/web_enterprise/controllers"))


def get_local_conn(dbname):
    cfg = configparser.ConfigParser()
    cfg.read("/home/zen/O20/odoo.conf")
    return psycopg2.connect(
        dbname=dbname,
        user=cfg["options"].get("db_user", "odoo"),
        password=cfg["options"].get("db_password", "odoo"),
        host=cfg["options"].get("db_host", "127.0.0.1"),
        port=int(cfg["options"].get("db_port", "5434")),
    )


def verify_db_state(dbname):
    conn = get_local_conn(dbname)
    cur = conn.cursor()

    # 1. Verify exactly 19 active DGM employees (DGM-001..DGM-019)
    cur.execute(
        """
        SELECT e.id, e.registration_number, e.name, e.user_id, v.wage, v.job_title
          FROM hr_employee e
          JOIN hr_version v ON v.id = e.current_version_id
         WHERE e.active = TRUE
         ORDER BY e.registration_number;
        """
    )
    emps = cur.fetchall()
    assert len(emps) == 19, f"{dbname}: Expected 19 active employees, got {len(emps)}"
    regs = [r[1] for r in emps]
    assert regs == [f"DGM-{i:03d}" for i in range(1, 20)], f"{dbname}: Unexpected regs {regs}"
    assert emps[0][3] == 2, f"{dbname}: Expected DGM-001 linked to admin user_id=2, got {emps[0][3]}"
    assert int(emps[0][4]) == 22556800, f"{dbname}: Expected DGM-001 wage 22,556,800, got {emps[0][4]}"
    assert emps[8][1] == "DGM-009" and emps[8][2] == "Trần Văn Huỳnh Phố" and int(emps[8][4]) == 9027000
    assert emps[9][1] == "DGM-010" and emps[9][2] == "Phạm Vũ Thắng" and int(emps[9][4]) == 31770000

    # 2. Verify 4 active departments
    cur.execute("SELECT COUNT(*) FROM hr_department WHERE active = TRUE;")
    dept_cnt = cur.fetchone()[0]
    assert dept_cnt == 4, f"{dbname}: Expected 4 active departments, got {dept_cnt}"

    # 3. Verify 0111000287863 leading zero preserved on Mai Thị Hồng Thắm's bank account
    cur.execute(
        """
        SELECT b.account_number, b.bank_name
          FROM res_partner_bank b
          JOIN hr_employee e ON e.work_contact_id = b.partner_id
         WHERE e.registration_number = 'DGM-003'
         LIMIT 1;
        """
    )
    b_row = cur.fetchone()
    assert b_row and b_row[0] == "0111000287863", f"{dbname}: Leading zero lost on DGM-003 bank account: {b_row}"

    # 4. Verify payslips & payslip runs
    cur.execute("SELECT COUNT(*) FROM hr_payslip_run WHERE active = TRUE;")
    runs_cnt = cur.fetchone()[0]
    assert runs_cnt >= 2, f"{dbname}: Expected >= 2 payslip runs, got {runs_cnt}"

    cur.execute("SELECT COUNT(*) FROM hr_payslip;")
    slips_cnt = cur.fetchone()[0]
    assert slips_cnt >= 19, f"{dbname}: Expected >= 19 payslips, got {slips_cnt}"

    # 5. Verify ir_config_parameter master registry & lifecycle
    cur.execute("SELECT value FROM ir_config_parameter WHERE key = 'dgm.hr.master_registry';")
    reg_row = cur.fetchone()
    assert reg_row, f"{dbname}: Missing dgm.hr.master_registry"
    reg_data = json.loads(reg_row[0])
    assert len(reg_data["employees"]) == 19
    assert sum(e["gross_wage"] for e in reg_data["employees"]) == 332451400
    assert reg_data["total_vcb_dgm"] == 287944000
    assert reg_data["total_acb_inno"] == 30150000

    conn.close()
    print(f"[✓] {dbname}: 19 DGM employees (DGM-001..DGM-019), 4 departments, 19 contracts, {slips_cnt} payslips, and VCB bank accounts verified")


def _setup_controller_module():
    import types

    insilos_mod = types.ModuleType("insilos")
    http_mod = types.ModuleType("insilos.http")

    class _DummyController:
        pass

    def _route(*args, **kwargs):
        def _dec(fn):
            return fn

        return _dec

    http_mod.Controller = _DummyController
    http_mod.route = _route
    http_mod.request = types.SimpleNamespace(env=None)
    insilos_mod.http = http_mod
    sys.modules["insilos"] = insilos_mod
    sys.modules["insilos.http"] = http_mod
    sys.modules["odoo"] = insilos_mod
    sys.modules["odoo.http"] = http_mod

    import employee_dashboard as ed

    return ed, http_mod


def verify_vcb_xlsx_generator():
    ed, _ = _setup_controller_module()

    headers = [
        "STT",
        "Số tài khoản thụ hưởng",
        "Số tiền chuyển khoản (VND)",
        "Loại tiền",
        "Tên người thụ hưởng",
        "Địa chỉ người thụ hưởng",
        "Ngân hàng thụ hưởng",
        "Mã ngân hàng (CITAD/BIC)",
        "Chi nhánh ngân hàng",
        "Nội dung thanh toán",
        "Phí chuyển khoản (OUR/BEN)",
    ]
    rows = []
    for idx, emp in enumerate(ed.CANONICAL_DGM_EMPLOYEES, start=1):
        calc = ed._compute_vn_payroll(emp["gross_wage"])
        rows.append(
            [
                str(idx),
                str(emp["bank_acc_number"]),
                int(calc["net_wage"]),
                "VND",
                emp["name"],
                "TP. Hồ Chí Minh, Việt Nam",
                emp["bank_name"],
                emp["bank_bic"],
                emp["bank_branch"],
                f"DIGIMATE THANH TOAN LUONG T10 2026 {emp['reg']} {emp['name']}",
                "OUR",
            ]
        )

    xlsx_bytes = ed._build_minimal_xlsx(headers, rows)
    assert len(xlsx_bytes) > 500, "Generated XLSX is unexpectedly small"
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as zf:
        names = zf.namelist()
        assert "xl/worksheets/sheet1.xml" in names
        sheet_xml = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
        # In xlsxwriter, strings may be in sharedStrings.xml or sheet1.xml
        all_xml = sheet_xml
        if "xl/sharedStrings.xml" in names:
            all_xml += zf.read("xl/sharedStrings.xml").decode("utf-8")
        assert "0111000287863" in all_xml, "Leading zero 0111000287863 missing in XLSX XML!"
        assert "Lê Xuân Hoàng" in all_xml
        assert "Thái Nguyễn Đăng Khoa" in all_xml
    print("[✓] VCB DigiBiz 11-Column Excel (.xlsx) generator verified (0111000287863 leading zero preserved)")


def verify_iso27701_privacy_and_maker_checker_workflow():
    import types

    ed, http_mod = _setup_controller_module()

    # 1. Verify Deterministic Partial Masking Helpers (ISO/IEC 27701 A.8.11)
    assert ed._mask_cccd("089094016917") == "089******917", ed._mask_cccd("089094016917")
    assert ed._mask_cccd("094094005852") == "094******852", ed._mask_cccd("094094005852")
    assert ed._mask_cccd("365931521") == "365***521", ed._mask_cccd("365931521")
    assert ed._mask_phone("0903881001") == "090*****01", ed._mask_phone("0903881001")
    assert ed._mask_bank_acc("1373068161") == "13****8161", ed._mask_bank_acc("1373068161")
    assert ed._mask_bank_acc("0111000287863") == "01*******7863", ed._mask_bank_acc("0111000287863")
    assert ed._mask_bank_acc("12154887") == "12**4887", ed._mask_bank_acc("12154887")

    # 2. Setup Mock Request Environment for Controller Functional Testing
    config_store = {}
    executed_queries = []

    class _MockIrConfig:
        def sudo(self):
            return self

        def get_param(self, key, default=None):
            return config_store.get(key, default)

        def set_param(self, key, value):
            config_store[key] = value

    class _MockHrEmployee:
        def sudo(self):
            return self

        def search(self, domain, limit=None):
            return None

        def browse(self, emp_id):
            return types.SimpleNamespace(
                id=emp_id,
                exists=lambda: True,
                user_id=types.SimpleNamespace(id=2 if emp_id == 1 else None),
                parent_id=types.SimpleNamespace(user_id=types.SimpleNamespace(id=2)),
                department_id=types.SimpleNamespace(
                    manager_id=types.SimpleNamespace(user_id=types.SimpleNamespace(id=2))
                ),
            )

    class _MockCr:
        def __init__(self, fail_on_lock=False):
            self.fail_on_lock = fail_on_lock

        def execute(self, query, params=None):
            if self.fail_on_lock and "FOR UPDATE NOWAIT" in query:
                raise RuntimeError("psycopg2.errors.LockNotAvailable: could not obtain lock on row in relation hr_employee")
            executed_queries.append((query, params))

    class _MockEnv:
        def __init__(self, uid=2, user_name="Lê Xuân Hoàng (CEO)", groups=None, fail_on_lock=False):
            self.uid = uid
            self.cr = _MockCr(fail_on_lock=fail_on_lock)
            self._groups = set(groups or [])
            self.user = types.SimpleNamespace(
                id=uid,
                name=user_name,
                has_group=lambda g: g in self._groups,
                _is_superuser=lambda: (uid in (1, 2)),
            )

        def __getitem__(self, model_name):
            if model_name == "ir.config_parameter":
                return _MockIrConfig()
            if model_name == "hr.employee":
                return _MockHrEmployee()
            raise KeyError(model_name)

    ed.request.env = _MockEnv(uid=2, user_name="Lê Xuân Hoàng (CEO)", groups={"base.group_system"})
    ctrl = ed.InsilosEmployeeDashboardController()

    # 2a. Verify default /insilos/employee_dashboard/data returns partially masked PII & Contract Lock
    dash_data = ctrl.get_employee_dashboard_data(employee_id=1)
    curr = dash_data["current_employee"]
    assert curr["is_partially_masked"] is True
    assert curr["identification_id"] == "089******917", curr["identification_id"]
    assert curr["work_phone"] == "090*****01", curr["work_phone"]
    assert curr["bank_acc_number"] == "13****8161", curr["bank_acc_number"]
    assert curr["has_active_contract"] is True
    assert curr["viewer_role"] == "HR_EXEC"
    assert curr["can_reveal_pii"] is True
    assert curr["can_approve_changes"] is True
    assert len(dash_data["change_requests"]) >= 2
    assert dash_data["pending_approval_count"] >= 1

    # Verify DGM-003 bank account is masked in payload ("01*******7863") while raw registry stays unmasked
    emp_003_masked = next(e for e in dash_data["all_employees"] if e["registration_number"] == "DGM-003")
    assert emp_003_masked["bank_acc_number"] == "01*******7863", emp_003_masked["bank_acc_number"]

    # 2b. Verify Controlled Audited 30s PII Reveal
    reveal_res = ctrl.reveal_pii(employee_id=3)
    assert reveal_res["ok"] is True
    assert reveal_res["identification_id_full"] == "093197003049"
    assert reveal_res["work_phone_full"] == "0903881003"
    assert reveal_res["bank_acc_number_full"] == "0111000287863"
    assert reveal_res["expires_in_seconds"] == 30
    assert reveal_res["privacy_audit_log"][0]["action"] == "REVEAL_PARTIAL_PII_30S"

    # 2c. Verify Role-Based Need-to-Know Scoping for LINE_MANAGER (no compensation, no PII reveal)
    ed.request.env = _MockEnv(uid=99, user_name="Line Manager", groups={"hr.group_hr_user"})
    lm_data = ctrl.get_employee_dashboard_data(employee_id=4)
    lm_emp = lm_data["current_employee"]
    assert lm_emp["viewer_role"] == "LINE_MANAGER"
    assert lm_emp["can_reveal_pii"] is False
    assert lm_emp["can_approve_changes"] is False
    assert lm_emp["can_view_compensation"] is False
    assert lm_emp["gross_wage"] == 0
    assert lm_emp["net_wage"] == 0
    assert lm_emp["gross_wage_masked"] == "**.***.000 ₫"
    lm_reveal = ctrl.reveal_pii(employee_id=4)
    assert lm_reveal["ok"] is False

    # 2d. Verify 2-Step Legal Profile Update Workflow (Maker -> Checker)
    ed.request.env = _MockEnv(uid=2, user_name="Lê Xuân Hoàng (CEO)", groups={"base.group_system"})
    step1_payload = ctrl.submit_change_request(
        employee_id=4,
        field_type="work_phone",
        new_value="0903887777",
        legal_reason="Đổi SĐT định danh VNeID Mức 2 theo Phụ lục HĐLĐ",
        evidence_doc_ref="VNeID-DGM004-TEST",
    )
    created_ticket = step1_payload["change_requests"][0]
    assert created_ticket["state"] == "pending"
    assert created_ticket["employee_code"] == "DGM-004"
    assert created_ticket["new_value"] == "0903887777"
    assert created_ticket["new_value_masked"] == "090*****77"
    assert created_ticket["requested_by_uid"] == 2
    assert step1_payload["privacy_audit_log"][0]["action"] == "STEP1_SUBMIT_CHANGE_REQUEST"

    # Ensure Step 1 did NOT mutate the underlying employee phone number yet
    pre_approve_reveal = ctrl.reveal_pii(employee_id=4)
    assert pre_approve_reveal["work_phone_full"] == "0903881004", pre_approve_reveal["work_phone_full"]

    # 2e. Verify TOCTOU Lock Contention Guard (`FOR UPDATE NOWAIT` failure)
    ed.request.env = _MockEnv(
        uid=2,
        user_name="Lê Xuân Hoàng (CEO)",
        groups={"base.group_system"},
        fail_on_lock=True,
    )
    lock_fail_res = ctrl.decide_change_request(
        request_id=created_ticket["request_id"],
        decision="approve",
        approver_note="Concurrent lock test",
        employee_id=4,
    )
    assert lock_fail_res["ok"] is False
    assert "TOCTOU lock" in lock_fail_res["error"], lock_fail_res

    # Step 2: Approve the change request as Superuser HR_EXEC (CEO override records sod_self_approved=True)
    ed.request.env = _MockEnv(uid=2, user_name="Lê Xuân Hoàng (CEO)", groups={"base.group_system"})
    executed_queries.clear()
    step2_payload = ctrl.decide_change_request(
        request_id=created_ticket["request_id"],
        decision="approve",
        approver_note="Đã đối chiếu VNeID Mức 2 & Phụ lục HĐLĐ.",
        employee_id=4,
    )
    approved_ticket = next(
        r for r in step2_payload["change_requests"] if r["request_id"] == created_ticket["request_id"]
    )
    assert approved_ticket["state"] == "approved"
    assert approved_ticket["sod_self_approved"] is True
    assert "Lê Xuân Hoàng" in approved_ticket["approved_by_name"]
    assert step2_payload["privacy_audit_log"][0]["action"] == "STEP2_APPROVE_LEGAL_CHANGE"
    assert step2_payload["privacy_audit_log"][0]["sod_self_approved"] is True
    assert step2_payload["current_employee"]["work_phone"] == "090*****77"
    assert any(
        "SELECT id FROM hr_employee WHERE id = %s FOR UPDATE NOWAIT" in q for q, _ in executed_queries
    ), f"Missing FOR UPDATE NOWAIT lock in {executed_queries}"

    # Ensure Step 2 mutated the underlying employee record
    post_approve_reveal = ctrl.reveal_pii(employee_id=4)
    assert post_approve_reveal["work_phone_full"] == "0903887777", post_approve_reveal["work_phone_full"]

    # 2f. Verify Non-Superuser HR_EXEC Segregation of Duties (SoD) Block & Dual-Control Approval
    ed.request.env = _MockEnv(
        uid=15,
        user_name="Mai Thị Hồng Thắm (HR Manager)",
        groups={"hr.group_hr_manager"},
    )
    sod_step1 = ctrl.submit_change_request(
        employee_id=3,
        field_type="work_phone",
        new_value="0903889999",
        legal_reason="Kiểm thử Phân tách Nhiệm vụ Maker-Checker (SoD)",
        evidence_doc_ref="SOD-TEST-001",
    )
    sod_ticket = sod_step1["change_requests"][0]
    assert sod_ticket["requested_by_uid"] == 15

    # Non-superuser Maker (uid=15) attempting to self-approve Step 2 MUST be blocked
    sod_self_res = ctrl.decide_change_request(
        request_id=sod_ticket["request_id"],
        decision="approve",
        approver_note="Self-approve attempt",
        employee_id=3,
    )
    assert sod_self_res["ok"] is False
    assert "Segregation of Duties (SoD) violation" in sod_self_res["error"], sod_self_res

    # Second distinct HR_EXEC Checker (uid=16) approves Step 2 -> succeeds with sod_self_approved=False
    ed.request.env = _MockEnv(
        uid=16,
        user_name="Trần Minh Quân (Checker)",
        groups={"hr.group_hr_manager"},
    )
    sod_peer_res = ctrl.decide_change_request(
        request_id=sod_ticket["request_id"],
        decision="approve",
        approver_note="Approved by distinct Checker",
        employee_id=3,
    )
    sod_approved = next(
        r for r in sod_peer_res["change_requests"] if r["request_id"] == sod_ticket["request_id"]
    )
    assert sod_approved["state"] == "approved"
    assert sod_approved["sod_self_approved"] is False
    assert sod_peer_res["privacy_audit_log"][0]["sod_self_approved"] is False

    # 2g. Verify 4-Pillar KPI Evaluation, Work Appraisal & Mandatory SWE Skill Upgrade Gate
    ed.request.env = _MockEnv(uid=2, user_name="Lê Xuân Hoàng (CEO)", groups={"base.group_system"})
    emp5_data = ctrl.get_employee_dashboard_data(employee_id=5)
    kh5 = emp5_data["kpi_skill_hub"]
    assert kh5["employee_code"] == "DGM-005"
    assert kh5["mandatory_skill_total"] == 5
    assert kh5["mandatory_skill_certified"] == 4
    assert kh5["mandatory_skill_pending"] == 1
    assert kh5["skill_gate_capped"] is True, "DGM-005 must be capped at tier_b while SKL-AI-MOJO is pending"
    assert kh5["rank_grade"] == "tier_b", f"Expected tier_b cap, got {kh5['rank_grade']}"
    assert kh5["promotion_eligible"] is False
    assert len(kh5["pillars"]) == 4

    # Verify SOP-DGM-11 OKR Hub, 360° HR Appraisal (capped at 84.90 / 9-Box [6] while skill gate pending) & Project PDCA Templates
    okr5 = emp5_data["okr_hub"]
    assert len(okr5["company_okrs"]) == 3
    assert [c["code"] for c in okr5["company_okrs"]] == [
        "OKR-2026-Q4-C01",
        "OKR-2026-Q4-C02",
        "OKR-2026-Q4-C03",
    ]
    assert len(okr5["employee_okrs"]) >= 1
    assert len(okr5["key_results"]) == 3
    assert 0.0 <= okr5["okr_score"] <= 1.0

    apr5_before = emp5_data["appraisal_hub"]
    assert apr5_before["code"] == "APR-2026-Q4-DGM005"
    assert apr5_before["period_code"] == "2026-Q4"
    assert apr5_before["skill_gate_capped"] is True
    assert apr5_before["calibrated_total_score"] == 84.90, apr5_before
    assert "9-Box [6]" in apr5_before["calibration_box"]

    pdca_tpls = emp5_data["project_pdca_templates"]
    assert len(pdca_tpls) == 4
    assert [t["code"] for t in pdca_tpls] == [
        "PRJ-TPL-PDCA-01",
        "PRJ-TPL-PDCA-02",
        "PRJ-TPL-PDCA-03",
        "PRJ-TPL-PDCA-04",
    ]
    for tpl in pdca_tpls:
        assert len(tpl["pdca_gates"]) == 4

    # Complete mandatory skill upgrade SKL-AI-MOJO for DGM-005 -> unlocks Tier S, promotion_eligible=True & 9-Box [9]
    unlocked_res = ctrl.complete_skill_upgrade(
        employee_id=5,
        skill_code="SKL-AI-MOJO",
        exam_score=96.0,
        certificate_ref="CERT-AIFLEET-DGM005-PASS",
    )
    kh5_after = unlocked_res["kpi_skill_hub"]
    assert kh5_after["mandatory_skill_pending"] == 0
    assert kh5_after["mandatory_skill_certified"] == 5
    assert kh5_after["skill_completion_pct"] == 100
    assert kh5_after["skill_gate_capped"] is False, "Skill gate cap should be lifted after 100% certification"
    assert kh5_after["rank_grade"] == "tier_s", f"Expected tier_s after skill gate unlock, got {kh5_after['rank_grade']}"
    assert kh5_after["promotion_eligible"] is True
    assert kh5_after["total_kpi_score"] >= 90.0
    assert unlocked_res["privacy_audit_log"][0]["action"] == "COMPLETE_MANDATORY_SKILL_UPGRADE"

    apr5_after = unlocked_res["appraisal_hub"]
    assert apr5_after["skill_gate_capped"] is False
    assert apr5_after["calibrated_total_score"] >= 90.0, apr5_after
    assert "9-Box [9]" in apr5_after["calibration_box"]

    # 2h. Verify Interactive OKR KR Check-in (`checkin_okr_kr`) & 360° HR Appraisal (`submit_hr_appraisal`)
    checkin_res = ctrl.checkin_okr_kr(
        employee_id=5,
        kr_code="KR-DGM-005-01",
        current_value=160.0,
        pdca_stage="act",
        evidence_ref="SLA-ONSITE-DGM005-160H-VERIFIED",
    )
    kr1_after = next(
        kr for kr in checkin_res["okr_hub"]["key_results"] if kr["code"] == "KR-DGM-005-01"
    )
    assert kr1_after["current_value"] == 160.0
    assert kr1_after["kr_score"] == 1.0
    assert kr1_after["pdca_stage"] == "act"
    assert checkin_res["privacy_audit_log"][0]["action"] == "OKR_PDCA_CHECKIN"

    # Submit Work KPI Review & 360° HR Appraisal for DGM-006 (who still has 1 pending mandatory skill SKL-K8S-PG)
    rev6_res = ctrl.submit_work_kpi_review(
        employee_id=6,
        kpi_delivery_score=95.0,
        kpi_quality_score=94.0,
        kpi_work_eval_score=95.0,
        next_training_roadmap="Hoàn tất chứng chỉ K8s & PostgreSQL HA trước 30/11/2026.",
        manager_review_note="Điểm công việc xuất sắc, chờ hoàn tất chứng chỉ K8s để mở khóa Hạng S.",
        approve_evaluation=True,
    )
    kh6 = rev6_res["kpi_skill_hub"]
    assert kh6["kpi_delivery_score"] == 95.0
    assert kh6["skill_gate_capped"] is True, "DGM-006 must remain capped at tier_b until SKL-K8S-PG is certified"
    assert kh6["rank_grade"] == "tier_b"
    assert rev6_res["privacy_audit_log"][0]["action"] == "SUBMIT_WORK_KPI_EVALUATION"

    apr6_res = ctrl.submit_hr_appraisal(
        employee_id=6,
        self_assessment_score=95.0,
        peer_client_360_score=96.0,
        manager_technical_score=95.0,
        pdca_next_quarter_plan="Plan: Ôn tập K8s HA → Do: Lab Patroni → Check: Thi CERT-K8SPG-2026 → Act: Mở khóa 9-Box [9].",
        sign_off=True,
    )
    apr6 = apr6_res["appraisal_hub"]
    assert apr6["code"] == "APR-2026-Q4-DGM006"
    assert apr6["skill_gate_capped"] is True
    assert apr6["calibrated_total_score"] == 84.90
    assert apr6["calibration_box_code"] == "box_6_emerging"
    assert "9-Box [6]" in apr6["calibration_box"]
    assert apr6_res["privacy_audit_log"][0]["action"] == "SUBMIT_360_HR_APPRAISAL"

    print(
        "[✓] ISO/IEC 27701 & Decree 13/2023/ND-CP Partial Masking, Need-to-Know RBAC, 30s Audited Reveal, TOCTOU FOR UPDATE NOWAIT Lock, Dual-Control SoD, OKR PDCA Loop, 360° HR Appraisal 9-Box & Mandatory SWE Skill Gate verified"
    )


def verify_frontend_sources():
    for rel in (
        "enterprise/web_enterprise/static/src/webclient/home_menu/home_menu.js",
        "enterprise/web_enterprise/static/src/webclient/home_menu/home_menu.xml",
        "enterprise/web_enterprise/static/src/webclient/home_menu/home_menu.scss",
        "enterprise/web_enterprise/static/src/webclient/home_menu/home_menu.dark.scss",
    ):
        p = os.path.join(ROOT_DIR, rel)
        with open(p, "r", encoding="utf-8") as f:
            c = f.read()
        if rel.endswith(".js"):
            assert "_loadEmployeeDashboard" in c
            assert "/insilos/employee_dashboard/data" in c
            assert "/insilos/employee_dashboard/toggle_step" in c
            assert "/insilos/employee_dashboard/complete_skill_upgrade" in c
            assert "/insilos/employee_dashboard/submit_work_kpi_review" in c
            assert "/insilos/employee_dashboard/checkin_okr_kr" in c
            assert "/insilos/employee_dashboard/submit_hr_appraisal" in c
            assert "onCompleteSkillUpgrade" in c
            assert "onSubmitWorkKpiReview" in c
            assert "onCheckinOkrKr" in c
            assert "onSubmitHrAppraisal" in c
        elif rel.endswith(".xml"):
            assert "o_insilos_emp_dashboard" in c
            assert "SOP-DGM-04" in c
            assert "VCB DigiBiz" in c
            assert "kpi_skills" in c
            assert "onCompleteSkillUpgrade" in c
            assert "onSubmitWorkKpiReview" in c
            assert "onCheckinOkrKr" in c
            assert "onSubmitHrAppraisal" in c
            assert "okr_hub" in c
            assert "appraisal_hub" in c
            assert "project_pdca_templates" in c
        elif rel.endswith("home_menu.scss"):
            assert ".o_insilos_emp_dashboard" in c
            assert "var(--insilos-bg-card)" in c
            assert ".o_emp_skill_gate_banner" in c
            assert ".o_emp_pdca_gate_box" in c
            # Ensure no bare #ffffff inside .o_insilos_emp_dashboard block
            idx = c.find(".o_insilos_emp_dashboard")
            dash_scss = c[idx:]
            assert "#ffffff" not in dash_scss.lower() and "#fff" not in dash_scss.lower()

    manifest_path = os.path.join(ROOT_DIR, "addons/insilos_al2c/__manifest__.py")
    with open(manifest_path, "r", encoding="utf-8") as mf:
        m_content = mf.read()
    assert "'data/dgm_hr_master_data.xml'" in m_content

    xml_path = os.path.join(ROOT_DIR, "addons/insilos_al2c/data/dgm_hr_master_data.xml")
    with open(xml_path, "r", encoding="utf-8") as xf:
        x_content = xf.read()
    for token in (
        'noupdate="1"',
        "dept_dgm_board",
        "dept_dgm_tech_ai",
        "dept_dgm_b2b_onsite",
        "dept_dgm_finance_hr",
        "job_dgm_ceo",
        "job_dgm_cto",
        "job_dgm_cfo_hr",
        "job_dgm_senior_onsite",
        "job_dgm_tech_lead",
        "job_dgm_swe_onsite",
        "job_dgm_junior_dev",
        "emp_dgm_001",
        "emp_dgm_008",
        "emp_dgm_009",
        "partner_dgm_mti",
        "partner_dgm_canva",
        "partner_dgm_mobifone_mds",
        "partner_dgm_temecula",
        "partner_dgm_vnpt",
        "partner_dgm_viettel_ca",
        "partner_dgm_customer_aifin",
    ):
        assert token in x_content, f"Missing {token} in dgm_hr_master_data.xml"
    print("[✓] OWL 2 HomeMenu Employee Dashboard JS/XML/SCSS, Sovereign Dark Mode Tokens & dgm_hr_master_data.xml verified")


def verify_k8s_and_live_bundles():
    k8s_script = """
import os, psycopg2

conn = psycopg2.connect(
    dbname=os.environ.get('DB_NAME', 'innoria_prod'),
    user=os.environ.get('DB_USER', 'odoo'),
    password=os.environ.get('PGPASSWORD', ''),
    host=os.environ.get('DB_HOST', 'pgbouncer-service'),
    port=int(os.environ.get('DB_PORT', '6432')),
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM hr_employee WHERE active = TRUE;")
emp_cnt = cur.fetchone()[0]
assert emp_cnt == 19, f'Expected 19 active employees on K8s, got {emp_cnt}'

cur.execute("SELECT COUNT(*) FROM hr_department WHERE active = TRUE;")
dept_cnt = cur.fetchone()[0]
assert dept_cnt == 4, f'Expected 4 active departments on K8s, got {dept_cnt}'

cur.execute("SELECT COUNT(*) FROM hr_payslip;")
slip_cnt = cur.fetchone()[0]
assert slip_cnt >= 18, f'Expected >=18 payslips on K8s, got {slip_cnt}'

cur.execute("SELECT COUNT(*) FROM dgm_okr_objective WHERE active = TRUE;")
okr_cnt = cur.fetchone()[0]
assert okr_cnt >= 12, f'Expected >=12 OKR objectives on K8s, got {okr_cnt}'

cur.execute("SELECT COUNT(*) FROM dgm_hr_appraisal_sheet WHERE active = TRUE;")
apr_cnt = cur.fetchone()[0]
assert apr_cnt >= 9, f'Expected >=9 Appraisal sheets on K8s, got {apr_cnt}'

cur.execute("SELECT COUNT(*) FROM dgm_project_pdca_template WHERE active = TRUE;")
pdca_cnt = cur.fetchone()[0]
assert pdca_cnt >= 4, f'Expected >=4 PDCA templates on K8s, got {pdca_cnt}'

cur.execute("SELECT store_fname, file_size FROM ir_attachment WHERE name LIKE '%web.assets_web.min.js%' AND store_fname IS NOT NULL ORDER BY id DESC LIMIT 1;")
row = cur.fetchone()
if not row:
    import urllib.request
    js_req = urllib.request.Request('http://127.0.0.1:8069/web/assets/any/web.assets_web.min.js', headers={'Host': 'innoria.com'})
    urllib.request.urlopen(js_req, timeout=60).read()
    conn.commit()
    cur.execute("SELECT store_fname, file_size FROM ir_attachment WHERE name LIKE '%web.assets_web.min.js%' AND store_fname IS NOT NULL ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
assert row, 'Missing warmed web.assets_web.min.js attachment on K8s!'
store_fname, file_size = row
fpath = os.path.join('/var/lib/insilos/filestore/filestore/innoria_prod', store_fname)
with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()
assert 'o_insilos_emp_dashboard' in js_content, 'o_insilos_emp_dashboard missing in K8s web.assets_web.min.js!'
assert '_loadEmployeeDashboard' in js_content, '_loadEmployeeDashboard missing in K8s web.assets_web.min.js!'
assert 'onCheckinOkrKr' in js_content, 'onCheckinOkrKr missing in K8s web.assets_web.min.js!'
assert 'onSubmitHrAppraisal' in js_content, 'onSubmitHrAppraisal missing in K8s web.assets_web.min.js!'
conn.close()
print(f'K8S_BUNDLE_AND_DB_OK emps={emp_cnt} depts={dept_cnt} slips={slip_cnt} okrs={okr_cnt} aprs={apr_cnt} pdca_tpls={pdca_cnt} asset_js_bytes={file_size}')
"""
    pod_name = "innoria-prod-app-7cdc9b8ddc-4hdbs"
    try:
        discovered = subprocess.check_output(
            ["kubectl", "get", "pods", "-n", "production", "-l", "app=innoria-prod", "--field-selector=status.phase=Running", "-o", "jsonpath={.items[0].metadata.name}"],
            text=True,
        ).strip()
        if discovered:
            pod_name = discovered
    except Exception:
        pass
    proc = subprocess.run(
        [
            "kubectl",
            "exec",
            "-i",
            "-n",
            "production",
            pod_name,
            "-c",
            "innoria",
            "--",
            "python3",
            "-",
        ],
        input=k8s_script,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "K8S_BUNDLE_AND_DB_OK" in proc.stdout, proc.stdout
    print(f"[✓] K8s live production (`innoria_prod`): {proc.stdout.strip()}")


def main():
    verify_db_state("insilos20_dev")
    verify_db_state("innoria_prod")
    verify_vcb_xlsx_generator()
    verify_iso27701_privacy_and_maker_checker_workflow()
    verify_frontend_sources()
    verify_k8s_and_live_bundles()
    sys.path.insert(0, os.path.join(ROOT_DIR, "tools"))
    import test_dgm_partner_onboarding
    test_dgm_partner_onboarding.main()
    print("[🎉] ALL DGM HR, PAYROLL, ONBOARDING, LEAVING & VCB DIGIBIZ DASHBOARD CHECKS PASSED (EXIT 0)")


if __name__ == "__main__":
    main()



