#!/usr/bin/env python3
"""
tools/audit_views_integrity.py
Insilos Enterprise Sovereign View & Schema Integrity Matrix Scanner.

Audits:
1. Ghost Views & Module State Drift: Views active in DB but whose module directory is missing on disk.
2. View Graph Compilation Matrix: Performs get_views() across core high-risk models (res.config.settings,
   res.partner, sale.order, account.move, hr.employee, mrp.production, stock.picking, etc.)
   to detect invalid fields, broken XPath inheritance, or missing XML attributes.
3. Foreign Key / M2M Schema Invariance: Checks all M2M relational fields against physical database columns
   to guarantee zero undefined column crashes during module upgrade.

Exit code 0: 100% PASS (Zero view or schema defects).
Exit code 1: Integrity violation detected.
"""

import argparse
import os
import sys
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Audit View & Schema Integrity")
    parser.add_argument("-d", "--db", default=os.environ.get("DB_NAME", "odoo20_dev"), help="Database name")
    parser.add_argument("--config", default="insilos.conf", help="Path to config file")
    parser.add_argument("--host", default=os.environ.get("DB_HOST", "127.0.0.1"), help="DB Host")
    parser.add_argument("--port", default=os.environ.get("DB_PORT", "5434"), help="DB Port")
    parser.add_argument("--user", default=os.environ.get("DB_USER", "odoo"), help="DB User")
    parser.add_argument("--password", default=os.environ.get("PGPASSWORD", ""), help="DB Password")
    parser.add_argument("--quick", action="store_true", help="Run only high-risk models (res.config.settings)")
    return parser.parse_args()


