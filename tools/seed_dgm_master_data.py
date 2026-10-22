#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotent Master Data & Governance Seeder for DGM / Innoria (`innoria_prod`).
Executes in <1s via psycopg2 on both local PostgreSQL and K8s pods.
"""
import json
import os
import sys
import psycopg2


CONFIG_PARAMS = [
    ("al2c.autonomy_enabled", "True"),
    ("dgm.autonomy_enabled", "True"),
    ("al2c.agent_daily_budget", "500"),
    ("al2c.max_discount", "10"),
    ("al2c.max_tcv", "500000000"),
    ("al2c.mail_mode", "draft_only"),
    ("insilos_al2c.timesheet_webhook_secret", "inno_al2c_timesheet_pubsub_secret_2026_prod_grade"),
]

CANONICAL_PARTNERS = [
    {
        "match_id": 592,
        "name": "CÔNG TY TNHH MTI TECHNOLOGY",
        "vat": "0314015511",
        "customer_rank": 1,
        "supplier_rank": 0,
        "country_code": "VN",
        "email": None,
        "street": "Tòa nhà Cộng Hòa Garden, 20 Đường Cộng Hòa, Phường 12, Quận Tân Bình, TP.HCM",
        "comment": "Canonical B2B IT engineering client under contract DIGIMATE2401-001 (Net 40 terms, tiered OT).",
    },
    {
        "match_id": None,
        "name": "Canva Pty Ltd",
        "vat": None,
        "customer_rank": 1,
        "supplier_rank": 0,
        "country_code": "AU",
        "email": "pub@digimate.vn",
        "street": "110 Kippax St, Surry Hills, NSW 2010, Australia",
        "comment": "Cross-border platform partner. 0% export VAT category, USD wire remittance subject to Decree 70 24h e-invoicing SLA.",
    },
    {
        "match_id": 580,
        "name": "Trung tâm Dịch vụ số MobiFone (MDS)",
        "vat": "0100686209",
        "customer_rank": 1,
        "supplier_rank": 0,
        "country_code": "VN",
        "email": None,
        "street": "Tầng 6, Tòa nhà MobiFone, Số 5, Ngõ 82, Phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, TP. Hà Nội",
        "comment": "Telecom AI CSP revenue-share partner for MobiAI service (48h customer care SLA).",
    },
    {
        "match_id": None,
        "name": "Temecula Valley Unified School District",
        "vat": None,
        "customer_rank": 1,
        "supplier_rank": 0,
        "country_code": "US",
        "email": None,
        "street": "31350 Rancho Vista Road, Temecula, CA 92592, USA",
        "comment": "California Local Education Agency client under Student Data Privacy Agreement CA-NDPA v1.5 (FERPA/COPPA 45-day privacy SLA).",
    },
    {
        "match_id": None,
        "name": "VNPT TP.HCM (Chi nhánh Tập đoàn Bưu chính Viễn thông Việt Nam)",
        "vat": "0300954529",
        "customer_rank": 0,
        "supplier_rank": 1,
        "country_code": "VN",
        "email": None,
        "street": "125 Hai Bà Trưng, Phường Sài Gòn, TP.HCM",
        "comment": "High-speed optical internet provider under contract HDHCM1684072614 (14-month prepaid bundle 1K26TKA-338235 amortized via TK 242).",
    },
    {
        "match_id": None,
        "name": "Viettel-CA (Viettel TP.HCM - Chi nhánh Tập đoàn Công nghiệp - Viễn thông Quân đội)",
        "vat": "0100109106-122",
        "customer_rank": 0,
        "supplier_rank": 1,
        "country_code": "VN",
        "email": None,
        "street": "Số 285 Đường Cách Mạng Tháng Tám, Phường 12, Quận 10, TP.HCM",
        "comment": "Statutory digital signature authority & SInvoice provider (36-month CTS combo 1K23TVA-2368750 amortized via TK 242).",
    },
    {
        "match_id": None,
        "name": "CÔNG TY CỔ PHẦN AIFIN COMPANY GLOBAL",
        "vat": "0319631994",
        "customer_rank": 1,
        "supplier_rank": 0,
        "country_code": "VN",
        "email": "huy.nguyen@aifin.com.vn",
        "street": "51-53 Võ Văn Tần, Phường Xuân Hòa, Thành Phố Hồ Chí Minh, Việt Nam",
        "comment": "Strategic B2B Staff Augmentation Client under DIGIMATE-AIFIN-VN_2610-001 (Senior SWE Trần Văn Huỳnh Phố, 350,000 VND/hr - 56,000,000 VND/month, Net 40) & 360-Sales Platform Contract AIFIN-DIGIMATE/360-SALES/2026 (200,000,000 VND).",
    },
]

CANONICAL_EMPLOYEES = [
    {
        "reg": "DGM-001",
        "match_id": 63,
        "name": "Lê Xuân Hoàng",
        "aliases": ["Lê Xuân Hoàng"],
        "id_card_name": "089094016917",
        "job_title": "Chủ tịch HĐQT & Tổng Giám đốc",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "account_number": "1373068161",
    },
    {
        "reg": "DGM-002",
        "match_id": 55,
        "name": "Nguyễn Hoài Ân",
        "aliases": ["Nguyễn Hoài Ân"],
        "id_card_name": "096095006609",
        "job_title": "Cổ đông sáng lập & CTO",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "account_number": "1901014028",
    },
    {
        "reg": "DGM-003",
        "match_id": 60,
        "name": "Mai Thị Hồng Thắm",
        "aliases": ["Mai Thị Hồng Thắm"],
        "id_card_name": "093197003049",
        "job_title": "Cổ đông sáng lập & CFO/HR Lead",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "account_number": "0111000287863",
    },
    {
        "reg": "DGM-004",
        "match_id": 73,
        "name": "Bùi Hữu Tài",
        "aliases": ["Bùi Hữu Tài", "Bùi Hửu Tài", "Tài Bùi", "BUI HUU TAI"],
        "id_card_name": "094094005852",
        "job_title": "Kỹ sư Phần mềm Senior (MTI Onsite)",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "account_number": "1045246615",
    },
    {
        "reg": "DGM-005",
        "match_id": 69,
        "name": "Huỳnh Trần Quang Khánh",
        "aliases": ["Huỳnh Trần Quang Khánh", "Khánh Huỳnh", "HUYNH TRAN QUANG KHANH"],
        "id_card_name": "089085004243",
        "job_title": "Kỹ sư Phần mềm Senior / Tech Lead",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "account_number": "12154887",
    },
    {
        "reg": "DGM-006",
        "match_id": 57,
        "name": "Ngô Thành Lộc",
        "aliases": ["Ngô Thành Lộc", "Ngô Thanh Lộc", "Lộc Ngô", "NGO THANH LOC"],
        "id_card_name": "086091003038",
        "job_title": "Kỹ sư Phần mềm Senior (MTI Onsite)",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "account_number": "12154937",
    },
    {
        "reg": "DGM-007",
        "match_id": 62,
        "name": "Lê Cao Bảo Phúc",
        "aliases": ["Lê Cao Bảo Phúc", "Phúc Lê", "LE CAO BAO PHUC"],
        "id_card_name": "089095016227",
        "job_title": "Kỹ sư Phần mềm (MTI Onsite)",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "account_number": "12154917",
    },
    {
        "reg": "DGM-008",
        "match_id": None,
        "name": "Thái Nguyễn Đăng Khoa",
        "aliases": ["Thái Nguyễn Đăng Khoa", "Khoa Thái", "THAI NGUYEN DANG KHOA"],
        "id_card_name": "079203037187",
        "job_title": "Kỹ sư Phần mềm / Junior Developer",
        "bank_name": "ACB",
        "bank_bic": "ASCBVNVX",
        "account_number": "47070467",
    },
    {
        "reg": "DGM-009",
        "match_id": 86,
        "name": "Trần Văn Huỳnh Phố",
        "aliases": ["Trần Văn Huỳnh Phố", "Trần Văn Huỳnh Phố Phố", "TRAN VAN HUYNH PHO"],
        "id_card_name": "083201003426",
        "job_title": "Kỹ sư Phần mềm Senior (AIfin Onsite)",
        "bank_name": "VIETCOMBANK",
        "bank_bic": "BFTVVNVX",
        "account_number": "1045289901",
    },
]

CANONICAL_CRONS = [
    {
        "name": "DGM Autonomous Document Triage & Multipage Split Watchdog",
        "model": "documents.document",
        "code": "model.cron_dgm_document_triage_split()",
        "interval_number": 1,
        "interval_type": "hours",
    },
    {
        "name": "DGM Autonomous Legal Entity & 24h Export E-Invoice SLA Watchdog",
        "model": "al2c.compliance.scanner",
        "code": "model.cron_dgm_legal_entity_sla_watchdog()",
        "interval_number": 1,
        "interval_type": "hours",
    },
    {
        "name": "DGM Autonomous BHXH (TZ0857G) Zero-Arrears & Prepaid TK 242 Watchdog",
        "model": "al2c.compliance.scanner",
        "code": "model.cron_dgm_bhxh_tk242_watchdog()",
        "interval_number": 1,
        "interval_type": "days",
    },
]


def get_connection():
    dbname = os.environ.get("DB_NAME", "innoria_prod")
    user = os.environ.get("DB_USER", "odoo")
    password = os.environ.get("PGPASSWORD")
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "5434"))
    kwargs = dict(dbname=dbname, user=user, host=host, port=port)
    if password:
        kwargs["password"] = password
    return psycopg2.connect(**kwargs)


def seed_master_data():
    conn = get_connection()
    cur = conn.cursor()

    # 1. ir_config_parameter
    for key, val in CONFIG_PARAMS:
        cur.execute("SELECT id FROM ir_config_parameter WHERE key = %s;", (key,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE ir_config_parameter SET value = %s, write_uid = 1, write_date = NOW() WHERE id = %s;",
                (val, row[0]),
            )
        else:
            cur.execute(
                """
                INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 1, 1, NOW(), NOW());
                """,
                (key, val),
            )

    # Resolve countries
    cur.execute("SELECT code, id FROM res_country WHERE code IN ('VN', 'AU', 'US');")
    countries = dict(cur.fetchall())

    # 2. 6 Canonical B2B/Platform Partners
    partner_ids = []
    for p in CANONICAL_PARTNERS:
        country_id = countries.get(p["country_code"])
        pid = None
        if p["vat"]:
            cur.execute("SELECT id FROM party_master WHERE vat = %s ORDER BY id LIMIT 1;", (p["vat"],))
            r = cur.fetchone()
            if r:
                pid = r[0]
        if not pid:
            cur.execute("SELECT id FROM party_master WHERE LOWER(TRIM(name)) = LOWER(%s) ORDER BY id LIMIT 1;", (p["name"],))
            r = cur.fetchone()
            if r:
                pid = r[0]
        if not pid and p["match_id"]:
            cur.execute("SELECT id FROM party_master WHERE id = %s;", (p["match_id"],))
            r = cur.fetchone()
            if r:
                pid = r[0]

        if pid:
            cur.execute(
                """
                UPDATE party_master
                   SET name = %s,
                       complete_name = %s,
                       commercial_company_name = %s,
                       commercial_partner_id = %s,
                       vat = %s,
                       customer_rank = %s,
                       supplier_rank = %s,
                       country_id = %s,
                       email = COALESCE(%s, email),
                       email_normalized = COALESCE(%s, email_normalized),
                       street = %s,
                       comment = %s,
                       is_company = TRUE,
                       active = TRUE,
                       partner_share = TRUE,
                       company_id = 1,
                       type = 'contact',
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (
                    p["name"],
                    p["name"],
                    p["name"],
                    pid,
                    p["vat"],
                    p["customer_rank"],
                    p["supplier_rank"],
                    country_id,
                    p["email"],
                    p["email"],
                    p["street"],
                    p["comment"],
                    pid,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO party_master (
                    name, complete_name, commercial_company_name, vat,
                    customer_rank, supplier_rank, country_id, email, email_normalized,
                    street, comment, is_company, active, partner_share, company_id,
                    type, autopost_bills, group_rfq, group_on, create_uid, write_uid,
                    create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, TRUE, TRUE, TRUE, 1,
                    'contact', 'ask', 'default', 'default', 1, 1,
                    NOW(), NOW()
                ) RETURNING id;
                """,
                (
                    p["name"],
                    p["name"],
                    p["name"],
                    p["vat"],
                    p["customer_rank"],
                    p["supplier_rank"],
                    country_id,
                    p["email"],
                    p["email"],
                    p["street"],
                    p["comment"],
                ),
            )
            pid = cur.fetchone()[0]
            cur.execute("UPDATE party_master SET commercial_partner_id = %s WHERE id = %s;", (pid, pid))
        partner_ids.append(pid)

    # 3. 8 Canonical DGM Employees + Work Contacts + Bank Accounts
    vn_id = countries.get("VN", 241)
    emp_ids = []
    for e in CANONICAL_EMPLOYEES:
        emp_id = None
        cur.execute(
            """
            SELECT id, work_contact_id, resource_id, current_version_id
              FROM hr_employee
             WHERE registration_number = %s
                OR barcode = %s
                OR TRIM(name) = ANY(%s)
             ORDER BY active DESC, id ASC
             LIMIT 1;
            """,
            (e["reg"], e["reg"], e["aliases"]),
        )
        r = cur.fetchone()
        if r:
            emp_id, work_contact_id, resource_id, current_version_id = r
        elif e["match_id"]:
            cur.execute(
                "SELECT id, work_contact_id, resource_id, current_version_id FROM hr_employee WHERE id = %s;",
                (e["match_id"],),
            )
            r = cur.fetchone()
            if r:
                emp_id, work_contact_id, resource_id, current_version_id = r
            else:
                work_contact_id = None
                resource_id = None
                current_version_id = None
        else:
            work_contact_id = None
            resource_id = None
            current_version_id = None

        # Ensure work_contact_id exists in party_master
        if work_contact_id:
            cur.execute(
                """
                UPDATE party_master
                   SET name = %s,
                       complete_name = %s,
                       is_company = FALSE,
                       active = TRUE,
                       employee = TRUE,
                       company_id = 1,
                       country_id = COALESCE(country_id, %s),
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (e["name"], e["name"], vn_id, work_contact_id),
            )
        else:
            cur.execute(
                """
                SELECT id FROM party_master
                 WHERE is_company = FALSE AND TRIM(name) = ANY(%s)
                 ORDER BY id LIMIT 1;
                """,
                (e["aliases"],),
            )
            r = cur.fetchone()
            if r:
                work_contact_id = r[0]
                cur.execute(
                    """
                    UPDATE party_master
                       SET name = %s,
                           complete_name = %s,
                           active = TRUE,
                           employee = TRUE,
                           company_id = 1,
                           write_uid = 1,
                           write_date = NOW()
                     WHERE id = %s;
                    """,
                    (e["name"], e["name"], work_contact_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO party_master (
                        name, complete_name, is_company, active, employee, partner_share,
                        company_id, country_id, type, autopost_bills, group_rfq, group_on,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, %s, FALSE, TRUE, TRUE, FALSE,
                        1, %s, 'contact', 'ask', 'default', 'default',
                        1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (e["name"], e["name"], vn_id),
                )
                work_contact_id = cur.fetchone()[0]
                cur.execute(
                    "UPDATE party_master SET commercial_partner_id = %s WHERE id = %s;",
                    (work_contact_id, work_contact_id),
                )

        # Ensure resource_resource exists
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

        # Insert or update hr_employee
        if emp_id:
            cur.execute(
                """
                UPDATE hr_employee
                   SET name = %s,
                       legal_name = %s,
                       registration_number = %s,
                       barcode = %s,
                       id_card_name = %s,
                       work_contact_id = %s,
                       resource_id = %s,
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
                    work_contact_id,
                    resource_id,
                    emp_id,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO hr_employee (
                    name, legal_name, registration_number, barcode, id_card_name,
                    work_contact_id, resource_id, company_id, active, color,
                    birthday_public_display, work_permit_scheduled_activity, is_flexible,
                    structure_type_id, create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, 1, TRUE, 0,
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
                    work_contact_id,
                    resource_id,
                ),
            )
            emp_id = cur.fetchone()[0]

        # Ensure hr_version exists and has job_title + identification_id
        if current_version_id:
            cur.execute(
                """
                UPDATE hr_version
                   SET job_title = %s,
                       identification_id = COALESCE(NULLIF(%s, ''), identification_id),
                       active = TRUE,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (e["job_title"], e["id_card_name"], current_version_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO hr_version (
                    company_id, employee_id, last_modified_uid, private_country_id,
                    km_home_work, address_id, work_location_id, resource_calendar_id,
                    structure_type_id, hr_responsible_id, create_uid, write_uid,
                    distance_home_work_unit, marital, tz, date_version,
                    job_title, identification_id, active, is_custom_job_title,
                    last_modified_date, create_date, write_date, attendance_based,
                    work_entry_source, standard_calendar_id, employee_type,
                    schedule_pay, wage_type, work_time_rate, overtime_from_attendance,
                    l10n_us_filing_status, l10n_us_pre_retirement_type,
                    l10n_us_pre_retirement_matching_type, l10n_us_post_roth_401k_type,
                    l10n_us_pre_retirement_matching_yearly_cap
                ) VALUES (
                    1, %s, 1, %s,
                    0, 1, 1, 1,
                    1, 1, 1, 1,
                    'kilometers', 'single', 'Asia/Ho_Chi_Minh', CURRENT_DATE,
                    %s, NULLIF(%s, ''), TRUE, TRUE,
                    NOW(), NOW(), NOW(), FALSE,
                    'calendar', 1, 'employee',
                    'monthly', 'monthly', 1.0, FALSE,
                    'single', 'percent',
                    'percent', 'percent',
                    100.0
                ) RETURNING id;
                """,
                (emp_id, vn_id, e["job_title"], e["id_card_name"]),
            )
            current_version_id = cur.fetchone()[0]
            cur.execute(
                "UPDATE hr_employee SET current_version_id = %s WHERE id = %s;",
                (current_version_id, emp_id),
            )

        # Upsert res_partner_bank
        stk = e["account_number"].strip()
        cur.execute(
            """
            SELECT id FROM res_partner_bank
             WHERE sanitized_account_number = %s AND partner_id = %s
             LIMIT 1;
            """,
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
                    partner_id, clearing_label_id, account_number, sanitized_account_number,
                    holder_name, bank_name, bank_bic, company_id, country_id,
                    active, allow_out_payment, l10n_us_bank_account_type,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, 1, %s, %s,
                    %s, %s, %s, 1, %s,
                    TRUE, TRUE, 'checking',
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (work_contact_id, stk, stk, e["name"], e["bank_name"], e["bank_bic"], vn_id),
            )
            bank_id = cur.fetchone()[0]

        # Link employee <-> bank account
        cur.execute(
            """
            INSERT INTO employee_bank_account_rel (employee_id, bank_account_id)
            VALUES (%s, %s)
            ON CONFLICT (employee_id, bank_account_id) DO NOTHING;
            """,
            (emp_id, bank_id),
        )
        emp_ids.append(emp_id)

    # 4. 3 DGM Autonomous Watchdog Crons
    cur.execute("SELECT id FROM ir_model WHERE model = 'al2c.compliance.scanner' LIMIT 1;")
    scanner_model = cur.fetchone()
    if not scanner_model:
        cur.execute(
            """
            INSERT INTO ir_model (model, "order", state, name, transient, create_uid, write_uid, create_date, write_date)
            VALUES ('al2c.compliance.scanner', 'id', 'base', '{"en_US": "AL2C Compliance Scanner"}'::jsonb, TRUE, 1, 1, NOW(), NOW())
            RETURNING id;
            """
        )
        scanner_model_id = cur.fetchone()[0]
    else:
        scanner_model_id = scanner_model[0]

    cur.execute("SELECT id FROM ir_model WHERE model = 'documents.document' LIMIT 1;")
    doc_model_id = cur.fetchone()[0]
    model_map = {
        "documents.document": doc_model_id,
        "al2c.compliance.scanner": scanner_model_id,
    }

    cron_ids = []
    for c in CANONICAL_CRONS:
        mid = model_map[c["model"]]
        cur.execute(
            "SELECT id, ir_actions_server_id FROM ir_cron WHERE cron_name = %s LIMIT 1;",
            (c["name"],),
        )
        crow = cur.fetchone()
        if crow:
            cid, act_id = crow
            cur.execute(
                """
                UPDATE ir_act_server
                   SET name = %s::jsonb,
                       model_id = %s,
                       state = 'code',
                       usage = 'ir_cron',
                       code = %s,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (json.dumps({"en_US": c["name"]}), mid, c["code"], act_id),
            )
            cur.execute(
                """
                UPDATE ir_cron
                   SET active = TRUE,
                       interval_number = %s,
                       interval_type = %s,
                       user_id = 1,
                       write_uid = 1,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (c["interval_number"], c["interval_type"], cid),
            )
        else:
            cur.execute(
                """
                INSERT INTO ir_act_server (
                    type, binding_type, name, model_id, usage, state, code,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    'ir.actions.server', 'action', %s::jsonb, %s, 'ir_cron', 'code', %s,
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (json.dumps({"en_US": c["name"]}), mid, c["code"]),
            )
            act_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO ir_cron (
                    ir_actions_server_id, user_id, interval_number, interval_type,
                    priority, active, cron_name, nextcall,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, 1, %s, %s,
                    5, TRUE, %s, NOW(),
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (act_id, c["interval_number"], c["interval_type"], c["name"]),
            )
            cid = cur.fetchone()[0]
        cron_ids.append(cid)

    conn.commit()

    # Verification summary
    cur.execute(
        "SELECT key, value FROM ir_config_parameter WHERE key = ANY(%s) ORDER BY key;",
        ([k for k, _ in CONFIG_PARAMS],),
    )
    params_out = cur.fetchall()

    cur.execute(
        "SELECT id, name, vat, customer_rank, supplier_rank, is_company FROM res_partner WHERE id = ANY(%s) ORDER BY id;",
        (partner_ids,),
    )
    partners_out = cur.fetchall()

    cur.execute(
        """
        SELECT e.id, e.registration_number, e.barcode, e.name, e.legal_name,
               e.id_card_name, v.job_title, e.work_contact_id,
               b.bank_name, b.bank_bic, b.account_number
          FROM hr_employee e
          LEFT JOIN hr_version v ON v.id = e.current_version_id
          LEFT JOIN employee_bank_account_rel rel ON rel.employee_id = e.id
          LEFT JOIN res_partner_bank b ON b.id = rel.bank_account_id
         WHERE e.id = ANY(%s)
         ORDER BY e.registration_number;
        """,
        (emp_ids,),
    )
    emps_out = cur.fetchall()

    cur.execute(
        "SELECT id, cron_name, interval_number, interval_type, active FROM ir_cron WHERE id = ANY(%s) ORDER BY id;",
        (cron_ids,),
    )
    crons_out = cur.fetchall()

    print(f"=== DGM MASTER DATA SEED SUMMARY ({os.environ.get('DB_HOST', '127.0.0.1')}:{os.environ.get('DB_PORT', '5434')}/{os.environ.get('DB_NAME', 'innoria_prod')}) ===")
    print(f"[1] ir_config_parameter ({len(params_out)}/7):")
    for r in params_out:
        print("   ", r)
    print(f"[2] Canonical res_partner ({len(partners_out)}/6):")
    for r in partners_out:
        print("   ", r)
    print(f"[3] Canonical hr_employee + bank ({len(emps_out)}/8):")
    for r in emps_out:
        print("   ", r)
    print(f"[4] Canonical DGM ir_cron ({len(crons_out)}/3):")
    for r in crons_out:
        print("   ", r)

    cur.close()
    conn.close()

    try:
        from seed_dgm_partner_onboarding import seed_partner_onboarding
        seed_partner_onboarding(os.environ.get("DB_NAME", "innoria_prod"))
    except Exception as exc:
        print(f"[WARN] seed_partner_onboarding hook skipped: {exc}")


if __name__ == "__main__":
    seed_master_data()

