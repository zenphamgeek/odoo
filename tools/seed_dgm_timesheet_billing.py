#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP-DGM-08 Idempotent End-to-End Post-Onboarding Delivery-to-Cash Seeder:
- Initializes schema, ACLs, views, and Sovereign bridges for `dgm.project.notification`,
  `dgm.project.timesheet.sheet`, `dgm.project.timesheet.line`, and `account.move`.
- Seeds Knowledge Article `SOP-DGM-08: Quy trình Thông báo Dự án, Chấm công Timesheet,
  Khách hàng Nghiệm thu & Xuất Hóa đơn Nháp / Chính thức (Chuẩn MTI & AIfin)`
  under DGM Knowledge Root (`insilos_al2c.kb_dgm_sop_08_timesheet_billing`).
- Seeds & executes the full 5-stage pipeline for MTI Technology (`PTN-DGM-2026-0001`,
  `PRJ-NTF-202610-0001`, `TS-DGM-202610-0001`, 4 engineers DGM-004..007, 250M/270M VND)
  and AIfin (`PTN-DGM-2026-0007`, `PRJ-NTF-202610-0002`, `TS-DGM-202610-0002`,
  engineer Trần Văn Huỳnh Phố DGM-009, 35M/37.8M VND).
- Enforces the Zero Empty Folders Invariant across `documents_document`.
"""
import configparser
import os
import site
import sys
import types
import psycopg2

ROOT_DIR = "/app/insilos" if os.path.isdir("/app/insilos") else "/home/zen/O20"
VENV_SITE = os.path.join(ROOT_DIR, ".venv/lib/python3.12/site-packages")
if os.path.isdir(VENV_SITE):
    site.addsitedir(VENV_SITE)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    import xmlsec  # noqa: F401
except Exception:
    sys.modules["xmlsec"] = types.ModuleType("xmlsec")

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.tools.convert import convert_file


def get_pg_conn(dbname):
    cfg = configparser.ConfigParser()
    conf_path = os.path.join(ROOT_DIR, "odoo.conf")
    if os.path.exists(conf_path):
        cfg.read(conf_path)
    opts = cfg["options"] if "options" in cfg else {}
    return psycopg2.connect(
        dbname=dbname,
        user=os.environ.get("DB_USER", opts.get("db_user", "odoo")),
        password=os.environ.get("PGPASSWORD", opts.get("db_password", "odoo")),
        host=os.environ.get("DB_HOST", opts.get("db_host", "127.0.0.1")),
        port=int(os.environ.get("DB_PORT", opts.get("db_port", "5434"))),
    )


def ensure_pre_registry_columns(dbname):
    """Ensures `finance_journal_entry` / `account_move` has all SOP-DGM-08 columns
    before `Registry.new(dbname)` initializes compatibility views."""
    conn = get_pg_conn(dbname)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'finance_journal_entry';
        """
    )
    row = cur.fetchone()
    base_move_table = "finance_journal_entry" if (row and row[0] == "BASE TABLE") else "account_move"

    move_cols = [
        ("dgm_timesheet_sheet_id", "INTEGER"),
        ("dgm_invoice_stage", "VARCHAR DEFAULT 'draft_internal'"),
        ("dgm_draft_confirmed_by", "VARCHAR"),
        ("dgm_draft_confirmed_at", "TIMESTAMP WITHOUT TIME ZONE"),
        ("dgm_einvoice_symbol", "VARCHAR DEFAULT '1C26TAA'"),
        ("dgm_einvoice_number", "VARCHAR"),
        ("dgm_einvoice_issued_at", "TIMESTAMP WITHOUT TIME ZONE"),
        ("dgm_einvoice_lookup_code", "VARCHAR"),
    ]
    for col, col_def in move_cols:
        cur.execute("SAVEPOINT sp_move_col;")
        try:
            cur.execute(f"ALTER TABLE public.{base_move_table} ADD COLUMN IF NOT EXISTS {col} {col_def};")
            cur.execute("RELEASE SAVEPOINT sp_move_col;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_move_col;")

    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'account_move';
        """
    )
    am_row = cur.fetchone()
    if am_row and am_row[0] == "VIEW" and base_move_table == "finance_journal_entry":
        cur.execute("SAVEPOINT sp_am_view;")
        try:
            cur.execute("CREATE OR REPLACE VIEW public.account_move AS SELECT * FROM public.finance_journal_entry;")
            cur.execute("RELEASE SAVEPOINT sp_am_view;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_am_view;")

    conn.commit()
    cur.close()
    conn.close()


def seed_sop_dgm_08_knowledge_article(cr):
    """Seeds or updates Knowledge Article `SOP-DGM-08` under DGM SOP Root (`ID 170` or by name)
    and registers `insilos_al2c.kb_dgm_sop_08_timesheet_billing` in `ir_model_data`."""
    sop08_title = (
        "SOP-DGM-08: Quy trình Thông báo Dự án, Chấm công Timesheet, Khách hàng Nghiệm thu "
        "& Xuất Hóa đơn Nháp / Chính thức (Chuẩn MTI & AIfin)"
    )
    sop08_body = """<div class="o_knowledge_behavior_anchor dgm-sop-container">
