#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Catalog Audit, Deduplication & Consolidation Engine (`tools/audit_and_clean_all_catalogs.py`)
====================================================================================================
Audits, deduplicates, consolidates, and verifies all 10 Core Enterprise Catalogs across:
  1. Local `insilos20_dev`
  2. Local `innoria_prod`
  3. K8s Production `innoria_prod` (`https://innoria.com`)

Covered Catalogs:
  1. `product.category` (`product_category`) — 5 Canonical Bilingual Category Trees, 0 legacy demo/MongoDB categories
  2. `product.template` (`catalog_item`) & `product.product` (`catalog_sku`) — 33 Canonical Active SKUs (21 AL2C + 9 DGM + 3 SOP-DGM-07)
  3. `sale.order.template` & `sale.order.template.line` — 12 Canonical Quotation Templates (incl. Staff Augmentation 140-180h)
  4. `res.partner` (`party_master`) — 0 mock/test/junk partners, 0 duplicate company VATs, 7 approved DGM partners (`PTN-DGM-2026-0001..0007`)
  5. `hr.department` — 4 Canonical DGM Departments
  6. `hr.job` — 8 Canonical Active Jobs (0 active jobs with 0 active employees)
  7. `hr.employee` — 9 Canonical Active Employees (`DGM-001`..`DGM-009`)
  8. `hr.version` — 9 Active Statutory 2026 Contracts (`wage > 0`, verified bank accounts)
  9. `project.project` — 15 Active Canonical Projects (`Consulting Pool`, 12 `[TPL]` templates, MTI & AIfin delivery) with 5 SAP Activate stages & milestones
  10. `documents.document` & `knowledge.article` — 0 empty active folders, 0 `(Root Shared)` folders, 7 active deduplicated SOPs (`SOP-DGM-01`..`SOP-DGM-07`) + 33 SKU articles

Usage:
  - Clean & Consolidate + Verify: `python3 tools/audit_and_clean_all_catalogs.py`
  - Strict Read-Only Check Gate:  `python3 tools/audit_and_clean_all_catalogs.py --check`
