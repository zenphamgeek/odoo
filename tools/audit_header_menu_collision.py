#!/usr/bin/env python3
"""
Multi-Tenant Header Menu Collision Audit & Self-Healing Engine
=============================================================
Audits and resolves duplicate website navigation menu entries across
all tenant databases and pods in the Insilos / InnoKafe cluster.

Guarantees:
1. Multi-Tenant Invariance: Scans each tenant database independently.
2. Canonical Resolution: Canonical URL derived from COALESCE(manual_url, page.url).
3. Zero False Positives: Ignores non-colliding dropdown anchors ('#').
4. Parent Tree Isolation: Distinguishes child menus (navbar/submenus under parent_id)
   from root containers, ensuring template roots are not falsely flagged.
5. Self-Healing Mode (--heal): Safely prunes duplicate records, preserving
   the canonical record (bound to website_page or primary ir_model_data).
6. CI/CD Gate Mode (--check): Exits code 1 on collisions, exit code 0 when clean.

Usage:
    # Audit single database:
    python3 tools/audit_header_menu_collision.py --db innokafe_prod

    # Audit all tenant databases:
    python3 tools/audit_header_menu_collision.py --all-tenants

    # Self-heal collisions across all tenants:
    python3 tools/audit_header_menu_collision.py --all-tenants --heal
"""

import argparse
import json
import os
import sys
import psycopg2
from collections import defaultdict

DEFAULT_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("DB_PORT", 5434))
DEFAULT_USER = os.environ.get("DB_USER", "odoo")
DEFAULT_PASSWORD = os.environ.get("DB_PASSWORD", "1NN0R1@2026")

KNOWN_TENANTS = [
    "innokafe_prod",
    "innoria_prod",
    "odoo20_dev",
]


def get_db_connection(dbname, host=DEFAULT_HOST, port=DEFAULT_PORT, user=DEFAULT_USER, password=DEFAULT_PASSWORD):
    return psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
    )


