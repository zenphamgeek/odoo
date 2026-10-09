#!/usr/bin/env python3
"""
Sync Innoria views from XML files into PostgreSQL innoria_prod database.
Converts <template id="xyz"> to Odoo's native QWeb <t t-name="module.key"> format.
Supports local (127.0.0.1:5434) and production environments.
"""

import sys
import os
import re
import json
import psycopg2

def extract_template_arch(xml_path, template_id, full_key):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Search for <template id="template_id" ...> ... </template>
    pattern = rf'(<template\s+[^>]*id=["\']{template_id}["\'][^>]*>)(.*?)(</template>)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Template '{template_id}' not found in {xml_path}")
    
    open_tag = match.group(1)
    body = match.group(2)
    
    name_match = re.search(r'name=["\']([^"\']+)["\']', open_tag)
    name_attr = f' name="{name_match.group(1)}"' if name_match else ''
    
    # Convert <template> to standard Odoo QWeb root <t t-name="...">
    return f'<t t-name="{full_key}"{name_attr}>{body}</t>'

def sync_database(host, port, user, password, dbname):
    print(f"[*] Connecting to {dbname} on {host}:{port} as {user}...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname
    )
    conn.autocommit = False
    cur = conn.cursor()

    candidate_dirs = [
        "/app/insilos/enterprise/insilos_website",
        "/app/insilos/apps/insilos_website",
        os.path.abspath("enterprise/insilos_website"),
        os.path.abspath("/home/zen/O20/enterprise/insilos_website"),
    ]
    module_dir = None
    for cand in candidate_dirs:
        if os.path.exists(os.path.join(cand, "views", "innoria_homepage.xml")):
            module_dir = cand
            break

    if not module_dir:
        raise FileNotFoundError(f"Could not find insilos_website module directory in candidates: {candidate_dirs}")

    print(f"[✓] Using module dir: {module_dir}")
    xml_homepage = os.path.join(module_dir, "views/innoria_homepage.xml")
    xml_snippets = os.path.join(module_dir, "views/snippets_3d.xml")
    xml_pages = os.path.join(module_dir, "views/innoria_pages.xml")
    xml_cctv = os.path.join(module_dir, "views/snippets_cctv.xml")

    targets = [
        ("innoria_navbar", "insilos_website.innoria_navbar", xml_homepage),
        ("innoria_homepage_template", "insilos_website.innoria_homepage_template", xml_homepage),
        ("innoria_footer", "insilos_website.innoria_footer", xml_homepage),
        ("s_innoria_3d_topology", "insilos_website.s_innoria_3d_topology", xml_snippets),
        ("s_innoria_3d_architecture_deck", "insilos_website.s_innoria_3d_architecture_deck", xml_snippets),
        ("s_innoria_3d_solutions_erp", "insilos_website.s_innoria_3d_solutions_erp", xml_snippets),
        ("s_innoria_3d_erp_shift", "insilos_website.s_innoria_3d_erp_shift", xml_snippets),
        ("s_insilos_cctv_ai_camera", "insilos_website.s_insilos_cctv_ai_camera", xml_cctv),
        ("insilos_about_page", "insilos_website.insilos_about_page", xml_pages),
        ("insilos_platform_page", "insilos_website.insilos_platform_page", xml_pages),
        ("innoria_digiforce_page", "insilos_website.innoria_digiforce_page", xml_pages),
        ("innoria_blockchain_page", "insilos_website.innoria_blockchain_page", xml_pages),
        ("insilos_solutions_page", "insilos_website.insilos_solutions_page", xml_pages),
        ("insilos_industries_page", "insilos_website.insilos_industries_page", xml_pages),
        ("innoria_contactus", "insilos_website.innoria_contactus", xml_pages),
    ]

    for tmpl_id, key, xml_path in targets:
        arch_xml = extract_template_arch(xml_path, tmpl_id, key)
        arch_dict = {"en_US": arch_xml}
        
        # Check if view exists
        cur.execute("SELECT id, name FROM ir_ui_view WHERE key = %s", (key,))
        row = cur.fetchone()
        if row:
            view_id, name = row
            cur.execute("""
                UPDATE ir_ui_view
                SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
                WHERE id = %s
            """, (json.dumps(arch_dict), view_id))
            print(f"[✓] Updated view {view_id} ({key}) - {len(arch_xml)} bytes (active=True, arch_fs=NULL)")
        else:
            cur.execute("""
                INSERT INTO ir_ui_view (name, key, type, mode, priority, active, arch_updated, arch_db, arch_fs, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 'qweb', 'primary', 16, true, true, %s::jsonb, NULL, 1, 1, NOW(), NOW())
                RETURNING id
            """, (tmpl_id, key, json.dumps(arch_dict)))
            new_view_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
                VALUES (%s, 'insilos_website', 'ir.ui.view', %s, false)
                ON CONFLICT (module, name) DO UPDATE SET res_id = EXCLUDED.res_id
            """, (tmpl_id, new_view_id))
            print(f"[✓] Inserted view {new_view_id} ({key}) - {len(arch_xml)} bytes (active=True, arch_fs=NULL)")

    # Also sync to insilos_website.insilos_homepage so controller fallback serves Innoria homepage
    homepage_arch_xml = extract_template_arch(xml_homepage, "innoria_homepage_template", "insilos_website.insilos_homepage")
    homepage_arch_dict = {"en_US": homepage_arch_xml}
    cur.execute("SELECT id FROM ir_ui_view WHERE key = 'insilos_website.insilos_homepage'")
    for row in cur.fetchall():
        v_id = row[0]
        cur.execute("""
            UPDATE ir_ui_view
            SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
            WHERE id = %s
        """, (json.dumps(homepage_arch_dict), v_id))
        print(f"[✓] Also synced homepage arch to insilos_website.insilos_homepage view {v_id} ({len(homepage_arch_xml)} bytes)")

    # Also sync to all website.homepage views (e.g. view 980 and 1688) so native website resolution serves the same hero slider
    cur.execute("SELECT id FROM ir_ui_view WHERE key = 'website.homepage'")
    for row in cur.fetchall():
        v_id = row[0]
        cur.execute("""
            UPDATE ir_ui_view
            SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
            WHERE id = %s
        """, (json.dumps(homepage_arch_dict), v_id))
        print(f"[✓] Also synced homepage arch to website.homepage view {v_id} ({len(homepage_arch_xml)} bytes)")

    # Ensure all innoria views have active = True
    cur.execute("UPDATE ir_ui_view SET active = true WHERE key LIKE '%innoria%' AND (active IS NULL OR active = false)")
    activated_views = cur.rowcount
    if activated_views > 0:
        print(f"[✓] Activated {activated_views} previously inactive innoria views")

    # Zero-Downtime Asset Lifecycle:
    # We DO NOT execute destructive 'DELETE FROM ir_attachment WHERE name LIKE web.assets_%'
    # Destructive deletes cause client-side 404s, unstyled flash, and concurrent compilation stampedes.
    # Instead, assets are pre-warmed atomically via tools/safe_asset_warmup.py.
    print("[✓] Preserving active asset bundles (atomic rotation handled by safe_asset_warmup.py)")

    conn.commit()
    conn.close()
    print("[✓] Synchronization committed successfully.")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'local'
    if target == 'local':
        sync_database('127.0.0.1', 5434, 'odoo', '1NN0R1@2026', 'innoria_prod')
    elif target == 'prod_pod':
        sync_database(
            os.environ.get('DB_HOST', 'pgbouncer-service'),
            int(os.environ.get('DB_PORT', 6432)),
            os.environ.get('DB_USER', 'insilos'),
            os.environ.get('PGPASSWORD', ''),
            'innoria_prod'
        )
