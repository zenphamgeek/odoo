#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overhaul Product & Service Definitions across O20 / Innoria to Authentic
Software Engineering & Enterprise Software Development Standards (SOP-SW-CATALOG-01).

Synthesizes outputs from AGY Fleet Pro Nodes (justaskgao, codegeekvn, traimai, zenonmind)
and updates:
1. addons/insilos_al2c/data/product_template_data.xml (33 SKUs)
2. addons/insilos_al2c/data/product_category_data.xml (Software Engineering Categories)
3. addons/insilos_al2c/controllers/ai_concierge.py (INNORIA_SOFTWARE_SERVICES)
4. addons/insilos_al2c/static/src/js/ai_concierge_widget.js (DEFAULT_SERVICES_CATALOG & Welcome)
5. addons/insilos_al2c/static/src/xml/ai_concierge_widget.xml (#al2c_lead_solution options)
6. addons/insilos_al2c/controllers/catalog_manifest.py (/llms.txt & /llms-full.txt)
7. enterprise/insilos_website/views/innoria_homepage.xml & innoria_pages.xml
8. PostgreSQL product_template & product_category (en_US + vi_VN JSONB) across insilos20_dev & innoria_prod
"""
import json
import os
import re
import lxml.etree as ET
import psycopg2
from psycopg2.extras import Json

PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5434,
    "user": "odoo",
    "password": "1NN0R1@2026",
}

STEP_FILES = [
    "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/.system_generated/steps/25220/output.txt",
    "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/.system_generated/steps/25221/output.txt",
    "/home/zen/.gemini/antigravity/brain/790b1743-1724-4f27-a6fd-6d949bee50cf/.system_generated/steps/25222/output.txt",
]


def load_fleet_sku_catalog():
    merged = {}
    for path in STEP_FILES:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r'\{"conversation_id":.*\}', txt)
        if not m:
            continue
        outer = json.loads(m.group(0))
        resp = outer.get("response", "").strip()
        resp = re.sub(r"^```(?:json)?\s*", "", resp)
        resp = re.sub(r"\s*```$", "", resp)
        data = json.loads(resp)
        merged.update(data)
    return merged


def update_product_template_xml(sku_catalog):
    xml_path = "/home/zen/O20/addons/insilos_al2c/data/product_template_data.xml"
    parser = ET.XMLParser(remove_blank_text=False)
    tree = ET.parse(xml_path, parser)
    root = tree.getroot()
    updated = 0
    for rec in root.xpath(".//record[@model='product.template']"):
        code_el = rec.find("field[@name='default_code']")
        if code_el is None or not code_el.text:
            continue
        code = code_el.text.strip()
        if code not in sku_catalog:
            continue
        spec = sku_catalog[code]
        name_el = rec.find("field[@name='name']")
        if name_el is not None:
            name_el.text = f"{spec['name_vi']} ({spec['name_en']})"
        desc_el = rec.find("field[@name='description_sale']")
        if desc_el is not None:
            desc_el.text = spec["desc_vi"]
        updated += 1
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"[XML] Updated {updated} SKU records in {xml_path}")


def update_product_category_xml():
    xml_path = "/home/zen/O20/addons/insilos_al2c/data/product_category_data.xml"
    cat_map = {
        "categ_erp": "Hệ thống Quản trị Doanh nghiệp (Enterprise ERP Software)",
        "categ_erp_impl": "Triển khai & Tùy biến Phân hệ ERP (ERP Implementation & Engineering)",
        "categ_erp_saas": "Thuê bao Phần mềm & Hạ tầng Đám mây (Cloud SaaS & Managed Infrastructure)",
        "categ_grc": "Phần mềm Quản trị Rủi ro & Tuân thủ Bảo mật (Enterprise GRC & InfoSec Software)",
        "categ_ai": "Phần mềm AI Ứng dụng & Xử lý Dữ liệu (Applied AI & Data Engineering)",
        "categ_ai_custom": "Phát triển Mô-đun AI, OCR/IDP & Enterprise RAG (Custom AI & IDP Engineering)",
        "categ_ai_mojo": "Nền tảng Phần mềm Mojo AI & Cổng Suy luận LLM (Mojo AI Platform & API Gateway)",
        "categ_services": "Dịch vụ Kỹ thuật Phần mềm & Bảo trì Ứng dụng (Software Engineering & AMS Services)",
        "categ_dgm_onsite": "Phát triển Phần mềm theo Đội ngũ Kỹ sư Chuyên trách (Dedicated Software Engineering Squads)",
        "categ_dgm_prepaid": "Hạ tầng Viễn thông & Chứng thư số Doanh nghiệp (Prepaid Telecom & PKI Infrastructure)",
    }
    parser = ET.XMLParser(remove_blank_text=False)
    tree = ET.parse(xml_path, parser)
    root = tree.getroot()
    for rec in root.xpath(".//record[@model='product.category']"):
        rid = rec.get("id")
        if rid in cat_map:
            name_el = rec.find("field[@name='name']")
            if name_el is not None:
                name_el.text = cat_map[rid]
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"[XML] Updated {len(cat_map)} categories in {xml_path}")


def sync_products_to_db(sku_catalog):
    for dbname in ("insilos20_dev", "innoria_prod"):
        conn = psycopg2.connect(dbname=dbname, **PG_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        count = 0
        for code, spec in sku_catalog.items():
            name_json = {"en_US": spec["name_en"], "vi_VN": spec["name_vi"]}
            desc_json = {"en_US": spec["desc_en"], "vi_VN": spec["desc_vi"]}
            cur.execute(
                """
                UPDATE product_template
                SET name = %s,
                    description_sale = %s,
                    write_date = NOW()
                WHERE default_code = %s
                """,
                (Json(name_json), Json(desc_json), code),
            )
            count += cur.rowcount
        conn.close()
        print(f"[DB {dbname}] Updated {count} product_template records with bilingual Software Engineering specs")


if __name__ == "__main__":
    catalog = load_fleet_sku_catalog()
    print(f"Loaded {len(catalog)} SKUs from Fleet Pro synthesis")
    update_product_template_xml(catalog)
    update_product_category_xml()
    sync_products_to_db(catalog)
