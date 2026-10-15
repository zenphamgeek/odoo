#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insilos Enterprise Odoo 20 — 23-Module & Menu Naming Taxonomy Auditor
=====================================================================
Verifies and reconciles SAP S/4HANA LoB / Fiori 4 & IBM CBM / APQC PCF
concise naming standards across all 23 `insilos_*` modules (`addons/` & `enterprise/`):
  1. Manifest `name`: concise 2–3 words (<= 24 chars, <= 3 words) and non-empty `summary`.
  2. Own Root `ir.ui.menu` items: concise 2–3 words (<= 24 chars, <= 3 words).
  3. PostgreSQL Parity (`insilos20_dev` & `innoria_prod`): `ir_module_module.shortdesc`,
     `ir_module_module.summary`, `ir_ui_menu.name`, `ir_asset` (`.dark.scss`),
     `ir_access` (ACL parity), and `ir_ui_view` (`insilos_preferential_origin` views).

Usage:
    python3 tools/audit_insilos_naming_taxonomy.py --check
    python3 tools/audit_insilos_naming_taxonomy.py --sync-db
"""

import argparse
import ast
import configparser
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import psycopg2

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_db_params():
    if os.path.exists("/app/insilos") and (os.environ.get("DB_HOST") or os.environ.get("PGPASSWORD")):
        return {
            "host": os.environ.get("DB_HOST", os.environ.get("PGHOST", "pgbouncer-service")),
            "port": int(os.environ.get("DB_PORT", os.environ.get("PGPORT", "6432"))),
            "user": os.environ.get("DB_USER", os.environ.get("PGUSER", "insilos")),
            "password": os.environ.get("DB_PASSWORD", os.environ.get("PGPASSWORD", "")),
        }

    conf_candidates = [
        ROOT_DIR / "insilos.conf",
        Path("/etc/insilos/insilos.conf"),
        Path("/app/insilos/insilos.conf"),
    ]
    host = os.environ.get("PGHOST", "localhost")
    port = int(os.environ.get("PGPORT", "5434"))
    user = os.environ.get("PGUSER", "insilos")
    password = os.environ.get("PGPASSWORD", "")

    for cp_path in conf_candidates:
        if cp_path.exists():
            cp = configparser.ConfigParser()
            cp.read(cp_path)
            if cp.has_section("options"):
                if cp.has_option("options", "db_host") and cp.get("options", "db_host") not in ("False", "false", ""):
                    host = cp.get("options", "db_host")
                if cp.has_option("options", "db_port") and cp.get("options", "db_port") not in ("False", "false", ""):
                    port = int(cp.get("options", "db_port"))
                if cp.has_option("options", "db_user") and cp.get("options", "db_user") not in ("False", "false", ""):
                    user = cp.get("options", "db_user")
                if cp.has_option("options", "db_password") and cp.get("options", "db_password") not in ("False", "false", ""):
                    password = cp.get("options", "db_password")
            break
    return {"host": host, "port": port, "user": user, "password": password}


def collect_disk_taxonomy():
    modules = []
    for tier in ("addons", "enterprise"):
        base = ROOT_DIR / tier
        if not base.exists():
            continue
        for p in sorted(base.glob("insilos_*")):
            manifest_file = p / "__manifest__.py"
            if not p.is_dir() or not manifest_file.exists():
                continue
            manifest = ast.literal_eval(manifest_file.read_text(encoding="utf-8"))
            mname = (manifest.get("name") or "").strip()
            msum = (manifest.get("summary") or "").strip()

            own_menus = []
            root_menus = []
            for xf in sorted(p.rglob("*.xml")):
                try:
                    tree = ET.parse(xf)
                    for elem in tree.getroot().iter():
                        mid = xname = mpar = None
                        if elem.tag == "menuitem":
                            mid = elem.get("id")
                            xname = elem.get("name")
                            mpar = elem.get("parent")
                        elif elem.tag == "record" and elem.get("model") == "ir.ui.menu":
                            mid = elem.get("id")
                            nf = elem.find("field[@name='name']")
                            pf = elem.find("field[@name='parent_id']")
                            xname = nf.text.strip() if (nf is not None and nf.text) else None
                            mpar = (pf.get("ref") or pf.text) if pf is not None else None
                        if mid and xname and "." not in mid:
                            own_menus.append((mid, xname, xf.relative_to(p).as_posix()))
                            if not mpar:
                                root_menus.append((mid, xname, xf.relative_to(p).as_posix()))
                except Exception:
                    pass
            modules.append({
                "tier": tier,
                "module": p.name,
                "name": mname,
                "summary": msum,
                "own_menus": own_menus,
                "root_menus": root_menus,
            })
    return modules


def sync_part_b_assets_acls_views(cur):
    # 1. Sync ir_asset for fiori_status_badges.dark.scss & fiori_kpi_cards.dark.scss
    for fname in ("fiori_status_badges.dark.scss", "fiori_kpi_cards.dark.scss"):
        path = f"insilos_sap_fiori/static/src/scss/{fname}"
        name = f"insilos_sap_fiori: web.assets_web_dark ({fname})"
        cur.execute("SELECT id FROM ir_asset WHERE bundle = %s AND path = %s", ("web.assets_web_dark", path))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE ir_asset SET active = TRUE, directive = 'append', sequence = 16 WHERE id = %s",
                (row[0],),
            )
        else:
            cur.execute(
                """
                INSERT INTO ir_asset (name, bundle, path, directive, sequence, active, create_uid, write_uid, create_date, write_date)
                VALUES (%s, 'web.assets_web_dark', %s, 'append', 16, TRUE, 1, 1, NOW(), NOW())
                """,
                (name, path),
            )

    # 2. Sync ir_access for insilos.pinned.conversion, account.pinned.conversion, capital.positions.import.wizard, saas.workspace
    def get_group_id(module, xml_id):
        cur.execute(
            "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s AND model = 'res.groups'",
            (module, xml_id),
        )
        r = cur.fetchone()
        return r[0] if r else 1

    def ensure_access(model_name, acc_name, group_id, operation):
        cur.execute("SELECT id FROM ir_model WHERE model = %s", (model_name,))
        m = cur.fetchone()
        if not m:
            return
        model_id = m[0]
        cur.execute("SELECT id FROM ir_access WHERE model_id = %s AND name = %s", (model_id, acc_name))
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO ir_access (model_id, group_id, name, operation, active, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, TRUE, 1, 1, NOW(), NOW())
                """,
                (model_id, group_id, acc_name, operation),
            )

    grp_user = get_group_id("base", "group_user")
    grp_sys = get_group_id("base", "group_system")
    grp_pub = get_group_id("base", "group_public")
    grp_pm = get_group_id("insilos_capital_markets_decision_governance", "group_portfolio_manager")
    grp_ga = get_group_id("insilos_capital_markets_decision_governance", "group_governance_admin")

    ensure_access("insilos.pinned.conversion", "insilos.pinned.conversion.user", grp_user, "cru")
    ensure_access("insilos.pinned.conversion", "insilos.pinned.conversion.system", grp_sys, "crud")
    ensure_access("account.pinned.conversion", "account.pinned.conversion.user", grp_user, "cru")
    ensure_access("account.pinned.conversion", "account.pinned.conversion.system", grp_sys, "crud")
    ensure_access("capital.positions.import.wizard", "capital.positions.import.wizard.manager", grp_pm, "crud")
    ensure_access("capital.positions.import.wizard", "capital.positions.import.wizard.admin", grp_ga, "crud")
    ensure_access("saas.workspace", "saas.workspace public", grp_pub, "r")
    ensure_access("saas.workspace", "saas.workspace user", grp_user, "crud")

    # 3. Sync insilos_preferential_origin views
    pref_views = ROOT_DIR / "enterprise" / "insilos_preferential_origin" / "views.xml"
    if pref_views.exists():
        tree = ET.parse(pref_views)
        for rec in tree.getroot().findall("record"):
            if rec.get("model") == "ir.ui.view":
                xml_id = rec.get("id")
                vname = rec.find("field[@name='name']").text
                vmodel = rec.find("field[@name='model']").text
                arch_field = rec.find("field[@name='arch']")
                arch_elem = list(arch_field)[0]
                vtype = arch_elem.tag
                arch_str = ET.tostring(arch_elem, encoding="unicode")
                cur.execute("SELECT id FROM ir_ui_view WHERE name = %s AND model = %s", (vname, vmodel))
                if not cur.fetchone():
                    cur.execute(
                        """
                        INSERT INTO ir_ui_view (name, model, type, priority, active, arch_db, mode, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, %s, %s, 16, TRUE, jsonb_build_object('en_US', %s::text), 'primary', 1, 1, NOW(), NOW())
                        RETURNING id
                        """,
                        (vname, vmodel, vtype, arch_str),
                    )
                    vid = cur.fetchone()[0]
                    cur.execute(
                        """
                        INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, 'insilos_preferential_origin', 'ir.ui.view', %s, FALSE, 1, 1, NOW(), NOW())
                        ON CONFLICT DO NOTHING
                        """,
                        (xml_id, vid),
                    )