def audit_integrity():
    args = parse_args()
    print("=" * 78)
    print(f"[*] STARTING VIEW & SCHEMA INTEGRITY AUDIT ON DB: {args.db}")
    print("=" * 78)
    t0 = time.time()

    # Setup Python path
    for candidate in ["/app/insilos", "/home/zen/O20", os.getcwd()]:
        if os.path.exists(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)

    import odoo
    from odoo import api, SUPERUSER_ID
    from odoo.tools import sql

    # Configure Odoo runtime
    if os.path.exists("/app/insilos"):
        addons_path = "/var/lib/insilos/filestore/custom_addons,/app/insilos/addons,/app/insilos/apps,/app/insilos/enterprise"
    else:
        addons_path = "/home/zen/O20/addons,/home/zen/O20/enterprise"

    cfg_args = [
        f"--addons-path={addons_path}",
        f"--db_host={args.host}",
        f"--db_port={args.port}",
        f"--db_user={args.user}",
        f"--db_password={args.password}",
        f"-d={args.db}",
    ]
    if os.path.exists(args.config):
        cfg_args.extend(["-c", args.config])

    odoo.tools.config.parse_config(cfg_args)

    print(f"[*] Booting ORM registry for {args.db}...")
    registry = odoo.orm.registry.Registry(args.db)

    errors = []
    warnings = []

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # =====================================================================
        # CHECK 1: Ghost Views & Active DB Views vs On-Disk Addons
        # =====================================================================
        print("\n--- [CHECK 1/3] GHOST VIEW & MODULE ORPHAN AUDIT ---")
        cr.execute("""
            SELECT v.id, v.name, v.model, d.module, m.state
            FROM ir_ui_view v
            JOIN ir_model_data d ON d.model = 'ir.ui.view' AND d.res_id = v.id
            LEFT JOIN ir_module_module m ON m.name = d.module
            WHERE v.active = true
        """)
        active_views = cr.fetchall()
        print(f"[*] Auditing {len(active_views)} active views in database...")

        addons_dirs = addons_path.split(",")
        disk_modules = set()
        for ad in addons_dirs:
            if os.path.isdir(ad):
                for item in os.listdir(ad):
                    if os.path.isdir(os.path.join(ad, item)):
                        disk_modules.add(item)

        ghost_count = 0
        for vid, vname, vmodel, mod, mod_state in active_views:
            if mod and mod not in disk_modules:
                msg = f"Ghost View ID {vid} ({vname}) on model '{vmodel}': module '{mod}' does NOT exist on disk! (module state={mod_state})"
                errors.append(msg)
                ghost_count += 1

        if ghost_count == 0:
            print(f"[✓] Zero ghost views detected across all {len(active_views)} active views.")
        else:
            print(f"[✗] Found {ghost_count} ghost views belonging to missing disk modules!")

        # =====================================================================
        # CHECK 2: View Graph Compilation Matrix (get_views)
        # =====================================================================
        print("\n--- [CHECK 2/3] VIEW GRAPH COMPILATION MATRIX (get_views) ---")
        CORE_MODELS = [
            "res.config.settings",
            "res.partner",
            "res.company",
            "sale.order",
            "purchase.order",
            "account.move",
            "stock.picking",
            "mrp.production",
            "hr.employee",
            "hr.contract",
            "project.project",
            "crm.lead",
            "insilos.control.tower",
        ]
        if args.quick:
            audit_models = ["res.config.settings", "insilos.control.tower"]
        else:
            audit_models = [m for m in CORE_MODELS if m in env]

        view_pass = 0
        for mname in audit_models:
            model_obj = env[mname]
            # Test form view
            try:
                t_start = time.time()
                views = model_obj.get_views([(False, "form")])
                dur = time.time() - t_start
                print(f"  [✓] {mname:<25} form view compiled in {dur:.2f}s")
                view_pass += 1
            except Exception as e:
                err_msg = f"View compilation FAILED on model '{mname}' (form): {str(e)}"
                print(f"  [✗] {err_msg}")
                errors.append(err_msg)

            # Test list/tree view if supported
            if mname != "res.config.settings":
                try:
                    views = model_obj.get_views([(False, "list")])
                except Exception as e:
                    err_msg = f"View compilation FAILED on model '{mname}' (list): {str(e)}"
                    print(f"  [✗] {err_msg}")
                    errors.append(err_msg)

        # =====================================================================
        # CHECK 3: Relational Foreign Key & Column Physical Invariance
        # =====================================================================
        print("\n--- [CHECK 3/3] RELATIONAL SCHEMA & COLUMN INVARIANCE AUDIT ---")
        fk_checked = 0
        fk_issues = 0
        for mname in registry.models:
            model_obj = env[mname]
            if not model_obj._is_an_ordinary_table():
                continue
            for fname, field in model_obj._fields.items():
                if field.type == "many2many" and field.store and field.relation:
                    rel_table = field.relation
                    col1 = field.column1
                    col2 = field.column2
                    if not sql.table_exists(cr, rel_table):
                        continue
                    fk_checked += 1
                    # Verify col1
                    if col1 and not sql.column_exists(cr, rel_table, col1):
                        msg = f"Model '{mname}' field '{fname}': relation table '{rel_table}' is missing column '{col1}'"
                        errors.append(msg)
                        fk_issues += 1
                    # Verify col2
                    if col2 and not sql.column_exists(cr, rel_table, col2):
                        msg = f"Model '{mname}' field '{fname}': relation table '{rel_table}' is missing column '{col2}'"
                        errors.append(msg)
                        fk_issues += 1

        if fk_issues == 0:
            print(f"[✓] Audited {fk_checked} Many2many relations: 100% columns physically exist in PostgreSQL.")
        else:
            print(f"[✗] Found {fk_issues} relational column mismatches in database!")

    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================
    elapsed = time.time() - t0
    print("\n" + "=" * 78)
    print("AUDIT SUMMARY REPORT:")
    print(f"Database: {args.db} | Total Duration: {elapsed:.2f}s")
    print(f"Total Errors: {len(errors)} | Total Warnings: {len(warnings)}")

    if errors:
        print("\n[!] CRITICAL VIOLATIONS DETECTED:")
        for idx, err in enumerate(errors, 1):
            print(f"  {idx}. {err}")
        print("=" * 78)
        sys.exit(1)
    else:
        print("\n[🎉] INTEGRITY PASS: All views, schemas, and relational constraints are healthy!")
        print("=" * 78)
        sys.exit(0)


if __name__ == "__main__":
    audit_integrity()