<h1>SOP-DGM-08: QUY TRÌNH THÔNG BÁO DỰ ÁN, CHẤM CÔNG TIMESHEET, KHÁCH HÀNG NGHIỆM THU &amp; XUẤT HÓA ĐƠN NHÁP / CHÍNH THỨC (CHUẨN MTI &amp; AIFIN)</h1>
<p><strong>Mã quy trình:</strong> <code>SOP-DGM-08</code> | <strong>Phiên bản:</strong> 2.0 (10/2026) | <strong>Pháp nhân áp dụng:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: <code>0317958465</code>)</p>
<p><strong>Phạm vi:</strong> Chuỗi vận hành khép kín sau On-boarding Đối tác (<code>SOP-DGM-06</code>) và Ký Hợp đồng Biệt phái Nhân sự / Phát triển Phần mềm (<code>SOP-DGM-07</code>), áp dụng chuẩn đối soát 2 bước của <strong>MTI Technology</strong> (<code>PTN-DGM-2026-0001</code>) và <strong>AIfin Company Global</strong> (<code>PTN-DGM-2026-0007</code>).</p>
<hr/>
<h2>Stage 1: Thông báo Khởi động Dự án &amp; Bàn giao Nhân sự Kỹ thuật (Project Kickoff &amp; Personnel Dispatch — <code>dgm.project.notification</code>)</h2>
<ul>
  <li><strong>Mã định danh:</strong> <code>PRJ-NTF-202610-XXXX</code> (Model: <code>dgm.project.notification</code>).</li>
  <li><strong>Cơ chế vận hành:</strong> Ngay sau khi Đối tác hoàn tất On-boarding (hoặc ở chế độ <em>Provisional Sales Unblocked</em>) và xác nhận Sale Order / Project, PM phát hành Thông báo Khởi động Dự án &amp; Quyết định Biệt phái Kỹ sư (<code>notification_type='kickoff_handover'</code>).</li>
  <li><strong>Lưu trữ tự động:</strong> Hệ thống sinh chứng từ HTML song ngữ và lưu trực tiếp vào thư mục Hồ sơ Thương mại của Đối tác trên <strong>Documents</strong> (<code>owner_id=False</code>, <code>access_internal='edit'</code>).</li>
</ul>
<h2>Stage 2: Tập hợp Bảng Chấm công Dự án Cuối kỳ (Monthly Project Timesheet Consolidation — <code>dgm.project.timesheet.sheet</code>)</h2>
<ul>
  <li><strong>Mã định danh:</strong> <code>TS-DGM-202610-XXXX</code> (Model: <code>dgm.project.timesheet.sheet</code> &amp; <code>dgm.project.timesheet.line</code>).</li>
  <li><strong>Đồng bộ dữ liệu:</strong> Hàm <code>action_sync_from_project_timesheets()</code> tự động tổng hợp dữ liệu giờ công từ <code>account.analytic.line</code> (và <code>al2c.timesheet.staging</code>) theo từng Kỹ sư, quy đổi ngày công chuẩn (<code>22.0 ngày/tháng</code>), giờ làm thêm (OT) và tính thành tiền theo đơn giá hợp đồng (Pro-rata).</li>
  <li><strong>Hồ sơ phát sinh:</strong> Khi PM bấm <code>action_submit_for_customer_approval()</code>, hệ thống tạo chứng từ <code>01_Bang_Cham_Cong_Timesheet_&lt;PartnerCode&gt;_&lt;Period&gt;.html</code> (<code>timesheet_doc_id</code>) và gửi thông báo <code>customer_approval_req</code> kèm đường dẫn Portal bảo mật.</li>
</ul>
<h2>Stage 3: Khách hàng Phê duyệt Timesheet &amp; Cấp Chứng thư Nghiệm thu Điện tử (Customer Timesheet Approval &amp; Digital Acceptance Certificate)</h2>
<ul>
  <li><strong>Cổng Phê duyệt Trực tuyến (Portal):</strong> <code>/insilos/timesheet_approval/&lt;sheet_id&gt;/&lt;token&gt;</code> bảo vệ bằng thuật toán so sánh hằng thời gian <code>hmac.compare_digest</code> chống tấn công timing attack và <code>readonly=False</code> trên toàn bộ route ghi dữ liệu.</li>
  <li><strong>Luồng Yêu cầu Điều chỉnh (Revision Loop):</strong> Nếu Khách hàng phản hồi điều chỉnh (<code>action_request_revision</code>), phiếu chuyển về trạng thái <code>revision_requested</code> để PM cập nhật và gửi lại.</li>
  <li><strong>Chữ ký Băm SHA-256 &amp; Biên bản Nghiệm thu:</strong> Khi Khách hàng phê duyệt (<code>action_customer_approve</code>), hệ thống ghi nhận chữ ký băm <code>customer_signature_hash</code> (SHA-256 64 ký tự hex), cập nhật <code>qty_delivered</code> trên Sale Order và sinh <code>02_Bien_Ban_Nghiem_Thu_Timesheet_&lt;PartnerCode&gt;_&lt;Period&gt;.html</code> (<code>acceptance_doc_id</code>).</li>
