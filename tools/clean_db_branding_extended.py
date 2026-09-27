#!/usr/bin/env python3
"""
tools/clean_db_branding_extended.py
Extended database sanitization for ir_module_module, ir_ui_view.arch_prev, and ir_model.info.
Follows HARD_REFACTOR_PART_A and PART_B guidelines:
- Strict protection of technical contracts (model names, table names, XML IDs, internal python packages, JS bootstrap contracts).
- Idempotent and transaction safe.
"""

import psycopg2
import json
import re

def clean_module_descriptions(cur):
    print("1. Cleaning ir_module_module descriptions & URLs...")
    cur.execute("""
        SELECT id, name, description, url, reports_by_module, views_by_module 
        FROM ir_module_module 
        WHERE (description IS NOT NULL AND description::text ILIKE '%odoo%')
           OR (url IS NOT NULL AND url ~* 'odoo')
           OR (reports_by_module IS NOT NULL AND reports_by_module ~* '\\y(odoo)\\y')
           OR (views_by_module IS NOT NULL AND views_by_module ~* '\\y(odoo)\\y')
    """)
    rows = cur.fetchall()
    print(f"   Found {len(rows)} ir_module_module records matching.")

    updated_count = 0
    for mid, mname, desc, url, rep, views in rows:
        updates = []
        params = []

        if desc and isinstance(desc, dict):
            new_desc = {}
            changed = False
            for lang, val in desc.items():
                if val and isinstance(val, str):
                    new_val = re.sub(r'https?://(?:www\.)?odoo\.com', 'https://insilos.com', val)
                    new_val = re.sub(r'\bOdooBot\b', 'InsilosBot', new_val)
                    new_val = re.sub(r'\bOdoo\b', 'Insilos', new_val)
                    new_val = re.sub(r'\bODOO\b', 'INSILOS', new_val)
                    new_val = re.sub(r'\bodoo\b', 'insilos', new_val)
                    if new_val != val:
                        changed = True
                    new_desc[lang] = new_val
                else:
                    new_desc[lang] = val
            if changed:
                updates.append("description = %s::jsonb")
                params.append(json.dumps(new_desc))

        if url and 'odoo' in url.lower():
            new_url = 'https://insilos.com/app/mobile' if 'com.odoo.mobile' in url else re.sub(r'odoo\.com', 'insilos.com', url)
            updates.append("url = %s")
            params.append(new_url)

        if rep and re.search(r'\bodoo\b', rep, re.IGNORECASE):
            new_rep = re.sub(r'\bOdoo\b', 'Insilos', rep)
            new_rep = re.sub(r'\bodoo\b', 'insilos', new_rep)
            updates.append("reports_by_module = %s")
            params.append(new_rep)

        if views and re.search(r'\bodoo\b', views, re.IGNORECASE):
            new_views = re.sub(r'\bOdoo\b', 'Insilos', views)
            new_views = re.sub(r'\bodoo\b', 'insilos', new_views)
            updates.append("views_by_module = %s")
            params.append(new_views)

        if updates:
            params.append(mid)
            cur.execute(f"UPDATE ir_module_module SET {', '.join(updates)} WHERE id = %s", tuple(params))
            updated_count += 1

    print(f"   Successfully sanitized {updated_count} ir_module_module records.")

def clean_arch_prev(cur):
    print("2. Cleaning ir_ui_view arch_prev...")
    cur.execute("""
        SELECT id, name, arch_prev 
        FROM ir_ui_view 
        WHERE arch_prev IS NOT NULL 
          AND (arch_prev ~* '\\y(odoo|odoobot)\\y' OR arch_prev ~* '#875a7b|#714b67|/odoo/')
    """)
    rows = cur.fetchall()
    print(f"   Found {len(rows)} ir_ui_view arch_prev records to clean.")

    # Protected contracts to keep
    protected = [
        'odoo.__session_info__',
        'odoo.define',
        'window.odoo',
        'odoo.reloadMenus',
        'odoo.loadMenusPromise',
        'odoo.preparation_display',
    ]

    updated_count = 0
    for vid, vname, prev in rows:
        new_prev = prev
        # Replace URLs
        new_prev = re.sub(r'/odoo/action-', '/insilos/action-', new_prev)
        new_prev = re.sub(r'/odoo/(\d+)/action-', r'/insilos/\1/action-', new_prev)
        new_prev = re.sub(r'/odoo/users/', '/insilos/users/', new_prev)
        new_prev = re.sub(r'/odoo/sdd-mandates/', '/insilos/sdd-mandates/', new_prev)
        new_prev = re.sub(r'/odoo/accounting/', '/insilos/accounting/', new_prev)
        new_prev = new_prev.replace("url = '/odoo'", "url = '/insilos'")
        new_prev = re.sub(r'https?://(?:www\.)?odoo\.com', 'https://insilos.com', new_prev)

        # Replace legacy colors
        new_prev = re.sub(r'#875A7B', '#004455', new_prev, flags=re.IGNORECASE)
        new_prev = re.sub(r'#714B67', '#004455', new_prev, flags=re.IGNORECASE)

        # Replace user-facing words line by line, preserving protected JS contracts
        lines = new_prev.split('\n')
        new_lines = []
        for line in lines:
            if any(p in line for p in protected):
                new_lines.append(line)
            else:
                l = re.sub(r'\bOdooBot\b', 'InsilosBot', line)
                l = re.sub(r'\bodoobot\b', 'insilosbot', l)
                l = re.sub(r'\bOdoo\b', 'Insilos', l)
                l = re.sub(r'\bODOO\b', 'INSILOS', l)
                # Be careful not to replace python module names or xml namespaces
                if not any(skip in l for skip in ['xmlns', 'odoo/addons', 'from odoo', 'import odoo']):
                    l = re.sub(r'\bodoo\b', 'insilos', l)
                new_lines.append(l)
        new_prev = '\n'.join(new_lines)

        if new_prev != prev:
            cur.execute("UPDATE ir_ui_view SET arch_prev = %s WHERE id = %s", (new_prev, vid))
            updated_count += 1

    print(f"   Successfully sanitized {updated_count} ir_ui_view arch_prev records.")