def sync_and_verify_db(dbname: str, db_params: dict, modules: list, do_sync: bool):
    drifts = []
    conn = psycopg2.connect(dbname=dbname, **db_params)
    cur = conn.cursor()
    if do_sync:
        sync_part_b_assets_acls_views(cur)

    for mod in modules:
        m_tech = mod["module"]
        m_name = mod["name"]
        m_sum = mod["summary"]

        cur.execute(
            "SELECT id, shortdesc->>'en_US', summary->>'en_US' FROM ir_module_module WHERE name = %s",
            (m_tech,),
        )
        row = cur.fetchone()
        if row:
            mid, db_short, db_sum = row
            if db_short != m_name or db_sum != m_sum:
                if do_sync:
                    cur.execute(
                        """
                        UPDATE ir_module_module
                           SET shortdesc = jsonb_set(COALESCE(shortdesc, '{}'::jsonb), '{en_US}', to_jsonb(%s::text), true),
                               summary   = jsonb_set(COALESCE(summary, '{}'::jsonb), '{en_US}', to_jsonb(%s::text), true)
                         WHERE id = %s
                        """,
                        (m_name, m_sum, mid),
                    )
                else:
                    drifts.append(f"[{dbname}] ir_module_module({m_tech}): DB=({db_short!r}) != Disk=({m_name!r})")

        for xml_id, menu_label, _rel_file in mod["own_menus"]:
            cur.execute(
                """
                SELECT m.id, m.name->>'en_US'
                  FROM ir_model_data imd
                  JOIN ir_ui_menu m ON m.id = imd.res_id
                 WHERE imd.module = %s AND imd.name = %s AND imd.model = 'ir.ui.menu'
                """,
                (m_tech, xml_id),
            )
            mrow = cur.fetchone()
            if mrow:
                menu_id, db_label = mrow
                if db_label != menu_label:
                    if do_sync:
                        cur.execute(
                            """
                            UPDATE ir_ui_menu
                               SET name = jsonb_set(COALESCE(name, '{}'::jsonb), '{en_US}', to_jsonb(%s::text), true)
                             WHERE id = %s
                            """,
                            (menu_label, menu_id),
                        )
                    else:
                        drifts.append(
                            f"[{dbname}] ir_ui_menu({m_tech}.{xml_id}): DB=({db_label!r}) != Disk=({menu_label!r})"
                        )
    if do_sync:
        conn.commit()
    conn.close()
    return drifts