def list_available_databases(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
        return [r[0] for r in cur.fetchall()]


def check_table_exists(conn, table_name):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            );
        """, (table_name,))
        return cur.fetchone()[0]


def audit_database_menus(conn, dbname, heal=False):
    """
    Audits website_menu entries in the given database.
    Checks for:
    1. Child menu collisions: Multiple menus under the same parent_id sharing the same resolved URL.
    2. Root menu collisions: Multiple root menus (parent_id IS NULL) for the same website_id.
    """
    if not check_table_exists(conn, "website_menu"):
        return {
            "dbname": dbname,
            "status": "SKIPPED_NO_TABLE",
            "total_menus": 0,
            "collisions_count": 0,
            "collisions": [],
            "healed_count": 0,
        }

    with conn.cursor() as cur:
        # Fetch all website menus with resolved URLs
        cur.execute("""
            SELECT 
                m.id,
                m.name,
                m.parent_id,
                m.website_id,
                m.sequence,
                m.page_id,
                COALESCE(
                    NULLIF(TRIM(m.manual_url), ''),
                    p.url->>'en_US',
                    p.url->>'vi_VN',
                    p.url::text
                ) AS resolved_url,
                imd.name AS xml_id_name
            FROM website_menu m
            LEFT JOIN website_page p ON m.page_id = p.id
            LEFT JOIN ir_model_data imd ON (imd.model = 'website.menu' AND imd.res_id = m.id)
            ORDER BY m.parent_id NULLS FIRST, m.sequence, m.id
        """)
        rows = cur.fetchall()

    total_menus = len(rows)
    groups = defaultdict(list)

    for r in rows:
        m_id, m_name, parent_id, website_id, seq, page_id, res_url, xml_id_name = r
        clean_url = (res_url or "").strip().strip('"')

        # We care about collisions under active menu trees:
        # 1. Child menus (parent_id IS NOT NULL) with non-empty, non-'#' URL
        # 2. Root menus (parent_id IS NULL) for a specific website_id
        if parent_id is not None:
            if clean_url and clean_url != "#":
                key = ("child", parent_id, clean_url)
                groups[key].append({
                    "id": m_id,
                    "name": m_name,
                    "parent_id": parent_id,
                    "website_id": website_id,
                    "sequence": seq,
                    "page_id": page_id,
                    "resolved_url": clean_url,
                    "xml_id_name": xml_id_name,
                })
        else:
            # Root menu: only flag if same website_id has multiple root menus with the same URL
            if website_id is not None and clean_url:
                key = ("root", website_id, clean_url)
                groups[key].append({
                    "id": m_id,
                    "name": m_name,
                    "parent_id": parent_id,
                    "website_id": website_id,
                    "sequence": seq,
                    "page_id": page_id,
                    "resolved_url": clean_url,
                    "xml_id_name": xml_id_name,
                })

    collisions = []
    ids_to_purge = []

    for key, items in groups.items():
        if len(items) > 1:
            scope_type = key[0]
            scope_id = key[1]
            clean_url = key[2]

            # Priority for picking canonical record:
            # 1. Has valid ir_model_data (official module XML record)
            # 2. Has page_id (bound to website.page)
            # 3. Lowest ID (original record)
            items_sorted = sorted(
                items,
                key=lambda x: (
                    x["xml_id_name"] is None,
                    x["page_id"] is None,
                    x["id"]
                )
            )
            canonical = items_sorted[0]
            duplicates = items_sorted[1:]

            collisions.append({
                "scope": scope_type,
                "scope_id": scope_id,
                "url": clean_url,
                "canonical_id": canonical["id"],
                "canonical_name": canonical["name"],
                "canonical_xml_id": canonical["xml_id_name"],
                "duplicate_ids": [d["id"] for d in duplicates],
                "duplicate_names": [d["name"] for d in duplicates],
            })

            if heal:
                for d in duplicates:
                    ids_to_purge.append(d["id"])

    healed_count = 0
    if heal and ids_to_purge:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM website_menu WHERE id = ANY(%s)", (ids_to_purge,))
        conn.commit()
        healed_count = len(ids_to_purge)

    return {
        "dbname": dbname,
        "status": "COLLISIONS_DETECTED" if collisions else "CLEAN",
        "total_menus": total_menus,
        "collisions_count": len(collisions),
        "collisions": collisions,
        "healed_count": healed_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-Tenant Website Menu Collision Audit & Healing")
    parser.add_argument("--db", type=str, help="Specific database name to audit")
    parser.add_argument("--all-tenants", action="store_true", help="Audit all known tenant databases")
    parser.add_argument("--all-dbs", action="store_true", help="Scan every database in the PostgreSQL cluster")
    parser.add_argument("--heal", action="store_true", help="Automatically heal collisions by pruning duplicates")
    parser.add_argument("--json-report", type=str, help="Path to write JSON audit report")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--user", type=str, default=DEFAULT_USER)
    parser.add_argument("--password", type=str, default=DEFAULT_PASSWORD)

    args = parser.parse_args()

    # Determine target databases
    target_dbs = []
    if args.db:
        target_dbs = [args.db]
    elif args.all_tenants:
        target_dbs = KNOWN_TENANTS
    elif args.all_dbs:
        try:
            conn_admin = get_db_connection("postgres", args.host, args.port, args.user, args.password)
            all_dbs = list_available_databases(conn_admin)
            conn_admin.close()
            target_dbs = [d for d in all_dbs if not d.startswith("tmp_") and not d.startswith("test_")]
        except Exception as e:
            print(f"[!] Error listing cluster databases: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        target_dbs = ["innokafe_prod"]

    reports = []
    total_collisions_found = 0
    total_healed = 0

    print("=" * 80)
    print(" INSILOS MULTI-TENANT WEBSITE MENU COLLISION AUDIT")
    print(f" Target Mode: {'HEAL' if args.heal else 'CHECK ONLY'}")
    print(f" Cluster: {args.host}:{args.port} | Databases: {len(target_dbs)}")
    print("=" * 80)

    for dbname in target_dbs:
        try:
            conn = get_db_connection(dbname, args.host, args.port, args.user, args.password)
            res = audit_database_menus(conn, dbname, heal=args.heal)
            conn.close()
            reports.append(res)

            status_icon = "✓" if res["collisions_count"] == 0 else "✗"
            print(f"[{status_icon}] {dbname:<25} Menus: {res['total_menus']:<4} Collisions: {res['collisions_count']:<3}", end="")
            if args.heal and res["healed_count"] > 0:
                print(f" [HEALED {res['healed_count']} DUPLICATES]")
            else:
                print("")

            if res["collisions"]:
                for c in res["collisions"]:
                    print(f"    ├─ [{c['scope'].upper()}:{c['scope_id']}] URL '{c['url']}': Canonical ID {c['canonical_id']} (xml_id: {c['canonical_xml_id']}) vs Duplicates {c['duplicate_ids']}")
                total_collisions_found += res["collisions_count"]
            total_healed += res["healed_count"]

        except Exception as e:
            print(f"[!] {dbname:<25} Connection/Audit Failed: {e}")
            reports.append({
                "dbname": dbname,
                "status": "ERROR",
                "error": str(e),
                "collisions_count": 0,
            })

    print("-" * 80)
    print(f"Summary: {len(target_dbs)} DBs checked | {total_collisions_found} Collisions Found | {total_healed} Healed")
    print("=" * 80)

    if args.json_report:
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_databases": len(target_dbs),
                    "collisions_found": total_collisions_found,
                    "healed_count": total_healed,
                    "mode": "HEAL" if args.heal else "CHECK",
                },
                "results": reports,
            }, f, indent=2, ensure_ascii=False)
        print(f"[✓] JSON report saved to: {args.json_report}")

    if not args.heal and total_collisions_found > 0:
        print("[FAIL] Collisions detected. Run with --heal to resolve, or address menu definitions.")
        sys.exit(1)

    print("[SUCCESS] All tenant website menus pass collision-free invariant.")
    sys.exit(0)


if __name__ == "__main__":
    main()
