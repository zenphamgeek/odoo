#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/sync_sovereign_db_bridge.py
=================================
Automated Sovereign Database Bridge Synchronizer & Health Guardian.

Ensures 100% bidirectional table/view compatibility between Sovereign IBM Enterprise
naming conventions and legacy Odoo schema across all tenant databases and fresh databases:
1. party_master <-> res_partner
2. organization_unit <-> res_company
3. system_attachment <-> ir_attachment
4. party_classification <-> res_partner_category
5. catalog_item <-> product_template
6. catalog_sku <-> product_product
7. procurement_order <-> purchase_order
8. procurement_order_line <-> purchase_order_line
9. order_header <-> sale_order
10. order_line <-> sale_order_line
11. logistics_transfer <-> stock_picking
12. logistics_movement <-> stock_move
13. manufacturing_order <-> mrp_production
14. manufacturing_bom <-> mrp_bom
15. finance_journal_entry <-> account_move
16. finance_journal_line <-> account_move_line

Usage:
  python3 tools/sync_sovereign_db_bridge.py --all
  python3 tools/sync_sovereign_db_bridge.py --db insilos
  python3 tools/sync_sovereign_db_bridge.py --check
"""

import argparse
import subprocess
import sys

DB_NAMESPACE = "database"
PG_POD = "postgres-0"
DB_USER = "insilos"

SOVEREIGN_TABLE_BRIDGES = [
    ("party_master", "res_partner"),
    ("organization_unit", "res_company"),
    ("system_attachment", "ir_attachment"),
    ("party_classification", "res_partner_category"),
    ("catalog_item", "product_template"),
    ("catalog_sku", "product_product"),
    ("procurement_order", "purchase_order"),
    ("procurement_order_line", "purchase_order_line"),
    ("order_header", "sale_order"),
    ("order_line", "sale_order_line"),
    ("logistics_transfer", "stock_picking"),
    ("logistics_movement", "stock_move"),
    ("manufacturing_order", "mrp_production"),
    ("manufacturing_bom", "mrp_bom"),
    ("finance_journal_entry", "account_move"),
    ("finance_journal_line", "account_move_line"),
]

SYSTEM_DATABASES = {"postgres", "template0", "template1", "triggerdev"}


def run_psql(sql: str, dbname: str = "postgres", user: str = "postgres") -> str:
    """Execute SQL securely via stdin without bash variable expansion."""
    cmd = ["kubectl", "-n", DB_NAMESPACE, "exec", "-i", PG_POD, "--", "psql", "-tA", "-U", user, "-d", dbname]
    p = subprocess.run(
        cmd,
        input=sql,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        err = p.stderr.strip() if p.stderr else f"Exit code {p.returncode}"
        raise RuntimeError(f"PSQL failed on '{dbname}':\nError: {err}")
    return p.stdout.strip()


def list_candidate_databases() -> list[str]:
    """Retrieve all tenant and application databases on PostgreSQL."""
    sql = "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
    out = run_psql(sql)
    dbs = []
    for line in out.splitlines():
        line = line.strip()
        if line and line not in SYSTEM_DATABASES and not line.startswith("datname") and not line.startswith("-"):
            dbs.append(line)
    return dbs


def audit_and_sync_database(dbname: str, apply_fixes: bool = True) -> dict:
    """Audit and optionally auto-heal sovereign bridge views on a specific database."""
    print(f"\n🔍 Inspecting Database: {dbname}")
    
    # Check total table count in public schema
    count_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
    try:
        tbl_count = int(run_psql(count_sql, dbname=dbname) or "0")
    except Exception as e:
        print(f"  ❌ Cannot access database '{dbname}': {e}")
        return {"status": "error", "error": str(e)}

    print(f"  • Total public relations: {tbl_count}")
    if tbl_count < 10:
        print(f"  ⚠️ Database '{dbname}' appears empty or uninitialized (<10 tables). Skipping.")
        return {"status": "empty", "table_count": tbl_count}

    # Query all relations matching our bridge pairs
    all_names = set()
    for sov, leg in SOVEREIGN_TABLE_BRIDGES:
        all_names.add(sov)
        all_names.add(leg)
    all_names.add("res_partner_res_partner_category_rel")
    all_names.add("party_classification_rel")

    names_clause = ",".join(f"'{n}'" for n in all_names)
    rel_sql = f"""
    SELECT relname, relkind 
    FROM pg_class 
    WHERE relname IN ({names_clause}) 
      AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
    """
    out = run_psql(rel_sql, dbname=dbname)
    relations = {}
    for line in out.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 2 and parts[0] in all_names:
            relations[parts[0]] = parts[1]  # 'r' = table, 'v' = view

    missing_bridges = []
    for sov, leg in SOVEREIGN_TABLE_BRIDGES:
        has_sov = sov in relations
        has_leg = leg in relations
        if has_leg and not has_sov:
            missing_bridges.append((sov, leg, f"CREATE OR REPLACE VIEW \"{sov}\" AS SELECT * FROM \"{leg}\";"))
        elif has_sov and not has_leg:
            missing_bridges.append((leg, sov, f"CREATE OR REPLACE VIEW \"{leg}\" AS SELECT * FROM \"{sov}\";"))

    # M2M check
    if "res_partner_res_partner_category_rel" in relations and "party_classification_rel" not in relations:
        missing_bridges.append((
            "party_classification_rel",
            "res_partner_res_partner_category_rel",
            "CREATE OR REPLACE VIEW party_classification_rel AS SELECT category_id, partner_id FROM res_partner_res_partner_category_rel;"
        ))
    elif "party_classification_rel" in relations and "res_partner_res_partner_category_rel" not in relations:
        missing_bridges.append((
            "res_partner_res_partner_category_rel",
            "party_classification_rel",
            "CREATE OR REPLACE VIEW res_partner_res_partner_category_rel AS SELECT category_id, partner_id FROM party_classification_rel;"
        ))

    if not missing_bridges:
        print(f"  ✅ All sovereign bridges present and intact ({len(relations)} relations matched).")
        return {"status": "ok", "table_count": tbl_count, "missing": 0}

    print(f"  ⚠️ Found {len(missing_bridges)} missing bridge relation(s):")
    for target, source, _ in missing_bridges:
        print(f"     -> Missing '{target}' (source: '{source}')")

    if apply_fixes:
        print("  🔨 Applying view creation and granting permissions...")
        sql_lines = ["BEGIN;"]
        for _, _, stmt in missing_bridges:
            sql_lines.append(stmt)
        sql_lines.append(f"GRANT ALL ON ALL TABLES IN SCHEMA public TO {DB_USER};")
        sql_lines.append(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {DB_USER};")
        sql_lines.append(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER};")
        sql_lines.append(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER};")
        sql_lines.append("COMMIT;")
        
        run_psql("\n".join(sql_lines), dbname=dbname)
        print(f"  ✅ Successfully created {len(missing_bridges)} views and updated grants.")

    return {"status": "healed" if apply_fixes else "unhealthy", "table_count": tbl_count, "missing": len(missing_bridges)}


def main():
    parser = argparse.ArgumentParser(description="Audit and sync sovereign database bridges.")
    parser.add_argument("--all", action="store_true", help="Audit and sync all candidate databases.")
    parser.add_argument("--db", type=str, help="Specific database to audit and sync.")
    parser.add_argument("--check", action="store_true", help="Audit only without applying changes.")
    args = parser.parse_args()

    apply_fixes = not args.check

    if args.db:
        dbs = [args.db]
    elif args.all:
        dbs = list_candidate_databases()
    else:
        dbs = list_candidate_databases()

    print("=" * 75)
    print("🛡️  SOVEREIGN DATABASE BRIDGE SYNCHRONIZER & AUDITOR")
    print(f"• Mode: {'AUDIT & AUTO-HEAL' if apply_fixes else 'CHECK-ONLY (Dry Run)'}")
    print(f"• Target Databases: {len(dbs)}")
    print("=" * 75)

    results = {}
    for db in dbs:
        results[db] = audit_and_sync_database(db, apply_fixes=apply_fixes)

    print("\n" + "=" * 75)
    print("📊 SUMMARY OF SOVEREIGN BRIDGE AUDIT")
    print("=" * 75)
    for db, res in sorted(results.items()):
        status = res.get("status")
        if status in ("ok", "healed"):
            icon = "✅"
        elif status == "empty":
            icon = "⚪"
        else:
            icon = "❌"
        print(f"{icon} {db:<30} : Status={status:<10} | Tables={res.get('table_count', 0)}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
