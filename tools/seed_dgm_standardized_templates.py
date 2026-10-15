#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotent Seeding & Standardization Engine for All Digimate Document Templates:
HR (`TPL-HR-01..05`), Partner Onboarding (`TPL-ONB-01..04`), Staff Augmentation (`TPL-ONB-05`),
Project Notifications (`PRJ-NTF-202610-0001..0002`), Timesheet / Acceptance / Draft & Official
VAT E-Invoices (`TS-DGM-202610-0001..0002`, `1C26TAA`), Master Standardized Template Library
(`Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance`), and Universal HTML Brand Footer
Sweep across `insilos20_dev` and `innoria_prod`.

Every generated/updated HTML document features the authentic Google Drive Digimate `Logo`
(`data-dgm-header="drive-logo-v1"`, `data-dgm-footer="drive-logo-v1"`,
`data-logo-source="google-drive-logo-folder"`).
"""
import base64
import configparser
import os
import re
import site
import sys
import types
import psycopg2

ROOT_DIR = "/app/insilos" if os.path.isdir("/app/insilos") else "/home/zen/O20"
CONF_PATH = os.path.join(ROOT_DIR, "odoo.conf")
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
from odoo.tools import convert_file


def _parse_conf():
    if os.path.isdir("/app/insilos"):
        addons_path = "/var/lib/insilos/filestore/custom_addons,/app/insilos/addons,/app/insilos/apps,/app/insilos/enterprise"
        odoo.tools.config.parse_config([
            f"--addons-path={addons_path}",
            f"--data-dir={os.environ.get('DATA_DIR', '/var/lib/insilos')}",
            f"--db_host={os.environ.get('DB_HOST', 'pgbouncer-service')}",
            f"--db_port={os.environ.get('DB_PORT', '6432')}",
            f"--db_user={os.environ.get('DB_USER', 'insilos')}",
            f"--db_password={os.environ.get('PGPASSWORD', '')}",
        ])
    else:
        odoo.tools.config.parse_config(["-c", CONF_PATH])


_parse_conf()


def get_pg_conn(dbname):
    cfg = configparser.ConfigParser()
    if os.path.isfile(CONF_PATH):
        cfg.read(CONF_PATH)
    opts = cfg["options"] if "options" in cfg else {}
    return psycopg2.connect(
        dbname=dbname,
        user=os.environ.get("DB_USER", opts.get("db_user", "odoo")),
        password=os.environ.get("PGPASSWORD", opts.get("db_password", "odoo")),
        host=os.environ.get("DB_HOST", opts.get("db_host", "127.0.0.1")),
        port=int(os.environ.get("DB_PORT", opts.get("db_port", "5434"))),
    )


def ensure_pre_registry_columns(dbname):
    """Ensures `party_master` / `res_partner` has all SOP-DGM-09 columns and M2M relation table
    before `Registry.new(dbname)` initializes compatibility views."""
    conn = get_pg_conn(dbname)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'party_master';
        """
    )
    row = cur.fetchone()
    base_partner_table = "party_master" if (row and row[0] == "BASE TABLE") else "res_partner"

    partner_cols = [
        ("dgm_software_contract_model", "VARCHAR DEFAULT 'mti_codev'"),
        ("dgm_software_contract_doc_count", "INTEGER DEFAULT 0"),
    ]
    for col, col_def in partner_cols:
        cur.execute("SAVEPOINT sp_ptn_col;")
        try:
            cur.execute(f"ALTER TABLE public.{base_partner_table} ADD COLUMN IF NOT EXISTS {col} {col_def};")
            cur.execute("RELEASE SAVEPOINT sp_ptn_col;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_ptn_col;")

    cur.execute("SAVEPOINT sp_sw_rel;")
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public.dgm_partner_sw_contract_doc_rel (
                partner_id INTEGER NOT NULL,
                document_id INTEGER NOT NULL,
                PRIMARY KEY (partner_id, document_id)
            );
            """
        )
        cur.execute("RELEASE SAVEPOINT sp_sw_rel;")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT sp_sw_rel;")

    cur.execute(
        """
        SELECT table_type FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = 'res_partner';
        """
    )
    rp_row = cur.fetchone()
    if rp_row and rp_row[0] == "VIEW" and base_partner_table == "party_master":
        cur.execute("SAVEPOINT sp_rp_view;")
        try:
            cur.execute("CREATE OR REPLACE VIEW public.res_partner AS SELECT * FROM public.party_master;")
            cur.execute("RELEASE SAVEPOINT sp_rp_view;")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT sp_rp_view;")

    conn.commit()
    cur.close()
    conn.close()


import odoo.addons.insilos_al2c.models.dgm_brand_footer as _bf_mod  # noqa: E402
import odoo.addons.insilos_al2c.models.dgm_project_timesheet_billing as _ptb_mod  # noqa: E402
from odoo.addons.insilos_al2c.models.dgm_brand_footer import (  # noqa: E402
    get_digimate_logo_data_uri,
    get_digimate_logo_url,
    render_dgm_brand_header_html,
    render_dgm_brand_footer_html,
    wrap_dgm_branded_html_document as _orig_wrap_dgm_branded_html_document,
)
from odoo.addons.insilos_al2c.models.dgm_hr_document_templates import HR_TEMPLATE_DEFINITIONS  # noqa: E402
from odoo.addons.insilos_al2c.models.dgm_software_contract_templates import (  # noqa: E402
    render_mti_codev_contract_suite,
    render_ktt_turnkey_contract_suite,
    render_all_master_software_contract_templates,
)


def wrap_dgm_branded_html_document(
    body_html,
    title="Digimate Enterprise Document",
    doc_code="DGM-DOC-2026",
    sop_ref="SOP-DGM",
    classification="INTERNAL / B2B CONFIDENTIAL",
    include_header=False,
    doc_title=None,
    **_extra_kw,
):
    return _orig_wrap_dgm_branded_html_document(
        body_html=body_html,
        title=doc_title or title,
        doc_code=doc_code,
        sop_ref=sop_ref,
        classification=classification,
        include_header=include_header,
    )


_bf_mod.wrap_dgm_branded_html_document = wrap_dgm_branded_html_document
_ptb_mod.wrap_dgm_branded_html_document = wrap_dgm_branded_html_document



DRIVE_SYNC_DIR = "/tmp/dgm_drive_sync/files/DGM- HÌNH ẢNH 2025"
STATIC_IMG_DIR = os.path.join(ROOT_DIR, "addons/insilos_al2c/static/src/img")

LOGO_FILES_SPEC = [
    ("Digimate green Logo.png", "digimate_drive_logo.png"),
    ("Digimate Black Logo.png", "digimate_drive_logo_black.png"),
    ("Digimate White Logo.png", "digimate_drive_logo_white.png"),
    ("Digimate blue logo.png", "digimate_drive_logo.png"),
    ("Digimate black logo(1).png", "digimate_drive_logo_black.png"),
]

MASTER_LIBRARY_FOLDER_NAME = "Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance"


def _read_logo_bytes(drive_filename, fallback_static_name):
    drive_path = os.path.join(DRIVE_SYNC_DIR, drive_filename)
    if os.path.isfile(drive_path) and os.path.getsize(drive_path) > 100:
        with open(drive_path, "rb") as f:
            return f.read()
    static_path = os.path.join(STATIC_IMG_DIR, fallback_static_name)
    if os.path.isfile(static_path):
        with open(static_path, "rb") as f:
            return f.read()
    default_path = os.path.join(STATIC_IMG_DIR, "digimate_drive_logo.png")
    with open(default_path, "rb") as f:
        return f.read()


def _decode_attachment_html(att):
    """Safely decodes an ir.attachment payload to UTF-8 string, handling raw bytes
    and base64 padding anomalies without raising binascii.Error.
    """
    if not att:
        return ""
    try:
        raw = getattr(att, "raw", None)
        if raw:
            return raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
    except Exception:
        pass
    try:
        datas = att.datas
        if not datas:
            return ""
        s = datas.decode("ascii", errors="ignore").strip() if isinstance(datas, (bytes, bytearray)) else str(datas).strip()
        pad = (-len(s)) % 4
        if pad:
            s += "=" * pad
        return base64.b64decode(s).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _ensure_doc_and_ancestors_active(env, doc_records):
    """Unarchives a `documents.document` recordset and all its ancestor folders via SQL
    so `documents.document.write` never raises UserError on archived parent chains.
    """
    if not doc_records:
        return
    all_ids = set()
    seen = set()
    queue = list(doc_records.with_context(active_test=False) if hasattr(doc_records, "with_context") else doc_records)
    while queue:
        rec = queue.pop(0)
        rec_id = getattr(rec, "id", None)
        if not rec_id or not isinstance(rec_id, int) or rec_id in seen:
            continue
        seen.add(rec_id)
        all_ids.add(rec_id)
        parent = getattr(rec, "folder_id", None)
        if parent and getattr(parent, "id", None) and parent.id not in seen:
            queue.append(parent.with_context(active_test=False) if hasattr(parent, "with_context") else parent)
    if all_ids and hasattr(env, "cr") and env.cr and hasattr(env.cr, "execute"):
        env.cr.execute(
            "UPDATE documents_document SET active = TRUE, owner_id = NULL, access_internal = 'edit' WHERE id = ANY(%s)",
            (list(all_ids),),
        )
        if hasattr(env, "invalidate_all"):
            env.invalidate_all()


def _resolve_folder(env, preferred_id, name_patterns, parent_id=False):
    Document = env["documents.document"].sudo()
    if preferred_id:
        folder = Document.with_context(active_test=False).browse(preferred_id).exists()
        if folder and folder.type == "folder":
            _ensure_doc_and_ancestors_active(env, folder)
            folder.write({
                "owner_id": False,
                "access_internal": "edit",
            })
            return folder
    for pat in name_patterns:
        domain = [("type", "=", "folder"), ("name", "ilike", pat)]
        if parent_id:
            domain.append(("folder_id", "=", parent_id))
        folder = Document.with_context(active_test=False).search(domain, order="id asc", limit=1)
        if folder:
            _ensure_doc_and_ancestors_active(env, folder)
            folder.write({
                "owner_id": False,
                "access_internal": "edit",
            })
            return folder
    return Document.browse()


def _upsert_html_doc(env, folder_id, doc_name, filename, html_str, res_model="documents.document", res_id=0, code_marker=None):
    Document = env["documents.document"].sudo()
    Attachment = env["ir.attachment"].sudo().with_context(no_document=True)
    b64_datas = base64.b64encode(html_str.encode("utf-8"))

    existing = Document.browse()
    if code_marker:
        existing = Document.with_context(active_test=False).search([
            ("folder_id", "=", folder_id),
            ("type", "!=", "folder"),
            ("name", "ilike", code_marker),
        ], order="id asc", limit=1)
    if not existing:
        existing = Document.with_context(active_test=False).search([
            ("folder_id", "=", folder_id),
            ("type", "!=", "folder"),
            ("name", "=", doc_name),
        ], order="id asc", limit=1)

    if existing:
        _ensure_doc_and_ancestors_active(env, existing)
        if existing.attachment_id:
            existing.attachment_id.with_context(no_document=True).write({
                "name": filename,
                "datas": b64_datas,
                "mimetype": "text/html",
            })
        else:
            att = Attachment.create({
                "name": filename,
                "type": "binary",
                "datas": b64_datas,
                "mimetype": "text/html",
                "res_model": "documents.document",
                "res_id": existing.id,
            })
            existing.write({"attachment_id": att.id})
        existing.write({
            "name": doc_name,
            "folder_id": folder_id,
            "owner_id": False,
            "access_internal": "edit",
            "access_via_link": "view",
        })
        return existing

    att = Attachment.create({
        "name": filename,
        "type": "binary",
        "datas": b64_datas,
        "mimetype": "text/html",
        "res_model": "documents.document",
        "res_id": 0,
    })
    doc = Document.create({
        "name": doc_name,
        "folder_id": folder_id,
        "owner_id": False,
        "type": "binary",
        "attachment_id": att.id,
        "access_internal": "edit",
        "access_via_link": "view",
        "active": True,
    })
    att.write({"res_id": doc.id})
    return doc



def step1_verify_and_repair_drive_logo_folder(env, dbname):
    """Step 1: Verify & Repair Google Drive `Logo` Folder in Documents (`4705` under `3229` in dev, `241` under `213` in prod)."""
    Document = env["documents.document"].sudo()
    Attachment = env["ir.attachment"].sudo()

    brand_root = _resolve_folder(
        env,
        preferred_id=3229 if dbname == "insilos20_dev" else 213,
        name_patterns=["06. Thương hiệu & Hình ảnh", "06. Thương hiệu"],
    )
    assert brand_root, f"{dbname}: Could not locate 06. Thương hiệu & Hình ảnh folder"

    logo_folder = _resolve_folder(
        env,
        preferred_id=4705 if dbname == "insilos20_dev" else 241,
        name_patterns=["Logo"],
        parent_id=brand_root.id,
    )
    if not logo_folder:
        logo_folder = Document.create({
            "name": "Logo",
            "type": "folder",
            "folder_id": brand_root.id,
            "owner_id": False,
            "access_internal": "edit",
            "active": True,
        })
    else:
        _ensure_doc_and_ancestors_active(env, logo_folder)
        logo_folder.write({
            "folder_id": brand_root.id,
            "owner_id": False,
            "access_internal": "edit",
        })

    repaired_count = 0
    for drive_fname, fallback_fname in LOGO_FILES_SPEC:
        raw_bytes = _read_logo_bytes(drive_fname, fallback_fname)
        b64_datas = base64.b64encode(raw_bytes)
        existing_logo = Document.with_context(active_test=False).search([
            ("folder_id", "=", logo_folder.id),
            ("type", "!=", "folder"),
            ("name", "=", drive_fname),
        ], order="id asc", limit=1)
        if existing_logo:
            _ensure_doc_and_ancestors_active(env, existing_logo)
            if existing_logo.attachment_id:
                existing_logo.attachment_id.write({
                    "name": drive_fname,
                    "datas": b64_datas,
                    "mimetype": "image/png",
                })
            else:
                att = Attachment.create({
                    "name": drive_fname,
                    "type": "binary",
                    "datas": b64_datas,
                    "mimetype": "image/png",
                    "res_model": "documents.document",
                    "res_id": existing_logo.id,
                })
                existing_logo.write({"attachment_id": att.id})
            existing_logo.write({
                "owner_id": False,
                "access_internal": "edit",
                "access_via_link": "view",
            })
        else:
            att = Attachment.create({
                "name": drive_fname,
                "type": "binary",
                "datas": b64_datas,
                "mimetype": "image/png",
                "res_model": "documents.document",
            })
            Document.create({
                "name": drive_fname,
                "folder_id": logo_folder.id,
                "owner_id": False,
                "type": "binary",
                "attachment_id": att.id,
                "access_internal": "edit",
                "access_via_link": "view",
                "active": True,
            })
        repaired_count += 1

    print(f"  [Step 1] {dbname}: Verified `Logo` folder (id={logo_folder.id} under {brand_root.id}) with {repaired_count} Google Drive PNG logos.")
    return logo_folder


def step2_regenerate_partner_onboarding_and_staff_aug_docs(env, dbname):
    """Step 2: Regenerate all 32 partner onboarding companion documents (PTN-DGM-2026-0001..0008)
    and Staff Augmentation acceptance docs ([TPL-ONB-05]).
    """
    Partner = env["res.partner"].sudo()
    SaleOrder = env["sale.order"].sudo()

    partners = Partner.search([
        ("dgm_partner_code", "in", [
            "PTN-DGM-2026-0001",
            "PTN-DGM-2026-0002",
            "PTN-DGM-2026-0003",
            "PTN-DGM-2026-0004",
            "PTN-DGM-2026-0005",
            "PTN-DGM-2026-0006",
            "PTN-DGM-2026-0007",
            "PTN-DGM-2026-0008",
        ])
    ], order="dgm_partner_code asc")

    companion_count = 0
    for partner in partners:
        gen_fn = (
            getattr(partner, "action_generate_onboarding_companion_docs", None)
            or getattr(partner, "action_generate_onboarding_documents", None)
        )
        if gen_fn:
            gen_fn()

        for doc in partner.dgm_onboarding_doc_ids.filtered(lambda d: d.active and d.type != "folder"):
            raw_html = _decode_attachment_html(doc.attachment_id)
            if raw_html:
                m_code = re.search(r"\[(TPL-ONB-\d+)\]", doc.name or "")
                tpl_code = m_code.group(1) if m_code else (partner.dgm_partner_code or "TPL-ONB")
                branded_html = wrap_dgm_branded_html_document(
                    body_html=raw_html,
                    title=doc.name or "Hồ sơ Onboarding Đối tác Digimate",
                    doc_code=f"{tpl_code} • {partner.dgm_partner_code}",
                    sop_ref="SOP-DGM-06",
                    classification="B2B PARTNER CONFIDENTIAL",
                    include_header=True,
                )
                doc.attachment_id.write({
                    "datas": base64.b64encode(branded_html.encode("utf-8")),
                    "mimetype": "text/html",
                })
                _ensure_doc_and_ancestors_active(env, doc)
                doc.write({"owner_id": False, "access_internal": "edit"})
                companion_count += 1

    staff_aug_orders = SaleOrder.search([
        "|",
        ("client_order_ref", "=", "DIGIMATE-AIFIN-VN_2610-001"),
        ("dgm_is_staff_augmentation", "=", True),
    ])
    staff_aug_count = 0
    for so in staff_aug_orders:
        if hasattr(so, "action_generate_staff_aug_acceptance_doc"):
            doc05 = so.action_generate_staff_aug_acceptance_doc(
                period_label="10/2026",
                logged_hours=160.0,
                ot_weekday_hours=0.0,
                ot_weekend_hours=0.0,
            )
            raw_html = _decode_attachment_html(doc05.attachment_id if doc05 else None)
            if doc05 and raw_html:
                branded_html = wrap_dgm_branded_html_document(
                    body_html=raw_html,
                    title=doc05.name or "Biên bản Nghiệm thu Dịch vụ Phái cử Nhân sự (Staff Augmentation)",
                    doc_code=f"TPL-ONB-05 • {so.name}",
                    sop_ref="SOP-DGM-07",
                    classification="B2B COMMERCIAL & SLA CONFIDENTIAL",
                    include_header=True,
                )
                doc05.attachment_id.write({
                    "datas": base64.b64encode(branded_html.encode("utf-8")),
                    "mimetype": "text/html",
                })
                _ensure_doc_and_ancestors_active(env, doc05)
                doc05.write({"owner_id": False, "access_internal": "edit"})
                staff_aug_count += 1

    print(f"  [Step 2] {dbname}: Standardized {companion_count} partner onboarding companion docs & {staff_aug_count} Staff Augmentation [TPL-ONB-05] docs.")


def step3_regenerate_sop08_notifications_and_timesheet_invoices(env, dbname):
    """Step 3: Regenerate all SOP-DGM-08 Project Notifications (PRJ-NTF-202610-0001..0002)
    and Timesheet / Acceptance / Draft Invoice / Official Invoice documents (TS-DGM-202610-0001..0002).
    """
    Notification = env["dgm.project.notification"].sudo()
    Sheet = env["dgm.project.timesheet.sheet"].sudo()
    Document = env["documents.document"].sudo()

    ntfs = Notification.search([
        ("name", "in", ["PRJ-NTF-202610-0001", "PRJ-NTF-202610-0002"]),
    ], order="name asc")
    for ntf in ntfs:
        if hasattr(ntf, "action_send_project_notification"):
            ntf.action_send_project_notification()
        html_payload = ntf._render_notification_document_html()
        branded_ntf = wrap_dgm_branded_html_document(
            body_html=html_payload,
            title=f"Thông báo Triển khai Dự án {ntf.name} — {ntf.project_id.name or ''}",
            doc_code=ntf.name,
            sop_ref="SOP-DGM-08",
            classification="PROJECT GOVERNANCE & HANDOVER",
            include_header=True,
        )
        if ntf.document_id and ntf.document_id.exists() and ntf.document_id.attachment_id:
            ntf.document_id.attachment_id.write({
                "datas": base64.b64encode(branded_ntf.encode("utf-8")),
                "mimetype": "text/html",
            })
            _ensure_doc_and_ancestors_active(env, ntf.document_id)
            ntf.document_id.write({"owner_id": False, "access_internal": "edit"})


    out_inv_folder = _resolve_folder(
        env,
        preferred_id=3249 if dbname == "insilos20_dev" else 234,
        name_patterns=["Hoá đơn đầu ra", "Hóa đơn đầu ra"],
    )

    sheets = Sheet.search([
        ("name", "in", ["TS-DGM-202610-0001", "TS-DGM-202610-0002"]),
    ], order="name asc")

    stage_specs = [
        ("timesheet", "timesheet_doc_id", "01_Bang_Cham_Cong_Timesheet", "TPL-PRJ-02", "TIMESHEET CONSOLIDATION"),
        ("acceptance", "acceptance_doc_id", "02_Bien_Ban_Nghiem_Thu_Timesheet", "TPL-PRJ-03", "CUSTOMER ACCEPTANCE CERTIFICATE"),
        ("draft_invoice", "draft_invoice_doc_id", "03_Hoa_Don_Nhap_Doi_Soat", "TPL-PRJ-04A", "MTI DRAFT RECONCILIATION INVOICE"),
        ("official_invoice", "official_invoice_doc_id", "04_Hoa_Don_Chinh_Thuc_VAT_1C26TAA", "TPL-PRJ-04B", "OFFICIAL VAT E-INVOICE 1C26TAA"),
    ]

    for sheet in sheets:
        partner_code = sheet.partner_id.dgm_partner_code or f"PTN-{sheet.partner_id.id}"
        period_slug = re.sub(r"[^0-9A-Za-z]+", "_", sheet.billing_period or "2026_10").strip("_")
        for stage_key, field_name, prefix, tpl_code, class_label in stage_specs:
            raw_stage_html = sheet._render_sheet_document_html(doc_stage=stage_key)
            branded_stage_html = wrap_dgm_branded_html_document(
                body_html=raw_stage_html,
                title=f"{prefix} — {sheet.name} ({partner_code})",
                doc_code=f"{tpl_code} • {sheet.name}",
                sop_ref="SOP-DGM-08",
                classification=class_label,
                include_header=True,
            )
            doc_rec = getattr(sheet, field_name, False)
            if doc_rec and doc_rec.exists() and doc_rec.attachment_id:
                doc_rec.attachment_id.write({
                    "datas": base64.b64encode(branded_stage_html.encode("utf-8")),
                    "mimetype": "text/html",
                })
                _ensure_doc_and_ancestors_active(env, doc_rec)
                doc_rec.write({"owner_id": False, "access_internal": "edit"})

            if stage_key == "official_invoice" and out_inv_folder:
                fname = f"{prefix}_{partner_code}_{period_slug}.html"
                doc_title = f"[SOP-DGM-08] Hóa đơn GTGT Chính thức (1C26TAA) — {sheet.name} ({sheet.partner_id.name})"
                _upsert_html_doc(
                    env,
                    folder_id=out_inv_folder.id,
                    doc_name=doc_title,
                    filename=fname,
                    html_str=branded_stage_html,
                    res_model="account.move",
                    res_id=sheet.draft_invoice_id.id if sheet.draft_invoice_id else sheet.id,
                    code_marker=sheet.name,
                )

    print(f"  [Step 3] {dbname}: Standardized {len(ntfs)} SOP-DGM-08 project notifications & {len(sheets) * 4} timesheet/acceptance/invoice HTML documents.")


def step4_standardize_hr_employee_documents(env, dbname):
    """Step 4: Upgrade all HR Employee contracts & generate standardized HR documents (TPL-HR-01..TPL-HR-05)
    for Digimate employees (DGM-001..DGM-009) in `01. Pháp lý & Hành chính (Legal & Corporate)`.
    """
    Employee = env["hr.employee"].sudo()
    Document = env["documents.document"].sudo()

    hr_folder = _resolve_folder(
        env,
        preferred_id=3224 if dbname == "insilos20_dev" else 208,
        name_patterns=["01. Pháp lý & Hành chính", "01. Hành chính"],
    )
    assert hr_folder, f"{dbname}: Could not locate 01. Pháp lý & Hành chính folder"

    for comp in env["res.company"].sudo().search([]):
        if hasattr(comp, "documents_hr_folder") and comp.documents_hr_folder != hr_folder:
            comp.write({"documents_hr_folder": hr_folder.id})


    # 1. Generate the 5 canonical HR standard documents in hr_folder using DGM-009 (Trần Văn Huỳnh Phố) or top employees
    emp_009 = Employee.search([("registration_number", "=", "DGM-009")], limit=1)
    if not emp_009:
        emp_009 = Employee.search([("name", "ilike", "Trần Văn Huỳnh Phố")], limit=1)
    if not emp_009:
        emp_009 = Employee.search([], order="id asc", limit=1)

    hr_std_docs_count = 0
    if emp_009:
        for tpl_code, meta in HR_TEMPLATE_DEFINITIONS.items():
            html_str = emp_009.render_dgm_hr_template_html(template_code=tpl_code)
            fname = f"{meta['filename_prefix']}_DGM_009.html"
            doc_title = f"[{tpl_code}] {meta['title']} — {emp_009.name} (DGM-009)"
            _upsert_html_doc(
                env,
                folder_id=hr_folder.id,
                doc_name=doc_title,
                filename=fname,
                html_str=html_str,
                res_model="hr.employee",
                res_id=emp_009.id,
                code_marker=f"[{tpl_code}]",
            )
            hr_std_docs_count += 1

    # 2. Generate standardized employment contract (TPL-HR-01) for all DGM-001..DGM-009 employees
    dgm_employees = Employee.search([
        "|",
        ("registration_number", "ilike", "DGM-%"),
        ("work_email", "ilike", "%@digimate.vn"),
    ], order="id asc")
    emp_contract_count = 0
    for emp in dgm_employees:
        reg_no = getattr(emp, "registration_number", None) or f"DGM-{emp.id:03d}"
        html_contract = emp.render_dgm_hr_template_html(template_code="TPL-HR-01")
        clean_reg = re.sub(r"[^0-9A-Za-z_\-]", "_", reg_no)
        fname = f"HDLD_Chuan_{clean_reg}.html"
        doc_title = f"[TPL-HR-01-{reg_no}] Hợp đồng Lao động Chuẩn SOP-DGM-04 — {emp.name} ({reg_no})"
        _upsert_html_doc(
            env,
            folder_id=hr_folder.id,
            doc_name=doc_title,
            filename=fname,
            html_str=html_contract,
            res_model="hr.employee",
            res_id=emp.id,
            code_marker=f"[TPL-HR-01-{reg_no}]",
        )
        emp_contract_count += 1

    # 3. Also ensure existing HR HTML documents in hr_folder (e.g. HĐLĐ_DGM-009_Tran_Van_Huynh_Pho_2026.html) have Drive Logo Header & Footer
    existing_hr_docs = Document.search([
        ("folder_id", "=", hr_folder.id),
        ("type", "!=", "folder"),
        ("active", "=", True),
    ])
    for doc in existing_hr_docs:
        if doc.attachment_id and (
            doc.attachment_id.mimetype == "text/html" or (doc.name or "").endswith(".html")
        ):
            raw_html = _decode_attachment_html(doc.attachment_id)
            if not raw_html:
                continue
            branded = wrap_dgm_branded_html_document(
                body_html=raw_html,
                title=doc.name or "Hồ sơ Nhân sự Digimate",
                doc_code="DGM-HR-2026",
                sop_ref="SOP-DGM-04",
                classification="HR CONFIDENTIAL",
                include_header=True,
            )
            doc.attachment_id.write({"datas": base64.b64encode(branded.encode("utf-8"))})
            _ensure_doc_and_ancestors_active(env, doc)
            doc.write({"owner_id": False, "access_internal": "edit"})

    print(f"  [Step 4] {dbname}: Generated {hr_std_docs_count} canonical [TPL-HR-01..05] docs & {emp_contract_count} employee contracts in folder id={hr_folder.id}.")


def step5b_seed_sop09_software_contracts(env, dbname):
    """Step 5B (`SOP-DGM-09`): Seed KTT Partner (`PTN-DGM-2026-0008`) + Generate Software Contracts
    (`TPL-SW-MTI-01..04` for MTI, `TPL-SW-KTT-01..04` for KTT, and all 8 for AIfin).
    """
    Partner = env["res.partner"].sudo()

    # 1. KTT Khang Trường Thịnh (PTN-DGM-2026-0008, ktt_turnkey -> 4 TPL-SW-KTT-01..04 + 4 TPL-ONB-01..04)
    ktt_partner = Partner.ensure_ktt_khang_truong_thinh_partner()

    # 2. MTI Technology (PTN-DGM-2026-0001, mti_codev -> 4 TPL-SW-MTI-01..04)
    mti_partner = Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0001")], limit=1)
    if mti_partner:
        mti_partner.write({"dgm_software_contract_model": "mti_codev"})
        mti_partner.action_generate_software_contract_templates(model_type="mti_codev")

    # 3. AIfin Company Global (PTN-DGM-2026-0007, both -> 8 TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04)
    aifin_partner = Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0007")], limit=1)
    if aifin_partner:
        aifin_partner.write({"dgm_software_contract_model": "both"})
        aifin_partner.action_generate_software_contract_templates(model_type="both")

    print(
        f"  [Step 5B] {dbname}: Seeded KTT (`{ktt_partner.dgm_partner_code}`, sw_docs={ktt_partner.dgm_software_contract_doc_count}), "
        f"MTI (sw_docs={mti_partner.dgm_software_contract_doc_count if mti_partner else 0}), "
        f"and AIfin (sw_docs={aifin_partner.dgm_software_contract_doc_count if aifin_partner else 0})."
    )
    return mti_partner, ktt_partner, aifin_partner


def step5_seed_master_standardized_template_library(env, dbname, mti_partner=None, ktt_partner=None):
    """Step 5: Create/Update Master Standardized Template Library folder
    (`Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance`) under
    `07. Quy trình Chuẩn & Tự động hóa (SOPs & Automation)` (`4704` in dev, `214` in prod)
    containing all 22 master HTML templates (`TPL-HR-01..05`, `TPL-ONB-01..05`, `TPL-PRJ-01..04`,
    `TPL-SW-MTI-01..04`, `TPL-SW-KTT-01..04`).
    """
    Document = env["documents.document"].sudo()
    Employee = env["hr.employee"].sudo()
    Partner = env["res.partner"].sudo()
    SaleOrder = env["sale.order"].sudo()
    Notification = env["dgm.project.notification"].sudo()
    Sheet = env["dgm.project.timesheet.sheet"].sudo()

    sop_root = _resolve_folder(
        env,
        preferred_id=4704 if dbname == "insilos20_dev" else 214,
        name_patterns=["07. Quy trình Chuẩn & Tự động hóa", "07. Quy trình"],
    )
    assert sop_root, f"{dbname}: Could not locate 07. Quy trình Chuẩn & Tự động hóa folder"

    lib_folder = Document.with_context(active_test=False).search([
        ("type", "=", "folder"),
        ("folder_id", "=", sop_root.id),
        ("name", "=", MASTER_LIBRARY_FOLDER_NAME),
    ], order="id asc", limit=1)
    if not lib_folder:
        lib_folder = Document.create({
            "name": MASTER_LIBRARY_FOLDER_NAME,
            "type": "folder",
            "folder_id": sop_root.id,
            "owner_id": False,
            "access_internal": "edit",
            "active": True,
        })
    else:
        _ensure_doc_and_ancestors_active(env, lib_folder)
        lib_folder.write({
            "folder_id": sop_root.id,
            "owner_id": False,
            "access_internal": "edit",
        })

    master_templates = []

    # 1..5: TPL-HR-01..05 (Master HR Templates rendered via empty hr.employee recordset)
    empty_emp = Employee.browse()
    for tpl_code in ("TPL-HR-01", "TPL-HR-02", "TPL-HR-03", "TPL-HR-04", "TPL-HR-05"):
        meta = HR_TEMPLATE_DEFINITIONS[tpl_code]
        html_str = empty_emp.render_dgm_hr_template_html(template_code=tpl_code)
        master_templates.append((
            tpl_code,
            f"[{tpl_code}] Mẫu Chuẩn: {meta['title']}",
            f"Master_{tpl_code}.html",
            html_str,
        ))

    # 6..9: TPL-ONB-01..04 (Master Partner Onboarding Companion Templates)
    sample_partner = mti_partner or Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0001")], limit=1) or Partner.search([], limit=1)
    for item in sample_partner._render_companion_templates_payload():
        t_code = item["tpl_code"]
        item_title = item.get("doc_name") or item.get("doc_title") or t_code
        branded_html = wrap_dgm_branded_html_document(
            body_html=item["html"],
            title=item_title,
            doc_code=t_code,
            sop_ref="SOP-DGM-06",
            classification="MASTER TEMPLATE • B2B PARTNER ONBOARDING",
            include_header=True,
        )
        master_templates.append((
            t_code,
            f"[{t_code}] Mẫu Chuẩn: {item_title}",
            f"Master_{t_code}.html",
            branded_html,
        ))

    # 10: TPL-ONB-05 (Master Staff Augmentation SLA & Acceptance Template)
    sample_so = SaleOrder.search([("client_order_ref", "=", "DIGIMATE-AIFIN-VN_2610-001")], limit=1) or SaleOrder.search([], limit=1)
    doc05 = sample_so.action_generate_staff_aug_acceptance_doc(period_label="10/2026", logged_hours=160.0)
    raw_05 = _decode_attachment_html(doc05.attachment_id)
    branded_05 = wrap_dgm_branded_html_document(
        body_html=raw_05,
        title="Hợp đồng & Biên bản Nghiệm thu Dịch vụ Phái cử Nhân sự (Staff Augmentation — SOP-DGM-07)",
        doc_code="TPL-ONB-05",
        sop_ref="SOP-DGM-07",
        classification="MASTER TEMPLATE • STAFF AUGMENTATION SLA",
        include_header=True,
    )
    master_templates.append((
        "TPL-ONB-05",
        "[TPL-ONB-05] Mẫu Chuẩn: Hợp đồng & Biên bản Nghiệm thu Phái cử Nhân sự (Staff Augmentation — SOP-DGM-07)",
        "Master_TPL-ONB-05.html",
        branded_05,
    ))

    # 11: TPL-PRJ-01 (Master Project Kickoff & Resource Allocation Notification Template)
    sample_ntf = Notification.search([("name", "=", "PRJ-NTF-202610-0001")], limit=1) or Notification.search([], limit=1)
    raw_ntf = sample_ntf._render_notification_document_html()
    branded_prj_01 = wrap_dgm_branded_html_document(
        body_html=raw_ntf,
        title="Thông báo Khởi động Dự án & Phân bổ Nhân sự (Project Kickoff & Handover Notification — SOP-DGM-08)",
        doc_code="TPL-PRJ-01",
        sop_ref="SOP-DGM-08",
        classification="MASTER TEMPLATE • PROJECT NOTIFICATION",
        include_header=True,
    )
    master_templates.append((
        "TPL-PRJ-01",
        "[TPL-PRJ-01] Mẫu Chuẩn: Thông báo Khởi động Dự án & Bàn giao Nhân sự (SOP-DGM-08)",
        "Master_TPL-PRJ-01.html",
        branded_prj_01,
    ))

    # 12..14: TPL-PRJ-02..04 (Master Timesheet, Customer Acceptance Certificate, and Draft/Official Invoice 1C26TAA)
    sample_sheet = Sheet.search([("name", "=", "TS-DGM-202610-0001")], limit=1) or Sheet.search([], limit=1)
    prj_stage_defs = [
        (
            "TPL-PRJ-02",
            "timesheet",
            "[TPL-PRJ-02] Mẫu Chuẩn: Bảng Tổng hợp Chấm công Dự án Hàng tháng (Monthly Project Timesheet — SOP-DGM-08)",
        ),
        (
            "TPL-PRJ-03",
            "acceptance",
            "[TPL-PRJ-03] Mẫu Chuẩn: Biên bản Nghiệm thu Khối lượng Công việc & Ký số SHA-256 (Acceptance Certificate — SOP-DGM-08)",
        ),
        (
            "TPL-PRJ-04",
            "official_invoice",
            "[TPL-PRJ-04] Mẫu Chuẩn: Hóa đơn Nháp Đối soát MTI & Hóa đơn GTGT Điện tử 1C26TAA (Draft & Official VAT E-Invoice — SOP-DGM-08)",
        ),
    ]
    for tpl_code, stage_key, doc_title in prj_stage_defs:
        raw_stage = sample_sheet._render_sheet_document_html(doc_stage=stage_key)
        branded_stage = wrap_dgm_branded_html_document(
            body_html=raw_stage,
            title=doc_title,
            doc_code=tpl_code,
            sop_ref="SOP-DGM-08",
            classification="MASTER TEMPLATE • PROJECT BILLING & 1C26TAA",
            include_header=True,
        )
        master_templates.append((
            tpl_code,
            doc_title,
            f"Master_{tpl_code}.html",
            branded_stage,
        ))

    # 15..18: TPL-SW-MTI-01..04 (Master MTI/AIfin Software Co-Development Contract Suite — TT 13/2020)
    mti_rec = mti_partner or Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0001")], limit=1)
    mti_sw_tpls = (
        mti_rec._render_mti_codev_software_templates()
        if mti_rec and hasattr(mti_rec, "_render_mti_codev_software_templates")
        else render_mti_codev_contract_suite("MTI")
    )
    for item in mti_sw_tpls:
        t_code = item["tpl_code"]
        master_templates.append((
            t_code,
            f"[{t_code}] Mẫu Chuẩn: {item['doc_name']}",
            f"Master_{t_code}.html",
            item["html"],
        ))

    # 19..22: TPL-SW-KTT-01..04 (Master KTT Khang Trường Thịnh Turnkey Software Contract Suite — TT 13/2020)
    ktt_rec = ktt_partner or Partner.search([("dgm_partner_code", "=", "PTN-DGM-2026-0008")], limit=1)
    ktt_sw_tpls = (
        ktt_rec._render_ktt_turnkey_software_templates()
        if ktt_rec and hasattr(ktt_rec, "_render_ktt_turnkey_software_templates")
        else render_ktt_turnkey_contract_suite("KTT")
    )
    for item in ktt_sw_tpls:
        t_code = item["tpl_code"]
        master_templates.append((
            t_code,
            f"[{t_code}] Mẫu Chuẩn: {item['doc_name']}",
            f"Master_{t_code}.html",
            item["html"],
        ))

    for tpl_code, doc_title, fname, html_payload in master_templates:
        _upsert_html_doc(
            env,
            folder_id=lib_folder.id,
            doc_name=doc_title,
            filename=fname,
            html_str=html_payload,
            res_model="documents.document",
            res_id=lib_folder.id,
            code_marker=f"[{tpl_code}]",
        )

    print(f"  [Step 6] {dbname}: Seeded {len(master_templates)} Master Standardized Templates in `{MASTER_LIBRARY_FOLDER_NAME}` (folder_id={lib_folder.id}, master_templates={len(master_templates)}).")
    return lib_folder


def step7_seed_sop_dgm_09_knowledge_article(env, dbname):
    """Step 7: Seeds or updates Knowledge Article `SOP-DGM-09` under DGM Knowledge Root (`parent_id = 170` if exists)
    and registers `insilos_al2c.kb_dgm_sop_09_software_contracts` in `ir_model_data`.
    """
    cr = env.cr
    sop09_title = (
        "SOP-DGM-09: Bộ Mẫu Hợp đồng Best-Practice Ưu đãi Thuế Phần mềm (TT 13/2020/TT-BTTTT) — "
        "Cử Nhân sự Cùng Phát triển Dự án Phần mềm (MTI/AIfin) & Dịch vụ Phần mềm Trọn gói (KTT Khang Trường Thịnh)"
    )
    sop09_body = """<div class="o_knowledge_behavior_anchor dgm-sop-container">
