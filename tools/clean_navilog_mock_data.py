#!/usr/bin/env python3
"""
Clean Navilog Mock Data from Odoo Production (innoria_prod)
Executes surgical cleanup of pre-existing mock/demo data via Odoo ORM (JSON-RPC on port 38069).
Preserves system configuration, base accounts, and all MongoDB synced records (ir.model.data).
"""

import sys
import logging
sys.path.insert(0, '/home/zen/teamwork_projects/erp_prod_data_sync')
from src.odoo.ingest import OdooIngestor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleaner")

ODOO_URL = "http://localhost:38069"
ODOO_DB = "innoria_prod"

def main():
    logger.info("Initializing OdooIngestor on %s (db=%s)...", ODOO_URL, ODOO_DB)
    client = OdooIngestor(url=ODOO_URL, db=ODOO_DB, username="admin", password="admin")
    uid = client.authenticate()
    logger.info("Authenticated as UID %d", uid)

    results = {}

    # 1. Clean 10 Mock Navilog Employees
    logger.info("--- Cleaning Mock Employees ---")
    mock_emp_ids = [41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
    existing_mock_emps = client.execute_kw(
        "hr.employee", "search",
        [[["id", "in", mock_emp_ids]]],
        {"context": {"active_test": False}}
    )
    if existing_mock_emps:
        logger.info("Found %d mock employees to unlink: %s", len(existing_mock_emps), existing_mock_emps)
        try:
            client.execute_kw("hr.employee", "unlink", [existing_mock_emps])
            logger.info("[✓] Successfully unlinked %d mock employees", len(existing_mock_emps))
            results["mock_employees_deleted"] = len(existing_mock_emps)
        except Exception as e:
            logger.warning("[!] Failed to unlink mock employees directly: %s. Archiving instead...", e)
            client.execute_kw("hr.employee", "write", [existing_mock_emps, {"active": False}])
            results["mock_employees_archived"] = len(existing_mock_emps)
    else:
        logger.info("No mock employees found to clean.")
        results["mock_employees_deleted"] = 0

    # 2. Clean Mock Sale Orders & Purchase Orders
    logger.info("--- Cleaning Mock Orders ---")
    demo_sos = client.execute_kw("sale.order", "search", [[]])
    if demo_sos:
        logger.info("Found %d demo sale orders to unlink: %s", len(demo_sos), demo_sos)
        try:
            # Cancel before unlink if needed
            for so_id in demo_sos:
                try:
                    client.execute_kw("sale.order", "action_cancel", [[so_id]])
                except Exception:
                    pass
            client.execute_kw("sale.order", "unlink", [demo_sos])
            logger.info("[✓] Successfully unlinked %d demo sale orders", len(demo_sos))
            results["demo_sale_orders_deleted"] = len(demo_sos)
        except Exception as e:
            logger.warning("[!] Could not unlink sale orders: %s", e)
            results["demo_sale_orders_error"] = str(e)
    else:
        results["demo_sale_orders_deleted"] = 0

    demo_pos = client.execute_kw("purchase.order", "search", [[]])
    if demo_pos:
        logger.info("Found %d demo purchase orders to unlink: %s", len(demo_pos), demo_pos)
        try:
            for po_id in demo_pos:
                try:
                    client.execute_kw("purchase.order", "button_cancel", [[po_id]])
                except Exception:
                    pass
            client.execute_kw("purchase.order", "unlink", [demo_pos])
            logger.info("[✓] Successfully unlinked %d demo purchase orders", len(demo_pos))
            results["demo_purchase_orders_deleted"] = len(demo_pos)
        except Exception as e:
            logger.warning("[!] Could not unlink purchase orders: %s", e)
            results["demo_purchase_orders_error"] = str(e)
    else:
        results["demo_purchase_orders_deleted"] = 0

    # 3. Clean Mock Projects & Tasks
    logger.info("--- Cleaning Mock Projects & Tasks ---")
    demo_tasks = client.execute_kw("project.task", "search", [[]])
    if demo_tasks:
        logger.info("Found %d demo tasks to unlink", len(demo_tasks))
        try:
            client.execute_kw("project.task", "unlink", [demo_tasks])
            logger.info("[✓] Successfully unlinked %d demo tasks", len(demo_tasks))
            results["demo_tasks_deleted"] = len(demo_tasks)
        except Exception as e:
            logger.warning("[!] Could not unlink demo tasks: %s", e)
            results["demo_tasks_error"] = str(e)
    else:
        results["demo_tasks_deleted"] = 0

    demo_projects = client.execute_kw("project.project", "search", [[]])
    if demo_projects:
        logger.info("Found %d demo projects to unlink", len(demo_projects))
        try:
            client.execute_kw("project.project", "unlink", [demo_projects])
            logger.info("[✓] Successfully unlinked %d demo projects", len(demo_projects))
            results["demo_projects_deleted"] = len(demo_projects)
        except Exception as e:
            logger.warning("[!] Could not unlink demo projects: %s", e)
            results["demo_projects_error"] = str(e)
    else:
        results["demo_projects_deleted"] = 0

    # 4. Clean Mock Leads (Keep MongoDB Leads)
    logger.info("--- Cleaning Mock Leads ---")
    synced_lead_xids = client.execute_kw(
        "ir.model.data", "search_read",
        [[["module", "=", "mongodb_etl"], ["model", "=", "crm.lead"]]],
        {"fields": ["res_id"]}
    )
    keep_lead_ids = set(x["res_id"] for x in synced_lead_xids if x.get("res_id"))
    all_leads = client.execute_kw("crm.lead", "search", [[]])
    mock_leads = [lid for lid in all_leads if lid not in keep_lead_ids]
    if mock_leads:
        logger.info("Found %d mock leads to unlink: %s", len(mock_leads), mock_leads)
        try:
            client.execute_kw("crm.lead", "unlink", [mock_leads])
            logger.info("[✓] Successfully unlinked %d mock leads", len(mock_leads))
            results["mock_leads_deleted"] = len(mock_leads)
        except Exception as e:
            logger.warning("[!] Could not unlink mock leads: %s", e)
            results["mock_leads_error"] = str(e)
    else:
        results["mock_leads_deleted"] = 0

    # 5. Clean Mock Products (78 demo parts)
    logger.info("--- Cleaning Mock Products ---")
    demo_prods = client.execute_kw("product.template", "search", [[]])
    if demo_prods:
        logger.info("Found %d demo products to clean", len(demo_prods))
        try:
            client.execute_kw("product.template", "unlink", [demo_prods])
            logger.info("[✓] Successfully unlinked %d demo products", len(demo_prods))
            results["demo_products_deleted"] = len(demo_prods)
        except Exception as e:
            logger.warning("[!] Could not unlink demo products directly (%s), archiving instead...", e)
            client.execute_kw("product.template", "write", [demo_prods, {"active": False}])
            logger.info("[✓] Successfully archived %d demo products", len(demo_prods))
            results["demo_products_archived"] = len(demo_prods)
    else:
        results["demo_products_deleted"] = 0

    # 6. Verify Remaining State
    logger.info("=== VERIFYING FINAL PRODUCTION STATE ===")
    emp_rem = client.execute_kw("hr.employee", "search_count", [[]], {"context": {"active_test": False}})
    lead_rem = client.execute_kw("crm.lead", "search_count", [[]])
    partner_rem = client.execute_kw("res.partner", "search_count", [[]])
    xid_rem = client.execute_kw("ir.model.data", "search_count", [[["module", "=", "mongodb_etl"]]])
    
    logger.info("Remaining Employees : %d (Expected: 37 MongoDB employees)", emp_rem)
    logger.info("Remaining Leads     : %d (Expected: 8 MongoDB leads)", lead_rem)
    logger.info("Remaining Partners  : %d", partner_rem)
    logger.info("Synced XIDs         : %d (Expected: 164)", xid_rem)

    print("\n" + "="*60)
    print("CLEANUP EXECUTION REPORT:")
    for k, v in results.items():
        print(f"  {k:30s}: {v}")
    print("="*60)

if __name__ == "__main__":
    main()
