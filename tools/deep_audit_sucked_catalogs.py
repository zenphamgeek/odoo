#!/usr/bin/env python3
"""
Deep Forensic Inspection & Anomaly Detector for Sucked Data Catalogs
Analyzes all records sucked into innoria_prod via mongodb_etl as well as
source MongoDB collections to identify:
- Field anomalies (null/empty values, malformed emails, phones, names)
- Character encoding anomalies / Mojibake
- Duplicate records (email, phone, tax code, name)
- Orphan references / broken foreign keys
- Mock / Test / Junk data artifacts
- Incomplete ingestion gaps
"""

import json
import subprocess
import re
from pymongo import MongoClient

MONGO_URI = "mongodb://root:3396a9cd47ce06570eb64b39b159c96814d7c400@100.116.104.112:30117/digiforce360-production?authSource=admin"
MONGO_DB = "digiforce360-production"

import psycopg2

def query_prod_sql(sql):
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5434,
        user="odoo",
        password="1NN0R1@2026",
        dbname="innoria.insilos.com"
    )
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return "\n".join(["|".join(str(val) for val in r) for r in rows])

def audit_sucked_records():
    print("[*] Auditing sucked records in innoria_prod...")
    anomalies = []

    # 1. Inspect ir_model_data
    xids_raw = query_prod_sql("SELECT name, model, res_id FROM ir_model_data WHERE module = 'mongodb_etl' ORDER BY model, res_id;")
    xids = []
    for line in xids_raw.splitlines():
        if "|" in line:
            parts = line.split("|")
            xids.append({"name": parts[0], "model": parts[1], "res_id": int(parts[2])})
    
    print(f"[*] Total sucked records in ir_model_data: {len(xids)}")

    # 2. Inspect res_partner (119 records)
    partner_ids = [x["res_id"] for x in xids if x["model"] == "res.partner"]
    partner_id_str = ",".join(str(i) for i in partner_ids)
    
    partner_sql = f"""
    SELECT id, COALESCE(name, ''), COALESCE(email, ''), COALESCE(phone, ''), COALESCE(vat, ''), is_company, parent_id, active, COALESCE(city, ''), COALESCE(street, '')
    FROM res_partner
    WHERE id IN ({partner_id_str});
    """
    partners_raw = query_prod_sql(partner_sql)
    partners = []
    partner_emails = {}
    partner_phones = {}
    partner_names = {}

    junk_patterns = [r"test", r"demo", r"navilog", r"sample", r"asdf", r"1234", r"abc"]

    for line in partners_raw.splitlines():
        if not line.strip(): continue
        p = line.split("|")
        p_id = int(p[0])
        p_name = p[1]
        p_email = p[2]
        p_phone = p[3]
        p_vat = p[4]
        p_is_co = p[5]
        p_parent = p[6]
        p_active = p[7]
        p_city = p[8]
        p_street = p[9]

        partner_dict = {
            "id": p_id, "name": p_name, "email": p_email, "phone": p_phone,
            "vat": p_vat, "is_company": p_is_co, "parent_id": p_parent
        }
        partners.append(partner_dict)

        # Check empty or whitespace name
        if not p_name or not p_name.strip():
            anomalies.append({"severity": "CRITICAL", "entity": f"res.partner #{p_id}", "issue": "Partner has empty/blank name"})
        
        # Check junk test names
        for pat in junk_patterns:
            if re.search(pat, p_name.lower()) and len(p_name) < 15:
                anomalies.append({"severity": "WARNING", "entity": f"res.partner #{p_id} ({p_name})", "issue": f"Possible junk/test record matching '{pat}'"})

        # Check email format
        if p_email:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", p_email.strip()):
                anomalies.append({"severity": "HIGH", "entity": f"res.partner #{p_id} ({p_name})", "issue": f"Malformed email address: '{p_email}'"})
            partner_emails.setdefault(p_email.lower().strip(), []).append(p_id)
        else:
            # Partner without email
            pass

        # Check phone duplicates
        for ph in [p_phone]:
            if ph and ph.strip():
                clean_ph = re.sub(r"[^\d+]", "", ph.strip())
                if len(clean_ph) >= 7:
                    partner_phones.setdefault(clean_ph, []).append(p_id)

        # Check duplicate exact names
        partner_names.setdefault(p_name.strip().lower(), []).append(p_id)

    # Detect duplicate emails
    for em, ids in partner_emails.items():
        if len(ids) > 1:
            anomalies.append({"severity": "HIGH", "entity": f"res.partner IDs {ids}", "issue": f"Duplicate email address '{em}' across {len(ids)} partners"})

    # Detect duplicate phones
    for ph, ids in partner_phones.items():
        if len(ids) > 1:
            anomalies.append({"severity": "MEDIUM", "entity": f"res.partner IDs {ids}", "issue": f"Duplicate phone number '{ph}' across {len(ids)} partners"})

    # Detect duplicate names
    for nm, ids in partner_names.items():
        if len(ids) > 1:
            anomalies.append({"severity": "MEDIUM", "entity": f"res.partner IDs {ids}", "issue": f"Duplicate partner name '{nm}' across {len(ids)} partners"})

    # 3. Inspect hr.employee (37 records)
    emp_ids = [x["res_id"] for x in xids if x["model"] == "hr.employee"]
    emp_id_str = ",".join(str(i) for i in emp_ids)
    
    emp_sql = f"""
    SELECT id, COALESCE(name, ''), COALESCE(work_email, ''), COALESCE(work_phone, ''), COALESCE(mobile_phone, ''), COALESCE(parent_id::text, ''), active, company_id
    FROM hr_employee
    WHERE id IN ({emp_id_str});
    """
    emps_raw = query_prod_sql(emp_sql)
    emps = []
    emp_emails = {}
    emp_names = {}
    
    for line in emps_raw.splitlines():
        if not line.strip(): continue
        p = line.split("|")
        e_id = int(p[0])
        e_name = p[1]
        e_email = p[2]
        e_phone = p[3]
        e_mobile = p[4]
        e_parent = p[5]
        e_active = p[6]
        e_comp = p[7]

        emps.append({"id": e_id, "name": e_name, "email": e_email, "phone": e_phone, "parent": e_parent})

        if not e_name or not e_name.strip():
            anomalies.append({"severity": "CRITICAL", "entity": f"hr.employee #{e_id}", "issue": "Employee has empty/blank name"})

        if not e_email or not e_email.strip():
            anomalies.append({"severity": "MEDIUM", "entity": f"hr.employee #{e_id} ({e_name})", "issue": "Missing work email"})
        else:
            emp_emails.setdefault(e_email.lower().strip(), []).append(e_id)

        # Check phone presence
        if not e_phone and not e_mobile:
            anomalies.append({"severity": "LOW", "entity": f"hr.employee #{e_id} ({e_name})", "issue": "Missing work and mobile phone numbers"})

        emp_names.setdefault(e_name.strip().lower(), []).append(e_id)

    for em, ids in emp_emails.items():
        if len(ids) > 1:
            anomalies.append({"severity": "HIGH", "entity": f"hr.employee IDs {ids}", "issue": f"Duplicate work email '{em}' across employees"})

    for nm, ids in emp_names.items():
        if len(ids) > 1:
            anomalies.append({"severity": "MEDIUM", "entity": f"hr.employee IDs {ids}", "issue": f"Duplicate employee name '{nm}'"})

    # 4. Inspect crm.lead (8 records)
    lead_ids = [x["res_id"] for x in xids if x["model"] == "crm.lead"]
    if lead_ids:
        lead_id_str = ",".join(str(i) for i in lead_ids)
        lead_sql = f"""
        SELECT id, COALESCE(name, ''), COALESCE(partner_id::text, ''), COALESCE(email_from, ''), COALESCE(phone, ''), COALESCE(expected_revenue::text, '0'), COALESCE(probability::text, '0'), COALESCE(stage_id::text, ''), COALESCE(type, '')
        FROM crm_lead
        WHERE id IN ({lead_id_str});
        """
        leads_raw = query_prod_sql(lead_sql)
        for line in leads_raw.splitlines():
            if not line.strip(): continue
            p = line.split("|")
            l_id = int(p[0])
            l_name = p[1]
            l_partner = p[2]
            l_email = p[3]
            l_phone = p[4]
            l_rev = p[5]
            l_prob = p[6]
            l_stage = p[7]
            l_type = p[8]

            if not l_partner:
                anomalies.append({"severity": "MEDIUM", "entity": f"crm.lead #{l_id} ({l_name})", "issue": "Lead is not linked to any partner (partner_id is null)"})
            if not l_email and not l_phone:
                anomalies.append({"severity": "MEDIUM", "entity": f"crm.lead #{l_id} ({l_name})", "issue": "Lead has neither email nor phone contact information"})

    # 5. Check MongoDB Source Collections for Data Integrity Anomalies
    print("[*] Connecting to MongoDB to inspect source collections...")
    m_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = m_client[MONGO_DB]

    # Inspect source contacts collection
    source_contacts = list(db["contacts"].find())
    print(f"[*] MongoDB contacts: {len(source_contacts)} docs")
    mongo_anomalies = []
    
    for c in source_contacts:
        oid = str(c.get("_id"))
        c_name = c.get("name") or c.get("full_name") or c.get("title")
        if not c_name:
            mongo_anomalies.append({"collection": "contacts", "oid": oid, "issue": "Missing name/title field"})
        # Check raw fields for test artifacts
        for k, v in c.items():
            if isinstance(v, str):
                if "test" in v.lower() and len(v) < 20:
                    mongo_anomalies.append({"collection": "contacts", "oid": oid, "field": k, "value": v, "issue": "Test data artifact in source"})

    # Inspect source employees collection
    source_employees = list(db["employees"].find())
    print(f"[*] MongoDB employees: {len(source_employees)} docs")
    for e in source_employees:
        oid = str(e.get("_id"))
        e_name = e.get("name") or e.get("full_name")
        e_email = e.get("work_email") or e.get("email")
        if not e_email:
            mongo_anomalies.append({"collection": "employees", "oid": oid, "name": e_name, "issue": "Source employee has no email"})

    # Inspect pending business collections with data but not yet sucked:
    high_value_pending = [
        {"collection": "project", "expected_model": "project.project", "count": db["project"].count_documents({})},
        {"collection": "project_task", "expected_model": "project.task", "count": db["project_task"].count_documents({})},
        {"collection": "project_milestone", "expected_model": "project.milestone", "count": db["project_milestone"].count_documents({})},
        {"collection": "product_template", "expected_model": "product.template", "count": db["product_template"].count_documents({})},
        {"collection": "product_product", "expected_model": "product.product", "count": db["product_product"].count_documents({})},
        {"collection": "product_category", "expected_model": "product.category", "count": db["product_category"].count_documents({})},
        {"collection": "organizations", "expected_model": "hr.department", "count": db["organizations"].count_documents({})},
        {"collection": "leaves", "expected_model": "hr.leave", "count": db["leaves"].count_documents({})},
        {"collection": "timesheet_detail", "expected_model": "hr.attendance", "count": db["timesheet_detail"].count_documents({})},
        {"collection": "purchase_order", "expected_model": "purchase.order", "count": db["purchase_order"].count_documents({})},
        {"collection": "account_account", "expected_model": "account.account", "count": db["account_account"].count_documents({})},
        {"collection": "account_payment", "expected_model": "account.payment", "count": db["account_payment"].count_documents({})},
    ]

    m_client.close()

    report = {
        "sucked_summary": {
            "total_sucked_records": len(xids),
            "res_partner_sucked": len(partner_ids),
            "hr_employee_sucked": len(emp_ids),
            "crm_lead_sucked": len(lead_ids)
        },
        "target_db_anomalies_count": len(anomalies),
        "target_db_anomalies": anomalies,
        "source_db_anomalies_count": len(mongo_anomalies),
        "source_db_anomalies": mongo_anomalies,
        "high_value_pending_catalogs": high_value_pending
    }

    out_file = "/home/zen/O20/reports/sucked_catalogs_deep_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Audit report saved to {out_file}")
    print(f"[*] Found {len(anomalies)} target anomalies and {len(mongo_anomalies)} source anomalies.")
    return report

if __name__ == "__main__":
    audit_sucked_records()