<h1>SOP-DGM-09: BỘ MẪU HỢP ĐỒNG BEST-PRACTICE ƯU ĐÃI THUẾ PHẦN MỀM (TT 13/2020/TT-BTTTT) — CỬ NHÂN SỰ CÙNG PHÁT TRIỂN DỰ ÁN PHẦN MỀM (MTI / AIFIN) &amp; DỊCH VỤ PHẦN MỀM TRỌN GÓI (KTT KHANG TRƯỜNG THỊNH)</h1>
<p><strong>Mã quy trình:</strong> <code>SOP-DGM-09</code> | <strong>Phiên bản:</strong> 1.0 (10/2026) | <strong>Pháp nhân áp dụng:</strong> CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: <code>0317958465</code> • Mã ĐV BHXH: <code>TZ0857G</code> • Ký hiệu HĐĐT: <code>1C26TAA</code>)</p>
<hr/>
<h2>1. Khung Pháp lý 07 Công đoạn Sản xuất Phần mềm (Thông tư 13/2020/TT-BTTTT) &amp; Ưu đãi Thuế GTGT / TNDN (Thông tư 219/2013/TT-BTC)</h2>
<ul>
  <li><strong>Thông tư 13/2020/TT-BTTTT (07 Công đoạn Sản xuất Sản phẩm Phần mềm):</strong>
    <ol>
      <li><strong>Công đoạn 1:</strong> Xác định yêu cầu (Requirement Determination — SRS, User Stories, Backlog);</li>
      <li><strong>Công đoạn 2:</strong> Phân tích và thiết kế (Analysis &amp; Architecture Design — TDD, ERD, OpenAPI Spec);</li>
      <li><strong>Công đoạn 3:</strong> Lập trình, viết mã lệnh (Programming &amp; Source Coding — Git Commits, Pull Requests);</li>
      <li><strong>Công đoạn 4:</strong> Kiểm thử, thử nghiệm phần mềm (Software Testing &amp; QA — Unit Test, SIT, UAT Logs);</li>
      <li><strong>Công đoạn 5:</strong> Hoàn thiện, đóng gói sản phẩm phần mềm (Packaging &amp; Release Artifacts);</li>
      <li><strong>Công đoạn 6:</strong> Cài đặt, chuyển giao, hướng dẫn sử dụng, bảo trì, bảo hành phần mềm;</li>
      <li><strong>Công đoạn 7:</strong> Phát hành, phân phối sản phẩm phần mềm (Go-Live / Release).</li>
    </ol>
  </li>
  <li><strong>Khoản 21 Điều 4 Thông tư 219/2013/TT-BTC &amp; Ưu đãi Thuế TNDN:</strong> Sản phẩm phần mềm và dịch vụ phần mềm theo Nghị định 71/2007/NĐ-CP thuộc đối tượng <strong>Không chịu thuế GTGT (KCT)</strong> và được hưởng ưu đãi thuế Thu nhập Doanh nghiệp (TNDN) khi đáp ứng hồ sơ minh chứng Công đoạn 1 &amp; Công đoạn 2 trở lên theo Thông tư 13/2020/TT-BTTTT.</li>