</ul>
<h2>Stage 4: Quy trình Xuất Hóa đơn 2 Bước Chuẩn MTI — Hóa đơn Nháp Đối soát &amp; Hóa đơn GTGT Chính thức (MTI-Style Two-Stage Invoicing)</h2>
<ul>
  <li><strong>Chốt chặn Kiểm soát (Fail-Closed Guardrail):</strong> Hệ thống <strong>NGHIÊM CẤM</strong> tạo Hóa đơn Nháp (<code>action_generate_mti_draft_invoice</code> raises <code>UserError</code>) nếu Bảng chấm công chưa ở trạng thái <code>customer_approved</code>.</li>
  <li><strong>Bước 4A — Hóa đơn Nháp Đối soát (Draft Invoice Reconciliation):</strong> Tạo bút toán <code>account.move</code> (<code>dgm_invoice_stage='draft_reconciliation'</code>) và xuất bản xem trước <code>03_Hoa_Don_Nhap_Doi_Soat_&lt;PartnerCode&gt;_&lt;Period&gt;.html</code> (<code>draft_invoice_doc_id</code>) có đóng dấu mờ để Kế toán Khách hàng kiểm tra Mã số thuế, tên pháp nhân, diễn giải dòng hàng và thuế suất GTGT 8% (Nghị định 174/2025/NĐ-CP).</li>
  <li><strong>Bước 4B — Phát hành Hóa đơn GTGT Điện tử Chính thức (Official VAT E-Invoice <code>1C26TAA</code>):</strong> Sau khi Khách hàng xác nhận Hóa đơn Nháp (<code>action_confirm_draft_and_issue_official_invoice</code>), hệ thống vào sổ <code>account.move</code> (<code>dgm_invoice_stage='official_issued'</code>), cấp ký hiệu <code>1C26TAA</code>, số hóa đơn 8 chữ số và mã tra cứu HĐĐT, đồng thời lưu trữ <code>04_Hoa_Don_Chinh_Thuc_VAT_&lt;PartnerCode&gt;_&lt;Period&gt;.html</code> (<code>official_invoice_doc_id</code>) vào cả <strong>Hồ sơ Đối tác</strong> lẫn thư mục <strong><code>02. Tài chính - Kế toán - Thuế</code> &rarr; <code>Hoá đơn đầu ra</code></strong>.</li>
</ul>
</div>"""

    cr.execute(
        "SELECT id FROM knowledge_article WHERE id = 170 OR name ILIKE 'DGM · Quy Trình Vận Hành Chuẩn%' ORDER BY (id = 170) DESC, id ASC LIMIT 1;"
    )
    root_row = cr.fetchone()
    root_kb_id = root_row[0] if root_row else None

    cr.execute("SELECT id FROM knowledge_article WHERE name ILIKE 'SOP-DGM-08%' ORDER BY id ASC LIMIT 1;")
    kb_row = cr.fetchone()
    if kb_row:
        kb08_id = kb_row[0]
        cr.execute(
            """
            UPDATE knowledge_article
               SET name = %s,
                   icon = '🧾',
                   body = %s,
                   parent_id = COALESCE(%s, parent_id),
                   root_article_id = COALESCE(%s, root_article_id),
                   internal_permission = 'write',
                   category = 'workspace',
                   is_article_visible_by_everyone = TRUE,
                   active = TRUE,
                   write_date = NOW()
             WHERE id = %s;
            """,
            (sop08_title, sop08_body, root_kb_id, root_kb_id, kb08_id),
        )
    else:
        cr.execute(
            """
            INSERT INTO knowledge_article (
                name, icon, body, parent_id, root_article_id,
                internal_permission, category, sequence, active,
                is_article_visible_by_everyone, create_uid, write_uid, create_date, write_date
            ) VALUES (
                %s, '🧾', %s, %s, %s,
                'write', 'workspace', 160, TRUE,
                TRUE, 1, 1, NOW(), NOW()
            ) RETURNING id;
            """,
            (sop08_title, sop08_body, root_kb_id, root_kb_id),
        )
        kb08_id = cr.fetchone()[0]

    cr.execute(
        "SELECT id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = 'kb_dgm_sop_08_timesheet_billing' LIMIT 1;"
    )
    imd_row = cr.fetchone()
    if imd_row:
        cr.execute(
            "UPDATE ir_model_data SET model = 'knowledge.article', res_id = %s, write_date = NOW() WHERE id = %s;",
            (kb08_id, imd_row[0]),
        )
    else:
        cr.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
            VALUES ('insilos_al2c', 'kb_dgm_sop_08_timesheet_billing', 'knowledge.article', %s, FALSE, 1, 1, NOW(), NOW());
            """,
            (kb08_id,),
        )
    return kb08_id


def _ensure_employee(env, code, name, job_title):
    Employee = env["hr.employee"].sudo()
    emp = Employee.search(
        ["|", ("registration_number", "=", code), ("name", "ilike", name)],
        order="id asc",
        limit=1,
    )
    if not emp:
        emp = Employee.create({
            "name": name,
            "registration_number": code,
            "company_id": 1,
            "active": True,
        })
    else:
        env.cr.execute(
            """
            UPDATE hr_employee
               SET registration_number = %s,
                   active = TRUE,
                   write_date = NOW()
             WHERE id = %s;
            """,
            (code, emp.id),
        )
    return emp