def clean_arch_db(cur):
    print("3. Cleaning ir_ui_view arch_db user-facing views...")
    # View 173 (API Key show)
    cur.execute("""
        UPDATE ir_ui_view 
        SET arch_db = jsonb_set(arch_db, '{en_US}', to_jsonb(replace(arch_db->>'en_US', 'ODOO_MCP_KEY', 'INSILOS_MCP_KEY')))
        WHERE id = 173 AND arch_db::text LIKE '%ODOO_MCP_KEY%';
    """)
    # View 5879 (Recruitment apply)
    cur.execute("""
        UPDATE ir_ui_view 
        SET arch_db = jsonb_set(arch_db, '{en_US}', to_jsonb(replace(arch_db->>'en_US', 'https://www.linkedin.com/in/fpodoo', 'https://www.linkedin.com/in/insilos')))
        WHERE id = 5879 AND arch_db::text LIKE '%fpodoo%';
    """)
    # View 1178 (Facebook page snippet)
    cur.execute("""
        UPDATE ir_ui_view 
        SET arch_db = jsonb_set(arch_db, '{en_US}', to_jsonb(replace(arch_db->>'en_US', 'https%3A%2F%2Fwww.facebook.com%2FOdoo', 'https%3A%2F%2Fwww.facebook.com%2Finsilos')))
        WHERE id = 1178 AND arch_db::text LIKE '%facebook.com%2FOdoo%';
    """)
    # View 660 (digest_section_mobile)
    cur.execute("""
        UPDATE ir_ui_view 
        SET arch_db = jsonb_set(
            jsonb_set(arch_db, '{en_US}', to_jsonb(replace(arch_db->>'en_US', 'https://download.odoocdn.com/digests/digest/static/src/img/google_play.png', '/digest/static/src/img/google_play.png'))),
            '{en_US}', to_jsonb(replace(arch_db->>'en_US', 'https://download.odoocdn.com/digests/digest/static/src/img/app_store.png', '/digest/static/src/img/app_store.png'))
        )
        WHERE id = 660 AND arch_db::text LIKE '%download.odoocdn.com%';
    """)
    # View 8587 (Document Sign)
    cur.execute("""
        UPDATE ir_ui_view 
        SET arch_db = jsonb_set(arch_db, '{en_US}', to_jsonb(replace(arch_db->>'en_US', 'alt=\"Signed\"', 'alt=\"Insilos Sign\"')))
        WHERE id = 8587;
    """)
    print("   Sanitized key user-facing views in arch_db.")

def clean_model_info(cur):
    print("4. Cleaning ir_model.info docstrings...")
    cur.execute("""
        UPDATE ir_model 
        SET info = replace(replace(replace(info, 'database-persisted Odoo models', 'database-persisted Insilos models'), 'Odoo models are created', 'Insilos models are created'), 'for regular Odoo', 'for regular Insilos')
        WHERE info LIKE '%Odoo%';
    """)
    print(f"   Updated {cur.rowcount} ir_model.info records.")

def main():
    print("[EXTENDED DB CLEAN] Connecting to database...")
    conn = psycopg2.connect("host=127.0.0.1 port=5434 dbname=odoo20_dev user=odoo password=1NN0R1@2026")
    cur = conn.cursor()

    try:
        clean_module_descriptions(cur)
        clean_arch_prev(cur)
        clean_arch_db(cur)
        clean_model_info(cur)
        conn.commit()
        print("[PASS] Extended database clean committed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[FAIL] Error during extended db clean: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()