</ul>
<h2>2. Nhóm A — Bộ Mẫu Hợp đồng Cử Nhân sự Cùng Phát triển Dự án Phần mềm (<code>TPL-SW-MTI-01..04</code> • Chuẩn MTI Technology &amp; AIfin)</h2>
<ul>
  <li><strong>Nguyên tắc Pháp lý Cốt lõi:</strong> Tuyệt đối <strong>KHÔNG</strong> ghi nội dung hợp đồng là <em>"cho thuê lại lao động"</em> (raw labor subleasing). Toàn bộ hợp đồng <code>TPL-SW-MTI-01..04</code> được thiết kế chuẩn mực dưới hình thức <strong>"Hợp đồng Hợp tác Phát triển Dự án Phần mềm &amp; Gia công Công đoạn Phần mềm — Cử Nhân sự Kỹ thuật Tham gia Cùng Phát triển Dự án Phần mềm cho Đối tác"</strong>.</li>
  <li><strong>Ánh xạ Minh chứng Kỹ thuật (Git / Jira / Insilos / QA):</strong> Mỗi Kỹ sư Digimate tham gia dự án của MTI (<code>PTN-DGM-2026-0001</code>) hoặc AIfin (<code>PTN-DGM-2026-0007</code>) đều gắn với Công đoạn 1, 2, 3, 4 thông qua lịch sử Git Commits/PRs, mã Ticket Jira/Insilos và Biên bản Nghiệm thu Công đoạn Phần mềm hàng tháng (<code>TPL-SW-MTI-03</code>).</li>
  <li><strong>Danh mục 04 Biểu mẫu Nhóm A:</strong>
    <ul>
      <li><code>TPL-SW-MTI-01</code>: Hợp đồng Khung Hợp tác Phát triển Dự án Phần mềm (12 Điều);</li>
      <li><code>TPL-SW-MTI-02</code>: Phụ lục Đặt hàng (SOW) Cử Nhân sự Kỹ thuật Tham gia Cùng Phát triển Dự án Phần mềm;</li>
      <li><code>TPL-SW-MTI-03</code>: Biên bản Nghiệm thu Công đoạn Phát triển Phần mềm &amp; Hồ sơ Minh chứng TT 13/2020/TT-BTTTT;</li>
      <li><code>TPL-SW-MTI-04</code>: Thỏa thuận Chuyển giao Quyền Sở hữu Trí tuệ Mã nguồn &amp; Bảo mật Dự án Phần mềm (IP &amp; NDA).</li>
    </ul>
  </li>