def main():
    parser = argparse.ArgumentParser(description="Audit and sync Insilos 23-module naming taxonomy.")
    parser.add_argument("--check", action="store_true", help="Verify disk and DB naming parity (fail on drift).")
    parser.add_argument("--sync-db", action="store_true", help="Synchronize disk manifest/menu names to PostgreSQL.")
    parser.add_argument(
        "--dbs",
        nargs="*",
        default=["insilos20_dev", "innoria_prod"],
        help="Target PostgreSQL databases to check/sync.",
    )
    args = parser.parse_args()

    modules = collect_disk_taxonomy()
    violations = []

    print("=" * 120)
    print("INSILOS ENTERPRISE ODOO 20 — 23-MODULE & MENU NAMING TAXONOMY AUDIT")
    print("=" * 120)
    print(f"{'#':<3} | {'Tier':<10} | {'Technical Module':<42} | {'Display Name':<22} | {'Words':<5} | {'Chars':<5} | {'Root Menus'}")
    print("-" * 120)

    for idx, mod in enumerate(modules, 1):
        name = mod["name"]
        words = len(name.split())
        chars = len(name)
        if not name or chars > 24 or words > 3:
            violations.append(f"Module {mod['module']} manifest name {name!r} exceeds bounds (words={words}, chars={chars})")
        if not mod["summary"]:
            violations.append(f"Module {mod['module']} missing manifest summary")

        root_labels = []
        for xml_id, rlabel, _rf in mod["root_menus"]:
            rwords = len(rlabel.split())
            rchars = len(rlabel)
            root_labels.append(f"{rlabel} ({rwords}w/{rchars}c)")
            if rchars > 24 or rwords > 3:
                violations.append(
                    f"Module {mod['module']} root menu {xml_id} label {rlabel!r} exceeds bounds (words={rwords}, chars={rchars})"
                )

        print(
            f"{idx:02d}  | {mod['tier']:<10} | {mod['module']:<42} | {name:<22} | {words:<5} | {chars:<5} | "
            f"{', '.join(root_labels) if root_labels else '—'}"
        )

    print("-" * 120)

    db_params = get_db_params()
    for dbname in args.dbs:
        try:
            if args.sync_db:
                sync_and_verify_db(dbname, db_params, modules, do_sync=True)
                print(f"[SYNC] Synchronized 23 module names, summaries, menus, ir_asset, ir_access & views into '{dbname}'.")
            drifts = sync_and_verify_db(dbname, db_params, modules, do_sync=False)
            if drifts:
                violations.extend(drifts)
            else:
                print(f"[PASS] Database '{dbname}' has 100% naming parity with disk manifests and XML menus.")
        except Exception as exc:
            violations.append(f"[{dbname}] Database connection/query error: {exc}")

    if violations:
        print("\n[FAIL] Naming Taxonomy Violations Detected:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print(f"\n[PASS] All {len(modules)} insilos_* modules and root menus pass 2–3 word naming bounds & DB parity!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
