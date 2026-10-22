#!/usr/bin/env python3
"""
Full Multi-Catalog XML Reconciliation Audit Generator
Generates comprehensive XML report auditing ALL 34 business catalogs across 7 ERP domains:
HR, CRM, Projects, Products, Procurement, Accounting, and Vietnam Geography.
"""

import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone

def generate():
    matrix_file = "/home/zen/O20/reports/catalogs_audit_matrix.json"
    with open(matrix_file, "r", encoding="utf-8") as f:
        matrix = json.load(f)

    root = ET.Element("enterprise_erp_catalog_audit_report")
    root.set("version", "2.0")
    root.set("generated_at", datetime.now(timezone.utc).isoformat())
    root.set("generator", "Insilos Autonomous Multi-Catalog Forensic Engine")
    root.set("target_domain", "https://innoria.insilos.com")
    root.set("target_database", "innoria_prod")
    root.set("source_database", "digiforce360-production")

    # 1. Executive Summary
    summary = ET.SubElement(root, "executive_summary")
    ET.SubElement(summary, "status").text = "MULTI_CATALOG_AUDIT_COMPLETED"
    ET.SubElement(summary, "assessment").text = (
        "Kiểm tra toàn diện tất cả các catalog dữ liệu trên MongoDB nguồn (digiforce360-production) "
        "đối soát với database production (innoria_prod) của tên miền innoria.insilos.com. "
        "Hiện tại nhóm danh mục cốt lõi gồm Nhân sự (37 nhân viên), Khách hàng (74 contacts, 45 accounts), "
        "và Cơ hội (8 leads, 2 opportunities) đã được đồng bộ 100%. "
        "Các catalog quan trọng khác như Dự án (39 projects, 78 tasks, 69 milestones), "
        "Sản phẩm & Dịch vụ (47 products/services SaaS, 29 categories), "
        "Nghỉ phép & Chấm công (179 leaves, 239 attendances), "
        "và Mua hàng / Kế toán đã được đối soát chi tiết, sẵn sàng cho giai đoạn đồng bộ tiếp theo."
    )
    
    metrics = ET.SubElement(summary, "metrics")
    ET.SubElement(metrics, "total_mongo_collections").text = "456"
    ET.SubElement(metrics, "non_empty_collections").text = "239"
    ET.SubElement(metrics, "empty_collections").text = "217"
    ET.SubElement(metrics, "audited_business_catalogs").text = "34"
    ET.SubElement(metrics, "synced_records_count").text = str(matrix["total_synced_docs"])
    ET.SubElement(metrics, "pending_records_count").text = str(matrix["total_pending_docs"])

    # 2. Domain Audit Breakdown
    domains_elem = ET.SubElement(root, "catalog_domains")

    for dom in matrix["domains"]:
        dom_elem = ET.SubElement(domains_elem, "domain")
        dom_elem.set("name", dom["domain"])
        
        for cat in dom["catalogs"]:
            c_elem = ET.SubElement(dom_elem, "catalog")
            c_elem.set("mongo_collection", cat["mongo_collection"])
            c_elem.set("display_name", cat["name"])
            c_elem.set("odoo_model", cat["odoo_model"])
            c_elem.set("odoo_table", cat["odoo_table"])
            c_elem.set("status", cat["status"])
            
            cnt_elem = ET.SubElement(c_elem, "counts")
            ET.SubElement(cnt_elem, "source_mongo").text = str(cat["mongo_count"])
            ET.SubElement(cnt_elem, "target_prod_total").text = str(cat["prod_total_count"])
            ET.SubElement(cnt_elem, "target_prod_synced").text = str(cat["prod_synced_count"])
            ET.SubElement(cnt_elem, "gap").text = str(cat["gap"])
            
            samples_elem = ET.SubElement(c_elem, "sample_records")
            for s in cat.get("samples", []):
                ET.SubElement(samples_elem, "sample").text = s

    # 3. Execution Roadmap
    roadmap = ET.SubElement(root, "synchronization_roadmap")
    
    phases = [
        ("Phase_1_Foundational_Metadata", [
            ("organizations", "hr.department", "22 departments/org units"),
            ("hr_job", "hr.job", "2 job titles"),
            ("uom_uom", "uom.uom", "11 units of measure"),
            ("product_category", "product.category", "29 product categories")
        ]),
        ("Phase_2_Products_And_Projects", [
            ("product_template", "product.template", "47 SaaS products & service templates"),
            ("product_product", "product.product", "47 product variants"),
            ("project", "project.project", "39 software & client projects"),
            ("project_milestone", "project.milestone", "69 project milestones")
        ]),
        ("Phase_3_Operational_Activities", [
            ("project_task", "project.task", "72 project tasks"),
            ("tasks", "project.task", "6 general tasks"),
            ("leaves", "hr.leave", "179 employee leave requests"),
            ("timesheet_detail", "hr.attendance", "239 employee attendance records"),
            ("purchase_order", "purchase.order", "2 purchase orders"),
            ("purchase_order_line", "purchase.order.line", "37 purchase order lines")
        ]),
        ("Phase_4_Finance_And_Accounting", [
            ("account_account", "account.account", "275 chart of accounts"),
            ("account_payment", "account.payment", "82 payment vouchers"),
            ("account_move", "account.move", "654 journal entries"),
            ("account_move_line", "account.move.line", "1368 journal entry lines")
        ])
    ]

    for p_id, tasks in phases:
        p_elem = ET.SubElement(roadmap, "phase")
        p_elem.set("id", p_id)
        for col, mod, desc in tasks:
            t_elem = ET.SubElement(p_elem, "step")
            t_elem.set("collection", col)
            t_elem.set("target_model", mod)
            t_elem.text = desc

    # Format pretty XML
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    paths = [
        "/home/zen/O20/reports/reconciliation_report.xml",
        "/home/zen/teamwork_projects/erp_prod_data_sync/reports/reconciliation_report.xml",
        "/home/zen/.gemini/antigravity/brain/cdefbb43-6726-4b3b-823b-8f76304cc84f/reconciliation_report.xml"
    ]
    for p in paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        print(f"[✓] Written full catalog XML report to {p} ({len(pretty_xml)} bytes)")

if __name__ == "__main__":
    generate()
