#!/usr/bin/env python3
"""
Test Cleanup Script for Navilog Mock Data with Dry-Run / Rollback
Verifies foreign key constraints and exact cascading delete execution.
"""

import subprocess

TEST_CLEANUP_SQL = """
BEGIN;

-- 1. Logistics IDP & Custom Orders
DELETE FROM order_line;
DELETE FROM order_header;
DELETE FROM logistics_idp_case;
DELETE FROM logistics_transfer;

-- 2. Sales & Purchases
DELETE FROM sale_order_line;
DELETE FROM sale_order;
DELETE FROM purchase_order_line;
DELETE FROM purchase_order;

-- 3. Invoices & Journal Entries
DELETE FROM account_partial_reconcile;
DELETE FROM account_move_line;
DELETE FROM account_move;

-- 4. Projects & Tasks
DELETE FROM project_task;
DELETE FROM project_project;

-- 4. Stock Quants & Moves (demo products)
DELETE FROM stock_quant;
DELETE FROM stock_move_line;
DELETE FROM stock_move;
DELETE FROM stock_picking;

-- 5. Products
DELETE FROM product_supplierinfo;
DELETE FROM product_product;
DELETE FROM product_template;

-- 6. Leads (keep MongoDB leads)
DELETE FROM crm_lead 
WHERE id NOT IN (SELECT res_id FROM ir_model_data WHERE module = 'mongodb_etl' AND model = 'crm.lead');

-- 7. Mock Employees (keep MongoDB employees)
DELETE FROM hr_employee 
WHERE id NOT IN (SELECT res_id FROM ir_model_data WHERE module = 'mongodb_etl' AND model = 'hr.employee');

-- 8. Mock Partners (keep system company, admin user, and MongoDB partners)
DELETE FROM res_partner
WHERE id NOT IN (SELECT res_id FROM ir_model_data WHERE module = 'mongodb_etl' AND model = 'res.partner')
  AND id NOT IN (SELECT partner_id FROM res_company)
  AND id NOT IN (SELECT partner_id FROM res_users WHERE partner_id IS NOT NULL);

-- Check remaining counts
SELECT 'hr_employee' as tbl, count(*) FROM hr_employee
UNION ALL
SELECT 'res_partner', count(*) FROM res_partner
UNION ALL
SELECT 'crm_lead', count(*) FROM crm_lead
UNION ALL
SELECT 'project_project', count(*) FROM project_project
UNION ALL
SELECT 'project_task', count(*) FROM project_task
UNION ALL
SELECT 'product_template', count(*) FROM product_template;

-- Dry run rollback
ROLLBACK;
"""

def main():
    cmd = [
        "/snap/kubectl/3855/kubectl", "-n", "production", "exec", "pod/insilos-saas-app-dfcb7cf44-2bwsl",
        "-c", "insilos", "--",
        "psql", "-h", "pgbouncer-service", "-p", "6432", "-U", "insilos", "-d", "innoria_prod",
        "-c", TEST_CLEANUP_SQL
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    if res.stderr:
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    main()