def _ensure_analytic_timesheet_line(cr, project, task, employee, date_str, hours, description, partner_id, so_id=None):
    """Idempotently upserts an `account.analytic.line` row for the given project & employee in October 2026."""
    cr.execute(
        """
        SELECT id FROM account_analytic_line
         WHERE project_id = %s AND employee_id = %s
           AND date >= '2026-10-01' AND date <= '2026-10-31'
         ORDER BY id ASC LIMIT 1;
        """,
        (project.id, employee.id),
    )
    row = cr.fetchone()
    account_id = project.account_id.id if getattr(project, "account_id", False) else None
    if not account_id:
        cr.execute("SELECT id FROM account_analytic_account WHERE active = TRUE ORDER BY id ASC LIMIT 1;")
        acc_row = cr.fetchone()
        account_id = acc_row[0] if acc_row else None

    if row:
        line_id = row[0]
        cr.execute(
            """
            UPDATE account_analytic_line
               SET name = %s,
                   date = %s,
                   unit_amount = %s,
                   task_id = COALESCE(%s, task_id),
                   partner_id = %s,
                   order_id = COALESCE(%s, order_id),
                   account_id = COALESCE(%s, account_id),
                   write_date = NOW()
             WHERE id = %s;
            """,
            (description, date_str, hours, task.id if task else None, partner_id, so_id, account_id, line_id),
        )
        # Remove any extra duplicate analytic lines for the same employee & project in 10/2026
        cr.execute(
            """
            DELETE FROM account_analytic_line
             WHERE project_id = %s AND employee_id = %s
               AND date >= '2026-10-01' AND date <= '2026-10-31'
               AND id != %s;
            """,
            (project.id, employee.id, line_id),
        )
        return line_id
    else:
        cr.execute(
            """
            INSERT INTO account_analytic_line (
                name, date, amount, unit_amount, project_id, task_id,
                employee_id, partner_id, order_id, account_id,
                company_id, user_id, create_uid, write_uid, create_date, write_date
            ) VALUES (
                %s, %s, 0.0, %s, %s, %s,
                %s, %s, %s, %s,
                1, 2, 1, 1, NOW(), NOW()
            ) RETURNING id;
            """,
            (description, date_str, hours, project.id, task.id if task else None, employee.id, partner_id, so_id, account_id),
        )
        return cr.fetchone()[0]


def _ensure_mti_sale_order(cr, mti_partner_id, mti_project_id):
    """Ensures MTI Technology's Sale Order `S01504` (`MTI-DIGIMATE-TS-2026-09`) exists and links to MTI's project."""
    cr.execute(
        "SELECT table_type FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'order_header';"
    )
    oh_row = cr.fetchone()
    so_tbl = "order_header" if (oh_row and oh_row[0] == "BASE TABLE") else "sale_order"

    cr.execute(
        f"""
        SELECT id FROM {so_tbl}
         WHERE name = 'S01504' OR client_order_ref = 'MTI-DIGIMATE-TS-2026-09'
         ORDER BY id ASC LIMIT 1;
        """
    )
    so_row = cr.fetchone()
    if so_row:
        so_id = so_row[0]
        cr.execute(
            f"""
            UPDATE {so_tbl}
               SET partner_id = %s,
                   partner_invoice_id = %s,
                   partner_shipping_id = %s,
                   project_id = %s,
                   client_order_ref = COALESCE(client_order_ref, 'MTI-DIGIMATE-TS-2026-09'),
                   state = 'sale',
                   dgm_is_staff_augmentation = TRUE,
                   write_date = NOW()
             WHERE id = %s;
            """,
            (mti_partner_id, mti_partner_id, mti_partner_id, mti_project_id, so_id),
        )
        return so_id

    cr.execute("SELECT id FROM res_currency WHERE name = 'VND' LIMIT 1;")
    vnd_row = cr.fetchone()
    vnd_id = vnd_row[0] if vnd_row else 23
    cr.execute("SELECT id FROM product_pricelist WHERE active = TRUE ORDER BY id ASC LIMIT 1;")
    pl_row = cr.fetchone()
    pl_id = pl_row[0] if pl_row else 1

    cr.execute(
        f"""
        INSERT INTO {so_tbl} (
            name, company_id, partner_id, partner_invoice_id, partner_shipping_id,
            pricelist_id, currency_id, currency_rate, user_id, team_id,
            client_order_ref, state, document_tax_mode, invoice_status, picking_policy, warehouse_id,
            date_order, validity_date, amount_untaxed, amount_tax, amount_total,
            project_id, dgm_is_staff_augmentation,
            dgm_min_monthly_hours, dgm_max_standard_hours, dgm_hourly_rate_vnd,
            dgm_payment_term_days, dgm_replacement_notice_days, dgm_free_trial_days,
            require_signature, require_payment, prepayment_percent,
            create_uid, write_uid, create_date, write_date
        ) VALUES (
            'S01504', 1, %s, %s, %s,
            %s, %s, 1.0, 2, 1,
            'MTI-DIGIMATE-TS-2026-09', 'sale', 'tax_excluded', 'to invoice', 'direct', 1,
            '2026-10-01 08:30:00', '2027-09-30', 250000000.0, 20000000.0, 270000000.0,
            %s, TRUE,
            140.0, 180.0, 350000.0,
            40, 30, 5,
            TRUE, FALSE, 0.0,
            1, 1, NOW(), NOW()
        ) RETURNING id;
        """,
        (mti_partner_id, mti_partner_id, mti_partner_id, pl_id, vnd_id, mti_project_id),
    )
    return cr.fetchone()[0]