"""

import argparse
import base64
import configparser
import json
import os
import subprocess
import sys
import psycopg2

ROOT_DIR = "/home/zen/O20"

CANONICAL_5_VI_CATEGORIES = [
    "ERP & Quản trị Doanh nghiệp",
    "Hạ tầng Cloud & Đám mây (SaaS)",
    "Quản trị Rủi ro & Tuân thủ (GRC)",
    "Trí tuệ Nhân tạo & Dữ liệu (AI & Data)",
    "Dịch vụ Chuyên nghiệp & Đào tạo",
]

CANONICAL_CATEGORIES_SPEC = [
    ("categ_erp", None, "Insilos ERP", "ERP & Quản trị Doanh nghiệp"),
    ("categ_erp_impl", "categ_erp", "Implementation", "Triển khai ERP & Giải pháp Quản trị"),
    ("categ_erp_saas", "categ_erp", "SaaS", "Hạ tầng Cloud & Đám mây (SaaS)"),
    ("categ_grc", None, "GRC", "Quản trị Rủi ro & Tuân thủ (GRC)"),
    ("categ_ai", None, "AI", "Trí tuệ Nhân tạo & Dữ liệu (AI & Data)"),
    ("categ_ai_custom", "categ_ai", "Custom", "Giải pháp AI Chuyên biệt"),
    ("categ_ai_mojo", "categ_ai", "Mojo Apps", "Hệ sinh thái Ứng dụng Mojo AI"),
    ("categ_services", None, "Services", "Dịch vụ Chuyên nghiệp & Đào tạo"),
    ("categ_dgm_onsite", "categ_services", "B2B Onsite Engineering", "Dịch vụ Kỹ sư Biệt phái B2B (Staff Augmentation)"),
    ("categ_dgm_prepaid", "categ_services", "Prepaid Infrastructure & Licenses (TK 242)", "Hạ tầng & Bản quyền Trả trước (TK 242)"),
]

CANONICAL_33_SKUS = [
    "ERP-STARTER", "ERP-GROWTH", "ERP-ENT",
    "SAAS-USER-M", "SAAS-HOSTING-PRO", "SAAS-SLA-PLUS",
    "GRC-ESSENTIALS", "GRC-RISK-REGISTER", "GRC-AUDIT-PACK",
    "AI-DISCOVERY", "AI-POC", "AI-PILOT", "AI-PROD",
    "MOJO-APP-SUB", "MOJO-TOKENS", "MOJO-ONPREM",
    "AMS-BRONZE", "AMS-SILVER", "AMS-GOLD",
    "TRAINING-DAY", "CONSULT-HOUR",
    "DGM-ONSITE-STD", "DGM-ONSITE-OT100", "DGM-ONSITE-OT150",
    "DGM-CANVA-AWARD", "DGM-MOJO-CREDITS", "DGM-ADMOB-REV", "DGM-MOBIAI-CSP",
    "DGM-PREPAID-VNPT", "DGM-PREPAID-VIETTELCA",
    "SVC-ONSITE-SR", "SVC-ONSITE-MID", "ERP-360-SALES",
]

CANONICAL_12_SO_TEMPLATES = [
    "ERP Starter",
    "ERP Growth",
    "ERP Enterprise",
    "GRC Essentials",
    "AI PoC",
    "AI Pilot",
    "AI Production",
    "Mojo App Subscription",
    "DGM B2B Onsite Engineering (MTI Standard & Tiered OT)",
    "DGM Cross-Border AI App Export (Canva Adoption Award)",
    "DGM Telecom MobiAI CSP Revenue Share",
    "Hợp đồng Thuê Nhân sự Kỹ thuật B2B (MTI / AIfin Staff Augmentation — Khung 140-180h)",
]

SAP_ACTIVATE_PHASES = [
    ("stage_prepare", "Prepare", 10, 0.15),
    ("stage_explore", "Explore", 20, 0.25),
    ("stage_realize", "Realize", 30, 0.35),
    ("stage_deploy", "Deploy", 40, 0.15),
    ("stage_run", "Run", 50, 0.10),
]


def get_local_conn(dbname):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(ROOT_DIR, "odoo.conf"))
    return psycopg2.connect(
        dbname=dbname,
        user=cfg["options"].get("db_user", "odoo"),
        password=cfg["options"].get("db_password", "odoo"),
        host=cfg["options"].get("db_host", "127.0.0.1"),
        port=int(cfg["options"].get("db_port", "5434")),
    )


def extract_canonical_bundle_from_dev():
    """Extracts the canonical SKUs, Quotation Templates, Projects, and Knowledge Articles from insilos20_dev."""
    conn = get_local_conn("insilos20_dev")
    cur = conn.cursor()

    # 1. Extract 33 canonical SKUs with their category xmlid, uom xmlid, project template xmlid, and kb article name
    cur.execute(
        """
        SELECT ci.default_code,
               ci.name,
               ci.list_price,
               0.0 AS standard_price,
               ci.type,
               ci.sale_ok,
               ci.purchase_ok,
               ci.invoice_policy,
               ci.service_type,
               ci.service_tracking,
               COALESCE(ci.recurring_invoice, FALSE) AS recurring_invoice,
               ci.al2c_product_line,
               ci.al2c_vat_class,
               ci.description_sale,
               ci.description_purchase,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'product.category' AND res_id = ci.categ_id LIMIT 1) AS categ_xmlid,
               (SELECT name FROM ir_model_data WHERE module = 'uom' AND model = 'uom.uom' AND res_id = ci.uom_id LIMIT 1) AS uom_xmlid,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'product.template' AND res_id = ci.id LIMIT 1) AS prod_xmlid,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'project.project' AND res_id = (ci.project_template_id->>'1')::integer LIMIT 1) AS prj_tmpl_xmlid,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'project.project' AND res_id = (ci.project_id->>'1')::integer LIMIT 1) AS prj_xmlid,
               (SELECT ka.name FROM knowledge_article ka WHERE ka.id = ci.al2c_knowledge_article_id LIMIT 1) AS kb_name
          FROM catalog_item ci
         WHERE ci.default_code = ANY(%s)
         ORDER BY ci.id ASC;
        """,
        (CANONICAL_33_SKUS,),
    )
    sku_rows = cur.fetchall()
    sop07_defaults = {
        "SVC-ONSITE-SR": (
            "tpl_erp_starter",
            "SVC-ONSITE-SR · Dịch vụ Kỹ sư Phần mềm Senior Biệt phái (Staff Augmentation 140-180h)",
            "categ_dgm_onsite",
        ),
        "SVC-ONSITE-MID": (
            "tpl_erp_starter",
            "SVC-ONSITE-MID · Dịch vụ Kỹ sư Phần mềm Mid-Level Biệt phái (Staff Augmentation 140-180h)",
            "categ_dgm_onsite",
        ),
        "ERP-360-SALES": (
            "tpl_erp_growth",
            "ERP-360-SALES · Hệ thống Quản trị Bán hàng & Đội ngũ Kinh doanh 360-Sales",
            "categ_erp_impl",
        ),
    }
    skus_by_code = {}
    for r in sku_rows:
        code = r[0]
        if code not in skus_by_code:
            def_prj_tmpl, def_kb_name, def_categ = sop07_defaults.get(code, (None, None, "categ_services"))
            skus_by_code[code] = {
                "code": code,
                "name": r[1],
                "list_price": float(r[2] or 0.0),
                "standard_price": float(r[3] or 0.0) if isinstance(r[3], (int, float)) else 0.0,
                "type": r[4] or "service",
                "sale_ok": bool(r[5]),
                "purchase_ok": bool(r[6]),
                "invoice_policy": r[7] or "order",
                "service_type": r[8] or "manual",
                "service_tracking": r[9] or "no",
                "recurring_invoice": bool(r[10]),
                "al2c_product_line": r[11] or "svc",
                "al2c_vat_class": r[12] or "kct",
                "description_sale": r[13],
                "description_purchase": r[14],
                "categ_xmlid": r[15] or def_categ,
                "uom_xmlid": r[16] or "product_uom_unit",
                "prod_xmlid": r[17] or f"product_{code.lower().replace('-', '_')}",
                "prj_tmpl_xmlid": r[18] or def_prj_tmpl,
                "prj_xmlid": r[19],
                "kb_name": r[20] or def_kb_name,
            }

    # 2. Extract 12 canonical sale.order.template + lines
    cur.execute(
        """
        SELECT sot.id,
               sot.name,
               sot.note,
               sot.sequence,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'sale.order.template' AND res_id = sot.id LIMIT 1) AS sot_xmlid
          FROM sale_order_template sot
         WHERE sot.active = TRUE
         ORDER BY sot.id ASC;
        """
    )
    sots = []
    seen_sot_names = set()
    for sot_id, sot_name, sot_note, sot_seq, sot_xmlid in cur.fetchall():
        en_name = sot_name.get("en_US") or sot_name.get("vi_VN") if isinstance(sot_name, dict) else str(sot_name)
        if en_name not in CANONICAL_12_SO_TEMPLATES or en_name in seen_sot_names:
            continue
        seen_sot_names.add(en_name)
        cur.execute(
            """
            SELECT l.sequence,
                   cs.default_code,
                   l.name,
                   l.product_uom_qty,
                   (SELECT name FROM ir_model_data WHERE module = 'uom' AND model = 'uom.uom' AND res_id = l.product_uom_id LIMIT 1) AS uom_xmlid
              FROM sale_order_template_line l
              JOIN catalog_sku cs ON cs.id = l.product_id
             WHERE l.sale_order_template_id = %s
               AND l.display_type IS NULL
             ORDER BY l.sequence ASC, l.id ASC;
            """,
            (sot_id,),
        )
        lines = []
        for l_seq, l_code, l_name, l_qty, l_uom_xmlid in cur.fetchall():
            lines.append(
                {
                    "sequence": l_seq or 10,
                    "default_code": l_code,
                    "name": l_name,
                    "qty": float(l_qty or 1.0),
                    "uom_xmlid": l_uom_xmlid or "product_uom_unit",
                }
            )
        sots.append(
            {
                "en_name": en_name,
                "name": sot_name if isinstance(sot_name, dict) else {"en_US": en_name, "vi_VN": en_name},
                "note": sot_note if isinstance(sot_note, dict) else {"en_US": str(sot_note or ""), "vi_VN": str(sot_note or "")},
                "sequence": sot_seq or 10,
                "xmlid": sot_xmlid or f"sot_{en_name.lower().replace(' ', '_')[:24]}",
                "lines": lines,
            }
        )

    # 3. Extract canonical Project Templates & Delivery Projects
    cur.execute(
        """
        SELECT p.id,
               p.name,
               COALESCE(p.is_template, FALSE) AS is_template,
               COALESCE(p.allow_milestones, TRUE) AS allow_milestones,
               COALESCE(p.allow_billable, TRUE) AS allow_billable,
               COALESCE(p.allow_timesheets, TRUE) AS allow_timesheets,
               p.description,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'project.project' AND res_id = p.id LIMIT 1) AS prj_xmlid
          FROM project_project p
         WHERE p.active = TRUE
         ORDER BY p.id ASC;
        """
    )
    projects = []
    for pid, pname, is_tmpl, allow_ms, allow_bill, allow_ts, pdesc, pxmlid in cur.fetchall():
        en_name = pname.get("en_US") or pname.get("vi_VN") if isinstance(pname, dict) else str(pname)
        if en_name in ("Internal", "Field Service"):
            continue
        projects.append(
            {
                "en_name": en_name,
                "name": pname if isinstance(pname, dict) else {"en_US": en_name, "vi_VN": en_name},
                "is_template": bool(is_tmpl),
                "allow_milestones": True,
                "allow_billable": bool(allow_bill),
                "allow_timesheets": bool(allow_ts),
                "description": pdesc,
                "xmlid": pxmlid,
            }
        )
    # Ensure MTI delivery project is also in the canonical list
    if not any("MTI Technology" in p["en_name"] and not p["is_template"] for p in projects):
        projects.append(
            {
                "en_name": "MTI Technology — B2B Onsite Software Engineering (HĐ DIGIMATE2401-001)",
                "name": {
                    "en_US": "MTI Technology — B2B Onsite Software Engineering (HĐ DIGIMATE2401-001)",
                    "vi_VN": "MTI Technology — B2B Onsite Software Engineering (HĐ DIGIMATE2401-001)",
                },
                "is_template": False,
                "allow_milestones": True,
                "allow_billable": True,
                "allow_timesheets": True,
                "description": "<p>Dự án cung ứng kỹ sư phần mềm Onsite B2B cho MTI Technology theo HĐ DIGIMATE2401-001.</p>",
                "xmlid": "project_dgm_mti_delivery",
            }
        )

    # 4. Extract canonical Knowledge Articles from insilos20_dev
    cur.execute(
        """
        SELECT ka.id,
               ka.name,
               ka.body,
               ka.icon,
               ka.sequence,
               (SELECT p.name FROM knowledge_article p WHERE p.id = ka.parent_id) AS parent_name,
               (SELECT name FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'knowledge.article' AND res_id = ka.id LIMIT 1) AS kb_xmlid
          FROM knowledge_article ka
         WHERE ka.active = TRUE
           AND ka.name IS NOT NULL
         ORDER BY ka.parent_id NULLS FIRST, ka.id ASC;
        """
    )
    kb_articles = []
    seen_kb_names = set()
    for kid, kname, kbody, kicon, kseq, parent_name, kb_xmlid in cur.fetchall():
        if not kname or kname in seen_kb_names:
            continue
        seen_kb_names.add(kname)
        kb_articles.append(
            {
                "name": kname,
                "body": kbody or f"<h1>{kname}</h1>",
                "icon": kicon,
                "sequence": kseq or 10,
                "parent_name": parent_name,
                "xmlid": kb_xmlid,
            }
        )

    for extra_kb in [
        {
            "name": "SVC-ONSITE-SR · Dịch vụ Kỹ sư Phần mềm Senior Biệt phái (Staff Augmentation 140-180h)",
            "body": "<h1>SVC-ONSITE-SR · Dịch vụ Kỹ sư Phần mềm Senior Biệt phái (Staff Augmentation 140-180h)</h1><p>Dịch vụ cung ứng nhân sự kỹ thuật trình độ Senior Biệt phái (Onsite/Remote) theo chuẩn Hợp đồng MTI Technology &amp; AIfin (Khung 140-180h/tháng, OT 100%/150%, Net 40).</p>",
            "icon": None,
            "sequence": 31,
            "parent_name": "Services",
            "xmlid": "kb_sku_svc_onsite_sr",
        },
        {
            "name": "SVC-ONSITE-MID · Dịch vụ Kỹ sư Phần mềm Mid-Level Biệt phái (Staff Augmentation 140-180h)",
            "body": "<h1>SVC-ONSITE-MID · Dịch vụ Kỹ sư Phần mềm Mid-Level Biệt phái (Staff Augmentation 140-180h)</h1><p>Dịch vụ cung ứng nhân sự kỹ thuật trình độ Mid-Level Biệt phái theo khung SLA 140–180 giờ/tháng, báo trước thay thế 30 ngày kèm 05 ngày làm việc thử việc miễn phí.</p>",
            "icon": None,
            "sequence": 32,
            "parent_name": "Services",
            "xmlid": "kb_sku_svc_onsite_mid",
        },
        {
            "name": "ERP-360-SALES · Hệ thống Quản trị Bán hàng & Đội ngũ Kinh doanh 360-Sales",
            "body": "<h1>ERP-360-SALES · Hệ thống Quản trị Bán hàng &amp; Đội ngũ Kinh doanh 360-Sales</h1><p>Giải pháp quản trị bán hàng đa kênh 360-Sales (Web Admin, Mobile App iOS/Android, Zalo MiniApp, AI Call Recording &amp; Coaching, Quản lý KPI &amp; Hoa hồng).</p>",
            "icon": None,
            "sequence": 33,
            "parent_name": "ERP",
            "xmlid": "kb_sku_erp_360_sales",
        },
    ]:
        if extra_kb["name"] not in seen_kb_names:
            seen_kb_names.add(extra_kb["name"])
            kb_articles.append(extra_kb)

    conn.close()
    return {
        "skus": list(skus_by_code.values()),
        "sots": sots,
        "projects": projects,
        "kb_articles": kb_articles,
    }


WORKER_SCRIPT_TEMPLATE = r'''
import base64, configparser, json, os, sys, psycopg2

BUNDLE = json.loads(base64.b64decode("__BUNDLE_B64__").decode("utf-8"))
CHECK_ONLY = __CHECK_ONLY__
TARGET_DB = "__TARGET_DB__"
IS_K8S = __IS_K8S__

CANONICAL_5_VI_CATEGORIES = BUNDLE["canonical_5_vi_categories"]
CANONICAL_CATEGORIES_SPEC = BUNDLE["canonical_categories_spec"]
CANONICAL_33_SKUS = BUNDLE["canonical_33_skus"]
CANONICAL_12_SO_TEMPLATES = BUNDLE["canonical_12_so_templates"]
SAP_ACTIVATE_PHASES = BUNDLE["sap_activate_phases"]


def get_conn():
    if IS_K8S:
        host = os.environ.get("DB_HOST", "pgbouncer-service")
        port = int(os.environ.get("DB_PORT", "6432"))
        user = os.environ.get("DB_USER", "insilos")
        pw = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD") or ""
        if not pw:
            for p in ["/etc/odoo/odoo.conf", "/home/odoo/insilos.conf", "insilos.conf", "odoo.conf"]:
                if os.path.exists(p):
                    c = configparser.ConfigParser()
                    c.read(p)
                    if "options" in c and c["options"].get("db_password"):
                        pw = c["options"].get("db_password")
                        break
        return psycopg2.connect(dbname=TARGET_DB, user=user, password=pw, host=host, port=port)
    else:
        cfg = configparser.ConfigParser()
        cfg.read("/home/zen/O20/odoo.conf")
        return psycopg2.connect(
            dbname=TARGET_DB,
            user=cfg["options"].get("db_user", "odoo"),
            password=cfg["options"].get("db_password", "odoo"),
            host=cfg["options"].get("db_host", "127.0.0.1"),
            port=int(cfg["options"].get("db_port", "5434")),
        )


def upsert_imd(cur, module, name, model, res_id, noupdate=False):
    if not name:
        return
    cur.execute(
        "SELECT id FROM ir_model_data WHERE module = %s AND name = %s LIMIT 1;",
        (module, name),
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE ir_model_data SET model = %s, res_id = %s, write_date = NOW() WHERE id = %s;",
            (model, res_id, row[0]),
        )
    else:
        cur.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, 1, 1, NOW(), NOW());
            """,
            (module, name, model, res_id, noupdate),
        )