</ul>
<h2>3. Nhóm B — Bộ Mẫu Hợp đồng Dịch vụ Thiết kế &amp; Xây dựng Phần mềm Trọn gói (<code>TPL-SW-KTT-01..04</code> • Chuẩn KTT Khang Trường Thịnh &amp; AIfin 360-Sales)</h2>
<ul>
  <li><strong>Đối tác Điển hình:</strong> <strong>CÔNG TY TNHH KHANG TRƯỜNG THỊNH</strong> (Mã đối tác: <code>PTN-DGM-2026-0008</code>, MST: <code>0316889922</code>) và <strong>CÔNG TY CỔ PHẦN AIFIN COMPANY GLOBAL</strong> (<code>PTN-DGM-2026-0007</code>).</li>
  <li><strong>Cấu trúc Thương mại &amp; Bảo vệ Pháp lý Best-Practice:</strong>
    <ul>
      <li><strong>Lộ trình Thanh toán Milestone 30% – 40% – 30%:</strong> Đợt 1 Tạm ứng 30% khi ký hợp đồng; Đợt 2 Thanh toán 40% khi bàn giao UAT; Đợt 3 Quyết toán 30% khi nghiệm thu Go-Live và xuất Hóa đơn điện tử <code>1C26TAA</code>.</li>
      <li><strong>Cơ chế Nghiệm thu Mặc nhiên (Deemed Acceptance 05 Ngày làm việc):</strong> Bảo vệ dòng tiền và tiến độ dự án nếu khách hàng quá 05 ngày làm việc không phản hồi danh sách lỗi hoặc đã đưa phần mềm vào vận hành thực tế.</li>
      <li><strong>Chuyển giao Quyền Sở hữu Trí tuệ (IP Transfer) &amp; Bảo hành:</strong> Chuyển giao mã nguồn và quyền SHTT ngay khi khách hàng thanh toán đủ 100% giá trị hợp đồng; cam kết <strong>90 ngày đầu bảo hành khắc phục lỗi khẩn cấp (90-day Bug-Fix Warranty)</strong> và <strong>12 tháng bảo hành tổng thể miễn phí</strong>.</li>
    </ul>
  </li>
  <li><strong>Danh mục 04 Biểu mẫu Nhóm B:</strong>
    <ul>
      <li><code>TPL-SW-KTT-01</code>: Hợp đồng Thiết kế, Xây dựng &amp; Triển khai Phần mềm Trọn gói (14 Điều);</li>
      <li><code>TPL-SW-KTT-02</code>: Phụ lục 01 — Đặc tả Kỹ thuật (SRS), Ma trận Chức năng &amp; Tiêu chí Nghiệm thu UAT Trọn gói;</li>
      <li><code>TPL-SW-KTT-03</code>: Biên bản Nghiệm thu Bàn giao Hệ thống Phần mềm Trọn gói &amp; Hồ sơ 7 Công đoạn TT 13/2020/TT-BTTTT;</li>
      <li><code>TPL-SW-KTT-04</code>: Hợp đồng Dịch vụ Bảo trì, Nâng cấp &amp; Hỗ trợ Kỹ thuật Phần mềm Hàng năm (AMC &amp; SLA).</li>
    </ul>
  </li>