def archive_empty_folders(cr):
    """Archives (`active = False`) any active folder in `documents_document` that has no active children."""
    total_archived = 0
    for _ in range(6):
        cr.execute(
            """
            UPDATE documents_document f
               SET active = FALSE,
                   write_date = NOW()
             WHERE f.type = 'folder'
               AND f.active = TRUE
               AND NOT EXISTS (
                   SELECT 1 FROM documents_document c
                    WHERE c.folder_id = f.id AND c.active = TRUE
               )
            RETURNING f.id;
            """
        )
        rows = cr.fetchall()
        if not rows:
            break
        total_archived += len(rows)
    return total_archived


def seed_database(dbname):
    print(f"\n=== [SOP-DGM-08] INITIALIZING & SEEDING DATABASE: {dbname} ===")
    ensure_pre_registry_columns(dbname)

    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # 1. Initialize SOP-DGM-08 models, security ACLs, views, and Sovereign bridges
        reg.init_models(
            cr,
            [
                "dgm.project.notification",
                "dgm.project.timesheet.sheet",
                "dgm.project.timesheet.line",
                "account.move",
                "project.project",
                "sale.order",
                "res.partner",
            ],
            {"module": "insilos_al2c"},
            install=True,
        )
        convert_file(
            env,
            "insilos_al2c",
            "security/ir.access.csv",
            {},
            mode="init",
            noupdate=False,
        )
        views_rel_path = "views/dgm_project_timesheet_billing_views.xml"
        if os.path.exists(os.path.join(ROOT_DIR, "addons/insilos_al2c", views_rel_path)):
            convert_file(
                env,
                "insilos_al2c",
                views_rel_path,
                {},
                mode="init",
                noupdate=False,
            )
        reg._ensure_sovereign_bridges(cr)

        # 2. Seed Knowledge Article SOP-DGM-08
        kb08_id = seed_sop_dgm_08_knowledge_article(cr)
        print(f"  [✓] Seeded Knowledge Article SOP-DGM-08 (id={kb08_id}, xml_id=insilos_al2c.kb_dgm_sop_08_timesheet_billing)")

        Partner = env["res.partner"].sudo()
        Project = env["project.project"].sudo()
        Task = env["project.task"].sudo()
        SaleOrder = env["sale.order"].sudo()
        Notification = env["dgm.project.notification"].sudo()
        TimesheetSheet = env["dgm.project.timesheet.sheet"].sudo()
        TimesheetLine = env["dgm.project.timesheet.line"].sudo()

        # =====================================================================
        # 3. Canonical End-to-End Pipeline for MTI Technology (PTN-DGM-2026-0001)
        # =====================================================================
        mti_partner = Partner.search(
            ["|", ("dgm_partner_code", "=", "PTN-DGM-2026-0001"), ("vat", "=", "0314015511")],
            order="id asc",
            limit=1,
        )
        assert mti_partner, f"{dbname}: Missing MTI Technology partner (PTN-DGM-2026-0001)"

        mti_project = Project.browse(1328).exists()
        if not mti_project or "MTI Technology" not in (mti_project.name or ""):
            mti_project = Project.search(
                [("name", "ilike", "MTI Technology — B2B Onsite Software Engineering")],
                order="id asc",
                limit=1,
            )
        mti_folder_id = mti_partner.dgm_onboarding_folder_id.id if mti_partner.dgm_onboarding_folder_id else None
        if not mti_project:
            mti_project = Project.with_context(mail_create_nosubscribe=True).create({
                "name": "MTI Technology — B2B Onsite Software Engineering (HĐ DIGIMATE2401-001)",
                "partner_id": mti_partner.id,
                "documents_folder_id": mti_folder_id or False,
                "allow_timesheets": True,
                "company_id": 1,
                "active": True,
            })
        else:
            cr.execute(
                """
                UPDATE project_project
                   SET partner_id = %s,
                       documents_folder_id = COALESCE(%s, documents_folder_id),
                       allow_timesheets = TRUE,
                       active = TRUE,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (mti_partner.id, mti_folder_id, mti_project.id),
            )
            env.invalidate_all()

        mti_so_id = _ensure_mti_sale_order(cr, mti_partner.id, mti_project.id)
        env.invalidate_all()
        mti_so = SaleOrder.browse(mti_so_id)

        mti_task = Task.search([("project_id", "=", mti_project.id)], order="id asc", limit=1)
        if not mti_task:
            mti_task = Task.with_context(mail_create_nosubscribe=True).create({
                "name": "Realize: Core Software Engineering & Monthly Timesheet Execution (MTI Onsite)",
                "project_id": mti_project.id,
                "partner_id": mti_partner.id,
            })

        mti_engineers_spec = [
            (
                10,
                "DGM-004",
                "Bùi Hữu Tài",
                "Senior Software Engineer (MTI Onsite)",
                65_000_000.0,
                "Phát triển Backend Microservices & Tối ưu API hiệu năng cao dự án CLV (MTI Technology) kỳ 10/2026.",
            ),
            (
                20,
                "DGM-005",
                "Huỳnh Trần Quang Khánh",
                "Senior Software Engineer / Tech Lead",
                70_000_000.0,
                "Tech Lead dự án LifeSocket (MTI Technology): Thiết kế kiến trúc, Code Review & Điều phối Sprint kỳ 10/2026.",
            ),
            (
                30,
                "DGM-006",
                "Ngô Thanh Lộc",
                "Senior Software Engineer (MTI Onsite)",
                60_000_000.0,
                "Phát triển tính năng Core Platform & Tích hợp hệ thống thanh toán dự án CLV (MTI Technology) kỳ 10/2026.",
            ),
            (
                40,
                "DGM-007",
                "Lê Cao Bảo Phúc",
                "Software Engineer (MTI Onsite)",
                55_000_000.0,
                "Phát triển Frontend/Mobile UI, Kiểm thử tích hợp & Bàn giao UAT dự án CLV (MTI Technology) kỳ 10/2026.",
            ),
        ]

        mti_emp_records = []
        mti_emp_Analytic_map = {}
        for seq_no, emp_code, emp_name, role_title, rate_vnd, work_desc in mti_engineers_spec:
            emp = _ensure_employee(env, emp_code, emp_name, role_title)
            mti_emp_records.append((seq_no, emp, role_title, rate_vnd, work_desc))
            aline_id = _ensure_analytic_timesheet_line(
                cr,
                mti_project,
                mti_task,
                emp,
                "2026-10-25",
                176.0,  # 22.0 days * 8h
                work_desc,
                mti_partner.id,
                mti_so.id,
            )
            mti_emp_Analytic_map[emp.id] = [aline_id]

        env.invalidate_all()

        # Kickoff Notification PRJ-NTF-202610-0001
        ntf_mti = Notification.search([("name", "=", "PRJ-NTF-202610-0001")], limit=1)
        mti_emp_ids = [item[1].id for item in mti_emp_records]
        if ntf_mti:
            ntf_mti.write({
                "project_id": mti_project.id,
                "partner_id": mti_partner.id,
                "sale_order_id": mti_so.id,
                "notification_type": "kickoff_handover",
                "employee_ids": [(6, 0, mti_emp_ids)],
                "recipient_email": mti_partner.email or "accounting@mti-tech.vn",
            })
        else:
            ntf_mti = Notification.create({
                "name": "PRJ-NTF-202610-0001",
                "project_id": mti_project.id,
                "partner_id": mti_partner.id,
                "sale_order_id": mti_so.id,
                "notification_type": "kickoff_handover",
                "employee_ids": [(6, 0, mti_emp_ids)],
                "recipient_email": mti_partner.email or "accounting@mti-tech.vn",
            })
        ntf_mti.action_send_project_notification()

        # Monthly Timesheet Sheet TS-DGM-202610-0001
        ts_mti = TimesheetSheet.search([("name", "=", "TS-DGM-202610-0001")], limit=1)
        if ts_mti:
            ts_mti.write({
                "partner_id": mti_partner.id,
                "sale_order_id": mti_so.id,
                "project_id": mti_project.id,
                "billing_period": "10/2026",
                "date_start": "2026-10-01",
                "date_end": "2026-10-31",
                "standard_working_days": 22.0,
                "vat_rate": "8",
                "state": "draft",
            })
        else:
            ts_mti = TimesheetSheet.create({
                "name": "TS-DGM-202610-0001",
                "partner_id": mti_partner.id,
                "sale_order_id": mti_so.id,
                "project_id": mti_project.id,
                "billing_period": "10/2026",
                "date_start": "2026-10-01",
                "date_end": "2026-10-31",
                "standard_working_days": 22.0,
                "vat_rate": "8",
            })

        # Sync from project timesheets and enforce exact contract rates & role titles for the 4 MTI engineers
        ts_mti.action_sync_from_project_timesheets()
        ts_mti.line_ids.unlink()
        for seq_no, emp, role_title, rate_vnd, work_desc in mti_emp_records:
            TimesheetLine.create({
                "sheet_id": ts_mti.id,
                "sequence": seq_no,
                "employee_id": emp.id,
                "role_title": role_title,
                "task_id": mti_task.id,
                "contract_monthly_rate_vnd": rate_vnd,
                "standard_days": 22.0,
                "actual_worked_days": 22.0,
                "overtime_hours": 0.0,
                "work_summary": work_desc,
                "analytic_line_ids": [(6, 0, mti_emp_Analytic_map.get(emp.id, []))],
            })

        # Progress TS-DGM-202610-0001 through all 5 stages
        ts_mti.action_submit_for_customer_approval()
        ts_mti.action_customer_approve(
            approver_name="Tanaka Kenji — Engineering Director (MTI Technology)",
            approver_email="accounting@mti-tech.vn",
            approver_title="Engineering Director",
            note="Approved 100% man-days for October 2026.",
        )
        ts_mti.action_generate_mti_draft_invoice()
        ts_mti.action_confirm_draft_and_issue_official_invoice(
            confirmed_by="Phòng Kế toán MTI Technology (accounting@mti-tech.vn)"
        )
        ntf_mti.write({"timesheet_sheet_id": ts_mti.id})
        print(
            f"  [✓] Seeded MTI Pipeline: {ntf_mti.name} ({ntf_mti.state}) & {ts_mti.name} "
            f"(state={ts_mti.state}, untaxed={ts_mti.amount_untaxed_vnd:,.0f}, total={ts_mti.amount_total_vnd:,.0f}, "
            f"einvoice={ts_mti.draft_invoice_id.dgm_einvoice_symbol}-{ts_mti.draft_invoice_id.dgm_einvoice_number})"
        )

        # =====================================================================
        # 4. Canonical End-to-End Pipeline for AIfin (PTN-DGM-2026-0007)
        # =====================================================================
        aifin_partner = Partner.search(
            ["|", ("dgm_partner_code", "=", "PTN-DGM-2026-0007"), ("vat", "=", "0319631994")],
            order="id asc",
            limit=1,
        )
        assert aifin_partner, f"{dbname}: Missing AIfin partner (PTN-DGM-2026-0007)"

        aifin_project = Project.browse(1327).exists()
        if not aifin_project or "AIFin" not in (aifin_project.name or ""):
            aifin_project = Project.search(
                [("name", "ilike", "AIFin 360-Sales & Onsite Engineering")],
                order="id asc",
                limit=1,
            )
        aifin_folder_id = aifin_partner.dgm_onboarding_folder_id.id if aifin_partner.dgm_onboarding_folder_id else None
        if not aifin_project:
            aifin_project = Project.with_context(mail_create_nosubscribe=True).create({
                "name": "AIFin 360-Sales & Onsite Engineering (Trần Văn Huỳnh Phố - DGM-009)",
                "partner_id": aifin_partner.id,
                "documents_folder_id": aifin_folder_id or False,
                "allow_timesheets": True,
                "company_id": 1,
                "active": True,
            })
        else:
            cr.execute(
                """
                UPDATE project_project
                   SET partner_id = %s,
                       documents_folder_id = COALESCE(%s, documents_folder_id),
                       allow_timesheets = TRUE,
                       active = TRUE,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (aifin_partner.id, aifin_folder_id, aifin_project.id),
            )
            env.invalidate_all()

        aifin_so = SaleOrder.search(
            [
                "|",
                ("client_order_ref", "=", "DIGIMATE-AIFIN-VN_2610-001"),
                ("name", "=", "SO-DGM-AIFIN-2610"),
            ],
            order="id asc",
            limit=1,
        )
        if aifin_so:
            cr.execute(
                "SELECT table_type FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'order_header';"
            )
            oh_r = cr.fetchone()
            so_t = "order_header" if (oh_r and oh_r[0] == "BASE TABLE") else "sale_order"
            cr.execute(
                f"UPDATE {so_t} SET partner_id = %s, project_id = %s, write_date = NOW() WHERE id = %s;",
                (aifin_partner.id, aifin_project.id, aifin_so.id),
            )
            env.invalidate_all()

        aifin_task = Task.search([("project_id", "=", aifin_project.id)], order="id asc", limit=1)
        if not aifin_task:
            aifin_task = Task.create({
                "name": "Realize: Onsite Engineering — Project AIFin 360-Sales (Trần Văn Huỳnh Phố - DGM-009)",
                "project_id": aifin_project.id,
                "partner_id": aifin_partner.id,
            })

        emp_pho = _ensure_employee(
            env,
            "DGM-009",
            "Trần Văn Huỳnh Phố",
            "Senior Software Engineer — Project AIFin 360-Sales",
        )
        aifin_work_desc = (
            "Biệt phái Kỹ sư Phần mềm Senior (Trần Văn Huỳnh Phố - DGM-009 / PhoTVH) phát triển hệ thống "
            "AIFin 360-Sales (Web App, Mobile App, Zalo MiniApp, AI Call Coaching) theo HĐ DIGIMATE-AIFIN-VN_2610-001 kỳ 10/2026."
        )
        pho_aline_id = _ensure_analytic_timesheet_line(
            cr,
            aifin_project,
            aifin_task,
            emp_pho,
            "2026-10-25",
            176.0,  # 22.0 days * 8h
            aifin_work_desc,
            aifin_partner.id,
            aifin_so.id if aifin_so else None,
        )
        env.invalidate_all()

        # Kickoff Notification PRJ-NTF-202610-0002
        ntf_aifin = Notification.search([("name", "=", "PRJ-NTF-202610-0002")], limit=1)
        if ntf_aifin:
            ntf_aifin.write({
                "project_id": aifin_project.id,
                "partner_id": aifin_partner.id,
                "sale_order_id": aifin_so.id if aifin_so else False,
                "notification_type": "kickoff_handover",
                "employee_ids": [(6, 0, [emp_pho.id])],
                "recipient_email": aifin_partner.email or "huy.nguyen@aifin.com.vn",
            })
        else:
            ntf_aifin = Notification.create({
                "name": "PRJ-NTF-202610-0002",
                "project_id": aifin_project.id,
                "partner_id": aifin_partner.id,
                "sale_order_id": aifin_so.id if aifin_so else False,
                "notification_type": "kickoff_handover",
                "employee_ids": [(6, 0, [emp_pho.id])],
                "recipient_email": aifin_partner.email or "huy.nguyen@aifin.com.vn",
            })
        ntf_aifin.action_send_project_notification()

        # Monthly Timesheet Sheet TS-DGM-202610-0002
        ts_aifin = TimesheetSheet.search([("name", "=", "TS-DGM-202610-0002")], limit=1)
        if ts_aifin:
            ts_aifin.write({
                "partner_id": aifin_partner.id,
                "sale_order_id": aifin_so.id if aifin_so else False,
                "project_id": aifin_project.id,
                "billing_period": "10/2026",
                "date_start": "2026-10-01",
                "date_end": "2026-10-31",
                "standard_working_days": 22.0,
                "vat_rate": "8",
                "state": "draft",
            })
        else:
            ts_aifin = TimesheetSheet.create({
                "name": "TS-DGM-202610-0002",
                "partner_id": aifin_partner.id,
                "sale_order_id": aifin_so.id if aifin_so else False,
                "project_id": aifin_project.id,
                "billing_period": "10/2026",
                "date_start": "2026-10-01",
                "date_end": "2026-10-31",
                "standard_working_days": 22.0,
                "vat_rate": "8",
            })

        ts_aifin.action_sync_from_project_timesheets()
        ts_aifin.line_ids.unlink()
        TimesheetLine.create({
            "sheet_id": ts_aifin.id,
            "sequence": 10,
            "employee_id": emp_pho.id,
            "role_title": "Senior Software Engineer — Project AIFin 360-Sales",
            "task_id": aifin_task.id,
            "contract_monthly_rate_vnd": 35_000_000.0,
            "standard_days": 22.0,
            "actual_worked_days": 22.0,
            "overtime_hours": 0.0,
            "work_summary": aifin_work_desc,
            "analytic_line_ids": [(6, 0, [pho_aline_id])],
        })

        # Progress TS-DGM-202610-0002 through all 5 stages
        ts_aifin.action_submit_for_customer_approval()
        ts_aifin.action_customer_approve(
            approver_name="Nguyễn Quốc Huy — Tổng Giám đốc (AIfin)",
            approver_email="huy.nguyen@aifin.com.vn",
            approver_title="CEO / Tổng Giám đốc",
            note="Nghiệm thu 22/22 ngày công tháng 10/2026 của Kỹ sư Trần Văn Huỳnh Phố (DGM-009).",
        )
        ts_aifin.action_generate_mti_draft_invoice()
        ts_aifin.action_confirm_draft_and_issue_official_invoice(
            confirmed_by="Nguyễn Quốc Huy — Tổng Giám đốc (AIfin)"
        )
        ntf_aifin.write({"timesheet_sheet_id": ts_aifin.id})
        print(
            f"  [✓] Seeded AIfin Pipeline: {ntf_aifin.name} ({ntf_aifin.state}) & {ts_aifin.name} "
            f"(state={ts_aifin.state}, untaxed={ts_aifin.amount_untaxed_vnd:,.0f}, total={ts_aifin.amount_total_vnd:,.0f}, "
            f"einvoice={ts_aifin.draft_invoice_id.dgm_einvoice_symbol}-{ts_aifin.draft_invoice_id.dgm_einvoice_number})"
        )

        # 5. Zero Empty Folders Invariant
        env.flush_all()
        archived_cnt = archive_empty_folders(cr)
        print(f"  [✓] Zero Empty Folders Invariant enforced (archived {archived_cnt} empty folders)")

        cr.commit()


def main():
    if os.path.isdir("/app/insilos"):
        addons_path = "/var/lib/insilos/filestore/custom_addons,/app/insilos/addons,/app/insilos/apps,/app/insilos/enterprise"
        odoo.tools.config.parse_config([
            f"--addons-path={addons_path}",
            f"--db_host={os.environ.get('DB_HOST', 'pgbouncer-service')}",
            f"--db_port={os.environ.get('DB_PORT', '6432')}",
            f"--db_user={os.environ.get('DB_USER', 'insilos')}",
            f"--db_password={os.environ.get('PGPASSWORD', '')}",
        ])
    else:
        odoo.tools.config.parse_config(["-c", os.path.join(ROOT_DIR, "odoo.conf")])

    if len(sys.argv) > 1:
        target_dbs = sys.argv[1:]
    else:
        target_dbs = ["insilos20_dev", "innoria_prod"]

    for dbname in target_dbs:
        seed_database(dbname)


if __name__ == "__main__":
    main()