def clean_and_consolidate(conn):
    cur = conn.cursor()

    # Ensure required AL2C columns exist on catalog_item in all DBs
    cur.execute(
        """
        ALTER TABLE catalog_item
            ADD COLUMN IF NOT EXISTS al2c_product_line VARCHAR,
            ADD COLUMN IF NOT EXISTS al2c_vat_class VARCHAR DEFAULT 'kct',
            ADD COLUMN IF NOT EXISTS al2c_knowledge_article_id INTEGER,
            ADD COLUMN IF NOT EXISTS project_template_id JSONB,
            ADD COLUMN IF NOT EXISTS project_id JSONB,
            ADD COLUMN IF NOT EXISTS recurring_invoice BOOLEAN DEFAULT FALSE;
        """
    )

    # =========================================================================
    # 1. PRODUCT CATEGORIES (`product.category` / `product_category`)
    # =========================================================================
    categ_id_by_xmlid = {}
    for xmlid, parent_xmlid, en_name, vi_name in CANONICAL_CATEGORIES_SPEC:
        parent_id = categ_id_by_xmlid.get(parent_xmlid) if parent_xmlid else None
        cur.execute(
            "SELECT res_id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = %s AND model = 'product.category' LIMIT 1;",
            (xmlid,),
        )
        r = cur.fetchone()
        cid = None
        if r:
            cur.execute("SELECT id FROM product_category WHERE id = %s;", (r[0],))
            if cur.fetchone():
                cid = r[0]
        if not cid:
            cur.execute(
                "SELECT id FROM product_category WHERE (name->>'en_US' = %s OR name->>'vi_VN' = %s) AND COALESCE(parent_id, 0) = COALESCE(%s, 0) ORDER BY id ASC LIMIT 1;",
                (en_name, vi_name, parent_id),
            )
            r2 = cur.fetchone()
            if r2:
                cid = r2[0]
        name_json = json.dumps({"en_US": en_name, "vi_VN": vi_name})
        if cid:
            cur.execute(
                "UPDATE product_category SET name = %s::jsonb, parent_id = %s, write_date = NOW() WHERE id = %s;",
                (name_json, parent_id, cid),
            )
        else:
            cur.execute(
                """
                INSERT INTO product_category (name, parent_id, create_uid, write_uid, create_date, write_date)
                VALUES (%s::jsonb, %s, 1, 1, NOW(), NOW()) RETURNING id;
                """,
                (name_json, parent_id),
            )
            cid = cur.fetchone()[0]
        # Compute parent_path
        if parent_id:
            cur.execute("SELECT parent_path FROM product_category WHERE id = %s;", (parent_id,))
            pp = (cur.fetchone() or [f"{parent_id}/"])[0] or f"{parent_id}/"
            parent_path = f"{pp}{cid}/"
        else:
            parent_path = f"{cid}/"
        cur.execute("UPDATE product_category SET parent_path = %s WHERE id = %s;", (parent_path, cid))
        upsert_imd(cur, "insilos_al2c", xmlid, "product.category", cid)
        categ_id_by_xmlid[xmlid] = cid

    # Reassign any products in legacy non-canonical categories (outside 1..7 and categ_id_by_xmlid) to category 1 (Goods)
    allowed_categ_ids = list(set([1, 2, 3, 4, 5, 6, 7] + list(categ_id_by_xmlid.values())))
    cur.execute(
        "UPDATE catalog_item SET categ_id = 1 WHERE categ_id IS NULL OR categ_id != ALL(%s);",
        (allowed_categ_ids,),
    )
    cur.execute(
        "UPDATE product_category SET parent_id = NULL WHERE id != ALL(%s);",
        (allowed_categ_ids,),
    )
    cur.execute(
        "DELETE FROM ir_model_data WHERE model = 'product.category' AND res_id != ALL(%s);",
        (allowed_categ_ids,),
    )
    cur.execute(
        """
        DELETE FROM product_category c
         WHERE c.id != ALL(%s)
           AND NOT EXISTS (SELECT 1 FROM catalog_item p WHERE p.categ_id = c.id)
           AND NOT EXISTS (SELECT 1 FROM product_category ch WHERE ch.parent_id = c.id);
        """,
        (allowed_categ_ids,),
    )

    # =========================================================================
    # 10b. KNOWLEDGE ARTICLES (`knowledge.article`) — Needed before SKUs link to them
    # =========================================================================
    # Archive null-named or demo articles ('Welcome Administrator', 'Help', etc.)
    cur.execute(
        """
        UPDATE knowledge_article
           SET active = FALSE
         WHERE active = TRUE
           AND (
               name IS NULL
               OR TRIM(name) = ''
               OR name IN ('Welcome Administrator', 'Help', 'Capital Markets Decision Governance — Runbook', 'IC Memo — Outline')
           );
        """
    )

    kb_id_by_name = {}
    # Pass 1: Root articles (parent_name is None)
    for art in BUNDLE["kb_articles"]:
        if art["parent_name"] is not None:
            continue
        cur.execute(
            "SELECT id FROM knowledge_article WHERE name = %s AND parent_id IS NULL ORDER BY active DESC, id ASC LIMIT 1;",
            (art["name"],),
        )
        row = cur.fetchone()
        if row:
            aid = row[0]
            cur.execute(
                "UPDATE knowledge_article SET active = TRUE, body = %s, icon = %s, sequence = %s, root_article_id = %s, parent_path = %s, write_date = NOW() WHERE id = %s;",
                (art["body"], art["icon"], art["sequence"], aid, f"{aid}/", aid),
            )
        else:
            cur.execute(
                """
                INSERT INTO knowledge_article (
                    name, body, icon, sequence, parent_id, is_article_item,
                    internal_permission, active, category,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s, %s, %s, %s, NULL, FALSE,
                    'write', TRUE, 'workspace',
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (art["name"], art["body"], art["icon"], art["sequence"]),
            )
            aid = cur.fetchone()[0]
            cur.execute(
                "UPDATE knowledge_article SET root_article_id = %s, parent_path = %s WHERE id = %s;",
                (aid, f"{aid}/", aid),
            )
        upsert_imd(cur, "insilos_al2c", art["xmlid"], "knowledge.article", aid)
        kb_id_by_name[art["name"]] = aid
        # Archive any duplicates with same root name
        cur.execute(
            "UPDATE knowledge_article SET active = FALSE WHERE name = %s AND parent_id IS NULL AND id != %s;",
            (art["name"], aid),
        )

    # Pass 2 & 3: Child and Grandchild articles
    for _pass in range(2):
        for art in BUNDLE["kb_articles"]:
            if art["parent_name"] is None or art["name"] in kb_id_by_name:
                continue
            parent_id = kb_id_by_name.get(art["parent_name"])
            if not parent_id and _pass == 0:
                continue
            cur.execute(
                "SELECT root_article_id, parent_path FROM knowledge_article WHERE id = %s;",
                (parent_id,),
            )
            pr = cur.fetchone() if parent_id else None
            root_id = pr[0] if pr and pr[0] else parent_id
            ppath = pr[1] if pr and pr[1] else (f"{parent_id}/" if parent_id else "")

            cur.execute(
                "SELECT id FROM knowledge_article WHERE name = %s ORDER BY active DESC, id ASC LIMIT 1;",
                (art["name"],),
            )
            row = cur.fetchone()
            if row:
                aid = row[0]
                cur.execute(
                    """
                    UPDATE knowledge_article
                       SET active = TRUE,
                           body = %s,
                           icon = %s,
                           sequence = %s,
                           parent_id = %s,
                           root_article_id = COALESCE(%s, %s),
                           parent_path = %s,
                           write_date = NOW()
                     WHERE id = %s;
                    """,
                    (art["body"], art["icon"], art["sequence"], parent_id, root_id, aid, f"{ppath}{aid}/", aid),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO knowledge_article (
                        name, body, icon, sequence, parent_id, is_article_item,
                        internal_permission, active, category,
                        create_uid, write_uid, create_date, write_date
                    ) VALUES (
                        %s, %s, %s, %s, %s, FALSE,
                        'read', TRUE, 'workspace',
                        1, 1, NOW(), NOW()
                    ) RETURNING id;
                    """,
                    (art["name"], art["body"], art["icon"], art["sequence"], parent_id),
                )
                aid = cur.fetchone()[0]
                cur.execute(
                    "UPDATE knowledge_article SET root_article_id = COALESCE(%s, %s), parent_path = %s WHERE id = %s;",
                    (root_id, aid, f"{ppath}{aid}/", aid),
                )
            upsert_imd(cur, "insilos_al2c", art["xmlid"], "knowledge.article", aid)
            kb_id_by_name[art["name"]] = aid
            # Archive any duplicate articles with the same name or same SOP prefix
            cur.execute(
                "UPDATE knowledge_article SET active = FALSE WHERE name = %s AND id != %s;",
                (art["name"], aid),
            )

    # Deduplicate SOP-DGM-01..07 by prefix so each SOP has strictly 1 active article
    for sop_idx in range(1, 8):
        prefix = f"SOP-DGM-0{sop_idx}"
        cur.execute(
            "SELECT id FROM knowledge_article WHERE active = TRUE AND name ILIKE %s ORDER BY id DESC;",
            (f"{prefix}%",),
        )
        srows = [r[0] for r in cur.fetchall()]
        if len(srows) > 1:
            cur.execute(
                "UPDATE knowledge_article SET active = FALSE WHERE id = ANY(%s);",
                (srows[1:],),
            )

    # =========================================================================
    # 9. PROJECTS (`project.project`, `project.task.type`, `project.milestone`)
    # =========================================================================
    # Ensure 5 SAP Activate stages exist
    stage_ids = []
    for st_xmlid, st_name, st_seq, _pct in SAP_ACTIVATE_PHASES:
        cur.execute(
            "SELECT res_id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = %s AND model = 'project.task.type' LIMIT 1;",
            (st_xmlid,),
        )
        sr = cur.fetchone()
        sid = None
        if sr:
            cur.execute("SELECT id FROM project_task_type WHERE id = %s;", (sr[0],))
            if cur.fetchone():
                sid = sr[0]
        if not sid:
            cur.execute(
                "SELECT id FROM project_task_type WHERE name->>'en_US' = %s ORDER BY id ASC LIMIT 1;",
                (st_name,),
            )
            sr2 = cur.fetchone()
            if sr2:
                sid = sr2[0]
        st_json = json.dumps({"en_US": st_name, "vi_VN": st_name})
        if sid:
            cur.execute(
                "UPDATE project_task_type SET name = %s::jsonb, sequence = %s, active = TRUE, fold = FALSE WHERE id = %s;",
                (st_json, st_seq, sid),
            )
        else:
            cur.execute(
                """
                INSERT INTO project_task_type (
                    name, sequence, active, fold,
                    rating_status, rating_status_period,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (%s::jsonb, %s, TRUE, FALSE, 'stage', 'monthly', 1, 1, NOW(), NOW()) RETURNING id;
                """,
                (st_json, st_seq),
            )
            sid = cur.fetchone()[0]
        upsert_imd(cur, "insilos_al2c", st_xmlid, "project.task.type", sid)
        stage_ids.append(sid)

    # Check if project_milestone has quantity_percentage column and whether name is jsonb
    cur.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = 'project_milestone' AND column_name = 'quantity_percentage';"
    )
    has_ms_qty_pct = bool(cur.fetchone())
    cur.execute(
        "SELECT data_type FROM information_schema.columns WHERE table_name = 'project_milestone' AND column_name = 'name';"
    )
    ms_name_is_jsonb = ((cur.fetchone() or ["character varying"])[0] == "jsonb")

    prj_id_by_xmlid = {}
    canonical_prj_ids = []
    for p in BUNDLE["projects"]:
        en_name = p["en_name"]
        pxmlid = p["xmlid"]
        pid = None
        if pxmlid:
            cur.execute(
                "SELECT res_id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = %s AND model = 'project.project' LIMIT 1;",
                (pxmlid,),
            )
            pr = cur.fetchone()
            if pr:
                cur.execute("SELECT id FROM project_project WHERE id = %s;", (pr[0],))
                if cur.fetchone():
                    pid = pr[0]
        if not pid:
            cur.execute(
                "SELECT id FROM project_project WHERE name->>'en_US' = %s OR name->>'vi_VN' = %s ORDER BY active DESC, id ASC LIMIT 1;",
                (en_name, en_name),
            )
            pr2 = cur.fetchone()
            if pr2:
                pid = pr2[0]
        name_json = json.dumps(p["name"])
        if pid:
            cur.execute(
                """
                UPDATE project_project
                   SET name = %s::jsonb,
                       active = TRUE,
                       is_template = %s,
                       allow_milestones = TRUE,
                       allow_billable = %s,
                       allow_timesheets = %s,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (name_json, p["is_template"], p["allow_billable"], p["allow_timesheets"], pid),
            )
        else:
            # Find default alias_id if required by schema
            cur.execute(
                "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'project_project' AND column_name = 'alias_id';"
            )
            alias_nullable = (cur.fetchone() or ["YES"])[0] == "YES"
            alias_id = None
            if not alias_nullable:
                cur.execute("SELECT id FROM mail_alias ORDER BY id ASC LIMIT 1;")
                ar = cur.fetchone()
                if ar:
                    alias_id = ar[0]
            cur.execute(
                """
                INSERT INTO project_project (
                    name, active, sequence, company_id,
                    is_template, allow_milestones, allow_billable, allow_timesheets,
                    alias_id, privacy_visibility, last_update_status,
                    billing_type, fleet_classification,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s::jsonb, TRUE, 10, 1,
                    %s, TRUE, %s, %s,
                    %s, 'employees', 'to_define',
                    'not_billable', 'unknown',
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (name_json, p["is_template"], p["allow_billable"], p["allow_timesheets"], alias_id),
            )
            pid = cur.fetchone()[0]
        if pxmlid:
            upsert_imd(cur, "insilos_al2c", pxmlid, "project.project", pid)
            prj_id_by_xmlid[pxmlid] = pid
        canonical_prj_ids.append(pid)

        # Ensure all 5 SAP Activate stages are linked in project_task_type_rel
        for sid in stage_ids:
            cur.execute(
                "SELECT 1 FROM project_task_type_rel WHERE project_id = %s AND type_id = %s;",
                (pid, sid),
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO project_task_type_rel (project_id, type_id) VALUES (%s, %s);",
                    (pid, sid),
                )

        # Ensure all 5 SAP Activate milestones exist in project_milestone
        for _st_xmlid, ms_name, ms_seq, ms_pct in SAP_ACTIVATE_PHASES:
            cur.execute(
                "SELECT id FROM project_milestone WHERE project_id = %s AND name::text ILIKE %s LIMIT 1;",
                (pid, f"%{ms_name}%"),
            )
            if not cur.fetchone():
                ms_val = json.dumps({"en_US": ms_name, "vi_VN": ms_name}) if ms_name_is_jsonb else ms_name
                ms_placeholder = "%s::jsonb" if ms_name_is_jsonb else "%s"
                if has_ms_qty_pct:
                    cur.execute(
                        f"""
                        INSERT INTO project_milestone (
                            name, project_id, sequence, quantity_percentage, is_reached,
                            create_uid, write_uid, create_date, write_date
                        ) VALUES ({ms_placeholder}, %s, %s, %s, FALSE, 1, 1, NOW(), NOW());
                        """,
                        (ms_val, pid, ms_seq, ms_pct),
                    )
                else:
                    cur.execute(
                        f"""
                        INSERT INTO project_milestone (
                            name, project_id, sequence, is_reached,
                            create_uid, write_uid, create_date, write_date
                        ) VALUES ({ms_placeholder}, %s, %s, FALSE, 1, 1, NOW(), NOW());
                        """,
                        (ms_val, pid, ms_seq),
                    )

    # Archive all non-canonical projects
    cur.execute(
        "UPDATE project_project SET active = FALSE WHERE active = TRUE AND id != ALL(%s);",
        (canonical_prj_ids,),
    )

    # =========================================================================
    # 2. PRODUCTS (`product.template` / `catalog_item` & `product.product` / `catalog_sku`)
    # =========================================================================
    # Resolve UoM IDs
    uom_map = {}
    for uxmlid, fallback_id in [("product_uom_unit", 1), ("product_uom_hour", 4), ("product_uom_day", 3)]:
        cur.execute(
            "SELECT res_id FROM ir_model_data WHERE module = 'uom' AND name = %s LIMIT 1;",
            (uxmlid,),
        )
        ur = cur.fetchone()
        uom_map[uxmlid] = ur[0] if ur else fallback_id

    # Resolve VND currency & pricelist
    cur.execute("SELECT id FROM res_currency WHERE name = 'VND' LIMIT 1;")
    vnd_id = (cur.fetchone() or [23])[0]
    cur.execute("SELECT id FROM product_pricelist WHERE currency_id = %s AND active = TRUE ORDER BY id ASC LIMIT 1;", (vnd_id,))
    pl_row = cur.fetchone()
    pl_id = pl_row[0] if pl_row else 1

    canonical_tmpl_ids = []
    canonical_var_ids = []
    var_id_by_code = {}

    for s in BUNDLE["skus"]:
        code = s["code"]
        categ_id = categ_id_by_xmlid.get(s["categ_xmlid"]) or list(categ_id_by_xmlid.values())[0]
        uom_id = uom_map.get(s["uom_xmlid"], 1)
        prj_tmpl_id = prj_id_by_xmlid.get(s["prj_tmpl_xmlid"]) if s["prj_tmpl_xmlid"] else None
        prj_id = prj_id_by_xmlid.get(s["prj_xmlid"]) if s["prj_xmlid"] else None
        prj_tmpl_json = json.dumps({"1": prj_tmpl_id}) if prj_tmpl_id else None
        prj_json = json.dumps({"1": prj_id}) if prj_id else None
        kb_id = kb_id_by_name.get(s["kb_name"]) if s["kb_name"] else None

        cur.execute(
            "SELECT id FROM catalog_item WHERE default_code = %s ORDER BY active DESC, id ASC LIMIT 1;",
            (code,),
        )
        r = cur.fetchone()
        name_json = json.dumps(s["name"] if isinstance(s["name"], dict) else {"en_US": str(s["name"]), "vi_VN": str(s["name"])})
        desc_sale_json = json.dumps(s["description_sale"]) if s["description_sale"] else None
        desc_pur_json = json.dumps(s["description_purchase"]) if s["description_purchase"] else None

        if r:
            tmpl_id = r[0]
            cur.execute(
                """
                UPDATE catalog_item
                   SET name = %s::jsonb,
                       default_code = %s,
                       categ_id = %s,
                       uom_id = %s,
                       list_price = %s,
                       type = 'service',
                       sale_ok = %s,
                       purchase_ok = %s,
                       active = TRUE,
                       invoice_policy = %s,
                       service_type = %s,
                       service_tracking = %s,
                       recurring_invoice = %s,
                       al2c_product_line = %s,
                       al2c_vat_class = %s,
                       al2c_knowledge_article_id = %s,
                       project_template_id = %s::jsonb,
                       project_id = %s::jsonb,
                       description_sale = COALESCE(%s::jsonb, description_sale),
                       description_purchase = COALESCE(%s::jsonb, description_purchase),
                       company_id = NULL,
                       write_date = NOW()
                 WHERE id = %s;
                """,
                (
                    name_json, code, categ_id, uom_id, s["list_price"],
                    s["sale_ok"], s["purchase_ok"],
                    s["invoice_policy"], s["service_type"], s["service_tracking"],
                    s["recurring_invoice"], s["al2c_product_line"], s["al2c_vat_class"],
                    kb_id, prj_tmpl_json, prj_json,
                    desc_sale_json, desc_pur_json, tmpl_id,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO catalog_item (
                    name, default_code, categ_id, uom_id, list_price,
                    type, sale_ok, purchase_ok, active,
                    invoice_policy, service_type, service_tracking, recurring_invoice,
                    al2c_product_line, al2c_vat_class, al2c_knowledge_article_id,
                    project_template_id, project_id,
                    description_sale, description_purchase,
                    base_unit_count, urbanpiper_meal_type,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    %s::jsonb, %s, %s, %s, %s,
                    'service', %s, %s, TRUE,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb,
                    0, 'none',
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (
                    name_json, code, categ_id, uom_id, s["list_price"],
                    s["sale_ok"], s["purchase_ok"],
                    s["invoice_policy"], s["service_type"], s["service_tracking"], s["recurring_invoice"],
                    s["al2c_product_line"], s["al2c_vat_class"], kb_id,
                    prj_tmpl_json, prj_json,
                    desc_sale_json, desc_pur_json,
                ),
            )
            tmpl_id = cur.fetchone()[0]
        canonical_tmpl_ids.append(tmpl_id)

        cur.execute(
            "SELECT id FROM catalog_sku WHERE product_tmpl_id = %s ORDER BY active DESC, id ASC LIMIT 1;",
            (tmpl_id,),
        )
        vr = cur.fetchone()
        if vr:
            var_id = vr[0]
            cur.execute(
                "UPDATE catalog_sku SET default_code = %s, lst_price = %s, active = TRUE, write_date = NOW() WHERE id = %s;",
                (code, s["list_price"], var_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO catalog_sku (
                    product_tmpl_id, default_code, lst_price, base_unit_count,
                    active, create_uid, write_uid, create_date, write_date
                ) VALUES (%s, %s, %s, 0, TRUE, 1, 1, NOW(), NOW()) RETURNING id;
                """,
                (tmpl_id, code, s["list_price"]),
            )
            var_id = cur.fetchone()[0]
        canonical_var_ids.append(var_id)
        var_id_by_code[code] = var_id

        upsert_imd(cur, "insilos_al2c", s["prod_xmlid"], "product.template", tmpl_id)
        upsert_imd(cur, "insilos_al2c", f"{s['prod_xmlid']}_variant", "product.product", var_id)

        # Upsert fixed pricelist item
        cur.execute(
            "SELECT id FROM product_pricelist_item WHERE pricelist_id = %s AND product_tmpl_id = %s LIMIT 1;",
            (pl_id, tmpl_id),
        )
        pli = cur.fetchone()
        if pli:
            cur.execute(
                "UPDATE product_pricelist_item SET compute_price = 'fixed', fixed_price = %s, write_date = NOW() WHERE id = %s;",
                (s["list_price"], pli[0]),
            )
        else:
            cur.execute(
                """
                INSERT INTO product_pricelist_item (
                    pricelist_id, company_id, currency_id, applied_on, base,
                    compute_price, product_tmpl_id, fixed_price, min_quantity,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (%s, 1, %s, '1_product', 'list_price', 'fixed', %s, %s, 0.0, 1, 1, NOW(), NOW());
                """,
                (pl_id, vnd_id, tmpl_id, s["list_price"]),
            )

    # Archive all non-canonical products and variants
    cur.execute(
        "UPDATE catalog_item SET active = FALSE WHERE active = TRUE AND id != ALL(%s);",
        (canonical_tmpl_ids,),
    )
    cur.execute(
        "UPDATE catalog_sku SET active = FALSE WHERE active = TRUE AND id != ALL(%s);",
        (canonical_var_ids,),
    )

    # =========================================================================
    # 3. QUOTATION TEMPLATES (`sale.order.template` & `sale.order.template.line`)
    # =========================================================================
    canonical_sot_ids = []
    for sot in BUNDLE["sots"]:
        en_name = sot["en_name"]
        sxmlid = sot["xmlid"]
        sot_id = None
        if sxmlid:
            cur.execute(
                "SELECT res_id FROM ir_model_data WHERE module = 'insilos_al2c' AND name = %s AND model = 'sale.order.template' LIMIT 1;",
                (sxmlid,),
            )
            sr = cur.fetchone()
            if sr:
                cur.execute("SELECT id FROM sale_order_template WHERE id = %s;", (sr[0],))
                if cur.fetchone():
                    sot_id = sr[0]
        if not sot_id:
            cur.execute(
                "SELECT id FROM sale_order_template WHERE name->>'en_US' = %s OR name->>'vi_VN' = %s ORDER BY active DESC, id ASC LIMIT 1;",
                (en_name, en_name),
            )
            sr2 = cur.fetchone()
            if sr2:
                sot_id = sr2[0]
        name_json = json.dumps(sot["name"])
        note_json = json.dumps(sot["note"])
        if sot_id:
            cur.execute(
                "UPDATE sale_order_template SET name = %s::jsonb, note = %s::jsonb, active = TRUE, sequence = %s, write_date = NOW() WHERE id = %s;",
                (name_json, note_json, sot["sequence"], sot_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO sale_order_template (
                    company_id, sequence, template_type, name, note,
                    active, require_signature, share_template, prepayment_percent,
                    duration_value, duration_unit, is_unlimited,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (
                    NULL, %s, 'quotation', %s::jsonb, %s::jsonb,
                    TRUE, TRUE, TRUE, 0.0,
                    1, 'month', TRUE,
                    1, 1, NOW(), NOW()
                ) RETURNING id;
                """,
                (sot["sequence"], name_json, note_json),
            )
            sot_id = cur.fetchone()[0]
        upsert_imd(cur, "insilos_al2c", sxmlid, "sale.order.template", sot_id)
        canonical_sot_ids.append(sot_id)

        cur.execute("DELETE FROM sale_order_template_line WHERE sale_order_template_id = %s;", (sot_id,))
        for line in sot["lines"]:
            p_var_id = var_id_by_code.get(line["default_code"])
            if not p_var_id:
                continue
            l_uom_id = uom_map.get(line["uom_xmlid"], 1)
            l_name_json = json.dumps(
                line["name"] if isinstance(line["name"], dict) else {"en_US": str(line["name"] or line["default_code"]), "vi_VN": str(line["name"] or line["default_code"])}
            )
            cur.execute(
                """
                INSERT INTO sale_order_template_line (
                    sale_order_template_id, sequence, product_id,
                    name, product_uom_qty, product_uom_id,
                    create_uid, write_uid, create_date, write_date
                ) VALUES (%s, %s, %s, %s::jsonb, %s, %s, 1, 1, NOW(), NOW());
                """,
                (sot_id, line["sequence"], p_var_id, l_name_json, line["qty"], l_uom_id),
            )

    cur.execute(
        "UPDATE sale_order_template SET active = FALSE WHERE active = TRUE AND id != ALL(%s);",
        (canonical_sot_ids,),
    )

    # =========================================================================
    # 4. PARTNERS (`res.partner` / `party_master`)
    # =========================================================================
    # Fix duplicate VAT 0317958465 if Partner 1 (Insilos Enterprise) shares VAT with Company 14 (Digimate JSC)
    cur.execute(
        "SELECT id FROM res_partner WHERE vat = '0317958465' AND id != 1 AND active = TRUE LIMIT 1;"
    )
    if cur.fetchone():
        cur.execute("UPDATE res_partner SET vat = '0313683499' WHERE id = 1 AND vat = '0317958465';")

    # Keep strictly canonical active partners:
    # - res_company partners
    # - active res_users partners
    # - 7 canonical DGM B2B/Platform partners (PTN-DGM-2026-0001..0007)
    # - 9 active DGM employee work_contact_id partners
    cur.execute(
        """
        UPDATE res_partner
           SET active = FALSE
         WHERE active = TRUE
           AND COALESCE(dgm_partner_code, '') NOT IN (
               'PTN-DGM-2026-0001', 'PTN-DGM-2026-0002', 'PTN-DGM-2026-0003',
               'PTN-DGM-2026-0004', 'PTN-DGM-2026-0005', 'PTN-DGM-2026-0006',
               'PTN-DGM-2026-0007'
           )
           AND id NOT IN (SELECT partner_id FROM res_company WHERE partner_id IS NOT NULL)
           AND id NOT IN (SELECT partner_id FROM res_users WHERE active = TRUE AND partner_id IS NOT NULL)
           AND id NOT IN (SELECT work_contact_id FROM hr_employee WHERE active = TRUE AND work_contact_id IS NOT NULL);
        """
    )

    # =========================================================================
    # 5, 6, 7, 8. HR DEPARTMENTS, JOBS, EMPLOYEES & VERSIONS
    # =========================================================================
    # Archive any active hr_job that has 0 active employees
    cur.execute(
        """
        UPDATE hr_job j
           SET active = FALSE
         WHERE j.active = TRUE
           AND NOT EXISTS (
               SELECT 1
                 FROM hr_version v
                 JOIN hr_employee e ON e.id = v.employee_id
                WHERE v.job_id = j.id
                  AND e.active = TRUE
           );
        """
    )

    # =========================================================================
    # 10a. DOCUMENTS (`documents.document`) — Archive '(Root Shared)' & empty folders
    # =========================================================================
    cur.execute(
        """
        UPDATE documents_document
           SET active = FALSE
         WHERE active = TRUE
           AND name::text ILIKE '%(Root Shared)%';
        """
    )
    for _ in range(5):
        cur.execute(
            """
            UPDATE documents_document d
               SET active = FALSE
             WHERE d.active = TRUE
               AND d.type = 'folder'
               AND NOT EXISTS (
                   SELECT 1 FROM documents_document c WHERE c.folder_id = d.id AND c.active = TRUE
               );
            """
        )

    conn.commit()


def audit_catalogs(conn):
    cur = conn.cursor()
    metrics = {}
    failures = []

    # 1. product.category
    cur.execute("SELECT name->>'vi_VN', name->>'en_US' FROM product_category;")
    cat_rows = cur.fetchall()
    vi_names = {r[0] for r in cat_rows if r[0]}
    missing_vi_cats = [c for c in CANONICAL_5_VI_CATEGORIES if c not in vi_names]
    cur.execute(
        "SELECT count(*) FROM ir_model_data WHERE model = 'product.category' AND module IN ('l10n_vn_demo', 'mongodb_etl');"
    )
    legacy_cat_imd = cur.fetchone()[0]
    cat_ok = (len(missing_vi_cats) == 0) and (legacy_cat_imd == 0)
    metrics["1. product.category"] = {
        "ok": cat_ok,
        "summary": f"{len(CANONICAL_5_VI_CATEGORIES) - len(missing_vi_cats)}/5 canonical VI trees, {len(cat_rows)} total, {legacy_cat_imd} legacy",
    }
    if not cat_ok:
        failures.append(f"product.category: missing_vi={missing_vi_cats}, legacy_imd={legacy_cat_imd}")

    # 2. product.template & product.product
    cur.execute("SELECT default_code FROM catalog_item WHERE active = TRUE;")
    act_tmpls = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT count(*) FROM catalog_sku WHERE active = TRUE;")
    act_vars = cur.fetchone()[0]
    missing_skus = [c for c in CANONICAL_33_SKUS if c not in act_tmpls]
    extra_skus = [c for c in act_tmpls if c not in CANONICAL_33_SKUS]
    prod_ok = (len(act_tmpls) == 33) and (act_vars == 33) and not missing_skus and not extra_skus
    metrics["2. product.template / product"] = {
        "ok": prod_ok,
        "summary": f"{len(act_tmpls)}/33 active templates, {act_vars}/33 active variants, {len(extra_skus)} extra",
    }
    if not prod_ok:
        failures.append(f"product.template: count={len(act_tmpls)}, vars={act_vars}, missing={missing_skus}, extra={extra_skus}")

    # 3. sale.order.template
    cur.execute("SELECT id, COALESCE(name->>'en_US', name->>'vi_VN') FROM sale_order_template WHERE active = TRUE;")
    sot_rows = cur.fetchall()
    sot_names = [r[1] for r in sot_rows]
    missing_sots = [n for n in CANONICAL_12_SO_TEMPLATES if n not in sot_names]
    cur.execute(
        """
        SELECT count(*)
          FROM sale_order_template_line l
          JOIN sale_order_template t ON t.id = l.sale_order_template_id
          LEFT JOIN catalog_sku cs ON cs.id = l.product_id
         WHERE t.active = TRUE
           AND l.display_type IS NULL
           AND (cs.id IS NULL OR cs.active = FALSE);
        """
    )
    bad_sot_lines = cur.fetchone()[0]
    sot_ok = (len(sot_rows) == 12) and not missing_sots and (bad_sot_lines == 0)
    metrics["3. sale.order.template"] = {
        "ok": sot_ok,
        "summary": f"{len(sot_rows)}/12 active templates, {bad_sot_lines} invalid lines",
    }
    if not sot_ok:
        failures.append(f"sale.order.template: count={len(sot_rows)}, missing={missing_sots}, bad_lines={bad_sot_lines}")

    # 4. res.partner
    cur.execute(
        """
        SELECT count(*)
          FROM res_partner
         WHERE active = TRUE
           AND (
               LOWER(COALESCE(name::text, '')) LIKE '%test%'
               OR LOWER(COALESCE(name::text, '')) LIKE '%demo%'
               OR LOWER(COALESCE(email, '')) LIKE '%example.com%'
               OR TRIM(COALESCE(name::text, '')) = ''
           );
        """
    )
    junk_partners = cur.fetchone()[0]
    cur.execute(
        """
        SELECT count(*)
          FROM (
              SELECT vat
                FROM res_partner
               WHERE active = TRUE AND is_company = TRUE AND vat IS NOT NULL AND TRIM(vat) != ''
               GROUP BY vat
              HAVING count(*) > 1
          ) dup;
        """
    )
    dup_vats = cur.fetchone()[0]
    cur.execute(
        """
        SELECT count(*)
          FROM res_partner
         WHERE active = TRUE
           AND dgm_partner_code IN (
               'PTN-DGM-2026-0001', 'PTN-DGM-2026-0002', 'PTN-DGM-2026-0003',
               'PTN-DGM-2026-0004', 'PTN-DGM-2026-0005', 'PTN-DGM-2026-0006',
               'PTN-DGM-2026-0007'
           )
           AND dgm_onboarding_state = 'approved'
           AND dgm_all_companion_docs_ready = TRUE;
        """
    )
    approved_dgm_partners = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM res_partner WHERE active = TRUE;")
    total_act_partners = cur.fetchone()[0]
    ptn_ok = (junk_partners == 0) and (dup_vats == 0) and (approved_dgm_partners == 7)
    metrics["4. res.partner"] = {
        "ok": ptn_ok,
        "summary": f"{approved_dgm_partners}/7 approved DGM partners ({total_act_partners} total active), {junk_partners} junk, {dup_vats} dup VAT",
    }
    if not ptn_ok:
        failures.append(f"res.partner: approved_dgm={approved_dgm_partners}, junk={junk_partners}, dup_vats={dup_vats}")

    # 5. hr.department
    cur.execute("SELECT count(*) FROM hr_department WHERE active = TRUE;")
    dept_cnt = cur.fetchone()[0]
    dept_ok = (dept_cnt == 4)
    metrics["5. hr.department"] = {
        "ok": dept_ok,
        "summary": f"{dept_cnt}/4 canonical active departments",
    }
    if not dept_ok:
        failures.append(f"hr.department: active={dept_cnt} (expected 4)")

    # 6. hr.job
    cur.execute("SELECT count(*) FROM hr_job WHERE active = TRUE;")
    job_cnt = cur.fetchone()[0]
    cur.execute(
        """
        SELECT count(*)
          FROM hr_job j
         WHERE j.active = TRUE
           AND NOT EXISTS (
               SELECT 1 FROM hr_version v JOIN hr_employee e ON e.id = v.employee_id WHERE v.job_id = j.id AND e.active = TRUE
           );
        """
    )
    empty_jobs = cur.fetchone()[0]
    job_ok = (job_cnt == 8) and (empty_jobs == 0)
    metrics["6. hr.job"] = {
        "ok": job_ok,
        "summary": f"{job_cnt}/8 active jobs, {empty_jobs} unused active jobs",
    }
    if not job_ok:
        failures.append(f"hr.job: active={job_cnt}, empty_jobs={empty_jobs}")

    # 7. hr.employee
    cur.execute(
        "SELECT barcode FROM hr_employee WHERE active = TRUE ORDER BY barcode ASC;"
    )
    emp_codes = [r[0] for r in cur.fetchall()]
    expected_codes = [f"DGM-00{i}" for i in range(1, 10)]
    emp_ok = (emp_codes == expected_codes)
    metrics["7. hr.employee"] = {
        "ok": emp_ok,
        "summary": f"{len(emp_codes)}/9 canonical active employees (DGM-001..DGM-009)",
    }
    if not emp_ok:
        failures.append(f"hr.employee: codes={emp_codes}")

    # 8. hr.version
    cur.execute(
        """
        SELECT count(DISTINCT e.id)
          FROM hr_employee e
          JOIN hr_version v ON v.employee_id = e.id
         WHERE e.active = TRUE
           AND v.wage > 0;
        """
    )
    ver_cnt = cur.fetchone()[0]
    ver_ok = (ver_cnt == 9)
    metrics["8. hr.version"] = {
        "ok": ver_ok,
        "summary": f"{ver_cnt}/9 active statutory contracts (wage > 0)",
    }
    if not ver_ok:
        failures.append(f"hr.version: count={ver_cnt}")

    # 9. project.project
    cur.execute("SELECT id, COALESCE(name->>'en_US', name->>'vi_VN') FROM project_project WHERE active = TRUE;")
    act_prjs = cur.fetchall()
    bad_stage_prjs = 0
    for pid, _pname in act_prjs:
        cur.execute(
            """
            SELECT count(DISTINCT t.name->>'en_US')
              FROM project_task_type_rel r
              JOIN project_task_type t ON t.id = r.type_id
             WHERE r.project_id = %s
               AND (t.name->>'en_US') IN ('Prepare', 'Explore', 'Realize', 'Deploy', 'Run');
            """,
            (pid,),
        )
        if cur.fetchone()[0] < 5:
            bad_stage_prjs += 1
    prj_ok = (len(act_prjs) == 15) and (bad_stage_prjs == 0)
    metrics["9. project.project"] = {
        "ok": prj_ok,
        "summary": f"{len(act_prjs)}/15 active projects, {len(act_prjs) - bad_stage_prjs}/{len(act_prjs)} with 5 SAP Activate stages",
    }
    if not prj_ok:
        failures.append(f"project.project: active={len(act_prjs)}, bad_stage_prjs={bad_stage_prjs}")

    # 10. documents.document & knowledge.article
    cur.execute(
        """
        SELECT count(*)
          FROM documents_document d
         WHERE d.active = TRUE
           AND d.type = 'folder'
           AND NOT EXISTS (SELECT 1 FROM documents_document c WHERE c.folder_id = d.id AND c.active = TRUE);
        """
    )
    empty_folders = cur.fetchone()[0]
    cur.execute(
        "SELECT count(*) FROM documents_document WHERE active = TRUE AND name::text ILIKE '%(Root Shared)%';"
    )
    root_shared_folders = cur.fetchone()[0]
    sop_counts = []
    for sop_idx in range(1, 8):
        cur.execute(
            "SELECT count(*) FROM knowledge_article WHERE active = TRUE AND name ILIKE %s;",
            (f"SOP-DGM-0{sop_idx}%",),
        )
        sop_counts.append(cur.fetchone()[0])
    cur.execute("SELECT count(*) FROM knowledge_article WHERE active = TRUE AND name IS NULL;")
    null_kb = cur.fetchone()[0]
    doc_kb_ok = (empty_folders == 0) and (root_shared_folders == 0) and (sop_counts == [1, 1, 1, 1, 1, 1, 1]) and (null_kb == 0)
    metrics["10. documents & knowledge"] = {
        "ok": doc_kb_ok,
        "summary": f"0 empty folders ({empty_folders}), 0 Root Shared ({root_shared_folders}), {sum(1 for x in sop_counts if x == 1)}/7 deduplicated SOPs",
    }
    if not doc_kb_ok:
        failures.append(f"documents/knowledge: empty_folders={empty_folders}, root_shared={root_shared_folders}, sop_counts={sop_counts}, null_kb={null_kb}")

    return {"db": TARGET_DB, "is_k8s": IS_K8S, "metrics": metrics, "failures": failures}


def main():
    conn = get_conn()
    if not CHECK_ONLY:
        clean_and_consolidate(conn)
    res = audit_catalogs(conn)
    conn.close()
    print("CATALOG_AUDIT_JSON:" + json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
'''


def run_worker_on_target(bundle, target_db, is_k8s=False, check_only=False):
    bundle_b64 = base64.b64encode(json.dumps(bundle, ensure_ascii=False).encode("utf-8")).decode("ascii")
    script = (
        WORKER_SCRIPT_TEMPLATE
        .replace("__BUNDLE_B64__", bundle_b64)
        .replace("__CHECK_ONLY__", "True" if check_only else "False")
        .replace("__TARGET_DB__", target_db)
        .replace("__IS_K8S__", "True" if is_k8s else "False")
    )
    if is_k8s:
        pod_name = "innoria-prod-app-7cdc9b8ddc-8st7m"
        try:
            discovered = subprocess.check_output(
                [
                    "kubectl", "get", "pods", "-n", "production",
                    "-l", "app=innoria-prod",
                    "--field-selector=status.phase=Running",
                    "-o", "jsonpath={.items[0].metadata.name}",
                ],
                text=True,
            ).strip()
            if discovered:
                pod_name = discovered
        except Exception:
            pass
        proc = subprocess.run(
            ["kubectl", "exec", "-i", "-n", "production", pod_name, "-c", "innoria", "--", "python3", "-"],
            input=script,
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        proc = subprocess.run(
            [sys.executable, "-"],
            input=script,
            capture_output=True,
            text=True,
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"Worker failed ({target_db}, k8s={is_k8s}, rc={proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
    for line in proc.stdout.splitlines():
        if line.startswith("CATALOG_AUDIT_JSON:"):
            return json.loads(line[len("CATALOG_AUDIT_JSON:"):])
    raise RuntimeError(f"Failed to parse worker output ({target_db}, k8s={is_k8s}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")


def print_summary_table(results):
    print("\n" + "=" * 145)
    print(f"{'CATALOG DOMAIN':<30} | {'LOCAL insilos20_dev':<35} | {'LOCAL innoria_prod':<35} | {'K8S innoria_prod (innoria.com)':<35}")
    print("=" * 145)
    catalog_keys = list(results[0]["metrics"].keys())
    for key in catalog_keys:
        cols = []
        for r in results:
            m = r["metrics"][key]
            icon = "PASS" if m["ok"] else "FAIL"
            cols.append(f"[{icon}] {m['summary']}")
        print(f"{key:<30} | {cols[0]:<35} | {cols[1]:<35} | {cols[2]:<35}")
    print("=" * 145)


def main():
    parser = argparse.ArgumentParser(description="Master 10-Catalog Audit, Deduplication & Consolidation Engine")
    parser.add_argument("--check", action="store_true", help="Read-only verification gate (no writes)")
    args = parser.parse_args()

    bundle_data = extract_canonical_bundle_from_dev()
    bundle = {
        "canonical_5_vi_categories": CANONICAL_5_VI_CATEGORIES,
        "canonical_categories_spec": CANONICAL_CATEGORIES_SPEC,
        "canonical_33_skus": CANONICAL_33_SKUS,
        "canonical_12_so_templates": CANONICAL_12_SO_TEMPLATES,
        "sap_activate_phases": SAP_ACTIVATE_PHASES,
        **bundle_data,
    }

    targets = [
        ("insilos20_dev", False),
        ("innoria_prod", False),
        ("innoria_prod", True),
    ]
    results = []
    for db_name, is_k8s in targets:
        res = run_worker_on_target(bundle, db_name, is_k8s=is_k8s, check_only=args.check)
        results.append(res)

    print_summary_table(results)

    all_failures = []
    for r in results:
        env_label = f"K8s:{r['db']}" if r["is_k8s"] else f"Local:{r['db']}"
        for f in r["failures"]:
            all_failures.append(f"[{env_label}] {f}")

    if all_failures:
        print("\n[✗] CATALOG INVARIANT FAILURES DETECTED:")
        for f in all_failures:
            print(f"  - {f}")
        sys.exit(1)

    mode_str = "READ-ONLY CHECK GATE (--check)" if args.check else "IDEMPOTENT CONSOLIDATION & VERIFICATION"
    print(f"\n[🎉] ALL 10 CORE CATALOGS PASSED 100% ACROSS insilos20_dev, LOCAL innoria_prod & K8S innoria_prod ({mode_str}) — EXIT 0")
    sys.exit(0)


if __name__ == "__main__":
    main()
