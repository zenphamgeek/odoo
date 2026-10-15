#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Idempotent HR, Payroll, Contracts (`hr.version`), Payslips (`hr.payslip`),
Onboarding (`SOP-DGM-04`), and Leaving/Offboarding (`SOP-DGM-03/04`) Seeder for
CÔNG TY CỔ PHẦN DIGIMATE (DGM / Innoria).
Supports local `insilos20_dev`, local `innoria_prod`, and K8s `innoria_prod`.
"""
import configparser
import json
import os
import sys
import psycopg2


DEPARTMENTS = [
    {
        "code": "DEPT-EXEC",
        "name_vi": "Ban Giám Đốc & Quản Trị (Executive Board)",
        "name_en": "Ban Giám Đốc & Quản Trị (Executive Board)",
        "manager_reg": "DGM-001",
        "color": 1,
    },
    {
        "code": "DEPT-AI-ENG",
        "name_vi": "Khối Công Nghệ & AI (AI & Engineering — Mojo AI / ERP)",
        "name_en": "Khối Công Nghệ & AI (AI & Engineering — Mojo AI / ERP)",
        "manager_reg": "DGM-002",
        "color": 4,
    },
    {
        "code": "DEPT-B2B-MTI",
        "name_vi": "Khối Dịch Vụ Kỹ Sư Onsite B2B (Enterprise B2B & MTI Delivery)",
        "name_en": "Khối Dịch Vụ Kỹ Sư Onsite B2B (Enterprise B2B & MTI Delivery)",
        "manager_reg": "DGM-004",
        "color": 10,
    },
    {
        "code": "DEPT-FIN-HR",
        "name_vi": "Khối Tài Chính - Kế Toán - Nhân Sự (Finance, Accounting & HR)",
        "name_en": "Khối Tài Chính - Kế Toán - Nhân Sự (Finance, Accounting & HR)",
        "manager_reg": "DGM-003",
        "color": 3,
    },
]

EMPLOYEES = [
    {
        "reg": "DGM-001",
        "match_id": 63,
        "name": "Lê Xuân Hoàng",
        "aliases": ["Lê Xuân Hoàng"],
        "id_card_name": "089094016917",
        "job_title": "Chủ tịch HĐQT & Tổng Giám đốc",
        "dept_code": "DEPT-EXEC",
        "manager_reg": None,
        "work_email": "hoang.le@inno.ai.vn",
        "work_phone": "0903881001",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "bank_branch": "CN TP.HCM",
        "account_number": "1373068161",
        "gross_wage": 45000000,
        "join_date": "2024-01-01",
        "link_admin_uid": 2,
    },
    {
        "reg": "DGM-002",
        "match_id": 55,
        "name": "Nguyễn Hoài Ân",
        "aliases": ["Nguyễn Hoài Ân"],
        "id_card_name": "096095006609",
        "job_title": "Cổ đông sáng lập & CTO",
        "dept_code": "DEPT-AI-ENG",
        "manager_reg": "DGM-001",
        "work_email": "an.nguyen@inno.ai.vn",
        "work_phone": "0903881002",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "bank_branch": "CN TP.HCM",
        "account_number": "1901014028",
        "gross_wage": 42000000,
        "join_date": "2024-01-01",
        "link_admin_uid": None,
    },
    {
        "reg": "DGM-003",
        "match_id": 60,
        "name": "Mai Thị Hồng Thắm",
        "aliases": ["Mai Thị Hồng Thắm"],
        "id_card_name": "093197003049",
        "job_title": "Cổ đông sáng lập & CFO/HR Lead",
        "dept_code": "DEPT-FIN-HR",
        "manager_reg": "DGM-001",
        "work_email": "tham.mai@inno.ai.vn",
        "work_phone": "0903881003",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "bank_branch": "CN Nam Sài Gòn",
        "account_number": "0111000287863",
        "gross_wage": 35000000,
        "join_date": "2024-01-01",
        "link_admin_uid": None,
    },
    {
        "reg": "DGM-004",
        "match_id": 73,
        "name": "Bùi Hữu Tài",
        "aliases": ["Bùi Hữu Tài", "Bùi Hửu Tài"],
        "id_card_name": "365931521",
        "job_title": "Kỹ sư Phần mềm Senior (MTI Onsite)",
        "dept_code": "DEPT-B2B-MTI",
        "manager_reg": "DGM-001",
        "work_email": "tai.bui@inno.ai.vn",
        "work_phone": "0903881004",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "bank_branch": "CN Tân Bình",
        "account_number": "1045246615",
        "gross_wage": 32000000,
        "join_date": "2024-01-01",
        "link_admin_uid": None,
    },
    {
        "reg": "DGM-005",
        "match_id": 69,
        "name": "Huỳnh Trần Quang Khánh",
        "aliases": ["Huỳnh Trần Quang Khánh"],
        "id_card_name": "089085004243",
        "job_title": "Kỹ sư Phần mềm Senior / Tech Lead",
        "dept_code": "DEPT-AI-ENG",
        "manager_reg": "DGM-002",
        "work_email": "khanh.huynh@inno.ai.vn",
        "work_phone": "0903881005",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "bank_branch": "CN Sài Gòn",
        "account_number": "12154887",
        "gross_wage": 34000000,
        "join_date": "2024-02-01",
        "link_admin_uid": None,
    },
    {
        "reg": "DGM-006",
        "match_id": 57,
        "name": "Ngô Thanh Lộc",
        "aliases": ["Ngô Thanh Lộc", "Ngô Thành Lộc"],
        "id_card_name": "079096011234",
        "job_title": "Kỹ sư Phần mềm Senior (MTI Onsite)",
        "dept_code": "DEPT-B2B-MTI",
        "manager_reg": "DGM-004",
        "work_email": "loc.ngo@inno.ai.vn",
        "work_phone": "0903881006",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "bank_branch": "CN Cộng Hòa",
        "account_number": "12154937",
        "gross_wage": 28000000,
        "join_date": "2024-02-01",
        "link_admin_uid": None,
    },
    {
        "reg": "DGM-007",
        "match_id": 62,
        "name": "Lê Cao Bảo Phúc",
        "aliases": ["Lê Cao Bảo Phúc"],
        "id_card_name": "079097022345",
        "job_title": "Kỹ sư Phần mềm (MTI Onsite)",
        "dept_code": "DEPT-B2B-MTI",
        "manager_reg": "DGM-004",
        "work_email": "phuc.le@inno.ai.vn",
        "work_phone": "0903881007",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "bank_branch": "CN Cộng Hòa",
        "account_number": "12154917",
        "gross_wage": 25000000,
        "join_date": "2024-03-01",
        "link_admin_uid": None,
    },
    {
        "reg": "DGM-008",
        "match_id": None,
        "name": "Thái Nguyễn Đăng Khoa",
        "aliases": ["Thái Nguyễn Đăng Khoa"],
        "id_card_name": "079099033456",
        "job_title": "Kỹ sư Phần mềm / Junior Developer",
        "dept_code": "DEPT-AI-ENG",
        "manager_reg": "DGM-002",
        "work_email": "khoa.thai@inno.ai.vn",
        "work_phone": "0903881008",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "bank_branch": "CN Tân Thuận",
        "account_number": "47070467",
        "gross_wage": 18000000,
        "join_date": "2024-06-01",
        "link_admin_uid": None,
    },
]


def compute_vn_payroll(gross):
    """Compute VN 2026 statutory BHXH (8%), BHYT (1.5%), BHTN (1%), PIT, and Net."""
    bhxh = round(gross * 0.08)
    bhyt = round(gross * 0.015)
    bhtn = round(gross * 0.01)
    total_ins = bhxh + bhyt + bhtn
    personal_deduction = 11000000
    taxable = max(0, gross - total_ins - personal_deduction)
    if taxable <= 0:
        pit = 0
    elif taxable <= 5000000:
        pit = round(taxable * 0.05)
    elif taxable <= 10000000:
        pit = round(taxable * 0.10 - 250000)
    elif taxable <= 18000000:
        pit = round(taxable * 0.15 - 750000)
    elif taxable <= 32000000:
        pit = round(taxable * 0.20 - 1650000)
    elif taxable <= 52000000:
        pit = round(taxable * 0.25 - 3250000)
    else:
        pit = round(taxable * 0.30 - 5850000)
    net = gross - total_ins - pit
    return {
        "gross_wage": gross,
        "bhxh_amount": bhxh,
        "bhyt_amount": bhyt,
        "bhtn_amount": bhtn,
        "total_insurance": total_ins,
        "taxable_income": taxable,
        "pit_amount": pit,
        "net_wage": net,
    }


def default_lifecycle_state(emp):
    return {
        "onboarding": {
            "status": "in_progress",
            "steps": [
                {
                    "id": "onb_1",
                    "code": "SOP-DGM-04.1",
                    "title": "Hồ sơ Pháp lý, CCCD & Định danh Thuế TNCN",
                    "description": "Thu thập CCCD gắn chip, MST cá nhân, đăng ký giảm trừ gia cảnh và hồ sơ nhân sự gốc.",
                    "owner": "HR & Legal (Mai Thị Hồng Thắm)",
                    "sla": "Ngày 1",
                    "done": True,
                    "completed_at": "2024-01-02",
                },
                {
                    "id": "onb_2",
                    "code": "SOP-DGM-04.2",
                    "title": "Ký Hợp đồng Lao động 12 Điều Chuẩn DGM & Cam kết NDA/SHTT",
                    "description": "Ký HĐLĐ mẫu chuẩn 12 điều, thỏa thuận bảo mật NDA và quyền sở hữu trí tuệ mã nguồn.",
                    "owner": "Ban Giám Đốc & Pháp chế",
                    "sla": "Ngày 1",
                    "done": True,
                    "completed_at": "2024-01-02",
                },
                {
                    "id": "onb_3",
                    "code": "SOP-DGM-04.3",
                    "title": "Báo tăng BHXH Quận 7 (Mã ĐV: TZ0857G) & Xác thực Tài khoản Lương",
                    "description": f"Đăng ký BHXH/BHYT/BHTN tại BHXH Quận 7 và liên kết TK {emp['bank_name']} ({emp['account_number']}) trên VCB DigiBiz.",
                    "owner": "Kế toán Tiền lương (FIN-HR)",
                    "sla": "Trong 15 ngày đầu",
                    "done": True,
                    "completed_at": "2024-01-10",
                },
                {
                    "id": "onb_4",
                    "code": "SOP-DGM-04.4",
                    "title": "Cấp phát Tài khoản Innoria ERP, Email @inno.ai.vn, GitHub & VPN",
                    "description": f"Khởi tạo định danh SSO ({emp['work_email']}), phân quyền kho tài liệu Documents (5 phân vùng) & môi trường Dev.",
                    "owner": "IT & SecOps (Nguyễn Hoài Ân)",
                    "sla": "Ngày 1",
                    "done": True,
                    "completed_at": "2024-01-02",
                },
                {
                    "id": "onb_5",
                    "code": "SOP-DGM-04.5",
                    "title": "Đánh giá Hội nhập 60 Ngày & Bàn giao KPI Quý",
                    "description": "Hoàn tất đánh giá thử việc/hội nhập kỹ thuật cùng Quản lý trực tiếp và xác nhận mục tiêu OKR/KPI.",
                    "owner": "Trưởng bộ phận & HR",
                    "sla": "Ngày 60",
                    "done": False,
                    "completed_at": None,
                },
            ],
        },
        "leaving": {
            "status": "active_employment",
            "notice_date": "",
            "expected_last_day": "",
            "handover_assignee": "Nguyễn Hoài Ân (CTO)",
            "reason": "",
            "steps": [
                {
                    "id": "off_1",
                    "code": "SOP-DGM-03.1",
                    "title": "Tiếp nhận Đơn xin nghỉ việc & Phê duyệt Thời hạn Báo trước",
                    "description": "Kiểm tra thời hạn báo trước theo Bộ luật Lao động (30/45 ngày) và xác nhận ngày làm việc cuối cùng.",
                    "owner": "Trưởng bộ phận & HR",
                    "sla": "T-30 ngày",
                    "done": False,
                    "completed_at": None,
                },
                {
                    "id": "off_2",
                    "code": "SOP-DGM-03.2",
                    "title": "Bàn giao Mã nguồn (Git/PR), Tài liệu Kỹ thuật & Dự án MTI/Mojo AI",
                    "description": "Nghiệm thu toàn bộ PR, tài liệu kiến trúc, khóa API và chuyển giao quyền sở hữu trên kho Documents.",
                    "owner": "CTO / Tech Lead",
                    "sla": "T-7 ngày",
                    "done": False,
                    "completed_at": None,
                },
                {
                    "id": "off_3",
                    "code": "SOP-DGM-03.3",
                    "title": "Thu hồi Thiết bị (Laptop/Thẻ từ) & Đóng quyền Truy cập SSO/GitHub/VPN",
                    "description": "Thu hồi tài sản vật lý và vô hiệu hóa token truy cập hệ thống sản xuất,クラウド, VPN, Email.",
                    "owner": "IT & SecOps",
                    "sla": "Ngày cuối (T-0)",
                    "done": False,
                    "completed_at": None,
                },
                {
                    "id": "off_4",
                    "code": "SOP-DGM-04.4",
                    "title": "Đối soát Công nợ Tạm ứng (TK 141) & Quyết toán Lương / Thuế TNCN",
                    "description": "Tính lương ngày công thực tế, phép năm tồn, khấu trừ thuế TNCN và tất toán qua VCB DigiBiz.",
                    "owner": "Kế toán Trưởng (Mai Thị Hồng Thắm)",
                    "sla": "T+7 ngày",
                    "done": False,
                    "completed_at": None,
                },
                {
                    "id": "off_5",
                    "code": "SOP-DGM-04.5",
                    "title": "Báo giảm BHXH Quận 7 (TZ0857G), Chốt sổ BHXH & Ban hành Quyết định Thôi việc",
                    "description": "Nộp hồ sơ báo giảm điện tử lên BHXH Quận 7, bàn giao tờ rời sổ BHXH và chứng từ khấu trừ thuế TNCN.",
                    "owner": "HR & Pháp chế",
                    "sla": "T+14 ngày",
                    "done": False,
                    "completed_at": None,
                },
            ],
        },
    }


def get_connection(dbname=None):
    db = dbname or os.environ.get("DB_NAME", "innoria_prod")
    user = os.environ.get("DB_USER")
    password = os.environ.get("PGPASSWORD")
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "5434"))
    if not user or not password:
        cfg_path = "/home/zen/O20/odoo.conf"
        if os.path.exists(cfg_path):
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path)
            user = user or cfg["options"].get("db_user", "odoo")
            password = password or cfg["options"].get("db_password", "odoo")
            host = os.environ.get("DB_HOST") or cfg["options"].get("db_host", "127.0.0.1")
            port = int(os.environ.get("DB_PORT") or cfg["options"].get("db_port", "5434"))
    kwargs = dict(dbname=db, user=user or "odoo", host=host, port=port)
    if password:
        kwargs["password"] = password
    return psycopg2.connect(**kwargs)


def upsert_config_param(cur, key, val):
    cur.execute("SELECT id FROM ir_config_parameter WHERE key = %s;", (key,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE ir_config_parameter SET value = %s, write_uid = 1, write_date = NOW() WHERE id = %s;",
            (val, row[0]),
        )
    else:
        cur.execute(
            "INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date) VALUES (%s, %s, 1, 1, NOW(), NOW());",
            (key, val),
        )


def seed_hr_payroll_for_db(dbname):
    conn = get_connection(dbname)
    cur = conn.cursor()

    cur.execute("SELECT id FROM res_country WHERE code = 'VN' LIMIT 1;")
    r = cur.fetchone()
    vn_id = r[0] if r else 241

    # 1. Upsert 4 Canonical Departments
    dept_map = {}
    for d in DEPARTMENTS:
        name_json = json.dumps({"en_US": d["name_en"], "vi_VN": d["name_vi"]})
        cur.execute(
            """
            SELECT id FROM hr_department
             WHERE name->>'vi_VN' = %s OR name->>'en_US' = %s
             ORDER BY id LIMIT 1;
            """,
            (d["name_vi"], d["name_en"]),
        )
        row = cur.fetchone()
        if row:
            dept_id = row[0]
            cur.execute(
                """
                UPDATE hr_department
                   SET name = %s::jsonb,
                       company_id = 1,
                       color = %s,
                       active = TRUE,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (name_json, d["color"], dept_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO hr_department (
                    name, company_id, color, active, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s::jsonb, 1, %s, TRUE, 1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (name_json, d["color"]),
            )
            dept_id = cur.fetchone()[0]
            cur.execute("UPDATE hr_department SET parent_path = %s WHERE id = %s;", (f"{dept_id}/", dept_id))
        dept_map[d["code"]] = dept_id

    # Deactivate non-canonical departments so HR department view stays clean
    canonical_dept_ids = list(dept_map.values())
    cur.execute(
        "UPDATE hr_department SET active = FALSE WHERE id != ALL(%s);",
        (canonical_dept_ids,),
    )

    # 2. Upsert Canonical Jobs (`hr_job`)
    cur.execute("SELECT id FROM ir_model WHERE model IN ('hr.applicant', 'hr.job') ORDER BY CASE WHEN model='hr.applicant' THEN 0 ELSE 1 END LIMIT 1;")
    alias_model_id = cur.fetchone()[0]

    job_map = {}
    for idx, e in enumerate(EMPLOYEES, start=1):
        jtitle = e["job_title"]
        dept_id = dept_map[e["dept_code"]]
        key = (jtitle, dept_id)
        if key in job_map:
            continue
        name_json = json.dumps({"en_US": jtitle, "vi_VN": jtitle})
        cur.execute(
            """
            SELECT id FROM hr_job
             WHERE (name->>'vi_VN' = %s OR name->>'en_US' = %s)
               AND COALESCE(department_id, %s) = %s
             ORDER BY id LIMIT 1;
            """,
            (jtitle, jtitle, dept_id, dept_id),
        )
        row = cur.fetchone()
        if row:
            job_id = row[0]
            cur.execute(
                """
                UPDATE hr_job
                   SET name = %s::jsonb,
                       department_id = %s,
                       company_id = 1,
                       active = TRUE,
                       no_of_recruitment = 1,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (name_json, dept_id, job_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO mail_alias (
                    alias_model_id, alias_contact, alias_defaults, create_uid, write_uid, create_date, write_date
                ) VALUES (%s, 'everyone', '{}', 1, 1, NOW(), NOW())
                RETURNING id;
                """,
                (alias_model_id,),
            )
            alias_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO hr_job (
                    sequence, name, department_id, company_id, alias_id, payment_interval,
                    no_of_recruitment, active, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s::jsonb, %s, 1, %s, 'monthly',
                    1, TRUE, 1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (idx * 10, name_json, dept_id, alias_id),
            )
            job_id = cur.fetchone()[0]
        job_map[key] = job_id

    # 3. Clear user_id=2 on any non-DGM-001 employee so we can bind admin user (uid=2) to DGM-001 cleanly
    cur.execute("UPDATE hr_employee SET user_id = NULL WHERE user_id = 2 AND COALESCE(registration_number, '') != 'DGM-001';")

    # 4. Upsert 8 Canonical Employees, Work Contacts, Bank Accounts, and Contracts (`hr_version`)
    emp_id_by_reg = {}
    version_id_by_reg = {}
    canonical_emp_ids = []

    # Check ifdocuments folder exists for HR & Legal
    cur.execute("SELECT to_regclass('public.documents_document');")
    has_docs = cur.fetchone()[0] is not None
    hr_folder_id = None
    if has_docs:
        cur.execute(
            "SELECT id FROM documents_document WHERE active = TRUE AND type = 'folder' AND name::text ILIKE '%04 - Nhân sự%' ORDER BY id LIMIT 1;"
        )
        r = cur.fetchone()
        if r:
            hr_folder_id = r[0]

    for e in EMPLOYEES:
        emp_id = None
        work_contact_id = None
        resource_id = None
        current_version_id = None

        cur.execute(
            """
            SELECT id, work_contact_id, resource_id, current_version_id
              FROM hr_employee
             WHERE registration_number = %s
                OR barcode = %s
                OR TRIM(name) = ANY(%s)
             ORDER BY CASE WHEN registration_number = %s THEN 0 ELSE 1 END, id
             LIMIT 1;
            """,
            (e["reg"], e["reg"], e["aliases"], e["reg"]),
        )
        r = cur.fetchone()
        if r:
            emp_id, work_contact_id, resource_id, current_version_id = r

        if not emp_id and e["match_id"]:
            cur.execute(
                "SELECT id, work_contact_id, resource_id, current_version_id FROM hr_employee WHERE id = %s;",
                (e["match_id"],),
            )
            r = cur.fetchone()
            if r and r[0]:
                emp_id, work_contact_id, resource_id, current_version_id = r

        if emp_id:
            cur.execute(
                "UPDATE hr_employee SET barcode = NULL, registration_number = NULL WHERE (barcode = %s OR registration_number = %s) AND id != %s;",
                (e["reg"], e["reg"], emp_id),
            )
        else:
            cur.execute(
                "UPDATE hr_employee SET barcode = NULL, registration_number = NULL WHERE barcode = %s OR registration_number = %s;",
                (e["reg"], e["reg"]),
            )

        # Ensure party_master work_contact_id
        if work_contact_id:
            cur.execute(
                """
                UPDATE party_master
                   SET name = %s,
                       complete_name = %s,
                       email = %s,
                       email_normalized = %s,
                       phone = %s,
                       is_company = FALSE,
                       active = TRUE,
                       employee = TRUE,
                       company_id = 1,
                       country_id = COALESCE(country_id, %s),
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (e["name"], e["name"], e["work_email"], e["work_email"], e["work_phone"], vn_id, work_contact_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO party_master (
                    name, complete_name, email, email_normalized, phone,
                    is_company, active, employee, partner_share,
                    company_id, country_id, type, autopost_bills, group_rfq, group_on,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    FALSE, TRUE, TRUE, FALSE,
                    1, %s, 'contact', 'ask', 'default', 'default',
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (e["name"], e["name"], e["work_email"], e["work_email"], e["work_phone"], vn_id),
            )
            work_contact_id = cur.fetchone()[0]
            cur.execute(
                "UPDATE party_master SET commercial_partner_id = %s WHERE id = %s;",
                (work_contact_id, work_contact_id),
            )

        # Ensure resource_resource
        if resource_id:
            cur.execute(
                "UPDATE resource_resource SET name = %s, active = TRUE, company_id = 1, write_date = NOW() WHERE id = %s;",
                (e["name"], resource_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO resource_resource (
                    name, resource_type, company_id, calendar_id, tz, active,
                    time_efficiency, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, 'user', 1, 1, 'Asia/Ho_Chi_Minh', TRUE,
                    100, 1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (e["name"],),
            )
            resource_id = cur.fetchone()[0]

        # Upsert hr_employee
        if emp_id:
            cur.execute(
                """
                UPDATE hr_employee
                   SET name = %s,
                       legal_name = %s,
                       registration_number = %s,
                       barcode = %s,
                       id_card_name = %s,
                       work_email = %s,
                       work_phone = %s,
                       mobile_phone = %s,
                       work_contact_id = %s,
                       resource_id = %s,
                       user_id = COALESCE(%s, user_id),
                       company_id = 1,
                       active = TRUE,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (
                    e["name"],
                    e["name"],
                    e["reg"],
                    e["reg"],
                    e["id_card_name"],
                    e["work_email"],
                    e["work_phone"],
                    e["work_phone"],
                    work_contact_id,
                    resource_id,
                    e["link_admin_uid"],
                    emp_id,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO hr_employee (
                    name, legal_name, registration_number, barcode, id_card_name,
                    work_email, work_phone, mobile_phone,
                    work_contact_id, resource_id, user_id, company_id, active, color,
                    birthday_public_display, work_permit_scheduled_activity, is_flexible,
                    structure_type_id, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, 1, TRUE, 0,
                    FALSE, FALSE, FALSE,
                    1, 1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (
                    e["name"],
                    e["name"],
                    e["reg"],
                    e["reg"],
                    e["id_card_name"],
                    e["work_email"],
                    e["work_phone"],
                    e["work_phone"],
                    work_contact_id,
                    resource_id,
                    e["link_admin_uid"],
                ),
            )
            emp_id = cur.fetchone()[0]

        dept_id = dept_map[e["dept_code"]]
        job_id = job_map[(e["job_title"], dept_id)]
        contract_name = f"HĐLĐ/{e['reg']}/2026 — {e['name']}"

        # Ensure hr_version has department_id, job_id, job_title, wage, contract_date_start, identification_id
        if current_version_id:
            cur.execute(
                """
                UPDATE hr_version
                   SET name = %s,
                       department_id = %s,
                       job_id = %s,
                       job_title = %s,
                       wage = %s,
                       contract_date_start = %s::date,
                       date_version = %s::date,
                       identification_id = %s,
                       active = TRUE,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (
                    contract_name,
                    dept_id,
                    job_id,
                    e["job_title"],
                    e["gross_wage"],
                    e["join_date"],
                    e["join_date"],
                    e["id_card_name"],
                    current_version_id,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO hr_version (
                    company_id, employee_id, last_modified_uid, private_country_id,
                    km_home_work, address_id, work_location_id, resource_calendar_id,
                    structure_type_id, hr_responsible_id, create_uid, write_uid,
                    distance_home_work_unit, marital, tz, date_version, contract_date_start,
                    name, department_id, job_id, job_title, wage, identification_id,
                    active, is_custom_job_title, last_modified_date, create_date, write_date,
                    attendance_based, work_entry_source, standard_calendar_id, employee_type,
                    schedule_pay, wage_type, work_time_rate, overtime_from_attendance,
                    l10n_us_filing_status, l10n_us_pre_retirement_type,
                    l10n_us_pre_retirement_matching_type, l10n_us_post_roth_401k_type,
                    l10n_us_pre_retirement_matching_yearly_cap
                ) VALUES (
                    1, %s, 1, %s,
                    0, 1, 1, 1,
                    1, 1, 1, 1,
                    'kilometers', 'single', 'Asia/Ho_Chi_Minh', %s::date, %s::date,
                    %s, %s, %s, %s, %s, %s,
                    TRUE, TRUE, NOW(), NOW(), NOW(),
                    FALSE, 'calendar', 1, 'employee',
                    'monthly', 'monthly', 1.0, FALSE,
                    'single', 'percent',
                    'percent', 'percent',
                    100.0
                ) RETURNING id;
                """,
                (
                    emp_id,
                    vn_id,
                    e["join_date"],
                    e["join_date"],
                    contract_name,
                    dept_id,
                    job_id,
                    e["job_title"],
                    e["gross_wage"],
                    e["id_card_name"],
                ),
            )
            current_version_id = cur.fetchone()[0]
            cur.execute(
                "UPDATE hr_employee SET current_version_id = %s WHERE id = %s;",
                (current_version_id, emp_id),
            )

        # Upsert res_partner_bank and link via employee_bank_account_rel
        stk = e["account_number"].strip()
        cur.execute(
            "SELECT id FROM res_partner_bank WHERE sanitized_account_number = %s AND partner_id = %s LIMIT 1;",
            (stk, work_contact_id),
        )
        b_row = cur.fetchone()
        if b_row:
            bank_id = b_row[0]
            cur.execute(
                """
                UPDATE res_partner_bank
                   SET account_number = %s,
                       sanitized_account_number = %s,
                       bank_name = %s,
                       bank_bic = %s,
                       holder_name = %s,
                       company_id = 1,
                       country_id = %s,
                       active = TRUE,
                       allow_out_payment = TRUE,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (stk, stk, e["bank_name"], e["bank_bic"], e["name"], vn_id, bank_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO res_partner_bank (
                    account_number, sanitized_account_number, bank_name, bank_bic,
                    holder_name, partner_id, company_id, country_id, active,
                    allow_out_payment, sequence, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, 1, %s, TRUE,
                    TRUE, 10, 1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (stk, stk, e["bank_name"], e["bank_bic"], e["name"], work_contact_id, vn_id),
            )
            bank_id = cur.fetchone()[0]

        cur.execute(
            "SELECT 1 FROM employee_bank_account_rel WHERE employee_id = %s AND bank_account_id = %s;",
            (emp_id, bank_id),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO employee_bank_account_rel (employee_id, bank_account_id) VALUES (%s, %s);",
                (emp_id, bank_id),
            )

        # Pre-bind ir_model_data XML IDs so `-u insilos_al2c` never duplicates employees/contacts/banks
        emp_xml_suffix = {
            "DGM-001": ("001", "hoang"),
            "DGM-002": ("002", "an"),
            "DGM-003": ("003", "tham"),
            "DGM-004": ("004", "tai"),
            "DGM-005": ("005", "khanh"),
            "DGM-006": ("006", "loc"),
            "DGM-007": ("007", "phuc"),
            "DGM-008": ("008", "khoa"),
        }[e["reg"]]
        for xname, xmodel, xid in [
            (f"emp_dgm_{emp_xml_suffix[0]}", "hr.employee", emp_id),
            (f"hr_employee_dgm_{emp_xml_suffix[0]}", "hr.employee", emp_id),
            (f"partner_emp_{emp_xml_suffix[1]}", "party.master", work_contact_id),
            (f"bank_emp_{emp_xml_suffix[1]}", "res.partner.bank", bank_id),
        ]:
            cur.execute(
                """
                INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
                VALUES (%s, 'insilos_al2c', %s, %s, TRUE, 1, 1, NOW(), NOW())
                ON CONFLICT (module, name) DO UPDATE
                   SET model = EXCLUDED.model,
                       res_id = EXCLUDED.res_id,
                       noupdate = TRUE,
                       write_date = NOW();
                """,
                (xname, xmodel, xid),
            )

        # Seed lifecycle state in ir_config_parameter if not already set
        lifecycle_key = f"dgm.hr.lifecycle.{emp_id}"
        cur.execute("SELECT id FROM ir_config_parameter WHERE key = %s;", (lifecycle_key,))
        if not cur.fetchone():
            upsert_config_param(cur, lifecycle_key, json.dumps(default_lifecycle_state(e), ensure_ascii=False))

        emp_id_by_reg[e["reg"]] = emp_id
        version_id_by_reg[e["reg"]] = current_version_id
        canonical_emp_ids.append(emp_id)

    # Pre-bind ir_model_data XML IDs for the 4 canonical departments and 7 canonical jobs
    dept_xml_map = {
        "DEPT-EXEC": "dept_dgm_board",
        "DEPT-AI-ENG": "dept_dgm_tech_ai",
        "DEPT-B2B-MTI": "dept_dgm_b2b_onsite",
        "DEPT-FIN-HR": "dept_dgm_finance_hr",
    }
    for dcode, xname in dept_xml_map.items():
        cur.execute(
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
            VALUES (%s, 'insilos_al2c', 'hr.department', %s, TRUE, 1, 1, NOW(), NOW())
            ON CONFLICT (module, name) DO UPDATE
               SET model = 'hr.department',
                   res_id = EXCLUDED.res_id,
                   noupdate = TRUE,
                   write_date = NOW();
            """,
            (xname, dept_map[dcode]),
        )

    job_xml_map = {
        ("Chủ tịch HĐQT & Tổng Giám đốc", dept_map["DEPT-EXEC"]): "job_dgm_ceo",
        ("Cổ đông sáng lập & CTO", dept_map["DEPT-AI-ENG"]): "job_dgm_cto",
        ("Cổ đông sáng lập & CFO/HR Lead", dept_map["DEPT-FIN-HR"]): "job_dgm_cfo_hr",
        ("Kỹ sư Phần mềm Senior (MTI Onsite)", dept_map["DEPT-B2B-MTI"]): "job_dgm_senior_onsite",
        ("Kỹ sư Phần mềm Senior / Tech Lead", dept_map["DEPT-AI-ENG"]): "job_dgm_tech_lead",
        ("Kỹ sư Phần mềm (MTI Onsite)", dept_map["DEPT-B2B-MTI"]): "job_dgm_swe_onsite",
        ("Kỹ sư Phần mềm / Junior Developer", dept_map["DEPT-AI-ENG"]): "job_dgm_junior_dev",
    }
    for jkey, xname in job_xml_map.items():
        if jkey in job_map:
            cur.execute(
                """
                INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
                VALUES (%s, 'insilos_al2c', 'hr.job', %s, TRUE, 1, 1, NOW(), NOW())
                ON CONFLICT (module, name) DO UPDATE
                   SET model = 'hr.job',
                       res_id = EXCLUDED.res_id,
                       noupdate = TRUE,
                       write_date = NOW();
                """,
                (xname, job_map[jkey]),
            )

    # 5. Archive any non-canonical / demo employees so HR directory has exactly 8 active DGM employees
    cur.execute(
        "UPDATE hr_employee SET active = FALSE WHERE id != ALL(%s);",
        (canonical_emp_ids,),
    )

    # 6. Set parent_id / coach_id hierarchy on hr_employee and manager_id on hr_department
    for e in EMPLOYEES:
        emp_id = emp_id_by_reg[e["reg"]]
        mgr_id = emp_id_by_reg.get(e["manager_reg"]) if e["manager_reg"] else emp_id_by_reg["DGM-001"]
        parent_id = emp_id_by_reg.get(e["manager_reg"]) if e["manager_reg"] else None
        cur.execute(
            "UPDATE hr_employee SET parent_id = %s, coach_id = %s WHERE id = %s;",
            (parent_id, mgr_id, emp_id),
        )

    for d in DEPARTMENTS:
        dept_id = dept_map[d["code"]]
        mgr_id = emp_id_by_reg.get(d["manager_reg"])
        cur.execute("UPDATE hr_department SET manager_id = %s WHERE id = %s;", (mgr_id, dept_id))

    # 7. Seed Payslip Runs (`hr_payslip_run`) & Payslips (`hr_payslip` + `hr_payslip_line`)
    cur.execute("SELECT id FROM hr_payroll_structure ORDER BY id LIMIT 1;")
    s_row = cur.fetchone()
    struct_id = s_row[0] if s_row else 1

    cur.execute("SELECT code, id FROM hr_salary_rule WHERE code IN ('BASIC', 'GROSS', 'DEDUCTION', 'NET');")
    rule_map = dict(cur.fetchall())
    cur.execute("SELECT id FROM hr_salary_rule ORDER BY id LIMIT 1;")
    fallback_rule_id = cur.fetchone()[0]

    batches = [
        ("Bảng lương DGM — Tháng 09/2026 (Đã chi qua VCB DigiBiz)", "2026-09-01", "2026-09-30", "03_paid"),
        ("Bảng lương DGM — Tháng 10/2026 (Chuẩn VCB DigiBiz)", "2026-10-01", "2026-10-31", "02_close"),
    ]

    latest_run_id = None
    latest_slip_by_reg = {}

    for b_name, d_start, d_end, b_state in batches:
        total_gross = sum(e["gross_wage"] for e in EMPLOYEES)
        total_net = sum(compute_vn_payroll(e["gross_wage"])["net_wage"] for e in EMPLOYEES)

        cur.execute(
            "SELECT id FROM hr_payslip_run WHERE date_start = %s::date AND date_end = %s::date ORDER BY id LIMIT 1;",
            (d_start, d_end),
        )
        r = cur.fetchone()
        if r:
            run_id = r[0]
            cur.execute(
                """
                UPDATE hr_payslip_run
                   SET name = %s,
                       state = %s,
                       structure_id = %s,
                       payslip_count = %s,
                       gross_sum = %s,
                       net_sum = %s,
                       schedule_pay = 'monthly',
                       active = TRUE,
                       company_id = 1,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (b_name, b_state, struct_id, len(EMPLOYEES), total_gross, total_net, run_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO hr_payslip_run (
                    name, state, structure_id, payslip_count, gross_sum, net_sum,
                    schedule_pay, date_start, date_end, active, company_id,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    'monthly', %s::date, %s::date, TRUE, 1,
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (b_name, b_state, struct_id, len(EMPLOYEES), total_gross, total_net, d_start, d_end),
            )
            run_id = cur.fetchone()[0]

        latest_run_id = run_id
        ym = d_start[:7].replace("-", "")

        for idx, e in enumerate(EMPLOYEES, start=1):
            emp_id = emp_id_by_reg[e["reg"]]
            ver_id = version_id_by_reg[e["reg"]]
            dept_id = dept_map[e["dept_code"]]
            job_id = job_map[(e["job_title"], dept_id)]
            calc = compute_vn_payroll(e["gross_wage"])
            slip_name = f"Phiếu lương {e['name']} ({e['reg']}) - {d_start[:7]}"
            slip_number = f"SLIP/{ym}/{idx:03d}"

            cur.execute(
                """
                SELECT id FROM hr_payslip
                 WHERE employee_id = %s AND date_from = %s::date AND date_to = %s::date
                 ORDER BY id LIMIT 1;
                """,
                (emp_id, d_start, d_end),
            )
            sr = cur.fetchone()
            if sr:
                slip_id = sr[0]
                cur.execute(
                    """
                    UPDATE hr_payslip
                       SET name = %s,
                           state = %s,
                           struct_id = %s,
                           version_id = %s,
                           department_id = %s,
                           job_id = %s,
                           payslip_run_id = %s,
                           basic_wage = %s,
                           gross_wage = %s,
                           net_wage = %s,
                           compute_date = CURRENT_DATE,
                           company_id = 1,
                           write_uid = 1,
                           write_date = NOW()
                     WHERE id = %s;
                    """,
                    (
                        slip_name,
                        "paid" if b_state == "03_paid" else "done",
                        struct_id,
                        ver_id,
                        dept_id,
                        job_id,
                        run_id,
                        calc["gross_wage"],
                        calc["gross_wage"],
                        calc["net_wage"],
                        slip_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO hr_payslip (
                        name, state, struct_id, employee_id, version_id,
                        department_id, job_id, payslip_run_id, date_from, date_to,
                        basic_wage, gross_wage, net_wage, compute_date, company_id,
                        warning_count, error_count, create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s::date, %s::date,
                        %s, %s, %s, CURRENT_DATE, 1,
                        0, 0, 1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (
                        slip_name,
                        "paid" if b_state == "03_paid" else "done",
                        struct_id,
                        emp_id,
                        ver_id,
                        dept_id,
                        job_id,
                        run_id,
                        d_start,
                        d_end,
                        calc["gross_wage"],
                        calc["gross_wage"],
                        calc["net_wage"],
                    ),
                )
                slip_id = cur.fetchone()[0]

            latest_slip_by_reg[e["reg"]] = (slip_id, slip_number)

            # Replace payslip lines cleanly
            cur.execute("DELETE FROM hr_payslip_line WHERE slip_id = %s;", (slip_id,))
            lines = [
                (10, "Lương Cơ bản & Phụ cấp Trách nhiệm (Gross)", "BASIC", calc["gross_wage"]),
                (20, "Bảo hiểm Xã hội (BHXH 8% — ĐV TZ0857G)", "BHXH", -calc["bhxh_amount"]),
                (30, "Bảo hiểm Y tế (BHYT 1.5% — ĐV TZ0857G)", "BHYT", -calc["bhyt_amount"]),
                (40, "Bảo hiểm Thất nghiệp (BHTN 1% — ĐV TZ0857G)", "BHTN", -calc["bhtn_amount"]),
                (50, "Thuế Thu nhập Cá nhân (TNCN Lũy tiến)", "PIT", -calc["pit_amount"]),
                (100, "Thực lĩnh Chuyển khoản VCB DigiBiz (Net)", "NET", calc["net_wage"]),
            ]
            for seq, l_name, l_code, l_amt in lines:
                s_rule_id = rule_map.get(l_code) or rule_map.get("DEDUCTION") or fallback_rule_id
                cur.execute(
                    """
                    INSERT INTO hr_payslip_line (
                        sequence, slip_id, salary_rule_id, version_id, employee_id,
                        name, code, date_from, date_to, rate, amount, quantity, total, ytd,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s::date, %s::date, 100.0, %s, 1.0, %s, %s,
                        1, 1, NOW(), NOW()
                    );
                    """,
                    (seq, slip_id, s_rule_id, ver_id, emp_id, l_name, l_code, d_start, d_end, l_amt, l_amt, l_amt),
                )

    # 8. Store complete canonical snapshot in ir_config_parameter (`dgm.hr.master_registry`)
    registry_rows = []
    for e in EMPLOYEES:
        calc = compute_vn_payroll(e["gross_wage"])
        dept_info = next(d for d in DEPARTMENTS if d["code"] == e["dept_code"])
        mgr_name = next((m["name"] for m in EMPLOYEES if m["reg"] == e["manager_reg"]), "Hội đồng Quản trị DGM")
        slip_id, slip_number = latest_slip_by_reg[e["reg"]]
        registry_rows.append(
            {
                "id": emp_id_by_reg[e["reg"]],
                "version_id": version_id_by_reg[e["reg"]],
                "registration_number": e["reg"],
                "name": e["name"],
                "job_title": e["job_title"],
                "department_code": e["dept_code"],
                "department_name": dept_info["name_vi"],
                "manager_name": mgr_name,
                "work_email": e["work_email"],
                "work_phone": e["work_phone"],
                "identification_id": e["id_card_name"],
                "bank_name": e["bank_name"],
                "bank_bic": e["bank_bic"],
                "bank_branch": e["bank_branch"],
                "bank_acc_number": e["account_number"],
                "bhxh_unit": "TZ0857G (BHXH Quận 7)",
                "contract_name": "HĐLĐ Chuẩn Digimate 2026 (12 Điều)",
                "join_date": "01/01/2024",
                "gross_wage": calc["gross_wage"],
                "bhxh_amount": calc["bhxh_amount"],
                "bhyt_amount": calc["bhyt_amount"],
                "bhtn_amount": calc["bhtn_amount"],
                "total_insurance": calc["total_insurance"],
                "taxable_income": calc["taxable_income"],
                "pit_amount": calc["pit_amount"],
                "net_wage": calc["net_wage"],
                "latest_payslip_id": slip_id,
                "latest_payslip_name": slip_number,
                "latest_payslip_state": "Đã duyệt — Chuẩn VCB DigiBiz (Tháng 10/2026)",
                "documents_folder_id": hr_folder_id,
            }
        )

    upsert_config_param(
        cur,
        "dgm.hr.master_registry",
        json.dumps(
            {
                "company_name": "CÔNG TY CỔ PHẦN DIGIMATE (INNORIA)",
                "tax_id": "0318201249",
                "bhxh_unit": "TZ0857G (BHXH Quận 7)",
                "payslip_run_id": latest_run_id,
                "month_label": "Tháng 10/2026",
                "employees": registry_rows,
            },
            ensure_ascii=False,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
    print(
        f"[✓] {dbname}: Seeded {len(DEPARTMENTS)} departments, {len(EMPLOYEES)} active DGM employees "
        f"(linked admin uid=2 -> DGM-001), 8 contracts (`hr.version`), 16 payslips (`hr.payslip`), and lifecycle SOPs."
    )


def main():
    targets = sys.argv[1:] or [os.environ.get("DB_NAME", "innoria_prod")]
    for db in targets:
        seed_hr_payroll_for_db(db)


if __name__ == "__main__":
    main()
