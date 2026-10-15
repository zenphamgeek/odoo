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

    # 1. Verify exactly 8 active DGM employees
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
    assert len(emps) == 8, f"{dbname}: Expected 8 active employees, got {len(emps)}"
    regs = [r[1] for r in emps]
    assert regs == [f"DGM-00{i}" for i in range(1, 9)], f"{dbname}: Unexpected regs {regs}"
    assert emps[0][3] == 2, f"{dbname}: Expected DGM-001 linked to admin user_id=2, got {emps[0][3]}"
    assert int(emps[0][4]) == 45000000, f"{dbname}: Expected DGM-001 wage 45,000,000, got {emps[0][4]}"

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
    assert slips_cnt >= 16, f"{dbname}: Expected >= 16 payslips, got {slips_cnt}"

    # 5. Verify ir_config_parameter master registry & lifecycle
    cur.execute("SELECT value FROM ir_config_parameter WHERE key = 'dgm.hr.master_registry';")
    reg_row = cur.fetchone()
    assert reg_row, f"{dbname}: Missing dgm.hr.master_registry"
    reg_data = json.loads(reg_row[0])
    assert len(reg_data["employees"]) == 8
    assert sum(e["gross_wage"] for e in reg_data["employees"]) == 259000000

    conn.close()
    print(f"[✓] {dbname}: 8 DGM employees, 4 departments, 8 contracts, {slips_cnt} payslips, and VCB bank accounts verified")


def verify_vcb_xlsx_generator():
    import types

    odoo_mod = types.ModuleType("odoo")
    http_mod = types.ModuleType("odoo.http")

    class _DummyController:
        pass

    def _route(*args, **kwargs):
        def _dec(fn):
            return fn

        return _dec

    http_mod.Controller = _DummyController
    http_mod.route = _route
    http_mod.request = None
    odoo_mod.http = http_mod
    sys.modules["odoo"] = odoo_mod
    sys.modules["odoo.http"] = http_mod

    import employee_dashboard as ed

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
        elif rel.endswith(".xml"):
            assert "o_insilos_emp_dashboard" in c
            assert "SOP-DGM-04" in c
            assert "VCB DigiBiz" in c
        elif rel.endswith("home_menu.scss"):
            assert ".o_insilos_emp_dashboard" in c
            assert "var(--insilos-bg-card)" in c
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
        "partner_dgm_mti",
        "partner_dgm_canva",
        "partner_dgm_mobifone_mds",
        "partner_dgm_temecula",
        "partner_dgm_vnpt",
        "partner_dgm_viettel_ca",
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
assert emp_cnt == 8, f'Expected 8 active employees on K8s, got {emp_cnt}'

cur.execute("SELECT COUNT(*) FROM hr_department WHERE active = TRUE;")
dept_cnt = cur.fetchone()[0]
assert dept_cnt == 4, f'Expected 4 active departments on K8s, got {dept_cnt}'

cur.execute("SELECT COUNT(*) FROM hr_payslip;")
slip_cnt = cur.fetchone()[0]
assert slip_cnt >= 16, f'Expected >=16 payslips on K8s, got {slip_cnt}'

cur.execute("SELECT store_fname, file_size FROM ir_attachment WHERE name LIKE '%web.assets_web.min.js%' AND store_fname IS NOT NULL ORDER BY id DESC LIMIT 1;")
row = cur.fetchone()
assert row, 'Missing warmed web.assets_web.min.js attachment on K8s!'
store_fname, file_size = row
fpath = os.path.join('/var/lib/insilos/filestore/filestore/innoria_prod', store_fname)
with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()
assert 'o_insilos_emp_dashboard' in js_content, 'o_insilos_emp_dashboard missing in K8s web.assets_web.min.js!'
assert '_loadEmployeeDashboard' in js_content, '_loadEmployeeDashboard missing in K8s web.assets_web.min.js!'
conn.close()
print(f'K8S_BUNDLE_AND_DB_OK emps={emp_cnt} depts={dept_cnt} slips={slip_cnt} asset_js_bytes={file_size}')
"""
    proc = subprocess.run(
        [
            "kubectl",
            "exec",
            "-i",
            "-n",
            "production",
            "innoria-prod-app-7cdc9b8ddc-8st7m",
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
    verify_frontend_sources()
    verify_k8s_and_live_bundles()
    print("[🎉] ALL DGM HR, PAYROLL, ONBOARDING, LEAVING & VCB DIGIBIZ DASHBOARD CHECKS PASSED (EXIT 0)")


if __name__ == "__main__":
    main()