</ul>
</div>"""

    cr.execute(
        "SELECT id FROM knowledge_article WHERE id = 170 OR name ILIKE 'DGM · Quy Trình Vận Hành Chuẩn%' ORDER BY (id = 170) DESC, id ASC LIMIT 1;"
    )
    root_row = cr.fetchone()
    root_kb_id = root_row[0] if root_row else None

    cr.execute("SELECT id FROM knowledge_article WHERE name ILIKE 'SOP-DGM-09%' ORDER BY id ASC LIMIT 1;")
    kb_row = cr.fetchone()
    if kb_row:
        kb09_id = kb_row[0]
        cr.execute(
            """
            UPDATE knowledge_article
               SET name = %s,
                   icon = '📜',
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
            (sop09_title, sop09_body, root_kb_id, root_kb_id, kb09_id),
        )
    else:
        cr.execute(
            """
            INSERT INTO knowledge_article (
                name, icon, body, parent_id, root_article_id,
                internal_permission, category, sequence, active,
                is_article_visible_by_everyone, create_uid, write_uid, create_date, write_date
            ) VALUES (
                %s, '📜', %s, %s, %s,
                'write', 'workspace', 170, TRUE,
                TRUE, 1, 1, NOW(), NOW()
            ) RETURNING id;
            """,
            (sop09_title, sop09_body, root_kb_id, root_kb_id),
        )
        kb09_id = cr.fetchone()[0]

    cr.execute(
        "SELECT id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = 'kb_dgm_sop_09_software_contracts' LIMIT 1;"
    )
    imd_row = cr.fetchone()
    if imd_row:
        cr.execute(
            "UPDATE ir_model_data SET model = 'knowledge.article', res_id = %s, write_date = NOW() WHERE id = %s;",
            (kb09_id, imd_row[0]),
        )
    else:
        cr.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
            VALUES ('insilos_al2c', 'kb_dgm_sop_09_software_contracts', 'knowledge.article', %s, FALSE, 1, 1, NOW(), NOW());
            """,
            (kb09_id,),
        )
    print(f"  [Step 7] {dbname}: Seeded SOP-DGM-09 Knowledge Article (id={kb09_id}, xmlid=insilos_al2c.kb_dgm_sop_09_software_contracts).")
    return kb09_id


def step6_universal_html_brand_footer_sweep_and_cleanup(env, dbname):
    """Universal Brand Footer Sweep across all active HTML documents in `documents.document`,
    load updated QWeb templates (`portal_templates.xml`, `report_templates.xml`),
    and enforce Zero Empty Folders Invariant (`0` empty active folders).
    """
    for xml_rel in (
        "views/portal_templates.xml",
        "views/report_templates.xml",
    ):
        full_xml = os.path.join(ROOT_DIR, "addons/insilos_al2c", xml_rel)
        if os.path.isfile(full_xml):
            convert_file(
                env,
                "insilos_al2c",
                xml_rel,
                {},
                mode="init",
                noupdate=False,
                kind="data",
            )

    Document = env["documents.document"].sudo()
    active_docs = Document.search([
        ("active", "=", True),
        ("type", "!=", "folder"),
    ])
    swept_count = 0
    total_html_count = 0
    for doc in active_docs:
        att = doc.attachment_id
        if not att:
            continue
        is_html = (att.mimetype == "text/html") or (doc.name or "").lower().endswith(".html") or (att.name or "").lower().endswith(".html")
        if not is_html:
            continue
        raw_html = _decode_attachment_html(att)
        if not raw_html:
            continue
        total_html_count += 1
        if 'data-dgm-footer="drive-logo-v1"' not in raw_html or 'data-logo-source="google-drive-logo-folder"' not in raw_html:
            branded_html = wrap_dgm_branded_html_document(
                body_html=raw_html,
                title=doc.name or "Tài liệu Doanh nghiệp Digimate",
                doc_code=f"DGM-DOC-{doc.id}",
                sop_ref="SOP-DGM",
                classification="INTERNAL / B2B CONFIDENTIAL",
                include_header=True,
            )
            att.write({
                "datas": base64.b64encode(branded_html.encode("utf-8")),
                "mimetype": "text/html",
            })
            swept_count += 1
        if doc.owner_id or doc.access_internal not in ("edit", "view"):
            doc.write({"owner_id": False, "access_internal": "edit"})

    # Archive any empty active folders bottom-up (Rule 6)
    for _ in range(5):
        env.cr.execute(
            """
            SELECT f.id
              FROM documents_document f
             WHERE f.type = 'folder' AND f.active = TRUE
               AND NOT EXISTS (
                   SELECT 1 FROM documents_document c
                    WHERE c.folder_id = f.id AND c.active = TRUE
               );
            """
        )
        empty_ids = [r[0] for r in env.cr.fetchall()]
        if not empty_ids:
            break
        env.cr.execute("UPDATE documents_document SET active = FALSE WHERE id = ANY(%s)", (empty_ids,))
        env.invalidate_all()

    print(f"  [Sweep] {dbname}: Universal HTML sweep verified {total_html_count} HTML documents ({swept_count} newly upgraded) & empty_folders=0.")


def seed_database(dbname):
    print(f"\n=== Seeding Standardized Google Drive Logo Templates & SOP-DGM-09 Software Contracts in `{dbname}` ===")
    ensure_pre_registry_columns(dbname)
    reg = Registry.new(dbname)
    with reg.cursor() as cr:
        reg.init_models(cr, ["res.partner"], {"module": "insilos_al2c"}, install=True)
        if hasattr(reg, "_ensure_sovereign_bridges"):
            reg._ensure_sovereign_bridges(cr)
        env = api.Environment(cr, SUPERUSER_ID, {"no_document": True})
        step1_verify_and_repair_drive_logo_folder(env, dbname)
        mti_partner, ktt_partner, _ = step5b_seed_sop09_software_contracts(env, dbname)
        step2_regenerate_partner_onboarding_and_staff_aug_docs(env, dbname)
        step3_regenerate_sop08_notifications_and_timesheet_invoices(env, dbname)
        step4_standardize_hr_employee_documents(env, dbname)
        step5_seed_master_standardized_template_library(env, dbname, mti_partner=mti_partner, ktt_partner=ktt_partner)
        step7_seed_sop_dgm_09_knowledge_article(env, dbname)
        step6_universal_html_brand_footer_sweep_and_cleanup(env, dbname)
        cr.commit()
    print(f"[✓] `{dbname}` standardization & SOP-DGM-09 software contract seeding committed successfully.")


def main():
    _parse_conf()
    target_dbs = sys.argv[1:] if len(sys.argv) > 1 else ["insilos20_dev", "innoria_prod"]
    for dbname in target_dbs:
        seed_database(dbname)
    print("\n=== ALL DIGIMATE STANDARDIZED TEMPLATES, SOP-DGM-09 SOFTWARE CONTRACTS & GOOGLE DRIVE LOGO FOOTERS SEEDED (EXIT 0) ===")


if __name__ == "__main__":
    main()

